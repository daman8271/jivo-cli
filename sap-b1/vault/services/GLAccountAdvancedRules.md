---
entity: GLAccountAdvancedRules
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 318
---
# GLAccountAdvancedRules
Advanced G/L account determination rules that override default posting accounts per item/item-group/BP criteria. Live rows in JIVO_OIL_HANADB: 318.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query GLAccountAdvancedRules --top 5
./sapb1 query GLAccountAdvancedRules --count
./sapb1 query GLAccountAdvancedRules --select "Code,Description,ItemGroup,InventoryAccount" --top 10
```
Useful filter — only the rules currently in force:
```bash
./sapb1 query GLAccountAdvancedRules --filter "IsActive eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsoluteEntry | Internal entry number (key) |
| Code | Rule code |
| Description | Rule description |
| IsActive | Rule active flag |
| ItemCode | Item the rule matches |
| ItemGroup | Item group the rule matches |
| BPCode | Business partner it matches |
| BPGroup | BP group it matches |
| FinancialYear | Fiscal year scope |
| FromDate | Effective-from date |
| InventoryAccount | Override inventory account |
| ExpensesAccount | Override expense account |
| PurchaseAcct | Override purchase account |
| SalesAcct | Override sales revenue account |

## Connections
- Domain: [[financials-accounting-2]]
- [[ChartOfAccounts]] via the override account fields (InventoryAccount, SalesAcct, …)
- [[Items]] via ItemCode criterion
- [[ItemGroups]] via ItemGroup criterion
- [[BusinessPartners]] via BPCode criterion
- [[Warehouses]] via warehouse-scoped determination criteria
