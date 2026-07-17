# Akasha ontology — the knowledge map: a cross-cutting overview of ALL domains.
# A capstone META layer. Part 1 classifies the domains built across this work
# into the branches of knowledge. Part 2 defines the UNIFYING concepts that recur
# across domains (system, network, evolution, information…), each bridging to the
# many fields where it manifests — the transversal 俯瞰 (consilience). Base pack.

def "knowledge" "The organised map of human knowledge and its domains (知の体系)."
def "knowledge:branch:natural_science" "自然科学 — the study of nature."
ln knowledge:branch:natural_science knowledge thesaurus:related
def "knowledge:branch:formal_science" "形式科学 — the study of formal systems (math, logic, computation)."
ln knowledge:branch:formal_science knowledge thesaurus:related
def "knowledge:branch:social_science" "社会科学 — the study of society and human behaviour."
ln knowledge:branch:social_science knowledge thesaurus:related
def "knowledge:branch:humanities" "人文学 — the study of human culture, thought and expression."
ln knowledge:branch:humanities knowledge thesaurus:related
def "knowledge:branch:applied_science" "応用科学・工学 — knowledge applied to practical ends."
ln knowledge:branch:applied_science knowledge thesaurus:related
def "knowledge:branch:arts" "芸術 — creative and performing arts."
ln knowledge:branch:arts knowledge thesaurus:related
def "knowledge:branch:interdisciplinary" "学際 — fields spanning several branches."
ln knowledge:branch:interdisciplinary knowledge thesaurus:related

# ── classify the domains into branches ──
ln ecol knowledge:branch:natural_science knowledge:in_branch
ln enveng knowledge:branch:natural_science knowledge:in_branch
ln agron knowledge:branch:natural_science knowledge:in_branch
ln life knowledge:branch:natural_science knowledge:in_branch
ln earthsci knowledge:branch:natural_science knowledge:in_branch
ln astrophys knowledge:branch:natural_science knowledge:in_branch
ln foodsci knowledge:branch:natural_science knowledge:in_branch
ln math knowledge:branch:formal_science knowledge:in_branch
ln cs knowledge:branch:formal_science knowledge:in_branch
ln socio knowledge:branch:social_science knowledge:in_branch
ln econ knowledge:branch:social_science knowledge:in_branch
ln psy knowledge:branch:social_science knowledge:in_branch
ln socwork knowledge:branch:social_science knowledge:in_branch
ln geog knowledge:branch:social_science knowledge:in_branch
ln ling knowledge:branch:humanities knowledge:in_branch
ln phil:philosophy knowledge:branch:humanities knowledge:in_branch
ln artsci knowledge:branch:humanities knowledge:in_branch
ln archaeo knowledge:branch:humanities knowledge:in_branch
ln foodstud knowledge:branch:humanities knowledge:in_branch
ln med:medicine knowledge:branch:applied_science knowledge:in_branch
ln nursing knowledge:branch:applied_science knowledge:in_branch
ln care knowledge:branch:applied_science knowledge:in_branch
ln rehab knowledge:branch:applied_science knowledge:in_branch
ln chemeng knowledge:branch:applied_science knowledge:in_branch
ln matsci knowledge:branch:applied_science knowledge:in_branch
ln resource knowledge:branch:applied_science knowledge:in_branch
ln mecheng knowledge:branch:applied_science knowledge:in_branch
ln eleceng knowledge:branch:applied_science knowledge:in_branch
ln electron knowledge:branch:applied_science knowledge:in_branch
ln bme knowledge:branch:applied_science knowledge:in_branch
ln law:law knowledge:branch:applied_science knowledge:in_branch
ln occupation knowledge:branch:applied_science knowledge:in_branch
ln artsci knowledge:branch:arts knowledge:in_branch
ln dh knowledge:branch:interdisciplinary knowledge:in_branch
ln bib knowledge:branch:interdisciplinary knowledge:in_branch
ln academia knowledge:branch:interdisciplinary knowledge:in_branch
ln cite knowledge:branch:interdisciplinary knowledge:in_branch
ln collab knowledge:branch:interdisciplinary knowledge:in_branch
ln nutrisci knowledge:branch:interdisciplinary knowledge:in_branch
ln sportsci knowledge:branch:interdisciplinary knowledge:in_branch
ln neuro knowledge:branch:interdisciplinary knowledge:in_branch
ln devpsy knowledge:branch:interdisciplinary knowledge:in_branch
ln edupsy knowledge:branch:interdisciplinary knowledge:in_branch
ln pedagogy knowledge:branch:interdisciplinary knowledge:in_branch
ln work knowledge:branch:interdisciplinary knowledge:in_branch
ln sensory knowledge:branch:interdisciplinary knowledge:in_branch

def "knowledge:cognitive_science" "Cognitive science — the convergence of psychology, neuroscience, linguistics, philosophy of mind and AI on the mind."
ln knowledge:cognitive_science knowledge:branch:interdisciplinary thesaurus:related
ln knowledge:cognitive_science psy thesaurus:related
ln knowledge:cognitive_science neuro thesaurus:related
ln knowledge:cognitive_science ling thesaurus:related
ln knowledge:cognitive_science phil:field:philosophy_of_mind thesaurus:related
ln knowledge:cognitive_science ai:embedding thesaurus:related

# ══ PART 2: cross-cutting unifying concepts (分野横断の統一概念) ══
def "crosscut" "A concept that recurs across many domains — the threads that unify knowledge (通底概念)."
def "crosscut:system" "A set of interacting parts forming a whole."
ln crosscut:system crosscut thesaurus:related
ln crosscut:system socio:social_institution crosscut:manifests_in
ln crosscut:system ecol:ecosystem crosscut:manifests_in
ln crosscut:system mecheng:mechatronics crosscut:manifests_in
ln crosscut:system gov:function:public_works crosscut:manifests_in
ln crosscut:system econ:market crosscut:manifests_in
ln crosscut:system cs:algorithm crosscut:manifests_in
ln crosscut:system earthsci:hydrology crosscut:manifests_in
def "crosscut:network" "A structure of nodes and connections."
ln crosscut:network crosscut thesaurus:related
ln crosscut:network sys:network crosscut:manifests_in
ln crosscut:network cite:citation_network crosscut:manifests_in
ln crosscut:network collab:coauthorship_network crosscut:manifests_in
ln crosscut:network dh:social_network_analysis crosscut:manifests_in
ln crosscut:network neuro:neural_network crosscut:manifests_in
ln crosscut:network ecol:food_web crosscut:manifests_in
ln crosscut:network ling:language_family crosscut:manifests_in
ln crosscut:network life:phylogeny crosscut:manifests_in
ln crosscut:network math:graph_theory crosscut:manifests_in
ln crosscut:network infra:electricity_supply crosscut:manifests_in
def "crosscut:structure" "The arrangement of parts that gives a whole its form."
ln crosscut:structure crosscut thesaurus:related
ln crosscut:structure socio:social_structure crosscut:manifests_in
ln crosscut:structure matsci:crystal_structure crosscut:manifests_in
ln crosscut:structure ling:syntax crosscut:manifests_in
ln crosscut:structure ms:quire crosscut:manifests_in
ln crosscut:structure math:set crosscut:manifests_in
ln crosscut:structure law:law crosscut:manifests_in
def "crosscut:process" "A sequence of steps transforming inputs to outputs."
ln crosscut:process crosscut thesaurus:related
ln crosscut:process chemeng:unit_operations crosscut:manifests_in
ln crosscut:process research:methodology crosscut:manifests_in
ln crosscut:process nursing:nursing_assessment crosscut:manifests_in
ln crosscut:process law:process:litigation crosscut:manifests_in
ln crosscut:process work:promotion crosscut:manifests_in
def "crosscut:feedback" "Output looping back to regulate a system."
ln crosscut:feedback crosscut thesaurus:related
ln crosscut:feedback mecheng:control_system crosscut:manifests_in
ln crosscut:feedback econ:monetary_policy crosscut:manifests_in
ln crosscut:feedback ecol:carrying_capacity crosscut:manifests_in
ln crosscut:feedback edupsy:feedback crosscut:manifests_in
ln crosscut:feedback org:coaching crosscut:manifests_in
def "crosscut:equilibrium" "A balanced state of opposing forces."
ln crosscut:equilibrium crosscut thesaurus:related
ln crosscut:equilibrium econ:equilibrium_price crosscut:manifests_in
ln crosscut:equilibrium ecol:ecological_succession crosscut:manifests_in
ln crosscut:equilibrium matsci:phase_diagram crosscut:manifests_in
ln crosscut:equilibrium astrophys:stellar_evolution crosscut:manifests_in
def "crosscut:evolution" "Change and selection over time producing complexity."
ln crosscut:evolution crosscut thesaurus:related
ln crosscut:evolution life:evolution crosscut:manifests_in
ln crosscut:evolution ling:language_change crosscut:manifests_in
ln crosscut:evolution socio:social_change crosscut:manifests_in
ln crosscut:evolution astrophys:stellar_evolution crosscut:manifests_in
ln crosscut:evolution cs:algorithm crosscut:manifests_in
ln crosscut:evolution art:movement crosscut:manifests_in
def "crosscut:information" "Structured difference that reduces uncertainty."
ln crosscut:information crosscut thesaurus:related
ln crosscut:information cs:information_theory crosscut:manifests_in
ln crosscut:information ling:semantics crosscut:manifests_in
ln crosscut:information dh:knowledge_graph crosscut:manifests_in
ln crosscut:information metastd:dublin_core crosscut:manifests_in
ln crosscut:information neuro:semantic_memory crosscut:manifests_in
ln crosscut:information bib:bibliometrics crosscut:manifests_in
ln crosscut:information rdm:metadata crosscut:manifests_in
def "crosscut:energy" "The capacity to do work, conserved and transformed."
ln crosscut:energy crosscut thesaurus:related
ln crosscut:energy mecheng:thermodynamics crosscut:manifests_in
ln crosscut:energy energy:transmission crosscut:manifests_in
ln crosscut:energy life:cellular_respiration crosscut:manifests_in
ln crosscut:energy astrophys:nuclear_fusion crosscut:manifests_in
ln crosscut:energy econ:capital crosscut:manifests_in
ln crosscut:energy sportsci:aerobic_capacity crosscut:manifests_in
def "crosscut:scale" "The span from the very small to the very large."
ln crosscut:scale crosscut thesaurus:related
ln crosscut:scale admin_scale:5 crosscut:manifests_in
ln crosscut:scale astrophys:light_year crosscut:manifests_in
ln crosscut:scale matsci:nanomaterial crosscut:manifests_in
ln crosscut:scale chemeng:scale_up crosscut:manifests_in
ln crosscut:scale math:infinity crosscut:manifests_in
def "crosscut:optimization" "Finding the best outcome under constraints."
ln crosscut:optimization crosscut thesaurus:related
ln crosscut:optimization math:optimization crosscut:manifests_in
ln crosscut:optimization invest:modern_portfolio_theory crosscut:manifests_in
ln crosscut:optimization ai:reinforcement_learning crosscut:manifests_in
ln crosscut:optimization chemeng:process_design crosscut:manifests_in
ln crosscut:optimization resource:resource_management crosscut:manifests_in
ln crosscut:optimization sportsci:strength_conditioning crosscut:manifests_in
def "crosscut:adaptation" "Adjusting to fit a changing environment."
ln crosscut:adaptation crosscut thesaurus:related
ln crosscut:adaptation life:natural_selection crosscut:manifests_in
ln crosscut:adaptation neuro:neuroplasticity crosscut:manifests_in
ln crosscut:adaptation edupsy:self_regulated_learning crosscut:manifests_in
ln crosscut:adaptation futureag:drought_resistant_crop crosscut:manifests_in
ln crosscut:adaptation socio:socialization crosscut:manifests_in
def "crosscut:cycle" "A recurring sequence returning to its start."
ln crosscut:cycle crosscut thesaurus:related
ln crosscut:cycle ecol:carbon_cycle crosscut:manifests_in
ln crosscut:cycle earthsci:rock_cycle crosscut:manifests_in
ln crosscut:cycle econ:business_cycle crosscut:manifests_in
ln crosscut:cycle resource:circular_economy crosscut:manifests_in
ln crosscut:cycle foodsustain:circular_food_economy crosscut:manifests_in
def "crosscut:hierarchy" "Levels ordered by inclusion or rank."
ln crosscut:hierarchy crosscut thesaurus:related
ln crosscut:hierarchy admin:within crosscut:manifests_in
ln crosscut:hierarchy status:outranks crosscut:manifests_in
ln crosscut:hierarchy socio:social_stratification crosscut:manifests_in
ln crosscut:hierarchy org:hierarchy crosscut:manifests_in
ln crosscut:hierarchy edupsy:bloom_taxonomy crosscut:manifests_in
ln crosscut:hierarchy acad:outranks crosscut:manifests_in
def "crosscut:emergence" "Higher-order patterns arising from simple interactions."
ln crosscut:emergence crosscut thesaurus:related
ln crosscut:emergence socio:collective_behavior crosscut:manifests_in
ln crosscut:emergence life:evolution crosscut:manifests_in
ln crosscut:emergence neuro:consciousness crosscut:manifests_in
ln crosscut:emergence ecol:ecosystem crosscut:manifests_in
ln crosscut:emergence econ:market crosscut:manifests_in
def "crosscut:symmetry" "Invariance under transformation."
ln crosscut:symmetry crosscut thesaurus:related
ln crosscut:symmetry math:symmetry crosscut:manifests_in
ln crosscut:symmetry matsci:crystal_structure crosscut:manifests_in
ln crosscut:symmetry artsci:composition crosscut:manifests_in
ln crosscut:symmetry sys:antonym crosscut:manifests_in
def "crosscut:scarcity" "Limited means against unlimited wants."
ln crosscut:scarcity crosscut thesaurus:related
ln crosscut:scarcity econ:scarcity crosscut:manifests_in
ln crosscut:scarcity resource:resource_depletion crosscut:manifests_in
ln crosscut:scarcity ecol:carrying_capacity crosscut:manifests_in
ln crosscut:scarcity foodsec:food_security crosscut:manifests_in

# ── ways of knowing (認識の方法) ──
def "knowledge:method:empirical" "knowing from observation and data."
ln knowledge:method:empirical knowledge thesaurus:related
def "knowledge:method:theoretical" "knowing by building models and theory."
ln knowledge:method:theoretical knowledge thesaurus:related
def "knowledge:method:experimental" "knowing by controlled intervention."
ln knowledge:method:experimental knowledge thesaurus:related
def "knowledge:method:interpretive" "knowing by understanding meaning (Verstehen)."
ln knowledge:method:interpretive knowledge thesaurus:related
def "knowledge:method:computational" "knowing by simulation and computation."
ln knowledge:method:computational knowledge thesaurus:related
ln knowledge:method:empirical research:method:empirical thesaurus:related
ln knowledge:method:experimental research:experiment thesaurus:related
ln knowledge:method:interpretive socio:ethnography thesaurus:related
ln knowledge:method:computational cs:algorithm thesaurus:related
ln knowledge research:induction thesaurus:related
ln knowledge research:deduction thesaurus:related
