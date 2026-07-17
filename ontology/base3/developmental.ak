# Akasha ontology — developmental psychology (発達心理学), deepened.
# Lifespan development, attachment, and the cognitive/social/moral strands.
# Bridged to psy:, kin:, school:, care: and neuro:. Base pack.

def "devpsy" "Developmental psychology — how mind and behaviour change across life (発達心理学)."
ln devpsy psy:developmental_psychology thesaurus:related

# ── lifespan stages (生涯発達) ──
def "devpsy:infancy" "Birth to ~2 years — rapid sensory and motor growth (乳児期)."
ln devpsy:infancy devpsy thesaurus:related
ln devpsy:infancy devpsy:early_childhood chrono:before
def "devpsy:early_childhood" "~2–6 years — language and imagination bloom (幼児期)."
ln devpsy:early_childhood devpsy thesaurus:related
ln devpsy:early_childhood devpsy:middle_childhood chrono:before
def "devpsy:middle_childhood" "~6–12 years — schooling and peer worlds (児童期)."
ln devpsy:middle_childhood devpsy thesaurus:related
ln devpsy:middle_childhood devpsy:adolescence chrono:before
def "devpsy:adolescence" "The teens — identity, puberty and autonomy (青年期)."
ln devpsy:adolescence devpsy thesaurus:related
ln devpsy:adolescence devpsy:adulthood chrono:before
def "devpsy:adulthood" "Maturity — work, partnership, generativity (成人期)."
ln devpsy:adulthood devpsy thesaurus:related
ln devpsy:adulthood devpsy:old_age chrono:before
def "devpsy:old_age" "Later life — reflection, loss and wisdom (老年期)."
ln devpsy:old_age devpsy thesaurus:related
ln devpsy:early_childhood home:childrens_room thesaurus:related
ln devpsy:middle_childhood school:elementary_school thesaurus:related
ln devpsy:adolescence school:high_school thesaurus:related
ln devpsy:old_age care:gerontology thesaurus:related

# ── attachment & socioemotional (愛着) ──
def "devpsy:attachment" "The emotional bond between infant and caregiver (Bowlby) (愛着)."
ln devpsy:attachment devpsy thesaurus:related
ln devpsy:attachment kin:parent_of thesaurus:related
ln devpsy:attachment emo:trust thesaurus:related
ln devpsy:attachment emo:adoration thesaurus:related
def "devpsy:secure_attachment" "A confident bond from responsive care — a base for exploration."
ln devpsy:secure_attachment devpsy thesaurus:related
ln devpsy:secure_attachment kin:child_of thesaurus:related
ln devpsy:secure_attachment emo:trust thesaurus:related
def "devpsy:insecure_attachment" "Anxious or avoidant bonds from inconsistent care."
ln devpsy:insecure_attachment devpsy thesaurus:related
def "devpsy:temperament" "Inborn individual differences in reactivity and mood."
ln devpsy:temperament devpsy thesaurus:related
ln devpsy:temperament psy:big_five thesaurus:related
def "devpsy:theory_of_mind" "Understanding that others have their own minds and beliefs (心の理論)."
ln devpsy:theory_of_mind devpsy thesaurus:related
ln devpsy:theory_of_mind counsel:empathy thesaurus:related
ln devpsy:theory_of_mind psy:social_psychology thesaurus:related
def "devpsy:erikson_stages" "Erikson's eight psychosocial crises across life."
ln devpsy:erikson_stages devpsy thesaurus:related
def "devpsy:identity_formation" "The adolescent task of forming a coherent self (Erikson)."
ln devpsy:identity_formation devpsy thesaurus:related
ln devpsy:identity_formation phil:identity thesaurus:related
ln devpsy:identity_formation psy:developmental_psychology thesaurus:related
# ── cognitive, language & moral development ──
def "devpsy:sensorimotor_stage" "Piaget's first stage — knowing through senses and action."
ln devpsy:sensorimotor_stage devpsy thesaurus:related
ln devpsy:sensorimotor_stage psy:piaget_stages thesaurus:related
def "devpsy:preoperational_stage" "Symbolic but pre-logical thought in early childhood."
ln devpsy:preoperational_stage devpsy thesaurus:related
def "devpsy:concrete_operational_stage" "Logical thought about concrete things."
ln devpsy:concrete_operational_stage devpsy thesaurus:related
def "devpsy:formal_operational_stage" "Abstract and hypothetical reasoning."
ln devpsy:formal_operational_stage devpsy thesaurus:related
ln devpsy:formal_operational_stage psy:piaget_stages thesaurus:related
ln devpsy:formal_operational_stage edupsy:cognitivism thesaurus:related
def "devpsy:language_acquisition" "How children come to understand and produce language (言語獲得)."
ln devpsy:language_acquisition devpsy thesaurus:related
ln devpsy:language_acquisition psy:cognition thesaurus:related
ln devpsy:language_acquisition neuro:cerebral_cortex thesaurus:related
def "devpsy:critical_period" "A window when development is especially sensitive to input."
ln devpsy:critical_period devpsy thesaurus:related
ln devpsy:critical_period neuro:neuroplasticity thesaurus:related
def "devpsy:nature_nurture" "The interplay of genes and environment in development."
ln devpsy:nature_nurture devpsy thesaurus:related
def "devpsy:developmental_milestone" "An age-typical achievement (first steps, first words)."
ln devpsy:developmental_milestone devpsy thesaurus:related
ln devpsy:developmental_milestone devpsy:infancy thesaurus:related
def "devpsy:scaffolded_development" "Growth supported within the zone of proximal development."
ln devpsy:scaffolded_development devpsy thesaurus:related
ln devpsy:scaffolded_development edupsy:zone_of_proximal_development thesaurus:related
