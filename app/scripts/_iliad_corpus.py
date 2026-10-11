#!/usr/bin/env python3
"""
_iliad_corpus.py — the Homeric *Iliad* stylometry case (data only; the SUBSET model `sty`).

Pure single-lens 文献測定学: the Iliad as an ordered sequence of 24 books, each measured across a
small textual feature space, adjacent-book discontinuities surfaced as candidate seams, and three
competing models of composition held side by side. This module is DATA ONLY — no Iliad-specific
operator. The generic stylometry operators (`sty.work` / `sty.locus` / `sty.feature` / `sty.measure`
/ `sty.matrix` / `sty.seams` / `sty.compare` / `sty.project`) build and read it, exactly as for the
Milindapañha; only the corpus differs. app/scripts/stylometry_lab.py builds it; scripts/
gen_stylometry_iliad_ak.py writes the durable app/ontology/base3/stylometry_iliad.ak catalog.

⚠ A discontinuity is NOT an attribution. The matrix below is a DEFENSIBLE ILLUSTRATIVE table (the
Catalogue of Ships in Book II is name-dense; the Doloneia in Book X — athetised in antiquity — is
lexically unusual and simile-poor; the embassy/ransom books IX/XXIV are speech-heavy; the Shield in
XVIII is simile-rich). Measurement is EVIDENCE, not truth — see PROVENANCE. Replace with values
measured from a real tokenised edition via `io.ingest model=sty into=iliad path=<matrix.jsonl>`.
"""

WORK = "iliad"

QUESTION = "Where does one poem change its voice — and does a seam imply another hand?"
INTRO = ("The Iliad is treated as an ordered sequence of twenty-four books. Each book is measured "
         "across lexical, formulaic, narrative, and stylistic features. Adjacent-book discontinuities "
         "are surfaced as candidate seams, then compared against competing models of composition. "
         "A discontinuity is not an attribution — the laboratory preserves the distinction between "
         "measurement and interpretation.")

# provenance is mandatory: the reading of a classical Greek text depends on the edition and the
# tokenisation, so every measurement carries where it came from. Here the values are illustrative.
PROVENANCE = {
    "source_edition": "Homerus, Ilias — ed. M.L. West (Bibliotheca Teubneriana, 1998–2000)",
    "tokenization": "whitespace + elision-aware, illustrative (no real tokeniser was run)",
    "normalization": "lowercased, diacritics folded (illustrative)",
    "feature_version": "iliad-v1",
    "status": "ILLUSTRATIVE — grounded in the philology, not measured from a tokenised edition",
    "note": "Measurement is evidence, not truth. Values are placeholders for a real feature run.",
}

# the edition the (illustrative) values are 'measured' on — the witness in stylometry terms
WITNESSES = [
    ("west_teubner", "Homeri Ilias, ed. M.L. West (Teubner, 1998–2000)", "grc"),
    ("oct_monro_allen", "Homeri Opera I–II, ed. Monro & Allen (OCT, 3rd ed.)", "grc"),
]

# composition strata the hypotheses group over (a locus belongs to exactly one)
LAYERS = [
    ("il_main",      "Main narrative", "The dominant texture of the poem — the wrath and its battle books."),
    ("il_catalogue", "The Catalogue (Book II)", "The Catalogue of Ships — a distinct, name-dense register."),
    ("il_doloneia",  "The Doloneia (Book X)", "The night-raid episode, athetised in antiquity as a later insertion."),
]

# id, title, layer, attested-in (editions). 24 books in reading order.
LOCI = [
    ("il1",  "I · The Plague and the Wrath",       "il_main",      "west_teubner,oct_monro_allen"),
    ("il2",  "II · The Catalogue of Ships",        "il_catalogue", "west_teubner,oct_monro_allen"),
    ("il3",  "III · The Duel of Paris and Menelaus","il_main",     "west_teubner,oct_monro_allen"),
    ("il4",  "IV · The Oath Broken",               "il_main",      "west_teubner,oct_monro_allen"),
    ("il5",  "V · The Aristeia of Diomedes",       "il_main",      "west_teubner,oct_monro_allen"),
    ("il6",  "VI · Hector and Andromache",         "il_main",      "west_teubner,oct_monro_allen"),
    ("il7",  "VII · The Duel of Hector and Ajax",  "il_main",      "west_teubner,oct_monro_allen"),
    ("il8",  "VIII · The Tide of Battle Turns",    "il_main",      "west_teubner,oct_monro_allen"),
    ("il9",  "IX · The Embassy to Achilles",       "il_main",      "west_teubner,oct_monro_allen"),
    ("il10", "X · The Doloneia (the Night Raid)",  "il_doloneia",  "west_teubner,oct_monro_allen"),
    ("il11", "XI · The Aristeia of Agamemnon",     "il_main",      "west_teubner,oct_monro_allen"),
    ("il12", "XII · The Battle at the Wall",       "il_main",      "west_teubner,oct_monro_allen"),
    ("il13", "XIII · The Battle at the Ships",     "il_main",      "west_teubner,oct_monro_allen"),
    ("il14", "XIV · The Deception of Zeus",        "il_main",      "west_teubner,oct_monro_allen"),
    ("il15", "XV · The Achaeans Driven Back",      "il_main",      "west_teubner,oct_monro_allen"),
    ("il16", "XVI · The Aristeia of Patroclus",    "il_main",      "west_teubner,oct_monro_allen"),
    ("il17", "XVII · The Fight over Patroclus",    "il_main",      "west_teubner,oct_monro_allen"),
    ("il18", "XVIII · The Shield of Achilles",     "il_main",      "west_teubner,oct_monro_allen"),
    ("il19", "XIX · The Reconciliation",           "il_main",      "west_teubner,oct_monro_allen"),
    ("il20", "XX · The Gods Enter the War",        "il_main",      "west_teubner,oct_monro_allen"),
    ("il21", "XXI · The Battle at the River",      "il_main",      "west_teubner,oct_monro_allen"),
    ("il22", "XXII · The Death of Hector",         "il_main",      "west_teubner,oct_monro_allen"),
    ("il23", "XXIII · The Funeral Games",          "il_main",      "west_teubner,oct_monro_allen"),
    ("il24", "XXIV · The Ransom of Hector",        "il_main",      "west_teubner,oct_monro_allen"),
]

# the seven textual features (all single-lens = stylometry). id, title, desc, higher(unused hint).
FEATURES = [
    ("formulaic_density",   "Formulaic density",   "Density of repeated formulaic phrases and epithets (not a marker of age).", ""),
    ("hapax_ratio",         "Hapax ratio",         "Share of once-occurring word-types.", ""),
    ("vocabulary_richness", "Vocabulary richness", "Length-normalised type–token richness (MATTR-style).", ""),
    ("mean_clause_length",  "Mean clause length",  "Average words per clause (edition-robust; safer than sentence length in Greek).", ""),
    ("direct_speech_ratio", "Direct-speech ratio", "Share of the book given to direct speech vs narration.", ""),
    ("simile_density",      "Simile density",      "Density of extended (epic) similes.", ""),
    ("proper_name_density", "Proper-name density", "Density of personal and place names (catalogue detector).", ""),
]

# posited candidate seams (the boundaries the hypotheses argue about — NOT pre-judged winners)
SEAMS = [
    ("il_seam_catalogue",    "il1",  "I ▸ II — the entry into the name-dense Catalogue of Ships."),
    ("il_seam_doloneia_in",  "il9",  "IX ▸ X — into the Doloneia, athetised in antiquity (schol. 'inserted by Peisistratus')."),
    ("il_seam_doloneia_out", "il10", "X ▸ XI — back out of the Doloneia to the main battle narrative."),
]

# three competing models — deliberately NOT the crude single-vs-multiple-author dichotomy
HYPS = [
    ("unity", "Substantially Unified",
        "The poem is stylistically heterogeneous but does not require strong compositional "
        "stratification — the variation is within one shaping design.", "", ""),
    ("oral_layering", "Oral-Formulaic Layering",
        "Measured differences reflect oral-compositional practice, performance context, and inherited "
        "formulaic material rather than discrete authorship layers.", "", "il_catalogue,il_doloneia"),
    ("stratified", "Multiple-Strata / Editorial Growth",
        "Some sections (the Catalogue, the Doloneia) may represent later incorporation, revision, or "
        "compositional strata distinguishable from the dominant texture of the poem.",
        "il_seam_catalogue,il_seam_doloneia_in,il_seam_doloneia_out", "il_doloneia,il_catalogue"),
]

SOURCES = [
    ("wolf_1795", "Prolegomena ad Homerum", "F.A. Wolf", "1795",
        "stratified", "unity", "the founding Analyst statement"),
    ("parry_1971", "The Making of Homeric Verse", "Milman Parry (ed. A. Parry)", "1971",
        "oral_layering", "stratified", "the oral-formulaic theory"),
    ("lord_1960", "The Singer of Tales", "Albert B. Lord", "1960",
        "oral_layering", "", "oral composition in performance"),
    ("kirk_1985", "The Iliad: A Commentary, vol. I", "G.S. Kirk", "1985",
        "unity,oral_layering", "", "Cambridge commentary — a monumental design by one main poet"),
    ("danek_1988", "Studien zur Dolonie", "Georg Danek", "1988",
        "stratified", "", "on Book X (the Doloneia)"),
    ("west_2011", "The Making of the Iliad", "M.L. West", "2011",
        "stratified", "oral_layering", "analytic reconstruction; the poet 'P'"),
    ("hainsworth_1993", "The Iliad: A Commentary, vol. III (Books 9–12)", "Bryan Hainsworth", "1993",
        "unity,oral_layering", "", "on the embassy and the Doloneia"),
]

# the special-case focus for the Book-X inspection panel (sty.compare target)
FOCUS = "il10"

# ── the feature × book matrix (illustrative; grounded in the philology) ──
# order of the tuple: formulaic, hapax, vocab, clause_len, direct_speech, simile, proper_name
_M = {
    "il1":  (0.58, 0.33, 0.63, 11.5, 0.46, 0.14, 0.30),
    "il2":  (0.55, 0.47, 0.72, 10.2, 0.10, 0.08, 0.95),   # Catalogue of Ships — names
    "il3":  (0.57, 0.34, 0.64, 11.0, 0.40, 0.13, 0.42),
    "il4":  (0.60, 0.32, 0.62, 11.3, 0.30, 0.15, 0.38),
    "il5":  (0.65, 0.30, 0.60, 12.0, 0.18, 0.22, 0.52),   # Diomedes aristeia
    "il6":  (0.56, 0.35, 0.65, 11.4, 0.48, 0.18, 0.34),
    "il7":  (0.61, 0.33, 0.61, 11.6, 0.34, 0.14, 0.40),
    "il8":  (0.64, 0.31, 0.60, 12.1, 0.22, 0.16, 0.48),
    "il9":  (0.52, 0.36, 0.67, 12.6, 0.62, 0.12, 0.26),   # Embassy — speeches
    "il10": (0.44, 0.49, 0.75, 13.4, 0.30, 0.07, 0.44),   # Doloneia — lexically unusual, simile-poor
    "il11": (0.66, 0.30, 0.59, 12.2, 0.20, 0.20, 0.55),   # Agamemnon aristeia
    "il12": (0.64, 0.31, 0.60, 12.0, 0.18, 0.19, 0.47),
    "il13": (0.65, 0.30, 0.60, 12.1, 0.22, 0.18, 0.50),
    "il14": (0.58, 0.34, 0.64, 11.8, 0.42, 0.16, 0.36),   # Deception of Zeus
    "il15": (0.65, 0.31, 0.60, 12.0, 0.20, 0.19, 0.49),
    "il16": (0.62, 0.32, 0.62, 12.3, 0.30, 0.28, 0.44),   # Patroclus — simile-rich pathos
    "il17": (0.65, 0.30, 0.60, 12.0, 0.20, 0.21, 0.52),
    "il18": (0.53, 0.38, 0.74, 13.0, 0.34, 0.30, 0.30),   # Shield of Achilles — ekphrasis
    "il19": (0.55, 0.35, 0.65, 12.2, 0.55, 0.13, 0.30),   # Reconciliation — speeches
    "il20": (0.63, 0.31, 0.61, 12.1, 0.28, 0.20, 0.50),
    "il21": (0.60, 0.33, 0.63, 12.4, 0.26, 0.26, 0.42),   # Battle at the river — similes
    "il22": (0.57, 0.34, 0.64, 12.0, 0.50, 0.18, 0.40),   # Death of Hector
    "il23": (0.58, 0.36, 0.66, 11.7, 0.36, 0.15, 0.58),   # Funeral games — names
    "il24": (0.53, 0.35, 0.67, 12.8, 0.58, 0.17, 0.30),   # Ransom — speeches, pathos
}
_ORDER = [f[0] for f in FEATURES]
MATRIX = {lid: {f: v for f, v in zip(_ORDER, vals)} for lid, vals in _M.items()}
