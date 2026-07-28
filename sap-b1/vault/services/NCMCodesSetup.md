---
entity: NCMCodesSetup
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# NCMCodesSetup
Brazil-localization NCM (Mercosur commodity nomenclature) tax classification codes for items; unused/empty in this Indian DB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query NCMCodesSetup --top 5
./sapb1 query NCMCodesSetup --count
./sapb1 query NCMCodesSetup --select "AbsEntry,NCMCode,Description" --top 10
# Chapter 15 of the NCM nomenclature = edible oils & fats (if this ever gets populated):
./sapb1 query NCMCodesSetup --filter "startswith(NCMCode,'15')" --top 10
```
Set is empty here — confirm live field names with `./sapb1 fields NCMCodesSetup` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| NCMCode | Mercosur nomenclature code |
| Description | Commodity description |

(No key fields captured in recon — the set is empty; fields above are the standard Service Layer schema.)

## Connections
- Domain: [[administration-setup-3]]
- No related entities in recon — Brazil-only feature, irrelevant to this Indian localization.
