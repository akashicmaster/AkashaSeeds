# conflict_zones.ak
# Active and recent conflict zones and frozen conflicts — post-1990
# Sources: UCDP, ACLED, SIPRI, UN OCHA — data as of 2025
#

# ── Namespace anchors ─────────────────────────────────────────────────────────

def "conflict:zone" "Active or recent armed conflict zone — root for all conflict zone atoms."
def "conflict:frozen" "Frozen conflict: armistice or ceasefire without political resolution — root atom."
def "conflict:region:europe" "European active and recent conflict zones."
def "conflict:region:middle_east" "Middle East and North Africa conflict zones."
def "conflict:region:africa" "Sub-Saharan African conflict zones."
def "conflict:region:asia" "Asian conflict zones."
def "conflict:region:americas" "Americas conflict zones."
def "conflict:type:interstate" "Conflict between recognised states — type anchor."
def "conflict:type:civil_war" "Intrastate armed conflict between organised factions — type anchor."
def "conflict:type:insurgency" "Asymmetric insurgency or terrorism against a state — type anchor."
def "conflict:type:territorial" "Territorial or border dispute with violence potential — type anchor."

set.add name="ontology.conflict_zones" id="conflict:zone"
set.add name="ontology.conflict_zones" id="conflict:frozen"
set.add name="ontology.conflict_zones" id="conflict:region:europe"
set.add name="ontology.conflict_zones" id="conflict:region:middle_east"
set.add name="ontology.conflict_zones" id="conflict:region:africa"
set.add name="ontology.conflict_zones" id="conflict:region:asia"
set.add name="ontology.conflict_zones" id="conflict:region:americas"
set.add name="ontology.conflict_zones" id="conflict:type:interstate"
set.add name="ontology.conflict_zones" id="conflict:type:civil_war"
set.add name="ontology.conflict_zones" id="conflict:type:insurgency"
set.add name="ontology.conflict_zones" id="conflict:type:territorial"

# ── Europe ────────────────────────────────────────────────────────────────────

def "conflict:zone:russia_ukraine" "Russia-Ukraine War (2022–); full-scale Russian invasion Feb 2022; follows 2014 Donbas conflict; largest conventional war in Europe since WWII; Bakhmut, Kherson, Zaporizhzhia fronts."
ln conflict:zone:russia_ukraine conflict:zone sys:part_of
ln conflict:zone:russia_ukraine conflict:region:europe sys:part_of
ln conflict:zone:russia_ukraine conflict:type:interstate sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:russia_ukraine"

def "conflict:zone:donbas_2014" "Donbas Conflict (2014–2022); Donetsk/Luhansk separatists backed by Russia; Minsk I and II agreements failed; absorbed into the 2022 full-scale invasion."
ln conflict:zone:donbas_2014 conflict:zone sys:part_of
ln conflict:zone:donbas_2014 conflict:region:europe sys:part_of
ln conflict:zone:donbas_2014 conflict:type:civil_war sys:part_of
ln conflict:zone:donbas_2014 conflict:zone:russia_ukraine war:led_to
set.add name="ontology.conflict_zones" id="conflict:zone:donbas_2014"

def "conflict:zone:nagorno_karabakh" "Nagorno-Karabakh Conflict (1988–2023); Armenia vs Azerbaijan; 2020 war: Azerbaijani victory; Sep 2023: Azerbaijani operation ended Armenian presence; dispute effectively resolved by force."
ln conflict:zone:nagorno_karabakh conflict:zone sys:part_of
ln conflict:zone:nagorno_karabakh conflict:region:europe sys:part_of
ln conflict:zone:nagorno_karabakh conflict:type:interstate sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:nagorno_karabakh"

# ── Middle East / North Africa ────────────────────────────────────────────────

def "conflict:zone:israel_palestine" "Israeli-Palestinian Conflict (ongoing); Gaza War escalation Oct 2023; Hamas attack 7 Oct 2023; Israeli military operation; 40,000+ deaths by 2024; acute humanitarian crisis."
ln conflict:zone:israel_palestine conflict:zone sys:part_of
ln conflict:zone:israel_palestine conflict:region:middle_east sys:part_of
ln conflict:zone:israel_palestine conflict:type:interstate sys:part_of
ln conflict:zone:israel_palestine conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:israel_palestine"

def "conflict:zone:syria" "Syrian Civil War (2011–); Assad regime vs rebels, ISIS, Kurds; foreign intervention by Russia, Iran, Turkey, USA; 500,000+ dead; Assad fell Dec 2024; reconstruction phase."
ln conflict:zone:syria conflict:zone sys:part_of
ln conflict:zone:syria conflict:region:middle_east sys:part_of
ln conflict:zone:syria conflict:type:civil_war sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:syria"

def "conflict:zone:yemen" "Yemen Civil War (2014–); Houthis vs Saudi-led coalition and Yemeni government; humanitarian catastrophe; 377,000+ dead; ceasefire 2022 fragile; Houthi Red Sea attacks 2023–."
ln conflict:zone:yemen conflict:zone sys:part_of
ln conflict:zone:yemen conflict:region:middle_east sys:part_of
ln conflict:zone:yemen conflict:type:civil_war sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:yemen"

def "conflict:zone:iraq_isis" "Iraq Insurgency (2013–); ISIS caliphate 2014–2017; defeated territorially by 2017; ongoing IS insurgency in Iraq and Syria; Yazidi genocide recognised by multiple states."
ln conflict:zone:iraq_isis conflict:zone sys:part_of
ln conflict:zone:iraq_isis conflict:region:middle_east sys:part_of
ln conflict:zone:iraq_isis conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:iraq_isis"

def "conflict:zone:libya" "Libyan Civil War (2011–); NATO intervention, Gaddafi killed; competing Tripoli and Tobruk governments; foreign involvement by Turkey, UAE, Russia/Wagner Group."
ln conflict:zone:libya conflict:zone sys:part_of
ln conflict:zone:libya conflict:region:middle_east sys:part_of
ln conflict:zone:libya conflict:type:civil_war sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:libya"

def "conflict:zone:sudan" "Sudan Civil War (2023–); SAF (Sudanese Armed Forces) vs RSF (Rapid Support Forces); Khartoum engulfed; 10M+ displaced; humanitarian catastrophe as of 2025."
ln conflict:zone:sudan conflict:zone sys:part_of
ln conflict:zone:sudan conflict:region:middle_east sys:part_of
ln conflict:zone:sudan conflict:type:civil_war sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:sudan"

# ── Africa ────────────────────────────────────────────────────────────────────

def "conflict:zone:ethiopia_tigray" "Tigray War (2020–2022); Ethiopian federal forces + Eritrea vs TPLF; 300,000–500,000 dead; Pretoria peace agreement Nov 2022; partial implementation ongoing."
ln conflict:zone:ethiopia_tigray conflict:zone sys:part_of
ln conflict:zone:ethiopia_tigray conflict:region:africa sys:part_of
ln conflict:zone:ethiopia_tigray conflict:type:civil_war sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:ethiopia_tigray"

def "conflict:zone:drc_eastern" "Eastern DRC Conflict (ongoing); M23/RDF, FDLR, ADF, dozens of armed groups; North and South Kivu provinces; 6M+ displaced; resource war dimension."
ln conflict:zone:drc_eastern conflict:zone sys:part_of
ln conflict:zone:drc_eastern conflict:region:africa sys:part_of
ln conflict:zone:drc_eastern conflict:type:civil_war sys:part_of
ln conflict:zone:drc_eastern conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:drc_eastern"

def "conflict:zone:somalia" "Somali Civil War (1991–); Al-Shabaab insurgency; African Union Mission (AMISOM/AUSSOM); failed state partial recovery; periodic government and clan offensives."
ln conflict:zone:somalia conflict:zone sys:part_of
ln conflict:zone:somalia conflict:region:africa sys:part_of
ln conflict:zone:somalia conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:somalia"

def "conflict:zone:mali_sahel" "Sahel Insurgency (2012–); jihadist groups JNIM and ISGS across Mali, Burkina Faso, Niger; French Barkhane withdrawal; Wagner/Russian influence; AES military coup bloc."
ln conflict:zone:mali_sahel conflict:zone sys:part_of
ln conflict:zone:mali_sahel conflict:region:africa sys:part_of
ln conflict:zone:mali_sahel conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:mali_sahel"

def "conflict:zone:nigeria_northeast" "Northeast Nigeria Conflict (2009–); Boko Haram and ISWAP (Islamic State West Africa Province); Lake Chad basin; 350,000+ dead; mass kidnappings."
ln conflict:zone:nigeria_northeast conflict:zone sys:part_of
ln conflict:zone:nigeria_northeast conflict:region:africa sys:part_of
ln conflict:zone:nigeria_northeast conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:nigeria_northeast"

def "conflict:zone:mozambique_cabo_delgado" "Cabo Delgado Insurgency (2017–); Islamic State-linked Ansar al-Sunna; gas-rich northern province; SADC and Rwandan forces deployed; 1M+ displaced."
ln conflict:zone:mozambique_cabo_delgado conflict:zone sys:part_of
ln conflict:zone:mozambique_cabo_delgado conflict:region:africa sys:part_of
ln conflict:zone:mozambique_cabo_delgado conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:mozambique_cabo_delgado"

def "conflict:zone:cameroon_anglophone" "Anglophone Crisis (2016–); Northwest/Southwest separatist Ambazonia movement vs Cameroonian state; 6,000+ dead; 700,000+ displaced; low-level ongoing war."
ln conflict:zone:cameroon_anglophone conflict:zone sys:part_of
ln conflict:zone:cameroon_anglophone conflict:region:africa sys:part_of
ln conflict:zone:cameroon_anglophone conflict:type:civil_war sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:cameroon_anglophone"

# ── Asia ──────────────────────────────────────────────────────────────────────

def "conflict:zone:afghanistan" "Afghan Conflict (2001–); US invasion post-9/11; Taliban takeover Aug 2021; IS-K resistance ongoing; humanitarian collapse; women's rights crisis under Taliban."
ln conflict:zone:afghanistan conflict:zone sys:part_of
ln conflict:zone:afghanistan conflict:region:asia sys:part_of
ln conflict:zone:afghanistan conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:afghanistan"

def "conflict:zone:myanmar" "Myanmar Civil War (2021–); military coup Feb 2021; NUG/People's Defence Forces and ethnic armed organisations vs Tatmadaw; widespread atrocities; 2M+ displaced."
ln conflict:zone:myanmar conflict:zone sys:part_of
ln conflict:zone:myanmar conflict:region:asia sys:part_of
ln conflict:zone:myanmar conflict:type:civil_war sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:myanmar"

def "conflict:zone:kashmir" "Kashmir Conflict (1947–); India-Pakistan dispute over Line of Control; 70,000+ dead since 1989 insurgency; nuclear-armed states; UN resolutions unimplemented."
ln conflict:zone:kashmir conflict:zone sys:part_of
ln conflict:zone:kashmir conflict:region:asia sys:part_of
ln conflict:zone:kashmir conflict:type:territorial sys:part_of
ln conflict:zone:kashmir conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:kashmir"

def "conflict:zone:xinjiang" "Xinjiang Uyghur Detention (2017–); Chinese government mass internment of Uyghurs; 1M+ in camps; cultural genocide allegations; UN Human Rights Office 2022 report."
ln conflict:zone:xinjiang conflict:zone sys:part_of
ln conflict:zone:xinjiang conflict:region:asia sys:part_of
ln conflict:zone:xinjiang conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:xinjiang"

# ── Frozen conflicts ──────────────────────────────────────────────────────────

def "conflict:frozen:korea" "Korean Stalemate (1953–); armistice but no peace treaty; DMZ; 70-year division; nuclear North Korea (first test 2006); periodic provocation cycles."
ln conflict:frozen:korea conflict:frozen sys:part_of
ln conflict:frozen:korea conflict:type:territorial sys:part_of
set.add name="ontology.conflict_zones" id="conflict:frozen:korea"

def "conflict:frozen:cyprus" "Cyprus Division (1974–); Turkish military intervention; Republic of Cyprus vs TRNC (recognised only by Turkey); UN buffer zone; EU membership complication."
ln conflict:frozen:cyprus conflict:frozen sys:part_of
ln conflict:frozen:cyprus conflict:region:europe sys:part_of
ln conflict:frozen:cyprus conflict:type:territorial sys:part_of
set.add name="ontology.conflict_zones" id="conflict:frozen:cyprus"

def "conflict:frozen:western_sahara" "Western Sahara Dispute (1975–); Morocco vs Polisario Front/SADR; ceasefire 1991; UN self-determination referendum never held; Morocco controls approximately 80%."
ln conflict:frozen:western_sahara conflict:frozen sys:part_of
ln conflict:frozen:western_sahara conflict:region:africa sys:part_of
ln conflict:frozen:western_sahara conflict:type:territorial sys:part_of
set.add name="ontology.conflict_zones" id="conflict:frozen:western_sahara"

def "conflict:frozen:transnistria" "Transnistrian Conflict (1992–); Moldova vs Russian-backed Transnistria; ceasefire holding; Russian troops present; concern reactivated following Russia-Ukraine 2022 invasion."
ln conflict:frozen:transnistria conflict:frozen sys:part_of
ln conflict:frozen:transnistria conflict:region:europe sys:part_of
ln conflict:frozen:transnistria conflict:type:territorial sys:part_of
set.add name="ontology.conflict_zones" id="conflict:frozen:transnistria"

def "conflict:frozen:abkhazia_ossetia" "Georgian Frozen Conflicts (1992–); Abkhazia and South Ossetia; Russian recognition after 2008 war; Georgia maintains sovereignty claim; effectively frozen."
ln conflict:frozen:abkhazia_ossetia conflict:frozen sys:part_of
ln conflict:frozen:abkhazia_ossetia conflict:region:europe sys:part_of
ln conflict:frozen:abkhazia_ossetia conflict:type:territorial sys:part_of
set.add name="ontology.conflict_zones" id="conflict:frozen:abkhazia_ossetia"

# ── Ongoing territorial disputes ──────────────────────────────────────────────

def "conflict:zone:south_china_sea" "South China Sea Disputes; China vs Vietnam, Philippines, Malaysia, Brunei, Taiwan; island-building campaigns; UNCLOS vs nine-dash line; US freedom-of-navigation operations."
ln conflict:zone:south_china_sea conflict:zone sys:part_of
ln conflict:zone:south_china_sea conflict:region:asia sys:part_of
ln conflict:zone:south_china_sea conflict:type:territorial sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:south_china_sea"

def "conflict:zone:taiwan_strait" "Taiwan Strait Tensions; PRC claims Taiwan; US Taiwan Relations Act; military exercises; strategic ambiguity doctrine; most-watched potential flashpoint as of 2025."
ln conflict:zone:taiwan_strait conflict:zone sys:part_of
ln conflict:zone:taiwan_strait conflict:region:asia sys:part_of
ln conflict:zone:taiwan_strait conflict:type:territorial sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:taiwan_strait"

def "conflict:zone:haiti" "Haiti Gang Crisis (2021–); PM Moïse assassination; gangs control 80%+ of Port-au-Prince; Kenyan-led Multinational Security Support Mission deployed 2024; state collapse."
ln conflict:zone:haiti conflict:zone sys:part_of
ln conflict:zone:haiti conflict:region:americas sys:part_of
ln conflict:zone:haiti conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:haiti"

def "conflict:zone:colombia_eln" "Colombia Residual Conflict (ongoing); ELN (National Liberation Army) and FARC dissidents active; government peace talks; drug economy nexus; persistent rural violence."
ln conflict:zone:colombia_eln conflict:zone sys:part_of
ln conflict:zone:colombia_eln conflict:region:americas sys:part_of
ln conflict:zone:colombia_eln conflict:type:insurgency sys:part_of
set.add name="ontology.conflict_zones" id="conflict:zone:colombia_eln"

# ── Cross-zone causal links ───────────────────────────────────────────────────

ln conflict:zone:donbas_2014 conflict:zone:russia_ukraine war:led_to
ln conflict:zone:iraq_isis conflict:zone:syria war:influenced_by
ln conflict:zone:mali_sahel conflict:zone:nigeria_northeast war:influenced_by
ln conflict:zone:afghanistan conflict:zone:mali_sahel war:influenced_by
