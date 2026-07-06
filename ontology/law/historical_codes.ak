# historical_codes.ak
# Historical law codes, charters, and foundational legal texts — ancient to 19th century
# Sources: Yale Avalon Project, Corpus Juris Civilis, ICS — Public domain
#

# ── Namespace anchor ──────────────────────────────────────────────────────────

def "law:code" "Root namespace for historical law codes, charters, constitutions, and foundational legal texts."

set.add name="ontology.legal_codes" id="law:code"

# ── Ancient Near Eastern codes ────────────────────────────────────────────────

def "law:code:ur_nammu" "Code of Ur-Nammu (c.2100 BCE, Sumer); oldest known law code; 57 laws surviving; compensatory fines rather than talion; King Ur-Nammu of Third Dynasty of Ur; divine prologue to Nanna."
def "law:code:lipit_ishtar" "Code of Lipit-Ishtar (c.1930 BCE, Isin); 38 laws in Sumerian; property, family, and slavery provisions; predates Hammurabi; king claims divine mandate from Enlil and Nippur."
def "law:code:eshnunna" "Laws of Eshnunna (c.1770 BCE, Eshnunna); price controls and interest rate limits; talion clauses for assault; earlier than Hammurabi; two tablets discovered at Tell Abu Harmal."
def "law:code:hammurabi" "Code of Hammurabi (c.1754 BCE, Babylon); 282 laws on black diorite stele; lex talionis; class-differentiated penalties; prologue invokes Marduk and Shamash; Yale and Louvre copies."
def "law:code:hittite_laws" "Hittite Laws (c.1650-1180 BCE); two tablets; generally compensatory over talion; progressive revision reducing penalties over time; bilingual Hittite and Akkadian traditions."
def "law:code:middle_assyrian_laws" "Middle Assyrian Laws (c.1400 BCE, Assur); harsh corporal penalties; detailed property and women's status law; veiling rules distinguishing respectable women from slaves and prostitutes."

ln law:code:ur_nammu law:code sys:part_of
ln law:code:lipit_ishtar law:code sys:part_of
ln law:code:eshnunna law:code sys:part_of
ln law:code:hammurabi law:code sys:part_of
ln law:code:hittite_laws law:code sys:part_of
ln law:code:middle_assyrian_laws law:code sys:part_of

ln law:code:ur_nammu law:tradition:sumerian_law law:codified_in
ln law:code:lipit_ishtar law:tradition:sumerian_law law:codified_in
ln law:code:eshnunna law:tradition:babylonian_law law:codified_in
ln law:code:hammurabi law:tradition:babylonian_law law:codified_in
ln law:code:hittite_laws law:tradition:hittite_law law:codified_in
ln law:code:middle_assyrian_laws law:tradition:assyrian_law law:codified_in

ln law:code:lipit_ishtar law:code:ur_nammu law:influenced_by
ln law:code:eshnunna law:code:lipit_ishtar law:influenced_by
ln law:code:hammurabi law:code:eshnunna law:influenced_by
ln law:code:hammurabi law:code:lipit_ishtar law:influenced_by

set.add name="ontology.legal_codes" id="law:code:ur_nammu"
set.add name="ontology.legal_codes" id="law:code:lipit_ishtar"
set.add name="ontology.legal_codes" id="law:code:eshnunna"
set.add name="ontology.legal_codes" id="law:code:hammurabi"
set.add name="ontology.legal_codes" id="law:code:hittite_laws"
set.add name="ontology.legal_codes" id="law:code:middle_assyrian_laws"

# ── Biblical and Torah law texts ──────────────────────────────────────────────

def "law:code:decalogue" "Ten Commandments; Exodus 20 and Deuteronomy 5; foundational Mosaic law; ethical and ritual commandments; foundation of Abrahamic legal ethics and Western moral-legal discourse."
def "law:code:covenant_code" "Book of the Covenant (Exodus 20-23); oldest Pentateuchal law code; talion principle; slave law; festival calendar; scholars date c.9th-8th century BCE."
def "law:code:deuteronomic_code" "Deuteronomy 12-26; judicial reform of older covenant code; centralised worship at single sanctuary; protections for poor, alien, widow, orphan; 7th century BCE redaction."

ln law:code:decalogue law:code sys:part_of
ln law:code:covenant_code law:code sys:part_of
ln law:code:deuteronomic_code law:code sys:part_of

ln law:code:decalogue law:tradition:halakha law:source_of
ln law:code:covenant_code law:tradition:halakha law:source_of
ln law:code:deuteronomic_code law:tradition:halakha law:source_of
ln law:code:covenant_code law:code:decalogue law:influenced_by
ln law:code:deuteronomic_code law:code:covenant_code law:influenced_by

set.add name="ontology.legal_codes" id="law:code:decalogue"
set.add name="ontology.legal_codes" id="law:code:covenant_code"
set.add name="ontology.legal_codes" id="law:code:deuteronomic_code"

# ── Ancient Greek codes ───────────────────────────────────────────────────────

def "law:code:draconian_laws" "Laws of Draco (c.621 BCE, Athens); first written Athenian laws; almost all offences punishable by death; Draco reportedly said he used blood not ink; origin of 'draconian.'"
def "law:code:solonian_reforms" "Solon's laws (594 BCE, Athens); abolished debt slavery (seisachtheia, shaking off of burdens); property-based political classes; foundation of Athenian democracy; displayed on axones."
def "law:code:gortyn_code" "Gortyn Code (c.450 BCE, Crete); earliest surviving extensive Greek legal inscription; 600 lines carved on curved stone wall; family law, property, status of free persons and slaves."

ln law:code:draconian_laws law:code sys:part_of
ln law:code:solonian_reforms law:code sys:part_of
ln law:code:gortyn_code law:code sys:part_of

ln law:code:draconian_laws law:tradition:athenian_law law:codified_in
ln law:code:solonian_reforms law:tradition:athenian_law law:codified_in
ln law:code:gortyn_code law:tradition:gortyn_law law:codified_in

ln law:code:solonian_reforms law:code:draconian_laws law:derived_from

set.add name="ontology.legal_codes" id="law:code:draconian_laws"
set.add name="ontology.legal_codes" id="law:code:solonian_reforms"
set.add name="ontology.legal_codes" id="law:code:gortyn_code"

# ── Roman codes ───────────────────────────────────────────────────────────────

def "law:code:twelve_tables" "Lex Duodecim Tabularum (c.450 BCE, Rome); first codified Roman law; displayed in the Forum; foundation of ius civile; covers family, property, procedure, delict, and succession."
def "law:code:corpus_juris_civilis" "Corpus Juris Civilis (529-534 CE, Justinian I); Digest, Institutes, Code, and Novels; systematic compilation of Roman jurisprudence; foundation of the civil law tradition worldwide."
def "law:code:justinian_digest" "Digest (Pandects, 533 CE); 50 books of extracts from classical jurists (Ulpian, Papinian, Paul, Gaius, Modestinus); core juristic component of Corpus Juris Civilis."
def "law:code:justinian_institutes" "Institutes (533 CE); law student textbook; 4 books covering persons, things, and actions; modelled on Gaius's 2nd-century Institutes; had force of law under Justinian."

ln law:code:twelve_tables law:code sys:part_of
ln law:code:corpus_juris_civilis law:code sys:part_of
ln law:code:justinian_digest law:code sys:part_of
ln law:code:justinian_institutes law:code sys:part_of

ln law:code:twelve_tables law:tradition:roman_republic_law law:codified_in
ln law:code:corpus_juris_civilis law:tradition:byzantine_law law:codified_in
ln law:code:justinian_digest law:code:corpus_juris_civilis sys:part_of
ln law:code:justinian_institutes law:code:corpus_juris_civilis sys:part_of

ln law:code:corpus_juris_civilis law:code:twelve_tables law:influenced_by

set.add name="ontology.legal_codes" id="law:code:twelve_tables"
set.add name="ontology.legal_codes" id="law:code:corpus_juris_civilis"
set.add name="ontology.legal_codes" id="law:code:justinian_digest"
set.add name="ontology.legal_codes" id="law:code:justinian_institutes"

# ── Byzantine codes ───────────────────────────────────────────────────────────

def "law:code:ecloga" "Ecloga (726 CE, Emperor Leo III and Constantine V); reformed Justinianic law; Christian moral influence; replaced many death penalties with mutilation; issued in Greek."
def "law:code:basilika" "Basilika (886-911 CE, Emperor Leo VI); Greek synthesis of entire Corpus Juris Civilis in 60 books; final and most comprehensive Byzantine legal codification."

ln law:code:ecloga law:code sys:part_of
ln law:code:basilika law:code sys:part_of

ln law:code:ecloga law:tradition:byzantine_law law:codified_in
ln law:code:basilika law:tradition:byzantine_law law:codified_in
ln law:code:ecloga law:code:corpus_juris_civilis law:derived_from
ln law:code:basilika law:code:corpus_juris_civilis law:derived_from
ln law:code:basilika law:code:ecloga law:influenced_by

set.add name="ontology.legal_codes" id="law:code:ecloga"
set.add name="ontology.legal_codes" id="law:code:basilika"

# ── European medieval codes ───────────────────────────────────────────────────

def "law:code:lex_salica" "Salic Law (Lex Salica, c.507 CE, Franks); commissioned by Clovis I; detailed wergild tariffs in 65 titles; later clauses excluding women from land inheritance shaped French succession law."
def "law:code:lombard_laws" "Lombard Laws (Edictum Rothari, 643 CE); 388 clauses; compensation-based Germanic system; supplements added by Liutprand (713-735 CE); influence on Italian customary law."
def "law:code:sachsenspiegel" "Sachsenspiegel (Saxon Mirror, c.1220-1235, Eike von Repgow); oldest major German law text; feudal, manorial, and procedural law; influenced German law for three centuries."
def "law:code:magna_carta" "Magna Carta (1215 CE, England); forced on King John by barons; 63 clauses; no taxation without representation; due process precursor; habeas corpus root; reissued 1216, 1217, 1225."
def "law:code:golden_bull_1222" "Golden Bull of 1222 (Hungary, King Andreas II); established noble privileges; restricted royal power over nobility; exempted nobles from certain taxes; called the 'Hungarian Magna Carta.'"
def "law:code:siete_partidas" "Siete Partidas (c.1265, Alfonso X of Castile, 'the Wise'); seven-part legal encyclopedia; synthesises Roman, canon, and customary law; profoundly influenced Latin American legal tradition."
def "law:code:golden_bull_1356" "Golden Bull of 1356 (Holy Roman Empire, Charles IV); defined electoral procedure for emperor; seven named prince-electors; foundational imperial constitutional document; in force until 1806."
def "law:code:joeishikimoku" "Joei Formulary / Goseibai Shikimoku (1232, Kamakura Japan); first samurai law code; 51 articles; shogunate governance; precedent-based administration of warrior estates."

ln law:code:lex_salica law:code sys:part_of
ln law:code:lombard_laws law:code sys:part_of
ln law:code:sachsenspiegel law:code sys:part_of
ln law:code:magna_carta law:code sys:part_of
ln law:code:golden_bull_1222 law:code sys:part_of
ln law:code:siete_partidas law:code sys:part_of
ln law:code:golden_bull_1356 law:code sys:part_of
ln law:code:joeishikimoku law:code sys:part_of

ln law:code:lex_salica law:tradition:salic_law law:codified_in
ln law:code:lex_salica law:tradition:germanic_customary_law law:codified_in
ln law:code:lombard_laws law:tradition:germanic_customary_law law:codified_in
ln law:code:sachsenspiegel law:tradition:germanic_customary_law law:codified_in
ln law:code:magna_carta law:tradition:feudal_law law:codified_in
ln law:code:magna_carta law:tradition:english_common_law law:source_of
ln law:code:siete_partidas law:tradition:civil_law_tradition law:codified_in
ln law:code:siete_partidas law:code:corpus_juris_civilis law:influenced_by
ln law:code:joeishikimoku law:tradition:buke_hatto law:codified_in

set.add name="ontology.legal_codes" id="law:code:lex_salica"
set.add name="ontology.legal_codes" id="law:code:lombard_laws"
set.add name="ontology.legal_codes" id="law:code:sachsenspiegel"
set.add name="ontology.legal_codes" id="law:code:magna_carta"
set.add name="ontology.legal_codes" id="law:code:golden_bull_1222"
set.add name="ontology.legal_codes" id="law:code:siete_partidas"
set.add name="ontology.legal_codes" id="law:code:golden_bull_1356"
set.add name="ontology.legal_codes" id="law:code:joeishikimoku"

# ── Early Modern codes and charters ──────────────────────────────────────────

def "law:code:habeas_corpus_act" "Habeas Corpus Act (1679, England); strengthened the ancient writ against unlawful imprisonment; required courts to act within prescribed time limits; landmark constitutional safeguard."
def "law:code:english_bill_of_rights" "English Bill of Rights (1689); constitutional settlement after Glorious Revolution; Parliamentary sovereignty; free elections; prohibition of cruel and unusual punishment; standing army limits."
def "law:code:peace_of_westphalia" "Peace of Westphalia (1648); Treaties of Munster and Osnabruck ending Thirty Years War; state sovereignty principle; non-interference in internal affairs; foundation of international law."
def "law:code:declaration_rights_man" "Declaration of the Rights of Man and Citizen (1789, France, National Assembly); liberty, property, security, and resistance to oppression; constitutional foundation of French Republic."
def "law:code:us_constitution" "United States Constitution (1787, Philadelphia Convention); federal republic; separation of powers; Bill of Rights added 1791 (10 amendments: speech, press, religion, due process, arms)."
def "law:code:napoleonic_code" "Code Napoleon / Code Civil (1804, France, Napoleon Bonaparte); systematic civil law code; private law of persons, property, and obligations; influenced Belgium, Spain, Latin America, Quebec, Louisiana."
def "law:code:meiji_civil_code" "Meiji Civil Code (1896, Japan); drafted with German BGB influence via Gustave Boissonade; family and property law; modernised Japan's legal system for international recognition."
def "law:code:bgb" "Burgerliches Gesetzbuch (BGB, 1900, Germany); systematic civil code in 5 books: general part, obligations, property, family, succession; model for East Asian and European civil law systems."

ln law:code:habeas_corpus_act law:code sys:part_of
ln law:code:english_bill_of_rights law:code sys:part_of
ln law:code:peace_of_westphalia law:code sys:part_of
ln law:code:declaration_rights_man law:code sys:part_of
ln law:code:us_constitution law:code sys:part_of
ln law:code:napoleonic_code law:code sys:part_of
ln law:code:meiji_civil_code law:code sys:part_of
ln law:code:bgb law:code sys:part_of

ln law:code:habeas_corpus_act law:tradition:english_common_law law:codified_in
ln law:code:habeas_corpus_act law:code:magna_carta law:influenced_by
ln law:code:english_bill_of_rights law:tradition:english_common_law law:codified_in
ln law:code:english_bill_of_rights law:code:magna_carta law:influenced_by
ln law:code:declaration_rights_man law:tradition:natural_law_school law:influenced_by
ln law:code:us_constitution law:tradition:natural_law_school law:influenced_by
ln law:code:us_constitution law:code:magna_carta law:influenced_by
ln law:code:napoleonic_code law:tradition:civil_law_tradition law:codified_in
ln law:code:napoleonic_code law:code:corpus_juris_civilis law:influenced_by
ln law:code:meiji_civil_code law:tradition:ritsuryo_system law:influenced_by
ln law:code:meiji_civil_code law:code:bgb law:influenced_by
ln law:code:bgb law:tradition:civil_law_tradition law:codified_in
ln law:code:bgb law:code:corpus_juris_civilis law:influenced_by
ln law:code:meiji_civil_code law:code:napoleonic_code law:influenced_by

set.add name="ontology.legal_codes" id="law:code:habeas_corpus_act"
set.add name="ontology.legal_codes" id="law:code:english_bill_of_rights"
set.add name="ontology.legal_codes" id="law:code:peace_of_westphalia"
set.add name="ontology.legal_codes" id="law:code:declaration_rights_man"
set.add name="ontology.legal_codes" id="law:code:us_constitution"
set.add name="ontology.legal_codes" id="law:code:napoleonic_code"
set.add name="ontology.legal_codes" id="law:code:meiji_civil_code"
set.add name="ontology.legal_codes" id="law:code:bgb"

# ── Islamic law texts ─────────────────────────────────────────────────────────

def "law:code:quran_legal" "Quran as primary legal source; approximately 500 verses of explicit legal content; property, family, criminal law, contracts; interpreted through fiqh methodology and classical commentaries."
def "law:code:fatawa_alamgiri" "Fatawa-e-Alamgiri (1670s, Mughal India, Emperor Aurangzeb); largest Hanafi fiqh compilation; 30 volumes compiled by 500 scholars; governed Mughal legal practice across the subcontinent."

ln law:code:quran_legal law:code sys:part_of
ln law:code:fatawa_alamgiri law:code sys:part_of

ln law:code:quran_legal law:tradition:fiqh law:source_of
ln law:code:quran_legal law:tradition:sharia law:source_of
ln law:code:fatawa_alamgiri law:tradition:hanafi_school law:codified_in
ln law:code:fatawa_alamgiri law:tradition:mughal_law law:codified_in

set.add name="ontology.legal_codes" id="law:code:quran_legal"
set.add name="ontology.legal_codes" id="law:code:fatawa_alamgiri"

# ── Chinese codes ─────────────────────────────────────────────────────────────

def "law:code:tang_code" "Tang Code (Tang lu shu yi, 653 CE, Tang dynasty); 502 articles in 12 chapters with detailed sub-commentary (shu yi); influenced Korean, Japanese, and Vietnamese law for centuries."
def "law:code:da_ming_hui_dian" "Da Ming Huidian (Great Ming Collected Statutes, 1587 final edition); Ming dynasty administrative and civil law; comprehensive statutory compilation; successor to Tang-Song tradition."
def "law:code:da_qing_lu_li" "Da Qing Luli (Great Qing Code, 1740 final form); 436 main articles plus accumulated sub-statutes; detailed penal and civil provisions; used until fall of Qing dynasty in 1912."

ln law:code:tang_code law:code sys:part_of
ln law:code:da_ming_hui_dian law:code sys:part_of
ln law:code:da_qing_lu_li law:code sys:part_of

ln law:code:tang_code law:tradition:tang_code_tradition law:codified_in
ln law:code:da_ming_hui_dian law:tradition:tang_code_tradition law:codified_in
ln law:code:da_qing_lu_li law:tradition:tang_code_tradition law:codified_in

ln law:code:da_ming_hui_dian law:code:tang_code law:influenced_by
ln law:code:da_qing_lu_li law:code:da_ming_hui_dian law:influenced_by
ln law:code:tang_code law:tradition:ritsuryo_system law:source_of
ln law:code:tang_code law:tradition:korean_legal_tradition law:source_of

set.add name="ontology.legal_codes" id="law:code:tang_code"
set.add name="ontology.legal_codes" id="law:code:da_ming_hui_dian"
set.add name="ontology.legal_codes" id="law:code:da_qing_lu_li"
