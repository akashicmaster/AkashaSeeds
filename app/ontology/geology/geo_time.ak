# geo_time.ak
# Geological Time Scale — International Commission on Stratigraphy (ICS) 2024
# https://stratigraphy.org/ — Public domain
#

# ─── EONS ───────────────────────────────────────────────────────────────────

def "geo:time:eon:hadean" "Hadean Eon (4,600–4,031 Ma): Earth's formation and early differentiation; no rocks preserved; Moon-forming giant impact (~4,500 Ma); late heavy bombardment."
al geo:time:eon:hadean geo:time:eon:hadean:alias
set.add name="ontology.geological_time" id="geo:time:eon:hadean"

def "geo:time:eon:archean" "Archean Eon (4,031–2,500 Ma): oldest surviving rocks; origin of first life (prokaryotes); reducing atmosphere; earliest cratons form."
set.add name="ontology.geological_time" id="geo:time:eon:archean"

def "geo:time:eon:proterozoic" "Proterozoic Eon (2,500–538.8 Ma): first eukaryotes (~1,800 Ma); snowball Earth glaciations; first multicellular life; Great Oxidation Event transforms atmosphere."
set.add name="ontology.geological_time" id="geo:time:eon:proterozoic"

def "geo:time:eon:phanerozoic" "Phanerozoic Eon (538.8 Ma–present): eon of visible animal life; encompasses Paleozoic, Mesozoic, and Cenozoic eras."
set.add name="ontology.geological_time" id="geo:time:eon:phanerozoic"

# ─── ARCHEAN ERAS ───────────────────────────────────────────────────────────

def "geo:time:era:eoarchean" "Eoarchean Era (4,031–3,600 Ma): earliest Archean; Isua Greenstone Belt (oldest known rocks ~3,800 Ma); no confirmed life."
ln geo:time:era:eoarchean geo:time:eon:archean sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:eoarchean"

def "geo:time:era:paleoarchean" "Paleoarchean Era (3,600–3,200 Ma): possible earliest microbial life; oldest known stromatolites (~3,480 Ma, Pilbara, Australia)."
ln geo:time:era:paleoarchean geo:time:eon:archean sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:paleoarchean"

def "geo:time:era:mesoarchean" "Mesoarchean Era (3,200–2,800 Ma): continental crust growth; widespread stromatolites; early plate tectonic activity."
ln geo:time:era:mesoarchean geo:time:eon:archean sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:mesoarchean"

def "geo:time:era:neoarchean" "Neoarchean Era (2,800–2,500 Ma): cratonisation peaks; diverse microbial mat communities; transition to Great Oxidation Event."
ln geo:time:era:neoarchean geo:time:eon:archean sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:neoarchean"

# ─── PROTEROZOIC ERAS AND PERIODS ───────────────────────────────────────────

def "geo:time:era:paleoproterozoic" "Paleoproterozoic Era (2,500–1,600 Ma): Great Oxidation Event (~2,400 Ma) transforms atmosphere to oxygen-rich; first eukaryotes appear late in era."
ln geo:time:era:paleoproterozoic geo:time:eon:proterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:paleoproterozoic"

def "geo:time:period:siderian" "Siderian Period (2,500–2,300 Ma): opening period of Paleoproterozoic; iron formations abundant; Great Oxidation Event begins."
ln geo:time:period:siderian geo:time:era:paleoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:siderian"

def "geo:time:period:rhyacian" "Rhyacian Period (2,300–2,050 Ma): Huronian glaciation (earliest known snowball Earth event); continued banded iron formations."
ln geo:time:period:rhyacian geo:time:era:paleoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:rhyacian"

def "geo:time:period:orosirian" "Orosirian Period (2,050–1,800 Ma): major orogenic (mountain-building) events worldwide; Penokean and Trans-Hudson orogeny."
ln geo:time:period:orosirian geo:time:era:paleoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:orosirian"

def "geo:time:period:statherian" "Statherian Period (1,800–1,600 Ma): stabilisation of cratons; first confirmed eukaryotic fossils; supercontinent Columbia (Nuna) assembles."
ln geo:time:period:statherian geo:time:era:paleoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:statherian"

def "geo:time:era:mesoproterozoic" "Mesoproterozoic Era (1,600–1,000 Ma): supercontinent Rodinia assembles; early sexual reproduction; diversification of eukaryotes."
ln geo:time:era:mesoproterozoic geo:time:eon:proterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:mesoproterozoic"

def "geo:time:period:calymmian" "Calymmian Period (1,600–1,400 Ma): platform covers expand on cratons; early eukaryote diversification."
ln geo:time:period:calymmian geo:time:era:mesoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:calymmian"

def "geo:time:period:ectasian" "Ectasian Period (1,400–1,200 Ma): extension of platform covers; red algae appear; Rodinia assembly continues."
ln geo:time:period:ectasian geo:time:era:mesoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:ectasian"

def "geo:time:period:stenian" "Stenian Period (1,200–1,000 Ma): narrow mobile belts form; Grenville orogeny builds mountains; Rodinia largely assembled by end."
ln geo:time:period:stenian geo:time:era:mesoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:stenian"

def "geo:time:era:neoproterozoic" "Neoproterozoic Era (1,000–538.8 Ma): Rodinia breaks up; Snowball Earth glaciations; Ediacaran fauna — first complex multicellular animals."
ln geo:time:era:neoproterozoic geo:time:eon:proterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:neoproterozoic"

def "geo:time:period:tonian" "Tonian Period (1,000–720 Ma): Rodinia rifts apart; early evolution of animal-grade multicellularity; first acritarchs diversify."
ln geo:time:period:tonian geo:time:era:neoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:tonian"

def "geo:time:period:cryogenian" "Cryogenian Period (720–635 Ma): Snowball Earth events (Sturtian ~717 Ma, Marinoan ~635 Ma); global glaciation to equator; carbon isotope excursions."
ln geo:time:period:cryogenian geo:time:era:neoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:cryogenian"

def "geo:time:period:ediacaran" "Ediacaran Period (635–538.8 Ma): first complex macroscopic multicellular organisms (Ediacara biota); first animals with bilateral symmetry; Cambrian explosion precursor."
ln geo:time:period:ediacaran geo:time:era:neoproterozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:ediacaran"

# ─── PALEOZOIC ERA AND PERIODS ───────────────────────────────────────────────

def "geo:time:era:paleozoic" "Paleozoic Era (538.8–251.9 Ma): explosion of animal life in seas; colonisation of land by plants, invertebrates, and vertebrates; ends with largest mass extinction in Earth history."
ln geo:time:era:paleozoic geo:time:eon:phanerozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:paleozoic"

def "geo:time:period:cambrian" "Cambrian Period (538.8–485.4 Ma): Cambrian explosion — rapid diversification of most animal phyla; trilobites, brachiopods, echinoderms; Burgess Shale fauna."
ln geo:time:period:cambrian geo:time:era:paleozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:cambrian"

def "geo:time:period:ordovician" "Ordovician Period (485.4–443.8 Ma): great marine invertebrate diversification; first vertebrate fish; ends with Late Ordovician mass extinction (second largest)."
ln geo:time:period:ordovician geo:time:era:paleozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:ordovician"

def "geo:time:period:silurian" "Silurian Period (443.8–419.2 Ma): recovery from Ordovician extinction; first vascular plants colonise land; first jawed fish (gnathostomes); coral reefs widespread."
ln geo:time:period:silurian geo:time:era:paleozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:silurian"

def "geo:time:period:devonian" "Devonian Period (419.2–358.9 Ma): Age of Fishes; first amphibians venture onto land; first forests (Archaeopteris); Late Devonian mass extinction."
ln geo:time:period:devonian geo:time:era:paleozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:devonian"

def "geo:time:period:carboniferous" "Carboniferous Period (358.9–298.9 Ma): vast coal swamp forests (source of most coal deposits); first reptiles; first winged insects; Pangaea begins to assemble."
ln geo:time:period:carboniferous geo:time:era:paleozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:carboniferous"

def "geo:time:period:mississippian" "Mississippian Sub-period (358.9–323.2 Ma): early Carboniferous; abundant crinoids and calamitiean trees; widespread shallow seas in North America."
ln geo:time:period:mississippian geo:time:period:carboniferous sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:mississippian"

def "geo:time:period:pennsylvanian" "Pennsylvanian Sub-period (323.2–298.9 Ma): late Carboniferous; coal-forming swamp forests peak; first reptiles; major glaciations in southern Gondwana."
ln geo:time:period:pennsylvanian geo:time:period:carboniferous sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:pennsylvanian"

def "geo:time:period:permian" "Permian Period (298.9–251.9 Ma): Pangaea fully assembled; diverse reptile fauna; ends with Permian–Triassic mass extinction (96% of species lost — largest in Earth history)."
ln geo:time:period:permian geo:time:era:paleozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:permian"

# ─── MESOZOIC ERA AND PERIODS ────────────────────────────────────────────────

def "geo:time:era:mesozoic" "Mesozoic Era (251.9–66 Ma): Age of Reptiles; dinosaurs dominant; first mammals, first birds, first flowering plants; Pangaea breaks up; ends with K-Pg mass extinction."
ln geo:time:era:mesozoic geo:time:eon:phanerozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:mesozoic"

def "geo:time:period:triassic" "Triassic Period (251.9–201.4 Ma): recovery from Permian extinction; first dinosaurs (~230 Ma); first mammals; Pangaea begins to rift; ends with Triassic–Jurassic extinction."
ln geo:time:period:triassic geo:time:era:mesozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:triassic"

def "geo:time:period:jurassic" "Jurassic Period (201.4–145 Ma): giant sauropod dinosaurs; Archaeopteryx (first bird, ~150 Ma); Pangaea fully splits into Laurasia and Gondwana; ammonites widespread."
ln geo:time:period:jurassic geo:time:era:mesozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:jurassic"

def "geo:time:period:cretaceous" "Cretaceous Period (145–66 Ma): flowering plants (angiosperms) radiate; peak dinosaur diversity; chalk deposits; ends with K-Pg extinction (Chicxulub impact) wiping out non-avian dinosaurs."
ln geo:time:period:cretaceous geo:time:era:mesozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:cretaceous"

# ─── CENOZOIC ERA, PERIODS, AND EPOCHS ──────────────────────────────────────

def "geo:time:era:cenozoic" "Cenozoic Era (66 Ma–present): Age of Mammals; grasslands, modern ocean circulation, polar ice caps; hominins evolve; current era."
ln geo:time:era:cenozoic geo:time:eon:phanerozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:era:cenozoic"

def "geo:time:period:paleogene" "Paleogene Period (66–23.03 Ma): rapid mammal diversification following K-Pg extinction; greenhouse climate; Tethys Sea closes; India collides with Asia."
ln geo:time:period:paleogene geo:time:era:cenozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:paleogene"

def "geo:time:epoch:paleocene" "Paleocene Epoch (66–56 Ma): mammal diversification and radiation after K-Pg extinction; archaic mammal orders dominate; no grasses yet; warm climate."
ln geo:time:epoch:paleocene geo:time:period:paleogene sys:part_of
set.add name="ontology.geological_time" id="geo:time:epoch:paleocene"

def "geo:time:epoch:eocene" "Eocene Epoch (56–33.9 Ma): warm greenhouse climate (Eocene Optimum); first grasses; first whales (archaeocetes); India-Asia collision begins Himalayan uplift; ends with Grande Coupure cooling."
ln geo:time:epoch:eocene geo:time:period:paleogene sys:part_of
set.add name="ontology.geological_time" id="geo:time:epoch:eocene"

def "geo:time:epoch:oligocene" "Oligocene Epoch (33.9–23.03 Ma): global cooling; Antarctic glaciation begins; grasslands expand; modern mammal orders consolidate; Drake Passage opens."
ln geo:time:epoch:oligocene geo:time:period:paleogene sys:part_of
set.add name="ontology.geological_time" id="geo:time:epoch:oligocene"

def "geo:time:period:neogene" "Neogene Period (23.03–2.58 Ma): continued cooling and drying; C4 grass expansion; great ape diversification; Panama Isthmus closes (~3 Ma); Arctic ice cap forms."
ln geo:time:period:neogene geo:time:era:cenozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:neogene"

def "geo:time:epoch:miocene" "Miocene Epoch (23.03–5.33 Ma): great apes diversify; kelp forests appear; C4 grasses spread; Tethys Sea dries (Messinian salinity crisis); African-Eurasian land bridge."
ln geo:time:epoch:miocene geo:time:period:neogene sys:part_of
set.add name="ontology.geological_time" id="geo:time:epoch:miocene"

def "geo:time:epoch:pliocene" "Pliocene Epoch (5.33–2.58 Ma): hominins evolve (Australopithecus, early Homo); Arctic ice cap forms; Mediterranean refills; global cooling accelerates."
ln geo:time:epoch:pliocene geo:time:period:neogene sys:part_of
set.add name="ontology.geological_time" id="geo:time:epoch:pliocene"

def "geo:time:period:quaternary" "Quaternary Period (2.58 Ma–present): repeated glacial-interglacial cycles; megafauna extinctions; evolution and global spread of Homo sapiens; current period."
ln geo:time:period:quaternary geo:time:era:cenozoic sys:part_of
set.add name="ontology.geological_time" id="geo:time:period:quaternary"

def "geo:time:epoch:pleistocene" "Pleistocene Epoch (2.58 Ma–11,700 ya): ice ages with up to 20 glacial cycles; woolly mammoths, sabretooth cats, giant ground sloths; Homo sapiens evolves (~300,000 ya) and spreads globally."
ln geo:time:epoch:pleistocene geo:time:period:quaternary sys:part_of
set.add name="ontology.geological_time" id="geo:time:epoch:pleistocene"

def "geo:time:epoch:holocene" "Holocene Epoch (11,700 ya–present): current warm interglacial; end of most Pleistocene megafauna; rise of agriculture (~10,000 ya) and human civilisation; ongoing."
ln geo:time:epoch:holocene geo:time:period:quaternary sys:part_of
set.add name="ontology.geological_time" id="geo:time:epoch:holocene"

# Note: Anthropocene proposed by IUCN/Anthropocene Working Group but not formally ratified
# by ICS as of 2024; not included as a formal unit.
