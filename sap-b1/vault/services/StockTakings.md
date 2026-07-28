---
entity: StockTakings
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 126820
---
# StockTakings
Physical inventory count records (counted quantities per item per warehouse, with custom box/litre fields) used to reconcile book stock during stock takes. Live rows in JIVO_OIL_HANADB: 126,820.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query StockTakings --top 5
./sapb1 query StockTakings --count
./sapb1 query StockTakings --select "ItemCode,WarehouseCode,Counted,U_UNE_LTR" --top 10
# Only rows where a physical quantity was actually counted
./sapb1 query StockTakings --filter "Counted gt 0" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| ItemCode | Item being counted (key) |
| WarehouseCode | Warehouse counted in (key) |
| Counted | Physically counted quantity |
| U_UNE_BOX | Custom counted boxes (UDF) |
| U_UNE_LTR | Custom counted litres (UDF) |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[Items]] via ItemCode — item master for the counted SKU
- [[Warehouses]] via WarehouseCode — depot where the count was taken
