---
entity: DeterminationCriterias
domain: system-other-1
readable: true
methods: [GET, PATCH]
rows_oil: 14
---
# DeterminationCriterias
Configures G/L account determination criteria (by warehouse, item group, etc.) that steer automatic journal-account selection. Live rows in JIVO_OIL_HANADB: 14.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DeterminationCriterias --top 5
./sapb1 query DeterminationCriterias --count
./sapb1 query DeterminationCriterias --select "DmcId,DeterminationCriteria,IsActive,Priority" --top 10
# Only the criteria actually switched on:
./sapb1 query DeterminationCriterias --filter "IsActive eq 'tYES'" --top 10
```
No POST/DELETE in the catalog for this set — criteria are predefined by SAP and only activated/prioritised via PATCH (out of scope under our read-only rule).

## Key fields
| Field | Meaning |
|---|---|
| DmcId | Criteria record key |
| DeterminationCriteria | Criteria dimension (warehouse, item group…) |
| IsActive | Criteria switched on? |
| Priority | Evaluation order among criteria |

## Connections
- Domain: [[system-other-1]]
