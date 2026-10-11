# Akasha ontology — folklore studies / folkloristics.
# The field adjacent to cultural anthropology. Its materials existed scattered —
# oral:* (genres & tools of oral tradition), tale:* (the world's folktales), myth:* —
# but had no discipline spine. This adds folk:* and cross-links them. general-education breadth; research
# depth reserved for level-C packs. Base pack.

def "folk:folklore" "民俗学 — the study of the traditional culture of ordinary people: their tales, songs, customs, beliefs and crafts, and how these pass by word of mouth and imitation."
ln folk:folklore knowledge:branch:humanities knowledge:in_branch
ln folk:folklore anthro:anthropology thesaurus:related
ln folk:folklore socio thesaurus:related
ln folk:folklore oral:oral_tradition thesaurus:related

# ══ verbal folklore — the genres ══
def "folk:genre" "The kinds of verbal folklore — the spoken and sung forms (口承文芸)."
ln folk:genre folk:folklore sys:part_of
def "folk:genre:folktale" "A traditional prose story told as fiction, passed down orally."
ln folk:genre:folktale folk:genre sys:part_of
ln folk:genre:folktale oral:folktale thesaurus:related
ln folk:genre:folktale tale:aesop_fox_grapes thesaurus:related
def "folk:genre:fairy_tale" "A wonder tale of magic and marvels (Märchen), as collected by the Grimms."
ln folk:genre:fairy_tale folk:genre sys:part_of
ln folk:genre:fairy_tale tale:grimm_cinderella thesaurus:related
ln folk:genre:fairy_tale oral:tale_type thesaurus:related
def "folk:genre:fable" "A short tale, often with animals, pointing to a moral (Aesop, La Fontaine, the Panchatantra, the Jatakas)."
ln folk:genre:fable folk:genre sys:part_of
ln folk:genre:fable tale:aesop_ant_grasshopper thesaurus:related
ln folk:genre:fable tale:lafontaine_animaux_peste thesaurus:related
ln folk:genre:fable tale:panchatantra_blue_jackal thesaurus:related
def "folk:genre:legend" "A story told as true and set in the real world, of heroes, saints or the uncanny."
ln folk:genre:legend folk:genre sys:part_of
ln folk:genre:legend oral:legend thesaurus:related
def "folk:genre:myth_genre" "A sacred story of gods and origins (studied together with folklore)."
ln folk:genre:myth_genre folk:genre sys:part_of
ln folk:genre:myth_genre myth:monomyth thesaurus:related
ln folk:genre:myth_genre myth:creation_cosmic_egg thesaurus:related
def "folk:genre:epic" "A long heroic narrative in verse, carried by singers of tales."
ln folk:genre:epic folk:genre sys:part_of
ln folk:genre:epic oral:epic thesaurus:related
ln folk:genre:epic oral:oral_formulaic_theory thesaurus:related
def "folk:genre:ballad" "A narrative folk song."
ln folk:genre:ballad folk:genre sys:part_of
ln folk:genre:ballad oral:ballad thesaurus:related
def "folk:genre:proverb" "A short, fixed saying carrying folk wisdom."
ln folk:genre:proverb folk:genre sys:part_of
ln folk:genre:proverb oral:proverb thesaurus:related
def "folk:genre:riddle" "A puzzle-question in traditional form."
ln folk:genre:riddle folk:genre sys:part_of
ln folk:genre:riddle oral:riddle thesaurus:related
def "folk:genre:trickster_tale" "Tales of the cunning trickster who breaks the rules (Anansi, Maui, the fox, Nasreddin)."
ln folk:genre:trickster_tale folk:genre sys:part_of
ln folk:genre:trickster_tale myth:maui_trickster thesaurus:related
ln folk:genre:trickster_tale tale:nasreddin_age_forty thesaurus:related
def "folk:genre:folk_song" "The traditional songs of a community, learned by ear."
ln folk:genre:folk_song folk:genre sys:part_of
ln folk:genre:folk_song oral:praise_poetry thesaurus:related
def "folk:genre:urban_legend" "A modern legend of the plausible-but-untrue, spread as having happened to 'a friend of a friend'."
ln folk:genre:urban_legend folk:genre sys:part_of
ln folk:genre:urban_legend oral:legend thesaurus:related

# ══ customary & material folklore ══
def "folk:custom" "Folklore beyond words — the customs, festivals, beliefs and made things of tradition (行事・習俗・物質文化)."
ln folk:custom folk:folklore sys:part_of
def "folk:custom:festival" "A recurring communal celebration (matsuri, carnival, harvest feast)."
ln folk:custom:festival folk:custom sys:part_of
ln folk:custom:festival season:spring thesaurus:related
ln folk:custom:festival myth:calendar_animals thesaurus:related
def "folk:custom:calendar_custom" "Customs tied to the turning year — new year, solstice, seasonal rites."
ln folk:custom:calendar_custom folk:custom sys:part_of
ln folk:custom:calendar_custom season:winter thesaurus:related
def "folk:custom:life_cycle_rite" "Customs marking birth, coming-of-age, marriage and death."
ln folk:custom:life_cycle_rite folk:custom sys:part_of
ln folk:custom:life_cycle_rite anthro:concept:rite_of_passage thesaurus:related
def "folk:custom:folk_belief" "Traditional beliefs about luck, omens and the unseen; superstition."
ln folk:custom:folk_belief folk:custom sys:part_of
ln folk:custom:folk_belief myth:mythical_method thesaurus:related
def "folk:custom:folk_religion" "The lived, local religion of ordinary people, beside the official creed."
ln folk:custom:folk_religion folk:custom sys:part_of
ln folk:custom:folk_religion anthro:concept:magic_religion thesaurus:related
def "folk:custom:folk_medicine" "Traditional healing: herbs, charms and the folk practitioner."
ln folk:custom:folk_medicine folk:custom sys:part_of
ln folk:custom:folk_medicine med:medicine thesaurus:related
def "folk:custom:foodways" "The traditional foods of a people and the customs of preparing and sharing them."
ln folk:custom:foodways folk:custom sys:part_of
ln folk:custom:foodways anthro:concept:material_culture thesaurus:related
def "folk:custom:folk_craft" "The handmade objects of vernacular tradition — pottery, weaving, toys."
ln folk:custom:folk_craft folk:custom sys:part_of
ln folk:custom:folk_craft crafthist:jomon_pottery thesaurus:related
ln folk:custom:folk_craft anthro:concept:material_culture thesaurus:related
def "folk:custom:folk_costume" "Traditional dress marking region, status and occasion."
ln folk:custom:folk_costume folk:custom sys:part_of
ln folk:custom:folk_costume anthro:concept:material_culture thesaurus:related
def "folk:custom:folk_dance" "The traditional dances of a community."
ln folk:custom:folk_dance folk:custom sys:part_of
ln folk:custom:folk_dance perf:hist:modern_dance thesaurus:related
ln folk:custom:folk_dance anthro:concept:ritual thesaurus:related
def "folk:custom:folk_games" "Traditional games and play passed among children and communities."
ln folk:custom:folk_games folk:custom sys:part_of
def "folk:custom:vernacular_architecture" "The traditional building of ordinary dwellings, in local materials and style."
ln folk:custom:vernacular_architecture folk:custom sys:part_of
ln folk:custom:vernacular_architecture anthro:concept:material_culture thesaurus:related

# ══ theory & method ══
def "folk:concept" "The theory and method of folkloristics — how tradition is gathered, classified and understood."
ln folk:concept folk:folklore sys:part_of
def "folk:concept:oral_tradition" "The body of culture carried and renewed by word of mouth, not writing."
ln folk:concept:oral_tradition folk:concept sys:part_of
ln folk:concept:oral_tradition oral:oral_tradition thesaurus:related
ln folk:concept:oral_tradition oral:transmission thesaurus:related
def "folk:concept:transmission" "How a tradition passes from teller to teller and place to place."
ln folk:concept:transmission folk:concept sys:part_of
ln folk:concept:transmission oral:transmission thesaurus:related
ln folk:concept:transmission crosscut:network thesaurus:related
def "folk:concept:variant" "One of the many differing versions a tale takes as it travels — folklore's basic unit."
ln folk:concept:variant folk:concept sys:part_of
ln folk:concept:variant oral:variant thesaurus:related
def "folk:concept:tale_type" "A recurring plot pattern catalogued in the Aarne-Thompson-Uther (ATU) index."
ln folk:concept:tale_type folk:concept sys:part_of
ln folk:concept:tale_type oral:tale_type thesaurus:related
def "folk:concept:motif" "The smallest recurring element of a tale — a magic object, a task, a trick — indexed by Thompson."
ln folk:concept:motif folk:concept sys:part_of
ln folk:concept:motif oral:motif thesaurus:related
def "folk:concept:the_folk" "The community whose shared tradition folklore studies — not only peasants but any group with its own lore."
ln folk:concept:the_folk folk:concept sys:part_of
ln folk:concept:the_folk socio:social_group thesaurus:related
def "folk:concept:performance" "The idea that folklore lives in the telling — the event, teller and audience, not just the text."
ln folk:concept:performance folk:concept sys:part_of
ln folk:concept:performance oral:storyteller thesaurus:related
ln folk:concept:performance socio:dramaturgy thesaurus:related
def "folk:concept:fieldwork_collecting" "Going out to record living tradition from its bearers."
ln folk:concept:fieldwork_collecting folk:concept sys:part_of
ln folk:concept:fieldwork_collecting anthro:concept:fieldwork thesaurus:related
ln folk:concept:fieldwork_collecting oral:informant thesaurus:related
ln folk:concept:fieldwork_collecting oral:field_recording thesaurus:related
def "folk:concept:folklorism_fakelore" "Revived, marketed or invented 'tradition' presented as authentic folklore."
ln folk:concept:folklorism_fakelore folk:concept sys:part_of
def "folk:concept:diffusion" "The spread of a tale or custom from place to place (against independent re-invention)."
ln folk:concept:diffusion folk:concept sys:part_of
ln folk:concept:diffusion crosscut:network thesaurus:related
def "folk:concept:morphology_of_the_folktale" "Propp's finding that wonder tales share a fixed sequence of functions — a grammar of story."
ln folk:concept:morphology_of_the_folktale folk:concept sys:part_of
ln folk:concept:morphology_of_the_folktale anthro:concept:structuralism_anthro thesaurus:related
ln folk:concept:morphology_of_the_folktale ling:field:structural thesaurus:related
ln folk:concept:morphology_of_the_folktale myth:monomyth thesaurus:related

# ══ the Japanese tradition ══
def "folk:jp:minzokugaku" "日本民俗学 — the Japanese science of folklore founded by Yanagita Kunio, centred on the everyday life of the common people."
ln folk:jp:minzokugaku folk:folklore sys:part_of
def "folk:jp:jomin" "常民 — Yanagita's 'ordinary folk', the common people whose unwritten tradition is folklore's true subject."
ln folk:jp:jomin folk:jp:minzokugaku sys:part_of
def "folk:jp:tono_monogatari" "遠野物語 — Yanagita's 1910 collection of the legends of Tono, the founding text of Japanese folklore studies."
ln folk:jp:tono_monogatari folk:jp:minzokugaku sys:part_of
ln folk:jp:jomin folk:concept:the_folk thesaurus:related
ln folk:jp:tono_monogatari folk:genre:legend thesaurus:related
ln folk:jp:tono_monogatari tale:japan_urashima_taro thesaurus:related
ln folk:jp:minzokugaku folk:custom:folk_religion thesaurus:related

# ══ founders (person:jacob_grimm already exists — only linked) ══
ln person:jacob_grimm folk:folklore thesaurus:related
ln person:jacob_grimm folk:genre:fairy_tale thesaurus:related
def "person:wilhelm_grimm" "With his brother Jacob, collected the 'Children's and Household Tales' (Grimms' Fairy Tales), founding tale-collection."
ln person:wilhelm_grimm person:figure thesaurus:related
ln person:wilhelm_grimm person:field:literature person:worked_in
ln person:wilhelm_grimm folk:folklore person:worked_in
ln person:wilhelm_grimm hist:period:modern_era person:active_in
ln person:wilhelm_grimm folk:genre:fairy_tale thesaurus:related
def "person:yanagita_kunio" "Founder of Japanese folklore studies (民俗学); author of 'The Legends of Tōno' and champion of the 'common folk'."
ln person:yanagita_kunio person:figure thesaurus:related
ln person:yanagita_kunio person:field:anthropology person:worked_in
ln person:yanagita_kunio folk:folklore person:worked_in
ln person:yanagita_kunio hist:period:modern_era person:active_in
ln person:yanagita_kunio folk:jp:minzokugaku thesaurus:related
def "person:vladimir_propp" "Russian scholar whose 'Morphology of the Folktale' found the fixed functions underlying wonder tales."
ln person:vladimir_propp person:figure thesaurus:related
ln person:vladimir_propp person:field:literature person:worked_in
ln person:vladimir_propp folk:folklore person:worked_in
ln person:vladimir_propp hist:period:modern_era person:active_in
ln person:vladimir_propp folk:concept:morphology_of_the_folktale thesaurus:related
def "person:stith_thompson" "Compiled the great Motif-Index and, with Aarne, the tale-type index that folklorists use worldwide."
ln person:stith_thompson person:figure thesaurus:related
ln person:stith_thompson person:field:literature person:worked_in
ln person:stith_thompson folk:folklore person:worked_in
ln person:stith_thompson hist:period:modern_era person:active_in
ln person:stith_thompson folk:concept:motif thesaurus:related
def "person:alan_dundes" "American folklorist who defined 'the folk' broadly and read folklore for its deep meanings."
ln person:alan_dundes person:figure thesaurus:related
ln person:alan_dundes person:field:anthropology person:worked_in
ln person:alan_dundes folk:folklore person:worked_in
ln person:alan_dundes hist:period:modern_era person:active_in
ln person:alan_dundes folk:concept:the_folk thesaurus:related
def "person:lafcadio_hearn" "Writer (小泉八雲) who gathered and retold Japanese ghost stories and legends for the wider world."
ln person:lafcadio_hearn person:figure thesaurus:related
ln person:lafcadio_hearn person:field:literature person:worked_in
ln person:lafcadio_hearn folk:folklore person:worked_in
ln person:lafcadio_hearn hist:period:modern_era person:active_in
ln person:lafcadio_hearn folk:genre:legend thesaurus:related

# ── the world's folktale corpora (representative anchors, one per tradition) ──
ln tale:aesop_fox_crow folk:genre:folktale sys:part_of
ln tale:lafontaine_animaux_peste folk:genre:folktale sys:part_of
ln tale:panchatantra_blue_jackal folk:genre:folktale sys:part_of
ln tale:jataka_ass_lions_skin folk:genre:folktale sys:part_of
ln tale:grimm_cinderella folk:genre:folktale sys:part_of
ln tale:china_butterfly_dream folk:genre:folktale sys:part_of
ln tale:nasreddin_age_forty folk:genre:folktale sys:part_of
ln tale:japan_urashima_taro folk:genre:folktale sys:part_of
ln tale:native_coyote_and_death folk:genre:folktale sys:part_of
