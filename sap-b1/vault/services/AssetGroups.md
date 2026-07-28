---
entity: AssetGroups
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# AssetGroups
Fixed-asset group master data used to categorize asset items (empty in JIVO_OIL). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AssetGroups --top 5
./sapb1 query AssetGroups --count
./sapb1 query AssetGroups --select "Code,Description" --top 10
```
Useful filter — find a group by name fragment:
```bash
./sapb1 query AssetGroups --filter "contains(Description,'Machinery')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Asset group code (key) |
| Description | Group name |

## Connections
- Domain: [[fixed-assets]]
- [[AssetClasses]] via classes categorized under this group
- [[Items]] via AssetGroup on fixed-asset item master
