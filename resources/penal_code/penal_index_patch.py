# -*- coding: utf-8 -*-
import re

PATH = "index.html"
content = open(PATH, encoding='utf-8').read()

before_div_count = content.count('<div')
before_closediv_count = content.count('</div>')

old_header = '<span class="supp-group-name">Texas Penal Code <span class="supp-group-count">3 resources</span></span>'
new_header = '<span class="supp-group-name">Texas Penal Code <span class="supp-group-count">22 resources</span></span>'
assert content.count(old_header) == 1, "header anchor not found exactly once"
content = content.replace(old_header, new_header)

anchor = '''    <a class="supp-card status-live" href="alt-quizzes/8-penal-code-sorting-game.html">
      <div class="supp-name">Ch. 8 Penal Code — Offense Sorting Game</div>
      <div class="supp-desc">Drag-and-drop (or tap-to-select) mini-game — 65 boxes covering every offense in the site's Penal Code reference plus three general boxes (mental-state definitions &amp; doctrine, general defenses &amp; justifications, cross-cutting Ch.12 enhancements). 189 cards: culpable mental states, base offense-level tiers, enhancements with their resulting classification, and defenses/affirmative defenses — sort each into the offense it belongs to and track correct/incorrect across sessions.</div>
    </a>
'''
assert content.count(anchor) == 1, "insertion anchor not found exactly once"

CARD_T = '''    <a class="supp-card status-live" href="alt-quizzes/{href}">
      <div class="supp-name">{name}</div>
      <div class="supp-desc">{desc}</div>
    </a>
'''

cards_data = [
    ("penal-general-preparatory-sorting-game.html",
     "Penal Code &mdash; General Provisions &amp; Preparatory Offenses Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; 17 statute-section boxes, 42 subsection cards, covering Chapter 1 (General Provisions: objectives, jurisdiction, construction, definitions, preemption, federal-firearms-enforcement restriction) and Chapter 15 (Preparatory Offenses: attempt, conspiracy, solicitation, solicitation of a minor, child grooming, renunciation defense)."),
    ("penal-homicide-kidnapping-trafficking-sorting-game.html",
     "Penal Code &mdash; Homicide, Kidnapping &amp; Trafficking of Persons Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; 17 statute-section boxes, 49 subsection cards, covering Chapter 19 (Criminal Homicide), Chapter 20 (Unlawful Restraint, Kidnapping, Aggravated Kidnapping, Smuggling of Persons), and Chapter 20A (Trafficking of Persons)."),
    ("penal-sexual-offenses-sorting-game.html",
     "Penal Code &mdash; Sexual Offenses Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; all of Chapter 21, 15 statute-section boxes and 64 subsection cards, from continuous sexual abuse and indecency with a child through invasive visual recording, voyeurism, and sexual coercion."),
    ("penal-assaultive-offenses-sorting-game.html",
     "Penal Code &mdash; Assaultive Offenses Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; all of Chapter 22, 15 statute-section boxes and 75 subsection cards, covering assault through aggravated sexual assault, injury to a child/elderly/disabled individual, deadly conduct, terroristic threat, and harassment of public servants."),
    ("penal-offenses-against-family-sorting-game.html",
     "Penal Code &mdash; Offenses Against the Family Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; all of Chapter 25, 15 statute-section boxes and 53 subsection cards, from bigamy and interference with child custody through sale of a child and continuous violence against the family."),
    ("penal-arson-robbery-burglary-sorting-game.html",
     "Penal Code &mdash; Arson, Robbery, Burglary &amp; Criminal Trespass Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; 21 statute-section boxes, 99 subsection cards, covering Chapter 28 (Arson, Criminal Mischief, Graffiti), Chapter 29 (Robbery, Aggravated Robbery, Jugging), and Chapter 30 (Burglary, Burglary of Vehicles, Criminal Trespass, handgun-license trespass). Boxes default to a collapsed view given the size."),
    ("penal-computer-telecom-crimes-sorting-game.html",
     "Penal Code &mdash; Computer &amp; Telecommunications Crimes Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; 17 statute-section boxes, 56 subsection cards, covering Chapter 33 (Breach of Computer Security, Online Solicitation of a Minor, ransomware, Online Impersonation) and Chapter 33A (Telecommunications Service theft/unauthorized use/device offenses)."),
    ("penal-theft-sorting-game.html",
     "Penal Code &mdash; Theft Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; all of Chapter 31, 23 statute-section boxes and 102 subsection cards, from theft and theft of service through organized retail theft, cargo theft, mail theft, and real property theft. Boxes default to a collapsed view given the size."),
    ("penal-fraud-1-sorting-game.html",
     "Penal Code &mdash; Fraud I Sorting Game (Forgery, Fiscal Instruments &amp; Deceptive Practices)",
     "First of two Chapter 32 games (Fraud runs 36 sections, split in half) &mdash; 18 statute-section boxes, 67 subsection cards, covering forgery, credit/debit card abuse, bad checks, deceptive business practices, commercial bribery, and rigging a contest."),
    ("penal-fraud-2-sorting-game.html",
     "Penal Code &mdash; Fraud II Sorting Game (Fiduciary, Identity &amp; Real Property Fraud)",
     "Second of two Chapter 32 games &mdash; 18 statute-section boxes, 72 subsection cards, covering misapplication of fiduciary property, identity fraud, fraudulent/fictitious degrees and military records, financial abuse of the elderly, real property fraud, and &sect;32.56 &mdash; enacted four separate times under the same number for four unrelated offenses, each kept here as its own box."),
    ("penal-bribery-perjury-sorting-game.html",
     "Penal Code &mdash; Bribery, Perjury &amp; Official Falsification Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; 27 statute-section boxes, 77 subsection cards, covering Chapter 36 (Bribery, Coercion of a Public Servant, Tampering With a Witness) and Chapter 37 (Perjury, False Report to a Peace Officer, Tampering With Evidence/Governmental Records, Impersonating a Public Servant). Boxes default to a collapsed view given the size."),
    ("penal-obstructing-govt-1-sorting-game.html",
     "Penal Code &mdash; Obstructing Governmental Operation I Sorting Game",
     "First of two Chapter 38 games (Obstructing Governmental Operation runs 30 sections, split in half) &mdash; 15 statute-section boxes, 60 subsection cards, covering failure to identify, resisting arrest, evading arrest/detention, escape, bail jumping, and correctional-facility contraband offenses."),
    ("penal-obstructing-govt-2-abuse-office-sorting-game.html",
     "Penal Code &mdash; Obstructing Governmental Operation II &amp; Abuse of Office Sorting Game",
     "Second of two Chapter 38 games, plus all of Chapter 39 &mdash; 24 statute-section boxes, 82 subsection cards, covering barratry, interference with public duties/police service animals, failure to report a felony or child abuse (Ch.38), and abuse of official capacity, official oppression, and misuse of official information (Ch.39). Boxes default to a collapsed view given the size."),
    ("penal-disorderly-conduct-1-sorting-game.html",
     "Penal Code &mdash; Disorderly Conduct I Sorting Game",
     "First of two Chapter 42 games (Disorderly Conduct runs 26 sections, split in half) &mdash; 13 statute-section boxes, 46 subsection cards, covering disorderly conduct, riot, false alarms/reports, silent 9-1-1 calls, harassment, and stalking."),
    ("penal-disorderly-conduct-2-public-indecency-sorting-game.html",
     "Penal Code &mdash; Disorderly Conduct II &amp; Public Indecency Sorting Game",
     "Second of two Chapter 42 games, plus all of Chapter 43 &mdash; 24 statute-section boxes, 107 subsection cards, covering animal cruelty, dog/cockfighting, and firearm-discharge offenses (Ch.42), plus prostitution, promotion of prostitution, and child pornography offenses (Ch.43). Boxes default to a collapsed view given the size."),
    ("penal-weapons-sorting-game.html",
     "Penal Code &mdash; Weapons Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; all of Chapter 46, 17 statute-section boxes and 88 subsection cards, from unlawful carrying and prohibited weapons through hoax bombs, weapon-free school zones, and firearm smuggling. Boxes default to a collapsed view given the size."),
    ("penal-gambling-sorting-game.html",
     "Penal Code &mdash; Gambling Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; all of Chapter 47, 11 statute-section boxes and 23 subsection cards, covering gambling, gambling promotion, keeping a gambling place, and gambling-device possession."),
    ("penal-public-health-intoxication-fireworks-sorting-game.html",
     "Penal Code &mdash; Public Health, Intoxication &amp; Fireworks Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; 23 statute-section boxes, 71 subsection cards, covering Chapter 48 (Smoking Tobacco, Sale of Human Organs/Fetal Tissue, Prohibited Camping), Chapter 49 (Public Intoxication, DWI/BWI/FWI, Intoxication Assault/Manslaughter), and Chapter 50 (Unlawful Use of Fireworks)."),
    ("penal-organized-crime-sorting-game.html",
     "Penal Code &mdash; Organized Crime &amp; Criminal Street Gangs Sorting Game",
     "Drag-and-drop (or tap-to-select) sorting game &mdash; all of Chapter 71, 10 statute-section boxes and 28 subsection cards, covering engaging in organized criminal activity, gang membership coercion/solicitation, gang-free zones, and the renunciation defense."),
]

new_cards = ''.join(CARD_T.format(href=h, name=n, desc=d) for h, n, d in cards_data)

content = content.replace(anchor, anchor + new_cards)

after_div_count = content.count('<div')
after_closediv_count = content.count('</div>')

print("div delta:", after_div_count - before_div_count, "closediv delta:", after_closediv_count - before_closediv_count)
assert (after_div_count - before_div_count) == (after_closediv_count - before_closediv_count), "div balance mismatch!"

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html patched OK. new length:", len(content))
