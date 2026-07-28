---
entity: NotaFiscalCFOP
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# NotaFiscalCFOP
Brazilian CFOP operation-nature codes for Nota Fiscal documents (Brazil localization; empty in this India DB). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query NotaFiscalCFOP --top 5
./sapb1 query NotaFiscalCFOP --count
```
(Empty set in JIVO_OIL — `--count` returns 0, so there is nothing useful to `--select` or `--filter` yet.)

## Key fields
_No rows in JIVO_OIL_HANADB — field-level recon not captured for this empty Brazil-localization set._

## Connections
- Domain: [[financials-accounting-2]]
- [[NFTaxCategories]] via the tax category a CFOP code is processed under
