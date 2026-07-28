---
entity: ResourceProperties
domain: production-mrp
readable: true
methods: ["GET ResourceProperties(id)", "GET ResourceProperties", "PATCH ResourceProperties(id)"]
rows_oil: 64
---
# ResourceProperties
Master list of tag-like property definitions that can be flagged on resources for classification and filtering. Live rows in JIVO_OIL_HANADB: 64.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ResourceProperties --top 5
./sapb1 query ResourceProperties --count
./sapb1 query ResourceProperties --select "Code,Name" --top 10
# find a property definition by name
./sapb1 query ResourceProperties --filter "contains(Name,'Line')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Property number/key |
| Name | Property display name |

## Connections
- Domain: [[production-mrp]]
- [[Resources]] via property flags — resources tagged with this property
