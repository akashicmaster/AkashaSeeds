#!/usr/bin/env python3
# Generate two general-education-level (general-education) disciplinary maps for base3:
#   app/ontology/base3/natural_sciences.ak  — the spine of the natural sciences
#   app/ontology/base3/engineering.ak       — the spine of engineering
# These do NOT re-define the detailed atoms that already live in base3 (phys:law:*,
# chem:*, life:*, earthsci:*, astrophys:*, mecheng:*, eleceng:* …). They add the
# missing top-level spine — the disciplines and their major branches — and cross-link
# (bridge) the scattered existing atoms under it, wiring the whole into the
# knowledge_map capstone (knowledge:branch:natural_science / :applied_science).

import os

def esc(s):
    return s.replace('"', "'")

def emit(lines, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    ndef = sum(1 for l in lines if l.startswith("def "))
    nln = sum(1 for l in lines if l.startswith("ln "))
    print(f"{path}: def={ndef} ln={nln} ({len(lines)} lines)")

# ─────────────────────────────────────────────────────────────────────────────
# NATURAL SCIENCES
# ─────────────────────────────────────────────────────────────────────────────
# disciplines: (id, gloss, [ (branch_id, branch_gloss, [existing atoms to cross-link],
#                              [thesaurus:related bridges]) ], [discipline bridges])
NS = [
 ("phys:physics",
  "物理学 — the science of matter, energy, motion, and the fundamental laws that govern the universe, from particles to galaxies.",
  [
   ("phys:branch:classical_mechanics", "古典力学 — motion, force and energy of everyday bodies: Newton's laws, momentum, gravitation.",
     ["phys:law:newtons_first_law","phys:law:newtons_second_law","phys:law:newtons_third_law","phys:law:conservation_of_energy","phys:force:friction","phys:energy:potential_energy"], ["math:calculus"]),
   ("phys:branch:thermodynamics", "熱力学 — heat, temperature, energy and entropy; how energy flows and disperses.",
     ["phys:law:conservation_of_energy"], ["chem:thermo:enthalpy","mecheng:thermodynamics","crosscut:energy"]),
   ("phys:branch:electromagnetism", "電磁気学 — electric and magnetic fields unified: the force behind light, electricity and chemistry.",
     ["phys:law:maxwells_equations","phys:law:coulombs_law","phys:law:amperes_law","phys:law:faradays_law","phys:em:electric_field","phys:em:magnetic_field","phys:em:electromagnetic_wave","phys:em:electric_current"], ["eleceng:electromagnetism"]),
   ("phys:branch:optics", "光学 — the behaviour of light: reflection, refraction, colour, and its wave and particle nature.",
     ["phys:optics:absorption","phys:optics:chromophore","phys:optics:conjugation"], ["phys:em:electromagnetic_wave"]),
   ("phys:branch:waves_acoustics", "波動・音響学 — oscillations, waves and sound; how disturbances travel through media.",
     [], ["phys:em:electromagnetic_wave"]),
   ("phys:branch:relativity", "相対性理論 — space, time, mass and gravity as Einstein reframed them at high speed and large scale.",
     [], ["phys:const:c","astrophys:gravity"]),
   ("phys:branch:quantum_mechanics", "量子力学 — the physics of the very small, where energy is quantised and matter is also wave.",
     ["phys:const:h","phys:const:hbar"], ["chem:quantum:electronegativity","phys:const:alpha"]),
   ("phys:branch:atomic_nuclear_particle", "原子・核・素粒子物理学 — the constituents of matter, from atoms and nuclei down to quarks and leptons.",
     ["phys:const:e","phys:const:me","phys:const:mp","phys:const:mn"], ["astrophys:nuclear_fusion"]),
   ("phys:branch:condensed_matter", "物性物理学 — the collective behaviour of matter in solid and liquid states.",
     [], ["matsci","phys:const:k"]),
   ("phys:branch:statistical_mechanics", "統計力学 — deriving heat and bulk properties from the statistics of countless particles.",
     ["phys:const:k","phys:const:na"], ["math:statistics","phys:branch:thermodynamics"]),
   ("phys:branch:astrophysics", "宇宙物理学 — physics applied to stars, galaxies and the cosmos as a whole.",
     [], ["astrophys","astro:astronomy"]),
  ],
  ["math","knowledge:method:experimental"]),

 ("chem:chemistry",
  "化学 — the science of substances: their composition, structure, properties, and the transformations they undergo.",
  [
   ("chem:branch:physical_chemistry", "物理化学 — the physical principles behind chemical systems: thermodynamics, kinetics, quantum structure.",
     ["chem:thermo:enthalpy","chem:quantum:electronegativity","chem:catalysis:heterogeneous_catalysis"], ["phys:physics","phys:branch:thermodynamics"]),
   ("chem:branch:organic_chemistry", "有機化学 — the chemistry of carbon compounds, the backbone of life and materials.",
     ["chem:func:hydroxyl","chem:class:ester","chem:compound:benzene","chem:compound:ethanol"], ["chem:branch:biochemistry"]),
   ("chem:branch:inorganic_chemistry", "無機化学 — the chemistry of elements and compounds other than carbon chains: metals, minerals, salts.",
     ["chem:element:iron","chem:element:carbon","chem:bond:ionic_bond"], ["matsci"]),
   ("chem:branch:analytical_chemistry", "分析化学 — identifying and measuring what a sample contains, and how much.",
     ["chem:analytical:nmr_spectroscopy"], ["phys:branch:optics"]),
   ("chem:branch:biochemistry", "生化学 — the chemistry of living things: proteins, nucleic acids, metabolism.",
     ["chem:protein:collagen","chem:amino:glycine","chem:lipid:triglyceride","chem:carbo:glucose"], ["bio:biology","life:metabolism","bio:metabolism:metabolism"]),
   ("chem:branch:polymer_chemistry", "高分子化学 — long-chain molecules, from proteins and DNA to plastics and rubber.",
     ["chem:polymer:polyethylene","chem:polymer:nylon"], ["matsci","eng:branch:materials"]),
   ("chem:branch:electrochemistry", "電気化学 — chemical change driven by, or producing, electric current: batteries, corrosion, electrolysis.",
     [], ["phys:branch:electromagnetism","eleceng:current"]),
   ("chem:branch:environmental_chemistry", "環境化学 — chemical processes in air, water and soil, and human impact on them.",
     [], ["ecol","enveng"]),
  ],
  ["phys:physics","math"]),

 ("bio:biology",
  "生物学 — the science of living organisms: their structure, function, growth, heredity, evolution and interactions.",
  [
   ("bio:branch:molecular_biology", "分子生物学 — life at the molecular level: DNA, RNA, proteins and the central dogma.",
     ["life:dna","life:rna","life:gene","life:protein_synthesis","bio:concept:central_dogma"], ["chem:branch:biochemistry"]),
   ("bio:branch:cell_biology", "細胞生物学 — the cell, life's basic unit: membranes, organelles, division.",
     ["life:cell","life:cell_membrane","life:mitochondria","life:ribosome","life:nucleus_cell"], []),
   ("bio:branch:genetics", "遺伝学 — heredity and variation: genes, alleles, inheritance, genomics.",
     ["life:genetics","life:allele","life:heredity","life:genotype","life:phenotype","life:mutation","life:genomics"], ["life:gene_editing"]),
   ("bio:branch:evolution", "進化生物学 — how life diversifies over time: natural selection, common descent, speciation.",
     ["life:evolution","life:natural_selection","life:common_descent","life:speciation","life:phylogeny","life:adaptation","life:fitness"], ["crosscut:evolution"]),
   ("bio:branch:physiology", "生理学 — how living bodies work: the function of organs and systems.",
     ["bio:metabolism:metabolism","life:metabolism","life:cellular_respiration"], ["med:medicine"]),
   ("bio:branch:microbiology", "微生物学 — bacteria, viruses and other microbes.",
     ["life:microbiology","life:bacteria","life:virus","life:immunity"], []),
   ("bio:branch:botany", "植物学 — the biology of plants.",
     ["life:photosynthesis"], ["agron","ecol"]),
   ("bio:branch:zoology", "動物学 — the biology of animals.",
     [], ["ecol"]),
   ("bio:branch:ecology", "生態学 — organisms in relation to one another and their environment.",
     [], ["ecol","ecol:ecosystem","ecol:food_web"]),
   ("bio:branch:developmental_biology", "発生生物学 — how an organism grows from a single cell.",
     ["life:epigenetics"], ["bio:branch:genetics"]),
   ("bio:branch:neuroscience", "神経科学 — the nervous system and the biological basis of mind and behaviour.",
     [], ["neuro","knowledge:cognitive_science"]),
   ("bio:branch:biochemistry", "生化学 — the chemistry of life (shared with chemistry).",
     [], ["chem:branch:biochemistry"]),
  ],
  ["chem:chemistry","med:medicine"]),

 ("earthsci:earth_science",
  "地球科学 — the science of the Earth: its rocks, oceans, atmosphere, and the deep-time processes that shape them.",
  [
   ("earthsci:branch:geology", "地質学 — the solid Earth: rocks, minerals, structure and history.",
     ["earthsci:geology","earthsci:mineralogy","earthsci:rock_cycle","earthsci:stratigraphy","earthsci:plate_tectonics","earthsci:seismology","earthsci:volcanology","earthsci:geomorphology"], ["crosscut:cycle"]),
   ("earthsci:branch:meteorology", "気象学 — the atmosphere and weather.",
     [], ["weather:climate","phys:branch:thermodynamics"]),
   ("earthsci:branch:climatology", "気候学 — climate: long-term patterns of weather and their change.",
     [], ["ecol:carbon_cycle","enveng"]),
   ("earthsci:branch:oceanography", "海洋学 — the oceans: their water, currents, life and floor.",
     [], ["crosscut:cycle"]),
   ("earthsci:branch:hydrology", "水文学 — water on and under the land: rivers, groundwater, the water cycle.",
     [], ["crosscut:cycle","crosscut:system"]),
   ("earthsci:branch:paleontology", "古生物学 — ancient life read from fossils; the bridge to evolution and deep time.",
     [], ["bio:branch:evolution","archaeo"]),
  ],
  ["phys:physics","chem:chemistry","astrophys"]),

 ("astro:astronomy",
  "天文学 — the science of the heavens: the Sun, Moon, planets, stars, galaxies and the universe.",
  [
   ("astro:branch:planetary_science", "惑星科学 — the Sun's planets, moons and small bodies.",
     ["astrophys:exoplanet","astrophys:habitable_zone","astrophys:orbital_mechanics"], ["earthsci:earth_science"]),
   ("astro:branch:stellar_astrophysics", "恒星天文学 — the birth, life and death of stars.",
     ["astrophys:stellar_evolution","astrophys:nuclear_fusion","astrophys:supernova","astrophys:neutron_star","astrophys:black_hole","astrophys:nebula"], ["phys:branch:atomic_nuclear_particle"]),
   ("astro:branch:cosmology", "宇宙論 — the origin, structure and fate of the universe as a whole.",
     ["astrophys:cosmology","astrophys:big_bang","astrophys:cosmic_expansion","astrophys:cosmic_microwave_background","astrophys:dark_matter","astrophys:dark_energy","astrophys:redshift"], ["phys:branch:relativity"]),
   ("astro:branch:observational_astronomy", "観測天文学 — the instruments and methods of watching the sky: telescopes, spectroscopy.",
     ["astrophys:spectroscopy_astro","astrophys:light_year"], ["phys:branch:optics"]),
  ],
  ["phys:physics","phys:branch:astrophysics"]),
]

def build_natsci():
    L = [
      "# Akasha ontology — natural sciences: the general-education-level disciplinary map.",
      "# Names each natural-science discipline and its major branches, and cross-link (bridges)",
      "# the detailed atoms already in base3 (phys:law:*, chem:*, life:*, earthsci:*,",
      "# astrophys:*) under that spine. Wired into the knowledge_map capstone.",
      "# General-education breadth; research depth is reserved for level-C packs. Base pack.",
      "",
      'def "knowledge:branch:natural_science" "自然科学 — the study of nature."',
    ]
    for disc, gloss, branches, dbridges in NS:
        L.append("")
        L.append(f'def "{disc}" "{esc(gloss)}"')
        L.append(f"ln {disc} knowledge:branch:natural_science knowledge:in_branch")
        for b in dbridges:
            if b:
                L.append(f"ln {disc} {b} thesaurus:related")
        for bid, bgloss, kids, brs in branches:
            L.append(f'def "{bid}" "{esc(bgloss)}"')
            L.append(f"ln {bid} {disc} sys:part_of")
            for k in kids:
                if k:
                    L.append(f"ln {k} {bid} sys:part_of")
            for br in brs:
                if br:
                    L.append(f"ln {bid} {br} thesaurus:related")
    return L

# ─────────────────────────────────────────────────────────────────────────────
# ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────
# branches: (id, gloss, domain-hub token(s) to cross-link, applied science(s), sample atoms)
ENG_BRANCHES = [
 ("eng:branch:mechanical", "機械工学 — the design of machines, engines and moving structures: forces, motion, heat, materials.",
   ["mecheng"], ["phys:physics","phys:branch:classical_mechanics"],
   ["mecheng:statics","mecheng:dynamics","mecheng:thermodynamics","mecheng:fluid_mechanics","mecheng:heat_transfer","mecheng:machine_design","mecheng:mechanics_of_materials"]),
 ("eng:branch:electrical", "電気工学 — the generation, transmission and use of electric power.",
   ["eleceng"], ["phys:branch:electromagnetism"],
   ["eleceng:circuit","eleceng:ohms_law","eleceng:power_system","eleceng:motor","eleceng:generator","eleceng:transformer"]),
 ("eng:branch:electronic", "電子工学 — circuits and devices that process signals and information: semiconductors, chips.",
   ["electron"], ["phys:branch:electromagnetism","phys:branch:quantum_mechanics"],
   []),
 ("eng:branch:civil", "土木工学 — the built environment: buildings, bridges, roads, dams, water and sanitation.",
   ["ce"], ["phys:branch:classical_mechanics"],
   []),
 ("eng:branch:chemical", "化学工学 — turning raw materials into products at scale: reactions, separations, process design.",
   ["chemeng"], ["chem:chemistry","chem:branch:physical_chemistry"],
   ["chemeng:distillation","chemeng:reactor","chemeng:mass_balance","chemeng:heat_exchanger","chemeng:process_design","chemeng:unit_operations"]),
 ("eng:branch:materials", "材料工学 — designing materials for purpose: metals, ceramics, polymers, composites.",
   ["matsci"], ["chem:chemistry","phys:branch:condensed_matter"],
   []),
 ("eng:branch:aerospace", "航空宇宙工学 — flight and space: aerodynamics, propulsion, structures, orbits.",
   [], ["phys:branch:classical_mechanics","phys:branch:thermodynamics"],
   ["phys:aero:thrust","astrophys:orbital_mechanics"]),
 ("eng:branch:biomedical", "生体医工学 — engineering for medicine: prosthetics, imaging, biomaterials, devices.",
   ["bme"], ["bio:biology","med:medicine"],
   []),
 ("eng:branch:computer", "計算機工学・ソフトウェア工学 — the design of computing hardware and software systems.",
   ["cs"], ["math","knowledge:branch:formal_science"],
   ["cs:algorithm"]),
 ("eng:branch:environmental", "環境工学 — protecting and remediating air, water and land; sustainable systems.",
   ["enveng"], ["chem:branch:environmental_chemistry","ecol"],
   []),
 ("eng:branch:industrial", "経営・生産工学 — designing and optimising processes, production and systems of work.",
   ["mfg"], ["math:statistics"],
   ["crosscut:optimization"]),
 ("eng:branch:control_robotics", "制御・ロボット工学・メカトロニクス — feedback, automation, and machines that sense and act.",
   ["ctrl","robotics","mecha"], ["math"],
   ["mecheng:mechatronics","eleceng:control_system","crosscut:feedback"]),
 ("eng:branch:energy", "エネルギー工学 — generating, storing and delivering power, from fuels to renewables to nuclear.",
   ["energy"], ["phys:branch:thermodynamics"],
   ["astrophys:nuclear_fusion","crosscut:energy"]),
]

# cross-cutting engineering concepts
ENG_CONCEPTS = [
 ("eng:concept:design", "設計 — conceiving a structure or device to meet a need under constraints.", ["crosscut:optimization"]),
 ("eng:concept:constraint", "制約 — the limits (cost, weight, safety, material) a design must satisfy.", ["crosscut:scarcity"]),
 ("eng:concept:safety_factor", "安全率 — building in margin so a design holds well beyond its rated load.", ["mecheng:stress"]),
 ("eng:concept:efficiency", "効率 — useful output per unit of input; a central engineering measure.", ["crosscut:energy","crosscut:optimization"]),
 ("eng:concept:tolerance", "公差 — the allowed deviation in a manufactured dimension.", ["mecheng:tolerance"]),
 ("eng:concept:standardization", "標準化 — shared specifications that make parts and systems interoperable.", ["crosscut:system"]),
 ("eng:concept:systems_thinking", "システム思考 — designing the whole, not just the parts, and their interactions.", ["crosscut:system","crosscut:feedback"]),
 ("eng:concept:trade_off", "トレードオフ — improving one property at the expense of another; the heart of engineering judgement.", ["crosscut:optimization"]),
]

def build_eng():
    L = [
      "# Akasha ontology — engineering: the general-education-level disciplinary map.",
      "# Names the main branches of engineering, cross-link (bridges) the detailed atoms already",
      "# in base3 (mecheng:*, eleceng:*, chemeng:*, matsci:* …) under that spine, makes the",
      "# science→engineering bridge explicit (eng:applies), and defines the shared craft",
      "# concepts. Wired into the knowledge_map capstone (knowledge:branch:applied_science).",
      "# General-education breadth; research depth is reserved for level-C packs. Base pack.",
      "",
      'def "knowledge:branch:applied_science" "応用科学・工学 — knowledge applied to practical ends."',
      'def "eng:engineering" "工学 — the disciplined application of scientific and mathematical knowledge to design, build and improve practical things."',
      "ln eng:engineering knowledge:branch:applied_science knowledge:in_branch",
      "ln eng:engineering knowledge:branch:natural_science thesaurus:related",
    ]
    # domain-hub atoms that the knowledge map needs but that were never defined
    # as bare tokens (unlike ecol/matsci/mecheng/…). Define them here, glossed and
    # anchored to a representative existing atom, so the hub layer is complete.
    NEW_HUBS = [
      ("ce", "土木工学 — civil engineering: the built environment (structures, transport, water).", "ce:bridge_engineering"),
      ("energy", "エネルギー工学 — energy systems: generation, storage, distribution.", "energy:battery_storage"),
      ("ctrl", "制御工学 — control engineering: feedback, stability, automation.", "ctrl:bode_design"),
      ("robotics", "ロボット工学 — robotics: kinematics, sensing and autonomous action.", "robotics:forward_kinematics"),
      ("mecha", "メカトロニクス — mechatronics: the fusion of mechanical, electronic and software systems.", "mecha:encoder"),
      ("mfg", "生産工学 — manufacturing and production engineering.", "mfg:capacity_planning"),
    ]
    for hid, hgloss, child in NEW_HUBS:
        L.append(f'def "{hid}" "{esc(hgloss)}"')
        L.append(f"ln {hid} knowledge:branch:applied_science knowledge:in_branch")
        L.append(f"ln {child} {hid} sys:part_of")
    for bid, gloss, hubs, applies, atoms in ENG_BRANCHES:
        L.append("")
        L.append(f'def "{bid}" "{esc(gloss)}"')
        L.append(f"ln {bid} eng:engineering sys:part_of")
        L.append(f"ln {bid} knowledge:branch:applied_science knowledge:in_branch")
        for h in hubs:
            if h:
                L.append(f"ln {bid} {h} thesaurus:related")
        for a in applies:
            if a:
                L.append(f"ln {bid} {a} eng:applies")
        for at in atoms:
            if at:
                L.append(f"ln {at} {bid} sys:part_of")
    L.append("")
    L.append("# ── the shared craft: cross-cutting engineering concepts ──")
    L.append('def "eng:concept" "The shared ideas of the engineering craft, common to every branch (工学の共通概念)."')
    L.append("ln eng:concept eng:engineering sys:part_of")
    for cid, gloss, brs in ENG_CONCEPTS:
        L.append(f'def "{cid}" "{esc(gloss)}"')
        L.append(f"ln {cid} eng:concept sys:part_of")
        for br in brs:
            if br:
                L.append(f"ln {cid} {br} thesaurus:related")
    return L

emit(build_natsci(), "app/ontology/base3/natural_sciences.ak")
emit(build_eng(), "app/ontology/base3/engineering.ak")
