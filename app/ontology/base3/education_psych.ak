# Akasha ontology — educational psychology & education studies.
# The learning sciences and the study of teaching — cross-linking psy:, school:,
# teaching:, org: motivation, and ai: (human vs machine learning). Base pack.

def "edupsy" "Educational psychology — how people learn and how to teach effectively (教育心理学)."
ln edupsy psy thesaurus:related
ln edupsy school:teacher thesaurus:related

# ── learning theories ──
def "edupsy:learning_theory" "Accounts of how learning happens."
ln edupsy:learning_theory edupsy thesaurus:related
def "edupsy:behaviorism" "Learning as conditioned response to stimuli and reinforcement."
ln edupsy:behaviorism edupsy thesaurus:related
ln edupsy:behaviorism psy:operant_conditioning thesaurus:related
ln edupsy:behaviorism ai:reinforcement_learning thesaurus:related
def "edupsy:cognitivism" "Learning as active mental processing of information."
ln edupsy:cognitivism edupsy thesaurus:related
ln edupsy:cognitivism psy:cognition thesaurus:related
ln edupsy:cognitivism psy:working_memory thesaurus:related
def "edupsy:constructivism" "Learners actively build knowledge (Piaget) (構成主義)."
ln edupsy:constructivism edupsy thesaurus:related
ln edupsy:constructivism psy:piaget_stages thesaurus:related
def "edupsy:social_constructivism" "Knowledge is built through social interaction (Vygotsky)."
ln edupsy:social_constructivism edupsy thesaurus:related
ln edupsy:social_constructivism psy:vygotsky_sociocultural thesaurus:related
def "edupsy:connectivism" "Learning as forming connections across networks — apt for the digital, networked age."
ln edupsy:connectivism edupsy thesaurus:related
ln edupsy:connectivism sys:network thesaurus:related
ln edupsy:connectivism ai:embedding thesaurus:related
# ── learning processes & motivation ──
def "edupsy:motivation_to_learn" "What drives a learner to engage and persist."
ln edupsy:motivation_to_learn edupsy thesaurus:related
ln edupsy:motivation_to_learn org:intrinsic_motivation thesaurus:related
ln edupsy:motivation_to_learn org:extrinsic_motivation thesaurus:related
ln edupsy:motivation_to_learn psy:motivation thesaurus:related
def "edupsy:self_efficacy" "Belief in one's capacity to succeed (Bandura) (自己効力感)."
ln edupsy:self_efficacy edupsy thesaurus:related
ln edupsy:self_efficacy psy:bandura_social_learning thesaurus:related
def "edupsy:growth_mindset" "Belief that ability grows with effort (Dweck)."
ln edupsy:growth_mindset edupsy thesaurus:related
def "edupsy:zone_of_proximal_development" "The gap between what a learner can do alone and with help (ZPD/最近接発達領域)."
ln edupsy:zone_of_proximal_development edupsy thesaurus:related
ln edupsy:zone_of_proximal_development psy:vygotsky_sociocultural thesaurus:related
def "edupsy:scaffolding" "Temporary support that is withdrawn as competence grows (足場かけ)."
ln edupsy:scaffolding edupsy thesaurus:related
def "edupsy:metacognition" "Thinking about one's own thinking and learning (メタ認知)."
ln edupsy:metacognition edupsy thesaurus:related
ln edupsy:metacognition psy:cognition thesaurus:related
def "edupsy:cognitive_load" "The working-memory demand of a task."
ln edupsy:cognitive_load edupsy thesaurus:related
ln edupsy:cognitive_load psy:working_memory thesaurus:related
def "edupsy:self_regulated_learning" "Learners planning, monitoring and adjusting their own learning."
ln edupsy:self_regulated_learning edupsy thesaurus:related
def "edupsy:bloom_taxonomy" "A hierarchy of learning objectives from remembering to creating."
ln edupsy:bloom_taxonomy edupsy thesaurus:related
def "edupsy:moral_development" "Kohlberg's stages of moral reasoning."
ln edupsy:moral_development edupsy thesaurus:related
ln edupsy:moral_development socio:norm thesaurus:related
ln edupsy:moral_development socio:value thesaurus:related
# ── assessment & instruction ──
def "edupsy:formative_assessment" "Ongoing assessment to guide learning."
ln edupsy:formative_assessment edupsy thesaurus:related
ln edupsy:formative_assessment school:quiz thesaurus:related
ln edupsy:formative_assessment teaching:grading thesaurus:related
def "edupsy:summative_assessment" "Assessment of learning at the end of a unit."
ln edupsy:summative_assessment edupsy thesaurus:related
ln edupsy:summative_assessment school:exam thesaurus:related
ln edupsy:summative_assessment school:report_card thesaurus:related
def "edupsy:feedback" "Information to a learner about performance, key to improvement."
ln edupsy:feedback edupsy thesaurus:related
ln edupsy:feedback work:performance_review thesaurus:related
def "edupsy:differentiated_instruction" "Adapting teaching to diverse learners."
ln edupsy:differentiated_instruction edupsy thesaurus:related
# ── education studies & pedagogy ──
def "pedagogy" "The theory and practice of teaching and education (教育学)."
ln pedagogy edupsy thesaurus:related
ln pedagogy teaching:lecture thesaurus:related
ln pedagogy occupation:teacher thesaurus:related

def "pedagogy:didactics" "The systematic art and science of teaching."
ln pedagogy:didactics pedagogy thesaurus:related
def "pedagogy:andragogy" "The theory and practice of adult learning (成人教育学)."
ln pedagogy:andragogy pedagogy thesaurus:related
ln pedagogy:andragogy work:performance_review thesaurus:related
def "pedagogy:curriculum_theory" "The study of what is taught, why and how it is organised."
ln pedagogy:curriculum_theory pedagogy thesaurus:related
ln pedagogy:curriculum_theory school:elementary_school thesaurus:related
ln pedagogy:curriculum_theory teaching:curriculum thesaurus:related
def "pedagogy:instructional_design" "Systematic design of learning experiences."
ln pedagogy:instructional_design pedagogy thesaurus:related
def "pedagogy:educational_philosophy" "Philosophical foundations of aims and methods of education."
ln pedagogy:educational_philosophy pedagogy thesaurus:related
def "pedagogy:progressive_education" "Dewey's learning by doing and experience."
ln pedagogy:progressive_education pedagogy thesaurus:related
def "pedagogy:montessori_method" "Child-led learning in a prepared environment."
ln pedagogy:montessori_method pedagogy thesaurus:related
def "pedagogy:critical_pedagogy" "Freire's education for critical consciousness and liberation."
ln pedagogy:critical_pedagogy pedagogy thesaurus:related
ln pedagogy:critical_pedagogy socio:conflict_theory thesaurus:related
ln pedagogy:critical_pedagogy socio:inequality thesaurus:related
def "pedagogy:inclusive_education" "Teaching that includes learners of all abilities."
ln pedagogy:inclusive_education pedagogy thesaurus:related
def "pedagogy:special_education" "Education adapted for learners with special needs (特別支援教育)."
ln pedagogy:special_education pedagogy thesaurus:related
ln pedagogy:special_education school:school_counselor thesaurus:related
ln pedagogy:special_education care:long_term_care thesaurus:related
def "pedagogy:lifelong_learning" "Continuing learning across the whole life (生涯学習)."
ln pedagogy:lifelong_learning pedagogy thesaurus:related
ln pedagogy:lifelong_learning school:cram_school thesaurus:related
ln pedagogy:lifelong_learning academia thesaurus:related
def "pedagogy:literacy" "The ability to read and write; also numeracy, digital literacy."
ln pedagogy:literacy pedagogy thesaurus:related
ln pedagogy:literacy lib:reference_service thesaurus:related
def "pedagogy:educational_technology" "Technology used to support learning (EdTech)."
ln pedagogy:educational_technology pedagogy thesaurus:related
ln pedagogy:educational_technology dh:knowledge_graph thesaurus:related
ln pedagogy:educational_technology ai:embedding thesaurus:related
def "pedagogy:teacher_education" "The preparation and development of teachers."
ln pedagogy:teacher_education pedagogy thesaurus:related
def "pedagogy:educational_policy" "Government direction of education systems."
ln pedagogy:educational_policy pedagogy thesaurus:related
ln pedagogy:educational_policy gov:function:education thesaurus:related
ln pedagogy:educational_policy admin:municipality thesaurus:related
