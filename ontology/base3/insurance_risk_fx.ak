# Akasha ontology — insurance, foreign exchange & risk management (保険・為替・リスク管理).
# Extends fin:/invest:. Bridged to gov:benefit:, place:bank, admin:country. Base pack.

def "insur" "Insurance — pooling risk against uncertain loss."
def "insur:insurance" "A contract transferring the risk of loss to an insurer for a premium (保険)."
ln insur:insurance insur thesaurus:related
def "insur:policy" "The insurance contract setting out cover and terms (保険契約)."
ln insur:policy insur thesaurus:related
def "insur:premium" "The price paid for insurance cover (保険料)."
ln insur:premium insur thesaurus:related
def "insur:insurer" "The company that carries the risk and pays claims."
ln insur:insurer insur thesaurus:related
def "insur:policyholder" "The person who owns the policy and pays premiums."
ln insur:policyholder insur thesaurus:related
def "insur:beneficiary" "The person who receives the payout (受取人)."
ln insur:beneficiary insur thesaurus:related
def "insur:claim" "A request for payment under a policy (保険金請求)."
ln insur:claim insur thesaurus:related
def "insur:deductible" "The amount the insured pays before cover starts (免責額)."
ln insur:deductible insur thesaurus:related
def "insur:coverage" "The scope of risks a policy protects against (補償範囲)."
ln insur:coverage insur thesaurus:related
def "insur:underwriting" "Assessing risk and setting terms/price for a policy."
ln insur:underwriting insur thesaurus:related
def "insur:actuary" "A specialist who prices risk using statistics and probability (保険数理士)."
ln insur:actuary insur thesaurus:related
ln insur:actuary person:field:mathematics thesaurus:related
def "insur:actuarial_science" "The mathematics of risk, longevity and insurance pricing."
ln insur:actuarial_science insur thesaurus:related
ln insur:actuarial_science person:field:mathematics thesaurus:related
def "insur:risk_pool" "Many premiums pooled to pay the losses of the few — the core mechanism."
ln insur:risk_pool insur thesaurus:related
ln insur:risk_pool risk:risk_management thesaurus:related
def "insur:reinsurance" "Insurance bought by insurers to spread their own risk."
ln insur:reinsurance insur thesaurus:related
def "insur:moral_hazard" "When being insured makes one take more risk."
ln insur:moral_hazard insur thesaurus:related
def "insur:adverse_selection" "When the riskiest are likeliest to buy insurance, skewing the pool."
ln insur:adverse_selection insur thesaurus:related
def "insur:indemnity" "Restoring the insured to their pre-loss position, no more."
ln insur:indemnity insur thesaurus:related
# ── insurance types (保険の種類) ──
def "insur:life_insurance" "Pays out on death (or maturity) (生命保険)."
ln insur:life_insurance insur thesaurus:related
def "insur:health_insurance" "Covers medical costs (医療保険)."
ln insur:health_insurance insur thesaurus:related
ln insur:health_insurance place:hospital thesaurus:related
ln insur:health_insurance gov:benefit:social_security thesaurus:related
def "insur:auto_insurance" "Covers vehicle damage and liability (自動車保険)."
ln insur:auto_insurance insur thesaurus:related
ln insur:auto_insurance gov:service:police thesaurus:related
def "insur:property_insurance" "Covers damage to buildings and contents (火災保険)."
ln insur:property_insurance insur thesaurus:related
ln insur:property_insurance home:dwelling:detached_house thesaurus:related
def "insur:liability_insurance" "Covers legal liability to others."
ln insur:liability_insurance insur thesaurus:related
def "insur:disability_insurance" "Replaces income if unable to work."
ln insur:disability_insurance insur thesaurus:related
ln insur:disability_insurance gov:benefit:disability_benefit thesaurus:related
def "insur:social_insurance" "State-run pooled insurance (pension, health, unemployment) (社会保険)."
ln insur:social_insurance insur thesaurus:related
ln insur:social_insurance gov:benefit:social_security thesaurus:related
ln insur:social_insurance gov:benefit:pension thesaurus:related
ln insur:social_insurance gov:benefit:unemployment_benefit thesaurus:related
# ── foreign exchange (為替) ──
def "fx" "Foreign exchange — the trading and valuation of currencies."
def "fx:foreign_exchange" "The conversion and trading of one currency for another (外国為替)."
ln fx:foreign_exchange fx thesaurus:related
ln fx:foreign_exchange fin:forex_market thesaurus:related
def "fx:exchange_rate" "The price of one currency in terms of another (為替レート)."
ln fx:exchange_rate fx thesaurus:related
def "fx:currency" "A nation's money (通貨)."
ln fx:currency fx thesaurus:related
ln fx:currency admin:country thesaurus:related
def "fx:currency_pair" "Two currencies quoted against each other (e.g. USD/JPY)."
ln fx:currency_pair fx thesaurus:related
def "fx:spot_rate" "The rate for immediate exchange."
ln fx:spot_rate fx thesaurus:related
def "fx:forward_rate" "An agreed rate for exchange at a future date."
ln fx:forward_rate fx thesaurus:related
def "fx:appreciation" "A currency rising in value (通貨高)."
ln fx:appreciation fx thesaurus:related
def "fx:currency_depreciation" "A currency falling in value (通貨安)."
ln fx:currency_depreciation fx thesaurus:related
def "fx:floating_exchange_rate" "A rate set by the market (変動相場制)."
ln fx:floating_exchange_rate fx thesaurus:related
def "fx:fixed_exchange_rate" "A rate pegged by authorities (固定相場制)."
ln fx:fixed_exchange_rate fx thesaurus:related
def "fx:devaluation" "A deliberate lowering of a pegged currency."
ln fx:devaluation fx thesaurus:related
def "fx:currency_hedging" "Protecting against adverse exchange-rate moves."
ln fx:currency_hedging fx thesaurus:related
ln fx:currency_hedging invest:hedging thesaurus:related
def "fx:arbitrage" "Profiting from price differences across markets."
ln fx:arbitrage fx thesaurus:related
ln fx:arbitrage fin:financial_market thesaurus:related
def "fx:carry_trade" "Borrowing a low-rate currency to invest in a higher-rate one."
ln fx:carry_trade fx thesaurus:related
def "fx:reserve_currency" "A currency widely held by central banks (e.g. the US dollar)."
ln fx:reserve_currency fx thesaurus:related
ln fx:reserve_currency admin:country thesaurus:related
def "fx:purchasing_power_parity" "The theory that exchange rates equalise price levels (PPP)."
ln fx:purchasing_power_parity fx thesaurus:related
ln fx:purchasing_power_parity econ:inflation thesaurus:related
def "fx:remittance" "Money sent home by workers abroad (送金)."
ln fx:remittance fx thesaurus:related
# ── risk management (リスク管理) ──
def "risk" "Risk management — identifying, assessing and controlling exposure to loss."
def "risk:risk_management" "The systematic handling of risks that threaten objectives (リスク管理)."
ln risk:risk_management risk thesaurus:related
ln risk:risk_management invest:risk thesaurus:related
ln risk:risk_management fin:corporate_finance thesaurus:related
def "risk:risk_assessment" "Estimating the likelihood and impact of risks."
ln risk:risk_assessment risk thesaurus:related
def "risk:risk_mitigation" "Reducing a risk's probability or impact."
ln risk:risk_mitigation risk thesaurus:related
def "risk:risk_transfer" "Shifting risk to another party — the essence of insurance."
ln risk:risk_transfer risk thesaurus:related
ln risk:risk_transfer insur:insurance thesaurus:related
def "risk:risk_avoidance" "Not taking on the risk at all."
ln risk:risk_avoidance risk thesaurus:related
def "risk:risk_retention" "Deliberately bearing a risk oneself."
ln risk:risk_retention risk thesaurus:related
def "risk:systematic_risk" "Market-wide risk that cannot be diversified away (市場リスク)."
ln risk:systematic_risk risk thesaurus:related
ln risk:systematic_risk invest:risk thesaurus:related
ln risk:systematic_risk invest:diversification thesaurus:related
def "risk:unsystematic_risk" "Asset-specific risk that diversification can remove."
ln risk:unsystematic_risk risk thesaurus:related
ln risk:unsystematic_risk invest:diversification thesaurus:related
def "risk:credit_risk" "The risk a borrower defaults."
ln risk:credit_risk risk thesaurus:related
ln risk:credit_risk fin:credit_score thesaurus:related
def "risk:liquidity_risk" "The risk of being unable to sell without loss."
ln risk:liquidity_risk risk thesaurus:related
def "risk:operational_risk" "Risk from failed processes, people or systems."
ln risk:operational_risk risk thesaurus:related
def "risk:value_at_risk" "A statistical estimate of the maximum likely loss over a period (VaR)."
ln risk:value_at_risk risk thesaurus:related
ln risk:value_at_risk invest:volatility thesaurus:related
def "risk:beta" "An asset's sensitivity to market moves."
ln risk:beta risk thesaurus:related
def "risk:sharpe_ratio" "Return earned per unit of risk taken."
ln risk:sharpe_ratio risk thesaurus:related
ln risk:sharpe_ratio invest:return thesaurus:related
ln risk:sharpe_ratio invest:volatility thesaurus:related
def "risk:stress_test" "Modelling performance under extreme adverse scenarios."
ln risk:stress_test risk thesaurus:related
def "risk:tail_risk" "The risk of rare, extreme 'black swan' events."
ln risk:tail_risk risk thesaurus:related
def "risk:expected_value" "The probability-weighted average of possible outcomes."
ln risk:expected_value risk thesaurus:related
ln risk:expected_value person:field:mathematics thesaurus:related
def "risk:uncertainty" "Unquantifiable unknowns, distinct from measurable risk (Knight)."
ln risk:uncertainty risk thesaurus:related
