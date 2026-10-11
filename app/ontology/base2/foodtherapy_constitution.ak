# Akasha ontology — yakuzen (medicinal cuisine) constitution/symptom recommendation view.
# A constitution or symptom RECOMMENDS a food nature/action; foods carrying
# that nature/action (tcm:nature / tcm:action links) are the recommendations —
# so constitution → recommends → foods is one graph traversal. Descriptive.

def "tcm:action:regulate_qi" "理気 — regulate/move qi."
ln tcm:action:regulate_qi tradition:tcm thesaurus:related
ln ingred:veg:radish tcm:action:regulate_qi tcm:action
ln ingred:herb:mint tcm:action:regulate_qi tcm:action
ln ingred:spice:fennel_seed tcm:action:regulate_qi tcm:action
ln ingred:condiment:vinegar tcm:action:regulate_qi tcm:action
ln ingred:veg:tomato tcm:action:regulate_qi tcm:action

def "tcm:constitution:yang_deficiency" "陽虚 — deficient warmth; cold limbs, fatigue."
ln tcm:constitution:yang_deficiency tradition:tcm thesaurus:related
ln tcm:constitution:yang_deficiency tcm:nature:warm tcm:recommends_nature
ln tcm:constitution:yang_deficiency tcm:nature:hot tcm:recommends_nature
ln tcm:constitution:yang_deficiency tcm:action:tonify_yang tcm:recommends_action
ln tcm:constitution:yang_deficiency tcm:action:warm_middle tcm:recommends_action
def "tcm:constitution:yin_deficiency" "陰虚 — deficient fluids; heat signs, dryness."
ln tcm:constitution:yin_deficiency tradition:tcm thesaurus:related
ln tcm:constitution:yin_deficiency tcm:nature:cool tcm:recommends_nature
ln tcm:constitution:yin_deficiency tcm:action:nourish_yin tcm:recommends_action
ln tcm:constitution:yin_deficiency tcm:action:generate_fluids tcm:recommends_action
ln tcm:constitution:yin_deficiency tcm:action:moisten_dryness tcm:recommends_action
def "tcm:constitution:qi_deficiency" "気虚 — deficient qi; fatigue, weak digestion."
ln tcm:constitution:qi_deficiency tradition:tcm thesaurus:related
ln tcm:constitution:qi_deficiency tcm:nature:warm tcm:recommends_nature
ln tcm:constitution:qi_deficiency tcm:nature:neutral tcm:recommends_nature
ln tcm:constitution:qi_deficiency tcm:action:tonify_qi tcm:recommends_action
ln tcm:constitution:qi_deficiency tcm:action:strengthen_spleen tcm:recommends_action
def "tcm:constitution:blood_deficiency" "血虚 — deficient blood; pallor, dizziness."
ln tcm:constitution:blood_deficiency tradition:tcm thesaurus:related
ln tcm:constitution:blood_deficiency tcm:nature:neutral tcm:recommends_nature
ln tcm:constitution:blood_deficiency tcm:action:tonify_blood tcm:recommends_action
def "tcm:constitution:phlegm_damp" "痰湿 — phlegm-damp; heaviness, oedema."
ln tcm:constitution:phlegm_damp tradition:tcm thesaurus:related
ln tcm:constitution:phlegm_damp tcm:nature:warm tcm:recommends_nature
ln tcm:constitution:phlegm_damp tcm:action:drain_damp tcm:recommends_action
ln tcm:constitution:phlegm_damp tcm:action:resolve_phlegm tcm:recommends_action
def "tcm:constitution:damp_heat" "湿熱 — damp-heat; heat + heaviness."
ln tcm:constitution:damp_heat tradition:tcm thesaurus:related
ln tcm:constitution:damp_heat tcm:nature:cool tcm:recommends_nature
ln tcm:constitution:damp_heat tcm:action:clear_heat tcm:recommends_action
ln tcm:constitution:damp_heat tcm:action:drain_damp tcm:recommends_action
def "tcm:constitution:blood_stasis" "血瘀 — blood stasis; fixed pain."
ln tcm:constitution:blood_stasis tradition:tcm thesaurus:related
ln tcm:constitution:blood_stasis tcm:action:invigorate_blood tcm:recommends_action
def "tcm:constitution:qi_stagnation" "気鬱 — qi stagnation; distension, mood."
ln tcm:constitution:qi_stagnation tradition:tcm thesaurus:related
ln tcm:constitution:qi_stagnation tcm:action:regulate_qi tcm:recommends_action
ln tcm:constitution:qi_stagnation tcm:action:aid_digestion tcm:recommends_action
def "tcm:constitution:balanced" "平和 — balanced constitution; varied diet."
ln tcm:constitution:balanced tradition:tcm thesaurus:related
ln tcm:constitution:balanced tcm:nature:neutral tcm:recommends_nature

def "tcm:symptom:cold_intolerance" "冷え — cold intolerance."
ln tcm:symptom:cold_intolerance tradition:tcm thesaurus:related
ln tcm:symptom:cold_intolerance tcm:action:warm_middle tcm:recommends_action
ln tcm:symptom:cold_intolerance tcm:action:tonify_yang tcm:recommends_action
def "tcm:symptom:constipation" "便秘 — constipation."
ln tcm:symptom:constipation tradition:tcm thesaurus:related
ln tcm:symptom:constipation tcm:action:moisten_dryness tcm:recommends_action
def "tcm:symptom:insomnia" "不眠 — insomnia."
ln tcm:symptom:insomnia tradition:tcm thesaurus:related
ln tcm:symptom:insomnia tcm:action:calm_spirit tcm:recommends_action
def "tcm:symptom:cough" "咳 — cough."
ln tcm:symptom:cough tradition:tcm thesaurus:related
ln tcm:symptom:cough tcm:action:stop_cough tcm:recommends_action
ln tcm:symptom:cough tcm:action:resolve_phlegm tcm:recommends_action
def "tcm:symptom:edema" "むくみ — oedema."
ln tcm:symptom:edema tradition:tcm thesaurus:related
ln tcm:symptom:edema tcm:action:drain_damp tcm:recommends_action
def "tcm:symptom:indigestion" "消化不良 — indigestion."
ln tcm:symptom:indigestion tradition:tcm thesaurus:related
ln tcm:symptom:indigestion tcm:action:aid_digestion tcm:recommends_action
ln tcm:symptom:indigestion tcm:action:strengthen_spleen tcm:recommends_action
def "tcm:symptom:heat_signs" "熱証 — heat signs."
ln tcm:symptom:heat_signs tradition:tcm thesaurus:related
ln tcm:symptom:heat_signs tcm:action:clear_heat tcm:recommends_action
ln tcm:symptom:heat_signs tcm:action:generate_fluids tcm:recommends_action
