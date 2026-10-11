#!/usr/bin/env python3
# Generate a broad general-education-level linguistics map:
#   app/ontology/base3/linguistics_map.ak
# Linguistics matters especially to Akasha, which is itself a text engine (Weaver
# decomposes words; the tensor layer learns distributional meaning). The core ling:*
# concepts already exist (split across base3/linguistics.ak + world/ling.ak) but are
# FLAT — no subfield spine. This adds:
#   - ling:field:*        the levels of analysis + the branch/interface fields
# - ling:concept:* general-education gaps (POS, inflection, tense/aspect/mood, typology,
#                         writing systems, pidgin/creole, NLP terms…)
#   - person:*            the founding linguists (Panini, Saussure, Chomsky, …)
#   - an Akasha bridge    linking distributional semantics / NLP to Akasha's own
#                         text mechanism (ai:embedding, ai:akasha_pattern)
# and cross-links the existing ling:* atoms under the right level.
#
# ling (top) already exists — NOT re-def'd; existing ling:* atoms only linked.

import os

def esc(s):
    return s.replace('"', "'")

L = [
 "# Akasha ontology — linguistics: a broad general-education-level map.",
 "# Levels of analysis + branch fields + founders + an Akasha text-engine bridge,",
 "# over the existing (flat) ling:* atoms. ling (top) already exists — only linked.",
 "# General-education breadth; research depth is reserved for level-C packs. Base pack.",
 "",
 "ln ling knowledge:branch:humanities knowledge:in_branch",
 "ln ling knowledge:branch:social_science thesaurus:related",
 "ln ling knowledge:cognitive_science thesaurus:related",
]

# ── the levels of analysis (structural core), sound → meaning ────────────────
#
LEVELS = [
 ("phonetics", "音声学 — the physical sounds of speech: how they are produced, transmitted and heard.",
   ["ling:phonetics"]),
 ("phonology", "音韻論 — the sound SYSTEM of a language: which contrasts carry meaning.",
   ["ling:phonology","ling:phoneme"]),
 ("morphology", "形態論 — the internal structure of words, built from morphemes.",
   ["ling:morphology","ling:morpheme","ling:root_word","ling:word"]),
 ("syntax", "統語論 — how words combine into phrases and sentences.",
   ["ling:syntax","ling:sentence","ling:grammar","ling:recursion","ling:universal_grammar","ling:structure"]),
 ("semantics", "意味論 — literal meaning: of words, and of how they combine.",
   ["ling:semantics","ling:meaning","ling:lexicon","ling:reference","ling:polysemy","ling:metaphor","ling:symbolic_meaning","ling:signified","ling:signifier","ling:sign"]),
 ("pragmatics", "語用論 — meaning in use: how context and intent shape what is meant.",
   ["ling:pragmatics","ling:deixis","ling:speech_act","ling:implication","ling:context","ling:utterance","ling:reference"]),
 ("discourse", "談話分析 — language above the sentence: conversation, narrative and text.",
   ["ling:narrative_discourse","ling:dialogue","ling:rhetoric","ling:register","ling:code"]),
]
L += ["", "# ══ levels of analysis (structural core) ══",
      'def "ling:field:structural" "The structural core of linguistics — the levels of analysis from sound to meaning (理論言語学の中核)."',
      "ln ling:field:structural ling sys:part_of"]
prev = None
for slug, gloss, kids in LEVELS:
    fid = f"ling:field:{slug}"
    L.append(f'def "{fid}" "{esc(gloss)}"')
    L.append(f"ln {fid} ling:field:structural sys:part_of")
    for k in kids:
        L.append(f"ln {k} {fid} sys:part_of")
    if prev:
        # the analytic ladder: each level builds on the one below
        L.append(f"ln {prev} {fid} ling:feeds_into")
    prev = fid

# ── the branch / interface fields ───────────────────────────────────────────
BRANCHES = [
 ("historical", "歴史言語学 — how languages change over time and how they are related.",
   ["ling:historical_linguistics","ling:language_change","ling:language_family","ling:etymology"], ["crosscut:evolution"]),
 ("sociolinguistics", "社会言語学 — language in society: dialect, register, variation, bilingualism.",
   ["ling:sociolinguistics","ling:dialect","ling:register","ling:bilingualism"], ["socio:culture"]),
 ("psycholinguistics", "心理言語学 — how language is produced, understood and acquired in the mind.",
   ["ling:psycholinguistics"], ["psy:field:cognitive","knowledge:cognitive_science"]),
 ("neurolinguistics", "神経言語学 — how the brain represents and processes language.",
   [], ["neuro:cognitive_neuroscience","neuro:cerebral_cortex"]),
 ("computational", "計算言語学 — modelling and processing language by computer (NLP).",
   ["ling:computational_linguistics"], ["cs","ai:embedding","crosscut:information"]),
 ("applied", "応用言語学 — language teaching, translation, lexicography and policy.",
   [], ["edupsy:learning_theory","lib:indexing"]),
 ("typology", "言語類型論 — comparing the structures of the world's languages.",
   [], ["ling:language_family"]),
 ("semiotics", "記号論 — signs and meaning in general, of which language is one system.",
   ["ling:sign","ling:signifier","ling:signified","ling:symbolic_meaning"], ["crosscut:information"]),
 ("pragmatics_field", "語用・談話研究 — the study of language in context and interaction.",
   ["ling:speech_act","ling:dialogue"], ["ling:field:pragmatics"]),
]
L += ["", "# ══ branch / interface fields ══"]
for slug, gloss, kids, bridges in BRANCHES:
    fid = f"ling:field:{slug}"
    L.append(f'def "{fid}" "{esc(gloss)}"')
    L.append(f"ln {fid} ling sys:part_of")
    for k in kids:
        L.append(f"ln {k} {fid} sys:part_of")
    for b in bridges:
        L.append(f"ln {fid} {b} thesaurus:related")

# ── general-education-level concepts filling the gaps (new) ───────────────────────────────
CONCEPTS = [
 # (slug, gloss, field, [bridges])
 ("allophone", "One of the several actual sounds that realise a single phoneme without changing meaning.", "phonology", ["ling:phoneme"]),
 ("prosody", "The rhythm, stress and intonation of speech, which carry meaning of their own.", "phonology", []),
 ("inflection", "A change in a word's form to mark grammar (tense, number, case) without making a new word.", "morphology", ["ling:morpheme"]),
 ("derivation", "Making a new word from another by adding an affix (happy → happiness).", "morphology", ["ling:morpheme"]),
 ("part_of_speech", "The grammatical class of a word: noun, verb, adjective and so on.", "syntax", ["ling:word"]),
 ("lexeme", "An abstract vocabulary unit — the family of forms 'run, runs, ran, running' share.", "morphology", ["ling:lexicon"]),
 ("tense_aspect_mood", "How language marks time, the flow of an event, and the speaker's stance (real, wished, commanded).", "morphology", ["ling:grammar"]),
 ("grammatical_case", "The marking of a noun's role in a sentence (subject, object, possessor).", "syntax", []),
 ("agreement", "When one word's form must match another's (the verb agreeing with its subject).", "syntax", []),
 ("phrase_clause", "The units between word and sentence: the phrase, and the clause with its own verb.", "syntax", ["ling:sentence"]),
 ("ambiguity", "When a form has more than one possible meaning or structure.", "semantics", ["ling:polysemy"]),
 ("connotation_denotation", "A word's plain reference (denotation) versus its felt associations (connotation).", "semantics", ["ling:meaning"]),
 ("grammaticalization", "How ordinary words erode over time into grammatical markers.", "historical", ["ling:language_change"]),
 ("sound_change", "The regular, law-like shifts in pronunciation over time (e.g. Grimm's law).", "historical", ["ling:phonology"]),
 ("language_acquisition", "How children acquire a first language, and how we learn later ones.", "psycholinguistics", ["devpsy:language_acquisition"]),
 ("linguistic_relativity", "The idea that the language one speaks shapes how one thinks (Sapir-Whorf).", "sociolinguistics", ["socio:culture"]),
 ("pidgin_creole", "A makeshift contact language (pidgin) and the full native language it can become (creole).", "sociolinguistics", ["ling:dialect"]),
 ("linguistic_typology_classes", "Types by word-building: isolating, agglutinative, fusional, polysynthetic.", "typology", []),
 ("writing_system", "How languages are written: logographic, syllabic, alphabetic and mixed.", "applied", ["epig:inscription","ms:script"]),
 ("langue_parole", "Saussure's split: the shared language system (langue) versus individual speech (parole).", "semiotics", ["ling:sign"]),
 ("competence_performance", "Chomsky's split: tacit knowledge of a language versus its actual use.", "psycholinguistics", ["ling:universal_grammar"]),
 ("corpus", "A large, structured body of real texts, the evidence base of modern linguistics.", "computational", ["ai:embedding"]),
 ("tokenization", "Splitting text into words or sub-word units — the first step of language processing.", "computational", ["ling:word"]),
 ("parsing", "Analysing a sentence into its grammatical structure automatically.", "computational", ["ling:syntax"]),
]
L += ["", "# ══ general-education-level concepts (new) ══"]
for slug, gloss, field, bridges in CONCEPTS:
    cid = f"ling:concept:{slug}"
    L.append(f'def "{cid}" "{esc(gloss)}"')
    L.append(f"ln {cid} ling:field:{field} sys:part_of")
    for b in bridges:
        L.append(f"ln {cid} {b} thesaurus:related")

# ── founders (person:*) ─────────────────────────────────────────────────────
# (slug, gloss, hist_period, [bridges])
PEOPLE = [
 ("panini", "Ancient Indian grammarian (c.5th-4th c. BCE) whose formal grammar of Sanskrit is the first great linguistic analysis.", "classical_antiquity",
   ["ling:morphology","ling:grammar"]),
 ("jacob_grimm", "Philologist who, with the comparative method, formulated the sound law (Grimm's law) of the Germanic consonant shift.", "industrial_revolution",
   ["ling:concept:sound_change","ling:historical_linguistics"]),
 ("ferdinand_de_saussure", "Founder of structural linguistics; the arbitrary sign, langue vs parole, and language as a system of differences.", "modern_era",
   ["ling:sign","ling:concept:langue_parole","ling:field:semiotics"]),
 ("roman_jakobson", "Structuralist who mapped the functions of language and advanced phonology and poetics.", "modern_era",
   ["ling:phonology","ling:field:discourse"]),
 ("edward_sapir", "Anthropological linguist central to the idea that language and culture shape thought.", "modern_era",
   ["ling:concept:linguistic_relativity"]),
 ("noam_chomsky", "Founder of generative grammar; universal grammar and the competence/performance distinction transformed the field.", "modern_era",
   ["ling:universal_grammar","ling:concept:competence_performance","ling:syntax"]),
]
L += ["", "# ══ founders (person:*) ══"]
for slug, gloss, period, bridges in PEOPLE:
    pid = f"person:{slug}"
    L.append(f'def "{pid}" "{esc(gloss)}"')
    L.append(f"ln {pid} person:figure thesaurus:related")
    L.append(f"ln {pid} person:field:linguistics_scholarship person:worked_in")
    L.append(f"ln {pid} hist:period:{period} person:active_in")
    for b in bridges:
        L.append(f"ln {pid} {b} thesaurus:related")

# ── the Akasha bridge: linguistics ↔ Akasha's own text engine ────────────────
# Akasha IS a text engine: Weaver decomposes utterances into proto-words/morphemes,
# and the tensor layer learns meaning distributionally (Firth: 'you shall know a word
# by the company it keeps') — exactly PPMI co-occurrence. Make that lineage explicit.
L += ["", "# ══ the Akasha bridge — linguistics ↔ Akasha's text engine ══",
 'def "ling:concept:distributional_semantics" "Meaning learned from the company a word keeps (Firth): words used in similar contexts have similar meanings — the principle behind word embeddings, and behind Akasha\'s own learned semantic layer."',
 "ln ling:concept:distributional_semantics ling:field:semantics sys:part_of",
 "ln ling:concept:distributional_semantics ling:field:computational thesaurus:related",
 "ln ling:concept:distributional_semantics ai:embedding thesaurus:related",
 "ln ling:concept:distributional_semantics crosscut:information thesaurus:related",
 'def "ling:concept:lexical_decomposition" "Breaking an utterance into its smallest meaning-bearing units — the linguistic counterpart of Akasha\'s Weaver, which decomposes text into proto-words and component sets."',
 "ln ling:concept:lexical_decomposition ling:field:morphology sys:part_of",
 "ln ling:concept:lexical_decomposition ling:morpheme thesaurus:related",
 "ln ling:concept:lexical_decomposition ai:akasha_pattern thesaurus:related",
 "ln ling:field:computational ai:akasha_pattern thesaurus:related",
]

path = "app/ontology/base3/linguistics_map.ak"
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
ndef = sum(1 for l in L if l.startswith("def "))
nln = sum(1 for l in L if l.startswith("ln "))
print(f"{path}: def={ndef} ln={nln} ({len(L)} lines)")
