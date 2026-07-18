# Akasha ontology — natural sciences: the general-education-level disciplinary map.
# Names each natural-science discipline and its major branches, and cross-link (bridges)
# the detailed atoms already in base3 (phys:law:*, chem:*, life:*, earthsci:*,
# astrophys:*) under that spine. Wired into the knowledge_map capstone.
# General-education breadth; research depth is reserved for level-C packs. Base pack.

def "knowledge:branch:natural_science" "自然科学 — the study of nature."

def "phys:physics" "物理学 — the science of matter, energy, motion, and the fundamental laws that govern the universe, from particles to galaxies."
ln phys:physics knowledge:branch:natural_science knowledge:in_branch
ln phys:physics math thesaurus:related
ln phys:physics knowledge:method:experimental thesaurus:related
def "phys:branch:classical_mechanics" "古典力学 — motion, force and energy of everyday bodies: Newton's laws, momentum, gravitation."
ln phys:branch:classical_mechanics phys:physics sys:part_of
ln phys:law:newtons_first_law phys:branch:classical_mechanics sys:part_of
ln phys:law:newtons_second_law phys:branch:classical_mechanics sys:part_of
ln phys:law:newtons_third_law phys:branch:classical_mechanics sys:part_of
ln phys:law:conservation_of_energy phys:branch:classical_mechanics sys:part_of
ln phys:force:friction phys:branch:classical_mechanics sys:part_of
ln phys:energy:potential_energy phys:branch:classical_mechanics sys:part_of
ln phys:branch:classical_mechanics math:calculus thesaurus:related
def "phys:branch:thermodynamics" "熱力学 — heat, temperature, energy and entropy; how energy flows and disperses."
ln phys:branch:thermodynamics phys:physics sys:part_of
ln phys:law:conservation_of_energy phys:branch:thermodynamics sys:part_of
ln phys:branch:thermodynamics chem:thermo:enthalpy thesaurus:related
ln phys:branch:thermodynamics mecheng:thermodynamics thesaurus:related
ln phys:branch:thermodynamics crosscut:energy thesaurus:related
def "phys:branch:electromagnetism" "電磁気学 — electric and magnetic fields unified: the force behind light, electricity and chemistry."
ln phys:branch:electromagnetism phys:physics sys:part_of
ln phys:law:maxwells_equations phys:branch:electromagnetism sys:part_of
ln phys:law:coulombs_law phys:branch:electromagnetism sys:part_of
ln phys:law:amperes_law phys:branch:electromagnetism sys:part_of
ln phys:law:faradays_law phys:branch:electromagnetism sys:part_of
ln phys:em:electric_field phys:branch:electromagnetism sys:part_of
ln phys:em:magnetic_field phys:branch:electromagnetism sys:part_of
ln phys:em:electromagnetic_wave phys:branch:electromagnetism sys:part_of
ln phys:em:electric_current phys:branch:electromagnetism sys:part_of
ln phys:branch:electromagnetism eleceng:electromagnetism thesaurus:related
def "phys:branch:optics" "光学 — the behaviour of light: reflection, refraction, colour, and its wave and particle nature."
ln phys:branch:optics phys:physics sys:part_of
ln phys:optics:absorption phys:branch:optics sys:part_of
ln phys:optics:chromophore phys:branch:optics sys:part_of
ln phys:optics:conjugation phys:branch:optics sys:part_of
ln phys:branch:optics phys:em:electromagnetic_wave thesaurus:related
def "phys:branch:waves_acoustics" "波動・音響学 — oscillations, waves and sound; how disturbances travel through media."
ln phys:branch:waves_acoustics phys:physics sys:part_of
ln phys:branch:waves_acoustics phys:em:electromagnetic_wave thesaurus:related
def "phys:branch:relativity" "相対性理論 — space, time, mass and gravity as Einstein reframed them at high speed and large scale."
ln phys:branch:relativity phys:physics sys:part_of
ln phys:branch:relativity phys:const:c thesaurus:related
ln phys:branch:relativity astrophys:gravity thesaurus:related
def "phys:branch:quantum_mechanics" "量子力学 — the physics of the very small, where energy is quantised and matter is also wave."
ln phys:branch:quantum_mechanics phys:physics sys:part_of
ln phys:const:h phys:branch:quantum_mechanics sys:part_of
ln phys:const:hbar phys:branch:quantum_mechanics sys:part_of
ln phys:branch:quantum_mechanics chem:quantum:electronegativity thesaurus:related
ln phys:branch:quantum_mechanics phys:const:alpha thesaurus:related
def "phys:branch:atomic_nuclear_particle" "原子・核・素粒子物理学 — the constituents of matter, from atoms and nuclei down to quarks and leptons."
ln phys:branch:atomic_nuclear_particle phys:physics sys:part_of
ln phys:const:e phys:branch:atomic_nuclear_particle sys:part_of
ln phys:const:me phys:branch:atomic_nuclear_particle sys:part_of
ln phys:const:mp phys:branch:atomic_nuclear_particle sys:part_of
ln phys:const:mn phys:branch:atomic_nuclear_particle sys:part_of
ln phys:branch:atomic_nuclear_particle astrophys:nuclear_fusion thesaurus:related
def "phys:branch:condensed_matter" "物性物理学 — the collective behaviour of matter in solid and liquid states."
ln phys:branch:condensed_matter phys:physics sys:part_of
ln phys:branch:condensed_matter matsci thesaurus:related
ln phys:branch:condensed_matter phys:const:k thesaurus:related
def "phys:branch:statistical_mechanics" "統計力学 — deriving heat and bulk properties from the statistics of countless particles."
ln phys:branch:statistical_mechanics phys:physics sys:part_of
ln phys:const:k phys:branch:statistical_mechanics sys:part_of
ln phys:const:na phys:branch:statistical_mechanics sys:part_of
ln phys:branch:statistical_mechanics math:statistics thesaurus:related
ln phys:branch:statistical_mechanics phys:branch:thermodynamics thesaurus:related
def "phys:branch:astrophysics" "宇宙物理学 — physics applied to stars, galaxies and the cosmos as a whole."
ln phys:branch:astrophysics phys:physics sys:part_of
ln phys:branch:astrophysics astrophys thesaurus:related
ln phys:branch:astrophysics astro:astronomy thesaurus:related

def "chem:chemistry" "化学 — the science of substances: their composition, structure, properties, and the transformations they undergo."
ln chem:chemistry knowledge:branch:natural_science knowledge:in_branch
ln chem:chemistry phys:physics thesaurus:related
ln chem:chemistry math thesaurus:related
def "chem:branch:physical_chemistry" "物理化学 — the physical principles behind chemical systems: thermodynamics, kinetics, quantum structure."
ln chem:branch:physical_chemistry chem:chemistry sys:part_of
ln chem:thermo:enthalpy chem:branch:physical_chemistry sys:part_of
ln chem:quantum:electronegativity chem:branch:physical_chemistry sys:part_of
ln chem:catalysis:heterogeneous_catalysis chem:branch:physical_chemistry sys:part_of
ln chem:branch:physical_chemistry phys:physics thesaurus:related
ln chem:branch:physical_chemistry phys:branch:thermodynamics thesaurus:related
def "chem:branch:organic_chemistry" "有機化学 — the chemistry of carbon compounds, the backbone of life and materials."
ln chem:branch:organic_chemistry chem:chemistry sys:part_of
ln chem:func:hydroxyl chem:branch:organic_chemistry sys:part_of
ln chem:class:ester chem:branch:organic_chemistry sys:part_of
ln chem:compound:benzene chem:branch:organic_chemistry sys:part_of
ln chem:compound:ethanol chem:branch:organic_chemistry sys:part_of
ln chem:branch:organic_chemistry chem:branch:biochemistry thesaurus:related
def "chem:branch:inorganic_chemistry" "無機化学 — the chemistry of elements and compounds other than carbon chains: metals, minerals, salts."
ln chem:branch:inorganic_chemistry chem:chemistry sys:part_of
ln chem:element:iron chem:branch:inorganic_chemistry sys:part_of
ln chem:element:carbon chem:branch:inorganic_chemistry sys:part_of
ln chem:bond:ionic_bond chem:branch:inorganic_chemistry sys:part_of
ln chem:branch:inorganic_chemistry matsci thesaurus:related
def "chem:branch:analytical_chemistry" "分析化学 — identifying and measuring what a sample contains, and how much."
ln chem:branch:analytical_chemistry chem:chemistry sys:part_of
ln chem:analytical:nmr_spectroscopy chem:branch:analytical_chemistry sys:part_of
ln chem:branch:analytical_chemistry phys:branch:optics thesaurus:related
def "chem:branch:biochemistry" "生化学 — the chemistry of living things: proteins, nucleic acids, metabolism."
ln chem:branch:biochemistry chem:chemistry sys:part_of
ln chem:protein:collagen chem:branch:biochemistry sys:part_of
ln chem:amino:glycine chem:branch:biochemistry sys:part_of
ln chem:lipid:triglyceride chem:branch:biochemistry sys:part_of
ln chem:carbo:glucose chem:branch:biochemistry sys:part_of
ln chem:branch:biochemistry bio:biology thesaurus:related
ln chem:branch:biochemistry life:metabolism thesaurus:related
ln chem:branch:biochemistry bio:metabolism:metabolism thesaurus:related
def "chem:branch:polymer_chemistry" "高分子化学 — long-chain molecules, from proteins and DNA to plastics and rubber."
ln chem:branch:polymer_chemistry chem:chemistry sys:part_of
ln chem:polymer:polyethylene chem:branch:polymer_chemistry sys:part_of
ln chem:polymer:nylon chem:branch:polymer_chemistry sys:part_of
ln chem:branch:polymer_chemistry matsci thesaurus:related
ln chem:branch:polymer_chemistry eng:branch:materials thesaurus:related
def "chem:branch:electrochemistry" "電気化学 — chemical change driven by, or producing, electric current: batteries, corrosion, electrolysis."
ln chem:branch:electrochemistry chem:chemistry sys:part_of
ln chem:branch:electrochemistry phys:branch:electromagnetism thesaurus:related
ln chem:branch:electrochemistry eleceng:current thesaurus:related
def "chem:branch:environmental_chemistry" "環境化学 — chemical processes in air, water and soil, and human impact on them."
ln chem:branch:environmental_chemistry chem:chemistry sys:part_of
ln chem:branch:environmental_chemistry ecol thesaurus:related
ln chem:branch:environmental_chemistry enveng thesaurus:related

def "bio:biology" "生物学 — the science of living organisms: their structure, function, growth, heredity, evolution and interactions."
ln bio:biology knowledge:branch:natural_science knowledge:in_branch
ln bio:biology chem:chemistry thesaurus:related
ln bio:biology med:medicine thesaurus:related
def "bio:branch:molecular_biology" "分子生物学 — life at the molecular level: DNA, RNA, proteins and the central dogma."
ln bio:branch:molecular_biology bio:biology sys:part_of
ln life:dna bio:branch:molecular_biology sys:part_of
ln life:rna bio:branch:molecular_biology sys:part_of
ln life:gene bio:branch:molecular_biology sys:part_of
ln life:protein_synthesis bio:branch:molecular_biology sys:part_of
ln bio:concept:central_dogma bio:branch:molecular_biology sys:part_of
ln bio:branch:molecular_biology chem:branch:biochemistry thesaurus:related
def "bio:branch:cell_biology" "細胞生物学 — the cell, life's basic unit: membranes, organelles, division."
ln bio:branch:cell_biology bio:biology sys:part_of
ln life:cell bio:branch:cell_biology sys:part_of
ln life:cell_membrane bio:branch:cell_biology sys:part_of
ln life:mitochondria bio:branch:cell_biology sys:part_of
ln life:ribosome bio:branch:cell_biology sys:part_of
ln life:nucleus_cell bio:branch:cell_biology sys:part_of
def "bio:branch:genetics" "遺伝学 — heredity and variation: genes, alleles, inheritance, genomics."
ln bio:branch:genetics bio:biology sys:part_of
ln life:genetics bio:branch:genetics sys:part_of
ln life:allele bio:branch:genetics sys:part_of
ln life:heredity bio:branch:genetics sys:part_of
ln life:genotype bio:branch:genetics sys:part_of
ln life:phenotype bio:branch:genetics sys:part_of
ln life:mutation bio:branch:genetics sys:part_of
ln life:genomics bio:branch:genetics sys:part_of
ln bio:branch:genetics life:gene_editing thesaurus:related
def "bio:branch:evolution" "進化生物学 — how life diversifies over time: natural selection, common descent, speciation."
ln bio:branch:evolution bio:biology sys:part_of
ln life:evolution bio:branch:evolution sys:part_of
ln life:natural_selection bio:branch:evolution sys:part_of
ln life:common_descent bio:branch:evolution sys:part_of
ln life:speciation bio:branch:evolution sys:part_of
ln life:phylogeny bio:branch:evolution sys:part_of
ln life:adaptation bio:branch:evolution sys:part_of
ln life:fitness bio:branch:evolution sys:part_of
ln bio:branch:evolution crosscut:evolution thesaurus:related
def "bio:branch:physiology" "生理学 — how living bodies work: the function of organs and systems."
ln bio:branch:physiology bio:biology sys:part_of
ln bio:metabolism:metabolism bio:branch:physiology sys:part_of
ln life:metabolism bio:branch:physiology sys:part_of
ln life:cellular_respiration bio:branch:physiology sys:part_of
ln bio:branch:physiology med:medicine thesaurus:related
def "bio:branch:microbiology" "微生物学 — bacteria, viruses and other microbes."
ln bio:branch:microbiology bio:biology sys:part_of
ln life:microbiology bio:branch:microbiology sys:part_of
ln life:bacteria bio:branch:microbiology sys:part_of
ln life:virus bio:branch:microbiology sys:part_of
ln life:immunity bio:branch:microbiology sys:part_of
def "bio:branch:botany" "植物学 — the biology of plants."
ln bio:branch:botany bio:biology sys:part_of
ln life:photosynthesis bio:branch:botany sys:part_of
ln bio:branch:botany agron thesaurus:related
ln bio:branch:botany ecol thesaurus:related
def "bio:branch:zoology" "動物学 — the biology of animals."
ln bio:branch:zoology bio:biology sys:part_of
ln bio:branch:zoology ecol thesaurus:related
def "bio:branch:ecology" "生態学 — organisms in relation to one another and their environment."
ln bio:branch:ecology bio:biology sys:part_of
ln bio:branch:ecology ecol thesaurus:related
ln bio:branch:ecology ecol:ecosystem thesaurus:related
ln bio:branch:ecology ecol:food_web thesaurus:related
def "bio:branch:developmental_biology" "発生生物学 — how an organism grows from a single cell."
ln bio:branch:developmental_biology bio:biology sys:part_of
ln life:epigenetics bio:branch:developmental_biology sys:part_of
ln bio:branch:developmental_biology bio:branch:genetics thesaurus:related
def "bio:branch:neuroscience" "神経科学 — the nervous system and the biological basis of mind and behaviour."
ln bio:branch:neuroscience bio:biology sys:part_of
ln bio:branch:neuroscience neuro thesaurus:related
ln bio:branch:neuroscience knowledge:cognitive_science thesaurus:related
def "bio:branch:biochemistry" "生化学 — the chemistry of life (shared with chemistry)."
ln bio:branch:biochemistry bio:biology sys:part_of
ln bio:branch:biochemistry chem:branch:biochemistry thesaurus:related

def "earthsci:earth_science" "地球科学 — the science of the Earth: its rocks, oceans, atmosphere, and the deep-time processes that shape them."
ln earthsci:earth_science knowledge:branch:natural_science knowledge:in_branch
ln earthsci:earth_science phys:physics thesaurus:related
ln earthsci:earth_science chem:chemistry thesaurus:related
ln earthsci:earth_science astrophys thesaurus:related
def "earthsci:branch:geology" "地質学 — the solid Earth: rocks, minerals, structure and history."
ln earthsci:branch:geology earthsci:earth_science sys:part_of
ln earthsci:geology earthsci:branch:geology sys:part_of
ln earthsci:mineralogy earthsci:branch:geology sys:part_of
ln earthsci:rock_cycle earthsci:branch:geology sys:part_of
ln earthsci:stratigraphy earthsci:branch:geology sys:part_of
ln earthsci:plate_tectonics earthsci:branch:geology sys:part_of
ln earthsci:seismology earthsci:branch:geology sys:part_of
ln earthsci:volcanology earthsci:branch:geology sys:part_of
ln earthsci:geomorphology earthsci:branch:geology sys:part_of
ln earthsci:branch:geology crosscut:cycle thesaurus:related
def "earthsci:branch:meteorology" "気象学 — the atmosphere and weather."
ln earthsci:branch:meteorology earthsci:earth_science sys:part_of
ln earthsci:branch:meteorology weather:climate thesaurus:related
ln earthsci:branch:meteorology phys:branch:thermodynamics thesaurus:related
def "earthsci:branch:climatology" "気候学 — climate: long-term patterns of weather and their change."
ln earthsci:branch:climatology earthsci:earth_science sys:part_of
ln earthsci:branch:climatology ecol:carbon_cycle thesaurus:related
ln earthsci:branch:climatology enveng thesaurus:related
def "earthsci:branch:oceanography" "海洋学 — the oceans: their water, currents, life and floor."
ln earthsci:branch:oceanography earthsci:earth_science sys:part_of
ln earthsci:branch:oceanography crosscut:cycle thesaurus:related
def "earthsci:branch:hydrology" "水文学 — water on and under the land: rivers, groundwater, the water cycle."
ln earthsci:branch:hydrology earthsci:earth_science sys:part_of
ln earthsci:branch:hydrology crosscut:cycle thesaurus:related
ln earthsci:branch:hydrology crosscut:system thesaurus:related
def "earthsci:branch:paleontology" "古生物学 — ancient life read from fossils; the bridge to evolution and deep time."
ln earthsci:branch:paleontology earthsci:earth_science sys:part_of
ln earthsci:branch:paleontology bio:branch:evolution thesaurus:related
ln earthsci:branch:paleontology archaeo thesaurus:related

def "astro:astronomy" "天文学 — the science of the heavens: the Sun, Moon, planets, stars, galaxies and the universe."
ln astro:astronomy knowledge:branch:natural_science knowledge:in_branch
ln astro:astronomy phys:physics thesaurus:related
ln astro:astronomy phys:branch:astrophysics thesaurus:related
def "astro:branch:planetary_science" "惑星科学 — the Sun's planets, moons and small bodies."
ln astro:branch:planetary_science astro:astronomy sys:part_of
ln astrophys:exoplanet astro:branch:planetary_science sys:part_of
ln astrophys:habitable_zone astro:branch:planetary_science sys:part_of
ln astrophys:orbital_mechanics astro:branch:planetary_science sys:part_of
ln astro:branch:planetary_science earthsci:earth_science thesaurus:related
def "astro:branch:stellar_astrophysics" "恒星天文学 — the birth, life and death of stars."
ln astro:branch:stellar_astrophysics astro:astronomy sys:part_of
ln astrophys:stellar_evolution astro:branch:stellar_astrophysics sys:part_of
ln astrophys:nuclear_fusion astro:branch:stellar_astrophysics sys:part_of
ln astrophys:supernova astro:branch:stellar_astrophysics sys:part_of
ln astrophys:neutron_star astro:branch:stellar_astrophysics sys:part_of
ln astrophys:black_hole astro:branch:stellar_astrophysics sys:part_of
ln astrophys:nebula astro:branch:stellar_astrophysics sys:part_of
ln astro:branch:stellar_astrophysics phys:branch:atomic_nuclear_particle thesaurus:related
def "astro:branch:cosmology" "宇宙論 — the origin, structure and fate of the universe as a whole."
ln astro:branch:cosmology astro:astronomy sys:part_of
ln astrophys:cosmology astro:branch:cosmology sys:part_of
ln astrophys:big_bang astro:branch:cosmology sys:part_of
ln astrophys:cosmic_expansion astro:branch:cosmology sys:part_of
ln astrophys:cosmic_microwave_background astro:branch:cosmology sys:part_of
ln astrophys:dark_matter astro:branch:cosmology sys:part_of
ln astrophys:dark_energy astro:branch:cosmology sys:part_of
ln astrophys:redshift astro:branch:cosmology sys:part_of
ln astro:branch:cosmology phys:branch:relativity thesaurus:related
def "astro:branch:observational_astronomy" "観測天文学 — the instruments and methods of watching the sky: telescopes, spectroscopy."
ln astro:branch:observational_astronomy astro:astronomy sys:part_of
ln astrophys:spectroscopy_astro astro:branch:observational_astronomy sys:part_of
ln astrophys:light_year astro:branch:observational_astronomy sys:part_of
ln astro:branch:observational_astronomy phys:branch:optics thesaurus:related
