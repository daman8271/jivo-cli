---
entity: Branches
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# Branches
Legacy company branch definitions for segmenting employees/transactions by branch (single-branch setup here; India localizations use BusinessPlaces instead). Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Branches --top 5
./sapb1 query Branches --count
./sapb1 query Branches --select "Code,Name,Description" --top 10
# Find a branch by name fragment:
./sapb1 query Branches --filter "contains(Name,'Main')" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Branch numeric key |
| Name | Branch display name |
| Description | Free-text branch description |

## Connections
- Domain: [[administration-setup-3]]
- [[BusinessPlaces]] — the India-localization branch mechanism (GSTIN business places) that supersedes this legacy table
