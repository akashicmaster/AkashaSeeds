# Akasha ontology — namespace: sky
# atoms: 16

def "sky.artifact" "Physical artifacts of flight imagination — machines, drawings, sites."
ln sky.artifact ont.sky_dreamers sys:part_of
set.add name="ontology.sky_dreamers" id="sky.artifact"

def "sky.enigma" "Figures, places, and objects that remain unresolved mysteries of the sky."
ln sky.enigma ont.sky_dreamers sys:part_of
set.add name="ontology.sky_dreamers" id="sky.enigma"

def "sky.event" "Key moments and milestones in the history of flight."
ln sky.event ont.sky_dreamers sys:part_of
set.add name="ontology.sky_dreamers" id="sky.event"

def "sky.myth" "Mythological and legendary flight narratives."
ln sky.myth ont.sky_dreamers sys:part_of
set.add name="ontology.sky_dreamers" id="sky.myth"

def "sky.pioneer" "Historical inventors and aviators who pursued flight."
ln sky.pioneer ont.sky_dreamers sys:part_of
set.add name="ontology.sky_dreamers" id="sky.pioneer"

def "sky:artifact:ornithopter" "Da Vinci's ornithopter design, c.1485. A machine that generates lift by flapping wings, mimicking birds. Built from wood, leather, and canvas; never constructed or flown in his lifetime. The design anticipated principles of aerodynamics by four centuries."
ln sky:artifact:ornithopter sky.artifact sys:part_of
set.add name="ontology.sky_dreamers" id="sky:artifact:ornithopter"

def "sky:enigma:earhart_disappearance" "Amelia Earhart (1897–1937?). First woman to fly solo across the Atlantic Ocean (May 1932). Disappeared over the central Pacific on July 2 1937 during an attempted circumnavigation of the globe near Howland Island. No confirmed wreckage or remains found. The most famous disappearance in aviation history."
ln sky:enigma:earhart_disappearance sky.enigma sys:part_of
ln sky:enigma:earhart_disappearance sky:enigma:saint_exupery_disappearance sys:related_to
ln sky:enigma:earhart_disappearance emo:anticipation calc:has_emotion
ln sky:enigma:earhart_disappearance emo:sadness calc:has_emotion
ln sky:enigma:earhart_disappearance sky:myth:icarus sys:related_to
set.add name="ontology.sky_dreamers" id="sky:enigma:earhart_disappearance"

def "sky:enigma:nazca_lines" "Geoglyphs etched into the Nazca Desert, Peru, c.500 BCE–500 CE. Visible in full only from altitude. Purpose disputed: astronomical calendar, offering lines for processions, or messages to sky deities. They presuppose a sky-view that no one in that era possessed."
ln sky:enigma:nazca_lines sky.enigma sys:part_of
ln sky:enigma:nazca_lines sky.artifact sys:part_of
ln sky:enigma:nazca_lines sky:myth:icarus sys:related_to
ln sky:enigma:nazca_lines emo:awe calc:has_emotion
ln sky:enigma:nazca_lines sky:pioneer:da_vinci @precedes_conceptually
set.add name="ontology.sky_dreamers" id="sky:enigma:nazca_lines"

def "sky:enigma:saint_exupery_disappearance" "Antoine de Saint-Exupéry (1900–1944?). French author (Le Petit Prince, 1943; Vol de nuit, 1931), mail-route pilot, and wartime aviator. Disappeared on a reconnaissance mission over southern France or the Mediterranean, July 31 1944. Wreckage of his P-38 found off Marseille in 2000; fate of pilot remains unknown."
ln sky:enigma:saint_exupery_disappearance sky.enigma sys:part_of
ln sky:enigma:saint_exupery_disappearance sky:enigma:earhart_disappearance sys:related_to
ln sky:enigma:saint_exupery_disappearance emo:sadness calc:has_emotion
ln sky:enigma:saint_exupery_disappearance emo:awe calc:has_emotion
ln sky:enigma:saint_exupery_disappearance sky:myth:icarus sys:related_to
set.add name="ontology.sky_dreamers" id="sky:enigma:saint_exupery_disappearance"

def "sky:event:lindbergh_transatlantic" "Charles Lindbergh's solo nonstop transatlantic flight, Roosevelt Field (New York) to Le Bourget (Paris), May 20–21 1927. Duration: 33 hours 30 minutes in the monoplane Spirit of St. Louis. First solo transatlantic crossing. Prize: $25,000 Orteig Prize."
ln sky:event:lindbergh_transatlantic sky.event sys:part_of
ln sky:event:lindbergh_transatlantic sky:enigma:earhart_disappearance @precedes
ln sky:event:lindbergh_transatlantic sky:enigma:saint_exupery_disappearance @precedes
set.add name="ontology.sky_dreamers" id="sky:event:lindbergh_transatlantic"

def "sky:event:montgolfier_first_flight" "Montgolfier brothers' first crewed balloon ascent, Paris, November 21 1783. Passengers: Pilâtre de Rozier and the Marquis d'Arlandes. The first time humans left the ground under lift and returned alive. Prior test: a sheep, a duck, and a rooster (September 19 1783)."
ln sky:event:montgolfier_first_flight sky.event sys:part_of
ln sky:event:montgolfier_first_flight tech:aviation:hot_air_balloon sys:related_to
ln sky:event:montgolfier_first_flight sky:pioneer:lilienthal @precedes
set.add name="ontology.sky_dreamers" id="sky:event:montgolfier_first_flight"

def "sky:event:wright_first_flight" "Wright Brothers' first sustained powered heavier-than-air flight, Kitty Hawk, North Carolina, December 17 1903. Four flights that day; first: 12 seconds, 36 metres (Orville). Fourth: 59 seconds, 260 metres (Wilbur). The Wrights were self-taught bicycle manufacturers."
ln sky:event:wright_first_flight sky.event sys:part_of
ln sky:event:wright_first_flight sci:history:wright_brothers_flight sys:same_as
ln sky:event:wright_first_flight sky:event:lindbergh_transatlantic @precedes
set.add name="ontology.sky_dreamers" id="sky:event:wright_first_flight"

def "sky:myth:daedalus" "Master craftsman of Crete. Fashioned wings of feathers and beeswax for himself and his son; escaped Minos's labyrinth by air; survived. The first engineer of flight in myth — and the first to grieve from altitude."
ln sky:myth:daedalus sky.myth sys:part_of
ln sky:myth:daedalus sky:myth:icarus sys:related_to
ln sky:myth:daedalus emo:sadness calc:has_emotion
set.add name="ontology.sky_dreamers" id="sky:myth:daedalus"

def "sky:myth:icarus" "Son of Daedalus. Flew with wings of feathers and beeswax; flew too close to the sun; fell into the Aegean Sea. The archetypal dreamer who overreached — and in doing so, first touched the sky."
ln sky:myth:icarus sky.myth sys:part_of
ln sky:myth:icarus sky:myth:daedalus sys:related_to
ln sky:myth:icarus emo:awe calc:has_emotion
ln sky:myth:icarus emo:fear calc:has_emotion
ln sky:myth:icarus sky:enigma:nazca_lines sys:related_to
ln sky:myth:icarus sky:pioneer:lilienthal sys:related_to
set.add name="ontology.sky_dreamers" id="sky:myth:icarus"

def "sky:pioneer:da_vinci" "Leonardo da Vinci (1452–1519). Polymath; designed the ornithopter (flapping-wing machine) and aerial screw (proto-helicopter) c.1485–1490. Never achieved powered flight. His notebooks were not widely published until centuries later."
ln sky:pioneer:da_vinci sky.pioneer sys:part_of
ln sky:pioneer:da_vinci sky:artifact:ornithopter sys:related_to
ln sky:pioneer:da_vinci sky:myth:icarus sys:related_to
ln sky:pioneer:da_vinci emo:anticipation calc:has_emotion
ln sky:pioneer:da_vinci sky:event:montgolfier_first_flight @precedes_conceptually
set.add name="ontology.sky_dreamers" id="sky:pioneer:da_vinci"

def "sky:pioneer:lilienthal" "Otto Lilienthal (1848–1896). German aviation pioneer; made over 2,000 successful glider flights from Rhinow Hills and the Fliegeberg, 1891–1896. Fatally crashed August 9 1896 near Rhinow; died the next day. Last words attributed: 'Opfer müssen gebracht werden.' (Sacrifices must be made.)"
ln sky:pioneer:lilienthal sky.pioneer sys:part_of
ln sky:pioneer:lilienthal tech:aviation:glider sys:related_to
ln sky:pioneer:lilienthal sky:myth:icarus sys:related_to
ln sky:pioneer:lilienthal emo:fear calc:has_emotion
ln sky:pioneer:lilienthal emo:sadness calc:has_emotion
ln sky:pioneer:lilienthal sky:event:wright_first_flight @precedes
set.add name="ontology.sky_dreamers" id="sky:pioneer:lilienthal"
