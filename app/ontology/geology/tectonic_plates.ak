# tectonic_plates.ak
# Major and minor tectonic plates + boundary types
# Source: USGS, geological surveys — Public domain
#

# ─── NAMESPACE ANCHOR ───────────────────────────────────────────────────────

def "geo:plate" "The set of rigid lithospheric plates whose relative motion drives plate tectonics; covers Earth's surface in a mosaic of interlocking segments."
set.add name="ontology.tectonic_plates" id="geo:plate"

# ─── MAJOR PLATES ────────────────────────────────────────────────────────────

def "geo:plate:pacific" "Pacific Plate: largest tectonic plate (~103 million km²); almost entirely oceanic lithosphere; bounded by the Ring of Fire — the most seismically and volcanically active zone on Earth."
ln geo:plate:pacific geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:pacific"

def "geo:plate:north_american" "North American Plate: second-largest plate (~76 million km²); carries North America, Greenland, Cuba, and western North Atlantic; western margin is San Andreas transform; eastern margin is Mid-Atlantic Ridge."
ln geo:plate:north_american geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:north_american"

def "geo:plate:eurasian" "Eurasian Plate: third-largest (~68 million km²); carries Europe and most of Asia; moving NE at ~2.1 cm/yr; southern boundary produces Alps (Africa collision) and Himalayas (India collision)."
ln geo:plate:eurasian geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:eurasian"

def "geo:plate:african" "African Plate: (~61 million km²); carries Africa and eastern Atlantic Ocean floor; rifting internally along East African Rift, slowly splitting Africa; collision with Eurasia closing Mediterranean."
ln geo:plate:african geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:african"

def "geo:plate:antarctic" "Antarctic Plate: (~60 million km²); surrounds Antarctica; bounded almost entirely by divergent mid-ocean ridges; moves slowly; subducts only at South Sandwich Trench."
ln geo:plate:antarctic geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:antarctic"

def "geo:plate:indo_australian" "Indo-Australian Plate: (~58 million km²); carries India and Australia together with surrounding Indian Ocean floor; fastest-moving major plate, pushing NE ~5–6 cm/yr; India's collision with Eurasia built the Himalayas."
ln geo:plate:indo_australian geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:indo_australian"

def "geo:plate:south_american" "South American Plate: (~44 million km²); carries South America and western South Atlantic; Nazca Plate subducts beneath its western margin, building the Andes; eastern margin is Mid-Atlantic Ridge."
ln geo:plate:south_american geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:south_american"

# ─── MINOR / SECONDARY PLATES ────────────────────────────────────────────────

def "geo:plate:nazca" "Nazca Plate: oceanic plate in the eastern Pacific off South America (~9.5 million km²); subducting rapidly beneath South American Plate at ~7.9 cm/yr; drives Andean volcanism and earthquakes."
ln geo:plate:nazca geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:nazca"

def "geo:plate:cocos" "Cocos Plate: small oceanic plate (~2.9 million km²) in the eastern Pacific off Central America; subducting beneath the Caribbean and North American plates; produces Middle America Trench and Central American volcanoes."
ln geo:plate:cocos geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:cocos"

def "geo:plate:caribbean" "Caribbean Plate: (~3.3 million km²); carries the Caribbean Sea and island arcs; bounded by transform faults (Motagua, Septentrional) on north and south; subducts under North American Plate at Puerto Rico Trench (deepest Atlantic point)."
ln geo:plate:caribbean geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:caribbean"

def "geo:plate:philippine" "Philippine Plate: (~5.5 million km²) in the western Pacific; subducting beneath the Eurasian Plate to the west (producing Japan, Philippines, and Mariana Trench — Earth's deepest point at ~11 km)."
ln geo:plate:philippine geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:philippine"

def "geo:plate:arabian" "Arabian Plate: (~5 million km²); carries the Arabian Peninsula; moving NE ~2.5 cm/yr; collision with Eurasian Plate creates the Zagros Mountains; Red Sea is an active rift spreading centre."
ln geo:plate:arabian geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:arabian"

def "geo:plate:juan_de_fuca" "Juan de Fuca Plate: small remnant (~250,000 km²) of the ancient Farallon Plate in the Pacific NW; subducting beneath the North American Plate along the Cascadia subduction zone; drives Cascade volcanoes (Mt St Helens, Mt Rainier); fault capable of Mw ~9 megathrust earthquakes."
ln geo:plate:juan_de_fuca geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:juan_de_fuca"

def "geo:plate:scotia" "Scotia Plate: (~1.6 million km²); occupies the Drake Passage between South America and Antarctica; Scotia Arc forms its eastern boundary; mostly oceanic; movement opens the deep-water connection between Pacific and Atlantic."
ln geo:plate:scotia geo:plate sys:part_of
set.add name="ontology.tectonic_plates" id="geo:plate:scotia"

# ─── PLATE BOUNDARY TYPES ────────────────────────────────────────────────────

def "geo:plate:boundary:convergent" "Convergent boundary: plates collide; produces mountains (continent-continent, e.g. Himalayas from India-Eurasia), volcanic arcs and ocean trenches (ocean-continent, e.g. Andes from Nazca-South America), or island arcs (ocean-ocean, e.g. Japan); generates deep-focus earthquakes."
set.add name="ontology.tectonic_plates" id="geo:plate:boundary:convergent"

def "geo:plate:boundary:divergent" "Divergent boundary: plates pull apart; produces mid-ocean ridges where new seafloor is created by upwelling basaltic magma (e.g. Mid-Atlantic Ridge); on continents produces rift valleys (e.g. East African Rift); shallow earthquakes and effusive volcanism."
set.add name="ontology.tectonic_plates" id="geo:plate:boundary:divergent"

def "geo:plate:boundary:transform" "Transform boundary: plates slide laterally past one another along strike-slip faults; no crust created or destroyed; produces shallow, moderate-to-large earthquakes; examples: San Andreas Fault (Pacific-North American plates), Alpine Fault (New Zealand)."
set.add name="ontology.tectonic_plates" id="geo:plate:boundary:transform"

# ─── GEOLOGICAL CONCEPTS ─────────────────────────────────────────────────────

def "geo:concept:subduction" "Subduction: process by which a denser oceanic lithospheric plate descends beneath a less-dense plate into the asthenosphere; produces deep-ocean trenches, volcanic arcs, and deep-focus earthquakes; primary driver of plate recycling."
ln geo:concept:subduction geo:plate:boundary:convergent sys:part_of
set.add name="ontology.tectonic_plates" id="geo:concept:subduction"

def "geo:concept:mid_ocean_ridge" "Mid-ocean ridge: continuous underwater mountain range ~65,000 km long where tectonic plates diverge and new oceanic crust is formed by seafloor spreading; most volcanically active geological feature on Earth; examples: Mid-Atlantic Ridge, East Pacific Rise."
ln geo:concept:mid_ocean_ridge geo:plate:boundary:divergent sys:part_of
set.add name="ontology.tectonic_plates" id="geo:concept:mid_ocean_ridge"

def "geo:concept:continental_drift" "Continental drift: hypothesis proposed by Alfred Wegener (1912) that continents move relative to each other over geological time; initially rejected; vindicated by seafloor spreading evidence in the 1960s and subsumed into plate tectonics theory."
set.add name="ontology.tectonic_plates" id="geo:concept:continental_drift"

def "geo:concept:plate_tectonics" "Plate tectonics: unifying theory of Earth's lithosphere, accepted by the scientific community in the 1960s; explains earthquakes, volcanism, mountain building, ocean basin formation, and continental configurations through the movement of rigid lithospheric plates."
ln geo:concept:plate_tectonics geo:concept:continental_drift @supersedes
set.add name="ontology.tectonic_plates" id="geo:concept:plate_tectonics"

def "geo:concept:pangaea" "Pangaea: supercontinent that existed approximately 335–175 Ma, formed by collision of Gondwana and Laurasia; began rifting ~200 Ma; its breakup produced the current continental arrangement; concept central to plate tectonics."
ln geo:concept:pangaea geo:concept:continental_drift @evidences
set.add name="ontology.tectonic_plates" id="geo:concept:pangaea"

def "geo:concept:ring_of_fire" "Ring of Fire: horseshoe-shaped zone ~40,000 km long encircling the Pacific Plate and its neighbouring plates; hosts ~75% of Earth's active volcanoes and ~90% of the world's earthquakes; driven by subduction of Pacific, Nazca, Cocos, Juan de Fuca, and Philippine plates."
ln geo:concept:ring_of_fire geo:plate:pacific @surrounds
set.add name="ontology.tectonic_plates" id="geo:concept:ring_of_fire"
