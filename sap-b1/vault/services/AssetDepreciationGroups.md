---
entity: AssetDepreciationGroups
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# AssetDepreciationGroups
Grouping master data for reporting depreciation across sets of fixed assets (empty in JIVO_OIL). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AssetDepreciationGroups --top 5
./sapb1 query AssetDepreciationGroups --count
./sapb1 query AssetDepreciationGroups --select "Code,Description" --top 10
```
Useful filter — find a group by name fragment:
```bash
./sapb1 query AssetDepreciationGroups --filter "contains(Description,'Plant')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Depreciation group code (key) |
| Description | Group name |

## Connections
- Domain: [[fixed-assets]]
- [[AssetClasses]] via depreciation group assigned on asset class / asset item
