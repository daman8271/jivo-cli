---
entity: BinLocationFields
domain: inventory-warehouse-1
readable: true
methods: [GET, PATCH]
rows_oil: 14
---
# BinLocationFields
Configures the sublevel/segment field structure used to compose bin location codes in bin-managed warehouses. Live rows in JIVO_OIL_HANADB: 14.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BinLocationFields --top 5
./sapb1 query BinLocationFields --count
./sapb1 query BinLocationFields --select "AbsEntry,Name,FieldNumber,Activated" --top 10
# Only the sublevel fields that are actually switched on:
./sapb1 query BinLocationFields --filter "Activated eq 'tYES'" --top 14
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| Name | Custom field display name |
| DefaultFieldName | System default field name |
| FieldNumber | Sublevel/segment position number |
| FieldType | Field data type |
| Activated | Whether the sublevel is active |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[BinLocations]] via Sublevel1–4 code segments composed from these fields
- [[Warehouses]] via bin-enabled warehouses that apply this sublevel structure
