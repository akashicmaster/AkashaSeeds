# Akasha ontology — namespace: chem
# atoms: 327

def "chem:amino:alanine" "A simple, non-polar amino acid."
ln chem:amino:alanine chem:amino:amino_acid sys:is_a

def "chem:amino:amino_acid" "An organic compound containing both an amino group (-NH₂) and a carboxyl group (-COOH); the monomer units of proteins."

def "chem:amino:arginine" "A basic, positively charged amino acid with a guanidino group."
ln chem:amino:arginine chem:amino:amino_acid sys:is_a
ln chem:amino:arginine nutri:concept:conditionally_essential_amino_acid sys:is_a

def "chem:amino:asparagine" "A polar amino acid containing an amide group."
ln chem:amino:asparagine chem:amino:amino_acid sys:is_a

def "chem:amino:aspartic_acid" "An acidic, negatively charged amino acid."
ln chem:amino:aspartic_acid chem:amino:amino_acid sys:is_a
ln chem:amino:aspartic_acid prop:chem:acidic @has_property
ln chem:amino:aspartic_acid chem:func:carboxyl @contains

def "chem:amino:glutamic_acid" "An acidic, negatively charged amino acid, source of umami flavor."
ln chem:amino:glutamic_acid chem:amino:amino_acid sys:is_a

def "chem:amino:glutamine" "A polar amino acid with an amide side chain."
ln chem:amino:glutamine chem:amino:amino_acid sys:is_a
ln chem:amino:glutamine nutri:concept:conditionally_essential_amino_acid sys:is_a

def "chem:amino:glycine" "The simplest amino acid, side chain is a single hydrogen."
ln chem:amino:glycine chem:amino:amino_acid sys:is_a
ln chem:amino:glycine prop:chem:nonpolar @has_property

def "chem:amino:histidine" "A basic amino acid that can be neutral or positive depending on pH."
ln chem:amino:histidine chem:amino:amino_acid sys:is_a
ln chem:amino:histidine nutri:concept:essential_amino_acid sys:is_a

def "chem:amino:isoleucine" "An isomer of leucine, non-polar and hydrophobic."
ln chem:amino:isoleucine chem:amino:amino_acid sys:is_a
ln chem:amino:isoleucine nutri:concept:essential_amino_acid sys:is_a
ln chem:amino:isoleucine nutri:concept:bcaa sys:is_a

def "chem:amino:leucine" "A hydrophobic amino acid essential for protein synthesis."
ln chem:amino:leucine chem:amino:amino_acid sys:is_a
ln chem:amino:leucine nutri:concept:essential_amino_acid sys:is_a
ln chem:amino:leucine nutri:concept:bcaa sys:is_a

def "chem:amino:lysine" "A basic, positively charged amino acid."
ln chem:amino:lysine chem:amino:amino_acid sys:is_a
ln chem:amino:lysine prop:chem:basic @has_property
ln chem:amino:lysine chem:func:amino @contains
ln chem:amino:lysine nutri:concept:essential_amino_acid sys:is_a

def "chem:amino:methionine" "A sulfur-containing, non-polar amino acid; often the start codon."
ln chem:amino:methionine chem:amino:amino_acid sys:is_a
ln chem:amino:methionine nutri:concept:essential_amino_acid sys:is_a

def "chem:amino:phenylalanine" "A non-polar amino acid with a phenyl ring."
ln chem:amino:phenylalanine chem:amino:amino_acid sys:is_a
ln chem:amino:phenylalanine nutri:concept:essential_amino_acid sys:is_a
ln chem:amino:phenylalanine nutri:role:neurotransmitter_precursor @acts_as
ln chem:amino:phenylalanine bio:neurotransmitter:dopamine @precursor_of

def "chem:amino:proline" "A unique amino acid where the side chain is cyclic, restricting backbone flexibility."
ln chem:amino:proline chem:amino:amino_acid sys:is_a
ln chem:amino:proline prop:chem:polar @contrasts_with

def "chem:amino:serine" "A polar amino acid containing a hydroxyl group."
ln chem:amino:serine chem:amino:amino_acid sys:is_a
ln chem:amino:serine prop:chem:hydrophilic @has_property
ln chem:amino:serine chem:func:hydroxyl @contains

def "chem:amino:threonine" "A polar amino acid with a hydroxyl group."
ln chem:amino:threonine chem:amino:amino_acid sys:is_a
ln chem:amino:threonine nutri:concept:essential_amino_acid sys:is_a

def "chem:amino:tryptophan" "A bulky, hydrophobic amino acid with an indole group."
ln chem:amino:tryptophan chem:amino:amino_acid sys:is_a
ln chem:amino:tryptophan nutri:concept:essential_amino_acid sys:is_a
ln chem:amino:tryptophan nutri:role:neurotransmitter_precursor @acts_as
ln chem:amino:tryptophan bio:neurotransmitter:serotonin @precursor_of

def "chem:amino:tyrosine" "A polar amino acid with a phenolic hydroxyl group."
ln chem:amino:tyrosine chem:amino:amino_acid sys:is_a
ln chem:amino:tyrosine bio:hormone:adrenaline @precursor_of
ln chem:amino:tyrosine bio:neurotransmitter:dopamine @precursor_of

def "chem:amino:valine" "A branched-chain, non-polar amino acid."
ln chem:amino:valine chem:amino:amino_acid sys:is_a
ln chem:amino:valine prop:chem:hydrophobic @has_property
ln chem:amino:valine nutri:concept:essential_amino_acid sys:is_a
ln chem:amino:valine nutri:concept:bcaa sys:is_a

def "chem:analytical:ir_spectroscopy" "The measurement of the interaction of infrared radiation with matter by absorption, emission, or reflection; used to identify functional groups."
ln chem:analytical:ir_spectroscopy phys:spectrum:infrared @utilizes
ln chem:analytical:ir_spectroscopy phys:phenomenon:molecular_vibration @measures
ln chem:analytical:ir_spectroscopy chem:func:hydroxyl @detects
ln chem:analytical:ir_spectroscopy chem:func:carbonyl @detects
ln chem:analytical:ir_spectroscopy chem:func:amino @detects

def "chem:analytical:nmr_spectroscopy" "Nuclear magnetic resonance spectroscopy; a technique used to determine the structure of organic compounds by measuring the magnetic environment of specific nuclei."
ln chem:analytical:nmr_spectroscopy phys:spectrum:radio_wave @utilizes
ln chem:analytical:nmr_spectroscopy phys:phenomenon:nuclear_spin @measures
ln chem:analytical:nmr_spectroscopy chem:element:hydrogen @detects
ln chem:analytical:nmr_spectroscopy chem:element:carbon @detects

def "chem:analytical:raman_spectroscopy" "A spectroscopic technique based on inelastic scattering of monochromatic light, used to observe vibrational, rotational, and other low-frequency modes."

def "chem:analytical:uv_vis_spectroscopy" "Absorption spectroscopy in the ultraviolet-visible spectral region, used to quantify conjugated systems and transition metal complexes."
ln chem:analytical:uv_vis_spectroscopy phys:spectrum:ultraviolet @utilizes
ln chem:analytical:uv_vis_spectroscopy phys:spectrum:visible_light @utilizes
ln chem:analytical:uv_vis_spectroscopy phys:optics:absorption @measures
ln chem:analytical:uv_vis_spectroscopy phys:optics:conjugation @detects

def "chem:analytical:x_ray_crystallography" "A technique used for determining the atomic and molecular structure of a crystal, in which the crystalline structure causes a beam of incident X-rays to diffract."
ln chem:analytical:x_ray_crystallography phys:spectrum:x_ray @utilizes

def "chem:bond:covalent_bond" "A chemical bond that involves the sharing of electron pairs between atoms."
ln chem:bond:covalent_bond chem_quant.bonding sys:is_a
ln chem:bond:covalent_bond chem:orbital:molecular_orbital @forms
set.add name="ontology.quantum_chemistry" id="chem:bond:covalent_bond"

def "chem:bond:disulfide_bond" "A covalent bond derived from two thiol groups, crucial for stabilizing tertiary and quaternary structures."
ln chem:bond:disulfide_bond chem:structure:tertiary @stabilizes
ln chem:bond:disulfide_bond chem:compound:cysteine @derived_from

def "chem:bond:glycosidic_bond" "A type of covalent bond that joins a carbohydrate molecule to another group, which may or may not be another carbohydrate."

def "chem:bond:hydrogen_bond" "A primarily electrostatic force of attraction between a hydrogen atom covalently bound to a more electronegative atom or group."
ln chem:bond:hydrogen_bond prop:phys:boiling_point @elevates

def "chem:bond:ionic_bond" "A type of chemical bonding that involves the electrostatic attraction between oppositely charged ions."
ln chem:bond:ionic_bond chem_quant.bonding sys:is_a
ln chem:bond:ionic_bond prop:phys:brittleness @causes
set.add name="ontology.quantum_chemistry" id="chem:bond:ionic_bond"

def "chem:bond:pi_bond" "Covalent chemical bonds where two lobes of an orbital on one atom overlap two lobes of an orbital on another atom."
ln chem:bond:pi_bond chem_quant.bonding sys:is_a
ln chem:bond:pi_bond chem:orbital:p_orbital @utilizes
set.add name="ontology.quantum_chemistry" id="chem:bond:pi_bond"

def "chem:bond:sigma_bond" "The strongest type of covalent chemical bond, formed by head-on overlapping between atomic orbitals."
ln chem:bond:sigma_bond chem_quant.bonding sys:is_a
ln chem:bond:sigma_bond chem:orbital:s_orbital @utilizes
set.add name="ontology.quantum_chemistry" id="chem:bond:sigma_bond"

def "chem:bond:sp2_hybridization" "The mixing of one s and two p orbitals to form three identical sp2 hybrid orbitals (trigonal planar)."
ln chem:bond:sp2_hybridization chem_quant.bonding sys:is_a
ln chem:bond:sp2_hybridization chem:bond:pi_bond @enables
set.add name="ontology.quantum_chemistry" id="chem:bond:sp2_hybridization"

def "chem:bond:sp3_hybridization" "The mixing of one s and three p orbitals to form four identical sp3 hybrid orbitals (tetrahedral)."
ln chem:bond:sp3_hybridization chem_quant.bonding sys:is_a
ln chem:bond:sp3_hybridization chem:bond:sigma_bond @enables
set.add name="ontology.quantum_chemistry" id="chem:bond:sp3_hybridization"

def "chem:bond:van_der_waals_force" "Distance-dependent interactions between atoms or molecules, weaker than covalent or ionic bonds."

def "chem:carbo:carbohydrate" "A biomolecule consisting of carbon, hydrogen and oxygen atoms, usually with a hydrogen-oxygen atom ratio of 2:1."
ln chem:carbo:carbohydrate med:condition:diabetes @associated_with
ln chem:carbo:carbohydrate nutri:concept:macronutrient sys:is_a

def "chem:carbo:disaccharide" "A sugar formed when two monosaccharides are joined by a glycosidic linkage."
ln chem:carbo:disaccharide chem:bond:glycosidic_bond @utilizes

def "chem:carbo:fructose" "A simple ketonic monosaccharide found in many plants, where it is often bonded to glucose to form sucrose."
ln chem:carbo:fructose chem:carbo:monosaccharide sys:is_a
ln chem:carbo:fructose dna:taste:sweet calc:associated_with

def "chem:carbo:galactose" "A monosaccharide sugar that is about as sweet as glucose, often found combined with glucose to form lactose."
ln chem:carbo:galactose chem:carbo:monosaccharide sys:is_a

def "chem:carbo:glucose" "A simple sugar and an important energy source in living organisms, widely found in nature."
ln chem:carbo:glucose chem:carbo:monosaccharide sys:is_a
ln chem:carbo:glucose bio:role:energy_source @acts_as

def "chem:carbo:glycogen" "A multibranched polysaccharide of glucose that serves as a form of energy storage in animals and fungi."
ln chem:carbo:glycogen chem:carbo:polysaccharide sys:is_a
ln chem:carbo:glycogen chem:carbo:glucose @composed_of

def "chem:carbo:lactose" "A disaccharide sugar synthesized by galactose and glucose subunits, present in milk."
ln chem:carbo:lactose chem:carbo:disaccharide sys:is_a
ln chem:carbo:lactose chem:carbo:glucose @contains
ln chem:carbo:lactose chem:carbo:galactose @contains

def "chem:carbo:maltose" "Malt sugar, a disaccharide formed from two units of glucose."
ln chem:carbo:maltose chem:carbo:disaccharide sys:is_a
ln chem:carbo:maltose chem:carbo:glucose @contains

def "chem:carbo:monosaccharide" "The most basic form of carbohydrates, consisting of a single sugar unit that cannot be further hydrolyzed."

def "chem:carbo:polysaccharide" "Long polymeric chains of monosaccharide units bound together by glycosidic linkages."
ln chem:carbo:polysaccharide chem:bond:glycosidic_bond @utilizes

def "chem:carbo:ribose" "A simple sugar and carbohydrate with formula C5H10O5, a key component of RNA."

def "chem:carbo:sucrose" "Common table sugar, a disaccharide composed of glucose and fructose."
ln chem:carbo:sucrose chem:carbo:disaccharide sys:is_a
ln chem:carbo:sucrose chem:carbo:glucose @contains
ln chem:carbo:sucrose chem:carbo:fructose @contains
ln chem:carbo:sucrose dna:taste:sweet calc:associated_with

def "chem:catalysis:ch_activation" "The cleavage of a carbon-hydrogen bond and its replacement with a new functional group, bypassing traditional reactive intermediates."
ln chem:catalysis:ch_activation chem_org.catalysis sys:is_a
ln chem:catalysis:ch_activation chem:concept:atom_economy @improves
set.add name="ontology.modern_organic" id="chem:catalysis:ch_activation"

def "chem:catalysis:heterogeneous_catalysis" "Catalysis where the phase of catalysts differs from that of the reactants or products."

def "chem:catalysis:homogeneous_catalysis" "Catalysis in a solution by a soluble catalyst."

def "chem:catalysis:organocatalysis" "The use of small organic molecules to catalyze chemical reactions, notably asymmetric synthesis."
ln chem:catalysis:organocatalysis chem_org.catalysis sys:is_a
ln chem:catalysis:organocatalysis chem:concept:enantioselectivity @achieves
set.add name="ontology.modern_organic" id="chem:catalysis:organocatalysis"

def "chem:catalysis:photocatalysis" "The acceleration of a photoreaction in the presence of a catalyst, allowing light to drive difficult organic transformations."
ln chem:catalysis:photocatalysis chem_org.catalysis sys:is_a
set.add name="ontology.modern_organic" id="chem:catalysis:photocatalysis"

def "chem:class:aldehyde" "Organic compounds featuring a formyl group, odors vary from pungent to pleasant and floral/fruity."
ln chem:class:aldehyde chem:func:carbonyl @contains

def "chem:class:amine" "Derivatives of ammonia, often associated with the smell of rotting meat or fish."
ln chem:class:amine chem:func:amino @contains

def "chem:class:ester" "Often responsible for the sweet, fruity smells of flowers and fruits."
ln chem:class:ester chem:func:ester_group @contains
ln chem:class:ester dna:smell:fragrant calc:associated_with

def "chem:class:lactone" "Cyclic esters, often contributing to creamy, buttery, or fruity (peach/coconut) aromas."

def "chem:class:phenol" "Aromatic compounds often characterized by medicinal, smoky, or spicy aromas."

def "chem:class:terpene" "A large and diverse class of organic compounds produced by a variety of plants, often strong-smelling."
ln chem:class:terpene dna:smell:fragrant calc:associated_with

def "chem:class:thiol" "Organosulfur compounds that often have strong, repulsive odors resembling rotten eggs or garlic."
ln chem:class:thiol chem:func:sulfhydryl @contains
ln chem:class:thiol dna:smell:pungent calc:associated_with

def "chem:colloid:aerosol" "A colloidal suspension of fine solid particles or liquid droplets in a gas."
ln chem:colloid:aerosol chem:colloid:dispersed_phase @requires
ln chem:colloid:aerosol chem:colloid:dispersion_medium @requires

def "chem:colloid:colloid" "A mixture in which one substance of microscopically dispersed insoluble particles is suspended throughout another substance."
ln chem:colloid:colloid phys:phenomenon:tyndall_effect @exhibits
ln chem:colloid:colloid phys:phenomenon:brownian_motion @exhibits

def "chem:colloid:dispersed_phase" "The phase that is scattered or distributed throughout the dispersion medium in a colloid."

def "chem:colloid:dispersion_medium" "The continuous phase in which the dispersed phase is distributed."

def "chem:colloid:emulsion" "A colloid of two or more liquids that are normally immiscible."
ln chem:colloid:emulsion chem:colloid:dispersed_phase @requires
ln chem:colloid:emulsion chem:colloid:dispersion_medium @requires
ln chem:colloid:emulsion sci:cook:emulsion sys:same_as

def "chem:colloid:foam" "A colloidal dispersion of a gas in a liquid or a solid."

def "chem:colloid:gel" "A solid jelly-like colloidal material that can have properties ranging from soft and weak to hard and tough; liquid dispersed in a solid."
ln chem:colloid:gel sci:cook:hydrocolloid @associated_with

def "chem:colloid:sol" "A colloidal suspension of very small solid particles in a continuous liquid medium."

def "chem:compound:acetic_acid" "A simple carboxylic acid featuring a carboxyl group, giving vinegar its sour taste."
ln chem:compound:acetic_acid chem:func:carboxyl @contains

def "chem:compound:acetone" "The simplest ketone, featuring a carbonyl group, widely used as a solvent."
ln chem:compound:acetone chem:func:carbonyl @contains

def "chem:compound:ammonia" "A colorless gas with a pungent smell, vital for fertilizer production."
ln chem:compound:ammonia chem_ind.inorganic sys:is_a
ln chem:compound:ammonia word:en:fertilizer @used_in
set.add name="ontology.industrial_chemistry" id="chem:compound:ammonia"

def "chem:compound:atp" "Adenosine triphosphate, an organic chemical providing energy to drive many processes in living cells."
ln chem:compound:atp chem:func:phosphate @contains

def "chem:compound:benzene" "An important organic chemical compound with a ring of six carbon atoms, an elementary petrochemical."
ln chem:compound:benzene chem_ind.petrochemicals sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:compound:benzene"

def "chem:compound:carbon_dioxide" "An acidic colorless gas with a density about 53% higher than that of dry air."

def "chem:compound:cysteine" "A semi-essential proteinogenic amino acid containing a sulfhydryl group."
ln chem:compound:cysteine chem:func:sulfhydryl @contains
ln chem:compound:cysteine chem:func:amino @contains
ln chem:compound:cysteine chem:func:carboxyl @contains
ln chem:compound:cysteine chem:amino:amino_acid sys:is_a
ln chem:compound:cysteine chem:bond:covalent_bond @forms

def "chem:compound:dinitrogen" "Molecular nitrogen (N₂), a colorless, odorless diatomic gas forming the majority of the Earth's atmosphere."

def "chem:compound:ethanol" "A simple alcohol featuring a hydroxyl group, found in alcoholic beverages."
ln chem:compound:ethanol chem:func:hydroxyl @contains

def "chem:compound:ethyl_acetate" "A common ester featuring an ester group, known for its sweet smell."
ln chem:compound:ethyl_acetate chem:func:ester_group @contains

def "chem:compound:ethylene" "A colorless flammable gas, the most produced organic compound in the world."
ln chem:compound:ethylene chem_ind.petrochemicals sys:is_a
ln chem:compound:ethylene chem:polymer:polyethylene @polymerizes_to
set.add name="ontology.industrial_chemistry" id="chem:compound:ethylene"

def "chem:compound:methylamine" "The simplest primary amine, featuring an amino group."
ln chem:compound:methylamine chem:func:amino @contains

def "chem:compound:nitric_acid" "A highly corrosive mineral acid used in the production of fertilizers and explosives."
ln chem:compound:nitric_acid chem_ind.inorganic sys:is_a
ln chem:compound:nitric_acid word:en:acid sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:compound:nitric_acid"

def "chem:compound:propylene" "An unsaturated organic compound, the second most important starting product in the petrochemical industry."
ln chem:compound:propylene chem_ind.petrochemicals sys:is_a
ln chem:compound:propylene chem:polymer:polypropylene @polymerizes_to
set.add name="ontology.industrial_chemistry" id="chem:compound:propylene"

def "chem:compound:silica" "Silicon dioxide (SiO₂), most commonly found in nature as quartz."

def "chem:compound:sodium_hydroxide" "A highly caustic metallic base and alkali salt, also known as lye or caustic soda."
ln chem:compound:sodium_hydroxide chem_ind.inorganic sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:compound:sodium_hydroxide"

def "chem:compound:sulfuric_acid" "A highly corrosive strong mineral acid, the most widely produced chemical in the world."
ln chem:compound:sulfuric_acid chem_ind.inorganic sys:is_a
ln chem:compound:sulfuric_acid word:en:acid sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:compound:sulfuric_acid"

def "chem:compound:toluene" "An aromatic hydrocarbon widely used as an industrial feedstock and solvent."
ln chem:compound:toluene chem_ind.petrochemicals sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:compound:toluene"

def "chem:compound:urea" "An organic compound widely used in fertilizers as a convenient source of nitrogen."
ln chem:compound:urea chem_ind.inorganic sys:is_a
ln chem:compound:urea word:en:fertilizer @used_in
set.add name="ontology.industrial_chemistry" id="chem:compound:urea"

def "chem:compound:water" "An inorganic, transparent, tasteless, odorless, and nearly colorless chemical substance."
ln chem:compound:water chem:bond:hydrogen_bond @exhibits

def "chem:concept:atom_economy" "A concept in green chemistry evaluating the conversion efficiency of a chemical process in terms of all atoms involved."
ln chem:concept:atom_economy chem_org.synthesis sys:is_a
set.add name="ontology.modern_organic" id="chem:concept:atom_economy"

def "chem:concept:enantioselectivity" "The degree to which a reaction produces one enantiomer preferentially over the other."
ln chem:concept:enantioselectivity chem_org.catalysis sys:is_a
set.add name="ontology.modern_organic" id="chem:concept:enantioselectivity"

def "chem:element:actinium" "Atomic No: 89. Symbol: Ac. A soft, silvery-white radioactive metal."
ln chem:element:actinium chem:group:actinide sys:is_a

def "chem:element:aluminum" "Atomic No: 13. Symbol: Al. A lightweight, silvery-white post-transition metal."
ln chem:element:aluminum chem:group:post_transition_metal sys:is_a

def "chem:element:americium" "Atomic No: 95. Symbol: Am. A synthetic radioactive element."
ln chem:element:americium chem:group:actinide sys:is_a

def "chem:element:antimony" "Atomic No: 51. Symbol: Sb. A lustrous gray metalloid."
ln chem:element:antimony chem:group:metalloid sys:is_a

def "chem:element:argon" "Atomic No: 18. Symbol: Ar. The most abundant noble gas in Earth's atmosphere."
ln chem:element:argon chem:group:noble_gas sys:is_a

def "chem:element:arsenic" "Atomic No: 33. Symbol: As. A metalloid well known for its toxicity."
ln chem:element:arsenic chem:group:metalloid sys:is_a

def "chem:element:astatine" "Atomic No: 85. Symbol: At. The rarest naturally occurring element in the Earth's crust."
ln chem:element:astatine chem:group:halogen sys:is_a

def "chem:element:barium" "Atomic No: 56. Symbol: Ba. A soft, silvery alkaline earth metal."
ln chem:element:barium chem:group:alkaline_earth_metal sys:is_a

def "chem:element:berkelium" "Atomic No: 97. Symbol: Bk. A transuranic radioactive chemical element."
ln chem:element:berkelium chem:group:actinide sys:is_a

def "chem:element:beryllium" "Atomic No: 4. Symbol: Be. A strong, lightweight alkaline earth metal."
ln chem:element:beryllium chem:group:alkaline_earth_metal sys:is_a

def "chem:element:bismuth" "Atomic No: 83. Symbol: Bi. A brittle metal with a dark silver-pink hue."
ln chem:element:bismuth chem:group:post_transition_metal sys:is_a

def "chem:element:bohrium" "Atomic No: 107. Symbol: Bh. A synthetic element."
ln chem:element:bohrium chem:group:transition_metal sys:is_a

def "chem:element:boron" "Atomic No: 5. Symbol: B. A metalloid used in fiberglass and detergents."
ln chem:element:boron chem:group:metalloid sys:is_a

def "chem:element:bromine" "Atomic No: 35. Symbol: Br. A fuming red-brown liquid at room temperature, a highly reactive halogen."
ln chem:element:bromine chem:group:halogen sys:is_a

def "chem:element:cadmium" "Atomic No: 48. Symbol: Cd. A soft, bluish-white metal."
ln chem:element:cadmium chem:group:transition_metal sys:is_a

def "chem:element:calcium" "Atomic No: 20. Symbol: Ca. An alkaline earth metal vital for living organisms."
ln chem:element:calcium chem:group:alkaline_earth_metal sys:is_a
ln chem:element:calcium nutri:concept:dietary_mineral sys:is_a
ln chem:element:calcium med:condition:osteoporosis @prevents

def "chem:element:californium" "Atomic No: 98. Symbol: Cf. A radioactive metallic chemical element."
ln chem:element:californium chem:group:actinide sys:is_a

def "chem:element:carbon" "Atomic No: 6. Symbol: C. The basis of all known life, forms organic compounds."
ln chem:element:carbon chem:group:nonmetal sys:is_a

def "chem:element:cerium" "Atomic No: 58. Symbol: Ce. The most abundant of the rare earth metals."
ln chem:element:cerium chem:group:lanthanide sys:is_a

def "chem:element:cesium" "Atomic No: 55. Symbol: Cs. A soft, silvery-golden alkali metal."
ln chem:element:cesium chem:group:alkali_metal sys:is_a

def "chem:element:chlorine" "Atomic No: 17. Symbol: Cl. A yellow-green toxic gas, a highly reactive halogen."
ln chem:element:chlorine chem:group:halogen sys:is_a

def "chem:element:chromium" "Atomic No: 24. Symbol: Cr. A steely-gray, lustrous transition metal known for high corrosion resistance."
ln chem:element:chromium chem:group:transition_metal sys:is_a

def "chem:element:cobalt" "Atomic No: 27. Symbol: Co. A hard, lustrous transition metal used in magnetic alloys."
ln chem:element:cobalt chem:group:transition_metal sys:is_a
ln chem:element:cobalt prop:phys:ferromagnetism @exhibits

def "chem:element:copernicium" "Atomic No: 112. Symbol: Cn. A synthetic element."
ln chem:element:copernicium chem:group:transition_metal sys:is_a

def "chem:element:copper" "Atomic No: 29. Symbol: Cu. A soft, malleable, and ductile transition metal with very high thermal and electrical conductivity."
ln chem:element:copper chem:group:transition_metal sys:is_a

def "chem:element:curium" "Atomic No: 96. Symbol: Cm. A transuranic radioactive element."
ln chem:element:curium chem:group:actinide sys:is_a

def "chem:element:darmstadtium" "Atomic No: 110. Symbol: Ds. A synthetic element."
ln chem:element:darmstadtium chem:group:transition_metal sys:is_a

def "chem:element:dubnium" "Atomic No: 105. Symbol: Db. A highly radioactive synthetic element."
ln chem:element:dubnium chem:group:transition_metal sys:is_a

def "chem:element:dysprosium" "Atomic No: 66. Symbol: Dy. A rare earth metal with a metallic silver luster."
ln chem:element:dysprosium chem:group:lanthanide sys:is_a

def "chem:element:einsteinium" "Atomic No: 99. Symbol: Es. A synthetic element, member of the actinide series."
ln chem:element:einsteinium chem:group:actinide sys:is_a

def "chem:element:erbium" "Atomic No: 68. Symbol: Er. A silvery-white solid metal when artificially isolated."
ln chem:element:erbium chem:group:lanthanide sys:is_a

def "chem:element:europium" "Atomic No: 63. Symbol: Eu. The most reactive lanthanide."
ln chem:element:europium chem:group:lanthanide sys:is_a

def "chem:element:fermium" "Atomic No: 100. Symbol: Fm. A synthetic element, the heaviest that can be formed by neutron bombardment of lighter elements."
ln chem:element:fermium chem:group:actinide sys:is_a

def "chem:element:flerovium" "Atomic No: 114. Symbol: Fl. A superheavy synthetic element."
ln chem:element:flerovium chem:group:post_transition_metal sys:is_a

def "chem:element:fluorine" "Atomic No: 9. Symbol: F. The most electronegative and reactive of all elements."
ln chem:element:fluorine chem:group:halogen sys:is_a

def "chem:element:francium" "Atomic No: 87. Symbol: Fr. An extremely radioactive alkali metal."
ln chem:element:francium chem:group:alkali_metal sys:is_a

def "chem:element:gadolinium" "Atomic No: 64. Symbol: Gd. A silvery-white metal with unusual metallurgic properties."
ln chem:element:gadolinium chem:group:lanthanide sys:is_a

def "chem:element:gallium" "Atomic No: 31. Symbol: Ga. A soft post-transition metal that melts near room temperature."
ln chem:element:gallium chem:group:post_transition_metal sys:is_a

def "chem:element:germanium" "Atomic No: 32. Symbol: Ge. A lustrous, hard-brittle metalloid."
ln chem:element:germanium chem:group:metalloid sys:is_a

def "chem:element:gold" "Atomic No: 79. Symbol: Au. A bright, slightly orange-yellow, dense, soft, malleable, and ductile metal."
ln chem:element:gold chem:group:transition_metal sys:is_a

def "chem:element:hafnium" "Atomic No: 72. Symbol: Hf. A lustrous, silvery gray, tetravalent transition metal."
ln chem:element:hafnium chem:group:transition_metal sys:is_a

def "chem:element:hassium" "Atomic No: 108. Symbol: Hs. A synthetic element."
ln chem:element:hassium chem:group:transition_metal sys:is_a

def "chem:element:helium" "Atomic No: 2. Symbol: He. A colorless, inert gas."
ln chem:element:helium chem:group:noble_gas sys:is_a

def "chem:element:holmium" "Atomic No: 67. Symbol: Ho. A relatively soft and malleable silvery-white metal."
ln chem:element:holmium chem:group:lanthanide sys:is_a

def "chem:element:hydrogen" "Atomic No: 1. Symbol: H. The lightest and most abundant element in the universe."
ln chem:element:hydrogen chem:group:nonmetal sys:is_a

def "chem:element:indium" "Atomic No: 49. Symbol: In. A very soft, silvery-white post-transition metal."
ln chem:element:indium chem:group:post_transition_metal sys:is_a

def "chem:element:iodine" "Atomic No: 53. Symbol: I. The heaviest stable halogen, existing as a lustrous, purple-black nonmetallic solid."
ln chem:element:iodine chem:group:halogen sys:is_a
ln chem:element:iodine nutri:concept:dietary_mineral sys:is_a

def "chem:element:iridium" "Atomic No: 77. Symbol: Ir. A very hard, brittle, silvery-white transition metal."
ln chem:element:iridium chem:group:transition_metal sys:is_a

def "chem:element:iron" "Atomic No: 26. Symbol: Fe. The most common element on Earth by mass, forming much of its core."
ln chem:element:iron chem:group:transition_metal sys:is_a
ln chem:element:iron nutri:concept:dietary_mineral sys:is_a
ln chem:element:iron bio:role:cofactor sys:is_a
ln chem:element:iron chem:protein:hemoglobin @essential_for
ln chem:element:iron med:condition:anemia @prevents
ln chem:element:iron prop:phys:ferromagnetism @exhibits

def "chem:element:krypton" "Atomic No: 36. Symbol: Kr. A colorless, odorless noble gas."
ln chem:element:krypton chem:group:noble_gas sys:is_a

def "chem:element:lanthanum" "Atomic No: 57. Symbol: La. A soft, ductile, silvery-white metal."
ln chem:element:lanthanum chem:group:lanthanide sys:is_a

def "chem:element:lawrencium" "Atomic No: 103. Symbol: Lr. A synthetic chemical element."
ln chem:element:lawrencium chem:group:actinide sys:is_a

def "chem:element:lead" "Atomic No: 82. Symbol: Pb. A heavy metal that is denser than most common materials, soft and malleable."
ln chem:element:lead chem:group:post_transition_metal sys:is_a

def "chem:element:lithium" "Atomic No: 3. Symbol: Li. A soft, silvery-white alkali metal."
ln chem:element:lithium chem:group:alkali_metal sys:is_a

def "chem:element:livermorium" "Atomic No: 116. Symbol: Lv. A synthetic element."
ln chem:element:livermorium chem:group:post_transition_metal sys:is_a

def "chem:element:lutetium" "Atomic No: 71. Symbol: Lu. A silvery white metal, the last element in the lanthanide series."
ln chem:element:lutetium chem:group:lanthanide sys:is_a

def "chem:element:magnesium" "Atomic No: 12. Symbol: Mg. A shiny gray alkaline earth metal."
ln chem:element:magnesium chem:group:alkaline_earth_metal sys:is_a

def "chem:element:manganese" "Atomic No: 25. Symbol: Mn. A hard, brittle transition metal."
ln chem:element:manganese chem:group:transition_metal sys:is_a

def "chem:element:meitnerium" "Atomic No: 109. Symbol: Mt. A synthetic element."
ln chem:element:meitnerium chem:group:transition_metal sys:is_a

def "chem:element:mendelevium" "Atomic No: 101. Symbol: Md. A synthetic element."
ln chem:element:mendelevium chem:group:actinide sys:is_a

def "chem:element:mercury" "Atomic No: 80. Symbol: Hg. A heavy, silvery d-block element, liquid at standard conditions for temperature and pressure."
ln chem:element:mercury chem:group:transition_metal sys:is_a

def "chem:element:molybdenum" "Atomic No: 42. Symbol: Mo. A transition metal that withstands extreme temperatures without significantly expanding."
ln chem:element:molybdenum chem:group:transition_metal sys:is_a

def "chem:element:moscovium" "Atomic No: 115. Symbol: Mc. A synthetic element."
ln chem:element:moscovium chem:group:post_transition_metal sys:is_a

def "chem:element:neodymium" "Atomic No: 60. Symbol: Nd. A soft silvery metal, critical for powerful permanent magnets."
ln chem:element:neodymium chem:group:lanthanide sys:is_a

def "chem:element:neon" "Atomic No: 10. Symbol: Ne. An inert noble gas known for its reddish-orange glow in discharge tubes."
ln chem:element:neon chem:group:noble_gas sys:is_a

def "chem:element:neptunium" "Atomic No: 93. Symbol: Np. A radioactive actinide metal."
ln chem:element:neptunium chem:group:actinide sys:is_a

def "chem:element:nickel" "Atomic No: 28. Symbol: Ni. A silvery-white transition metal with a slight golden tinge."
ln chem:element:nickel chem:group:transition_metal sys:is_a
ln chem:element:nickel prop:phys:ferromagnetism @exhibits

def "chem:element:nihonium" "Atomic No: 113. Symbol: Nh. A synthetic element."
ln chem:element:nihonium chem:group:post_transition_metal sys:is_a

def "chem:element:niobium" "Atomic No: 41. Symbol: Nb. A light grey, crystalline, and ductile transition metal."
ln chem:element:niobium chem:group:transition_metal sys:is_a

def "chem:element:nitrogen" "Atomic No: 7. Symbol: N. A gas forming about 78% of Earth's atmosphere."
ln chem:element:nitrogen chem:group:nonmetal sys:is_a

def "chem:element:nobelium" "Atomic No: 102. Symbol: No. A synthetic chemical element."
ln chem:element:nobelium chem:group:actinide sys:is_a

def "chem:element:oganesson" "Atomic No: 118. Symbol: Og. A synthetic element with the highest atomic number currently known."
ln chem:element:oganesson chem:group:noble_gas sys:is_a

def "chem:element:osmium" "Atomic No: 76. Symbol: Os. A hard, brittle, bluish-white transition metal, the densest naturally occurring element."
ln chem:element:osmium chem:group:transition_metal sys:is_a

def "chem:element:oxygen" "Atomic No: 8. Symbol: O. A highly reactive nonmetal, essential for respiration."
ln chem:element:oxygen chem:group:nonmetal sys:is_a

def "chem:element:palladium" "Atomic No: 46. Symbol: Pd. A rare and lustrous silvery-white metal discovered in 1803."
ln chem:element:palladium chem:group:transition_metal sys:is_a

def "chem:element:phosphorus" "Atomic No: 15. Symbol: P. A highly reactive nonmetal existing in several allotropes (white, red)."
ln chem:element:phosphorus chem:group:nonmetal sys:is_a

def "chem:element:platinum" "Atomic No: 78. Symbol: Pt. A dense, malleable, ductile, highly unreactive transition metal."
ln chem:element:platinum chem:group:transition_metal sys:is_a

def "chem:element:plutonium" "Atomic No: 94. Symbol: Pu. A radioactive actinide metal of silvery-gray appearance."
ln chem:element:plutonium chem:group:actinide sys:is_a

def "chem:element:polonium" "Atomic No: 84. Symbol: Po. A rare and highly radioactive metal."
ln chem:element:polonium chem:group:post_transition_metal sys:is_a

def "chem:element:potassium" "Atomic No: 19. Symbol: K. A silvery-white alkali metal."
ln chem:element:potassium chem:group:alkali_metal sys:is_a

def "chem:element:praseodymium" "Atomic No: 59. Symbol: Pr. A soft, silvery, malleable and ductile metal."
ln chem:element:praseodymium chem:group:lanthanide sys:is_a

def "chem:element:promethium" "Atomic No: 61. Symbol: Pm. A radioactive lanthanide."
ln chem:element:promethium chem:group:lanthanide sys:is_a

def "chem:element:protactinium" "Atomic No: 91. Symbol: Pa. A dense, silvery-gray radioactive actinide metal."
ln chem:element:protactinium chem:group:actinide sys:is_a

def "chem:element:radium" "Atomic No: 88. Symbol: Ra. A highly radioactive alkaline earth metal."
ln chem:element:radium chem:group:alkaline_earth_metal sys:is_a

def "chem:element:radon" "Atomic No: 86. Symbol: Rn. A radioactive, colorless, odorless, tasteless noble gas."
ln chem:element:radon chem:group:noble_gas sys:is_a

def "chem:element:rhenium" "Atomic No: 75. Symbol: Re. A silvery-gray, heavy, third-row transition metal."
ln chem:element:rhenium chem:group:transition_metal sys:is_a

def "chem:element:rhodium" "Atomic No: 45. Symbol: Rh. A rare, silvery-white, hard, and corrosion-resistant transition metal."
ln chem:element:rhodium chem:group:transition_metal sys:is_a

def "chem:element:roentgenium" "Atomic No: 111. Symbol: Rg. A synthetic element."
ln chem:element:roentgenium chem:group:transition_metal sys:is_a

def "chem:element:rubidium" "Atomic No: 37. Symbol: Rb. A very soft, silvery-white alkali metal."
ln chem:element:rubidium chem:group:alkali_metal sys:is_a

def "chem:element:ruthenium" "Atomic No: 44. Symbol: Ru. A rare transition metal belonging to the platinum group."
ln chem:element:ruthenium chem:group:transition_metal sys:is_a

def "chem:element:rutherfordium" "Atomic No: 104. Symbol: Rf. A highly radioactive synthetic element."
ln chem:element:rutherfordium chem:group:transition_metal sys:is_a

def "chem:element:samarium" "Atomic No: 62. Symbol: Sm. A moderately hard silvery metal."
ln chem:element:samarium chem:group:lanthanide sys:is_a

def "chem:element:scandium" "Atomic No: 21. Symbol: Sc. A silvery-white metallic transition metal."
ln chem:element:scandium chem:group:transition_metal sys:is_a

def "chem:element:seaborgium" "Atomic No: 106. Symbol: Sg. A synthetic element."
ln chem:element:seaborgium chem:group:transition_metal sys:is_a

def "chem:element:selenium" "Atomic No: 34. Symbol: Se. A nonmetal with properties intermediate between sulfur and tellurium."
ln chem:element:selenium chem:group:nonmetal sys:is_a

def "chem:element:silicon" "Atomic No: 14. Symbol: Si. A hard, brittle crystalline metalloid, crucial for semiconductors."
ln chem:element:silicon chem:group:metalloid sys:is_a

def "chem:element:silver" "Atomic No: 47. Symbol: Ag. A soft, white, lustrous transition metal with the highest electrical conductivity."
ln chem:element:silver chem:group:transition_metal sys:is_a

def "chem:element:sodium" "Atomic No: 11. Symbol: Na. A soft, highly reactive alkali metal."
ln chem:element:sodium chem:group:alkali_metal sys:is_a

def "chem:element:strontium" "Atomic No: 38. Symbol: Sr. An alkaline earth metal that burns with a red flame."
ln chem:element:strontium chem:group:alkaline_earth_metal sys:is_a

def "chem:element:sulfur" "Atomic No: 16. Symbol: S. An abundant, multivalent nonmetal, yellow in crystalline form."
ln chem:element:sulfur chem:group:nonmetal sys:is_a

def "chem:element:tantalum" "Atomic No: 73. Symbol: Ta. A rare, hard, blue-gray, lustrous transition metal."
ln chem:element:tantalum chem:group:transition_metal sys:is_a

def "chem:element:technetium" "Atomic No: 43. Symbol: Tc. The lightest element whose isotopes are all radioactive."
ln chem:element:technetium chem:group:transition_metal sys:is_a

def "chem:element:tellurium" "Atomic No: 52. Symbol: Te. A brittle, mildly toxic, rare, silver-white metalloid."
ln chem:element:tellurium chem:group:metalloid sys:is_a

def "chem:element:tennessine" "Atomic No: 117. Symbol: Ts. A synthetic element."
ln chem:element:tennessine chem:group:halogen sys:is_a

def "chem:element:terbium" "Atomic No: 65. Symbol: Tb. A silvery-white rare earth metal."
ln chem:element:terbium chem:group:lanthanide sys:is_a

def "chem:element:thallium" "Atomic No: 81. Symbol: Tl. A gray post-transition metal that is not found free in nature."
ln chem:element:thallium chem:group:post_transition_metal sys:is_a

def "chem:element:thorium" "Atomic No: 90. Symbol: Th. A weakly radioactive metallic chemical element."
ln chem:element:thorium chem:group:actinide sys:is_a

def "chem:element:thulium" "Atomic No: 69. Symbol: Tm. The second-least abundant of the lanthanides."
ln chem:element:thulium chem:group:lanthanide sys:is_a

def "chem:element:tin" "Atomic No: 50. Symbol: Sn. A silvery metal that characteristically has a faint yellow hue."
ln chem:element:tin chem:group:post_transition_metal sys:is_a

def "chem:element:titanium" "Atomic No: 22. Symbol: Ti. A lustrous transition metal with a high strength-to-weight ratio."
ln chem:element:titanium chem:group:transition_metal sys:is_a

def "chem:element:tungsten" "Atomic No: 74. Symbol: W. A rare metal with the highest melting point of all discovered elements."
ln chem:element:tungsten chem:group:transition_metal sys:is_a

def "chem:element:uranium" "Atomic No: 92. Symbol: U. A silvery-white metal, key to nuclear power."
ln chem:element:uranium chem:group:actinide sys:is_a

def "chem:element:vanadium" "Atomic No: 23. Symbol: V. A hard, silvery-gray transition metal."
ln chem:element:vanadium chem:group:transition_metal sys:is_a

def "chem:element:xenon" "Atomic No: 54. Symbol: Xe. A colorless, dense, odorless noble gas."
ln chem:element:xenon chem:group:noble_gas sys:is_a

def "chem:element:ytterbium" "Atomic No: 70. Symbol: Yb. A soft, silvery, metallic element."
ln chem:element:ytterbium chem:group:lanthanide sys:is_a

def "chem:element:yttrium" "Atomic No: 39. Symbol: Y. A silvery-metallic transition metal."
ln chem:element:yttrium chem:group:transition_metal sys:is_a

def "chem:element:zinc" "Atomic No: 30. Symbol: Zn. A slightly brittle metal at room temperature, commonly used for galvanization."
ln chem:element:zinc chem:group:transition_metal sys:is_a
ln chem:element:zinc nutri:concept:dietary_mineral sys:is_a
ln chem:element:zinc bio:role:cofactor sys:is_a

def "chem:element:zirconium" "Atomic No: 40. Symbol: Zr. A lustrous, grey-white, strong transition metal."
ln chem:element:zirconium chem:group:transition_metal sys:is_a

def "chem:eq:dynamic_equilibrium" "A state of balance between continuing processes; the rate of the forward reaction equals the rate of the reverse reaction."
ln chem:eq:dynamic_equilibrium chem_rxn.equilibrium sys:is_a
set.add name="ontology.chemistry_reactions" id="chem:eq:dynamic_equilibrium"

def "chem:eq:equilibrium_constant" "The value of the reaction quotient when a reversible chemical reaction has reached equilibrium."
ln chem:eq:equilibrium_constant chem_rxn.equilibrium sys:is_a
ln chem:eq:equilibrium_constant chem:eq:dynamic_equilibrium @quantifies
set.add name="ontology.chemistry_reactions" id="chem:eq:equilibrium_constant"

def "chem:eq:le_chateliers_principle" "If a dynamic equilibrium is disturbed by changing the conditions, the position of equilibrium moves to counteract the change."
ln chem:eq:le_chateliers_principle chem_rxn.equilibrium sys:is_a
ln chem:eq:le_chateliers_principle chem:eq:dynamic_equilibrium @governs
set.add name="ontology.chemistry_reactions" id="chem:eq:le_chateliers_principle"

def "chem:fatty_acid:linoleic_acid" "A polyunsaturated omega-6 fatty acid essential in the human diet."
ln chem:fatty_acid:linoleic_acid chem:fatty_acid:unsaturated_fatty_acid sys:is_a

def "chem:fatty_acid:oleic_acid" "A monounsaturated omega-9 fatty acid found in various animal and vegetable sources, a major component of olive oil."
ln chem:fatty_acid:oleic_acid chem:fatty_acid:unsaturated_fatty_acid sys:is_a

def "chem:fatty_acid:palmitic_acid" "A common saturated fatty acid found in animals, plants, and microorganisms."
ln chem:fatty_acid:palmitic_acid chem:fatty_acid:saturated_fatty_acid sys:is_a

def "chem:fatty_acid:saturated_fatty_acid" "A fatty acid chain in which all carbon-carbon bonds are single bonds."
ln chem:fatty_acid:saturated_fatty_acid prop:phys:melting_point @elevates

def "chem:fatty_acid:trans_fatty_acid" "An unsaturated fatty acid that contains a trans double bond, commonly produced by partial hydrogenation."

def "chem:fatty_acid:unsaturated_fatty_acid" "A fatty acid chain that contains at least one carbon-carbon double bond."
ln chem:fatty_acid:unsaturated_fatty_acid prop:phys:melting_point @lowers

def "chem:func:amide_group" "A carbonyl group linked to a nitrogen atom (-CON-). Forms peptide bonds."

def "chem:func:amino" "A nitrogen atom bonded to two hydrogen atoms (-NH2). Acts as a base."
ln chem:func:amino prop:chem:basic @imparts
ln chem:func:amino prop:chem:polar @imparts
ln chem:func:amino prop:chem:hydrophilic @imparts

def "chem:func:carbonyl" "A carbon atom double-bonded to an oxygen atom (C=O). Found in aldehydes and ketones."
ln chem:func:carbonyl prop:chem:polar @imparts

def "chem:func:carboxyl" "A carbonyl and hydroxyl group attached to the same carbon atom (-COOH). Acts as an acid."
ln chem:func:carboxyl prop:chem:acidic @imparts
ln chem:func:carboxyl prop:chem:polar @imparts

def "chem:func:cyano" "A carbon atom triple-bonded to a nitrogen atom (-C≡N). Also known as nitrile."

def "chem:func:ester_group" "Derived from an acid in which an -OH group is replaced by an -O-alkyl group (-COO-)."

def "chem:func:ether_group" "An oxygen atom connected to two alkyl or aryl groups (R-O-R')."

def "chem:func:ethyl" "An alkyl derived from ethane (-C2H5)."

def "chem:func:hydroxyl" "An oxygen atom bonded to a hydrogen atom (-OH). Characteristic of alcohols."
ln chem:func:hydroxyl prop:chem:polar @imparts
ln chem:func:hydroxyl prop:chem:hydrophilic @imparts
ln chem:func:hydroxyl chem:bond:hydrogen_bond @promotes

def "chem:func:methyl" "An alkyl derived from methane, containing one carbon atom bonded to three hydrogen atoms (-CH3)."
ln chem:func:methyl prop:chem:nonpolar @imparts
ln chem:func:methyl prop:chem:hydrophobic @imparts

def "chem:func:nitro" "A nitrogen atom bonded to two oxygen atoms (-NO2). Highly electron-withdrawing."

def "chem:func:phenyl" "A cyclic group of atoms with the formula C6H5, derived from benzene."
ln chem:func:phenyl prop:chem:nonpolar @imparts
ln chem:func:phenyl prop:chem:hydrophobic @imparts

def "chem:func:phosphate" "A phosphorus atom bonded to four oxygen atoms (-OPO3). Highly acidic and charged."
ln chem:func:phosphate prop:chem:acidic @imparts
ln chem:func:phosphate prop:chem:hydrophilic @imparts

def "chem:func:sulfhydryl" "A sulfur atom bonded to a hydrogen atom (-SH). Also known as a thiol group."
ln chem:func:sulfhydryl prop:chem:polar @imparts
ln chem:func:sulfhydryl chem:compound:cysteine sys:associated_with

def "chem:group:actinide" "Radioactive elements (atomic numbers 89–103)."

def "chem:group:alkali_metal" "Group 1 elements; highly reactive metals."

def "chem:group:alkaline_earth_metal" "Group 2 elements; somewhat reactive shiny metals."

def "chem:group:halogen" "Group 17 elements; highly reactive nonmetals."

def "chem:group:lanthanide" "Rare earth elements (atomic numbers 57–71)."

def "chem:group:metalloid" "Elements with properties intermediate between metals and nonmetals."

def "chem:group:noble_gas" "Group 18 elements; odorless, colorless, monatomic, and highly inert."

def "chem:group:nonmetal" "Elements that typically lack metallic attributes."

def "chem:group:post_transition_metal" "Soft, brittle metals in the p-block."

def "chem:group:transition_metal" "Metallic elements occupying the d-block."
ln chem:group:transition_metal phys:optics:d_d_transition @exhibits
ln chem:group:transition_metal prop:phys:malleability @exhibits
ln chem:group:transition_metal prop:phys:ductility @exhibits
ln chem:group:transition_metal prop:phys:electrical_conductivity @exhibits
ln chem:group:transition_metal prop:phys:thermal_conductivity @exhibits

def "chem:lipid:cholesterol" "A type of sterol that is an essential structural component of animal cell membranes and a precursor for steroid hormones."
ln chem:lipid:cholesterol chem:lipid:sterol sys:is_a
ln chem:lipid:cholesterol chem:func:hydroxyl @contains
ln chem:lipid:cholesterol med:condition:atherosclerosis @associated_with
ln chem:lipid:cholesterol bio:hormone:testosterone @precursor_of
ln chem:lipid:cholesterol bio:hormone:estrogen @precursor_of
ln chem:lipid:cholesterol bio:hormone:cortisol @precursor_of

def "chem:lipid:lipid" "A broad group of naturally occurring molecules that include fats, waxes, sterols, fat-soluble vitamins, and phospholipids."
ln chem:lipid:lipid nutri:concept:macronutrient sys:is_a

def "chem:lipid:phospholipid" "A class of lipids whose molecule has a hydrophilic head containing a phosphate group, and two hydrophobic tails derived from fatty acids."
ln chem:lipid:phospholipid chem:lipid:lipid sys:is_a
ln chem:lipid:phospholipid chem:func:phosphate @contains

def "chem:lipid:sterol" "A subgroup of the steroids with a hydroxyl group at the 3-position of the A-ring, e.g., cholesterol."
ln chem:lipid:sterol chem:lipid:lipid sys:is_a

def "chem:lipid:triglyceride" "An ester derived from glycerol and three fatty acids, the main constituent of body fat in humans and other animals, as well as vegetable fat."
ln chem:lipid:triglyceride chem:lipid:lipid sys:is_a
ln chem:lipid:triglyceride chem:func:ester_group @contains
ln chem:lipid:triglyceride med:condition:atherosclerosis @associated_with

def "chem:materials:conductive_polymer" "Organic polymers that conduct electricity, merging the electronic properties of metals with the processing advantages of plastics."
ln chem:materials:conductive_polymer chem_org.materials sys:is_a
ln chem:materials:conductive_polymer word:en:polymer sys:is_a
set.add name="ontology.modern_organic" id="chem:materials:conductive_polymer"

def "chem:materials:covalent_organic_framework" "Two- or three-dimensional porous crystalline materials made entirely from light elements linked by strong covalent bonds."
ln chem:materials:covalent_organic_framework chem_org.materials sys:is_a
set.add name="ontology.modern_organic" id="chem:materials:covalent_organic_framework"

def "chem:odor:allicin" "An organosulfur compound obtained from garlic, responsible for its distinct pungent smell."
ln chem:odor:allicin chem:class:thiol sys:is_a

def "chem:odor:cinnamaldehyde" "An organic compound that gives cinnamon its flavor and odor."
ln chem:odor:cinnamaldehyde chem:class:aldehyde sys:is_a

def "chem:odor:diacetyl" "A diketone compound with an intensely buttery flavor and aroma."

def "chem:odor:hydrogen_sulfide" "A colorless chalcogen hydride gas with the characteristic foul odor of rotten eggs."
ln chem:odor:hydrogen_sulfide dna:smell:rotten calc:associated_with

def "chem:odor:isoamyl_acetate" "An ester with a strong odor universally described as banana or pear."
ln chem:odor:isoamyl_acetate prop:chem:volatility @has_property
ln chem:odor:isoamyl_acetate chem:class:ester sys:is_a

def "chem:odor:limonene" "A cyclic monoterpene possessing a strong smell of oranges."
ln chem:odor:limonene prop:chem:volatility @has_property
ln chem:odor:limonene chem:class:terpene sys:is_a

def "chem:odor:menthol" "A terpene alcohol with a minty odor and a cooling sensation."

def "chem:odor:trimethylamine" "A tertiary amine with a strong 'fishy' odor in low concentrations."
ln chem:odor:trimethylamine chem:class:amine sys:is_a
ln chem:odor:trimethylamine dna:smell:rotten calc:associated_with

def "chem:odor:vanillin" "A phenolic aldehyde, the primary component of the extract of the vanilla bean."
ln chem:odor:vanillin chem:class:phenol sys:is_a
ln chem:odor:vanillin chem:class:aldehyde sys:is_a

def "chem:orbital:d_orbital" "A complex atomic orbital, typically cloverleaf-shaped, characteristic of transition metals."
ln chem:orbital:d_orbital chem_quant.orbitals sys:is_a
set.add name="ontology.quantum_chemistry" id="chem:orbital:d_orbital"

def "chem:orbital:homo" "Highest Occupied Molecular Orbital; the highest energy MO that contains electrons."
ln chem:orbital:homo chem_quant.orbitals sys:is_a
ln chem:orbital:homo word:en:electron @donates
set.add name="ontology.quantum_chemistry" id="chem:orbital:homo"

def "chem:orbital:lumo" "Lowest Unoccupied Molecular Orbital; the lowest energy MO that does not contain electrons."
ln chem:orbital:lumo chem_quant.orbitals sys:is_a
ln chem:orbital:lumo word:en:electron @accepts
set.add name="ontology.quantum_chemistry" id="chem:orbital:lumo"

def "chem:orbital:molecular_orbital" "A mathematical function describing the wave-like behavior of an electron in a molecule."
ln chem:orbital:molecular_orbital chem_quant.orbitals sys:is_a
set.add name="ontology.quantum_chemistry" id="chem:orbital:molecular_orbital"

def "chem:orbital:p_orbital" "A dumbbell-shaped atomic orbital."
ln chem:orbital:p_orbital chem_quant.orbitals sys:is_a
set.add name="ontology.quantum_chemistry" id="chem:orbital:p_orbital"

def "chem:orbital:s_orbital" "A spherically symmetric atomic orbital."
ln chem:orbital:s_orbital chem_quant.orbitals sys:is_a
set.add name="ontology.quantum_chemistry" id="chem:orbital:s_orbital"

def "chem:pigment:anthocyanin" "Water-soluble vacuolar pigments that, depending on their pH, may appear red, purple, blue, or black."
ln chem:pigment:anthocyanin sci:cook:ph_level @moderates
ln chem:pigment:anthocyanin dna:color:red calc:associated_with
ln chem:pigment:anthocyanin dna:color:blue calc:associated_with
ln chem:pigment:anthocyanin dna:color:purple calc:associated_with

def "chem:pigment:azo_dye" "A class of synthetic organic compounds containing a nitrogen-nitrogen double bond, widely used for their vibrant colors (often red, orange, yellow)."
ln chem:pigment:azo_dye phys:optics:conjugation @utilizes

def "chem:pigment:carotene" "An orange photosynthetic pigment important for photosynthesis, highly conjugated."
ln chem:pigment:carotene phys:optics:conjugation @utilizes
ln chem:pigment:carotene dna:color:orange calc:associated_with

def "chem:pigment:chlorophyll" "A green pigment found in cyanobacteria and the chloroplasts of algae and plants, essential for photosynthesis."
ln chem:pigment:chlorophyll chem:element:magnesium @contains
ln chem:pigment:chlorophyll dna:color:green calc:associated_with

def "chem:pigment:curcumin" "A bright yellow chemical produced by plants of the Curcuma longa species."
ln chem:pigment:curcumin dna:color:yellow calc:associated_with

def "chem:pigment:heme" "A coordination complex consisting of an iron ion coordinated to a porphyrin acting as a tetradentate ligand, responsible for the red color of blood."
ln chem:pigment:heme chem:element:iron @contains
ln chem:pigment:heme dna:color:red calc:associated_with

def "chem:pigment:indigo" "A deep and rich color close to the color wheel blue, historically extracted from plants but now synthesized globally for denim."
ln chem:pigment:indigo dna:color:blue calc:associated_with

def "chem:pigment:lycopene" "A bright red carotene and carotenoid pigment found in tomatoes and other red fruits and vegetables."
ln chem:pigment:lycopene phys:optics:conjugation @utilizes
ln chem:pigment:lycopene dna:color:red calc:associated_with

def "chem:pigment:melanin" "A broad term for a group of natural pigments found in most organisms, typically producing brown or black colors."

def "chem:pigment:titanium_dioxide" "A naturally occurring oxide of titanium, brilliant white and highly refractive, used universally as a white pigment."
ln chem:pigment:titanium_dioxide chem:element:titanium @contains
ln chem:pigment:titanium_dioxide dna:color:white calc:associated_with

def "chem:polymer:cellulose" "An organic polysaccharide consisting of a linear chain of several hundred to many thousands of beta-linked D-glucose units; structural component of primary cell walls in green plants."
ln chem:polymer:cellulose chem:carbo:polysaccharide sys:is_a

def "chem:polymer:dna" "Deoxyribonucleic acid, a polymer composed of two polynucleotide chains that coil around each other to form a double helix carrying genetic instructions."
ln chem:polymer:dna prop:chem:hydrophilic @has_property

def "chem:polymer:epoxy_resin" "A class of reactive prepolymers and polymers which contain epoxide groups, forming strong thermosetting materials."
ln chem:polymer:epoxy_resin prop:material:thermosetting sys:is_a

def "chem:polymer:kevlar" "A heat-resistant and strong synthetic fiber, related to other aramids such as Nomex and Technora."
ln chem:polymer:kevlar chem:func:amide_group @contains

def "chem:polymer:nylon" "A generic designation for a family of synthetic polymers known as polyamides."
ln chem:polymer:nylon prop:material:thermoplastic sys:is_a
ln chem:polymer:nylon chem:func:amide_group @contains

def "chem:polymer:pet" "Polyethylene terephthalate, the most common thermoplastic polymer resin of the polyester family."
ln chem:polymer:pet prop:material:thermoplastic sys:is_a
ln chem:polymer:pet chem:func:ester_group @contains

def "chem:polymer:polyethylene" "The most common plastic, primarily used in packaging."
ln chem:polymer:polyethylene chem_ind.polymers sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:polymer:polyethylene"

def "chem:polymer:polypropylene" "A thermoplastic polymer used in a wide variety of applications including packaging and textiles."
ln chem:polymer:polypropylene chem_ind.polymers sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:polymer:polypropylene"

def "chem:polymer:polystyrene" "A synthetic aromatic hydrocarbon polymer made from the monomer styrene."
ln chem:polymer:polystyrene chem_ind.polymers sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:polymer:polystyrene"

def "chem:polymer:polyurethane" "A polymer composed of organic units joined by carbamate (urethane) links, often used in foams."
ln chem:polymer:polyurethane prop:material:elastomer sys:is_a

def "chem:polymer:polyvinyl_chloride" "The world's third-most widely produced synthetic plastic polymer, heavily used in construction."
ln chem:polymer:polyvinyl_chloride chem_ind.polymers sys:is_a
set.add name="ontology.industrial_chemistry" id="chem:polymer:polyvinyl_chloride"

def "chem:polymer:rna" "Ribonucleic acid, a polymeric molecule essential in various biological roles in coding, decoding, regulation and expression of genes."
ln chem:polymer:rna prop:chem:hydrophilic @has_property

def "chem:polymer:starch" "A polymeric carbohydrate consisting of numerous glucose units joined by glycosidic bonds; acts as an energy store in plants."
ln chem:polymer:starch chem:carbo:polysaccharide sys:is_a
ln chem:polymer:starch chem:carbo:glucose @composed_of

def "chem:polymer:teflon" "Polytetrafluoroethylene (PTFE), a synthetic fluoropolymer of tetrafluoroethylene known for its non-stick properties."

def "chem:protein:antibody" "A large Y-shaped protein used by the immune system to identify and neutralize foreign objects like bacteria and viruses."

def "chem:protein:chaperone" "A protein that assists the conformational folding or unfolding of other proteins."

def "chem:protein:collagen" "A structural protein that provides strength and support to skin, tendons, and ligaments."

def "chem:protein:enzyme" "A protein that acts as a biological catalyst to accelerate chemical reactions."
ln chem:protein:enzyme chem:rxn:catalyst sys:is_a
ln chem:protein:enzyme chem:thermo:activation_energy @lowers
ln chem:protein:enzyme bio:enzyme:active_site @contains

def "chem:protein:hemoglobin" "An iron-containing protein in red blood cells that carries oxygen from the lungs to the tissues."
ln chem:protein:hemoglobin chem:protein:enzyme @contrasts_with

def "chem:quantum:aufbau_principle" "Electrons fill atomic orbitals of the lowest available energy levels before occupying higher levels."
ln chem:quantum:aufbau_principle chem_quant.principles sys:is_a
ln chem:quantum:aufbau_principle chem:orbital:d_orbital @governs
set.add name="ontology.quantum_chemistry" id="chem:quantum:aufbau_principle"

def "chem:quantum:electronegativity" "A chemical property that describes the tendency of an atom to attract a shared pair of electrons."
ln chem:quantum:electronegativity chem_quant.principles sys:is_a
ln chem:quantum:electronegativity chem:bond:ionic_bond @determines
ln chem:quantum:electronegativity chem:bond:covalent_bond @determines
set.add name="ontology.quantum_chemistry" id="chem:quantum:electronegativity"

def "chem:quantum:hunds_rule" "Every orbital in a subshell is singly occupied with one electron before any one orbital is doubly occupied."
ln chem:quantum:hunds_rule chem_quant.principles sys:is_a
ln chem:quantum:hunds_rule chem:orbital:p_orbital @governs
set.add name="ontology.quantum_chemistry" id="chem:quantum:hunds_rule"

def "chem:quantum:pauli_exclusion_principle" "No two electrons in an atom can have the same four quantum numbers."
ln chem:quantum:pauli_exclusion_principle chem_quant.principles sys:is_a
ln chem:quantum:pauli_exclusion_principle chem:orbital:s_orbital @governs
set.add name="ontology.quantum_chemistry" id="chem:quantum:pauli_exclusion_principle"

def "chem:quantum:resonance" "A way of describing bonding in certain molecules or ions by the combination of several contributing structures."
ln chem:quantum:resonance chem_quant.principles sys:is_a
set.add name="ontology.quantum_chemistry" id="chem:quantum:resonance"

def "chem:reaction:addition_polymerization" "A chain-growth polymerization process where monomers link together without the co-generation of other products."
ln chem:reaction:addition_polymerization chem:polymer:teflon @produces
ln chem:reaction:addition_polymerization chem:polymer:polyethylene @produces
ln chem:reaction:addition_polymerization chem:polymer:polypropylene @produces
ln chem:reaction:addition_polymerization chem:polymer:polyvinyl_chloride @produces
ln chem:reaction:addition_polymerization chem:polymer:polystyrene @produces

def "chem:reaction:caramelization" "The browning of sugar, a process used extensively in cooking for the resulting sweet nutty flavor and brown color."
ln chem:reaction:caramelization chem:carbo:carbohydrate @requires
ln chem:reaction:caramelization sci:cook:caramelization sys:same_as
ln chem:reaction:caramelization dna:taste:bitter calc:associated_with

def "chem:reaction:condensation_polymerization" "A step-growth polymerization process where molecules join together, losing small molecules as byproducts such as water or methanol."
ln chem:reaction:condensation_polymerization chem:polymer:nylon @produces
ln chem:reaction:condensation_polymerization chem:polymer:pet @produces

def "chem:reaction:hydrogenation" "A chemical reaction between molecular hydrogen and another compound or element, often used to turn liquid unsaturated fats into solid fats."
ln chem:reaction:hydrogenation chem:fatty_acid:unsaturated_fatty_acid @consumes
ln chem:reaction:hydrogenation chem:fatty_acid:trans_fatty_acid @produces

def "chem:reaction:hydrolysis" "Any chemical reaction in which a molecule of water breaks one or more chemical bonds."
ln chem:reaction:hydrolysis chem:bond:glycosidic_bond @breaks

def "chem:reaction:lipid_oxidation" "A complex series of chemical reactions between lipids and oxygen, causing food rancidity."
ln chem:reaction:lipid_oxidation dna:smell:musty calc:associated_with

def "chem:reaction:maillard_reaction" "A chemical reaction between amino acids and reducing sugars that gives browned food its distinctive flavor."
ln chem:reaction:maillard_reaction chem:carbo:monosaccharide @requires
ln chem:reaction:maillard_reaction chem:func:amino @requires
ln chem:reaction:maillard_reaction sci:cook:maillard_reaction sys:same_as
ln chem:reaction:maillard_reaction dna:taste:umami calc:associated_with

def "chem:reaction:saponification" "A process that produces soap, usually from fats and lye (sodium hydroxide)."
ln chem:reaction:saponification chem:lipid:triglyceride @consumes

def "chem:rxn:catalyst" "A substance that increases the rate of a chemical reaction without itself undergoing any permanent chemical change."
ln chem:rxn:catalyst chem_rxn.thermodynamics sys:is_a
ln chem:rxn:catalyst chem:thermo:activation_energy @lowers
set.add name="ontology.chemistry_reactions" id="chem:rxn:catalyst"

def "chem:rxn:combustion" "An exothermic reaction between a fuel and an oxidant, producing heat and often light."
ln chem:rxn:combustion chem_rxn.types sys:is_a
ln chem:rxn:combustion chem:thermo:exothermic sys:is_a
set.add name="ontology.chemistry_reactions" id="chem:rxn:combustion"

def "chem:rxn:decomposition" "A reaction where a single compound breaks down into two or more simpler substances."
ln chem:rxn:decomposition chem_rxn.types sys:is_a
ln chem:rxn:decomposition chem:thermo:endothermic @often_is
set.add name="ontology.chemistry_reactions" id="chem:rxn:decomposition"

def "chem:rxn:neutralization" "A reaction in which an acid and a base react quantitatively with each other, usually forming water and a salt."
ln chem:rxn:neutralization chem_rxn.types sys:is_a
ln chem:rxn:neutralization chem:rxn:redox @contrasts_with
set.add name="ontology.chemistry_reactions" id="chem:rxn:neutralization"

def "chem:rxn:redox" "A reaction involving the transfer of electrons between two species (oxidation-reduction)."
ln chem:rxn:redox chem_rxn.types sys:is_a
set.add name="ontology.chemistry_reactions" id="chem:rxn:redox"

def "chem:rxn:synthesis" "A reaction where multiple reactants combine to form a single product."
ln chem:rxn:synthesis chem_rxn.types sys:is_a
ln chem:rxn:synthesis chem:rxn:decomposition sys:antonym
set.add name="ontology.chemistry_reactions" id="chem:rxn:synthesis"

def "chem:structure:denaturation" "The process in which a protein loses its native structure due to external stress (heat, pH)."
ln chem:structure:denaturation sci:cook:protein_denaturation sys:same_as
ln chem:structure:denaturation chem:structure:tertiary @disrupts

def "chem:structure:primary" "The linear sequence of amino acids in a polypeptide chain."
ln chem:structure:primary nutri:concept:macronutrient sys:is_a

def "chem:structure:quaternary" "The structure formed by several protein molecules (polypeptide chains), which usually function as a single protein complex."
ln chem:structure:quaternary chem:structure:tertiary @follows

def "chem:structure:secondary" "Local folded structures that form within a polypeptide due to interactions between atoms of the backbone (e.g., alpha helix, beta sheet)."
ln chem:structure:secondary chem:structure:primary @follows

def "chem:structure:tertiary" "The overall three-dimensional shape of a single polypeptide molecule."
ln chem:structure:tertiary chem:structure:secondary @follows

def "chem:synthesis:bioorthogonal_chemistry" "Chemical reactions that can occur inside of living systems without interfering with native biochemical processes."
ln chem:synthesis:bioorthogonal_chemistry chem_org.synthesis sys:is_a
ln chem:synthesis:bioorthogonal_chemistry chem:synthesis:click_chemistry @utilizes
set.add name="ontology.modern_organic" id="chem:synthesis:bioorthogonal_chemistry"

def "chem:synthesis:click_chemistry" "A class of biocompatible small molecule reactions commonly used in bioconjugation, allowing joining of substrates of choice with specific biomolecules."
ln chem:synthesis:click_chemistry chem_org.synthesis sys:is_a
set.add name="ontology.modern_organic" id="chem:synthesis:click_chemistry"

def "chem:synthesis:cross_coupling" "A reaction where two hydrocarbon fragments are coupled with the aid of a metal catalyst."
ln chem:synthesis:cross_coupling chem_org.synthesis sys:is_a
ln chem:synthesis:cross_coupling chem:group:transition_metal @requires
set.add name="ontology.modern_organic" id="chem:synthesis:cross_coupling"

def "chem:theory:atomic_theory" "John Dalton's scientific theory proposing that all matter is composed of indivisible atoms of different weights."
ln chem:theory:atomic_theory sci:history:modern_chemistry @foundational_for
ln chem:theory:atomic_theory sci:history:alchemy @departs_from

def "chem:theory:conservation_of_mass" "The principle that the mass of a closed system must remain constant over time, regardless of the processes acting inside the system."
ln chem:theory:conservation_of_mass phys:mech:mass @governs
ln chem:theory:conservation_of_mass phys:law:conservation_of_energy calc:associated_with

def "chem:theory:oxygen_theory_of_combustion" "Antoine Lavoisier's theory that combustion requires oxygen, fundamentally replacing the phlogiston theory."
ln chem:theory:oxygen_theory_of_combustion chem:element:oxygen @utilizes

def "chem:theory:phlogiston_theory" "A superseded scientific theory that postulated the existence of a fire-like element called phlogiston contained within combustible bodies and released during combustion."
ln chem:theory:phlogiston_theory chem:theory:oxygen_theory_of_combustion @replaced_by

def "chem:thermo:activation_energy" "The minimum quantity of energy which the reacting species must possess in order to undergo a specified reaction."
ln chem:thermo:activation_energy chem_rxn.thermodynamics sys:is_a
set.add name="ontology.chemistry_reactions" id="chem:thermo:activation_energy"

def "chem:thermo:endothermic" "A process or reaction in which the system absorbs energy from its surroundings."
ln chem:thermo:endothermic chem_rxn.thermodynamics sys:is_a
set.add name="ontology.chemistry_reactions" id="chem:thermo:endothermic"

def "chem:thermo:enthalpy" "A thermodynamic quantity equivalent to the total heat content of a system."
ln chem:thermo:enthalpy chem_rxn.thermodynamics sys:is_a
set.add name="ontology.chemistry_reactions" id="chem:thermo:enthalpy"

def "chem:thermo:entropy" "A thermodynamic quantity representing the unavailability of a system's thermal energy for conversion into mechanical work, often interpreted as the degree of disorder."
ln chem:thermo:entropy chem_rxn.thermodynamics sys:is_a
set.add name="ontology.chemistry_reactions" id="chem:thermo:entropy"

def "chem:thermo:exothermic" "A process or reaction that releases energy from the system to its surroundings, usually in the form of heat."
ln chem:thermo:exothermic chem_rxn.thermodynamics sys:is_a
set.add name="ontology.chemistry_reactions" id="chem:thermo:exothermic"
