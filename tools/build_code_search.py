#!/usr/bin/env python3
"""
build_code_search.py

Turns a folder of Texas statute chapter files (plain-text downloads from
statutes.capitol.texas.gov, one file per chapter) into the data files that
codes.html uses to browse and search a code.

  * Source files are only ever opened for reading. Nothing in SOURCE_DIR is
    written, moved, or deleted.
  * Output goes to OUTPUT_ROOT/<CODE_ID>/ plus a shared OUTPUT_ROOT/codes.json
    listing every code that has been built.
  * Legislative history ("Added by Acts...", "Amended by:" blocks, etc.) is
    dropped, EXCEPT for sections that exist in more than one version (same
    section number twice in a chapter) or that carry a "Text of section/
    subsection ..." version note. For those, the history is kept because it is
    what tells the versions apart.

Usage (from the repo root or anywhere):
    python tools/build_code_search.py
"""

from pathlib import Path

# ============================ CONFIGURATION ============================
# Edit these to build a different code.
REPO_ROOT    = Path(__file__).resolve().parent.parent
SOURCE_DIR   = REPO_ROOT / "resources" / "fam_code"   # where the chapter .txt files are read from
FILE_PATTERN = "fa.*.txt"                             # which files in SOURCE_DIR to read (glob; case-insensitive)
OUTPUT_ROOT  = REPO_ROOT / "assets" / "codes"         # generated files go in OUTPUT_ROOT/<CODE_ID>/
CODE_ID      = "FA"                                   # short code id; also used in statutes.capitol.texas.gov URLs
CODE_NAME    = "Family Code"                          # display name
SOURCE_ENCODING = "utf-8"                             # source files are ASCII; bad bytes are replaced, not fatal
SECTION_WORDS = ("Sec", "Art")                        # words that start a section line ("Sec. 51.02." / "Art. 2A.001.")
INDEX_PREFIX_LEN = 2                                  # search-index shard key length (first N chars of each word)
SOURCE_AS_OF = None                                   # "YYYY-MM-DD" date the source files were downloaded, shown on the
                                                      # site; None = most common file-modified date in SOURCE_DIR
# =======================================================================

import json
import re
import sys
from datetime import datetime, timezone

# ---- line patterns -----------------------------------------------------
# Structural headings at column 0: "TITLE 3. JUVENILE JUSTICE CODE", "SUBCHAPTER B-1.  COMMUNITY-BASED CARE"
RE_HEADING = re.compile(r'^(TITLE|SUBTITLE|CHAPTER|SUBCHAPTER|PART)\s+([0-9A-Z][0-9A-Za-z-]*)\.\s+(.*\S)\s*$')
# Section start (indented): "      Sec. 51.02.  DEFINITIONS.  In this title: ..."
RE_SECTION = re.compile(r'^\s+(?:' + '|'.join(SECTION_WORDS) + r')\.\s+(\d+[A-Za-z]?\.\d+[A-Za-z0-9-]*)\.\s*(.*)$')
# Section title = leading run with no lowercase letters, ending in a period (or end of line)
RE_TITLE = re.compile(r'^([^a-z]+?)\.(?:\s{2,}(.*))?$')
# Legislative history lines
RE_HISTORY = re.compile(r'^(Added by Acts|Amended by|Acts \d{4}|Redesignated|Renumbered|Transferred|'
                        r'Reenacted|Expired by|Amended and redesignated)')
# "Repealed by Acts ..." after a section that is still printed = a pending repeal; shown as a note, not dropped
RE_REPEAL = re.compile(r'^Repealed by Acts')
# Version notes that describe a whole section/article (may sit just before OR just after the "Sec." line)
RE_SECTION_VERSION_NOTE = re.compile(r'^Text of (section|article)\b', re.I)
# Page footers left over from the PDF-to-text conversion: "\tPage -2 -"
RE_PAGE = re.compile(r'^Page\s*-\s*\d+\s*-$')
# Editorial notes that sit at column 0 inside a section
RE_NOTE = re.compile(r'^(Text of|See note|For |Notwithstanding|Subchapter |Section |This section|'
                     r'Sections? .* (expires?|expired|effective))')
# Table rows: text with a wide internal gap
RE_TABLE = re.compile(r'\S {4,}\S')
# Search tokenizer: words and section-style numbers ("51.02", "35a")
RE_TOKEN = re.compile(r'[a-z0-9]+(?:\.[a-z0-9]+)*')


def natural_key(num):
    """Sort '1' < '2' < '35' < '35A' < '101'."""
    m = re.match(r'(\d+)(.*)', num)
    return (int(m.group(1)), m.group(2).upper()) if m else (10**9, num)


def section_key(num):
    a, _, b = num.partition('.')
    return natural_key(a) + natural_key(b)


def normalize_for_search(s):
    s = s.lower()
    s = re.sub(r'[‐-―-]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def parse_chapter(path):
    """Parse one chapter file into a dict (see write step for shape)."""
    raw = path.read_text(encoding=SOURCE_ENCODING, errors='replace')
    lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    chapter = {"n": None, "t": "", "ctx": [], "items": []}
    cur = None              # current section dict
    open_heading = None     # heading whose text may continue on the next line (long titles wrap)
    in_history = False
    pending_notes = []      # "Text of section ..." notes waiting for the section they describe
    warnings = []

    def new_section(num, rest):
        m = RE_TITLE.match(rest.strip())
        if m:
            title, body = m.group(1).strip(), (m.group(2) or '').strip()
        elif not re.search(r'[a-z]', rest):
            title, body = rest.strip().rstrip('.'), ''
        else:
            title, body = '', rest.strip()
        sec = {"n": num, "t": title, "l": [], "h": [], "notes": list(pending_notes)}
        pending_notes.clear()
        if body:
            add_body(sec, 0, body)
        return sec

    def add_body(sec, level, text):
        if RE_TABLE.search(text):
            sec["l"].append(["pre", level, text.rstrip()])
        else:
            sec["l"].append(["p", level, re.sub(r'\s+', ' ', text).strip()])

    first_text_seen = False
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        if not first_text_seen:
            first_text_seen = True
            if stripped == stripped.upper() and not RE_HEADING.match(stripped):
                continue  # code-name banner on line 1, e.g. "FAMILY CODE", "CODE OF CRIMINAL PROCEDURE"
        if RE_PAGE.match(stripped):
            continue
        indent = len(line) - len(line.lstrip(' \t'))

        # --- section start
        m = RE_SECTION.match(line)
        if m:
            in_history = False
            open_heading = None
            cur = new_section(m.group(1), m.group(2))
            chapter["items"].append(cur)
            continue

        # --- column-0 lines
        if indent == 0:
            h = RE_HEADING.match(stripped)
            if h:
                in_history = False
                kind = h.group(1)
                if kind == 'CHAPTER' and chapter["n"] is None:
                    chapter["n"] = h.group(2).upper()
                    chapter["t"] = re.sub(r'\s+', ' ', h.group(3))
                    open_heading = ("chapter",)
                elif kind in ('TITLE', 'SUBTITLE') and chapter["n"] is None:
                    chapter["ctx"].append(re.sub(r'\s+', ' ', stripped))
                    open_heading = ("ctx", len(chapter["ctx"]) - 1)
                else:
                    cur = None
                    chapter["items"].append({"sub": re.sub(r'\s+', ' ', stripped)})
                    open_heading = ("sub", chapter["items"][-1])
                continue
            # an all-caps line straight after a heading is the rest of that heading's title
            if open_heading and stripped == stripped.upper() and not RE_HISTORY.match(stripped):
                extra = ' ' + re.sub(r'\s+', ' ', stripped)
                if open_heading[0] == "chapter":
                    chapter["t"] += extra
                elif open_heading[0] == "ctx":
                    chapter["ctx"][open_heading[1]] += extra
                else:
                    open_heading[1]["sub"] += extra
                continue
            open_heading = None
            if RE_REPEAL.match(stripped) and cur is not None:
                in_history = False
                cur["l"].append(["n", 0, re.sub(r'\s+', ' ', stripped)])
                continue
            if RE_HISTORY.match(stripped):
                in_history = True
                if cur is not None:
                    cur["h"].append(re.sub(r'\s+', ' ', stripped))
                continue
            in_history = False
            if RE_NOTE.match(stripped):
                text = re.sub(r'\s+', ' ', stripped)
                if RE_SECTION_VERSION_NOTE.match(text) and cur is not None and not cur["l"]:
                    cur.setdefault("notes", []).append(text)   # note printed just after the heading
                elif RE_SECTION_VERSION_NOTE.match(text) or cur is None:
                    pending_notes.append(text)                 # note printed just before the next heading
                else:
                    cur["l"].append(["n", 0, text])
                continue
            # other column-0 text inside a section: compact articles ("ARTICLE I"), form text, etc.
            if cur is not None:
                is_caps = stripped == stripped.upper() and re.search(r'[A-Z]', stripped) and len(stripped) < 90
                cur["l"].append(["h" if is_caps else "p", 0, re.sub(r'\s+', ' ', stripped)])
            else:
                warnings.append(f"{path.name}:{lineno}: text outside any section: {stripped[:70]}")
            continue

        # --- indented lines
        if in_history and stripped.startswith('Acts '):
            if cur is not None:
                cur["h"].append(re.sub(r'\s+', ' ', stripped))
            continue
        in_history = False
        if cur is None:
            warnings.append(f"{path.name}:{lineno}: indented text outside any section: {stripped[:70]}")
            continue
        level = max(0, (indent - 6) // 6)
        add_body(cur, level, line.strip(' \t') if RE_TABLE.search(stripped) else stripped)

    if pending_notes:
        warnings.append(f"{path.name}: note(s) with no following section: {pending_notes}")

    # --- versions: keep history only where it distinguishes versions (or a version note / pending repeal is present)
    secs = [it for it in chapter["items"] if "n" in it]
    counts = {}
    for s in secs:
        counts[s["n"]] = counts.get(s["n"], 0) + 1
    seen = {}
    for s in secs:
        seen[s["n"]] = seen.get(s["n"], 0) + 1
        has_version_note = any(x.startswith('Text of') for x in s["notes"]) or \
                           any(t == 'n' and (x.startswith('Text of') or RE_REPEAL.match(x)) for t, _, x in s["l"])
        if counts[s["n"]] > 1:
            s["v"] = seen[s["n"]]            # version 1, 2, ...
        if not (counts[s["n"]] > 1 or has_version_note):
            s["h"] = []
        if not s["h"]:
            s.pop("h")
        if not s["notes"]:
            s.pop("notes")

    if chapter["n"] is None:
        m = re.search(r'\.([0-9]+[A-Za-z]?)\.txt$', path.name, re.I)
        chapter["n"] = m.group(1).upper() if m else path.stem
        warnings.append(f"{path.name}: no CHAPTER heading found; using number from file name")
    return chapter, warnings


def section_search_text(sec):
    parts = [sec["n"], sec.get("t", "")]
    parts += sec.get("notes", [])
    parts += [x for _, _, x in sec["l"]]
    return ' '.join(parts)


def main():
    if not SOURCE_DIR.is_dir():
        sys.exit(f"SOURCE_DIR not found: {SOURCE_DIR}")
    out_dir = OUTPUT_ROOT / CODE_ID
    if SOURCE_DIR.resolve() in out_dir.resolve().parents or out_dir.resolve() == SOURCE_DIR.resolve():
        sys.exit("OUTPUT_ROOT must not be inside SOURCE_DIR (source files are read-only).")

    pattern = re.compile(re.escape(FILE_PATTERN).replace(r'\*', '.*').replace(r'\?', '.') + '$', re.I)
    files = sorted(p for p in SOURCE_DIR.iterdir() if p.is_file() and pattern.match(p.name))
    if not files:
        sys.exit(f"No files in {SOURCE_DIR} match {FILE_PATTERN}")

    chapters, all_warnings = [], []
    for f in files:
        ch, w = parse_chapter(f)
        chapters.append(ch)
        all_warnings += w
    chapters.sort(key=lambda c: natural_key(c["n"]))

    dup_ch = [c["n"] for c in chapters]
    if len(set(dup_ch)) != len(dup_ch):
        all_warnings.append(f"duplicate chapter numbers: {sorted(set(x for x in dup_ch if dup_ch.count(x) > 1))}")

    # ---- write chapter files + table of contents
    (out_dir / "ch").mkdir(parents=True, exist_ok=True)
    (out_dir / "idx").mkdir(parents=True, exist_ok=True)
    toc_chapters, toc_sections, postings = [], [], {}
    written = set()
    for ci, ch in enumerate(chapters):
        fname = f"ch/{ch['n']}.json"
        toc_chapters.append({"n": ch["n"], "t": ch["t"], "ctx": ch["ctx"], "f": fname})
        for it in ch["items"]:
            if "n" not in it:
                continue
            sid = len(toc_sections)
            entry = [it["n"], it.get("t", ""), ci]
            if "v" in it:
                entry.append(it["v"])
            toc_sections.append(entry)
            for tok in set(RE_TOKEN.findall(normalize_for_search(section_search_text(it)))):
                if len(tok) >= 2:
                    postings.setdefault(tok, []).append(sid)
        data = {"code": CODE_ID, "n": ch["n"], "t": ch["t"], "ctx": ch["ctx"], "items": ch["items"]}
        p = out_dir / fname
        p.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        written.add(p.resolve())

    if SOURCE_AS_OF:
        as_of = SOURCE_AS_OF
    else:  # most common modified date, so one hand-edited file doesn't move the date
        dates = [datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).strftime('%Y-%m-%d') for f in files]
        as_of = max(set(dates), key=dates.count)
    toc = {"code": CODE_ID, "name": CODE_NAME, "asOf": as_of,
           "source": SOURCE_DIR.relative_to(REPO_ROOT).as_posix() if REPO_ROOT in SOURCE_DIR.parents else str(SOURCE_DIR),
           "prefixLen": INDEX_PREFIX_LEN, "chapters": toc_chapters, "sections": toc_sections}
    p = out_dir / "toc.json"
    p.write_text(json.dumps(toc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    written.add(p.resolve())

    # ---- search index, sharded by the first INDEX_PREFIX_LEN characters of each word.
    # Each shard maps word -> section ids, delta-encoded (ids ascending; store gaps).
    shards = {}
    for tok, ids in postings.items():
        ids = sorted(set(ids))
        deltas = [ids[0]] + [b - a for a, b in zip(ids, ids[1:])]
        shards.setdefault(tok[:INDEX_PREFIX_LEN], {})[tok] = deltas
    for key, shard in shards.items():
        p = out_dir / "idx" / (key.replace('.', '_') + ".json")
        p.write_text(json.dumps(shard, separators=(',', ':')), encoding='utf-8')
        written.add(p.resolve())

    # ---- remove files left over from an earlier build of this code (generated dir only)
    stale = [p for p in out_dir.rglob('*.json') if p.resolve() not in written]
    for p in stale:
        try:
            p.unlink()
        except OSError as e:
            all_warnings.append(f"could not remove stale file {p}: {e}")

    # ---- shared list of built codes
    codes_path = OUTPUT_ROOT / "codes.json"
    try:
        codes = json.loads(codes_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        codes = []
    codes = [c for c in codes if c.get("code") != CODE_ID]
    codes.append({"code": CODE_ID, "name": CODE_NAME, "asOf": as_of,
                  "chapters": len(toc_chapters), "sections": len(toc_sections)})
    codes.sort(key=lambda c: c["name"])
    codes_path.write_text(json.dumps(codes, ensure_ascii=False, indent=1), encoding='utf-8')

    # ---- report
    n_hist = sum(1 for ch in chapters for it in ch["items"] if "h" in it)
    n_ver = sum(1 for ch in chapters for it in ch["items"] if "v" in it)
    size = sum(p.stat().st_size for p in out_dir.rglob('*.json'))
    print(f"{CODE_NAME} ({CODE_ID}): {len(files)} files -> {len(toc_chapters)} chapters, "
          f"{len(toc_sections)} sections, {len(postings)} indexed words in {len(shards)} shards")
    print(f"  sections with multiple versions: {n_ver}; sections keeping history: {n_hist}")
    print(f"  output: {out_dir} ({size/1024/1024:.1f} MB), source as of {as_of}")
    if all_warnings:
        print(f"  {len(all_warnings)} warning(s):")
        for w in all_warnings[:50]:
            print("   -", w)
        if len(all_warnings) > 50:
            print(f"   ... and {len(all_warnings) - 50} more")


if __name__ == "__main__":
    main()
