---
entity: InventoryCountings
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# InventoryCountings
Physical stock-count documents recording counted vs system quantities before posting differences (unused in JIVO_OIL). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query InventoryCountings --top 5
./sapb1 query InventoryCountings --count
./sapb1 query InventoryCountings --select "DocumentEntry,DocumentNumber,CountDate,Remarks" --top 10
# Counts taken this year (if counting is ever adopted):
./sapb1 query InventoryCountings --filter "CountDate ge '2026-01-01'" --top 10
```

Also exposes a `Close` document action (write — out of scope under our READ-ONLY rule).

## Key fields
| Field | Meaning |
|---|---|
| DocumentEntry | Internal document key |
| DocumentNumber | Visible document number |
| CountDate | Date of the count |
| Series | Numbering series |
| Remarks | Free-text remarks |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] via ItemCode on counting lines
- [[Warehouses]] via WarehouseCode on counting lines
- [[InventoryPostings]] via base counting document on difference postings
- [[InventoryCycles]] via CycleCode driving scheduled counts
