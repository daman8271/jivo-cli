---
entity: Sections
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 26
---
# Sections
India-localization TDS/withholding-tax sections (e.g. 194C, 194J) referenced by withholding tax codes — 26 statutory sections defined. Live rows in JIVO_OIL_HANADB: 26.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Sections --top 5
./sapb1 query Sections --count
./sapb1 query Sections --select "AbsEntry,Code,Description,ECode" --top 10
./sapb1 query Sections --filter "contains(Code,'194')" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| Code | Statutory section code (e.g. 194C) |
| Description | Section description text |
| ECode | Electronic/e-filing section code |
## Connections
- Domain: [[system-other-2]]
- [[WithholdingTaxCodes]] via Section (AbsEntry)
