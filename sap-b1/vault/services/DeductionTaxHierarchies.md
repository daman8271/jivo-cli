---
entity: DeductionTaxHierarchies
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# DeductionTaxHierarchies
Hierarchy levels linking deduction tax groups and subgroups for deduction-at-source reporting (unused). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DeductionTaxHierarchies --top 5
./sapb1 query DeductionTaxHierarchies --count
./sapb1 fields DeductionTaxHierarchies   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query DeductionTaxHierarchies --filter "Code ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields DeductionTaxHierarchies` |

## Connections
- Domain: [[financials-accounting-1]]
- [[DeductionTaxGroups]] via group code — hierarchy levels organize the deduction groups
- [[DeductionTaxSubGroups]] via subgroup code — and their subgroup breakdown
