---
entity: DeductionTaxGroups
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# DeductionTaxGroups
Withholding/deduction-at-source tax groups (Israel-style deduction localization, unused in this Indian DB). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DeductionTaxGroups --top 5
./sapb1 query DeductionTaxGroups --count
./sapb1 fields DeductionTaxGroups   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query DeductionTaxGroups --filter "Code ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields DeductionTaxGroups` |

## Connections
- Domain: [[financials-accounting-1]]
- [[DeductionTaxSubGroups]] via group code — subgroups break a deduction group down further
- [[DeductionTaxHierarchies]] via group code — hierarchy levels tie groups and subgroups together
- [[BusinessPartners]] via deduction group assignment — BPs subject to deduction-at-source reference a group
