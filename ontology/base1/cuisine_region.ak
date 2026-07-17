# Akasha ontology — culinary macro-regions (地域クラスタ).
# Group cuisines into regions so shared regional character is visible; some
# cuisines span two regions (turkish, moroccan, french). Base pack.

def "region" "Culinary macro-region."
def "region:east_asia" "東アジア — east asia culinary region."
ln region:east_asia region thesaurus:related
ln cuisine:chinese region:east_asia culinary:region
ln cuisine:japanese region:east_asia culinary:region
ln cuisine:korean region:east_asia culinary:region
ln cuisine:cantonese region:east_asia culinary:region
ln cuisine:sichuan region:east_asia culinary:region
ln cuisine:taiwanese region:east_asia culinary:region
ln cuisine:mongolian region:east_asia culinary:region
ln cuisine:tibetan region:east_asia culinary:region
ln cuisine:okinawan region:east_asia culinary:region
ln cuisine:shandong region:east_asia culinary:region
ln cuisine:huaiyang region:east_asia culinary:region
def "region:southeast_asia" "東南アジア — southeast asia culinary region."
ln region:southeast_asia region thesaurus:related
ln cuisine:thai region:southeast_asia culinary:region
ln cuisine:vietnamese region:southeast_asia culinary:region
ln cuisine:indonesian region:southeast_asia culinary:region
ln cuisine:filipino region:southeast_asia culinary:region
ln cuisine:malaysian region:southeast_asia culinary:region
ln cuisine:cambodian region:southeast_asia culinary:region
ln cuisine:burmese region:southeast_asia culinary:region
ln cuisine:singaporean region:southeast_asia culinary:region
ln cuisine:nyonya region:southeast_asia culinary:region
ln cuisine:laotian region:southeast_asia culinary:region
def "region:south_asia" "南アジア — south asia culinary region."
ln region:south_asia region thesaurus:related
ln cuisine:indian region:south_asia culinary:region
ln cuisine:pakistani region:south_asia culinary:region
ln cuisine:bangladeshi region:south_asia culinary:region
ln cuisine:sri_lankan region:south_asia culinary:region
ln cuisine:mughlai region:south_asia culinary:region
ln cuisine:bengali region:south_asia culinary:region
ln cuisine:punjabi region:south_asia culinary:region
ln cuisine:tamil region:south_asia culinary:region
ln cuisine:gujarati region:south_asia culinary:region
def "region:middle_east" "中東 — middle east culinary region."
ln region:middle_east region thesaurus:related
ln cuisine:turkish region:middle_east culinary:region
ln cuisine:lebanese region:middle_east culinary:region
ln cuisine:persian region:middle_east culinary:region
ln cuisine:iranian region:middle_east culinary:region
ln cuisine:syrian region:middle_east culinary:region
ln cuisine:iraqi region:middle_east culinary:region
ln cuisine:israeli region:middle_east culinary:region
ln cuisine:levantine region:middle_east culinary:region
ln cuisine:yemeni region:middle_east culinary:region
ln cuisine:kurdish region:middle_east culinary:region
ln cuisine:azerbaijani region:middle_east culinary:region
def "region:mediterranean" "地中海 — mediterranean culinary region."
ln region:mediterranean region thesaurus:related
ln cuisine:italian region:mediterranean culinary:region
ln cuisine:greek region:mediterranean culinary:region
ln cuisine:spanish region:mediterranean culinary:region
ln cuisine:french region:mediterranean culinary:region
ln cuisine:turkish region:mediterranean culinary:region
ln cuisine:moroccan region:mediterranean culinary:region
ln cuisine:sicilian region:mediterranean culinary:region
ln cuisine:neapolitan region:mediterranean culinary:region
ln cuisine:catalan region:mediterranean culinary:region
ln cuisine:tuscan region:mediterranean culinary:region
ln cuisine:provencal region:mediterranean culinary:region
ln cuisine:sardinian region:mediterranean culinary:region
ln cuisine:iberian region:mediterranean culinary:region
def "region:mesoamerica" "メソアメリカ — mesoamerica culinary region."
ln region:mesoamerica region thesaurus:related
ln cuisine:mexican region:mesoamerica culinary:region
ln cuisine:oaxacan region:mesoamerica culinary:region
ln cuisine:yucatecan region:mesoamerica culinary:region
ln cuisine:guatemalan region:mesoamerica culinary:region
def "region:south_america" "南米/アンデス — south america culinary region."
ln region:south_america region thesaurus:related
ln cuisine:peruvian region:south_america culinary:region
ln cuisine:chilean region:south_america culinary:region
ln cuisine:bolivian region:south_america culinary:region
ln cuisine:argentine region:south_america culinary:region
ln cuisine:brazilian region:south_america culinary:region
ln cuisine:colombian region:south_america culinary:region
ln cuisine:venezuelan region:south_america culinary:region
ln cuisine:nikkei region:south_america culinary:region
ln cuisine:chifa region:south_america culinary:region
def "region:north_africa" "北アフリカ — north africa culinary region."
ln region:north_africa region thesaurus:related
ln cuisine:moroccan region:north_africa culinary:region
ln cuisine:tunisian region:north_africa culinary:region
ln cuisine:algerian region:north_africa culinary:region
ln cuisine:egyptian region:north_africa culinary:region
ln cuisine:libyan region:north_africa culinary:region
ln cuisine:maghrebi region:north_africa culinary:region
def "region:west_africa" "西アフリカ — west africa culinary region."
ln region:west_africa region thesaurus:related
ln cuisine:nigerian region:west_africa culinary:region
ln cuisine:senegalese region:west_africa culinary:region
ln cuisine:ghanaian region:west_africa culinary:region
ln cuisine:ivorian region:west_africa culinary:region
ln cuisine:yoruba region:west_africa culinary:region
def "region:east_africa" "東アフリカ — east africa culinary region."
ln region:east_africa region thesaurus:related
ln cuisine:ethiopian region:east_africa culinary:region
ln cuisine:eritrean region:east_africa culinary:region
ln cuisine:kenyan region:east_africa culinary:region
ln cuisine:somali region:east_africa culinary:region
def "region:europe_north" "北・中欧 — europe north culinary region."
ln region:europe_north region thesaurus:related
ln cuisine:french region:europe_north culinary:region
ln cuisine:german region:europe_north culinary:region
ln cuisine:british region:europe_north culinary:region
ln cuisine:polish region:europe_north culinary:region
ln cuisine:russian region:europe_north culinary:region
ln cuisine:dutch region:europe_north culinary:region
ln cuisine:austrian region:europe_north culinary:region
ln cuisine:hungarian region:europe_north culinary:region
ln cuisine:nordic region:europe_north culinary:region
ln cuisine:czech region:europe_north culinary:region
def "region:caribbean" "カリブ — caribbean culinary region."
ln region:caribbean region thesaurus:related
ln cuisine:jamaican region:caribbean culinary:region
ln cuisine:cuban region:caribbean culinary:region
ln cuisine:haitian region:caribbean culinary:region
ln cuisine:trinidadian region:caribbean culinary:region
def "region:pacific" "太平洋 — pacific culinary region."
ln region:pacific region thesaurus:related
ln cuisine:hawaiian region:pacific culinary:region
ln cuisine:fijian region:pacific culinary:region
