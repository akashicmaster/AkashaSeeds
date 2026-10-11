# Akasha ontology — Ayurvedic materia medica (dravya) + constitution (prakṛti).
# Extends the food-science layer (base2/foodtherapy_ayurveda.ak) and the philosophy nexus
# (world/indian_thought.ak) with the herb/formula layer and the constitutional-assessment layer.
#
# DESCRIPTIVE traditional knowledge, provenance: traditional. NOT medical advice, dosage, or a claim
# of efficacy. Dosha effects follow classical texts (pacifies / aggravates in excess). Herbs reuse the
# existing rasa/virya/dosha vocabulary; formulas are made_from their component herbs.

# ═══ CONSTITUTION (prakṛti) — the assessment layer ═══════════════════════════════════════════════
def "ayurveda:prakriti" "Prakriti (constitution) — the inborn balance of the three doshas a person is born with; the baseline that Ayurvedic assessment reads a person against. (The word echoes samkhya:prakriti, primordial nature.)"
ln ayurveda:prakriti tradition:ayurveda thesaurus:related
ln ayurveda:prakriti samkhya:prakriti thesaurus:related
def "ayurveda:vikriti" "Vikriti — the current, disturbed state of the doshas (imbalance), read against the inborn prakriti; the target of balancing. Assessment compares vikriti to prakriti."
ln ayurveda:vikriti ayurveda:prakriti thesaurus:related
ln ayurveda:vikriti tradition:ayurveda thesaurus:related

# the seven constitutional types (three single, three dual, one balanced)
def "ayurveda:prakriti:vata" "Vata prakriti — a constitution dominated by Vata: light, dry, quick, changeable."
def "ayurveda:prakriti:pitta" "Pitta prakriti — a constitution dominated by Pitta: hot, sharp, focused, intense."
def "ayurveda:prakriti:kapha" "Kapha prakriti — a constitution dominated by Kapha: heavy, steady, calm, enduring."
def "ayurveda:prakriti:vata_pitta" "Vata-Pitta — a dual constitution combining Vata and Pitta."
def "ayurveda:prakriti:pitta_kapha" "Pitta-Kapha — a dual constitution combining Pitta and Kapha."
def "ayurveda:prakriti:vata_kapha" "Vata-Kapha — a dual constitution combining Vata and Kapha."
def "ayurveda:prakriti:tridoshic" "Tridoshic (sama-prakriti) — a balanced constitution of all three doshas; considered rare and ideal."
ln ayurveda:prakriti:vata ayurveda:prakriti sys:is_a
ln ayurveda:prakriti:pitta ayurveda:prakriti sys:is_a
ln ayurveda:prakriti:kapha ayurveda:prakriti sys:is_a
ln ayurveda:prakriti:vata_pitta ayurveda:prakriti sys:is_a
ln ayurveda:prakriti:pitta_kapha ayurveda:prakriti sys:is_a
ln ayurveda:prakriti:vata_kapha ayurveda:prakriti sys:is_a
ln ayurveda:prakriti:tridoshic ayurveda:prakriti sys:is_a
# each type's dominant dosha(s)
ln ayurveda:prakriti:vata ayurveda:dosha:vata thesaurus:related
ln ayurveda:prakriti:pitta ayurveda:dosha:pitta thesaurus:related
ln ayurveda:prakriti:kapha ayurveda:dosha:kapha thesaurus:related
ln ayurveda:prakriti:vata_pitta ayurveda:dosha:vata thesaurus:related
ln ayurveda:prakriti:vata_pitta ayurveda:dosha:pitta thesaurus:related
ln ayurveda:prakriti:pitta_kapha ayurveda:dosha:pitta thesaurus:related
ln ayurveda:prakriti:pitta_kapha ayurveda:dosha:kapha thesaurus:related
ln ayurveda:prakriti:vata_kapha ayurveda:dosha:vata thesaurus:related
ln ayurveda:prakriti:vata_kapha ayurveda:dosha:kapha thesaurus:related
ln ayurveda:prakriti:tridoshic ayurveda:dosha:vata thesaurus:related
ln ayurveda:prakriti:tridoshic ayurveda:dosha:pitta thesaurus:related
ln ayurveda:prakriti:tridoshic ayurveda:dosha:kapha thesaurus:related

# ── the diagnostic qualities (gurvādi guṇa) — the observable markers assessment reads ──
# (rel ayurveda:quality: the dosha/substance exhibits this quality). Constitution is read
# through these: quality → dosha → prakriti.
def "ayurveda:quality:heavy" "Guru (heavy) — the quality of weight and grounding."
def "ayurveda:quality:light" "Laghu (light) — the quality of lightness."
def "ayurveda:quality:hot" "Ushna (hot) — the quality of heat."
def "ayurveda:quality:cold" "Shita (cold) — the quality of coolness."
def "ayurveda:quality:oily" "Snigdha (oily / unctuous) — the quality of moisture and smoothness."
def "ayurveda:quality:dry" "Ruksha (dry) — the quality of dryness."
def "ayurveda:quality:sharp" "Tikshna (sharp / penetrating) — the quality of intensity and quick action."
def "ayurveda:quality:dull" "Manda (dull / slow) — the quality of slowness."
def "ayurveda:quality:mobile" "Chala (mobile) — the quality of movement and change."
def "ayurveda:quality:stable" "Sthira (stable) — the quality of steadiness."
# Vata: dry, light, cold, mobile
ln ayurveda:dosha:vata ayurveda:quality:dry ayurveda:quality
ln ayurveda:dosha:vata ayurveda:quality:light ayurveda:quality
ln ayurveda:dosha:vata ayurveda:quality:cold ayurveda:quality
ln ayurveda:dosha:vata ayurveda:quality:mobile ayurveda:quality
# Pitta: hot, sharp, oily(light), light
ln ayurveda:dosha:pitta ayurveda:quality:hot ayurveda:quality
ln ayurveda:dosha:pitta ayurveda:quality:sharp ayurveda:quality
ln ayurveda:dosha:pitta ayurveda:quality:oily ayurveda:quality
ln ayurveda:dosha:pitta ayurveda:quality:light ayurveda:quality
# Kapha: heavy, cold, oily, dull, stable
ln ayurveda:dosha:kapha ayurveda:quality:heavy ayurveda:quality
ln ayurveda:dosha:kapha ayurveda:quality:cold ayurveda:quality
ln ayurveda:dosha:kapha ayurveda:quality:oily ayurveda:quality
ln ayurveda:dosha:kapha ayurveda:quality:dull ayurveda:quality
ln ayurveda:dosha:kapha ayurveda:quality:stable ayurveda:quality

# ═══ MATERIA MEDICA (dravya) — herbs + rejuvenation (rasāyana) ════════════════════════════════════
def "ayurveda:rasayana" "Rasayana — the rejuvenation branch of Ayurveda; substances and practices said to restore vitality, immunity, and longevity."
ln ayurveda:rasayana tradition:ayurveda thesaurus:related

def "ayurveda:herb:ashwagandha" "Ashwagandha (Withania somnifera) — a premier rasayana and adaptogen; grounding and strengthening, classically for Vata."
ln ayurveda:herb:ashwagandha tradition:ayurveda thesaurus:related
ln ayurveda:herb:ashwagandha ayurveda:rasayana thesaurus:related
ln ayurveda:herb:ashwagandha ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:ashwagandha ayurveda:rasa:bitter ayurveda:rasa
ln ayurveda:herb:ashwagandha ayurveda:rasa:astringent ayurveda:rasa
ln ayurveda:herb:ashwagandha ayurveda:rasa:sweet ayurveda:rasa
ln ayurveda:herb:ashwagandha ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:ashwagandha ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:herb:ashwagandha ayurveda:dosha:pitta ayurveda:aggravates

def "ayurveda:herb:amalaki" "Amalaki / Amla (Phyllanthus emblica) — a great rasayana; sour-dominant but five-tasted (no salt), notably cooling and Pitta-pacifying."
ln ayurveda:herb:amalaki tradition:ayurveda thesaurus:related
ln ayurveda:herb:amalaki ayurveda:rasayana thesaurus:related
ln ayurveda:herb:amalaki ayurveda:virya:cooling ayurveda:virya
ln ayurveda:herb:amalaki ayurveda:rasa:sour ayurveda:rasa
ln ayurveda:herb:amalaki ayurveda:rasa:sweet ayurveda:rasa
ln ayurveda:herb:amalaki ayurveda:rasa:astringent ayurveda:rasa
ln ayurveda:herb:amalaki ayurveda:dosha:pitta ayurveda:pacifies
ln ayurveda:herb:amalaki ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:amalaki ayurveda:dosha:kapha ayurveda:pacifies

def "ayurveda:herb:haritaki" "Haritaki (Terminalia chebula) — 'king of medicines'; astringent-dominant rasayana, especially Vata-pacifying."
ln ayurveda:herb:haritaki tradition:ayurveda thesaurus:related
ln ayurveda:herb:haritaki ayurveda:rasayana thesaurus:related
ln ayurveda:herb:haritaki ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:haritaki ayurveda:rasa:astringent ayurveda:rasa
ln ayurveda:herb:haritaki ayurveda:rasa:bitter ayurveda:rasa
ln ayurveda:herb:haritaki ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:haritaki ayurveda:dosha:kapha ayurveda:pacifies

def "ayurveda:herb:bibhitaki" "Bibhitaki (Terminalia bellirica) — astringent; classically Kapha-pacifying, supports the respiratory channels."
ln ayurveda:herb:bibhitaki tradition:ayurveda thesaurus:related
ln ayurveda:herb:bibhitaki ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:bibhitaki ayurveda:rasa:astringent ayurveda:rasa
ln ayurveda:herb:bibhitaki ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:herb:bibhitaki ayurveda:dosha:pitta ayurveda:pacifies

def "ayurveda:herb:brahmi" "Brahmi (Bacopa monnieri) — a medhya rasayana (for the mind); cooling and calming, classically Pitta/Vata-pacifying."
ln ayurveda:herb:brahmi tradition:ayurveda thesaurus:related
ln ayurveda:herb:brahmi ayurveda:rasayana thesaurus:related
ln ayurveda:herb:brahmi ayurveda:virya:cooling ayurveda:virya
ln ayurveda:herb:brahmi ayurveda:rasa:bitter ayurveda:rasa
ln ayurveda:herb:brahmi ayurveda:rasa:astringent ayurveda:rasa
ln ayurveda:herb:brahmi ayurveda:dosha:pitta ayurveda:pacifies
ln ayurveda:herb:brahmi ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:brahmi guna:sattva thesaurus:related

def "ayurveda:herb:shatavari" "Shatavari (Asparagus racemosus) — a sweet, cooling rasayana, classically nourishing and Pitta/Vata-pacifying."
ln ayurveda:herb:shatavari tradition:ayurveda thesaurus:related
ln ayurveda:herb:shatavari ayurveda:rasayana thesaurus:related
ln ayurveda:herb:shatavari ayurveda:virya:cooling ayurveda:virya
ln ayurveda:herb:shatavari ayurveda:rasa:sweet ayurveda:rasa
ln ayurveda:herb:shatavari ayurveda:rasa:bitter ayurveda:rasa
ln ayurveda:herb:shatavari ayurveda:dosha:pitta ayurveda:pacifies
ln ayurveda:herb:shatavari ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:shatavari ayurveda:dosha:kapha ayurveda:aggravates

def "ayurveda:herb:tulsi" "Tulsi / Holy Basil (Ocimum sanctum) — pungent and heating; classically Kapha/Vata-pacifying, sattvic."
ln ayurveda:herb:tulsi tradition:ayurveda thesaurus:related
ln ayurveda:herb:tulsi ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:tulsi ayurveda:rasa:pungent ayurveda:rasa
ln ayurveda:herb:tulsi ayurveda:rasa:bitter ayurveda:rasa
ln ayurveda:herb:tulsi ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:herb:tulsi ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:tulsi ayurveda:dosha:pitta ayurveda:aggravates
ln ayurveda:herb:tulsi guna:sattva thesaurus:related

def "ayurveda:herb:neem" "Neem / Nimba (Azadirachta indica) — intensely bitter and cooling; classically Pitta/Kapha-pacifying, a great blood/skin herb."
ln ayurveda:herb:neem tradition:ayurveda thesaurus:related
ln ayurveda:herb:neem ayurveda:virya:cooling ayurveda:virya
ln ayurveda:herb:neem ayurveda:rasa:bitter ayurveda:rasa
ln ayurveda:herb:neem ayurveda:rasa:astringent ayurveda:rasa
ln ayurveda:herb:neem ayurveda:dosha:pitta ayurveda:pacifies
ln ayurveda:herb:neem ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:herb:neem ayurveda:dosha:vata ayurveda:aggravates

def "ayurveda:herb:guduchi" "Guduchi / Giloy (Tinospora cordifolia) — a bitter, tridoshic rasayana; classically for immunity and clearing heat."
ln ayurveda:herb:guduchi tradition:ayurveda thesaurus:related
ln ayurveda:herb:guduchi ayurveda:rasayana thesaurus:related
ln ayurveda:herb:guduchi ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:guduchi ayurveda:rasa:bitter ayurveda:rasa
ln ayurveda:herb:guduchi ayurveda:rasa:astringent ayurveda:rasa
ln ayurveda:herb:guduchi ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:guduchi ayurveda:dosha:pitta ayurveda:pacifies
ln ayurveda:herb:guduchi ayurveda:dosha:kapha ayurveda:pacifies

def "ayurveda:herb:yashtimadhu" "Yashtimadhu / Licorice (Glycyrrhiza glabra) — sweet and cooling; classically Vata/Pitta-pacifying, soothing and a rasayana."
ln ayurveda:herb:yashtimadhu tradition:ayurveda thesaurus:related
ln ayurveda:herb:yashtimadhu ayurveda:rasayana thesaurus:related
ln ayurveda:herb:yashtimadhu ayurveda:virya:cooling ayurveda:virya
ln ayurveda:herb:yashtimadhu ayurveda:rasa:sweet ayurveda:rasa
ln ayurveda:herb:yashtimadhu ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:yashtimadhu ayurveda:dosha:pitta ayurveda:pacifies
ln ayurveda:herb:yashtimadhu ayurveda:dosha:kapha ayurveda:aggravates

def "ayurveda:herb:shunthi" "Shunthi (dry ginger, Zingiber officinale) — pungent and heating; kindles agni, classically Vata/Kapha-pacifying. The dried form of culinary ginger."
ln ayurveda:herb:shunthi tradition:ayurveda thesaurus:related
ln ayurveda:herb:shunthi ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:shunthi ayurveda:rasa:pungent ayurveda:rasa
ln ayurveda:herb:shunthi ayurveda:rasa:sweet ayurveda:rasa
ln ayurveda:herb:shunthi ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:shunthi ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:herb:shunthi ayurveda:dosha:pitta ayurveda:aggravates
ln ayurveda:herb:shunthi ingred:spice:ginger thesaurus:related

def "ayurveda:herb:haridra" "Haridra (turmeric, Curcuma longa) — bitter, pungent and astringent, heating; classically Kapha-reducing and a blood/skin herb. The medicinal aspect of culinary turmeric."
ln ayurveda:herb:haridra tradition:ayurveda thesaurus:related
ln ayurveda:herb:haridra ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:haridra ayurveda:rasa:bitter ayurveda:rasa
ln ayurveda:herb:haridra ayurveda:rasa:pungent ayurveda:rasa
ln ayurveda:herb:haridra ayurveda:rasa:astringent ayurveda:rasa
ln ayurveda:herb:haridra ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:herb:haridra ingred:spice:turmeric thesaurus:related

def "ayurveda:herb:pippali" "Pippali (long pepper, Piper longum) — pungent and heating; a rasayana for the lungs, classically Vata/Kapha-pacifying."
ln ayurveda:herb:pippali tradition:ayurveda thesaurus:related
ln ayurveda:herb:pippali ayurveda:rasayana thesaurus:related
ln ayurveda:herb:pippali ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:pippali ayurveda:rasa:pungent ayurveda:rasa
ln ayurveda:herb:pippali ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:pippali ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:herb:pippali ayurveda:dosha:pitta ayurveda:aggravates

def "ayurveda:herb:maricha" "Maricha (black pepper, Piper nigrum) — pungent and heating; kindles agni, classically Kapha/Vata-pacifying. The medicinal aspect of culinary black pepper."
ln ayurveda:herb:maricha tradition:ayurveda thesaurus:related
ln ayurveda:herb:maricha ayurveda:virya:heating ayurveda:virya
ln ayurveda:herb:maricha ayurveda:rasa:pungent ayurveda:rasa
ln ayurveda:herb:maricha ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:herb:maricha ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:herb:maricha ayurveda:dosha:pitta ayurveda:aggravates
ln ayurveda:herb:maricha ingred:spice:black_pepper thesaurus:related

# ── Classical compound formulas (made_from their component herbs) ──
def "ayurveda:formula:triphala" "Triphala — 'three fruits': amalaki, haritaki, and bibhitaki in equal parts. A gentle, tridoshic rasayana used for digestion and cleansing."
ln ayurveda:formula:triphala tradition:ayurveda thesaurus:related
ln ayurveda:formula:triphala ayurveda:rasayana thesaurus:related
ln ayurveda:formula:triphala ayurveda:herb:amalaki sys:made_from
ln ayurveda:formula:triphala ayurveda:herb:haritaki sys:made_from
ln ayurveda:formula:triphala ayurveda:herb:bibhitaki sys:made_from
ln ayurveda:formula:triphala ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:formula:triphala ayurveda:dosha:pitta ayurveda:pacifies
ln ayurveda:formula:triphala ayurveda:dosha:kapha ayurveda:pacifies

def "ayurveda:formula:trikatu" "Trikatu — 'three pungents': dry ginger, long pepper, and black pepper. Kindles agni (digestive fire); classically Kapha/Vata-pacifying."
ln ayurveda:formula:trikatu tradition:ayurveda thesaurus:related
ln ayurveda:formula:trikatu ayurveda:herb:shunthi sys:made_from
ln ayurveda:formula:trikatu ayurveda:herb:pippali sys:made_from
ln ayurveda:formula:trikatu ayurveda:herb:maricha sys:made_from
ln ayurveda:formula:trikatu ayurveda:virya:heating ayurveda:virya
ln ayurveda:formula:trikatu ayurveda:dosha:kapha ayurveda:pacifies
ln ayurveda:formula:trikatu ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:formula:trikatu ayurveda:dosha:pitta ayurveda:aggravates

def "ayurveda:formula:chyawanprash" "Chyawanprash — a classical amalaki-based rasayana paste (herbal jam) taken as a daily tonic for vitality and immunity."
ln ayurveda:formula:chyawanprash tradition:ayurveda thesaurus:related
ln ayurveda:formula:chyawanprash ayurveda:rasayana thesaurus:related
ln ayurveda:formula:chyawanprash ayurveda:herb:amalaki sys:made_from
ln ayurveda:formula:chyawanprash ayurveda:dosha:vata ayurveda:pacifies
ln ayurveda:formula:chyawanprash ayurveda:dosha:pitta ayurveda:pacifies

# ── rasāyana as a rejuvenation practice sits close to Yoga's aim of vitality ──
ln ayurveda:rasayana yoga:yoga thesaurus:related
