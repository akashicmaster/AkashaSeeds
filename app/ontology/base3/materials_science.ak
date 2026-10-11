# Akasha ontology — materials science.
# The classes, structure, properties and processing of materials. Bridged to
# chem:/geo:mineral/electron:/bme:/mecheng:. Base pack.

def "matsci" "Materials science — the structure, properties and processing of materials (材料科学)."
# ── material classes ──
def "matsci:metal" "An opaque, ductile, conductive material (金属)."
ln matsci:metal matsci thesaurus:related
ln matsci:metal geo:mineral:pyrite thesaurus:related
def "matsci:alloy" "A metal blended with other elements for improved properties (合金)."
ln matsci:alloy matsci thesaurus:related
def "matsci:ceramic" "A hard, brittle, heat-resistant inorganic material (セラミックス)."
ln matsci:ceramic matsci thesaurus:related
ln matsci:ceramic geo:mineral:corundum thesaurus:related
def "matsci:polymer" "A material of long repeating molecular chains — plastics, rubbers (高分子/ポリマー)."
ln matsci:polymer matsci thesaurus:related
ln matsci:polymer mn:polymer thesaurus:related
ln matsci:polymer matsci:composite thesaurus:related
def "matsci:composite" "A material combining two or more constituents for synergy (複合材料)."
ln matsci:composite matsci thesaurus:related
def "matsci:semiconductor" "A material of controllable conductivity, basis of electronics (半導体)."
ln matsci:semiconductor matsci thesaurus:related
ln matsci:semiconductor electron:semiconductor thesaurus:related
ln matsci:semiconductor electron:transistor thesaurus:related
def "matsci:glass" "An amorphous (non-crystalline) solid (ガラス)."
ln matsci:glass matsci thesaurus:related
ln matsci:glass foodsci:glass_transition thesaurus:related
def "matsci:biomaterial" "A material designed to work with living tissue (生体材料)."
ln matsci:biomaterial matsci thesaurus:related
ln matsci:biomaterial bme:biomaterial thesaurus:related
ln matsci:biomaterial bme:implant thesaurus:related
def "matsci:nanomaterial" "A material structured at the nanometre scale (ナノ材料)."
ln matsci:nanomaterial matsci thesaurus:related
# ── properties, structure & processing ──
def "matsci:mechanical_property" "How a material responds to force — strength, stiffness, toughness."
ln matsci:mechanical_property matsci thesaurus:related
ln matsci:mechanical_property mecheng:mechanics_of_materials thesaurus:related
ln matsci:mechanical_property mecheng:stress thesaurus:related
def "matsci:tensile_strength" "The stress a material bears before breaking in tension (引張強度)."
ln matsci:tensile_strength matsci thesaurus:related
ln matsci:tensile_strength mecheng:stress thesaurus:related
def "matsci:hardness" "Resistance to indentation and scratching (硬度)."
ln matsci:hardness matsci thesaurus:related
ln matsci:hardness geo:mineral:corundum thesaurus:related
ln matsci:hardness geo:mineral:diamond thesaurus:related
def "matsci:ductility" "The ability to deform plastically without fracture (延性)."
ln matsci:ductility matsci thesaurus:related
def "matsci:elasticity" "The ability to return to shape after load."
ln matsci:elasticity matsci thesaurus:related
def "matsci:electrical_conductivity" "How readily a material carries current."
ln matsci:electrical_conductivity matsci thesaurus:related
ln matsci:electrical_conductivity eleceng:resistance thesaurus:related
ln matsci:electrical_conductivity matsci:semiconductor thesaurus:related
def "matsci:corrosion" "Chemical degradation of a material, esp. metal rusting (腐食)."
ln matsci:corrosion matsci thesaurus:related
ln matsci:corrosion matsci:metal thesaurus:related
def "matsci:crystal_structure" "The ordered lattice arrangement of atoms (結晶構造)."
ln matsci:crystal_structure matsci thesaurus:related
ln matsci:crystal_structure geo:mineral:quartz thesaurus:related
ln matsci:crystal_structure geo:mineral:diamond thesaurus:related
def "matsci:microstructure" "The fine structure (grains, phases) governing properties (微細組織)."
ln matsci:microstructure matsci thesaurus:related
def "matsci:phase_diagram" "A map of stable phases vs composition and temperature (状態図)."
ln matsci:phase_diagram matsci thesaurus:related
def "matsci:heat_treatment" "Altering properties by controlled heating and cooling (熱処理)."
ln matsci:heat_treatment matsci thesaurus:related
def "matsci:annealing" "Softening and relieving stress by controlled cooling (焼きなまし)."
ln matsci:annealing matsci thesaurus:related
def "matsci:sintering" "Bonding powder into a solid by heat below melting (焼結)."
ln matsci:sintering matsci thesaurus:related
def "matsci:materials_characterization" "Measuring structure and properties (microscopy, XRD, spectroscopy)."
ln matsci:materials_characterization matsci thesaurus:related
ln matsci:materials_characterization bme:medical_imaging thesaurus:related
