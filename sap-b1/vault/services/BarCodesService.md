---
entity: BarCodesService
domain: inventory-warehouse-1
readable: true
methods: ["BarCodesService_GetList (GET)", "BarCodesService_GetList (POST)"]
rows_oil: null
---
# BarCodesService
RPC-style list access to item barcode records (companion to the BarCodes entity set).

## Operations
- BarCodesService_GetList (GET)
- BarCodesService_GetList (POST)

Entity sets are the read path in the CLI — read barcode rows through the [[BarCodes]] entity set (`./sapb1 query BarCodes`); browse this service's ops with `./sapb1 ops BarCodesService`.

## Connections
- Domain: [[inventory-warehouse-1]]
- [[BarCodes]] — the entity set this service lists
- [[Items]] — items the barcodes belong to
