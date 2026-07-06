# instruments_hs.ak
# Musical instrument classification (Hornbostel-Sachs) + notable traditional instruments
# Source: Hornbostel-Sachs 1914 rev. ICTM 2011; UNESCO ICH; Grove Music — Public domain
#

# ── Hornbostel-Sachs class anchors ─────────────────────────────────────────────

def "instr:class" "Root anchor for the Hornbostel-Sachs instrument classification system"

def "instr:chordophone" "Instruments with vibrating strings as primary sound source (HS 3)"
ln instr:chordophone instr:class sys:part_of

def "instr:aerophone" "Instruments in which vibrating air is the primary sound source (HS 4)"
ln instr:aerophone instr:class sys:part_of

def "instr:membranophone" "Instruments with a vibrating stretched membrane as primary sound source (HS 2)"
ln instr:membranophone instr:class sys:part_of

def "instr:idiophone" "Instruments that are themselves the primary vibrating body; no membrane or string (HS 1)"
ln instr:idiophone instr:class sys:part_of

def "instr:lute" "Lutes: neck-bearing chordophones; string runs parallel to soundboard (HS 321)"
ln instr:lute instr:class sys:part_of

def "instr:zither" "Zithers: chordophones with no resonating neck; strings over a body (HS 312)"
ln instr:zither instr:class sys:part_of

def "instr:harp" "Harps: chordophones in which strings run perpendicular to the soundboard (HS 322)"
ln instr:harp instr:class sys:part_of

def "instr:bowl_lyre" "Bowl lyres: yoke-bearing chordophones with bowl resonator (HS 321.2)"
ln instr:bowl_lyre instr:class sys:part_of

def "instr:flute" "Flutes: edge aerophones; air split against an edge (HS 421)"
ln instr:flute instr:class sys:part_of

def "instr:reed_aerophone" "Reed instruments: air column excited by a vibrating reed (HS 422)"
ln instr:reed_aerophone instr:class sys:part_of

def "instr:frame_drum" "Frame drums: membranophones in which the shell depth is less than the membrane radius (HS 211)"
ln instr:frame_drum instr:class sys:part_of

def "instr:barrel_drum" "Barrel and cylindrical drums: tubular membranophones (HS 211.2)"
ln instr:barrel_drum instr:class sys:part_of

def "instr:gong" "Gongs and struck metallophones: percussion idiophones of metal (HS 111.2)"
ln instr:gong instr:class sys:part_of

# ── Japanese instruments ────────────────────────────────────────────────────────

def "instr:koto" "Koto: 13-string Japanese board zither; movable bridges; silk or nylon strings; national instrument"
ln instr:koto instr:zither sys:part_of
ln instr:koto music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:koto"

def "instr:shamisen" "Shamisen: 3-string long-necked lute with cat or dog skin drum head; plucked with large plectrum; Edo period"
ln instr:shamisen instr:lute sys:part_of
ln instr:shamisen music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:shamisen"

def "instr:biwa" "Biwa: pear-shaped Japanese lute; 4–5 strings; used in court music and blind monk storytelling traditions"
ln instr:biwa instr:lute sys:part_of
ln instr:biwa music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:biwa"

def "instr:shakuhachi" "Shakuhachi: end-blown notched bamboo flute; 5 holes; Zen Buddhist meditation tradition; Kinko and Tozan schools"
ln instr:shakuhachi instr:flute sys:part_of
ln instr:shakuhachi music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:shakuhachi"

def "instr:nohkan" "Nohkan: transverse bamboo flute for Noh theatre; narrow bore insert produces shrill overblown tone"
ln instr:nohkan instr:flute sys:part_of
ln instr:nohkan music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:nohkan"

def "instr:shinobue" "Shinobue: thin-walled bamboo transverse flute; higher pitch than nohkan; folk festivals and matsuri"
ln instr:shinobue instr:flute sys:part_of
ln instr:shinobue music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:shinobue"

def "instr:sho" "Sho: Japanese mouth organ; 17 bamboo pipes arranged in circle; plays chords; central to gagaku"
ln instr:sho instr:aerophone sys:part_of
ln instr:sho music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:sho"

def "instr:hichiriki" "Hichiriki: double-reed cylindrical oboe; 9 holes; penetrating nasal tone; core gagaku melody instrument"
ln instr:hichiriki instr:reed_aerophone sys:part_of
ln instr:hichiriki music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:hichiriki"

def "instr:taiko" "Taiko: Japanese barrel drum family; festival, ceremonial, and theatrical use; many sizes from shime to o-daiko"
ln instr:taiko instr:barrel_drum sys:part_of
ln instr:taiko music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:taiko"

def "instr:tsuzumi" "Tsuzumi (ko-tsuzumi): hourglass tension drum; lacquered shell; used in Noh and Nagauta ensembles"
ln instr:tsuzumi instr:membranophone sys:part_of
ln instr:tsuzumi music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:tsuzumi"

# ── Chinese instruments ─────────────────────────────────────────────────────────

def "instr:guqin" "Guqin: 7-string silk-strung board zither; 3,000-year history; literati tradition; UNESCO ICH 2003"
ln instr:guqin instr:zither sys:part_of
ln instr:guqin music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:guqin"

def "instr:guzheng" "Guzheng: 21+ string movable-bridge board zither; standard concert repertoire; descended from ancient se"
ln instr:guzheng instr:zither sys:part_of
ln instr:guzheng music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:guzheng"

def "instr:pipa" "Pipa: 4-string pear-shaped plucked lute; plectrum technique; Tang dynasty court and narrative traditions"
ln instr:pipa instr:lute sys:part_of
ln instr:pipa music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:pipa"

def "instr:erhu" "Erhu: 2-string spike fiddle; bowed with horsehair bow; silk strings; most common Chinese bowed chordophone"
ln instr:erhu instr:chordophone sys:part_of
ln instr:erhu music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:erhu"

def "instr:dizi" "Dizi: transverse bamboo flute; membrane-covered hole (mo) adds buzzing timbre; bright penetrating tone"
ln instr:dizi instr:flute sys:part_of
ln instr:dizi music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:dizi"

def "instr:xiao" "Xiao: end-blown notched bamboo flute; softer and darker tone than dizi; ensemble and solo use"
ln instr:xiao instr:flute sys:part_of
ln instr:xiao music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:xiao"

def "instr:sheng" "Sheng: Chinese mouth organ; 17–36 bamboo pipes in gourd or metal wind-chest; prototype of Western free-reed instruments"
ln instr:sheng instr:aerophone sys:part_of
ln instr:sheng music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:sheng"

def "instr:suona" "Suona: loud double-reed shawm with conical bore and flared metal bell; outdoor ceremonies and processions"
ln instr:suona instr:reed_aerophone sys:part_of
ln instr:suona music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:suona"

def "instr:bianzhong" "Bianzhong: set of tuned bronze bells suspended in frames; Zhou dynasty; pitched idiophone; ritual music"
ln instr:bianzhong instr:idiophone sys:part_of
ln instr:bianzhong music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:bianzhong"

# ── Korean instruments ──────────────────────────────────────────────────────────

def "instr:gayageum" "Gayageum: 12-string (later 25-string) Korean plucked zither; movable bridges; court and folk traditions"
ln instr:gayageum instr:zither sys:part_of
ln instr:gayageum music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:gayageum"

def "instr:geomungo" "Geomungo: 6-string plucked zither; struck and plucked with bamboo stick (suldae); aristocratic court music"
ln instr:geomungo instr:zither sys:part_of
ln instr:geomungo music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:geomungo"

def "instr:haegeum" "Haegeum: 2-string spike fiddle; bowed; used in court music (jeong ak) and folk genres"
ln instr:haegeum instr:chordophone sys:part_of
ln instr:haegeum music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:haegeum"

def "instr:daegeum" "Daegeum: large Korean transverse bamboo flute; membrane hole (cheong) adds resonant buzzing timbre"
ln instr:daegeum instr:flute sys:part_of
ln instr:daegeum music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:daegeum"

def "instr:janggu" "Janggu: hourglass double-headed drum; struck with stick and hand; most common Korean percussion instrument"
ln instr:janggu instr:membranophone sys:part_of
ln instr:janggu music:region:east_asian sys:part_of
set.add name="ontology.instruments" id="instr:janggu"

# ── Indian instruments ──────────────────────────────────────────────────────────

def "instr:sitar" "Sitar: long-necked plucked lute; 18–20 strings (7 main, 11–13 sympathetic); Hindustani classical"
ln instr:sitar instr:lute sys:part_of
ln instr:sitar music:region:south_asian sys:part_of
set.add name="ontology.instruments" id="instr:sitar"

def "instr:sarod" "Sarod: short-necked plucked lute; metal fingerboard with no frets; sympathetic strings; Hindustani classical"
ln instr:sarod instr:lute sys:part_of
ln instr:sarod music:region:south_asian sys:part_of
set.add name="ontology.instruments" id="instr:sarod"

def "instr:sarangi" "Sarangi: short-necked bowed fiddle; 3 main gut strings plus ~37 sympathetic; Hindustani accompaniment"
ln instr:sarangi instr:chordophone sys:part_of
ln instr:sarangi music:region:south_asian sys:part_of
set.add name="ontology.instruments" id="instr:sarangi"

def "instr:veena" "Veena (vina): fretted long-necked plucked lute; many regional forms; primary Carnatic classical instrument"
ln instr:veena instr:lute sys:part_of
ln instr:veena music:region:south_asian sys:part_of
set.add name="ontology.instruments" id="instr:veena"

def "instr:tabla" "Tabla: pair of hand drums; right (tabla, treble) and left (bayan, bass); primary Hindustani classical percussion"
ln instr:tabla instr:membranophone sys:part_of
ln instr:tabla music:region:south_asian sys:part_of
set.add name="ontology.instruments" id="instr:tabla"

def "instr:mridangam" "Mridangam: double-headed barrel drum; primary Carnatic classical percussion; right and left heads differently tuned"
ln instr:mridangam instr:barrel_drum sys:part_of
ln instr:mridangam music:region:south_asian sys:part_of
set.add name="ontology.instruments" id="instr:mridangam"

def "instr:tampura" "Tampura (tambura): 4-string long-necked drone lute; sustains tonic and fifth; not melodic but foundational"
ln instr:tampura instr:lute sys:part_of
ln instr:tampura music:region:south_asian sys:part_of
set.add name="ontology.instruments" id="instr:tampura"

def "instr:bansuri" "Bansuri: side-blown bamboo flute; 6–8 holes; Hindustani classical; associated with Krishna in iconography"
ln instr:bansuri instr:flute sys:part_of
ln instr:bansuri music:region:south_asian sys:part_of
set.add name="ontology.instruments" id="instr:bansuri"

# ── Middle Eastern and Persian instruments ──────────────────────────────────────

def "instr:oud" "Oud: short-necked fretless lute; 11 strings (5 double courses plus bass); Arab, Ottoman, and Persian classical"
ln instr:oud instr:lute sys:part_of
ln instr:oud music:region:middle_eastern sys:part_of
set.add name="ontology.instruments" id="instr:oud"

def "instr:ney" "Ney: oblique end-blown open-tube flute; 6 front holes plus thumb hole; Persian, Arab, and Turkish classical"
ln instr:ney instr:flute sys:part_of
ln instr:ney music:region:middle_eastern sys:part_of
set.add name="ontology.instruments" id="instr:ney"

def "instr:saz" "Saz (baglama): long-necked Turkish lute; 7 strings in 3 courses; folk and classical Anatolian music"
ln instr:saz instr:lute sys:part_of
ln instr:saz music:region:middle_eastern sys:part_of
set.add name="ontology.instruments" id="instr:saz"

def "instr:santur" "Santur: hammered dulcimer; 72–100 strings over movable bridges; Persian and Iraqi classical music"
ln instr:santur instr:zither sys:part_of
ln instr:santur music:region:middle_eastern sys:part_of
set.add name="ontology.instruments" id="instr:santur"

def "instr:duduk" "Duduk: double-reed cylindrical pipe of apricot wood; Armenian; warm, mournful tone; UNESCO ICH 2005"
ln instr:duduk instr:reed_aerophone sys:part_of
ln instr:duduk music:region:middle_eastern sys:part_of
set.add name="ontology.instruments" id="instr:duduk"

def "instr:tar" "Tar: long-necked plucked lute; 6 strings; waisted double-bowl body; Persian and Azerbaijani classical"
ln instr:tar instr:lute sys:part_of
ln instr:tar music:region:middle_eastern sys:part_of
set.add name="ontology.instruments" id="instr:tar"

def "instr:darbuka" "Darbuka: single-headed goblet drum; clay or metal shell; widespread in Arab and Turkish music"
ln instr:darbuka instr:membranophone sys:part_of
ln instr:darbuka music:region:middle_eastern sys:part_of
set.add name="ontology.instruments" id="instr:darbuka"

def "instr:riq" "Riq: small tambourine with 5 pairs of brass cymbals (zills); Arab classical and folk music"
ln instr:riq instr:frame_drum sys:part_of
ln instr:riq music:region:middle_eastern sys:part_of
set.add name="ontology.instruments" id="instr:riq"

# ── African instruments ─────────────────────────────────────────────────────────

def "instr:kora" "Kora: 21-string bridge harp-lute; West Africa; primary instrument of griot (djeli) musicians"
ln instr:kora instr:harp sys:part_of
ln instr:kora music:region:african sys:part_of
set.add name="ontology.instruments" id="instr:kora"

def "instr:balafon" "Balafon: wooden-keyed xylophone with gourd resonators; West Africa; griot ensemble instrument"
ln instr:balafon instr:idiophone sys:part_of
ln instr:balafon music:region:african sys:part_of
set.add name="ontology.instruments" id="instr:balafon"

def "instr:mbira" "Mbira (thumb piano): lamellaphone; metal tines plucked with thumbs; Zimbabwe Shona spirit ceremonies"
ln instr:mbira instr:idiophone sys:part_of
ln instr:mbira music:region:african sys:part_of
set.add name="ontology.instruments" id="instr:mbira"

def "instr:djembe" "Djembe: goblet-shaped rope-tuned hand drum; West Africa; bass, tone, and slap timbres"
ln instr:djembe instr:membranophone sys:part_of
ln instr:djembe music:region:african sys:part_of
set.add name="ontology.instruments" id="instr:djembe"

def "instr:talking_drum" "Talking drum (dundun): hourglass tension drum; Yoruba; pressure changes pitch to encode tonal language"
ln instr:talking_drum instr:membranophone sys:part_of
ln instr:talking_drum music:region:african sys:part_of
set.add name="ontology.instruments" id="instr:talking_drum"

# ── Southeast Asian instruments ─────────────────────────────────────────────────

def "instr:gamelan_gong" "Gong ageng: large hanging bronze gong; Javanese gamelan; marks the end of formal phrase cycles"
ln instr:gamelan_gong instr:gong sys:part_of
ln instr:gamelan_gong music:region:southeast_asian sys:part_of
set.add name="ontology.instruments" id="instr:gamelan_gong"

def "instr:gamelan_gender" "Gender: bronze metallophone with individual tube resonators beneath each key; Javanese and Balinese gamelan"
ln instr:gamelan_gender instr:idiophone sys:part_of
ln instr:gamelan_gender music:region:southeast_asian sys:part_of
set.add name="ontology.instruments" id="instr:gamelan_gender"

def "instr:gamelan_kendang" "Kendang: double-headed barrel drum; regulates tempo and cues transitions in Javanese and Balinese gamelan"
ln instr:gamelan_kendang instr:barrel_drum sys:part_of
ln instr:gamelan_kendang music:region:southeast_asian sys:part_of
set.add name="ontology.instruments" id="instr:gamelan_kendang"

def "instr:suling" "Suling: Sundanese and Balinese end-blown bamboo flute; 4 holes; soft melodic voice in gamelan"
ln instr:suling instr:flute sys:part_of
ln instr:suling music:region:southeast_asian sys:part_of
set.add name="ontology.instruments" id="instr:suling"

def "instr:rebab" "Rebab: 2-string spike fiddle; bowed; used in Javanese gamelan and Arab classical music; shared ancestor"
ln instr:rebab instr:chordophone sys:part_of
ln instr:rebab music:region:southeast_asian sys:part_of
set.add name="ontology.instruments" id="instr:rebab"

# ── European early and folk instruments ────────────────────────────────────────

def "instr:lute_european" "European lute: 6+ course plucked lute; rounded back; central to Renaissance and Baroque music"
ln instr:lute_european instr:lute sys:part_of
ln instr:lute_european music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:lute_european"

def "instr:vihuela" "Vihuela: Spanish guitar-shaped lute; 6 double courses; Renaissance polyphony and song accompaniment"
ln instr:vihuela instr:lute sys:part_of
ln instr:vihuela music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:vihuela"

def "instr:theorbo" "Theorbo: extended-neck lute with additional bass strings and re-entrant tuning; Baroque basso continuo"
ln instr:theorbo instr:lute sys:part_of
ln instr:theorbo music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:theorbo"

def "instr:hurdy_gurdy" "Hurdy-gurdy: wheel-bowed lute; hand-cranked rosined wheel bows strings; drone strings sustain tonic"
ln instr:hurdy_gurdy instr:chordophone sys:part_of
ln instr:hurdy_gurdy music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:hurdy_gurdy"

def "instr:rebec" "Rebec: pear-shaped bowed fiddle; 3 strings; medieval Europe; derived from Arab rabab via Iberia"
ln instr:rebec instr:chordophone sys:part_of
ln instr:rebec music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:rebec"

def "instr:crumhorn" "Crumhorn: double-reed capped wind instrument; curved body; buzzing tone; Renaissance consort music"
ln instr:crumhorn instr:reed_aerophone sys:part_of
ln instr:crumhorn music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:crumhorn"

def "instr:recorder" "Recorder (flute a bec): end-blown fipple flute; Renaissance and Baroque consort and solo repertoire"
ln instr:recorder instr:flute sys:part_of
ln instr:recorder music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:recorder"

def "instr:harpsichord" "Harpsichord: keyboard instrument; strings plucked by quills; Baroque solo, chamber, and continuo use"
ln instr:harpsichord instr:chordophone sys:part_of
ln instr:harpsichord music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:harpsichord"

def "instr:clavichord" "Clavichord: keyboard instrument; strings struck by tangents; very soft dynamic; favoured for private practice"
ln instr:clavichord instr:chordophone sys:part_of
ln instr:clavichord music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:clavichord"

def "instr:uilleann_pipes" "Uilleann pipes: Irish bellows-blown bagpipe; sweetest-toned of all bagpipes; regulators allow chords"
ln instr:uilleann_pipes instr:aerophone sys:part_of
ln instr:uilleann_pipes music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:uilleann_pipes"

def "instr:bodhran" "Bodhran: Irish shallow frame drum; goatskin or synthetic head; beaten with tipper (cipin)"
ln instr:bodhran instr:frame_drum sys:part_of
ln instr:bodhran music:region:european_folk sys:part_of
set.add name="ontology.instruments" id="instr:bodhran"
