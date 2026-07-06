# Akasha ontology — namespace: sci
# atoms: 78

def "sci:archaeo:chichen_itza" "At Chichen Itza, on the afternoons of the equinoxes, the stepped edge of the great pyramid throws a zigzag of light and shadow down the side of the northern stair, joining a carved serpent's head at its foot — and the Feathered Serpent, Kukulkan, seems to descend the temple. Astronomy, architecture, and the god made one. — archaeoastronomy (Maya)"
ln sci:archaeo:chichen_itza myth:archaeoastronomy sys:part_of
ln sci:archaeo:chichen_itza deity:quetzalcoatl @related_to
ln sci:archaeo:chichen_itza sun @related_to
set.add name="ontology.archaeoastronomy" id="sci:archaeo:chichen_itza"

def "sci:archaeo:giza_orion_thuban" "The Great Pyramid of Giza is squared to the four directions with astonishing precision, and its narrow shafts point to the sky: south toward the belt of Orion, the stars of Osiris, and north toward Thuban, the pole star of that age. The pharaoh's tomb aimed at the stars of the afterlife. — archaeoastronomy"
ln sci:archaeo:giza_orion_thuban myth:archaeoastronomy sys:part_of
ln sci:archaeo:giza_orion_thuban astro:constellation:orion @related_to
ln sci:archaeo:giza_orion_thuban word:ar:الثعبان @related_to
ln sci:archaeo:giza_orion_thuban deity:osiris @related_to
set.add name="ontology.archaeoastronomy" id="sci:archaeo:giza_orion_thuban"

def "sci:archaeo:maya_venus_tables" "The Maya bound their astronomy into their sacred books: the Dresden Codex holds tables that track and foretell the motions of Venus over centuries with great precision, timing its risings — the warlike star of Kukulkan — to ritual and to war. A calendar of the sky kept in a painted book. — archaeoastronomy (Maya)"
ln sci:archaeo:maya_venus_tables myth:archaeoastronomy sys:part_of
ln sci:archaeo:maya_venus_tables venus @related_to
ln sci:archaeo:maya_venus_tables myth:maya_venus @related_to
set.add name="ontology.archaeoastronomy" id="sci:archaeo:maya_venus_tables"

def "sci:archaeo:nebra_disc" "The Nebra sky-disc, a bronze disc some three and a half thousand years old, shows in gold the sun or full moon, the crescent moon, and a little cluster of seven stars — the Pleiades — perhaps a device to reconcile the moon's months with the sun's year. The oldest known image of the heavens. — archaeoastronomy"
ln sci:archaeo:nebra_disc myth:archaeoastronomy sys:part_of
ln sci:archaeo:nebra_disc pleiades @related_to
ln sci:archaeo:nebra_disc astro:constellation:taurus @related_to
set.add name="ontology.archaeoastronomy" id="sci:archaeo:nebra_disc"

def "sci:archaeo:newgrange" "At Newgrange in Ireland, a passage tomb older than the pyramids, a slot above the door is set so that on the midwinter dawn — and only then — the rising sun pours straight down the long passage to flood the inner chamber with light. The shortest day, caught and kept in stone. — archaeoastronomy"
ln sci:archaeo:newgrange myth:archaeoastronomy sys:part_of
ln sci:archaeo:newgrange solstice @explains
ln sci:archaeo:newgrange sun @related_to
set.add name="ontology.archaeoastronomy" id="sci:archaeo:newgrange"

def "sci:archaeo:stonehenge" "Stonehenge, raised on Salisbury Plain across centuries around five thousand years ago, stands aligned to the midsummer sunrise and the midwinter sunset: a calendar in stone, by which the year's great turnings could be marked from the ring itself. — archaeoastronomy"
ln sci:archaeo:stonehenge myth:archaeoastronomy sys:part_of
ln sci:archaeo:stonehenge solstice @explains
ln sci:archaeo:stonehenge sun @related_to
set.add name="ontology.archaeoastronomy" id="sci:archaeo:stonehenge"

def "sci:astro:dark_nebulae" "The dark rifts in the Milky Way are not empty but full: clouds of dust in the galactic plane that block the starlight behind them. The peoples who drew their constellations in the DARK — the Aboriginal Emu, the Inca dark Llama — were tracing the real dust-lanes of our galaxy, reading structure no telescope yet named."
ln sci:astro:dark_nebulae myth:aboriginal_emu_sky @grounds
ln sci:astro:dark_nebulae myth:inca_dark_llama @grounds
ln sci:astro:dark_nebulae milky_way sys:related_to
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:dark_nebulae"

def "sci:astro:eclipse_mechanism" "An eclipse is only a shadow: the Moon between Sun and Earth, or the Earth's shadow on the Moon, in a brief alignment. The very Babylonians whose myths told of a sky-beast devouring the Sun also tracked the eighteen-year saros and PREDICTED these alignments — myth and reckoning held in the same hands."
ln sci:astro:eclipse_mechanism eclipse @explains
ln sci:astro:eclipse_mechanism myth:hindu_rahu @grounds
ln sci:astro:eclipse_mechanism myth:babylonian_sky_origin @grounds
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:eclipse_mechanism"

def "sci:astro:ecliptic_zodiac_plane" "The planets keep to the narrow band of the zodiac because the solar system is nearly flat: the Sun, Moon, and planets all ride close to one plane, the ecliptic, and the zodiac is that plane drawn against the far stars. The circle of beasts the Babylonians marked is the edge of our own planetary disc, seen from inside."
ln sci:astro:ecliptic_zodiac_plane zodiac @explains
ln sci:astro:ecliptic_zodiac_plane myth:babylonian_sky_origin @grounds
ln sci:astro:ecliptic_zodiac_plane word:he:מזרות @grounds
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:ecliptic_zodiac_plane"

def "sci:astro:galactic_center_sagittarius" "The crowded heart of our galaxy lies in the direction of Sagittarius, where the Milky Way is brightest and thickest with stars. The Archer's drawn bow points, all unknowing, at the centre of the galaxy — and there shines Nunki, the one star-name to survive from Sumer, marking the way to our galaxy's core."
ln sci:astro:galactic_center_sagittarius word:akk:nunki @grounds
ln sci:astro:galactic_center_sagittarius astro:constellation:sagittarius @explains
ln sci:astro:galactic_center_sagittarius milky_way sys:related_to
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:galactic_center_sagittarius"

def "sci:astro:impact_events" "Comets and asteroids do strike the Earth: the Tunguska blast flattened a Siberian forest in 1908, Meteor Crater scars Arizona, and the Chicxulub impact ended the age of the dinosaurs. The dread the comet carried as an omen of doom had, at bottom, a real ground — fire does sometimes fall from the sky. — earth science"
ln sci:astro:impact_events comet @explains
ln sci:astro:impact_events myth:comet_omen @grounds
ln sci:astro:impact_events myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:astro:impact_events"

def "sci:astro:mars_iron_oxide" "Mars is red because its surface is rusted — iron oxide in the dust. The colour that led Rome to name it for the war-god, and led the Greeks to call the rival red star Antares the 'anti-Ares', is the plain chemistry of rust."
ln sci:astro:mars_iron_oxide word:la:mars @grounds
ln sci:astro:mars_iron_oxide word:la:antares @grounds
ln sci:astro:mars_iron_oxide mars @explains
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:mars_iron_oxide"

def "sci:astro:mercury_orbit" "Mercury is the innermost planet, racing round the Sun in only eighty-eight days, never seen far from it in dawn or dusk. The ancients named it for the swift-footed messenger god without knowing its orbit — yet the name caught the very fact: it is the fastest wanderer of all."
ln sci:astro:mercury_orbit word:la:mercury @grounds
ln sci:astro:mercury_orbit mercury @explains
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:mercury_orbit"

def "sci:astro:milky_way_galaxy" "The pale band across the sky is the disc of our own galaxy seen edge-on from within — hundreds of billions of stars. Galileo's telescope first dissolved the milk into uncountable points of light. And the science kept the myth's word: galaxy, from the Greek for milk, the milk of Hera still in the name."
ln sci:astro:milky_way_galaxy milky_way @explains
ln sci:astro:milky_way_galaxy myth:greek_milky_way @grounds
ln sci:astro:milky_way_galaxy word:en:galaxy @grounds
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:milky_way_galaxy"

def "sci:astro:saturn_rings_slow" "Saturn, ringed with ice and rock, takes nearly thirty years to plod once round the Sun — the slowest wanderer the naked eye can follow. The old, slow god of time the ancients matched to it was matched to the truth: it is the farthest of the classical planets."
ln sci:astro:saturn_rings_slow word:la:saturn @grounds
ln sci:astro:saturn_rings_slow saturn @explains
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:saturn_rings_slow"

def "sci:astro:solar_storms" "The Sun hurls out great flares and storms of charged particles. The Carrington Event of 1859 lit auroras as far as the tropics and set telegraph wires sparking; and the rings of old trees record even mightier blasts in the years 774 and 993, when blood-red skies were seen and written into the chronicles. The omen-light in the heavens was sometimes the Sun's own violence. — earth science"
ln sci:astro:solar_storms aurora @explains
ln sci:astro:solar_storms myth:aurora_spirits @grounds
ln sci:astro:solar_storms myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:astro:solar_storms"

def "sci:astro:sun_is_a_star" "The Sun is a star: a sphere of plasma fusing hydrogen into helium in its core, the energy of that fusion the light and heat of every day. It is one ordinary star among the hundreds of billions of our galaxy — the god the myths crowned is a main-sequence star."
ln sci:astro:sun_is_a_star sun @explains
ln sci:astro:sun_is_a_star word:la:sol @grounds
ln sci:astro:sun_is_a_star deity:helios @grounds
ln sci:astro:sun_is_a_star stars sys:is_a
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:sun_is_a_star"

def "sci:astro:variable_stars" "Some stars truly change. Algol dims every few days because a dark companion eclipses it — and the Arabs had named it Ras al-Ghul, the Demon's Head, the winking star. Mira fades and returns as it pulses, and was named 'the Wonderful'. Eta Carinae erupted in the 1840s — and the Boorong had a name for that red star. The names caught the change before the physics could."
ln sci:astro:variable_stars astro:star:algol @grounds
ln sci:astro:variable_stars word:la:mira @grounds
ln sci:astro:variable_stars word:wdj:collowgullouric_war @grounds
ln sci:astro:variable_stars stars sys:related_to
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:variable_stars"

def "sci:astro:venus_inferior_orbit" "Venus circles the Sun inside Earth's own orbit, so it never strays far from the Sun and shows as either a morning or an evening star — which is why the Greeks' two stars, Phosphoros and Hesperos, are one. The puzzle the ancients solved by guess, orbital geometry settles: a single brilliant world, the hottest, wrapped in a runaway greenhouse."
ln sci:astro:venus_inferior_orbit venus @explains
ln sci:astro:venus_inferior_orbit myth:greek_venus_twin @grounds
ln sci:astro:venus_inferior_orbit word:la:venus @grounds
set.add name="ontology.astronomy_myth_nexus" id="sci:astro:venus_inferior_orbit"

def "sci:bio:epidemic_disease" "Epidemics are the work of microbes that leap from animals to people and spread unseen; ancient DNA has now named the killers — the bacterium Yersinia pestis behind both the Black Death and the Plague of Justinian. The arrows of a plague-god, and the stalking figure of Death, were the face a people gave to a contagion they could not see. — biology / history"
ln sci:bio:epidemic_disease plague @explains
ln sci:bio:epidemic_disease myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:bio:epidemic_disease"

def "sci:cook:caramelization" "The browning of sugar, a process used extensively in cooking for the resulting sweet nutty flavor and brown color."
ln sci:cook:caramelization culinary_science.thermal sys:is_a
ln sci:cook:caramelization cook:temp:searing_hot @requires
ln sci:cook:caramelization verb:cook:caramelize sys:refers_to
ln sci:cook:caramelization dna:taste:sweet calc:associated_with
ln sci:cook:caramelization dna:taste:bitter calc:associated_with
set.add name="ontology.culinary_science" id="sci:cook:caramelization"

def "sci:cook:coagulation" "The transformation of proteins from a liquid state to a solid form."
ln sci:cook:coagulation culinary_science.thermal sys:is_a
ln sci:cook:coagulation sci:cook:protein_denaturation @follows
set.add name="ontology.culinary_science" id="sci:cook:coagulation"

def "sci:cook:emulsification" "The process of forcing two immiscible liquids (like oil and water) to combine in a suspension."
ln sci:cook:emulsification culinary_science.physical sys:is_a
ln sci:cook:emulsification verb:cook:emulsify sys:refers_to
ln sci:cook:emulsification sci:cook:emulsion @creates
ln sci:cook:emulsification dna:texture:smooth calc:associated_with
set.add name="ontology.culinary_science" id="sci:cook:emulsification"

def "sci:cook:emulsion" "A mixture of two or more liquids that are normally unblendable."
ln sci:cook:emulsion culinary_science.functional sys:is_a
set.add name="ontology.culinary_science" id="sci:cook:emulsion"

def "sci:cook:enzymatic_browning" "An oxidation reaction that takes place in some foods, mostly fruit and vegetables, causing them to turn brown."
ln sci:cook:enzymatic_browning culinary_science.physical sys:is_a
ln sci:cook:enzymatic_browning dna:color:red calc:associated_with
set.add name="ontology.culinary_science" id="sci:cook:enzymatic_browning"

def "sci:cook:gelatinization" "The process where starch and water are subjected to heat, causing the starch granules to swell."
ln sci:cook:gelatinization culinary_science.thermal sys:is_a
ln sci:cook:gelatinization verb:cook:simmer sys:refers_to
ln sci:cook:gelatinization dna:texture:viscous calc:associated_with
set.add name="ontology.culinary_science" id="sci:cook:gelatinization"

def "sci:cook:hydrocolloid" "A substance that forms a gel in the presence of water, used for thickening and gelling."
ln sci:cook:hydrocolloid culinary_science.functional sys:is_a
set.add name="ontology.culinary_science" id="sci:cook:hydrocolloid"

def "sci:cook:maillard_reaction" "Chemical reaction between amino acids and reducing sugars that gives browned food its distinctive flavor."
ln sci:cook:maillard_reaction culinary_science.thermal sys:is_a
ln sci:cook:maillard_reaction cook:temp:searing_hot @requires
ln sci:cook:maillard_reaction verb:cook:sear sys:refers_to
ln sci:cook:maillard_reaction verb:cook:roast sys:refers_to
ln sci:cook:maillard_reaction dna:taste:umami calc:associated_with
set.add name="ontology.culinary_science" id="sci:cook:maillard_reaction"

def "sci:cook:osmosis" "The movement of solvent molecules through a semipermeable membrane into a region of higher solute concentration."
ln sci:cook:osmosis culinary_science.physical sys:is_a
ln sci:cook:osmosis verb:cook:brine sys:refers_to
ln sci:cook:osmosis verb:cook:cure sys:refers_to
set.add name="ontology.culinary_science" id="sci:cook:osmosis"

def "sci:cook:ph_level" "A measure of acidity or alkalinity of water soluble substances."
ln sci:cook:ph_level culinary_science.functional sys:is_a
ln sci:cook:ph_level sci:cook:enzymatic_browning @moderates
set.add name="ontology.culinary_science" id="sci:cook:ph_level"

def "sci:cook:protein_denaturation" "The alteration of a protein shape through some form of external stress (e.g., heat, acid)."
ln sci:cook:protein_denaturation culinary_science.thermal sys:is_a
ln sci:cook:protein_denaturation verb:cook:boil sys:refers_to
ln sci:cook:protein_denaturation verb:cook:marinate sys:refers_to
set.add name="ontology.culinary_science" id="sci:cook:protein_denaturation"

def "sci:cook:retrogradation" "A reaction where amylose and amylopectin chains in cooked, gelatinized starch realign as they cool."
ln sci:cook:retrogradation culinary_science.thermal sys:is_a
ln sci:cook:retrogradation dna:texture:hard calc:associated_with
ln sci:cook:retrogradation cook:temp:chilled @requires
set.add name="ontology.culinary_science" id="sci:cook:retrogradation"

def "sci:cook:spherification" "The culinary process of shaping a liquid into spheres which visually and texturally resemble roe."
ln sci:cook:spherification culinary_science.physical sys:is_a
ln sci:cook:spherification sci:cook:hydrocolloid @requires
ln sci:cook:spherification dna:texture:soft calc:associated_with
set.add name="ontology.culinary_science" id="sci:cook:spherification"

def "sci:geo:black_sea_flood" "By one debated hypothesis, the Mediterranean broke through the Bosphorus some seven and a half thousand years ago and flooded the freshwater basin that became the Black Sea, drowning its shores within a lifetime — a candidate for the catastrophe behind the Near-Eastern flood. The claim is contested, but the basin did flood. — earth science (hypothesis)"
ln sci:geo:black_sea_flood flood @explains
ln sci:geo:black_sea_flood myth:mesopotamian_flood @grounds
set.add name="ontology.geomyth_nexus" id="sci:geo:black_sea_flood"

def "sci:geo:deglaciation_floods" "When the last Ice Age ended, the melting ice sheets raised the sea some hundred and twenty metres over a few thousand years, drowning coastlines and land bridges all around the world and driving peoples from lands now under water. A real, near-global memory of rising waters may underlie why the flood is told almost everywhere. — earth science"
ln sci:geo:deglaciation_floods flood @explains
ln sci:geo:deglaciation_floods myth:world_flood_myths @grounds
set.add name="ontology.geomyth_nexus" id="sci:geo:deglaciation_floods"

def "sci:geo:earthquake_tectonics" "An earthquake is the sudden slip of the great plates of the Earth's crust along a fault, releasing strain stored in the rock. The shaking that myth gave to a bound giant, a buried beast, or an angry god is the ground itself letting go. — earth science"
ln sci:geo:earthquake_tectonics earthquake @explains
ln sci:geo:earthquake_tectonics myth:loki_baldr_death @grounds
ln sci:geo:earthquake_tectonics deity:poseidon @grounds
set.add name="ontology.geomyth_nexus" id="sci:geo:earthquake_tectonics"

def "sci:geo:event_4200" "Around 2200 BCE a severe drought, lasting generations, fell across much of the world: the Akkadian Empire collapsed, Egypt's Old Kingdom broke apart, and the cities of the Indus declined. This 4.2-kiloyear event is one of the sharpest climate blows in the human record — and it struck just as the old powers fell. — earth science"
ln sci:geo:event_4200 drought @explains
ln sci:geo:event_4200 famine @explains
ln sci:geo:event_4200 myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:geo:event_4200"

def "sci:geo:fossils_as_monsters" "The bones of long-dead creatures, weathering out of the rock, were read by the ancients as the remains of giants, dragons, and monsters. The griffin may be born from the beaked, four-legged skeletons of Protoceratops in the gold-bearing deserts of the East; the one-eyed Cyclops from the great central nasal cavity of dwarf-elephant skulls in Mediterranean caves; and China's 'dragon bones', ground for medicine, are the fossils of dinosaurs and ancient beasts. — earth science / folklore"
ln sci:geo:fossils_as_monsters fossil @explains
ln sci:geo:fossils_as_monsters giant @grounds
ln sci:geo:fossils_as_monsters myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:geo:fossils_as_monsters"

def "sci:geo:shuruppak_flood_layer" "The spade gives a humbler witness: in the old Sumerian cities the archaeologists found thick bands of river-laid silt from great floods of the Tigris and Euphrates — including at Shuruppak, the very city the king-lists name as the home of Ziusudra, the flood-hero behind Utnapishtim. A real flood-layer beneath the flood-king's town. — archaeology"
ln sci:geo:shuruppak_flood_layer flood @explains
ln sci:geo:shuruppak_flood_layer myth:mesopotamian_flood @grounds
set.add name="ontology.geomyth_nexus" id="sci:geo:shuruppak_flood_layer"

def "sci:geo:tsunami_science" "A tsunami is a great wave raised by an undersea earthquake or landslide, that can cross an ocean and swallow a coast in minutes. A legend of the sea suddenly rising and devouring the land may be the memory of a real one. — earth science"
ln sci:geo:tsunami_science tsunami @explains
set.add name="ontology.geomyth_nexus" id="sci:geo:tsunami_science"

def "sci:geo:volcanism" "A volcano is the Earth's molten interior breaking through the crust, in lava, ash, and fire. The fire-mountain that myth made a smith-god's forge or a buried monster's breath is rising magma. — earth science"
ln sci:geo:volcanism volcano @explains
ln sci:geo:volcanism deity:hephaestus @grounds
set.add name="ontology.geomyth_nexus" id="sci:geo:volcanism"

def "sci:history:age_of_discovery" "A period from the 15th to 17th century during which European ships traveled around the world to search for new trading routes and partners."
ln sci:history:age_of_discovery sci:history:columbian_exchange @triggers

def "sci:history:alchemy" "An ancient branch of natural philosophy, a philosophical and protoscientific tradition historically practiced in China, India, the Muslim world, and Europe."
ln sci:history:alchemy sci:history:chemical_revolution @precedes

def "sci:history:bronze_age_collapse" "Around 1200 BCE drought and upheaval and the raiding Sea Peoples toppled the great kingdoms of the eastern Mediterranean almost at once — Mycenae, the Hittites, Ugarit — and Greece fell into a dark age. The memory of that lost heroic world, dimly kept, became the songs of Troy. — history"
ln sci:history:bronze_age_collapse drought @explains
ln sci:history:bronze_age_collapse myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:history:bronze_age_collapse"

def "sci:history:chemical_revolution" "The early modern reformulation of chemistry that culminated in the law of conservation of mass and the oxygen theory of combustion."
ln sci:history:chemical_revolution sci:history:modern_chemistry @initiates
ln sci:history:chemical_revolution chem:theory:conservation_of_mass @establishes

def "sci:history:chinese_alchemy" "The ancient Chinese practice of alchemy, primarily focused on finding the elixir of immortality, which accidentally led to the invention of gunpowder."
ln sci:history:chinese_alchemy sci:history:alchemy sys:is_a
ln sci:history:chinese_alchemy tech:concept:gunpowder @discovers_accidentally

def "sci:history:columbian_exchange" "The widespread transfer of plants, animals, culture, human populations, technology, and ideas between the Americas and the Old World in the 15th and 16th centuries."
ln sci:history:columbian_exchange agri:crop:potato @transmits_globally
ln sci:history:columbian_exchange agri:crop:maize @transmits_globally
ln sci:history:columbian_exchange agri:crop:sweet_potato @transmits_globally
ln sci:history:columbian_exchange agri:crop:chili_pepper @transmits_globally

def "sci:history:copernican_revolution" "Copernicus, Kepler, and Galileo moved the Earth from the centre and set the Sun there, the planets wheeling round it on their orbits. The wandering 'planet-gods' the ancients named became worlds — and the heavens stopped turning about us."
ln sci:history:copernican_revolution word:en:planet @grounds
ln sci:history:copernican_revolution word:la:jupiter @grounds
set.add name="ontology.astronomy_myth_nexus" id="sci:history:copernican_revolution"

def "sci:history:electrification" "The process of powering by electricity and, in many contexts, the introduction of such power by changing over from an earlier power source."
ln sci:history:electrification sci:history:second_industrial_revolution @triggers

def "sci:history:event_536" "In 536 CE a veil of volcanic dust dimmed the sun for more than a year; the chroniclers wrote that it gave light without warmth, like the moon. Harvests failed across the world in a long cold, famine spread, and the great plague followed soon after — by some reckoning the worst year ever to be alive. — earth science / history"
ln sci:history:event_536 volcano @explains
ln sci:history:event_536 famine @explains
ln sci:history:event_536 myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:history:event_536"

def "sci:history:galileo_jupiter_moons" "In 1610 Galileo turned his telescope on Jupiter and saw four small moons circling it — plain proof that not everything turns about the Earth. The king of the planet-gods, named for sheer lordliness, proved indeed the greatest, with its own wheeling court that broke the old cosmos open."
ln sci:history:galileo_jupiter_moons word:la:jupiter @grounds
ln sci:history:galileo_jupiter_moons sci:history:copernican_revolution sys:part_of
set.add name="ontology.astronomy_myth_nexus" id="sci:history:galileo_jupiter_moons"

def "sci:history:halley_comet" "Edmond Halley reckoned that the comets of 1531, 1607, and 1682 were one body returning, and foretold its coming again in 1758. It came. With that, the comet ceased to be an omen of doom and became a clockwork visitor on a long, faithful orbit."
ln sci:history:halley_comet comet @explains
ln sci:history:halley_comet myth:comet_omen @grounds
set.add name="ontology.astronomy_myth_nexus" id="sci:history:halley_comet"

def "sci:history:halley_foretold" "Edmond Halley's comet is the model case: the dread hairy star, reckoned to be one body returning on a long orbit, and foretold to come again — and it came, in 1758, after his death. The omen kept its appointment like a clock, and was an omen no longer. — history of science"
ln sci:history:halley_foretold comet @related_to
ln sci:history:halley_foretold myth:comet_omen @grounds
ln sci:history:halley_foretold sci:history:halley_comet @related_to
ln sci:history:halley_foretold myth:omen_to_prediction sys:part_of
set.add name="ontology.foreknowledge" id="sci:history:halley_foretold"

def "sci:history:hippocratic_prognosis" "Hippocrates turned the healer from a reader of omens into a reader of the body: the 'sacred disease', epilepsy, he declared no more sacred than any other, having a natural cause; and he taught physicians the art of prognosis, to follow an illness and foretell its critical days. Disease became a natural course to be predicted, not a god's arrow to be appeased. — history of medicine"
ln sci:history:hippocratic_prognosis plague @related_to
ln sci:history:hippocratic_prognosis myth:apollo_plague @grounds
ln sci:history:hippocratic_prognosis sci:bio:epidemic_disease @related_to
ln sci:history:hippocratic_prognosis myth:omen_to_prediction sys:part_of
set.add name="ontology.foreknowledge" id="sci:history:hippocratic_prognosis"

def "sci:history:house_of_wisdom" "A major Abbasid public academy and intellectual center in Baghdad where many classical works were translated and mathematics advanced."
ln sci:history:house_of_wisdom math:discipline:algebra @develops
ln sci:history:house_of_wisdom math:concept:algorithm @develops
ln sci:history:house_of_wisdom sci:history:translation_movement @transmitted_via

def "sci:history:humorism" "A historic system of medicine detailing the makeup and workings of the human body, adopted by Ancient Greek and Roman physicians."
ln sci:history:humorism med:system:western_medicine @historical_basis_of

def "sci:history:industrial_revolution" "The transition to new manufacturing processes in Europe and the US, heavily reliant on a large urban workforce."
ln sci:history:industrial_revolution sci:history:second_industrial_revolution @precedes

def "sci:history:jet_age" "A period in the history of aviation defined by the advent of aircraft powered by turbine engines, leading to fast global travel."

def "sci:history:jogan_869" "The chronicles record the great Jogan earthquake and the wave that drowned the Sendai plain in 869. Centuries later, geologists reading its buried sand layers warned that such a tsunami could come again — a warning the Tohoku disaster of 2011 tragically fulfilled, almost exactly along the old line. — history / earth science"
ln sci:history:jogan_869 tsunami @explains
ln sci:history:jogan_869 earthquake @explains
ln sci:history:jogan_869 myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:history:jogan_869"

def "sci:history:liber_abaci" "A historic 1202 Latin manuscript on arithmetic by Fibonacci, which introduced the Hindu-Arabic numeral system to Western Europe."

def "sci:history:lisbon_1755" "On All Saints' Day, 1755, a great earthquake struck Lisbon, then a tsunami, then fire, killing tens of thousands. The shock ran through Europe's mind as much as its ground: it drove Voltaire and the philosophers to ask anew how a good God could allow such ruin, and it helped found the science of earthquakes. — history"
ln sci:history:lisbon_1755 earthquake @explains
ln sci:history:lisbon_1755 tsunami @explains
ln sci:history:lisbon_1755 myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:history:lisbon_1755"

def "sci:history:military_revolution" "The radical change in military strategy and tactics in early modern Europe resulting from the introduction of gunpowder weapons, leading to the decline of feudal castles and knights."

def "sci:history:modern_chemistry" "The evolution of chemistry into a quantitative physical science based on atoms, elements, and conservation laws."

def "sci:history:mongol_empire" "The largest contiguous land empire in history, which facilitated trade, cultural exchange, and the rapid spread of technologies like gunpowder across Eurasia."
ln sci:history:mongol_empire tech:weapon:fire_lance @encounters
ln sci:history:mongol_empire tech:concept:gunpowder @transmits_globally

def "sci:history:philosophers_stone" "A mythical alchemical substance capable of turning base metals such as lead into gold, or granting immortality."

def "sci:history:printing_revolution" "The introduction of mass production of information via the printing press in 15th-century Europe, fundamentally changing how knowledge was stored and shared."
ln sci:history:printing_revolution sci:history:translation_movement @accelerates_legacy_of

def "sci:history:second_industrial_revolution" "A phase of rapid standardization and industrialization from the late 19th century into the early 20th century, largely driven by electricity."

def "sci:history:song_dynasty_innovation" "The period in China when Bi Sheng invented the first known movable type system (initially using baked clay, later wood and metal)."
ln sci:history:song_dynasty_innovation tech:concept:woodblock_printing @refines
ln sci:history:song_dynasty_innovation tech:concept:movable_type @invents

def "sci:history:stars_are_distant_suns" "In 1838 Bessel measured the tiny yearly shift of the star 61 Cygni and found its distance — the first proof that the stars are other suns, unthinkably far. The heroes, beasts, and gods the myths fixed in the sky are suns scattered across light-years, each a Sun to worlds we cannot see."
ln sci:history:stars_are_distant_suns stars @explains
ln sci:history:stars_are_distant_suns sci:astro:sun_is_a_star sys:related_to
set.add name="ontology.astronomy_myth_nexus" id="sci:history:stars_are_distant_suns"

def "sci:history:storegga_doggerland" "Some eight thousand years ago the Storegga submarine landslide off Norway sent a tsunami sweeping across the North Sea, helping to drown Doggerland, the low country that had joined Britain to the continent. A real lost land beneath the waves, behind the world's many tales of sunken countries. — earth science"
ln sci:history:storegga_doggerland tsunami @explains
ln sci:history:storegga_doggerland flood @related_to
set.add name="ontology.geomyth_nexus" id="sci:history:storegga_doggerland"

def "sci:history:thales_eclipse" "Thales of Miletus is said to have foretold the solar eclipse that fell in 585 BCE upon a battle between the Medes and the Lydians; the day turned to night, and the armies, taking it for a sign, laid down their arms and made peace. The eclipse foreseen, not feared — knowledge standing where the omen stood. — history of science"
ln sci:history:thales_eclipse eclipse @explains
ln sci:history:thales_eclipse myth:omen_to_prediction sys:part_of
ln sci:history:thales_eclipse sci:astro:eclipse_mechanism @related_to
set.add name="ontology.foreknowledge" id="sci:history:thales_eclipse"

def "sci:history:thera_eruption" "Around the sixteenth century BCE the volcano of Thera (Santorini) erupted with shattering force, burying its city and convulsing the eastern Mediterranean as the Minoan world declined. Many have linked the memory of that catastrophe — debated, but real — to Plato's tale of Atlantis, the great island swallowed by the sea. — archaeology / earth science"
ln sci:history:thera_eruption volcano @explains
ln sci:history:thera_eruption myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:history:thera_eruption"

def "sci:history:translation_movement" "A large, well-funded effort during the Islamic Golden Age and later in medieval Spain/Italy to translate texts from Greek, Sanskrit, and Arabic into Latin."
ln sci:history:translation_movement sci:history:liber_abaci @influences

def "sci:history:transmutation" "The alchemical pursuit of turning base metals into noble metals like gold."

def "sci:history:venus_transit" "Even the path of a planet could be foretold to the hour: the rare passages of Venus across the face of the Sun, predicted by Kepler's laws, watched by Horrocks in 1639, and pursued across the world in 1761 and 1769 to measure the very size of the solar system. The wandering star's crossing, named in advance. — history of science"
ln sci:history:venus_transit venus @related_to
ln sci:history:venus_transit myth:omen_to_prediction sys:part_of
set.add name="ontology.foreknowledge" id="sci:history:venus_transit"

def "sci:history:vesuvius_79" "In 79 CE Vesuvius buried Pompeii and Herculaneum under ash and stone in a single day. Pliny the Younger, watching from across the bay, wrote the first clear eyewitness account of an eruption — while his uncle Pliny the Elder died going to the rescue. A city stopped in an afternoon, and the first science of the volcano. — history"
ln sci:history:vesuvius_79 volcano @explains
ln sci:history:vesuvius_79 sci:geo:volcanism @related_to
ln sci:history:vesuvius_79 myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="sci:history:vesuvius_79"

def "sci:history:war_of_the_currents" "A series of events in the late 1880s and early 1890s that established the standard for electric power transmission."
ln sci:history:war_of_the_currents tech:power:direct_current @evaluates
ln sci:history:war_of_the_currents tech:power:alternating_current @evaluates

def "sci:history:wright_brothers_flight" "The first successful sustained flight of a powered, controlled, heavier-than-air airplane (1903)."
ln sci:history:wright_brothers_flight tech:aviation:airplane @demonstrates
