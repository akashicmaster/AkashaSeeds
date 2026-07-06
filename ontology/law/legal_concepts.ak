# legal_concepts.ak
# Foundational legal concepts, doctrines, and procedural principles
# Sources: Black's Law Dictionary, Berger, Gordley — Public domain terminology
#

# ── Namespace anchors ─────────────────────────────────────────────────────────

def "law:concept" "Root namespace for foundational legal concepts, doctrines, and procedural principles across traditions."
def "law:procedure" "Procedural law concepts; rules governing how legal proceedings are conducted, initiated, and resolved."
def "law:doctrine" "Substantive law doctrines; legal rules and principles determining rights, duties, and liabilities."
def "law:philosophy" "Jurisprudential and legal philosophy concepts; theories of the nature, source, and purpose of law."

set.add name="ontology.legal_concepts" id="law:concept"
set.add name="ontology.legal_concepts" id="law:procedure"
set.add name="ontology.legal_concepts" id="law:doctrine"
set.add name="ontology.legal_concepts" id="law:philosophy"

# ── Procedural concepts ───────────────────────────────────────────────────────

def "law:concept:habeas_corpus" "\"You shall have the body\"; writ commanding jailer to produce prisoner before court; protects against unlawful detention; English origin traced to Magna Carta; formalised in 1679 Act."
def "law:concept:due_process" "Legal proceedings must respect established rules and individual rights; substantive dimension (what rights) and procedural dimension (fair hearing, notice, impartial tribunal); US 5th/14th Amendment."
def "law:concept:presumption_of_innocence" "Accused person presumed innocent until proven guilty beyond reasonable doubt; prosecution bears entire burden of proof; fundamental to adversarial criminal trial; Coffin v. US (1895) classically stated."
def "law:concept:burden_of_proof" "Obligation resting on a party to prove a factual claim to a required standard; civil: balance of probabilities; criminal: beyond reasonable doubt; evidential vs. legal burden distinguished."
def "law:concept:res_judicata" "\"The matter has been judged\"; final judgment on the merits bars re-litigation of same cause of action between same parties; prevents endless re-opening of settled disputes; Roman origin."
def "law:concept:stare_decisis" "\"Stand by what has been decided\"; doctrine of binding precedent in common law systems; lower courts bound by ratio decidendi of higher courts on same point; creates predictability."
def "law:concept:ratio_decidendi" "\"Reason for the decision\"; the legal rule or principle the court applied to reach its conclusion; binding element of a precedent; must be identified against obiter dicta."
def "law:concept:obiter_dictum" "\"Said in passing\"; judicial remarks not essential to the decision reached; persuasive authority in common law but not binding; can be highly influential in later development."
def "law:concept:appeal" "Right to challenge a lower court decision before a higher tribunal; may be on law only, on law and fact, or de novo; not universally guaranteed in all traditions."
def "law:concept:adversarial_system" "Opposing parties present their evidence and argument to a passive, neutral judge or jury; common law tradition; truth-finding by contest; contrasted with inquisitorial system."
def "law:concept:inquisitorial_system" "Judge actively investigates the facts; dominant in civil law tradition (France, Germany); judge may call witnesses independently; less party control over evidence presentation."
def "law:concept:trial_by_jury" "Lay peers determine questions of fact; judge applies law to facts so found; English origin; 12th-century Assize of Clarendon; cornerstone of common law criminal procedure."
def "law:concept:trial_by_ordeal" "Divine judgment through physical test (fire, water, hot iron); God revealed guilt or innocence through survival or injury; medieval; abolished in England after Lateran IV (1215)."
def "law:concept:wager_of_battle" "Trial by combat; truth determined by outcome of champion duel; introduced to England by Normans 1066; technically unrepealed in England until 1819 (Thornton v. Ashford)."
def "law:concept:compurgation" "Oath-helping; accused cleared by marshalling required number of oath-swearers (compurgators) to swear to his innocence; Germanic and Anglo-Saxon; survived in canon law courts."
def "law:concept:locus_standi" "Standing; the right of a party to bring a claim before a court; must demonstrate sufficient legal interest in the outcome; prevents actio popularis in most common law systems."
def "law:concept:statute_of_limitations" "Time limit on bringing legal claims (prescription); varying by offence and jurisdiction; reflects interests in evidence freshness, certainty, and repose; Roman praescriptio temporis."

ln law:concept:habeas_corpus law:procedure sys:part_of
ln law:concept:due_process law:procedure sys:part_of
ln law:concept:presumption_of_innocence law:procedure sys:part_of
ln law:concept:burden_of_proof law:procedure sys:part_of
ln law:concept:res_judicata law:procedure sys:part_of
ln law:concept:stare_decisis law:procedure sys:part_of
ln law:concept:ratio_decidendi law:procedure sys:part_of
ln law:concept:obiter_dictum law:procedure sys:part_of
ln law:concept:appeal law:procedure sys:part_of
ln law:concept:adversarial_system law:procedure sys:part_of
ln law:concept:inquisitorial_system law:procedure sys:part_of
ln law:concept:trial_by_jury law:procedure sys:part_of
ln law:concept:trial_by_ordeal law:procedure sys:part_of
ln law:concept:wager_of_battle law:procedure sys:part_of
ln law:concept:compurgation law:procedure sys:part_of
ln law:concept:locus_standi law:procedure sys:part_of
ln law:concept:statute_of_limitations law:procedure sys:part_of

ln law:concept:ratio_decidendi law:concept:stare_decisis sys:part_of
ln law:concept:obiter_dictum law:concept:stare_decisis law:contrasts_with
ln law:concept:adversarial_system law:concept:inquisitorial_system law:contrasts_with
ln law:concept:trial_by_jury law:concept:trial_by_ordeal law:contrasts_with
ln law:concept:trial_by_ordeal law:concept:compurgation law:contrasts_with
ln law:concept:trial_by_ordeal law:concept:wager_of_battle law:contrasts_with
ln law:concept:stare_decisis law:tradition:english_common_law law:codified_in
ln law:concept:adversarial_system law:tradition:english_common_law sys:part_of
ln law:concept:inquisitorial_system law:tradition:civil_law_tradition sys:part_of

set.add name="ontology.legal_concepts" id="law:concept:habeas_corpus"
set.add name="ontology.legal_concepts" id="law:concept:due_process"
set.add name="ontology.legal_concepts" id="law:concept:presumption_of_innocence"
set.add name="ontology.legal_concepts" id="law:concept:burden_of_proof"
set.add name="ontology.legal_concepts" id="law:concept:res_judicata"
set.add name="ontology.legal_concepts" id="law:concept:stare_decisis"
set.add name="ontology.legal_concepts" id="law:concept:ratio_decidendi"
set.add name="ontology.legal_concepts" id="law:concept:obiter_dictum"
set.add name="ontology.legal_concepts" id="law:concept:appeal"
set.add name="ontology.legal_concepts" id="law:concept:adversarial_system"
set.add name="ontology.legal_concepts" id="law:concept:inquisitorial_system"
set.add name="ontology.legal_concepts" id="law:concept:trial_by_jury"
set.add name="ontology.legal_concepts" id="law:concept:trial_by_ordeal"
set.add name="ontology.legal_concepts" id="law:concept:wager_of_battle"
set.add name="ontology.legal_concepts" id="law:concept:compurgation"
set.add name="ontology.legal_concepts" id="law:concept:locus_standi"
set.add name="ontology.legal_concepts" id="law:concept:statute_of_limitations"

# ── Substantive doctrines ─────────────────────────────────────────────────────

def "law:concept:lex_talionis" "Law of retaliation; eye for an eye, tooth for a tooth; proportional punishment exactly matching the injury; Hammurabi Code; Exodus 21:24; talion principle across Near Eastern and biblical law."
def "law:concept:wergild" "Germanic blood money; monetary compensation for killing or serious injury paid to victim's kin; scaled by victim's social rank; avoided blood feud; Salic Law, Anglo-Saxon dooms, Norse law."
def "law:concept:diya" "Islamic blood money; monetary compensation for homicide or bodily injury; alternative to qisas (retaliation) or pardon; tariffs set by Hanafi school; victim or heirs may choose remedy."
def "law:concept:qisas" "Islamic law of retaliation; victim or heirs may demand equal punishment inflicted on perpetrator; or accept diya instead; or pardon freely; operates in intentional homicide and battery."
def "law:concept:mens_rea" "\"Guilty mind\"; mental element required for criminal liability; intention, recklessness, and negligence distinguished; Roman dolus (fraud) and culpa (fault); no crime without guilty mind."
def "law:concept:actus_reus" "\"Guilty act\"; physical conduct element of crime; voluntary act or punishable omission; both mens rea and actus reus must concur for criminal conviction in common law."
def "law:concept:legal_fiction" "Treats something known to be false as true for legal purposes; corporation as person; Blackstone: an assumption which conceals a legal change; Roman law device adapted widely."
def "law:concept:legal_personhood" "Capacity to hold rights and bear legal duties; natural persons plus juristic persons (corporations, states, temples historically); basis of standing and contractual capacity."
def "law:concept:equity" "Conscience-based relief beyond strict common law; Court of Chancery; trust, injunction, specific performance, rescission; maxims: equity follows the law; he who comes in equity must come with clean hands."
def "law:concept:trust" "Equitable obligation: trustee holds legal title to property for the benefit of beneficiaries; English creation without Roman/civil law equivalent; basis of pension funds, charities, and estate planning."
def "law:concept:contract" "Agreement creating legally enforceable obligations; Roman stipulatio; elements: offer, acceptance, consideration (common law) or causa (civil law); breach entitles innocent party to damages."
def "law:concept:tort" "Civil wrong causing harm and entitling the victim to damages; common law term; Roman delictum; negligence, trespass, nuisance, defamation are major categories; contrasted with crime."
def "law:concept:property_rights" "Legal rights to own, use, derive fruits from, exclude others from, and alienate things; Locke: property arises from mixing labour with nature; Roman dominium as paradigm."
def "law:concept:sovereignty" "Supreme legal authority over a territory and its population; Bodin (1576): indivisible and perpetual; Westphalia (1648): state sovereignty and non-interference; parliamentary sovereignty in UK."
def "law:concept:force_majeure" "Superior force; unforeseeable event entirely beyond a party's control excusing non-performance of contractual obligation; vis maior in Roman law; earthquake, war, plague as classic examples."
def "law:concept:jus_cogens" "Peremptory norms of international law; non-derogable rules binding all states regardless of consent; prohibition on genocide, slavery, torture, and aggressive war; Vienna Convention Art.53."
def "law:concept:comity" "Mutual recognition and enforcement of foreign laws and judgments between legal systems; courtesy principle among sovereign states; not legally compelled; Hilton v. Guyot (1895)."
def "law:concept:lex_mercatoria_concept" "Law merchant as legal concept; medieval customary commercial law; bill of exchange, bottomry loan, insurance, partnership; fairs of Champagne; absorbed into national law 17th-19th century."
def "law:concept:prescription" "Acquisition of rights or extinguishment of claims by passage of time; usucaption in Roman law (ownership by long possession); statute of limitations in criminal law; varies by jurisdiction."
def "law:concept:fiction_of_continuity" "Legal fiction that judges find rather than make law; declaratory theory of common law; conceals judicial law-making; Blackstone's ideology; contrasted with the legislative model."

ln law:concept:lex_talionis law:doctrine sys:part_of
ln law:concept:wergild law:doctrine sys:part_of
ln law:concept:diya law:doctrine sys:part_of
ln law:concept:qisas law:doctrine sys:part_of
ln law:concept:mens_rea law:doctrine sys:part_of
ln law:concept:actus_reus law:doctrine sys:part_of
ln law:concept:legal_fiction law:doctrine sys:part_of
ln law:concept:legal_personhood law:doctrine sys:part_of
ln law:concept:equity law:doctrine sys:part_of
ln law:concept:trust law:doctrine sys:part_of
ln law:concept:contract law:doctrine sys:part_of
ln law:concept:tort law:doctrine sys:part_of
ln law:concept:property_rights law:doctrine sys:part_of
ln law:concept:sovereignty law:doctrine sys:part_of
ln law:concept:force_majeure law:doctrine sys:part_of
ln law:concept:jus_cogens law:doctrine sys:part_of
ln law:concept:comity law:doctrine sys:part_of
ln law:concept:lex_mercatoria_concept law:doctrine sys:part_of
ln law:concept:prescription law:doctrine sys:part_of
ln law:concept:fiction_of_continuity law:doctrine sys:part_of

ln law:concept:lex_talionis law:concept:wergild law:contrasts_with
ln law:concept:wergild law:concept:diya law:influenced_by
ln law:concept:qisas law:concept:diya law:contrasts_with
ln law:concept:qisas law:concept:lex_talionis law:influenced_by
ln law:concept:mens_rea law:concept:actus_reus sys:part_of
ln law:concept:trust law:concept:equity law:derived_from
ln law:concept:equity law:tradition:english_common_law sys:part_of
ln law:concept:lex_mercatoria_concept law:tradition:lex_mercatoria sys:part_of
ln law:concept:statute_of_limitations law:concept:prescription law:derived_from
ln law:concept:sovereignty law:code:peace_of_westphalia law:codified_in

set.add name="ontology.legal_concepts" id="law:concept:lex_talionis"
set.add name="ontology.legal_concepts" id="law:concept:wergild"
set.add name="ontology.legal_concepts" id="law:concept:diya"
set.add name="ontology.legal_concepts" id="law:concept:qisas"
set.add name="ontology.legal_concepts" id="law:concept:mens_rea"
set.add name="ontology.legal_concepts" id="law:concept:actus_reus"
set.add name="ontology.legal_concepts" id="law:concept:legal_fiction"
set.add name="ontology.legal_concepts" id="law:concept:legal_personhood"
set.add name="ontology.legal_concepts" id="law:concept:equity"
set.add name="ontology.legal_concepts" id="law:concept:trust"
set.add name="ontology.legal_concepts" id="law:concept:contract"
set.add name="ontology.legal_concepts" id="law:concept:tort"
set.add name="ontology.legal_concepts" id="law:concept:property_rights"
set.add name="ontology.legal_concepts" id="law:concept:sovereignty"
set.add name="ontology.legal_concepts" id="law:concept:force_majeure"
set.add name="ontology.legal_concepts" id="law:concept:jus_cogens"
set.add name="ontology.legal_concepts" id="law:concept:comity"
set.add name="ontology.legal_concepts" id="law:concept:lex_mercatoria_concept"
set.add name="ontology.legal_concepts" id="law:concept:prescription"
set.add name="ontology.legal_concepts" id="law:concept:fiction_of_continuity"

# ── Roman law concepts ────────────────────────────────────────────────────────

def "law:concept:ius_civile" "Roman law applicable only to Roman citizens; original body of Roman law developed from Twelve Tables; contrasted with ius gentium; administered by pontiffs then praetors."
def "law:concept:ius_gentium" "\"Law of peoples\"; Roman law governing non-citizens and international commerce; derived from common human reason; bridge between ius civile and ius naturale."
def "law:concept:ius_naturale" "Natural law; universal law applicable to all humans and animals; derived from nature; Ulpian's definition; basis of Stoic and later Enlightenment natural rights theory."
def "law:concept:actio" "Roman law action; specific procedural form through which plaintiff initiated suit before praetor; formulary system; actiones in personam (against person) vs. in rem (against thing)."
def "law:concept:stipulatio" "Roman verbal contract; formal oral exchange: \"Do you solemnly promise?\" — \"I do\"; strict formalism; could serve novation, guarantee, or any obligation; abolished by Justinian."
def "law:concept:dominium" "Roman full ownership; exclusive right to use (usus), enjoy fruits of (fructus), and dispose of (abusus) a thing; contrasted with mere possession (possessio) and lesser real rights."

al law:concept:ius_civile law:latin:ius_civile
al law:concept:ius_gentium law:latin:ius_gentium
al law:concept:ius_naturale law:latin:ius_naturale
al law:concept:actio law:latin:actio
al law:concept:stipulatio law:latin:stipulatio
al law:concept:dominium law:latin:dominium

ln law:concept:ius_civile law:doctrine sys:part_of
ln law:concept:ius_gentium law:doctrine sys:part_of
ln law:concept:ius_naturale law:doctrine sys:part_of
ln law:concept:actio law:procedure sys:part_of
ln law:concept:stipulatio law:doctrine sys:part_of
ln law:concept:dominium law:doctrine sys:part_of

ln law:concept:ius_civile law:tradition:roman_law sys:part_of
ln law:concept:ius_gentium law:tradition:roman_law sys:part_of
ln law:concept:ius_naturale law:tradition:roman_law sys:part_of
ln law:concept:actio law:tradition:roman_law sys:part_of
ln law:concept:stipulatio law:tradition:roman_law sys:part_of
ln law:concept:dominium law:tradition:roman_law sys:part_of

ln law:concept:ius_civile law:concept:ius_gentium law:contrasts_with
ln law:concept:ius_gentium law:concept:ius_naturale law:influenced_by
ln law:concept:dominium law:concept:property_rights law:source_of
ln law:concept:actio law:concept:locus_standi law:influenced_by
ln law:concept:stipulatio law:concept:contract law:source_of

set.add name="ontology.legal_concepts" id="law:concept:ius_civile"
set.add name="ontology.legal_concepts" id="law:concept:ius_gentium"
set.add name="ontology.legal_concepts" id="law:concept:ius_naturale"
set.add name="ontology.legal_concepts" id="law:concept:actio"
set.add name="ontology.legal_concepts" id="law:concept:stipulatio"
set.add name="ontology.legal_concepts" id="law:concept:dominium"

# ── Legal philosophy concepts ─────────────────────────────────────────────────

def "law:concept:natural_law" "Law derived from nature, reason, or divine order; Aquinas: participation of eternal law in rational creatures; Grotius: binding even if God did not exist; Locke: natural rights precede state."
def "law:concept:positive_law" "Law as human enactment; Bentham and Austin: law = command of sovereign backed by sanction; Hart: rule of recognition; separates legal obligation from moral obligation."
def "law:concept:customary_law" "Law arising from long-established community practice accepted as legally binding; lex non scripta; opinio juris et necessitatis; foundational in pre-literate societies and international law."
def "law:concept:social_contract" "Political authority derives from consent of the governed; Hobbes (Leviathan 1651): surrender natural freedom for security; Locke (1689): limited government; Rousseau (1762): general will."
def "law:concept:rule_of_law" "Government and citizens subject to law, not arbitrary power; Aristotle: rule of law over men; Dicey (1885): equality before law, no punishment without breach; fundamental constitutional ideal."
def "law:concept:separation_of_powers" "Montesquieu (L'Esprit des Lois, 1748): legislative, executive, and judicial powers must be held separately; corruption follows their combination; US Constitution canonical implementation."
def "law:concept:judicial_review" "Courts review constitutionality of legislative and executive acts; Marbury v. Madison (1803, USA, Marshall CJ); not universal — absent in pure parliamentary sovereignty systems."
def "law:concept:grundnorm" "Kelsen's basic norm; presupposed foundation of the entire positive legal order; not itself a positive law; validates all norms in the hierarchy; pure theory of law without moral content."

ln law:concept:natural_law law:philosophy sys:part_of
ln law:concept:positive_law law:philosophy sys:part_of
ln law:concept:customary_law law:philosophy sys:part_of
ln law:concept:social_contract law:philosophy sys:part_of
ln law:concept:rule_of_law law:philosophy sys:part_of
ln law:concept:separation_of_powers law:philosophy sys:part_of
ln law:concept:judicial_review law:philosophy sys:part_of
ln law:concept:grundnorm law:philosophy sys:part_of

ln law:concept:natural_law law:concept:positive_law law:contrasts_with
ln law:concept:positive_law law:tradition:legal_positivism sys:part_of
ln law:concept:natural_law law:tradition:natural_law_school sys:part_of
ln law:concept:customary_law law:concept:positive_law law:contrasts_with
ln law:concept:social_contract law:concept:sovereignty law:influenced_by
ln law:concept:rule_of_law law:concept:separation_of_powers law:influenced_by
ln law:concept:grundnorm law:concept:positive_law sys:part_of
ln law:concept:judicial_review law:code:us_constitution law:codified_in

set.add name="ontology.legal_concepts" id="law:concept:natural_law"
set.add name="ontology.legal_concepts" id="law:concept:positive_law"
set.add name="ontology.legal_concepts" id="law:concept:customary_law"
set.add name="ontology.legal_concepts" id="law:concept:social_contract"
set.add name="ontology.legal_concepts" id="law:concept:rule_of_law"
set.add name="ontology.legal_concepts" id="law:concept:separation_of_powers"
set.add name="ontology.legal_concepts" id="law:concept:judicial_review"
set.add name="ontology.legal_concepts" id="law:concept:grundnorm"

# ── Islamic jurisprudential concepts ─────────────────────────────────────────

def "law:concept:usul_al_fiqh" "Roots of Islamic jurisprudence; theory of legal sources and their application; al-Shafi'i's Risala (c.820) first systematic account; Quran, Sunna, ijma, and qiyas as four roots."
def "law:concept:ijma" "Consensus of qualified Islamic scholars; third source of fiqh after Quran and Sunna; once established cannot be contradicted; Sunni scholars debate whose consensus counts."
def "law:concept:qiyas" "Analogical reasoning in Islamic law; extending an existing ruling to a new case sharing the same effective cause (illa); fourth source of fiqh; developed by al-Shafi'i systematically."
def "law:concept:ijtihad" "Independent legal reasoning; qualified jurist's personal effort to derive a ruling from primary sources where no clear text exists; \"door of ijtihad\" debate in classical and modern periods."
def "law:concept:fatwa" "Legal opinion issued by a qualified Islamic scholar (mufti); non-binding on individuals though carrying authority; differs from a court ruling (qada); issued in response to specific question."
def "law:concept:hudud" "Fixed punishments prescribed in Quran for specific offences; theft, adultery (zina), defamation (qadhf); strict evidentiary requirements make conviction rare in classical practice."
def "law:concept:tazir" "Discretionary punishment for offences lacking fixed Quranic penalty; judge determines appropriate sanction; forms the majority of Islamic criminal law in practice."
def "law:concept:maslaha" "Public interest as legal consideration; used to develop new rulings where no explicit text applies; particularly prominent in Maliki school; al-Ghazali and al-Tufi theorised its limits."

al law:concept:usul_al_fiqh law:arabic:usul_al_fiqh
al law:concept:ijma law:arabic:ijma
al law:concept:qiyas law:arabic:qiyas
al law:concept:ijtihad law:arabic:ijtihad
al law:concept:fatwa law:arabic:fatwa
al law:concept:hudud law:arabic:hudud
al law:concept:tazir law:arabic:tazir
al law:concept:maslaha law:arabic:maslaha

ln law:concept:usul_al_fiqh law:doctrine sys:part_of
ln law:concept:ijma law:doctrine sys:part_of
ln law:concept:qiyas law:doctrine sys:part_of
ln law:concept:ijtihad law:doctrine sys:part_of
ln law:concept:fatwa law:doctrine sys:part_of
ln law:concept:hudud law:doctrine sys:part_of
ln law:concept:tazir law:doctrine sys:part_of
ln law:concept:maslaha law:doctrine sys:part_of

ln law:concept:usul_al_fiqh law:tradition:fiqh sys:part_of
ln law:concept:ijma law:concept:usul_al_fiqh sys:part_of
ln law:concept:qiyas law:concept:usul_al_fiqh sys:part_of
ln law:concept:ijtihad law:concept:usul_al_fiqh sys:part_of
ln law:concept:fatwa law:concept:ijtihad law:derived_from
ln law:concept:hudud law:tradition:sharia sys:part_of
ln law:concept:tazir law:tradition:sharia sys:part_of
ln law:concept:hudud law:concept:tazir law:contrasts_with
ln law:concept:maslaha law:tradition:maliki_school sys:part_of
ln law:concept:diya law:concept:hudud sys:part_of
ln law:concept:qisas law:concept:hudud sys:part_of

set.add name="ontology.legal_concepts" id="law:concept:usul_al_fiqh"
set.add name="ontology.legal_concepts" id="law:concept:ijma"
set.add name="ontology.legal_concepts" id="law:concept:qiyas"
set.add name="ontology.legal_concepts" id="law:concept:ijtihad"
set.add name="ontology.legal_concepts" id="law:concept:fatwa"
set.add name="ontology.legal_concepts" id="law:concept:hudud"
set.add name="ontology.legal_concepts" id="law:concept:tazir"
set.add name="ontology.legal_concepts" id="law:concept:maslaha"

# ── Jewish legal concepts ─────────────────────────────────────────────────────

def "law:concept:halakha_concept" "Jewish law (halakha) as concept; \"the way to walk\"; encompasses all aspects of Jewish life from ritual to commerce; rabbinic development of Torah commandments through Talmud."
def "law:concept:responsa" "Teshuvot; written rabbinical rulings on specific legal questions submitted to authorities; from Geonic period (7th century) to present; functions as ongoing case law within halakha."
def "law:concept:takkanah" "Rabbinic enactment; new law promulgated by rabbinic authority beyond what Torah explicitly requires; distinguished from gezerah (protective fence) and minhag (custom)."
def "law:concept:dina_demalkhuta_dina" "\"The law of the land is the law\"; principle that secular state law is binding on Jews in civil matters; attributed to Shmuel of Nehardea (3rd century CE); limits scope of halakha."

al law:concept:halakha_concept law:hebrew:halakha
al law:concept:responsa law:hebrew:teshuvot
al law:concept:takkanah law:hebrew:takkanah
al law:concept:dina_demalkhuta_dina law:aramaic:dina_demalkhuta_dina

ln law:concept:halakha_concept law:doctrine sys:part_of
ln law:concept:responsa law:doctrine sys:part_of
ln law:concept:takkanah law:doctrine sys:part_of
ln law:concept:dina_demalkhuta_dina law:doctrine sys:part_of

ln law:concept:halakha_concept law:tradition:halakha sys:part_of
ln law:concept:responsa law:tradition:responsa_literature sys:part_of
ln law:concept:responsa law:concept:halakha_concept sys:part_of
ln law:concept:takkanah law:concept:halakha_concept sys:part_of
ln law:concept:dina_demalkhuta_dina law:concept:customary_law law:influenced_by

set.add name="ontology.legal_concepts" id="law:concept:halakha_concept"
set.add name="ontology.legal_concepts" id="law:concept:responsa"
set.add name="ontology.legal_concepts" id="law:concept:takkanah"
set.add name="ontology.legal_concepts" id="law:concept:dina_demalkhuta_dina"
