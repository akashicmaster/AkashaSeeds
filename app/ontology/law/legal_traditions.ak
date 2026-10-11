# legal_traditions.ak
# Legal traditions and jurisprudential schools — ancient to early modern
# Sources: Oxford Companion to Law, Brockelmann, Schacht, Watson — Public domain terminology
#

# ── Namespace anchors ────────────────────────────────────────────────────────

def "law:tradition" "Root namespace for legal traditions and jurisprudential schools across cultures and history."
def "law:region:near_east" "Ancient Near Eastern legal cultures; Mesopotamia, Anatolia, Levant; cuneiform law tradition."
def "law:region:mediterranean" "Greco-Roman and Mediterranean legal cultures; city-states, republic, empire."
def "law:region:european" "European legal development from Germanic custom through canon law to modern codification."
def "law:region:islamic" "Islamic legal traditions; fiqh schools derived from Quran, Sunna, ijma, and qiyas."
def "law:region:jewish" "Jewish legal traditions; Torah law, rabbinic elaboration, halakha across diaspora communities."
def "law:region:south_asian" "Indian subcontinent legal traditions; dharmashastra, arthashastra, vinaya, Mughal synthesis."
def "law:region:east_asian" "East Asian legal traditions; Chinese legalism, Confucian jurisprudence, Tang Code and its heirs."

# ── Ancient Near Eastern traditions ──────────────────────────────────────────

def "law:tradition:sumerian_law" "Earliest known legal system; city-state laws; lex talionis present; divine sanction through Nanna/Utu; commercial contracts and debt relief common; c.2100 BCE."
def "law:tradition:babylonian_law" "Hammurabi's Babylon and successors; comprehensive codified statutes; class-differentiated penalties; talion principle; c.1754 BCE."
def "law:tradition:assyrian_law" "Middle Assyrian Laws; severe corporal punishment; elaborate property and family law; veiling rules for respectable women; c.1400 BCE."
def "law:tradition:hittite_law" "Hittite Laws (hapaliya); generally compensatory rather than talion; refined procedural law; progressive reduction of penalties over time; c.1650 BCE."

ln law:tradition:sumerian_law law:region:near_east sys:part_of
ln law:tradition:babylonian_law law:region:near_east sys:part_of
ln law:tradition:assyrian_law law:region:near_east sys:part_of
ln law:tradition:hittite_law law:region:near_east sys:part_of

ln law:tradition:babylonian_law law:tradition:sumerian_law law:influenced_by
ln law:tradition:assyrian_law law:tradition:babylonian_law law:influenced_by

set.add name="ontology.legal_traditions" id="law:tradition:sumerian_law"
set.add name="ontology.legal_traditions" id="law:tradition:babylonian_law"
set.add name="ontology.legal_traditions" id="law:tradition:assyrian_law"
set.add name="ontology.legal_traditions" id="law:tradition:hittite_law"

# ── Ancient Mediterranean traditions ─────────────────────────────────────────

def "law:tradition:athenian_law" "Democratic Athenian legal system; Draco's code (c.621 BCE); Solon's reforms (594 BCE); popular courts (dikasteria); graphe paranomon; property-based political classes."
def "law:tradition:spartan_law" "Lycurgan constitution; oral tradition; agoge education as legal order; rhetra (sacred laws); collective discipline over individual rights."
def "law:tradition:gortyn_law" "Gortyn Code (c.450 BCE, Crete); oldest surviving extensive Greek legal inscription; 600 lines on stone; detailed property and family law."
def "law:tradition:roman_law" "Foundation of Western legal order; Twelve Tables to Corpus Juris Civilis; ius civile/gentium/naturale distinction; centrepiece of ius commune across medieval Europe."
def "law:tradition:roman_republic_law" "Twelve Tables (c.450 BCE); pontiffs as law's guardians; praetorian edict; ius civile expansion through juristic interpretation."
def "law:tradition:roman_imperial_law" "Principate and Dominate; imperial rescripts and constitutions; classical jurisprudence of Gaius, Ulpian, Papinian, and Paul; 1st-3rd century CE."
def "law:tradition:byzantine_law" "Eastern Roman continuation; Justinian Corpus (529-534 CE); Ecloga (726 CE); Basilika (886-911 CE); fused Roman, Greek, and Christian legal elements."
def "law:tradition:egyptian_pharaonic_law" "Ma'at as cosmic legal principle; pharaoh as supreme law-giver; demotic law texts; local oracle courts; compensation-based dispute resolution."

ln law:tradition:athenian_law law:region:mediterranean sys:part_of
ln law:tradition:spartan_law law:region:mediterranean sys:part_of
ln law:tradition:gortyn_law law:region:mediterranean sys:part_of
ln law:tradition:roman_law law:region:mediterranean sys:part_of
ln law:tradition:roman_republic_law law:region:mediterranean sys:part_of
ln law:tradition:roman_imperial_law law:region:mediterranean sys:part_of
ln law:tradition:byzantine_law law:region:mediterranean sys:part_of
ln law:tradition:egyptian_pharaonic_law law:region:mediterranean sys:part_of

ln law:tradition:roman_republic_law law:tradition:roman_law sys:part_of
ln law:tradition:roman_imperial_law law:tradition:roman_law sys:part_of
ln law:tradition:byzantine_law law:tradition:roman_law law:derived_from
ln law:tradition:roman_imperial_law law:tradition:roman_republic_law law:derived_from
ln law:tradition:athenian_law law:tradition:spartan_law law:contrasts_with

set.add name="ontology.legal_traditions" id="law:tradition:athenian_law"
set.add name="ontology.legal_traditions" id="law:tradition:spartan_law"
set.add name="ontology.legal_traditions" id="law:tradition:gortyn_law"
set.add name="ontology.legal_traditions" id="law:tradition:roman_law"
set.add name="ontology.legal_traditions" id="law:tradition:roman_republic_law"
set.add name="ontology.legal_traditions" id="law:tradition:roman_imperial_law"
set.add name="ontology.legal_traditions" id="law:tradition:byzantine_law"
set.add name="ontology.legal_traditions" id="law:tradition:egyptian_pharaonic_law"

# ── European traditions ───────────────────────────────────────────────────────

def "law:tradition:germanic_customary_law" "Tribal leges barbarorum; Salic, Lombard, Visigothic Law; wergild (blood money); oral custom written under Roman influence; 5th-8th century CE."
def "law:tradition:salic_law" "Frankish law (Lex Salica, c.507 CE); detailed tariff system for injuries and killings; famously excluded women from land inheritance; basis of later French succession rules."
def "law:tradition:anglo_saxon_law" "Dooms of Aethelberht (c.600 CE) and Alfred (c.890 CE); wergild; communal oath-helping (compurgation); precursor to English common law."
def "law:tradition:norse_law" "Thing (assembly) system; Gragas (Icelandic Commonwealth law, c.1117); Gulathing Law; outlawry as primary sanction; no professional judiciary; consensus-based."
def "law:tradition:canon_law" "Law of the Catholic Church; Gratian's Decretum (c.1140); papal decretals; church courts; jurisdiction over marriage, wills, and moral offences; ius commune synthesis."
def "law:tradition:feudal_law" "Hierarchical obligation system; lord-vassal relationships; tenure and homage; feudal incidents; manorial courts; Magna Carta as foundational feudal document."
def "law:tradition:lex_mercatoria" "Medieval merchants' law; customary commercial rules across Europe; bill of exchange, insurance, partnership; fairs of Champagne; later absorbed into national law."
def "law:tradition:english_common_law" "Judge-made law through precedent (stare decisis); jury system; writs; equity as supplement; exported to British Empire; developed from 11th century onwards."
def "law:tradition:equity" "Court of Chancery; conscience-based relief beyond common law rigidity; trust, injunction, specific performance; Lord Chancellor; maxims: equity follows the law."
def "law:tradition:civil_law_tradition" "Roman-Germanic codified law; systematic codes replacing case law; no binding precedent doctrine; France, Germany, Spain, Italy, Latin America, Meiji Japan."
def "law:tradition:ius_commune" "Medieval learned law; fusion of Justinian Corpus and canon law; university-taught across Europe; applied by trained jurists; 12th-17th century."
def "law:tradition:natural_law_school" "Aquinas: law participates in eternal reason; Grotius: natural law independent of theology; Locke: natural rights; Pufendorf, Vattel; rationalist jurisprudence."
def "law:tradition:legal_positivism" "Law as social fact separate from morality; Bentham and Austin: law = command of sovereign; Hart: rule of recognition; Kelsen: pure theory; 19th-20th century."

ln law:tradition:germanic_customary_law law:region:european sys:part_of
ln law:tradition:salic_law law:region:european sys:part_of
ln law:tradition:anglo_saxon_law law:region:european sys:part_of
ln law:tradition:norse_law law:region:european sys:part_of
ln law:tradition:canon_law law:region:european sys:part_of
ln law:tradition:feudal_law law:region:european sys:part_of
ln law:tradition:lex_mercatoria law:region:european sys:part_of
ln law:tradition:english_common_law law:region:european sys:part_of
ln law:tradition:equity law:region:european sys:part_of
ln law:tradition:civil_law_tradition law:region:european sys:part_of
ln law:tradition:ius_commune law:region:european sys:part_of
ln law:tradition:natural_law_school law:region:european sys:part_of
ln law:tradition:legal_positivism law:region:european sys:part_of

ln law:tradition:salic_law law:tradition:germanic_customary_law sys:part_of
ln law:tradition:anglo_saxon_law law:tradition:germanic_customary_law law:derived_from
ln law:tradition:english_common_law law:tradition:anglo_saxon_law law:influenced_by
ln law:tradition:english_common_law law:tradition:feudal_law law:influenced_by
ln law:tradition:equity law:tradition:english_common_law sys:part_of
ln law:tradition:ius_commune law:tradition:roman_law law:derived_from
ln law:tradition:ius_commune law:tradition:canon_law law:derived_from
ln law:tradition:civil_law_tradition law:tradition:roman_law law:derived_from
ln law:tradition:civil_law_tradition law:tradition:ius_commune law:influenced_by
ln law:tradition:english_common_law law:tradition:civil_law_tradition law:contrasts_with
ln law:tradition:natural_law_school law:tradition:legal_positivism law:contrasts_with

set.add name="ontology.legal_traditions" id="law:tradition:germanic_customary_law"
set.add name="ontology.legal_traditions" id="law:tradition:salic_law"
set.add name="ontology.legal_traditions" id="law:tradition:anglo_saxon_law"
set.add name="ontology.legal_traditions" id="law:tradition:norse_law"
set.add name="ontology.legal_traditions" id="law:tradition:canon_law"
set.add name="ontology.legal_traditions" id="law:tradition:feudal_law"
set.add name="ontology.legal_traditions" id="law:tradition:lex_mercatoria"
set.add name="ontology.legal_traditions" id="law:tradition:english_common_law"
set.add name="ontology.legal_traditions" id="law:tradition:equity"
set.add name="ontology.legal_traditions" id="law:tradition:civil_law_tradition"
set.add name="ontology.legal_traditions" id="law:tradition:ius_commune"
set.add name="ontology.legal_traditions" id="law:tradition:natural_law_school"
set.add name="ontology.legal_traditions" id="law:tradition:legal_positivism"

# ── Islamic traditions ────────────────────────────────────────────────────────

def "law:tradition:fiqh" "Islamic jurisprudence; derives law from Quran, Sunna, ijma, qiyas; five categories of acts (wajib/mandub/mubah/makruh/haram); developed systematically 8th-10th century."
def "law:tradition:hanafi_school" "Founded by Abu Hanifa (d.767); largest Sunni school; Iraq, Ottoman Empire, South Asia; strong use of qiyas (analogy) and istihsan (juristic preference)."
def "law:tradition:maliki_school" "Founded by Malik ibn Anas (d.795); Medina practice (amal) as authoritative source; dominant in North and West Africa; weights local custom of Medina heavily."
def "law:tradition:shafii_school" "Founded by al-Shafi'i (d.820); systematised usul al-fiqh (legal theory); dominant in East Africa and Southeast Asia; strong emphasis on hadith over local custom."
def "law:tradition:hanbali_school" "Founded by Ibn Hanbal (d.855); strictest textualism; Arabian Peninsula; theological and legal base of Wahhabi and Salafi movements."
def "law:tradition:jafari_school" "Shia Twelver school; named for Imam Ja'far al-Sadiq (d.765); dominant in Iran, Iraq, Lebanon; differs on inheritance, temporary marriage (mutah), scope of ijtihad."
def "law:tradition:sharia" "Islamic sacred law; encompasses ritual, ethics, and civil/criminal regulation; comprehensive social order; not equivalent to modern state law alone; interpreted through fiqh."

ln law:tradition:fiqh law:region:islamic sys:part_of
ln law:tradition:hanafi_school law:region:islamic sys:part_of
ln law:tradition:maliki_school law:region:islamic sys:part_of
ln law:tradition:shafii_school law:region:islamic sys:part_of
ln law:tradition:hanbali_school law:region:islamic sys:part_of
ln law:tradition:jafari_school law:region:islamic sys:part_of
ln law:tradition:sharia law:region:islamic sys:part_of

ln law:tradition:hanafi_school law:tradition:fiqh sys:part_of
ln law:tradition:maliki_school law:tradition:fiqh sys:part_of
ln law:tradition:shafii_school law:tradition:fiqh sys:part_of
ln law:tradition:hanbali_school law:tradition:fiqh sys:part_of
ln law:tradition:jafari_school law:tradition:fiqh sys:part_of
ln law:tradition:sharia law:tradition:fiqh law:source_of
ln law:tradition:hanafi_school law:tradition:jafari_school law:contrasts_with

set.add name="ontology.legal_traditions" id="law:tradition:fiqh"
set.add name="ontology.legal_traditions" id="law:tradition:hanafi_school"
set.add name="ontology.legal_traditions" id="law:tradition:maliki_school"
set.add name="ontology.legal_traditions" id="law:tradition:shafii_school"
set.add name="ontology.legal_traditions" id="law:tradition:hanbali_school"
set.add name="ontology.legal_traditions" id="law:tradition:jafari_school"
set.add name="ontology.legal_traditions" id="law:tradition:sharia"

# ── Jewish traditions ─────────────────────────────────────────────────────────

def "law:tradition:halakha" "Jewish law (halakha) encompassing all aspects of life; Torah commandments elaborated through Talmud and rabbinic authority; evolves through responsa literature; binding on observant Jews."
def "law:tradition:talmudic_law" "Mishnah (c.200 CE) and Gemara (Babylonian c.500 CE, Palestinian c.400 CE); case-based dialectical reasoning; oral Torah reduced to writing; foundational to all subsequent halakha."
def "law:tradition:responsa_literature" "Teshuvot; written rabbinical rulings on specific legal questions; from Geonic period (7th century) to present; functions as ongoing case law within the halakhic system."
def "law:tradition:sephardic_law" "Iberian and Oriental Jewish tradition; Maimonides' Mishneh Torah (1170-1180); Karo's Shulchan Aruch (1565); Spanish, North African, and Middle Eastern communities."
def "law:tradition:ashkenazic_law" "Franco-German tradition; Rashi and Tosafist commentaries; Isserles' Mappah gloss to Shulchan Aruch; Eastern European legal custom (minhag) weighted heavily."

ln law:tradition:halakha law:region:jewish sys:part_of
ln law:tradition:talmudic_law law:region:jewish sys:part_of
ln law:tradition:responsa_literature law:region:jewish sys:part_of
ln law:tradition:sephardic_law law:region:jewish sys:part_of
ln law:tradition:ashkenazic_law law:region:jewish sys:part_of

ln law:tradition:talmudic_law law:tradition:halakha law:source_of
ln law:tradition:responsa_literature law:tradition:halakha sys:part_of
ln law:tradition:sephardic_law law:tradition:halakha sys:part_of
ln law:tradition:ashkenazic_law law:tradition:halakha sys:part_of
ln law:tradition:sephardic_law law:tradition:ashkenazic_law law:contrasts_with

set.add name="ontology.legal_traditions" id="law:tradition:halakha"
set.add name="ontology.legal_traditions" id="law:tradition:talmudic_law"
set.add name="ontology.legal_traditions" id="law:tradition:responsa_literature"
set.add name="ontology.legal_traditions" id="law:tradition:sephardic_law"
set.add name="ontology.legal_traditions" id="law:tradition:ashkenazic_law"

# ── South Asian traditions ────────────────────────────────────────────────────

def "law:tradition:dharmashastra" "Sanskrit law literature; dharma as cosmic-social order regulating all conduct; Manusmriti, Yajnavalkya Smriti, Naradasmriti; varna-based social duties; 200 BCE-1000 CE."
def "law:tradition:arthashastra_tradition" "Kautilya's statecraft tradition; pragmatic political-legal administration; taxation, diplomacy, espionage, and punishment; rational state governance; c.300 BCE."
def "law:tradition:vinaya" "Buddhist monastic code; rules governing the sangha; Patimokkha (227 rules for monks); procedural law for internal monastic disputes; parallel to secular legal orders."
def "law:tradition:mughal_law" "Synthesis of Hanafi fiqh and Indic custom; Fatawa-e-Alamgiri (Aurangzeb, 1670s); largest Hanafi compilation; governed Mughal India's legal practice across diverse populations."

ln law:tradition:dharmashastra law:region:south_asian sys:part_of
ln law:tradition:arthashastra_tradition law:region:south_asian sys:part_of
ln law:tradition:vinaya law:region:south_asian sys:part_of
ln law:tradition:mughal_law law:region:south_asian sys:part_of

ln law:tradition:mughal_law law:tradition:hanafi_school law:derived_from
ln law:tradition:mughal_law law:tradition:dharmashastra law:influenced_by
ln law:tradition:arthashastra_tradition law:tradition:dharmashastra law:contrasts_with

set.add name="ontology.legal_traditions" id="law:tradition:dharmashastra"
set.add name="ontology.legal_traditions" id="law:tradition:arthashastra_tradition"
set.add name="ontology.legal_traditions" id="law:tradition:vinaya"
set.add name="ontology.legal_traditions" id="law:tradition:mughal_law"

# ── East Asian traditions ─────────────────────────────────────────────────────

def "law:tradition:chinese_legalism" "Fa (written law) over custom; Shang Yang and Han Fei theorised strict uniform law applied equally; Qin dynasty codification (221 BCE); statecraft through deterrence."
def "law:tradition:confucian_jurisprudence" "Li (ritual propriety) over fa (law); harmony restoration prioritised over punishment; education and moral persuasion as primary legal instruments; Tang Code synthesised both."
def "law:tradition:tang_code_tradition" "Tang Code (lu ling ge shi, 653 CE) and dynastic successors; Chinese imperial penal and administrative law; detailed commentary; model for Korea, Japan, and Vietnam."
def "law:tradition:ritsuryo_system" "Japanese ritsuryo system; Tang-derived administrative and penal codes; Taiho Code (701 CE), Yoro Code (718 CE); aristocratic Nara-Heian governance."
def "law:tradition:buke_hatto" "Japanese warrior law (bukeho); Kamakura shogunate Joei Formulary (1232); Tokugawa Buke Shohatto (1615); parallel legal order to imperial ritsuryo system."
def "law:tradition:korean_legal_tradition" "Koryo and Choson dynasty law; Tang Code as base with Korean custom overlay; Kyongguk Taejon (1485, Choson legal code); continuous sinitic legal heritage."

ln law:tradition:chinese_legalism law:region:east_asian sys:part_of
ln law:tradition:confucian_jurisprudence law:region:east_asian sys:part_of
ln law:tradition:tang_code_tradition law:region:east_asian sys:part_of
ln law:tradition:ritsuryo_system law:region:east_asian sys:part_of
ln law:tradition:buke_hatto law:region:east_asian sys:part_of
ln law:tradition:korean_legal_tradition law:region:east_asian sys:part_of

ln law:tradition:tang_code_tradition law:tradition:chinese_legalism law:derived_from
ln law:tradition:tang_code_tradition law:tradition:confucian_jurisprudence law:influenced_by
ln law:tradition:ritsuryo_system law:tradition:tang_code_tradition law:derived_from
ln law:tradition:korean_legal_tradition law:tradition:tang_code_tradition law:derived_from
ln law:tradition:buke_hatto law:tradition:ritsuryo_system law:contrasts_with
ln law:tradition:chinese_legalism law:tradition:confucian_jurisprudence law:contrasts_with

set.add name="ontology.legal_traditions" id="law:tradition:chinese_legalism"
set.add name="ontology.legal_traditions" id="law:tradition:confucian_jurisprudence"
set.add name="ontology.legal_traditions" id="law:tradition:tang_code_tradition"
set.add name="ontology.legal_traditions" id="law:tradition:ritsuryo_system"
set.add name="ontology.legal_traditions" id="law:tradition:buke_hatto"
set.add name="ontology.legal_traditions" id="law:tradition:korean_legal_tradition"

# ── Namespace anchors into collection ─────────────────────────────────────────

set.add name="ontology.legal_traditions" id="law:tradition"
set.add name="ontology.legal_traditions" id="law:region:near_east"
set.add name="ontology.legal_traditions" id="law:region:mediterranean"
set.add name="ontology.legal_traditions" id="law:region:european"
set.add name="ontology.legal_traditions" id="law:region:islamic"
set.add name="ontology.legal_traditions" id="law:region:jewish"
set.add name="ontology.legal_traditions" id="law:region:south_asian"
set.add name="ontology.legal_traditions" id="law:region:east_asian"
