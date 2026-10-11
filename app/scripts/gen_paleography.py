#!/usr/bin/env python3
# Generate a focused general-education-level map of paleography / old-document studies (komonjo) and its
# sister source-critical disciplines:
#   app/ontology/base3/paleography.ak
# The raw materials already exist scattered — ms:* (the handwritten book & scripts),
# epig:* (inscriptions), textcrit:* (textual criticism) — but there is no discipline
# spine tying them together. This adds:
# - auxhist the auxiliary sciences of history umbrella
# - paleo:paleography / old-document studies (komonjo): reading, dating and localising scripts
# - paleo:diplomatics / diplomatics: the critical study of charters and documents
#   - small sister nodes    chronology, sigillography, numismatics, archival science,
#                           papyrology, philology
# and cross-links the existing ms:/epig:/textcrit:/digarch:/archaeo: atoms under them.
#
# ms / epig / textcrit tops already exist — NOT re-def'd; only linked.

import os

def esc(s):
    return s.replace('"', "'")

L = [
 "# Akasha ontology — paleography / old-document studies (komonjo) and the auxiliary sciences of history.",
 "# Focused general-education-level spine over the existing ms:/epig:/textcrit: atoms.",
 "# ms (codicology) / epig (epigraphy) / textcrit already exist as tops — only linked.",
 "# General-education breadth; research depth is reserved for level-C packs. Base pack.",
 "",
 # ── umbrella: the auxiliary sciences of history ──
 'def "auxhist" "歴史補助学 — the auxiliary (source-critical) sciences of history: the disciplines that let us read, date and authenticate the documents and objects of the past."',
 "ln auxhist knowledge:branch:humanities knowledge:in_branch",
 "ln auxhist archaeo thesaurus:related",
 "ln auxhist historiography.method thesaurus:related",
]

# members of the auxiliary sciences: (id, gloss, is_new, [bridges])
# is_new=False → existing top, only link it under auxhist (no def).
MEMBERS = [
 ("paleo:paleography", "古書体学・古文書学 — the study of ancient and medieval handwriting: reading old scripts and dating and localising the hand.", True,
   ["ms","epig"]),
 ("ms", "写本学・書物学 (codicology) — the handwritten book as a physical object.", False, []),
 ("epig", "碑文学 (epigraphy) — inscriptions cut in stone, metal and other hard materials.", False, []),
 ("paleo:diplomatics", "文書学 (diplomatics) — the critical study of charters and documents: their forms, formulae and authenticity.", True,
   ["textcrit:critical_edition"]),
 ("textcrit:textual_criticism", "本文批判 (textual criticism) — reconstructing the most authentic text from its variant witnesses.", "maybe",
   []),
 ("paleo:chronology", "年代学 (chronology) — establishing the dates of documents and events, and the calendars they used.", True,
   ["archaeo:dating","hist:period:modern_era"]),
 ("paleo:sigillography", "印章学 (sigillography) — the study of seals used to authenticate documents.", True,
   ["ms:colophon"]),
 ("paleo:numismatics", "貨幣学 (numismatics) — the study of coins and currency as historical evidence.", True,
   ["archaeo"]),
 ("paleo:papyrology", "パピルス学 (papyrology) — the study of texts written on papyrus, chiefly from the ancient world.", True,
   ["epig:ostracon","ms:scroll"]),
 ("paleo:archival_science", "文書館学 (archival science) — the theory and practice of preserving and arranging archives.", True,
   ["lib:accession","digarch:digital_archive"]),
 ("paleo:philology", "文献学 (philology) — the study of language in historical written sources.", True,
   ["ling","textcrit:critical_edition"]),
]

# resolve the textcrit top: it does not exist as a bare 'textcrit' atom, so define a
# proper discipline node textcrit:textual_criticism and hang the existing textcrit:* off it.
L += ["", "# ══ members of the auxiliary sciences of history ══"]
for mid, gloss, isnew, bridges in MEMBERS:
    if isnew is True or isnew == "maybe":
        L.append(f'def "{mid}" "{esc(gloss)}"')
    L.append(f"ln {mid} auxhist sys:part_of")
    for b in bridges:
        L.append(f"ln {mid} {b} thesaurus:related")

# ── paleography: the scripts it studies ──
L += ["", "# ══ paleography — the scripts studied (existing ms: atoms) ══"]
SCRIPTS = ["majuscule","uncial","half_uncial","insular_script","carolingian_minuscule",
           "minuscule","gothic_textualis","humanist_minuscule","cursive"]
for s in SCRIPTS:
    L.append(f"ln ms:{s} paleo:paleography paleo:script_studied")
# rough historical development of the Latin book hand
CHAIN = ["uncial","half_uncial","insular_script","carolingian_minuscule","gothic_textualis","humanist_minuscule"]
for a, b in zip(CHAIN, CHAIN[1:]):
    L.append(f"ln ms:{a} ms:{b} chrono:before")

# existing ms:/epig: technique atoms that are paleography's tools
L += ["", "# ── the paleographer's toolkit (existing atoms) ──"]
for a in ["ms:abbreviation","ms:tironian_notes","ms:ligature","ms:diplomatic_transcription",
          "ms:palimpsest","ms:watermark","ms:scriptorium","ms:marginalia","ms:gloss","ms:colophon"]:
    L.append(f"ln {a} paleo:paleography thesaurus:related")
for a in ["epig:leiden_conventions","epig:lacuna","epig:squeeze","epig:rubbing","epig:formula"]:
    L.append(f"ln {a} paleo:paleography thesaurus:related")

# ── new paleography concepts that fill genuine general-education gaps ──────────────────────
PALEO_CONCEPTS = [
 ("ductus", "The number, order and direction of the strokes that form a letter — a key to identifying a hand."),
 ("letterform", "The shape of a written character, which changes by period, region and scribe (litterae)."),
 ("scribal_hand", "The individual handwriting of one scribe, by which a text can be attributed and dated."),
 ("script_dating", "Assigning a date to a document from the style of its script (palaeographic dating)."),
 ("localisation", "Assigning a place of origin to a manuscript from its script, decoration and materials."),
 ("abbreviation_system", "The systems of contraction and suspension that let scribes write faster and save costly parchment."),
 ("transcription_convention", "Agreed rules for rendering a manuscript or inscription in modern type — diplomatic (as-written) or normalised."),
 ("forgery_detection", "Judging whether a document is authentic from its script, formulae, materials and internal consistency."),
 ("provenance", "The traced history of a document's ownership and custody, itself evidence for its authenticity."),
 ("hand_shift", "A change of scribe within one manuscript, detected where the hand changes."),
]
L += ["", "# ══ paleography concepts ══"]
for slug, gloss in PALEO_CONCEPTS:
    cid = f"paleo:concept:{slug}"
    L.append(f'def "{cid}" "{esc(gloss)}"')
    L.append(f"ln {cid} paleo:paleography sys:part_of")
# a few precise bridges from the new concepts to existing atoms
L += [
 "ln paleo:concept:abbreviation_system ms:abbreviation thesaurus:related",
 "ln paleo:concept:transcription_convention ms:diplomatic_transcription thesaurus:related",
 "ln paleo:concept:transcription_convention epig:leiden_conventions thesaurus:related",
 "ln paleo:concept:forgery_detection paleo:diplomatics thesaurus:related",
 "ln paleo:concept:script_dating paleo:chronology thesaurus:related",
 "ln paleo:concept:scribal_hand ms:scriptorium thesaurus:related",
]

# ── diplomatics: the parts of a charter ───────────────────────────
DIPLO = [
 ("protocol", "The opening formulae of a charter: invocation, address, greeting."),
 ("text_body", "The central part of a charter (the 'text'), stating the act itself."),
 ("eschatocol", "The closing formulae of a charter: dating clause, subscriptions, seal."),
 ("chancery", "The office that drafted and issued a ruler's or bishop's documents, with its own house style."),
 ("formula", "A set, repeated wording whose form helps date and authenticate a document."),
 ("authentication", "The means — seal, sign, subscription — by which a document was made valid."),
]
L += ["", "# ══ diplomatics — the anatomy of a charter ══"]
for slug, gloss in DIPLO:
    cid = f"paleo:diplomatics:{slug}"
    L.append(f'def "{cid}" "{esc(gloss)}"')
    L.append(f"ln {cid} paleo:diplomatics sys:part_of")
L += ["ln paleo:diplomatics:formula epig:formula thesaurus:related",
      "ln paleo:diplomatics:authentication paleo:sigillography thesaurus:related"]

# ── traditions: paleography is not only Latin (inclusive, light) ─────────────
TRAD = [
 ("latin", "The Latin book hands of the Western Middle Ages (uncial → Carolingian → Gothic → humanist)."),
 ("greek", "Greek scripts, from ancient majuscule to Byzantine minuscule."),
 ("east_asian", "East Asian document studies (Japanese 古文書学 komonjogaku): cursive kanji and kuzushiji hands."),
 ("arabic", "The Arabic scripts (kufic, naskh…) of manuscripts and documents."),
]
L += ["", "# ══ script traditions (inclusive) ══"]
for slug, gloss in TRAD:
    tid = f"paleo:tradition:{slug}"
    L.append(f'def "{tid}" "{esc(gloss)}"')
    L.append(f"ln {tid} paleo:paleography sys:part_of")
L += ["ln paleo:tradition:latin ms:carolingian_minuscule thesaurus:related",
      "ln paleo:tradition:greek epig:inscription thesaurus:related"]

# ── two concrete anchors (scribes) — keep pinpoint ───────────────────────────
L += ["", "# ══ two concrete anchors ══",
 'def "person:alcuin" "Alcuin of York (c.735-804), scholar at Charlemagne\'s court associated with the reform that spread the clear Carolingian minuscule."',
 "ln person:alcuin person:figure thesaurus:related",
 "ln person:alcuin ms:carolingian_minuscule thesaurus:related",
 "ln person:alcuin paleo:paleography thesaurus:related",
 "ln person:alcuin ms:scriptorium thesaurus:related",
 'def "person:eadfrith" "Eadfrith of Lindisfarne (d.721), the bishop traditionally named as scribe and artist of the Lindisfarne Gospels, a masterpiece of the insular script."',
 "ln person:eadfrith person:figure thesaurus:related",
 "ln person:eadfrith ms:insular_script thesaurus:related",
 "ln person:eadfrith ms:illuminated_manuscript thesaurus:related",
]

path = "app/ontology/base3/paleography.ak"
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
ndef = sum(1 for l in L if l.startswith("def "))
nln = sum(1 for l in L if l.startswith("ln "))
print(f"{path}: def={ndef} ln={nln} ({len(L)} lines)")
