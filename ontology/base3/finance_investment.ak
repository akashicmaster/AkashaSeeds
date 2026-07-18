# Akasha ontology — finance & investment.
# Corporate & personal finance, markets, instruments, and investing. Bridged to
# acct:, place:bank, gov:tax, gov:benefit:pension, work:salary, economics. Base pack.

def "fin" "Finance — the management of money, funding and value over time."
# ── corporate finance ──
def "fin:corporate_finance" "How firms raise, invest and manage capital to create value."
ln fin:corporate_finance fin thesaurus:related
def "fin:capital" "The funds (equity + debt) a business uses to operate and grow (資本)."
ln fin:capital fin thesaurus:related
ln fin:capital acct:equity thesaurus:related
def "fin:working_capital" "Current assets minus current liabilities — short-term operating liquidity (運転資本)."
ln fin:working_capital fin thesaurus:related
def "fin:capital_structure" "The mix of debt and equity financing a firm uses."
ln fin:capital_structure fin thesaurus:related
def "fin:cost_of_capital" "The required return needed to justify an investment; WACC blends debt and equity costs."
ln fin:cost_of_capital fin thesaurus:related
def "fin:leverage" "Using borrowed money to amplify returns — and risk (レバレッジ)."
ln fin:leverage fin thesaurus:related
def "fin:liquidity" "How easily assets convert to cash without loss of value (流動性)."
ln fin:liquidity fin thesaurus:related
def "fin:solvency" "The ability to meet long-term obligations."
ln fin:solvency fin thesaurus:related
def "fin:cash_flow" "The movement of cash into and out of a business (キャッシュフロー)."
ln fin:cash_flow fin thesaurus:related
def "fin:budgeting" "Planning income and expenditure over a period (予算)."
ln fin:budgeting fin thesaurus:related
ln fin:budgeting acct:fiscal_year thesaurus:related
# ── financial ratios ──
def "fin:financial_ratio" "A ratio of statement figures used to gauge performance and health."
ln fin:financial_ratio fin thesaurus:related
def "fin:roi" "Return on investment — gain relative to cost."
ln fin:roi fin thesaurus:related
def "fin:roe" "Return on equity — net income over shareholders' equity."
ln fin:roe fin thesaurus:related
ln fin:roe acct:equity thesaurus:related
def "fin:current_ratio" "Current assets over current liabilities — short-term solvency."
ln fin:current_ratio fin thesaurus:related
def "fin:debt_to_equity" "Total debt over equity — a leverage measure."
ln fin:debt_to_equity fin thesaurus:related
def "fin:gross_margin" "Gross profit as a percentage of revenue."
ln fin:gross_margin fin thesaurus:related
def "fin:net_margin" "Net income as a percentage of revenue."
ln fin:net_margin fin thesaurus:related
ln fin:net_margin acct:income_statement thesaurus:related
def "fin:eps" "Earnings per share — net income per outstanding share."
ln fin:eps fin thesaurus:related
ln fin:eps acct:net_income thesaurus:related
def "fin:pe_ratio" "Price-to-earnings — share price over EPS, a valuation gauge."
ln fin:pe_ratio fin thesaurus:related
def "fin:dividend_yield" "Annual dividend as a percentage of share price."
ln fin:dividend_yield fin thesaurus:related
# ── markets & instruments ──
def "fin:financial_market" "A marketplace for trading financial assets."
ln fin:financial_market fin thesaurus:related
def "fin:stock_market" "Where shares of companies are issued and traded (株式市場)."
ln fin:stock_market fin thesaurus:related
def "fin:bond_market" "Where debt securities are issued and traded (債券市場)."
ln fin:bond_market fin thesaurus:related
def "fin:money_market" "Short-term, low-risk lending and borrowing."
ln fin:money_market fin thesaurus:related
def "fin:forex_market" "The market for trading currencies."
ln fin:forex_market fin thesaurus:related
def "fin:security" "A tradable financial asset (証券)."
ln fin:security fin thesaurus:related
def "fin:stock" "A share of ownership in a company (株式)."
ln fin:stock fin thesaurus:related
ln fin:stock fin:stock_market thesaurus:related
def "fin:bond" "A debt security paying interest and repaying principal (債券)."
ln fin:bond fin thesaurus:related
ln fin:bond fin:bond_market thesaurus:related
def "fin:derivative" "A contract whose value derives from an underlying asset."
ln fin:derivative fin thesaurus:related
def "fin:option" "A right, not obligation, to buy/sell at a set price."
ln fin:option fin thesaurus:related
def "fin:futures_contract" "An obligation to buy/sell an asset at a future date and price."
ln fin:futures_contract fin thesaurus:related
def "fin:mutual_fund" "A pooled fund professionally managed across many assets (投資信託)."
ln fin:mutual_fund fin thesaurus:related
def "fin:etf" "An exchange-traded fund tracking an index, traded like a stock."
ln fin:etf fin thesaurus:related
def "fin:index_fund" "A fund that passively tracks a market index."
ln fin:index_fund fin thesaurus:related
def "fin:reit" "A real-estate investment trust holding income property."
ln fin:reit fin thesaurus:related
ln fin:reit fin:stock thesaurus:related
def "fin:dividend" "A share of profit paid to shareholders (配当)."
ln fin:dividend fin thesaurus:related
ln fin:dividend fin:dividend_yield thesaurus:related
def "fin:ipo" "Initial public offering — a company's first sale of shares to the public."
ln fin:ipo fin thesaurus:related
def "fin:valuation" "Estimating what an asset or company is worth (企業価値評価)."
ln fin:valuation fin thesaurus:related
ln fin:valuation acct:balance_sheet thesaurus:related
def "fin:market_capitalization" "Share price times shares outstanding — a company's market value."
ln fin:market_capitalization fin thesaurus:related
# ── banking & personal finance ──
def "fin:savings_account" "A bank account that holds money and earns interest."
ln fin:savings_account fin thesaurus:related
ln fin:savings_account place:bank thesaurus:related
def "fin:checking_account" "A bank account for everyday payments."
ln fin:checking_account fin thesaurus:related
ln fin:checking_account place:bank thesaurus:related
def "fin:loan" "Borrowed money repaid with interest (ローン)."
ln fin:loan fin thesaurus:related
ln fin:loan place:bank thesaurus:related
def "fin:mortgage" "A loan secured against property (住宅ローン)."
ln fin:mortgage fin thesaurus:related
ln fin:mortgage place:bank thesaurus:related
ln fin:mortgage home:dwelling:detached_house thesaurus:related
def "fin:interest_rate" "The price of borrowing, as a percentage (金利)."
ln fin:interest_rate fin thesaurus:related
ln fin:interest_rate fin:compound_interest thesaurus:related
def "fin:compound_interest" "Interest earned on interest — growth that accelerates over time (複利)."
ln fin:compound_interest fin thesaurus:related
def "fin:credit_score" "A rating of a borrower's creditworthiness."
ln fin:credit_score fin thesaurus:related
def "fin:debt" "Money owed (借金/負債)."
ln fin:debt fin thesaurus:related
ln fin:debt acct:liability thesaurus:related
def "fin:inflation" "A general rise in prices, eroding money's purchasing power (インフレ)."
ln fin:inflation fin thesaurus:related
def "fin:personal_budget" "A household plan for income and spending (家計)."
ln fin:personal_budget fin thesaurus:related
ln fin:personal_budget work:salary thesaurus:related
ln fin:personal_budget concept:daily_necessities thesaurus:related
# ── investment ──
def "invest" "Investment — committing capital now for future return."
def "invest:investment" "Committing money to an asset expecting future income or gain."
ln invest:investment invest thesaurus:related
def "invest:portfolio" "An investor's collection of holdings (ポートフォリオ)."
ln invest:portfolio invest thesaurus:related
ln invest:portfolio fin:stock thesaurus:related
ln invest:portfolio fin:bond thesaurus:related
def "invest:diversification" "Spreading investments to reduce risk ('not all eggs in one basket')."
ln invest:diversification invest thesaurus:related
def "invest:asset_allocation" "Dividing a portfolio across asset classes (stocks/bonds/cash)."
ln invest:asset_allocation invest thesaurus:related
def "invest:risk" "The chance that actual returns differ from expected (リスク)."
ln invest:risk invest thesaurus:related
def "invest:return" "The gain or loss on an investment over time (リターン)."
ln invest:return invest thesaurus:related
def "invest:risk_tolerance" "How much risk an investor can bear."
ln invest:risk_tolerance invest thesaurus:related
def "invest:time_value_of_money" "A sum today is worth more than the same sum later — the root of finance."
ln invest:time_value_of_money invest thesaurus:related
ln invest:time_value_of_money fin:compound_interest thesaurus:related
def "invest:present_value" "Today's worth of a future cash flow, discounted."
ln invest:present_value invest thesaurus:related
def "invest:compound_return" "Return compounding over time, the engine of long-term wealth."
ln invest:compound_return invest thesaurus:related
def "invest:yield" "The income from an investment as a percentage."
ln invest:yield invest thesaurus:related
ln invest:yield fin:dividend_yield thesaurus:related
def "invest:capital_gain" "Profit from selling an asset above its purchase price (譲渡益)."
ln invest:capital_gain invest thesaurus:related
ln invest:capital_gain gov:tax:income_tax thesaurus:related
ln invest:capital_gain gov:tax thesaurus:related
def "invest:dollar_cost_averaging" "Investing fixed amounts regularly to smooth out price swings (積立投資)."
ln invest:dollar_cost_averaging invest thesaurus:related
ln invest:dollar_cost_averaging gov:benefit:pension thesaurus:related
def "invest:value_investing" "Buying assets priced below intrinsic value (Graham/Buffett)."
ln invest:value_investing invest thesaurus:related
ln invest:value_investing fin:valuation thesaurus:related
def "invest:growth_investing" "Buying companies expected to grow fast."
ln invest:growth_investing invest thesaurus:related
def "invest:passive_investing" "Tracking the market cheaply via index funds rather than picking."
ln invest:passive_investing invest thesaurus:related
ln invest:passive_investing fin:index_fund thesaurus:related
ln invest:passive_investing fin:etf thesaurus:related
def "invest:buy_and_hold" "Holding investments long-term through ups and downs."
ln invest:buy_and_hold invest thesaurus:related
def "invest:hedging" "Taking an offsetting position to limit risk."
ln invest:hedging invest thesaurus:related
def "invest:fundamental_analysis" "Valuing an asset from its financials and prospects."
ln invest:fundamental_analysis invest thesaurus:related
ln invest:fundamental_analysis acct:financial_statements thesaurus:related
ln invest:fundamental_analysis fin:pe_ratio thesaurus:related
def "invest:technical_analysis" "Forecasting from price and volume patterns."
ln invest:technical_analysis invest thesaurus:related
def "invest:modern_portfolio_theory" "Optimising return for a given risk by diversification (Markowitz)."
ln invest:modern_portfolio_theory invest thesaurus:related
def "invest:efficient_market_hypothesis" "The idea that prices already reflect all information."
ln invest:efficient_market_hypothesis invest thesaurus:related
def "invest:volatility" "The degree of variation in an asset's price."
ln invest:volatility invest thesaurus:related
def "invest:compound_interest" "See fin:compound_interest — the same force driving investment growth."
ln invest:compound_interest invest thesaurus:related
ln invest:compound_interest fin:compound_interest thesaurus:related
# ── retirement & the pension bridge ──
def "invest:retirement_account" "A tax-advantaged account for retirement saving (401k/IRA/iDeCo/NISA)."
ln invest:retirement_account invest thesaurus:related
ln invest:retirement_account gov:benefit:pension thesaurus:related
ln invest:retirement_account work:retirement thesaurus:related
ln fin occupation:banker thesaurus:related
ln fin place:bank thesaurus:related
ln invest person:field:economics thesaurus:related
