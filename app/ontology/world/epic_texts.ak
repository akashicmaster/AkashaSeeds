# Akasha ontology (world pack) — world epics & foundational texts.
# The origin-texts of storytelling were thin: myth:/tale: were rich but the great
# EPICS (Iliad, Gilgamesh, Mahabharata, Shahnameh, Journey to the West…) were
# missing. Add them as first-class atoms, tied to their culture (ethnicity:/hist:/
# geo:), their gods (deity:), the narrative shape (nar:) and related tales. A-tier.

def "epic:epic" "A foundational epic or classic text — a civilization's origin-story (叙事詩/古典)."
def "epic:era:ancient" "The the earliest written epics."
def "epic:era:classical" "The the Greco-Roman/Sanskrit/Persian classics."
def "epic:era:medieval" "The the medieval epics and romances."
def "epic:era:early_modern" "The the early-modern classics."

# ── the epics ──
def "epic:epic_of_gilgamesh" "The oldest great epic — a king's quest for immortality after the death of his friend Enkidu; the flood story that prefigures Noah."
ln epic:epic_of_gilgamesh epic:epic thesaurus:related
ln epic:epic_of_gilgamesh epic:era:ancient epic:era_of
ln epic:epic_of_gilgamesh hist:babylonia epic:from_culture
ln epic:epic_of_gilgamesh deity:ishtar epic:from_culture
ln epic:epic_of_gilgamesh myth:gilgamesh_bull_of_heaven thesaurus:related
ln epic:epic_of_gilgamesh nar:structure:hero_journey thesaurus:related
def "epic:iliad" "Homer's epic of the wrath of Achilles in the tenth year of the Trojan War — the fountainhead of Western literature."
ln epic:iliad epic:epic thesaurus:related
ln epic:iliad epic:era:classical epic:era_of
ln epic:iliad ancient_greece epic:from_culture
ln epic:iliad deity:zeus epic:from_culture
ln epic:iliad deity:athena thesaurus:related
ln epic:iliad nar:conflict:person_vs_fate thesaurus:related
def "epic:odyssey" "Homer's epic of Odysseus's ten-year homeward voyage of monsters and cunning — the archetypal journey."
ln epic:odyssey epic:epic thesaurus:related
ln epic:odyssey epic:era:classical epic:era_of
ln epic:odyssey ancient_greece epic:from_culture
ln epic:odyssey deity:poseidon epic:from_culture
ln epic:odyssey nar:structure:hero_journey thesaurus:related
ln epic:odyssey journey:the_road_back thesaurus:related
def "epic:aeneid" "Virgil's epic of Aeneas fleeing fallen Troy to found the Roman line — Rome's national myth."
ln epic:aeneid epic:epic thesaurus:related
ln epic:aeneid epic:era:classical epic:era_of
ln epic:aeneid roman_empire epic:from_culture
ln epic:aeneid deity:venus epic:from_culture
ln epic:aeneid nar:conflict:person_vs_fate thesaurus:related
def "epic:metamorphoses" "Ovid's tapestry of transformation myths, from creation to Caesar — the West's mythology handbook."
ln epic:metamorphoses epic:epic thesaurus:related
ln epic:metamorphoses epic:era:classical epic:era_of
ln epic:metamorphoses roman_empire epic:from_culture
ln epic:metamorphoses nar:metamorphosis thesaurus:related
def "epic:mahabharata" "The vast Sanskrit epic of the Kurukshetra war and dharma — the world's longest poem, holding the Bhagavad Gita."
ln epic:mahabharata epic:epic thesaurus:related
ln epic:mahabharata epic:era:classical epic:era_of
ln epic:mahabharata indo_aryans epic:from_culture
ln epic:mahabharata deity:krishna epic:from_culture
ln epic:mahabharata quote:vyasa_mahabharata thesaurus:related
ln epic:mahabharata nar:conflict:person_vs_self thesaurus:related
def "epic:ramayana" "Valmiki's epic of prince Rama's exile, Sita's abduction by Ravana, and her rescue — the model of duty and devotion."
ln epic:ramayana epic:epic thesaurus:related
ln epic:ramayana epic:era:classical epic:era_of
ln epic:ramayana indo_aryans epic:from_culture
ln epic:ramayana deity:vishnu epic:from_culture
ln epic:ramayana quote:valmiki_ramayana thesaurus:related
ln epic:ramayana deity:hanuman thesaurus:related
def "epic:shahnameh" "Ferdowsi's 'Book of Kings' — the mythic-historical epic of Persia that saved the Persian tongue."
ln epic:shahnameh epic:epic thesaurus:related
ln epic:shahnameh epic:era:medieval epic:era_of
ln epic:shahnameh persians epic:from_culture
ln epic:shahnameh achaemenid_persia epic:from_culture
ln epic:shahnameh nar:succession thesaurus:related
def "epic:beowulf" "The Old English epic of the hero who slays Grendel, its mother and a dragon — the seed of every dragon-fight."
ln epic:beowulf epic:epic thesaurus:related
ln epic:beowulf epic:era:medieval epic:era_of
ln epic:beowulf roman_empire epic:from_culture
ln epic:beowulf myth:beowulf thesaurus:related
ln epic:beowulf nar:conflict:person_vs_supernatural thesaurus:related
def "epic:poetic_edda" "The Norse poems preserving the myths of Odin, Thor and Ragnarök."
ln epic:poetic_edda epic:epic thesaurus:related
ln epic:poetic_edda epic:era:medieval epic:era_of
ln epic:poetic_edda deity:odin epic:from_culture
ln epic:poetic_edda deity:pantheon:norse thesaurus:related
ln epic:poetic_edda deity:norse_thor thesaurus:related
def "epic:nibelungenlied" "The Middle High German epic of Siegfried, the dragon's hoard, and Kriemhild's terrible revenge."
ln epic:nibelungenlied epic:epic thesaurus:related
ln epic:nibelungenlied epic:era:medieval epic:era_of
ln epic:nibelungenlied hist:gaul epic:from_culture
ln epic:nibelungenlied nar:revenge thesaurus:related
def "epic:kalevala" "Elias Lönnrot's Finnish national epic, woven from oral runo-song — Väinämöinen and the magic Sampo."
ln epic:kalevala epic:epic thesaurus:related
ln epic:kalevala epic:era:medieval epic:era_of
ln epic:kalevala oral:oral_formulaic_theory thesaurus:related
def "epic:tain_bo_cuailnge" "The 'Cattle Raid of Cooley' — Ireland's epic of the hero Cú Chulainn defending Ulster alone."
ln epic:tain_bo_cuailnge epic:epic thesaurus:related
ln epic:tain_bo_cuailnge epic:era:medieval epic:era_of
ln epic:tain_bo_cuailnge deity:the_morrigan epic:from_culture
ln epic:tain_bo_cuailnge deity:pantheon:celtic thesaurus:related
def "epic:journey_to_the_west" "Wu Cheng'en's classic — the Monkey King Sun Wukong escorting the monk Xuanzang to fetch the sutras."
ln epic:journey_to_the_west epic:epic thesaurus:related
ln epic:journey_to_the_west epic:era:early_modern epic:era_of
ln epic:journey_to_the_west han_chinese epic:from_culture
ln epic:journey_to_the_west nar:structure:hero_journey thesaurus:related
ln epic:journey_to_the_west nar:quest thesaurus:related
def "epic:romance_of_three_kingdoms" "The historical epic-novel of the war of the Three Kingdoms — loyalty, strategy and the fall of Han."
ln epic:romance_of_three_kingdoms epic:epic thesaurus:related
ln epic:romance_of_three_kingdoms epic:era:early_modern epic:era_of
ln epic:romance_of_three_kingdoms han_chinese epic:from_culture
ln epic:romance_of_three_kingdoms han_china epic:from_culture
ln epic:romance_of_three_kingdoms nar:conflict:person_vs_person thesaurus:related
def "epic:water_margin" "The tale of 108 outlaws of Mount Liang who rise against corruption — China's Robin Hood epic."
ln epic:water_margin epic:epic thesaurus:related
ln epic:water_margin epic:era:early_modern epic:era_of
ln epic:water_margin han_chinese epic:from_culture
ln epic:water_margin nar:rebellion thesaurus:related
def "epic:dream_of_red_chamber" "Cao Xueqin's masterpiece of a great family's decline — the summit of Chinese fiction."
ln epic:dream_of_red_chamber epic:epic thesaurus:related
ln epic:dream_of_red_chamber epic:era:early_modern epic:era_of
ln epic:dream_of_red_chamber han_chinese epic:from_culture
ln epic:dream_of_red_chamber nar:fall thesaurus:related
def "epic:tale_of_genji" "Murasaki Shikibu's 11th-c. masterpiece, often called the world's first novel — the shining prince Genji."
ln epic:tale_of_genji epic:epic thesaurus:related
ln epic:tale_of_genji epic:era:medieval epic:era_of
ln epic:tale_of_genji japanese_people epic:from_culture
ln epic:tale_of_genji nar:element:mood thesaurus:related
def "epic:heike_monogatari" "The elegiac war epic of the Genpei war and the fall of the Taira — impermanence made narrative."
ln epic:heike_monogatari epic:epic thesaurus:related
ln epic:heike_monogatari epic:era:medieval epic:era_of
ln epic:heike_monogatari japanese_people epic:from_culture
ln epic:heike_monogatari nar:tragedy thesaurus:related
def "epic:kojiki" "Japan's oldest chronicle — the myths of Izanagi, Izanami and Amaterasu, and the imperial descent."
ln epic:kojiki epic:epic thesaurus:related
ln epic:kojiki epic:era:ancient epic:era_of
ln epic:kojiki japanese_people epic:from_culture
ln epic:kojiki deity:japanese_amaterasu epic:from_culture
ln epic:kojiki deity:izanagi thesaurus:related
ln epic:kojiki deity:pantheon:japanese thesaurus:related
def "epic:popol_vuh" "The Maya 'Book of the People' — creation, the Hero Twins, and the maize origin of humankind."
ln epic:popol_vuh epic:epic thesaurus:related
ln epic:popol_vuh epic:era:classical epic:era_of
ln epic:popol_vuh maya_people epic:from_culture
ln epic:popol_vuh maya_civilization epic:from_culture
ln epic:popol_vuh myth:maya_hero_twins thesaurus:related
def "epic:epic_of_sundiata" "The Mande oral epic of Sundiata Keita, founder of the Mali Empire — sung by griots still."
ln epic:epic_of_sundiata epic:epic thesaurus:related
ln epic:epic_of_sundiata epic:era:medieval epic:era_of
ln epic:epic_of_sundiata oral:griot thesaurus:related
def "epic:one_thousand_and_one_nights" "Scheherazade's frame of nested tales — Aladdin, Sinbad, Ali Baba; the frame-story par excellence."
ln epic:one_thousand_and_one_nights epic:epic thesaurus:related
ln epic:one_thousand_and_one_nights epic:era:medieval epic:era_of
ln epic:one_thousand_and_one_nights arabs epic:from_culture
ln epic:one_thousand_and_one_nights nar:structure:frame_story thesaurus:related
ln epic:one_thousand_and_one_nights nar:device:cliffhanger thesaurus:related
def "epic:divine_comedy" "Dante's journey through Hell, Purgatory and Paradise — the summit of medieval Christian imagination."
ln epic:divine_comedy epic:epic thesaurus:related
ln epic:divine_comedy epic:era:medieval epic:era_of
ln epic:divine_comedy ethnicity:italians epic:from_culture
ln epic:divine_comedy nar:structure:hero_journey thesaurus:related
ln epic:divine_comedy nar:pilgrimage thesaurus:related
def "epic:canterbury_tales" "Chaucer's pilgrims telling tales on the road to Canterbury — a frame of English social comedy."
ln epic:canterbury_tales epic:epic thesaurus:related
ln epic:canterbury_tales epic:era:medieval epic:era_of
ln epic:canterbury_tales hist:gaul epic:from_culture
ln epic:canterbury_tales nar:structure:frame_story thesaurus:related
def "epic:song_of_roland" "The French chanson de geste of Roland's last stand at Roncevaux — the epic of Charlemagne's paladins."
ln epic:song_of_roland epic:epic thesaurus:related
ln epic:song_of_roland epic:era:medieval epic:era_of
ln epic:song_of_roland french epic:from_culture
ln epic:song_of_roland gaul epic:from_culture
ln epic:song_of_roland nar:sacrifice thesaurus:related
def "epic:el_cid" "The Castilian epic of Rodrigo Díaz, 'the Cid', exile and reconqueror — Spain's national hero-poem."
ln epic:el_cid epic:epic thesaurus:related
ln epic:el_cid epic:era:medieval epic:era_of
ln epic:el_cid nar:exile thesaurus:related
def "epic:morte_darthur" "Malory's compilation of the Arthurian legend — Camelot, the Round Table, the Grail and the fall."
ln epic:morte_darthur epic:epic thesaurus:related
ln epic:morte_darthur epic:era:medieval epic:era_of
ln epic:morte_darthur nar:fall thesaurus:related
ln epic:morte_darthur nar:quest thesaurus:related
def "epic:don_quixote" "Cervantes's tale of the mad knight and Sancho Panza — the first modern novel, and the death of chivalry."
ln epic:don_quixote epic:epic thesaurus:related
ln epic:don_quixote epic:era:early_modern epic:era_of
ln epic:don_quixote nar:character:foil thesaurus:related
def "epic:paradise_lost" "Milton's epic of the fall of Satan and of Man — the grandest poem in English."
ln epic:paradise_lost epic:epic thesaurus:related
ln epic:paradise_lost epic:era:early_modern epic:era_of
ln epic:paradise_lost nar:fall thesaurus:related
ln epic:paradise_lost nar:conflict:person_vs_fate thesaurus:related
def "epic:prose_edda" "Snorri Sturluson's handbook of Norse myth and skaldic craft."
ln epic:prose_edda epic:epic thesaurus:related
ln epic:prose_edda epic:era:medieval epic:era_of
ln epic:prose_edda deity:odin epic:from_culture
ln epic:prose_edda deity:pantheon:norse thesaurus:related
