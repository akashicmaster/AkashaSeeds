# Akasha ontology (world pack) — regional specialties, produce & country facts.
# Named specialties tied to country and to the food/craft they are;
# a fact axis framing the measurable dimensions of a place, bridged to
# the existing geo: relations. A-tier.
def "product:specialty" "A product a place is famous for (名産/特産品)."
def "product:food" "A famous food/drink specialty."
def "product:craft" "A famous craft/manufactured specialty."
# ── specialties → country ──
def "product:champagne_wine" "Sparkling wine from the Champagne region."
ln product:champagne_wine product:food thesaurus:related
ln product:champagne_wine geo:country:FRA product:from
ln product:champagne_wine wine:style:sparkling_wine product:is_a
def "product:roquefort_cheese" "The blue sheep's-milk cheese of the Causses."
ln product:roquefort_cheese product:food thesaurus:related
ln product:roquefort_cheese geo:country:FRA product:from
ln product:roquefort_cheese cheese:roquefort product:is_a
def "product:parma_ham" "Dry-cured Prosciutto di Parma."
ln product:parma_ham product:food thesaurus:related
ln product:parma_ham geo:country:ITA product:from
def "product:parmigiano_reggiano" "The hard aged cow's-milk cheese."
ln product:parmigiano_reggiano product:food thesaurus:related
ln product:parmigiano_reggiano geo:country:ITA product:from
def "product:kobe_beef" "Prized marbled wagyu from Hyōgo."
ln product:kobe_beef product:food thesaurus:related
ln product:kobe_beef geo:country:JPN product:from
def "product:darjeeling_tea" "The 'champagne of teas' from the Himalayas."
ln product:darjeeling_tea product:food thesaurus:related
ln product:darjeeling_tea geo:country:IND product:from
ln product:darjeeling_tea tea:darjeeling product:is_a
def "product:colombian_coffee" "Balanced, world-famous Arabica coffee."
ln product:colombian_coffee product:food thesaurus:related
ln product:colombian_coffee geo:country:COL product:from
ln product:colombian_coffee coffee:colombian_coffee product:is_a
def "product:swiss_chocolate" "Fine milk chocolate of Switzerland."
ln product:swiss_chocolate product:food thesaurus:related
ln product:swiss_chocolate geo:country:CHE product:from
ln product:swiss_chocolate chocolate:milk_chocolate product:is_a
def "product:belgian_beer" "Trappist and abbey ales of Belgium."
ln product:belgian_beer product:food thesaurus:related
ln product:belgian_beer geo:country:BEL product:from
ln product:belgian_beer beer:beer product:is_a
def "product:scotch_whisky" "Malt whisky of Scotland."
ln product:scotch_whisky product:food thesaurus:related
ln product:scotch_whisky geo:country:GBR product:from
ln product:scotch_whisky whiskey:scotch product:is_a
def "product:mexican_tequila" "Agave spirit of Jalisco."
ln product:mexican_tequila product:food thesaurus:related
ln product:mexican_tequila geo:country:MEX product:from
ln product:mexican_tequila spirit:tequila product:is_a
def "product:swiss_watches" "Precision mechanical watches."
ln product:swiss_watches product:craft thesaurus:related
ln product:swiss_watches geo:country:CHE product:from
def "product:persian_carpets" "Hand-knotted Persian rugs."
ln product:persian_carpets product:craft thesaurus:related
ln product:persian_carpets geo:country:IRN product:from
def "product:murano_glass" "Venetian art glass."
ln product:murano_glass product:craft thesaurus:related
ln product:murano_glass geo:country:ITA product:from
def "product:chinese_silk" "The silk of the ancient Silk Road."
ln product:chinese_silk product:craft thesaurus:related
ln product:chinese_silk geo:country:CHN product:from
def "product:japanese_ceramics" "Porcelain and stoneware traditions."
ln product:japanese_ceramics product:craft thesaurus:related
ln product:japanese_ceramics geo:country:JPN product:from
def "product:colombian_emeralds" "The world's finest emeralds."
ln product:colombian_emeralds product:craft thesaurus:related
ln product:colombian_emeralds geo:country:COL product:from
# ── country fact axis — dimensions, bridged to geo: ──
def "fact:statistic" "A measurable fact about a place (statistical dimension)."
def "fact:population" "The number of inhabitants (人口)."
ln fact:population fact:statistic thesaurus:related
def "fact:area" "The land area (面積)."
ln fact:area fact:statistic thesaurus:related
def "fact:gdp" "The gross domestic product (GDP)."
ln fact:gdp fact:statistic thesaurus:related
def "fact:gdp_per_capita" "The GDP per person."
ln fact:gdp_per_capita fact:statistic thesaurus:related
def "fact:hdi" "The Human Development Index."
ln fact:hdi fact:statistic thesaurus:related
def "fact:capital" "The the seat of government (首都)."
ln fact:capital fact:statistic thesaurus:related
def "fact:currency" "The the official money (通貨)."
ln fact:currency fact:statistic thesaurus:related
def "fact:official_language" "The the state language(s) (公用語)."
ln fact:official_language fact:statistic thesaurus:related
def "fact:life_expectancy" "The average lifespan."
ln fact:life_expectancy fact:statistic thesaurus:related
def "fact:literacy_rate" "The share who can read and write."
ln fact:literacy_rate fact:statistic thesaurus:related
def "fact:major_export" "The the leading export good."
ln fact:major_export fact:statistic thesaurus:related
def "fact:climate_zone" "The the prevailing climate."
ln fact:climate_zone fact:statistic thesaurus:related
# bridge the fact axis to the existing geo: relations that already carry these
ln fact:gdp econ:gdp thesaurus:related
ln fact:currency fx:currency thesaurus:related
ln fact:population geog:demography thesaurus:related
ln fact:major_export econ:trade thesaurus:related
ln fact:climate_zone earthsci:climatology thesaurus:related
ln fact:hdi socwork:social_welfare thesaurus:related
