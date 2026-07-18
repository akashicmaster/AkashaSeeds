# Akasha ontology (world pack) — narrative craft: the storyteller's toolkit.
# Enriches the existing structure layer (nar:/polti:/plot:/journey:) with the
# working craft — structure models, character, conflict, devices, viewpoint,
# elements. Bridged to arch:* archetypes, myth:/tale: examples, and the Jataka
# narrator engine. Colon convention throughout.

def "nar:craft" "The craft of shaping story — structure, character, conflict and technique."

# ── structure models ──
def "nar:structure:three_act" "Setup → Confrontation → Resolution — the dominant Western shape."
ln nar:structure:three_act nar:craft {'hero_journey': ['journey:call_to_adventure', 'journey:ordeal'], 'kishotenketsu': ['nar:structure:three_act'], 'frame_story': ['tale:aesop_crow_pitcher']}
def "nar:structure:freytag_pyramid" "Five acts: exposition, rising action, climax, falling action, denouement."
ln nar:structure:freytag_pyramid nar:craft {'hero_journey': ['journey:call_to_adventure', 'journey:ordeal'], 'kishotenketsu': ['nar:structure:three_act'], 'frame_story': ['tale:aesop_crow_pitcher']}
def "nar:structure:kishotenketsu" "起承転結 — the East-Asian four-part shape (intro/development/TWIST/reconciliation) that needs no central conflict."
ln nar:structure:kishotenketsu nar:craft {'hero_journey': ['journey:call_to_adventure', 'journey:ordeal'], 'kishotenketsu': ['nar:structure:three_act'], 'frame_story': ['tale:aesop_crow_pitcher']}
def "nar:structure:hero_journey" "The monomyth cycle of departure, initiation and return (Campbell/Vogler)."
ln nar:structure:hero_journey nar:craft {'hero_journey': ['journey:call_to_adventure', 'journey:ordeal'], 'kishotenketsu': ['nar:structure:three_act'], 'frame_story': ['tale:aesop_crow_pitcher']}
def "nar:structure:in_medias_res" "Opening in the middle of the action, filling in the past later."
ln nar:structure:in_medias_res nar:craft {'hero_journey': ['journey:call_to_adventure', 'journey:ordeal'], 'kishotenketsu': ['nar:structure:three_act'], 'frame_story': ['tale:aesop_crow_pitcher']}
def "nar:structure:frame_story" "A story enclosing another (a tale told within a tale)."
ln nar:structure:frame_story nar:craft {'hero_journey': ['journey:call_to_adventure', 'journey:ordeal'], 'kishotenketsu': ['nar:structure:three_act'], 'frame_story': ['tale:aesop_crow_pitcher']}
def "nar:structure:nonlinear" "Events told out of chronological order."
ln nar:structure:nonlinear nar:craft {'hero_journey': ['journey:call_to_adventure', 'journey:ordeal'], 'kishotenketsu': ['nar:structure:three_act'], 'frame_story': ['tale:aesop_crow_pitcher']}
def "nar:structure:save_the_cat" "A modern 15-beat screenwriting template."
ln nar:structure:save_the_cat nar:craft {'hero_journey': ['journey:call_to_adventure', 'journey:ordeal'], 'kishotenketsu': ['nar:structure:three_act'], 'frame_story': ['tale:aesop_crow_pitcher']}
# structure stages
def "nar:stage:exposition" "The opening that establishes world, character and situation."
ln nar:stage:exposition nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:inciting_incident" "The event that sets the story in motion."
ln nar:stage:inciting_incident nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:rising_action" "Escalating complications toward the crisis."
ln nar:stage:rising_action nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:climax" "The peak turning point of highest tension."
ln nar:stage:climax nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:falling_action" "The unwinding after the climax."
ln nar:stage:falling_action nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:denouement" "The final resolution and new equilibrium (結)."
ln nar:stage:denouement nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:ki" "起 — the introduction (kishōtenketsu)."
ln nar:stage:ki nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:sho" "承 — the development."
ln nar:stage:sho nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:ten" "転 — the twist/turn, the pivot of kishōtenketsu."
ln nar:stage:ten nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}
def "nar:stage:ketsu" "結 — the reconciliation/conclusion."
ln nar:stage:ketsu nar:craft {'climax': ['nar:structure:freytag_pyramid'], 'ten': ['nar:structure:kishotenketsu'], 'ki': ['nar:structure:kishotenketsu']}

# ── character ──
def "nar:character:protagonist" "The central character the story follows."
ln nar:character:protagonist nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:antagonist" "The force or character opposing the protagonist."
ln nar:character:antagonist nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:deuteragonist" "The second most important character."
ln nar:character:deuteragonist nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:foil" "A character whose contrast highlights another."
ln nar:character:foil nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:confidant" "One to whom a character confides, revealing interior life."
ln nar:character:confidant nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:character_arc" "The inner change a character undergoes across the story."
ln nar:character:character_arc nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:positive_arc" "A character grows and overcomes their flaw."
ln nar:character:positive_arc nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:negative_arc" "A character declines into their flaw (a fall)."
ln nar:character:negative_arc nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:flat_arc" "A steadfast character who changes the world, not themselves."
ln nar:character:flat_arc nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:characterization" "The means by which a character is revealed."
ln nar:character:characterization nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
def "nar:character:archetype" "A recurring character pattern (hero, mentor, shadow…)."
ln nar:character:archetype nar:craft {'antagonist': ['arch:shadow'], 'archetype': ['arch:hero', 'arch:mentor', 'arch:trickster'], 'positive_arc': ['nar:redemption', 'nar:coming_of_age'], 'negative_arc': ['nar:fall', 'nar:tragedy'], 'protagonist': ['arch:hero']}
# archetype bridges (Vogler/Jung) → arch:*
ln nar:character:archetype arch:hero thesaurus:related
ln nar:character:archetype arch:mentor thesaurus:related
ln nar:character:archetype arch:threshold_guardian thesaurus:related
ln nar:character:archetype arch:herald thesaurus:related
ln nar:character:archetype arch:shapeshifter thesaurus:related
ln nar:character:archetype arch:shadow thesaurus:related
ln nar:character:archetype arch:trickster thesaurus:related
ln nar:character:archetype arch:ally thesaurus:related

# ── conflict types ──
def "nar:conflict:person_vs_person" "Struggle against another character."
ln nar:conflict:person_vs_person nar:craft {'person_vs_self': ['nar:conversion', 'nar:redemption'], 'person_vs_society': ['socio:social_conflict', 'nar:rebellion'], 'person_vs_fate': ['nar:prophecy', 'myth:greek_persephone'], 'person_vs_supernatural': ['myth:beowulf', 'deity:loki']}
def "nar:conflict:person_vs_self" "Internal struggle within the character."
ln nar:conflict:person_vs_self nar:craft {'person_vs_self': ['nar:conversion', 'nar:redemption'], 'person_vs_society': ['socio:social_conflict', 'nar:rebellion'], 'person_vs_fate': ['nar:prophecy', 'myth:greek_persephone'], 'person_vs_supernatural': ['myth:beowulf', 'deity:loki']}
def "nar:conflict:person_vs_nature" "Struggle against the natural world."
ln nar:conflict:person_vs_nature nar:craft {'person_vs_self': ['nar:conversion', 'nar:redemption'], 'person_vs_society': ['socio:social_conflict', 'nar:rebellion'], 'person_vs_fate': ['nar:prophecy', 'myth:greek_persephone'], 'person_vs_supernatural': ['myth:beowulf', 'deity:loki']}
def "nar:conflict:person_vs_society" "Struggle against social order or norms."
ln nar:conflict:person_vs_society nar:craft {'person_vs_self': ['nar:conversion', 'nar:redemption'], 'person_vs_society': ['socio:social_conflict', 'nar:rebellion'], 'person_vs_fate': ['nar:prophecy', 'myth:greek_persephone'], 'person_vs_supernatural': ['myth:beowulf', 'deity:loki']}
def "nar:conflict:person_vs_fate" "Struggle against destiny or the gods."
ln nar:conflict:person_vs_fate nar:craft {'person_vs_self': ['nar:conversion', 'nar:redemption'], 'person_vs_society': ['socio:social_conflict', 'nar:rebellion'], 'person_vs_fate': ['nar:prophecy', 'myth:greek_persephone'], 'person_vs_supernatural': ['myth:beowulf', 'deity:loki']}
def "nar:conflict:person_vs_supernatural" "Struggle against gods, monsters or the uncanny."
ln nar:conflict:person_vs_supernatural nar:craft {'person_vs_self': ['nar:conversion', 'nar:redemption'], 'person_vs_society': ['socio:social_conflict', 'nar:rebellion'], 'person_vs_fate': ['nar:prophecy', 'myth:greek_persephone'], 'person_vs_supernatural': ['myth:beowulf', 'deity:loki']}
def "nar:conflict:person_vs_technology" "Struggle against machines or the systems they build."
ln nar:conflict:person_vs_technology nar:craft {'person_vs_self': ['nar:conversion', 'nar:redemption'], 'person_vs_society': ['socio:social_conflict', 'nar:rebellion'], 'person_vs_fate': ['nar:prophecy', 'myth:greek_persephone'], 'person_vs_supernatural': ['myth:beowulf', 'deity:loki']}

# ── narrative devices ──
def "nar:device:foreshadowing" "Hinting at events to come."
ln nar:device:foreshadowing nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:flashback" "A scene set earlier than the main timeline."
ln nar:device:flashback nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:flashforward" "A glimpse of a future moment."
ln nar:device:flashforward nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:chekhovs_gun" "Every introduced element must pay off — no idle details."
ln nar:device:chekhovs_gun nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:macguffin" "An object that drives the plot but matters little in itself."
ln nar:device:macguffin nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:deus_ex_machina" "An implausible sudden rescue resolving the plot."
ln nar:device:deus_ex_machina nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:red_herring" "A misleading clue."
ln nar:device:red_herring nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:dramatic_irony" "The audience knows what a character does not."
ln nar:device:dramatic_irony nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:situational_irony" "An outcome contrary to expectation."
ln nar:device:situational_irony nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:verbal_irony" "Saying the opposite of what is meant."
ln nar:device:verbal_irony nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:symbolism" "An object standing for a larger meaning."
ln nar:device:symbolism nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:motif" "A recurring image or idea threading the work."
ln nar:device:motif nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:allegory" "A story whose surface encodes an abstract meaning."
ln nar:device:allegory nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:unreliable_narrator" "A narrator whose account cannot be fully trusted."
ln nar:device:unreliable_narrator nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:cliffhanger" "An unresolved tense ending that compels continuation."
ln nar:device:cliffhanger nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:plot_twist" "A sudden unexpected turn (転)."
ln nar:device:plot_twist nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}
def "nar:device:leitmotif" "A recurring theme tied to a character or idea."
ln nar:device:leitmotif nar:craft {'motif': ['oral:motif', 'oral:motif_index'], 'allegory': ['tale:aesop_crow_pitcher'], 'plot_twist': ['nar:stage:ten', 'nar:unmasking'], 'dramatic_irony': ['nar:tragedy'], 'symbolism': ['foodstud:food_symbolism']}

# ── point of view ──
def "nar:pov:first_person" "Narrated by a character as 'I'."
ln nar:pov:first_person nar:craft {'stream_of_consciousness': ['psy:consciousness'], 'first_person': ['oral:oral_history']}
def "nar:pov:second_person" "Narrated as 'you', addressing the reader."
ln nar:pov:second_person nar:craft {'stream_of_consciousness': ['psy:consciousness'], 'first_person': ['oral:oral_history']}
def "nar:pov:third_limited" "Third person confined to one character's knowledge."
ln nar:pov:third_limited nar:craft {'stream_of_consciousness': ['psy:consciousness'], 'first_person': ['oral:oral_history']}
def "nar:pov:third_omniscient" "An all-knowing narrator across all characters."
ln nar:pov:third_omniscient nar:craft {'stream_of_consciousness': ['psy:consciousness'], 'first_person': ['oral:oral_history']}
def "nar:pov:third_objective" "An outside camera-eye, reporting only the observable."
ln nar:pov:third_objective nar:craft {'stream_of_consciousness': ['psy:consciousness'], 'first_person': ['oral:oral_history']}
def "nar:pov:stream_of_consciousness" "Rendering the unfiltered flow of a mind."
ln nar:pov:stream_of_consciousness nar:craft {'stream_of_consciousness': ['psy:consciousness'], 'first_person': ['oral:oral_history']}

# ── story elements ──
def "nar:element:theme" "The underlying idea or meaning of a work."
ln nar:element:theme nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}
def "nar:element:tone" "The author's attitude conveyed by style."
ln nar:element:tone nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}
def "nar:element:mood" "The emotional atmosphere felt by the reader."
ln nar:element:mood nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}
def "nar:element:setting" "The time and place of the story."
ln nar:element:setting nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}
def "nar:element:pacing" "The rhythm at which the story unfolds."
ln nar:element:pacing nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}
def "nar:element:subplot" "A secondary storyline supporting the main."
ln nar:element:subplot nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}
def "nar:element:fabula" "The story — events in chronological order."
ln nar:element:fabula nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}
def "nar:element:syuzhet" "The plot — the order and manner events are told."
ln nar:element:syuzhet nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}
def "nar:element:exposition_element" "Background information the reader needs."
ln nar:element:exposition_element nar:craft {'theme': ['nar:craft'], 'mood': ['emo:joy', 'emo:anxiety'], 'setting': ['geog:place'], 'fabula': ['nar:structure:nonlinear']}

# ── the craft feeds the Jataka narrator (story assembly) ──
def "nar:narration" "Assembling interpreted material into a told story — Jataka's work."
ln nar:narration nar:craft thesaurus:related
ln nar:narration nar:structure:hero_journey thesaurus:related
ln nar:craft polti:01 thesaurus:related
ln nar:craft plot:the_quest thesaurus:related
