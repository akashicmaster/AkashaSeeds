# Akasha ontology — namespace: bio
# atoms: 51

def "bio:concept:anticodon" "A sequence of three nucleotides in tRNA that is complementary to a specific mRNA codon."

def "bio:concept:central_dogma" "The framework describing the flow of genetic information: DNA is transcribed to RNA, which is translated to protein."
ln bio:concept:central_dogma bio:process:transcription sys:part_of
ln bio:concept:central_dogma bio:process:translation sys:part_of
ln bio:concept:central_dogma bio:process:dna_replication sys:part_of

def "bio:concept:codon" "A sequence of three nucleotides in mRNA that specifies a particular amino acid or stop signal during translation."
ln bio:concept:codon bio:concept:anticodon @binds_to
ln bio:concept:codon chem:amino:amino_acid @codes_for_type

def "bio:concept:gene" "A sequence of DNA that encodes a functional product, typically a protein or RNA molecule."
ln bio:concept:gene chem:polymer:dna sys:part_of

def "bio:enzyme:active_site" "The region of an enzyme or catalyst where substrate molecules bind and undergo a chemical reaction."

def "bio:enzyme:hydrolase" "An enzyme that catalyzes the hydrolysis of a chemical bond."
ln bio:enzyme:hydrolase chem:protein:enzyme sys:is_a
ln bio:enzyme:hydrolase chem:reaction:hydrolysis @catalyzes

def "bio:enzyme:isomerase" "An enzyme that catalyzes the structural rearrangement of isomers."
ln bio:enzyme:isomerase chem:protein:enzyme sys:is_a

def "bio:enzyme:ligase" "An enzyme that catalyzes the joining of two large molecules by forming a new chemical bond, usually with accompanying hydrolysis of ATP."
ln bio:enzyme:ligase chem:protein:enzyme sys:is_a

def "bio:enzyme:lyase" "An enzyme that catalyzes the breaking of various chemical bonds by means other than hydrolysis and oxidation, often forming a new double bond."
ln bio:enzyme:lyase chem:protein:enzyme sys:is_a

def "bio:enzyme:oxidoreductase" "An enzyme that catalyzes the transfer of electrons from one molecule to another."
ln bio:enzyme:oxidoreductase chem:protein:enzyme sys:is_a
ln bio:enzyme:oxidoreductase chem:rxn:redox @catalyzes

def "bio:enzyme:substrate" "The substance on which an enzyme acts."
ln bio:enzyme:substrate bio:enzyme:active_site @binds_to

def "bio:enzyme:transferase" "An enzyme that catalyzes the transfer of a specific functional group from one molecule to another."
ln bio:enzyme:transferase chem:protein:enzyme sys:is_a

def "bio:hormone:adrenaline" "A hormone involved in regulating visceral functions (e.g., respiration, fight-or-flight response)."

def "bio:hormone:cortisol" "A steroid hormone produced by the adrenal gland, released in response to stress and low blood-glucose concentration."
ln bio:hormone:cortisol bio:metabolism:catabolism @promotes

def "bio:hormone:estrogen" "A category of sex hormone responsible for the development and regulation of the female reproductive system."

def "bio:hormone:glucagon" "A peptide hormone produced by alpha cells of the pancreas; raises the concentration of glucose in the bloodstream."
ln bio:hormone:glucagon chem:carbo:glucose @stimulates_release_of
ln bio:hormone:glucagon bio:metabolism:catabolism @promotes

def "bio:hormone:insulin" "A peptide hormone produced by beta cells of the pancreas; the main anabolic hormone of the body."
ln bio:hormone:insulin chem:carbo:glucose @regulates_uptake_of
ln bio:hormone:insulin bio:metabolism:anabolism @promotes
ln bio:hormone:insulin med:condition:diabetes @associated_with

def "bio:hormone:testosterone" "The primary sex hormone and anabolic steroid in males."

def "bio:mechanism:allosteric_regulation" "The regulation of an enzyme by binding an effector molecule at a site other than the enzyme's active site."

def "bio:mechanism:competitive_inhibition" "Interruption of a chemical pathway owing to one chemical substance inhibiting the effect of another by competing with it for binding at the active site."
ln bio:mechanism:competitive_inhibition bio:enzyme:active_site @blocks

def "bio:mechanism:induced_fit_model" "A model proposing that the initial interaction rapidly induces conformational changes in the enzyme that strengthen binding."
ln bio:mechanism:induced_fit_model bio:enzyme:substrate @describes

def "bio:mechanism:lock_and_key_model" "A model for enzyme-substrate interaction suggesting that the enzyme and the substrate possess specific complementary geometric shapes."
ln bio:mechanism:lock_and_key_model bio:enzyme:substrate @describes

def "bio:metabolism:absorption" "The process of absorbing or assimilating substances into cells or across the tissues and organs."

def "bio:metabolism:anabolism" "The set of metabolic pathways that construct molecules from smaller units, requiring energy."
ln bio:metabolism:anabolism nutri:diet:calorie @requires
ln bio:metabolism:anabolism bio:metabolism:metabolism sys:part_of

def "bio:metabolism:catabolism" "The set of metabolic pathways that breaks down molecules into smaller units to release energy."
ln bio:metabolism:catabolism nutri:diet:calorie @releases
ln bio:metabolism:catabolism bio:metabolism:metabolism sys:part_of

def "bio:metabolism:cellular_respiration" "A set of metabolic reactions in cells to convert biochemical energy from nutrients into ATP."
ln bio:metabolism:cellular_respiration chem:carbo:glucose @consumes
ln bio:metabolism:cellular_respiration chem:compound:atp @produces

def "bio:metabolism:digestion" "The breakdown of large insoluble food molecules into small water-soluble food molecules so that they can be absorbed into the blood plasma."
ln bio:metabolism:digestion bio:metabolism:absorption @precedes
ln bio:metabolism:digestion chem:reaction:hydrolysis @utilizes
ln bio:metabolism:digestion bio:enzyme:hydrolase @requires

def "bio:metabolism:metabolism" "The set of life-sustaining chemical reactions in organisms, divided into catabolism and anabolism."

def "bio:molecule:mrna" "Messenger RNA; a single-stranded RNA molecule transcribed from DNA that carries the coding sequence for protein synthesis."

def "bio:molecule:ribosome" "A complex molecular machine found in living cells that performs biological protein synthesis."
ln bio:molecule:ribosome bio:molecule:rrna sys:part_of

def "bio:molecule:rna_polymerase" "An enzyme that synthesizes RNA from a DNA template during transcription."

def "bio:molecule:rrna" "Ribosomal RNA; the RNA component of the ribosome, essential for peptide-bond formation."

def "bio:molecule:trna" "Transfer RNA; an adaptor molecule that decodes mRNA codons and delivers the corresponding amino acid to the ribosome."
ln bio:molecule:trna chem:amino:amino_acid @transports_type

def "bio:neurotransmitter:acetylcholine" "An organic chemical that functions in the brain and body as a neurotransmitter, playing a role in muscle movement and memory."

def "bio:neurotransmitter:dopamine" "A neuromodulatory molecule that plays several important roles in cells, heavily involved in reward-motivated behavior."

def "bio:neurotransmitter:serotonin" "A monoamine neurotransmitter with complex functions, modulating mood, cognition, reward, and physiological processes."

def "bio:olfaction:olfactory_receptor" "Proteins expressed in the cell membranes of olfactory receptor neurons, responsible for the detection of odorants."
ln bio:olfaction:olfactory_receptor prop:chem:volatility @requires

def "bio:process:dna_replication" "The biological process of producing two identical copies of DNA from one original DNA molecule."

def "bio:process:transcription" "The synthesis of RNA from a DNA template by RNA polymerase."
ln bio:process:transcription chem:polymer:dna @reads
ln bio:process:transcription bio:molecule:mrna @produces
ln bio:process:transcription bio:molecule:rna_polymerase @requires

def "bio:process:translation" "The ribosomal process of synthesizing a protein from an mRNA template."
ln bio:process:translation bio:molecule:mrna @reads
ln bio:process:translation bio:molecule:ribosome @requires
ln bio:process:translation bio:molecule:trna @requires
ln bio:process:translation chem:structure:primary @produces

def "bio:receptor:receptor" "A protein molecule that receives chemical signals from outside a cell."

def "bio:receptor:transporter" "A membrane protein involved in the movement of ions, small molecules, and macromolecules across a biological membrane."

def "bio:role:antioxidant" "A molecule that inhibits the oxidation of other molecules, preventing cellular damage from free radicals."

def "bio:role:coenzyme" "Organic non-protein molecules that bind with the protein molecule (apoenzyme) to form the active enzyme (holoenzyme)."
ln bio:role:coenzyme bio:enzyme:active_site @assists

def "bio:role:cofactor" "A non-protein chemical compound or metallic ion that is required for an enzyme's role as a catalyst."
ln bio:role:cofactor bio:enzyme:active_site @assists

def "bio:role:energy_source" "A primary function of carbohydrates in biological systems, providing fuel for cellular respiration."

def "bio:structure:cell_membrane" "A biological membrane that separates the interior of all cells from the outside environment, primarily composed of a phospholipid bilayer."
ln bio:structure:cell_membrane chem:lipid:phospholipid @composed_of
ln bio:structure:cell_membrane chem:lipid:cholesterol @contains

def "bio:system:circulatory_system" "An organ system that permits blood to circulate and transport nutrients, oxygen, carbon dioxide, hormones, and blood cells."

def "bio:system:endocrine_system" "A messenger system comprising feedback loops of hormones released by internal glands of an organism directly into the circulatory system."
ln bio:system:endocrine_system bio:hormone:insulin @secretes
ln bio:system:endocrine_system bio:hormone:adrenaline @secretes

def "bio:system:immune_system" "A host defense system comprising many biological structures and processes within an organism that protects against disease."

def "bio:system:nervous_system" "The highly complex part of an animal that coordinates its actions and sensory information by transmitting signals."
ln bio:system:nervous_system bio:neurotransmitter:dopamine @utilizes
ln bio:system:nervous_system bio:neurotransmitter:serotonin @utilizes
