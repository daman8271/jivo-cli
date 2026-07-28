---
entity: ItemProperties
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 64
---
# ItemProperties
The 64 checkbox-style item property flags (Properties 1–64) used to tag and filter items in reports and pricing. Live rows in JIVO_OIL_HANADB: 64.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ItemProperties --top 5
./sapb1 query ItemProperties --count
./sapb1 query ItemProperties --select "Number,PropertyName" --top 10
# The first bank of property slots (most likely to be renamed/in use):
./sapb1 query ItemProperties --filter "Number le 10" --select "Number,PropertyName" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Number | Property slot number (1–64) |
| PropertyName | Property display name |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] via the Properties1–64 flags on the item master
