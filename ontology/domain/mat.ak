# Akasha ontology — namespace: mat
# atoms: 19

def "mat:class:ceramic" "An inorganic, non-metallic, often crystalline oxide, nitride or carbide material."
ln mat:class:ceramic chem:bond:ionic_bond @utilizes
ln mat:class:ceramic chem:bond:covalent_bond @utilizes
ln mat:class:ceramic prop:phys:brittleness @exhibits

def "mat:class:composite" "A material made from two or more constituent materials with significantly different physical or chemical properties."

def "mat:class:metal" "A material that is typically hard, opaque, shiny, and features good electrical and thermal conductivity."
ln mat:class:metal prop:phys:electrical_conductivity @exhibits
ln mat:class:metal prop:phys:malleability @exhibits

def "mat:class:semiconductor" "A material which has electrical conductivity between that of a conductor and an insulator."

def "mat:crystal:amorphous" "A non-crystalline solid that lacks a well-defined long-range order."

def "mat:crystal:grain_boundary" "The interface where two crystals (grains) of the same phase meet in a polycrystalline material."
ln mat:crystal:grain_boundary mat:prop:yield_strength @increases

def "mat:crystal:unit_cell" "The smallest repeating spatial unit of a crystal lattice."

def "mat:failure:creep" "The tendency of a solid material to move slowly or deform permanently under the influence of persistent mechanical stresses."

def "mat:failure:fatigue" "The weakening of a material caused by repeatedly applied loads."
ln mat:failure:fatigue mat:prop:stress @driven_by

def "mat:process:annealing" "A heat treatment that alters the physical and sometimes chemical properties of a material to increase its ductility and reduce its hardness."
ln mat:process:annealing prop:phys:ductility @increases
ln mat:process:annealing mat:prop:hardness @decreases

def "mat:process:quenching" "The rapid cooling of a workpiece to obtain certain material properties, like increased hardness in steel."
ln mat:process:quenching mat:prop:hardness @increases
ln mat:process:quenching prop:phys:brittleness @increases

def "mat:process:sintering" "The process of compacting and forming a solid mass of material by heat or pressure without melting it to the point of liquefaction."

def "mat:process:work_hardening" "The strengthening of a metal or polymer by plastic deformation."
ln mat:process:work_hardening mat:prop:yield_strength @increases
ln mat:process:work_hardening prop:phys:ductility @decreases
ln mat:process:work_hardening mat:crystal:grain_boundary @generates

def "mat:prop:hardness" "A measure of the resistance to localized plastic deformation induced by either mechanical indentation or abrasion."

def "mat:prop:strain" "The relative deformation or change in shape and size of a material under stress."

def "mat:prop:stress" "The internal restoring force per unit area within a material undergoing deformation."
ln mat:prop:stress phys:force:force @derived_from

def "mat:prop:toughness" "The ability of a material to absorb energy and deform plastically before fracturing."

def "mat:prop:yield_strength" "The stress at which a specific amount of plastic deformation is produced."

def "mat:prop:youngs_modulus" "A mechanical property that measures the tensile or compressive stiffness of a solid material."
ln mat:prop:youngs_modulus mat:prop:stress @relates_to
ln mat:prop:youngs_modulus mat:prop:strain @relates_to
