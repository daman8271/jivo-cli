---
entity: TaxCodeDeterminationsTCD
domain: financials-accounting-2
readable: true
methods: [GET, PATCH]
rows_oil: 4
---
# TaxCodeDeterminationsTCD
India/localized TCD tax-code determination setup holding default AP/AR tax codes plus key-field and usage-based rules. Live rows in JIVO_OIL_HANADB: 4.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TaxCodeDeterminationsTCD --top 5
./sapb1 query TaxCodeDeterminationsTCD --count
./sapb1 query TaxCodeDeterminationsTCD --select "AbsId,TcdType,DftApCode,DftArCode" --top 10
```
Useful filter — pull one determination setup with all its nested rule collections:
```bash
./sapb1 query TaxCodeDeterminationsTCD --filter "AbsId eq 1" --json
```

## Key fields
| Field | Meaning |
|---|---|
| AbsId | Internal setup ID (key) |
| TcdType | Determination type (AP/AR etc.) |
| DftApCode | Default AP tax code |
| DftArCode | Default AR tax code |
| TaxCodeDeterminationTCDKeyFields | Key-field criteria lines |
| TaxCodeDeterminationTCDByUsages | Usage-based rule lines |
| TaxCodeDeterminationTCDDefaultWTs | Default withholding-tax lines |

## Connections
- Domain: [[financials-accounting-2]]
- [[VatGroups]] via DftApCode / DftArCode default tax codes
- [[WithholdingTaxCodes]] via TaxCodeDeterminationTCDDefaultWTs default WT lines
