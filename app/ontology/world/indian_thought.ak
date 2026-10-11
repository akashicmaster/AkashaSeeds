# Akasha ontology — Indian knowledge systems: the six darśanas, Yoga, and the NEXUS that binds
# Ayurveda's food-science layer (ayurveda:*) and its medicine-system layer (med:*) to their shared
# philosophical root (Sāṃkhya) and to Yoga, its sister science.
#
# DESCRIPTIVE cultural / philosophical knowledge, provenance: traditional. NOT medical advice or a
# claim of efficacy. This file introduces NO parallel duplicates — it defines the philosophy/yoga
# scaffold that was missing and then LINKS the existing atoms (ayurveda:*, med:*, tradition:ayurveda,
# phil:school, religion:hinduism) that were previously disconnected.

# ── The six orthodox darśanas (āstika), placed in the EXISTING philosophy tree (phil:school) ──
def "phil:group:darshana" "The six orthodox (astika) schools of Indian philosophy (shad-darshana), which accept the authority of the Vedas: Nyaya, Vaisheshika, Samkhya, Yoga, Mimamsa, Vedanta."
ln phil:group:darshana phil:school thesaurus:related
ln phil:group:darshana religion:hinduism thesaurus:related

def "phil:school:nyaya" "Nyaya — the school of logic and epistemology; analysis of the means of valid knowledge (pramana)."
ln phil:school:nyaya phil:group:darshana thesaurus:related
ln phil:school:nyaya phil:school thesaurus:related

def "phil:school:vaisheshika" "Vaisheshika — atomism and the categorisation of reality into padarthas; classically paired with Nyaya."
ln phil:school:vaisheshika phil:group:darshana thesaurus:related
ln phil:school:vaisheshika phil:school thesaurus:related
ln phil:school:vaisheshika phil:school:nyaya thesaurus:related

def "phil:school:samkhya" "Samkhya — the dualist enumeration of 25 tattvas; the interplay of prakriti (nature) and purusha (consciousness). The metaphysical basis shared by Yoga AND Ayurveda."
ln phil:school:samkhya phil:group:darshana thesaurus:related
ln phil:school:samkhya phil:school thesaurus:related

def "phil:school:yoga" "Yoga darshana — Patanjali's system of stilling the fluctuations of the mind (citta-vritti-nirodha); it takes over Samkhya's metaphysics and adds practice and Ishvara."
ln phil:school:yoga phil:group:darshana thesaurus:related
ln phil:school:yoga phil:school thesaurus:related
ln phil:school:yoga phil:school:samkhya thesaurus:related

def "phil:school:mimamsa" "Mimamsa (Purva Mimamsa) — the exegesis of Vedic ritual and dharma; hermeneutics of the Vedas."
ln phil:school:mimamsa phil:group:darshana thesaurus:related
ln phil:school:mimamsa phil:school thesaurus:related

def "phil:school:vedanta" "Vedanta (Uttara Mimamsa) — inquiry into the Upanishads: brahman, atman, and liberation (moksha)."
ln phil:school:vedanta phil:group:darshana thesaurus:related
ln phil:school:vedanta phil:school thesaurus:related

# ── Sāṃkhya metaphysics — the substrate that Yoga AND Ayurveda both stand on ──
def "samkhya:prakriti" "Prakriti — primordial, unconscious nature/matter; the source from which the tattvas evolve. In Ayurveda the word also names an individual's inborn constitution."
ln samkhya:prakriti phil:school:samkhya thesaurus:related
def "samkhya:purusha" "Purusha — pure witnessing consciousness, wholly distinct from prakriti; liberation is discerning the two."
ln samkhya:purusha phil:school:samkhya thesaurus:related

# the five great elements (pañca-mahābhūta) — the substance the doshas are made of
def "samkhya:mahabhuta" "Pancha-mahabhuta — the five great elements (ether, air, fire, water, earth) from which the material world and the three doshas are composed."
ln samkhya:mahabhuta samkhya:prakriti thesaurus:related
def "samkhya:bhuta:ether" "Akasha (ether / space) — the subtlest of the five great elements."
def "samkhya:bhuta:air" "Vayu (air) — the element of movement."
def "samkhya:bhuta:fire" "Tejas / Agni (fire) — the element of transformation and heat."
def "samkhya:bhuta:water" "Ap / Jala (water) — the element of cohesion and fluidity."
def "samkhya:bhuta:earth" "Prithvi (earth) — the densest element, of solidity and structure."
ln samkhya:bhuta:ether samkhya:mahabhuta sys:part_of
ln samkhya:bhuta:air samkhya:mahabhuta sys:part_of
ln samkhya:bhuta:fire samkhya:mahabhuta sys:part_of
ln samkhya:bhuta:water samkhya:mahabhuta sys:part_of
ln samkhya:bhuta:earth samkhya:mahabhuta sys:part_of

# ── The three guṇas — the qualitative/mental axis shared by Sāṃkhya, Yoga, and Ayurveda ──
def "guna:triguna" "Tri-guna — the three fundamental qualities woven through prakriti (sattva, rajas, tamas); the qualitative axis shared by Samkhya, Yoga, and Ayurveda's mental constitution (manasa prakriti)."
ln guna:triguna samkhya:prakriti thesaurus:related
ln guna:triguna phil:school:samkhya thesaurus:related
def "guna:sattva" "Sattva — the guna of clarity, harmony, and lightness."
def "guna:rajas" "Rajas — the guna of activity, passion, and movement."
def "guna:tamas" "Tamas — the guna of inertia, heaviness, and dullness."
ln guna:sattva guna:triguna sys:part_of
ln guna:rajas guna:triguna sys:part_of
ln guna:tamas guna:triguna sys:part_of

# ── Yoga — the darśana as lived practice: Patañjali's eight limbs (Aṣṭāṅga) ──
def "yoga:yoga" "Yoga — union; the darshana and the practice of stilling the mind. Sister science to Ayurveda: Yoga tends the mind, Ayurveda the body, on one shared metaphysics."
ln yoga:yoga phil:school:yoga thesaurus:related
ln yoga:yoga religion:hinduism thesaurus:related
def "yoga:ashtanga" "Ashtanga — the eight limbs of Patanjali's Yoga, a graded path from ethics to absorption."
ln yoga:ashtanga yoga:yoga sys:part_of
def "yoga:limb:yama" "Yama — ethical restraints (ahimsa, satya, ...); the first limb."
def "yoga:limb:niyama" "Niyama — observances (sauca, santosha, ...); the second limb."
def "yoga:limb:asana" "Asana — steady, comfortable posture; the third limb."
def "yoga:limb:pranayama" "Pranayama — regulation of prana through the breath; the fourth limb."
def "yoga:limb:pratyahara" "Pratyahara — withdrawal of the senses; the fifth limb."
def "yoga:limb:dharana" "Dharana — concentration; the sixth limb."
def "yoga:limb:dhyana" "Dhyana — meditation; the seventh limb."
def "yoga:limb:samadhi" "Samadhi — absorption / union; the eighth limb."
ln yoga:limb:yama yoga:ashtanga sys:part_of
ln yoga:limb:niyama yoga:ashtanga sys:part_of
ln yoga:limb:asana yoga:ashtanga sys:part_of
ln yoga:limb:pranayama yoga:ashtanga sys:part_of
ln yoga:limb:pratyahara yoga:ashtanga sys:part_of
ln yoga:limb:dharana yoga:ashtanga sys:part_of
ln yoga:limb:dhyana yoga:ashtanga sys:part_of
ln yoga:limb:samadhi yoga:ashtanga sys:part_of
def "yoga:prana" "Prana — the vital life-force carried by the breath; the shared ground of Yoga (pranayama) and Ayurveda (prana as a vital principle)."
ln yoga:prana yoga:yoga thesaurus:related

# the five sheaths (pañca-kośa) — the annamaya (food) sheath ties Yoga's body-model to Ayurveda's food-body
def "yoga:kosha:annamaya" "Annamaya kosha — the food sheath (the physical body built from food); the layer where Ayurveda's food science acts."
def "yoga:kosha:pranamaya" "Pranamaya kosha — the vital-energy sheath (breath / prana)."
def "yoga:kosha:manomaya" "Manomaya kosha — the mental-emotional sheath."
def "yoga:kosha:vijnanamaya" "Vijnanamaya kosha — the sheath of intellect / discernment."
def "yoga:kosha:anandamaya" "Anandamaya kosha — the bliss sheath, the subtlest."
ln yoga:kosha:annamaya yoga:yoga thesaurus:related
ln yoga:kosha:pranamaya yoga:yoga thesaurus:related
ln yoga:kosha:manomaya yoga:yoga thesaurus:related
ln yoga:kosha:vijnanamaya yoga:yoga thesaurus:related
ln yoga:kosha:anandamaya yoga:yoga thesaurus:related
ln yoga:kosha:pranamaya yoga:prana thesaurus:related

# ═══ THE NEXUS ═══════════════════════════════════════════════════════════════════════════════
# (1) Unify the two Ayurveda representations that were disconnected: the food-science tradition node
#     and the medicine-system node denote the SAME system; each dosha IS a dosha in the medical sense.
ln tradition:ayurveda med:system:ayurveda sys:same_as
ln ayurveda:dosha:vata med:concept:dosha sys:is_a
ln ayurveda:dosha:pitta med:concept:dosha sys:is_a
ln ayurveda:dosha:kapha med:concept:dosha sys:is_a

# (2) The three doshas are composed of the five great elements (pañca-mahābhūta).
ln ayurveda:dosha:vata samkhya:bhuta:air sys:made_from
ln ayurveda:dosha:vata samkhya:bhuta:ether sys:made_from
ln ayurveda:dosha:pitta samkhya:bhuta:fire sys:made_from
ln ayurveda:dosha:pitta samkhya:bhuta:water sys:made_from
ln ayurveda:dosha:kapha samkhya:bhuta:earth sys:made_from
ln ayurveda:dosha:kapha samkhya:bhuta:water sys:made_from

# (3) Ayurveda is philosophically grounded in Sāṃkhya, and is Yoga's sister science.
ln tradition:ayurveda phil:school:samkhya thesaurus:related
ln med:system:ayurveda phil:school:samkhya thesaurus:related
ln tradition:ayurveda yoga:yoga thesaurus:related
ln yoga:yoga tradition:ayurveda thesaurus:related
ln yoga:prana ayurveda:dosha:vata thesaurus:related

# (4) The guṇas are Ayurveda's MENTAL constitution (mānasa prakṛti) — the bridge from the physical
#     doshas to the Sāṃkhya/Yoga mind-qualities. (Kept as association, not an equation of dosha=guna.)
ln tradition:ayurveda guna:triguna thesaurus:related
ln guna:triguna yoga:yoga thesaurus:related

# (5) The six tastes (rasa) arise from pairs of elements — the classical rasa→mahābhūta mapping,
#     tying the EXISTING rasa atoms into the elemental nexus.
ln ayurveda:rasa:sweet samkhya:bhuta:earth thesaurus:related
ln ayurveda:rasa:sweet samkhya:bhuta:water thesaurus:related
ln ayurveda:rasa:sour samkhya:bhuta:earth thesaurus:related
ln ayurveda:rasa:sour samkhya:bhuta:fire thesaurus:related
ln ayurveda:rasa:salty samkhya:bhuta:water thesaurus:related
ln ayurveda:rasa:salty samkhya:bhuta:fire thesaurus:related
ln ayurveda:rasa:pungent samkhya:bhuta:fire thesaurus:related
ln ayurveda:rasa:pungent samkhya:bhuta:air thesaurus:related
ln ayurveda:rasa:bitter samkhya:bhuta:air thesaurus:related
ln ayurveda:rasa:bitter samkhya:bhuta:ether thesaurus:related
ln ayurveda:rasa:astringent samkhya:bhuta:air thesaurus:related
ln ayurveda:rasa:astringent samkhya:bhuta:earth thesaurus:related

# (6) Virya (potency) tracks the fire/water polarity of the elements.
ln ayurveda:virya:heating samkhya:bhuta:fire thesaurus:related
ln ayurveda:virya:cooling samkhya:bhuta:water thesaurus:related

# (7) The annamaya (food) sheath is exactly where Ayurveda's food therapy operates.
ln yoga:kosha:annamaya tradition:ayurveda thesaurus:related
ln yoga:kosha:annamaya foodtherapy thesaurus:related
