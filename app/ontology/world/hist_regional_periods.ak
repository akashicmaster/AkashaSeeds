# Akasha ontology (world pack) — regional history periodization.
# Different civilizations divide time their own way. Each regional period → its
# country (geo:), the matching global period (hist:period:), and chained in order.

def "hist:regional_period" "A region-specific historical period/dynasty."
# ── Japan ──
def "hist:period:japan:jomon" "The hunter-gatherer age of cord-marked pottery (~14,000–300 BCE)."
ln hist:period:japan:jomon hist:regional_period thesaurus:related
ln hist:period:japan:jomon geo:country:JPN hist:period_of
ln hist:period:japan:jomon hist:period:neolithic hist:concurrent_with
def "hist:period:japan:yayoi" "Wet-rice farming, bronze and iron arrive from the continent."
ln hist:period:japan:yayoi hist:regional_period thesaurus:related
ln hist:period:japan:yayoi geo:country:JPN hist:period_of
ln hist:period:japan:yayoi hist:period:iron_age hist:concurrent_with
ln hist:period:japan:jomon hist:period:japan:yayoi chrono:before
def "hist:period:japan:kofun" "The age of great keyhole burial mounds and emerging state."
ln hist:period:japan:kofun hist:regional_period thesaurus:related
ln hist:period:japan:kofun geo:country:JPN hist:period_of
ln hist:period:japan:kofun hist:period:late_antiquity hist:concurrent_with
ln hist:period:japan:yayoi hist:period:japan:kofun chrono:before
def "hist:period:japan:nara" "The first permanent capital; Buddhism and the Chinese model."
ln hist:period:japan:nara hist:regional_period thesaurus:related
ln hist:period:japan:nara geo:country:JPN hist:period_of
ln hist:period:japan:nara hist:period:early_middle_ages hist:concurrent_with
ln hist:period:japan:kofun hist:period:japan:nara chrono:before
def "hist:period:japan:heian" "The classical court age of the Tale of Genji and courtly refinement."
ln hist:period:japan:heian hist:regional_period thesaurus:related
ln hist:period:japan:heian geo:country:JPN hist:period_of
ln hist:period:japan:heian hist:period:high_middle_ages hist:concurrent_with
ln hist:period:japan:nara hist:period:japan:heian chrono:before
def "hist:period:japan:kamakura" "The first shogunate; the rise of the samurai."
ln hist:period:japan:kamakura hist:regional_period thesaurus:related
ln hist:period:japan:kamakura geo:country:JPN hist:period_of
ln hist:period:japan:kamakura hist:period:high_middle_ages hist:concurrent_with
ln hist:period:japan:heian hist:period:japan:kamakura chrono:before
def "hist:period:japan:muromachi" "The Ashikaga shoguns; Zen, tea and civil war."
ln hist:period:japan:muromachi hist:regional_period thesaurus:related
ln hist:period:japan:muromachi geo:country:JPN hist:period_of
ln hist:period:japan:muromachi hist:period:late_middle_ages hist:concurrent_with
ln hist:period:japan:kamakura hist:period:japan:muromachi chrono:before
def "hist:period:japan:edo" "The Tokugawa peace of 250 closed years — cities, ukiyo-e, kabuki."
ln hist:period:japan:edo hist:regional_period thesaurus:related
ln hist:period:japan:edo geo:country:JPN hist:period_of
ln hist:period:japan:edo hist:period:early_modern hist:concurrent_with
ln hist:period:japan:muromachi hist:period:japan:edo chrono:before
def "hist:period:japan:meiji" "Headlong modernization after 1868."
ln hist:period:japan:meiji hist:regional_period thesaurus:related
ln hist:period:japan:meiji geo:country:JPN hist:period_of
ln hist:period:japan:meiji hist:period:modern_era hist:concurrent_with
ln hist:period:japan:edo hist:period:japan:meiji chrono:before

# ── China — dynasties ──
def "hist:period:china:shang" "The first documented dynasty — oracle bones and bronze."
ln hist:period:china:shang hist:regional_period thesaurus:related
ln hist:period:china:shang geo:country:CHN hist:period_of
ln hist:period:china:shang hist:period:bronze_age hist:concurrent_with
def "hist:period:china:zhou" "The long dynasty of the Mandate of Heaven and the Hundred Schools."
ln hist:period:china:zhou hist:regional_period thesaurus:related
ln hist:period:china:zhou geo:country:CHN hist:period_of
ln hist:period:china:zhou hist:period:iron_age hist:concurrent_with
ln hist:period:china:shang hist:period:china:zhou chrono:before
def "hist:period:china:qin" "The first unified empire — Great Wall, standardized script."
ln hist:period:china:qin hist:regional_period thesaurus:related
ln hist:period:china:qin geo:country:CHN hist:period_of
ln hist:period:china:qin hist:period:classical_antiquity hist:concurrent_with
ln hist:period:china:zhou hist:period:china:qin chrono:before
def "hist:period:china:han" "The classical empire that named the Han people; the Silk Road."
ln hist:period:china:han hist:regional_period thesaurus:related
ln hist:period:china:han geo:country:CHN hist:period_of
ln hist:period:china:han hist:period:classical_antiquity hist:concurrent_with
ln hist:period:china:qin hist:period:china:han chrono:before
def "hist:period:china:tang" "The cosmopolitan golden age of poetry and Buddhism."
ln hist:period:china:tang hist:regional_period thesaurus:related
ln hist:period:china:tang geo:country:CHN hist:period_of
ln hist:period:china:tang hist:period:early_middle_ages hist:concurrent_with
ln hist:period:china:han hist:period:china:tang chrono:before
def "hist:period:china:song" "An age of commerce, printing, gunpowder and the compass."
ln hist:period:china:song hist:regional_period thesaurus:related
ln hist:period:china:song geo:country:CHN hist:period_of
ln hist:period:china:song hist:period:high_middle_ages hist:concurrent_with
ln hist:period:china:tang hist:period:china:song chrono:before
def "hist:period:china:yuan" "Mongol rule under Kublai Khan."
ln hist:period:china:yuan hist:regional_period thesaurus:related
ln hist:period:china:yuan geo:country:CHN hist:period_of
ln hist:period:china:yuan hist:period:high_middle_ages hist:concurrent_with
ln hist:period:china:song hist:period:china:yuan chrono:before
def "hist:period:china:ming" "Restoration, the Forbidden City and the treasure voyages."
ln hist:period:china:ming hist:regional_period thesaurus:related
ln hist:period:china:ming geo:country:CHN hist:period_of
ln hist:period:china:ming hist:period:age_of_exploration hist:concurrent_with
ln hist:period:china:yuan hist:period:china:ming chrono:before
def "hist:period:china:qing" "The last, Manchu dynasty, to 1912."
ln hist:period:china:qing hist:regional_period thesaurus:related
ln hist:period:china:qing geo:country:CHN hist:period_of
ln hist:period:china:qing hist:period:early_modern hist:concurrent_with
ln hist:period:china:ming hist:period:china:qing chrono:before

# ── Egypt ──
def "hist:period:egypt:old_kingdom" "The Age of the Pyramids."
ln hist:period:egypt:old_kingdom hist:regional_period thesaurus:related
ln hist:period:egypt:old_kingdom geo:country:EGY hist:period_of
ln hist:period:egypt:old_kingdom hist:period:bronze_age hist:concurrent_with
def "hist:period:egypt:middle_kingdom" "Reunification and classical Egyptian literature."
ln hist:period:egypt:middle_kingdom hist:regional_period thesaurus:related
ln hist:period:egypt:middle_kingdom geo:country:EGY hist:period_of
ln hist:period:egypt:middle_kingdom hist:period:bronze_age hist:concurrent_with
ln hist:period:egypt:old_kingdom hist:period:egypt:middle_kingdom chrono:before
def "hist:period:egypt:new_kingdom" "The imperial age of Hatshepsut, Akhenaten, Tutankhamun and Ramesses."
ln hist:period:egypt:new_kingdom hist:regional_period thesaurus:related
ln hist:period:egypt:new_kingdom geo:country:EGY hist:period_of
ln hist:period:egypt:new_kingdom hist:period:bronze_age hist:concurrent_with
ln hist:period:egypt:middle_kingdom hist:period:egypt:new_kingdom chrono:before

# ── Mesoamerica ──
def "hist:period:mesoamerica:preclassic" "The Olmec foundation and early villages."
ln hist:period:mesoamerica:preclassic hist:regional_period thesaurus:related
ln hist:period:mesoamerica:preclassic geo:country:MEX hist:period_of
ln hist:period:mesoamerica:preclassic hist:period:bronze_age hist:concurrent_with
def "hist:period:mesoamerica:classic_maya" "The Maya florescence of glyphs, calendars and city-states."
ln hist:period:mesoamerica:classic_maya hist:regional_period thesaurus:related
ln hist:period:mesoamerica:classic_maya geo:country:MEX hist:period_of
ln hist:period:mesoamerica:classic_maya hist:period:classical_antiquity hist:concurrent_with
ln hist:period:mesoamerica:preclassic hist:period:mesoamerica:classic_maya chrono:before
def "hist:period:mesoamerica:postclassic" "The Toltec and Aztec era to the Spanish conquest."
ln hist:period:mesoamerica:postclassic hist:regional_period thesaurus:related
ln hist:period:mesoamerica:postclassic geo:country:MEX hist:period_of
ln hist:period:mesoamerica:postclassic hist:period:late_middle_ages hist:concurrent_with
ln hist:period:mesoamerica:classic_maya hist:period:mesoamerica:postclassic chrono:before

