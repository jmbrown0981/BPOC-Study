#!/usr/bin/env python3
"""
build_general_orders.py

Turns the Fort Worth Police Department General Orders (web version PDF, converted
to text with `pdftotext -layout`) into the same data files codes.html uses for the
Texas codes, under assets/codes/GO/.

    pdftotext -layout general-orders_web-version-MM_DD_YYYY.pdf resources/codes_raw/GO/general-orders_YYYY-MM-DD.txt
    python tools/build_general_orders.py

Structure in the source:
    100.00  ORGANIZATION                 series heading (only the 100 series prints one)
    101.00  CHARTER AND ORDINANCE ...    chapter  -> one ch/<n>.json file
    101.01 ESTABLISHMENT AND DUTIES      section  -> one searchable item
    A. / 1. / a. / (1) / (a)             outline levels 0-4 inside a section

  * The source text file is only read.
  * Output goes to assets/codes/GO/ (stale files from an earlier GO build are removed)
    and the GO entry in assets/codes/codes.json is replaced.
  * "TBP x.xx" (Texas Best Practices) references and "(Revised m/d/yyyy)" in a section
    title are moved to tags shown next to the title.
  * Sections the web version withholds ("319.05 Unavailable", "303.06 - 303.11 Unavailable")
    become one placeholder item per section number, so a lookup by number still lands.
"""

from pathlib import Path
import json, re, sys

# ============================ CONFIGURATION ============================
REPO_ROOT   = Path(__file__).resolve().parent.parent
SOURCE_FILE = REPO_ROOT / "resources" / "codes_raw" / "GO" / "general-orders_2026-11-11.txt"
OUTPUT_ROOT = REPO_ROOT / "assets" / "codes"
CODE_ID     = "GO"
CODE_NAME   = "FWPD General Orders"
SOURCE_AS_OF = "2026-11-11"          # date on the PDF (general-orders_web-version-11_11_2026.pdf)
INDEX_PREFIX_LEN = 2
# Series names. Only "100.00 ORGANIZATION" is printed in the PDF; the others are labeled by number
# until real names are filled in here.
SERIES_NAMES = {}
# =======================================================================

sys.dont_write_bytecode = True   # don't leave tools/__pycache__ behind
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_code_search import normalize_for_search, RE_TOKEN   # same tokenizer as the statute builder

PAGE_HEADER = "Fort Worth Police Department General Orders"
RE_PAGENUM  = re.compile(r'^\s{10,}\d{1,3}\s*$')
RE_SERIES   = re.compile(r'^\s+([1-9])00\.00\s+([A-Z][^a-z]*?)\s*$')
RE_CHAPTER  = re.compile(r'^\s*(\d{3})\.00\s+([A-Z][^a-z]*?)\s*$')
RE_SECTION  = re.compile(r'^\s{0,2}(\d{3}\.\d{2})(?:\s*[-–]\s*(\d{3}\.\d{2}))?\s+(\S.*?)\s*$')
RE_TBP      = re.compile(r'\s*\bTBP\s+\d+\.\d+(?:\s*,\s*(?:and\s+)?(?:TBP\s+)?\d+\.\d+)*(?:\s*,?\s*and\s+(?:TBP\s+)?\d+\.\d+)?')
RE_REVISED  = re.compile(r'\s*\((Revised[^)]*)\)')
# outline markers -> level
MARKERS = [
    (re.compile(r'^([A-Z])\.\s+'), 0),
    (re.compile(r'^(\d{1,2})\.\s+'), 1),
    (re.compile(r'^([a-z])\.\s+'), 2),
    (re.compile(r'^\((\d{1,2})\)\.?\s+'), 3),
    (re.compile(r'^\(([a-z])\)\.?\s+'), 4),
]
RE_NOTE   = re.compile(r'^(NOTE|Note)\s*:')
RE_GAP    = re.compile(r'\S {4,}\S')
SHORT_LINE = 72        # a line shorter than this (with its indent) ends its paragraph


def section_title(rest):
    """Split '<TITLE> TBP 1.05 (Revised ...)' into (title, tags) or None if it isn't a heading."""
    tags = []
    m = RE_REVISED.search(rest)
    if m:
        tags.append(m.group(1)); rest = rest[:m.start()] + rest[m.end():]
    for m in RE_TBP.finditer(rest):
        tags.insert(0, re.sub(r'\s+', ' ', m.group(0).strip()))
    rest = RE_TBP.sub('', rest).strip()
    if not rest or re.search(r'[a-z]', rest) or not re.search(r'[A-Z]{2}', rest):
        return None
    return re.sub(r'\s+', ' ', rest), tags


def range_numbers(a, b):
    ch, x = a.split('.'); _, y = b.split('.')
    return [f"{ch}.{i:02d}" for i in range(int(x), int(y) + 1)]


def parse(lines):
    # pass 1: drop page headers/footers; mark the gap so it doesn't end a paragraph
    clean = []
    for ln in lines:
        if ln.strip() == PAGE_HEADER or RE_PAGENUM.match(ln):
            clean.append(None)              # page break
        else:
            clean.append(ln.rstrip())
    chapters, warnings = [], []
    series = {}
    front = {"n": "COE", "t": "CODE OF ETHICS", "ctx": ["FRONT MATTER"], "items": []}
    coe = {"n": "COE", "t": "LAW ENFORCEMENT CODE OF ETHICS", "l": []}
    front["items"].append(coe)
    chapters.append(front)
    ch = None; cur = coe
    para = None          # [type, level, text, last_line_len, indent]
    closed = True
    last_level = 0
    pending_blank = False
    after_break = False
    pending_ch_title = None   # chapter whose heading may continue on the next caps line

    def flush():
        nonlocal para
        if para is not None and cur is not None:
            cur["l"].append([para[0], para[1], re.sub(r'\s+', ' ', para[2]).strip() if para[0] != 'pre' else para[2]])
        para = None

    i = 0
    n = len(clean)
    while i < n:
        ln = clean[i]; i += 1
        if ln is None:
            # page break: blank lines around it don't end the paragraph
            pending_blank = False
            after_break = True
            continue
        if not ln.strip():
            if after_break:
                continue
            # blank line: ends the paragraph unless a page break follows before the next text
            j = i
            while j < n and clean[j] is not None and not clean[j].strip():
                j += 1
            if j < n and clean[j] is None:
                continue
            pending_blank = True
            continue
        after_break = False
        stripped = ln.strip()
        indent = len(ln) - len(ln.lstrip())

        # chapter heading continued on the next line (e.g. "201.00 DEPARTMENT ORDERS, ... AND" / "FORMS")
        if pending_ch_title is not None:
            if indent >= 10 and not re.search(r'[a-z]', stripped) and not RE_SECTION.match(ln) and not RE_CHAPTER.match(ln):
                pending_ch_title["t"] += ' ' + re.sub(r'\s+', ' ', stripped)
                pending_ch_title = None
                continue
            pending_ch_title = None

        m = RE_SERIES.match(ln)
        if m and not RE_SECTION.match(ln):
            flush(); series[m.group(1)] = m.group(2).upper()
            continue
        m = RE_CHAPTER.match(ln)
        if m:
            flush()
            num = m.group(1)
            title = re.sub(r'\s{2,}', ' ', m.group(2))
            s = num[0]
            ch = {"n": num + ".00", "t": title, "series": s, "items": []}
            chapters.append(ch); cur = None; closed = True; last_level = 0
            pending_ch_title = ch
            continue
        m = RE_SECTION.match(ln)
        st = section_title(m.group(3)) if m else None
        unavailable = bool(m) and m.group(3).strip().lower() == 'unavailable'
        if m and (st or unavailable) and ch is not None and m.group(1)[:3] == ch["n"][:3]:
            flush()
            nums = range_numbers(m.group(1), m.group(2)) if m.group(2) else [m.group(1)]
            if unavailable:
                for x in nums:
                    ch["items"].append({"n": x, "t": "UNAVAILABLE",
                                        "l": [["n", 0, "Not included in the public web version of the General Orders."]]})
                cur = None
            else:
                if m.group(2):
                    warnings.append(f"range with a title: {stripped}")
                cur = {"n": nums[0], "t": st[0], "l": []}
                if st[1]:
                    cur["tg"] = st[1]
                ch["items"].append(cur)
            closed = True; last_level = 0; pending_blank = False
            continue
        if m and not st and not unavailable and re.match(r'^\d{3}\.\d{2}\s+[A-Z]{3,}', stripped):
            warnings.append(f"line {i}: looks like a section heading but wasn't used: {stripped[:80]}")

        # ---- body text
        if cur is None:
            if ch is not None and stripped.lower() == 'unavailable':
                ch["items"].append({"sub": "This chapter is not included in the public web version of the General Orders."})
                continue
            if ch is not None and not ch["items"]:
                # text between a chapter heading and its first section: keep as an intro item
                cur = {"n": ch["n"], "t": ch["t"], "l": []}
                ch["items"].append(cur)
            else:
                warnings.append(f"line {i}: text outside any section: {stripped[:80]}")
                continue

        # section heading continued on the next line (all caps, no outline marker, no body yet)
        if cur is not None and not cur["l"] and para is None and cur.get("t") and cur["t"] != "UNAVAILABLE" \
                and not pending_blank and not re.search(r'[a-z]', stripped) and re.search(r'[A-Z]{2}', stripped) \
                and not any(rx.match(stripped) for rx, _ in MARKERS) and len(stripped) < 60:
            joined = section_title(cur["t"] + ' ' + stripped)
            if joined:
                cur["t"] = joined[0]
                if joined[1]:
                    cur["tg"] = cur.get("tg", []) + joined[1]
            else:
                cur["t"] += ' ' + re.sub(r'\s+', ' ', stripped)
            continue

        if pending_blank:
            closed = True; pending_blank = False

        marker_level = None; body = stripped
        for rx, lvl in MARKERS:
            mm = rx.match(stripped)
            if mm:
                marker_level = lvl; body = stripped[mm.end():]
                break
        is_note = bool(RE_NOTE.match(stripped))
        is_table = bool(RE_GAP.search(body)) and not RE_GAP.search(stripped[:12]) or \
                   (marker_level is None and bool(RE_GAP.search(stripped)))
        if is_table and marker_level is not None and not RE_GAP.search(body):
            is_table = False

        if is_table:
            if para is not None and para[0] == 'pre':
                para[2] += '\n' + ln[min(indent, para[4]):]
            else:
                flush(); para = ['pre', last_level, ln[indent:], len(ln), indent]
            closed = True
            continue
        if marker_level is not None:
            flush()
            text = stripped[:len(stripped) - len(body)].rstrip() + ' ' + body
            para = ['p', marker_level, text, len(ln), indent]
            last_level = marker_level; closed = False
        elif is_note:
            flush(); para = ['n', last_level, stripped, len(ln), indent]; closed = False
        elif para is not None and para[0] != 'pre' and not closed and (para[3] >= SHORT_LINE or cur is coe):
            para[2] += ('' if re.search(r'[A-Za-z]-$', para[2]) else ' ') + stripped; para[3] = len(ln)
        else:
            flush()
            lvl = 0 if indent <= 2 else last_level
            para = ['p', lvl, stripped, len(ln), indent]; closed = False
        if para is not None and para[3] < SHORT_LINE and para[0] != 'n' and cur is not coe:
            closed = True
    flush()

    # series context for each chapter
    for c in chapters[1:]:
        s = c.pop("series")
        name = SERIES_NAMES.get(s) or series.get(s)
        c["ctx"] = [f"{s}00 SERIES" + (f" — {name}" if name else "")]
    # drop empty intro items (heading-only)
    for c in chapters:
        c["items"] = [it for it in c["items"] if "sub" in it or it["l"] or it["n"] != c["n"] or True]
    return chapters, warnings


def main():
    lines = SOURCE_FILE.read_text(encoding='utf-8', errors='replace').replace('\r\n', '\n').split('\n')
    chapters, warnings = parse(lines)
    out_dir = OUTPUT_ROOT / CODE_ID
    (out_dir / "ch").mkdir(parents=True, exist_ok=True)
    (out_dir / "idx").mkdir(parents=True, exist_ok=True)

    seen = {}
    toc_chapters, toc_sections, postings, written = [], [], {}, set()
    for ci, ch in enumerate(chapters):
        fname = f"ch/{ch['n']}.json"
        toc_chapters.append({"n": ch["n"], "t": ch["t"], "ctx": ch["ctx"], "f": fname})
        for it in ch["items"]:
            if "n" not in it:
                continue
            if it["n"] in seen:
                warnings.append(f"duplicate section number {it['n']} (chapters {seen[it['n']]} and {ch['n']})")
            seen[it["n"]] = ch["n"]
            sid = len(toc_sections)
            toc_sections.append([it["n"], it["t"], ci])
            text = ' '.join([it["n"], it["t"]] + it.get("tg", []) + [x for _, _, x in it["l"]])
            for tok in set(RE_TOKEN.findall(normalize_for_search(text))):
                if len(tok) >= 2:
                    postings.setdefault(tok, []).append(sid)
        data = {"code": CODE_ID, "n": ch["n"], "t": ch["t"], "ctx": ch["ctx"], "items": ch["items"]}
        p = out_dir / fname
        p.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        written.add(p.resolve())

    toc = {"code": CODE_ID, "name": CODE_NAME, "asOf": SOURCE_AS_OF,
           "source": SOURCE_FILE.relative_to(REPO_ROOT).as_posix(), "prefixLen": INDEX_PREFIX_LEN,
           "secLabel": "GO", "chLabel": "GO", "officialUrl": None, "groupCtx": True,
           "chapters": toc_chapters, "sections": toc_sections}
    p = out_dir / "toc.json"
    p.write_text(json.dumps(toc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    written.add(p.resolve())

    shards = {}
    for tok, ids in postings.items():
        ids = sorted(set(ids))
        shards.setdefault(tok[:INDEX_PREFIX_LEN], {})[tok] = [ids[0]] + [b - a for a, b in zip(ids, ids[1:])]
    for key, shard in shards.items():
        p = out_dir / "idx" / (key.replace('.', '_') + ".json")
        p.write_text(json.dumps(shard, separators=(',', ':')), encoding='utf-8')
        written.add(p.resolve())
    for p in out_dir.rglob('*.json'):
        if p.resolve() not in written:
            p.unlink()

    codes_path = OUTPUT_ROOT / "codes.json"
    codes = json.loads(codes_path.read_text(encoding='utf-8'))
    codes = [c for c in codes if c.get("code") != CODE_ID]
    codes.append({"code": CODE_ID, "name": CODE_NAME, "asOf": SOURCE_AS_OF,
                  "chapters": len(toc_chapters), "sections": len(toc_sections)})
    codes.sort(key=lambda c: c["name"])
    codes_path.write_text(json.dumps(codes, ensure_ascii=False, indent=1), encoding='utf-8')

    size = sum(p.stat().st_size for p in out_dir.rglob('*.json'))
    print(f"{CODE_NAME} ({CODE_ID}): {len(toc_chapters)} chapters, {len(toc_sections)} sections, "
          f"{len(postings)} indexed words in {len(shards)} shards, {size/1024/1024:.1f} MB")
    for w in warnings[:80]:
        print("  -", w)
    if len(warnings) > 80:
        print(f"  ... and {len(warnings) - 80} more")


if __name__ == "__main__":
    main()
