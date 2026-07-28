---
entity: ChartOfAccounts
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1423
---
# ChartOfAccounts
The company's G/L account master (chart of accounts) with hierarchy, types, currencies and live balances — the backbone of all journal postings. Live rows in JIVO_OIL_HANADB: 1423.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ChartOfAccounts --top 5
./sapb1 query ChartOfAccounts --count
./sapb1 query ChartOfAccounts --select "Code,Name,AccountType,Balance" --top 10
# Active revenue accounts only (at_Revenues / at_Expenses / at_Other):
./sapb1 query ChartOfAccounts --filter "ActiveAccount eq 'tYES' and AccountType eq 'at_Revenues'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| Code | G/L account code (key) |
| Name | Account name |
| AccountType | Revenue / expense / other |
| AccountLevel | Depth in hierarchy |
| FatherAccountKey | Parent (title) account |
| Category | Report category drawer |
| AcctCurrency | Account currency |
| Balance | Current balance (local) |
| Balance_syscurr | Balance in system currency |
| ActiveAccount | Active / inactive flag |
| CashAccount | Cash account flag |
| BudgetAccount | Budget-relevant flag |
| DefaultVatGroup | Default VAT/GST group |
| BPLID | Branch / business place |

## Connections
- Domain: [[financials-accounting-1]]
- [[AccountCategory]] via Category = CategoryCode — the financial-report drawer the account sits in
- [[VatGroups]] via DefaultVatGroup — default tax group applied on postings
- [[Currencies]] via AcctCurrency = Code — the account's posting currency
- [[CostElements]] via account-to-cost-element mapping — cost accounting analysis of expense accounts
- [[BusinessPlaces]] via BPLID — branch the account is assigned to
