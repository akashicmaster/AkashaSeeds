#!/usr/bin/env python3
# Three deliverables:
# app/ontology/base3/medicine_map.ak — general-education medicine map (organize the rich med:* content)
# app/ontology/base3/archaeology_spine.ak — archaeology subdiscipline spine (archaeo:branch:*)
#   app/ontology/base3/c_level_frames.ak    — level-C (master's/PhD) frames for EVERY domain
# The medicine content and archaeology atoms already exist; these add the organizing
# spine and cross-link the existing atoms. The C frames DEFINE the research-depth scope per
# domain without implementing it (per the A/B/C tier policy) — nutrition's C frame is
# flagged first-to-implement (concrete menus + food history + food folklore).

import os
def esc(s): return s.replace('"', "'")
def emit(lines, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    nd = sum(1 for l in lines if l.startswith("def "))
    nl = sum(1 for l in lines if l.startswith("ln "))
    print(f"{path}: def={nd} ln={nl} ({len(lines)} lines)")

# ═════════════════════════════════════════════════════════════════════════════
# MEDICINE — general-education map organizing the existing med:* atoms
# ═════════════════════════════════════════════════════════════════════════════
M = [
 "# Akasha ontology — medicine: the general-education-level map.",
 "# The content already exists richly (med:basic/clinical/specialty/evidence/drug/",
 "# pharma/condition/system) but had no spine tying it to med:medicine. This adds the",
 "# divisions and cross-links the existing atoms. med:medicine already exists — only linked.",
 "# General-education breadth; research depth reserved for level-C. Base pack.",
 "",
 "ln med:medicine knowledge:branch:applied_science knowledge:in_branch",
 "ln med:medicine bio:biology thesaurus:related",
 "ln med:medicine knowledge:cognitive_science thesaurus:related",
]
# (division_slug, gloss, [existing atoms], [bridges])
MED_DIV = [
 ("basic_science", "基礎医学 — the sciences underlying medicine: how the body is built and works, and how disease arises.",
   ["med:basic:anatomy","med:basic:physiology","med:basic:pathology","med:basic:pharmacology","med:basic:immunology","med:basic:epidemiology","med:basic:preventive_medicine","med:basic:public_health"],
   ["bio:branch:physiology","bio:branch:biochemistry"]),
 ("clinical_practice", "臨床医学 — the work of caring for patients: history, examination, diagnosis and treatment.",
   ["med:clinical:history_taking","med:clinical:physical_examination","med:clinical:vital_signs","med:clinical:diagnosis","med:clinical:differential_diagnosis","med:clinical:clinical_reasoning","med:clinical:treatment","med:clinical:prognosis","med:clinical:prescription","med:clinical:referral","med:clinical:informed_consent"],
   []),
 ("specialties", "診療科 — the branches of clinical medicine by body system, age or method.",
   ["med:specialty:internal_medicine","med:specialty:surgery","med:specialty:pediatrics","med:specialty:obstetrics_gynecology","med:specialty:psychiatry","med:specialty:neurology","med:specialty:cardiology","med:specialty:oncology","med:specialty:radiology","med:specialty:pathology","med:specialty:anesthesiology","med:specialty:emergency_medicine","med:specialty:family_medicine","med:specialty:geriatrics","med:specialty:public_health_medicine"],
   []),
 ("therapeutics", "治療学・薬理 — how disease is treated, above all with drugs.",
   ["med:drug:aspirin","med:drug:nsaid","med:drug:statin","med:drug:beta_blocker","med:drug:ssri","med:drug:l_dopa","med:pharma:pharmacodynamics","med:pharma:pharmacokinetics","med:pharma:agonist","med:pharma:antagonist"],
   ["chem:branch:biochemistry"]),
 ("evidence", "根拠に基づく医療 (EBM) — grounding practice in the best current research.",
   ["med:evidence:evidence_based_medicine","med:evidence:randomized_controlled_trial","med:evidence:systematic_review","med:evidence:meta_analysis","med:evidence:cohort_study","med:evidence:clinical_guideline","med:evidence:biostatistics","med:evidence:placebo"],
   ["math:statistics","dh:lens:statistical_inference"]),
 ("disease", "疾病学 — the diseases medicine confronts.",
   ["med:condition:diabetes","med:condition:atherosclerosis","med:condition:osteoporosis","med:condition:anemia","med:condition:scurvy","med:condition:kwashiorkor","med:condition:protein_deficiency","med:condition:night_blindness","med:condition:famine"],
   ["nutrisci"]),
 ("traditions", "医学の諸伝統 — the world's systems of medicine, Western and other.",
   ["med:system:western_medicine","med:system:tcm","med:system:kampo","med:system:ayurveda","med:system:medical_astrology","med:concept:hippocratic_oath","med:concept:dosha","med:concept:qi_blood_fluid"],
   ["tcm:action:clear_heat","anthro:concept:magic_religion"]),
 ("allied_health", "看護・ケア・生体医工 — the professions and technologies allied to medicine.",
   [],
   ["nursing:holistic_care","care:care_plan","bme:artificial_organ","eng:branch:biomedical"]),
]
M += ["", "# ══ divisions of medicine ══"]
for slug, gloss, kids, bridges in MED_DIV:
    d = f"med:division:{slug}"
    M.append(f'def "{d}" "{esc(gloss)}"')
    M.append(f"ln {d} med:medicine sys:part_of")
    for k in kids: M.append(f"ln {k} {d} sys:part_of")
    for b in bridges: M.append(f"ln {d} {b} thesaurus:related")
# cross bridges
M += ["ln med:specialty:psychiatry psy:field:clinical thesaurus:related",
      "ln med:specialty:neurology neuro thesaurus:related",
      "ln med:basic:anatomy bio:branch:physiology thesaurus:related",
      "ln med:basic:epidemiology dh:family:quantitative thesaurus:related"]
# a couple of founders
M += ["", "# ══ founders (new) ══",
 'def "person:hippocrates" "Greek physician (c.460-370 BCE) held as the father of Western medicine; the ethic of the Hippocratic Oath bears his name."',
 "ln person:hippocrates person:figure thesaurus:related",
 "ln person:hippocrates person:field:medicine person:worked_in",
 "ln person:hippocrates med:medicine person:worked_in",
 "ln person:hippocrates med:concept:hippocratic_oath thesaurus:related",
 "ln person:hippocrates hist:period:classical_antiquity person:active_in",
 'def "person:florence_nightingale" "English reformer (1820-1910), founder of modern nursing and a pioneer of medical statistics and hospital sanitation."',
 "ln person:florence_nightingale person:figure thesaurus:related",
 "ln person:florence_nightingale person:field:medicine person:worked_in",
 "ln person:florence_nightingale med:division:allied_health thesaurus:related",
 "ln person:florence_nightingale med:evidence:biostatistics thesaurus:related",
 "ln person:florence_nightingale hist:period:industrial_revolution person:active_in",
]
emit(M, "app/ontology/base3/medicine_map.ak")

# ═════════════════════════════════════════════════════════════════════════════
# ARCHAEOLOGY — subdiscipline spine (archaeo:branch:*)
# ═════════════════════════════════════════════════════════════════════════════
A = [
 "# Akasha ontology — archaeology: the subdiscipline spine.",
 "# archaeo:* atoms exist (cultures, dating methods, field concepts) but had no branch",
 "# spine. This adds archaeo:branch:* and cross-links the existing atoms + paleography/epigraphy.",
 "# archaeo (top) already exists — only linked. general-education breadth; research depth to level-C.",
 "",
 "ln archaeo knowledge:branch:humanities knowledge:in_branch",
 "ln archaeo auxhist thesaurus:related",
 "ln archaeo anthro:field:archaeological thesaurus:related",
 "ln archaeo hist:period:modern_era thesaurus:related",
]
#
ARCH_BR = [
 ("prehistoric", "先史考古学 — the human past before written records, from the Palaeolithic to the first states.",
   ["archaeo:culture:clovis","archaeo:culture:natufian","archaeo:culture:jomon_culture","archaeo:culture:yangshao","archaeo:culture:cucuteni_trypillia","archaeo:culture:harappan"],
   ["hist:period:classical_antiquity"]),
 ("protohistoric_classical", "原史・古典考古学 — the Bronze and Iron Age civilisations and the Greek and Roman world.",
   ["archaeo:culture:minoan","archaeo:culture:la_tene","archaeo:culture:olmec"],
   ["epig:inscription"]),
 ("near_eastern", "オリエント考古学 — the ancient Near East: Mesopotamia, the Levant, Anatolia and Persia.",
   [], ["epig:cuneiform"]),
 ("egyptology", "エジプト学 — the archaeology and philology of ancient Egypt.",
   [], ["epig:hieroglyph"]),
 ("historical_archaeology", "歴史考古学 — the material past of literate, historically-documented societies.",
   [], ["paleo:diplomatics","hist:period:modern_era"]),
 ("industrial_archaeology", "産業考古学 — the physical remains of the industrial age.",
   [], ["hist:period:industrial_revolution","matsci"]),
 ("underwater_archaeology", "水中考古学 — shipwrecks and submerged sites.",
   [], ["earthsci:branch:oceanography"]),
 ("bioarchaeology", "生物考古学 — human remains: diet, disease, ancestry and lifeways from bones.",
   [], ["bio:branch:evolution","med:basic:pathology"]),
 ("environmental_archaeology", "環境考古学 — reconstructing past climates, landscapes, plants and animals.",
   [], ["ecol","earthsci:branch:paleontology"]),
 ("archaeological_science", "考古科学 — the laboratory methods: dating, materials analysis and remote sensing.",
   ["archaeo:dating:absolute_dating","archaeo:dating:relative_dating","archaeo:dating:radiocarbon_dating_m","archaeo:dating:dendrochronology_m","archaeo:dating:potassium_argon","archaeo:dating:obsidian_hydration","archaeo:dating:thermoluminescence","archaeo:dating:uranium_series","archaeo:dating:varve_dating"],
   ["chem:branch:analytical_chemistry","dh:family:spatial"]),
]
A += ["", "# ══ branches of archaeology ══"]
for slug, gloss, kids, bridges in ARCH_BR:
    b = f"archaeo:branch:{slug}"
    A.append(f'def "{b}" "{esc(gloss)}"')
    A.append(f"ln {b} archaeo sys:part_of")
    for k in kids: A.append(f"ln {k} {b} sys:part_of")
    for br in bridges: A.append(f"ln {b} {br} thesaurus:related")
# method group — organize the existing field concepts
A += ["", "# ══ field method (existing archaeo: concepts) ══",
 'def "archaeo:method" "発掘・記録の方法 — how archaeology recovers and records material evidence."',
 "ln archaeo:method archaeo sys:part_of"]
for a in ["archaeo:archaeological_site","archaeo:artifact","archaeo:context","archaeo:cultural_layer","archaeo:culture","archaeo:dating"]:
    A.append(f"ln {a} archaeo:method sys:part_of")
A += ["ln archaeo:method paleo:paleography thesaurus:related",
      "ln archaeo:method dh:family:digitization_3d thesaurus:related",
      "ln archaeo:culture anthro:concept:material_culture thesaurus:related"]
emit(A, "app/ontology/base3/archaeology_spine.ak")

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL-C FRAMES — one research-depth slot per specialist domain (defined, not built)
# ═════════════════════════════════════════════════════════════════════════════
C = [
 "# Akasha ontology — Level-C frames.",
 "# The A/B/C tier policy: A = light, all editions; B = broad-but-shallow general-education (the maps",
 "# built across this work, Thesaurus); C = pinpoint, exhaustive research depth (master's/",
 "# PhD), a FUTURE opt-in pack per domain. This file only DEFINES each C frame's scope and",
 "# anchors it to the domain's B-tier spine — it loads NO C content. Building a C pack means",
 "# filling in its frame. nutrition:c is flagged first-to-implement. Base pack (frames only).",
 "",
 'def "c" "レベルC — the research-depth (master\'s/PhD) layer of the ontology. Each c:* frame defines the deep-dive scope for one domain; the content is a future opt-in pack, not loaded here."',
 "ln c knowledge thesaurus:related",
 "ln c crosscut:scale thesaurus:related",
 'def "c:priority:first" "The C frame slated to be implemented first."',
 "ln c:priority:first c sys:part_of",
]
# (frame_slug, scope gloss, [spine anchors it deepens])
FRAMES = [
 ("nutrition", "栄養・食のC — concrete recipe/menu deep-dive (per-dish composition, technique parameters, regional variants), food history (culinary_history), and food folklore/ethnology (foodways) refined to research depth. FIRST to implement.",
   ["nutrisci","foodsci","foodstud","foodstud:culinary_history","foodstud:food_folklore"]),
 ("medicine", "医学のC — full nosology (ICD/MeSH), pharmacology at molecular depth, clinical guidelines by specialty, and the primary-literature evidence base.",
   ["med:medicine"]),
 ("biology", "生物学のC — the NCBI-scale taxonomy of species, molecular pathways, and the genomics literature.",
   ["bio:biology"]),
 ("archaeology", "考古学のC — the Pleiades-scale gazetteer of sites, excavation reports, typologies and absolute-dating series.",
   ["archaeo"]),
 ("literature", "文学のC — full public-domain text corpora (Gutenberg-scale), critical editions, and the scholarship on each work.",
   ["lit:movement","epic:epic"]),
 ("history", "歴史学のC — the primary-source record: charters, chronicles, archives, and the historiographical debates.",
   ["hist:period","auxhist"]),
 ("physics", "物理学のC — the mathematical formalism (Lagrangian/field theory), derivations, and the experimental frontier.",
   ["phys:physics"]),
 ("chemistry", "化学のC — reaction mechanisms, spectroscopic databases, and the synthesis literature.",
   ["chem:chemistry"]),
 ("earth_science", "地球科学のC — regional geology, the stratigraphic record, and quantitative climate modelling.",
   ["earthsci:earth_science"]),
 ("astronomy", "天文学のC — survey catalogues (stars, galaxies, exoplanets) and the astrophysics literature.",
   ["astro:astronomy"]),
 ("mathematics", "数学のC — formal proofs, the research areas, and the theorem-dependency structure.",
   ["math"]),
 ("computer_science", "情報科学のC — algorithms with complexity proofs, systems internals, and the ML/AI research frontier.",
   ["cs"]),
 ("engineering", "工学のC — design codes and standards, quantitative analysis, and per-branch handbooks.",
   ["eng:engineering"]),
 ("economics", "経済学のC — formal models, econometric methods, and the empirical/theoretical literature.",
   ["econ"]),
 ("sociology", "社会学のC — social theory in depth, quantitative and qualitative methods, and empirical studies.",
   ["socio"]),
 ("political_science", "政治学のC — formal theory, comparative datasets, and the IR/political-economy literature.",
   ["polisci:political_science"]),
 ("law", "法学のC — statutes, case law, doctrine and comparative-law scholarship.",
   ["law:law","law:branch:constitutional_law"]),
 ("management", "経営学のC — strategy frameworks, quantitative finance, and the management-science literature.",
   ["mgmt:management"]),
 ("psychology", "心理学のC — measurement (psychometrics), experimental paradigms, and the empirical literature by subfield.",
   ["psy"]),
 ("linguistics", "言語学のC — formal grammars, typological databases, corpora and computational models.",
   ["ling"]),
 ("semiotics", "記号論のC — the primary theorists in depth and applied sign-analysis across media.",
   ["semio:semiotics"]),
 ("anthropology", "人類学のC — ethnographic monographs, kinship formalisms, and theory in depth.",
   ["anthro:anthropology"]),
 ("folklore", "民俗学のC — the ATU/motif indices in full, regional traditions, and fieldwork archives.",
   ["folk:folklore"]),
 ("paleography", "古文書学のC — script catalogues, manuscript descriptions, diplomatic editions and dating.",
   ["paleo:paleography"]),
 ("philosophy", "哲学のC — the primary texts, the argument structure, and the commentary tradition.",
   ["phil:philosophy"]),
 ("religion", "宗教学のC — scriptures, sects and doctrine, sacred sites and the comparative literature.",
   ["religion:religion"]),
 ("art", "芸術学のC — the catalogue of works and artists, techniques, and art-historical scholarship.",
   ["art:movement"]),
 ("music", "音楽学のC — scores and theory, the repertoire, and musicological analysis.",
   ["music:period"]),
 ("digital_humanities", "デジタル人文学のC — method implementations, tool pipelines, and reproducible analyses over the corpora.",
   ["dh"]),
 ("world_geography", "世界地理のC — every country and city in depth, classical polities and geographic objects, and the route networks (the world/geo C backlog).",
   ["hist:period","admin:city"]),
]
C += ["", "# ══ per-domain C frames (scope defined; content not loaded) ══"]
for slug, gloss, anchors in FRAMES:
    fid = f"c:{slug}"
    C.append(f'def "{fid}" "{esc(gloss)}"')
    C.append(f"ln {fid} c sys:part_of")
    for a in anchors:
        if a: C.append(f"ln {fid} {a} c:deepens")
# nutrition is first
C += ["", "# nutrition:c is the first C frame to be implemented",
      "ln c:nutrition c:priority:first thesaurus:related"]
emit(C, "app/ontology/base3/c_level_frames.ak")
