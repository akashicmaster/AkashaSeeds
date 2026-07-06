# Akasha ontology — namespace: person (fields, subfields, eras)
# Purpose: Occupation/field classification taxonomy for notable historical figures
# atoms: ~100 (fields, subfields, era anchors)

# ─────────────────────────────────────────────
# ERA ANCHORS
# ─────────────────────────────────────────────

def "person:era:ancient" "Pre-500 CE; civilisations of Greece, Rome, Egypt, Mesopotamia, India, China."
set.add name="person:eras" id="person:era:ancient"

def "person:era:late_antique" "300–700 CE; transition from classical antiquity to medieval world."
set.add name="person:eras" id="person:era:late_antique"

def "person:era:medieval" "500–1500 CE; feudal Europe, Islamic Golden Age, Song China, Byzantine Empire."
set.add name="person:eras" id="person:era:medieval"

def "person:era:renaissance" "1400–1600 CE; revival of classical learning, humanism, arts, and science in Europe."
set.add name="person:eras" id="person:era:renaissance"

def "person:era:early_modern" "1500–1800 CE; Reformation, European expansion, Scientific Revolution."
set.add name="person:eras" id="person:era:early_modern"

def "person:era:enlightenment" "1650–1800 CE; reason, empiricism, natural rights, secularism."
set.add name="person:eras" id="person:era:enlightenment"

def "person:era:romantic_era" "1780–1850 CE; reaction to Enlightenment rationalism; emotion, nature, nationalism."
set.add name="person:eras" id="person:era:romantic_era"

def "person:era:industrial_era" "1820–1920 CE; industrialisation, nation-states, positivism, mass science."
set.add name="person:eras" id="person:era:industrial_era"

# ─────────────────────────────────────────────
# TOP-LEVEL FIELD CATEGORIES
# ─────────────────────────────────────────────

def "person:field:philosophy" "Systematic inquiry into existence, knowledge, ethics, mind, and language."
set.add name="person:fields" id="person:field:philosophy"

def "person:field:science" "Empirical investigation of the natural world through observation and experiment."
set.add name="person:fields" id="person:field:science"

def "person:field:mathematics" "Formal study of quantity, structure, space, and change."
set.add name="person:fields" id="person:field:mathematics"

def "person:field:medicine" "Study, diagnosis, and treatment of disease and injury in human beings."
set.add name="person:fields" id="person:field:medicine"

def "person:field:literature" "Written works valued for form and expression; poetry, prose, drama, history."
set.add name="person:fields" id="person:field:literature"

def "person:field:music" "Art of organising sound in time; composition, performance, and theory."
set.add name="person:fields" id="person:field:music"

def "person:field:visual_arts" "Arts produced primarily for visual perception: painting, sculpture, printmaking."
set.add name="person:fields" id="person:field:visual_arts"

def "person:field:architecture" "Design and construction of buildings and built environments."
set.add name="person:fields" id="person:field:architecture"

def "person:field:religion" "Organised systems of belief, worship, ritual, and spiritual practice."
set.add name="person:fields" id="person:field:religion"

def "person:field:politics_statecraft" "Art and practice of governing peoples, states, and empires."
set.add name="person:fields" id="person:field:politics_statecraft"

def "person:field:military" "Organisation, strategy, and conduct of armed conflict."
set.add name="person:fields" id="person:field:military"

def "person:field:exploration_navigation" "Discovery and mapping of unknown lands, seas, and routes."
set.add name="person:fields" id="person:field:exploration_navigation"

def "person:field:law" "Systems of rules governing conduct within societies; jurisprudence and legislation."
set.add name="person:fields" id="person:field:law"

def "person:field:economics" "Study and management of production, distribution, and consumption of wealth."
set.add name="person:fields" id="person:field:economics"

def "person:field:engineering_invention" "Design and creation of tools, machines, and built systems; applied invention."
set.add name="person:fields" id="person:field:engineering_invention"

def "person:field:theater_performing_arts" "Live performance arts: drama, dance, rhetoric, opera, and related forms."
set.add name="person:fields" id="person:field:theater_performing_arts"

def "person:field:linguistics_scholarship" "Study of language structure, philology, translation, and textual criticism."
set.add name="person:fields" id="person:field:linguistics_scholarship"

# ─────────────────────────────────────────────
# PHILOSOPHY SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:metaphysics" "Inquiry into the fundamental nature of reality, being, and the cosmos."
ln person:subfield:metaphysics person:field:philosophy sys:part_of
set.add name="person:fields" id="person:subfield:metaphysics"

def "person:subfield:ethics" "Systematic study of moral principles, virtues, and right conduct."
ln person:subfield:ethics person:field:philosophy sys:part_of
set.add name="person:fields" id="person:subfield:ethics"

def "person:subfield:logic" "Formal study of valid inference, argument structure, and proof."
ln person:subfield:logic person:field:philosophy sys:part_of
set.add name="person:fields" id="person:subfield:logic"

def "person:subfield:political_philosophy" "Philosophical analysis of justice, authority, rights, and the good polity."
ln person:subfield:political_philosophy person:field:philosophy sys:part_of
ln person:subfield:political_philosophy person:field:politics_statecraft people:related_to
set.add name="person:fields" id="person:subfield:political_philosophy"

def "person:subfield:natural_philosophy" "Pre-modern inquiry into nature that preceded and seeded modern science."
ln person:subfield:natural_philosophy person:field:philosophy sys:part_of
ln person:subfield:natural_philosophy person:field:science people:related_to
set.add name="person:fields" id="person:subfield:natural_philosophy"

# ─────────────────────────────────────────────
# SCIENCE SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:physics" "Study of matter, energy, motion, and the fundamental laws of the universe."
ln person:subfield:physics person:field:science sys:part_of
set.add name="person:fields" id="person:subfield:physics"

def "person:subfield:chemistry" "Study of matter's composition, properties, and transformations."
ln person:subfield:chemistry person:field:science sys:part_of
set.add name="person:fields" id="person:subfield:chemistry"

def "person:subfield:biology" "Study of living organisms, their structure, function, evolution, and ecology."
ln person:subfield:biology person:field:science sys:part_of
set.add name="person:fields" id="person:subfield:biology"

def "person:subfield:astronomy" "Observation and theory of celestial bodies, cosmology, and the heavens."
ln person:subfield:astronomy person:field:science sys:part_of
set.add name="person:fields" id="person:subfield:astronomy"

def "person:subfield:geology" "Study of the Earth's physical structure, history, and processes."
ln person:subfield:geology person:field:science sys:part_of
set.add name="person:fields" id="person:subfield:geology"

# ─────────────────────────────────────────────
# MATHEMATICS SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:algebra" "Study of mathematical symbols, operations, and abstract structures."
ln person:subfield:algebra person:field:mathematics sys:part_of
set.add name="person:fields" id="person:subfield:algebra"

def "person:subfield:geometry" "Study of shapes, spatial relationships, and properties of figures."
ln person:subfield:geometry person:field:mathematics sys:part_of
set.add name="person:fields" id="person:subfield:geometry"

def "person:subfield:number_theory" "Study of integers, primes, and the deep properties of whole numbers."
ln person:subfield:number_theory person:field:mathematics sys:part_of
set.add name="person:fields" id="person:subfield:number_theory"

def "person:subfield:calculus" "Mathematical study of continuous change; differentiation and integration."
ln person:subfield:calculus person:field:mathematics sys:part_of
set.add name="person:fields" id="person:subfield:calculus"

def "person:subfield:combinatorics" "Study of counting, arrangement, and combination of discrete structures."
ln person:subfield:combinatorics person:field:mathematics sys:part_of
set.add name="person:fields" id="person:subfield:combinatorics"

# ─────────────────────────────────────────────
# MEDICINE SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:surgery" "Manual and instrumental treatment of disease or injury by operation."
ln person:subfield:surgery person:field:medicine sys:part_of
set.add name="person:fields" id="person:subfield:surgery"

def "person:subfield:pharmacology" "Study of drugs, their composition, effects, and therapeutic uses."
ln person:subfield:pharmacology person:field:medicine sys:part_of
set.add name="person:fields" id="person:subfield:pharmacology"

def "person:subfield:anatomy" "Study of the structure of the human body and its organs."
ln person:subfield:anatomy person:field:medicine sys:part_of
set.add name="person:fields" id="person:subfield:anatomy"

def "person:subfield:public_health" "Organised efforts to prevent disease and promote health across populations."
ln person:subfield:public_health person:field:medicine sys:part_of
set.add name="person:fields" id="person:subfield:public_health"

# ─────────────────────────────────────────────
# LITERATURE SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:poetry" "Metrically or rhythmically structured literary composition."
ln person:subfield:poetry person:field:literature sys:part_of
set.add name="person:fields" id="person:subfield:poetry"

def "person:subfield:prose" "Written language in its ordinary form, including novels, essays, and stories."
ln person:subfield:prose person:field:literature sys:part_of
set.add name="person:fields" id="person:subfield:prose"

def "person:subfield:drama" "Literary composition intended for theatrical performance."
ln person:subfield:drama person:field:literature sys:part_of
ln person:subfield:drama person:field:theater_performing_arts people:related_to
set.add name="person:fields" id="person:subfield:drama"

def "person:subfield:historiography" "Writing and methodology of history; chronicles, annals, and historical narrative."
ln person:subfield:historiography person:field:literature sys:part_of
set.add name="person:fields" id="person:subfield:historiography"

def "person:subfield:sacred_texts" "Religious scriptures, canonical writings, commentaries, and revealed literature."
ln person:subfield:sacred_texts person:field:literature sys:part_of
ln person:subfield:sacred_texts person:field:religion people:related_to
set.add name="person:fields" id="person:subfield:sacred_texts"

# ─────────────────────────────────────────────
# MUSIC SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:composition" "Creation and notation of original musical works."
ln person:subfield:composition person:field:music sys:part_of
set.add name="person:fields" id="person:subfield:composition"

def "person:subfield:music_theory" "Systematic description of the language and notation of music."
ln person:subfield:music_theory person:field:music sys:part_of
set.add name="person:fields" id="person:subfield:music_theory"

def "person:subfield:instrument_building" "Design and construction of musical instruments."
ln person:subfield:instrument_building person:field:music sys:part_of
ln person:subfield:instrument_building person:field:engineering_invention people:related_to
set.add name="person:fields" id="person:subfield:instrument_building"

# ─────────────────────────────────────────────
# VISUAL ARTS SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:painting" "Application of pigment to a surface to create a pictorial representation."
ln person:subfield:painting person:field:visual_arts sys:part_of
set.add name="person:fields" id="person:subfield:painting"

def "person:subfield:sculpture" "Three-dimensional art produced by carving, modelling, casting, or assembling."
ln person:subfield:sculpture person:field:visual_arts sys:part_of
set.add name="person:fields" id="person:subfield:sculpture"

def "person:subfield:printmaking" "Creation of images on a matrix transferred to paper or fabric."
ln person:subfield:printmaking person:field:visual_arts sys:part_of
set.add name="person:fields" id="person:subfield:printmaking"

def "person:subfield:illumination" "Decoration of manuscripts and books with gold, silver, and vivid pigments."
ln person:subfield:illumination person:field:visual_arts sys:part_of
set.add name="person:fields" id="person:subfield:illumination"

# ─────────────────────────────────────────────
# RELIGION SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:theology" "Systematic study of the nature of the divine and religious doctrine."
ln person:subfield:theology person:field:religion sys:part_of
set.add name="person:fields" id="person:subfield:theology"

def "person:subfield:mysticism" "Direct experiential pursuit of union with the divine or ultimate reality."
ln person:subfield:mysticism person:field:religion sys:part_of
set.add name="person:fields" id="person:subfield:mysticism"

def "person:subfield:monasticism" "Religious life organised around communal or solitary withdrawal and discipline."
ln person:subfield:monasticism person:field:religion sys:part_of
set.add name="person:fields" id="person:subfield:monasticism"

def "person:subfield:religious_law" "Legal codes derived from religious scripture and tradition."
ln person:subfield:religious_law person:field:religion sys:part_of
ln person:subfield:religious_law person:field:law people:related_to
set.add name="person:fields" id="person:subfield:religious_law"

# ─────────────────────────────────────────────
# POLITICS / STATECRAFT SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:statesmanship" "Skill in managing state affairs, leading governments, and shaping policy."
ln person:subfield:statesmanship person:field:politics_statecraft sys:part_of
set.add name="person:fields" id="person:subfield:statesmanship"

def "person:subfield:diplomacy" "Negotiation and management of relations between states and peoples."
ln person:subfield:diplomacy person:field:politics_statecraft sys:part_of
set.add name="person:fields" id="person:subfield:diplomacy"

def "person:subfield:lawgiving" "Creation and codification of foundational legal and constitutional frameworks."
ln person:subfield:lawgiving person:field:politics_statecraft sys:part_of
ln person:subfield:lawgiving person:field:law people:related_to
set.add name="person:fields" id="person:subfield:lawgiving"

def "person:subfield:colonial_administration" "Governance of overseas territories and subject peoples by imperial powers."
ln person:subfield:colonial_administration person:field:politics_statecraft sys:part_of
set.add name="person:fields" id="person:subfield:colonial_administration"

# ─────────────────────────────────────────────
# MILITARY SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:strategy" "High-level planning and direction of military campaigns and wars."
ln person:subfield:strategy person:field:military sys:part_of
set.add name="person:fields" id="person:subfield:strategy"

def "person:subfield:naval_command" "Leadership and conduct of naval forces and maritime warfare."
ln person:subfield:naval_command person:field:military sys:part_of
set.add name="person:fields" id="person:subfield:naval_command"

def "person:subfield:siege_warfare" "Techniques for attacking and defending fortified positions."
ln person:subfield:siege_warfare person:field:military sys:part_of
set.add name="person:fields" id="person:subfield:siege_warfare"

# ─────────────────────────────────────────────
# EXPLORATION / NAVIGATION SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:maritime_exploration" "Voyaging and discovery by sea; ocean crossing and coastal survey."
ln person:subfield:maritime_exploration person:field:exploration_navigation sys:part_of
set.add name="person:fields" id="person:subfield:maritime_exploration"

def "person:subfield:cartography" "Science and art of making maps; geographic representation of space."
ln person:subfield:cartography person:field:exploration_navigation sys:part_of
set.add name="person:fields" id="person:subfield:cartography"

def "person:subfield:overland_exploration" "Discovery and survey of land routes, continents, and interior territories."
ln person:subfield:overland_exploration person:field:exploration_navigation sys:part_of
set.add name="person:fields" id="person:subfield:overland_exploration"

# ─────────────────────────────────────────────
# ENGINEERING / INVENTION SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:civil_engineering" "Design and construction of infrastructure: roads, bridges, aqueducts, canals."
ln person:subfield:civil_engineering person:field:engineering_invention sys:part_of
set.add name="person:fields" id="person:subfield:civil_engineering"

def "person:subfield:mechanical_engineering" "Design of machines and mechanical systems that convert energy to useful work."
ln person:subfield:mechanical_engineering person:field:engineering_invention sys:part_of
set.add name="person:fields" id="person:subfield:mechanical_engineering"

def "person:subfield:hydraulics" "Engineering of water systems: dams, irrigation, water supply, and flood control."
ln person:subfield:hydraulics person:field:engineering_invention sys:part_of
set.add name="person:fields" id="person:subfield:hydraulics"

def "person:subfield:optics_instruments" "Design of lenses, telescopes, microscopes, and precision optical devices."
ln person:subfield:optics_instruments person:field:engineering_invention sys:part_of
ln person:subfield:optics_instruments person:field:science people:related_to
set.add name="person:fields" id="person:subfield:optics_instruments"

# ─────────────────────────────────────────────
# LINGUISTICS / SCHOLARSHIP SUBFIELDS
# ─────────────────────────────────────────────

def "person:subfield:philology" "Historical study of language and literary texts; textual criticism and edition."
ln person:subfield:philology person:field:linguistics_scholarship sys:part_of
set.add name="person:fields" id="person:subfield:philology"

def "person:subfield:translation" "Rendering of texts across languages; transmission of knowledge between cultures."
ln person:subfield:translation person:field:linguistics_scholarship sys:part_of
set.add name="person:fields" id="person:subfield:translation"

def "person:subfield:rhetoric" "Art of effective and persuasive speaking and writing."
ln person:subfield:rhetoric person:field:linguistics_scholarship sys:part_of
ln person:subfield:rhetoric person:field:theater_performing_arts people:related_to
set.add name="person:fields" id="person:subfield:rhetoric"

# ─────────────────────────────────────────────
# ERA LINKS — fields that strongly characterise certain eras
# ─────────────────────────────────────────────

ln person:field:philosophy person:era:ancient people:flourished_in
ln person:field:mathematics person:era:ancient people:flourished_in
ln person:field:architecture person:era:ancient people:flourished_in
ln person:field:military person:era:ancient people:flourished_in
ln person:field:religion person:era:ancient people:flourished_in

ln person:field:religion person:era:late_antique people:flourished_in
ln person:field:linguistics_scholarship person:era:late_antique people:flourished_in
ln person:subfield:theology person:era:late_antique people:flourished_in

ln person:field:religion person:era:medieval people:flourished_in
ln person:field:literature person:era:medieval people:flourished_in
ln person:field:mathematics person:era:medieval people:flourished_in
ln person:subfield:monasticism person:era:medieval people:flourished_in
ln person:subfield:illumination person:era:medieval people:flourished_in
ln person:subfield:siege_warfare person:era:medieval people:flourished_in

ln person:field:visual_arts person:era:renaissance people:flourished_in
ln person:field:architecture person:era:renaissance people:flourished_in
ln person:field:science person:era:renaissance people:flourished_in
ln person:subfield:painting person:era:renaissance people:flourished_in
ln person:subfield:sculpture person:era:renaissance people:flourished_in
ln person:subfield:natural_philosophy person:era:renaissance people:flourished_in

ln person:field:exploration_navigation person:era:early_modern people:flourished_in
ln person:field:music person:era:early_modern people:flourished_in
ln person:subfield:maritime_exploration person:era:early_modern people:flourished_in
ln person:subfield:cartography person:era:early_modern people:flourished_in
ln person:subfield:composition person:era:early_modern people:flourished_in

ln person:field:philosophy person:era:enlightenment people:flourished_in
ln person:field:science person:era:enlightenment people:flourished_in
ln person:field:economics person:era:enlightenment people:flourished_in
ln person:field:politics_statecraft person:era:enlightenment people:flourished_in
ln person:subfield:political_philosophy person:era:enlightenment people:flourished_in
ln person:subfield:calculus person:era:enlightenment people:flourished_in

ln person:field:literature person:era:romantic_era people:flourished_in
ln person:field:music person:era:romantic_era people:flourished_in
ln person:subfield:poetry person:era:romantic_era people:flourished_in
ln person:subfield:composition person:era:romantic_era people:flourished_in

ln person:field:science person:era:industrial_era people:flourished_in
ln person:field:engineering_invention person:era:industrial_era people:flourished_in
ln person:field:economics person:era:industrial_era people:flourished_in
ln person:subfield:chemistry person:era:industrial_era people:flourished_in
ln person:subfield:biology person:era:industrial_era people:flourished_in
ln person:subfield:civil_engineering person:era:industrial_era people:flourished_in
ln person:subfield:mechanical_engineering person:era:industrial_era people:flourished_in
