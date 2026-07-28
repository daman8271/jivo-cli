---
entity: Warehouses
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 58
---
# Warehouses
Warehouse master defining each stock location's address, G/L account determination, bin-location settings, and branch assignment (58 depots in JIVO oil DB). Live rows in JIVO_OIL_HANADB: 58.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Warehouses --top 5
./sapb1 query Warehouses --count
./sapb1 query Warehouses --select "WarehouseCode,WarehouseName,City,State" --top 10
# Only warehouses still in active use
./sapb1 query Warehouses --filter "Inactive eq 'tNO'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| WarehouseCode | Warehouse key |
| WarehouseName | Depot display name |
| Location | Statutory location link |
| BusinessPlaceID | GST branch assignment |
| Inactive | Warehouse retired flag |
| DropShip | Drop-ship (non-stock) flag |
| Nettable | Counts in MRP netting |
| EnableBinLocations | Bin management enabled |
| DefaultBin | Default bin location |
| City | Warehouse city |
| State | Warehouse state code |
| Country | Country code |
| FederalTaxID | Warehouse GSTIN/tax ID |
| Excisable | Excise-liable flag |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[WarehouseLocations]] via Location — statutory GSTIN/PAN identity of the depot
- [[ChartOfAccounts]] via account-determination fields — inventory/expense G/L accounts
- [[BusinessPlaces]] via BusinessPlaceID — GST branch the warehouse posts under
- [[Items]] via ItemWarehouseInfoCollection — per-warehouse stock and settings
- [[StockTransfers]] via FromWarehouse / ToWarehouse — movements between depots
- [[BinLocations]] via EnableBinLocations / DefaultBin — bin structure inside the warehouse
