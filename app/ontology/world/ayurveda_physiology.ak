# Akasha ontology — Ayurvedic physiology & regimen: vipāka (post-digestive taste), the dhātus
# (tissues), the srotas (bodily channels), and ritucharyā (seasonal regimen).
# Extends base2/foodtherapy_ayurveda.ak + world/ayurveda_materia_medica.ak.
#
# DESCRIPTIVE traditional knowledge, provenance: traditional. NOT medical advice. Reuses the existing
# ayurveda vocabulary; the only new relation is ayurveda:vipaka (auto-derived into the lexicon).

# ═══ AGNI + VIPĀKA — what digestion does to a taste ══════════════════════════════════════════════
def "ayurveda:agni" "Agni — the digestive fire that transforms food; its strength governs digestion and the making of tissue. Weak agni leaves ama (undigested residue)."
ln ayurveda:agni tradition:ayurveda thesaurus:related
def "ayurveda:ama" "Ama — the sticky, undigested residue left by weak agni; the root of many imbalances in classical theory."
ln ayurveda:ama ayurveda:agni thesaurus:related

def "ayurveda:vipaka" "Vipaka — the post-digestive taste: the lasting effect a food/herb has AFTER agni has acted on it, distinct from the rasa (taste on the tongue). One of three: sweet, sour, or pungent."
ln ayurveda:vipaka tradition:ayurveda thesaurus:related
ln ayurveda:vipaka ayurveda:agni thesaurus:related
def "ayurveda:vipaka:sweet" "Madhura vipaka (sweet) — a building, nourishing post-digestive effect."
def "ayurveda:vipaka:sour" "Amla vipaka (sour) — a mildly heating post-digestive effect."
def "ayurveda:vipaka:pungent" "Katu vipaka (pungent) — a lightening, reducing post-digestive effect."
ln ayurveda:vipaka:sweet ayurveda:vipaka sys:is_a
ln ayurveda:vipaka:sour ayurveda:vipaka sys:is_a
ln ayurveda:vipaka:pungent ayurveda:vipaka sys:is_a
# the classical rasa → vipaka rule (sweet+salty→sweet; sour→sour; pungent+bitter+astringent→pungent)
ln ayurveda:rasa:sweet ayurveda:vipaka:sweet ayurveda:vipaka
ln ayurveda:rasa:salty ayurveda:vipaka:sweet ayurveda:vipaka
ln ayurveda:rasa:sour ayurveda:vipaka:sour ayurveda:vipaka
ln ayurveda:rasa:pungent ayurveda:vipaka:pungent ayurveda:vipaka
ln ayurveda:rasa:bitter ayurveda:vipaka:pungent ayurveda:vipaka
ln ayurveda:rasa:astringent ayurveda:vipaka:pungent ayurveda:vipaka

# ═══ DHĀTU — the seven bodily tissues (built in sequence by agni) ═════════════════════════════════
def "ayurveda:dhatu" "Dhatu — the seven bodily tissues, each formed in turn from the previous by digestion: rasa, rakta, mamsa, meda, asthi, majja, shukra."
ln ayurveda:dhatu tradition:ayurveda thesaurus:related
def "ayurveda:dhatu:rasa" "Rasa dhatu — plasma / lymph, the first tissue and nourishing fluid."
def "ayurveda:dhatu:rakta" "Rakta dhatu — blood."
def "ayurveda:dhatu:mamsa" "Mamsa dhatu — muscle."
def "ayurveda:dhatu:meda" "Meda dhatu — fat / adipose tissue."
def "ayurveda:dhatu:asthi" "Asthi dhatu — bone."
def "ayurveda:dhatu:majja" "Majja dhatu — marrow and nervous tissue."
def "ayurveda:dhatu:shukra" "Shukra dhatu — the reproductive tissue, the finest essence."
ln ayurveda:dhatu:rasa ayurveda:dhatu sys:is_a
ln ayurveda:dhatu:rakta ayurveda:dhatu sys:is_a
ln ayurveda:dhatu:mamsa ayurveda:dhatu sys:is_a
ln ayurveda:dhatu:meda ayurveda:dhatu sys:is_a
ln ayurveda:dhatu:asthi ayurveda:dhatu sys:is_a
ln ayurveda:dhatu:majja ayurveda:dhatu sys:is_a
ln ayurveda:dhatu:shukra ayurveda:dhatu sys:is_a
# the nourishment sequence (each dhatu feeds the next)
ln ayurveda:dhatu:rakta ayurveda:dhatu:rasa thesaurus:related
ln ayurveda:dhatu:mamsa ayurveda:dhatu:rakta thesaurus:related
ln ayurveda:dhatu:meda ayurveda:dhatu:mamsa thesaurus:related
ln ayurveda:dhatu:asthi ayurveda:dhatu:meda thesaurus:related
ln ayurveda:dhatu:majja ayurveda:dhatu:asthi thesaurus:related
ln ayurveda:dhatu:shukra ayurveda:dhatu:majja thesaurus:related

# ═══ SROTAS — the bodily channels that carry substances through the body ═════════════════════════
def "ayurveda:srotas" "Srotas — the channels of the body through which substances (breath, food, tissues, wastes) flow; illness is often a blocked or over-flowing srotas."
ln ayurveda:srotas tradition:ayurveda thesaurus:related
def "ayurveda:srotas:pranavaha" "Pranavaha srotas — the channel of breath / respiration."
def "ayurveda:srotas:annavaha" "Annavaha srotas — the channel of food (the digestive tract)."
def "ayurveda:srotas:udakavaha" "Udakavaha srotas — the channel of water and hydration."
def "ayurveda:srotas:rasavaha" "Rasavaha srotas — the channel carrying rasa (plasma / lymph)."
def "ayurveda:srotas:raktavaha" "Raktavaha srotas — the channel carrying rakta (blood)."
def "ayurveda:srotas:mamsavaha" "Mamsavaha srotas — the channel carrying mamsa (muscle)."
def "ayurveda:srotas:medovaha" "Medovaha srotas — the channel carrying meda (fat)."
def "ayurveda:srotas:asthivaha" "Asthivaha srotas — the channel carrying asthi (bone)."
def "ayurveda:srotas:majjavaha" "Majjavaha srotas — the channel carrying majja (marrow / nerve)."
def "ayurveda:srotas:shukravaha" "Shukravaha srotas — the channel carrying shukra (reproductive tissue)."
def "ayurveda:srotas:mutravaha" "Mutravaha srotas — the channel of urine."
def "ayurveda:srotas:purishavaha" "Purishavaha srotas — the channel of faeces."
def "ayurveda:srotas:svedavaha" "Svedavaha srotas — the channel of sweat."
def "ayurveda:srotas:manovaha" "Manovaha srotas — the channel of the mind (thought and feeling)."
ln ayurveda:srotas:pranavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:annavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:udakavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:rasavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:raktavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:mamsavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:medovaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:asthivaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:majjavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:shukravaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:mutravaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:purishavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:svedavaha ayurveda:srotas sys:is_a
ln ayurveda:srotas:manovaha ayurveda:srotas sys:is_a
# each tissue-channel carries its dhatu
ln ayurveda:srotas:rasavaha ayurveda:dhatu:rasa thesaurus:related
ln ayurveda:srotas:raktavaha ayurveda:dhatu:rakta thesaurus:related
ln ayurveda:srotas:mamsavaha ayurveda:dhatu:mamsa thesaurus:related
ln ayurveda:srotas:medovaha ayurveda:dhatu:meda thesaurus:related
ln ayurveda:srotas:asthivaha ayurveda:dhatu:asthi thesaurus:related
ln ayurveda:srotas:majjavaha ayurveda:dhatu:majja thesaurus:related
ln ayurveda:srotas:shukravaha ayurveda:dhatu:shukra thesaurus:related
ln ayurveda:srotas:annavaha ayurveda:agni thesaurus:related
ln ayurveda:srotas:manovaha guna:triguna thesaurus:related

# ═══ RITUCHARYĀ — seasonal regimen (the dosha cycle through six seasons) ══════════════════════════
def "ayurveda:ritucharya" "Ritucharya — the seasonal regimen: adjusting diet and routine to the six seasons so the dosha that each season aggravates is kept in balance."
ln ayurveda:ritucharya tradition:ayurveda thesaurus:related
def "ayurveda:ritu" "Ritu — a season; Ayurveda divides the year into six (shishira, vasanta, grishma, varsha, sharad, hemanta)."
ln ayurveda:ritu ayurveda:ritucharya thesaurus:related
def "ayurveda:ritu:shishira" "Shishira — late winter (cold, damp); Kapha accumulates."
def "ayurveda:ritu:vasanta" "Vasanta — spring; the accumulated Kapha melts and is aggravated."
def "ayurveda:ritu:grishma" "Grishma — summer (hot, dry); Vata accumulates, Kapha wanes."
def "ayurveda:ritu:varsha" "Varsha — monsoon / rainy season; Vata is aggravated, Pitta accumulates."
def "ayurveda:ritu:sharad" "Sharad — autumn; the accumulated Pitta is aggravated."
def "ayurveda:ritu:hemanta" "Hemanta — early winter (cold); strong agni, doshas calm."
ln ayurveda:ritu:shishira ayurveda:ritu sys:is_a
ln ayurveda:ritu:vasanta ayurveda:ritu sys:is_a
ln ayurveda:ritu:grishma ayurveda:ritu sys:is_a
ln ayurveda:ritu:varsha ayurveda:ritu sys:is_a
ln ayurveda:ritu:sharad ayurveda:ritu sys:is_a
ln ayurveda:ritu:hemanta ayurveda:ritu sys:is_a
# dosha aggravation (prakopa) per season — reuses the existing pacifies/aggravates vocabulary
ln ayurveda:ritu:vasanta ayurveda:dosha:kapha ayurveda:aggravates
ln ayurveda:ritu:varsha ayurveda:dosha:vata ayurveda:aggravates
ln ayurveda:ritu:sharad ayurveda:dosha:pitta ayurveda:aggravates
ln ayurveda:ritu:grishma ayurveda:dosha:vata ayurveda:aggravates
ln ayurveda:ritu:grishma ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:ritu:hemanta ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:ritu:shishira ayurveda:dosha:kapha ayurveda:aggravates
