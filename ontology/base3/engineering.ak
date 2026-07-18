# Akasha ontology — engineering: the general-education-level disciplinary map.
# Names the main branches of engineering, cross-link (bridges) the detailed atoms already
# in base3 (mecheng:*, eleceng:*, chemeng:*, matsci:* …) under that spine, makes the
# science→engineering bridge explicit (eng:applies), and defines the shared craft
# concepts. Wired into the knowledge_map capstone (knowledge:branch:applied_science).
# General-education breadth; research depth is reserved for level-C packs. Base pack.

def "knowledge:branch:applied_science" "応用科学・工学 — knowledge applied to practical ends."
def "eng:engineering" "工学 — the disciplined application of scientific and mathematical knowledge to design, build and improve practical things."
ln eng:engineering knowledge:branch:applied_science knowledge:in_branch
ln eng:engineering knowledge:branch:natural_science thesaurus:related
def "ce" "土木工学 — civil engineering: the built environment (structures, transport, water)."
ln ce knowledge:branch:applied_science knowledge:in_branch
ln ce:bridge_engineering ce sys:part_of
def "energy" "エネルギー工学 — energy systems: generation, storage, distribution."
ln energy knowledge:branch:applied_science knowledge:in_branch
ln energy:battery_storage energy sys:part_of
def "ctrl" "制御工学 — control engineering: feedback, stability, automation."
ln ctrl knowledge:branch:applied_science knowledge:in_branch
ln ctrl:bode_design ctrl sys:part_of
def "robotics" "ロボット工学 — robotics: kinematics, sensing and autonomous action."
ln robotics knowledge:branch:applied_science knowledge:in_branch
ln robotics:forward_kinematics robotics sys:part_of
def "mecha" "メカトロニクス — mechatronics: the fusion of mechanical, electronic and software systems."
ln mecha knowledge:branch:applied_science knowledge:in_branch
ln mecha:encoder mecha sys:part_of
def "mfg" "生産工学 — manufacturing and production engineering."
ln mfg knowledge:branch:applied_science knowledge:in_branch
ln mfg:capacity_planning mfg sys:part_of

def "eng:branch:mechanical" "機械工学 — the design of machines, engines and moving structures: forces, motion, heat, materials."
ln eng:branch:mechanical eng:engineering sys:part_of
ln eng:branch:mechanical knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:mechanical mecheng thesaurus:related
ln eng:branch:mechanical phys:physics eng:applies
ln eng:branch:mechanical phys:branch:classical_mechanics eng:applies
ln mecheng:statics eng:branch:mechanical sys:part_of
ln mecheng:dynamics eng:branch:mechanical sys:part_of
ln mecheng:thermodynamics eng:branch:mechanical sys:part_of
ln mecheng:fluid_mechanics eng:branch:mechanical sys:part_of
ln mecheng:heat_transfer eng:branch:mechanical sys:part_of
ln mecheng:machine_design eng:branch:mechanical sys:part_of
ln mecheng:mechanics_of_materials eng:branch:mechanical sys:part_of

def "eng:branch:electrical" "電気工学 — the generation, transmission and use of electric power."
ln eng:branch:electrical eng:engineering sys:part_of
ln eng:branch:electrical knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:electrical eleceng thesaurus:related
ln eng:branch:electrical phys:branch:electromagnetism eng:applies
ln eleceng:circuit eng:branch:electrical sys:part_of
ln eleceng:ohms_law eng:branch:electrical sys:part_of
ln eleceng:power_system eng:branch:electrical sys:part_of
ln eleceng:motor eng:branch:electrical sys:part_of
ln eleceng:generator eng:branch:electrical sys:part_of
ln eleceng:transformer eng:branch:electrical sys:part_of

def "eng:branch:electronic" "電子工学 — circuits and devices that process signals and information: semiconductors, chips."
ln eng:branch:electronic eng:engineering sys:part_of
ln eng:branch:electronic knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:electronic electron thesaurus:related
ln eng:branch:electronic phys:branch:electromagnetism eng:applies
ln eng:branch:electronic phys:branch:quantum_mechanics eng:applies

def "eng:branch:civil" "土木工学 — the built environment: buildings, bridges, roads, dams, water and sanitation."
ln eng:branch:civil eng:engineering sys:part_of
ln eng:branch:civil knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:civil ce thesaurus:related
ln eng:branch:civil phys:branch:classical_mechanics eng:applies

def "eng:branch:chemical" "化学工学 — turning raw materials into products at scale: reactions, separations, process design."
ln eng:branch:chemical eng:engineering sys:part_of
ln eng:branch:chemical knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:chemical chemeng thesaurus:related
ln eng:branch:chemical chem:chemistry eng:applies
ln eng:branch:chemical chem:branch:physical_chemistry eng:applies
ln chemeng:distillation eng:branch:chemical sys:part_of
ln chemeng:reactor eng:branch:chemical sys:part_of
ln chemeng:mass_balance eng:branch:chemical sys:part_of
ln chemeng:heat_exchanger eng:branch:chemical sys:part_of
ln chemeng:process_design eng:branch:chemical sys:part_of
ln chemeng:unit_operations eng:branch:chemical sys:part_of

def "eng:branch:materials" "材料工学 — designing materials for purpose: metals, ceramics, polymers, composites."
ln eng:branch:materials eng:engineering sys:part_of
ln eng:branch:materials knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:materials matsci thesaurus:related
ln eng:branch:materials chem:chemistry eng:applies
ln eng:branch:materials phys:branch:condensed_matter eng:applies

def "eng:branch:aerospace" "航空宇宙工学 — flight and space: aerodynamics, propulsion, structures, orbits."
ln eng:branch:aerospace eng:engineering sys:part_of
ln eng:branch:aerospace knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:aerospace phys:branch:classical_mechanics eng:applies
ln eng:branch:aerospace phys:branch:thermodynamics eng:applies
ln phys:aero:thrust eng:branch:aerospace sys:part_of
ln astrophys:orbital_mechanics eng:branch:aerospace sys:part_of

def "eng:branch:biomedical" "生体医工学 — engineering for medicine: prosthetics, imaging, biomaterials, devices."
ln eng:branch:biomedical eng:engineering sys:part_of
ln eng:branch:biomedical knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:biomedical bme thesaurus:related
ln eng:branch:biomedical bio:biology eng:applies
ln eng:branch:biomedical med:medicine eng:applies

def "eng:branch:computer" "計算機工学・ソフトウェア工学 — the design of computing hardware and software systems."
ln eng:branch:computer eng:engineering sys:part_of
ln eng:branch:computer knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:computer cs thesaurus:related
ln eng:branch:computer math eng:applies
ln eng:branch:computer knowledge:branch:formal_science eng:applies
ln cs:algorithm eng:branch:computer sys:part_of

def "eng:branch:environmental" "環境工学 — protecting and remediating air, water and land; sustainable systems."
ln eng:branch:environmental eng:engineering sys:part_of
ln eng:branch:environmental knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:environmental enveng thesaurus:related
ln eng:branch:environmental chem:branch:environmental_chemistry eng:applies
ln eng:branch:environmental ecol eng:applies

def "eng:branch:industrial" "経営・生産工学 — designing and optimising processes, production and systems of work."
ln eng:branch:industrial eng:engineering sys:part_of
ln eng:branch:industrial knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:industrial mfg thesaurus:related
ln eng:branch:industrial math:statistics eng:applies
ln crosscut:optimization eng:branch:industrial sys:part_of

def "eng:branch:control_robotics" "制御・ロボット工学・メカトロニクス — feedback, automation, and machines that sense and act."
ln eng:branch:control_robotics eng:engineering sys:part_of
ln eng:branch:control_robotics knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:control_robotics ctrl thesaurus:related
ln eng:branch:control_robotics robotics thesaurus:related
ln eng:branch:control_robotics mecha thesaurus:related
ln eng:branch:control_robotics math eng:applies
ln mecheng:mechatronics eng:branch:control_robotics sys:part_of
ln eleceng:control_system eng:branch:control_robotics sys:part_of
ln crosscut:feedback eng:branch:control_robotics sys:part_of

def "eng:branch:energy" "エネルギー工学 — generating, storing and delivering power, from fuels to renewables to nuclear."
ln eng:branch:energy eng:engineering sys:part_of
ln eng:branch:energy knowledge:branch:applied_science knowledge:in_branch
ln eng:branch:energy energy thesaurus:related
ln eng:branch:energy phys:branch:thermodynamics eng:applies
ln astrophys:nuclear_fusion eng:branch:energy sys:part_of
ln crosscut:energy eng:branch:energy sys:part_of

# ── the shared craft: cross-cutting engineering concepts ──
def "eng:concept" "The shared ideas of the engineering craft, common to every branch (工学の共通概念)."
ln eng:concept eng:engineering sys:part_of
def "eng:concept:design" "設計 — conceiving a structure or device to meet a need under constraints."
ln eng:concept:design eng:concept sys:part_of
ln eng:concept:design crosscut:optimization thesaurus:related
def "eng:concept:constraint" "制約 — the limits (cost, weight, safety, material) a design must satisfy."
ln eng:concept:constraint eng:concept sys:part_of
ln eng:concept:constraint crosscut:scarcity thesaurus:related
def "eng:concept:safety_factor" "安全率 — building in margin so a design holds well beyond its rated load."
ln eng:concept:safety_factor eng:concept sys:part_of
ln eng:concept:safety_factor mecheng:stress thesaurus:related
def "eng:concept:efficiency" "効率 — useful output per unit of input; a central engineering measure."
ln eng:concept:efficiency eng:concept sys:part_of
ln eng:concept:efficiency crosscut:energy thesaurus:related
ln eng:concept:efficiency crosscut:optimization thesaurus:related
def "eng:concept:tolerance" "公差 — the allowed deviation in a manufactured dimension."
ln eng:concept:tolerance eng:concept sys:part_of
ln eng:concept:tolerance mecheng:tolerance thesaurus:related
def "eng:concept:standardization" "標準化 — shared specifications that make parts and systems interoperable."
ln eng:concept:standardization eng:concept sys:part_of
ln eng:concept:standardization crosscut:system thesaurus:related
def "eng:concept:systems_thinking" "システム思考 — designing the whole, not just the parts, and their interactions."
ln eng:concept:systems_thinking eng:concept sys:part_of
ln eng:concept:systems_thinking crosscut:system thesaurus:related
ln eng:concept:systems_thinking crosscut:feedback thesaurus:related
def "eng:concept:trade_off" "トレードオフ — improving one property at the expense of another; the heart of engineering judgement."
ln eng:concept:trade_off eng:concept sys:part_of
ln eng:concept:trade_off crosscut:optimization thesaurus:related
