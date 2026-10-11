# Ancient Civilizations — GENERATED from app/archives/ancient/ (index.html REGIONS +
# atlas.json geography) by scripts/ancient_atlas_to_ak.py. Do not edit by hand; re-run it.
# Every civilization, region, source link, excavation site, modern-country membership and
# schematic extent the atlas carries, as first-class ancient:<…> atoms the GUI references.

def "ancient:civilization" "An ancient civilization — a culture, kingdom or empire of the old world, gathered by region in the Ancient Civilizations atlas."
al ancient:civilization ancient_civilization
def "ancient:region" "A region of the ancient world — a sphere of related ancient cultures on the atlas (the fertile crescent, the Andes, Oceania, and so on)."
al ancient:region ancient_region

def "ancient:region:mesopotamia" "Mesopotamia & the Near East — the fertile crescent. Between the Tigris and Euphrates, the world wrote its first words and raised its first cities."
al ancient:region:mesopotamia mesopotamia
ln ancient:region:mesopotamia ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:mesopotamia"
def "ancient:region:mesopotamia:pin" "33, 44 (WGS84) — atlas map pin of Mesopotamia & the Near East"
ln ancient:region:mesopotamia ancient:region:mesopotamia:pin geo:has_coordinate
def "ancient:sumer" "Sumer (endonym ki-en-gir, c.4500–1900 BCE) — The first cities — Uruk, Ur, Eridu — and cuneiform, the earliest writing."
al ancient:sumer sumer
ln ancient:sumer ancient:civilization sys:is_a
ln ancient:sumer ancient:region:mesopotamia ancient:in_region
set.add name="set:ancient:all" id="ancient:sumer"
set.add name="set:ancient:region:mesopotamia:members" id="ancient:sumer"
def "ancient:src:sumer:uruk" "Uruk — https://en.wikipedia.org/wiki/Uruk"
ln ancient:sumer ancient:src:sumer:uruk ancient:source
set.add name="set:ancient:sources" id="ancient:src:sumer:uruk"
def "ancient:src:sumer:ur" "Ur — https://en.wikipedia.org/wiki/Ur"
ln ancient:sumer ancient:src:sumer:ur ancient:source
set.add name="set:ancient:sources" id="ancient:src:sumer:ur"
def "ancient:src:sumer:eridu" "Eridu — https://en.wikipedia.org/wiki/Eridu"
ln ancient:sumer ancient:src:sumer:eridu ancient:source
set.add name="set:ancient:sources" id="ancient:src:sumer:eridu"
def "ancient:src:sumer:nippur" "Nippur — https://en.wikipedia.org/wiki/Nippur"
ln ancient:sumer ancient:src:sumer:nippur ancient:source
set.add name="set:ancient:sources" id="ancient:src:sumer:nippur"
def "ancient:site:sumer:uruk" "Uruk (31.3242, 45.6372) — the first city; cuneiform"
ln ancient:sumer ancient:site:sumer:uruk ancient:site
set.add name="set:ancient:sites" id="ancient:site:sumer:uruk"
def "ancient:site:sumer:ur" "Ur (30.9625, 46.1031) — ziggurat; the royal tombs"
ln ancient:sumer ancient:site:sumer:ur ancient:site
set.add name="set:ancient:sites" id="ancient:site:sumer:ur"
def "ancient:site:sumer:eridu" "Eridu (30.8158, 45.9961) — the earliest temple layers"
ln ancient:sumer ancient:site:sumer:eridu ancient:site
set.add name="set:ancient:sites" id="ancient:site:sumer:eridu"
def "ancient:site:sumer:nippur" "Nippur (32.1261, 45.2309) — sacred city of Enlil"
ln ancient:sumer ancient:site:sumer:nippur ancient:site
set.add name="set:ancient:sites" id="ancient:site:sumer:nippur"
ln ancient:sumer geo:country:IRQ ancient:spans_country
def "ancient:extent:sumer" "Southern Mesopotamia — the lower Tigris–Euphrates plain. Schematic core outline (approximate, not a surveyed border). polygon lon,lat: 44.0,33.3; 45.6,32.9; 47.2,31.3; 48.3,30.2; 46.4,29.9; 44.9,30.9; 44.1,32.1; 44.0,33.3"
ln ancient:sumer ancient:extent:sumer ancient:has_extent
set.add name="set:ancient:extents" id="ancient:extent:sumer"
def "ancient:akkad" "Akkadian Empire (endonym Akkad, c.2334–2154 BCE) — Sargon of Akkad forged history’s first empire."
al ancient:akkad akkadian_empire
ln ancient:akkad ancient:civilization sys:is_a
ln ancient:akkad ancient:region:mesopotamia ancient:in_region
set.add name="set:ancient:all" id="ancient:akkad"
set.add name="set:ancient:region:mesopotamia:members" id="ancient:akkad"
ln ancient:akkad geo:country:IRQ ancient:spans_country
ln ancient:akkad geo:country:SYR ancient:spans_country
def "ancient:babylon" "Babylonia (endonym Bābilim, c.1894–539 BCE) — Hammurabi’s law-code; Nebuchadnezzar’s hanging gardens."
al ancient:babylon babylonia
ln ancient:babylon ancient:civilization sys:is_a
ln ancient:babylon ancient:region:mesopotamia ancient:in_region
set.add name="set:ancient:all" id="ancient:babylon"
set.add name="set:ancient:region:mesopotamia:members" id="ancient:babylon"
def "ancient:src:babylon:babylon" "Babylon — https://en.wikipedia.org/wiki/Babylon"
ln ancient:babylon ancient:src:babylon:babylon ancient:source
set.add name="set:ancient:sources" id="ancient:src:babylon:babylon"
def "ancient:site:babylon:babylon" "Babylon (32.5425, 44.4211) — Hammurabi's capital; the Ishtar Gate"
ln ancient:babylon ancient:site:babylon:babylon ancient:site
set.add name="set:ancient:sites" id="ancient:site:babylon:babylon"
ln ancient:babylon geo:country:IRQ ancient:spans_country
def "ancient:oldmap:babylon:babylonian_map_of_the_world_imago_mundi" "Babylonian Map of the World (Imago Mundi) (c.700 BCE) — British Museum, BM 92687 | https://en.wikipedia.org/wiki/Babylonian_Map_of_the_World"
ln ancient:babylon ancient:oldmap:babylon:babylonian_map_of_the_world_imago_mundi ancient:has_oldmap
set.add name="set:ancient:oldmaps" id="ancient:oldmap:babylon:babylonian_map_of_the_world_imago_mundi"
def "ancient:assyria" "Assyria (endonym Aššur, c.2500–609 BCE) — Iron armies and the great library of Ashurbanipal at Nineveh."
al ancient:assyria assyria
ln ancient:assyria ancient:civilization sys:is_a
ln ancient:assyria ancient:region:mesopotamia ancient:in_region
set.add name="set:ancient:all" id="ancient:assyria"
set.add name="set:ancient:region:mesopotamia:members" id="ancient:assyria"
def "ancient:src:assyria:nineveh" "Nineveh — https://en.wikipedia.org/wiki/Nineveh"
ln ancient:assyria ancient:src:assyria:nineveh ancient:source
set.add name="set:ancient:sources" id="ancient:src:assyria:nineveh"
def "ancient:src:assyria:assur" "Assur — https://en.wikipedia.org/wiki/Assur"
ln ancient:assyria ancient:src:assyria:assur ancient:source
set.add name="set:ancient:sources" id="ancient:src:assyria:assur"
def "ancient:src:assyria:nimrud" "Nimrud — https://en.wikipedia.org/wiki/Nimrud"
ln ancient:assyria ancient:src:assyria:nimrud ancient:source
set.add name="set:ancient:sources" id="ancient:src:assyria:nimrud"
def "ancient:site:assyria:nineveh" "Nineveh (36.3594, 43.1528) — Ashurbanipal's great library"
ln ancient:assyria ancient:site:assyria:nineveh ancient:site
set.add name="set:ancient:sites" id="ancient:site:assyria:nineveh"
def "ancient:site:assyria:assur" "Assur (35.4567, 43.2625) — the first Assyrian capital"
ln ancient:assyria ancient:site:assyria:assur ancient:site
set.add name="set:ancient:sites" id="ancient:site:assyria:assur"
def "ancient:site:assyria:nimrud" "Nimrud (36.0992, 43.3275) — Kalhu, the palace-city"
ln ancient:assyria ancient:site:assyria:nimrud ancient:site
set.add name="set:ancient:sites" id="ancient:site:assyria:nimrud"
ln ancient:assyria geo:country:IRQ ancient:spans_country
ln ancient:assyria geo:country:SYR ancient:spans_country
ln ancient:assyria geo:country:TUR ancient:spans_country
def "ancient:elam" "Elam (endonym Haltamti, c.3200–539 BCE) — The kingdom of Susa, ancient rival of Sumer."
al ancient:elam elam
ln ancient:elam ancient:civilization sys:is_a
ln ancient:elam ancient:region:mesopotamia ancient:in_region
set.add name="set:ancient:all" id="ancient:elam"
set.add name="set:ancient:region:mesopotamia:members" id="ancient:elam"
def "ancient:src:elam:susa" "Susa — https://en.wikipedia.org/wiki/Susa"
ln ancient:elam ancient:src:elam:susa ancient:source
set.add name="set:ancient:sources" id="ancient:src:elam:susa"
def "ancient:site:elam:susa" "Susa (32.1892, 48.2578) — the ancient capital of Elam"
ln ancient:elam ancient:site:elam:susa ancient:site
set.add name="set:ancient:sites" id="ancient:site:elam:susa"
ln ancient:elam geo:country:IRN ancient:spans_country
def "ancient:hittite" "Hittites (endonym Hatti, c.1650–1180 BCE) — An Anatolian iron-age power ruled from Hattusa."
al ancient:hittite hittites
ln ancient:hittite ancient:civilization sys:is_a
ln ancient:hittite ancient:region:mesopotamia ancient:in_region
set.add name="set:ancient:all" id="ancient:hittite"
set.add name="set:ancient:region:mesopotamia:members" id="ancient:hittite"
def "ancient:src:hittite:hattusa" "Hattusa — https://en.wikipedia.org/wiki/Hattusa"
ln ancient:hittite ancient:src:hittite:hattusa ancient:source
set.add name="set:ancient:sources" id="ancient:src:hittite:hattusa"
def "ancient:site:hittite:hattusa" "Hattusa (40.0197, 34.6153) — the Hittite capital"
ln ancient:hittite ancient:site:hittite:hattusa ancient:site
set.add name="set:ancient:sites" id="ancient:site:hittite:hattusa"
ln ancient:hittite geo:country:TUR ancient:spans_country
ln ancient:hittite geo:country:SYR ancient:spans_country
def "ancient:phoenicia" "Phoenicia (endonym Kanaʿan, c.1500–300 BCE) — Sea-traders of Tyre and Sidon who gave the world its alphabet."
al ancient:phoenicia phoenicia
ln ancient:phoenicia ancient:civilization sys:is_a
ln ancient:phoenicia ancient:region:mesopotamia ancient:in_region
set.add name="set:ancient:all" id="ancient:phoenicia"
set.add name="set:ancient:region:mesopotamia:members" id="ancient:phoenicia"
def "ancient:src:phoenicia:tyre" "Tyre — https://en.wikipedia.org/wiki/Tyre,_Lebanon"
ln ancient:phoenicia ancient:src:phoenicia:tyre ancient:source
set.add name="set:ancient:sources" id="ancient:src:phoenicia:tyre"
def "ancient:src:phoenicia:byblos" "Byblos — https://en.wikipedia.org/wiki/Byblos"
ln ancient:phoenicia ancient:src:phoenicia:byblos ancient:source
set.add name="set:ancient:sources" id="ancient:src:phoenicia:byblos"
def "ancient:site:phoenicia:tyre" "Tyre (33.2708, 35.1961) — island city of purple dye"
ln ancient:phoenicia ancient:site:phoenicia:tyre ancient:site
set.add name="set:ancient:sites" id="ancient:site:phoenicia:tyre"
def "ancient:site:phoenicia:byblos" "Byblos (34.1236, 35.6519) — the oldest port; the alphabet"
ln ancient:phoenicia ancient:site:phoenicia:byblos ancient:site
set.add name="set:ancient:sites" id="ancient:site:phoenicia:byblos"
ln ancient:phoenicia geo:country:LBN ancient:spans_country
ln ancient:phoenicia geo:country:SYR ancient:spans_country
ln ancient:phoenicia geo:country:ISR ancient:spans_country

def "ancient:region:egypt" "Ancient Egypt & the Nile — the gift of the river. A civilization three thousand years long, threaded on a single river from the delta to Nubia."
al ancient:region:egypt egypt
ln ancient:region:egypt ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:egypt"
def "ancient:region:egypt:pin" "25, 31 (WGS84) — atlas map pin of Ancient Egypt & the Nile"
ln ancient:region:egypt ancient:region:egypt:pin geo:has_coordinate
def "ancient:egypt:old_kingdom" "Old Kingdom Egypt (endonym Kemet, c.2686–2181 BCE) — The age of the pyramids of Giza."
al ancient:egypt:old_kingdom old_kingdom_egypt
ln ancient:egypt:old_kingdom ancient:civilization sys:is_a
ln ancient:egypt:old_kingdom ancient:region:egypt ancient:in_region
set.add name="set:ancient:all" id="ancient:egypt:old_kingdom"
set.add name="set:ancient:region:egypt:members" id="ancient:egypt:old_kingdom"
def "ancient:src:egypt_old_kingdom:giza" "Giza — https://en.wikipedia.org/wiki/Giza_pyramid_complex"
ln ancient:egypt:old_kingdom ancient:src:egypt_old_kingdom:giza ancient:source
set.add name="set:ancient:sources" id="ancient:src:egypt_old_kingdom:giza"
def "ancient:src:egypt_old_kingdom:saqqara" "Saqqara — https://en.wikipedia.org/wiki/Saqqara"
ln ancient:egypt:old_kingdom ancient:src:egypt_old_kingdom:saqqara ancient:source
set.add name="set:ancient:sources" id="ancient:src:egypt_old_kingdom:saqqara"
def "ancient:src:egypt_old_kingdom:memphis" "Memphis — https://en.wikipedia.org/wiki/Memphis,_Egypt"
ln ancient:egypt:old_kingdom ancient:src:egypt_old_kingdom:memphis ancient:source
set.add name="set:ancient:sources" id="ancient:src:egypt_old_kingdom:memphis"
def "ancient:site:egypt_old_kingdom:giza" "Giza (29.9761, 31.1328) — the great pyramids"
ln ancient:egypt:old_kingdom ancient:site:egypt_old_kingdom:giza ancient:site
set.add name="set:ancient:sites" id="ancient:site:egypt_old_kingdom:giza"
def "ancient:site:egypt_old_kingdom:saqqara" "Saqqara (29.8711, 31.2164) — the Step Pyramid of Djoser"
ln ancient:egypt:old_kingdom ancient:site:egypt_old_kingdom:saqqara ancient:site
set.add name="set:ancient:sites" id="ancient:site:egypt_old_kingdom:saqqara"
def "ancient:site:egypt_old_kingdom:memphis" "Memphis (29.8494, 31.255) — the Old Kingdom capital"
ln ancient:egypt:old_kingdom ancient:site:egypt_old_kingdom:memphis ancient:site
set.add name="set:ancient:sites" id="ancient:site:egypt_old_kingdom:memphis"
ln ancient:egypt:old_kingdom geo:country:EGY ancient:spans_country
def "ancient:extent:egypt_old_kingdom" "The Nile valley and delta — delta to the first cataract. Schematic core outline (approximate, not a surveyed border). polygon lon,lat: 30.0,31.6; 32.2,31.4; 31.4,30.0; 31.0,27.5; 32.2,25.0; 32.9,24.0; 32.5,24.0; 31.6,25.2; 30.7,27.8; 30.4,30.1; 29.7,31.4; 30.0,31.6"
ln ancient:egypt:old_kingdom ancient:extent:egypt_old_kingdom ancient:has_extent
set.add name="set:ancient:extents" id="ancient:extent:egypt_old_kingdom"
def "ancient:egypt:new_kingdom" "New Kingdom Egypt (endonym Kemet, c.1550–1070 BCE) — Thebes, Karnak, and the great pharaohs — Hatshepsut, Ramesses."
al ancient:egypt:new_kingdom new_kingdom_egypt
ln ancient:egypt:new_kingdom ancient:civilization sys:is_a
ln ancient:egypt:new_kingdom ancient:region:egypt ancient:in_region
set.add name="set:ancient:all" id="ancient:egypt:new_kingdom"
set.add name="set:ancient:region:egypt:members" id="ancient:egypt:new_kingdom"
def "ancient:src:egypt_new_kingdom:thebes" "Thebes — https://en.wikipedia.org/wiki/Thebes,_Egypt"
ln ancient:egypt:new_kingdom ancient:src:egypt_new_kingdom:thebes ancient:source
set.add name="set:ancient:sources" id="ancient:src:egypt_new_kingdom:thebes"
def "ancient:src:egypt_new_kingdom:valley_of_the_kings" "Valley of the Kings — https://en.wikipedia.org/wiki/Valley_of_the_Kings"
ln ancient:egypt:new_kingdom ancient:src:egypt_new_kingdom:valley_of_the_kings ancient:source
set.add name="set:ancient:sources" id="ancient:src:egypt_new_kingdom:valley_of_the_kings"
def "ancient:site:egypt_new_kingdom:thebes" "Thebes (25.7206, 32.6103) — Karnak, Luxor, the royal capital"
ln ancient:egypt:new_kingdom ancient:site:egypt_new_kingdom:thebes ancient:site
set.add name="set:ancient:sites" id="ancient:site:egypt_new_kingdom:thebes"
def "ancient:site:egypt_new_kingdom:valley_of_the_kings" "Valley of the Kings (25.7404, 32.6013) — the royal rock-cut tombs"
ln ancient:egypt:new_kingdom ancient:site:egypt_new_kingdom:valley_of_the_kings ancient:site
set.add name="set:ancient:sites" id="ancient:site:egypt_new_kingdom:valley_of_the_kings"
ln ancient:egypt:new_kingdom geo:country:EGY ancient:spans_country
def "ancient:oldmap:egypt_new_kingdom:turin_papyrus_map" "Turin Papyrus Map (c.1150 BCE) — Museo Egizio, Turin | https://en.wikipedia.org/wiki/Turin_Papyrus_Map"
ln ancient:egypt:new_kingdom ancient:oldmap:egypt_new_kingdom:turin_papyrus_map ancient:has_oldmap
set.add name="set:ancient:oldmaps" id="ancient:oldmap:egypt_new_kingdom:turin_papyrus_map"
def "ancient:kush" "Kerma & Kush (endonym Nubia, c.2500–350 BCE) — Nubian kingdoms whose kings ruled Egypt as the 25th Dynasty."
al ancient:kush kerma_kush
ln ancient:kush ancient:civilization sys:is_a
ln ancient:kush ancient:region:egypt ancient:in_region
set.add name="set:ancient:all" id="ancient:kush"
set.add name="set:ancient:region:egypt:members" id="ancient:kush"
def "ancient:src:kush:kerma" "Kerma — https://en.wikipedia.org/wiki/Kerma"
ln ancient:kush ancient:src:kush:kerma ancient:source
set.add name="set:ancient:sources" id="ancient:src:kush:kerma"
def "ancient:site:kush:kerma" "Kerma (19.6008, 30.4097) — the earliest Kushite capital"
ln ancient:kush ancient:site:kush:kerma ancient:site
set.add name="set:ancient:sites" id="ancient:site:kush:kerma"
ln ancient:kush geo:country:SDN ancient:spans_country
def "ancient:meroe" "Meroë (endonym Kingdom of Meroë, c.800 BCE–350 CE) — Iron and steep pyramids on the upper Nile."
al ancient:meroe mero
ln ancient:meroe ancient:civilization sys:is_a
ln ancient:meroe ancient:region:egypt ancient:in_region
set.add name="set:ancient:all" id="ancient:meroe"
set.add name="set:ancient:region:egypt:members" id="ancient:meroe"
def "ancient:src:meroe:mero" "Meroë — https://en.wikipedia.org/wiki/Pyramids_of_Mero%C3%AB"
ln ancient:meroe ancient:src:meroe:mero ancient:source
set.add name="set:ancient:sources" id="ancient:src:meroe:mero"
def "ancient:site:meroe:mero" "Meroë (16.9383, 33.7492) — the pyramids of the Kushite kings"
ln ancient:meroe ancient:site:meroe:mero ancient:site
set.add name="set:ancient:sites" id="ancient:site:meroe:mero"
ln ancient:meroe geo:country:SDN ancient:spans_country

def "ancient:region:indus" "Indus & South Asia — the cities of the seven rivers. From grid-planned cities on the Indus to the first empires of the subcontinent."
al ancient:region:indus indus
ln ancient:region:indus ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:indus"
def "ancient:region:indus:pin" "26, 72 (WGS84) — atlas map pin of Indus & South Asia"
ln ancient:region:indus ancient:region:indus:pin geo:has_coordinate
def "ancient:indus" "Indus Valley (Harappan) (endonym Meluhha, c.3300–1300 BCE) — Mohenjo-daro and Harappa — plumbing, planning, an unread script."
al ancient:indus indus_valley_harappan
ln ancient:indus ancient:civilization sys:is_a
ln ancient:indus ancient:region:indus ancient:in_region
set.add name="set:ancient:all" id="ancient:indus"
set.add name="set:ancient:region:indus:members" id="ancient:indus"
def "ancient:src:indus:mohenjo_daro" "Mohenjo-daro — https://en.wikipedia.org/wiki/Mohenjo-daro"
ln ancient:indus ancient:src:indus:mohenjo_daro ancient:source
set.add name="set:ancient:sources" id="ancient:src:indus:mohenjo_daro"
def "ancient:src:indus:harappa" "Harappa — https://en.wikipedia.org/wiki/Harappa"
ln ancient:indus ancient:src:indus:harappa ancient:source
set.add name="set:ancient:sources" id="ancient:src:indus:harappa"
def "ancient:src:indus:dholavira" "Dholavira — https://en.wikipedia.org/wiki/Dholavira"
ln ancient:indus ancient:src:indus:dholavira ancient:source
set.add name="set:ancient:sources" id="ancient:src:indus:dholavira"
def "ancient:src:indus:lothal" "Lothal — https://en.wikipedia.org/wiki/Lothal"
ln ancient:indus ancient:src:indus:lothal ancient:source
set.add name="set:ancient:sources" id="ancient:src:indus:lothal"
def "ancient:site:indus:mohenjo_daro" "Mohenjo-daro (27.3292, 68.1389) — the great bath; grid streets"
ln ancient:indus ancient:site:indus:mohenjo_daro ancient:site
set.add name="set:ancient:sites" id="ancient:site:indus:mohenjo_daro"
def "ancient:site:indus:harappa" "Harappa (30.6289, 72.8639) — the type-site of the culture"
ln ancient:indus ancient:site:indus:harappa ancient:site
set.add name="set:ancient:sites" id="ancient:site:indus:harappa"
def "ancient:site:indus:dholavira" "Dholavira (23.8886, 70.2136) — reservoirs; a stone signboard"
ln ancient:indus ancient:site:indus:dholavira ancient:site
set.add name="set:ancient:sites" id="ancient:site:indus:dholavira"
def "ancient:site:indus:lothal" "Lothal (22.5227, 72.2488) — a tidal dockyard"
ln ancient:indus ancient:site:indus:lothal ancient:site
set.add name="set:ancient:sites" id="ancient:site:indus:lothal"
ln ancient:indus geo:country:PAK ancient:spans_country
ln ancient:indus geo:country:IND ancient:spans_country
def "ancient:extent:indus" "The Indus and Ghaggar–Hakra basins, reaching into Gujarat. Schematic core outline (approximate, not a surveyed border). polygon lon,lat: 73.5,31.5; 74.6,29.5; 73.2,26.8; 72.6,24.0; 72.6,22.2; 70.0,22.6; 68.0,25.0; 67.1,27.4; 68.6,29.1; 70.6,30.6; 73.5,31.5"
ln ancient:indus ancient:extent:indus ancient:has_extent
set.add name="set:ancient:extents" id="ancient:extent:indus"
def "ancient:vedic" "Vedic Civilization (endonym Sapta Sindhu, c.1500–500 BCE) — The Vedas and the roots of Indian thought."
al ancient:vedic vedic_civilization
ln ancient:vedic ancient:civilization sys:is_a
ln ancient:vedic ancient:region:indus ancient:in_region
set.add name="set:ancient:all" id="ancient:vedic"
set.add name="set:ancient:region:indus:members" id="ancient:vedic"
def "ancient:src:vedic:hastinapur" "Hastinapur — https://en.wikipedia.org/wiki/Hastinapur"
ln ancient:vedic ancient:src:vedic:hastinapur ancient:source
set.add name="set:ancient:sources" id="ancient:src:vedic:hastinapur"
def "ancient:site:vedic:hastinapur" "Hastinapur (29.17, 78.02) — Painted Grey Ware; the Mahabharata city"
ln ancient:vedic ancient:site:vedic:hastinapur ancient:site
set.add name="set:ancient:sites" id="ancient:site:vedic:hastinapur"
ln ancient:vedic geo:country:IND ancient:spans_country
ln ancient:vedic geo:country:PAK ancient:spans_country
def "ancient:maurya" "Maurya Empire (endonym Maurya, c.322–185 BCE) — Ashoka the Great; the first empire over most of India."
al ancient:maurya maurya_empire
ln ancient:maurya ancient:civilization sys:is_a
ln ancient:maurya ancient:region:indus ancient:in_region
set.add name="set:ancient:all" id="ancient:maurya"
set.add name="set:ancient:region:indus:members" id="ancient:maurya"
def "ancient:src:maurya:pataliputra" "Pataliputra — https://en.wikipedia.org/wiki/Pataliputra"
ln ancient:maurya ancient:src:maurya:pataliputra ancient:source
set.add name="set:ancient:sources" id="ancient:src:maurya:pataliputra"
def "ancient:site:maurya:pataliputra" "Pataliputra (25.611, 85.144) — the Mauryan capital (Patna)"
ln ancient:maurya ancient:site:maurya:pataliputra ancient:site
set.add name="set:ancient:sites" id="ancient:site:maurya:pataliputra"
ln ancient:maurya geo:country:IND ancient:spans_country
ln ancient:maurya geo:country:PAK ancient:spans_country
ln ancient:maurya geo:country:BGD ancient:spans_country
ln ancient:maurya geo:country:NPL ancient:spans_country
ln ancient:maurya geo:country:AFG ancient:spans_country
def "ancient:gupta" "Gupta Empire (endonym Gupta, c.320–550 CE) — A golden age — the decimal zero, astronomy, Sanskrit arts."
al ancient:gupta gupta_empire
ln ancient:gupta ancient:civilization sys:is_a
ln ancient:gupta ancient:region:indus ancient:in_region
set.add name="set:ancient:all" id="ancient:gupta"
set.add name="set:ancient:region:indus:members" id="ancient:gupta"
def "ancient:src:gupta:udayagiri_caves" "Udayagiri Caves — https://en.wikipedia.org/wiki/Udayagiri_Caves"
ln ancient:gupta ancient:src:gupta:udayagiri_caves ancient:source
set.add name="set:ancient:sources" id="ancient:src:gupta:udayagiri_caves"
def "ancient:site:gupta:udayagiri_caves" "Udayagiri Caves (23.5364, 77.7722) — Gupta rock-cut Hindu shrines"
ln ancient:gupta ancient:site:gupta:udayagiri_caves ancient:site
set.add name="set:ancient:sites" id="ancient:site:gupta:udayagiri_caves"
ln ancient:gupta geo:country:IND ancient:spans_country
ln ancient:gupta geo:country:BGD ancient:spans_country
ln ancient:gupta geo:country:PAK ancient:spans_country

def "ancient:region:china" "Ancient China & East Asia — the middle kingdom & its neighbours. Oracle bones to the first empire, and the island and peninsula cultures that grew alongside."
al ancient:region:china china
ln ancient:region:china ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:china"
def "ancient:region:china:pin" "34, 110 (WGS84) — atlas map pin of Ancient China & East Asia"
ln ancient:region:china ancient:region:china:pin geo:has_coordinate
def "ancient:shang" "Shang Dynasty (endonym 商, c.1600–1046 BCE) — Bronze, oracle bones, the first attested Chinese state."
al ancient:shang shang_dynasty
ln ancient:shang ancient:civilization sys:is_a
ln ancient:shang ancient:region:china ancient:in_region
set.add name="set:ancient:all" id="ancient:shang"
set.add name="set:ancient:region:china:members" id="ancient:shang"
def "ancient:src:shang:yinxu_anyang" "Yinxu (Anyang) — https://en.wikipedia.org/wiki/Yinxu"
ln ancient:shang ancient:src:shang:yinxu_anyang ancient:source
set.add name="set:ancient:sources" id="ancient:src:shang:yinxu_anyang"
def "ancient:site:shang:yinxu_anyang" "Yinxu (Anyang) (36.1225, 114.3186) — oracle bones; the Shang capital"
ln ancient:shang ancient:site:shang:yinxu_anyang ancient:site
set.add name="set:ancient:sites" id="ancient:site:shang:yinxu_anyang"
ln ancient:shang geo:country:CHN ancient:spans_country
def "ancient:zhou" "Zhou Dynasty (endonym 周, 1046–256 BCE) — The Mandate of Heaven; Confucius and Laozi."
al ancient:zhou zhou_dynasty
ln ancient:zhou ancient:civilization sys:is_a
ln ancient:zhou ancient:region:china ancient:in_region
set.add name="set:ancient:all" id="ancient:zhou"
set.add name="set:ancient:region:china:members" id="ancient:zhou"
def "ancient:src:zhou:haojing_fenghao" "Haojing (Fenghao) — https://en.wikipedia.org/wiki/Fenghao"
ln ancient:zhou ancient:src:zhou:haojing_fenghao ancient:source
set.add name="set:ancient:sources" id="ancient:src:zhou:haojing_fenghao"
def "ancient:site:zhou:haojing_fenghao" "Haojing (Fenghao) (34.2167, 108.7167) — the Western Zhou capital near Xi'an"
ln ancient:zhou ancient:site:zhou:haojing_fenghao ancient:site
set.add name="set:ancient:sites" id="ancient:site:zhou:haojing_fenghao"
ln ancient:zhou geo:country:CHN ancient:spans_country
def "ancient:qin" "Qin Dynasty (endonym 秦, 221–206 BCE) — The first unified empire; the Terracotta Army; the Wall begun."
al ancient:qin qin_dynasty
ln ancient:qin ancient:civilization sys:is_a
ln ancient:qin ancient:region:china ancient:in_region
set.add name="set:ancient:all" id="ancient:qin"
set.add name="set:ancient:region:china:members" id="ancient:qin"
def "ancient:src:qin:xianyang" "Xianyang — https://en.wikipedia.org/wiki/Xianyang_(Qin)"
ln ancient:qin ancient:src:qin:xianyang ancient:source
set.add name="set:ancient:sources" id="ancient:src:qin:xianyang"
def "ancient:site:qin:xianyang" "Xianyang (34.4139, 108.8578) — the Qin capital; the Terracotta Army nearby"
ln ancient:qin ancient:site:qin:xianyang ancient:site
set.add name="set:ancient:sites" id="ancient:site:qin:xianyang"
ln ancient:qin geo:country:CHN ancient:spans_country
def "ancient:han" "Han Dynasty (endonym 漢, 206 BCE–220 CE) — The Silk Road, paper, and the classic model of empire."
al ancient:han han_dynasty
ln ancient:han ancient:civilization sys:is_a
ln ancient:han ancient:region:china ancient:in_region
set.add name="set:ancient:all" id="ancient:han"
set.add name="set:ancient:region:china:members" id="ancient:han"
def "ancient:src:han:chang_an" "Chang'an — https://en.wikipedia.org/wiki/Chang%27an"
ln ancient:han ancient:src:han:chang_an ancient:source
set.add name="set:ancient:sources" id="ancient:src:han:chang_an"
def "ancient:site:han:chang_an" "Chang'an (34.3044, 108.8572) — the great Han capital (Xi'an)"
ln ancient:han ancient:site:han:chang_an ancient:site
set.add name="set:ancient:sites" id="ancient:site:han:chang_an"
ln ancient:han geo:country:CHN ancient:spans_country
def "ancient:oldmap:han:mawangdui_silk_maps" "Mawangdui silk maps (168 BCE) — Hunan Museum, Changsha | https://en.wikipedia.org/wiki/Mawangdui"
ln ancient:han ancient:oldmap:han:mawangdui_silk_maps ancient:has_oldmap
set.add name="set:ancient:oldmaps" id="ancient:oldmap:han:mawangdui_silk_maps"
def "ancient:gojoseon" "Gojoseon (endonym 古朝鮮, c.2000?–108 BCE) — The first kingdom of Korea."
al ancient:gojoseon gojoseon
ln ancient:gojoseon ancient:civilization sys:is_a
ln ancient:gojoseon ancient:region:china ancient:in_region
set.add name="set:ancient:all" id="ancient:gojoseon"
set.add name="set:ancient:region:china:members" id="ancient:gojoseon"
def "ancient:src:gojoseon:wanggeom_seong" "Wanggeom-seong — https://en.wikipedia.org/wiki/Wanggeom-seong"
ln ancient:gojoseon ancient:src:gojoseon:wanggeom_seong ancient:source
set.add name="set:ancient:sources" id="ancient:src:gojoseon:wanggeom_seong"
def "ancient:site:gojoseon:wanggeom_seong" "Wanggeom-seong (39.0167, 125.7475) — the reputed capital (near Pyongyang; disputed)"
ln ancient:gojoseon ancient:site:gojoseon:wanggeom_seong ancient:site
set.add name="set:ancient:sites" id="ancient:site:gojoseon:wanggeom_seong"
ln ancient:gojoseon geo:country:PRK ancient:spans_country
ln ancient:gojoseon geo:country:KOR ancient:spans_country
ln ancient:gojoseon geo:country:CHN ancient:spans_country
def "ancient:yayoi" "Jōmon & Yayoi (endonym 縄文・弥生, c.14000 BCE–300 CE) — Japan’s cord-marked potters, then wet-rice and metal."
al ancient:yayoi j_mon_yayoi
ln ancient:yayoi ancient:civilization sys:is_a
ln ancient:yayoi ancient:region:china ancient:in_region
set.add name="set:ancient:all" id="ancient:yayoi"
set.add name="set:ancient:region:china:members" id="ancient:yayoi"
def "ancient:src:yayoi:yoshinogari" "Yoshinogari — https://en.wikipedia.org/wiki/Yoshinogari_site"
ln ancient:yayoi ancient:src:yayoi:yoshinogari ancient:source
set.add name="set:ancient:sources" id="ancient:src:yayoi:yoshinogari"
def "ancient:site:yayoi:yoshinogari" "Yoshinogari (33.3236, 130.3907) — a great moated Yayoi settlement"
ln ancient:yayoi ancient:site:yayoi:yoshinogari ancient:site
set.add name="set:ancient:sites" id="ancient:site:yayoi:yoshinogari"
ln ancient:yayoi geo:country:JPN ancient:spans_country

def "ancient:region:aegean" "The Aegean & Mediterranean — the wine-dark sea. Palace-kingdoms of Crete, the world of Homer, and the classical powers that shaped the West."
al ancient:region:aegean aegean
ln ancient:region:aegean ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:aegean"
def "ancient:region:aegean:pin" "39, 20 (WGS84) — atlas map pin of The Aegean & Mediterranean"
ln ancient:region:aegean ancient:region:aegean:pin geo:has_coordinate
def "ancient:minoan" "Minoan Crete (endonym Kaptara, c.3000–1100 BCE) — Knossos and Linear A — Europe’s first civilization."
al ancient:minoan minoan_crete
ln ancient:minoan ancient:civilization sys:is_a
ln ancient:minoan ancient:region:aegean ancient:in_region
set.add name="set:ancient:all" id="ancient:minoan"
set.add name="set:ancient:region:aegean:members" id="ancient:minoan"
def "ancient:src:minoan:knossos" "Knossos — https://en.wikipedia.org/wiki/Knossos"
ln ancient:minoan ancient:src:minoan:knossos ancient:source
set.add name="set:ancient:sources" id="ancient:src:minoan:knossos"
def "ancient:site:minoan:knossos" "Knossos (35.2981, 25.1631) — the palace of the labyrinth"
ln ancient:minoan ancient:site:minoan:knossos ancient:site
set.add name="set:ancient:sites" id="ancient:site:minoan:knossos"
ln ancient:minoan geo:country:GRC ancient:spans_country
def "ancient:mycenae" "Mycenaean Greece (endonym Aḫḫiyawa, c.1600–1100 BCE) — Linear B and the citadels of the Homeric age."
al ancient:mycenae mycenaean_greece
ln ancient:mycenae ancient:civilization sys:is_a
ln ancient:mycenae ancient:region:aegean ancient:in_region
set.add name="set:ancient:all" id="ancient:mycenae"
set.add name="set:ancient:region:aegean:members" id="ancient:mycenae"
def "ancient:src:mycenae:mycenae" "Mycenae — https://en.wikipedia.org/wiki/Mycenae"
ln ancient:mycenae ancient:src:mycenae:mycenae ancient:source
set.add name="set:ancient:sources" id="ancient:src:mycenae:mycenae"
def "ancient:site:mycenae:mycenae" "Mycenae (37.7303, 22.7575) — the Lion Gate; the shaft graves"
ln ancient:mycenae ancient:site:mycenae:mycenae ancient:site
set.add name="set:ancient:sites" id="ancient:site:mycenae:mycenae"
ln ancient:mycenae geo:country:GRC ancient:spans_country
def "ancient:greece" "Classical Greece (endonym Hellas, c.800–323 BCE) — The polis — democracy, philosophy, drama, geometry."
al ancient:greece classical_greece
ln ancient:greece ancient:civilization sys:is_a
ln ancient:greece ancient:region:aegean ancient:in_region
set.add name="set:ancient:all" id="ancient:greece"
set.add name="set:ancient:region:aegean:members" id="ancient:greece"
def "ancient:src:greece:athens" "Athens — https://en.wikipedia.org/wiki/Acropolis_of_Athens"
ln ancient:greece ancient:src:greece:athens ancient:source
set.add name="set:ancient:sources" id="ancient:src:greece:athens"
def "ancient:src:greece:delphi" "Delphi — https://en.wikipedia.org/wiki/Delphi"
ln ancient:greece ancient:src:greece:delphi ancient:source
set.add name="set:ancient:sources" id="ancient:src:greece:delphi"
def "ancient:site:greece:athens" "Athens (37.9717, 23.7261) — the Acropolis; the Parthenon"
ln ancient:greece ancient:site:greece:athens ancient:site
set.add name="set:ancient:sites" id="ancient:site:greece:athens"
def "ancient:site:greece:delphi" "Delphi (38.4823, 22.5013) — the oracle of Apollo"
ln ancient:greece ancient:site:greece:delphi ancient:site
set.add name="set:ancient:sites" id="ancient:site:greece:delphi"
ln ancient:greece geo:country:GRC ancient:spans_country
ln ancient:greece geo:country:TUR ancient:spans_country
def "ancient:etruscan" "Etruscans (endonym Rasenna, c.900–100 BCE) — The tomb-painters of pre-Roman Italy."
al ancient:etruscan etruscans
ln ancient:etruscan ancient:civilization sys:is_a
ln ancient:etruscan ancient:region:aegean ancient:in_region
set.add name="set:ancient:all" id="ancient:etruscan"
set.add name="set:ancient:region:aegean:members" id="ancient:etruscan"
def "ancient:src:etruscan:cerveteri" "Cerveteri — https://en.wikipedia.org/wiki/Cerveteri"
ln ancient:etruscan ancient:src:etruscan:cerveteri ancient:source
set.add name="set:ancient:sources" id="ancient:src:etruscan:cerveteri"
def "ancient:site:etruscan:cerveteri" "Cerveteri (42.0055, 12.1009) — the Banditaccia necropolis"
ln ancient:etruscan ancient:site:etruscan:cerveteri ancient:site
set.add name="set:ancient:sites" id="ancient:site:etruscan:cerveteri"
ln ancient:etruscan geo:country:ITA ancient:spans_country
def "ancient:rome" "Ancient Rome (endonym Roma, 753 BCE–476 CE) — Republic to empire — law, roads, concrete, an inherited world."
al ancient:rome ancient_rome
ln ancient:rome ancient:civilization sys:is_a
ln ancient:rome ancient:region:aegean ancient:in_region
set.add name="set:ancient:all" id="ancient:rome"
set.add name="set:ancient:region:aegean:members" id="ancient:rome"
def "ancient:src:rome:rome" "Rome — https://en.wikipedia.org/wiki/Roman_Forum"
ln ancient:rome ancient:src:rome:rome ancient:source
set.add name="set:ancient:sources" id="ancient:src:rome:rome"
def "ancient:site:rome:rome" "Rome (41.8925, 12.4853) — the Forum, the Colosseum, the capital"
ln ancient:rome ancient:site:rome:rome ancient:site
set.add name="set:ancient:sites" id="ancient:site:rome:rome"
ln ancient:rome geo:country:ITA ancient:spans_country
def "ancient:oldmap:rome:tabula_peutingeriana" "Tabula Peutingeriana (Roman itinerarium; surviving copy c.1200) — Österreichische Nationalbibliothek, Vienna | https://en.wikipedia.org/wiki/Tabula_Peutingeriana"
ln ancient:rome ancient:oldmap:rome:tabula_peutingeriana ancient:has_oldmap
set.add name="set:ancient:oldmaps" id="ancient:oldmap:rome:tabula_peutingeriana"
def "ancient:oldmap:rome:forma_urbis_romae_severan_marble_plan" "Forma Urbis Romae (Severan Marble Plan) (203–211 CE) — Rome | https://en.wikipedia.org/wiki/Forma_Urbis_Romae"
ln ancient:rome ancient:oldmap:rome:forma_urbis_romae_severan_marble_plan ancient:has_oldmap
set.add name="set:ancient:oldmaps" id="ancient:oldmap:rome:forma_urbis_romae_severan_marble_plan"
def "ancient:carthage" "Carthage (endonym Qart-ḥadašt, c.814–146 BCE) — A Phoenician sea-empire; Hannibal crossed the Alps."
al ancient:carthage carthage
ln ancient:carthage ancient:civilization sys:is_a
ln ancient:carthage ancient:region:aegean ancient:in_region
set.add name="set:ancient:all" id="ancient:carthage"
set.add name="set:ancient:region:aegean:members" id="ancient:carthage"
def "ancient:src:carthage:carthage" "Carthage — https://en.wikipedia.org/wiki/Carthage"
ln ancient:carthage ancient:src:carthage:carthage ancient:source
set.add name="set:ancient:sources" id="ancient:src:carthage:carthage"
def "ancient:site:carthage:carthage" "Carthage (36.8529, 10.3217) — the great Punic sea-power"
ln ancient:carthage ancient:site:carthage:carthage ancient:site
set.add name="set:ancient:sites" id="ancient:site:carthage:carthage"
ln ancient:carthage geo:country:TUN ancient:spans_country

def "ancient:region:persia" "Persia & the Iranian Plateau — the kings of kings. From Cyrus to the Sasanians — a millennium of empires bridging East and West."
al ancient:region:persia persia
ln ancient:region:persia ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:persia"
def "ancient:region:persia:pin" "32, 53 (WGS84) — atlas map pin of Persia & the Iranian Plateau"
ln ancient:region:persia ancient:region:persia:pin geo:has_coordinate
def "ancient:achaemenid" "Achaemenid Persia (endonym Pārsa, 550–330 BCE) — Cyrus and Darius; Persepolis; the largest empire of its age."
al ancient:achaemenid achaemenid_persia
ln ancient:achaemenid ancient:civilization sys:is_a
ln ancient:achaemenid ancient:region:persia ancient:in_region
set.add name="set:ancient:all" id="ancient:achaemenid"
set.add name="set:ancient:region:persia:members" id="ancient:achaemenid"
def "ancient:src:achaemenid:persepolis" "Persepolis — https://en.wikipedia.org/wiki/Persepolis"
ln ancient:achaemenid ancient:src:achaemenid:persepolis ancient:source
set.add name="set:ancient:sources" id="ancient:src:achaemenid:persepolis"
def "ancient:src:achaemenid:pasargadae" "Pasargadae — https://en.wikipedia.org/wiki/Pasargadae"
ln ancient:achaemenid ancient:src:achaemenid:pasargadae ancient:source
set.add name="set:ancient:sources" id="ancient:src:achaemenid:pasargadae"
def "ancient:site:achaemenid:persepolis" "Persepolis (29.9355, 52.8916) — the ceremonial capital"
ln ancient:achaemenid ancient:site:achaemenid:persepolis ancient:site
set.add name="set:ancient:sites" id="ancient:site:achaemenid:persepolis"
def "ancient:site:achaemenid:pasargadae" "Pasargadae (30.1939, 53.1672) — Cyrus's capital and tomb"
ln ancient:achaemenid ancient:site:achaemenid:pasargadae ancient:site
set.add name="set:ancient:sites" id="ancient:site:achaemenid:pasargadae"
ln ancient:achaemenid geo:country:IRN ancient:spans_country
def "ancient:parthia" "Parthian Empire (endonym Ashkâniân, 247 BCE–224 CE) — Rome’s eastern rival; masters of the horse-archer."
al ancient:parthia parthian_empire
ln ancient:parthia ancient:civilization sys:is_a
ln ancient:parthia ancient:region:persia ancient:in_region
set.add name="set:ancient:all" id="ancient:parthia"
set.add name="set:ancient:region:persia:members" id="ancient:parthia"
def "ancient:src:parthia:ctesiphon" "Ctesiphon — https://en.wikipedia.org/wiki/Ctesiphon"
ln ancient:parthia ancient:src:parthia:ctesiphon ancient:source
set.add name="set:ancient:sources" id="ancient:src:parthia:ctesiphon"
def "ancient:site:parthia:ctesiphon" "Ctesiphon (33.0936, 44.5808) — the great arched palace"
ln ancient:parthia ancient:site:parthia:ctesiphon ancient:site
set.add name="set:ancient:sites" id="ancient:site:parthia:ctesiphon"
ln ancient:parthia geo:country:IRN ancient:spans_country
ln ancient:parthia geo:country:IRQ ancient:spans_country
ln ancient:parthia geo:country:TKM ancient:spans_country
def "ancient:sasanian" "Sasanian Empire (endonym Ērānshahr, 224–651 CE) — The last pre-Islamic Persian empire; Zoroastrian high culture."
al ancient:sasanian sasanian_empire
ln ancient:sasanian ancient:civilization sys:is_a
ln ancient:sasanian ancient:region:persia ancient:in_region
set.add name="set:ancient:all" id="ancient:sasanian"
set.add name="set:ancient:region:persia:members" id="ancient:sasanian"
def "ancient:src:sasanian:firuzabad_gor" "Firuzabad (Gor) — https://en.wikipedia.org/wiki/Palace_of_Ardashir"
ln ancient:sasanian ancient:src:sasanian:firuzabad_gor ancient:source
set.add name="set:ancient:sources" id="ancient:src:sasanian:firuzabad_gor"
def "ancient:site:sasanian:firuzabad_gor" "Firuzabad (Gor) (28.8529, 52.5327) — Ardashir's round city and palace"
ln ancient:sasanian ancient:site:sasanian:firuzabad_gor ancient:site
set.add name="set:ancient:sites" id="ancient:site:sasanian:firuzabad_gor"
ln ancient:sasanian geo:country:IRN ancient:spans_country
ln ancient:sasanian geo:country:IRQ ancient:spans_country
def "ancient:media" "Median Empire (endonym Māda, c.678–550 BCE) — The first Iranian empire, overthrown by Cyrus."
al ancient:media median_empire
ln ancient:media ancient:civilization sys:is_a
ln ancient:media ancient:region:persia ancient:in_region
set.add name="set:ancient:all" id="ancient:media"
set.add name="set:ancient:region:persia:members" id="ancient:media"
def "ancient:src:media:ecbatana" "Ecbatana — https://en.wikipedia.org/wiki/Ecbatana"
ln ancient:media ancient:src:media:ecbatana ancient:source
set.add name="set:ancient:sources" id="ancient:src:media:ecbatana"
def "ancient:site:media:ecbatana" "Ecbatana (34.8064, 48.5161) — the Median capital (Hamadan)"
ln ancient:media ancient:site:media:ecbatana ancient:site
set.add name="set:ancient:sites" id="ancient:site:media:ecbatana"
ln ancient:media geo:country:IRN ancient:spans_country

def "ancient:region:steppe" "The Steppe & Central Asia — the sea of grass. Horse-lords and Silk-Road cities across the great grasslands between the settled empires."
al ancient:region:steppe steppe
ln ancient:region:steppe ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:steppe"
def "ancient:region:steppe:pin" "47, 64 (WGS84) — atlas map pin of The Steppe & Central Asia"
ln ancient:region:steppe ancient:region:steppe:pin geo:has_coordinate
def "ancient:scythian" "Scythians (endonym Skuδa, c.900–200 BCE) — Nomad horsemen famous for their golden animal art."
al ancient:scythian scythians
ln ancient:scythian ancient:civilization sys:is_a
ln ancient:scythian ancient:region:steppe ancient:in_region
set.add name="set:ancient:all" id="ancient:scythian"
set.add name="set:ancient:region:steppe:members" id="ancient:scythian"
def "ancient:src:scythian:chertomlyk" "Chertomlyk — https://www.megalithic.co.uk/article.php?sid=56468"
ln ancient:scythian ancient:src:scythian:chertomlyk ancient:source
set.add name="set:ancient:sources" id="ancient:src:scythian:chertomlyk"
def "ancient:site:scythian:chertomlyk" "Chertomlyk (47.7176, 34.2993) — a royal Scythian kurgan"
ln ancient:scythian ancient:site:scythian:chertomlyk ancient:site
set.add name="set:ancient:sites" id="ancient:site:scythian:chertomlyk"
ln ancient:scythian geo:country:UKR ancient:spans_country
ln ancient:scythian geo:country:RUS ancient:spans_country
ln ancient:scythian geo:country:KAZ ancient:spans_country
def "ancient:xiongnu" "Xiongnu (endonym 匈奴, c.209 BCE–100 CE) — The steppe confederation the Han built the Wall against."
al ancient:xiongnu xiongnu
ln ancient:xiongnu ancient:civilization sys:is_a
ln ancient:xiongnu ancient:region:steppe ancient:in_region
set.add name="set:ancient:all" id="ancient:xiongnu"
set.add name="set:ancient:region:steppe:members" id="ancient:xiongnu"
def "ancient:src:xiongnu:noin_ula" "Noin-Ula — https://en.wikipedia.org/wiki/Noin-Ula_burial_site"
ln ancient:xiongnu ancient:src:xiongnu:noin_ula ancient:source
set.add name="set:ancient:sources" id="ancient:src:xiongnu:noin_ula"
def "ancient:site:xiongnu:noin_ula" "Noin-Ula (48.3862, 106.755) — royal Xiongnu burial mounds"
ln ancient:xiongnu ancient:site:xiongnu:noin_ula ancient:site
set.add name="set:ancient:sites" id="ancient:site:xiongnu:noin_ula"
ln ancient:xiongnu geo:country:MNG ancient:spans_country
ln ancient:xiongnu geo:country:CHN ancient:spans_country
def "ancient:sogdia" "Sogdia & Bactria (endonym Suγδ, c.600 BCE–800 CE) — The Oxus cities and the merchants of the Silk Road."
al ancient:sogdia sogdia_bactria
ln ancient:sogdia ancient:civilization sys:is_a
ln ancient:sogdia ancient:region:steppe ancient:in_region
set.add name="set:ancient:all" id="ancient:sogdia"
set.add name="set:ancient:region:steppe:members" id="ancient:sogdia"
def "ancient:src:sogdia:samarkand_afrasiab" "Samarkand (Afrasiab) — https://en.wikipedia.org/wiki/Afrasiyab_(Samarkand)"
ln ancient:sogdia ancient:src:sogdia:samarkand_afrasiab ancient:source
set.add name="set:ancient:sources" id="ancient:src:sogdia:samarkand_afrasiab"
def "ancient:site:sogdia:samarkand_afrasiab" "Samarkand (Afrasiab) (39.6714, 66.9878) — the Sogdian merchant city"
ln ancient:sogdia ancient:site:sogdia:samarkand_afrasiab ancient:site
set.add name="set:ancient:sites" id="ancient:site:sogdia:samarkand_afrasiab"
ln ancient:sogdia geo:country:UZB ancient:spans_country
ln ancient:sogdia geo:country:TJK ancient:spans_country
def "ancient:kushan" "Kushan Empire (endonym Kushan, c.30–375 CE) — Gandhara and the Greco-Buddhist fusion of art."
al ancient:kushan kushan_empire
ln ancient:kushan ancient:civilization sys:is_a
ln ancient:kushan ancient:region:steppe ancient:in_region
set.add name="set:ancient:all" id="ancient:kushan"
set.add name="set:ancient:region:steppe:members" id="ancient:kushan"
def "ancient:src:kushan:begram" "Begram — https://en.wikipedia.org/wiki/Bagram"
ln ancient:kushan ancient:src:kushan:begram ancient:source
set.add name="set:ancient:sources" id="ancient:src:kushan:begram"
def "ancient:site:kushan:begram" "Begram (34.9403, 69.255) — the Kushan royal treasure"
ln ancient:kushan ancient:site:kushan:begram ancient:site
set.add name="set:ancient:sites" id="ancient:site:kushan:begram"
ln ancient:kushan geo:country:AFG ancient:spans_country
ln ancient:kushan geo:country:PAK ancient:spans_country
ln ancient:kushan geo:country:IND ancient:spans_country
ln ancient:kushan geo:country:TJK ancient:spans_country
ln ancient:kushan geo:country:UZB ancient:spans_country

def "ancient:region:europe" "Ancient Europe — beyond the Mediterranean. The iron-age peoples of temperate Europe and the seafarers of the North."
al ancient:region:europe europe
ln ancient:region:europe ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:europe"
def "ancient:region:europe:pin" "50, 9 (WGS84) — atlas map pin of Ancient Europe"
ln ancient:region:europe ancient:region:europe:pin geo:has_coordinate
def "ancient:celt" "Celts (endonym Keltoi, c.1200 BCE–50 CE) — Hallstatt and La Tène — Gaul, Britain, Iberia, Galatia."
al ancient:celt celts
ln ancient:celt ancient:civilization sys:is_a
ln ancient:celt ancient:region:europe ancient:in_region
set.add name="set:ancient:all" id="ancient:celt"
set.add name="set:ancient:region:europe:members" id="ancient:celt"
def "ancient:src:celt:hallstatt" "Hallstatt — https://en.wikipedia.org/wiki/Hallstatt"
ln ancient:celt ancient:src:celt:hallstatt ancient:source
set.add name="set:ancient:sources" id="ancient:src:celt:hallstatt"
def "ancient:site:celt:hallstatt" "Hallstatt (47.5635, 13.6367) — the salt-mine culture"
ln ancient:celt ancient:site:celt:hallstatt ancient:site
set.add name="set:ancient:sites" id="ancient:site:celt:hallstatt"
ln ancient:celt geo:country:FRA ancient:spans_country
ln ancient:celt geo:country:GBR ancient:spans_country
ln ancient:celt geo:country:IRL ancient:spans_country
ln ancient:celt geo:country:DEU ancient:spans_country
def "ancient:thracian" "Thracians (endonym Thrāix, c.1500–300 BCE) — Balkan warrior-culture famed for gold hoards."
al ancient:thracian thracians
ln ancient:thracian ancient:civilization sys:is_a
ln ancient:thracian ancient:region:europe ancient:in_region
set.add name="set:ancient:all" id="ancient:thracian"
set.add name="set:ancient:region:europe:members" id="ancient:thracian"
def "ancient:src:thracian:kazanlak" "Kazanlak — https://en.wikipedia.org/wiki/Thracian_Tomb_of_Kazanlak"
ln ancient:thracian ancient:src:thracian:kazanlak ancient:source
set.add name="set:ancient:sources" id="ancient:src:thracian:kazanlak"
def "ancient:site:thracian:kazanlak" "Kazanlak (42.6258, 25.3992) — the painted Thracian tomb"
ln ancient:thracian ancient:site:thracian:kazanlak ancient:site
set.add name="set:ancient:sites" id="ancient:site:thracian:kazanlak"
ln ancient:thracian geo:country:BGR ancient:spans_country
ln ancient:thracian geo:country:ROU ancient:spans_country
ln ancient:thracian geo:country:GRC ancient:spans_country
ln ancient:thracian geo:country:TUR ancient:spans_country
def "ancient:norse" "Norse & Vikings (endonym Norrœnir, c.400–1100 CE) — Sagas, longships, and a reach from Baghdad to Newfoundland."
al ancient:norse norse_vikings
ln ancient:norse ancient:civilization sys:is_a
ln ancient:norse ancient:region:europe ancient:in_region
set.add name="set:ancient:all" id="ancient:norse"
set.add name="set:ancient:region:europe:members" id="ancient:norse"
def "ancient:src:norse:jelling" "Jelling — https://en.wikipedia.org/wiki/Jelling_stones"
ln ancient:norse ancient:src:norse:jelling ancient:source
set.add name="set:ancient:sources" id="ancient:src:norse:jelling"
def "ancient:site:norse:jelling" "Jelling (55.7567, 9.4194) — the royal runestones"
ln ancient:norse ancient:site:norse:jelling ancient:site
set.add name="set:ancient:sites" id="ancient:site:norse:jelling"
ln ancient:norse geo:country:NOR ancient:spans_country
ln ancient:norse geo:country:SWE ancient:spans_country
ln ancient:norse geo:country:DNK ancient:spans_country
ln ancient:norse geo:country:ISL ancient:spans_country
def "ancient:iberian" "Tartessos & Iberians (endonym Tartessos, c.1200–200 BCE) — The rich cultures of the ancient Iberian peninsula."
al ancient:iberian tartessos_iberians
ln ancient:iberian ancient:civilization sys:is_a
ln ancient:iberian ancient:region:europe ancient:in_region
set.add name="set:ancient:all" id="ancient:iberian"
set.add name="set:ancient:region:europe:members" id="ancient:iberian"
def "ancient:src:iberian:elche_la_alcudia" "Elche (La Alcudia) — https://en.wikipedia.org/wiki/La_Alcudia"
ln ancient:iberian ancient:src:iberian:elche_la_alcudia ancient:source
set.add name="set:ancient:sources" id="ancient:src:iberian:elche_la_alcudia"
def "ancient:site:iberian:elche_la_alcudia" "Elche (La Alcudia) (38.2392, -0.6953) — site of the Lady of Elche"
ln ancient:iberian ancient:site:iberian:elche_la_alcudia ancient:site
set.add name="set:ancient:sites" id="ancient:site:iberian:elche_la_alcudia"
ln ancient:iberian geo:country:ESP ancient:spans_country
ln ancient:iberian geo:country:PRT ancient:spans_country

def "ancient:region:mesoamerica" "Mesoamerica — the land of the sacred count. From the Olmec mother-culture to the Aztec sun — writing, the Long Count, and towering cities."
al ancient:region:mesoamerica mesoamerica
ln ancient:region:mesoamerica ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:mesoamerica"
def "ancient:region:mesoamerica:pin" "19, -99 (WGS84) — atlas map pin of Mesoamerica"
ln ancient:region:mesoamerica ancient:region:mesoamerica:pin geo:has_coordinate
def "ancient:olmec" "Olmec (endonym the mother-culture, c.1500–400 BCE) — Colossal basalt heads; the root of Mesoamerican culture."
al ancient:olmec olmec
ln ancient:olmec ancient:civilization sys:is_a
ln ancient:olmec ancient:region:mesoamerica ancient:in_region
set.add name="set:ancient:all" id="ancient:olmec"
set.add name="set:ancient:region:mesoamerica:members" id="ancient:olmec"
def "ancient:src:olmec:la_venta" "La Venta — https://en.wikipedia.org/wiki/La_Venta"
ln ancient:olmec ancient:src:olmec:la_venta ancient:source
set.add name="set:ancient:sources" id="ancient:src:olmec:la_venta"
def "ancient:site:olmec:la_venta" "La Venta (18.1033, -94.0402) — the colossal stone heads"
ln ancient:olmec ancient:site:olmec:la_venta ancient:site
set.add name="set:ancient:sites" id="ancient:site:olmec:la_venta"
ln ancient:olmec geo:country:MEX ancient:spans_country
def "ancient:maya" "Maya (endonym Maya, c.2000 BCE–1500 CE) — Full writing, the Long Count calendar, Tikal and Palenque."
al ancient:maya maya
ln ancient:maya ancient:civilization sys:is_a
ln ancient:maya ancient:region:mesoamerica ancient:in_region
set.add name="set:ancient:all" id="ancient:maya"
set.add name="set:ancient:region:mesoamerica:members" id="ancient:maya"
def "ancient:src:maya:tikal" "Tikal — https://en.wikipedia.org/wiki/Tikal"
ln ancient:maya ancient:src:maya:tikal ancient:source
set.add name="set:ancient:sources" id="ancient:src:maya:tikal"
def "ancient:src:maya:chich_n_itz" "Chichén Itzá — https://en.wikipedia.org/wiki/Chichen_Itza"
ln ancient:maya ancient:src:maya:chich_n_itz ancient:source
set.add name="set:ancient:sources" id="ancient:src:maya:chich_n_itz"
def "ancient:site:maya:tikal" "Tikal (17.2219, -89.6236) — the great jungle city"
ln ancient:maya ancient:site:maya:tikal ancient:site
set.add name="set:ancient:sites" id="ancient:site:maya:tikal"
def "ancient:site:maya:chich_n_itz" "Chichén Itzá (20.6829, -88.5686) — El Castillo pyramid"
ln ancient:maya ancient:site:maya:chich_n_itz ancient:site
set.add name="set:ancient:sites" id="ancient:site:maya:chich_n_itz"
ln ancient:maya geo:country:MEX ancient:spans_country
ln ancient:maya geo:country:GTM ancient:spans_country
ln ancient:maya geo:country:BLZ ancient:spans_country
ln ancient:maya geo:country:HND ancient:spans_country
ln ancient:maya geo:country:SLV ancient:spans_country
def "ancient:zapotec" "Zapotec (endonym Bene Za, c.500 BCE–1521 CE) — Monte Albán, high above the Oaxaca valley."
al ancient:zapotec zapotec
ln ancient:zapotec ancient:civilization sys:is_a
ln ancient:zapotec ancient:region:mesoamerica ancient:in_region
set.add name="set:ancient:all" id="ancient:zapotec"
set.add name="set:ancient:region:mesoamerica:members" id="ancient:zapotec"
def "ancient:src:zapotec:monte_alb_n" "Monte Albán — https://en.wikipedia.org/wiki/Monte_Alb%C3%A1n"
ln ancient:zapotec ancient:src:zapotec:monte_alb_n ancient:source
set.add name="set:ancient:sources" id="ancient:src:zapotec:monte_alb_n"
def "ancient:site:zapotec:monte_alb_n" "Monte Albán (17.0439, -96.7678) — the mountaintop capital"
ln ancient:zapotec ancient:site:zapotec:monte_alb_n ancient:site
set.add name="set:ancient:sites" id="ancient:site:zapotec:monte_alb_n"
ln ancient:zapotec geo:country:MEX ancient:spans_country
def "ancient:teotihuacan" "Teotihuacan (endonym the place of the gods, c.100 BCE–550 CE) — A vast planned city and its Pyramid of the Sun."
al ancient:teotihuacan teotihuacan
ln ancient:teotihuacan ancient:civilization sys:is_a
ln ancient:teotihuacan ancient:region:mesoamerica ancient:in_region
set.add name="set:ancient:all" id="ancient:teotihuacan"
set.add name="set:ancient:region:mesoamerica:members" id="ancient:teotihuacan"
def "ancient:src:teotihuacan:teotihuacan" "Teotihuacan — https://en.wikipedia.org/wiki/Teotihuacan"
ln ancient:teotihuacan ancient:src:teotihuacan:teotihuacan ancient:source
set.add name="set:ancient:sources" id="ancient:src:teotihuacan:teotihuacan"
def "ancient:site:teotihuacan:teotihuacan" "Teotihuacan (19.6925, -98.8438) — the Pyramids of the Sun and Moon"
ln ancient:teotihuacan ancient:site:teotihuacan:teotihuacan ancient:site
set.add name="set:ancient:sites" id="ancient:site:teotihuacan:teotihuacan"
ln ancient:teotihuacan geo:country:MEX ancient:spans_country
def "ancient:toltec" "Toltec (endonym Tōltēcah, c.900–1150 CE) — The builders of Tula, revered by the Aztecs who followed."
al ancient:toltec toltec
ln ancient:toltec ancient:civilization sys:is_a
ln ancient:toltec ancient:region:mesoamerica ancient:in_region
set.add name="set:ancient:all" id="ancient:toltec"
set.add name="set:ancient:region:mesoamerica:members" id="ancient:toltec"
def "ancient:src:toltec:tula" "Tula — https://en.wikipedia.org/wiki/Tula_(Mesoamerican_site)"
ln ancient:toltec ancient:src:toltec:tula ancient:source
set.add name="set:ancient:sources" id="ancient:src:toltec:tula"
def "ancient:site:toltec:tula" "Tula (20.0642, -99.3408) — the Atlantean warrior columns"
ln ancient:toltec ancient:site:toltec:tula ancient:site
set.add name="set:ancient:sites" id="ancient:site:toltec:tula"
ln ancient:toltec geo:country:MEX ancient:spans_country
def "ancient:aztec" "Aztec (Mexica) (endonym Mēxihcah, c.1300–1521 CE) — Tenochtitlan on the lake and the Triple Alliance."
al ancient:aztec aztec_mexica
ln ancient:aztec ancient:civilization sys:is_a
ln ancient:aztec ancient:region:mesoamerica ancient:in_region
set.add name="set:ancient:all" id="ancient:aztec"
set.add name="set:ancient:region:mesoamerica:members" id="ancient:aztec"
def "ancient:src:aztec:tenochtitlan" "Tenochtitlan — https://en.wikipedia.org/wiki/Templo_Mayor"
ln ancient:aztec ancient:src:aztec:tenochtitlan ancient:source
set.add name="set:ancient:sources" id="ancient:src:aztec:tenochtitlan"
def "ancient:site:aztec:tenochtitlan" "Tenochtitlan (19.4349, -99.1314) — the Templo Mayor; Mexico City"
ln ancient:aztec ancient:site:aztec:tenochtitlan ancient:site
set.add name="set:ancient:sites" id="ancient:site:aztec:tenochtitlan"
ln ancient:aztec geo:country:MEX ancient:spans_country

def "ancient:region:andes" "The Andes & South America — the four quarters. The Americas’ oldest cities, and a chain of highland and coastal states ending with the Inca."
al ancient:region:andes andes
ln ancient:region:andes ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:andes"
def "ancient:region:andes:pin" "-13, -72 (WGS84) — atlas map pin of The Andes & South America"
ln ancient:region:andes ancient:region:andes:pin geo:has_coordinate
def "ancient:caral" "Norte Chico (Caral) (endonym Caral-Supe, c.3500–1800 BCE) — The oldest known civilization in the Americas."
al ancient:caral norte_chico_caral
ln ancient:caral ancient:civilization sys:is_a
ln ancient:caral ancient:region:andes ancient:in_region
set.add name="set:ancient:all" id="ancient:caral"
set.add name="set:ancient:region:andes:members" id="ancient:caral"
def "ancient:src:caral:caral" "Caral — https://en.wikipedia.org/wiki/Caral"
ln ancient:caral ancient:src:caral:caral ancient:source
set.add name="set:ancient:sources" id="ancient:src:caral:caral"
def "ancient:site:caral:caral" "Caral (-10.8936, -77.5203) — the oldest city in the Americas"
ln ancient:caral ancient:site:caral:caral ancient:site
set.add name="set:ancient:sites" id="ancient:site:caral:caral"
ln ancient:caral geo:country:PER ancient:spans_country
def "ancient:chavin" "Chavín (endonym Chavín, c.900–200 BCE) — A pan-Andean cult and art-style from the highlands."
al ancient:chavin chav_n
ln ancient:chavin ancient:civilization sys:is_a
ln ancient:chavin ancient:region:andes ancient:in_region
set.add name="set:ancient:all" id="ancient:chavin"
set.add name="set:ancient:region:andes:members" id="ancient:chavin"
def "ancient:src:chavin:chav_n_de_hu_ntar" "Chavín de Huántar — https://en.wikipedia.org/wiki/Chav%C3%ADn_de_Hu%C3%A1ntar"
ln ancient:chavin ancient:src:chavin:chav_n_de_hu_ntar ancient:source
set.add name="set:ancient:sources" id="ancient:src:chavin:chav_n_de_hu_ntar"
def "ancient:site:chavin:chav_n_de_hu_ntar" "Chavín de Huántar (-9.5928, -77.1785) — the carved stone temple"
ln ancient:chavin ancient:site:chavin:chav_n_de_hu_ntar ancient:site
set.add name="set:ancient:sites" id="ancient:site:chavin:chav_n_de_hu_ntar"
ln ancient:chavin geo:country:PER ancient:spans_country
def "ancient:nazca" "Nazca (endonym Nasca, c.100 BCE–800 CE) — The great geoglyphs drawn across the desert floor."
al ancient:nazca nazca
ln ancient:nazca ancient:civilization sys:is_a
ln ancient:nazca ancient:region:andes ancient:in_region
set.add name="set:ancient:all" id="ancient:nazca"
set.add name="set:ancient:region:andes:members" id="ancient:nazca"
def "ancient:src:nazca:nazca" "Nazca — https://en.wikipedia.org/wiki/Nazca_Lines"
ln ancient:nazca ancient:src:nazca:nazca ancient:source
set.add name="set:ancient:sources" id="ancient:src:nazca:nazca"
def "ancient:site:nazca:nazca" "Nazca (-14.739, -75.1301) — the great desert geoglyphs"
ln ancient:nazca ancient:site:nazca:nazca ancient:site
set.add name="set:ancient:sites" id="ancient:site:nazca:nazca"
ln ancient:nazca geo:country:PER ancient:spans_country
def "ancient:moche" "Moche (endonym Moche, c.100–800 CE) — North-coast lords and their vivid portrait ceramics."
al ancient:moche moche
ln ancient:moche ancient:civilization sys:is_a
ln ancient:moche ancient:region:andes ancient:in_region
set.add name="set:ancient:all" id="ancient:moche"
set.add name="set:ancient:region:andes:members" id="ancient:moche"
def "ancient:src:moche:huacas_de_moche" "Huacas de Moche — https://en.wikipedia.org/wiki/Huaca_del_Sol"
ln ancient:moche ancient:src:moche:huacas_de_moche ancient:source
set.add name="set:ancient:sources" id="ancient:src:moche:huacas_de_moche"
def "ancient:site:moche:huacas_de_moche" "Huacas de Moche (-8.1322, -78.9947) — the Huaca del Sol and de la Luna"
ln ancient:moche ancient:site:moche:huacas_de_moche ancient:site
set.add name="set:ancient:sites" id="ancient:site:moche:huacas_de_moche"
ln ancient:moche geo:country:PER ancient:spans_country
def "ancient:tiwanaku" "Tiwanaku (endonym Tiwanaku, c.550–1000 CE) — The great state on the shores of Lake Titicaca."
al ancient:tiwanaku tiwanaku
ln ancient:tiwanaku ancient:civilization sys:is_a
ln ancient:tiwanaku ancient:region:andes ancient:in_region
set.add name="set:ancient:all" id="ancient:tiwanaku"
set.add name="set:ancient:region:andes:members" id="ancient:tiwanaku"
def "ancient:src:tiwanaku:tiwanaku" "Tiwanaku — https://en.wikipedia.org/wiki/Tiwanaku"
ln ancient:tiwanaku ancient:src:tiwanaku:tiwanaku ancient:source
set.add name="set:ancient:sources" id="ancient:src:tiwanaku:tiwanaku"
def "ancient:site:tiwanaku:tiwanaku" "Tiwanaku (-16.5547, -68.6733) — the Gate of the Sun"
ln ancient:tiwanaku ancient:site:tiwanaku:tiwanaku ancient:site
set.add name="set:ancient:sites" id="ancient:site:tiwanaku:tiwanaku"
ln ancient:tiwanaku geo:country:BOL ancient:spans_country
ln ancient:tiwanaku geo:country:PER ancient:spans_country
def "ancient:wari" "Wari (endonym Wari, c.600–1000 CE) — An Andean empire of roads a half-millennium before the Inca."
al ancient:wari wari
ln ancient:wari ancient:civilization sys:is_a
ln ancient:wari ancient:region:andes ancient:in_region
set.add name="set:ancient:all" id="ancient:wari"
set.add name="set:ancient:region:andes:members" id="ancient:wari"
def "ancient:src:wari:wari" "Wari — https://en.wikipedia.org/wiki/Wari_(archaeological_site)"
ln ancient:wari ancient:src:wari:wari ancient:source
set.add name="set:ancient:sources" id="ancient:src:wari:wari"
def "ancient:site:wari:wari" "Wari (-13.0606, -74.1989) — the highland imperial capital"
ln ancient:wari ancient:site:wari:wari ancient:site
set.add name="set:ancient:sites" id="ancient:site:wari:wari"
ln ancient:wari geo:country:PER ancient:spans_country
def "ancient:chimu" "Chimú (endonym Chimor, c.900–1470 CE) — Chan Chan, the largest adobe city on earth."
al ancient:chimu chim
ln ancient:chimu ancient:civilization sys:is_a
ln ancient:chimu ancient:region:andes ancient:in_region
set.add name="set:ancient:all" id="ancient:chimu"
set.add name="set:ancient:region:andes:members" id="ancient:chimu"
def "ancient:src:chimu:chan_chan" "Chan Chan — https://en.wikipedia.org/wiki/Chan_Chan"
ln ancient:chimu ancient:src:chimu:chan_chan ancient:source
set.add name="set:ancient:sources" id="ancient:src:chimu:chan_chan"
def "ancient:site:chimu:chan_chan" "Chan Chan (-8.1058, -79.0744) — the great adobe city"
ln ancient:chimu ancient:site:chimu:chan_chan ancient:site
set.add name="set:ancient:sites" id="ancient:site:chimu:chan_chan"
ln ancient:chimu geo:country:PER ancient:spans_country
def "ancient:inca" "Inca (endonym Tawantinsuyu, c.1400–1533 CE) — Cusco, Machu Picchu — the largest empire of the Americas."
al ancient:inca inca
ln ancient:inca ancient:civilization sys:is_a
ln ancient:inca ancient:region:andes ancient:in_region
set.add name="set:ancient:all" id="ancient:inca"
set.add name="set:ancient:region:andes:members" id="ancient:inca"
def "ancient:src:inca:cusco" "Cusco — https://en.wikipedia.org/wiki/Cusco"
ln ancient:inca ancient:src:inca:cusco ancient:source
set.add name="set:ancient:sources" id="ancient:src:inca:cusco"
def "ancient:src:inca:machu_picchu" "Machu Picchu — https://en.wikipedia.org/wiki/Machu_Picchu"
ln ancient:inca ancient:src:inca:machu_picchu ancient:source
set.add name="set:ancient:sources" id="ancient:src:inca:machu_picchu"
def "ancient:site:inca:cusco" "Cusco (-13.5173, -71.98) — the Inca capital"
ln ancient:inca ancient:site:inca:cusco ancient:site
set.add name="set:ancient:sites" id="ancient:site:inca:cusco"
def "ancient:site:inca:machu_picchu" "Machu Picchu (-13.1631, -72.545) — the royal estate in the clouds"
ln ancient:inca ancient:site:inca:machu_picchu ancient:site
set.add name="set:ancient:sites" id="ancient:site:inca:machu_picchu"
ln ancient:inca geo:country:PER ancient:spans_country
ln ancient:inca geo:country:BOL ancient:spans_country
ln ancient:inca geo:country:ECU ancient:spans_country
ln ancient:inca geo:country:CHL ancient:spans_country
ln ancient:inca geo:country:ARG ancient:spans_country
ln ancient:inca geo:country:COL ancient:spans_country

def "ancient:region:north_america" "North America — the mound-builders & the pueblos. The city-builders and earthwork cultures of the North American continent."
al ancient:region:north_america north_america
ln ancient:region:north_america ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:north_america"
def "ancient:region:north_america:pin" "37, -104 (WGS84) — atlas map pin of North America"
ln ancient:region:north_america ancient:region:north_america:pin geo:has_coordinate
def "ancient:puebloan" "Ancestral Puebloan (endonym Anasazi, c.100–1600 CE) — Chaco Canyon and the great cliff dwellings."
al ancient:puebloan ancestral_puebloan
ln ancient:puebloan ancient:civilization sys:is_a
ln ancient:puebloan ancient:region:north_america ancient:in_region
set.add name="set:ancient:all" id="ancient:puebloan"
set.add name="set:ancient:region:north_america:members" id="ancient:puebloan"
def "ancient:src:puebloan:mesa_verde_cliff_palace" "Mesa Verde (Cliff Palace) — https://en.wikipedia.org/wiki/Mesa_Verde_National_Park"
ln ancient:puebloan ancient:src:puebloan:mesa_verde_cliff_palace ancient:source
set.add name="set:ancient:sources" id="ancient:src:puebloan:mesa_verde_cliff_palace"
def "ancient:site:puebloan:mesa_verde_cliff_palace" "Mesa Verde (Cliff Palace) (37.1666, -108.4733) — the cliff dwellings"
ln ancient:puebloan ancient:site:puebloan:mesa_verde_cliff_palace ancient:site
set.add name="set:ancient:sites" id="ancient:site:puebloan:mesa_verde_cliff_palace"
ln ancient:puebloan geo:country:USA ancient:spans_country
def "ancient:hohokam" "Hohokam (endonym Huhugam, c.300–1500 CE) — Canal-farmers of the Sonoran desert."
al ancient:hohokam hohokam
ln ancient:hohokam ancient:civilization sys:is_a
ln ancient:hohokam ancient:region:north_america ancient:in_region
set.add name="set:ancient:all" id="ancient:hohokam"
set.add name="set:ancient:region:north_america:members" id="ancient:hohokam"
def "ancient:src:hohokam:snaketown" "Snaketown — https://en.wikipedia.org/wiki/Snaketown"
ln ancient:hohokam ancient:src:hohokam:snaketown ancient:source
set.add name="set:ancient:sources" id="ancient:src:hohokam:snaketown"
def "ancient:site:hohokam:snaketown" "Snaketown (33.1875, -111.9245) — the great canal-irrigation town"
ln ancient:hohokam ancient:site:hohokam:snaketown ancient:site
set.add name="set:ancient:sites" id="ancient:site:hohokam:snaketown"
ln ancient:hohokam geo:country:USA ancient:spans_country
def "ancient:hopewell" "Hopewell & Adena (endonym Hopewell, c.800 BCE–500 CE) — The great earthwork-builders of the Ohio valley."
al ancient:hopewell hopewell_adena
ln ancient:hopewell ancient:civilization sys:is_a
ln ancient:hopewell ancient:region:north_america ancient:in_region
set.add name="set:ancient:all" id="ancient:hopewell"
set.add name="set:ancient:region:north_america:members" id="ancient:hopewell"
def "ancient:src:hopewell:mound_city" "Mound City — https://en.wikipedia.org/wiki/Hopewell_Culture_National_Historical_Park"
ln ancient:hopewell ancient:src:hopewell:mound_city ancient:source
set.add name="set:ancient:sources" id="ancient:src:hopewell:mound_city"
def "ancient:site:hopewell:mound_city" "Mound City (39.376, -83.007) — the great earthwork mounds"
ln ancient:hopewell ancient:site:hopewell:mound_city ancient:site
set.add name="set:ancient:sites" id="ancient:site:hopewell:mound_city"
ln ancient:hopewell geo:country:USA ancient:spans_country
def "ancient:cahokia" "Mississippian (Cahokia) (endonym Mississippian, c.800–1600 CE) — Cahokia, a mound-city that rivaled medieval European towns."
al ancient:cahokia mississippian_cahokia
ln ancient:cahokia ancient:civilization sys:is_a
ln ancient:cahokia ancient:region:north_america ancient:in_region
set.add name="set:ancient:all" id="ancient:cahokia"
set.add name="set:ancient:region:north_america:members" id="ancient:cahokia"
def "ancient:src:cahokia:cahokia" "Cahokia — https://en.wikipedia.org/wiki/Cahokia"
ln ancient:cahokia ancient:src:cahokia:cahokia ancient:source
set.add name="set:ancient:sources" id="ancient:src:cahokia:cahokia"
def "ancient:site:cahokia:cahokia" "Cahokia (38.6607, -90.062) — Monks Mound; the great plaza"
ln ancient:cahokia ancient:site:cahokia:cahokia ancient:site
set.add name="set:ancient:sites" id="ancient:site:cahokia:cahokia"
ln ancient:cahokia geo:country:USA ancient:spans_country

def "ancient:region:africa" "Sub-Saharan Africa — the gold, the bronze & the stone. The empires and city-states of the west, the east coast, and the great stone city of the south."
al ancient:region:africa africa
ln ancient:region:africa ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:africa"
def "ancient:region:africa:pin" "8, 14 (WGS84) — atlas map pin of Sub-Saharan Africa"
ln ancient:region:africa ancient:region:africa:pin geo:has_coordinate
def "ancient:nok" "Nok (endonym Nok, c.1500 BCE–300 CE) — Nigeria’s terracotta sculptors and early iron-workers."
al ancient:nok nok
ln ancient:nok ancient:civilization sys:is_a
ln ancient:nok ancient:region:africa ancient:in_region
set.add name="set:ancient:all" id="ancient:nok"
set.add name="set:ancient:region:africa:members" id="ancient:nok"
def "ancient:src:nok:nok" "Nok — https://latitude.to/satellite-map/ng/nigeria/7348/nok-culture"
ln ancient:nok ancient:src:nok:nok ancient:source
set.add name="set:ancient:sources" id="ancient:src:nok:nok"
def "ancient:site:nok:nok" "Nok (9.5, 8.0) — the terracotta sculpture culture (area centroid)"
ln ancient:nok ancient:site:nok:nok ancient:site
set.add name="set:ancient:sites" id="ancient:site:nok:nok"
ln ancient:nok geo:country:NGA ancient:spans_country
def "ancient:aksum" "Aksum (endonym Aksum, c.100–940 CE) — An Ethiopian empire of obelisks and Red-Sea trade."
al ancient:aksum aksum
ln ancient:aksum ancient:civilization sys:is_a
ln ancient:aksum ancient:region:africa ancient:in_region
set.add name="set:ancient:all" id="ancient:aksum"
set.add name="set:ancient:region:africa:members" id="ancient:aksum"
def "ancient:src:aksum:aksum" "Aksum — https://en.wikipedia.org/wiki/Axum"
ln ancient:aksum ancient:src:aksum:aksum ancient:source
set.add name="set:ancient:sources" id="ancient:src:aksum:aksum"
def "ancient:site:aksum:aksum" "Aksum (14.1322, 38.7197) — the great carved stelae"
ln ancient:aksum ancient:site:aksum:aksum ancient:site
set.add name="set:ancient:sites" id="ancient:site:aksum:aksum"
ln ancient:aksum geo:country:ETH ancient:spans_country
ln ancient:aksum geo:country:ERI ancient:spans_country
def "ancient:ghana" "Ghana Empire (endonym Wagadou, c.300–1200 CE) — The first great gold-empire of the western Sahel."
al ancient:ghana ghana_empire
ln ancient:ghana ancient:civilization sys:is_a
ln ancient:ghana ancient:region:africa ancient:in_region
set.add name="set:ancient:all" id="ancient:ghana"
set.add name="set:ancient:region:africa:members" id="ancient:ghana"
def "ancient:src:ghana:koumbi_saleh" "Koumbi Saleh — https://en.wikipedia.org/wiki/Koumbi_Saleh"
ln ancient:ghana ancient:src:ghana:koumbi_saleh ancient:source
set.add name="set:ancient:sources" id="ancient:src:ghana:koumbi_saleh"
def "ancient:site:ghana:koumbi_saleh" "Koumbi Saleh (15.7656, -7.9686) — the reputed capital of Ghana"
ln ancient:ghana ancient:site:ghana:koumbi_saleh ancient:site
set.add name="set:ancient:sites" id="ancient:site:ghana:koumbi_saleh"
ln ancient:ghana geo:country:MRT ancient:spans_country
ln ancient:ghana geo:country:MLI ancient:spans_country
def "ancient:mali" "Mali Empire (endonym Manden Kurufaba, c.1235–1600 CE) — Mansa Musa and the scholars of Timbuktu."
al ancient:mali mali_empire
ln ancient:mali ancient:civilization sys:is_a
ln ancient:mali ancient:region:africa ancient:in_region
set.add name="set:ancient:all" id="ancient:mali"
set.add name="set:ancient:region:africa:members" id="ancient:mali"
def "ancient:src:mali:timbuktu" "Timbuktu — https://en.wikipedia.org/wiki/Timbuktu"
ln ancient:mali ancient:src:mali:timbuktu ancient:source
set.add name="set:ancient:sources" id="ancient:src:mali:timbuktu"
def "ancient:site:mali:timbuktu" "Timbuktu (16.7666, -3.0026) — the Saharan city of gold and learning"
ln ancient:mali ancient:site:mali:timbuktu ancient:site
set.add name="set:ancient:sites" id="ancient:site:mali:timbuktu"
ln ancient:mali geo:country:MLI ancient:spans_country
ln ancient:mali geo:country:GIN ancient:spans_country
ln ancient:mali geo:country:SEN ancient:spans_country
ln ancient:mali geo:country:MRT ancient:spans_country
def "ancient:songhai" "Songhai Empire (endonym Songhay, c.1430–1591 CE) — The largest state in African history."
al ancient:songhai songhai_empire
ln ancient:songhai ancient:civilization sys:is_a
ln ancient:songhai ancient:region:africa ancient:in_region
set.add name="set:ancient:all" id="ancient:songhai"
set.add name="set:ancient:region:africa:members" id="ancient:songhai"
def "ancient:src:songhai:gao" "Gao — https://en.wikipedia.org/wiki/Gao"
ln ancient:songhai ancient:src:songhai:gao ancient:source
set.add name="set:ancient:sources" id="ancient:src:songhai:gao"
def "ancient:site:songhai:gao" "Gao (16.267, -0.05) — the Songhai capital"
ln ancient:songhai ancient:site:songhai:gao ancient:site
set.add name="set:ancient:sites" id="ancient:site:songhai:gao"
ln ancient:songhai geo:country:MLI ancient:spans_country
ln ancient:songhai geo:country:NER ancient:spans_country
def "ancient:benin" "Ife & Benin (endonym Ilé-Ifẹ̀ · Edo, c.1000–1897 CE) — The Yoruba and Edo masters of brass and bronze."
al ancient:benin ife_benin
ln ancient:benin ancient:civilization sys:is_a
ln ancient:benin ancient:region:africa ancient:in_region
set.add name="set:ancient:all" id="ancient:benin"
set.add name="set:ancient:region:africa:members" id="ancient:benin"
def "ancient:src:benin:benin_city" "Benin City — https://en.wikipedia.org/wiki/Benin_City"
ln ancient:benin ancient:src:benin:benin_city ancient:source
set.add name="set:ancient:sources" id="ancient:src:benin:benin_city"
def "ancient:site:benin:benin_city" "Benin City (6.3333, 5.6222) — the walled city; the bronzes"
ln ancient:benin ancient:site:benin:benin_city ancient:site
set.add name="set:ancient:sites" id="ancient:site:benin:benin_city"
ln ancient:benin geo:country:NGA ancient:spans_country
def "ancient:great_zimbabwe" "Great Zimbabwe (endonym Dzimba dza mabwe, c.1100–1450 CE) — A great dry-stone city ruling the southern gold trade."
al ancient:great_zimbabwe great_zimbabwe
ln ancient:great_zimbabwe ancient:civilization sys:is_a
ln ancient:great_zimbabwe ancient:region:africa ancient:in_region
set.add name="set:ancient:all" id="ancient:great_zimbabwe"
set.add name="set:ancient:region:africa:members" id="ancient:great_zimbabwe"
def "ancient:src:great_zimbabwe:great_zimbabwe" "Great Zimbabwe — https://en.wikipedia.org/wiki/Great_Zimbabwe"
ln ancient:great_zimbabwe ancient:src:great_zimbabwe:great_zimbabwe ancient:source
set.add name="set:ancient:sources" id="ancient:src:great_zimbabwe:great_zimbabwe"
def "ancient:site:great_zimbabwe:great_zimbabwe" "Great Zimbabwe (-20.2674, 30.9335) — the great dry-stone enclosures"
ln ancient:great_zimbabwe ancient:site:great_zimbabwe:great_zimbabwe ancient:site
set.add name="set:ancient:sites" id="ancient:site:great_zimbabwe:great_zimbabwe"
ln ancient:great_zimbabwe geo:country:ZWE ancient:spans_country
def "ancient:swahili" "Swahili Coast (endonym Waswahili, c.800–1500 CE) — Kilwa and the Indian-Ocean city-states."
al ancient:swahili swahili_coast
ln ancient:swahili ancient:civilization sys:is_a
ln ancient:swahili ancient:region:africa ancient:in_region
set.add name="set:ancient:all" id="ancient:swahili"
set.add name="set:ancient:region:africa:members" id="ancient:swahili"
def "ancient:src:swahili:kilwa_kisiwani" "Kilwa Kisiwani — https://en.wikipedia.org/wiki/Kilwa_Kisiwani"
ln ancient:swahili ancient:src:swahili:kilwa_kisiwani ancient:source
set.add name="set:ancient:sources" id="ancient:src:swahili:kilwa_kisiwani"
def "ancient:site:swahili:kilwa_kisiwani" "Kilwa Kisiwani (-8.96, 39.5128) — the great coral-stone port"
ln ancient:swahili ancient:site:swahili:kilwa_kisiwani ancient:site
set.add name="set:ancient:sites" id="ancient:site:swahili:kilwa_kisiwani"
ln ancient:swahili geo:country:KEN ancient:spans_country
ln ancient:swahili geo:country:TZA ancient:spans_country
ln ancient:swahili geo:country:MOZ ancient:spans_country
ln ancient:swahili geo:country:SOM ancient:spans_country

def "ancient:region:oceania" "Oceania & Polynesia — the voyagers of the great ocean. The longest human migration — the settlement of a third of the planet by open-ocean canoe."
al ancient:region:oceania oceania
ln ancient:region:oceania ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:oceania"
def "ancient:region:oceania:pin" "-18, 150 (WGS84) — atlas map pin of Oceania & Polynesia"
ln ancient:region:oceania ancient:region:oceania:pin geo:has_coordinate
def "ancient:lapita" "Lapita (endonym Lapita, c.1600–500 BCE) — The ancestral pottery-making voyagers of the Pacific."
al ancient:lapita lapita
ln ancient:lapita ancient:civilization sys:is_a
ln ancient:lapita ancient:region:oceania ancient:in_region
set.add name="set:ancient:all" id="ancient:lapita"
set.add name="set:ancient:region:oceania:members" id="ancient:lapita"
def "ancient:src:lapita:teouma" "Teouma — https://en.wikipedia.org/wiki/Teouma"
ln ancient:lapita ancient:src:lapita:teouma ancient:source
set.add name="set:ancient:sources" id="ancient:src:lapita:teouma"
def "ancient:site:lapita:teouma" "Teouma (-17.7856, 168.3862) — the oldest cemetery in the Pacific"
ln ancient:lapita ancient:site:lapita:teouma ancient:site
set.add name="set:ancient:sites" id="ancient:site:lapita:teouma"
ln ancient:lapita geo:country:PNG ancient:spans_country
ln ancient:lapita geo:country:FJI ancient:spans_country
ln ancient:lapita geo:country:VUT ancient:spans_country
ln ancient:lapita geo:country:TON ancient:spans_country
def "ancient:polynesia" "Polynesian Voyagers (endonym the great triangle, c.900–1300 CE) — The settlement of the Pacific from Hawaiʻi to Aotearoa."
al ancient:polynesia polynesian_voyagers
ln ancient:polynesia ancient:civilization sys:is_a
ln ancient:polynesia ancient:region:oceania ancient:in_region
set.add name="set:ancient:all" id="ancient:polynesia"
set.add name="set:ancient:region:oceania:members" id="ancient:polynesia"
def "ancient:src:polynesia:taputapuatea" "Taputapuatea — https://en.wikipedia.org/wiki/Taputapuatea_marae"
ln ancient:polynesia ancient:src:polynesia:taputapuatea ancient:source
set.add name="set:ancient:sources" id="ancient:src:polynesia:taputapuatea"
def "ancient:site:polynesia:taputapuatea" "Taputapuatea (-16.8361, -151.3592) — the great ocean-voyaging marae"
ln ancient:polynesia ancient:site:polynesia:taputapuatea ancient:site
set.add name="set:ancient:sites" id="ancient:site:polynesia:taputapuatea"
ln ancient:polynesia geo:country:WSM ancient:spans_country
ln ancient:polynesia geo:country:TON ancient:spans_country
ln ancient:polynesia geo:country:PYF ancient:spans_country
def "ancient:rapa_nui" "Rapa Nui (endonym Rapa Nui, c.1200–1700 CE) — Easter Island and its moai."
al ancient:rapa_nui rapa_nui
ln ancient:rapa_nui ancient:civilization sys:is_a
ln ancient:rapa_nui ancient:region:oceania ancient:in_region
set.add name="set:ancient:all" id="ancient:rapa_nui"
set.add name="set:ancient:region:oceania:members" id="ancient:rapa_nui"
def "ancient:src:rapa_nui:rano_raraku" "Rano Raraku — https://en.wikipedia.org/wiki/Rano_Raraku"
ln ancient:rapa_nui ancient:src:rapa_nui:rano_raraku ancient:source
set.add name="set:ancient:sources" id="ancient:src:rapa_nui:rano_raraku"
def "ancient:site:rapa_nui:rano_raraku" "Rano Raraku (-27.1242, -109.2859) — the moai quarry"
ln ancient:rapa_nui ancient:site:rapa_nui:rano_raraku ancient:site
set.add name="set:ancient:sites" id="ancient:site:rapa_nui:rano_raraku"
ln ancient:rapa_nui geo:country:CHL ancient:spans_country
def "ancient:maori" "Māori (endonym Māori, c.1300 CE–) — The settling of Aotearoa / New Zealand."
al ancient:maori m_ori
ln ancient:maori ancient:civilization sys:is_a
ln ancient:maori ancient:region:oceania ancient:in_region
set.add name="set:ancient:all" id="ancient:maori"
set.add name="set:ancient:region:oceania:members" id="ancient:maori"
def "ancient:src:maori:wairau_bar" "Wairau Bar — https://en.wikipedia.org/wiki/Wairau_Bar"
ln ancient:maori ancient:src:maori:wairau_bar ancient:source
set.add name="set:ancient:sources" id="ancient:src:maori:wairau_bar"
def "ancient:site:maori:wairau_bar" "Wairau Bar (-41.5094, 174.0638) — the earliest Māori settlement"
ln ancient:maori ancient:site:maori:wairau_bar ancient:site
set.add name="set:ancient:sites" id="ancient:site:maori:wairau_bar"
ln ancient:maori geo:country:NZL ancient:spans_country
def "ancient:tonga" "Hawaiian & Tongan states (endonym Hawaiʻi · Tonga, c.1000–1800 CE) — Island chiefdoms and the sea-empire of the Tuʻi Tonga."
al ancient:tonga hawaiian_tongan_states
ln ancient:tonga ancient:civilization sys:is_a
ln ancient:tonga ancient:region:oceania ancient:in_region
set.add name="set:ancient:all" id="ancient:tonga"
set.add name="set:ancient:region:oceania:members" id="ancient:tonga"
def "ancient:src:tonga:ha_amonga_a_maui" "Haʻamonga ʻa Maui — https://en.wikipedia.org/wiki/Ha%CA%BBamonga_%CA%BBa_Maui"
ln ancient:tonga ancient:src:tonga:ha_amonga_a_maui ancient:source
set.add name="set:ancient:sources" id="ancient:src:tonga:ha_amonga_a_maui"
def "ancient:site:tonga:ha_amonga_a_maui" "Haʻamonga ʻa Maui (-21.1367, -175.0481) — the great stone trilithon"
ln ancient:tonga ancient:site:tonga:ha_amonga_a_maui ancient:site
set.add name="set:ancient:sites" id="ancient:site:tonga:ha_amonga_a_maui"
ln ancient:tonga geo:country:TON ancient:spans_country
def "ancient:aboriginal_australia" "Aboriginal Australia (endonym the songlines, c.50000 BCE–) — The world’s oldest continuous living culture."
al ancient:aboriginal_australia aboriginal_australia
ln ancient:aboriginal_australia ancient:civilization sys:is_a
ln ancient:aboriginal_australia ancient:region:oceania ancient:in_region
set.add name="set:ancient:all" id="ancient:aboriginal_australia"
set.add name="set:ancient:region:oceania:members" id="ancient:aboriginal_australia"
def "ancient:src:aboriginal_australia:uluru" "Uluru — https://en.wikipedia.org/wiki/Uluru"
ln ancient:aboriginal_australia ancient:src:aboriginal_australia:uluru ancient:source
set.add name="set:ancient:sources" id="ancient:src:aboriginal_australia:uluru"
def "ancient:site:aboriginal_australia:uluru" "Uluru (-25.345, 131.0361) — the sacred monolith"
ln ancient:aboriginal_australia ancient:site:aboriginal_australia:uluru ancient:site
set.add name="set:ancient:sites" id="ancient:site:aboriginal_australia:uluru"
ln ancient:aboriginal_australia geo:country:AUS ancient:spans_country

def "ancient:region:southeast_asia" "Southeast Asia — the temple-kingdoms & the sea-empires. The Hindu-Buddhist god-kings of the mainland and the maritime empires of the archipelago."
al ancient:region:southeast_asia southeast_asia
ln ancient:region:southeast_asia ancient:region sys:is_a
set.add name="set:ancient:regions" id="ancient:region:southeast_asia"
def "ancient:region:southeast_asia:pin" "12, 103 (WGS84) — atlas map pin of Southeast Asia"
ln ancient:region:southeast_asia ancient:region:southeast_asia:pin geo:has_coordinate
def "ancient:funan" "Funan (endonym Funan, c.100–550 CE) — The first great state of the Mekong delta."
al ancient:funan funan
ln ancient:funan ancient:civilization sys:is_a
ln ancient:funan ancient:region:southeast_asia ancient:in_region
set.add name="set:ancient:all" id="ancient:funan"
set.add name="set:ancient:region:southeast_asia:members" id="ancient:funan"
def "ancient:src:funan:c_eo" "Óc Eo — https://en.wikipedia.org/wiki/%C3%93c_Eo"
ln ancient:funan ancient:src:funan:c_eo ancient:source
set.add name="set:ancient:sources" id="ancient:src:funan:c_eo"
def "ancient:site:funan:c_eo" "Óc Eo (10.2328, 105.1517) — the delta trading port"
ln ancient:funan ancient:site:funan:c_eo ancient:site
set.add name="set:ancient:sites" id="ancient:site:funan:c_eo"
ln ancient:funan geo:country:KHM ancient:spans_country
ln ancient:funan geo:country:VNM ancient:spans_country
def "ancient:champa" "Champa (endonym Campā, c.192–1832 CE) — The coastal Hindu-Cham kingdoms of central Vietnam."
al ancient:champa champa
ln ancient:champa ancient:civilization sys:is_a
ln ancient:champa ancient:region:southeast_asia ancient:in_region
set.add name="set:ancient:all" id="ancient:champa"
set.add name="set:ancient:region:southeast_asia:members" id="ancient:champa"
def "ancient:src:champa:m_s_n" "Mỹ Sơn — https://en.wikipedia.org/wiki/M%E1%BB%B9_S%C6%A1n"
ln ancient:champa ancient:src:champa:m_s_n ancient:source
set.add name="set:ancient:sources" id="ancient:src:champa:m_s_n"
def "ancient:site:champa:m_s_n" "Mỹ Sơn (15.767, 108.117) — the brick Hindu temple valley"
ln ancient:champa ancient:site:champa:m_s_n ancient:site
set.add name="set:ancient:sites" id="ancient:site:champa:m_s_n"
ln ancient:champa geo:country:VNM ancient:spans_country
def "ancient:srivijaya" "Srivijaya (endonym Śrīvijaya, c.650–1288 CE) — The Sumatran empire that ruled the sea-lanes."
al ancient:srivijaya srivijaya
ln ancient:srivijaya ancient:civilization sys:is_a
ln ancient:srivijaya ancient:region:southeast_asia ancient:in_region
set.add name="set:ancient:all" id="ancient:srivijaya"
set.add name="set:ancient:region:southeast_asia:members" id="ancient:srivijaya"
def "ancient:src:srivijaya:palembang" "Palembang — https://en.wikipedia.org/wiki/Palembang"
ln ancient:srivijaya ancient:src:srivijaya:palembang ancient:source
set.add name="set:ancient:sources" id="ancient:src:srivijaya:palembang"
def "ancient:site:srivijaya:palembang" "Palembang (-2.9909, 104.7566) — the reputed Srivijayan capital"
ln ancient:srivijaya ancient:site:srivijaya:palembang ancient:site
set.add name="set:ancient:sites" id="ancient:site:srivijaya:palembang"
ln ancient:srivijaya geo:country:IDN ancient:spans_country
ln ancient:srivijaya geo:country:MYS ancient:spans_country
def "ancient:khmer" "Khmer Empire (endonym Kambuja, c.802–1431 CE) — Angkor Wat and the Khmer god-kings."
al ancient:khmer khmer_empire
ln ancient:khmer ancient:civilization sys:is_a
ln ancient:khmer ancient:region:southeast_asia ancient:in_region
set.add name="set:ancient:all" id="ancient:khmer"
set.add name="set:ancient:region:southeast_asia:members" id="ancient:khmer"
def "ancient:src:khmer:angkor" "Angkor — https://en.wikipedia.org/wiki/Angkor"
ln ancient:khmer ancient:src:khmer:angkor ancient:source
set.add name="set:ancient:sources" id="ancient:src:khmer:angkor"
def "ancient:site:khmer:angkor" "Angkor (13.4125, 103.8667) — Angkor Wat; the great temple-city"
ln ancient:khmer ancient:site:khmer:angkor ancient:site
set.add name="set:ancient:sites" id="ancient:site:khmer:angkor"
ln ancient:khmer geo:country:KHM ancient:spans_country
ln ancient:khmer geo:country:THA ancient:spans_country
ln ancient:khmer geo:country:LAO ancient:spans_country
def "ancient:pagan" "Pagan (Bagan) (endonym Bagan, c.849–1297 CE) — The temple-plain of the first Burmese empire."
al ancient:pagan pagan_bagan
ln ancient:pagan ancient:civilization sys:is_a
ln ancient:pagan ancient:region:southeast_asia ancient:in_region
set.add name="set:ancient:all" id="ancient:pagan"
set.add name="set:ancient:region:southeast_asia:members" id="ancient:pagan"
def "ancient:src:pagan:bagan" "Bagan — https://en.wikipedia.org/wiki/Bagan"
ln ancient:pagan ancient:src:pagan:bagan ancient:source
set.add name="set:ancient:sources" id="ancient:src:pagan:bagan"
def "ancient:site:pagan:bagan" "Bagan (21.1725, 94.86) — the plain of a thousand temples"
ln ancient:pagan ancient:site:pagan:bagan ancient:site
set.add name="set:ancient:sites" id="ancient:site:pagan:bagan"
ln ancient:pagan geo:country:MMR ancient:spans_country
def "ancient:majapahit" "Majapahit (endonym Majapahit, c.1293–1527 CE) — The Javanese thalassocracy of the archipelago."
al ancient:majapahit majapahit
ln ancient:majapahit ancient:civilization sys:is_a
ln ancient:majapahit ancient:region:southeast_asia ancient:in_region
set.add name="set:ancient:all" id="ancient:majapahit"
set.add name="set:ancient:region:southeast_asia:members" id="ancient:majapahit"
def "ancient:src:majapahit:trowulan" "Trowulan — https://en.wikipedia.org/wiki/Trowulan"
ln ancient:majapahit ancient:src:majapahit:trowulan ancient:source
set.add name="set:ancient:sources" id="ancient:src:majapahit:trowulan"
def "ancient:site:majapahit:trowulan" "Trowulan (-7.5419, 112.391) — the reputed Majapahit capital"
ln ancient:majapahit ancient:site:majapahit:trowulan ancient:site
set.add name="set:ancient:sites" id="ancient:site:majapahit:trowulan"
ln ancient:majapahit geo:country:IDN ancient:spans_country

