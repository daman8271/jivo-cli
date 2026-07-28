---
entity: AssetClasses
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 3
---
# AssetClasses
Asset class master data mapping asset categories to G/L account determinations and depreciation settings per area (3 classes defined). Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AssetClasses --top 5
./sapb1 query AssetClasses --count
./sapb1 query AssetClasses --select "Code,Description,AssetType,BPLID" --top 10
```
Useful filter — classes with a capitalization value limit set:
```bash
./sapb1 query AssetClasses --filter "ValueLimitTo gt 0" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Asset class code (key) |
| Description | Class name |
| AssetType | Regular / low-value type |
| AttributeGroup | Linked attribute group |
| BPLID | Branch (business place) ID |
| ValueLimitFrom | Lower acquisition value limit |
| ValueLimitTo | Upper acquisition value limit |
| AssetClassCollection | Per-area account/depreciation lines |

## Connections
- Domain: [[fixed-assets]]
- [[DepreciationAreas]] via AssetClassCollection.DepreciationArea (per-area settings lines)
- [[AssetGroups]] via asset group assigned to items of this class
- [[ChartOfAccounts]] via G/L account determination codes in AssetClassCollection
