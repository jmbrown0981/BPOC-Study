# Alt Quiz Bank Format

This is the hand-writable markdown format for Alt Quiz question banks. Each BPOC chapter (or
supplemental topic) gets its own bank file at `alt-quizzes/bank/{chapter-num}-{slug}.md`
(e.g. `alt-quizzes/bank/04-tcole-rules.md`, `alt-quizzes/bank/08-penal-code.md`). The
`alt-quiz.html` engine loads a bank file, parses it client-side, and renders it as an
interactive quiz — nothing needs to be compiled or converted first. You can add, edit, or
reorder questions directly in the `.md` file and reload the page to see the changes.

## File skeleton

```markdown
# Chapter 4: TCOLE Rules — Question Bank

### Q1 — Recall
**LO:** 4.2 · **Source:** BPOC 4.2

TCOLE was created by the ______ Legislature through Senate Bill 236, effective August 30, 1965.

- [ ] 58th
- [x] 59th
- [ ] 65th
- [ ] 88th

**Explanation:** TCOLE was created by the 59th Legislature via SB 236, effective August 30, 1965.

---

### Q2 — True/False
**LO:** 4.3 · **Source:** BPOC 4.3

TCOLE's Part 7 rules are organized under Title 37 of the Texas Administrative Code, Chapters
211–229.

- [x] True
- [ ] False

**Explanation:** Confirmed by the chapter list in BPOC 4.3.

---
```

## Anatomy of a question block

Every question is its own `###` heading, and blocks are separated by a line containing only
`---`. The parser splits the file on `---` first, then reads each block independently — so
as long as a block has the pieces below, order within the block doesn't matter much, but
keeping it consistent (heading → metadata → prompt → options → explanation) makes the file
easy for a human to scan.

**1. Heading — `### Q<number> — <Format Tag>`**
The number is just a label (doesn't need to be sequential, but keep it unique within the file
so you can refer to a question by name). The format tag after the em dash is free text, but
stick to this vocabulary so the quiz UI's badges/filters stay meaningful:

| Tag | Use for |
|---|---|
| `Recall` | Straightforward "what does the rule say" fact retrieval |
| `Fill-in-Blank` | A sentence with a blank, completed by picking the right option |
| `True/False` | Exactly two options, `True` and `False` |
| `Definition` | Term ↔ definition matching (what is L2? what is SOAH?) |
| `Concept` | Regular multiple choice that requires understanding, not just lookup |
| `Scenario` | A fact pattern/case study the reader has to apply a rule to |

**2. Metadata line (optional but recommended) — `**LO:** X.X · **Source:** ...`**
`LO` is the BPOC learning-objective number this question supports (e.g. `4.5`). `Source` is
whatever citation backs the answer — a rule section (`§218.3(b)(1)`), a BPOC bullet
(`BPOC 4.1`), or both. This isn't shown to the quiz-taker by default; it's there so you (or a
future editor) can trace a question back to its source text without re-deriving it. Skip it
only for genuinely uncited general-knowledge questions.

**3. Prompt**
Plain text (or a short fact pattern for `Scenario` questions). For `Fill-in-Blank`, use
`______` (six underscores) where the blank goes.

**4. Options — GitHub-style task list**
```
- [ ] wrong option
- [x] correct option
- [ ] wrong option
- [ ] wrong option
```
`- [x]` (lowercase x, inside the brackets) marks the correct answer. Use 4 options for regular
multiple choice, or exactly 2 — `True` and `False` — for a True/False question. Only mark
**one** option correct; the engine doesn't currently support multi-select.

Distractor guidance (matches what's worked well so far): pull wrong options from real
neighboring concepts in the same chapter, not made-up nonsense — e.g. for a question about the
40-hour continuing-education minimum, use other real hour thresholds from the same rule as
distractors, not random numbers. Someone who half-remembers the material should find the wrong
answers genuinely tempting.

**Important — keep each option on one physical line, however long.** The parser reads options
line by line; it does not support soft-wrapping an option's text onto a second line the way
you might wrap a prompt or explanation. If an option runs long, let the editor's line-wrap
handle it visually — don't insert a real line break inside it. (The prompt and explanation
fields *can* span multiple lines/paragraphs; only options can't.)

**5. Explanation (optional but recommended) — `**Explanation:** ...`**
Shown after the quiz-taker answers. This is your chance to state the rule clearly in plain
language, not just "correct/incorrect" — treat it as a mini study note.

## Full worked example (all 6 format tags)

```markdown
### Q7 — Definition
**LO:** 4.4 · **Source:** §217.7(a)(10)(A)(i)

What does the **L3** form represent in the appointment process?

- [ ] Statement of appointment
- [ ] Declaration of the lack of any drug dependency or illegal drug use
- [x] Declaration of psychological and emotional health
- [ ] Separation of appointment

**Explanation:** L1 = statement of appointment, L2 = drug/illegal-use declaration, L3 =
psychological/emotional health declaration, F-5 = separation of appointment.

---

### Q8 — Scenario
**LO:** 4.4 · **Source:** §217.7(a)(7), §217.7(a)(10)(A)

An officer resigned six months ago and is starting at a new department. The new department has
his L1 ready to sign, his F5-R completed, a full background investigation, and his personal
history statement and CCH on file. Which of the following is he still missing before he can be
appointed?

- [ ] A copy of his DD-214
- [x] Current firearms qualification within the last 12 months, plus new L2/L3 forms (since more than 180 days have passed since his last appointment)
- [ ] A new Personal History Statement
- [ ] Nothing — he's ready to be appointed

**Explanation:** §217.7(a)(7) requires proof of weapons qualification within the preceding 12
months for peace officers, and §217.7(a)(10)(A) requires a fresh L2 and L3 for any licensee
whose last appointment was more than 180 days ago — six months clears that threshold.

---

### Q9 — Concept
**LO:** 4.8 · **Source:** §223.17

True or false: a licensee who didn't maintain their legislatively required continuing
education during a suspension can reinstate their license the same way as one who did.

- [x] False
- [ ] True

**Explanation:** §223.17(b) — if a licensee didn't meet current training requirements or
didn't maintain CE during the suspension/probation, they must meet the *reactivation*
requirements instead of the simpler reinstatement process in §223.17(a).
```

(That last one shows a `True/False`-shaped question filed under a different tag — the tag is
about how you want it grouped/filtered in the UI, not a strict rendering rule. If the options
are literally `True`/`False`, the engine renders the True/False button layout regardless of
the tag you give it.)

## Dual-selector Scenario questions (Offense + Classification)

For chapters where the point is "read the fact pattern, name the offense, and name its
punishment classification," a question can use **two independent answer groups** instead of
one flat option list — one for the offense, one for the classification. Each is graded and
scored separately (half credit each), so a quiz-taker who correctly IDs the offense but picks
the wrong degree still gets partial credit.

```markdown
### Q1 — Scenario
**LO:** 8.9 · **Source:** PC 19.02(b)(1), 19.02(c)

A man intentionally shoots and kills a rival during a bar fight after an argument over a pool
game.

**Offense:**
- [ ] Manslaughter
- [x] Murder
- [ ] Criminally Negligent Homicide
- [ ] Aggravated Assault

**Classification:**
- [ ] Third Degree Felony
- [x] First Degree Felony
- [ ] State Jail Felony
- [ ] Class A Misdemeanor

**Explanation:** Intentionally causing death is Murder under PC 19.02(b)(1), a first-degree
felony under 19.02(c).

---
```

Rules for this shape:
- The literal lines `**Offense:**` and `**Classification:**` (each alone on its own line, no
  trailing text) switch the parser into that answer group. Everything before the first of
  these two headers is the scenario prompt.
- Each group needs its own `- [ ]`/`- [x]` option list, same rules as regular options (one
  correct answer per group, 4 options recommended, single physical line each, no soft-wrap).
- If a block has *both* an `**Offense:**` and a `**Classification:**` group, the engine treats
  it as a dual-selector question automatically — no separate tag is required, though tagging it
  `Scenario` is the convention.
- For "no offense committed" trick scenarios, make the correct offense option something like
  `No offense — [reason]` and pair it with a `N/A — no offense committed` classification option
  as the correct answer there too, so both groups still resolve to exactly one right answer.
- A block with only a flat option list (no `**Offense:**`/`**Classification:**` headers) parses
  exactly like before — this shape is fully backward-compatible with every existing bank.

## Fill-in-the-blank term identification (`**Answer:**` questions)

For a bank where the point is "read the full definition, name the term it defines" — as opposed to
picking the right definition off a list of options — a question block can skip `- [ ]`/`- [x]`
options entirely and use an `**Answer:**` field instead. The quiz-taker types the term into a text
box; the engine grades it spelling-exact but case-insensitive (hyphens and spaces are treated as
interchangeable, so "Right-of-way" and "Right of way" both match).

```markdown
### Q1 — Term ID
**LO:** 22.1 · **Source:** TC 541.201(1)

**Answer:** Authorized Emergency Vehicle

"______" means: (A) a fire department or police vehicle; (B) a public or private ambulance
operated by a person who has been issued a license by the Department of State Health Services...

**Explanation:** The term this defines is "Authorized Emergency Vehicle," straight from TC 541.201(1).

---
```

Rules for this shape:
- The heading tag is free text same as any other question — `Term ID` is the convention used so far,
  parallel to `Definition`/`Recall`/etc., but nothing enforces it.
- `**Answer:**` must appear before the blank-containing prompt text (right after the `**LO:**` line,
  same position `- [ ]` options would occupy) and holds the accepted term(s). Use `______` (six
  underscores, matching the `Fill-in-Blank` convention) at each spot in the prompt where the term
  would go — for definitions that name the same concept twice under two labels (e.g. Transportation
  Code's `"Park" or "parking" means...`), blank both.
- A block with an `**Answer:**` field and *no* `- [ ]` options parses as a fill-in-the-blank
  question. A block with options and no `**Answer:**` field parses as regular multiple choice, same
  as before — this is fully backward-compatible.
- **Multiple acceptable spellings** — when the source text defines two names for the same thing in
  one subsection — separate them with ` | ` in the `**Answer:**` field: `**Answer:** Park | Parking`.
  Either one is graded correct; the quiz only needs one match, not both.
- Keep the prompt text **verbatim** from the source (statute, rule, or lecture material) with only
  the term itself swapped for the blank — this question type exists specifically so the reader is
  studying the real defining language, not a paraphrase.

## What the engine does with this

- Loads every `.md` file in `alt-quizzes/bank/`, one per chapter.
- Chapter picker mirrors `quiz.html`'s chip row.
- Within a chapter, you can filter by format tag (e.g. "just Scenario questions") or run the
  full mixed bank.
- Options are shuffled per question at render time; question order is shuffled per attempt.
- No build step — edit the `.md`, refresh the page.

## Conventions to keep the bank maintainable

- One `.md` file per BPOC chapter number, named `{2-digit chapter}-{slug}.md`.
- Keep the `LO`/`Source` metadata even though it's invisible to quiz-takers — it's what makes
  a wrong answer fixable later without re-reading the whole rule chapter.
- If a fact can't be traced to specific rule text (instructor-added lecture content, a website
  reference, etc.), say so in the Explanation rather than presenting it with false certainty.
