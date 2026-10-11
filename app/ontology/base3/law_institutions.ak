# Akasha ontology — law as institution: the formal face of the norm.
# The existing law: layer is rich in jurisprudence, legal history and comparative
# traditions (law:concept/tradition/code). This adds the everyday INSTITUTIONAL
# machinery — branches, institutions, process, actors, sources, sanctions — and
# frames law as codified, enforceable norms, bridging socio:norm. Base pack.

def "law:law" "Law — the body of codified, enforceable norms backed by the state (法)."
ln law:law socio:norm thesaurus:related
ln law:law socio:social_institution thesaurus:related
ln law:law socio:social_control thesaurus:related
ln law:law law:concept:rule_of_law thesaurus:related
ln law:law civ:responsibility thesaurus:related

# ── branches of law ──
def "law:branch:criminal_law" "Law defining offences against the public and their punishment (刑法)."
ln law:branch:criminal_law law:law thesaurus:related
ln law:branch:criminal_law socio:deviance thesaurus:related
ln law:branch:criminal_law gov:service:police thesaurus:related
ln law:branch:criminal_law law:concept:mens_rea thesaurus:related
ln law:branch:criminal_law law:concept:actus_reus thesaurus:related
def "law:branch:civil_law_branch" "Law governing disputes and obligations between private parties (民事法)."
ln law:branch:civil_law_branch law:law thesaurus:related
ln law:branch:civil_law_branch law:concept:tort thesaurus:related
ln law:branch:civil_law_branch law:tradition:civil_law_tradition thesaurus:related
def "law:branch:constitutional_law" "Law of the state's basic structure and fundamental rights (憲法)."
ln law:branch:constitutional_law law:law thesaurus:related
ln law:branch:constitutional_law admin:country thesaurus:related
ln law:branch:constitutional_law law:concept:separation_of_powers thesaurus:related
def "law:branch:administrative_law" "Law governing the actions of public agencies (行政法)."
ln law:branch:administrative_law law:law thesaurus:related
ln law:branch:administrative_law gov:function:public_works thesaurus:related
ln law:branch:administrative_law admin:municipality thesaurus:related
def "law:branch:contract_law" "Law of enforceable agreements (契約法)."
ln law:branch:contract_law law:law thesaurus:related
ln law:branch:contract_law biz:contract thesaurus:related
ln law:branch:contract_law fin:corporate_finance thesaurus:related
ln law:branch:contract_law law:concept:stipulatio thesaurus:related
def "law:branch:tort_law" "Law of civil wrongs and compensation for harm (不法行為法)."
ln law:branch:tort_law law:law thesaurus:related
def "law:branch:property_law" "Law of ownership and rights in things (物権法/財産法)."
ln law:branch:property_law law:law thesaurus:related
ln law:branch:property_law acct:asset thesaurus:related
ln law:branch:property_law home:dwelling:detached_house thesaurus:related
ln law:branch:property_law law:concept:property_rights thesaurus:related
def "law:branch:family_law" "Law of marriage, kinship, custody and inheritance (家族法)."
ln law:branch:family_law law:law thesaurus:related
ln law:branch:family_law kin:parent_of thesaurus:related
ln law:branch:family_law kin:partner_of thesaurus:related
def "law:branch:labor_law" "Law of employment, wages and workplace rights (労働法)."
ln law:branch:labor_law law:law thesaurus:related
ln law:branch:labor_law work:overtime thesaurus:related
ln law:branch:labor_law work:minimum_wage thesaurus:related
ln law:branch:labor_law work:paid_leave thesaurus:related
def "law:branch:tax_law" "Law governing taxation (税法)."
ln law:branch:tax_law law:law thesaurus:related
ln law:branch:tax_law gov:tax thesaurus:related
ln law:branch:tax_law acct:tax_accounting thesaurus:related
def "law:branch:intellectual_property" "Law of rights in creations — copyright, patent, trademark (知的財産法)."
ln law:branch:intellectual_property law:law thesaurus:related
ln law:branch:intellectual_property pub:paper thesaurus:related
ln law:branch:intellectual_property academia thesaurus:related
ln law:branch:intellectual_property cite:cites thesaurus:related
def "law:branch:international_law" "Law governing relations between states (国際法)."
ln law:branch:international_law law:law thesaurus:related
ln law:branch:international_law fx:foreign_exchange thesaurus:related
ln law:branch:international_law law:concept:ius_gentium thesaurus:related
def "law:branch:commercial_law" "Law of trade, companies and finance (商法)."
ln law:branch:commercial_law law:law thesaurus:related
ln law:branch:commercial_law fin:stock thesaurus:related
ln law:branch:commercial_law econ:market thesaurus:related
def "law:branch:environmental_law" "Law protecting the environment (環境法)."
ln law:branch:environmental_law law:law thesaurus:related
ln law:branch:environmental_law foodsustain:carbon_footprint_food thesaurus:related
ln law:branch:environmental_law econ:externality thesaurus:related
# ── legal institutions ──
def "law:institution:court" "A tribunal that hears and decides legal cases (裁判所)."
ln law:institution:court law:law thesaurus:related
ln law:institution:court occupation:judge thesaurus:related
ln law:institution:court occupation:lawyer thesaurus:related
def "law:institution:supreme_court" "The highest court, final on questions of law (最高裁)."
ln law:institution:supreme_court law:law thesaurus:related
ln law:institution:supreme_court law:concept:judicial_review thesaurus:related
def "law:institution:trial_court" "The court of first instance where cases are heard."
ln law:institution:trial_court law:law thesaurus:related
def "law:institution:appellate_court" "A court reviewing decisions of lower courts (控訴審)."
ln law:institution:appellate_court law:law thesaurus:related
def "law:institution:legislature" "The body that makes law (議会/立法府)."
ln law:institution:legislature law:law thesaurus:related
ln law:institution:legislature admin:country thesaurus:related
ln law:institution:legislature occupation:official thesaurus:related
ln law:institution:legislature law:concept:separation_of_powers thesaurus:related
def "law:institution:judiciary" "The system of courts and judges (司法)."
ln law:institution:judiciary law:law thesaurus:related
ln law:institution:judiciary law:concept:judicial_review thesaurus:related
ln law:institution:judiciary occupation:judge thesaurus:related
def "law:institution:jury" "Citizens who decide questions of fact at trial (陪審)."
ln law:institution:jury law:law thesaurus:related
ln law:institution:jury law:concept:trial_by_jury thesaurus:related
def "law:institution:prosecution_service" "The public body that brings criminal charges (検察)."
ln law:institution:prosecution_service law:law thesaurus:related
# ── legal process ──
def "law:process:legislation" "The making of statutes by a legislature (立法)."
ln law:process:legislation law:law thesaurus:related
ln law:process:legislation law:source:statute thesaurus:related
ln law:process:legislation admin:country thesaurus:related
def "law:process:litigation" "The process of resolving a dispute through the courts (訴訟)."
ln law:process:litigation law:law thesaurus:related
def "law:process:lawsuit" "A civil action brought before a court."
ln law:process:lawsuit law:law thesaurus:related
def "law:process:trial" "The formal examination of a case before a court (裁判/公判)."
ln law:process:trial law:law thesaurus:related
ln law:process:trial law:concept:due_process thesaurus:related
ln law:process:trial law:concept:burden_of_proof thesaurus:related
def "law:process:hearing" "A proceeding at which parties are heard."
ln law:process:hearing law:law thesaurus:related
ln law:process:hearing civ:public_hearing thesaurus:related
def "law:process:verdict" "The decision of a jury or court on the facts (評決)."
ln law:process:verdict law:law thesaurus:related
def "law:process:judgment" "The court's final decision (判決)."
ln law:process:judgment law:law thesaurus:related
def "law:process:appeal" "A request to a higher court to review a decision (控訴/上告)."
ln law:process:appeal law:law thesaurus:related
ln law:process:appeal law:concept:appeal thesaurus:related
def "law:process:sentencing" "Imposing a penalty after conviction (量刑)."
ln law:process:sentencing law:law thesaurus:related
def "law:process:arrest" "Taking a suspect into custody (逮捕)."
ln law:process:arrest law:law thesaurus:related
ln law:process:arrest gov:service:police thesaurus:related
def "law:process:prosecution" "Bringing and conducting criminal charges (起訴)."
ln law:process:prosecution law:law thesaurus:related
ln law:process:prosecution law:institution:prosecution_service thesaurus:related
def "law:process:plea" "A defendant's formal answer to a charge (答弁)."
ln law:process:plea law:law thesaurus:related
def "law:process:settlement" "Resolving a dispute by agreement without judgment (和解)."
ln law:process:settlement law:law thesaurus:related
ln law:process:settlement law:branch:civil_law_branch thesaurus:related
def "law:process:arbitration" "Private binding dispute resolution by a chosen arbitrator (仲裁)."
ln law:process:arbitration law:law thesaurus:related
ln law:process:arbitration law:branch:commercial_law thesaurus:related
def "law:process:mediation" "Facilitated negotiation toward a voluntary agreement (調停)."
ln law:process:mediation law:law thesaurus:related
ln law:process:mediation civ:facilitation thesaurus:related
# ── legal actors ──
def "law:actor:legislator" "A member of a law-making body (議員)."
ln law:actor:legislator law:law thesaurus:related
ln law:actor:legislator occupation:official thesaurus:related
ln law:actor:legislator law:institution:legislature thesaurus:related
def "law:actor:prosecutor" "The lawyer who conducts a criminal case for the state (検察官)."
ln law:actor:prosecutor law:law thesaurus:related
ln law:actor:prosecutor occupation:lawyer thesaurus:related
ln law:actor:prosecutor law:institution:prosecution_service thesaurus:related
def "law:actor:defendant" "The party accused or sued (被告)."
ln law:actor:defendant law:law thesaurus:related
ln law:actor:defendant law:process:trial thesaurus:related
def "law:actor:plaintiff" "The party who brings a civil suit (原告)."
ln law:actor:plaintiff law:law thesaurus:related
ln law:actor:plaintiff law:process:lawsuit thesaurus:related
def "law:actor:defense_attorney" "The lawyer representing the accused/defendant (弁護人)."
ln law:actor:defense_attorney law:law thesaurus:related
ln law:actor:defense_attorney occupation:lawyer thesaurus:related
def "law:actor:juror" "A member of a jury."
ln law:actor:juror law:law thesaurus:related
ln law:actor:juror law:institution:jury thesaurus:related
def "law:actor:witness" "One who gives evidence under oath (証人)."
ln law:actor:witness law:law thesaurus:related
def "law:actor:magistrate" "A minor judicial officer."
ln law:actor:magistrate law:law thesaurus:related
# ── sources of law ──
def "law:source:statute" "A written law enacted by a legislature (制定法/法律)."
ln law:source:statute law:law thesaurus:related
ln law:source:statute socio:norm thesaurus:related
ln law:source:statute law:law thesaurus:related
def "law:source:regulation" "A rule made by an agency under statutory authority (規則/政令)."
ln law:source:regulation law:law thesaurus:related
ln law:source:regulation gov:function:public_works thesaurus:related
ln law:source:regulation admin:country thesaurus:related
def "law:source:ordinance" "A law made by a local authority (条例)."
ln law:source:ordinance law:law thesaurus:related
ln law:source:ordinance admin:municipality thesaurus:related
def "law:source:case_law" "Law established by judicial decisions (判例法)."
ln law:source:case_law law:law thesaurus:related
ln law:source:case_law law:concept:ratio_decidendi thesaurus:related
ln law:source:case_law law:tradition:english_common_law thesaurus:related
def "law:source:precedent" "A prior decision that guides later ones (先例)."
ln law:source:precedent law:law thesaurus:related
ln law:source:precedent law:concept:stare_decisis thesaurus:related
def "law:source:constitution" "The supreme law defining the state (憲法典)."
ln law:source:constitution law:law thesaurus:related
ln law:source:constitution law:branch:constitutional_law thesaurus:related
ln law:source:constitution law:code:english_bill_of_rights thesaurus:related
def "law:source:treaty" "A binding agreement between states (条約)."
ln law:source:treaty law:law thesaurus:related
ln law:source:treaty admin:country thesaurus:related
ln law:source:treaty law:branch:international_law thesaurus:related
def "law:source:customary_law" "Law arising from long-established practice (慣習法)."
ln law:source:customary_law law:law thesaurus:related
ln law:source:customary_law law:concept:customary_law thesaurus:related
ln law:source:customary_law socio:folkways thesaurus:related
# ── sanctions & remedies ──
def "law:sanction:sanction" "A penalty enforcing a law or norm (制裁)."
ln law:sanction:sanction law:law thesaurus:related
ln law:sanction:sanction socio:social_control thesaurus:related
def "law:sanction:penalty" "A punishment for breaking a rule."
ln law:sanction:penalty law:law thesaurus:related
def "law:sanction:fine" "A monetary penalty (罰金)."
ln law:sanction:fine law:law thesaurus:related
ln law:sanction:fine fin:debt thesaurus:related
def "law:sanction:imprisonment" "Confinement as punishment (拘禁/懲役)."
ln law:sanction:imprisonment law:law thesaurus:related
ln law:sanction:imprisonment gov:service:police thesaurus:related
ln law:sanction:imprisonment socio:discipline thesaurus:related
def "law:sanction:damages" "Money awarded to compensate for a wrong (損害賠償)."
ln law:sanction:damages law:law thesaurus:related
ln law:sanction:damages fin:debt thesaurus:related
ln law:sanction:damages law:branch:tort_law thesaurus:related
def "law:sanction:injunction" "A court order to do or stop doing something (差止命令)."
ln law:sanction:injunction law:law thesaurus:related
def "law:sanction:probation" "Supervised liberty in place of imprisonment (保護観察)."
ln law:sanction:probation law:law thesaurus:related
def "law:sanction:restitution" "Restoring what was wrongly taken (原状回復)."
ln law:sanction:restitution law:law thesaurus:related
ln law:sanction:restitution law:concept:qisas thesaurus:related
