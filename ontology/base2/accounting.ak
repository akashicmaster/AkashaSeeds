# Akasha ontology — accounting & bookkeeping (会計・簿記).
# Greenfield domain. Bridged to occupation:accountant/auditor, place:bank,
# gov:tax and person:field:economics. Base pack.

def "acct" "Accounting — recording, classifying and reporting financial activity."
# ── bookkeeping fundamentals (簿記) ──
def "acct:double_entry" "Every transaction recorded twice — a debit and an equal credit — so the books always balance (複式簿記)."
ln acct:double_entry acct thesaurus:related
def "acct:debit" "The left side of an entry; increases assets/expenses, decreases liabilities/equity."
ln acct:debit acct thesaurus:related
def "acct:credit" "The right side of an entry; increases liabilities/equity/revenue, decreases assets."
ln acct:credit acct thesaurus:related
def "acct:account" "A record of all changes to one item (cash, sales, wages…) (勘定)."
ln acct:account acct thesaurus:related
def "acct:journal" "The book of original entry where transactions are first recorded in order (仕訳帳)."
ln acct:journal acct thesaurus:related
def "acct:ledger" "The book where journal entries are posted and grouped by account (元帳)."
ln acct:ledger acct thesaurus:related
ln acct:ledger acct:account thesaurus:related
def "acct:journal_entry" "A single dated record of a transaction as debits and credits (仕訳)."
ln acct:journal_entry acct thesaurus:related
def "acct:posting" "Transferring journal entries into the ledger accounts."
ln acct:posting acct thesaurus:related
def "acct:trial_balance" "A list of all account balances, checking that debits equal credits (試算表)."
ln acct:trial_balance acct thesaurus:related
def "acct:chart_of_accounts" "The organised list of every account a business uses (勘定科目表)."
ln acct:chart_of_accounts acct thesaurus:related
def "acct:reconciliation" "Checking one record against another (e.g. books vs bank statement) to agree them."
ln acct:reconciliation acct thesaurus:related
ln acct:reconciliation place:bank thesaurus:related
# ── the accounting equation (貸借) ──
def "acct:accounting_equation" "Assets = Liabilities + Equity — the identity the balance sheet always upholds."
ln acct:accounting_equation acct thesaurus:related
def "acct:asset" "A resource owned that has value (cash, stock, equipment, receivables) (資産)."
ln acct:asset acct thesaurus:related
def "acct:liability" "An obligation owed to others (loans, payables) (負債)."
ln acct:liability acct thesaurus:related
def "acct:equity" "The owners' residual claim after liabilities — assets minus liabilities (純資産/資本)."
ln acct:equity acct thesaurus:related
def "acct:revenue" "Income earned from operations (sales, fees) (収益)."
ln acct:revenue acct thesaurus:related
ln acct:revenue acct:income_statement thesaurus:related
def "acct:expense" "The cost of earning revenue (wages, rent, materials) (費用)."
ln acct:expense acct thesaurus:related
ln acct:expense gov:tax thesaurus:related
def "acct:accounts_receivable" "Money owed to the business by customers (売掛金)."
ln acct:accounts_receivable acct thesaurus:related
def "acct:accounts_payable" "Money the business owes to suppliers (買掛金)."
ln acct:accounts_payable acct thesaurus:related
def "acct:cost_of_goods_sold" "The direct cost of the goods a business sold (売上原価)."
ln acct:cost_of_goods_sold acct thesaurus:related
def "acct:net_income" "Revenue minus all expenses — the bottom-line profit or loss (純利益)."
ln acct:net_income acct thesaurus:related
def "acct:retained_earnings" "Accumulated profits kept in the business rather than paid out."
ln acct:retained_earnings acct thesaurus:related
# ── principles & adjustments ──
def "acct:accrual_accounting" "Recording revenue and expenses when earned/incurred, not when cash moves (発生主義)."
ln acct:accrual_accounting acct thesaurus:related
def "acct:cash_accounting" "Recording only when cash actually changes hands (現金主義)."
ln acct:cash_accounting acct thesaurus:related
def "acct:matching_principle" "Matching expenses to the revenue they help earn, in the same period."
ln acct:matching_principle acct thesaurus:related
def "acct:depreciation" "Spreading a fixed asset's cost over its useful life (減価償却)."
ln acct:depreciation acct thesaurus:related
def "acct:amortization" "Depreciation applied to intangible assets or spreading a loan over time."
ln acct:amortization acct thesaurus:related
def "acct:fiscal_year" "The 12-month period a business reports on (会計年度)."
ln acct:fiscal_year acct thesaurus:related
def "acct:provision" "An amount set aside for a probable future liability."
ln acct:provision acct thesaurus:related
def "acct:going_concern" "The assumption that the business will continue operating."
ln acct:going_concern acct thesaurus:related
# ── financial statements (財務諸表) ──
def "acct:financial_statements" "The formal reports summarising a business's finances (財務諸表)."
ln acct:financial_statements acct thesaurus:related
def "acct:balance_sheet" "A snapshot of assets, liabilities and equity at a point in time (貸借対照表/BS)."
ln acct:balance_sheet acct thesaurus:related
ln acct:balance_sheet acct:accounting_equation thesaurus:related
def "acct:income_statement" "Revenue, expenses and profit over a period — the P&L (損益計算書/PL)."
ln acct:income_statement acct thesaurus:related
ln acct:income_statement acct:net_income thesaurus:related
def "acct:cash_flow_statement" "Cash in and out, split into operating, investing and financing (キャッシュフロー計算書)."
ln acct:cash_flow_statement acct thesaurus:related
def "acct:notes_to_accounts" "Explanatory disclosures accompanying the statements."
ln acct:notes_to_accounts acct thesaurus:related
# ── branches, standards & roles ──
def "acct:financial_accounting" "Reporting to outside parties under set standards."
ln acct:financial_accounting acct thesaurus:related
ln acct:financial_accounting person:field:economics thesaurus:related
def "acct:managerial_accounting" "Internal reporting to help managers decide."
ln acct:managerial_accounting acct thesaurus:related
def "acct:cost_accounting" "Measuring and controlling the cost of producing goods/services."
ln acct:cost_accounting acct thesaurus:related
def "acct:tax_accounting" "Preparing accounts and returns for taxation."
ln acct:tax_accounting acct thesaurus:related
ln acct:tax_accounting gov:tax thesaurus:related
ln acct:tax_accounting gov:tax:corporate_tax thesaurus:related
ln acct:tax_accounting gov:tax_return thesaurus:related
def "acct:auditing" "Independent examination of accounts for a true and fair view (監査)."
ln acct:auditing acct thesaurus:related
ln acct:auditing occupation:accountant thesaurus:related
def "acct:gaap" "Generally Accepted Accounting Principles — a national standards framework."
ln acct:gaap acct thesaurus:related
def "acct:ifrs" "International Financial Reporting Standards — the global framework."
ln acct:ifrs acct thesaurus:related
def "acct:bookkeeper" "One who records the day-to-day transactions."
ln acct:bookkeeper acct thesaurus:related
ln acct:bookkeeper occupation:accountant thesaurus:related
def "acct:auditor" "One who independently audits the accounts."
ln acct:auditor acct thesaurus:related
ln acct:auditor occupation:accountant thesaurus:related
ln acct occupation:accountant thesaurus:related
