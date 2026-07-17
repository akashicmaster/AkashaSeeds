# Akasha ontology — sports science & physical education (スポーツ科学・体育).
# Greenfield. Bridged to med:/bme:/nutrisci:/psy:/rehab:/activity:exercise/group:.
# Base pack.

def "sportsci" "Sports science — the science of human movement, exercise and performance (スポーツ科学)."
ln sportsci activity:exercise thesaurus:related
ln sportsci group:community_sports thesaurus:related

def "sportsci:exercise_physiology" "How the body responds and adapts to physical activity (運動生理学)."
ln sportsci:exercise_physiology sportsci thesaurus:related
ln sportsci:exercise_physiology med:basic:physiology thesaurus:related
ln sportsci:exercise_physiology life:cellular_respiration thesaurus:related
def "sportsci:biomechanics" "The mechanics of human movement — forces, joints, gait (バイオメカニクス)."
ln sportsci:biomechanics sportsci thesaurus:related
ln sportsci:biomechanics bme:biomechanics thesaurus:related
ln sportsci:biomechanics mecheng:mechanics_of_materials thesaurus:related
def "sportsci:kinesiology" "The study of human movement (運動学)."
ln sportsci:kinesiology sportsci thesaurus:related
def "sportsci:motor_control" "How the nervous system coordinates movement."
ln sportsci:motor_control sportsci thesaurus:related
ln sportsci:motor_control neuro:cerebellum thesaurus:related
ln sportsci:motor_control neuro:neuron thesaurus:related
def "sportsci:motor_learning" "How movement skills are acquired and refined (運動学習)."
ln sportsci:motor_learning sportsci thesaurus:related
ln sportsci:motor_learning psy:learning thesaurus:related
ln sportsci:motor_learning neuro:neuroplasticity thesaurus:related
def "sportsci:sports_medicine" "Medicine of exercise, injury and performance (スポーツ医学)."
ln sportsci:sports_medicine sportsci thesaurus:related
ln sportsci:sports_medicine med:medicine thesaurus:related
ln sportsci:sports_medicine rehab:physical_therapy thesaurus:related
def "sportsci:sports_nutrition" "Nutrition for training, performance and recovery (スポーツ栄養)."
ln sportsci:sports_nutrition sportsci thesaurus:related
ln sportsci:sports_nutrition nutrisci:functional_food thesaurus:related
ln sportsci:sports_nutrition nutrisci:metabolomics thesaurus:related
def "sportsci:sports_psychology" "The mental side of performance — motivation, focus, resilience (スポーツ心理学)."
ln sportsci:sports_psychology sportsci thesaurus:related
ln sportsci:sports_psychology psych:mental_health thesaurus:related
ln sportsci:sports_psychology edupsy:motivation_to_learn thesaurus:related
def "sportsci:strength_conditioning" "Training to build strength, power and endurance."
ln sportsci:strength_conditioning sportsci thesaurus:related
def "sportsci:aerobic_capacity" "The body's ability to use oxygen during sustained effort (有酸素能力)."
ln sportsci:aerobic_capacity sportsci thesaurus:related
def "sportsci:physical_education" "The teaching of movement, fitness and sport (体育)."
ln sportsci:physical_education sportsci thesaurus:related
ln sportsci:physical_education school:elementary_school thesaurus:related
ln sportsci:physical_education pedagogy:didactics thesaurus:related
ln sportsci:physical_education tool:yoga_mat thesaurus:related
def "sportsci:athletic_training" "Preparing and rehabilitating athletes."
ln sportsci:athletic_training sportsci thesaurus:related
ln sportsci:athletic_training group:sports_club thesaurus:related
ln sportsci:athletic_training rehab:functional_recovery thesaurus:related
def "sportsci:ergonomics" "Designing tasks and tools to fit the human body."
ln sportsci:ergonomics sportsci thesaurus:related
ln sportsci:ergonomics mecheng:machine_design thesaurus:related
def "sportsci:fitness" "The state of physical capacity and health (体力)."
ln sportsci:fitness sportsci thesaurus:related
ln sportsci:fitness activity:exercise thesaurus:related
ln sportsci:fitness work:work_life_balance thesaurus:related
def "sportsci:endurance" "The capacity to sustain prolonged effort."
ln sportsci:endurance sportsci thesaurus:related
