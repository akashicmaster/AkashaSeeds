# stage_forms.ak
# Stage dramatic forms, theatrical traditions, and dramaturgy concepts
# Sources: Oxford Companion to Theatre, Brockett's History of Theatre — Public domain terminology
#

# ── Namespace anchors ────────────────────────────────────────────────────────

def "stage:form" "Root namespace for stage dramatic and theatrical forms."
def "stage:tradition" "Root namespace for theatrical traditions by culture or school."
def "stage:concept" "Root namespace for dramaturgy and theatrical theory concepts."

# ── Stage dramatic forms ──────────────────────────────────────────────────────

def "stage:form:tragedy" "Tragedy: Greek origin; Aristotle's Poetics: hamartia, catharsis, mimesis; fall of a noble hero from prosperity to ruin through flaw or error; Sophocles, Shakespeare, Racine."
ln stage:form:tragedy stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:tragedy"

def "stage:form:comedy" "Comedy: humorous resolution; mistaken identity, social reconciliation, marriage as closure; movement from disorder to restored order; Aristophanes, Molière, Goldoni."
ln stage:form:comedy stage:form sys:part_of
ln stage:form:comedy stage:form:tragedy stage:contrasts_with
set.add name="ontology.stage_forms" id="stage:form:comedy"

def "stage:form:tragicomedy" "Tragicomedy: mixed tragic and comic register; uncertain or bittersweet resolution; Chekhov's The Cherry Orchard as exemplar; tragicomic ambiguity as the modern dramatic default."
ln stage:form:tragicomedy stage:form sys:part_of
ln stage:form:tragicomedy stage:form:tragedy stage:blends
ln stage:form:tragicomedy stage:form:comedy stage:blends
set.add name="ontology.stage_forms" id="stage:form:tragicomedy"

def "stage:form:satire" "Satire: social criticism through irony, exaggeration, and mockery; targets institutions, follies, and abuses of power; Aristophanes, Ben Jonson, Swift; didactic corrective intent."
ln stage:form:satire stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:satire"

def "stage:form:farce" "Farce: extreme comedy relying on rapid coincidences, physical humour, disguise, and misunderstanding; Feydeau, Plautus; door-slamming pace; plot mechanics over character depth."
ln stage:form:farce stage:form sys:part_of
ln stage:form:farce stage:form:comedy stage:subtype_of
set.add name="ontology.stage_forms" id="stage:form:farce"

def "stage:form:melodrama" "Melodrama: exaggerated emotion; clear moral polarisation into villain, hero, and victim; Victorian popular stage; accompanying music heightens emotional effect; virtue rewarded."
ln stage:form:melodrama stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:melodrama"

def "stage:form:well_made_play" "Well-Made Play (pièce bien faite): Eugène Scribe's formula; tight exposition, rising action, obligatory confrontation scene, logical dénouement; mechanical craft over poetic truth."
ln stage:form:well_made_play stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:well_made_play"

def "stage:form:naturalism" "Naturalism: Zola, Ibsen, Strindberg; slice-of-life representation; environment and heredity determine character; fourth wall convention; Ghosts, Miss Julie; scientific determinism on stage."
ln stage:form:naturalism stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:naturalism"

def "stage:form:expressionism_theatre" "Theatrical Expressionism: distorted reality externalising inner psychological states; Strindberg's A Dream Play as precursor; O'Neill, Kaiser; subjective vision over social surface."
ln stage:form:expressionism_theatre stage:form sys:part_of
ln stage:form:expressionism_theatre stage:form:naturalism stage:reacts_against
set.add name="ontology.stage_forms" id="stage:form:expressionism_theatre"

def "stage:form:epic_theatre" "Epic Theatre: Brecht; Verfremdungseffekt (alienation effect); gestus; placards and episodic structure; social learning prioritised over emotional empathy; Mother Courage and Her Children."
ln stage:form:epic_theatre stage:form sys:part_of
ln stage:form:epic_theatre stage:form:naturalism stage:reacts_against
set.add name="ontology.stage_forms" id="stage:form:epic_theatre"

def "stage:form:theatre_of_absurd" "Theatre of the Absurd: Beckett, Ionesco, Pinter, Genet; post-WWII meaninglessness; circular logic, language breakdown, repetition; Waiting for Godot, The Bald Soprano."
ln stage:form:theatre_of_absurd stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:theatre_of_absurd"

def "stage:form:theatre_of_cruelty" "Theatre of Cruelty: Antonin Artaud; visceral non-verbal performance; attack on audience senses; ritualised ceremony; influenced 1960s happenings, physical theatre, and immersive performance."
ln stage:form:theatre_of_cruelty stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:theatre_of_cruelty"

def "stage:form:documentary_theatre" "Documentary Theatre (Verbatim Theatre): real documents, interviews, and testimony used as script material; Peter Weiss, Erwin Piscator; Peter Weiss's The Investigation (1965)."
ln stage:form:documentary_theatre stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:documentary_theatre"

def "stage:form:musical_theatre" "Musical Theatre: integrated songs, spoken dialogue, and choreography; book plus music plus lyrics as unified form; Rodgers and Hammerstein consolidated the integrated model; Oklahoma! (1943)."
ln stage:form:musical_theatre stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:musical_theatre"

def "stage:form:revue" "Revue: variety format combining songs, comedy sketches, and spectacle without a unified narrative; topical satirical content; Berlin 1920s cabaret revues; Broadway revues; Music Box Revue."
ln stage:form:revue stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:revue"

def "stage:form:vaudeville" "Vaudeville: American variety entertainment; acrobatics, comedy, juggling, and song in succession; 1880s–1930s; Keith-Albee circuits; replaced by cinema and radio."
ln stage:form:vaudeville stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:vaudeville"

def "stage:form:music_hall" "Music Hall: British variety entertainment; pub and theatre origin; comic songs, dance, and character turns; Marie Lloyd, Dan Leno; 1850s–1930s; working-class popular culture."
ln stage:form:music_hall stage:form sys:part_of
ln stage:form:music_hall stage:form:vaudeville stage:parallel_to
set.add name="ontology.stage_forms" id="stage:form:music_hall"

def "stage:form:burlesque" "Burlesque: comic travesty of serious works through parody and grotesque exaggeration; Victorian British parody tradition; US variant also incorporated striptease variety elements."
ln stage:form:burlesque stage:form sys:part_of
ln stage:form:burlesque stage:form:satire stage:related_to
set.add name="ontology.stage_forms" id="stage:form:burlesque"

def "stage:form:mystery_play" "Mystery Play: medieval Christian drama staging biblical narrative from Creation to Last Judgement; performed by craft guilds; York, Chester, and Wakefield cycles."
ln stage:form:mystery_play stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:mystery_play"

def "stage:form:miracle_play" "Miracle Play: medieval drama depicting saints' lives and miraculous interventions; Marian miracle plays; French mystère; popular devotional and didactic entertainment."
ln stage:form:miracle_play stage:form sys:part_of
ln stage:form:miracle_play stage:form:mystery_play stage:related_to
set.add name="ontology.stage_forms" id="stage:form:miracle_play"

def "stage:form:morality_play" "Morality Play: allegorical medieval drama; personified virtues and vices battle for the human soul; Everyman (c. 1510); psychological and spiritual allegory in dramatic form."
ln stage:form:morality_play stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:morality_play"

def "stage:form:masque" "Masque: English courtly entertainment featuring spectacular staging, music, dance, and allegory; Inigo Jones designed scenery; Ben Jonson wrote texts; flourished 1605–1640 under James I and Charles I."
ln stage:form:masque stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:masque"

def "stage:form:opera_seria" "Opera Seria: Baroque and Classical serious opera; heroic or mythological subjects; da capo aria structure; Metastasio as dominant librettist; Handel, Gluck; reformed by Gluck in 1760s."
ln stage:form:opera_seria stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:opera_seria"

def "stage:form:opera_buffa" "Opera Buffa: comic opera; buffo bass as stock character; situational comedy and social satire; La Serva Padrona (Pergolesi, 1733); Mozart's Da Ponte operas as pinnacle."
ln stage:form:opera_buffa stage:form sys:part_of
ln stage:form:opera_buffa stage:form:opera_seria stage:contrasts_with
set.add name="ontology.stage_forms" id="stage:form:opera_buffa"

def "stage:form:operetta" "Operetta: light opera with spoken dialogue, songs, and romantic or comic plots; Offenbach, Johann Strauss II, Gilbert and Sullivan; intermediate between opera and musical theatre."
ln stage:form:operetta stage:form sys:part_of
ln stage:form:operetta stage:form:opera_buffa stage:descended_from
ln stage:form:operetta stage:form:musical_theatre stage:ancestor_of
set.add name="ontology.stage_forms" id="stage:form:operetta"

def "stage:form:singspiel" "Singspiel: German-language sung play; spoken dialogue alternates with musical numbers; Die Zauberflöte (Mozart, 1791); direct ancestor of the German musical and operetta traditions."
ln stage:form:singspiel stage:form sys:part_of
ln stage:form:singspiel stage:form:operetta stage:ancestor_of
set.add name="ontology.stage_forms" id="stage:form:singspiel"

def "stage:form:zarzuela" "Zarzuela: Spanish sung drama in vernacular; alternates spoken dialogue with musical scenes; 17th-century origin; 19th-century golden age; lyric theatre deeply rooted in Spanish national identity."
ln stage:form:zarzuela stage:form sys:part_of
set.add name="ontology.stage_forms" id="stage:form:zarzuela"

# ── Theatrical traditions ─────────────────────────────────────────────────────

def "stage:tradition:greek_tragedy" "Greek Tragedy: Athens 5th century BCE; Aeschylus, Sophocles, Euripides; performed at City Dionysia festival; chorus, mask, orchestra (dancing space); trilogy form (Aeschylus)."
ln stage:tradition:greek_tragedy stage:tradition sys:part_of
ln stage:tradition:greek_tragedy stage:form:tragedy stage:produced
set.add name="ontology.stage_forms" id="stage:tradition:greek_tragedy"

def "stage:tradition:greek_comedy" "Greek Comedy: Old Comedy (Aristophanes): political satire and fantasy; New Comedy (Menander): domestic situations and stock characters; New Comedy directly influenced Roman theatre."
ln stage:tradition:greek_comedy stage:tradition sys:part_of
ln stage:tradition:greek_comedy stage:form:comedy stage:produced
set.add name="ontology.stage_forms" id="stage:tradition:greek_comedy"

def "stage:tradition:roman_theatre" "Roman Theatre: Plautus and Terence in comedy; Seneca in tragedy (intended for reading); permanent stone theatres; entertainments for the masses; stock character types inherited from Greek New Comedy."
ln stage:tradition:roman_theatre stage:tradition sys:part_of
ln stage:tradition:roman_theatre stage:tradition:greek_comedy stage:descended_from
set.add name="ontology.stage_forms" id="stage:tradition:roman_theatre"

def "stage:tradition:elizabethan_theatre" "Elizabethan and Jacobean Theatre: England 1558–1642; Shakespeare, Marlowe, Jonson, Webster; open-air thrust stage; Globe Theatre; blank verse; mixed social audience; no scenery."
ln stage:tradition:elizabethan_theatre stage:tradition sys:part_of
set.add name="ontology.stage_forms" id="stage:tradition:elizabethan_theatre"

def "stage:tradition:french_classical" "French Classical Theatre: Corneille, Racine, Molière; strict observance of the unities of time, place, and action; alexandrine verse; bienséance (decorum); Comédie-Française (founded 1680)."
ln stage:tradition:french_classical stage:tradition sys:part_of
ln stage:tradition:french_classical stage:tradition:greek_tragedy stage:influenced_by
set.add name="ontology.stage_forms" id="stage:tradition:french_classical"

def "stage:tradition:commedia_dellarte" "Commedia dell'Arte: Italian improvised comedy; lazzi (comic business); fixed mask types (Arlecchino, Pantalone, il Dottore, Innamorati); travelling troupes; 16th–18th centuries."
ln stage:tradition:commedia_dellarte stage:tradition sys:part_of
ln stage:tradition:commedia_dellarte stage:form:comedy stage:related_to
set.add name="ontology.stage_forms" id="stage:tradition:commedia_dellarte"

def "stage:tradition:spanish_golden_age" "Spanish Golden Age Theatre (Siglo de Oro): Lope de Vega, Calderón de la Barca; corral de comedias (courtyard theatre); cape-and-sword plays; auto sacramental (allegorical religious play)."
ln stage:tradition:spanish_golden_age stage:tradition sys:part_of
set.add name="ontology.stage_forms" id="stage:tradition:spanish_golden_age"

def "stage:tradition:stanislavski_method" "Stanislavski System: Moscow Art Theatre; emotional memory; given circumstances; through-line of action; influenced Lee Strasberg's Method at the Actors Studio; psychological realism in acting."
ln stage:tradition:stanislavski_method stage:tradition sys:part_of
set.add name="ontology.stage_forms" id="stage:tradition:stanislavski_method"

def "stage:tradition:brechtian_theatre" "Brechtian Theatre: Berliner Ensemble; dialectical acting; gestus as social attitude made physical; historical materialism applied to dramatic form; political function of art over cathartic release."
ln stage:tradition:brechtian_theatre stage:tradition sys:part_of
ln stage:tradition:brechtian_theatre stage:form:epic_theatre stage:practices
ln stage:tradition:brechtian_theatre stage:tradition:stanislavski_method stage:reacts_against
set.add name="ontology.stage_forms" id="stage:tradition:brechtian_theatre"

def "stage:tradition:moscow_art_theatre" "Moscow Art Theatre: founded by Stanislavski and Nemirovich-Danchenko in 1898; Chekhov world premieres; ensemble acting ethic; psychological realism; The Seagull revival launched the company."
ln stage:tradition:moscow_art_theatre stage:tradition sys:part_of
ln stage:tradition:moscow_art_theatre stage:tradition:stanislavski_method stage:origin_of
set.add name="ontology.stage_forms" id="stage:tradition:moscow_art_theatre"

# ── Dramaturgy concepts ───────────────────────────────────────────────────────

def "stage:concept:catharsis" "Catharsis: Aristotle's Poetics; purgation of pity and fear through tragic action; audience achieves emotional release and moral clarification; debated whether medical or pleasurable metaphor."
ln stage:concept:catharsis stage:concept sys:part_of
ln stage:concept:catharsis stage:form:tragedy stage:produced_by
set.add name="ontology.stage_forms" id="stage:concept:catharsis"

def "stage:concept:hamartia" "Hamartia: Greek; tragic flaw or error of judgement causing the hero's downfall; Aristotle; hubris as the most discussed form; not necessarily a moral defect — may be ignorance or miscalculation."
ln stage:concept:hamartia stage:concept sys:part_of
ln stage:concept:hamartia stage:form:tragedy stage:belongs_to
set.add name="ontology.stage_forms" id="stage:concept:hamartia"

def "stage:concept:hubris" "Hubris: Greek; excessive pride or arrogance toward gods, fate, or social limits; classic form of hamartia; nemesis (divine retribution) follows as narrative consequence."
ln stage:concept:hubris stage:concept sys:part_of
ln stage:concept:hubris stage:concept:hamartia stage:subtype_of
set.add name="ontology.stage_forms" id="stage:concept:hubris"

def "stage:concept:dramatic_irony" "Dramatic Irony: audience possesses information withheld from one or more characters on stage; Oedipus Rex as structural example; creates suspense, pity, and tragic inevitability."
ln stage:concept:dramatic_irony stage:concept sys:part_of
set.add name="ontology.stage_forms" id="stage:concept:dramatic_irony"

def "stage:concept:fourth_wall" "Fourth Wall: imaginary boundary between actors and audience in the proscenium convention; naturalist assumption; breaking the fourth wall (direct address) foregrounds the theatrical contract."
ln stage:concept:fourth_wall stage:concept sys:part_of
ln stage:concept:fourth_wall stage:form:naturalism stage:codified_by
set.add name="ontology.stage_forms" id="stage:concept:fourth_wall"

def "stage:concept:unities" "Dramatic Unities: Aristotle/neoclassical doctrine; unity of time (action within 24 hours), unity of place (single location), unity of action (single main plot); French Classical strict; Elizabethan relaxed."
ln stage:concept:unities stage:concept sys:part_of
ln stage:concept:unities stage:tradition:french_classical stage:enforced_by
set.add name="ontology.stage_forms" id="stage:concept:unities"

def "stage:concept:soliloquy" "Soliloquy: character speaks thoughts aloud while alone on stage; inner life externalised for audience; Hamlet's 'To be or not to be'; convention that other characters cannot hear."
ln stage:concept:soliloquy stage:concept sys:part_of
ln stage:concept:soliloquy stage:tradition:elizabethan_theatre stage:characteristic_of
set.add name="ontology.stage_forms" id="stage:concept:soliloquy"

def "stage:concept:aside" "Aside: character speaks briefly and directly to audience, conventionally unheard by other characters on stage; confidential commentary; creates comic irony and audience complicity."
ln stage:concept:aside stage:concept sys:part_of
ln stage:concept:aside stage:concept:fourth_wall stage:breaks
set.add name="ontology.stage_forms" id="stage:concept:aside"

def "stage:concept:deus_ex_machina" "Deus ex Machina: implausible late resolution introduced from outside the drama's internal logic; originating in Greek theatre where a god was lowered by crane; now pejorative for contrived rescue."
ln stage:concept:deus_ex_machina stage:concept sys:part_of
ln stage:concept:deus_ex_machina stage:tradition:greek_tragedy stage:originated_in
set.add name="ontology.stage_forms" id="stage:concept:deus_ex_machina"

def "stage:concept:gestus" "Gestus: Brecht's term; social attitude expressed through characteristic physical behaviour and posture; reveals class, power, and ideology through the body; acting as social demonstration."
ln stage:concept:gestus stage:concept sys:part_of
ln stage:concept:gestus stage:tradition:brechtian_theatre stage:theorised_by
ln stage:concept:gestus stage:form:epic_theatre stage:belongs_to
set.add name="ontology.stage_forms" id="stage:concept:gestus"

def "stage:concept:leitmotif" "Leitmotif: recurring musical phrase, theme, or image associated with a character, place, or idea; Wagner's term from opera theory; extended to literature, film, and dramatic structure generally."
ln stage:concept:leitmotif stage:concept sys:part_of
set.add name="ontology.stage_forms" id="stage:concept:leitmotif"

def "stage:concept:obligatory_scene" "Obligatory Scene (scène à faire): confrontation or revelation scene that the preceding dramatic structure has promised the audience; Scribe's term; must be included or the audience feels cheated."
ln stage:concept:obligatory_scene stage:concept sys:part_of
ln stage:concept:obligatory_scene stage:form:well_made_play stage:belongs_to
set.add name="ontology.stage_forms" id="stage:concept:obligatory_scene"
