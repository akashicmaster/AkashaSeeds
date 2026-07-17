# Akasha ontology — mathematics (数学).
# Nearly greenfield (math: had 4). Branches, core objects and applied fields,
# bridged to person:field:mathematics, phys:/econ:/ai:/bib:/research:. Base pack.

def "math" "Mathematics — the science of number, structure, space and change (数学)."
ln math person:field:mathematics thesaurus:related
# ── branches ──
def "math:arithmetic" "The study of numbers and basic operations (算術)."
ln math:arithmetic math thesaurus:related
def "math:algebra" "The study of structure and of solving with symbols (代数学)."
ln math:algebra math thesaurus:related
def "math:geometry" "The study of shape, size and space (幾何学)."
ln math:geometry math thesaurus:related
def "math:calculus" "The study of continuous change — derivatives and integrals (微積分)."
ln math:calculus math thesaurus:related
ln math:calculus mecheng:dynamics thesaurus:related
ln math:calculus econ:marginal_utility thesaurus:related
def "math:analysis" "The rigorous study of limits, continuity and functions (解析学)."
ln math:analysis math thesaurus:related
def "math:number_theory" "The study of the integers and primes (数論)."
ln math:number_theory math thesaurus:related
def "math:topology" "The study of properties preserved under continuous deformation (位相幾何学)."
ln math:topology math thesaurus:related
def "math:probability" "The mathematics of chance and uncertainty (確率論)."
ln math:probability math thesaurus:related
ln math:probability risk:expected_value thesaurus:related
ln math:probability insur:actuarial_science thesaurus:related
def "math:statistics" "The science of collecting, analysing and inferring from data (統計学)."
ln math:statistics math thesaurus:related
ln math:statistics research:method:quantitative thesaurus:related
ln math:statistics bib:bibliometrics thesaurus:related
ln math:statistics med:evidence:biostatistics thesaurus:related
def "math:discrete_mathematics" "The mathematics of countable, distinct structures (離散数学)."
ln math:discrete_mathematics math thesaurus:related
def "math:logic" "The study of valid reasoning and formal systems (論理学)."
ln math:logic math thesaurus:related
ln math:logic law:concept:ratio_decidendi thesaurus:related
def "math:linear_algebra" "The study of vectors, matrices and linear maps (線形代数)."
ln math:linear_algebra math thesaurus:related
ln math:linear_algebra ai:embedding thesaurus:related
ln math:linear_algebra matsci:crystal_structure thesaurus:related
def "math:graph_theory" "The study of networks of nodes and edges (グラフ理論)."
ln math:graph_theory math thesaurus:related
ln math:graph_theory sys:network thesaurus:related
ln math:graph_theory cite:citation_network thesaurus:related
ln math:graph_theory dh:social_network_analysis thesaurus:related
def "math:optimization" "Finding the best solution under constraints (最適化)."
ln math:optimization math thesaurus:related
ln math:optimization invest:modern_portfolio_theory thesaurus:related
ln math:optimization ai:reinforcement_learning thesaurus:related
ln math:optimization chemeng:process_design thesaurus:related
# ── core objects & ideas ──
def "math:function" "A rule mapping inputs to outputs (関数)."
ln math:function math thesaurus:related
def "math:set" "A collection of distinct objects (集合)."
ln math:set math thesaurus:related
def "math:proof" "A rigorous demonstration that a statement is true (証明)."
ln math:proof math thesaurus:related
ln math:proof math:logic thesaurus:related
ln math:proof research:evidence thesaurus:related
def "math:theorem" "A proven mathematical statement (定理)."
ln math:theorem math thesaurus:related
def "math:axiom" "An assumed starting truth of a system (公理)."
ln math:axiom math thesaurus:related
def "math:equation" "A statement that two expressions are equal (方程式)."
ln math:equation math thesaurus:related
def "math:matrix" "A rectangular array of numbers (行列)."
ln math:matrix math thesaurus:related
ln math:matrix ai:embedding thesaurus:related
def "math:vector" "A quantity with magnitude and direction (ベクトル)."
ln math:vector math thesaurus:related
ln math:vector ai:embedding thesaurus:related
ln math:vector math:linear_algebra thesaurus:related
def "math:derivative" "The instantaneous rate of change of a function (微分)."
ln math:derivative math thesaurus:related
def "math:integral" "The accumulation/area under a function (積分)."
ln math:integral math thesaurus:related
def "math:limit" "The value a function approaches (極限)."
ln math:limit math thesaurus:related
def "math:prime_number" "A number divisible only by 1 and itself (素数)."
ln math:prime_number math thesaurus:related
ln math:prime_number net:encryption thesaurus:related
ln math:prime_number math:number_theory thesaurus:related
def "math:infinity" "The concept of the boundless (無限)."
ln math:infinity math thesaurus:related
def "math:symmetry" "Invariance under transformation (対称性)."
ln math:symmetry math thesaurus:related
ln math:symmetry matsci:crystal_structure thesaurus:related
ln math:symmetry math:geometry thesaurus:related
