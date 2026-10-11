# film_movements.ak
# Film movements, cinematographic concepts, awards, and television dramatic forms
# Sources: BFI, Cahiers du cinéma, Grove Film — Public domain terminology
#

# ── Namespace anchors ────────────────────────────────────────────────────────

def "film:movement" "Root namespace for cinematic movements and schools of filmmaking."
def "film:concept" "Root namespace for cinematographic and theoretical concepts."
def "film:award" "Root namespace for major international film awards."
def "tv:form" "Root namespace for television dramatic forms."
def "film:studio_era" "Root namespace for Hollywood studio system era categories."

# ── Film movements ────────────────────────────────────────────────────────────

def "film:movement:german_expressionism" "German Expressionism: Germany 1919–1927; The Cabinet of Dr. Caligari, Nosferatu; distorted sets, high-contrast shadow, psychological dread; influenced Film Noir."
ln film:movement:german_expressionism film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:german_expressionism"

def "film:movement:soviet_montage" "Soviet Montage: USSR 1920s; Eisenstein, Vertov, Pudovkin; Battleship Potemkin; dialectical montage as ideological argument; collision of shots creates meaning beyond each image."
ln film:movement:soviet_montage film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:soviet_montage"

def "film:movement:poetic_realism" "Poetic Realism: France 1930s; Renoir, Carné, Prévert; La Règle du Jeu; lyrical fatalism; working-class melancholy; studio-built streets evoking doomed atmosphere."
ln film:movement:poetic_realism film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:poetic_realism"

def "film:movement:italian_neorealism" "Italian Neorealism: Italy 1944–1952; Rossellini, De Sica, Visconti; Rome Open City, Bicycle Thieves; location shooting, non-professional actors, poverty themes."
ln film:movement:italian_neorealism film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:italian_neorealism"

def "film:movement:french_new_wave" "Nouvelle Vague: France 1958–1968; Godard, Truffaut, Chabrol, Rohmer; jump cuts, location shooting, auteur theory in practice; Breathless (1960) as founding text."
al film:movement:french_new_wave film:movement:nouvelle_vague
ln film:movement:french_new_wave film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:french_new_wave"

def "film:movement:direct_cinema" "Direct Cinema: USA 1960s; Maysles, Wiseman, Pennebaker; observational documentary; no narration, no staged events; fly-on-the-wall presence."
ln film:movement:direct_cinema film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:direct_cinema"

def "film:movement:cinema_verite" "Cinéma Vérité: France 1960s; Rouch, Marker; participatory documentary; filmmaker visible and interventionist; Chronicle of a Summer (1961)."
ln film:movement:cinema_verite film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:cinema_verite"

def "film:movement:new_hollywood" "New Hollywood: USA 1967–1980; Coppola, Scorsese, Kubrick, Altman, Bogdanovich; auteur influence on the studio system; Bonnie and Clyde, The Godfather."
ln film:movement:new_hollywood film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:new_hollywood"

def "film:movement:japanese_new_wave" "Japanese New Wave (Nuberu Bagu): Japan 1950s–1970s; Oshima, Imamura, Wakamatsu; social critique, sexuality, political radicalism; Nagisa Oshima's In the Realm of the Senses."
ln film:movement:japanese_new_wave film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:japanese_new_wave"

def "film:movement:iranian_new_wave" "Iranian New Wave: Iran 1960s–present; Kiarostami, Makhmalbaf, Panahi; minimalist realism, non-professional actors, poetic metaphor; Where Is the Friend's Home? (1987)."
ln film:movement:iranian_new_wave film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:iranian_new_wave"

def "film:movement:czech_new_wave" "Czech New Wave: Czechoslovakia 1960s; Forman, Menzel, Chytilová, Jireš; Prague Spring cultural context; Daisies (1966), Closely Watched Trains; dark surrealist comedy."
ln film:movement:czech_new_wave film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:czech_new_wave"

def "film:movement:parallel_cinema" "Parallel Cinema: India 1960s–1980s; Satyajit Ray, Mrinal Sen, Shyam Benegal; Bengali and regional art cinema counter to Bollywood; Apu Trilogy as touchstone."
ln film:movement:parallel_cinema film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:parallel_cinema"

def "film:movement:third_cinema" "Third Cinema: Latin America 1960s–70s; Solanas, Getino, Rocha; Towards a Third Cinema manifesto (1969); anti-Hollywood, anti-auteur, politically committed revolutionary cinema."
ln film:movement:third_cinema film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:third_cinema"

def "film:movement:hong_kong_new_wave" "Hong Kong New Wave: Hong Kong 1979–1990s; Ann Hui, Tsui Hark, Wong Kar-wai; stylised genre filmmaking fused with art cinema sensibility; Chungking Express (1994)."
ln film:movement:hong_kong_new_wave film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:hong_kong_new_wave"

def "film:movement:dogme_95" "Dogme 95: Denmark 1995; Lars von Trier, Vinterberg; Vow of Chastity: natural light, hand-held camera, location only, no non-diegetic music; The Celebration (1998)."
ln film:movement:dogme_95 film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:dogme_95"

def "film:movement:black_cinema_usa" "Black American Cinema: Blaxploitation and independent African-American film; Spike Lee, Charles Burnett; Killer of Sheep (1978), Do the Right Thing (1989)."
ln film:movement:black_cinema_usa film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:black_cinema_usa"

def "film:movement:new_latin_american_cinema" "New Latin American Cinema: 1960s–70s; Cuba, Brazil, Argentina; revolutionary politics; Cinema Novo (Rocha); Hour of the Furnaces (Solanas); anti-imperialist aesthetics."
ln film:movement:new_latin_american_cinema film:movement sys:part_of
set.add name="ontology.film_movements" id="film:movement:new_latin_american_cinema"

# inter-movement relations
ln film:movement:german_expressionism film:movement:french_new_wave film:influenced
ln film:movement:soviet_montage film:movement:french_new_wave film:influenced
ln film:movement:italian_neorealism film:movement:french_new_wave film:influenced
ln film:movement:italian_neorealism film:movement:parallel_cinema film:influenced
ln film:movement:french_new_wave film:movement:new_hollywood film:influenced
ln film:movement:direct_cinema film:movement:cinema_verite film:contrasts_with
ln film:movement:third_cinema film:movement:new_latin_american_cinema sys:part_of
ln film:movement:dogme_95 film:movement:direct_cinema film:influenced_by

# ── Cinematographic concepts ──────────────────────────────────────────────────

def "film:concept:montage" "Montage: editing as meaning-making; juxtaposing shots produces an idea beyond either shot alone; Eisenstein's Odessa Steps sequence; Kuleshov Effect (neutral face plus object equals implied emotion)."
ln film:concept:montage film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:montage"

def "film:concept:mise_en_scene" "Mise-en-scène: all visual elements composed within the frame — set, lighting, costume, actor position and movement, colour; contrasted with montage-centred film theory."
ln film:concept:mise_en_scene film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:mise_en_scene"

def "film:concept:auteur_theory" "Auteur Theory: director as primary creative intelligence of a film; Cahiers du cinéma critics (Truffaut 1954 essay); personal vision over industry formula; traceable stylistic signature."
ln film:concept:auteur_theory film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:auteur_theory"

def "film:concept:continuity_editing" "Continuity Editing: Hollywood invisible style; 180-degree rule, match on action, eyeline match; viewer forgets the editing; space and time appear seamless and unmediated."
ln film:concept:continuity_editing film:concept sys:part_of
ln film:concept:continuity_editing film:concept:montage film:contrasts_with
set.add name="ontology.film_concepts" id="film:concept:continuity_editing"

def "film:concept:deep_focus" "Deep Focus: large depth of field keeping foreground and background simultaneously sharp; Gregg Toland and Orson Welles in Citizen Kane (1941); expands spatial information within the frame."
ln film:concept:deep_focus film:concept sys:part_of
ln film:concept:deep_focus film:concept:mise_en_scene film:belongs_to
set.add name="ontology.film_concepts" id="film:concept:deep_focus"

def "film:concept:long_take" "Long Take: extended uncut shot; Tarkovsky, Ophüls, Hou Hsiao-hsien, Jancsó; real-time duration creates rhythm; camera movement substitutes for or enriches editing."
ln film:concept:long_take film:concept sys:part_of
ln film:concept:long_take film:concept:slow_cinema film:related_to
set.add name="ontology.film_concepts" id="film:concept:long_take"

def "film:concept:expressionist_lighting" "Expressionist Lighting: chiaroscuro; extreme shadow and highlight contrast; from German Expressionism to Film Noir; low-key, hard light sources; villain lit from below."
ln film:concept:expressionist_lighting film:concept sys:part_of
ln film:concept:expressionist_lighting film:concept:mise_en_scene film:belongs_to
ln film:concept:expressionist_lighting film:movement:german_expressionism film:originated_in
set.add name="ontology.film_concepts" id="film:concept:expressionist_lighting"

def "film:concept:verfremdungseffekt" "Verfremdungseffekt: Brecht's alienation effect applied to film; prevents emotional identification; reminds audience they are watching a constructed performance; titles, direct address, visible theatricality."
ln film:concept:verfremdungseffekt film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:verfremdungseffekt"

def "film:concept:diegetic_sound" "Diegetic Sound: sound that exists within the story world and can be heard by characters; contrasted with non-diegetic sound (orchestral score, voice-over narrator)."
ln film:concept:diegetic_sound film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:diegetic_sound"

def "film:concept:unreliable_narrator" "Unreliable Narrator: narrative voice or perspective that is distorted, deceived, or actively deceptive; Rashomon (Kurosawa, 1950); requires viewer reconstruction of events."
ln film:concept:unreliable_narrator film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:unreliable_narrator"

def "film:concept:neorealist_aesthetics" "Neorealist Aesthetics: location shooting, non-professional actors, natural light, working-class subject matter, improvisation; codified by De Sica and Rossellini in postwar Italy."
ln film:concept:neorealist_aesthetics film:concept sys:part_of
ln film:concept:neorealist_aesthetics film:movement:italian_neorealism film:originated_in
set.add name="ontology.film_concepts" id="film:concept:neorealist_aesthetics"

def "film:concept:slow_cinema" "Slow Cinema: contemplative pace; minimal plot; extended long takes; spiritual or material observation; Béla Tarr, Chantal Akerman, Apichatpong Weerasethakul, Lav Diaz."
ln film:concept:slow_cinema film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:slow_cinema"

def "film:concept:found_footage" "Found Footage: fictional or documentary style using supposedly pre-existing recordings as narrative material; mockumentary variant; The Blair Witch Project (1999) popularised horror application."
ln film:concept:found_footage film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:found_footage"

def "film:concept:genre_hybridity" "Genre Hybridity: deliberate mixing of genre conventions; spaghetti Western with noir elements; horror comedy; post-modern deconstruction and recombination of genre expectations."
ln film:concept:genre_hybridity film:concept sys:part_of
set.add name="ontology.film_concepts" id="film:concept:genre_hybridity"

# concept cross-links
ln film:concept:auteur_theory film:movement:french_new_wave film:theorised_by
ln film:concept:montage film:movement:soviet_montage film:theorised_by
ln film:concept:neorealist_aesthetics film:concept:continuity_editing film:differs_from

# ── Film awards ───────────────────────────────────────────────────────────────

def "film:award:academy_awards" "Academy Awards (Oscars): awarded by the Academy of Motion Picture Arts and Sciences since 1929; Hollywood-centric; categories include Best Picture, Director, Actor, Actress, and technical awards."
al film:award:academy_awards film:award:oscars
ln film:award:academy_awards film:award sys:part_of
set.add name="ontology.film_awards" id="film:award:academy_awards"

def "film:award:cannes_palme_dor" "Palme d'Or: top prize of the Cannes Film Festival since 1955 (present form); most prestigious European film competition; art cinema and international auteur focus."
ln film:award:cannes_palme_dor film:award sys:part_of
set.add name="ontology.film_awards" id="film:award:cannes_palme_dor"

def "film:award:venice_golden_lion" "Golden Lion (Leone d'Oro): top prize of the Venice Film Festival; oldest film festival (founded 1932); international competition spanning all genres and traditions."
ln film:award:venice_golden_lion film:award sys:part_of
set.add name="ontology.film_awards" id="film:award:venice_golden_lion"

def "film:award:berlin_golden_bear" "Golden Bear (Goldener Bär): top prize of the Berlin International Film Festival (Berlinale); international competition with pronounced political and social emphasis."
ln film:award:berlin_golden_bear film:award sys:part_of
set.add name="ontology.film_awards" id="film:award:berlin_golden_bear"

def "film:award:bafta_film" "BAFTA Film Awards: British Academy of Film and Television Arts annual film awards; British counterpart to the Academy Awards; covers international and British productions."
ln film:award:bafta_film film:award sys:part_of
set.add name="ontology.film_awards" id="film:award:bafta_film"

def "film:award:cesar_award" "César Award: French film industry awards since 1976; voted by Académie des Arts et Techniques du Cinéma; French equivalent of the Oscars."
ln film:award:cesar_award film:award sys:part_of
set.add name="ontology.film_awards" id="film:award:cesar_award"

def "film:award:golden_globe" "Golden Globe Awards: presented by the Hollywood Foreign Press Association since 1944; covers both film and television; distinct electorate from Academy Awards."
ln film:award:golden_globe film:award sys:part_of
set.add name="ontology.film_awards" id="film:award:golden_globe"

def "film:award:silver_bear" "Silver Bear: Berlin Film Festival secondary awards; includes Grand Jury Prize, Silver Bear for Director, Actor, and Actress; given alongside Golden Bear."
ln film:award:silver_bear film:award sys:part_of
ln film:award:silver_bear film:award:berlin_golden_bear film:awarded_at
set.add name="ontology.film_awards" id="film:award:silver_bear"

def "film:award:jury_prize_cannes" "Cannes Jury Prize: third-tier competition award at Cannes; often honours experimental, transgressive, or formally unconventional work overlooked by top prizes."
ln film:award:jury_prize_cannes film:award sys:part_of
ln film:award:jury_prize_cannes film:award:cannes_palme_dor film:awarded_at
set.add name="ontology.film_awards" id="film:award:jury_prize_cannes"

def "film:award:critics_week" "Semaine de la Critique (Critics' Week): parallel section at Cannes for first or second feature films; curated by the Syndicat Français de la Critique de Cinéma."
ln film:award:critics_week film:award sys:part_of
ln film:award:critics_week film:award:cannes_palme_dor film:parallel_to
set.add name="ontology.film_awards" id="film:award:critics_week"

# ── Television dramatic forms ─────────────────────────────────────────────────

def "tv:form:anthology_series" "Anthology Series: each episode or season tells an independent story with a new cast; The Twilight Zone (1959), True Detective seasons as separate self-contained narratives."
ln tv:form:anthology_series tv:form sys:part_of
set.add name="ontology.film_movements" id="tv:form:anthology_series"

def "tv:form:miniseries" "Miniseries: limited episode count, typically two to thirteen episodes; complete self-contained narrative arc; Roots (1977), Band of Brothers (2001)."
ln tv:form:miniseries tv:form sys:part_of
set.add name="ontology.film_movements" id="tv:form:miniseries"

def "tv:form:serial_drama" "Serial Drama: continuing storyline across all episodes requiring sequential viewing; soap opera ancestry; Dallas, Twin Peaks; narrative depends on accumulated prior knowledge."
ln tv:form:serial_drama tv:form sys:part_of
set.add name="ontology.film_movements" id="tv:form:serial_drama"

def "tv:form:prestige_drama" "Prestige Drama: cinematic production quality applied to long-form television; character complexity; The Sopranos (1999) inaugurated the era; auteur showrunners; often HBO-style."
ln tv:form:prestige_drama tv:form sys:part_of
ln tv:form:prestige_drama tv:form:serial_drama film:builds_on
set.add name="ontology.film_movements" id="tv:form:prestige_drama"

def "tv:form:docudrama" "Docudrama: dramatic reconstruction of real events; hybrid of documentary evidence and dramatic re-enactment; journalistic or historical subject matter."
ln tv:form:docudrama tv:form sys:part_of
set.add name="ontology.film_movements" id="tv:form:docudrama"

def "tv:form:kitchen_sink_drama" "Kitchen Sink Drama: British realist tradition; working-class domestic settings; Coronation Street as origin; kitchen as battleground for social and emotional conflict; 1950s–present."
ln tv:form:kitchen_sink_drama tv:form sys:part_of
set.add name="ontology.film_movements" id="tv:form:kitchen_sink_drama"

# ── Studio era categories ─────────────────────────────────────────────────────

def "film:studio_era:silent" "Silent Era: 1895–1927; no synchronised sound; intertitles carry dialogue; heightened physical performance; Chaplin, Keaton, Murnau, Eisenstein; ends with The Jazz Singer (1927)."
ln film:studio_era:silent film:studio_era sys:part_of
set.add name="ontology.film_movements" id="film:studio_era:silent"

def "film:studio_era:pre_code" "Pre-Code Hollywood: 1929–1934; before Hays Code strict enforcement; frank sexuality, violence, and moral ambiguity; Baby Face (1933), I Am a Fugitive from a Chain Gang (1932)."
ln film:studio_era:pre_code film:studio_era sys:part_of
ln film:studio_era:pre_code film:studio_era:silent film:follows
set.add name="ontology.film_movements" id="film:studio_era:pre_code"

def "film:studio_era:golden_age" "Golden Age of Hollywood: 1930s–1940s; studio system at peak efficiency; genre films; star contracts; Casablanca, Gone with the Wind, Stagecoach; major studios as dominant force."
ln film:studio_era:golden_age film:studio_era sys:part_of
set.add name="ontology.film_movements" id="film:studio_era:golden_age"

def "film:studio_era:classical_hollywood" "Classical Hollywood Cinema: 1917–1960; continuity editing as dominant mode; genre-based production; star system; three-act dramatic structure; omniscient narration."
al film:studio_era:classical_hollywood film:studio_era:studio_system
ln film:studio_era:classical_hollywood film:studio_era sys:part_of
ln film:studio_era:classical_hollywood film:concept:continuity_editing film:defined_by
set.add name="ontology.film_movements" id="film:studio_era:classical_hollywood"

def "film:studio_era:postwar_international" "Postwar International Cinema: 1945–1965; European and Japanese cinema rises to global prominence; Bergman, Kurosawa, Antonioni, Fellini; challenge to Hollywood dominance."
ln film:studio_era:postwar_international film:studio_era sys:part_of
ln film:studio_era:postwar_international film:studio_era:classical_hollywood film:follows
set.add name="ontology.film_movements" id="film:studio_era:postwar_international"
