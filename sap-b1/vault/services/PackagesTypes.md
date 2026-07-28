---
entity: PackagesTypes
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# PackagesTypes
Master list of packaging types (box, pallet, etc.) referenced when packing delivery documents (unused). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PackagesTypes --top 5
./sapb1 query PackagesTypes --count
./sapb1 query PackagesTypes --select "Number,Name,Description" --top 10
# Look up one package type by name (if any are ever defined):
./sapb1 query PackagesTypes --filter "Name eq 'Box'" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Number | Package type numeric key |
| Name | Package type name |
| Description | Package type description |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[DeliveryNotes]] via PackageType on document packages
- [[Items]] via items packed into these package types
