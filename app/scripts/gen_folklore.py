#!/usr/bin/env python3
# Focused general-education-level map of folklore studies / folkloristics:
#   app/ontology/base3/folklore.ak
# The adjacent field to cultural anthropology. Its materials already exist richly —
# oral:* (23 oral-tradition genres & tools), tale:* (276 folktales: Aesop, La Fontaine,
# Panchatantra, Jataka, Grimm, China, Nasreddin, Japan…), myth:* (388) — but there was
# no discipline namespace. This adds folk:* : the genres, the customary/material
# folklore, the theory/method, its founders, and the Japanese folklore-studies tradition, cross-linking
# the existing atoms. person:jacob_grimm already exists — only linked, not re-def'd.

import os

def esc(s):
    return s.replace('"', "'")

L = [
 "# Akasha ontology — folklore studies / folkloristics.",
 "# The field adjacent to cultural anthropology. Its materials existed scattered —",
 "# oral:* (genres & tools of oral tradition), tale:* (the world's folktales), myth:* —",
 "# but had no discipline spine. This adds folk:* and cross-links them. general-education breadth; research",
 "# depth reserved for level-C packs. Base pack.",
 "",
 'def "folk:folklore" "民俗学 — the study of the traditional culture of ordinary people: their tales, songs, customs, beliefs and crafts, and how these pass by word of mouth and imitation."',
 "ln folk:folklore knowledge:branch:humanities knowledge:in_branch",
 "ln folk:folklore anthro:anthropology thesaurus:related",
 "ln folk:folklore socio thesaurus:related",
 "ln folk:folklore oral:oral_tradition thesaurus:related",
]

# ── verbal folklore: the genres ──────────────────────────────────────────────
GENRES = [
 ("folktale", "A traditional prose story told as fiction, passed down orally.", ["oral:folktale","tale:aesop_fox_grapes"]),
 ("fairy_tale", "A wonder tale of magic and marvels (Märchen), as collected by the Grimms.", ["tale:grimm_cinderella","oral:tale_type"]),
 ("fable", "A short tale, often with animals, pointing to a moral (Aesop, La Fontaine, the Panchatantra, the Jatakas).", ["tale:aesop_ant_grasshopper","tale:lafontaine_animaux_peste","tale:panchatantra_blue_jackal"]),
 ("legend", "A story told as true and set in the real world, of heroes, saints or the uncanny.", ["oral:legend"]),
 ("myth_genre", "A sacred story of gods and origins (studied together with folklore).", ["myth:monomyth","myth:creation_cosmic_egg"]),
 ("epic", "A long heroic narrative in verse, carried by singers of tales.", ["oral:epic","oral:oral_formulaic_theory"]),
 ("ballad", "A narrative folk song.", ["oral:ballad"]),
 ("proverb", "A short, fixed saying carrying folk wisdom.", ["oral:proverb"]),
 ("riddle", "A puzzle-question in traditional form.", ["oral:riddle"]),
 ("trickster_tale", "Tales of the cunning trickster who breaks the rules (Anansi, Maui, the fox, Nasreddin).", ["myth:maui_trickster","tale:nasreddin_age_forty"]),
 ("folk_song", "The traditional songs of a community, learned by ear.", ["oral:praise_poetry"]),
 ("urban_legend", "A modern legend of the plausible-but-untrue, spread as having happened to 'a friend of a friend'.", ["oral:legend"]),
]
L += ["", "# ══ verbal folklore — the genres ══",
      'def "folk:genre" "The kinds of verbal folklore — the spoken and sung forms (口承文芸)."',
      "ln folk:genre folk:folklore sys:part_of"]
for slug, gloss, bridges in GENRES:
    gid = f"folk:genre:{slug}"
    L.append(f'def "{gid}" "{esc(gloss)}"')
    L.append(f"ln {gid} folk:genre sys:part_of")
    for b in bridges:
        L.append(f"ln {gid} {b} thesaurus:related")

# ── customary & material folklore ────────────────────────────────────────────
CUSTOMS = [
 ("festival", "A recurring communal celebration (matsuri, carnival, harvest feast).", ["season:spring","myth:calendar_animals"]),
 ("calendar_custom", "Customs tied to the turning year — new year, solstice, seasonal rites.", ["season:winter"]),
 ("life_cycle_rite", "Customs marking birth, coming-of-age, marriage and death.", ["anthro:concept:rite_of_passage"]),
 ("folk_belief", "Traditional beliefs about luck, omens and the unseen; superstition.", ["myth:mythical_method"]),
 ("folk_religion", "The lived, local religion of ordinary people, beside the official creed.", ["anthro:concept:magic_religion"]),
 ("folk_medicine", "Traditional healing: herbs, charms and the folk practitioner.", ["med:medicine"]),
 ("foodways", "The traditional foods of a people and the customs of preparing and sharing them.", ["anthro:concept:material_culture"]),
 ("folk_craft", "The handmade objects of vernacular tradition — pottery, weaving, toys.", ["crafthist:jomon_pottery","anthro:concept:material_culture"]),
 ("folk_costume", "Traditional dress marking region, status and occasion.", ["anthro:concept:material_culture"]),
 ("folk_dance", "The traditional dances of a community.", ["perf:hist:modern_dance","anthro:concept:ritual"]),
 ("folk_games", "Traditional games and play passed among children and communities.", []),
 ("vernacular_architecture", "The traditional building of ordinary dwellings, in local materials and style.", ["anthro:concept:material_culture"]),
]
L += ["", "# ══ customary & material folklore ══",
      'def "folk:custom" "Folklore beyond words — the customs, festivals, beliefs and made things of tradition (行事・習俗・物質文化)."',
      "ln folk:custom folk:folklore sys:part_of"]
for slug, gloss, bridges in CUSTOMS:
    cid = f"folk:custom:{slug}"
    L.append(f'def "{cid}" "{esc(gloss)}"')
    L.append(f"ln {cid} folk:custom sys:part_of")
    for b in bridges:
        L.append(f"ln {cid} {b} thesaurus:related")

# ── theory & method ──────────────────────────────────────────────────────────
CONCEPTS = [
 ("oral_tradition", "The body of culture carried and renewed by word of mouth, not writing.", ["oral:oral_tradition","oral:transmission"]),
 ("transmission", "How a tradition passes from teller to teller and place to place.", ["oral:transmission","crosscut:network"]),
 ("variant", "One of the many differing versions a tale takes as it travels — folklore's basic unit.", ["oral:variant"]),
 ("tale_type", "A recurring plot pattern catalogued in the Aarne-Thompson-Uther (ATU) index.", ["oral:tale_type"]),
 ("motif", "The smallest recurring element of a tale — a magic object, a task, a trick — indexed by Thompson.", ["oral:motif"]),
 ("the_folk", "The community whose shared tradition folklore studies — not only peasants but any group with its own lore.", ["socio:social_group"]),
 ("performance", "The idea that folklore lives in the telling — the event, teller and audience, not just the text.", ["oral:storyteller","socio:dramaturgy"]),
 ("fieldwork_collecting", "Going out to record living tradition from its bearers.", ["anthro:concept:fieldwork","oral:informant","oral:field_recording"]),
 ("folklorism_fakelore", "Revived, marketed or invented 'tradition' presented as authentic folklore.", []),
 ("diffusion", "The spread of a tale or custom from place to place (against independent re-invention).", ["crosscut:network"]),
 ("morphology_of_the_folktale", "Propp's finding that wonder tales share a fixed sequence of functions — a grammar of story.", ["anthro:concept:structuralism_anthro","ling:field:structural","myth:monomyth"]),
]
L += ["", "# ══ theory & method ══",
      'def "folk:concept" "The theory and method of folkloristics — how tradition is gathered, classified and understood."',
      "ln folk:concept folk:folklore sys:part_of"]
for slug, gloss, bridges in CONCEPTS:
    cid = f"folk:concept:{slug}"
    L.append(f'def "{cid}" "{esc(gloss)}"')
    L.append(f"ln {cid} folk:concept sys:part_of")
    for b in bridges:
        L.append(f"ln {cid} {b} thesaurus:related")

# ── the Japanese tradition ──────────────
JP = [
 ("folk:jp:minzokugaku", "日本民俗学 — the Japanese science of folklore founded by Yanagita Kunio, centred on the everyday life of the common people.", "folk:folklore"),
 ("folk:jp:jomin", "常民 — Yanagita's 'ordinary folk', the common people whose unwritten tradition is folklore's true subject.", "folk:jp:minzokugaku"),
 ("folk:jp:tono_monogatari", "遠野物語 — Yanagita's 1910 collection of the legends of Tono, the founding text of Japanese folklore studies.", "folk:jp:minzokugaku"),
]
L += ["", "# ══ the Japanese tradition ══"]
for jid, jgloss, jparent in JP:
    L.append(f'def "{jid}" "{esc(jgloss)}"')
    L.append(f"ln {jid} {jparent} sys:part_of")
L += [
 "ln folk:jp:jomin folk:concept:the_folk thesaurus:related",
 "ln folk:jp:tono_monogatari folk:genre:legend thesaurus:related",
 "ln folk:jp:tono_monogatari tale:japan_urashima_taro thesaurus:related",
 "ln folk:jp:minzokugaku folk:custom:folk_religion thesaurus:related",
]

# ── founders (person:*) ──────────────────────────────────────────────────────
# person:jacob_grimm already exists (linguistics) — relate it, do not re-def.
L += ["", "# ══ founders (person:jacob_grimm already exists — only linked) ══",
 "ln person:jacob_grimm folk:folklore thesaurus:related",
 "ln person:jacob_grimm folk:genre:fairy_tale thesaurus:related",
]
PEOPLE = [
 ("wilhelm_grimm", "With his brother Jacob, collected the 'Children's and Household Tales' (Grimms' Fairy Tales), founding tale-collection.", "literature", "modern_era", "folk:genre:fairy_tale"),
 ("yanagita_kunio", "Founder of Japanese folklore studies (民俗学); author of 'The Legends of Tōno' and champion of the 'common folk'.", "anthropology", "modern_era", "folk:jp:minzokugaku"),
 ("vladimir_propp", "Russian scholar whose 'Morphology of the Folktale' found the fixed functions underlying wonder tales.", "literature", "modern_era", "folk:concept:morphology_of_the_folktale"),
 ("stith_thompson", "Compiled the great Motif-Index and, with Aarne, the tale-type index that folklorists use worldwide.", "literature", "modern_era", "folk:concept:motif"),
 ("alan_dundes", "American folklorist who defined 'the folk' broadly and read folklore for its deep meanings.", "anthropology", "modern_era", "folk:concept:the_folk"),
 ("lafcadio_hearn", "Writer (小泉八雲) who gathered and retold Japanese ghost stories and legends for the wider world.", "literature", "modern_era", "folk:genre:legend"),
]
for slug, gloss, field, period, concept in PEOPLE:
    pid = f"person:{slug}"
    L.append(f'def "{pid}" "{esc(gloss)}"')
    L.append(f"ln {pid} person:figure thesaurus:related")
    L.append(f"ln {pid} person:field:{field} person:worked_in")
    L.append(f"ln {pid} folk:folklore person:worked_in")
    L.append(f"ln {pid} hist:period:{period} person:active_in")
    L.append(f"ln {pid} {concept} thesaurus:related")

# ── anchor the folktale genre to real tale:* corpora across cultures ──────────
L += ["", "# ── the world's folktale corpora (representative anchors, one per tradition) ──"]
ANCHORS = ["tale:aesop_fox_crow","tale:lafontaine_animaux_peste","tale:panchatantra_blue_jackal",
           "tale:jataka_ass_lions_skin","tale:grimm_cinderella","tale:china_butterfly_dream",
           "tale:nasreddin_age_forty","tale:japan_urashima_taro","tale:native_coyote_and_death"]
for a in ANCHORS:
    L.append(f"ln {a} folk:genre:folktale sys:part_of")

path = "app/ontology/base3/folklore.ak"
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
nd = sum(1 for l in L if l.startswith("def "))
nl = sum(1 for l in L if l.startswith("ln "))
print(f"{path}: def={nd} ln={nl} ({len(L)} lines)")
