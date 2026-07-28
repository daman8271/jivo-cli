---
entity: Items
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 2264
---
# Items
The item master — 2,264 SKUs of oils/materials with stock, pricing, tax, UoM, and warehouse settings; the backbone of all inventory and sales documents. Live rows in JIVO_OIL_HANADB: 2264.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Items --top 5
./sapb1 query Items --count
./sapb1 query Items --select "ItemCode,ItemName,QuantityOnStock,DefaultWarehouse" --top 10
# SKUs actually holding stock right now:
./sapb1 query Items --filter "QuantityOnStock gt 0" --select "ItemCode,ItemName,QuantityOnStock" --top 20
```

Also exposes a `Cancel` action (write — out of scope under our READ-ONLY rule).

## Key fields
| Field | Meaning |
|---|---|
| ItemCode | SKU key |
| ItemName | Item description |
| ForeignName | Alternate/foreign-language name |
| ItemsGroupCode | Item group number |
| BarCode | Default barcode/EAN |
| DefaultWarehouse | Default warehouse code |
| PurchaseUnit | Purchasing unit name |
| SalesUnit | Sales unit name |
| InventoryUOM | Stock-keeping unit name |
| QuantityOnStock | Total on-hand quantity |
| AvgStdPrice | Average/standard cost |
| VatLiable | Subject to VAT/GST |
| Manufacturer | Manufacturer code |
| CreateDate | Record creation date |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[ItemGroups]] via ItemsGroupCode
- [[Warehouses]] via DefaultWarehouse and ItemWarehouseInfoCollection
- [[BusinessPartners]] via preferred vendor / Manufacturer
- [[PriceLists]] via ItemPrices per price list
- [[ItemProperties]] via Properties1–64 flags
- [[ItemImages]] via ItemCode (picture attachment)
- [[UnitOfMeasurementGroups]] via UoMGroupEntry
