---
entity: DistributionRules
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 194
---
# DistributionRules
Cost-accounting distribution rules that allocate revenues/expenses across cost centers (dimensions) by factor weights. Live rows in JIVO_OIL_HANADB: 194.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DistributionRules --top 5
./sapb1 query DistributionRules --count
./sapb1 query DistributionRules --select "FactorCode,FactorDescription,InWhichDimension,Active" --top 10
```
Useful filter — active rules only (skip retired allocation keys):
```bash
./sapb1 query DistributionRules --filter "Active eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| FactorCode | Distribution rule code (key) |
| FactorDescription | Rule name |
| InWhichDimension | Cost dimension (1–5) it belongs to |
| Active | Rule active flag |
| Direct | Direct-allocation rule flag |
| IsFixedAmount | Allocate by fixed amount vs ratio |
| TotalFactor | Sum of all line factor weights |
| DistributionRuleLines | Per-cost-center factor lines |

## Connections
- Domain: [[financials-accounting-2]]
- [[ProfitCenters]] via DistributionRuleLines.ProfitCenter — each line weights one cost center
- [[JournalEntries]] via JournalEntryLines.CostingCode — JE lines carry the rule code for allocation
