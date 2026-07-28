---
entity: Forms1099
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# Forms1099
US 1099 tax form/box definitions for vendor payment reporting (US localization; empty in this India DB). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Forms1099 --top 5
./sapb1 query Forms1099 --count
```
(Empty set in JIVO_OIL — `--count` returns 0, so there is nothing useful to `--select` or `--filter` yet.)

## Key fields
_No rows in JIVO_OIL_HANADB — field-level recon not captured for this empty US-localization set._

## Connections
- Domain: [[financials-accounting-2]]
- [[BusinessPartners]] via the 1099 form/box assigned on US vendor master data
