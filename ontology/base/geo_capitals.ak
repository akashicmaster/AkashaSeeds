# Akasha ontology — namespace: geo:capital
# Capital cities for the 43 countries in the base package.
# Each capital is linked bidirectionally to its country:
#   geo:capital:X -[sys:capital_of]-> geo:country:ISO3
#   geo:country:ISO3 -[sys:has_capital]-> geo:capital:X
# atoms: 43

def "geo:capital:abu_dhabi" "Abu Dhabi — capital of the United Arab Emirates."
ln geo:capital:abu_dhabi geo:country:ARE sys:capital_of
ln geo:country:ARE geo:capital:abu_dhabi sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:abu_dhabi"

def "geo:capital:addis_ababa" "Addis Ababa — capital of Ethiopia; seat of the African Union."
ln geo:capital:addis_ababa geo:country:ETH sys:capital_of
ln geo:country:ETH geo:capital:addis_ababa sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:addis_ababa"

def "geo:capital:amsterdam" "Amsterdam — constitutional capital of the Netherlands (seat of government: The Hague)."
ln geo:capital:amsterdam geo:country:NLD sys:capital_of
ln geo:country:NLD geo:capital:amsterdam sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:amsterdam"

def "geo:capital:ankara" "Ankara — capital of Turkey."
ln geo:capital:ankara geo:country:TUR sys:capital_of
ln geo:country:TUR geo:capital:ankara sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:ankara"

def "geo:capital:bern" "Bern — federal city and de facto capital of Switzerland."
ln geo:capital:bern geo:country:CHE sys:capital_of
ln geo:country:CHE geo:capital:bern sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:bern"

def "geo:capital:beijing" "Beijing — capital of China; one of the world's most populous cities."
ln geo:capital:beijing geo:country:CHN sys:capital_of
ln geo:country:CHN geo:capital:beijing sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:beijing"

def "geo:capital:berlin" "Berlin — capital and largest city of Germany."
ln geo:capital:berlin geo:country:DEU sys:capital_of
ln geo:country:DEU geo:capital:berlin sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:berlin"

def "geo:capital:bogota" "Bogotá — capital of Colombia; highest-altitude major capital in South America."
ln geo:capital:bogota geo:country:COL sys:capital_of
ln geo:country:COL geo:capital:bogota sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:bogota"

def "geo:capital:brasilia" "Brasília — capital of Brazil; purpose-built city inaugurated in 1960."
ln geo:capital:brasilia geo:country:BRA sys:capital_of
ln geo:country:BRA geo:capital:brasilia sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:brasilia"

def "geo:capital:buenos_aires" "Buenos Aires — capital and largest city of Argentina."
ln geo:capital:buenos_aires geo:country:ARG sys:capital_of
ln geo:country:ARG geo:capital:buenos_aires sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:buenos_aires"

def "geo:capital:cairo" "Cairo — capital of Egypt; largest city in Africa and the Arab world."
ln geo:capital:cairo geo:country:EGY sys:capital_of
ln geo:country:EGY geo:capital:cairo sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:cairo"

def "geo:capital:canberra" "Canberra — capital of Australia; chosen as a compromise between Sydney and Melbourne."
ln geo:capital:canberra geo:country:AUS sys:capital_of
ln geo:country:AUS geo:capital:canberra sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:canberra"

def "geo:capital:hanoi" "Hanoi — capital of Vietnam."
ln geo:capital:hanoi geo:country:VNM sys:capital_of
ln geo:country:VNM geo:capital:hanoi sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:hanoi"

def "geo:capital:islamabad" "Islamabad — capital of Pakistan; purpose-built city replacing Karachi in 1966."
ln geo:capital:islamabad geo:country:PAK sys:capital_of
ln geo:country:PAK geo:capital:islamabad sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:islamabad"

def "geo:capital:jakarta" "Jakarta — capital of Indonesia; one of the world's largest urban agglomerations."
ln geo:capital:jakarta geo:country:IDN sys:capital_of
ln geo:country:IDN geo:capital:jakarta sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:jakarta"

def "geo:capital:jerusalem" "Jerusalem — declared capital of Israel; status internationally contested."
ln geo:capital:jerusalem geo:country:ISR sys:capital_of
ln geo:country:ISR geo:capital:jerusalem sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:jerusalem"

def "geo:capital:kyiv" "Kyiv — capital and largest city of Ukraine."
ln geo:capital:kyiv geo:country:UKR sys:capital_of
ln geo:country:UKR geo:capital:kyiv sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:kyiv"

def "geo:capital:lima" "Lima — capital of Peru; largest city on the Pacific coast of South America."
ln geo:capital:lima geo:country:PER sys:capital_of
ln geo:country:PER geo:capital:lima sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:lima"

def "geo:capital:london" "London — capital of the United Kingdom and England."
ln geo:capital:london geo:country:GBR sys:capital_of
ln geo:country:GBR geo:capital:london sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:london"

def "geo:capital:madrid" "Madrid — capital and largest city of Spain."
ln geo:capital:madrid geo:country:ESP sys:capital_of
ln geo:country:ESP geo:capital:madrid sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:madrid"

def "geo:capital:manila" "Manila — capital of the Philippines."
ln geo:capital:manila geo:country:PHL sys:capital_of
ln geo:country:PHL geo:capital:manila sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:manila"

def "geo:capital:mexico_city" "Mexico City — capital of Mexico; one of the most populous cities in the world."
ln geo:capital:mexico_city geo:country:MEX sys:capital_of
ln geo:country:MEX geo:capital:mexico_city sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:mexico_city"

def "geo:capital:moscow" "Moscow — capital of Russia; largest city in Europe."
ln geo:capital:moscow geo:country:RUS sys:capital_of
ln geo:country:RUS geo:capital:moscow sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:moscow"

def "geo:capital:nairobi" "Nairobi — capital of Kenya; major economic hub of East Africa."
ln geo:capital:nairobi geo:country:KEN sys:capital_of
ln geo:country:KEN geo:capital:nairobi sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:nairobi"

def "geo:capital:new_delhi" "New Delhi — capital of India; seat of three branches of the Government of India."
ln geo:capital:new_delhi geo:country:IND sys:capital_of
ln geo:country:IND geo:capital:new_delhi sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:new_delhi"

def "geo:capital:oslo" "Oslo — capital and most populous city of Norway."
ln geo:capital:oslo geo:country:NOR sys:capital_of
ln geo:country:NOR geo:capital:oslo sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:oslo"

def "geo:capital:ottawa" "Ottawa — capital of Canada."
ln geo:capital:ottawa geo:country:CAN sys:capital_of
ln geo:country:CAN geo:capital:ottawa sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:ottawa"

def "geo:capital:paris" "Paris — capital of France; global centre of art, fashion, and culture."
ln geo:capital:paris geo:country:FRA sys:capital_of
ln geo:country:FRA geo:capital:paris sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:paris"

def "geo:capital:pretoria" "Pretoria — administrative capital of South Africa (legislative: Cape Town; judicial: Bloemfontein)."
ln geo:capital:pretoria geo:country:ZAF sys:capital_of
ln geo:country:ZAF geo:capital:pretoria sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:pretoria"

def "geo:capital:rabat" "Rabat — capital of Morocco."
ln geo:capital:rabat geo:country:MAR sys:capital_of
ln geo:country:MAR geo:capital:rabat sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:rabat"

def "geo:capital:riyadh" "Riyadh — capital and largest city of Saudi Arabia."
ln geo:capital:riyadh geo:country:SAU sys:capital_of
ln geo:country:SAU geo:capital:riyadh sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:riyadh"

def "geo:capital:rome" "Rome — capital of Italy; known as the Eternal City."
ln geo:capital:rome geo:country:ITA sys:capital_of
ln geo:country:ITA geo:capital:rome sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:rome"

def "geo:capital:santiago" "Santiago — capital and largest city of Chile."
ln geo:capital:santiago geo:country:CHL sys:capital_of
ln geo:country:CHL geo:capital:santiago sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:santiago"

def "geo:capital:seoul" "Seoul — capital of South Korea; one of the world's largest metropolitan areas."
ln geo:capital:seoul geo:country:KOR sys:capital_of
ln geo:country:KOR geo:capital:seoul sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:seoul"

def "geo:capital:singapore" "Singapore — capital of the city-state of Singapore."
ln geo:capital:singapore geo:country:SGP sys:capital_of
ln geo:country:SGP geo:capital:singapore sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:singapore"

def "geo:capital:stockholm" "Stockholm — capital of Sweden; built on fourteen islands."
ln geo:capital:stockholm geo:country:SWE sys:capital_of
ln geo:country:SWE geo:capital:stockholm sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:stockholm"

def "geo:capital:tehran" "Tehran — capital of Iran."
ln geo:capital:tehran geo:country:IRN sys:capital_of
ln geo:country:IRN geo:capital:tehran sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:tehran"

def "geo:capital:tokyo" "Tokyo — capital of Japan; world's most populous metropolitan area."
ln geo:capital:tokyo geo:country:JPN sys:capital_of
ln geo:country:JPN geo:capital:tokyo sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:tokyo"

def "geo:capital:warsaw" "Warsaw — capital of Poland."
ln geo:capital:warsaw geo:country:POL sys:capital_of
ln geo:country:POL geo:capital:warsaw sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:warsaw"

def "geo:capital:washington_dc" "Washington D.C. — capital of the United States of America."
ln geo:capital:washington_dc geo:country:USA sys:capital_of
ln geo:country:USA geo:capital:washington_dc sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:washington_dc"

def "geo:capital:wellington" "Wellington — capital of New Zealand."
ln geo:capital:wellington geo:country:NZL sys:capital_of
ln geo:country:NZL geo:capital:wellington sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:wellington"

def "geo:capital:abuja" "Abuja — capital of Nigeria; replaced Lagos as capital in 1991."
ln geo:capital:abuja geo:country:NGA sys:capital_of
ln geo:country:NGA geo:capital:abuja sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:abuja"

def "geo:capital:bangkok" "Bangkok — capital and primate city of Thailand."
ln geo:capital:bangkok geo:country:THA sys:capital_of
ln geo:country:THA geo:capital:bangkok sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:bangkok"

def "geo:capital:brussels" "Brussels — capital of Belgium and seat of major EU institutions."
ln geo:capital:brussels geo:country:BEL sys:capital_of
ln geo:country:BEL geo:capital:brussels sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:brussels"

def "geo:capital:dhaka" "Dhaka — capital and largest city of Bangladesh."
ln geo:capital:dhaka geo:country:BGD sys:capital_of
ln geo:country:BGD geo:capital:dhaka sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:dhaka"

def "geo:capital:baghdad" "Baghdad — capital of Iraq; historic centre of the Abbasid Caliphate."
ln geo:capital:baghdad geo:country:IRQ sys:capital_of
ln geo:country:IRQ geo:capital:baghdad sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:baghdad"

def "geo:capital:kuala_lumpur" "Kuala Lumpur — capital of Malaysia."
ln geo:capital:kuala_lumpur geo:country:MYS sys:capital_of
ln geo:country:MYS geo:capital:kuala_lumpur sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:kuala_lumpur"
