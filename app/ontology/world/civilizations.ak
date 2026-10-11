# Ancient Civilizations — the ancient cultures of every continent, region by region.
# B-tier world pack; read by the archives 'Ancient Civilizations' room (/ancient/).
# Namespace: ancient:  — collision-free (civ: is the civic-administration namespace).
# ~77 civilizations across 14 civilisational regions. sys:is_a / sys:part_of taxonomy;
# ancient:all is the superset dictionary, ancient:region:<id>:members the per-region subsets.

# ── classes ──
def "ancient:civilization" "A civilization — an ancient culture, people, or state, set on the world map by region."
def "ancient:region" "A civilisational region — a culture-area grouping the ancient civilizations of one part of the world."

# ══ 1 · Mesopotamia & the Near East ══
def "ancient:region:mesopotamia" "Mesopotamia & the Near East — the fertile crescent. Between the Tigris and Euphrates, the world wrote its first words and raised its first cities."
ln ancient:region:mesopotamia ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:mesopotamia"
def "ancient:sumer" "Sumer · ki-en-gir (c.4500–1900 BCE) — The first cities — Uruk, Ur, Eridu — and cuneiform, the earliest writing."
ln ancient:sumer ancient:civilization sys:is_a
ln ancient:sumer ancient:region:mesopotamia sys:part_of
set.add name="ancient:all" id="ancient:sumer"
set.add name="ancient:region:mesopotamia:members" id="ancient:sumer"
def "ancient:akkad" "Akkadian Empire · Akkad (c.2334–2154 BCE) — Sargon of Akkad forged history’s first empire."
ln ancient:akkad ancient:civilization sys:is_a
ln ancient:akkad ancient:region:mesopotamia sys:part_of
set.add name="ancient:all" id="ancient:akkad"
set.add name="ancient:region:mesopotamia:members" id="ancient:akkad"
def "ancient:babylon" "Babylonia · Bābilim (c.1894–539 BCE) — Hammurabi’s law-code; Nebuchadnezzar’s hanging gardens."
ln ancient:babylon ancient:civilization sys:is_a
ln ancient:babylon ancient:region:mesopotamia sys:part_of
set.add name="ancient:all" id="ancient:babylon"
set.add name="ancient:region:mesopotamia:members" id="ancient:babylon"
def "ancient:assyria" "Assyria · Aššur (c.2500–609 BCE) — Iron armies and the great library of Ashurbanipal at Nineveh."
ln ancient:assyria ancient:civilization sys:is_a
ln ancient:assyria ancient:region:mesopotamia sys:part_of
set.add name="ancient:all" id="ancient:assyria"
set.add name="ancient:region:mesopotamia:members" id="ancient:assyria"
def "ancient:elam" "Elam · Haltamti (c.3200–539 BCE) — The kingdom of Susa, ancient rival of Sumer."
ln ancient:elam ancient:civilization sys:is_a
ln ancient:elam ancient:region:mesopotamia sys:part_of
set.add name="ancient:all" id="ancient:elam"
set.add name="ancient:region:mesopotamia:members" id="ancient:elam"
def "ancient:hittite" "Hittites · Hatti (c.1650–1180 BCE) — An Anatolian iron-age power ruled from Hattusa."
ln ancient:hittite ancient:civilization sys:is_a
ln ancient:hittite ancient:region:mesopotamia sys:part_of
set.add name="ancient:all" id="ancient:hittite"
set.add name="ancient:region:mesopotamia:members" id="ancient:hittite"
def "ancient:phoenicia" "Phoenicia · Kanaʿan (c.1500–300 BCE) — Sea-traders of Tyre and Sidon who gave the world its alphabet."
ln ancient:phoenicia ancient:civilization sys:is_a
ln ancient:phoenicia ancient:region:mesopotamia sys:part_of
set.add name="ancient:all" id="ancient:phoenicia"
set.add name="ancient:region:mesopotamia:members" id="ancient:phoenicia"

# ══ 2 · Ancient Egypt & the Nile ══
def "ancient:region:egypt" "Ancient Egypt & the Nile — the gift of the river. A civilization three thousand years long, threaded on a single river from the delta to Nubia."
ln ancient:region:egypt ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:egypt"
def "ancient:egypt:old_kingdom" "Old Kingdom Egypt · Kemet (c.2686–2181 BCE) — The age of the pyramids of Giza."
ln ancient:egypt:old_kingdom ancient:civilization sys:is_a
ln ancient:egypt:old_kingdom ancient:region:egypt sys:part_of
set.add name="ancient:all" id="ancient:egypt:old_kingdom"
set.add name="ancient:region:egypt:members" id="ancient:egypt:old_kingdom"
def "ancient:egypt:new_kingdom" "New Kingdom Egypt · Kemet (c.1550–1070 BCE) — Thebes, Karnak, and the great pharaohs — Hatshepsut, Ramesses."
ln ancient:egypt:new_kingdom ancient:civilization sys:is_a
ln ancient:egypt:new_kingdom ancient:region:egypt sys:part_of
set.add name="ancient:all" id="ancient:egypt:new_kingdom"
set.add name="ancient:region:egypt:members" id="ancient:egypt:new_kingdom"
def "ancient:kush" "Kerma & Kush · Nubia (c.2500–350 BCE) — Nubian kingdoms whose kings ruled Egypt as the 25th Dynasty."
ln ancient:kush ancient:civilization sys:is_a
ln ancient:kush ancient:region:egypt sys:part_of
set.add name="ancient:all" id="ancient:kush"
set.add name="ancient:region:egypt:members" id="ancient:kush"
def "ancient:meroe" "Meroë · Kingdom of Meroë (c.800 BCE–350 CE) — Iron and steep pyramids on the upper Nile."
ln ancient:meroe ancient:civilization sys:is_a
ln ancient:meroe ancient:region:egypt sys:part_of
set.add name="ancient:all" id="ancient:meroe"
set.add name="ancient:region:egypt:members" id="ancient:meroe"

# ══ 3 · Indus & South Asia ══
def "ancient:region:indus" "Indus & South Asia — the cities of the seven rivers. From grid-planned cities on the Indus to the first empires of the subcontinent."
ln ancient:region:indus ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:indus"
def "ancient:indus" "Indus Valley (Harappan) · Meluhha (c.3300–1300 BCE) — Mohenjo-daro and Harappa — plumbing, planning, an unread script."
ln ancient:indus ancient:civilization sys:is_a
ln ancient:indus ancient:region:indus sys:part_of
set.add name="ancient:all" id="ancient:indus"
set.add name="ancient:region:indus:members" id="ancient:indus"
def "ancient:vedic" "Vedic Civilization · Sapta Sindhu (c.1500–500 BCE) — The Vedas and the roots of Indian thought."
ln ancient:vedic ancient:civilization sys:is_a
ln ancient:vedic ancient:region:indus sys:part_of
set.add name="ancient:all" id="ancient:vedic"
set.add name="ancient:region:indus:members" id="ancient:vedic"
def "ancient:maurya" "Maurya Empire · Maurya (c.322–185 BCE) — Ashoka the Great; the first empire over most of India."
ln ancient:maurya ancient:civilization sys:is_a
ln ancient:maurya ancient:region:indus sys:part_of
set.add name="ancient:all" id="ancient:maurya"
set.add name="ancient:region:indus:members" id="ancient:maurya"
def "ancient:gupta" "Gupta Empire · Gupta (c.320–550 CE) — A golden age — the decimal zero, astronomy, Sanskrit arts."
ln ancient:gupta ancient:civilization sys:is_a
ln ancient:gupta ancient:region:indus sys:part_of
set.add name="ancient:all" id="ancient:gupta"
set.add name="ancient:region:indus:members" id="ancient:gupta"

# ══ 4 · Ancient China & East Asia ══
def "ancient:region:china" "Ancient China & East Asia — the middle kingdom & its neighbours. Oracle bones to the first empire, and the island and peninsula cultures that grew alongside."
ln ancient:region:china ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:china"
def "ancient:shang" "Shang Dynasty · 商 (c.1600–1046 BCE) — Bronze, oracle bones, the first attested Chinese state."
ln ancient:shang ancient:civilization sys:is_a
ln ancient:shang ancient:region:china sys:part_of
set.add name="ancient:all" id="ancient:shang"
set.add name="ancient:region:china:members" id="ancient:shang"
def "ancient:zhou" "Zhou Dynasty · 周 (1046–256 BCE) — The Mandate of Heaven; Confucius and Laozi."
ln ancient:zhou ancient:civilization sys:is_a
ln ancient:zhou ancient:region:china sys:part_of
set.add name="ancient:all" id="ancient:zhou"
set.add name="ancient:region:china:members" id="ancient:zhou"
def "ancient:qin" "Qin Dynasty · 秦 (221–206 BCE) — The first unified empire; the Terracotta Army; the Wall begun."
ln ancient:qin ancient:civilization sys:is_a
ln ancient:qin ancient:region:china sys:part_of
set.add name="ancient:all" id="ancient:qin"
set.add name="ancient:region:china:members" id="ancient:qin"
def "ancient:han" "Han Dynasty · 漢 (206 BCE–220 CE) — The Silk Road, paper, and the classic model of empire."
ln ancient:han ancient:civilization sys:is_a
ln ancient:han ancient:region:china sys:part_of
set.add name="ancient:all" id="ancient:han"
set.add name="ancient:region:china:members" id="ancient:han"
def "ancient:gojoseon" "Gojoseon · 古朝鮮 (c.2000?–108 BCE) — The first kingdom of Korea."
ln ancient:gojoseon ancient:civilization sys:is_a
ln ancient:gojoseon ancient:region:china sys:part_of
set.add name="ancient:all" id="ancient:gojoseon"
set.add name="ancient:region:china:members" id="ancient:gojoseon"
def "ancient:yayoi" "Jōmon & Yayoi · 縄文・弥生 (c.14000 BCE–300 CE) — Japan’s cord-marked potters, then wet-rice and metal."
ln ancient:yayoi ancient:civilization sys:is_a
ln ancient:yayoi ancient:region:china sys:part_of
set.add name="ancient:all" id="ancient:yayoi"
set.add name="ancient:region:china:members" id="ancient:yayoi"

# ══ 5 · The Aegean & Mediterranean ══
def "ancient:region:aegean" "The Aegean & Mediterranean — the wine-dark sea. Palace-kingdoms of Crete, the world of Homer, and the classical powers that shaped the West."
ln ancient:region:aegean ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:aegean"
def "ancient:minoan" "Minoan Crete · Kaptara (c.3000–1100 BCE) — Knossos and Linear A — Europe’s first civilization."
ln ancient:minoan ancient:civilization sys:is_a
ln ancient:minoan ancient:region:aegean sys:part_of
set.add name="ancient:all" id="ancient:minoan"
set.add name="ancient:region:aegean:members" id="ancient:minoan"
def "ancient:mycenae" "Mycenaean Greece · Aḫḫiyawa (c.1600–1100 BCE) — Linear B and the citadels of the Homeric age."
ln ancient:mycenae ancient:civilization sys:is_a
ln ancient:mycenae ancient:region:aegean sys:part_of
set.add name="ancient:all" id="ancient:mycenae"
set.add name="ancient:region:aegean:members" id="ancient:mycenae"
def "ancient:greece" "Classical Greece · Hellas (c.800–323 BCE) — The polis — democracy, philosophy, drama, geometry."
ln ancient:greece ancient:civilization sys:is_a
ln ancient:greece ancient:region:aegean sys:part_of
set.add name="ancient:all" id="ancient:greece"
set.add name="ancient:region:aegean:members" id="ancient:greece"
def "ancient:etruscan" "Etruscans · Rasenna (c.900–100 BCE) — The tomb-painters of pre-Roman Italy."
ln ancient:etruscan ancient:civilization sys:is_a
ln ancient:etruscan ancient:region:aegean sys:part_of
set.add name="ancient:all" id="ancient:etruscan"
set.add name="ancient:region:aegean:members" id="ancient:etruscan"
def "ancient:rome" "Ancient Rome · Roma (753 BCE–476 CE) — Republic to empire — law, roads, concrete, an inherited world."
ln ancient:rome ancient:civilization sys:is_a
ln ancient:rome ancient:region:aegean sys:part_of
set.add name="ancient:all" id="ancient:rome"
set.add name="ancient:region:aegean:members" id="ancient:rome"
def "ancient:carthage" "Carthage · Qart-ḥadašt (c.814–146 BCE) — A Phoenician sea-empire; Hannibal crossed the Alps."
ln ancient:carthage ancient:civilization sys:is_a
ln ancient:carthage ancient:region:aegean sys:part_of
set.add name="ancient:all" id="ancient:carthage"
set.add name="ancient:region:aegean:members" id="ancient:carthage"

# ══ 6 · Persia & the Iranian Plateau ══
def "ancient:region:persia" "Persia & the Iranian Plateau — the kings of kings. From Cyrus to the Sasanians — a millennium of empires bridging East and West."
ln ancient:region:persia ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:persia"
def "ancient:achaemenid" "Achaemenid Persia · Pārsa (550–330 BCE) — Cyrus and Darius; Persepolis; the largest empire of its age."
ln ancient:achaemenid ancient:civilization sys:is_a
ln ancient:achaemenid ancient:region:persia sys:part_of
set.add name="ancient:all" id="ancient:achaemenid"
set.add name="ancient:region:persia:members" id="ancient:achaemenid"
def "ancient:parthia" "Parthian Empire · Ashkâniân (247 BCE–224 CE) — Rome’s eastern rival; masters of the horse-archer."
ln ancient:parthia ancient:civilization sys:is_a
ln ancient:parthia ancient:region:persia sys:part_of
set.add name="ancient:all" id="ancient:parthia"
set.add name="ancient:region:persia:members" id="ancient:parthia"
def "ancient:sasanian" "Sasanian Empire · Ērānshahr (224–651 CE) — The last pre-Islamic Persian empire; Zoroastrian high culture."
ln ancient:sasanian ancient:civilization sys:is_a
ln ancient:sasanian ancient:region:persia sys:part_of
set.add name="ancient:all" id="ancient:sasanian"
set.add name="ancient:region:persia:members" id="ancient:sasanian"
def "ancient:media" "Median Empire · Māda (c.678–550 BCE) — The first Iranian empire, overthrown by Cyrus."
ln ancient:media ancient:civilization sys:is_a
ln ancient:media ancient:region:persia sys:part_of
set.add name="ancient:all" id="ancient:media"
set.add name="ancient:region:persia:members" id="ancient:media"

# ══ 7 · The Steppe & Central Asia ══
def "ancient:region:steppe" "The Steppe & Central Asia — the sea of grass. Horse-lords and Silk-Road cities across the great grasslands between the settled empires."
ln ancient:region:steppe ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:steppe"
def "ancient:scythian" "Scythians · Skuδa (c.900–200 BCE) — Nomad horsemen famous for their golden animal art."
ln ancient:scythian ancient:civilization sys:is_a
ln ancient:scythian ancient:region:steppe sys:part_of
set.add name="ancient:all" id="ancient:scythian"
set.add name="ancient:region:steppe:members" id="ancient:scythian"
def "ancient:xiongnu" "Xiongnu · 匈奴 (c.209 BCE–100 CE) — The steppe confederation the Han built the Wall against."
ln ancient:xiongnu ancient:civilization sys:is_a
ln ancient:xiongnu ancient:region:steppe sys:part_of
set.add name="ancient:all" id="ancient:xiongnu"
set.add name="ancient:region:steppe:members" id="ancient:xiongnu"
def "ancient:sogdia" "Sogdia & Bactria · Suγδ (c.600 BCE–800 CE) — The Oxus cities and the merchants of the Silk Road."
ln ancient:sogdia ancient:civilization sys:is_a
ln ancient:sogdia ancient:region:steppe sys:part_of
set.add name="ancient:all" id="ancient:sogdia"
set.add name="ancient:region:steppe:members" id="ancient:sogdia"
def "ancient:kushan" "Kushan Empire · Kushan (c.30–375 CE) — Gandhara and the Greco-Buddhist fusion of art."
ln ancient:kushan ancient:civilization sys:is_a
ln ancient:kushan ancient:region:steppe sys:part_of
set.add name="ancient:all" id="ancient:kushan"
set.add name="ancient:region:steppe:members" id="ancient:kushan"

# ══ 8 · Ancient Europe ══
def "ancient:region:europe" "Ancient Europe — beyond the Mediterranean. The iron-age peoples of temperate Europe and the seafarers of the North."
ln ancient:region:europe ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:europe"
def "ancient:celt" "Celts · Keltoi (c.1200 BCE–50 CE) — Hallstatt and La Tène — Gaul, Britain, Iberia, Galatia."
ln ancient:celt ancient:civilization sys:is_a
ln ancient:celt ancient:region:europe sys:part_of
set.add name="ancient:all" id="ancient:celt"
set.add name="ancient:region:europe:members" id="ancient:celt"
def "ancient:thracian" "Thracians · Thrāix (c.1500–300 BCE) — Balkan warrior-culture famed for gold hoards."
ln ancient:thracian ancient:civilization sys:is_a
ln ancient:thracian ancient:region:europe sys:part_of
set.add name="ancient:all" id="ancient:thracian"
set.add name="ancient:region:europe:members" id="ancient:thracian"
def "ancient:norse" "Norse & Vikings · Norrœnir (c.400–1100 CE) — Sagas, longships, and a reach from Baghdad to Newfoundland."
ln ancient:norse ancient:civilization sys:is_a
ln ancient:norse ancient:region:europe sys:part_of
set.add name="ancient:all" id="ancient:norse"
set.add name="ancient:region:europe:members" id="ancient:norse"
def "ancient:iberian" "Tartessos & Iberians · Tartessos (c.1200–200 BCE) — The rich cultures of the ancient Iberian peninsula."
ln ancient:iberian ancient:civilization sys:is_a
ln ancient:iberian ancient:region:europe sys:part_of
set.add name="ancient:all" id="ancient:iberian"
set.add name="ancient:region:europe:members" id="ancient:iberian"

# ══ 9 · Mesoamerica ══
def "ancient:region:mesoamerica" "Mesoamerica — the land of the sacred count. From the Olmec mother-culture to the Aztec sun — writing, the Long Count, and towering cities."
ln ancient:region:mesoamerica ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:mesoamerica"
def "ancient:olmec" "Olmec · the mother-culture (c.1500–400 BCE) — Colossal basalt heads; the root of Mesoamerican culture."
ln ancient:olmec ancient:civilization sys:is_a
ln ancient:olmec ancient:region:mesoamerica sys:part_of
set.add name="ancient:all" id="ancient:olmec"
set.add name="ancient:region:mesoamerica:members" id="ancient:olmec"
def "ancient:maya" "Maya · Maya (c.2000 BCE–1500 CE) — Full writing, the Long Count calendar, Tikal and Palenque."
ln ancient:maya ancient:civilization sys:is_a
ln ancient:maya ancient:region:mesoamerica sys:part_of
set.add name="ancient:all" id="ancient:maya"
set.add name="ancient:region:mesoamerica:members" id="ancient:maya"
def "ancient:zapotec" "Zapotec · Bene Za (c.500 BCE–1521 CE) — Monte Albán, high above the Oaxaca valley."
ln ancient:zapotec ancient:civilization sys:is_a
ln ancient:zapotec ancient:region:mesoamerica sys:part_of
set.add name="ancient:all" id="ancient:zapotec"
set.add name="ancient:region:mesoamerica:members" id="ancient:zapotec"
def "ancient:teotihuacan" "Teotihuacan · the place of the gods (c.100 BCE–550 CE) — A vast planned city and its Pyramid of the Sun."
ln ancient:teotihuacan ancient:civilization sys:is_a
ln ancient:teotihuacan ancient:region:mesoamerica sys:part_of
set.add name="ancient:all" id="ancient:teotihuacan"
set.add name="ancient:region:mesoamerica:members" id="ancient:teotihuacan"
def "ancient:toltec" "Toltec · Tōltēcah (c.900–1150 CE) — The builders of Tula, revered by the Aztecs who followed."
ln ancient:toltec ancient:civilization sys:is_a
ln ancient:toltec ancient:region:mesoamerica sys:part_of
set.add name="ancient:all" id="ancient:toltec"
set.add name="ancient:region:mesoamerica:members" id="ancient:toltec"
def "ancient:aztec" "Aztec (Mexica) · Mēxihcah (c.1300–1521 CE) — Tenochtitlan on the lake and the Triple Alliance."
ln ancient:aztec ancient:civilization sys:is_a
ln ancient:aztec ancient:region:mesoamerica sys:part_of
set.add name="ancient:all" id="ancient:aztec"
set.add name="ancient:region:mesoamerica:members" id="ancient:aztec"

# ══ 10 · The Andes & South America ══
def "ancient:region:andes" "The Andes & South America — the four quarters. The Americas’ oldest cities, and a chain of highland and coastal states ending with the Inca."
ln ancient:region:andes ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:andes"
def "ancient:caral" "Norte Chico (Caral) · Caral-Supe (c.3500–1800 BCE) — The oldest known civilization in the Americas."
ln ancient:caral ancient:civilization sys:is_a
ln ancient:caral ancient:region:andes sys:part_of
set.add name="ancient:all" id="ancient:caral"
set.add name="ancient:region:andes:members" id="ancient:caral"
def "ancient:chavin" "Chavín · Chavín (c.900–200 BCE) — A pan-Andean cult and art-style from the highlands."
ln ancient:chavin ancient:civilization sys:is_a
ln ancient:chavin ancient:region:andes sys:part_of
set.add name="ancient:all" id="ancient:chavin"
set.add name="ancient:region:andes:members" id="ancient:chavin"
def "ancient:nazca" "Nazca · Nasca (c.100 BCE–800 CE) — The great geoglyphs drawn across the desert floor."
ln ancient:nazca ancient:civilization sys:is_a
ln ancient:nazca ancient:region:andes sys:part_of
set.add name="ancient:all" id="ancient:nazca"
set.add name="ancient:region:andes:members" id="ancient:nazca"
def "ancient:moche" "Moche · Moche (c.100–800 CE) — North-coast lords and their vivid portrait ceramics."
ln ancient:moche ancient:civilization sys:is_a
ln ancient:moche ancient:region:andes sys:part_of
set.add name="ancient:all" id="ancient:moche"
set.add name="ancient:region:andes:members" id="ancient:moche"
def "ancient:tiwanaku" "Tiwanaku · Tiwanaku (c.550–1000 CE) — The great state on the shores of Lake Titicaca."
ln ancient:tiwanaku ancient:civilization sys:is_a
ln ancient:tiwanaku ancient:region:andes sys:part_of
set.add name="ancient:all" id="ancient:tiwanaku"
set.add name="ancient:region:andes:members" id="ancient:tiwanaku"
def "ancient:wari" "Wari · Wari (c.600–1000 CE) — An Andean empire of roads a half-millennium before the Inca."
ln ancient:wari ancient:civilization sys:is_a
ln ancient:wari ancient:region:andes sys:part_of
set.add name="ancient:all" id="ancient:wari"
set.add name="ancient:region:andes:members" id="ancient:wari"
def "ancient:chimu" "Chimú · Chimor (c.900–1470 CE) — Chan Chan, the largest adobe city on earth."
ln ancient:chimu ancient:civilization sys:is_a
ln ancient:chimu ancient:region:andes sys:part_of
set.add name="ancient:all" id="ancient:chimu"
set.add name="ancient:region:andes:members" id="ancient:chimu"
def "ancient:inca" "Inca · Tawantinsuyu (c.1400–1533 CE) — Cusco, Machu Picchu — the largest empire of the Americas."
ln ancient:inca ancient:civilization sys:is_a
ln ancient:inca ancient:region:andes sys:part_of
set.add name="ancient:all" id="ancient:inca"
set.add name="ancient:region:andes:members" id="ancient:inca"

# ══ 11 · North America ══
def "ancient:region:north_america" "North America — the mound-builders & the pueblos. The city-builders and earthwork cultures of the North American continent."
ln ancient:region:north_america ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:north_america"
def "ancient:puebloan" "Ancestral Puebloan · Anasazi (c.100–1600 CE) — Chaco Canyon and the great cliff dwellings."
ln ancient:puebloan ancient:civilization sys:is_a
ln ancient:puebloan ancient:region:north_america sys:part_of
set.add name="ancient:all" id="ancient:puebloan"
set.add name="ancient:region:north_america:members" id="ancient:puebloan"
def "ancient:hohokam" "Hohokam · Huhugam (c.300–1500 CE) — Canal-farmers of the Sonoran desert."
ln ancient:hohokam ancient:civilization sys:is_a
ln ancient:hohokam ancient:region:north_america sys:part_of
set.add name="ancient:all" id="ancient:hohokam"
set.add name="ancient:region:north_america:members" id="ancient:hohokam"
def "ancient:hopewell" "Hopewell & Adena · Hopewell (c.800 BCE–500 CE) — The great earthwork-builders of the Ohio valley."
ln ancient:hopewell ancient:civilization sys:is_a
ln ancient:hopewell ancient:region:north_america sys:part_of
set.add name="ancient:all" id="ancient:hopewell"
set.add name="ancient:region:north_america:members" id="ancient:hopewell"
def "ancient:cahokia" "Mississippian (Cahokia) · Mississippian (c.800–1600 CE) — Cahokia, a mound-city that rivaled medieval European towns."
ln ancient:cahokia ancient:civilization sys:is_a
ln ancient:cahokia ancient:region:north_america sys:part_of
set.add name="ancient:all" id="ancient:cahokia"
set.add name="ancient:region:north_america:members" id="ancient:cahokia"

# ══ 12 · Sub-Saharan Africa ══
def "ancient:region:africa" "Sub-Saharan Africa — the gold, the bronze & the stone. The empires and city-states of the west, the east coast, and the great stone city of the south."
ln ancient:region:africa ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:africa"
def "ancient:nok" "Nok · Nok (c.1500 BCE–300 CE) — Nigeria’s terracotta sculptors and early iron-workers."
ln ancient:nok ancient:civilization sys:is_a
ln ancient:nok ancient:region:africa sys:part_of
set.add name="ancient:all" id="ancient:nok"
set.add name="ancient:region:africa:members" id="ancient:nok"
def "ancient:aksum" "Aksum · Aksum (c.100–940 CE) — An Ethiopian empire of obelisks and Red-Sea trade."
ln ancient:aksum ancient:civilization sys:is_a
ln ancient:aksum ancient:region:africa sys:part_of
set.add name="ancient:all" id="ancient:aksum"
set.add name="ancient:region:africa:members" id="ancient:aksum"
def "ancient:ghana" "Ghana Empire · Wagadou (c.300–1200 CE) — The first great gold-empire of the western Sahel."
ln ancient:ghana ancient:civilization sys:is_a
ln ancient:ghana ancient:region:africa sys:part_of
set.add name="ancient:all" id="ancient:ghana"
set.add name="ancient:region:africa:members" id="ancient:ghana"
def "ancient:mali" "Mali Empire · Manden Kurufaba (c.1235–1600 CE) — Mansa Musa and the scholars of Timbuktu."
ln ancient:mali ancient:civilization sys:is_a
ln ancient:mali ancient:region:africa sys:part_of
set.add name="ancient:all" id="ancient:mali"
set.add name="ancient:region:africa:members" id="ancient:mali"
def "ancient:songhai" "Songhai Empire · Songhay (c.1430–1591 CE) — The largest state in African history."
ln ancient:songhai ancient:civilization sys:is_a
ln ancient:songhai ancient:region:africa sys:part_of
set.add name="ancient:all" id="ancient:songhai"
set.add name="ancient:region:africa:members" id="ancient:songhai"
def "ancient:benin" "Ife & Benin · Ilé-Ifẹ̀ · Edo (c.1000–1897 CE) — The Yoruba and Edo masters of brass and bronze."
ln ancient:benin ancient:civilization sys:is_a
ln ancient:benin ancient:region:africa sys:part_of
set.add name="ancient:all" id="ancient:benin"
set.add name="ancient:region:africa:members" id="ancient:benin"
def "ancient:great_zimbabwe" "Great Zimbabwe · Dzimba dza mabwe (c.1100–1450 CE) — A great dry-stone city ruling the southern gold trade."
ln ancient:great_zimbabwe ancient:civilization sys:is_a
ln ancient:great_zimbabwe ancient:region:africa sys:part_of
set.add name="ancient:all" id="ancient:great_zimbabwe"
set.add name="ancient:region:africa:members" id="ancient:great_zimbabwe"
def "ancient:swahili" "Swahili Coast · Waswahili (c.800–1500 CE) — Kilwa and the Indian-Ocean city-states."
ln ancient:swahili ancient:civilization sys:is_a
ln ancient:swahili ancient:region:africa sys:part_of
set.add name="ancient:all" id="ancient:swahili"
set.add name="ancient:region:africa:members" id="ancient:swahili"

# ══ 13 · Oceania & Polynesia ══
def "ancient:region:oceania" "Oceania & Polynesia — the voyagers of the great ocean. The longest human migration — the settlement of a third of the planet by open-ocean canoe."
ln ancient:region:oceania ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:oceania"
def "ancient:lapita" "Lapita · Lapita (c.1600–500 BCE) — The ancestral pottery-making voyagers of the Pacific."
ln ancient:lapita ancient:civilization sys:is_a
ln ancient:lapita ancient:region:oceania sys:part_of
set.add name="ancient:all" id="ancient:lapita"
set.add name="ancient:region:oceania:members" id="ancient:lapita"
def "ancient:polynesia" "Polynesian Voyagers · the great triangle (c.900–1300 CE) — The settlement of the Pacific from Hawaiʻi to Aotearoa."
ln ancient:polynesia ancient:civilization sys:is_a
ln ancient:polynesia ancient:region:oceania sys:part_of
set.add name="ancient:all" id="ancient:polynesia"
set.add name="ancient:region:oceania:members" id="ancient:polynesia"
def "ancient:rapa_nui" "Rapa Nui · Rapa Nui (c.1200–1700 CE) — Easter Island and its moai."
ln ancient:rapa_nui ancient:civilization sys:is_a
ln ancient:rapa_nui ancient:region:oceania sys:part_of
set.add name="ancient:all" id="ancient:rapa_nui"
set.add name="ancient:region:oceania:members" id="ancient:rapa_nui"
def "ancient:maori" "Māori · Māori (c.1300 CE–) — The settling of Aotearoa / New Zealand."
ln ancient:maori ancient:civilization sys:is_a
ln ancient:maori ancient:region:oceania sys:part_of
set.add name="ancient:all" id="ancient:maori"
set.add name="ancient:region:oceania:members" id="ancient:maori"
def "ancient:tonga" "Hawaiian & Tongan states · Hawaiʻi · Tonga (c.1000–1800 CE) — Island chiefdoms and the sea-empire of the Tuʻi Tonga."
ln ancient:tonga ancient:civilization sys:is_a
ln ancient:tonga ancient:region:oceania sys:part_of
set.add name="ancient:all" id="ancient:tonga"
set.add name="ancient:region:oceania:members" id="ancient:tonga"
def "ancient:aboriginal_australia" "Aboriginal Australia · the songlines (c.50000 BCE–) — The world’s oldest continuous living culture."
ln ancient:aboriginal_australia ancient:civilization sys:is_a
ln ancient:aboriginal_australia ancient:region:oceania sys:part_of
set.add name="ancient:all" id="ancient:aboriginal_australia"
set.add name="ancient:region:oceania:members" id="ancient:aboriginal_australia"

# ══ 14 · Southeast Asia ══
def "ancient:region:southeast_asia" "Southeast Asia — the temple-kingdoms & the sea-empires. The Hindu-Buddhist god-kings of the mainland and the maritime empires of the archipelago."
ln ancient:region:southeast_asia ancient:region sys:is_a
set.add name="ancient:regions" id="ancient:region:southeast_asia"
def "ancient:funan" "Funan · Funan (c.100–550 CE) — The first great state of the Mekong delta."
ln ancient:funan ancient:civilization sys:is_a
ln ancient:funan ancient:region:southeast_asia sys:part_of
set.add name="ancient:all" id="ancient:funan"
set.add name="ancient:region:southeast_asia:members" id="ancient:funan"
def "ancient:champa" "Champa · Campā (c.192–1832 CE) — The coastal Hindu-Cham kingdoms of central Vietnam."
ln ancient:champa ancient:civilization sys:is_a
ln ancient:champa ancient:region:southeast_asia sys:part_of
set.add name="ancient:all" id="ancient:champa"
set.add name="ancient:region:southeast_asia:members" id="ancient:champa"
def "ancient:srivijaya" "Srivijaya · Śrīvijaya (c.650–1288 CE) — The Sumatran empire that ruled the sea-lanes."
ln ancient:srivijaya ancient:civilization sys:is_a
ln ancient:srivijaya ancient:region:southeast_asia sys:part_of
set.add name="ancient:all" id="ancient:srivijaya"
set.add name="ancient:region:southeast_asia:members" id="ancient:srivijaya"
def "ancient:khmer" "Khmer Empire · Kambuja (c.802–1431 CE) — Angkor Wat and the Khmer god-kings."
ln ancient:khmer ancient:civilization sys:is_a
ln ancient:khmer ancient:region:southeast_asia sys:part_of
set.add name="ancient:all" id="ancient:khmer"
set.add name="ancient:region:southeast_asia:members" id="ancient:khmer"
def "ancient:pagan" "Pagan (Bagan) · Bagan (c.849–1297 CE) — The temple-plain of the first Burmese empire."
ln ancient:pagan ancient:civilization sys:is_a
ln ancient:pagan ancient:region:southeast_asia sys:part_of
set.add name="ancient:all" id="ancient:pagan"
set.add name="ancient:region:southeast_asia:members" id="ancient:pagan"
def "ancient:majapahit" "Majapahit · Majapahit (c.1293–1527 CE) — The Javanese thalassocracy of the archipelago."
ln ancient:majapahit ancient:civilization sys:is_a
ln ancient:majapahit ancient:region:southeast_asia sys:part_of
set.add name="ancient:all" id="ancient:majapahit"
set.add name="ancient:region:southeast_asia:members" id="ancient:majapahit"

# ── related cultures (curated bridges) ──
ln ancient:olmec ancient:maya thesaurus:related
ln ancient:toltec ancient:aztec thesaurus:related
ln ancient:wari ancient:inca thesaurus:related
ln ancient:tiwanaku ancient:inca thesaurus:related
ln ancient:minoan ancient:mycenae thesaurus:related
ln ancient:mycenae ancient:greece thesaurus:related
ln ancient:phoenicia ancient:carthage thesaurus:related
ln ancient:akkad ancient:sumer thesaurus:related
ln ancient:media ancient:achaemenid thesaurus:related
ln ancient:teotihuacan ancient:toltec thesaurus:related
ln ancient:chavin ancient:moche thesaurus:related
ln ancient:lapita ancient:polynesia thesaurus:related
ln ancient:polynesia ancient:rapa_nui thesaurus:related
