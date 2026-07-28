---
entity: DeductionTaxSubGroups
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# DeductionTaxSubGroups
Subgroup breakdown within deduction tax groups for deduction-at-source (unused). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DeductionTaxSubGroups --top 5
./sapb1 query DeductionTaxSubGroups --count
./sapb1 fields DeductionTaxSubGroups   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query DeductionTaxSubGroups --filter "Code ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields DeductionTaxSubGroups` |

## Connections
- Domain: [[financials-accounting-1]]
- [[DeductionTaxGroups]] via group code — each subgroup belongs to one deduction group
- [[DeductionTaxHierarchies]] via subgroup code — hierarchies reference subgroups for reporting
