# Akasha ontology — philosophy, organised into branches (哲学).
# phil: is rich in concepts; this adds the BRANCH structure and key positions,
# linking existing phil: concepts and bridging socio:/law:/psy:/math:logic. Base pack.

def "phil:philosophy" "Philosophy — the rational inquiry into fundamental questions (哲学)."
def "phil:field:metaphysics" "The study of being, reality and existence (形而上学)."
ln phil:field:metaphysics phil:philosophy thesaurus:related
def "phil:field:epistemology" "The study of knowledge, belief and justification (認識論)."
ln phil:field:epistemology phil:philosophy thesaurus:related
def "phil:field:ethics" "The study of right action and the good life (倫理学)."
ln phil:field:ethics phil:philosophy thesaurus:related
ln phil:field:ethics law:concept:natural_law thesaurus:related
ln phil:field:ethics socio:value thesaurus:related
ln phil:field:ethics med:clinical:informed_consent thesaurus:related
def "phil:field:aesthetics" "The philosophy of beauty and art (美学)."
ln phil:field:aesthetics phil:philosophy thesaurus:related
ln phil:field:aesthetics art:movement thesaurus:related
ln phil:field:aesthetics music thesaurus:related
def "phil:field:logic" "The study of valid inference and reasoning (論理学)."
ln phil:field:logic phil:philosophy thesaurus:related
ln phil:field:logic math:logic thesaurus:related
ln phil:field:logic cs:computability thesaurus:related
def "phil:field:political_philosophy" "The study of authority, justice and the state (政治哲学)."
ln phil:field:political_philosophy phil:philosophy thesaurus:related
ln phil:field:political_philosophy law:concept:social_contract thesaurus:related
ln phil:field:political_philosophy socio:power thesaurus:related
ln phil:field:political_philosophy econ:market thesaurus:related
def "phil:field:philosophy_of_mind" "The nature of mind, consciousness and the mental (心の哲学)."
ln phil:field:philosophy_of_mind phil:philosophy thesaurus:related
ln phil:field:philosophy_of_mind psy:consciousness thesaurus:related
ln phil:field:philosophy_of_mind neuro:cognitive_neuroscience thesaurus:related
ln phil:field:philosophy_of_mind phil:consciousness thesaurus:related
def "phil:field:philosophy_of_science" "The foundations, methods and implications of science (科学哲学)."
ln phil:field:philosophy_of_science phil:philosophy thesaurus:related
ln phil:field:philosophy_of_science research:hypothesis thesaurus:related
ln phil:field:philosophy_of_science research:induction thesaurus:related
ln phil:field:philosophy_of_science research:deduction thesaurus:related
def "phil:field:phenomenology" "The study of structures of experience and consciousness."
ln phil:field:phenomenology phil:philosophy thesaurus:related
# ── key positions & concepts ──
def "phil:free_will" "The question of whether we can act otherwise (自由意志)."
ln phil:free_will phil:philosophy thesaurus:related
ln phil:free_will phil:determinism thesaurus:related
ln phil:free_will neuro:prefrontal_cortex thesaurus:related
def "phil:justice" "Giving each their due; fairness in society (正義)."
ln phil:justice phil:philosophy thesaurus:related
ln phil:justice law:law thesaurus:related
ln phil:justice socio:inequality thesaurus:related
ln phil:justice econ:externality thesaurus:related
def "phil:virtue" "An excellent character trait (Aristotle) (徳)."
ln phil:virtue phil:philosophy thesaurus:related
ln phil:virtue phil:field:ethics thesaurus:related
ln phil:virtue socio:norm thesaurus:related
def "phil:truth" "The property of matching reality (真理)."
ln phil:truth phil:philosophy thesaurus:related
def "phil:knowledge" "Justified true belief, and its limits (知識)."
ln phil:knowledge phil:philosophy thesaurus:related
ln phil:knowledge phil:field:epistemology thesaurus:related
ln phil:knowledge phil:belief thesaurus:related
def "phil:utilitarianism" "The right act maximises overall happiness (功利主義)."
ln phil:utilitarianism phil:philosophy thesaurus:related
ln phil:utilitarianism econ:marginal_utility thesaurus:related
ln phil:utilitarianism phil:field:ethics thesaurus:related
def "phil:deontology" "Morality of duties and rules, not just outcomes (義務論)."
ln phil:deontology phil:philosophy thesaurus:related
def "phil:existentialism" "Meaning is made by the freely choosing individual (実存主義)."
ln phil:existentialism phil:philosophy thesaurus:related
def "phil:empiricism" "Knowledge comes from sensory experience (経験論)."
ln phil:empiricism phil:philosophy thesaurus:related
ln phil:empiricism research:method:empirical thesaurus:related
ln phil:empiricism phil:field:epistemology thesaurus:related
def "phil:rationalism" "Reason is a primary source of knowledge (合理論)."
ln phil:rationalism phil:philosophy thesaurus:related
ln phil:rationalism math:proof thesaurus:related
ln phil:rationalism phil:field:epistemology thesaurus:related
