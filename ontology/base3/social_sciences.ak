# Akasha ontology — social sciences: the general-education-level disciplinary map.
# Five disciplines — law, political science, economics, management, sociology —
# each given a spine of subfields, with the detailed atoms already in base3
# (econ:*, socio:*, law:branch:*, gov:*, mkt:/fin:/acct:/org:/pm:/biz:, econ:school:*,
# polthought:*) cross-linked under it. Wired into the knowledge_map capstone.
# General-education breadth; research depth is reserved for level-C packs. Base pack.

def "knowledge:branch:social_science" "社会科学 — the study of society and human behaviour."

# ══ Economics (econ top already defined) ══
ln econ knowledge:branch:social_science knowledge:in_branch
ln econ crosscut:scarcity thesaurus:related
def "econ:field:microeconomics" "ミクロ経済学 — the behaviour of individuals, firms and markets: supply, demand, prices, competition."
ln econ:field:microeconomics econ sys:part_of
ln econ:demand econ:field:microeconomics sys:part_of
ln econ:supply econ:field:microeconomics sys:part_of
ln econ:supply_and_demand econ:field:microeconomics sys:part_of
ln econ:equilibrium_price econ:field:microeconomics sys:part_of
ln econ:marginal_utility econ:field:microeconomics sys:part_of
ln econ:marginal_cost econ:field:microeconomics sys:part_of
ln econ:price_elasticity econ:field:microeconomics sys:part_of
ln econ:opportunity_cost econ:field:microeconomics sys:part_of
ln econ:economies_of_scale econ:field:microeconomics sys:part_of
ln econ:monopoly econ:field:microeconomics sys:part_of
ln econ:oligopoly econ:field:microeconomics sys:part_of
ln econ:perfect_competition econ:field:microeconomics sys:part_of
ln econ:market econ:field:microeconomics sys:part_of
ln econ:market_failure econ:field:microeconomics sys:part_of
ln econ:externality econ:field:microeconomics sys:part_of
ln econ:public_good econ:field:microeconomics sys:part_of
ln econ:game_theory econ:field:microeconomics sys:part_of
ln econ:field:microeconomics econ:school:neoclassical thesaurus:related
def "econ:field:macroeconomics" "マクロ経済学 — the economy as a whole: growth, inflation, unemployment, money and policy."
ln econ:field:macroeconomics econ sys:part_of
ln econ:gdp econ:field:macroeconomics sys:part_of
ln econ:inflation econ:field:macroeconomics sys:part_of
ln econ:deflation econ:field:macroeconomics sys:part_of
ln econ:recession econ:field:macroeconomics sys:part_of
ln econ:stagflation econ:field:macroeconomics sys:part_of
ln econ:business_cycle econ:field:macroeconomics sys:part_of
ln econ:economic_growth econ:field:macroeconomics sys:part_of
ln econ:unemployment econ:field:macroeconomics sys:part_of
ln econ:fiscal_policy econ:field:macroeconomics sys:part_of
ln econ:monetary_policy econ:field:macroeconomics sys:part_of
ln econ:money_supply econ:field:macroeconomics sys:part_of
ln econ:central_bank econ:field:macroeconomics sys:part_of
ln econ:national_debt econ:field:macroeconomics sys:part_of
ln econ:aggregate_demand econ:field:macroeconomics sys:part_of
ln econ:aggregate_supply econ:field:macroeconomics sys:part_of
ln econ:field:macroeconomics econ:school:keynesian thesaurus:related
ln econ:field:macroeconomics econ:school:monetarist thesaurus:related
def "econ:field:international_economics" "国際経済学 — trade, exchange and the economic relations between nations."
ln econ:field:international_economics econ sys:part_of
ln econ:comparative_advantage econ:field:international_economics sys:part_of
ln econ:trade econ:field:international_economics sys:part_of
ln econ:balance_of_payments econ:field:international_economics sys:part_of
ln econ:field:international_economics intl:free_trade_agreement thesaurus:related
ln econ:field:international_economics econ:school:mercantilism thesaurus:related
def "econ:field:behavioral_economics" "行動経済学 — how real, boundedly-rational people actually decide."
ln econ:field:behavioral_economics econ sys:part_of
ln econ:behavioral_economics econ:field:behavioral_economics sys:part_of
ln econ:field:behavioral_economics econ:school:behavioral thesaurus:related
ln econ:field:behavioral_economics psy thesaurus:related
def "econ:field:econometrics" "計量経済学 — measuring economic relationships with statistical method."
ln econ:field:econometrics econ sys:part_of
ln econ:field:econometrics math:statistics thesaurus:related
ln econ:field:econometrics knowledge:method:computational thesaurus:related
def "econ:field:development_economics" "開発経済学 — the economics of growth, poverty and institutions in developing economies."
ln econ:field:development_economics econ sys:part_of
ln econ:field:development_economics econ:economic_growth thesaurus:related
def "econ:field:public_economics" "公共経済学 — the state in the economy: taxation, public goods, redistribution."
ln econ:field:public_economics econ sys:part_of
ln econ:public_good econ:field:public_economics sys:part_of
ln econ:field:public_economics gov:function:taxation thesaurus:related
ln econ:field:public_economics gov:tax thesaurus:related
def "econ:field:economic_thought" "経済思想史 — the schools that shaped economics, from mercantilism to Keynes and beyond."
ln econ:field:economic_thought econ sys:part_of
ln econ:school:mercantilism econ:field:economic_thought sys:part_of
ln econ:school:physiocracy econ:field:economic_thought sys:part_of
ln econ:school:classical_economics econ:field:economic_thought sys:part_of
ln econ:school:marxist_economics econ:field:economic_thought sys:part_of
ln econ:school:neoclassical econ:field:economic_thought sys:part_of
ln econ:school:keynesian econ:field:economic_thought sys:part_of
ln econ:school:monetarist econ:field:economic_thought sys:part_of
ln econ:school:behavioral econ:field:economic_thought sys:part_of
ln econ:field:economic_thought polthought:socialism thesaurus:related

# ══ Political science (new spine; polti:* is narrative, unrelated) ══
def "polisci:political_science" "政治学 — the study of government, power, the state, and political behaviour."
ln polisci:political_science knowledge:branch:social_science knowledge:in_branch
ln polisci:political_science crosscut:hierarchy thesaurus:related
def "polisci:field:political_theory" "政治思想 — ideas of justice, authority, liberty and the state, from the classics to today."
ln polisci:field:political_theory polisci:political_science sys:part_of
ln polthought:classical_republicanism polisci:field:political_theory sys:part_of
ln polthought:social_contract polisci:field:political_theory sys:part_of
ln polthought:liberalism polisci:field:political_theory sys:part_of
ln polthought:conservatism polisci:field:political_theory sys:part_of
ln polthought:socialism polisci:field:political_theory sys:part_of
ln polthought:communism polisci:field:political_theory sys:part_of
ln polthought:anarchism polisci:field:political_theory sys:part_of
ln polthought:nationalism polisci:field:political_theory sys:part_of
ln polthought:liberal_democracy polisci:field:political_theory sys:part_of
ln polthought:fascism polisci:field:political_theory sys:part_of
ln polthought:feminist_theory polisci:field:political_theory sys:part_of
ln polisci:field:political_theory socio:power thesaurus:related
ln polisci:field:political_theory law:branch:constitutional_law thesaurus:related
def "polisci:field:comparative_politics" "比較政治学 — comparing political systems, regimes and institutions across countries."
ln polisci:field:comparative_politics polisci:political_science sys:part_of
ln polisci:field:comparative_politics polthought:liberal_democracy thesaurus:related
ln polisci:field:comparative_politics socio:bureaucracy thesaurus:related
ln polisci:field:comparative_politics socio:legitimacy thesaurus:related
def "polisci:field:international_relations" "国際関係論 — relations between states: diplomacy, war, trade, and global order."
ln polisci:field:international_relations polisci:political_science sys:part_of
ln polisci:field:international_relations intl:sanctions thesaurus:related
ln polisci:field:international_relations intl:geopolitical_risk thesaurus:related
ln polisci:field:international_relations polthought:nationalism thesaurus:related
ln polisci:field:international_relations law:branch:international_law thesaurus:related
def "polisci:field:public_administration" "行政学 — how governments organise and deliver public services."
ln polisci:field:public_administration polisci:political_science sys:part_of
ln gov:function:public_safety polisci:field:public_administration sys:part_of
ln gov:function:public_health polisci:field:public_administration sys:part_of
ln gov:function:taxation polisci:field:public_administration sys:part_of
ln gov:function:welfare polisci:field:public_administration sys:part_of
ln gov:function:urban_planning polisci:field:public_administration sys:part_of
ln gov:service:police polisci:field:public_administration sys:part_of
ln polisci:field:public_administration socio:bureaucracy thesaurus:related
ln polisci:field:public_administration admin:municipality thesaurus:related
def "polisci:field:public_policy" "公共政策学 — how policies are made, chosen and evaluated."
ln polisci:field:public_policy polisci:political_science sys:part_of
ln polisci:field:public_policy econ:field:public_economics thesaurus:related
ln polisci:field:public_policy gov:function:welfare thesaurus:related
def "polisci:field:political_economy" "政治経済学 — the interplay of political power and economic systems."
ln polisci:field:political_economy polisci:political_science sys:part_of
ln polisci:field:political_economy econ:field:macroeconomics thesaurus:related
ln polisci:field:political_economy polthought:socialism thesaurus:related
ln polisci:field:political_economy econ:school:marxist_economics thesaurus:related

# ══ Law (law:law top and law:branch:* already defined) ══
# Law is applied-science in the knowledge map; here we relate it to the social
# sciences and make its branch spine explicit (duplicate-safe sys:part_of).
ln law:law knowledge:branch:social_science thesaurus:related
ln law:law socio:social_control thesaurus:related
ln law:branch:constitutional_law law:law sys:part_of
ln law:branch:administrative_law law:law sys:part_of
ln law:branch:criminal_law law:law sys:part_of
ln law:branch:civil_law_branch law:law sys:part_of
ln law:branch:contract_law law:law sys:part_of
ln law:branch:tort_law law:law sys:part_of
ln law:branch:property_law law:law sys:part_of
ln law:branch:family_law law:law sys:part_of
ln law:branch:commercial_law law:law sys:part_of
ln law:branch:labor_law law:law sys:part_of
ln law:branch:tax_law law:law sys:part_of
ln law:branch:intellectual_property law:law sys:part_of
ln law:branch:international_law law:law sys:part_of
ln law:branch:environmental_law law:law sys:part_of
ln law:branch:constitutional_law polisci:political_science thesaurus:related
ln law:branch:commercial_law mgmt:management thesaurus:related
ln law:branch:labor_law econ:field:macroeconomics thesaurus:related

# ══ Management / business (new spine over biz/mkt/fin/acct/org/pm) ══
def "mgmt:management" "経営学 — the study of organising people and resources to achieve the goals of a firm or organisation."
ln mgmt:management knowledge:branch:social_science knowledge:in_branch
ln mgmt:management knowledge:branch:applied_science thesaurus:related
ln mgmt:management econ thesaurus:related
def "mgmt:field:strategy" "経営戦略 — how a firm positions itself to compete and create value."
ln mgmt:field:strategy mgmt:management sys:part_of
ln mgmt:field:strategy biz:differentiation thesaurus:related
ln mgmt:field:strategy econ:field:microeconomics thesaurus:related
def "mgmt:field:marketing" "マーケティング — understanding and reaching customers; brand, product and demand."
ln mgmt:field:marketing mgmt:management sys:part_of
ln mkt:brand_strategy mgmt:field:marketing sys:part_of
ln mkt:advertising mgmt:field:marketing sys:part_of
ln mkt:marketing_funnel mgmt:field:marketing sys:part_of
ln mkt:customer_journey mgmt:field:marketing sys:part_of
ln mkt:content_marketing mgmt:field:marketing sys:part_of
ln mgmt:field:marketing econ:demand thesaurus:related
def "mgmt:field:finance" "経営財務 — funding, investment and the financial health of the firm."
ln mgmt:field:finance mgmt:management sys:part_of
ln fin:corporate_finance mgmt:field:finance sys:part_of
ln fin:capital mgmt:field:finance sys:part_of
ln fin:capital_structure mgmt:field:finance sys:part_of
ln fin:cost_of_capital mgmt:field:finance sys:part_of
ln invest:asset_allocation mgmt:field:finance sys:part_of
ln invest:modern_portfolio_theory mgmt:field:finance sys:part_of
ln mgmt:field:finance econ:field:macroeconomics thesaurus:related
def "mgmt:field:accounting" "会計学 — recording, measuring and reporting the finances of an organisation."
ln mgmt:field:accounting mgmt:management sys:part_of
ln acct:accounting_equation mgmt:field:accounting sys:part_of
ln acct:balance_sheet mgmt:field:accounting sys:part_of
ln acct:cash_flow_statement mgmt:field:accounting sys:part_of
ln acct:auditing mgmt:field:accounting sys:part_of
ln acct:accrual_accounting mgmt:field:accounting sys:part_of
def "mgmt:field:organizational_behavior" "組織行動論 — people in organisations: motivation, leadership, teams, culture."
ln mgmt:field:organizational_behavior mgmt:management sys:part_of
ln org:hierarchy mgmt:field:organizational_behavior sys:part_of
ln org:collaboration mgmt:field:organizational_behavior sys:part_of
ln org:engagement mgmt:field:organizational_behavior sys:part_of
ln org:decision_making mgmt:field:organizational_behavior sys:part_of
ln org:conflict_resolution mgmt:field:organizational_behavior sys:part_of
ln mgmt:field:organizational_behavior socio:social_institution thesaurus:related
ln mgmt:field:organizational_behavior psy thesaurus:related
def "mgmt:field:operations" "生産・オペレーション管理 — designing and running the processes that deliver goods and services."
ln mgmt:field:operations mgmt:management sys:part_of
ln mgmt:field:operations mfg:capacity_planning thesaurus:related
ln mgmt:field:operations crosscut:optimization thesaurus:related
ln mgmt:field:operations eng:branch:industrial thesaurus:related
def "mgmt:field:project_management" "プロジェクトマネジメント — planning and steering time-bounded work to its goals."
ln mgmt:field:project_management mgmt:management sys:part_of
ln pm:agile mgmt:field:project_management sys:part_of
ln pm:kanban mgmt:field:project_management sys:part_of
ln pm:iron_triangle mgmt:field:project_management sys:part_of
ln pm:execution mgmt:field:project_management sys:part_of
ln pm:change_control mgmt:field:project_management sys:part_of
ln mgmt:field:project_management crosscut:process thesaurus:related
def "mgmt:field:entrepreneurship" "起業・アントレプレナーシップ — creating and growing new ventures."
ln mgmt:field:entrepreneurship mgmt:management sys:part_of
ln biz:differentiation mgmt:field:entrepreneurship sys:part_of
ln biz:customer mgmt:field:entrepreneurship sys:part_of
ln mgmt:field:entrepreneurship mkt:brand_strategy thesaurus:related

# ══ Sociology (socio top already defined; socio:* atoms are flat) ══
ln socio knowledge:branch:social_science knowledge:in_branch
ln socio crosscut:emergence thesaurus:related
def "socio:field:social_theory" "社会理論 — the great frameworks: functionalism, conflict theory, interactionism."
ln socio:field:social_theory socio sys:part_of
ln socio:functionalism socio:field:social_theory sys:part_of
ln socio:conflict_theory socio:field:social_theory sys:part_of
ln socio:symbolic_interactionism socio:field:social_theory sys:part_of
ln socio:social_constructionism socio:field:social_theory sys:part_of
ln socio:structure_agency socio:field:social_theory sys:part_of
ln socio:sociological_imagination socio:field:social_theory sys:part_of
ln socio:dramaturgy socio:field:social_theory sys:part_of
ln socio:habitus socio:field:social_theory sys:part_of
ln socio:verstehen socio:field:social_theory sys:part_of
def "socio:field:stratification" "社会階層論 — class, status, mobility and inequality."
ln socio:field:stratification socio sys:part_of
ln socio:social_class socio:field:stratification sys:part_of
ln socio:social_stratification socio:field:stratification sys:part_of
ln socio:social_mobility socio:field:stratification sys:part_of
ln socio:inequality socio:field:stratification sys:part_of
ln socio:caste socio:field:stratification sys:part_of
ln socio:elite socio:field:stratification sys:part_of
ln socio:cultural_capital socio:field:stratification sys:part_of
ln socio:social_status socio:field:stratification sys:part_of
ln socio:social_capital socio:field:stratification sys:part_of
ln socio:field:stratification econ:field:macroeconomics thesaurus:related
def "socio:field:culture_society" "文化社会学 — norms, values, culture and identity."
ln socio:field:culture_society socio sys:part_of
ln socio:culture socio:field:culture_society sys:part_of
ln socio:norm socio:field:culture_society sys:part_of
ln socio:value socio:field:culture_society sys:part_of
ln socio:mores socio:field:culture_society sys:part_of
ln socio:folkways socio:field:culture_society sys:part_of
ln socio:subculture socio:field:culture_society sys:part_of
ln socio:identity socio:field:culture_society sys:part_of
ln socio:socialization socio:field:culture_society sys:part_of
def "socio:field:deviance_crime" "逸脱と統制 — deviance, social control and order."
ln socio:field:deviance_crime socio sys:part_of
ln socio:deviance socio:field:deviance_crime sys:part_of
ln socio:anomie socio:field:deviance_crime sys:part_of
ln socio:social_control socio:field:deviance_crime sys:part_of
ln socio:alienation socio:field:deviance_crime sys:part_of
ln socio:discipline socio:field:deviance_crime sys:part_of
ln socio:field:deviance_crime law:branch:criminal_law thesaurus:related
def "socio:field:social_institutions" "社会制度論 — the enduring structures of society: authority, bureaucracy, civil society."
ln socio:field:social_institutions socio sys:part_of
ln socio:social_institution socio:field:social_institutions sys:part_of
ln socio:social_structure socio:field:social_institutions sys:part_of
ln socio:authority socio:field:social_institutions sys:part_of
ln socio:bureaucracy socio:field:social_institutions sys:part_of
ln socio:legitimacy socio:field:social_institutions sys:part_of
ln socio:civil_society socio:field:social_institutions sys:part_of
ln socio:power socio:field:social_institutions sys:part_of
ln socio:rationalization socio:field:social_institutions sys:part_of
ln socio:field:social_institutions polisci:field:public_administration thesaurus:related
def "socio:field:collective_behavior" "集合行動論 — movements, crowds, opinion and collective action."
ln socio:field:collective_behavior socio sys:part_of
ln socio:collective_behavior socio:field:collective_behavior sys:part_of
ln socio:collective_action socio:field:collective_behavior sys:part_of
ln socio:social_movement socio:field:collective_behavior sys:part_of
ln socio:social_change socio:field:collective_behavior sys:part_of
ln socio:public_opinion socio:field:collective_behavior sys:part_of
ln socio:public_sphere socio:field:collective_behavior sys:part_of
ln socio:deliberation socio:field:collective_behavior sys:part_of
ln socio:field:collective_behavior crosscut:emergence thesaurus:related
def "socio:field:groups_networks" "集団とネットワーク — groups, solidarity and social networks."
ln socio:field:groups_networks socio sys:part_of
ln socio:social_group socio:field:groups_networks sys:part_of
ln socio:primary_group socio:field:groups_networks sys:part_of
ln socio:secondary_group socio:field:groups_networks sys:part_of
ln socio:reference_group socio:field:groups_networks sys:part_of
ln socio:in_group socio:field:groups_networks sys:part_of
ln socio:out_group socio:field:groups_networks sys:part_of
ln socio:solidarity socio:field:groups_networks sys:part_of
ln socio:mechanical_solidarity socio:field:groups_networks sys:part_of
ln socio:organic_solidarity socio:field:groups_networks sys:part_of
ln socio:social_network socio:field:groups_networks sys:part_of
ln socio:social_trust socio:field:groups_networks sys:part_of
ln socio:gemeinschaft socio:field:groups_networks sys:part_of
ln socio:gesellschaft socio:field:groups_networks sys:part_of
ln socio:field:groups_networks crosscut:network thesaurus:related
def "socio:field:urban_modernization" "都市化と近代化 — cities, globalization and the modern transformation."
ln socio:field:urban_modernization socio sys:part_of
ln socio:urbanization socio:field:urban_modernization sys:part_of
ln socio:modernization socio:field:urban_modernization sys:part_of
ln socio:globalization socio:field:urban_modernization sys:part_of
ln socio:society socio:field:urban_modernization sys:part_of
ln socio:field:urban_modernization admin:city thesaurus:related
def "socio:field:methods" "社会調査法 — how sociology studies society: surveys, ethnography, observation."
ln socio:field:methods socio sys:part_of
ln socio:social_survey socio:field:methods sys:part_of
ln socio:ethnography socio:field:methods sys:part_of
ln socio:participant_observation socio:field:methods sys:part_of
ln socio:social_fact socio:field:methods sys:part_of
ln socio:field:methods knowledge:method:empirical thesaurus:related
ln socio:field:methods math:statistics thesaurus:related
