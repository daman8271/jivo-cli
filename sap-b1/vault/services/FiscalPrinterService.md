---
entity: FiscalPrinterService
domain: financials-accounting-1
readable: false
methods: ["FiscalPrinterService_GetFiscalPrinterList"]
rows_oil: null
---
# FiscalPrinterService
Returns configured fiscal printer devices used for legally mandated receipt printing in certain localizations.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[FiscalPrinter]] — the entity set counterpart holding the printer device records (query this instead)
