---
entity: WarehouseSublevelCodes
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# WarehouseSublevelCodes
Sublevel code values used to build bin-location hierarchies inside bin-enabled warehouses; unused (0 rows) in JIVO_OIL_HANADB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WarehouseSublevelCodes --top 5
./sapb1 query WarehouseSublevelCodes --count
./sapb1 query WarehouseSublevelCodes --select "AbsEntry,Code,WarehouseSublevel" --top 10
# Codes for a given warehouse (shape of a useful filter once populated)
./sapb1 query WarehouseSublevelCodes --filter "Warehouse eq 'WH01'"
```

## Key fields
Recon profiled no populated key fields — the entity set holds 0 rows in JIVO_OIL_HANADB (no warehouse uses bin-location sublevels). Standard SAP fields include AbsEntry, Code, Warehouse and WarehouseSublevel.

## Connections
- Domain: [[inventory-warehouse-2]]
- [[Warehouses]] via Warehouse — bin-enabled warehouse the sublevel codes belong to
- [[BinLocations]] via sublevel code segments — bins composed from these codes
