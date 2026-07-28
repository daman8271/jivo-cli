---
entity: ReportFilter
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# ReportFilter
Saved filter definitions applied to report layouts/printing; empty here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ReportFilter --top 5
./sapb1 query ReportFilter --count
./sapb1 query ReportFilter --select "AbsEntry,ReportCode" --top 10
# Filters saved for one report/document type (if any get defined):
./sapb1 query ReportFilter --filter "ReportCode eq 'INV1'" --top 10
```
Set is empty here — field names above are best-effort; confirm with `./sapb1 fields ReportFilter` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| ReportCode | Report/document type code |

(No key fields captured in recon — the set is empty; fields above are best-effort from the standard schema.)

## Connections
- Domain: [[administration-setup-3]]
- [[ReportTypes]] via report/document type code
