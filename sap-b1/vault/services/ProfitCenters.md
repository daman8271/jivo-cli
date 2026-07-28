---
entity: ProfitCenters
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 198
---
# ProfitCenters
Cost/profit centers (198 in JIVO_OIL) used for dimensional cost accounting and P&L segmentation. Live rows in JIVO_OIL_HANADB: 198.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ProfitCenters --top 5
./sapb1 query ProfitCenters --count
./sapb1 query ProfitCenters --select "CenterCode,CenterName,InWhichDimension,Active" --top 10
```
Useful filter — active centers in dimension 1 (the primary P&L axis):
```bash
./sapb1 query ProfitCenters --filter "Active eq 'tYES' and InWhichDimension eq 1" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| CenterCode | Cost/profit center code (key) |
| CenterName | Center name |
| CenterOwner | Responsible owner/employee |
| CostCenterType | Center type classification |
| GroupCode | Parent center group |
| InWhichDimension | Cost dimension (1–5) |
| EffectiveFrom | Valid-from date |
| EffectiveTo | Valid-to date |
| Active | Active flag |
| U_Co_Owner | UDF: co-owner |

## Connections
- Domain: [[financials-accounting-2]]
- [[DistributionRules]] via DistributionRuleLines.ProfitCenter — rules spread amounts across these centers
- [[JournalEntries]] via JournalEntryLines.CostingCode — JE lines carry the center for segmented P&L
