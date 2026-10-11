# Akasha ontology — namespace: geo:nation
# UK constituent nations and their capitals.
# Great Britain = England + Scotland + Wales (the main island).
# United Kingdom = Great Britain + Northern Ireland.
# geo_capitals.ak must load first (London already defined there).
# atoms: 8

def "geo:nation:GBR" "Great Britain (England, Scotland and Wales)"
al geo:nation:GBR britain
set.add name="set:geo:index" id="geo:nation:GBR"
ln geo:nation:GBR geo:country:GBR thesaurus:hypernym
ln geo:nation:GBR geo:region:northern_europe thesaurus:hypernym

def "geo:nation:ENG" "England"
al geo:nation:ENG eng
al geo:nation:ENG england
set.add name="set:geo:index" id="geo:nation:ENG"
ln geo:nation:ENG geo:nation:GBR thesaurus:hypernym
ln geo:nation:ENG geo:country:GBR thesaurus:hypernym
ln geo:nation:ENG geo:region:northern_europe thesaurus:hypernym

def "geo:nation:SCT" "Scotland"
al geo:nation:SCT sco
al geo:nation:SCT scotland
set.add name="set:geo:index" id="geo:nation:SCT"
ln geo:nation:SCT geo:nation:GBR thesaurus:hypernym
ln geo:nation:SCT geo:country:GBR thesaurus:hypernym
ln geo:nation:SCT geo:region:northern_europe thesaurus:hypernym

def "geo:nation:WLS" "Wales"
al geo:nation:WLS wls
al geo:nation:WLS wales
set.add name="set:geo:index" id="geo:nation:WLS"
ln geo:nation:WLS geo:nation:GBR thesaurus:hypernym
ln geo:nation:WLS geo:country:GBR thesaurus:hypernym
ln geo:nation:WLS geo:region:northern_europe thesaurus:hypernym

def "geo:nation:NIR" "Northern Ireland"
al geo:nation:NIR nir
al geo:nation:NIR northern_ireland
set.add name="set:geo:index" id="geo:nation:NIR"
ln geo:nation:NIR geo:country:GBR thesaurus:hypernym
ln geo:nation:NIR geo:region:northern_europe thesaurus:hypernym

# London (geo:capital:london) is defined in geo_capitals.ak; add England link here
ln geo:capital:london geo:nation:ENG sys:capital_of
ln geo:nation:ENG geo:capital:london sys:has_capital

def "geo:capital:edinburgh" "Edinburgh — capital of Scotland."
ln geo:capital:edinburgh geo:nation:SCT sys:capital_of
ln geo:nation:SCT geo:capital:edinburgh sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:edinburgh"

def "geo:capital:cardiff" "Cardiff — capital of Wales."
ln geo:capital:cardiff geo:nation:WLS sys:capital_of
ln geo:nation:WLS geo:capital:cardiff sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:cardiff"

def "geo:capital:belfast" "Belfast — capital of Northern Ireland."
ln geo:capital:belfast geo:nation:NIR sys:capital_of
ln geo:nation:NIR geo:capital:belfast sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:belfast"
