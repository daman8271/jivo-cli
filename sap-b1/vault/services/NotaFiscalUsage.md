---
entity: NotaFiscalUsage
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# NotaFiscalUsage
Brazilian Nota Fiscal usage codes describing the purpose of goods movement (Brazil localization; empty here). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query NotaFiscalUsage --top 5
./sapb1 query NotaFiscalUsage --count
```
(Empty set in JIVO_OIL — `--count` returns 0, so there is nothing useful to `--select` or `--filter` yet.)

## Key fields
_No rows in JIVO_OIL_HANADB — field-level recon not captured for this empty Brazil-localization set._

## Connections
- Domain: [[financials-accounting-2]]
- [[NotaFiscalCFOP]] via the CFOP operation codes a usage maps to
