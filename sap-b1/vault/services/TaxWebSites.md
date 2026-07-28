---
entity: TaxWebSites
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE, SetAsDefault]
rows_oil: 0
---
# TaxWebSites
Configured external tax-service websites/providers (e.g. US sales-tax engines) with a default selector (empty here). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TaxWebSites --top 5
./sapb1 query TaxWebSites --count
```
(Empty set in JIVO_OIL — `--count` returns 0, so there is nothing useful to `--select` or `--filter` yet.)

## Key fields
_No rows in JIVO_OIL_HANADB — field-level recon not captured for this empty set._

## Connections
- Domain: [[financials-accounting-2]]
