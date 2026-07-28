---
entity: DeductibleTaxes
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# DeductibleTaxes
Deductible-tax percentage definitions for partially deductible input tax (localization feature, unused here). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DeductibleTaxes --top 5
./sapb1 query DeductibleTaxes --count
./sapb1 fields DeductibleTaxes   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query DeductibleTaxes --filter "Code ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields DeductibleTaxes` |

## Connections
- Domain: [[financials-accounting-1]]
- [[VatGroups]] via deductible-tax code — VAT groups can reference a partial-deductibility definition
