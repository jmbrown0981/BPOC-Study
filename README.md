[README.md](https://github.com/user-attachments/files/30288508/README.md)
# BPOC Study Hub — Hosting Guide

**This study guide is a fork of https://just-a-trashpanda.github.io/BPOC-Study/index.html**

## Main URL

https://jmbrown0981.github.io/BPOC-Study/index.html

## What this is

A static, GitHub Pages-hosted study site built by and for the Fort Worth PD Academy BPOC (Basic Peace Officer Course) class. It supplements the official course material with a live study reference, hand-authored practice question banks, flashcards, and a plain-language case-law guide — all built from the actual BPOC chapter PDFs, Texas statute text, and course-cited case law, not generated from a generic prep-book question set.

There's no build step, bundler, or server-side code. Every page is a self-contained HTML file (styles and JavaScript inline) that fetches its content — chapter reference pages, quiz/flashcard banks, statute text — as plain files at runtime, so the whole thing runs straight off GitHub Pages.

## File Layout

```
BPOC-Study/
├── index.html                  Hub page — BPOC chapter grid, supplemental materials, links to everything below
├── study.html                  Live study reference, built out chapter by chapter as source material comes in
├── alt-quiz.html               Alt Quiz engine — loads and runs all 24 question banks, plus the "Full Practice
│                                  Exam" mode (250 questions randomly weighted across every bank)
├── flashcards.html             Flashcard engine — same 24 banks as Alt Quiz, front/back recall format instead
│                                  of multiple choice
├── case-law.html               Case-law reference — Summary + "Law Enforcement Application" for every case on
│                                  the master course case-law list
│
├── alt-quizzes/
│   ├── FORMAT.md                Markdown spec every question bank file follows (see "Quizzes & Flashcards" below)
│   ├── exam-weights.json        Per-bank weight config for the Full Practice Exam mode — tune this to change how
│   │                              often a given bank's questions show up, no code changes needed
│   ├── bank/                    The 24 live question bank files (one .md per BPOC chapter or topic, e.g.
│   │                              06-racial-profiling.md, case-law.md)
│   ├── drafts/                  Work-in-progress bank drafts not yet wired into the site
│   ├── 22-codes-index.html      Ch.22 mindmap tool — every code section the BPOC Ch.22 material cites, with a
│   │                              live link to that section on statutes.capitol.texas.gov
│   ├── 22-definitions-map.html  Ch.22 mindmap tool — defined terms from the traffic-code material, grouped by
│   │                              topic and cross-linked to their source section
│   ├── 22-offense-penalties.html  Ch.22 mindmap tool — every offense the Ch.22 material calls out with its
│   │                              statute, level, and fine/jail range, plus the general-penalty catchalls and
│   │                              the Illegal Dumping value ladder
│   └── 22-traffic-code-definitions-hierarchy.md   Working notes behind 22-definitions-map.html
│
├── assets/                      Shared theme CSS, Google Fonts config, site favicon, FWPD badge art, and
│                                  chapters-data.js (the shared chapter metadata behind study.html/flashcards.html)
│
├── supplemental/
│   ├── penal-code.html          Texas Penal Code offense reference (statute, plain-language definition,
│   │                              punishment range, enhancements, grade/theft-value ladders)
│   ├── laymans/                 Penal Code Layman's Guide — plain-language, chapter-by-chapter walkthroughs of
│   │                              what each offense means and how it's graded (26 chapters), plus a standalone
│   │                              classification chart, value-ladders page, and victim-enhancements page
│   └── laymans-ccp/             Plain-language Code of Criminal Procedure guide, organized by the CCP articles
│                                  BPOC actually cites (11 chapters)
│
├── resources/                   Source material everything else is built from — not linked from the site
│   │                              directly, but this is what to check against for ground truth
│   ├── BPOC_PDF/                 Original BPOC chapter PDFs (all 43 chapters) as issued for the course
│   ├── BPOC_markdown/            Text-extracted, markdown version of every BPOC chapter PDF — this is what
│   │                              question banks and reference pages are actually drafted from
│   ├── TCOLE_markdown/           TCOLE rules/handbook material in markdown
│   ├── TCOLE Rules/               Original TCOLE handbook PDF
│   ├── CCP/                      Texas Code of Criminal Procedure article text, plain .txt per article
│   ├── penal_code/                Texas Penal Code section text, plain .txt per section, plus html_laymans/ —
│   │                              the HTML source used to build supplemental/laymans/
│   ├── traffic_code/              Texas Transportation Code section text, plain .txt per section — source
│   │                              behind the Ch.22 mindmap tools and the Ch.22 Day 1-8 quiz banks
│   ├── health_safety_code/        Texas Health & Safety Code section text, plain .txt per section — covers the
│   │                              litter/illegal-dumping material the Ch.22 material cites
│   ├── TX Constitution/           Texas Constitution article text
│   ├── us_constitution/           U.S. Constitution text (markdown + PDF)
│   ├── case_law.txt               The master, deduplicated list of every case cited across the BPOC chapters
│   │                              this site covers — the single source of truth case-law.html and the
│   │                              case-law.md quiz/flashcard bank are both built from
│   └── Schedule/                  Class schedule images
│
└── README.md
```

## Quizzes & Flashcards share the same source material

Alt Quiz and Flashcards are two different front-ends over the *exact same* bank files in `alt-quizzes/bank/`. Neither has its own separate content to maintain — both fetch the same `.md` file for a given chapter, run it through the same `parseBank()` markdown parser, and just render the parsed questions differently (multiple-choice with scoring vs. a flip-card front/back). That means:

- Editing a question in a bank file changes it everywhere it's used — quiz, flashcards, and the Full Practice Exam pool — automatically, with nothing else to update.
- A bank only shows up in one of the two engines if its chapter key is missing from that engine's manifest (`ALT_QUIZ_CHAPTERS` in `alt-quiz.html` / `FLASHCARD_CHAPTERS` in `flashcards.html`). The standing convention on this project is that both manifests stay in sync — a new bank gets added to both at the same time.
- The bank markdown format (headings, `**LO:**`/`**Source:**` metadata, options, explanation, and the dual Offense/Classification format used by the Chapter 8 scenario bank) is documented in `alt-quizzes/FORMAT.md`.

## A note on accuracy

This site is built and checked carefully — question banks are verified both structurally (option counts, one correct answer, no malformed markdown) and by running them through the actual parser the live site uses, and case-law and statute content is cross-referenced against source material before publishing. That said, this is class-built study material, not an official BPOC or TCOLE publication, and it can contain mistakes — a mis-transcribed citation, a statute that's been amended since the source PDF was issued, a nuance lost in summarizing.

Treat everything here as a study aid, not a substitute for the primary sources. Before relying on anything for the actual exam or in the field, cross-check it against the material in `resources/` (the original BPOC chapter PDFs/markdown, CCP and Penal Code statute text, TCOLE handbook) and against publicly available, current BPOC curriculum and Texas statute sources — [statutes.capitol.texas.gov](https://statutes.capitol.texas.gov) for current Penal Code/CCP text, and TCOLE's own published curriculum and rules for anything TCOLE-specific. Statutes get amended and case law gets decided after this site was last updated; the primary source is always the tie-breaker.
