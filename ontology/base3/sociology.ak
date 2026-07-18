# Akasha ontology — sociology: a bird's-eye framing of the social.
# The theory layer over everything social already built — kin:/social:/community/
# group:/civ:/work:/status:/admin:/econ:/school:. Each concept bridges down to the
# concrete pieces it names, so the overview and the detail connect. Base pack.

def "socio" "Sociology — the study of society, social relations and institutions."
# ── foundations ──
def "socio:society" "An enduring community of people with shared institutions and culture (社会)."
ln socio:society socio thesaurus:related
def "socio:social_structure" "The patterned arrangements of relations and institutions that shape action (社会構造)."
ln socio:social_structure socio thesaurus:related
def "socio:social_institution" "A stable cluster of norms and roles organising a basic need (family, education, economy) (社会制度)."
ln socio:social_institution socio thesaurus:related
ln socio:social_institution kin:parent_of thesaurus:related
ln socio:social_institution school:university thesaurus:related
ln socio:social_institution econ:market thesaurus:related
ln socio:social_institution admin:municipality thesaurus:related
def "socio:culture" "The shared beliefs, values, symbols and practices of a group (文化)."
ln socio:culture socio thesaurus:related
def "socio:subculture" "A group with values distinct from the wider culture."
ln socio:subculture socio thesaurus:related
def "socio:norm" "A shared rule of expected behaviour (規範)."
ln socio:norm socio thesaurus:related
ln socio:norm org:norms thesaurus:related
ln socio:norm civ:responsibility thesaurus:related
def "socio:value" "A shared standard of what is good or desirable (価値)."
ln socio:value socio thesaurus:related
def "socio:folkways" "Everyday customs whose breach brings mild disapproval."
ln socio:folkways socio thesaurus:related
def "socio:mores" "Norms with strong moral weight whose breach brings serious sanction."
ln socio:mores socio thesaurus:related
def "socio:role" "The behaviour expected of a social position (役割)."
ln socio:role socio thesaurus:related
ln socio:role occupation:teacher thesaurus:related
ln socio:role kin:parent_of thesaurus:related
ln socio:role status:staff thesaurus:related
def "socio:social_status" "A recognised social position (地位)."
ln socio:social_status socio thesaurus:related
ln socio:social_status status:outranks thesaurus:related
ln socio:social_status acad:professor thesaurus:related
def "socio:identity" "The sense of who one is, formed in social interaction (アイデンティティ)."
ln socio:identity socio thesaurus:related
ln socio:identity phil:identity thesaurus:related
ln socio:identity foodstud:culinary_identity thesaurus:related
def "socio:socialization" "How individuals learn the norms and roles of their society (社会化)."
ln socio:socialization socio thesaurus:related
ln socio:socialization kin:parent_of thesaurus:related
ln socio:socialization school:teacher thesaurus:related
ln socio:socialization group:scouts thesaurus:related
# ── groups & networks ──
def "socio:social_group" "A set of people who interact and share identity (社会集団)."
ln socio:social_group socio thesaurus:related
def "socio:primary_group" "A small, intimate, enduring group — family, close friends (第一次集団)."
ln socio:primary_group socio thesaurus:related
ln socio:primary_group kin:parent_of thesaurus:related
ln socio:primary_group social:friend_of thesaurus:related
ln socio:primary_group social:childhood_friend_of thesaurus:related
def "socio:secondary_group" "A larger, impersonal, goal-oriented group — a workplace, an association."
ln socio:secondary_group socio thesaurus:related
ln socio:secondary_group group:pta thesaurus:related
ln socio:secondary_group work:department thesaurus:related
ln socio:secondary_group social:colleague_of thesaurus:related
def "socio:in_group" "A group one belongs to and identifies with."
ln socio:in_group socio thesaurus:related
def "socio:out_group" "A group one is outside of or set against."
ln socio:out_group socio thesaurus:related
def "socio:reference_group" "A group one measures oneself against."
ln socio:reference_group socio thesaurus:related
ln socio:reference_group social:senior_of thesaurus:related
def "socio:social_network" "The web of ties linking people — the object of network analysis (社会的ネットワーク)."
ln socio:social_network socio thesaurus:related
ln socio:social_network dh:social_network_analysis thesaurus:related
ln socio:social_network collab:coauthorship_network thesaurus:related
ln socio:social_network sys:network thesaurus:related
def "socio:gemeinschaft" "Community bound by kinship and place (Tönnies)."
ln socio:gemeinschaft socio thesaurus:related
ln socio:gemeinschaft concept:community thesaurus:related
ln socio:gemeinschaft concept:neighborhood thesaurus:related
def "socio:gesellschaft" "Society bound by impersonal, contractual ties (Tönnies)."
ln socio:gesellschaft socio thesaurus:related
ln socio:gesellschaft econ:market thesaurus:related
ln socio:gesellschaft admin:country thesaurus:related
# ── stratification & power ──
def "socio:social_stratification" "The structured ranking of groups into layers (社会階層)."
ln socio:social_stratification socio thesaurus:related
ln socio:social_stratification status:outranks thesaurus:related
ln socio:social_stratification acad:outranks thesaurus:related
def "socio:social_class" "A stratum defined by economic position (階級)."
ln socio:social_class socio thesaurus:related
ln socio:social_class fin:capital thesaurus:related
def "socio:caste" "A closed, hereditary stratum."
ln socio:caste socio thesaurus:related
def "socio:social_mobility" "Movement between social positions, up or down (社会移動)."
ln socio:social_mobility socio thesaurus:related
ln socio:social_mobility work:promotion thesaurus:related
ln socio:social_mobility acad:outranks thesaurus:related
def "socio:inequality" "The uneven distribution of resources, power and status (不平等)."
ln socio:inequality socio thesaurus:related
ln socio:inequality gov:benefit:public_assistance thesaurus:related
def "socio:power" "The capacity to achieve one's will despite resistance (権力)."
ln socio:power socio thesaurus:related
ln socio:power social:boss_of thesaurus:related
ln socio:power work:power_harassment thesaurus:related
def "socio:authority" "Power seen as legitimate (規範的に正当な権力)."
ln socio:authority socio thesaurus:related
ln socio:authority admin:municipality thesaurus:related
ln socio:authority social:leader_of thesaurus:related
ln socio:authority occupation:mayor thesaurus:related
def "socio:legitimacy" "The accepted right to exercise power."
ln socio:legitimacy socio thesaurus:related
def "socio:elite" "A small group holding disproportionate power or wealth."
ln socio:elite socio thesaurus:related
# ── social change & collective life ──
def "socio:social_interaction" "The mutual influence of people acting toward one another (社会的相互作用)."
ln socio:social_interaction socio thesaurus:related
def "socio:cooperation" "Working together toward a shared end."
ln socio:cooperation socio thesaurus:related
def "socio:social_conflict" "Struggle over resources, values or power (社会的対立)."
ln socio:social_conflict socio thesaurus:related
ln socio:social_conflict social:rival_of thesaurus:related
def "socio:deviance" "Behaviour violating significant social norms (逸脱)."
ln socio:deviance socio thesaurus:related
ln socio:deviance work:power_harassment thesaurus:related
ln socio:deviance gov:service:police thesaurus:related
def "socio:social_control" "The means by which conformity is encouraged (社会統制)."
ln socio:social_control socio thesaurus:related
ln socio:social_control gov:service:police thesaurus:related
ln socio:social_control socio:norm thesaurus:related
ln socio:social_control civ:public_trust thesaurus:related
def "socio:collective_behavior" "Spontaneous, unstructured group action (crowds, panics, fads)."
ln socio:collective_behavior socio thesaurus:related
def "socio:social_movement" "An organised, sustained effort for or against social change (社会運動)."
ln socio:social_movement socio thesaurus:related
ln socio:social_movement group:neighborhood_association thesaurus:related
ln socio:social_movement civ:appeal thesaurus:related
def "socio:social_change" "Transformation of social structure and culture over time (社会変動)."
ln socio:social_change socio thesaurus:related
def "socio:urbanization" "The growth of cities and city living (都市化)."
ln socio:urbanization socio thesaurus:related
ln socio:urbanization admin:city thesaurus:related
ln socio:urbanization admin:metropolis thesaurus:related
def "socio:globalization" "The deepening interconnection of societies worldwide (グローバル化)."
ln socio:globalization socio thesaurus:related
ln socio:globalization fx:foreign_exchange thesaurus:related
ln socio:globalization foodstud:columbian_exchange thesaurus:related
def "socio:modernization" "The shift toward industrial, rational, differentiated society."
ln socio:modernization socio thesaurus:related
# ── civil society & deliberation ──
def "socio:civil_society" "The realm of voluntary association between family, market and state (市民社会)."
ln socio:civil_society socio thesaurus:related
ln socio:civil_society group:neighborhood_association thesaurus:related
ln socio:civil_society group:pta thesaurus:related
ln socio:civil_society civ:ngo thesaurus:related
ln socio:civil_society concept:local_society thesaurus:related
def "socio:public_sphere" "The arena where private people reason together on public matters (Habermas) (公共圏)."
ln socio:public_sphere socio thesaurus:related
def "socio:public_opinion" "The aggregate of views held by a public (世論)."
ln socio:public_opinion socio thesaurus:related
ln socio:public_opinion civ:sentiment thesaurus:related
ln socio:public_opinion civ:survey_item thesaurus:related
ln socio:public_opinion civ:trend thesaurus:related
def "socio:deliberation" "Reasoned public discussion aimed at collective decision (熟議)."
ln socio:deliberation socio thesaurus:related
ln socio:deliberation civ:public_hearing thesaurus:related
ln socio:deliberation civ:consensus thesaurus:related
ln socio:deliberation civ:policy_option thesaurus:related
ln socio:deliberation civ:facilitation thesaurus:related
def "socio:collective_action" "Coordinated action by a group toward a shared goal."
ln socio:collective_action socio thesaurus:related
ln socio:collective_action group:community_sports thesaurus:related
ln socio:collective_action civ:representation thesaurus:related
def "socio:social_capital" "The value of social ties, trust and reciprocity (Putnam, Bourdieu) (社会関係資本)."
ln socio:social_capital socio thesaurus:related
ln socio:social_capital social:neighbor_of thesaurus:related
ln socio:social_capital concept:community thesaurus:related
ln socio:social_capital civ:public_trust thesaurus:related
def "socio:social_trust" "Generalised trust in others, a foundation of cooperation."
ln socio:social_trust socio thesaurus:related
ln socio:social_trust civ:public_trust thesaurus:related
ln socio:social_trust emo:trust thesaurus:related
def "socio:solidarity" "The bonds of mutual support holding a group together (連帯)."
ln socio:solidarity socio thesaurus:related
ln socio:solidarity concept:community thesaurus:related
# ── theory & method ──
def "socio:sociological_imagination" "Seeing personal troubles as public issues shaped by structure (C.W. Mills)."
ln socio:sociological_imagination socio thesaurus:related
def "socio:functionalism" "Viewing society as interdependent parts serving stability (Durkheim, Parsons)."
ln socio:functionalism socio thesaurus:related
def "socio:conflict_theory" "Viewing society through struggle over power and resources (Marx)."
ln socio:conflict_theory socio thesaurus:related
ln socio:conflict_theory socio:inequality thesaurus:related
def "socio:symbolic_interactionism" "Viewing society as built from meanings in everyday interaction."
ln socio:symbolic_interactionism socio thesaurus:related
def "socio:social_constructionism" "The view that social reality is collectively constructed."
ln socio:social_constructionism socio thesaurus:related
def "socio:structure_agency" "The debate over how far structure constrains vs individuals act."
ln socio:structure_agency socio thesaurus:related
def "socio:ethnography" "In-depth qualitative study of a group's way of life (エスノグラフィー)."
ln socio:ethnography socio thesaurus:related
ln socio:ethnography research:method:qualitative thesaurus:related
ln socio:ethnography research:fieldwork thesaurus:related
ln socio:ethnography foodstud:food_ethnology thesaurus:related
def "socio:participant_observation" "Studying a group by taking part in its life."
ln socio:participant_observation socio thesaurus:related
ln socio:participant_observation research:method:qualitative thesaurus:related
def "socio:social_survey" "Systematic questioning of a sample to measure attitudes/behaviour."
ln socio:social_survey socio thesaurus:related
ln socio:social_survey research:survey thesaurus:related
ln socio:social_survey civ:questionnaire thesaurus:related
ln socio:social_survey civ:sample thesaurus:related
# ── classic theorist-concepts ──
def "socio:social_fact" "A social phenomenon external to and constraining the individual (Durkheim)."
ln socio:social_fact socio thesaurus:related
def "socio:anomie" "Normlessness arising when social regulation breaks down (Durkheim) (アノミー)."
ln socio:anomie socio thesaurus:related
def "socio:mechanical_solidarity" "Cohesion from likeness in simple societies (Durkheim)."
ln socio:mechanical_solidarity socio thesaurus:related
def "socio:organic_solidarity" "Cohesion from interdependence in complex societies (Durkheim)."
ln socio:organic_solidarity socio thesaurus:related
def "socio:bureaucracy" "Rule by impersonal offices and rules — Weber's rational organisation (官僚制)."
ln socio:bureaucracy socio thesaurus:related
ln socio:bureaucracy org:hierarchy thesaurus:related
ln socio:bureaucracy occupation:official thesaurus:related
def "socio:rationalization" "The spread of calculative, efficient rationality (Weber)."
ln socio:rationalization socio thesaurus:related
ln socio:rationalization org:hierarchy thesaurus:related
def "socio:verstehen" "Interpretive understanding of the meaning actors give their action (Weber)."
ln socio:verstehen socio thesaurus:related
def "socio:alienation" "Estrangement of workers from their labour and selves (Marx) (疎外)."
ln socio:alienation socio thesaurus:related
ln socio:alienation work:overwork thesaurus:related
ln socio:alienation work:power_harassment thesaurus:related
def "socio:habitus" "Durable dispositions instilled by one's social position (Bourdieu)."
ln socio:habitus socio thesaurus:related
ln socio:habitus foodstud:culinary_identity thesaurus:related
ln socio:habitus status:outranks thesaurus:related
def "socio:cultural_capital" "Non-financial assets (education, taste) conferring advantage (Bourdieu)."
ln socio:cultural_capital socio thesaurus:related
ln socio:cultural_capital school:university thesaurus:related
ln socio:cultural_capital acad:professor thesaurus:related
def "socio:dramaturgy" "Social life as performance, managing impressions (Goffman)."
ln socio:dramaturgy socio thesaurus:related
ln socio:dramaturgy work:presentation thesaurus:related
def "socio:discipline" "Power that works by surveillance and normalisation (Foucault)."
ln socio:discipline socio thesaurus:related
ln socio:discipline gov:service:police thesaurus:related
ln socio:discipline school:exam thesaurus:related
