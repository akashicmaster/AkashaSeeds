#!/usr/bin/env python3
# Generate the general-education-level (general-education) social-sciences disciplinary map:
#   app/ontology/base3/social_sciences.ak
# Parallel to natural_sciences.ak / engineering.ak. Covers the five disciplines
# the user asked for — (law) · (political science) · (economics)
# · (management) · (sociology) — giving each a spine of subfields and
# cross-linking the scattered atoms already in base3 (econ:*, socio:*, law:branch:*,
# gov:*, mkt:/fin:/acct:/org:/pm:/biz:/invest:, econ:school:*, polthought:*) under
# it, wired into knowledge:branch:social_science.
#
# IMPORTANT: econ / socio / law:law already exist as top atoms — we DO NOT re-def
# them (that would collide the alias); we only add ln links. polisci / mgmt are new.

import os

def esc(s):
    return s.replace('"', "'")

L = [
 "# Akasha ontology — social sciences: the general-education-level disciplinary map.",
 "# Five disciplines — law, political science, economics, management, sociology —",
 "# each given a spine of subfields, with the detailed atoms already in base3",
 "# (econ:*, socio:*, law:branch:*, gov:*, mkt:/fin:/acct:/org:/pm:/biz:, econ:school:*,",
 "# polthought:*) cross-linked under it. Wired into the knowledge_map capstone.",
 "# General-education breadth; research depth is reserved for level-C packs. Base pack.",
 "",
 'def "knowledge:branch:social_science" "社会科学 — the study of society and human behaviour."',
]

def field(fid, gloss, parent, kids=None, bridges=None, rel="sys:part_of"):
    L.append(f'def "{fid}" "{esc(gloss)}"')
    L.append(f"ln {fid} {parent} sys:part_of")
    for k in (kids or []):
        L.append(f"ln {k} {fid} sys:part_of")
    for b in (bridges or []):
        L.append(f"ln {fid} {b} thesaurus:related")

# ── ECONOMICS (econ top already exists) ──────────────────────────────────────
L += ["", "# ══ Economics (econ top already defined) ══",
      "ln econ knowledge:branch:social_science knowledge:in_branch",
      "ln econ crosscut:scarcity thesaurus:related"]
field("econ:field:microeconomics", "ミクロ経済学 — the behaviour of individuals, firms and markets: supply, demand, prices, competition.", "econ",
  ["econ:demand","econ:supply","econ:supply_and_demand","econ:equilibrium_price","econ:marginal_utility","econ:marginal_cost","econ:price_elasticity","econ:opportunity_cost","econ:economies_of_scale","econ:monopoly","econ:oligopoly","econ:perfect_competition","econ:market","econ:market_failure","econ:externality","econ:public_good","econ:game_theory"],
  ["econ:school:neoclassical"])
field("econ:field:macroeconomics", "マクロ経済学 — the economy as a whole: growth, inflation, unemployment, money and policy.", "econ",
  ["econ:gdp","econ:inflation","econ:deflation","econ:recession","econ:stagflation","econ:business_cycle","econ:economic_growth","econ:unemployment","econ:fiscal_policy","econ:monetary_policy","econ:money_supply","econ:central_bank","econ:national_debt","econ:aggregate_demand","econ:aggregate_supply"],
  ["econ:school:keynesian","econ:school:monetarist"])
field("econ:field:international_economics", "国際経済学 — trade, exchange and the economic relations between nations.", "econ",
  ["econ:comparative_advantage","econ:trade","econ:balance_of_payments"],
  ["intl:free_trade_agreement","econ:school:mercantilism"])
field("econ:field:behavioral_economics", "行動経済学 — how real, boundedly-rational people actually decide.", "econ",
  ["econ:behavioral_economics"], ["econ:school:behavioral","psy"])
field("econ:field:econometrics", "計量経済学 — measuring economic relationships with statistical method.", "econ",
  [], ["math:statistics","knowledge:method:computational"])
field("econ:field:development_economics", "開発経済学 — the economics of growth, poverty and institutions in developing economies.", "econ",
  [], ["econ:economic_growth"])
field("econ:field:public_economics", "公共経済学 — the state in the economy: taxation, public goods, redistribution.", "econ",
  ["econ:public_good"], ["gov:function:taxation","gov:tax"])
field("econ:field:economic_thought", "経済思想史 — the schools that shaped economics, from mercantilism to Keynes and beyond.", "econ",
  ["econ:school:mercantilism","econ:school:physiocracy","econ:school:classical_economics","econ:school:marxist_economics","econ:school:neoclassical","econ:school:keynesian","econ:school:monetarist","econ:school:behavioral"],
  ["polthought:socialism"])

# ── POLITICAL SCIENCE (new top; polti:* is unrelated — Polti's dramatic situations) ─
L += ["", "# ══ Political science (new spine; polti:* is narrative, unrelated) ══",
      'def "polisci:political_science" "政治学 — the study of government, power, the state, and political behaviour."',
      "ln polisci:political_science knowledge:branch:social_science knowledge:in_branch",
      "ln polisci:political_science crosscut:hierarchy thesaurus:related"]
field("polisci:field:political_theory", "政治思想 — ideas of justice, authority, liberty and the state, from the classics to today.", "polisci:political_science",
  ["polthought:classical_republicanism","polthought:social_contract","polthought:liberalism","polthought:conservatism","polthought:socialism","polthought:communism","polthought:anarchism","polthought:nationalism","polthought:liberal_democracy","polthought:fascism","polthought:feminist_theory"],
  ["socio:power","law:branch:constitutional_law"])
field("polisci:field:comparative_politics", "比較政治学 — comparing political systems, regimes and institutions across countries.", "polisci:political_science",
  [], ["polthought:liberal_democracy","socio:bureaucracy","socio:legitimacy"])
field("polisci:field:international_relations", "国際関係論 — relations between states: diplomacy, war, trade, and global order.", "polisci:political_science",
  [], ["intl:sanctions","intl:geopolitical_risk","polthought:nationalism","law:branch:international_law"])
field("polisci:field:public_administration", "行政学 — how governments organise and deliver public services.", "polisci:political_science",
  ["gov:function:public_safety","gov:function:public_health","gov:function:taxation","gov:function:welfare","gov:function:urban_planning","gov:service:police"],
  ["socio:bureaucracy","admin:municipality"])
field("polisci:field:public_policy", "公共政策学 — how policies are made, chosen and evaluated.", "polisci:political_science",
  [], ["econ:field:public_economics","gov:function:welfare"])
field("polisci:field:political_economy", "政治経済学 — the interplay of political power and economic systems.", "polisci:political_science",
  [], ["econ:field:macroeconomics","polthought:socialism","econ:school:marxist_economics"])

# ── LAW (law:law top already exists, and law:branch:* already defined) ────────
L += ["", "# ══ Law (law:law top and law:branch:* already defined) ══",
      "# Law is applied-science in the knowledge map; here we relate it to the social",
      "# sciences and make its branch spine explicit (duplicate-safe sys:part_of).",
      "ln law:law knowledge:branch:social_science thesaurus:related",
      "ln law:law socio:social_control thesaurus:related"]
LAW_BRANCHES = ["constitutional_law","administrative_law","criminal_law","civil_law_branch","contract_law","tort_law","property_law","family_law","commercial_law","labor_law","tax_law","intellectual_property","international_law","environmental_law"]
for b in LAW_BRANCHES:
    L.append(f"ln law:branch:{b} law:law sys:part_of")
# a couple of cross-discipline bridges
L += ["ln law:branch:constitutional_law polisci:political_science thesaurus:related",
      "ln law:branch:commercial_law mgmt:management thesaurus:related",
      "ln law:branch:labor_law econ:field:macroeconomics thesaurus:related"]

# ── MANAGEMENT / BUSINESS (new top; scattered across biz/mkt/fin/acct/org/pm) ─
L += ["", "# ══ Management / business (new spine over biz/mkt/fin/acct/org/pm) ══",
      'def "mgmt:management" "経営学 — the study of organising people and resources to achieve the goals of a firm or organisation."',
      "ln mgmt:management knowledge:branch:social_science knowledge:in_branch",
      "ln mgmt:management knowledge:branch:applied_science thesaurus:related",
      "ln mgmt:management econ thesaurus:related"]
field("mgmt:field:strategy", "経営戦略 — how a firm positions itself to compete and create value.", "mgmt:management",
  [], ["biz:differentiation","econ:field:microeconomics"])
field("mgmt:field:marketing", "マーケティング — understanding and reaching customers; brand, product and demand.", "mgmt:management",
  ["mkt:brand_strategy","mkt:advertising","mkt:marketing_funnel","mkt:customer_journey","mkt:content_marketing"], ["econ:demand"])
field("mgmt:field:finance", "経営財務 — funding, investment and the financial health of the firm.", "mgmt:management",
  ["fin:corporate_finance","fin:capital","fin:capital_structure","fin:cost_of_capital","invest:asset_allocation","invest:modern_portfolio_theory"], ["econ:field:macroeconomics"])
field("mgmt:field:accounting", "会計学 — recording, measuring and reporting the finances of an organisation.", "mgmt:management",
  ["acct:accounting_equation","acct:balance_sheet","acct:cash_flow_statement","acct:auditing","acct:accrual_accounting"], [])
field("mgmt:field:organizational_behavior", "組織行動論 — people in organisations: motivation, leadership, teams, culture.", "mgmt:management",
  ["org:hierarchy","org:collaboration","org:engagement","org:decision_making","org:conflict_resolution"], ["socio:social_institution","psy"])
field("mgmt:field:operations", "生産・オペレーション管理 — designing and running the processes that deliver goods and services.", "mgmt:management",
  [], ["mfg:capacity_planning","crosscut:optimization","eng:branch:industrial"])
field("mgmt:field:project_management", "プロジェクトマネジメント — planning and steering time-bounded work to its goals.", "mgmt:management",
  ["pm:agile","pm:kanban","pm:iron_triangle","pm:execution","pm:change_control"], ["crosscut:process"])
field("mgmt:field:entrepreneurship", "起業・アントレプレナーシップ — creating and growing new ventures.", "mgmt:management",
  ["biz:differentiation","biz:customer"], ["mkt:brand_strategy"])

# ── SOCIOLOGY (socio top already exists; socio:* atoms are flat) ──────────────
L += ["", "# ══ Sociology (socio top already defined; socio:* atoms are flat) ══",
      "ln socio knowledge:branch:social_science knowledge:in_branch",
      "ln socio crosscut:emergence thesaurus:related"]
field("socio:field:social_theory", "社会理論 — the great frameworks: functionalism, conflict theory, interactionism.", "socio",
  ["socio:functionalism","socio:conflict_theory","socio:symbolic_interactionism","socio:social_constructionism","socio:structure_agency","socio:sociological_imagination","socio:dramaturgy","socio:habitus","socio:verstehen"], [])
field("socio:field:stratification", "社会階層論 — class, status, mobility and inequality.", "socio",
  ["socio:social_class","socio:social_stratification","socio:social_mobility","socio:inequality","socio:caste","socio:elite","socio:cultural_capital","socio:social_status","socio:social_capital"], ["econ:field:macroeconomics"])
field("socio:field:culture_society", "文化社会学 — norms, values, culture and identity.", "socio",
  ["socio:culture","socio:norm","socio:value","socio:mores","socio:folkways","socio:subculture","socio:identity","socio:socialization"], [])
field("socio:field:deviance_crime", "逸脱と統制 — deviance, social control and order.", "socio",
  ["socio:deviance","socio:anomie","socio:social_control","socio:alienation","socio:discipline"], ["law:branch:criminal_law"])
field("socio:field:social_institutions", "社会制度論 — the enduring structures of society: authority, bureaucracy, civil society.", "socio",
  ["socio:social_institution","socio:social_structure","socio:authority","socio:bureaucracy","socio:legitimacy","socio:civil_society","socio:power","socio:rationalization"], ["polisci:field:public_administration"])
field("socio:field:collective_behavior", "集合行動論 — movements, crowds, opinion and collective action.", "socio",
  ["socio:collective_behavior","socio:collective_action","socio:social_movement","socio:social_change","socio:public_opinion","socio:public_sphere","socio:deliberation"], ["crosscut:emergence"])
field("socio:field:groups_networks", "集団とネットワーク — groups, solidarity and social networks.", "socio",
  ["socio:social_group","socio:primary_group","socio:secondary_group","socio:reference_group","socio:in_group","socio:out_group","socio:solidarity","socio:mechanical_solidarity","socio:organic_solidarity","socio:social_network","socio:social_trust","socio:gemeinschaft","socio:gesellschaft"], ["crosscut:network"])
field("socio:field:urban_modernization", "都市化と近代化 — cities, globalization and the modern transformation.", "socio",
  ["socio:urbanization","socio:modernization","socio:globalization","socio:society"], ["admin:city"])
field("socio:field:methods", "社会調査法 — how sociology studies society: surveys, ethnography, observation.", "socio",
  ["socio:social_survey","socio:ethnography","socio:participant_observation","socio:social_fact"], ["knowledge:method:empirical","math:statistics"])

path = "app/ontology/base3/social_sciences.ak"
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
ndef = sum(1 for l in L if l.startswith("def "))
nln = sum(1 for l in L if l.startswith("ln "))
print(f"{path}: def={ndef} ln={nln} ({len(L)} lines)")
