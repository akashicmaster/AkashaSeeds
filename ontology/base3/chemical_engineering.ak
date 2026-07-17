# Akasha ontology — chemical engineering (化学工学).
# chem: is rich at the substance/reaction level; this adds the PROCESS level —
# unit operations, reaction engineering and plant design. Bridged to chem:,
# energy:, mfg: and foodsci: (bioprocess). Base pack.

def "chemeng" "Chemical engineering — designing processes that transform matter at scale (化学工学)."
# ── core & transport ──
def "chemeng:unit_operations" "The standard physical steps of a process (distillation, filtration…) (単位操作)."
ln chemeng:unit_operations chemeng thesaurus:related
def "chemeng:reaction_engineering" "Designing and sizing chemical reactors (反応工学)."
ln chemeng:reaction_engineering chemeng thesaurus:related
def "chemeng:process_design" "Configuring equipment into a working plant (プロセス設計)."
ln chemeng:process_design chemeng thesaurus:related
def "chemeng:transport_phenomena" "The unified study of momentum, heat and mass transfer (移動現象)."
ln chemeng:transport_phenomena chemeng thesaurus:related
ln chemeng:transport_phenomena mecheng:heat_transfer thesaurus:related
ln chemeng:transport_phenomena mecheng:fluid_mechanics thesaurus:related
def "chemeng:mass_transfer" "The movement of species between phases."
ln chemeng:mass_transfer chemeng thesaurus:related
def "chemeng:mass_balance" "Accounting for all matter in and out of a process (物質収支)."
ln chemeng:mass_balance chemeng thesaurus:related
def "chemeng:energy_balance" "Accounting for all energy in and out (エネルギー収支)."
ln chemeng:energy_balance chemeng thesaurus:related
ln chemeng:energy_balance mecheng:thermodynamics thesaurus:related
def "chemeng:process_control" "Regulating a process to hold set conditions."
ln chemeng:process_control chemeng thesaurus:related
ln chemeng:process_control electron:microcontroller thesaurus:related
def "chemeng:scale_up" "Moving a process from lab to plant scale."
ln chemeng:scale_up chemeng thesaurus:related
# ── unit operations & reactors ──
def "chemeng:distillation" "Separating liquids by boiling point (蒸留)."
ln chemeng:distillation chemeng thesaurus:related
ln chemeng:distillation chemeng:unit_operations thesaurus:related
def "chemeng:extraction" "Separating by preferential dissolution in a solvent (抽出)."
ln chemeng:extraction chemeng thesaurus:related
def "chemeng:filtration" "Separating solids from fluids (ろ過)."
ln chemeng:filtration chemeng thesaurus:related
def "chemeng:crystallization" "Forming solid crystals from solution (晶析)."
ln chemeng:crystallization chemeng thesaurus:related
ln chemeng:crystallization chemeng:unit_operations thesaurus:related
def "chemeng:absorption" "Dissolving a gas into a liquid to separate it."
ln chemeng:absorption chemeng thesaurus:related
def "chemeng:adsorption" "Adhering molecules onto a surface to separate them."
ln chemeng:adsorption chemeng thesaurus:related
def "chemeng:heat_exchanger" "A device transferring heat between streams (熱交換器)."
ln chemeng:heat_exchanger chemeng thesaurus:related
def "chemeng:reactor" "A vessel where chemical reactions are carried out (反応器)."
ln chemeng:reactor chemeng thesaurus:related
def "chemeng:catalysis" "Speeding a reaction with a catalyst that is not consumed (触媒作用)."
ln chemeng:catalysis chemeng thesaurus:related
ln chemeng:catalysis chemeng:reactor thesaurus:related
def "chemeng:catalyst" "A substance that accelerates a reaction (触媒)."
ln chemeng:catalyst chemeng thesaurus:related
def "chemeng:reaction_kinetics" "The rates and mechanisms of reactions (反応速度論)."
ln chemeng:reaction_kinetics chemeng thesaurus:related
def "chemeng:bioprocess" "Using living cells/enzymes to make products at scale (fermentation, brewing)."
ln chemeng:bioprocess chemeng thesaurus:related
ln chemeng:bioprocess foodsci:fermentation_science thesaurus:related
ln chemeng:bioprocess futurefood:precision_fermentation thesaurus:related
def "chemeng:petrochemical" "Chemicals and fuels derived from petroleum (石油化学)."
ln chemeng:petrochemical chemeng thesaurus:related
ln chemeng:petrochemical energy:fossil thesaurus:related
ln chemeng:petrochemical matsci:polymer thesaurus:related
