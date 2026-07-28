---
entity: LegalData
domain: system-other-1
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# LegalData
Localization store of statutory/legal registration details attached to the company or business partners. Live rows in JIVO_OIL_HANADB: 0 — statutory registrations live elsewhere (BP fiscal fields) in this India setup.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query LegalData --top 5
./sapb1 query LegalData --count
./sapb1 query LegalData --select "AbsEntry,CardCode,LegalDataType" --top 10
# Legal records for one business partner (if any get defined):
./sapb1 query LegalData --filter "CardCode eq 'C00001'" --top 10
```
No DELETE in the catalog for this set — records are created and amended only.

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Legal-data record key |
| CardCode | Owning business partner code |
| LegalDataType | Kind of statutory record |

## Connections
- Domain: [[system-other-1]]
- [[BusinessPartners]] via CardCode — the BP the legal registration belongs to
