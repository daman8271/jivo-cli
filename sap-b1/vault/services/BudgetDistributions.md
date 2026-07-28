---
entity: BudgetDistributions
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# BudgetDistributions
Budget distribution methods that spread an annual budget amount across the 12 months (equal, ascending, etc.). Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BudgetDistributions --top 5
./sapb1 query BudgetDistributions --count
./sapb1 query BudgetDistributions --select "DivisionCode,Description,BudgetAmount,January" --top 10
# Inspect one distribution method by its code:
./sapb1 query BudgetDistributions --filter "DivisionCode eq 1"
```

## Key fields
| Field | Meaning |
|---|---|
| DivisionCode | Distribution method code (key) |
| Description | Method description |
| BudgetAmount | Reference annual amount |
| January | January share/weight |
| February | February share/weight |
| March | March share/weight |
| April | April share/weight |
| December | December share/weight |

## Connections
- Domain: [[financials-accounting-1]]
- [[Budgets]] via DivisionCode — budget rows reference a distribution method to spread annual amounts monthly
