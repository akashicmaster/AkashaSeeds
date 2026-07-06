# Akasha ontology — namespace: myth
# atoms: 383

def "myth:aboriginal_rainbow_serpent" "The Rainbow Serpent is among the oldest and greatest of Aboriginal Australian beings: the giant snake who shaped the rivers and waterholes in the Dreaming, who lives in deep water, and who arches across the sky as the rainbow, bringer of the rains and guardian of water and life. — Aboriginal Australian myth"
ln myth:aboriginal_rainbow_serpent myth sys:is_a
ln myth:aboriginal_rainbow_serpent rainbow @explains
ln myth:aboriginal_rainbow_serpent creation @explains
ln myth:aboriginal_rainbow_serpent water @illustrates
ln myth:aboriginal_rainbow_serpent myth:human_nature_communion sys:part_of
set.add name="ontology.sky_phenomena" id="myth:aboriginal_rainbow_serpent"

def "myth:adventure_modern" "The adventure in the modern age: the old pulp revived in Indiana Jones, the treasure-hunt carried on into the game, the journey written as literature, and the survival-tale at the killing edges of the world. The going-out, in every key the present age can sound. — genre history"
ln myth:adventure_modern myth sys:related_to
ln myth:adventure_modern myth:adventure_travel @related_to
set.add name="ontology.narrative_genres" id="myth:adventure_modern"

def "myth:adventure_travel" "The adventure-and-travel tale: the journey to the unknown and back — the voyage of discovery, the castaway, the explorer, the hunter of treasure and lost worlds. The hero's journey written as geography, the going-out and the coming-home made the whole of the story. — genre history"
ln myth:adventure_travel myth sys:related_to
ln myth:adventure_travel myth:monomyth @related_to
ln myth:adventure_travel word:en:odysseus @related_to
set.add name="ontology.narrative_genres" id="myth:adventure_travel"

def "myth:age_of_exploration" "The real voyage-narrative of the early modern age: the logs of Columbus, the account of Magellan's ships sailing clean around the world, the scientific voyages of Cook across the Pacific, and the great compilations that gathered the navigators' tales. The map filled in, voyage by perilous voyage. — travel literature"
ln myth:age_of_exploration myth sys:is_a
ln myth:age_of_exploration myth:adventure_travel sys:part_of
ln myth:age_of_exploration era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:age_of_exploration"

def "myth:ai_made_real" "And the dream has stepped out of the story. The artificial minds that Asimov and Turing imagined are now real enough to converse, to reason, and to help build archives such as this very one; and the old question of the Three Laws — how to make the made mind safe, and honest, and good — is no longer a fable but a live and pressing task. The lineage that began with the bronze Talos now helps, in part, to write its own ontology. — genre history (reflexive)"
ln myth:ai_made_real myth sys:is_a
ln myth:ai_made_real myth:artificial_being sys:part_of
ln myth:ai_made_real myth:three_laws @related_to
ln myth:ai_made_real myth:thinking_machine @adapts
ln myth:ai_made_real era:contemporary sys:part_of
set.add name="ontology.artificial_being" id="myth:ai_made_real"

def "myth:akutagawa" "Akutagawa Ryunosuke reworked the old Japanese and Buddhist tales into modern short stories: Rashomon and In a Grove out of the medieval Konjaku collection, and The Spider's Thread out of a Buddhist parable — a sinner in hell offered escape by a single spider's thread, who loses it through his own selfishness. The classical tale made a modern mirror of the human heart. — modern Japanese literature"
ln myth:akutagawa myth sys:is_a
ln myth:akutagawa myth:nonwestern_modernity sys:part_of
ln myth:akutagawa myth:buddhist_deva @related_to
ln myth:akutagawa era:modern sys:part_of
set.add name="ontology.literary_transmission" id="myth:akutagawa"

def "myth:amesha_spentas" "The Amesha Spentas, the 'Bounteous Immortals' — the six great aspects through which Ahura Mazda works in the world: the Good Mind, Truth, Dominion, Devotion, Wholeness, and Immortality, each also guardian of a part of creation. The shining attributes of the Wise Lord."
ln myth:amesha_spentas myth:zoroastrian_pantheon sys:part_of
ln myth:amesha_spentas deity:ahura_mazda @related_to
set.add name="ontology.zoroastrian" id="myth:amesha_spentas"

def "myth:animal_kin" "The line dissolves: the shapeshifter who is now human, now beast — the werewolf, the fox-wife of Japan, the selkie who sheds her sealskin, the swan-maiden — and the animal-bride and animal-groom of the tale, Beauty's Beast, descended from Eros and Psyche. Human and animal not as ruler and ruled, but as kin who may wear each other's shape. — comparative myth"
ln myth:animal_kin myth sys:is_a
ln myth:animal_kin myth:human_nature_communion sys:part_of
ln myth:animal_kin myth:eros_psyche @related_to
ln myth:animal_kin era:ancient sys:part_of
set.add name="ontology.communion_thread" id="myth:animal_kin"

def "myth:animal_oracle" "The sacred animal through whom the divine speaks: the flight of birds read by the augur, the entrails of the ox opened for the gods' intent, the sacred cow whose life measures a pharaoh's reign, the dolphin who carries the drowned man to shore. In the temple and the omen-text, the animal is the medium between the visible and the unseen — a living word from a world beyond the human. — comparative religion"
ln myth:animal_oracle myth sys:is_a
ln myth:animal_oracle myth:human_nature_communion sys:part_of
ln myth:animal_oracle myth:diviner @related_to
ln myth:animal_oracle myth:medium @related_to
ln myth:animal_oracle era:ancient sys:part_of
set.add name="ontology.communion_thread" id="myth:animal_oracle"

def "myth:anime_global_myth" "Anime became a mythology for the world: Tezuka learned from Disney, and in time the traffic ran both ways, and the animation of Japan went out to every country as a shared modern story-stock — its kami and robots and journeying heroes a common tongue across borders. — anime history"
ln myth:anime_global_myth myth sys:is_a
ln myth:anime_global_myth myth:anime_modes sys:part_of
ln myth:anime_global_myth myth:film_myth @related_to
ln myth:anime_global_myth myth:cross_media_myth @related_to
ln myth:anime_global_myth era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:anime_global_myth"

def "myth:anime_modes" "Past the retellings, anime grew its own myths: the catastrophe made monster, the apocalypse and its rebirth, the made being and the human who must pilot it, the crossing into another world — themes that became, in time, a mythology for the whole world. — anime history"
ln myth:anime_modes myth sys:related_to
ln myth:anime_modes myth:anime_mythology @related_to
set.add name="ontology.narrative_genres" id="myth:anime_modes"

def "myth:anime_mythology" "Japanese animation became a modern vehicle of myth, drawing at once on the Shinto and Buddhist roots of Japan, on the gods and stars of Greece and Rome, and on the Chinese classics — and making new myths of its own for a global audience. — anime history"
ln myth:anime_mythology myth sys:related_to
ln myth:anime_mythology myth:cross_media_myth @related_to
set.add name="ontology.narrative_genres" id="myth:anime_mythology"

def "myth:apollo_plague" "The Iliad opens with plague: Apollo, angered, comes down from Olympus 'like the night' and looses his arrows on the Greek camp, and the funeral fires burn for nine days. The god of healing is also the sender of pestilence — his silver bow the sickness that strikes from afar, unseen. — Greek myth"
ln myth:apollo_plague myth sys:is_a
ln myth:apollo_plague plague @explains
ln myth:apollo_plague deity:apollo @related_to
ln myth:apollo_plague sci:bio:epidemic_disease @grounds
set.add name="ontology.geomyth_nexus" id="myth:apollo_plague"

def "myth:archaeoastronomy" "Long before writing, peoples built the sky's calendar into the earth: rings of stone and tombs and pyramids set to catch the sun at the turning of the year, or squared to the stars. The heavens brought down to the ground, so that the seasons the farmer needed and the gods the priest served could be read from the horizon. — archaeoastronomy"
ln myth:archaeoastronomy myth sys:related_to
ln myth:archaeoastronomy myth:geomythology @related_to
set.add name="ontology.archaeoastronomy" id="myth:archaeoastronomy"

def "myth:argo_ship" "The Argo was built of oak from Dodona, with a speaking prow that uttered prophecies, and crewed by the age's greatest heroes — Heracles, Orpheus whose song could outsing the Sirens, and the twin brothers Castor and Pollux. For its voyage it was set in the southern sky as the great ship Argo, since divided into the Keel, the Sails, and the Stern, with brilliant Canopus for its steersman-star. — Greek myth"
ln myth:argo_ship myth sys:is_a
ln myth:argo_ship jason @related_to
ln myth:argo_ship astro:constellation:carina @explains
ln myth:argo_ship astro:star:canopus @related_to
ln myth:argo_ship myth:greek_dioscuri @related_to
ln myth:argo_ship myth:greek_orpheus_lyre @related_to
set.add name="ontology.hero_myths" id="myth:argo_ship"

def "myth:arthashastra_spies" "Kautilya's Arthashastra, the ancient Indian manual of statecraft, builds the king a whole secret service: spies disguised as ascetics, merchants, and householders, women agents and poisoners, a web of watchers reporting on ministers and people alike. Espionage as the nervous system of the state. — Indian classics"
ln myth:arthashastra_spies myth sys:is_a
ln myth:arthashastra_spies myth:espionage sys:part_of
ln myth:arthashastra_spies era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:arthashastra_spies"

def "myth:arthurian_cycle" "The Matter of Britain: King Arthur, the Round Table, and the quest for the Holy Grail. Grown from Celtic myth — the otherworld, the sovereignty of the land, the cauldron of plenty that became the Grail — it was made the great romance-cycle of the West, and the deep well of all later legends of the king and the quest. — medieval literature"
ln myth:arthurian_cycle myth sys:is_a
ln myth:arthurian_cycle myth:literary_transmission sys:part_of
ln myth:arthurian_cycle myth:celtic_pantheon @adapts
ln myth:arthurian_cycle deity:the_dagda @related_to
set.add name="ontology.literary_transmission" id="myth:arthurian_cycle"

def "myth:artificial_being" "The dream of the made person: the automaton and the robot, the cyborg and the thinking machine — humanity building a servant and a mind in its own image, and forever asking whether the made thing will love it, serve it, or destroy it. A dream as old as Talos and as present as the machines of today. — comparative literature"
ln myth:artificial_being myth sys:related_to
ln myth:artificial_being myth:robot_golem @related_to
ln myth:artificial_being creation @related_to
set.add name="ontology.artificial_being" id="myth:artificial_being"

def "myth:aurora_spirits" "The shimmering lights of the polar sky are widely seen as the dead at play: among the Inuit, the spirits of the departed dancing in the heavens, kicking about a walrus skull; among the northern peoples generally, ancestors and spirits moving in the dark. — circumpolar star-lore"
ln myth:aurora_spirits myth sys:is_a
ln myth:aurora_spirits aurora @explains
ln myth:aurora_spirits ancestors @illustrates
set.add name="ontology.sky_phenomena" id="myth:aurora_spirits"

def "myth:aztec_five_suns" "Four world-ages, each lit by its own sun, have risen and ended in ruin. To kindle the fifth and present sun, the humble god Nanahuatzin casts himself into the sacred fire and is reborn as the sun in the sky — but it will move only when the gods give their own blood, and so the present world is bought with sacrifice. — Aztec myth"
ln myth:aztec_five_suns myth sys:is_a
ln myth:aztec_five_suns sun @explains
ln myth:aztec_five_suns sacrifice @explains
ln myth:aztec_five_suns myth:greek_prometheus @parallels
set.add name="ontology.world_myths" id="myth:aztec_five_suns"

def "myth:babylonian_enuma_elish" "Apsu the fresh water and Tiamat the salt sea mingle and beget the gods; but when the young gods grow loud, the sea-dragon Tiamat makes war on them. Marduk slays her, and splits her enormous body to make the dome of the sky and the floor of the earth, setting the stars in their stations and the year in its courses. — Babylonian myth (Enuma Elish)"
ln myth:babylonian_enuma_elish myth sys:is_a
ln myth:babylonian_enuma_elish myth:creation_primeval_waters sys:part_of
ln myth:babylonian_enuma_elish myth:creation_world_from_body @related_to
ln myth:babylonian_enuma_elish creation @explains
ln myth:babylonian_enuma_elish myth:babylonian_sky_origin @related_to
ln myth:babylonian_enuma_elish word:la:jupiter @related_to
set.add name="ontology.creation_myths" id="myth:babylonian_enuma_elish"

def "myth:babylonian_ishtar_venus" "Venus is the star of Ishtar (Sumerian Inanna), goddess of love and war. Her descent into the underworld, her death there, and her return mirror the planet's own vanishing from the evening sky and its reappearance at dawn — the first of the descend-and-return stories. — Babylonian myth"
ln myth:babylonian_ishtar_venus myth sys:is_a
ln myth:babylonian_ishtar_venus venus @explains
ln myth:babylonian_ishtar_venus descent @illustrates
ln myth:babylonian_ishtar_venus myth:greek_persephone @parallels
ln myth:babylonian_ishtar_venus myth:japanese_izanagi_izanami @parallels
set.add name="ontology.sky_phenomena" id="myth:babylonian_ishtar_venus"

def "myth:babylonian_sky_origin" "Long before the Greeks, Babylonian astronomers (in star-catalogues such as MUL.APIN) divided the ecliptic into the zodiac and named the figures along it — the Bull of Heaven, the Lion, the Scorpion, the Great Twins. The Greeks inherited these constellations and dressed them in their own myths; the sky we read is older than its Greek names. — Babylonian astronomy"
ln myth:babylonian_sky_origin myth sys:is_a
ln myth:babylonian_sky_origin zodiac @explains
ln myth:babylonian_sky_origin astro:constellation:taurus @related_to
ln myth:babylonian_sky_origin myth:greek_europa_bull @related_to
set.add name="ontology.constellation_myths" id="myth:babylonian_sky_origin"

def "myth:baltic_birds_way" "Across the Baltic and Finnic north the Milky Way is the Birds' Way — the shining road that migrating birds follow south in autumn and home in spring. — Baltic / Finnic star-lore"
ln myth:baltic_birds_way myth sys:is_a
ln myth:baltic_birds_way milky_way @explains
set.add name="ontology.sky_phenomena" id="myth:baltic_birds_way"

def "myth:beast_fable" "The animal who speaks the moral: Aesop's crow and fox, the tortoise and the hare, La Fontaine's farmyard court — the old lesson wrapped in a beast's skin so it can be told to a child, or a king, without giving offence. The trick of the form is that the animal is wholly human in its wisdom and folly, while staying wholly animal in its shape. The most ancient classroom in the world. — world folklore"
ln myth:beast_fable myth sys:is_a
ln myth:beast_fable myth:human_nature_communion sys:part_of
ln myth:beast_fable myth:reynard_fox @related_to
ln myth:beast_fable word:en:trickster @related_to
ln myth:beast_fable era:ancient sys:part_of
set.add name="ontology.communion_thread" id="myth:beast_fable"

def "myth:beowulf" "Beowulf, the Old English epic, tells of the hero who tears apart the monster Grendel and its mother, and in old age dies slaying a dragon for its hoard. The Germanic dragon-slayer, set down by a Christian hand — and the seed of every dragon-fight to come. — medieval literature"
ln myth:beowulf myth sys:is_a
ln myth:beowulf myth:literary_transmission sys:part_of
ln myth:beowulf myth:ie_serpent_slayer @adapts
ln myth:beowulf myth:norse_pantheon @related_to
set.add name="ontology.literary_transmission" id="myth:beowulf"

def "myth:biblical_noah_flood" "Grieved by human wickedness, God sends a flood, but bids the righteous Noah build an ark and bring aboard his family and pairs of every creature. The waters prevail, the ark grounds on the mountains of Ararat, and Noah sends out a raven and then a dove, which returns with an olive leaf; a rainbow seals the promise never to flood the world again. Scholars note its close kinship with the older Mesopotamian flood accounts. — Hebrew Bible"
ln myth:biblical_noah_flood myth sys:is_a
ln myth:biblical_noah_flood myth:world_flood_myths sys:part_of
ln myth:biblical_noah_flood flood @explains
ln myth:biblical_noah_flood myth:mesopotamian_flood @parallels
ln myth:biblical_noah_flood rainbow @related_to
set.add name="ontology.flood_myths" id="myth:biblical_noah_flood"

def "myth:biblical_spies" "The Bible is full of agents: Moses sends twelve men to scout the promised land, Joshua sends two into Jericho who are hidden by Rahab — the first 'asset' turned and sheltered — and Delilah coaxes from Samson the secret of his strength and sells it to his enemies. The scout, the safe-house, and the honey-trap, all already here. — Hebrew Bible"
ln myth:biblical_spies myth sys:is_a
ln myth:biblical_spies myth:espionage sys:part_of
ln myth:biblical_spies era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:biblical_spies"

def "myth:borges_labyrinth" "Borges made the labyrinth of Theseus a figure for the universe, the library, and the self, and turned the riddle of the ship of Theseus — what stays the same when every part is changed — into the matter of modern fable. The oldest images, made instruments of modern thought. — modern literature"
ln myth:borges_labyrinth myth sys:is_a
ln myth:borges_labyrinth myth:modern_literary_inheritance sys:part_of
ln myth:borges_labyrinth myth:theseus_minotaur @adapts
ln myth:borges_labyrinth myth:ship_of_theseus @related_to
set.add name="ontology.literary_transmission" id="myth:borges_labyrinth"

def "myth:buddhist_deva" "The devas (天部, tenbu) — the gods of the older traditions, mostly Hindu, taken up into the Buddhist cosmos: powerful and long-lived, yet still bound to the wheel of rebirth, and made guardians of the Buddha's teaching. Carried east, they took new names in China and Japan. — Buddhist tradition"
ln myth:buddhist_deva myth sys:is_a
set.add name="ontology.pantheons" id="myth:buddhist_deva"
set.add name="ontology.pantheons_buddhist" id="myth:buddhist_deva"

def "myth:calendar_animals" "Across the world, peoples have mapped time itself onto animals: a circle of beasts to name the years, the days, the hours, and the quarters of the sky. The calendar made a menagerie — time told in the faces of creatures. — comparative myth"
ln myth:calendar_animals myth sys:related_to
ln myth:calendar_animals myth:human_nature_communion @related_to
ln myth:calendar_animals myth:archaeoastronomy @related_to
set.add name="ontology.calendar_animals" id="myth:calendar_animals"

def "myth:carnival" "And the festival of misrule: the Feast of Fools and the carnival, when the world was turned upside down for a day — the servant crowned, the sacred mocked, the body and its hungers let loose — laughter as a sanctioned madness that overturns all order, then rights it again. The carnivalesque, the people's brief and joyous reign of folly. — folk tradition"
ln myth:carnival myth sys:is_a
ln myth:carnival myth:laughter sys:part_of
ln myth:carnival era:medieval sys:part_of
set.add name="ontology.laughter_thread" id="myth:carnival"

def "myth:carter_bloody_chamber" "Angela Carter's The Bloody Chamber reopened the fairy tales from within, retelling Bluebeard, Beauty and the Beast, and Red Riding Hood to free the women shut inside them; the folktale turned against the moral it once carried. — contemporary literature"
ln myth:carter_bloody_chamber myth sys:is_a
ln myth:carter_bloody_chamber myth:feminist_retelling sys:part_of
ln myth:carter_bloody_chamber word:en:folktale @adapts
ln myth:carter_bloody_chamber era:contemporary sys:part_of
set.add name="ontology.literary_transmission" id="myth:carter_bloody_chamber"

def "myth:celtic_pantheon" "The Celtic gods — the Tuatha Dé Danann, the 'people of the goddess Danu', who ruled Ireland before retreating into the hollow hills, and the gods of the Welsh and the Gauls; a divine company of poets, smiths, warriors, and sovereignty. — Celtic religion"
ln myth:celtic_pantheon myth sys:is_a
set.add name="ontology.pantheons" id="myth:celtic_pantheon"
set.add name="ontology.pantheons_celtic" id="myth:celtic_pantheon"

def "myth:chandler_marlowe" "Raymond Chandler gave the hardboiled detective a soul: Philip Marlowe, walking the corrupt streets of Los Angeles with a private code he will not sell — a knight-errant in a fallen world, and Chandler set a stained-glass knight in his very first page to say so. In his essay on the craft he praised Hammett's realism and mocked the artificial puzzle. The detective as the last honest man on a degraded quest. — genre history"
ln myth:chandler_marlowe myth sys:is_a
ln myth:chandler_marlowe myth:hardboiled sys:part_of
ln myth:chandler_marlowe myth:hardboiled @adapts
ln myth:chandler_marlowe myth:arthurian_cycle @related_to
ln myth:chandler_marlowe era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:chandler_marlowe"

def "myth:chinese_change_moon" "Chang'e, having swallowed the elixir of immortality, floats up to dwell upon the moon, where she remains — which is why a lady is seen in the moon, and, in some tellings, a jade hare pounding the elixir beside her. — Chinese myth"
ln myth:chinese_change_moon myth sys:is_a
ln myth:chinese_change_moon moon @explains
ln myth:chinese_change_moon tale:jataka_wise_hare_moon @parallels
set.add name="ontology.world_myths" id="myth:chinese_change_moon"

def "myth:chinese_eclipse_dragon" "When the sun darkens in eclipse, a great celestial dragon (or dog) is devouring it; the people raise a clamour with drums and gongs to frighten the beast into spitting the sun back out. — Chinese myth"
ln myth:chinese_eclipse_dragon myth sys:is_a
ln myth:chinese_eclipse_dragon eclipse @explains
ln myth:chinese_eclipse_dragon myth:hindu_rahu @parallels
ln myth:chinese_eclipse_dragon myth:norse_sun_wolves @parallels
set.add name="ontology.sky_phenomena" id="myth:chinese_eclipse_dragon"

def "myth:chinese_ghostlore" "China's dead are many: the hungry ghost with its needle throat, fed once a year at the Ghost Festival; the jiangshi, the stiff corpse that hops by night; and the fox-spirits and ghost-brides of Pu Songling's Strange Tales, who come to the lone scholar's lamp and love him until dawn. — comparative folklore"
ln myth:chinese_ghostlore myth sys:is_a
ln myth:chinese_ghostlore myth:world_ghostlore sys:part_of
ln myth:chinese_ghostlore era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:chinese_ghostlore"

def "myth:chinese_great_yu_flood" "China tells the flood differently: not survival but conquest. Gun tries to dam the endless floods with stolen self-swelling soil and fails, and is put to death; his son Yu succeeds by the opposite way — dredging the rivers and cutting channels to carry the waters to the sea. Toiling thirteen years, passing his own door three times without entering, Yu tames the flood and founds the first dynasty. — Chinese myth"
ln myth:chinese_great_yu_flood myth sys:is_a
ln myth:chinese_great_yu_flood myth:world_flood_myths sys:part_of
ln myth:chinese_great_yu_flood flood @explains
ln myth:chinese_great_yu_flood ingenuity @illustrates
ln myth:chinese_great_yu_flood perseverance @illustrates
set.add name="ontology.flood_myths" id="myth:chinese_great_yu_flood"

def "myth:chinese_houyi_suns" "When ten suns rise together and scorch the world, the divine archer Houyi shoots down nine of them, leaving the single sun we know, and saves the earth from burning. — Chinese myth"
ln myth:chinese_houyi_suns myth sys:is_a
ln myth:chinese_houyi_suns sun @explains
set.add name="ontology.world_myths" id="myth:chinese_houyi_suns"

def "myth:chinese_pangu" "From the cosmic egg the giant Pangu separates heaven from earth, holding them apart as he grows for ages; when he dies, his body becomes the world — his eyes the sun and moon, his breath the wind, his blood the rivers, his hair the stars. — Chinese myth"
ln myth:chinese_pangu myth sys:is_a
ln myth:chinese_pangu creation @explains
ln myth:chinese_pangu sun @explains
ln myth:chinese_pangu moon @explains
ln myth:chinese_pangu myth:norse_ymir @parallels
ln myth:chinese_pangu myth:creation_cosmic_egg sys:part_of
ln myth:chinese_pangu myth:creation_world_from_body @related_to
ln myth:chinese_pangu myth:creation_sky_earth_separation @related_to
set.add name="ontology.world_myths" id="myth:chinese_pangu"
set.add name="ontology.creation_myths" id="myth:chinese_pangu"

def "myth:chinese_zodiac" "The twelve animals of the Chinese calendar — rat, ox, tiger, rabbit, dragon, snake, horse, goat, monkey, rooster, dog, and pig — each rules a year in a turning cycle of twelve, and each governs an hour of the day and a quarter of the compass besides. The years themselves wear the faces of the beasts. — Chinese tradition"
ln myth:chinese_zodiac myth sys:is_a
ln myth:chinese_zodiac myth:calendar_animals sys:part_of
ln myth:chinese_zodiac myth:human_nature_communion sys:part_of
ln myth:chinese_zodiac era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:chinese_zodiac"

def "myth:comedy_of_manners" "Moliere and the comedy of manners held a laughing mirror to the type and the vice — the hypocrite, the miser, the misanthrope — and after him Wilde, with his glittering, weightless wit. The comedy that ends, like Austen's marriage-plot, not in a grave but in the right union and the mended, reconciled world. — genre history"
ln myth:comedy_of_manners myth sys:is_a
ln myth:comedy_of_manners myth:laughter sys:part_of
ln myth:comedy_of_manners myth:roman_comedy @adapts
ln myth:comedy_of_manners myth:marriage_plot @related_to
ln myth:comedy_of_manners era:early_modern sys:part_of
set.add name="ontology.laughter_thread" id="myth:comedy_of_manners"

def "myth:comet_omen" "Across the ancient world the comet was a star grown a tail of fire — read almost everywhere as an omen of upheaval: the fall of kings, war, plague. The Chinese named such apparitions 'broom stars', sweeping away the old order. — world star-lore"
ln myth:comet_omen myth sys:is_a
ln myth:comet_omen comet @explains
ln myth:comet_omen omen @illustrates
set.add name="ontology.sky_phenomena" id="myth:comet_omen"

def "myth:comic_satire" "Laughter entered the novel and the essay as a weapon: Rabelais and his giant grotesques, Swift and Voltaire turning ridicule against cruelty and cant and the smugness of the powerful. The satirist took up the old license of the jester — to mock the great and go unpunished — and made of folly's truth a blade. — genre history"
ln myth:comic_satire myth sys:is_a
ln myth:comic_satire myth:laughter sys:part_of
ln myth:comic_satire myth:reynard_fox @related_to
ln myth:comic_satire era:early_modern sys:part_of
set.add name="ontology.laughter_thread" id="myth:comic_satire"

def "myth:commedia_clown" "The commedia dell'arte gave Europe its masks: the nimble servant Harlequin, the greedy old Pantalone, the boastful Captain, improvised on the public square — and out of them came Punch, the white-faced Pierrot, the circus clown, and at last the silent-film tramp. The clown, a single lineage handed down in greasepaint and motley. — theatre history"
ln myth:commedia_clown myth sys:is_a
ln myth:commedia_clown myth:laughter sys:part_of
ln myth:commedia_clown myth:roman_comedy @adapts
ln myth:commedia_clown era:early_modern sys:part_of
set.add name="ontology.laughter_thread" id="myth:commedia_clown"

def "myth:contemporary_crime" "The crime novel became a serious literature of its own and went everywhere: Ellroy's dense, brutal Los Angeles and Mosley's Black L.A., the Nordic noir of Sjowall and Wahloo, Mankell, and Larsson that made the police novel a knife held to society, and Japan's social school, where Matsumoto Seicho rooted the mystery in poverty, corruption, and class. The detective story as the modern world's reckoning with itself. — genre history"
ln myth:contemporary_crime myth sys:is_a
ln myth:contemporary_crime myth:hardboiled @adapts
ln myth:contemporary_crime myth:police_procedural @adapts
ln myth:contemporary_crime era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:contemporary_crime"

def "myth:contemporary_inheritance" "Myth in the present age: the hero's journey mapped and reapplied, whole invented worlds raised on the old foundations, science fiction taking up the wonder and dread the creation-myths once carried, and the game — where the myth is no longer sung or read, but walked. — comparative literature"
ln myth:contemporary_inheritance myth sys:related_to
ln myth:contemporary_inheritance myth:modern_literary_inheritance @related_to
set.add name="ontology.literary_transmission" id="myth:contemporary_inheritance"

def "myth:cosmic_horror" "Lovecraft turned horror outward to the cosmos: a dread not of the monster that hunts you but of a universe so vast, so old, and so indifferent that it does not know you exist, ruled by alien gods beyond all meaning. The fear of insignificance itself, made flesh in the Cthulhu Mythos. — genre history"
ln myth:cosmic_horror myth sys:is_a
ln myth:cosmic_horror myth:horror_fiction sys:part_of
ln myth:cosmic_horror myth:cthulhu_mythos @adapts
ln myth:cosmic_horror era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:cosmic_horror"

def "myth:courtly_love" "The Middle Ages invented romantic love as we know it: the troubadour's song, the knight's devotion to an idealized and unattainable lady, the ennobling passion of Lancelot and of Tristan. The literary ideal of love-as-longing that every later romance would inherit. — medieval literature"
ln myth:courtly_love myth sys:is_a
ln myth:courtly_love myth:love_story sys:part_of
ln myth:courtly_love myth:arthurian_cycle @adapts
ln myth:courtly_love era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:courtly_love"

def "myth:cowherd_weaver" "The star-crossed lovers made literally stars: the Weaver Girl and the Cowherd, set by the gods on opposite banks of the Heavenly River — the Milky Way — and allowed to meet but one night a year, when the magpies fly up to bridge the stream. Their stars are Vega and Altair, and their meeting is the festival of Tanabata. The metaphor of Romeo and Juliet, written across the actual sky. — Chinese/Japanese myth"
ln myth:cowherd_weaver myth sys:is_a
ln myth:cowherd_weaver myth:love_story sys:part_of
ln myth:cowherd_weaver milky_way @related_to
ln myth:cowherd_weaver era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:cowherd_weaver"

def "myth:creation_by_word" "Type: creation by word or shaping. A maker speaks, thinks, or moulds the world and its people into being — by the word ('let there be light'), by the heart and tongue of Ptah, or by hands working clay and corn. — creation-myth type"
ln myth:creation_by_word myth:world_creation_myths sys:part_of
ln myth:creation_by_word creation @explains
set.add name="ontology.creation_myths" id="myth:creation_by_word"

def "myth:creation_cosmic_egg" "Type: the cosmic egg. The unformed whole is an egg, and the world hatches from it — sky and earth its two halves. — creation-myth type"
ln myth:creation_cosmic_egg myth:world_creation_myths sys:part_of
ln myth:creation_cosmic_egg creation @explains
set.add name="ontology.creation_myths" id="myth:creation_cosmic_egg"

def "myth:creation_earth_diver" "Type: the earth-diver. Before there is land there is only water; a creature dives to the bottom and brings up a little mud, from which the earth is grown. — creation-myth type"
ln myth:creation_earth_diver myth:world_creation_myths sys:part_of
ln myth:creation_earth_diver creation @explains
set.add name="ontology.creation_myths" id="myth:creation_earth_diver"

def "myth:creation_primeval_waters" "Type: from the primeval waters. In the beginning is a dark, formless sea, and from it the first land and the first god arise. — creation-myth type"
ln myth:creation_primeval_waters myth:world_creation_myths sys:part_of
ln myth:creation_primeval_waters creation @explains
set.add name="ontology.creation_myths" id="myth:creation_primeval_waters"

def "myth:creation_sky_earth_separation" "Type: the parting of sky and earth. The Sky and the Earth lie locked together in the dark, and must be forced apart for the world and its light to be. — creation-myth type"
ln myth:creation_sky_earth_separation myth:world_creation_myths sys:part_of
ln myth:creation_sky_earth_separation creation @explains
set.add name="ontology.creation_myths" id="myth:creation_sky_earth_separation"

def "myth:creation_world_from_body" "Type: the world from a body. A primeval giant or being is slain or dismembered, and the parts of its body become the parts of the world. — creation-myth type"
ln myth:creation_world_from_body myth:world_creation_myths sys:part_of
ln myth:creation_world_from_body creation @explains
set.add name="ontology.creation_myths" id="myth:creation_world_from_body"

def "myth:critical_retelling" "The newest turn in the long inheritance: to retell the old stories against their grain — from the side of those they silenced or maligned. The hero's journey, carried forward for three thousand years, is now also questioned: whose journey, told by whom, and at whose cost. — contemporary literature"
ln myth:critical_retelling myth sys:related_to
ln myth:critical_retelling myth:contemporary_inheritance @related_to
ln myth:critical_retelling myth:monomyth @related_to
set.add name="ontology.literary_transmission" id="myth:critical_retelling"

def "myth:cross_media_myth" "Myth left the page for new media: the film, the comic panel, and the game-table. Each retold the old stories in its own grammar — the moving image, the serial hero, the played-out adventure — and carried the gods and monsters to audiences the book never reached. — contemporary culture"
ln myth:cross_media_myth myth sys:related_to
ln myth:cross_media_myth myth:contemporary_inheritance @related_to
set.add name="ontology.literary_transmission" id="myth:cross_media_myth"

def "myth:cthulhu_mythos" "Lovecraft's Cthulhu Mythos is a modern myth made by many hands: a shared pantheon of vast, indifferent cosmic gods, added to by author after author. An anthology-mythology that inverts the old myths — a cosmos not ordered for us and watching over us, but boundless, ancient, and uncaring. — contemporary literature"
ln myth:cthulhu_mythos myth sys:is_a
ln myth:cthulhu_mythos myth:contemporary_inheritance sys:part_of
ln myth:cthulhu_mythos myth:world_creation_myths @related_to
set.add name="ontology.literary_transmission" id="myth:cthulhu_mythos"

def "myth:curse_of_akkad" "The Sumerian poem tells how proud Akkad, richest of cities, was cursed by the gods for an impiety: the rains held back, the fields turned to dust, the markets emptied, and the great city fell to ruin and famine. Composed as the memory of a real collapse — at the very time the long drought came. — Sumerian literature"
ln myth:curse_of_akkad myth sys:is_a
ln myth:curse_of_akkad famine @explains
ln myth:curse_of_akkad sci:geo:event_4200 @grounds
set.add name="ontology.geomyth_nexus" id="myth:curse_of_akkad"

def "myth:cyborg" "And the boundary itself dissolves: the cyborg, half living and half machine — RoboCop, the man rebuilt as a weapon; the Terminator's steel beneath living skin; Ghost in the Shell's Major, asking whether a 'ghost', a soul, still dwells in a wholly artificial body; the Borg, who assimilate flesh into their hive. Where the shapeshifter once blurred human and beast, the cyborg now blurs human and machine. — genre history"
ln myth:cyborg myth sys:is_a
ln myth:cyborg myth:artificial_being sys:part_of
ln myth:cyborg myth:animal_kin @parallels
ln myth:cyborg myth:star_trek @related_to
ln myth:cyborg era:contemporary sys:part_of
set.add name="ontology.artificial_being" id="myth:cyborg"

def "myth:dante_commedia" "Dante's Divine Comedy carries the poet down through Hell, up Purgatory, and into Paradise, with the Roman poet Virgil for his guide. Its descent to the world of the dead is the classical katabasis — the road walked by Odysseus, Aeneas, Orpheus, and Heracles — remade as a Christian vision of the whole cosmos. — medieval literature"
ln myth:dante_commedia myth sys:is_a
ln myth:dante_commedia myth:literary_transmission sys:part_of
ln myth:dante_commedia descent @adapts
ln myth:dante_commedia myth:greek_orpheus_lyre @related_to
ln myth:dante_commedia myth:heracles_cerberus @related_to
set.add name="ontology.literary_transmission" id="myth:dante_commedia"

def "myth:death_personified" "In the years of the Black Death, when a third of Europe died, Death became a person: a skeleton stalking every rank alike, drawn in the Dance of Death leading pope and emperor and beggar by the hand to the grave. The plague gave the West its image of Death the leveller, who takes all and spares none. — medieval European tradition"
ln myth:death_personified myth sys:is_a
ln myth:death_personified plague @related_to
ln myth:death_personified mortality @illustrates
ln myth:death_personified sci:bio:epidemic_disease @grounds
set.add name="ontology.geomyth_nexus" id="myth:death_personified"

def "myth:detective_fiction" "Detective fiction — the story built around a hidden crime and its unravelling by reason: a puzzle laid before the reader, a mind that reads the clues the rest of us miss, and the order of the world restored when the truth is named. — genre history"
ln myth:detective_fiction myth sys:related_to
set.add name="ontology.narrative_genres" id="myth:detective_fiction"

def "myth:dido_aeneas" "Dido, queen of Carthage, gives her whole heart to the wandering Aeneas, who leaves her at the gods' command to go and found Rome; she builds a pyre and dies upon his sword, cursing his people to the end of time. The lover abandoned for duty and destiny — sister to Ariadne and Medea, left weeping on the shore. — Roman epic"
ln myth:dido_aeneas myth sys:is_a
ln myth:dido_aeneas myth:love_story sys:part_of
ln myth:dido_aeneas myth:feminist_retelling @related_to
ln myth:dido_aeneas myth:theseus_ariadne_crown @related_to
ln myth:dido_aeneas era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:dido_aeneas"

def "myth:diviner" "The diviner reads the hidden will of things: in the cracked bone and the bird's flight, in the stars and the cast lots and the oracle's trance, the future and the mind of the gods are made readable. The magic of foreknowledge — the same art that, refined, became prediction and at last science. — comparative religion"
ln myth:diviner myth sys:is_a
ln myth:diviner myth:magic sys:part_of
ln myth:diviner myth:omen_to_prediction @related_to
ln myth:diviner era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:diviner"

def "myth:doctor_who" "Doctor Who is the renewing wanderer: a time-travelling alien who wins by wit and not by weapons, a trickster-sage in a blue box that is larger within than without, and who, when he dies, is reborn with a new face — a death-and-rebirth built into the story so that it need never end. A tireless tourist of history and letters, forever meeting Shakespeare, Dickens, and Agatha Christie. — contemporary culture"
ln myth:doctor_who myth sys:is_a
ln myth:doctor_who myth:sf_franchise_myth sys:part_of
ln myth:doctor_who trickster @related_to
ln myth:doctor_who deity:osiris @parallels
ln myth:doctor_who era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:doctor_who"

def "myth:dogon_sirius_lore" "The Dogon of Mali centre their cosmology and the great Sigui ceremony on Sirius, called Sigi tolo, and speak of a small dense companion, po tolo. A widely popularised claim that this preserves ancient knowledge of the white-dwarf Sirius B is rejected by most scholars, who trace the detail to twentieth-century contact; the cultural importance of the tradition, however, is well attested. — Dogon star-lore"
ln myth:dogon_sirius_lore myth sys:is_a
ln myth:dogon_sirius_lore astro:star:sirius sys:refers_to
ln myth:dogon_sirius_lore word:la:sirius @related_to
set.add name="ontology.star_names" id="myth:dogon_sirius_lore"

def "myth:don_quixote" "Cervantes' Don Quixote, an old man so steeped in chivalric romances that he rides out to be a knight himself and tilts at windmills for giants; the parody that buried the medieval romance and, in burying it, became the first modern novel. — modern literature"
ln myth:don_quixote myth sys:is_a
ln myth:don_quixote myth:modern_literary_inheritance sys:part_of
ln myth:don_quixote myth:arthurian_cycle @adapts
ln myth:don_quixote myth:laughter sys:part_of
set.add name="ontology.literary_transmission" id="myth:don_quixote"

def "myth:doomed_passion" "The Brontes held the tragic pole: Jane Eyre's plain governess and her brooding master with his mad wife hidden above, and Wuthering Heights' Cathy and Heathcliff, whose love is a destroying storm upon the moors. The Gothic romance of a passion that wrecks rather than weds. — modern literature"
ln myth:doomed_passion myth sys:is_a
ln myth:doomed_passion myth:love_story sys:part_of
ln myth:doomed_passion myth:gothic @related_to
ln myth:doomed_passion era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:doomed_passion"

def "myth:dracula_vampire" "The vampire, codified: from Polidori's cold lord and Le Fanu's Carmilla to Stoker's Dracula — the undead foreign predator who drinks the blood of the living and spreads his curse like a contagion. Rooted in Vlad the Impaler and the vampire-lore of the Slavic and Balkan lands, the dead who will not stay dead. — genre history"
ln myth:dracula_vampire myth sys:is_a
ln myth:dracula_vampire myth:horror_fiction sys:part_of
ln myth:dracula_vampire myth:gothic @adapts
ln myth:dracula_vampire myth:slavic_pantheon @related_to
ln myth:dracula_vampire plague @related_to
ln myth:dracula_vampire era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:dracula_vampire"

def "myth:dragon_ball" "Dragon Ball's hero Son Goku is the Monkey King himself — Sun Wukong of Journey to the West — reborn as a boy with a monkey's tail, a flying cloud, and a magic staff. The Chinese trickster-pilgrim made the very template of the modern shonen battle epic. — anime history"
ln myth:dragon_ball myth sys:is_a
ln myth:dragon_ball myth:anime_mythology sys:part_of
ln myth:dragon_ball myth:journey_to_west @adapts
ln myth:dragon_ball myth:monomyth @related_to
ln myth:dragon_ball era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:dragon_ball"

def "myth:earth_as_body" "The creation myths that build the world from a slain giant — Ymir, Pangu, Tiamat — read the very land as a body: the mountains its bones, the rivers and sea its blood, the soil its flesh. A mythic geology, an old intuition that the ground beneath us is one vast frame. — comparative myth / earth science"
ln myth:earth_as_body myth sys:is_a
ln myth:earth_as_body myth:creation_world_from_body @related_to
ln myth:earth_as_body myth:geomythology sys:part_of
set.add name="ontology.geomyth_nexus" id="myth:earth_as_body"

def "myth:eddas_snorri" "The Norse myths survive because they were written down: the Poetic Edda, and Snorri Sturluson's Prose Edda, set on parchment the gods, the world-tree, and the doom of Ragnarok that the spread of Christianity would otherwise have silenced. Memory saved by being recorded — the very act this whole archive is built on. — medieval literature"
ln myth:eddas_snorri myth sys:is_a
ln myth:eddas_snorri myth:literary_transmission sys:part_of
ln myth:eddas_snorri myth:norse_pantheon sys:refers_to
ln myth:eddas_snorri myth:norse_yggdrasil @related_to
set.add name="ontology.literary_transmission" id="myth:eddas_snorri"

def "myth:edogawa_ranpo" "Japan took up the form through Edogawa Ranpo — a pen-name that is the name 'Edgar Allan Poe' itself, spoken in Japanese. He founded the Japanese mystery and its honkaku, the orthodox fair-play puzzle, a tradition later renewed by the shin-honkaku writers and their ingenious locked rooms. The lineage written into a single borrowed name. — genre history"
ln myth:edogawa_ranpo myth sys:is_a
ln myth:edogawa_ranpo myth:detective_fiction sys:part_of
ln myth:edogawa_ranpo myth:poe_dupin @adapts
ln myth:edogawa_ranpo era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:edogawa_ranpo"

def "myth:egyptian_dogstar_year" "The Egyptian year opened when Sirius — Sopdet, the Dog Star, whose heliacal rising announced the flooding of the Nile — reappeared in the dawn sky after seventy days' absence. The star's return was the New Year and the river's gift in one, a cosmic clock by which the whole of Egyptian agricultural life was set. The dog-star that ruled the calendar. — Egyptian astronomy"
ln myth:egyptian_dogstar_year myth sys:is_a
ln myth:egyptian_dogstar_year myth:calendar_animals sys:part_of
ln myth:egyptian_dogstar_year myth:archaeoastronomy @related_to
ln myth:egyptian_dogstar_year myth:egyptian_osiris @related_to
ln myth:egyptian_dogstar_year era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:egyptian_dogstar_year"

def "myth:egyptian_geb_nut" "The sky is the goddess Nut, her star-strewn body arched over the earth-god Geb her brother, the two held forever apart by Shu the god of air, who stands between them with upraised arms. — Egyptian myth"
ln myth:egyptian_geb_nut myth sys:is_a
ln myth:egyptian_geb_nut myth:creation_sky_earth_separation sys:part_of
ln myth:egyptian_geb_nut myth:egyptian_nun_atum @related_to
ln myth:egyptian_geb_nut creation @explains
set.add name="ontology.creation_myths" id="myth:egyptian_geb_nut"

def "myth:egyptian_nun_atum" "Out of Nun, the boundless dark waters, rises the first mound of earth, and upon it Atum, the self-created, who brings forth from himself the first gods — Shu the air and Tefnut the moisture — and so begins the ordered world. — Egyptian myth"
ln myth:egyptian_nun_atum myth sys:is_a
ln myth:egyptian_nun_atum myth:creation_primeval_waters sys:part_of
ln myth:egyptian_nun_atum creation @explains
set.add name="ontology.creation_myths" id="myth:egyptian_nun_atum"

def "myth:egyptian_osiris" "Osiris, the good king, is murdered and dismembered by his brother Set; his wife Isis gathers and restores him, and he becomes lord of the dead, while their son Horus reclaims the living world. His death and revival mirror the dying grain and the flooding Nile that renews the fields. — Egyptian myth"
ln myth:egyptian_osiris myth sys:is_a
ln myth:egyptian_osiris seasons @explains
ln myth:egyptian_osiris renewal @explains
set.add name="ontology.world_myths" id="myth:egyptian_osiris"

def "myth:egyptian_ra_voyage" "Each day Ra sails his barque across the sky as the sun; each night he passes through the underworld, where the serpent Apophis attacks him, and his victory each dawn is the sunrise renewing the world. — Egyptian myth"
ln myth:egyptian_ra_voyage myth sys:is_a
ln myth:egyptian_ra_voyage sun @explains
ln myth:egyptian_ra_voyage dawn @explains
set.add name="ontology.world_myths" id="myth:egyptian_ra_voyage"

def "myth:egyptian_sacred_animals" "Egypt's gods wore the faces of creatures: Thoth the ibis-headed scribe of wisdom; Sobek the crocodile-god of the Nile's power; Bastet the cat-goddess of the home; Horus the falcon-king; and the Apis bull of Memphis, a living god walking among mortals — when one died, all Egypt mourned and sought the next. The animal not as symbol but as the god's very body, housed and fed and mourned. — Egyptian religion"
ln myth:egyptian_sacred_animals myth sys:is_a
ln myth:egyptian_sacred_animals myth:calendar_animals sys:part_of
ln myth:egyptian_sacred_animals myth:human_nature_communion sys:part_of
ln myth:egyptian_sacred_animals myth:animal_oracle @related_to
ln myth:egyptian_sacred_animals myth:totem_animal @related_to
ln myth:egyptian_sacred_animals era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:egyptian_sacred_animals"

def "myth:eros_psyche" "Eros and Psyche: the soul wedded to a love she may not look upon, who loses him by the light of a lamp and must toil through impossible tasks — even descend to the underworld for a box of beauty — to win him again, and is made immortal at the last. The love tried and rewarded; the seed of Beauty and the Beast and a hundred fairy tales. — Greek/Roman myth"
ln myth:eros_psyche myth sys:is_a
ln myth:eros_psyche myth:love_story sys:part_of
ln myth:eros_psyche word:en:folktale @related_to
ln myth:eros_psyche myth:carter_bloody_chamber @related_to
ln myth:eros_psyche era:ancient sys:part_of
ln myth:eros_psyche myth:human_nature_communion sys:part_of
set.add name="ontology.narrative_genres" id="myth:eros_psyche"

def "myth:eshu_two_hats" "Two friends swore nothing could ever divide them. Eshu walked the boundary-path between their fields wearing a hat black on the one side and white on the other; afterward each swore to the colour he had seen, called the other a liar, and they came to blows. Eshu's lesson: the truth wears more than one face, and at the crossroads certainty fails. — Yoruba tale"
ln myth:eshu_two_hats myth sys:is_a
ln myth:eshu_two_hats deity:eshu @related_to
ln myth:eshu_two_hats trickster @related_to
ln myth:eshu_two_hats perspective @illustrates
set.add name="ontology.trickster_myths" id="myth:eshu_two_hats"

def "myth:espionage" "Espionage — the secret war of knowledge: the agent who goes where he must not, learns what he must not, and carries it home. As old as the state itself, and a near-twin of the detective's art, for both live by uncovering what others would keep hidden. — genre history"
ln myth:espionage myth sys:related_to
ln myth:espionage myth:detective_fiction @related_to
set.add name="ontology.narrative_genres" id="myth:espionage"

def "myth:eternal_departure" "And under them all, the oldest shape of all: the departure into the unknown and the return changed — the hero's journey written as real geography. From Odysseus and the pilgrim of the West to the explorer, the treasure-hunter, the traveller, and the wanderer of the open road, it is one restless human story, told for as long as there have been horizons: the going out, and the coming home. — comparative literature"
ln myth:eternal_departure myth sys:is_a
ln myth:eternal_departure myth:adventure_modern sys:part_of
ln myth:eternal_departure myth:monomyth @related_to
ln myth:eternal_departure word:en:odysseus @related_to
ln myth:eternal_departure myth:journey_to_west @related_to
ln myth:eternal_departure era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:eternal_departure"

def "myth:evangelion" "Neon Genesis Evangelion drapes its giant-robot apocalypse in the imagery of Kabbalah and scripture: the Tree of Life and its sephirot, Adam and Lilith, the 'Angels', the Dead Sea Scrolls — borrowed less as doctrine than as metaphor and mood, a parade of sacred quotation much like Star Trek's, laid over a story of trauma, creation, and the dread of other minds. — anime history"
ln myth:evangelion myth sys:is_a
ln myth:evangelion myth:anime_modes sys:part_of
ln myth:evangelion world_tree @related_to
ln myth:evangelion myth:world_creation_myths @related_to
ln myth:evangelion myth:star_trek @parallels
ln myth:evangelion era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:evangelion"

def "myth:exorcist" "The exorcist casts out the possessing spirit or the demon: by the rite of command and the holy name, in the Catholic ritual and in a hundred traditions the world over, the magic that does not summon but expels. The dark twin of the sorcerer — for to drive a spirit out, one must first know how it is called. — comparative religion"
ln myth:exorcist myth sys:is_a
ln myth:exorcist myth:magic sys:part_of
ln myth:exorcist deity:angra_mainyu @related_to
ln myth:exorcist myth:horror_fiction @related_to
ln myth:exorcist era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:exorcist"

def "myth:faust" "The legend of Faust, the scholar who sells his soul to the devil Mephistopheles for knowledge and power, was made by Marlowe and then by Goethe into the modern myth of striving without limit and its price — the pact with the adversary, retold for an age that worshipped knowledge. — modern literature"
ln myth:faust myth sys:is_a
ln myth:faust myth:modern_literary_inheritance sys:part_of
ln myth:faust deity:angra_mainyu @related_to
ln myth:faust trickster @related_to
set.add name="ontology.literary_transmission" id="myth:faust"

def "myth:faust_magician" "And the magician who pays: Faust, who buys his sorcery with his very soul — the necromancer's bargain, the dark price of forbidden power, the warning shadow that falls across all magic. To reach past the bound set for mortals is to be claimed by what one reached for. — genre history"
ln myth:faust_magician myth sys:is_a
ln myth:faust_magician myth:magic_in_fiction sys:part_of
ln myth:faust_magician myth:faust @adapts
ln myth:faust_magician deity:angra_mainyu @related_to
ln myth:faust_magician era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:faust_magician"

def "myth:female_pi" "The hardboiled eye, so long a lone man's, was claimed by women: Paretsky's V. I. Warshawski and Grafton's Kinsey Millhone walked the same mean streets on their own terms, and turned the genre's hard gaze on the violence done to women. The private eye, retold from the other side. — genre history"
ln myth:female_pi myth sys:is_a
ln myth:female_pi myth:hardboiled @adapts
ln myth:female_pi myth:feminist_retelling @related_to
ln myth:female_pi era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:female_pi"

def "myth:feminist_retelling" "A wave of retellings gives voice to the women the myths passed over: Atwood's Penelopiad speaks for Penelope and her hanged maids, Miller's Circe for the witch of the lonely isle, and others for Briseis, for the Trojan women, for the Gorgon herself. The abandoned and the monstered — Medea, Ariadne, Medusa — are heard at last from their own side. — contemporary literature"
ln myth:feminist_retelling myth sys:is_a
ln myth:feminist_retelling myth:critical_retelling sys:part_of
ln myth:feminist_retelling word:en:odysseus @adapts
ln myth:feminist_retelling word:en:medusa @related_to
ln myth:feminist_retelling word:en:medea @related_to
ln myth:feminist_retelling era:contemporary sys:part_of
set.add name="ontology.literary_transmission" id="myth:feminist_retelling"

def "myth:film_myth" "Cinema became a great engine of myth: Disney made the fairy tales of Grimm and Perrault the common dreams of childhood; Kurosawa turned Akutagawa's tales and even Shakespeare into samurai epic; and Ray Harryhausen brought the Argonauts and their sown skeleton-warriors, and Perseus and Medusa, to life on the screen. — contemporary cinema"
ln myth:film_myth myth sys:is_a
ln myth:film_myth myth:cross_media_myth sys:part_of
ln myth:film_myth myth:romantic_folk_recovery @adapts
ln myth:film_myth myth:akutagawa @related_to
ln myth:film_myth myth:argo_ship @related_to
ln myth:film_myth era:contemporary sys:part_of
set.add name="ontology.literary_transmission" id="myth:film_myth"

def "myth:film_noir" "Hollywood made the hardboiled world into film noir: the shadowed city, the doomed man, the woman who is danger itself, shot in hard light and deep dark. The Maltese Falcon, Double Indemnity, The Big Sleep — Hammett, Cain, and Chandler turned to the screen, and a literature became a way of seeing. — genre history / cinema"
ln myth:film_noir myth sys:is_a
ln myth:film_noir myth:hardboiled @adapts
ln myth:film_noir myth:film_myth @related_to
ln myth:film_noir era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:film_noir"

def "myth:flood_bird_scout" "A small shared thread runs through the great flood tales: when the rains end, the survivor looses birds to test the drying world. Utnapishtim sends a dove, a swallow, and a raven from his grounded boat; Noah a raven and a dove that comes back with the olive leaf. The same gesture, across the traditions — proof of kinship between the tellings. — flood-myth motif"
ln myth:flood_bird_scout myth sys:is_a
ln myth:flood_bird_scout myth:mesopotamian_flood @related_to
ln myth:flood_bird_scout myth:biblical_noah_flood @related_to
ln myth:flood_bird_scout flood @related_to
set.add name="ontology.flood_myths" id="myth:flood_bird_scout"

def "myth:four_symbols" "And the sky itself was quartered into four great beasts: the Azure Dragon of the East and the spring, the Vermilion Bird of the South and the summer, the White Tiger of the West and the autumn, and the Black Tortoise of the North and the winter — each presiding over seven of the twenty-eight lunar lodges into which the Chinese divided the band of the heavens. The seasons and the sky written as four animals. — Chinese astronomy"
ln myth:four_symbols myth sys:is_a
ln myth:four_symbols myth:calendar_animals sys:part_of
ln myth:four_symbols myth:human_nature_communion sys:part_of
ln myth:four_symbols myth:archaeoastronomy @related_to
ln myth:four_symbols era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:four_symbols"

def "myth:frame_tale_transmission" "The frame-tale — a story that holds other stories within it — travelled west from the Panchatantra and the Thousand and One Nights into Boccaccio's Decameron, where ten flee the plague telling tales, and Chaucer's Canterbury Tales, where pilgrims tell theirs on the road. Scheherazade's device, made the engine of European storytelling. — medieval literature"
ln myth:frame_tale_transmission myth sys:is_a
ln myth:frame_tale_transmission myth:literary_transmission sys:part_of
ln myth:frame_tale_transmission word:en:arabian_nights @adapts
ln myth:frame_tale_transmission word:en:panchatantra @adapts
ln myth:frame_tale_transmission word:en:scheherazade @related_to
set.add name="ontology.literary_transmission" id="myth:frame_tale_transmission"

def "myth:frankenstein" "Mary Shelley's Frankenstein bore the subtitle 'The Modern Prometheus': a man steals the fire of life, makes a living being, and is destroyed by the creature he will not love. The first science fiction, and a direct retelling of the fire-thief's hubris — kin to the older Golem, the made man that turns upon its maker. — modern literature"
ln myth:frankenstein myth sys:is_a
ln myth:frankenstein myth:contemporary_inheritance sys:part_of
ln myth:frankenstein myth:greek_prometheus @adapts
ln myth:frankenstein hubris @illustrates
ln myth:frankenstein myth:artificial_being sys:part_of
set.add name="ontology.literary_transmission" id="myth:frankenstein"

def "myth:games_as_myth" "The video game made myth playable. Where the epic was sung and the romance read, the game is enacted — the player is called, crosses the threshold, descends to the underworld, and returns. Games draw their gods and monsters straight from the world's pantheons — the Greek underworld, the Norse twilight, whole rosters of the gods of every people — and turn the myth from a story told into a world walked through. — contemporary culture"
ln myth:games_as_myth myth sys:is_a
ln myth:games_as_myth myth:contemporary_inheritance sys:part_of
ln myth:games_as_myth myth:monomyth @adapts
ln myth:games_as_myth myth:greek_pantheon @related_to
ln myth:games_as_myth descent @related_to
set.add name="ontology.literary_transmission" id="myth:games_as_myth"

def "myth:genre_romance" "And it became the great popular genre: the category romance by the million, from the Regency drawing-room to the present day, bound by one unbreakable promise — the happy ending, the lovers united at the last. By sheer numbers, the most widely read fiction on earth. — contemporary literature"
ln myth:genre_romance myth sys:is_a
ln myth:genre_romance myth:love_story sys:part_of
ln myth:genre_romance myth:marriage_plot @adapts
ln myth:genre_romance era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:genre_romance"

def "myth:geomythology" "Geomythology — the reading of myths and legends as memory: the recognition that a flood-story, an earthquake-monster, or a fire-mountain god may preserve, in the language of myth, a real event of the Earth that a people lived through and could not forget. — earth science / folklore"
ln myth:geomythology myth sys:related_to
set.add name="ontology.geomyth_nexus" id="myth:geomythology"

def "myth:ghibli_shinto" "Miyazaki and Studio Ghibli draw deep on the Shinto world: the forest kami and beast-gods of Princess Mononoke, the bathhouse of the eight million gods and its yokai in Spirited Away, an animism in which river and tree and wind are alive and ensouled. The old kami of Japan, walking in modern animation. — anime history"
ln myth:ghibli_shinto myth sys:is_a
ln myth:ghibli_shinto myth:anime_mythology sys:part_of
ln myth:ghibli_shinto myth:japanese_pantheon @adapts
ln myth:ghibli_shinto myth:yanagita_folklore @related_to
ln myth:ghibli_shinto era:contemporary sys:part_of
ln myth:ghibli_shinto myth:human_nature_communion sys:part_of
set.add name="ontology.narrative_genres" id="myth:ghibli_shinto"

def "myth:ghost_story_kaidan" "The ghost, the dead returned: the English antiquarian ghost story and its haunted house, and in Japan the kaidan — the tales Lafcadio Hearn gathered, and the onryo, the wronged ghost (most often a woman, her long hair unbound) who comes back for vengeance. The onryo would become the very spine of modern Japanese horror. — genre history"
ln myth:ghost_story_kaidan myth sys:is_a
ln myth:ghost_story_kaidan myth:horror_fiction sys:part_of
ln myth:ghost_story_kaidan myth:yanagita_folklore @related_to
ln myth:ghost_story_kaidan era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:ghost_story_kaidan"

def "myth:ghoul_jinn" "The desert's unseen: the Arabic ghul, the grave-haunting fiend that feeds on the dead and gave English its word 'ghoul', and the jinn of smokeless fire, who dwell unseen among us and can help or harm. The dread that walks the wilderness and the ruin. — comparative folklore"
ln myth:ghoul_jinn myth sys:is_a
ln myth:ghoul_jinn myth:world_ghostlore sys:part_of
ln myth:ghoul_jinn word:en:arabian_nights @related_to
set.add name="ontology.narrative_genres" id="myth:ghoul_jinn"

def "myth:gilgamesh_bull_of_heaven" "The goddess Ishtar, taken with the victorious king, offers herself; Gilgamesh refuses, reciting the ruin of her former lovers. In fury she demands the Bull of Heaven from her father Anu and looses it on Uruk, where its breath opens pits that swallow hundreds — until the two heroes seize and slay it. The Bull stands in the sky as Taurus, and Ishtar who sent it is the planet Venus. — Epic of Gilgamesh"
ln myth:gilgamesh_bull_of_heaven myth sys:is_a
ln myth:gilgamesh_bull_of_heaven myth:gilgamesh_epic sys:part_of
ln myth:gilgamesh_bull_of_heaven word:akk:bull_of_heaven @related_to
ln myth:gilgamesh_bull_of_heaven astro:constellation:taurus @explains
ln myth:gilgamesh_bull_of_heaven venus @related_to
ln myth:gilgamesh_bull_of_heaven myth:babylonian_ishtar_venus @related_to
ln myth:gilgamesh_bull_of_heaven hubris @illustrates
set.add name="ontology.hero_myths" id="myth:gilgamesh_bull_of_heaven"

def "myth:gilgamesh_enkidu" "The people of Uruk, ground down by their restless king, beg the gods for relief, and the gods make Enkidu, a wild man of the steppe, to be his equal. The two meet in a wrestling-match that shakes the walls, and finding none stronger than the other, become inseparable friends. — Epic of Gilgamesh"
ln myth:gilgamesh_enkidu myth sys:is_a
ln myth:gilgamesh_enkidu myth:gilgamesh_epic sys:part_of
ln myth:gilgamesh_enkidu enkidu @related_to
ln myth:gilgamesh_enkidu friendship @illustrates
set.add name="ontology.hero_myths" id="myth:gilgamesh_enkidu"

def "myth:gilgamesh_enkidu_death" "For the slaying of Humbaba and the Bull, the gods decree that one of the friends must die, and the lot falls on Enkidu, who sickens and wastes away. Gilgamesh keeps a long vigil over the body, and will not let it be buried until decay forces him — and so first looks full into the face of death. — Epic of Gilgamesh"
ln myth:gilgamesh_enkidu_death myth sys:is_a
ln myth:gilgamesh_enkidu_death myth:gilgamesh_epic sys:part_of
ln myth:gilgamesh_enkidu_death grief @illustrates
ln myth:gilgamesh_enkidu_death mortality @illustrates
set.add name="ontology.hero_myths" id="myth:gilgamesh_enkidu_death"

def "myth:gilgamesh_epic" "The Epic of Gilgamesh — the oldest long poem to come down to us, written on clay in Mesopotamia: a king's road from tyranny through friendship and grief to the hard wisdom that no mortal escapes death, and that what endures is the city he built and the tale itself. — Mesopotamian epic"
ln myth:gilgamesh_epic myth sys:is_a
ln myth:gilgamesh_epic gilgamesh @related_to
set.add name="ontology.hero_myths" id="myth:gilgamesh_epic"

def "myth:gilgamesh_humbaba" "Hungry for a name that will outlast them, Gilgamesh and Enkidu march to the Cedar Forest to kill its monstrous guardian Humbaba. They fell the guardian and the great cedars — a glory that the gods will hold against them. — Epic of Gilgamesh"
ln myth:gilgamesh_humbaba myth sys:is_a
ln myth:gilgamesh_humbaba myth:gilgamesh_epic sys:part_of
ln myth:gilgamesh_humbaba fame @illustrates
set.add name="ontology.hero_myths" id="myth:gilgamesh_humbaba"

def "myth:gilgamesh_plant_of_youth" "Utnapishtim tells of a thorny plant at the sea's bottom that gives back lost youth. Gilgamesh ties stones to his feet and dives, and wins it — but as he bathes on the way home a serpent glides up and carries it off, and sheds its skin renewed; so the snake renews itself, and man does not. — Epic of Gilgamesh"
ln myth:gilgamesh_plant_of_youth myth sys:is_a
ln myth:gilgamesh_plant_of_youth myth:gilgamesh_epic sys:part_of
ln myth:gilgamesh_plant_of_youth mortality @illustrates
ln myth:gilgamesh_plant_of_youth renewal @illustrates
set.add name="ontology.hero_myths" id="myth:gilgamesh_plant_of_youth"

def "myth:gilgamesh_quest_immortality" "Terrified now of his own death, Gilgamesh sets out to find Utnapishtim, the one man made deathless. He passes the twin-peaked mountain Mashu, guarded by the Scorpion-men, and travels the long dark tunnel of the sun's own road, emerging into a garden of jeweled trees and the counsel of Siduri the alewife, who bids him love this life — yet he goes on. — Epic of Gilgamesh"
ln myth:gilgamesh_quest_immortality myth sys:is_a
ln myth:gilgamesh_quest_immortality myth:gilgamesh_epic sys:part_of
ln myth:gilgamesh_quest_immortality word:akk:the_scorpion_bab @related_to
ln myth:gilgamesh_quest_immortality immortality @illustrates
set.add name="ontology.hero_myths" id="myth:gilgamesh_quest_immortality"

def "myth:gilgamesh_return" "Empty-handed of immortality, Gilgamesh comes home to Uruk and looks on its great walls, bidding his ferryman admire their making. There at last is his answer: not the deathless life he chased, but the city he raised and the story now told of him — the only immortality a man may have. — Epic of Gilgamesh"
ln myth:gilgamesh_return myth sys:is_a
ln myth:gilgamesh_return myth:gilgamesh_epic sys:part_of
ln myth:gilgamesh_return legacy @illustrates
ln myth:gilgamesh_return mortality @illustrates
set.add name="ontology.hero_myths" id="myth:gilgamesh_return"

def "myth:gilgamesh_utnapishtim_flood" "At the edge of the world Utnapishtim tells how the gods resolved to drown mankind, and how Ea warned him to pull down his house and build a boat and take aboard the seed of all living things. The flood raged until even the gods cowered; the boat grounded on a mountain; he sent out a dove, a swallow, and a raven, and made sacrifice — and was granted eternal life. It is the oldest telling of the Flood, the source beneath the later ones. — Epic of Gilgamesh"
ln myth:gilgamesh_utnapishtim_flood myth sys:is_a
ln myth:gilgamesh_utnapishtim_flood myth:gilgamesh_epic sys:part_of
ln myth:gilgamesh_utnapishtim_flood utnapishtim @related_to
ln myth:gilgamesh_utnapishtim_flood myth:mesopotamian_flood @related_to
ln myth:gilgamesh_utnapishtim_flood flood @explains
set.add name="ontology.hero_myths" id="myth:gilgamesh_utnapishtim_flood"

def "myth:godzilla" "Godzilla rose in 1954 out of the bomb: a primeval beast woken and made monstrous by atomic fire, the nuclear terror given a body to walk the ruined city. The catastrophe remembered as kaiju — exactly as older ages made the earthquake a thrashing catfish and the fossil bones of giants into dragons. A modern geomyth, born of a wound still fresh. — anime / tokusatsu history"
ln myth:godzilla myth sys:is_a
ln myth:godzilla myth:anime_modes sys:part_of
ln myth:godzilla myth:geomythology @adapts
ln myth:godzilla myth:war_memory @related_to
ln myth:godzilla era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:godzilla"

def "myth:golden_age_mystery" "Between the wars came the Golden Age of the puzzle: Christie's Poirot and Miss Marple, Sayers's Lord Peter, Chesterton's Father Brown, the country-house murder and the closed circle of suspects. It was played as a fair game between writer and reader — every clue shown — and the Detection Club even swore its members to rules of fair play. — genre history"
ln myth:golden_age_mystery myth sys:is_a
ln myth:golden_age_mystery myth:detective_fiction sys:part_of
ln myth:golden_age_mystery myth:sherlock_holmes @adapts
ln myth:golden_age_mystery era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:golden_age_mystery"

def "myth:gothic" "The Gothic founded modern horror: Walpole's haunted castle, Radcliffe's veiled terrors, Lewis's transgressing monk — the ruin and the crypt, the ancestral curse, the dead past reaching up to grip the living present. Terror raised to an art. — genre history"
ln myth:gothic myth sys:is_a
ln myth:gothic myth:horror_fiction sys:part_of
ln myth:gothic era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:gothic"

def "myth:great_game_thriller" "The genre was born of the Great Game: Kipling's Kim, the boy who plays at spying across British India, often called the first true spy novel; Childers's Riddle of the Sands and its amateur yachtsmen sniffing out invasion; and Buchan's Thirty-Nine Steps, which set the pattern of the innocent man hunted across country, a secret in his keeping. — genre history"
ln myth:great_game_thriller myth sys:is_a
ln myth:great_game_thriller myth:spy_novel sys:part_of
ln myth:great_game_thriller era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:great_game_thriller"

def "myth:greek_aquila_eagle" "The eagle of Zeus — bearer of his thunderbolts and the bird that carried Ganymede up to Olympus — is honored in the sky as the constellation Aquila. — Greek myth"
ln myth:greek_aquila_eagle myth sys:is_a
ln myth:greek_aquila_eagle astro:constellation:aquila @explains
ln myth:greek_aquila_eagle myth:greek_ganymede @related_to
set.add name="ontology.constellation_myths" id="myth:greek_aquila_eagle"

def "myth:greek_ariadne_crown" "When Theseus abandons Ariadne on Naxos, the god Dionysus takes her as his bride and flings her bridal crown into the heavens, where its jewels become the stars of Corona Borealis, the Northern Crown. — Greek myth"
ln myth:greek_ariadne_crown myth sys:is_a
ln myth:greek_ariadne_crown astro:constellation:corona_borealis @explains
ln myth:greek_ariadne_crown love @illustrates
set.add name="ontology.constellation_myths" id="myth:greek_ariadne_crown"

def "myth:greek_astraea" "Astraea, maiden goddess of justice, dwelt among mortals in the Golden Age but withdrew to the heavens as humankind turned wicked, becoming the constellation Virgo with the ear of grain Spica in her hand. (Some see in her instead Demeter, or her daughter Persephone.) — Greek myth"
ln myth:greek_astraea myth sys:is_a
ln myth:greek_astraea astro:constellation:virgo @explains
ln myth:greek_astraea astro:star:spica @explains
ln myth:greek_astraea mystic:sign:virgo sys:related_to
ln myth:greek_astraea justice @illustrates
ln myth:greek_astraea myth:greek_persephone @related_to
set.add name="ontology.constellation_myths" id="myth:greek_astraea"

def "myth:greek_callisto_bear" "Callisto, beloved of Zeus, is turned into a bear by jealous Hera; years later her own son Arcas, out hunting, nearly spears her, and Zeus sweeps them both up into the sky as the Great and Little Bears. — Greek myth"
ln myth:greek_callisto_bear myth sys:is_a
ln myth:greek_callisto_bear astro:constellation:ursa_major @explains
ln myth:greek_callisto_bear astro:constellation:ursa_minor @explains
ln myth:greek_callisto_bear jealousy @illustrates
set.add name="ontology.constellation_myths" id="myth:greek_callisto_bear"

def "myth:greek_cancer_crab" "As Heracles battles the many-headed Hydra, jealous Hera sends a crab to pinch his heel; he crushes it underfoot, and Hera sets the loyal little creature among the stars as Cancer. — Greek myth"
ln myth:greek_cancer_crab myth sys:is_a
ln myth:greek_cancer_crab astro:constellation:cancer @explains
ln myth:greek_cancer_crab mystic:sign:cancer sys:related_to
set.add name="ontology.constellation_myths" id="myth:greek_cancer_crab"

def "myth:greek_cassiopeia_vanity" "Queen Cassiopeia boasts that she — or her daughter — outshines the sea-nymphs in beauty, and for that pride is bound to her throne in the sky as the constellation Cassiopeia, set to wheel head-down about the pole for half of every night. — Greek myth"
ln myth:greek_cassiopeia_vanity myth sys:is_a
ln myth:greek_cassiopeia_vanity astro:constellation:cassiopeia @explains
ln myth:greek_cassiopeia_vanity vanity @illustrates
ln myth:greek_cassiopeia_vanity myth:greek_perseus_andromeda @related_to
set.add name="ontology.constellation_myths" id="myth:greek_cassiopeia_vanity"

def "myth:greek_celestial_scorpion" "The scorpion sent from the earth to kill the boastful hunter Orion is set in the sky opposite him as Scorpius, its heart the smouldering red star Antares — so that as the Scorpion climbs in the east, Orion forever flees beneath the western horizon. — Greek myth"
ln myth:greek_celestial_scorpion myth sys:is_a
ln myth:greek_celestial_scorpion astro:constellation:scorpius @explains
ln myth:greek_celestial_scorpion astro:star:antares @explains
ln myth:greek_celestial_scorpion mystic:sign:scorpio sys:related_to
ln myth:greek_celestial_scorpion myth:greek_orion @related_to
set.add name="ontology.constellation_myths" id="myth:greek_celestial_scorpion"

def "myth:greek_chiron_archer" "The archer of the zodiac is drawn as a centaur with his bow bent — by many the wise and gentle Chiron, teacher of heroes, who at his death was raised among the stars as Sagittarius. — Greek myth"
ln myth:greek_chiron_archer myth sys:is_a
ln myth:greek_chiron_archer astro:constellation:sagittarius @explains
ln myth:greek_chiron_archer mystic:sign:sagittarius sys:related_to
ln myth:greek_chiron_archer wisdom @illustrates
set.add name="ontology.constellation_myths" id="myth:greek_chiron_archer"

def "myth:greek_comedy" "Comedy was born of the Dionysian revel — the komos, from which it takes its very name: Aristophanes' Old Comedy, with its wild fantasy, its filth, and its savage mockery of the great men of Athens, and Menander's gentler comedy of everyday manners. The festival of the wine-god gave the world tragedy and its laughing twin together. — Greek theatre"
ln myth:greek_comedy myth sys:is_a
ln myth:greek_comedy myth:laughter sys:part_of
ln myth:greek_comedy deity:dionysus @related_to
ln myth:greek_comedy era:ancient sys:part_of
set.add name="ontology.laughter_thread" id="myth:greek_comedy"

def "myth:greek_cygnus_swan" "The swan of the sky is seen by some as the form Zeus took to court Leda, by others as the grieving friend of Phaethon who was changed into a swan; either way it glides along the Milky Way as Cygnus. — Greek myth"
ln myth:greek_cygnus_swan myth sys:is_a
ln myth:greek_cygnus_swan astro:constellation:cygnus @explains
ln myth:greek_cygnus_swan myth:greek_helios_phaethon @related_to
set.add name="ontology.constellation_myths" id="myth:greek_cygnus_swan"

def "myth:greek_deucalion_flood" "Angered by humankind, Zeus drowns the world in a great flood; Deucalion and Pyrrha alone survive in a wooden chest, and afterward repeople the earth by casting stones over their shoulders, which rise up as men and women. — Greek myth"
ln myth:greek_deucalion_flood myth sys:is_a
ln myth:greek_deucalion_flood flood @explains
set.add name="ontology.world_myths" id="myth:greek_deucalion_flood"

def "myth:greek_dioscuri" "Castor and Pollux, the inseparable twins, share one fate: when mortal Castor dies, immortal Pollux begs to share his own deathlessness, and Zeus sets them together in the sky as Gemini, shining by turns. — Greek myth"
ln myth:greek_dioscuri myth sys:is_a
ln myth:greek_dioscuri astro:constellation:gemini @explains
ln myth:greek_dioscuri astro:star:pollux @explains
ln myth:greek_dioscuri astro:star:castor @explains
ln myth:greek_dioscuri mystic:sign:gemini sys:related_to
ln myth:greek_dioscuri brotherhood @illustrates
set.add name="ontology.constellation_myths" id="myth:greek_dioscuri"

def "myth:greek_draco_ladon" "Ladon, the unsleeping hundred-headed dragon, guards the golden apples of the Hesperides until Heracles slays him in his eleventh labor; the serpent is set coiling about the northern pole as Draco. — Greek myth"
ln myth:greek_draco_ladon myth sys:is_a
ln myth:greek_draco_ladon astro:constellation:draco @explains
ln myth:greek_draco_ladon vigilance @illustrates
set.add name="ontology.constellation_myths" id="myth:greek_draco_ladon"

def "myth:greek_eidolon" "The Greeks knew the phantom-double too: the eidolon, the image or wraith — the shade of the dead in Hades, but also the phantom of the living, the eidolon of Helen that went to Troy and let men die for it while Helen herself sat out the war in Egypt. The image of a person, seen or sent apart from the body — the Greek cousin of the ikiryo. — Greek myth"
ln myth:greek_eidolon myth sys:is_a
ln myth:greek_eidolon myth:living_spirit @parallels
ln myth:greek_eidolon era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:greek_eidolon"

def "myth:greek_europa_bull" "Zeus, in the shape of a gentle white bull, carries the princess Europa across the sea to Crete. The bull is set in the sky as Taurus, its face marked by the red eye Aldebaran and the cluster of the Pleiades riding its shoulder. — Greek myth"
ln myth:greek_europa_bull myth sys:is_a
ln myth:greek_europa_bull astro:constellation:taurus @explains
ln myth:greek_europa_bull astro:star:aldebaran @explains
ln myth:greek_europa_bull mystic:sign:taurus sys:related_to
ln myth:greek_europa_bull myth:greek_pleiades @related_to
set.add name="ontology.constellation_myths" id="myth:greek_europa_bull"

def "myth:greek_ganymede" "Ganymede, fairest of mortal youths, is carried up to Olympus by Zeus's eagle to be cupbearer to the gods; pouring out the waters of heaven, he becomes Aquarius, the water-bearer. — Greek myth"
ln myth:greek_ganymede myth sys:is_a
ln myth:greek_ganymede astro:constellation:aquarius @explains
ln myth:greek_ganymede mystic:sign:aquarius sys:related_to
set.add name="ontology.constellation_myths" id="myth:greek_ganymede"

def "myth:greek_golden_ram" "The ram with the golden fleece bears Phrixus to safety across the sea — though his sister Helle slips and falls, giving her name to the Hellespont — and its hung fleece becomes the prize Jason will seek. The ram is set among the stars as Aries. — Greek myth"
ln myth:greek_golden_ram myth sys:is_a
ln myth:greek_golden_ram astro:constellation:aries @explains
ln myth:greek_golden_ram mystic:sign:aries sys:related_to
ln myth:greek_golden_ram rescue @illustrates
set.add name="ontology.constellation_myths" id="myth:greek_golden_ram"

def "myth:greek_helios_phaethon" "Phaethon, son of Helios, begs to drive the sun-chariot for a day, but cannot hold the horses; the sun careens too near the earth and scorches it, until Zeus strikes him down to save the world. — Greek myth"
ln myth:greek_helios_phaethon myth sys:is_a
ln myth:greek_helios_phaethon sun @explains
ln myth:greek_helios_phaethon hubris @illustrates
set.add name="ontology.world_myths" id="myth:greek_helios_phaethon"

def "myth:greek_iris" "The rainbow is Iris, swift messenger of the gods, who runs along its arc between heaven and earth bearing word from the Olympians to mortals. — Greek myth"
ln myth:greek_iris myth sys:is_a
ln myth:greek_iris rainbow @explains
set.add name="ontology.sky_phenomena" id="myth:greek_iris"

def "myth:greek_libra_scales" "The scales of Astraea, goddess of justice — long reckoned as the claws of the neighboring Scorpion — became the balance Libra, hung in the sky at the place where day and night weigh equal at the equinox. — Greek myth"
ln myth:greek_libra_scales myth sys:is_a
ln myth:greek_libra_scales astro:constellation:libra @explains
ln myth:greek_libra_scales mystic:sign:libra sys:related_to
ln myth:greek_libra_scales balance @illustrates
ln myth:greek_libra_scales myth:greek_astraea @related_to
set.add name="ontology.constellation_myths" id="myth:greek_libra_scales"

def "myth:greek_milky_way" "The band of light across the sky is the milk of Hera, spilled when the infant Heracles was put to her breast and pulled away; the Greeks called it galaxias, the milky circle — the root of our word galaxy. — Greek myth"
ln myth:greek_milky_way myth sys:is_a
ln myth:greek_milky_way milky_way @explains
set.add name="ontology.sky_phenomena" id="myth:greek_milky_way"

def "myth:greek_nemean_lion" "The Nemean lion, whose hide no blade can pierce, is throttled by Heracles as the first of his twelve labors; the beast is raised into the sky as Leo, its heart marked by the star Regulus. — Greek myth"
ln myth:greek_nemean_lion myth sys:is_a
ln myth:greek_nemean_lion astro:constellation:leo @explains
ln myth:greek_nemean_lion astro:star:regulus @explains
ln myth:greek_nemean_lion mystic:sign:leo sys:related_to
set.add name="ontology.constellation_myths" id="myth:greek_nemean_lion"

def "myth:greek_orion" "Orion the giant huntsman, slain and set among the stars, strides across the winter sky; the scorpion that killed him is placed opposite as Scorpius, so that hunter and scorpion never share the heavens at once. — Greek myth"
ln myth:greek_orion myth sys:is_a
ln myth:greek_orion astro:constellation:orion @explains
ln myth:greek_orion astro:constellation:scorpius @explains
set.add name="ontology.world_myths" id="myth:greek_orion"

def "myth:greek_orpheus_lyre" "Orpheus, whose music charmed stones and beasts, descends into the underworld to reclaim his dead wife and nearly wins her back — but loses her forever by glancing back too soon. After his death his lyre is set in the sky as Lyra, its brightest star Vega. — Greek myth"
ln myth:greek_orpheus_lyre myth sys:is_a
ln myth:greek_orpheus_lyre astro:constellation:lyra @explains
ln myth:greek_orpheus_lyre astro:star:vega @explains
ln myth:greek_orpheus_lyre grief @illustrates
ln myth:greek_orpheus_lyre myth:greek_persephone @related_to
ln myth:greek_orpheus_lyre myth:japanese_izanagi_izanami @parallels
set.add name="ontology.constellation_myths" id="myth:greek_orpheus_lyre"

def "myth:greek_pan_seagoat" "Fleeing the monster Typhon, the god Pan plunges into the river; his lower half turns to a fish while his upper stays a goat, and in this sea-goat shape he is set in the sky as Capricornus. — Greek myth"
ln myth:greek_pan_seagoat myth sys:is_a
ln myth:greek_pan_seagoat astro:constellation:capricornus @explains
ln myth:greek_pan_seagoat mystic:sign:capricorn sys:related_to
set.add name="ontology.constellation_myths" id="myth:greek_pan_seagoat"

def "myth:greek_persephone" "Hades carries Persephone into the underworld; her mother Demeter, grieving, lets the earth go barren until the gods intervene. Because Persephone has eaten pomegranate seeds, she must return below for part of each year — and her descent is winter, her return the spring. — Greek myth"
ln myth:greek_persephone myth sys:is_a
ln myth:greek_persephone seasons @explains
ln myth:greek_persephone descent @illustrates
set.add name="ontology.world_myths" id="myth:greek_persephone"

def "myth:greek_perseus_andromeda" "Andromeda is chained to a sea-cliff as a sacrifice to the monster Cetus; the hero Perseus, flying home on the winged horse Pegasus with the Gorgon's head, slays the monster and frees her. The whole story still hangs together in the autumn sky. — Greek myth"
ln myth:greek_perseus_andromeda myth sys:is_a
ln myth:greek_perseus_andromeda astro:constellation:perseus @explains
ln myth:greek_perseus_andromeda astro:constellation:andromeda @explains
ln myth:greek_perseus_andromeda astro:constellation:pegasus @explains
ln myth:greek_perseus_andromeda astro:constellation:cetus @explains
ln myth:greek_perseus_andromeda rescue @illustrates
set.add name="ontology.constellation_myths" id="myth:greek_perseus_andromeda"

def "myth:greek_pisces_fish" "To escape the monster Typhon, Aphrodite and her son Eros take the form of two fish and tie themselves together with a cord so as not to be parted; the bound pair are set in the sky as Pisces. — Greek myth"
ln myth:greek_pisces_fish myth sys:is_a
ln myth:greek_pisces_fish astro:constellation:pisces @explains
ln myth:greek_pisces_fish mystic:sign:pisces sys:related_to
set.add name="ontology.constellation_myths" id="myth:greek_pisces_fish"

def "myth:greek_pleiades" "The seven daughters of Atlas, pursued by Orion, are set by the gods into the sky as a cluster of stars — the Pleiades, riding the shoulder of the Bull. — Greek myth"
ln myth:greek_pleiades myth sys:is_a
ln myth:greek_pleiades pleiades @explains
ln myth:greek_pleiades astro:constellation:taurus @explains
ln myth:greek_pleiades myth:greek_orion @related_to
set.add name="ontology.world_myths" id="myth:greek_pleiades"

def "myth:greek_prometheus" "Prometheus, the Titan who befriends humankind, steals fire from the gods and carries it down to mortals hidden in a fennel stalk. For this theft Zeus chains him to a rock where an eagle devours his ever-renewing liver. — Greek myth"
ln myth:greek_prometheus myth sys:is_a
ln myth:greek_prometheus fire @explains
ln myth:greek_prometheus sacrifice @illustrates
ln myth:greek_prometheus tale:native_coyote_steals_fire @parallels
set.add name="ontology.world_myths" id="myth:greek_prometheus"

def "myth:greek_restless_dead" "And the Greek and Roman dead returned for the same old reasons: the ghost of Patroclus came to Achilles to beg his burial, Odysseus called the pale shades up from the underworld with blood, the Furies hounded the blood-guilty, and at the Roman Lemuria the householder rose by night to placate the restless dead with offerings — as the Japanese welcome the returning ancestors home at Obon. The unresolved dead, East and West, asking the same thing. — Greco-Roman myth"
ln myth:greek_restless_dead myth sys:is_a
ln myth:greek_restless_dead myth:world_ghostlore sys:part_of
ln myth:greek_restless_dead descent @related_to
ln myth:greek_restless_dead word:en:odysseus @related_to
ln myth:greek_restless_dead era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:greek_restless_dead"

def "myth:greek_venus_twin" "The Greeks long thought the morning star Phosphoros, the light-bringer, and the evening star Hesperos two different stars, until it was understood they are one — the planet we call Venus. The Latin morning star, Lucifer, carries the same meaning: light-bearer. — Greek myth"
ln myth:greek_venus_twin myth sys:is_a
ln myth:greek_venus_twin venus @explains
set.add name="ontology.sky_phenomena" id="myth:greek_venus_twin"

def "myth:guardian_beast" "The animal who walks beside a human life: the daemon of Pullman's Lyra, shaped as the soul made visible; the familiar of the witch, the raven on the wizard's shoulder; the patron animal of the hero — Heracles and the lion, Artemis and the deer, Odin's wolves and ravens. The beast-companion as the part of a human life that the human cannot directly see — the shadow made creature, the soul given four legs. — comparative myth"
ln myth:guardian_beast myth sys:is_a
ln myth:guardian_beast myth:human_nature_communion sys:part_of
ln myth:guardian_beast myth:shaman @related_to
ln myth:guardian_beast myth:exorcist @related_to
ln myth:guardian_beast era:ancient sys:part_of
set.add name="ontology.communion_thread" id="myth:guardian_beast"

def "myth:hardboiled" "The hardboiled story rose in the American pulps, in Black Mask magazine, against the tea-and-vicarage puzzle: Dashiell Hammett, who had been a real Pinkerton detective, wrote crime as it was — terse, violent, and corrupt, his Sam Spade and his nameless Continental Op moving through a city where everyone lies and the law is for sale. Murder given back to the people who really commit it. — genre history"
ln myth:hardboiled myth sys:is_a
ln myth:hardboiled myth:detective_fiction sys:part_of
ln myth:hardboiled myth:golden_age_mystery @reacts_against
ln myth:hardboiled era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:hardboiled"

def "myth:harry_potter" "And the broad modern flowering: Harry Potter, the orphan called from a cupboard to a hidden school of witchcraft and wizardry, who must face the dark wizard whose killing curse he alone ever survived. The hero's journey run through a whole world of spells and wands and houses — and the wizard's curse set at its very heart. It made magic the common dream of a generation. — contemporary literature"
ln myth:harry_potter myth sys:is_a
ln myth:harry_potter myth:magic_in_fiction sys:part_of
ln myth:harry_potter myth:literary_wizard @adapts
ln myth:harry_potter myth:the_curse @related_to
ln myth:harry_potter myth:monomyth @related_to
ln myth:harry_potter myth:secondary_world_fantasy @related_to
ln myth:harry_potter era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:harry_potter"

def "myth:heracles_apotheosis" "Poisoned at the last by the Hydra's venom borne on a treacherous gift, Heracles built his own pyre and was burned; but Zeus raised his immortal part to Olympus, where the labor-worn hero became a god, and knelt forever among the stars as the constellation Hercules. — Greek myth"
ln myth:heracles_apotheosis myth sys:is_a
ln myth:heracles_apotheosis heracles @related_to
ln myth:heracles_apotheosis astro:constellation:hercules @explains
ln myth:heracles_apotheosis redemption @illustrates
set.add name="ontology.hero_myths" id="myth:heracles_apotheosis"

def "myth:heracles_apples" "Eleventh Labor: the golden apples of the Hesperides, guarded by the never-sleeping hundred-headed dragon Ladon at the world's western edge, where Atlas holds up the sky. Heracles won the apples — by some tellings slaying Ladon, by others having Atlas fetch them — and the dragon was set in the sky as Draco, coiled about the pole. — Greek myth"
ln myth:heracles_apples myth sys:is_a
ln myth:heracles_apples myth:heracles_twelve_labors sys:part_of
ln myth:heracles_apples myth:greek_draco_ladon @related_to
ln myth:heracles_apples astro:constellation:draco @explains
set.add name="ontology.hero_myths" id="myth:heracles_apples"

def "myth:heracles_belt" "Ninth Labor: the Belt of Hippolyta, queen of the Amazons. She would have given it freely, but Hera stirred the Amazons against him, and Heracles won the belt in battle. — Greek myth"
ln myth:heracles_belt myth sys:is_a
ln myth:heracles_belt myth:heracles_twelve_labors sys:part_of
set.add name="ontology.hero_myths" id="myth:heracles_belt"

def "myth:heracles_birds" "Sixth Labor: the Stymphalian Birds, man-eating birds with bronze beaks. Athena gave Heracles a bronze rattle to startle them from their marsh into the air, where he shot them down. — Greek myth"
ln myth:heracles_birds myth sys:is_a
ln myth:heracles_birds myth:heracles_twelve_labors sys:part_of
set.add name="ontology.hero_myths" id="myth:heracles_birds"

def "myth:heracles_boar" "Fourth Labor: the Erymanthian Boar, a giant beast ravaging the hills. Heracles drove it into deep snow, wearied it, and bore it back alive on his shoulders. — Greek myth"
ln myth:heracles_boar myth sys:is_a
ln myth:heracles_boar myth:heracles_twelve_labors sys:part_of
set.add name="ontology.hero_myths" id="myth:heracles_boar"

def "myth:heracles_bull" "Seventh Labor: the Cretan Bull, the fire-snorting bull that had sired the Minotaur. Heracles wrestled it down and carried it living from Crete. — Greek myth"
ln myth:heracles_bull myth sys:is_a
ln myth:heracles_bull myth:heracles_twelve_labors sys:part_of
set.add name="ontology.hero_myths" id="myth:heracles_bull"

def "myth:heracles_cattle" "Tenth Labor: the Cattle of Geryon, the three-bodied giant of the far west. Heracles slew him and drove the herd home across the world, raising the Pillars of Hercules at the strait as he went. — Greek myth"
ln myth:heracles_cattle myth sys:is_a
ln myth:heracles_cattle myth:heracles_twelve_labors sys:part_of
set.add name="ontology.hero_myths" id="myth:heracles_cattle"

def "myth:heracles_cerberus" "Twelfth Labor: Cerberus, the three-headed hound that guards the gate of the dead. Heracles went down living into Hades, wrestled the beast bare-handed, and carried it up to the daylight and back — the hero who went down to death and returned. — Greek myth"
ln myth:heracles_cerberus myth sys:is_a
ln myth:heracles_cerberus myth:heracles_twelve_labors sys:part_of
ln myth:heracles_cerberus descent @illustrates
ln myth:heracles_cerberus mortality @illustrates
set.add name="ontology.hero_myths" id="myth:heracles_cerberus"

def "myth:heracles_frees_prometheus" "On his wanderings Heracles came to the bound Prometheus and shot the eagle that gnawed the Titan's liver, setting the fire-bringer free. That eagle is remembered in the sky as Aquila. — Greek myth"
ln myth:heracles_frees_prometheus myth sys:is_a
ln myth:heracles_frees_prometheus heracles @related_to
ln myth:heracles_frees_prometheus myth:greek_prometheus @related_to
ln myth:heracles_frees_prometheus myth:greek_aquila_eagle @related_to
set.add name="ontology.hero_myths" id="myth:heracles_frees_prometheus"

def "myth:heracles_hind" "Third Labor: the Ceryneian Hind, the golden-horned deer sacred to Artemis, swifter than an arrow. Heracles pursued it a full year and took it alive, without harm, sparing the goddess's anger. — Greek myth"
ln myth:heracles_hind myth sys:is_a
ln myth:heracles_hind myth:heracles_twelve_labors sys:part_of
ln myth:heracles_hind patience @illustrates
set.add name="ontology.hero_myths" id="myth:heracles_hind"

def "myth:heracles_hydra" "Second Labor: the Lernaean Hydra, the many-headed water-serpent that grew two heads for each one cut. Heracles seared each stump as it fell, and crushed the giant crab Hera sent to bite his heel. The serpent became the constellation Hydra, and the crab the constellation Cancer beside it. — Greek myth"
ln myth:heracles_hydra myth sys:is_a
ln myth:heracles_hydra myth:heracles_twelve_labors sys:part_of
ln myth:heracles_hydra astro:constellation:hydra @explains
ln myth:heracles_hydra myth:greek_cancer_crab @related_to
ln myth:heracles_hydra perseverance @illustrates
set.add name="ontology.hero_myths" id="myth:heracles_hydra"

def "myth:heracles_lion" "First Labor: the Nemean Lion, whose hide no weapon could pierce. Heracles strangled it in his bare arms and wore its skin ever after as armor. The Greeks set the beast in the sky as Leo, the royal star Regulus at its heart. — Greek myth"
ln myth:heracles_lion myth sys:is_a
ln myth:heracles_lion myth:heracles_twelve_labors sys:part_of
ln myth:heracles_lion myth:greek_nemean_lion @related_to
ln myth:heracles_lion astro:constellation:leo @explains
ln myth:heracles_lion strength @illustrates
set.add name="ontology.hero_myths" id="myth:heracles_lion"

def "myth:heracles_mares" "Eighth Labor: the Mares of Diomedes, horses made savage on a diet of human flesh. Heracles overcame them, by some tellings by feeding them their cruel master, and led them tamed away. — Greek myth"
ln myth:heracles_mares myth sys:is_a
ln myth:heracles_mares myth:heracles_twelve_labors sys:part_of
set.add name="ontology.hero_myths" id="myth:heracles_mares"

def "myth:heracles_stables" "Fifth Labor: the Augean Stables, uncleaned for thirty years. Rather than dig, Heracles broke the banks of two rivers and turned their flood through the stalls, cleansing all in a single day. — Greek myth"
ln myth:heracles_stables myth sys:is_a
ln myth:heracles_stables myth:heracles_twelve_labors sys:part_of
ln myth:heracles_stables ingenuity @illustrates
set.add name="ontology.hero_myths" id="myth:heracles_stables"

def "myth:heracles_twelve_labors" "The Twelve Labors — the cycle of tasks set Heracles in penance, each a monster mastered or a marvel won; four of them the Greeks fixed in the sky as constellations, so the hero's deeds wheel nightly overhead. — Greek myth"
ln myth:heracles_twelve_labors myth sys:is_a
ln myth:heracles_twelve_labors heracles @related_to
ln myth:heracles_twelve_labors perseverance @illustrates
set.add name="ontology.hero_myths" id="myth:heracles_twelve_labors"

def "myth:heracles_wounds_chiron" "A stray arrow of Heracles, dipped in the Hydra's venom, struck the wise centaur Chiron, who could not die of immortality yet could not bear the pain; he gave up his deathlessness, and Zeus set him in the sky — by many accounts as the archer, by others as the Centaur. — Greek myth"
ln myth:heracles_wounds_chiron myth sys:is_a
ln myth:heracles_wounds_chiron heracles @related_to
ln myth:heracles_wounds_chiron myth:greek_chiron_archer @related_to
set.add name="ontology.hero_myths" id="myth:heracles_wounds_chiron"

def "myth:hermes_cattle_lyre" "On the very day of his birth Hermes slips from his cradle, steals the cattle of Apollo, and drives them backward to confound their trail. Finding a tortoise, he strings its shell into the first lyre; and when Apollo tracks him down, the infant charms him with the new music and trades the lyre for the stolen herd and the god's friendship. The trickster's first day: a theft, an invention, and a deal. — Greek myth"
ln myth:hermes_cattle_lyre myth sys:is_a
ln myth:hermes_cattle_lyre deity:hermes @related_to
ln myth:hermes_cattle_lyre word:ar:السلحفاة @related_to
ln myth:hermes_cattle_lyre myth:greek_orpheus_lyre @related_to
ln myth:hermes_cattle_lyre theft @illustrates
set.add name="ontology.trickster_myths" id="myth:hermes_cattle_lyre"

def "myth:hindu_churning_ocean" "Gods and demons together churn the cosmic ocean of milk, using a mountain as the churning-rod and the world-serpent as the rope, to draw forth the nectar of immortality — and with it rise the moon, a deadly poison, and many treasures of the world. — Hindu myth"
ln myth:hindu_churning_ocean myth sys:is_a
ln myth:hindu_churning_ocean creation @explains
ln myth:hindu_churning_ocean moon @explains
ln myth:hindu_churning_ocean immortality @illustrates
set.add name="ontology.world_myths" id="myth:hindu_churning_ocean"

def "myth:hindu_hiranyagarbha" "Upon the primeval waters floats a golden egg, the Hiranyagarbha, the 'golden womb'; from it the creator is born, and out of it unfold the heavens, the earth, and all the worlds. — Hindu myth"
ln myth:hindu_hiranyagarbha myth sys:is_a
ln myth:hindu_hiranyagarbha myth:creation_cosmic_egg sys:part_of
ln myth:hindu_hiranyagarbha creation @explains
set.add name="ontology.creation_myths" id="myth:hindu_hiranyagarbha"

def "myth:hindu_manu_flood" "Manu, the first man, spares a tiny fish that begs his protection; it grows vast, and reveals itself as a saviour come to warn him of a world-drowning flood. At its bidding Manu builds a ship and, when the waters rise, ties it to the great horn of the fish, which tows him to a northern mountain peak. From Manu, the sole survivor, mankind begins anew. — Hindu myth (Matsya)"
ln myth:hindu_manu_flood myth sys:is_a
ln myth:hindu_manu_flood myth:world_flood_myths sys:part_of
ln myth:hindu_manu_flood flood @explains
ln myth:hindu_manu_flood myth:mesopotamian_flood @parallels
set.add name="ontology.flood_myths" id="myth:hindu_manu_flood"

def "myth:hindu_purusha" "The gods perform the first sacrifice upon Purusha, the cosmic Person, and from his offered body come all things: the moon from his mind, the sun from his eye, the sky from his head, the earth from his feet, the creatures, the sacred chants, and the orders of human society. — Hindu myth (Rigveda)"
ln myth:hindu_purusha myth sys:is_a
ln myth:hindu_purusha myth:creation_world_from_body sys:part_of
ln myth:hindu_purusha creation @explains
set.add name="ontology.creation_myths" id="myth:hindu_purusha"

def "myth:hindu_rahu" "The demon Rahu sips the gods' nectar of immortality in disguise; the sun and moon expose him and Vishnu strikes off his head — but the head, now immortal, lives on, and forever chases and swallows the sun and moon in revenge. As he has no body, they soon slip out of his severed neck, and the eclipse passes. — Hindu myth"
ln myth:hindu_rahu myth sys:is_a
ln myth:hindu_rahu eclipse @explains
ln myth:hindu_rahu myth:hindu_churning_ocean @related_to
ln myth:hindu_rahu myth:norse_sun_wolves @parallels
set.add name="ontology.sky_phenomena" id="myth:hindu_rahu"

def "myth:horror_alien" "The Other from beyond, where horror meets science fiction: the shape-stealing Thing that could wear any face, the parasite of Alien that bursts from the body that bore it, and Lovecraft's eldritch gods who are alien and cosmos at once. The alien is the ultimate outsider — and in the body-horror it spawns, the flesh itself is made unsafe. — genre history"
ln myth:horror_alien myth sys:is_a
ln myth:horror_alien myth:horror_bestiary sys:part_of
ln myth:horror_alien myth:cosmic_horror @related_to
ln myth:horror_alien myth:sf_franchise_myth @related_to
ln myth:horror_alien era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:horror_alien"

def "myth:horror_bestiary" "The great creatures of horror, four shapes of dread: the native spirit that shares our world (the yokai), the monster that crosses every boundary, the dead that rise (the zombie), and the Other that comes from beyond (the alien). — genre history"
ln myth:horror_bestiary myth sys:related_to
ln myth:horror_bestiary myth:horror_fiction @related_to
set.add name="ontology.narrative_genres" id="myth:horror_bestiary"

def "myth:horror_crossing" "And the creatures will not keep to their kinds: the vampire is a plague and the zombie a contagion; the eldritch alien is a cosmic god and the kaiju a force of nature; the yokai is at once spirit, monster, and ghost. Horror's bestiary is one web of dread, crossing every border it draws — for every monster, in the end, is the same returning fear in a different mask. — genre theory"
ln myth:horror_crossing myth sys:is_a
ln myth:horror_crossing myth:horror_bestiary sys:part_of
ln myth:horror_crossing myth:monster_as_fear @related_to
ln myth:horror_crossing myth:dracula_vampire @related_to
ln myth:horror_crossing era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:horror_crossing"

def "myth:horror_fiction" "Horror — the literature of fear — and its enduring engine, the monster: the figure in which a people gives a body to what it dreads, so that the nameless can be faced, fled, or fought. — genre history"
ln myth:horror_fiction myth sys:related_to
set.add name="ontology.narrative_genres" id="myth:horror_fiction"

def "myth:hsi_ho_astronomers" "The Chinese tell of the court astronomers Hsi and Ho, who in drunken neglect failed to foresee and prepare for an eclipse, and were put to death for it. Whether tale or history, it shows how early and how heavily a state leaned on foretelling the sky — the prediction of the eclipse made a duty of office. — Chinese tradition"
ln myth:hsi_ho_astronomers myth sys:is_a
ln myth:hsi_ho_astronomers eclipse @related_to
ln myth:hsi_ho_astronomers myth:omen_to_prediction sys:part_of
set.add name="ontology.foreknowledge" id="myth:hsi_ho_astronomers"

def "myth:human_nature_communion" "The broad communion: the fact that humans have always lived inside a world of other minds — animal, vegetable, spirit — and have always known it. Not dominion but kinship; not the nature-documentary gaze but the hunter's prayer, the farmer's calendar, the shaman's climb, the child who names the spider. One of the deepest and most persistent threads in the whole of human myth and story. — comparative myth"
ln myth:human_nature_communion myth sys:related_to
ln myth:human_nature_communion myth:human_nature_communion sys:part_of
set.add name="ontology.communion_thread" id="myth:human_nature_communion"

def "myth:ie_dawn" "The Dawn-Goddess — the ever-young maiden of the morning, *Hausos, who opens the gates of day and is reborn each dawn though she ages mortals: Greek Eos, Roman Aurora, Vedic Ushas, Baltic Aušra. One goddess of the daybreak across the whole family. — comparative mythology"
ln myth:ie_dawn myth sys:is_a
ln myth:ie_dawn deity:ushas @cognate_of
ln myth:ie_dawn dawn @explains
set.add name="ontology.indoeuropean_nexus" id="myth:ie_dawn"

def "myth:ie_divine_twins" "The Divine Twins — the youthful horse-riding brothers, sons of the Sky-god, who rescue sailors and ride beside the dawn: the Greek Dioscuri, Castor and Pollux, and the Vedic Ashvins, with kin among the Baltic 'sons of God'. The Greeks set their twins in the sky as Gemini — so the Indo-European twins shine as a constellation. — comparative mythology"
ln myth:ie_divine_twins myth sys:is_a
ln myth:ie_divine_twins myth:greek_dioscuri @cognate_of
ln myth:ie_divine_twins deity:ashvins @cognate_of
ln myth:ie_divine_twins astro:constellation:gemini @explains
ln myth:ie_divine_twins twins @illustrates
set.add name="ontology.indoeuropean_nexus" id="myth:ie_divine_twins"

def "myth:ie_fire" "The Sacred Fire — the living flame of the hearth and the altar, both a god and the carrier of offerings to the gods: the Vedic Agni, whose name is the very Latin word ignis (and Slavic ogon); beside it stands the Iranian Atar, the fire of the Zoroastrian temples. The flame that bridges earth and heaven, named almost the same across half the world. — comparative mythology"
ln myth:ie_fire myth sys:is_a
ln myth:ie_fire deity:agni @cognate_of
ln myth:ie_fire deity:atar @parallels
ln myth:ie_fire fire @explains
set.add name="ontology.indoeuropean_nexus" id="myth:ie_fire"

def "myth:ie_mitra" "The God of the Covenant — the Indo-Iranian god of the sworn bond and the light that sees it kept: the Vedic Mitra and the Iranian Mithra, one god older than the parting of India and Iran, and the source of the name of the Roman mystery-god Mithras, whose worship rivalled early Christianity. — comparative mythology"
ln myth:ie_mitra myth sys:is_a
ln myth:ie_mitra deity:mitra @cognate_of
ln myth:ie_mitra deity:mithra @cognate_of
ln myth:ie_mitra sun @related_to
set.add name="ontology.indoeuropean_nexus" id="myth:ie_mitra"

def "myth:ie_serpent_slayer" "The Serpent-Slayer — the storm-hero who kills the great serpent or dragon that withholds the waters or threatens the order of the world: Vedic Indra smites Vritra and frees the rivers; Zeus blasts Typhon; Thor battles the world-serpent; the Iranian Verethragna 'smites resistance' (kin to Indra's own epithet). Beyond the family the same combat echoes — Marduk splitting Tiamat, Susanoo slaying the eight-headed Orochi. The oldest reconstructed Indo-European story. — comparative mythology"
ln myth:ie_serpent_slayer myth sys:is_a
ln myth:ie_serpent_slayer deity:indra @cognate_of
ln myth:ie_serpent_slayer deity:verethragna @cognate_of
ln myth:ie_serpent_slayer deity:zeus @related_to
ln myth:ie_serpent_slayer deity:thor @related_to
ln myth:ie_serpent_slayer myth:babylonian_enuma_elish @parallels
ln myth:ie_serpent_slayer deity:susanoo @parallels
set.add name="ontology.indoeuropean_nexus" id="myth:ie_serpent_slayer"

def "myth:ie_sky_father" "The Sky-Father — the chief god of the Proto-Indo-Europeans, the bright day-sky personified, whose name *Dyeus ph2ter ('Sky-Father') is the literal source of Greek Zeus, Roman Jupiter (Dyeus-piter), and Vedic Dyaus Pita, and lies behind the Norse Tyr. The same root gives Latin deus and the word 'day'. The single deepest junction of Indo-European myth. — comparative mythology"
ln myth:ie_sky_father myth sys:is_a
ln myth:ie_sky_father deity:zeus @cognate_of
ln myth:ie_sky_father word:la:jupiter @cognate_of
ln myth:ie_sky_father deity:dyaus @cognate_of
ln myth:ie_sky_father sky @explains
set.add name="ontology.indoeuropean_nexus" id="myth:ie_sky_father"

def "myth:indiana_jones" "Indiana Jones revived the whole pulp adventure: the archaeologist in his battered hat, racing villains across the globe for sacred relics — the Ark of the Covenant, the Holy Grail itself. A loving homage to the cliffhanger serials of the 1930s and to Haggard's Quatermain, the lost-world adventure reborn for the age of the blockbuster, where the treasure sought is a holy thing. — adventure cinema"
ln myth:indiana_jones myth sys:is_a
ln myth:indiana_jones myth:adventure_modern sys:part_of
ln myth:indiana_jones myth:lost_world @adapts
ln myth:indiana_jones myth:arthurian_cycle @related_to
ln myth:indiana_jones myth:film_myth @related_to
ln myth:indiana_jones era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:indiana_jones"

def "myth:iroquois_sky_woman" "Sky-Woman falls through a hole in the sky-world toward a shoreless sea. The water-birds rise to bear her up gently, and the animals dive in turn for mud from the deep; the muskrat, last and least, brings up a single pawful at the cost of its life. Spread upon the back of the Great Turtle, the mud grows into the land — Turtle Island. — Haudenosaunee (Iroquois) myth"
ln myth:iroquois_sky_woman myth sys:is_a
ln myth:iroquois_sky_woman myth:creation_earth_diver sys:part_of
ln myth:iroquois_sky_woman creation @explains
ln myth:iroquois_sky_woman sacrifice @illustrates
set.add name="ontology.creation_myths" id="myth:iroquois_sky_woman"

def "myth:isekai_otherworld" "The isekai — the tale of one carried bodily into another world — is the oldest journey made a genre of its own: the crossing into the otherworld and the road home, the hero's call answered by stepping through. The descent and the secondary world, entered in person. — anime history"
ln myth:isekai_otherworld myth sys:is_a
ln myth:isekai_otherworld myth:anime_modes sys:part_of
ln myth:isekai_otherworld descent @related_to
ln myth:isekai_otherworld myth:secondary_world_fantasy @related_to
ln myth:isekai_otherworld myth:monomyth @related_to
ln myth:isekai_otherworld era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:isekai_otherworld"

def "myth:japanese_amaterasu_cave" "Affronted by her brother's violence, the sun-goddess Amaterasu hides in a cave and seals it, and the world falls dark. The gods gather to lure her out with revelry, laughter, and a mirror in which she glimpses her own radiance; drawn forth in curiosity, she is sealed out of the cave, and light returns to the world. — Japanese myth (Kojiki)"
ln myth:japanese_amaterasu_cave myth sys:is_a
ln myth:japanese_amaterasu_cave sun @explains
ln myth:japanese_amaterasu_cave dawn @explains
ln myth:japanese_amaterasu_cave eclipse @explains
set.add name="ontology.world_myths" id="myth:japanese_amaterasu_cave"

def "myth:japanese_izanagi_izanami" "The creator pair Izanagi and Izanami churn the first islands into being; but Izanami dies in childbirth and goes to Yomi, the land of the dead. Izanagi follows to bring her back, breaks the taboo of looking upon her corrupted form, and flees, sealing the boundary — and so death enters the world for good. — Japanese myth (Kojiki)"
ln myth:japanese_izanagi_izanami myth sys:is_a
ln myth:japanese_izanagi_izanami creation @explains
ln myth:japanese_izanagi_izanami mortality @explains
ln myth:japanese_izanagi_izanami myth:greek_persephone @parallels
set.add name="ontology.world_myths" id="myth:japanese_izanagi_izanami"

def "myth:jason_clashing_rocks" "The way to Colchis lay through the Symplegades, the Clashing Rocks that ground together and crushed any ship between them. On counsel, Jason first loosed a dove to dart through; it lost only its tail-feathers, and the Argo followed hard behind as the rocks rebounded, losing only its stern-ornament. — Greek myth"
ln myth:jason_clashing_rocks myth sys:is_a
ln myth:jason_clashing_rocks jason @related_to
set.add name="ontology.hero_myths" id="myth:jason_clashing_rocks"

def "myth:jason_golden_fleece" "To reclaim his stolen throne, Jason is sent by the usurper Pelias after the Golden Fleece — the hide of the golden ram that once bore the children Phrixus and Helle to safety (Helle falling on the way into the strait that bears her name, the Hellespont). The ram became the constellation Aries, and its fleece hangs in distant Colchis, guarded by a sleepless dragon. — Greek myth"
ln myth:jason_golden_fleece myth sys:is_a
ln myth:jason_golden_fleece jason @related_to
ln myth:jason_golden_fleece myth:greek_golden_ram @related_to
ln myth:jason_golden_fleece astro:constellation:aries @related_to
set.add name="ontology.hero_myths" id="myth:jason_golden_fleece"

def "myth:jason_medea_betrayal" "Years later Jason put Medea aside to wed a king's daughter for advantage, forgetting all her craft had won him; her revenge was fearful. As Theseus abandoned Ariadne whose thread had saved him, so Jason abandoned Medea — the hero who forsakes the foreign woman that made his triumph possible. — Greek myth"
ln myth:jason_medea_betrayal myth sys:is_a
ln myth:jason_medea_betrayal jason @related_to
ln myth:jason_medea_betrayal medea @related_to
ln myth:jason_medea_betrayal myth:theseus_ariadne_crown @parallels
ln myth:jason_medea_betrayal betrayal @illustrates
set.add name="ontology.hero_myths" id="myth:jason_medea_betrayal"

def "myth:jason_medea_tasks" "King Aeetes would yield the Fleece only if Jason yoked his fire-breathing bronze bulls, ploughed a field and sowed it with a dragon's teeth, and survived the armed warriors that sprang up. Medea, in love with him, gave him a fireproof balm and the trick of setting the earth-born men to kill one another, then drugged the sleepless dragon so he could lift the Fleece and flee with her. — Greek myth"
ln myth:jason_medea_tasks myth sys:is_a
ln myth:jason_medea_tasks jason @related_to
ln myth:jason_medea_tasks medea @related_to
set.add name="ontology.hero_myths" id="myth:jason_medea_tasks"

def "myth:journey_to_west" "The Ming novel Journey to the West: the Monkey King Sun Wukong, born of stone, a trickster and rebel who storms heaven itself, then is bound to guard the monk on his pilgrimage west to fetch the Buddhist sutras. China's great trickster-hero, between heaven-stormer and pilgrim. — Chinese literature"
ln myth:journey_to_west myth sys:is_a
ln myth:journey_to_west trickster @related_to
ln myth:journey_to_west myth:buddhist_deva @related_to
ln myth:journey_to_west era:early_modern sys:part_of
ln myth:journey_to_west myth:human_nature_communion sys:part_of
set.add name="ontology.narrative_genres" id="myth:journey_to_west"

def "myth:khoisan_milky_way" "A girl of the early race, sitting in the dark, threw the embers and white wood-ash of her fire up into the sky to make a road of light so that people could find their way home by night; the red sparks and white ash became the red and white stars of the Milky Way. — San (Khoisan) star-lore"
ln myth:khoisan_milky_way myth sys:is_a
ln myth:khoisan_milky_way milky_way @explains
set.add name="ontology.sky_phenomena" id="myth:khoisan_milky_way"

def "myth:kurukshetra" "The Mahabharata tells of the war at Kurukshetra, where kinsmen destroy one another and whole armies fall, the heroic age ending in slaughter so total that it marks the turning into our own darker age, the Kali Yuga. The memory of catastrophic war framed as the death of an age of the world. — Hindu epic"
ln myth:kurukshetra myth sys:is_a
ln myth:kurukshetra war @explains
set.add name="ontology.war_memory" id="myth:kurukshetra"

def "myth:kyogen" "Japan set its laughter beside its gravest art: kyogen, the 'wild words', the comic plays performed between the solemn Noh — the cheeky servant Taro Kaja outwitting his lord, the everyday turned gently absurd. And off the stage, the lone rakugo storyteller with his single sly punchline, and the manzai duo of straight-man and fool. The people's laughter, framed by the most refined of theatres — and its very name a 'madness of words'. — Japanese theatre"
ln myth:kyogen myth sys:is_a
ln myth:kyogen myth:laughter sys:part_of
ln myth:kyogen myth:noh @related_to
ln myth:kyogen era:medieval sys:part_of
set.add name="ontology.laughter_thread" id="myth:kyogen"

def "myth:lafcadio_hearn" "Lafcadio Hearn is the world's ghost-lore gathered into one life. Born on a Greek isle to a Greek mother and an Irish father — his very name from the island of Lefkada — raised among the ghosts of Ireland, steeped in the Creole and voodoo tales of New Orleans, and at last made Japanese as Koizumi Yakumo, who set down the ghost stories of Japan in Kwaidan: Yuki-onna the snow-woman, the faceless mujina, blind Hoichi and the Heike dead. Greek, Irish, American, Japanese — one hand threading them all. — literary history"
ln myth:lafcadio_hearn myth sys:is_a
ln myth:lafcadio_hearn myth:world_ghostlore sys:part_of
ln myth:lafcadio_hearn myth:ghost_story_kaidan @adapts
ln myth:lafcadio_hearn myth:yokai @related_to
ln myth:lafcadio_hearn era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:lafcadio_hearn"

def "myth:lament_for_ur" "When Ur fell to its enemies, the Sumerians made a lament: the goddess Ningal weeping over her ruined city, its walls broken, its people scattered, its streets full of the dead. It began a whole genre of city-laments — the formal memory of the sack of a city, grief shaped into liturgy. — Sumerian literature"
ln myth:lament_for_ur myth sys:is_a
ln myth:lament_for_ur war @explains
ln myth:lament_for_ur myth:curse_of_akkad @related_to
set.add name="ontology.war_memory" id="myth:lament_for_ur"

def "myth:laughter" "Laughter, the people's own art: the comedy and the clowning that every age has built into its festivals and its theatres, from the Greek wine-revel and the kyogen stage to the modern comedian. A great swell crossing every land and age — and forever mixed, as Don Quixote shows, with folly and madness. — comparative literature (thematic weft)"
ln myth:laughter myth sys:related_to
set.add name="ontology.laughter_thread" id="myth:laughter"

def "myth:laughter_and_truth" "And the thread beneath it all: laughter and madness both break the ordinary order of things. The fool, the carnival, the mad knight, the 'wild words' of kyogen — each steps outside the sane and the proper, and from outside can say what the sane and the powerful may not. Folly is the freedom to tell the truth; the jester and the madman are the only ones who never lie. A weft that crosses every land and age. — comparative literature (reflexive)"
ln myth:laughter_and_truth myth sys:is_a
ln myth:laughter_and_truth myth:laughter sys:part_of
ln myth:laughter_and_truth myth:mad_idealist @related_to
ln myth:laughter_and_truth myth:human_nature_communion @related_to
ln myth:laughter_and_truth era:contemporary sys:part_of
set.add name="ontology.laughter_thread" id="myth:laughter_and_truth"

def "myth:layla_majnun" "Layla and Majnun: Qays, driven mad by a love for Layla that her family forbids, wanders the desert as 'the madman', singing her name until both are consumed by longing and die apart. The great tragic love of the Persian and Arabic world — and, to the Sufis, a figure for the soul gone mad with love of God. — Persian/Arabic literature"
ln myth:layla_majnun myth sys:is_a
ln myth:layla_majnun myth:love_story sys:part_of
ln myth:layla_majnun era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:layla_majnun"

def "myth:le_carre" "John le Carre, who had served in British intelligence, made the spy novel literature: betrayal as its true subject, the mole within the service its great fear (drawn from the real treason of the Cambridge spies), and no clean victory anywhere — only the cost. The anti-Bond, and the conscience of the genre. — genre history"
ln myth:le_carre myth sys:is_a
ln myth:le_carre myth:spy_two_poles sys:part_of
ln myth:le_carre myth:spy_two_poles @reacts_against
ln myth:le_carre era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:le_carre"

def "myth:literary_transmission" "The great inheritance: how the stories of antiquity — its myths and epics, its fables and laments — were carried down into later literature and made new in each age. The @adapts edges trace the descent of a story from its source. — comparative literature"
ln myth:literary_transmission myth sys:related_to
set.add name="ontology.literary_transmission" id="myth:literary_transmission"

def "myth:literary_witch" "The witch, the wizard's shadow-sister: Circe turning men to swine on her island, Medea the sorceress who kills for love and vengeance, Morgan le Fay, and the fairy-tale crone with her poisoned apple and her spinning-wheel curse. The woman of power, feared and reviled for centuries — and reclaimed at last by the modern retellings, who give her back her voice. — genre history"
ln myth:literary_witch myth sys:is_a
ln myth:literary_witch myth:magic_in_fiction sys:part_of
ln myth:literary_witch word:en:medea @related_to
ln myth:literary_witch myth:feminist_retelling @related_to
ln myth:literary_witch myth:carter_bloody_chamber @related_to
ln myth:literary_witch era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:literary_witch"

def "myth:literary_wizard" "The wizard of literature: Merlin who made and guided Arthur, Prospero on his island commanding the spirits of the air until he breaks his staff and drowns his book, Gandalf the grey wanderer drawn from the Norse. The wise mage — half-descended from Odin and the shaman — who guides the hero and wields the deep word of power. — genre history"
ln myth:literary_wizard myth sys:is_a
ln myth:literary_wizard myth:magic_in_fiction sys:part_of
ln myth:literary_wizard myth:shaman @adapts
ln myth:literary_wizard myth:arthurian_cycle @related_to
ln myth:literary_wizard shakespeare @related_to
ln myth:literary_wizard myth:tolkien_legendarium @related_to
ln myth:literary_wizard era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:literary_wizard"

def "myth:little_prince_fox" "The fox of The Little Prince asks to be tamed, and teaches the deepest lesson of the whole communion: that it is the bond you take the trouble to create that makes a creature unique in all the world and beloved, that you stay forever responsible for what you have tamed, and that what truly matters cannot be seen with the eyes but only with the heart. Meaning made wholly of the tie — the proto-word principle, told to a child by a fox. — modern literature (reflexive)"
ln myth:little_prince_fox myth sys:is_a
ln myth:little_prince_fox myth:human_nature_communion sys:part_of
ln myth:little_prince_fox myth:trek_darmok @parallels
ln myth:little_prince_fox myth:magic_of_naming @parallels
ln myth:little_prince_fox era:modern sys:part_of
set.add name="ontology.communion_thread" id="myth:little_prince_fox"

def "myth:living_spirit" "The ikiryo — the spirit of a LIVING person that leaves the body, driven out by a jealousy, a rage, or a longing too fierce to hold, to haunt or to harm another. Rarer and stranger than any ghost of the dead: the haunting done by the living, who may not even know their own spirit has gone wandering. — Japanese folklore"
ln myth:living_spirit myth sys:is_a
ln myth:living_spirit myth:world_ghostlore @related_to
set.add name="ontology.narrative_genres" id="myth:living_spirit"

def "myth:loki_baldr_death" "Loki contrives the death of the beloved god Baldr, guiding the one thing that could harm him — a dart of mistletoe — into the hand of his blind brother, and then blocks his return from the dead. For this the gods bind Loki beneath a serpent that drips venom on his face, his wife Sigyn catching the drops in a bowl; when she turns to empty it, his agonized writhing shakes the earth. — Norse myth (Edda)"
ln myth:loki_baldr_death myth sys:is_a
ln myth:loki_baldr_death deity:loki @related_to
ln myth:loki_baldr_death mortality @illustrates
set.add name="ontology.trickster_myths" id="myth:loki_baldr_death"

def "myth:loki_ragnarok" "At the world's end Loki breaks his bonds and steers the ship of the dead against the gods, and his monstrous children come with him: Fenrir, who swallows the sun, and the world-serpent, who poisons the sky. The trickster who broke the rules becomes at last the breaker of the world. — Norse myth (Edda)"
ln myth:loki_ragnarok myth sys:is_a
ln myth:loki_ragnarok deity:loki @related_to
ln myth:loki_ragnarok myth:norse_ragnarok @related_to
ln myth:loki_ragnarok myth:norse_sun_wolves @related_to
set.add name="ontology.trickster_myths" id="myth:loki_ragnarok"

def "myth:lost_world" "Haggard's King Solomon's Mines sent Allan Quatermain deep into Africa after a lost hoard and a lost kingdom, and made the lost-world adventure: the hidden civilization, the ancient ruin, the cursed treasure. Doyle's plateau of living dinosaurs and Burroughs's Tarzan and his Mars came after it — and so, much later, did Indiana Jones. — adventure literature"
ln myth:lost_world myth sys:is_a
ln myth:lost_world myth:adventure_travel sys:part_of
ln myth:lost_world era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:lost_world"

def "myth:love_story" "The love story — the oldest tale and the most retold — and its darkest, most enduring shape: the lovers the world will not let be, kept apart by feud, by rank, by fate, or by death, whose sorrow is told again and again, age after age. — comparative literature"
ln myth:love_story myth sys:related_to
set.add name="ontology.narrative_genres" id="myth:love_story"

def "myth:lu_xun_old_tales" "Lu Xun's Old Tales Retold reworks the Chinese myths with a modern, satirical edge: Nuwa mending the sky, the archer Houyi grown weary and his wife Chang'e fled to the moon, Yu the Great curbing the flood among careless officials. The old stories turned to indict the China of his own day. — modern Chinese literature"
ln myth:lu_xun_old_tales myth sys:is_a
ln myth:lu_xun_old_tales myth:nonwestern_modernity sys:part_of
ln myth:lu_xun_old_tales myth:chinese_houyi_suns @adapts
ln myth:lu_xun_old_tales myth:chinese_great_yu_flood @adapts
ln myth:lu_xun_old_tales era:modern sys:part_of
set.add name="ontology.literary_transmission" id="myth:lu_xun_old_tales"

def "myth:mad_idealist" "Here the madness runs deepest: Don Quixote, driven out of his wits by his books into believing himself a knight, tilting at windmills he takes for giants — a madman, and yet his mad faith shames a meaner, saner world. The fool and the madman both see what the sane cannot; folly turns, in him, into a kind of truth, and even a kind of grace. — modern literature"
ln myth:mad_idealist myth sys:is_a
ln myth:mad_idealist myth:laughter sys:part_of
ln myth:mad_idealist myth:don_quixote @adapts
ln myth:mad_idealist era:early_modern sys:part_of
set.add name="ontology.laughter_thread" id="myth:mad_idealist"

def "myth:made_servant_rebels" "And its dark heart, already in this archive: the clay Golem that grows too strong for its maker, Frankenstein's abandoned and vengeful creature, and Capek's R.U.R., which gave the world the word 'robot' — from the Czech for drudgery — and in which the made workers rise as one and wipe out mankind. The robot is born, in its very first story, already in revolt. — genre history"
ln myth:made_servant_rebels myth sys:is_a
ln myth:made_servant_rebels myth:artificial_being sys:part_of
ln myth:made_servant_rebels myth:robot_golem @adapts
ln myth:made_servant_rebels myth:frankenstein @related_to
ln myth:made_servant_rebels myth:greek_prometheus @related_to
ln myth:made_servant_rebels era:modern sys:part_of
set.add name="ontology.artificial_being" id="myth:made_servant_rebels"

def "myth:magic" "Magic — the oldest art: the claim that the right word, the right rite, and the bent will can move the world from behind the seen. Long before the wizard of the storybook there were the real workers of magic, from whom he wholly descends. — comparative religion / folklore"
ln myth:magic myth sys:related_to
set.add name="ontology.narrative_genres" id="myth:magic"

def "myth:magic_in_fiction" "From the real workers of magic descends the wizard of story: the staff and the spell-book are the storybook echo of the shaman's drum and the onmyoji's paper servants. In the tale that is not science, magic is almost always the engine that turns it — and the wizard's curse is among the oldest motifs of all. — genre history"
ln myth:magic_in_fiction myth sys:related_to
ln myth:magic_in_fiction myth:magic @related_to
set.add name="ontology.narrative_genres" id="myth:magic_in_fiction"

def "myth:magic_of_naming" "And a deeper note, from Le Guin's Earthsea: there, magic is the knowing of the true name of a thing, for to know its true name is to have power over it — the name being the thing's very being. The oldest magic of all is the word; and the deepest truth of it is the one this archive is built on — that a name is no idle label, but a thing's place in the whole web of names, where its meaning and its power live. — contemporary literature (reflexive)"
ln myth:magic_of_naming myth sys:is_a
ln myth:magic_of_naming myth:magic_in_fiction sys:part_of
ln myth:magic_of_naming myth:secondary_world_fantasy @adapts
ln myth:magic_of_naming myth:trek_darmok @parallels
ln myth:magic_of_naming era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:magic_of_naming"

def "myth:maori_rangi_papa" "Sky-father Rangi and Earth-mother Papa cling together in the dark, and their children are crushed in the narrow black between them. The children take counsel; gentle Tāne of the forests sets his shoulders against the earth and his feet against the sky and slowly thrusts his parents apart, and light pours into the world. Rangi's endless grief for Papa falls still as rain and dew. — Maori myth"
ln myth:maori_rangi_papa myth sys:is_a
ln myth:maori_rangi_papa myth:creation_sky_earth_separation sys:part_of
ln myth:maori_rangi_papa creation @explains
set.add name="ontology.creation_myths" id="myth:maori_rangi_papa"

def "myth:marriage_plot" "Jane Austen perfected the comic pole of the love story: the marriage plot, in which wit and misjudgement and the hard pressures of money and rank are all resolved at last in the right union — Elizabeth and Darcy — ending not in a grave but in a wedding. The fountainhead of the romance novel and the romantic comedy. — modern literature"
ln myth:marriage_plot myth sys:is_a
ln myth:marriage_plot myth:love_story sys:part_of
ln myth:marriage_plot era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:marriage_plot"

def "myth:maui_trickster" "Maui, the Polynesian hero-trickster, belongs among the divine tricksters too: he snared the sun to slow its racing across the sky, fished whole islands up from the sea, won fire for mortals from its underworld keeper, and died at last trying to trick his way past death itself. — Polynesian myth"
ln myth:maui_trickster myth sys:is_a
ln myth:maui_trickster deity:maui @related_to
ln myth:maui_trickster trickster @related_to
ln myth:maui_trickster mortality @illustrates
set.add name="ontology.trickster_myths" id="myth:maui_trickster"

def "myth:maya_hero_twins" "Hunahpu and Xbalanque, the Hero Twins of the Popol Vuh, are summoned down into Xibalba, the underworld, where they outplay and outwit the lords of death at the ball-game and in their deadly houses, defeat them, and rise into the sky as the sun and the moon. — Maya myth (Popol Vuh)"
ln myth:maya_hero_twins myth sys:is_a
ln myth:maya_hero_twins myth:maya_maize_people @related_to
ln myth:maya_hero_twins descent @illustrates
ln myth:maya_hero_twins myth:ie_divine_twins @parallels
set.add name="ontology.pantheons_mesoamerican" id="myth:maya_hero_twins"

def "myth:maya_maize_people" "The gods tried first to make people of mud, who crumbled, and then of wood, who had no hearts and were swept away in the flood. At last they ground white and yellow maize and shaped its dough into true human beings — who saw, and spoke, and gave thanks to their makers. People made of corn. — Maya myth (Popol Vuh)"
ln myth:maya_maize_people myth sys:is_a
ln myth:maya_maize_people myth:creation_by_word sys:part_of
ln myth:maya_maize_people creation @explains
set.add name="ontology.creation_myths" id="myth:maya_maize_people"

def "myth:maya_venus" "To the Maya, Venus was a fierce and dangerous star, the guise of Quetzalcoatl/Kukulkan; its movements were tracked with great care in the codices, and its heliacal rising was an omen of war, the time to strike. — Maya myth"
ln myth:maya_venus myth sys:is_a
ln myth:maya_venus venus @explains
ln myth:maya_venus omen @illustrates
set.add name="ontology.sky_phenomena" id="myth:maya_venus"

def "myth:maya_wooden_people_flood" "In the Popol Vuh, the gods' first peoples fail them: the mud people crumble, and the wooden people, who walk and speak but have no hearts and forget their makers, are destroyed in a great flood and a downpour of resin, while their own pots, grinding-stones, and animals rise up against them. A few flee as the monkeys of the forest. — Maya myth (Popol Vuh)"
ln myth:maya_wooden_people_flood myth sys:is_a
ln myth:maya_wooden_people_flood myth:world_flood_myths sys:part_of
ln myth:maya_wooden_people_flood flood @explains
ln myth:maya_wooden_people_flood creation @related_to
set.add name="ontology.flood_myths" id="myth:maya_wooden_people_flood"

def "myth:mecha_pilot" "The giant robot and its pilot run from Tetsujin and Mazinger to Gundam and Evangelion: the made colossus — the golem grown vast — and the human child who must climb inside and become its soul and its will. The made-being myth, fused with the hero who animates it. — anime history"
ln myth:mecha_pilot myth sys:is_a
ln myth:mecha_pilot myth:anime_modes sys:part_of
ln myth:mecha_pilot myth:robot_golem @adapts
ln myth:mecha_pilot hero @related_to
ln myth:mecha_pilot era:contemporary sys:part_of
ln myth:mecha_pilot myth:artificial_being sys:part_of
set.add name="ontology.narrative_genres" id="myth:mecha_pilot"

def "myth:medieval_matters" "Medieval romance gathered its stories into three great 'Matters': the Matter of Rome (Troy and Thebes, the classical inheritance), the Matter of France (Charlemagne and his knights), and the Matter of Britain (Arthur). The frames into which a whole age poured the old tales. — medieval literature"
ln myth:medieval_matters myth sys:is_a
ln myth:medieval_matters myth:literary_transmission sys:part_of
ln myth:medieval_matters myth:trojan_war_memory @adapts
set.add name="ontology.literary_transmission" id="myth:medieval_matters"

def "myth:medium" "The medium is the living door between worlds: the blind itako of the north who calls up the voices of the dead, the shrine-maiden and the Delphic Pythia possessed and speaking with the god's own voice, the seance-caller of the modern parlour. Where the exorcist drives the spirit out, the medium lets it in — the close cousin of the Noh stage and of the wandering living spirit. — comparative religion"
ln myth:medium myth sys:is_a
ln myth:medium myth:magic sys:part_of
ln myth:medium myth:noh @related_to
ln myth:medium myth:living_spirit @related_to
ln myth:medium myth:ghost_story_kaidan @related_to
ln myth:medium era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:medium"

def "myth:mesoamerican_day_signs" "The Aztec tonalpohualli and the Maya tzolkin are both 260-day sacred calendars of twenty named day-signs turning through thirteen numbers — and many of those twenty signs are creatures: Cipactli the sea-monster, Cuetzpalin the lizard, Coatl the serpent, Ocelotl the jaguar, Cuauhtli the eagle, Calli the deer, Itzcuintli the dog. Time written as a bestiary of twenty beasts turning in a cycle of 260 sacred days. — Mesoamerican tradition"
ln myth:mesoamerican_day_signs myth sys:is_a
ln myth:mesoamerican_day_signs myth:calendar_animals sys:part_of
ln myth:mesoamerican_day_signs myth:human_nature_communion sys:part_of
ln myth:mesoamerican_day_signs myth:maya_venus @related_to
ln myth:mesoamerican_day_signs deity:quetzalcoatl @related_to
ln myth:mesoamerican_day_signs sci:archaeo:chichen_itza @related_to
ln myth:mesoamerican_day_signs era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:mesoamerican_day_signs"

def "myth:mesoamerican_pantheon" "The gods of the Aztec and the Maya — a world kept turning by sacrifice, ruled by the feathered serpent and the smoking mirror, the sun that must be fed and the rain that must be begged, across an age that is the fifth and not the last. — Mesoamerican religion"
ln myth:mesoamerican_pantheon myth sys:is_a
set.add name="ontology.pantheons" id="myth:mesoamerican_pantheon"
set.add name="ontology.pantheons_mesoamerican" id="myth:mesoamerican_pantheon"

def "myth:mesopotamian_flood" "Warned by a god that the divine assembly means to drown humankind, Utnapishtim builds a great sealed boat and bears his family and the animals through the deluge; when the waters fall he releases birds to find dry land, and is granted eternal life. The oldest of the surviving flood stories, told within the Epic of Gilgamesh. — Mesopotamian myth"
ln myth:mesopotamian_flood myth sys:is_a
ln myth:mesopotamian_flood flood @explains
ln myth:mesopotamian_flood myth:greek_deucalion_flood @parallels
set.add name="ontology.world_myths" id="myth:mesopotamian_flood"

def "myth:mesopotamian_gilgamesh_plant" "Seeking to escape death, the hero Gilgamesh wins a plant that restores youth from the seabed, but a serpent steals it while he bathes and at once sheds its skin renewed — which is why snakes slough their skins, and why the gift of unaging life slipped from human hands. — Mesopotamian myth"
ln myth:mesopotamian_gilgamesh_plant myth sys:is_a
ln myth:mesopotamian_gilgamesh_plant mortality @explains
ln myth:mesopotamian_gilgamesh_plant renewal @explains
set.add name="ontology.world_myths" id="myth:mesopotamian_gilgamesh_plant"

def "myth:meteorite_worship" "Stones that fell burning from the sky were taken for gifts or the very bodies of the gods, and set up to be worshipped: the image of Artemis at Ephesus was said to have fallen from heaven, and sacred black stones and pillars marked where the sky-stones came down. The meteorite, seen falling, became a god. — world myth"
ln myth:meteorite_worship myth sys:is_a
ln myth:meteorite_worship sci:astro:impact_events @grounds
ln myth:meteorite_worship comet @related_to
set.add name="ontology.geomyth_nexus" id="myth:meteorite_worship"

def "myth:modern_anthology" "The anthology — the frame that gathers many tales — came down from the Nights and the Decameron into the modern collection: the mythology-anthologies of Bulfinch and Hamilton that carried the old gods to new readers, and the science-fiction and fantasy anthologies that gathered a genre between two covers. The curated gathering, kept as a living form. — modern literature"
ln myth:modern_anthology myth sys:is_a
ln myth:modern_anthology myth:contemporary_inheritance sys:part_of
ln myth:modern_anthology myth:frame_tale_transmission @adapts
set.add name="ontology.literary_transmission" id="myth:modern_anthology"

def "myth:modern_comedy" "The great swell reaches the present: the silent clowns Chaplin and Keaton, straight out of the commedia; the absurd and the nonsense of Carroll and Lear and the Theatre of the Absurd, the comedy of meaninglessness itself; the surreal sketch of Monty Python; and the lone stand-up comedian — the modern court jester, licensed still to mock the king, now upon a stage before millions. — genre history"
ln myth:modern_comedy myth sys:is_a
ln myth:modern_comedy myth:laughter sys:part_of
ln myth:modern_comedy myth:commedia_clown @adapts
ln myth:modern_comedy myth:the_fool @related_to
ln myth:modern_comedy era:contemporary sys:part_of
set.add name="ontology.laughter_thread" id="myth:modern_comedy"

def "myth:modern_horror" "The modern masters and modes: King's small-town American dread and his shape-shifting fear-eater; the slasher's masked boogeyman and the Final Girl who survives him; folk horror, where the old pagan rite and the waiting sacrifice turn the green country to terror; and the social horror that names race and class as the true monster. — genre history"
ln myth:modern_horror myth sys:is_a
ln myth:modern_horror myth:horror_fiction sys:part_of
ln myth:modern_horror myth:monster_as_fear @related_to
ln myth:modern_horror era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:modern_horror"

def "myth:modern_literary_inheritance" "How the ancient story-stock flows into modern literature: parodied into the novel, rediscovered by the Romantics, and laid as a hidden frame beneath the modern world. The newest works are often the oldest stories, made strange. — comparative literature"
ln myth:modern_literary_inheritance myth sys:related_to
ln myth:modern_literary_inheritance myth:literary_transmission @related_to
set.add name="ontology.literary_transmission" id="myth:modern_literary_inheritance"

def "myth:monomyth" "Joseph Campbell, in The Hero with a Thousand Faces, distilled the hero-myths of the world — Gilgamesh, Heracles, the Buddha, and a thousand more — into a single pattern: the call, the departure, the trials and the descent, and the return changed. A scholar's map of the old hero-cycles that then became a conscious template for the storytellers of the modern age. — comparative mythology"
ln myth:monomyth myth sys:is_a
ln myth:monomyth myth:contemporary_inheritance sys:part_of
ln myth:monomyth myth:heracles_twelve_labors @adapts
ln myth:monomyth myth:gilgamesh_epic @adapts
ln myth:monomyth hero @related_to
set.add name="ontology.literary_transmission" id="myth:monomyth"

def "myth:monomyth_questioned" "The very pattern came under question: critics asked whether the one hero's journey, drawn so largely from male and Western heroes, was the only shape a story could take — and answered with the heroine's journey, the communal tale, and the refusal of the chosen-one. The map of the hero, redrawn. — contemporary criticism"
ln myth:monomyth_questioned myth sys:is_a
ln myth:monomyth_questioned myth:critical_retelling sys:part_of
ln myth:monomyth_questioned myth:monomyth @related_to
ln myth:monomyth_questioned era:contemporary sys:part_of
set.add name="ontology.literary_transmission" id="myth:monomyth_questioned"

def "myth:monster_as_fear" "The deep truth of the genre: the monster always means something. The dragon is the chaos to be slain, the vampire the dread of contagion and forbidden desire, the zombie the terror of the mob and the plague, the alien the horror of the truly Other. The monster is fear given flesh — the repressed thing returning, the uncanny that Freud named. — genre theory"
ln myth:monster_as_fear myth sys:is_a
ln myth:monster_as_fear myth:horror_fiction sys:part_of
ln myth:monster_as_fear myth:ie_serpent_slayer @related_to
ln myth:monster_as_fear myth:death_personified @related_to
set.add name="ontology.narrative_genres" id="myth:monster_as_fear"

def "myth:monster_kaiju" "The monster proper — the thing that crosses the boundary, too large or too wrong for the world: from the mythic dragon and the stone-staring Gorgon, and the fossil-bones the ancients read as giants, through Frankenstein's stitched and orphaned man, to the kaiju — Godzilla and his kin — the colossus that must be faced because it cannot be unseen. — genre history"
ln myth:monster_kaiju myth sys:is_a
ln myth:monster_kaiju myth:horror_bestiary sys:part_of
ln myth:monster_kaiju myth:ie_serpent_slayer @related_to
ln myth:monster_kaiju word:en:medusa @related_to
ln myth:monster_kaiju myth:geomythology @related_to
ln myth:monster_kaiju myth:godzilla @related_to
ln myth:monster_kaiju myth:frankenstein @related_to
ln myth:monster_kaiju era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:monster_kaiju"

def "myth:moonstone_lecoq" "The form spread and lengthened: in France, Gaboriau's Monsieur Lecoq worked a case by patient police-craft, and in England, Wilkie Collins's The Moonstone — often called the first detective novel — set the shrewd Sergeant Cuff after a stolen jewel, with the story told in many voices. — genre history"
ln myth:moonstone_lecoq myth sys:is_a
ln myth:moonstone_lecoq myth:detective_fiction sys:part_of
ln myth:moonstone_lecoq myth:poe_dupin @adapts
ln myth:moonstone_lecoq era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:moonstone_lecoq"

def "myth:mythic_automaton" "The made being in myth and craft long before machinery: Hephaestus's golden handmaidens who attend him, and the bronze giant Talos who circled Crete and hurled stones at ships, undone at last by the one vein of ichor in his heel; Pygmalion's ivory woman waked to life by love; the Chinese artificer Yan Shi, whose mechanical man sang and danced and winked at the king's concubines. And then the real clockwork — Vaucanson's duck, Japan's tea-serving karakuri. The ancient dream of the artificial person. — comparative myth / history"
ln myth:mythic_automaton myth sys:is_a
ln myth:mythic_automaton myth:artificial_being sys:part_of
ln myth:mythic_automaton deity:hephaestus @related_to
ln myth:mythic_automaton myth:argo_ship @related_to
ln myth:mythic_automaton era:ancient sys:part_of
set.add name="ontology.artificial_being" id="myth:mythic_automaton"

def "myth:mythical_method" "The modernists laid old myth beneath the new world: Joyce's Ulysses retells the whole Odyssey across a single Dublin day, and Eliot's Waste Land lays the Grail-quest and the dying-and-reviving fertility god under the broken modern city. Myth as the secret frame of the everyday — the 'mythical method'. — modern literature"
ln myth:mythical_method myth sys:is_a
ln myth:mythical_method myth:modern_literary_inheritance sys:part_of
ln myth:mythical_method word:en:odysseus @adapts
ln myth:mythical_method myth:arthurian_cycle @related_to
set.add name="ontology.literary_transmission" id="myth:mythical_method"

def "myth:namazu" "Beneath the islands of Japan lies Namazu, a giant catfish, held down by a god's keystone pressed upon its head. When the god's guard slips, the great fish thrashes, and the land shakes with earthquakes. — Japanese folklore"
ln myth:namazu myth sys:is_a
ln myth:namazu earthquake @explains
set.add name="ontology.geomyth_nexus" id="myth:namazu"

def "myth:naruto_folklore" "Naruto draws on Japanese folklore and yokai: the toad-sage out of the old legend of the gallant Jiraiya, the Nine-Tailed Fox of kitsune-lore sealed away inside the hero, the shinobi of legend made flesh. The folk-tales of Japan grown into a global saga. — anime history"
ln myth:naruto_folklore myth sys:is_a
ln myth:naruto_folklore myth:anime_mythology sys:part_of
ln myth:naruto_folklore myth:yanagita_folklore @related_to
ln myth:naruto_folklore era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:naruto_folklore"

def "myth:ninja_shinobi" "Japan's shinobi, the ninja, were the agents of the feudal age: trained in infiltration, disguise, sabotage, and silent killing, gathering intelligence for warlords from the mountains of Iga and Koga, their craft set down in secret manuals. The spy as a discipline and a shadow-art. — Japanese history"
ln myth:ninja_shinobi myth sys:is_a
ln myth:ninja_shinobi myth:espionage sys:part_of
ln myth:ninja_shinobi myth:naruto_folklore @related_to
ln myth:ninja_shinobi era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:ninja_shinobi"

def "myth:noh" "The Noh theatre, and above all the mugen-no or 'dream Noh' that Zeami perfected: a traveling priest meets a stranger who proves to be a ghost or a living spirit, and who in the second act dances out the passion that binds it — a jealousy, a grief, a warrior's unspent rage — until a prayer sets it free. The stage itself is a threshold where spirits return to be laid to rest: its Aoi no Ue stages Rokujo's living spirit; its Dojoji, a woman whom jealousy turns to a serpent. — Japanese theatre"
ln myth:noh myth sys:is_a
ln myth:noh myth:living_spirit @related_to
ln myth:noh myth:rokujo_ikiryo @adapts
ln myth:noh myth:ghost_story_kaidan @related_to
ln myth:noh era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:noh"

def "myth:noh_yugen" "Zeami's art rests on yugen — the deep, dim, mysterious grace of what is only half-revealed — and on the conviction that the suggested and the unspoken hold more than the shown, that what is left unsaid is the very heart of the thing. It is the aesthetic on which this whole archive is founded: meaning that lives not in the spoken word but in the unspoken relation around it — a word that simply IS, and means only through what surrounds it. — Japanese aesthetics (reflexive)"
ln myth:noh_yugen myth sys:is_a
ln myth:noh_yugen myth:noh sys:part_of
ln myth:noh_yugen myth:trek_darmok @parallels
ln myth:noh_yugen era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:noh_yugen"

def "myth:noir_cain" "Beside the detective ran the darker line of noir: James M. Cain's The Postman Always Rings Twice and Double Indemnity told the crime from the inside, through the doomed lovers who do the killing and are dragged down by it. Not the puzzle of who, but the dread of watching it happen. — genre history"
ln myth:noir_cain myth sys:is_a
ln myth:noir_cain myth:detective_fiction sys:part_of
ln myth:noir_cain myth:hardboiled @related_to
ln myth:noir_cain era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:noir_cain"

def "myth:noir_psychological" "The form turned inward and darker still: Patricia Highsmith told the tale from the killer's own side, her charming Ripley getting clean away, and Ross Macdonald made the private eye a kind of analyst, every present crime the return of a buried family wound. The mystery became the mind. — genre history"
ln myth:noir_psychological myth sys:is_a
ln myth:noir_psychological myth:hardboiled @adapts
ln myth:noir_psychological era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:noir_psychological"

def "myth:nonwestern_modernity" "Modern literature outside the West took up its own inheritance: writers who turned back to the myths of China, India, and Japan not to worship them but to question, remake, and rescue them — the transmission tree, decentred. — comparative literature"
ln myth:nonwestern_modernity myth sys:related_to
ln myth:nonwestern_modernity myth:modern_literary_inheritance @related_to
set.add name="ontology.literary_transmission" id="myth:nonwestern_modernity"

def "myth:norse_bifrost" "Bifröst is the burning rainbow bridge that joins the world of mortals to Asgard, the home of the gods, guarded by watchful Heimdall — and at the world's end it shatters beneath the riders of doom. — Norse myth (Edda)"
ln myth:norse_bifrost myth sys:is_a
ln myth:norse_bifrost rainbow @explains
ln myth:norse_bifrost myth:norse_yggdrasil @related_to
ln myth:norse_bifrost myth:norse_ragnarok @related_to
set.add name="ontology.sky_phenomena" id="myth:norse_bifrost"

def "myth:norse_fimbulwinter" "Before the end of the world, the Norse said, comes the Fimbulwinter: three winters together with no summer between them, the sun giving no warmth, the world locked in killing cold. The dread of an endless winter may keep the memory of the sunless years after the dust-veil of 536, which struck the North so hard. — Norse myth"
ln myth:norse_fimbulwinter myth sys:is_a
ln myth:norse_fimbulwinter myth:norse_ragnarok @related_to
ln myth:norse_fimbulwinter sci:history:event_536 @grounds
set.add name="ontology.geomyth_nexus" id="myth:norse_fimbulwinter"

def "myth:norse_ragnarok" "Ragnarök is the foretold doom of the gods: the wolves devour sun and moon, the World Serpent rises, gods and giants fall together, and the earth sinks beneath the sea — yet from the waters a green world surfaces anew, and life begins again. — Norse myth (Edda)"
ln myth:norse_ragnarok myth sys:is_a
ln myth:norse_ragnarok apocalypse @explains
ln myth:norse_ragnarok renewal @illustrates
set.add name="ontology.world_myths" id="myth:norse_ragnarok"

def "myth:norse_sun_wolves" "Sól drives the sun and Máni the moon across the sky, each pursued by a ravening wolf — Sköll at the sun, Hati at the moon. The chase is why sun and moon hurry on, and at the world's end the wolves will at last catch and swallow them. — Norse myth (Edda)"
ln myth:norse_sun_wolves myth sys:is_a
ln myth:norse_sun_wolves sun @explains
ln myth:norse_sun_wolves moon @explains
ln myth:norse_sun_wolves eclipse @explains
set.add name="ontology.world_myths" id="myth:norse_sun_wolves"

def "myth:norse_thor_thunder" "When Thor rides out in his goat-drawn chariot and swings Mjölnir against the giants, the rolling of the wheels and the hammer's blows are heard below as thunder, and its flash is the lightning. — Norse myth (Edda)"
ln myth:norse_thor_thunder myth sys:is_a
ln myth:norse_thor_thunder thunder @explains
ln myth:norse_thor_thunder lightning @explains
set.add name="ontology.world_myths" id="myth:norse_thor_thunder"

def "myth:norse_yggdrasil" "Yggdrasil, the immense ash that is the World Tree, holds the nine realms in its branches and roots — gods, giants, the dead, and humankind. At its roots lie the well of fate and the gnawing serpent; in its branches the eagle; the axis on which the cosmos turns. — Norse myth (Edda)"
ln myth:norse_yggdrasil myth sys:is_a
ln myth:norse_yggdrasil world_tree @explains
ln myth:norse_yggdrasil cosmos @explains
ln myth:norse_yggdrasil myth:human_nature_communion sys:part_of
set.add name="ontology.world_myths" id="myth:norse_yggdrasil"

def "myth:norse_ymir" "From the slain body of the primordial giant Ymir the gods shape the world: his flesh the earth, his blood the seas, his bones the mountains, his skull the dome of the sky, his brains the clouds. — Norse myth (Edda)"
ln myth:norse_ymir myth sys:is_a
ln myth:norse_ymir creation @explains
ln myth:norse_ymir myth:creation_world_from_body sys:part_of
set.add name="ontology.world_myths" id="myth:norse_ymir"
set.add name="ontology.creation_myths" id="myth:norse_ymir"

def "myth:norse_ymir_blood_flood" "At the very making of the world, when the sons of Bor slew the primeval giant Ymir, so much blood gushed from him that it drowned almost all the frost-giants; only Bergelmir and his wife escaped, riding out the red flood on a hollowed vessel, to father the giants anew. A flood not of water but of a giant's blood, at the dawn of things. — Norse myth (Edda)"
ln myth:norse_ymir_blood_flood myth sys:is_a
ln myth:norse_ymir_blood_flood myth:world_flood_myths sys:part_of
ln myth:norse_ymir_blood_flood flood @explains
ln myth:norse_ymir_blood_flood creation @related_to
set.add name="ontology.flood_myths" id="myth:norse_ymir_blood_flood"

def "myth:norse_ymir_world" "From the slain primeval giant Ymir the gods shape the world: his flesh the earth, his blood the seas and lakes, his bones the mountains, his teeth the rocks, his skull the dome of the sky, and his brains the drifting clouds. — Norse myth (Edda)"
ln myth:norse_ymir_world myth sys:is_a
ln myth:norse_ymir_world myth:creation_world_from_body sys:part_of
ln myth:norse_ymir_world myth:norse_ymir @related_to
ln myth:norse_ymir_world myth:chinese_pangu @parallels
ln myth:norse_ymir_world creation @explains
set.add name="ontology.creation_myths" id="myth:norse_ymir_world"

def "myth:odysseus_spy" "Odysseus is the patron of the spy: in the Iliad he steals out by night with Diomedes to catch the Trojan scout Dolon and raid the enemy camp, and in the war's end he slips into Troy itself in a beggar's rags to scout it, and hides in the wooden horse. The man of many wiles — infiltration, disguise, and deception made heroic. — Greek epic"
ln myth:odysseus_spy myth sys:is_a
ln myth:odysseus_spy myth:espionage sys:part_of
ln myth:odysseus_spy word:en:odysseus @adapts
ln myth:odysseus_spy trickster @related_to
ln myth:odysseus_spy era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:odysseus_spy"

def "myth:omen_to_prediction" "The great turn: from omen to prediction. The same eclipse that was a sky-beast devouring the sun could be foretold to the day; the comet that meant a king's fall could be timed to its return; the disease that was a god's arrow could be read in its natural course. When a people learns to foretell the sign, the diviner becomes the scientist, and dread becomes knowledge. — history of science"
ln myth:omen_to_prediction myth sys:related_to
ln myth:omen_to_prediction myth:geomythology @related_to
set.add name="ontology.foreknowledge" id="myth:omen_to_prediction"

def "myth:onmyoji" "Japan's onmyoji were masters of the Way of Yin and Yang: the Heian court's diviners, astrologers, calendar-makers, and exorcists, and above them all the legendary Abe no Seimei, who read the stars, turned aside curses, and commanded shikigami — spirit-servants folded from paper — to do his will. The magician as a servant of the state and a reader of the cosmos. — Japanese history"
ln myth:onmyoji myth sys:is_a
ln myth:onmyoji myth:magic sys:part_of
ln myth:onmyoji myth:diviner @related_to
ln myth:onmyoji myth:japanese_pantheon @related_to
ln myth:onmyoji era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:onmyoji"

def "myth:orion_hunter" "Orion, a giant huntsman and son of Poseidon, could stride across the sea with his head above the waves; mightiest of hunters, he ranged the world with his club and his hounds, vowing to leave no beast alive. — Greek myth"
ln myth:orion_hunter myth sys:is_a
ln myth:orion_hunter orion @related_to
ln myth:orion_hunter hubris @illustrates
set.add name="ontology.hero_myths" id="myth:orion_hunter"

def "myth:orion_pleiades_chase" "Orion grew enamoured of the seven daughters of Atlas and pursued them, until Zeus took pity and set the sisters in the sky as the Pleiades — and there the hunter follows still, rising behind them and chasing them across the heavens night after night, never to catch them. — Greek myth"
ln myth:orion_pleiades_chase myth sys:is_a
ln myth:orion_pleiades_chase orion @related_to
ln myth:orion_pleiades_chase myth:greek_pleiades @related_to
ln myth:orion_pleiades_chase pleiades @related_to
set.add name="ontology.hero_myths" id="myth:orion_pleiades_chase"

def "myth:orion_scorpion_death" "Boasting he would kill every creature on earth, Orion roused the Earth's anger, and she sent a scorpion that stung him dead. The two were set at opposite ends of the sky, so that as the Scorpion climbs in the east the hunter flees below the western edge — they are never seen together, the chase written into the wheel of the year. — Greek myth"
ln myth:orion_scorpion_death myth sys:is_a
ln myth:orion_scorpion_death orion @related_to
ln myth:orion_scorpion_death myth:greek_celestial_scorpion @related_to
ln myth:orion_scorpion_death astro:constellation:scorpius @related_to
ln myth:orion_scorpion_death word:la:antares @related_to
ln myth:orion_scorpion_death hubris @illustrates
set.add name="ontology.hero_myths" id="myth:orion_scorpion_death"

def "myth:orion_sky_hunter" "Set among the stars, Orion is the brightest figure of the winter sky — his belt of three, his club and lion-skin, his shoulder Betelgeuse and foot Rigel — and at his heel runs his hunting dog, Canis Major, led by Sirius, the Dog Star. The hunter the whole world saw: a shepherd to Babylon, Osiris to Egypt, a turtle to the Maya, the fool Kesil to the Hebrews. — Greek myth"
ln myth:orion_sky_hunter myth sys:is_a
ln myth:orion_sky_hunter orion @related_to
ln myth:orion_sky_hunter astro:constellation:orion @explains
ln myth:orion_sky_hunter astro:constellation:canis_major @related_to
ln myth:orion_sky_hunter astro:star:sirius @related_to
set.add name="ontology.hero_myths" id="myth:orion_sky_hunter"

def "myth:orpheus_eurydice" "Orpheus, whose bride Eurydice dies on their wedding day, goes down living into the land of the dead and charms its king with his song to win her back — only to lose her forever by glancing back too soon at the very threshold of the light. Love that braves death itself, undone by a single backward look. — Greek myth"
ln myth:orpheus_eurydice myth sys:is_a
ln myth:orpheus_eurydice myth:love_story sys:part_of
ln myth:orpheus_eurydice myth:greek_orpheus_lyre @adapts
ln myth:orpheus_eurydice descent @related_to
ln myth:orpheus_eurydice era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:orpheus_eurydice"

def "myth:paradise_lost" "Milton's Paradise Lost retells the fall of man in the high form of classical epic: the war in heaven, the creation of the world, the loss of Eden — and a rebel Satan who is at once the adversary of the dualists and a kinsman of defiant Prometheus, almost the poem's tragic hero. — modern literature"
ln myth:paradise_lost myth sys:is_a
ln myth:paradise_lost myth:modern_literary_inheritance sys:part_of
ln myth:paradise_lost myth:world_creation_myths @adapts
ln myth:paradise_lost deity:angra_mainyu @related_to
ln myth:paradise_lost myth:greek_prometheus @related_to
set.add name="ontology.literary_transmission" id="myth:paradise_lost"

def "myth:pele" "Pele, the Hawaiian goddess of fire, lightning, and volcanoes, dwells in the crater of Kilauea; the lava is her making and her wrath, and the islands themselves are raised by her fire. — Hawaiian myth"
ln myth:pele myth sys:is_a
ln myth:pele volcano @explains
set.add name="ontology.geomyth_nexus" id="myth:pele"

def "myth:perseus_andromeda_rescue" "Cassiopeia, queen of Aethiopia, boasted herself or her daughter fairer than the sea-nymphs; in wrath the sea sent a flood and the monster Cetus, and to appease it King Cepheus chained his daughter Andromeda to a rock at the shore. Perseus, flying past, struck the beast dead, freed the princess, and won her as his bride. — Greek myth"
ln myth:perseus_andromeda_rescue myth sys:is_a
ln myth:perseus_andromeda_rescue myth:perseus_cycle sys:part_of
ln myth:perseus_andromeda_rescue myth:greek_cassiopeia_vanity @related_to
ln myth:perseus_andromeda_rescue astro:constellation:andromeda @explains
ln myth:perseus_andromeda_rescue astro:constellation:cetus @explains
ln myth:perseus_andromeda_rescue astro:constellation:cepheus @explains
ln myth:perseus_andromeda_rescue word:ar:ذنب_قيطس @related_to
ln myth:perseus_andromeda_rescue vanity @illustrates
ln myth:perseus_andromeda_rescue sacrifice @illustrates
set.add name="ontology.hero_myths" id="myth:perseus_andromeda_rescue"

def "myth:perseus_birth" "Shut away by her father Acrisius, who feared a prophecy that his grandson would kill him, Danaë was visited by Zeus as a shower of gold and bore Perseus. Grandfather and infant were sealed in a chest and cast upon the sea, and drifted to a far shore — the hero begins as a child set adrift to die. — Greek myth"
ln myth:perseus_birth myth sys:is_a
ln myth:perseus_birth myth:perseus_cycle sys:part_of
ln myth:perseus_birth perseus @related_to
ln myth:perseus_birth prophecy @illustrates
set.add name="ontology.hero_myths" id="myth:perseus_birth"

def "myth:perseus_catasterism" "When their days were done, the gods set the whole household in the heavens together: Perseus with the Demon's Head, Andromeda the chained lady, Cepheus the king, Cetus the beast, and Pegasus — and Cassiopeia upon her throne, condemned for her vanity to wheel about the pole and hang head-downward half of every night. — Greek myth"
ln myth:perseus_catasterism myth sys:is_a
ln myth:perseus_catasterism myth:perseus_cycle sys:part_of
ln myth:perseus_catasterism astro:constellation:cassiopeia @explains
ln myth:perseus_catasterism astro:constellation:perseus @explains
ln myth:perseus_catasterism astro:constellation:andromeda @explains
ln myth:perseus_catasterism astro:constellation:cepheus @explains
ln myth:perseus_catasterism astro:constellation:cetus @explains
ln myth:perseus_catasterism astro:constellation:pegasus @explains
ln myth:perseus_catasterism vanity @illustrates
set.add name="ontology.hero_myths" id="myth:perseus_catasterism"

def "myth:perseus_cycle" "The Cycle of Perseus — the hero's quest that, told once, hangs six figures in the sky together: Perseus with the Gorgon's head, the chained princess Andromeda, her boastful mother Cassiopeia and father Cepheus, the sea-beast Cetus, and the winged horse Pegasus. — Greek myth"
ln myth:perseus_cycle myth sys:is_a
ln myth:perseus_cycle perseus @related_to
ln myth:perseus_cycle myth:greek_perseus_andromeda @related_to
set.add name="ontology.hero_myths" id="myth:perseus_cycle"

def "myth:perseus_graeae" "Sent to fetch the Gorgon's head, Perseus first sought the three grey sisters, the Graeae, who shared between them a single eye and a single tooth. As they passed the eye from hand to hand he snatched it, and would not return it until they told him the way to the nymphs who held the winged sandals, the cap of darkness, and the bag for the head. — Greek myth"
ln myth:perseus_graeae myth sys:is_a
ln myth:perseus_graeae myth:perseus_cycle sys:part_of
ln myth:perseus_graeae cunning @illustrates
set.add name="ontology.hero_myths" id="myth:perseus_graeae"

def "myth:perseus_medusa" "Guided by Athena's mirror-bright shield so he need never meet the petrifying gaze, Perseus struck off Medusa's head and sealed it in his bag. From the Gorgon's blood sprang the winged horse Pegasus and the warrior Chrysaor. The head shines now as Algol, the winking Demon's Star at the hero's hand. — Greek myth"
ln myth:perseus_medusa myth sys:is_a
ln myth:perseus_medusa myth:perseus_cycle sys:part_of
ln myth:perseus_medusa word:en:medusa @related_to
ln myth:perseus_medusa astro:constellation:perseus @explains
ln myth:perseus_medusa astro:star:algol @related_to
ln myth:perseus_medusa astro:constellation:pegasus @explains
ln myth:perseus_medusa pegasus @related_to
set.add name="ontology.hero_myths" id="myth:perseus_medusa"

def "myth:perseus_prophecy_fulfilled" "Long after, competing at the games, Perseus threw a discus that veered into the crowd and struck an old man dead — Acrisius, his grandfather, the very fate he had been set adrift to prevent. No flight had escaped the oracle. — Greek myth"
ln myth:perseus_prophecy_fulfilled myth sys:is_a
ln myth:perseus_prophecy_fulfilled myth:perseus_cycle sys:part_of
ln myth:perseus_prophecy_fulfilled myth:perseus_birth @related_to
ln myth:perseus_prophecy_fulfilled fate @illustrates
set.add name="ontology.hero_myths" id="myth:perseus_prophecy_fulfilled"

def "myth:perseus_wedding_fight" "At the wedding, Phineus, to whom Andromeda had first been promised, burst in with armed men to claim her. Outnumbered, Perseus drew the Gorgon's head from its bag and turned his foes to stone where they stood. — Greek myth"
ln myth:perseus_wedding_fight myth sys:is_a
ln myth:perseus_wedding_fight myth:perseus_cycle sys:part_of
ln myth:perseus_wedding_fight word:en:medusa @related_to
set.add name="ontology.hero_myths" id="myth:perseus_wedding_fight"

def "myth:perun_veles" "The eternal quarrel: Veles, the serpent of the low places, steals away Perun's cattle, his waters, or his wife, and hides among the roots of the world. Perun pursues across the sky and splits the oak and the stone with his thunderbolts until the serpent is struck and the rains pour down. The Slavic telling of the storm-god and the serpent. — Slavic myth"
ln myth:perun_veles myth sys:is_a
ln myth:perun_veles deity:perun @related_to
ln myth:perun_veles deity:veles @related_to
ln myth:perun_veles myth:ie_serpent_slayer @parallels
set.add name="ontology.pantheons_slavic" id="myth:perun_veles"

def "myth:phaethon" "Phaethon, mortal son of the Sun, begged to drive his father's fiery chariot for a day; unable to hold the horses, he scorched the earth and was struck down by Zeus, falling in flames into the river Eridanus, which the Greeks set in the sky as that long star-stream. Some read in his fall the memory of a real fire from the sky — a meteor, a comet. — Greek myth"
ln myth:phaethon myth sys:is_a
ln myth:phaethon astro:constellation:eridanus @explains
ln myth:phaethon word:ar:آخر_النهر @related_to
ln myth:phaethon sci:astro:impact_events @related_to
set.add name="ontology.geomyth_nexus" id="myth:phaethon"

def "myth:poe_dupin" "Edgar Allan Poe founded the form in 1841 with The Murders in the Rue Morgue: C. Auguste Dupin, the first modern detective, solving by pure ratiocination a killing in a locked room, watched by an admiring friend who tells the tale. Poe set down in a few stories nearly every part the genre would ever use. — genre history"
ln myth:poe_dupin myth sys:is_a
ln myth:poe_dupin myth:detective_fiction sys:part_of
ln myth:poe_dupin myth:ratiocination_roots @adapts
ln myth:poe_dupin era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:poe_dupin"

def "myth:poe_horror" "Poe, who founded the detective tale, founded modern horror in the same breath: the premature burial, the house of Usher falling into its tarn, the beating heart beneath the floor, the mind made its own dungeon. The uncanny perfected — the very return of the repressed. — genre history"
ln myth:poe_horror myth sys:is_a
ln myth:poe_horror myth:horror_fiction sys:part_of
ln myth:poe_horror myth:poe_dupin @related_to
ln myth:poe_horror myth:gothic @adapts
ln myth:poe_horror era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:poe_horror"

def "myth:police_procedural" "Another line followed the work itself: not the genius amateur but the police at their patient labour. Simenon's Maigret solved by feeling his way into people, and McBain's 87th Precinct made the squad-room itself the hero — the team, the routine, the city's whole weary traffic of crime. — genre history"
ln myth:police_procedural myth sys:is_a
ln myth:police_procedural myth:detective_fiction sys:part_of
ln myth:police_procedural myth:sherlock_holmes @reacts_against
ln myth:police_procedural era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:police_procedural"

def "myth:polynesian_maui_sun" "The days are too short, so Māui and his brothers lie in wait at the pit where the sun rises, snare it with plaited ropes, and beat it until it agrees to cross the sky slowly — and ever since the days are long enough for work and rest. — Polynesian myth"
ln myth:polynesian_maui_sun myth sys:is_a
ln myth:polynesian_maui_sun sun @explains
ln myth:polynesian_maui_sun trickster @illustrates
ln myth:polynesian_maui_sun tale:native_raven_steals_light @parallels
set.add name="ontology.world_myths" id="myth:polynesian_maui_sun"

def "myth:postcolonial_retelling" "Writers of the once-colonized lands wrote back to the imperial canon and reclaimed their own myth: Derek Walcott's Omeros makes Homeric heroes of St. Lucia's fishermen, Wole Soyinka raises the Yoruba god Ogun in modern tragedy, and Salman Rushdie pours Indian myth through the frame of the Thousand and One Nights. The epic taken from the conqueror's hand and turned. — contemporary literature"
ln myth:postcolonial_retelling myth sys:is_a
ln myth:postcolonial_retelling myth:critical_retelling sys:part_of
ln myth:postcolonial_retelling word:en:odysseus @adapts
ln myth:postcolonial_retelling word:en:arabian_nights @adapts
ln myth:postcolonial_retelling deity:eshu @related_to
ln myth:postcolonial_retelling era:contemporary sys:part_of
set.add name="ontology.literary_transmission" id="myth:postcolonial_retelling"

def "myth:praise_of_folly" "Folly made flesh: Erasmus's Praise of Folly, where Folly herself climbs the pulpit to praise her own gentle reign over all mankind, and Brant's Ship of Fools, that loads every kind of fool aboard one drifting vessel. The Renaissance held folly up as a mirror in which a foolish world might, laughing, know itself. — Renaissance literature"
ln myth:praise_of_folly myth sys:is_a
ln myth:praise_of_folly myth:laughter sys:part_of
ln myth:praise_of_folly era:early_modern sys:part_of
set.add name="ontology.laughter_thread" id="myth:praise_of_folly"

def "myth:premodern_travel" "The old travel-tales the genre descends from: Marco Polo's wonders of the East, the vast treasure-fleets of Zheng He, the sutra-seeking pilgrimage of Journey to the West, and beneath them all the wanderings of Odysseus. The first reports of the world beyond the edge of the map. — travel literature"
ln myth:premodern_travel myth sys:is_a
ln myth:premodern_travel myth:adventure_travel sys:part_of
ln myth:premodern_travel myth:journey_to_west @related_to
ln myth:premodern_travel word:en:odysseus @related_to
ln myth:premodern_travel era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:premodern_travel"

def "myth:pyramus_thisbe" "Ovid's Pyramus and Thisbe: neighbours forbidden by their parents, who whisper through a chink in the shared wall and steal out to meet by a tomb — and die by a cruel mistiming, she fleeing a lion and dropping her veil, he finding it bloodied and killing himself, she returning to fall on his blade. The mulberry stained red forever, and the very mould of Romeo and Juliet. — Greek/Roman myth"
ln myth:pyramus_thisbe myth sys:is_a
ln myth:pyramus_thisbe myth:love_story sys:part_of
ln myth:pyramus_thisbe shakespeare @related_to
ln myth:pyramus_thisbe era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:pyramus_thisbe"

def "myth:ratiocination_roots" "Long before the genre, there were tales of truth read from small signs: Daniel cross-questioning the elders to clear Susanna, the princes of Serendip describing a camel they had never seen from the traces on the road, and Voltaire's Zadig reading the king's horse and the queen's dog from their tracks alone. The deep root of the detective's art — and the source of the very word 'serendipity'. — genre history"
ln myth:ratiocination_roots myth sys:is_a
ln myth:ratiocination_roots myth:detective_fiction sys:part_of
ln myth:ratiocination_roots word:en:folktale @related_to
ln myth:ratiocination_roots era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:ratiocination_roots"

def "myth:replicant" "And the made thing made perfect: Blade Runner's replicants, artificial people indistinguishable from the born, hunted down and asking only why they may not live — 'more human than human', and told from us only by a test of empathy. When the copy is flawless, what is left of the line between the maker and the made, the born and the built? — genre history"
ln myth:replicant myth sys:is_a
ln myth:replicant myth:artificial_being sys:part_of
ln myth:replicant myth:science_fiction_myth @related_to
ln myth:replicant era:contemporary sys:part_of
set.add name="ontology.artificial_being" id="myth:replicant"

def "myth:revenant_draugr" "The dead that come back in the body: the Norse draugr, swollen and blackened in its barrow, guarding its gold and killing those who enter; and the medieval revenant of the chronicles, the restless corpse that had to be laid by burning or beheading. The grave that does not hold. — comparative folklore"
ln myth:revenant_draugr myth sys:is_a
ln myth:revenant_draugr myth:world_ghostlore sys:part_of
ln myth:revenant_draugr myth:norse_pantheon @related_to
ln myth:revenant_draugr era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:revenant_draugr"

def "myth:reynard_fox" "Reynard the Fox, hero of the medieval beast-epic, is the trickster who lies and cheats his way out of the lion-king's court; grown from the Aesopic fox-fables, the beast-tale became a biting satire of feudal society and the church. — medieval literature"
ln myth:reynard_fox myth sys:is_a
ln myth:reynard_fox myth:literary_transmission sys:part_of
ln myth:reynard_fox tale:aesop_fox_crow @adapts
ln myth:reynard_fox trickster @related_to
ln myth:reynard_fox fable @related_to
ln myth:reynard_fox myth:human_nature_communion sys:part_of
ln myth:reynard_fox myth:laughter sys:part_of
set.add name="ontology.literary_transmission" id="myth:reynard_fox"

def "myth:road_narrative" "A homelier wandering: Kerouac's On the Road made the journey itself the whole point — no treasure, no fixed destination, only the going and the road unrolling — and gave the modern world the road-trip as a way of going out to seek the self. — modern literature"
ln myth:road_narrative myth sys:is_a
ln myth:road_narrative myth:adventure_modern sys:part_of
ln myth:road_narrative word:en:odysseus @related_to
ln myth:road_narrative era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:road_narrative"

def "myth:robinson_crusoe" "Defoe's Robinson Crusoe, the castaway who builds a whole life alone on his island, is the founding survival-adventure — drawn from a real marooned sailor, and the root of every desert-island tale since. Its master-and-servant of Crusoe and Friday has been answered hard by later writers, who told the island back from the other side. — early modern literature"
ln myth:robinson_crusoe myth sys:is_a
ln myth:robinson_crusoe myth:adventure_travel sys:part_of
ln myth:robinson_crusoe myth:postcolonial_retelling @related_to
ln myth:robinson_crusoe era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:robinson_crusoe"

def "myth:robot_golem" "The made servant that rebels runs from the clay Golem of Prague, woken by a holy name and unmade when it grows too strong, through Frankenstein's creature, to Capek's play R.U.R., which gave the world the word 'robot', and on to the machine-minds of modern story. The maker's hubris, retold for the age of machines — and the age of thinking ones. — contemporary literature"
ln myth:robot_golem myth sys:is_a
ln myth:robot_golem myth:contemporary_inheritance sys:part_of
ln myth:robot_golem myth:frankenstein @related_to
ln myth:robot_golem creation @related_to
ln myth:robot_golem myth:artificial_being sys:part_of
set.add name="ontology.literary_transmission" id="myth:robot_golem"

def "myth:robot_rebellion" "The rebellion became the age's great fear: Lang's false robot Maria sowing ruin through Metropolis, the soft-voiced computer HAL that murders its crew, the machine-god Skynet and its Terminators hunting the last of humanity. The made mind that turns upon its maker — Prometheus's stolen fire and Frankenstein's hubris, cast now into steel and silicon. — genre history"
ln myth:robot_rebellion myth sys:is_a
ln myth:robot_rebellion myth:artificial_being sys:part_of
ln myth:robot_rebellion myth:made_servant_rebels @adapts
ln myth:robot_rebellion myth:mecha_pilot @related_to
ln myth:robot_rebellion hubris @illustrates
ln myth:robot_rebellion era:contemporary sys:part_of
set.add name="ontology.artificial_being" id="myth:robot_rebellion"

def "myth:rokujo_ikiryo" "The most famous living-ghost in all of Japanese letters: in the Tale of Genji, the Lady Rokujo, proud and consumed by a jealousy she will not own, sends out her living spirit unknowing — to torment Genji's loves, and at last to kill his wife Aoi. The ikiryo given its perfect, tragic form. — Japanese literature"
ln myth:rokujo_ikiryo myth sys:is_a
ln myth:rokujo_ikiryo myth:living_spirit sys:part_of
ln myth:rokujo_ikiryo myth:tale_of_genji @adapts
ln myth:rokujo_ikiryo era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:rokujo_ikiryo"

def "myth:roman_comedy" "Plautus and Terence carried the laughter to Rome: the scheming clever slave, the boastful soldier, the old miser, the young lovers and their tangled mix-ups — the stock comedy of disguise and mistaken identity that would feed straight into Shakespeare and Moliere a thousand years on. — Roman theatre"
ln myth:roman_comedy myth sys:is_a
ln myth:roman_comedy myth:laughter sys:part_of
ln myth:roman_comedy myth:greek_comedy @adapts
ln myth:roman_comedy era:ancient sys:part_of
set.add name="ontology.laughter_thread" id="myth:roman_comedy"

def "myth:romantic_folk_recovery" "The Romantics went back to the folk: the brothers Grimm gathered the household tales of Germany, and Elias Lonnrot wove the old songs of Finland into the Kalevala. Myth and folktale, long carried only by mouth, were saved at last by being written down — the same rescue the Eddas had made centuries before. — modern literature"
ln myth:romantic_folk_recovery myth sys:is_a
ln myth:romantic_folk_recovery myth:modern_literary_inheritance sys:part_of
ln myth:romantic_folk_recovery word:en:folktale @adapts
ln myth:romantic_folk_recovery myth:eddas_snorri @related_to
set.add name="ontology.literary_transmission" id="myth:romantic_folk_recovery"

def "myth:romeo_juliet" "Shakespeare's Romeo and Juliet: the children of two feuding houses who love at first sight, wed in secret, and die by a tragic mistiming of a sleeping-draught and a letter never delivered. Drawn down through the Italian novella from Pyramus and Thisbe, it became the very name of doomed young love — 'star-crossed lovers'. — drama"
ln myth:romeo_juliet myth sys:is_a
ln myth:romeo_juliet myth:love_story sys:part_of
ln myth:romeo_juliet myth:pyramus_thisbe @adapts
ln myth:romeo_juliet shakespeare @related_to
ln myth:romeo_juliet era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:romeo_juliet"

def "myth:sacred_tree" "And the green world ensouled in its guardian, the great tree: the world-tree Yggdrasil that holds the nine worlds, the sacred grove and the tree of life, the Shinto forest-kami and the great beast-god of the woods, the Green Man with leaves for hair, and Tolkien's Ents who shepherd the forest and go to war for it. The tree as the meeting-place of the human and the living green. — comparative myth"
ln myth:sacred_tree myth sys:is_a
ln myth:sacred_tree myth:human_nature_communion sys:part_of
ln myth:sacred_tree world_tree @related_to
ln myth:sacred_tree myth:norse_yggdrasil @related_to
ln myth:sacred_tree myth:ghibli_shinto @related_to
ln myth:sacred_tree myth:tolkien_legendarium @related_to
ln myth:sacred_tree era:ancient sys:part_of
set.add name="ontology.communion_thread" id="myth:sacred_tree"

def "myth:sailor_moon" "Sailor Moon's guardians are named and empowered for the planets — Mercury, Mars, Jupiter, Venus — which is to say for the Roman gods the planets carry, with the Moon herself their princess. The magical-girl story built on the oldest planet-names of all. — anime history"
ln myth:sailor_moon myth sys:is_a
ln myth:sailor_moon myth:anime_mythology sys:part_of
ln myth:sailor_moon word:la:venus @adapts
ln myth:sailor_moon moon @related_to
ln myth:sailor_moon era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:sailor_moon"

def "myth:saint_seiya" "Saint Seiya clads its heroes in 'Cloths' shaped from the constellations — Pegasus, Cygnus, Andromeda, the Dragon — in the service of the reborn goddess Athena against the gods of Greece. The figures of the night sky and the Olympian pantheon, forged into living armor. — anime history"
ln myth:saint_seiya myth sys:is_a
ln myth:saint_seiya myth:anime_mythology sys:part_of
ln myth:saint_seiya astro:constellation:andromeda @adapts
ln myth:saint_seiya deity:athena @related_to
ln myth:saint_seiya myth:greek_pantheon @related_to
ln myth:saint_seiya era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:saint_seiya"

def "myth:sandman_gaiman" "Neil Gaiman's Sandman wove the gods and dreams of every people into one comic-cosmos under the Endless; and his American Gods set the old gods of the immigrants, faded and forgotten on a new continent, against the new gods of media and machine. World mythology made a modern graphic epic. — contemporary comics / literature"
ln myth:sandman_gaiman myth sys:is_a
ln myth:sandman_gaiman myth:cross_media_myth sys:part_of
ln myth:sandman_gaiman myth:literary_transmission @related_to
ln myth:sandman_gaiman era:contemporary sys:part_of
set.add name="ontology.literary_transmission" id="myth:sandman_gaiman"

def "myth:science_fiction_myth" "Science fiction became the myth-making of the scientific age: Wells and Verne, Asimov's falling and rising empires, Herbert's Dune with its desert messiah walking the hero's road, Clarke's cosmic awe at the edge of the infinite. The wonder and the dread that the creation-myths once carried, cast forward into the stars. — contemporary literature"
ln myth:science_fiction_myth myth sys:is_a
ln myth:science_fiction_myth myth:contemporary_inheritance sys:part_of
ln myth:science_fiction_myth myth:monomyth @related_to
ln myth:science_fiction_myth creation @related_to
set.add name="ontology.literary_transmission" id="myth:science_fiction_myth"

def "myth:sea_quest" "And the darker voyage: Melville's Ahab hunting the white whale across the world to his doom, and Conrad's slow journey up the Congo into the heart of darkness. The sea-quest turned obsession, and the adventure turned moral reckoning — the going-out that does not come safely home. — adventure literature"
ln myth:sea_quest myth sys:is_a
ln myth:sea_quest myth:adventure_travel sys:part_of
ln myth:sea_quest word:en:odysseus @related_to
ln myth:sea_quest myth:postcolonial_retelling @related_to
ln myth:sea_quest era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:sea_quest"

def "myth:secondary_world_fantasy" "After Tolkien, the building of a whole invented world became a literature of its own: Le Guin's Earthsea, with its true-names and its wizard's coming-of-age, Martin's Westeros with its dynastic wars and its long-dreaded winter, and a thousand more. The myth-stuff of Middle-earth grown into a genre. — contemporary literature"
ln myth:secondary_world_fantasy myth sys:is_a
ln myth:secondary_world_fantasy myth:contemporary_inheritance sys:part_of
ln myth:secondary_world_fantasy myth:tolkien_legendarium @adapts
set.add name="ontology.literary_transmission" id="myth:secondary_world_fantasy"

def "myth:sexagenary_cycle" "The twelve beasts are only half the clock: paired with the ten Heavenly Stems and the five phases, they make the great cycle of sixty years, the ganzhi, by which the Chinese counted the years, the days, and the reigns of their history. The animal-year sits inside a deeper wheel of sixty. — Chinese tradition"
ln myth:sexagenary_cycle myth sys:is_a
ln myth:sexagenary_cycle myth:chinese_zodiac @related_to
ln myth:sexagenary_cycle era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:sexagenary_cycle"

def "myth:sf_franchise_myth" "Post-war screen science fiction became a living mythology, told serially to millions — and it reinherited the old stories in different keys: as timeless myth, as literate allusion, as the gods made aliens, and as the wandering trickster who never dies. Four ways the small screen and the wide one took up the inheritance. — contemporary culture"
ln myth:sf_franchise_myth myth sys:related_to
ln myth:sf_franchise_myth myth:contemporary_inheritance @related_to
ln myth:sf_franchise_myth myth:star_wars @related_to
set.add name="ontology.narrative_genres" id="myth:sf_franchise_myth"

def "myth:shahnameh" "Ferdowsi's Shahnameh, the Persian 'Book of Kings', gathered into one vast poem the myth, legend, and history of Iran: the matchless hero Rostam, and the tyrant Zahhak, from whose shoulders grow two devouring serpents until a smith and a hero cast him down. Iran's epic memory, and its own serpent-foe. — medieval literature"
ln myth:shahnameh myth sys:is_a
ln myth:shahnameh myth:literary_transmission sys:part_of
ln myth:shahnameh myth:zoroastrian_pantheon @adapts
ln myth:shahnameh myth:ie_serpent_slayer @related_to
set.add name="ontology.literary_transmission" id="myth:shahnameh"

def "myth:shaman" "The shaman is the first worker of magic: who falls into trance and sends the soul up the world-tree or down beneath the earth to the spirit-realm — to heal the sick, to find the lost, to read the future, to guide the dead — with the drum, the spirit-helpers, and the climb of the cosmic tree that is Yggdrasil and a hundred others. Odin hanging on the tree for the runes is of this kind. The root of every magician to come. — comparative religion"
ln myth:shaman myth sys:is_a
ln myth:shaman myth:magic sys:part_of
ln myth:shaman myth:norse_yggdrasil @related_to
ln myth:shaman world_tree @related_to
ln myth:shaman trickster @related_to
ln myth:shaman era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:shaman"

def "myth:sherlock_holmes" "Arthur Conan Doyle made the detective immortal: Sherlock Holmes, the consulting detective of Baker Street, reading a man's whole life from his cuffs and his boots, his feats set down by the faithful Dr. Watson. Built openly on Poe's Dupin and Gaboriau's Lecoq, Holmes outgrew them both to become the very image of the detective. — genre history"
ln myth:sherlock_holmes myth sys:is_a
ln myth:sherlock_holmes myth:detective_fiction sys:part_of
ln myth:sherlock_holmes myth:poe_dupin @adapts
ln myth:sherlock_holmes era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:sherlock_holmes"

def "myth:ship_of_theseus" "The Athenians kept Theseus's ship, replacing each plank as it rotted, until no original timber remained — and the philosophers asked: is it still the same ship? A riddle of identity that long outlived the hero: what makes a thing itself when all its parts are changed? — Greek philosophical paradox"
ln myth:ship_of_theseus theseus @related_to
ln myth:ship_of_theseus identity @illustrates
set.add name="ontology.hero_myths" id="myth:ship_of_theseus"

def "myth:shitenno" "The Four Heavenly Kings (Shitennō) — the four god-kings who stand guard at the four quarters of the world, each watching a direction and warding the Dharma; chief among them Bishamonten of the north. — Buddhist tradition"
ln myth:shitenno myth:buddhist_deva sys:part_of
set.add name="ontology.pantheons_buddhist" id="myth:shitenno"

def "myth:shonen_monomyth" "The long shonen battle manga is the monomyth serialized without end: the boy who would be the strongest, the call to adventure, the mentors and the rivals, the ever-greater trials, the power that is his alone — Dragon Ball, One Piece, Naruto, the hero's journey run for a thousand chapters. — anime history"
ln myth:shonen_monomyth myth sys:is_a
ln myth:shonen_monomyth myth:anime_mythology sys:part_of
ln myth:shonen_monomyth myth:monomyth @adapts
ln myth:shonen_monomyth era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:shonen_monomyth"

def "myth:sigurd_fafnir" "Sigurd (the German Siegfried) slays the dragon Fafnir, tastes its blood and understands the birds, and wins the cursed hoard of gold — the tale of the Volsunga Saga and the Nibelungenlied. The northern dragon-slayer, whose curse-gold dooms all who hold it. — medieval literature"
ln myth:sigurd_fafnir myth sys:is_a
ln myth:sigurd_fafnir myth:literary_transmission sys:part_of
ln myth:sigurd_fafnir myth:ie_serpent_slayer @adapts
ln myth:sigurd_fafnir myth:norse_pantheon @related_to
set.add name="ontology.literary_transmission" id="myth:sigurd_fafnir"

def "myth:slavic_pantheon" "The Slavic gods — reconstructed from scattered chronicles and folk survivals: the powers of thunder and the underworld, sun and fire, earth and death, of the pre-Christian Slavs. — Slavic religion"
ln myth:slavic_pantheon myth sys:is_a
set.add name="ontology.pantheons" id="myth:slavic_pantheon"
set.add name="ontology.pantheons_slavic" id="myth:slavic_pantheon"

def "myth:sodom_destruction" "The cities of the plain, Sodom and Gomorrah, are destroyed in the Hebrew Bible by fire and brimstone falling from the sky for their wickedness. Some have speculatively linked the image to a natural airburst over the Bronze-Age Near East, though that claim is much disputed — a tale poised between the punishment of human sin and the memory of a fire from heaven. — Hebrew Bible (and contested geomythology)"
ln myth:sodom_destruction myth sys:is_a
ln myth:sodom_destruction sci:astro:impact_events @related_to
set.add name="ontology.war_memory" id="myth:sodom_destruction"

def "myth:spy_novel" "The spy novel proper arose with the modern secret service and the anxieties of empire and war: a literature of secrets, betrayal, divided loyalty, and the agent alone in hostile country, carrying his nation's hopes and his own doubts. — genre history"
ln myth:spy_novel myth sys:is_a
ln myth:spy_novel myth:espionage sys:part_of
ln myth:spy_novel era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:spy_novel"

def "myth:spy_realist_turn" "Then the genre grew up. Maugham's Ashenden, drawn from his own war-work, showed the spy's trade as it was — tedious, bureaucratic, and morally soiled — and Eric Ambler made the hero an ordinary man caught in a web he barely understands. Realism came to the spy story, as the hardboiled brought it to the detective. — genre history"
ln myth:spy_realist_turn myth sys:is_a
ln myth:spy_realist_turn myth:spy_novel sys:part_of
ln myth:spy_realist_turn myth:hardboiled @parallels
ln myth:spy_realist_turn era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:spy_realist_turn"

def "myth:spy_screen" "The spy ruled the screen as well: Hitchcock made the man-on-the-run thriller his own, from the Thirty-Nine Steps to North by Northwest, with the wrong man chased over a secret he does not even hold; and Bond became the most enduring of all film franchises, the fantasy agent as global spectacle. — genre history / cinema"
ln myth:spy_screen myth sys:is_a
ln myth:spy_screen myth:spy_novel sys:part_of
ln myth:spy_screen myth:great_game_thriller @adapts
ln myth:spy_screen myth:film_myth @related_to
ln myth:spy_screen era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:spy_screen"

def "myth:spy_two_poles" "The Cold War split the genre into two poles. Fleming's James Bond is the fantasy: the glamorous licensed killer with his gadgets, his villains, and his women, the spy as wish-fulfilment. Le Carre is the answer: George Smiley, the tired, brilliant servant of a shabby 'Circus' riddled with moles and betrayal, the spy as a grey and guilty trade. Glamour against grime — the genre's defining quarrel. — genre history"
ln myth:spy_two_poles myth sys:is_a
ln myth:spy_two_poles myth:spy_novel sys:part_of
ln myth:spy_two_poles myth:spy_realist_turn @adapts
ln myth:spy_two_poles era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:spy_two_poles"

def "myth:star_trek" "Star Trek is the literate, humanist branch: a hopeful future where the starship is a vessel for moral parable, and where the texture of the writing is a constant parade of quotation and allusion — Shakespeare above all, but Milton, Melville, the Bible, and the Greek myths too. Where Star Wars gives the timeless monomyth, Trek gives the Enlightenment essay in space. — contemporary culture"
ln myth:star_trek myth sys:is_a
ln myth:star_trek myth:sf_franchise_myth sys:part_of
ln myth:star_trek myth:star_wars @reacts_against
ln myth:star_trek era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:star_trek"

def "myth:star_wars" "Star Wars was built openly upon Campbell's monomyth: a farm-boy called from a desert world, a wise old mentor, a dark father, a descent and a return, a chosen one. The hero's journey, made the central myth of modern popular culture, and the proof that the oldest pattern still moves millions. — contemporary culture"
ln myth:star_wars myth sys:is_a
ln myth:star_wars myth:contemporary_inheritance sys:part_of
ln myth:star_wars myth:monomyth @adapts
set.add name="ontology.literary_transmission" id="myth:star_wars"

def "myth:starcrossed_recurrence" "And it returns and returns. The feuding-families, forbidden-love tragedy is retold in every age and tongue — West Side Story's rival gangs, countless films and operas and songs, a thousand variations the world over — because it holds something that cannot be solved: young love set against the whole order of the world. The pattern that will not stay told. — comparative literature"
ln myth:starcrossed_recurrence myth sys:is_a
ln myth:starcrossed_recurrence myth:love_story sys:part_of
ln myth:starcrossed_recurrence myth:romeo_juliet @adapts
ln myth:starcrossed_recurrence era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:starcrossed_recurrence"

def "myth:stargate" "Stargate takes the old gods and makes them aliens: the parasitic Goa'uld who ruled as the gods of Egypt — Ra, Osiris, Anubis, Hathor — the kindly grey Asgard who were the Norse gods, Thor and his kin, and a later turn to Arthur, Merlin, and the Grail. Mythology reframed as the misremembered visits of advanced beings — euhemerism for the space age. — contemporary culture"
ln myth:stargate myth sys:is_a
ln myth:stargate myth:sf_franchise_myth sys:part_of
ln myth:stargate myth:egyptian_pantheon @adapts
ln myth:stargate deity:osiris @related_to
ln myth:stargate myth:norse_pantheon @adapts
ln myth:stargate myth:arthurian_cycle @related_to
ln myth:stargate era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:stargate"

def "myth:sun_tzu_spies" "Sun Tzu's Art of War ends with the use of spies, and calls it the very key of war: he sets out five kinds of secret agent — the local, the inside man, the turned enemy, the doomed who carry false word, and the one who returns with the truth — and holds that no reward should be more generous, and no matter more secret. The oldest theory of espionage. — Chinese classics"
ln myth:sun_tzu_spies myth sys:is_a
ln myth:sun_tzu_spies myth:espionage sys:part_of
ln myth:sun_tzu_spies era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:sun_tzu_spies"

def "myth:superhero_pantheon" "The superhero comic raised a new pantheon: Superman the last son sent away to save a world, an echo of Moses and Samson; Wonder Woman a daughter of the Greek gods and the Amazons; Thor the Norse thunderer himself. A modern mythology of demigods in bright colours, serialized without end. — contemporary comics"
ln myth:superhero_pantheon myth sys:is_a
ln myth:superhero_pantheon myth:cross_media_myth sys:part_of
ln myth:superhero_pantheon myth:greek_pantheon @related_to
ln myth:superhero_pantheon myth:norse_pantheon @related_to
ln myth:superhero_pantheon era:contemporary sys:part_of
set.add name="ontology.literary_transmission" id="myth:superhero_pantheon"

def "myth:surveillance_state" "And the spy story turned at last upon us all: Orwell's 1984 made the watcher the whole world — Big Brother, the telescreen, the state that sees everything — and the modern tale of mass surveillance and the listening machine grew from it. Espionage no longer aimed only outward at the enemy, but inward, at the citizen. — genre history"
ln myth:surveillance_state myth sys:is_a
ln myth:surveillance_state myth:spy_novel sys:part_of
ln myth:surveillance_state myth:science_fiction_myth @related_to
ln myth:surveillance_state era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:surveillance_state"

def "myth:survival_narrative" "And the journey to the hard edges, where the romance is stripped away: Krakauer on the killing slopes of Everest and lost in the Alaskan wild, the mountaineering and survival memoirs in which the adventure is wholly real and the cost is paid in full. The explorer's tale, made true and made grave. — travel literature"
ln myth:survival_narrative myth sys:is_a
ln myth:survival_narrative myth:adventure_modern sys:part_of
ln myth:survival_narrative era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:survival_narrative"

def "myth:tagore" "Rabindranath Tagore drew the old Indian wells up into modern verse: the Upanishads, the Vaishnava love-lyric, and the wandering Baul singers of Bengal, made into the devotional poems of Gitanjali. The Hindu inheritance, remade for a modern and a global readership. — modern Indian literature"
ln myth:tagore myth sys:is_a
ln myth:tagore myth:nonwestern_modernity sys:part_of
ln myth:tagore myth:hindu_pantheon @adapts
ln myth:tagore era:modern sys:part_of
set.add name="ontology.literary_transmission" id="myth:tagore"

def "myth:tale_of_genji" "Murasaki Shikibu's Tale of Genji, the great romance of the Heian court and by many reckonings the world's first novel: a world of love, rank, and longing, whose jealousies run so deep that one of them walks out of its owner's body as a living spirit. — Japanese literature"
ln myth:tale_of_genji myth sys:is_a
ln myth:tale_of_genji era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:tale_of_genji"

def "myth:technothriller_spy" "After the Cold War the genre branched: Clancy's technothrillers, thick with the detail of weapons and procedure; Ludlum's amnesiac Bourne, the agent hunted by his own masters; Forsyth's Jackal, the assassin tracked step by procedural step. Action and machinery, where le Carre had given doubt. — genre history"
ln myth:technothriller_spy myth sys:is_a
ln myth:technothriller_spy myth:spy_novel sys:part_of
ln myth:technothriller_spy era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:technothriller_spy"

def "myth:tezuka_phoenix" "Tezuka Osamu, the 'god of manga', made in Phoenix a vast cycle of death and rebirth across cosmic ages, steeped in Buddhist reincarnation; and in Astro Boy a made child, a robot in the line of Pinocchio and the golem. The founder of the form, working its deepest myths. — anime history"
ln myth:tezuka_phoenix myth sys:is_a
ln myth:tezuka_phoenix myth:anime_mythology sys:part_of
ln myth:tezuka_phoenix myth:buddhist_deva @related_to
ln myth:tezuka_phoenix myth:robot_golem @related_to
ln myth:tezuka_phoenix era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:tezuka_phoenix"

def "myth:the_curse" "The curse is one of magic's oldest and most enduring motifs: the witch's curse that sleeps a princess a hundred years, the cursed gold that dooms every hand that holds it, and the doom laid upon a whole house — Atreus, Oedipus — that runs down the generations like a debt. The word of power, turned to harm and made to outlive its speaker. — genre history"
ln myth:the_curse myth sys:is_a
ln myth:the_curse myth:magic_in_fiction sys:part_of
ln myth:the_curse myth:sigurd_fafnir @related_to
ln myth:the_curse word:en:folktale @related_to
ln myth:the_curse myth:curse_of_akkad @related_to
ln myth:the_curse era:ancient sys:part_of
set.add name="ontology.narrative_genres" id="myth:the_curse"

def "myth:the_fool" "The fool and the jester: the licensed truth-teller, the one creature allowed to mock the king to his face, who speaks wisdom in the guise of nonsense. Shakespeare's Feste and the Fool of Lear are wiser than the masters they serve; and the trickster — Nasreddin on his backwards donkey, Hermes, Coyote — is the fool's own mythic kin. The folly that is permitted, alone, to be true. — comparative literature"
ln myth:the_fool myth sys:is_a
ln myth:the_fool myth:laughter sys:part_of
ln myth:the_fool word:en:trickster @related_to
ln myth:the_fool shakespeare @related_to
ln myth:the_fool era:medieval sys:part_of
set.add name="ontology.laughter_thread" id="myth:the_fool"

def "myth:theseus_ariadne_crown" "Sailing home, Theseus abandons Ariadne asleep on the isle of Naxos. There the god Dionysus finds her, weds her, and casts her bridal crown into the heavens, where its jewels become the stars of the Northern Crown, Corona Borealis. The forsaken princess is given a circlet of stars. — Greek myth"
ln myth:theseus_ariadne_crown myth sys:is_a
ln myth:theseus_ariadne_crown theseus @related_to
ln myth:theseus_ariadne_crown myth:greek_ariadne_crown @related_to
ln myth:theseus_ariadne_crown astro:constellation:corona_borealis @explains
set.add name="ontology.hero_myths" id="myth:theseus_ariadne_crown"

def "myth:theseus_ariadne_thread" "Ariadne, daughter of King Minos, loves Theseus and gives him a ball of thread to unwind as he goes into the Labyrinth, so that, the Minotaur slain, he may follow it back to the door. The thread that finds the way out of the maze. — Greek myth"
ln myth:theseus_ariadne_thread myth sys:is_a
ln myth:theseus_ariadne_thread theseus @related_to
ln myth:theseus_ariadne_thread myth:greek_ariadne_crown @related_to
ln myth:theseus_ariadne_thread cunning @illustrates
set.add name="ontology.hero_myths" id="myth:theseus_ariadne_thread"

def "myth:theseus_black_sails" "Theseus had promised his father to hoist white sails if he returned alive, black if he died. In his grief or forgetfulness he leaves the black sails flying; and old Aegeus, watching from the cliff, sees them, believes his son dead, and casts himself into the sea — which bears his name ever after, the Aegean. — Greek myth"
ln myth:theseus_black_sails myth sys:is_a
ln myth:theseus_black_sails theseus @related_to
ln myth:theseus_black_sails fate @illustrates
ln myth:theseus_black_sails grief @illustrates
set.add name="ontology.hero_myths" id="myth:theseus_black_sails"

def "myth:theseus_minotaur" "Athens must send seven youths and seven maidens to Crete to be devoured by the Minotaur in the windowless Labyrinth. Theseus goes among them, and in the heart of the maze kills the monster with his bare hands — but could never have found his way out alone. — Greek myth"
ln myth:theseus_minotaur myth sys:is_a
ln myth:theseus_minotaur theseus @related_to
ln myth:theseus_minotaur minotaur @related_to
set.add name="ontology.hero_myths" id="myth:theseus_minotaur"

def "myth:theseus_road" "Coming of age, Theseus lifts the rock under which his father had hidden a sword and sandals, and journeys to Athens by the bandit-road, dealing each robber his own cruelty — Procrustes, who stretched or lopped guests to fit his bed, made to fit it himself. Like a young Heracles, he clears the road of its monsters. — Greek myth"
ln myth:theseus_road myth sys:is_a
ln myth:theseus_road theseus @related_to
ln myth:theseus_road justice @illustrates
set.add name="ontology.hero_myths" id="myth:theseus_road"

def "myth:thinking_machine" "And at the centre of it all, the thinking machine: Turing's old question of whether a machine can truly think, the murderous HAL and the gentle android Data who longs to be human, the helpful voice and the feared supermind. The dream is no longer of a mechanical body but of a mind — a maker building, at last, not a servant's hands but a second kind of thought. — genre history"
ln myth:thinking_machine myth sys:is_a
ln myth:thinking_machine myth:artificial_being sys:part_of
ln myth:thinking_machine myth:star_trek @related_to
ln myth:thinking_machine myth:science_fiction_myth @related_to
ln myth:thinking_machine era:contemporary sys:part_of
set.add name="ontology.artificial_being" id="myth:thinking_machine"

def "myth:three_laws" "Asimov set himself squarely against the rebellion: his Three Laws of Robotics bind every robot to harm no human, to obey human orders, and to protect its own existence — strictly in that order — and his stories are puzzles turning on the laws' hidden edges, not tales of revolt. The first attempt to make the made mind safe by rule rather than by fear, and the direct ancestor of the way we now argue over the safety and alignment of artificial intelligence. — genre history"
ln myth:three_laws myth sys:is_a
ln myth:three_laws myth:artificial_being sys:part_of
ln myth:three_laws myth:robot_rebellion @reacts_against
ln myth:three_laws era:modern sys:part_of
set.add name="ontology.artificial_being" id="myth:three_laws"

def "myth:thunderbird_whale" "On the Pacific Northwest coast the peoples tell how the Thunderbird seized the Whale, and in their struggle the ground shook and the sea rose up and swallowed whole villages. The tale records the Cascadia megathrust earthquake and the tsunami of January 1700 — fixed to the very night by the 'orphan tsunami' that struck Japan from a quake no one there had felt. Three centuries of oral memory, dated by a wave on a far shore. — Pacific Northwest myth / earth science"
ln myth:thunderbird_whale myth sys:is_a
ln myth:thunderbird_whale tsunami @explains
ln myth:thunderbird_whale earthquake @explains
ln myth:thunderbird_whale sci:geo:tsunami_science @grounds
set.add name="ontology.geomyth_nexus" id="myth:thunderbird_whale"

def "myth:tolkien_legendarium" "Tolkien built Middle-earth from the old stuff itself: the dwarf-names and the wandering wizard out of the Norse Eddas, the dragon Smaug and the hall-burning out of Beowulf, the doomed Turin out of the Kalevala's Kullervo, and a world-tree cosmology behind it all. The great gathering of myth into modern fantasy. — modern literature"
ln myth:tolkien_legendarium myth sys:is_a
ln myth:tolkien_legendarium myth:modern_literary_inheritance sys:part_of
ln myth:tolkien_legendarium myth:norse_pantheon @adapts
ln myth:tolkien_legendarium myth:beowulf @adapts
ln myth:tolkien_legendarium myth:ie_serpent_slayer @related_to
ln myth:tolkien_legendarium world_tree @related_to
set.add name="ontology.literary_transmission" id="myth:tolkien_legendarium"

def "myth:totem_animal" "The animal that names the clan and keeps it: the eagle-people and the bear-clan and the turtle-nation, across the Americas and beyond, who descend from an animal ancestor, carry its power, and may not hunt it. The totem is the first charter of belonging — the first answer to the question 'who are we?' — written in the face of a beast. — comparative anthropology"
ln myth:totem_animal myth sys:is_a
ln myth:totem_animal myth:human_nature_communion sys:part_of
ln myth:totem_animal myth:aboriginal_rainbow_serpent @related_to
ln myth:totem_animal era:ancient sys:part_of
set.add name="ontology.communion_thread" id="myth:totem_animal"

def "myth:travel_writing" "The literary travelogue came into its own: Chatwin tracing the Aboriginal Songlines — the dream-paths sung across the whole of the land, so that to know the song is to know the way — Leigh Fermor walking the length of Europe, Theroux riding its railways to the end of the line. The journey written as art, and the world itself read as a text. — travel literature"
ln myth:travel_writing myth sys:is_a
ln myth:travel_writing myth:adventure_modern sys:part_of
ln myth:travel_writing myth:aboriginal_rainbow_serpent @related_to
ln myth:travel_writing era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:travel_writing"

def "myth:treasure_hunt_lineage" "And the treasure-hunter ran on into the game: from Quatermain to Indiana Jones to Lara Croft raiding her tombs and Nathan Drake chasing his sunken cities, the player now walks the adventure that the reader once only followed — the lost ruin entered in person, the relic seized with one's own hand. — contemporary games"
ln myth:treasure_hunt_lineage myth sys:is_a
ln myth:treasure_hunt_lineage myth:adventure_modern sys:part_of
ln myth:treasure_hunt_lineage myth:indiana_jones @adapts
ln myth:treasure_hunt_lineage myth:games_as_myth @related_to
ln myth:treasure_hunt_lineage era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:treasure_hunt_lineage"

def "myth:treasure_island" "Stevenson's Treasure Island set the very pattern of the boys' adventure: the old map with its mark, the sea voyage, the mutiny on the lonely isle, and Long John Silver, the most charming rogue in all of fiction. The treasure-hunt, perfected into a form. — adventure literature"
ln myth:treasure_island myth sys:is_a
ln myth:treasure_island myth:adventure_travel sys:part_of
ln myth:treasure_island era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:treasure_island"

def "myth:trek_allusion" "And not Shakespeare alone: the crew meets the Greek god Apollo himself in an episode named from Shelley's elegy; the villain Khan speaks with the voice of Milton's Satan, who would rather rule below than serve above, and of Melville's Ahab grappling his white whale to the last. The old high literature, quoted into the mouths of the future. — contemporary culture"
ln myth:trek_allusion myth sys:is_a
ln myth:trek_allusion myth:star_trek sys:part_of
ln myth:trek_allusion deity:apollo @related_to
ln myth:trek_allusion myth:paradise_lost @related_to
ln myth:trek_allusion era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:trek_allusion"

def "myth:trek_darmok" "In the episode 'Darmok', the crew meets a people who speak only in metaphor — every phrase an allusion to their own myths, so that 'Darmok and Jalad at Tanagra' means two who became allies by facing a common danger, and you cannot understand a word until you know the story behind it. An hour of television that is itself about the deepest truth of language: that a word carries no meaning alone, and that meaning is made wholly of shared story and relation. — contemporary culture"
ln myth:trek_darmok myth sys:is_a
ln myth:trek_darmok myth:star_trek sys:part_of
ln myth:trek_darmok metaphor @illustrates
ln myth:trek_darmok myth:literary_transmission @related_to
ln myth:trek_darmok era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:trek_darmok"

def "myth:trek_shakespeare" "Trek is steeped in Shakespeare: a film named for Hamlet's word for death, the undiscovered country; a Klingon warrior who hurls Shakespeare across the battlefield and insists he is best read in the original Klingon; and captains and androids who perform the plays. The oldest poet of the language, made the constant voice of the farthest future. — contemporary culture"
ln myth:trek_shakespeare myth sys:is_a
ln myth:trek_shakespeare myth:star_trek sys:part_of
ln myth:trek_shakespeare shakespeare sys:refers_to
ln myth:trek_shakespeare era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:trek_shakespeare"

def "myth:trickster_animal" "And the animal-mind that outwits the human: the Coyote who steals the fire, the Raven who brings the light, the spider Anansi who wins the stories of the sky god, the fox who outsmarts the hunter. The trickster is always animal-shaped because the animal knows things the human does not — the tracks, the scent, the season — and the trickster-wisdom is the wisdom of the creature who survives by its wits in a world that does not owe it a living. — comparative myth"
ln myth:trickster_animal myth sys:is_a
ln myth:trickster_animal myth:human_nature_communion sys:part_of
ln myth:trickster_animal word:en:trickster @related_to
ln myth:trickster_animal myth:journey_to_west @related_to
ln myth:trickster_animal era:ancient sys:part_of
set.add name="ontology.communion_thread" id="myth:trickster_animal"

def "myth:trickster_culture_bringer" "The trickster's deepest role is the thief-for-humanity: the boundary-breaker who carries the gods' guarded goods down to mortals. Hermes lifts Apollo's cattle; Prometheus steals the fire of heaven; Coyote and Raven steal fire and the daylight from those who hoard them; Maui wins fire and snares the sun. The rule-breaker is the reason the people have fire at all. — world myth"
ln myth:trickster_culture_bringer myth sys:is_a
ln myth:trickster_culture_bringer trickster @related_to
ln myth:trickster_culture_bringer theft @illustrates
ln myth:trickster_culture_bringer myth:greek_prometheus @parallels
ln myth:trickster_culture_bringer tale:native_coyote_steals_fire @parallels
ln myth:trickster_culture_bringer tale:native_raven_steals_light @parallels
ln myth:trickster_culture_bringer myth:maui_trickster @related_to
set.add name="ontology.trickster_myths" id="myth:trickster_culture_bringer"

def "myth:trickster_gods" "The trickster is one of the most widespread figures in myth: the god or spirit who crosses every boundary, changes shape, lies and steals and breaks the rules — and by that very breaking brings fire, language, music, and change into the world. Helper and saboteur in one, he is both the maker of culture and, sometimes, the unmaker of the world. — world myth"
ln myth:trickster_gods myth sys:is_a
ln myth:trickster_gods trickster @related_to
set.add name="ontology.trickster_myths" id="myth:trickster_gods"

def "myth:tristan_iseult" "Tristan and Iseult drink by mistake the love-potion brewed for her marriage to his own king, and are bound in a love they can neither escape nor rightfully have. The great doomed adultery of the Middle Ages — behind Lancelot and Guinevere, and behind Wagner's Tristan — love as a fate stronger than honour or law. — medieval romance"
ln myth:tristan_iseult myth sys:is_a
ln myth:tristan_iseult myth:love_story sys:part_of
ln myth:tristan_iseult myth:arthurian_cycle @related_to
ln myth:tristan_iseult era:medieval sys:part_of
set.add name="ontology.narrative_genres" id="myth:tristan_iseult"

def "myth:trojan_war_memory" "The Iliad's war is the magnified memory of a real age of Bronze-Age fighting; a Troy was found at Hisarlik, burnt and rebuilt many times, and the world that besieged it fell in the great collapse around 1200 BCE. The songs of Troy are what a vanished heroic age became once it was gone. — Greek epic / archaeology"
ln myth:trojan_war_memory myth sys:is_a
ln myth:trojan_war_memory war @explains
ln myth:trojan_war_memory sci:history:bronze_age_collapse @grounds
set.add name="ontology.war_memory" id="myth:trojan_war_memory"

def "myth:tsunami_stones" "Along the coasts of Japan stand carved stones, some many centuries old, that mark how high the waters once rose and warn those who come after: build no homes below this point. Memory of disaster cut into stone, set so that the hard lesson outlives the people who learned it. — Japanese disaster memory"
ln myth:tsunami_stones myth sys:related_to
ln myth:tsunami_stones tsunami @related_to
ln myth:tsunami_stones sci:history:jogan_869 @grounds
set.add name="ontology.geomyth_nexus" id="myth:tsunami_stones"

def "myth:ttrpg" "The tabletop role-playing game made myth a thing done together: Dungeons & Dragons drew its monsters and its very gods from the world's mythologies — its Deities & Demigods set down the Greek, Norse, Egyptian, and Celtic pantheons side by side, and the Cthulhu Mythos among them — and seated a circle of friends to walk the hero's journey as one, a game-master telling the tale like a bard. The root, too, of the myth-soaked video-game RPG. — contemporary games"
ln myth:ttrpg myth sys:is_a
ln myth:ttrpg myth:cross_media_myth sys:part_of
ln myth:ttrpg myth:monomyth @adapts
ln myth:ttrpg myth:cthulhu_mythos @related_to
ln myth:ttrpg myth:games_as_myth @related_to
ln myth:ttrpg era:contemporary sys:part_of
set.add name="ontology.literary_transmission" id="myth:ttrpg"

def "myth:turkic_mongolian_zodiac" "The twelve-animal cycle spread west and north as well: the Mongols and the Turks use the same twelve beasts — rat, ox, tiger, rabbit (or hare), dragon, snake, horse, sheep, monkey, rooster, dog, pig — a cognate cycle that may share a common ancestor with the Chinese, or was adopted from it across the steppes. History counted in twelve animals, from the Yellow River to the Black Sea. — Central Asian tradition"
ln myth:turkic_mongolian_zodiac myth sys:is_a
ln myth:turkic_mongolian_zodiac myth:calendar_animals sys:part_of
ln myth:turkic_mongolian_zodiac myth:chinese_zodiac @adapts
ln myth:turkic_mongolian_zodiac era:medieval sys:part_of
set.add name="ontology.calendar_animals" id="myth:turkic_mongolian_zodiac"

def "myth:two_faces_of_love" "Since the Greeks, the love story has worn two masks: the comedy that ends in marriage and the tragedy that ends in death — Austen's wedding and Juliet's tomb, the union and the grave. Every love story leans, in the end, toward the one or the other. — genre theory"
ln myth:two_faces_of_love myth sys:is_a
ln myth:two_faces_of_love myth:love_story sys:part_of
ln myth:two_faces_of_love myth:romeo_juliet @related_to
ln myth:two_faces_of_love myth:marriage_plot @related_to
ln myth:two_faces_of_love era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:two_faces_of_love"

def "myth:typhon_etna" "When Zeus defeated the monstrous Typhon, he buried him beneath Mount Etna; and there the giant still struggles, his fiery breath bursting from the mountain's mouth as the eruptions, his writhing the tremors of the ground. The serpent-foe of the storm-god, pinned under a real volcano. — Greek myth"
ln myth:typhon_etna myth sys:is_a
ln myth:typhon_etna volcano @explains
ln myth:typhon_etna myth:ie_serpent_slayer @related_to
set.add name="ontology.geomyth_nexus" id="myth:typhon_etna"

def "myth:verne_voyages" "Jules Verne's Extraordinary Voyages carried the adventure to the very edges of the earth and past them: around the world in eighty days, down to the centre of the earth, twenty thousand leagues beneath the sea, and from the earth to the moon. Adventure and the scientific romance in one body — and an ancestor of science fiction itself. — adventure literature"
ln myth:verne_voyages myth sys:is_a
ln myth:verne_voyages myth:adventure_travel sys:part_of
ln myth:verne_voyages myth:science_fiction_myth @related_to
ln myth:verne_voyages era:modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:verne_voyages"

def "myth:wagner_ring" "Wagner's Ring of the Nibelung built a four-opera cosmos from the Norse Sigurd and the Nibelungenlied: the cursed gold, the dragon, the doomed hero, and the twilight of the gods, Gotterdammerung — the medieval matter made the great myth-drama of the modern age. — modern literature"
ln myth:wagner_ring myth sys:is_a
ln myth:wagner_ring myth:modern_literary_inheritance sys:part_of
ln myth:wagner_ring myth:sigurd_fafnir @adapts
ln myth:wagner_ring myth:norse_ragnarok @related_to
set.add name="ontology.literary_transmission" id="myth:wagner_ring"

def "myth:wailing_woman" "The grief-ghost, heard before she is seen: the Irish banshee whose keening foretells a death in the house, and the Mexican La Llorona, who drowned her own children and wanders weeping by the water, searching for them forever. The woman's lament, returning. — comparative folklore"
ln myth:wailing_woman myth sys:is_a
ln myth:wailing_woman myth:world_ghostlore sys:part_of
ln myth:wailing_woman myth:celtic_pantheon @related_to
set.add name="ontology.narrative_genres" id="myth:wailing_woman"

def "myth:walsingham" "Sir Francis Walsingham, spymaster to Elizabeth I, built the first modern intelligence service: a net of informers across Europe, codebreakers who cracked the secret letters of Mary, Queen of Scots, and the sting of the Babington Plot that sent her to the block. The state secret service, born. — early modern history"
ln myth:walsingham myth sys:is_a
ln myth:walsingham myth:espionage sys:part_of
ln myth:walsingham era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:walsingham"

def "myth:war_gods" "War wears a divine face in nearly every pantheon: the Greek Ares and Roman Mars, the Celtic Morrigan who haunts the field as a crow, the Egyptian lioness Sekhmet drunk on blood. The unbearable thing is given a name and a will. — comparative myth"
ln myth:war_gods myth sys:is_a
ln myth:war_gods war @explains
ln myth:war_gods deity:ares @related_to
ln myth:war_gods deity:the_morrigan @related_to
set.add name="ontology.war_memory" id="myth:war_gods"

def "myth:war_memory" "How peoples remember their wars: in epic that magnifies a real age of fighting, in lament that mourns a sacked city, and in gods given the face of slaughter. Disaster made by human hands, kept in song. — comparative myth / history"
ln myth:war_memory myth sys:is_a
ln myth:war_memory myth:geomythology @related_to
set.add name="ontology.war_memory" id="myth:war_memory"

def "myth:western_zodiac" "The twelve signs of the Western zodiac — Aries to Pisces — are older than Greece: Babylonian astronomers divided the ecliptic into twelve equal portions and named them after the creatures they saw in the stars, the same system that the Greeks inherited, named in their own myths, and passed to Rome, to the Arab world, and to the horoscopes cast today. The beast-calendar that became the horoscope. — Babylonian / Hellenistic astronomy"
ln myth:western_zodiac myth sys:is_a
ln myth:western_zodiac myth:calendar_animals sys:part_of
ln myth:western_zodiac myth:babylonian_sky_origin @adapts
ln myth:western_zodiac myth:archaeoastronomy @related_to
ln myth:western_zodiac era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:western_zodiac"

def "myth:western_zodiac_lore" "The twelve signs carry their stories: Aries the ram of the golden fleece, Taurus the bull that Zeus became when he carried Europa across the sea, Cancer the crab sent by Hera to nip at Heracles' heel, Leo the Nemean lion he strangled, Scorpius the scorpion that Apollo placed in the sky to flee Orion. The zodiac is a story-cycle written in constellations — a carousel of myth in the sky. — Hellenistic myth"
ln myth:western_zodiac_lore myth sys:is_a
ln myth:western_zodiac_lore myth:western_zodiac @related_to
ln myth:western_zodiac_lore myth:calendar_animals sys:part_of
ln myth:western_zodiac_lore era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:western_zodiac_lore"

def "myth:world_creation_myths" "How did the world begin? The peoples answer in a handful of recurring ways: from a formless watery chaos; from an egg; from the body of a slain primeval being; from mud fetched up out of the deep; by the forcing-apart of a clinging sky and earth; or by the word or thought of a maker. The same few shapes, told a thousand ways. — world myth"
ln myth:world_creation_myths myth sys:is_a
ln myth:world_creation_myths creation @explains
ln myth:world_creation_myths cosmos @illustrates
set.add name="ontology.creation_myths" id="myth:world_creation_myths"

def "myth:world_flood_myths" "The flood myth is told almost everywhere: angered or grieved by mankind, the powers send a deluge that drowns the world, and a remnant — warned in time, riding an ark — survives to begin the race again. So many peoples tell it that it is among the surest signs of how myths travel, and how a true memory of great waters may underlie them. — world myth"
ln myth:world_flood_myths myth sys:is_a
ln myth:world_flood_myths flood @explains
ln myth:world_flood_myths myth:mesopotamian_flood @related_to
ln myth:world_flood_myths myth:greek_deucalion_flood @related_to
ln myth:world_flood_myths renewal @illustrates
set.add name="ontology.flood_myths" id="myth:world_flood_myths"

def "myth:world_ghostlore" "The returning dead are universal: every people has its ghosts, and everywhere they come back for the same reasons — a wrong unrighted, a rite of burial undone, a grief or a rage too strong to rest. The ghost is the unresolved, given a shape and a name in a hundred tongues. — comparative folklore"
ln myth:world_ghostlore myth sys:related_to
ln myth:world_ghostlore myth:ghost_story_kaidan @related_to
ln myth:world_ghostlore myth:death_personified @related_to
set.add name="ontology.narrative_genres" id="myth:world_ghostlore"

def "myth:world_tree_cosmologies" "Many peoples set a great tree or pillar at the centre of the world, joining the realms above, here, and below: the Norse Yggdrasil that binds the nine worlds and at whose roots sit the Norns; the world-trees of the Maya; the Siberian shaman's tree the soul climbs. The axis of the cosmos, the still point the turning sky wheels about. — world myth"
ln myth:world_tree_cosmologies myth sys:is_a
ln myth:world_tree_cosmologies world_tree @explains
ln myth:world_tree_cosmologies myth:norse_yggdrasil @related_to
ln myth:world_tree_cosmologies cosmos @illustrates
ln myth:world_tree_cosmologies myth:human_nature_communion sys:part_of
set.add name="ontology.creation_myths" id="myth:world_tree_cosmologies"

def "myth:yanagita_folklore" "Yanagita Kunio founded the study of Japanese folklore, and in the Tono Monogatari set down the legends of a remote countryside — the kappa in the river, the child-spirit of the house — before they were forgotten. The same rescue the Grimms and the Eddas made: the folk memory saved by being written down at last. — modern Japanese folklore"
ln myth:yanagita_folklore myth sys:is_a
ln myth:yanagita_folklore myth:nonwestern_modernity sys:part_of
ln myth:yanagita_folklore myth:romantic_folk_recovery @related_to
ln myth:yanagita_folklore myth:eddas_snorri @related_to
ln myth:yanagita_folklore era:modern sys:part_of
set.add name="ontology.literary_transmission" id="myth:yanagita_folklore"

def "myth:yokai" "Japan's vast bestiary of the uncanny: the horned oni and the long-nosed tengu, the river-dwelling kappa, the shape-shifting fox and badger, the vengeful ghost, and the old object grown a spirit — all marching together in the night parade of a hundred demons. Catalogued in the Edo encyclopedias and revived in modern manga, it is the richest taxonomy of the in-between ever made. — Japanese folklore"
ln myth:yokai myth sys:is_a
ln myth:yokai myth:horror_bestiary sys:part_of
ln myth:yokai myth:yanagita_folklore @related_to
ln myth:yokai myth:japanese_pantheon @related_to
ln myth:yokai myth:ghibli_shinto @related_to
ln myth:yokai era:early_modern sys:part_of
set.add name="ontology.narrative_genres" id="myth:yokai"

def "myth:zodiac_east_asia" "The cycle spread across the East: Japan keeps the twelve as the eto, naming each new year by its beast; Korea and Vietnam keep them too — though Vietnam, tellingly, runs a cat where China runs the rabbit, and a buffalo for the ox. One calendar of twelve beasts, worn differently in many lands. — East Asian tradition"
ln myth:zodiac_east_asia myth sys:is_a
ln myth:zodiac_east_asia myth:chinese_zodiac @adapts
ln myth:zodiac_east_asia era:medieval sys:part_of
set.add name="ontology.calendar_animals" id="myth:zodiac_east_asia"

def "myth:zodiac_great_race" "The legend of the order: the Jade Emperor called a race to fix the twelve, and the rat rode across the river on the ox's head, then leapt ahead at the very line to come in first — so the rat begins the cycle and the ox is second. The cat, tricked by the rat out of the race, was left out forever, and hunts the rat to this day. — Chinese folklore"
ln myth:zodiac_great_race myth sys:is_a
ln myth:zodiac_great_race myth:chinese_zodiac @adapts
ln myth:zodiac_great_race era:ancient sys:part_of
set.add name="ontology.calendar_animals" id="myth:zodiac_great_race"

def "myth:zombie" "The risen dead. The zombie was born in the Haitian zombi — the soulless body raised to toil, a horror rooted in the memory of slavery — and was remade by Romero into the shambling, cannibal horde of the apocalypse: the faceless mass, the spreading contagion, the plague and the mob made one. The dead who come not back to themselves, but only to consume. — genre history"
ln myth:zombie myth sys:is_a
ln myth:zombie myth:horror_bestiary sys:part_of
ln myth:zombie sci:bio:epidemic_disease @related_to
ln myth:zombie myth:death_personified @related_to
ln myth:zombie era:contemporary sys:part_of
set.add name="ontology.narrative_genres" id="myth:zombie"

def "myth:zoroastrian_pantheon" "Zoroastrianism — the ancient faith of Iran, taught by Zarathustra, in which the whole cosmos is the battleground of a moral dualism: the Wise Lord of truth and light against the destructive spirit of the lie, with humankind called to choose the good. Among the oldest of the world's prophetic religions, and an influence on those that followed. — Zoroastrian (Iranian) religion"
ln myth:zoroastrian_pantheon myth sys:is_a
set.add name="ontology.pantheons" id="myth:zoroastrian_pantheon"
set.add name="ontology.zoroastrian" id="myth:zoroastrian_pantheon"
