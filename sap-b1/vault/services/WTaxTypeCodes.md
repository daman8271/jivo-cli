---
entity: WTaxTypeCodes
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# WTaxTypeCodes
Withholding-tax type codes categorizing withholding codes by nature of payment (empty via this endpoint). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WTaxTypeCodes --top 5
./sapb1 query WTaxTypeCodes --count
```
(Empty via this endpoint in JIVO_OIL — `--count` returns 0, so there is nothing useful to `--select` or `--filter` yet.)

## Key fields
_No rows exposed via this endpoint in JIVO_OIL_HANADB — field-level recon not captured._

## Connections
- Domain: [[financials-accounting-2]]
- [[WithholdingTaxCodes]] via the type code classifying each withholding code
