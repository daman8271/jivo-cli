---
entity: TaxCodeDeterminations
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# TaxCodeDeterminations
Rules that auto-assign tax codes on marketing documents based on BP/item/location criteria (unused — empty). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TaxCodeDeterminations --top 5
./sapb1 query TaxCodeDeterminations --count
```
(Empty set in JIVO_OIL — `--count` returns 0, so there is nothing useful to `--select` or `--filter` yet. The India tax determination actually in use lives in [[TaxCodeDeterminationsTCD]].)

## Key fields
_No rows in JIVO_OIL_HANADB — field-level recon not captured for this empty set._

## Connections
- Domain: [[financials-accounting-2]]
- [[VatGroups]] via the tax code a matching rule assigns
- [[BusinessPartners]] via BP criteria in the rule key fields
- [[Items]] via item criteria in the rule key fields
