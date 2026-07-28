---
entity: ServiceGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# ServiceGroups
Service group codes (localization-specific, e.g. Brazil service tax groups) for classifying service items; empty here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceGroups --top 5
./sapb1 query ServiceGroups --count
./sapb1 query ServiceGroups --select "AbsEntry,Code,Name" --top 10
# Find a service group by (partial) name (if ever populated):
./sapb1 query ServiceGroups --filter "contains(Name,'Tax')" --top 10
```
Set is empty here — field names above are best-effort; confirm with `./sapb1 fields ServiceGroups` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| Code | Service group code |
| Name | Service group name |

(No key fields captured in recon — the set is empty; fields above are best-effort from the standard schema.)

## Connections
- Domain: [[administration-setup-3]]
- [[Items]] via service-group assignment on service-type items
