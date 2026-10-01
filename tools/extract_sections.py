# -*- coding: utf-8 -*-
"""
Run this ON THE DEVICE (python3 33_supplemental/../.. context) where the raw
BPOC_markdown/33_supplemental/*.txt files live. Extracts first-level
subsections for each cited section, builds six CATEGORIES json files (one per
sorting game), and writes them to 33_supplemental/_extracted/.
"""
import re, json, os

SUP_DIR = "33_supplemental"
OUT_DIR = os.path.join(SUP_DIR, "_extracted")
os.makedirs(OUT_DIR, exist_ok=True)

header_re = re.compile(r'^(\s*)(Art\.|Sec\.)\s+([0-9A-Za-z][0-9A-Za-z.\-]*)\.\s*(.*)$')
subitem_re = re.compile(r'^(\s*)\(([0-9]+(?:-[a-z])?|[a-z]+|[A-Z]+)\)\s*(.*)$')
history_re = re.compile(r'^(Added by|Amended by|Renumbered from|Acts \d{4},|Transferred from)')

file_cache = {}
def get_lines(fname):
    if fname not in file_cache:
        with open(os.path.join(SUP_DIR, fname), encoding='utf-8', errors='replace') as f:
            file_cache[fname] = f.readlines()
    return file_cache[fname]


def extract_section(fname, num):
    """Return (title, [ (marker, text), ... ]) for the given section number."""
    lines = get_lines(fname)
    start_idx = None
    header_indent = None
    title = None
    header_rest = None
    for i, line in enumerate(lines):
        m = header_re.match(line)
        if m and m.group(3) == num:
            start_idx = i
            header_indent = len(m.group(1))
            header_rest = m.group(4)
            break
    if start_idx is None:
        return None, []

    # title = text up to first ". " after all-caps run, or up to first subsection marker
    # header_rest looks like: "DEFINITIONS.  In this chapter:" or "JURISDICTION.  (a)  This title..."
    title_m = re.match(r'^([A-Z0-9 ;,\'&/\-]+)\.\s*(.*)$', header_rest)
    if title_m:
        title = title_m.group(1).strip()
        remainder_first_line = title_m.group(2)
    else:
        title = header_rest.strip()
        remainder_first_line = ''

    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        m2 = header_re.match(lines[j])
        if m2:
            end_idx = j
            break

    # gather body lines (skip legislative history lines and blank lines at top-level scanning)
    body_lines = []
    if remainder_first_line.strip():
        body_lines.append((header_indent, remainder_first_line))
    for j in range(start_idx + 1, end_idx):
        raw = lines[j].rstrip('\n')
        if history_re.match(raw.strip()):
            continue
        if not raw.strip():
            continue
        body_lines.append((len(raw) - len(raw.lstrip()), raw.strip()))

    # find first-level subsection markers: indent equal to the shallowest marker indent seen
    marker_positions = []
    for idx, (indent, text) in enumerate(body_lines):
        m3 = subitem_re.match(text)
        # subitem_re expects raw text starting with '(' -- but we've already stripped leading ws
        m3b = re.match(r'^\(([0-9]+(?:-[a-z])?|[a-z]+|[A-Z]+)\)\s*(.*)$', text)
        if m3b:
            marker_positions.append((idx, indent, m3b.group(1), m3b.group(2)))

    if not marker_positions:
        # no subsections detected -- whole body is one card
        full_text = ' '.join(t for _, t in body_lines).strip()
        return title, [(None, full_text)]

    shallowest = min(p[1] for p in marker_positions)
    top_markers = [p for p in marker_positions if p[1] == shallowest]

    subsections = []
    for k, (idx, indent, marker, first_text) in enumerate(top_markers):
        end = top_markers[k + 1][0] if k + 1 < len(top_markers) else len(body_lines)
        pieces = [first_text]
        for m_idx in range(idx + 1, end):
            pieces.append(body_lines[m_idx][1])
        text = ' '.join(p for p in pieces if p).strip()
        subsections.append((marker, text))

    return title, subsections


def clean_text(t):
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def smart_trim(card_text, num, soft_limit=650, hard_limit=800):
    """Cut overly long cards at a clean clause boundary rather than mid-sentence,
    and note that the full text continues in the code (never silently drop the
    controlling rule -- this just trims exhaustive enumerated sub-lists)."""
    if len(card_text) <= hard_limit:
        return card_text
    window = card_text[:hard_limit]
    best_cut = -1
    for sep in ['; ', ': ', '. ']:
        pos = window.rfind(sep, soft_limit)
        if pos > best_cut:
            best_cut = pos + 1  # keep the punctuation, drop trailing space
    if best_cut == -1:
        # no clean boundary found -- fall back to a word boundary
        best_cut = window.rsplit(' ', 1)
        best_cut = len(best_cut[0]) if len(best_cut) > 1 else hard_limit
    trimmed = card_text[:best_cut].rstrip()
    return trimmed + f" — (see Sec./Art. {num} for the complete list)"


def build_game(sections, max_chars=420):
    """sections: list of (fname, num, override_title_or_None)"""
    categories = []
    for fname, num, override in sections:
        title, subs = extract_section(fname, num)
        if title is None:
            categories.append({"name": f"[MISSING {fname} {num}]", "items": []})
            continue
        display_title = override or title.title()
        items = []
        for marker, text in subs:
            text = clean_text(text)
            if not text:
                continue
            if marker:
                card_text = f"({marker}) {text}"
            else:
                card_text = text
            card_text = smart_trim(card_text, num)
            items.append({"text": card_text})
        if not items:
            items.append({"text": f"(No subsections on file for {num} — see {fname})"})
        bucket_name = f"{num} — {display_title}"
        categories.append({"name": bucket_name, "items": items})
    return categories


# ---------------------------------------------------------------------------
# GAME DEFINITIONS
# ---------------------------------------------------------------------------

GAME_A = [
    ("fa.51.txt", "51.01", "Purpose and Interpretation"),
    ("fa.51.txt", "51.02", "Definitions"),
    ("fa.51.txt", "51.03", "Delinquent Conduct; Conduct Indicating a Need for Supervision"),
    ("pe.49.txt", "49.04", "Driving While Intoxicated"),
    ("pe.49.txt", "49.05", "Flying While Intoxicated"),
    ("pe.49.txt", "49.06", "Boating While Intoxicated"),
    ("pe.49.txt", "49.07", "Intoxication Assault"),
    ("pe.49.txt", "49.08", "Intoxication Manslaughter"),
    ("al.106.txt", "106.04", "Consumption of Alcohol by a Minor"),
    ("fa.51.txt", "51.04", "Jurisdiction"),
    ("fa.51.txt", "51.09", "Waiver of Rights"),
    ("fa.51.txt", "51.095", "Admissibility of a Statement of a Child"),
    ("cr.38.txt", "38.22", "When Statements May Be Used"),
    ("cr.2b.txt", "2B.0202", "Recording of Custodial Interrogation Required; Exceptions"),
    ("fa.51.txt", "51.11", "Guardian Ad Litem"),
    ("fa.51.txt", "51.13", "Effect of Adjudication or Disposition"),
]

GAME_B = [
    ("fa.51.txt", "51.12", "Place and Conditions of Detention"),
    ("fa.52.txt", "52.025", "Designation of Juvenile Processing Office"),
    ("fa.52.txt", "52.026", "Responsibility for Transporting Juvenile Offenders"),
    ("fa.58.txt", "58.001", "Law Enforcement Collection and Transmittal of Records of Children"),
    ("fa.58.txt", "58.002", "Photographs and Fingerprints of Children"),
    ("fa.58.txt", "58.0021", "Fingerprints or Photographs for Comparison in Investigation"),
    ("fa.58.txt", "58.0022", "Fingerprints or Photographs to Identify Runaways"),
    ("fa.51.txt", "51.151", "Polygraph Examination"),
    ("fa.52.txt", "52.01", "Taking Into Custody; Issuance of Warning Notice"),
    ("fa.52.txt", "52.015", "Directive to Apprehend"),
    ("cr.45a.txt", "45A.453", "Child Taken Into Custody"),
    ("pe.25.txt", "25.03", "Interference With Child Custody"),
    ("pe.25.txt", "25.031", "Agreement to Abduct From Custody"),
    ("pe.25.txt", "25.04", "Enticing a Child"),
    ("pe.25.txt", "25.06", "Harboring Runaway Child"),
    ("pe.25.txt", "25.10", "Interference With Rights of Guardian of the Person"),
    ("pe.38.txt", "38.05", "Hindering Apprehension or Prosecution"),
    ("pe.38.txt", "38.15", "Interference With Public Duties"),
]

GAME_C = [
    ("fa.52.txt", "52.02", "Release or Delivery to Court"),
    ("fa.52.txt", "52.03", "Disposition Without Referral to Court"),
    ("fa.52.txt", "52.031", "First Offender Program"),
    ("fa.52.txt", "52.032", "Informal Disposition Guidelines"),
    ("fa.52.txt", "52.04", "Referral to Juvenile Court; Notice to Parents"),
    ("fa.54.txt", "54.02", "Waiver of Jurisdiction and Discretionary Transfer to Criminal Court"),
    ("fa.53.txt", "53.02", "Release From Detention"),
    ("fa.54.txt", "54.01", "Detention Hearing"),
    ("fa.54.txt", "54.011", "Detention Hearings for Status Offenders and Nonoffenders; Penalty"),
    ("cr.45a.txt", "45A.507", "Youth Diversion Coordinator"),
    ("fa.151.txt", "151.001", "Rights and Duties of Parent"),
    ("fa.151.txt", "151.003", "Limitation on State Agency Action"),
    ("fa.153.txt", "153.074", "Rights and Duties During Period of Possession"),
]

GAME_D = [
    ("fa.261.txt", "261.001", "Definitions"),
    ("fa.261.txt", "261.101", "Persons Required to Report; Time to Report"),
    ("fa.261.txt", "261.102", "Matters to Be Reported"),
    ("fa.261.txt", "261.103", "Report Made to Appropriate Agency"),
    ("fa.261.txt", "261.104", "Contents of Report; Notice"),
    ("fa.261.txt", "261.105", "Referral of Report by Department or Law Enforcement"),
    ("fa.261.txt", "261.106", "Immunities"),
    ("fa.261.txt", "261.107", "False Report; Criminal Penalty; Civil Penalty"),
    ("fa.261.txt", "261.109", "Failure to Report; Penalty"),
    ("pe.38.txt", "38.17", "Failure to Stop or Report Sexual or Assaultive Offense Against Child"),
    ("fa.261.txt", "261.202", "Privileged Communication"),
    ("fa.261.txt", "261.301", "Investigation of Report"),
    ("__WEB__", "2A.057", "Investigation of Certain Reports Alleging Abuse, Neglect, or Exploitation"),
    ("fa.261.txt", "261.302", "Conduct of Investigation"),
    ("fa.261.txt", "261.3126", "Colocation of Investigators"),
    ("fa.261.txt", "261.3032", "Interference With Investigation; Criminal Penalty"),
    ("fa.261.txt", "261.401", "Agency Investigation"),
    ("fa.261.txt", "261.405", "Investigations in Juvenile Justice Programs and Facilities"),
]

GAME_E = [
    ("fa.32.txt", "32.001", "Consent by Non-Parent"),
    ("fa.32.txt", "32.003", "Consent to Treatment by Child"),
    ("fa.32.txt", "32.005", "Examination Without Consent of Abuse or Neglect of Child"),
    ("fa.262.txt", "262.003", "Civil Liability"),
    ("fa.262.txt", "262.004", "Accepting Voluntary Delivery of Possession of Child"),
    ("fa.262.txt", "262.007", "Possession and Delivery of Missing Child"),
    ("fa.262.txt", "262.104", "Taking Possession of a Child in Emergency Without a Court Order"),
    ("__WEB__", "2A.051", "General Powers and Duties of Peace Officers"),
    ("fa.262.txt", "262.108", "Unacceptable Facilities for Housing Child"),
    ("fa.262.txt", "262.110", "Taking Possession of Child in Emergency With Intent to Return Home"),
    ("fa.264.txt", "264.403", "Interagency Memorandum of Understanding"),
    ("fa.264.txt", "264.408", "Use of Information and Records; Confidentiality and Ownership"),
]

GAME_F = [
    ("cr.15.txt", "15.27", "Notification to Schools Required"),
    ("cr.63.txt", "63.001", "Definitions"),
    ("cr.63.txt", "63.0015", "Presumption Regarding Parentage"),
    ("cr.63.txt", "63.002", "Missing Children and Missing Persons Information Clearinghouse"),
    ("cr.63.txt", "63.003", "Function of Clearinghouse"),
    ("cr.63.txt", "63.009", "Law Enforcement Requirements Generally"),
    ("cr.63.txt", "63.00905", "Law Enforcement Requirements for Report of Missing Child"),
    ("cr.63.txt", "63.0091", "Law Enforcement Requirements Regarding Reports of Certain Missing Children"),
    ("cr.63.txt", "63.011", "Missing Children Investigations"),
    ("cr.63.txt", "63.021", "System for Flagging Records"),
    ("cr.63.txt", "63.020", "Duty of Schools and Other Entities to Flag Missing Children's Records"),
    ("cr.63.txt", "63.022", "Removal of Flag From Records"),
    ("cr.63.txt", "63.019", "School Records System"),
    ("cr.63.txt", "63.017", "Confidentiality of Certain Records"),
    ("gv.411.txt", "411.351", "Definitions"),
    ("gv.411.txt", "411.352", "Statewide AMBER Alert System for Abducted Children"),
    ("gv.411.txt", "411.355", "Activation"),
    ("gv.411.txt", "411.358", "Termination"),
]

# Web-sourced sections not present in the local supplemental files
WEB_SECTIONS = {
    "2A.051": {
        "title": "General Powers and Duties of Peace Officers",
        "items": [
            {"text": "(1) Preserve the peace within the officer's jurisdiction using all lawful means"},
            {"text": "(2) In every case authorized by this code, interfere without a warrant to prevent or suppress crime"},
            {"text": "(3) Execute all lawful process issued to the officer by a magistrate or court"},
            {"text": "(4) Give notice to an appropriate magistrate of all offenses committed in the officer's jurisdiction, where the officer has good reason to believe there has been a violation of the penal law"},
            {"text": "(5) When authorized by law, arrest an offender without a warrant so the offender may be taken before the proper magistrate or court and be tried"},
            {"text": "(6) Take possession of a child under Article 63.00905(g)"},
            {"text": "(7) On a request made by the Texas Civil Commitment Office, execute an emergency detention order issued by that office"},
        ],
    },
    "2A.057": {
        "title": "Investigation of Certain Reports Alleging Abuse, Neglect, or Exploitation",
        "items": [
            {"text": "(a) In this article, ‘department’ means the Department of Family and Protective Services"},
            {"text": "(b) A peace officer shall investigate jointly with the department if the report is assigned the highest priority and alleges an immediate risk of physical or sexual abuse of a child that could result in death or serious harm by a person responsible for the child's care, custody, or welfare"},
            {"text": "(c) As soon as possible, but not later than 24 hours, after being notified by the department of a highest-priority report, the peace officer shall accompany the department investigator in initially responding to the report"},
            {"text": "(d) On receipt of a report of abuse, neglect, exploitation, or other complaint regarding a resident of a nursing home, convalescent home, or similar institution or assisted living facility, the local law enforcement agency shall investigate as required by Section 260A.017, Health and Safety Code"},
        ],
    },
}


def build_game_with_web(sections, max_chars=420):
    categories = []
    for fname, num, override in sections:
        if fname == "__WEB__":
            web = WEB_SECTIONS[num]
            categories.append({
                "name": f"{num} — {web['title']}",
                "items": web["items"],
            })
            continue
        title, subs = extract_section(fname, num)
        if title is None:
            categories.append({"name": f"[MISSING {fname} {num}]", "items": []})
            continue
        display_title = override or title.title()
        items = []
        for marker, text in subs:
            text = clean_text(text)
            if not text:
                continue
            card_text = f"({marker}) {text}" if marker else text
            card_text = smart_trim(card_text, num)
            items.append({"text": card_text})
        if not items:
            items.append({"text": f"(No subsections on file for {num} — see {fname})"})
        categories.append({"name": f"{num} — {display_title}", "items": items})
    return categories


GAMES = {
    "game_a_fundamentals": GAME_A,
    "game_b_custody_records": GAME_B,
    "game_c_court_process": GAME_C,
    "game_d_abuse_investigation": GAME_D,
    "game_e_medical_emergency": GAME_E,
    "game_f_missing_children_amber": GAME_F,
}

summary = {}
for key, sections in GAMES.items():
    cats = build_game_with_web(sections)
    total_cards = sum(len(c["items"]) for c in cats)
    missing = [c["name"] for c in cats if c["name"].startswith("[MISSING")]
    summary[key] = {"buckets": len(cats), "cards": total_cards, "missing": missing}
    with open(os.path.join(OUT_DIR, key + ".json"), "w", encoding="utf-8") as f:
        json.dump(cats, f, ensure_ascii=False, indent=None)

for k, v in summary.items():
    print(k, "-> buckets:", v["buckets"], "cards:", v["cards"], "missing:", v["missing"])
