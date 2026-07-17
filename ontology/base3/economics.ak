# Akasha ontology — economics: microeconomics & macroeconomics (経済学).
# Classified by econ_field (micro/macro). Bridged to fin:/fx:/gov:tax/geo:gdp/
# admin:country/person:field:economics. Base pack.

def "econ" "Economics — how societies allocate scarce resources."
def "econ_field:micro" "Microeconomics — individual agents and markets."
def "econ_field:macro" "Macroeconomics — the economy as a whole."
ln econ person:field:economics thesaurus:related

# ── microeconomics (ミクロ経済学) ──
def "econ:scarcity" "Limited resources against unlimited wants — the root economic problem (希少性)."
ln econ:scarcity econ thesaurus:related
ln econ:scarcity econ_field:micro econ:field
def "econ:supply_and_demand" "The forces setting price and quantity in a market (需要と供給)."
ln econ:supply_and_demand econ thesaurus:related
ln econ:supply_and_demand econ_field:micro econ:field
def "econ:supply" "How much producers offer at each price."
ln econ:supply econ thesaurus:related
ln econ:supply econ_field:micro econ:field
def "econ:demand" "How much buyers want at each price."
ln econ:demand econ thesaurus:related
ln econ:demand econ_field:micro econ:field
def "econ:equilibrium_price" "The price where supply meets demand (均衡価格)."
ln econ:equilibrium_price econ thesaurus:related
ln econ:equilibrium_price econ_field:micro econ:field
def "econ:price_elasticity" "How much quantity responds to a price change (弾力性)."
ln econ:price_elasticity econ thesaurus:related
ln econ:price_elasticity econ_field:micro econ:field
def "econ:marginal_utility" "The added satisfaction from one more unit; it tends to diminish."
ln econ:marginal_utility econ thesaurus:related
ln econ:marginal_utility econ_field:micro econ:field
def "econ:opportunity_cost" "The value of the next-best alternative forgone (機会費用)."
ln econ:opportunity_cost econ thesaurus:related
ln econ:opportunity_cost econ_field:micro econ:field
def "econ:marginal_cost" "The cost of producing one more unit."
ln econ:marginal_cost econ thesaurus:related
ln econ:marginal_cost econ_field:micro econ:field
def "econ:economies_of_scale" "Falling unit cost as output grows (規模の経済)."
ln econ:economies_of_scale econ thesaurus:related
ln econ:economies_of_scale econ_field:micro econ:field
def "econ:market" "Any arrangement where buyers and sellers exchange."
ln econ:market econ thesaurus:related
ln econ:market econ_field:micro econ:field
def "econ:perfect_competition" "Many small firms, identical goods, no price power."
ln econ:perfect_competition econ thesaurus:related
ln econ:perfect_competition econ_field:micro econ:field
def "econ:monopoly" "A single seller with price-setting power (独占)."
ln econ:monopoly econ thesaurus:related
ln econ:monopoly econ_field:micro econ:field
ln econ:monopoly biz:competitor thesaurus:related
def "econ:oligopoly" "A few dominant sellers (寡占)."
ln econ:oligopoly econ thesaurus:related
ln econ:oligopoly econ_field:micro econ:field
def "econ:externality" "A cost or benefit falling on third parties (pollution, vaccination) (外部性)."
ln econ:externality econ thesaurus:related
ln econ:externality econ_field:micro econ:field
ln econ:externality foodsustain:carbon_footprint_food thesaurus:related
ln econ:externality gov:function:public_health thesaurus:related
def "econ:public_good" "A non-excludable, non-rival good (defence, clean air)."
ln econ:public_good econ thesaurus:related
ln econ:public_good econ_field:micro econ:field
ln econ:public_good gov:function:public_safety thesaurus:related
ln econ:public_good place:park thesaurus:related
def "econ:market_failure" "When free markets allocate inefficiently."
ln econ:market_failure econ thesaurus:related
ln econ:market_failure econ_field:micro econ:field
ln econ:market_failure gov:function:taxation thesaurus:related
def "econ:comparative_advantage" "Gains from each producing what it forgoes least — the case for trade (比較優位)."
ln econ:comparative_advantage econ thesaurus:related
ln econ:comparative_advantage econ_field:micro econ:field
ln econ:comparative_advantage fx:foreign_exchange thesaurus:related
def "econ:game_theory" "The analysis of strategic interaction between agents."
ln econ:game_theory econ thesaurus:related
ln econ:game_theory econ_field:micro econ:field
def "econ:behavioral_economics" "How real, biased human psychology shapes economic choices."
ln econ:behavioral_economics econ thesaurus:related
ln econ:behavioral_economics econ_field:micro econ:field
# ── macroeconomics (マクロ経済学) ──
def "econ:gdp" "Gross domestic product — the total value of goods and services produced (国内総生産)."
ln econ:gdp econ thesaurus:related
ln econ:gdp econ_field:macro econ:field
ln econ:gdp admin:country thesaurus:related
def "econ:economic_growth" "A sustained rise in output over time."
ln econ:economic_growth econ thesaurus:related
ln econ:economic_growth econ_field:macro econ:field
def "econ:inflation" "A general rise in prices (インフレ)."
ln econ:inflation econ thesaurus:related
ln econ:inflation econ_field:macro econ:field
ln econ:inflation fin:inflation thesaurus:related
def "econ:deflation" "A general fall in prices (デフレ)."
ln econ:deflation econ thesaurus:related
ln econ:deflation econ_field:macro econ:field
def "econ:unemployment" "The share of the labour force without work (失業)."
ln econ:unemployment econ thesaurus:related
ln econ:unemployment econ_field:macro econ:field
ln econ:unemployment work:layoff thesaurus:related
ln econ:unemployment gov:benefit:unemployment_benefit thesaurus:related
def "econ:business_cycle" "The alternation of expansion and recession."
ln econ:business_cycle econ thesaurus:related
ln econ:business_cycle econ_field:macro econ:field
def "econ:recession" "A significant, broad decline in activity (景気後退)."
ln econ:recession econ thesaurus:related
ln econ:recession econ_field:macro econ:field
def "econ:fiscal_policy" "Government use of taxing and spending to steer the economy (財政政策)."
ln econ:fiscal_policy econ thesaurus:related
ln econ:fiscal_policy econ_field:macro econ:field
ln econ:fiscal_policy gov:function:taxation thesaurus:related
ln econ:fiscal_policy gov:tax thesaurus:related
def "econ:monetary_policy" "A central bank's use of interest rates and money supply (金融政策)."
ln econ:monetary_policy econ thesaurus:related
ln econ:monetary_policy econ_field:macro econ:field
ln econ:monetary_policy fin:interest_rate thesaurus:related
ln econ:monetary_policy fx:exchange_rate thesaurus:related
def "econ:central_bank" "The authority managing money and interest rates (中央銀行)."
ln econ:central_bank econ thesaurus:related
ln econ:central_bank econ_field:macro econ:field
ln econ:central_bank place:bank thesaurus:related
ln econ:central_bank admin:country thesaurus:related
def "econ:money_supply" "The total money circulating in an economy."
ln econ:money_supply econ thesaurus:related
ln econ:money_supply econ_field:macro econ:field
def "econ:aggregate_demand" "Total demand for output across the economy."
ln econ:aggregate_demand econ thesaurus:related
ln econ:aggregate_demand econ_field:macro econ:field
def "econ:aggregate_supply" "Total output supplied across the economy."
ln econ:aggregate_supply econ thesaurus:related
ln econ:aggregate_supply econ_field:macro econ:field
def "econ:stagflation" "Stagnation with inflation together — a policy dilemma."
ln econ:stagflation econ thesaurus:related
ln econ:stagflation econ_field:macro econ:field
def "econ:balance_of_payments" "The record of a country's transactions with the world."
ln econ:balance_of_payments econ thesaurus:related
ln econ:balance_of_payments econ_field:macro econ:field
ln econ:balance_of_payments fx:foreign_exchange thesaurus:related
def "econ:national_debt" "The total the government owes (国債残高)."
ln econ:national_debt econ thesaurus:related
ln econ:national_debt econ_field:macro econ:field
ln econ:national_debt fin:bond thesaurus:related
ln econ:national_debt gov:tax thesaurus:related
def "econ:keynesian_economics" "The view that demand management can stabilise the economy."
ln econ:keynesian_economics econ thesaurus:related
ln econ:keynesian_economics econ_field:macro econ:field
def "econ:monetarism" "The view that controlling money supply is key to stability."
ln econ:monetarism econ thesaurus:related
ln econ:monetarism econ_field:macro econ:field
def "econ:trade" "The exchange of goods and services within and between economies."
ln econ:trade econ thesaurus:related
ln econ:trade econ_field:macro econ:field
ln econ:trade fx:foreign_exchange thesaurus:related
ln econ:trade foodstud:spice_trade thesaurus:related
# ── bridges ──
ln econ:central_bank fin:money_market thesaurus:related
ln econ:fiscal_policy gov:function:welfare thesaurus:related
