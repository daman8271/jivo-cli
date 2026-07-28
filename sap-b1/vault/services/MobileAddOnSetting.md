---
entity: MobileAddOnSetting
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# MobileAddOnSetting
Configuration settings for the SAP B1 mobile add-on/app (per-user or per-device mobile client preferences); empty in JIVO_OIL_HANADB so no fields are inferable. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query MobileAddOnSetting --top 5
./sapb1 query MobileAddOnSetting --count
```
No field list is available (the set is empty here and recon surfaced no key fields), so `--select`/`--filter` examples cannot be given — inspect a live row first if this set ever fills.

## Key fields
| Field | Meaning |
|---|---|
| — | No fields inferable (empty in this database) |

## Connections
- Domain: [[business-partners-crm]]
