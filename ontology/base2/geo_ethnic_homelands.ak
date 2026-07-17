# Akasha ontology — geo:people / geo:autonomous
# Ethnic homelands that span multiple political units.
# geo:people: — a named people or ethnic group as a geographic concept
# geo:autonomous: — an administrative unit with ethnic/cultural character
# All descriptions are geographic and cultural; no political framing.
# atoms: 28

# ── Mongolia capital ───────────────────────────────────────────────────────────
# (geo:country:MNG defined in geo_countries.ak)

def "geo:capital:ulaanbaatar" "Ulaanbaatar — capital of Mongolia."
ln geo:capital:ulaanbaatar geo:country:MNG sys:capital_of
ln geo:country:MNG geo:capital:ulaanbaatar sys:has_capital
set.add name="set:geo:capitals" id="geo:capital:ulaanbaatar"

# Mongolia geographic properties
set.add name="set:geo:landlocked" id="geo:country:MNG"
set.add name="set:geo:northern_hemisphere" id="geo:country:MNG"
set.add name="set:geo:polar" id="geo:country:MNG"
ln geo:country:MNG geo:country:CHN geo:borders
ln geo:country:CHN geo:country:MNG geo:borders
ln geo:country:MNG geo:country:RUS geo:borders
ln geo:country:RUS geo:country:MNG geo:borders
ln geo:country:MNG geo:org:UN geo:member_of
set.add name="set:geo:un" id="geo:country:MNG"

# ── Mongolic peoples ───────────────────────────────────────────────────────────

def "geo:people:MONGOLS" "Mongolic peoples — sharing Mongolic languages and nomadic pastoral traditions across Central and East Asia."
al geo:people:MONGOLS mongols
set.add name="set:geo:index" id="geo:people:MONGOLS"
ln geo:people:MONGOLS geo:country:MNG thesaurus:related
ln geo:people:MONGOLS geo:region:eastern_asia thesaurus:related

def "geo:autonomous:CHN_NM" "Inner Mongolia (Nei Mongol) — autonomous region of northern China with Mongolic-speaking communities."
al geo:autonomous:CHN_NM inner_mongolia
set.add name="set:geo:index" id="geo:autonomous:CHN_NM"
ln geo:autonomous:CHN_NM geo:country:CHN thesaurus:hypernym
ln geo:autonomous:CHN_NM geo:people:MONGOLS thesaurus:related
ln geo:autonomous:CHN_NM geo:region:eastern_asia thesaurus:hypernym

def "geo:autonomous:RUS_BU" "Republic of Buryatia — federal subject of Russia around Lake Baikal; Buryat Mongolian culture."
al geo:autonomous:RUS_BU buryatia
set.add name="set:geo:index" id="geo:autonomous:RUS_BU"
ln geo:autonomous:RUS_BU geo:country:RUS thesaurus:hypernym
ln geo:autonomous:RUS_BU geo:people:MONGOLS thesaurus:related
ln geo:autonomous:RUS_BU geo:region:eastern_europe thesaurus:hypernym

def "geo:autonomous:RUS_KL" "Republic of Kalmykia — federal subject of Russia on the Caspian steppe; Kalmyk (Western Mongol) culture."
al geo:autonomous:RUS_KL kalmykia
set.add name="set:geo:index" id="geo:autonomous:RUS_KL"
ln geo:autonomous:RUS_KL geo:country:RUS thesaurus:hypernym
ln geo:autonomous:RUS_KL geo:people:MONGOLS thesaurus:related
ln geo:autonomous:RUS_KL geo:region:eastern_europe thesaurus:hypernym

# ── Kurdish peoples ────────────────────────────────────────────────────────────

def "geo:people:KURDS" "Kurdish peoples — Indo-Iranian speaking people of the mountainous region across Turkey, Iraq, Iran and Syria."
al geo:people:KURDS kurds
set.add name="set:geo:index" id="geo:people:KURDS"
ln geo:people:KURDS geo:country:TUR thesaurus:related
ln geo:people:KURDS geo:country:IRN thesaurus:related
ln geo:people:KURDS geo:region:western_asia thesaurus:related

def "geo:autonomous:IRQ_KR" "Kurdistan Region — autonomous region of northern Iraq with a Kurdish majority."
al geo:autonomous:IRQ_KR kurdistan
set.add name="set:geo:index" id="geo:autonomous:IRQ_KR"
ln geo:autonomous:IRQ_KR geo:people:KURDS thesaurus:related
ln geo:autonomous:IRQ_KR geo:region:western_asia thesaurus:hypernym

# ── Basque peoples ─────────────────────────────────────────────────────────────

def "geo:people:BASQUES" "Basque people — language isolate speakers of the Pyrenean borderland of Spain and France."
al geo:people:BASQUES basques
set.add name="set:geo:index" id="geo:people:BASQUES"
ln geo:people:BASQUES geo:country:ESP thesaurus:related
ln geo:people:BASQUES geo:country:FRA thesaurus:related
ln geo:people:BASQUES geo:region:southern_europe thesaurus:related

def "geo:autonomous:ESP_EU" "Basque Country (Euskadi) — autonomous community of northern Spain."
al geo:autonomous:ESP_EU euskadi
set.add name="set:geo:index" id="geo:autonomous:ESP_EU"
ln geo:autonomous:ESP_EU geo:country:ESP thesaurus:hypernym
ln geo:autonomous:ESP_EU geo:people:BASQUES thesaurus:related
ln geo:autonomous:ESP_EU geo:region:southern_europe thesaurus:hypernym

def "geo:autonomous:FRA_PB" "French Basque Country (Pays Basque) — Basque-speaking area within Pyrénées-Atlantiques, France."
al geo:autonomous:FRA_PB pays_basque
set.add name="set:geo:index" id="geo:autonomous:FRA_PB"
ln geo:autonomous:FRA_PB geo:country:FRA thesaurus:hypernym
ln geo:autonomous:FRA_PB geo:people:BASQUES thesaurus:related
ln geo:autonomous:FRA_PB geo:region:western_europe thesaurus:hypernym

# ── Catalan peoples ────────────────────────────────────────────────────────────

def "geo:people:CATALANS" "Catalan people — Romance-language speakers of north-eastern Iberia, southern France and the Balearic Islands."
al geo:people:CATALANS catalans
set.add name="set:geo:index" id="geo:people:CATALANS"
ln geo:people:CATALANS geo:country:ESP thesaurus:related
ln geo:people:CATALANS geo:country:FRA thesaurus:related
ln geo:people:CATALANS geo:region:southern_europe thesaurus:related

def "geo:autonomous:ESP_CT" "Catalonia — autonomous community of north-eastern Spain; Catalan language and culture."
al geo:autonomous:ESP_CT catalonia
set.add name="set:geo:index" id="geo:autonomous:ESP_CT"
ln geo:autonomous:ESP_CT geo:country:ESP thesaurus:hypernym
ln geo:autonomous:ESP_CT geo:people:CATALANS thesaurus:related
ln geo:autonomous:ESP_CT geo:region:southern_europe thesaurus:hypernym

def "geo:autonomous:FRA_RC" "Northern Catalonia (Roussillon) — Catalan-speaking area in southern France."
al geo:autonomous:FRA_RC roussillon
set.add name="set:geo:index" id="geo:autonomous:FRA_RC"
ln geo:autonomous:FRA_RC geo:country:FRA thesaurus:hypernym
ln geo:autonomous:FRA_RC geo:people:CATALANS thesaurus:related
ln geo:autonomous:FRA_RC geo:region:western_europe thesaurus:hypernym

# ── Tibetan peoples ────────────────────────────────────────────────────────────

def "geo:people:TIBETANS" "Tibetan people — Sino-Tibetan speaking people of the Tibetan Plateau and surrounding highlands."
al geo:people:TIBETANS tibetans
set.add name="set:geo:index" id="geo:people:TIBETANS"
ln geo:people:TIBETANS geo:country:CHN thesaurus:related
ln geo:people:TIBETANS geo:region:southern_asia thesaurus:related

def "geo:autonomous:CHN_XZ" "Tibet Autonomous Region (Xizang) — autonomous region of western China on the Tibetan Plateau."
al geo:autonomous:CHN_XZ tibet
set.add name="set:geo:index" id="geo:autonomous:CHN_XZ"
ln geo:autonomous:CHN_XZ geo:country:CHN thesaurus:hypernym
ln geo:autonomous:CHN_XZ geo:people:TIBETANS thesaurus:related
ln geo:autonomous:CHN_XZ geo:region:southern_asia thesaurus:hypernym
