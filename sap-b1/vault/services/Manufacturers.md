---
entity: Manufacturers
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# Manufacturers
Item manufacturer lookup referenced by the item master Manufacturer field. Live rows in JIVO_OIL_HANADB: 1 — and it's only the built-in placeholder (Code -1, "- No Manufacturer -"), so no real manufacturers are maintained.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Manufacturers --top 5
./sapb1 query Manufacturers --count
./sapb1 query Manufacturers --select "Code,ManufacturerName" --top 10
# Real manufacturers only, excluding the "- No Manufacturer -" placeholder (empty today):
./sapb1 query Manufacturers --filter "Code ne -1" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Manufacturer numeric key (-1 = none) |
| ManufacturerName | Manufacturer display name |

## Connections
- Domain: [[system-other-1]]
- [[Items]] via Manufacturer — item master Manufacturer field stores this Code
