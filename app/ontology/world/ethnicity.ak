# Akasha ontology (world pack) — ethnicity, made first-class.
# Turns the ethnic threads noted in hist_polities into atoms & relations:
# a people descends_from a historical polity, has a homeland (geo:country),
# speaks a language (lang:), and belongs to an ethnolinguistic family. A-tier.

def "ethnicity:people" "An ethnic group — a people sharing descent, language and culture (民族)."
def "ethnicity:family" "An ethnolinguistic family grouping related peoples/languages."
def "ethnicity:family:indo_european" "The vast family from europe to india (romance, germanic, slavic, indo-iranian, hellenic)."
ln ethnicity:family:indo_european ethnicity:family thesaurus:related
def "ethnicity:family:semitic" "Arabic, hebrew, aramaic, amharic peoples."
ln ethnicity:family:semitic ethnicity:family thesaurus:related
def "ethnicity:family:afroasiatic" "Semitic plus egyptian, berber and cushitic."
ln ethnicity:family:afroasiatic ethnicity:family thesaurus:related
def "ethnicity:family:sino_tibetan" "Han chinese, tibetan and burmese peoples."
ln ethnicity:family:sino_tibetan ethnicity:family thesaurus:related
def "ethnicity:family:turkic" "Turks, azeris, kazakhs, uzbeks."
ln ethnicity:family:turkic ethnicity:family thesaurus:related
def "ethnicity:family:niger_congo" "The bantu and west african peoples."
ln ethnicity:family:niger_congo ethnicity:family thesaurus:related
def "ethnicity:family:dravidian" "Tamil, telugu and south indian peoples."
ln ethnicity:family:dravidian ethnicity:family thesaurus:related
def "ethnicity:family:austronesian" "Malay, polynesian and filipino peoples."
ln ethnicity:family:austronesian ethnicity:family thesaurus:related
def "ethnicity:family:uralic" "Finns, hungarians and estonians."
ln ethnicity:family:uralic ethnicity:family thesaurus:related
def "ethnicity:family:japonic" "The japanese people."
ln ethnicity:family:japonic ethnicity:family thesaurus:related
def "ethnicity:family:koreanic" "The korean people."
ln ethnicity:family:koreanic ethnicity:family thesaurus:related
def "ethnicity:family:uto_aztecan" "Nahua and related mesoamerican peoples."
ln ethnicity:family:uto_aztecan ethnicity:family thesaurus:related
def "ethnicity:family:quechuan" "The andean quechua peoples."
ln ethnicity:family:quechuan ethnicity:family thesaurus:related

# ── peoples → homeland / descent / language / family ──
def "ethnicity:egyptians" "The people of the Nile."
ln ethnicity:egyptians ethnicity:people thesaurus:related
ln ethnicity:egyptians geo:country:EGY ethnicity:homeland
ln ethnicity:egyptians ethnicity:family:afroasiatic ethnicity:belongs_to
ln ethnicity:egyptians hist:ancient_egypt ethnicity:descends_from
ln ethnicity:egyptians lang:ar ethnicity:speaks
def "ethnicity:assyrians" "Aramaic-speaking Christians of Mesopotamia."
ln ethnicity:assyrians ethnicity:people thesaurus:related
ln ethnicity:assyrians geo:country:IRQ ethnicity:homeland
ln ethnicity:assyrians ethnicity:family:semitic ethnicity:belongs_to
ln ethnicity:assyrians hist:assyria ethnicity:descends_from
def "ethnicity:arabs" "The Arabic-speaking peoples of the Middle East and North Africa."
ln ethnicity:arabs ethnicity:people thesaurus:related
ln ethnicity:arabs geo:country:SAU ethnicity:homeland
ln ethnicity:arabs ethnicity:family:semitic ethnicity:belongs_to
ln ethnicity:arabs lang:ar ethnicity:speaks
def "ethnicity:persians" "The Iranian people, heirs to ancient Persia."
ln ethnicity:persians ethnicity:people thesaurus:related
ln ethnicity:persians geo:country:IRN ethnicity:homeland
ln ethnicity:persians ethnicity:family:indo_european ethnicity:belongs_to
ln ethnicity:persians hist:achaemenid_persia ethnicity:descends_from
ln ethnicity:persians lang:fa ethnicity:speaks
def "ethnicity:greeks" "The Hellenic people, continuous since antiquity."
ln ethnicity:greeks ethnicity:people thesaurus:related
ln ethnicity:greeks geo:country:GRC ethnicity:homeland
ln ethnicity:greeks ethnicity:family:indo_european ethnicity:belongs_to
ln ethnicity:greeks hist:ancient_greece ethnicity:descends_from
ln ethnicity:greeks lang:el ethnicity:speaks
def "ethnicity:italians" "The people of Italy, at the heart of Rome's legacy."
ln ethnicity:italians ethnicity:people thesaurus:related
ln ethnicity:italians geo:country:ITA ethnicity:homeland
ln ethnicity:italians ethnicity:family:indo_european ethnicity:belongs_to
ln ethnicity:italians hist:roman_empire ethnicity:descends_from
ln ethnicity:italians lang:it ethnicity:speaks
def "ethnicity:turks" "The Turkic people of Anatolia, heirs to the Ottomans."
ln ethnicity:turks ethnicity:people thesaurus:related
ln ethnicity:turks geo:country:TUR ethnicity:homeland
ln ethnicity:turks ethnicity:family:turkic ethnicity:belongs_to
ln ethnicity:turks hist:ottoman_empire ethnicity:descends_from
def "ethnicity:lebanese" "The Levantine people who trace descent to Phoenicia."
ln ethnicity:lebanese ethnicity:people thesaurus:related
ln ethnicity:lebanese geo:country:LBN ethnicity:homeland
ln ethnicity:lebanese ethnicity:family:semitic ethnicity:belongs_to
ln ethnicity:lebanese hist:phoenicia ethnicity:descends_from
ln ethnicity:lebanese lang:ar ethnicity:speaks
def "ethnicity:han_chinese" "The world's largest ethnic group, named for the Han empire."
ln ethnicity:han_chinese ethnicity:people thesaurus:related
ln ethnicity:han_chinese geo:country:CHN ethnicity:homeland
ln ethnicity:han_chinese ethnicity:family:sino_tibetan ethnicity:belongs_to
ln ethnicity:han_chinese hist:han_china ethnicity:descends_from
ln ethnicity:han_chinese lang:zh ethnicity:speaks
def "ethnicity:mongols" "The steppe people of Genghis Khan."
ln ethnicity:mongols ethnicity:people thesaurus:related
ln ethnicity:mongols geo:country:MNG ethnicity:homeland
ln ethnicity:mongols ethnicity:family:turkic ethnicity:belongs_to
ln ethnicity:mongols hist:mongol_empire ethnicity:descends_from
def "ethnicity:japanese_people" "The people of the Japanese archipelago."
ln ethnicity:japanese_people ethnicity:people thesaurus:related
ln ethnicity:japanese_people geo:country:JPN ethnicity:homeland
ln ethnicity:japanese_people ethnicity:family:japonic ethnicity:belongs_to
ln ethnicity:japanese_people lang:ja ethnicity:speaks
def "ethnicity:koreans" "The people of the Korean peninsula."
ln ethnicity:koreans ethnicity:people thesaurus:related
ln ethnicity:koreans geo:country:KOR ethnicity:homeland
ln ethnicity:koreans ethnicity:family:koreanic ethnicity:belongs_to
ln ethnicity:koreans lang:ko ethnicity:speaks
def "ethnicity:indo_aryans" "The northern Indian peoples of Indo-European speech."
ln ethnicity:indo_aryans ethnicity:people thesaurus:related
ln ethnicity:indo_aryans geo:country:IND ethnicity:homeland
ln ethnicity:indo_aryans ethnicity:family:indo_european ethnicity:belongs_to
ln ethnicity:indo_aryans lang:hi ethnicity:speaks
def "ethnicity:tamils" "A major Dravidian people of South India and Sri Lanka."
ln ethnicity:tamils ethnicity:people thesaurus:related
ln ethnicity:tamils geo:country:IND ethnicity:homeland
ln ethnicity:tamils ethnicity:family:dravidian ethnicity:belongs_to
def "ethnicity:maya_people" "The Maya, still speaking Mayan languages in Mesoamerica."
ln ethnicity:maya_people ethnicity:people thesaurus:related
ln ethnicity:maya_people geo:country:GTM ethnicity:homeland
ln ethnicity:maya_people ethnicity:family:uto_aztecan ethnicity:belongs_to
ln ethnicity:maya_people hist:maya_civilization ethnicity:descends_from
def "ethnicity:nahua" "The Nahuatl-speaking heirs of the Aztecs."
ln ethnicity:nahua ethnicity:people thesaurus:related
ln ethnicity:nahua geo:country:MEX ethnicity:homeland
ln ethnicity:nahua ethnicity:family:uto_aztecan ethnicity:belongs_to
ln ethnicity:nahua hist:aztec_empire ethnicity:descends_from
def "ethnicity:quechua" "The Andean people, heirs to the Inca."
ln ethnicity:quechua ethnicity:people thesaurus:related
ln ethnicity:quechua geo:country:PER ethnicity:homeland
ln ethnicity:quechua ethnicity:family:quechuan ethnicity:belongs_to
ln ethnicity:quechua hist:inca_empire ethnicity:descends_from
def "ethnicity:french" "The people of France, on Gaulish and Frankish roots."
ln ethnicity:french ethnicity:people thesaurus:related
ln ethnicity:french geo:country:FRA ethnicity:homeland
ln ethnicity:french ethnicity:family:indo_european ethnicity:belongs_to
ln ethnicity:french hist:gaul ethnicity:descends_from
ln ethnicity:french lang:fr ethnicity:speaks
def "ethnicity:amhara" "A major Ethiopian people, heirs to Aksum."
ln ethnicity:amhara ethnicity:people thesaurus:related
ln ethnicity:amhara geo:country:ETH ethnicity:homeland
ln ethnicity:amhara ethnicity:family:afroasiatic ethnicity:belongs_to
ln ethnicity:amhara hist:aksum ethnicity:descends_from
ln ethnicity:amhara lang:am ethnicity:speaks
def "ethnicity:bantu" "The great family of Sub-Saharan African peoples."
ln ethnicity:bantu ethnicity:people thesaurus:related
ln ethnicity:bantu geo:country:COD ethnicity:homeland
ln ethnicity:bantu ethnicity:family:niger_congo ethnicity:belongs_to
def "ethnicity:russians" "The largest Slavic people."
ln ethnicity:russians ethnicity:people thesaurus:related
ln ethnicity:russians geo:country:RUS ethnicity:homeland
ln ethnicity:russians ethnicity:family:indo_european ethnicity:belongs_to
