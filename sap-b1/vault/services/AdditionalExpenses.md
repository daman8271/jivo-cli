---
entity: AdditionalExpenses
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 11
---
# AdditionalExpenses
Defines freight/additional expense types (e.g. shipping, handling) that can be added to marketing documents, with their G/L account and tax mappings. Live rows in JIVO_OIL_HANADB: 11.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AdditionalExpenses --top 5
./sapb1 query AdditionalExpenses --count
./sapb1 query AdditionalExpenses --select "ExpensCode,Name,ExpenseAccount,DistributionMethod" --top 10
# expense types that are tax liable
./sapb1 query AdditionalExpenses --filter "TaxLiable eq 'tYES'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| ExpensCode | Expense type key |
| Name | Expense description |
| ExpenseAccount | Purchase-side G/L account |
| RevenuesAccount | Sales-side G/L account |
| FreightOffsetAccount | Freight offset account |
| InputVATGroup | Purchase tax group |
| OutputVATGroup | Sales tax group |
| FixedAmountExpenses | Fixed purchase amount |
| FixedAmountRevenues | Fixed sales amount |
| LastPurchasePrice | Include in last price |
| DistributionMethod | Line allocation method |
| Project | Default project code |
| TaxLiable | Subject to tax |
| Stock | Affects inventory value |
## Connections
- Domain: [[system-other-1]]
- [[ChartOfAccounts]] via ExpenseAccount / RevenuesAccount / FreightOffsetAccount — G/L posting accounts
- [[VatGroups]] via InputVATGroup / OutputVATGroup — tax groups applied to the expense
- [[Projects]] via Project — default project assigned to the expense
