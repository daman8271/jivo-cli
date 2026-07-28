---
entity: InventoryPostings
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# InventoryPostings
Posts the stock differences found by inventory countings into stock and G/L (unused). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query InventoryPostings --top 5
./sapb1 query InventoryPostings --count
./sapb1 query InventoryPostings --select "DocumentEntry,DocumentNumber,CountDate,PriceSource" --top 10
# Difference postings from counts taken this year (if ever used):
./sapb1 query InventoryPostings --filter "CountDate ge '2026-01-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| DocumentEntry | Internal document key |
| DocumentNumber | Visible document number |
| CountDate | Date of underlying count |
| Series | Numbering series |
| Remarks | Free-text remarks |
| PriceSource | Valuation price source |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[InventoryCountings]] via base counting document on posting lines
- [[Items]] via ItemCode on posting lines
- [[Warehouses]] via WarehouseCode on posting lines
- [[ChartOfAccounts]] via the stock-difference G/L account
