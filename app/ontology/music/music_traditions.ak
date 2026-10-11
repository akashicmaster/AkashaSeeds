# music_traditions.ak
# Classical and ethnic music traditions — worldwide pre-modern and living folk traditions
# Sources: UNESCO ICH, Grove Music Online, various — Public domain terminology
#

# ── Namespace root ──────────────────────────────────────────────────────────────

def "music:tradition" "Root namespace anchor for music tradition concepts"

# ── Cultural region anchors ──────────────────────────────────────────────────────

def "music:region:western" "Western art music cultural region"
def "music:region:south_asian" "South Asian classical and folk music region"
def "music:region:middle_eastern" "Middle Eastern and Persian music region"
def "music:region:east_asian" "East Asian music region"
def "music:region:southeast_asian" "Southeast Asian music region"
def "music:region:african" "African music traditions region"
def "music:region:european_folk" "European folk music traditions region"
def "music:region:pacific" "Pacific and Oceanic music traditions region"

# ── Western art music periods ────────────────────────────────────────────────────

def "music:tradition:gregorian_chant" "Plainchant of the Western church; monophonic; 9th–16th century; named after Pope Gregory I"
ln music:tradition:gregorian_chant music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:gregorian_chant"

def "music:tradition:ars_antiqua" "Notre-Dame school polyphony; organum and clausula; c. 1170–1310; Léonin and Pérotin"
ln music:tradition:ars_antiqua music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:ars_antiqua"

def "music:tradition:ars_nova" "14th-century French and Italian polyphony; isorhythm; Machaut and Landini"
ln music:tradition:ars_nova music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:ars_nova"

def "music:tradition:renaissance_polyphony" "1400–1600; Palestrina, Josquin des Prez, Lassus; modal counterpoint; imitative texture"
ln music:tradition:renaissance_polyphony music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:renaissance_polyphony"

def "music:tradition:baroque_music" "1600–1750; Bach, Handel, Vivaldi, Monteverdi; basso continuo; terraced dynamics"
ln music:tradition:baroque_music music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:baroque_music"

def "music:tradition:classical_period_music" "1750–1820; Haydn, Mozart, early Beethoven; sonata form, symphony, string quartet"
ln music:tradition:classical_period_music music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:classical_period_music"

def "music:tradition:romantic_music" "1820–1900; Beethoven, Schubert, Wagner, Brahms; expanded orchestration, chromaticism, nationalism"
ln music:tradition:romantic_music music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:romantic_music"

def "music:tradition:impressionist_music" "1890–1930; Debussy, Ravel; non-functional harmony, whole-tone scales, timbre as structure"
ln music:tradition:impressionist_music music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:impressionist_music"

def "music:tradition:early_music" "General term for Western pre-1750 repertoire performed with historically informed practice"
ln music:tradition:early_music music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:early_music"

def "music:tradition:byzantine_chant" "Eastern Orthodox liturgical chant; oktoechos eight-mode system; neumatic notation"
ln music:tradition:byzantine_chant music:region:western sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:byzantine_chant"

# ── South Asian classical traditions ───────────────────────────────────────────

def "music:tradition:hindustani" "North Indian classical music; raga and tala system; gharana lineage transmission; improvisation-centred"
ln music:tradition:hindustani music:region:south_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:hindustani"

def "music:tradition:carnatic" "South Indian classical music; 72 melakarta raga system; kriti as primary form; composed repertoire"
ln music:tradition:carnatic music:region:south_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:carnatic"

def "music:tradition:dhrupad" "Oldest surviving Hindustani vocal form; four vani schools; dhammar tala; alap-jod-jhala structure"
ln music:tradition:dhrupad music:region:south_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:dhrupad"

def "music:tradition:qawwali" "Sufi devotional music of the Chishti order; ecstatic performance; Pakistan and North India"
ln music:tradition:qawwali music:region:south_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:qawwali"

# ── Middle Eastern and Persian traditions ───────────────────────────────────────

def "music:tradition:maqam_system" "Arab modal framework; 24+ maqamat; melodic mode defined by scale, pivotal tone, and movement"
ln music:tradition:maqam_system music:region:middle_eastern sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:maqam_system"

def "music:tradition:turkish_makam" "Ottoman and Turkish classical music; 600+ makam; hicaz, rast, segah among primary modes"
ln music:tradition:turkish_makam music:region:middle_eastern sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:turkish_makam"

def "music:tradition:persian_dastgah" "Iranian classical music; 7 dastgah plus 5 avaz secondary modes; radif canon as foundational repertoire"
ln music:tradition:persian_dastgah music:region:middle_eastern sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:persian_dastgah"

def "music:tradition:andalusian_music" "Moorish-Iberian musical synthesis; nuba suite form; preserved in Maghreb courts after 1492"
ln music:tradition:andalusian_music music:region:middle_eastern sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:andalusian_music"

def "music:tradition:armenian_duduk_music" "Armenian reed-pipe tradition centred on the duduk; expressive ornamentation; UNESCO ICH 2005"
ln music:tradition:armenian_duduk_music music:region:middle_eastern sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:armenian_duduk_music"

def "music:tradition:mugham" "Azerbaijani modal improvisation tradition; related to Persian dastgah; UNESCO ICH 2008"
ln music:tradition:mugham music:region:middle_eastern sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:mugham"

# ── East Asian traditions ───────────────────────────────────────────────────────

def "music:tradition:gagaku" "Japanese imperial court music; 5th-century origin; biwa, sho, hichiriki ensemble; oldest living orchestral tradition"
ln music:tradition:gagaku music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:gagaku"

def "music:tradition:nohgaku_music" "Music for Noh theatre; fue flute, ko-tsuzumi, o-tsuzumi, taiko; UNESCO ICH 2008"
ln music:tradition:nohgaku_music music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:nohgaku_music"

def "music:tradition:nagauta" "Long-song genre for Kabuki theatre; shamisen-led ensemble with hayashi percussion"
ln music:tradition:nagauta music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:nagauta"

def "music:tradition:jiuta" "Japanese chamber vocal music; koto or shamisen with voice; refined lyric aesthetic"
ln music:tradition:jiuta music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:jiuta"

def "music:tradition:sankyoku" "Japanese trio chamber tradition; koto, shamisen, and shakuhachi; Edo period salon music"
ln music:tradition:sankyoku music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:sankyoku"

def "music:tradition:shomyo" "Japanese Buddhist chant; Tendai and Shingon school variants; melodic liturgical recitation"
ln music:tradition:shomyo music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:shomyo"

def "music:tradition:guqin_music" "Chinese qin zither art-music tradition; literati aesthetic; UNESCO ICH 2003"
ln music:tradition:guqin_music music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:guqin_music"

def "music:tradition:kunqu_opera" "Oldest surviving Chinese opera form; 600-year history; refined singing and gesture; UNESCO ICH 2001"
ln music:tradition:kunqu_opera music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:kunqu_opera"

def "music:tradition:jingju" "Peking opera; 200-year tradition; four role types; acrobatics and stylised combat; UNESCO ICH 2010"
ln music:tradition:jingju music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:jingju"

def "music:tradition:jeong_ak" "Korean court and aristocratic music; encompasses aak (Confucian ritual), dangak, and hyangak styles"
ln music:tradition:jeong_ak music:region:east_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:jeong_ak"

# ── Southeast Asian traditions ──────────────────────────────────────────────────

def "music:tradition:gamelan_javanese" "Javanese gamelan orchestra; pélog and sléndro tuning systems; court and village contexts"
ln music:tradition:gamelan_javanese music:region:southeast_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:gamelan_javanese"

def "music:tradition:gamelan_balinese" "Balinese gamelan; kebyar modern style; faster tempos, more dynamic contrasts than Javanese"
ln music:tradition:gamelan_balinese music:region:southeast_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:gamelan_balinese"

def "music:tradition:pinpeat" "Cambodian court music ensemble; wedding, temple, and ceremonial contexts"
ln music:tradition:pinpeat music:region:southeast_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:pinpeat"

def "music:tradition:mahori" "Thai chamber music; string-led court ensemble; combined with piphat wind-percussion"
ln music:tradition:mahori music:region:southeast_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:mahori"

def "music:tradition:ca_tru" "Vietnamese ceremonial and chamber singing; dan tranh zither accompaniment; UNESCO ICH 2009"
ln music:tradition:ca_tru music:region:southeast_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:ca_tru"

def "music:tradition:mo_lam" "Lao-Isan folk singing tradition; khaen free-reed mouth organ; call-and-response vocal style"
ln music:tradition:mo_lam music:region:southeast_asian sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:mo_lam"

# ── African traditions ──────────────────────────────────────────────────────────

def "music:tradition:griot_tradition" "West African oral historian-musician lineage; kora, balafon, ngoni; djeli in Mande culture"
ln music:tradition:griot_tradition music:region:african sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:griot_tradition"

def "music:tradition:mbira_music" "Zimbabwean Shona mbira lamellophone tradition; spirit communication (bira ceremony); UNESCO ICH 2020"
ln music:tradition:mbira_music music:region:african sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:mbira_music"

def "music:tradition:isicathamiya" "Zulu male a cappella tradition; South Africa; soft-shoe movement style; UNESCO ICH 2008"
ln music:tradition:isicathamiya music:region:african sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:isicathamiya"

# ── European folk traditions ────────────────────────────────────────────────────

def "music:tradition:flamenco_music" "Andalusian tradition of cante (song), toque (guitar), and baile (dance); cante jondo deep song; UNESCO ICH 2010"
ln music:tradition:flamenco_music music:region:european_folk sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:flamenco_music"

def "music:tradition:irish_traditional" "Irish trad music; reel, jig, hornpipe, and slow air; fiddle, uilleann pipes, flute, and bodhrán"
ln music:tradition:irish_traditional music:region:european_folk sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:irish_traditional"

def "music:tradition:scottish_piping" "Highland bagpipe tradition; piobaireachd (ceol mór) classical form; competitive piping culture"
ln music:tradition:scottish_piping music:region:european_folk sys:part_of
set.add name="ontology.music_traditions" id="music:tradition:scottish_piping"
