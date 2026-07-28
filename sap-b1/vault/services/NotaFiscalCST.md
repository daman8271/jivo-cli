---
entity: NotaFiscalCST
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# NotaFiscalCST
Brazilian CST tax-situation codes for Nota Fiscal tax lines (Brazil localization; empty here). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query NotaFiscalCST --top 5
./sapb1 query NotaFiscalCST --count
```
(Empty set in JIVO_OIL — `--count` returns 0, so there is nothing useful to `--select` or `--filter` yet.)

## Key fields
_No rows in JIVO_OIL_HANADB — field-level recon not captured for this empty Brazil-localization set._

## Connections
- Domain: [[financials-accounting-2]]
- [[NFTaxCategories]] via the tax category a CST code belongs to
