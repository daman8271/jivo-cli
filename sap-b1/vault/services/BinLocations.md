---
entity: BinLocations
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# BinLocations
Master data of individual bin storage locations within warehouses (empty — JIVO_OIL warehouses are not bin-managed). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BinLocations --top 5
./sapb1 query BinLocations --count
./sapb1 query BinLocations --select "AbsEntry,BinCode,Warehouse,Description" --top 10
# Bins of one specific warehouse (if bin management is ever enabled):
./sapb1 query BinLocations --filter "Warehouse eq '01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| BinCode | Full composed bin code |
| Warehouse | Owning warehouse code |
| Sublevel1 | First bin code segment |
| Description | Bin description text |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Warehouses]] via Warehouse
- [[BinLocationAttributes]] via the Attribute slots on each bin
- [[BinLocationFields]] via Sublevel1–4 segment structure
