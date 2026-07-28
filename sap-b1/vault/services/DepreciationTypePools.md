---
entity: DepreciationTypePools
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# DepreciationTypePools
Pools that bundle depreciation types for group/pooled depreciation calculation (1 pool defined). Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DepreciationTypePools --top 5
./sapb1 query DepreciationTypePools --count
./sapb1 query DepreciationTypePools --select "Code,Description" --top 10
```
Useful filter — find a pool by name fragment:
```bash
./sapb1 query DepreciationTypePools --filter "contains(Description,'Pool')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Pool code (key) |
| Description | Pool name |

## Connections
- Domain: [[fixed-assets]]
- [[DepreciationAreas]] via depreciation types applied per area
