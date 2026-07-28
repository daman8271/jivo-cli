---
entity: SerialNumberDetails
domain: inventory-warehouse-2
readable: true
methods: [GET, PATCH]
rows_oil: 0
---
# SerialNumberDetails
Master records of individual item serial numbers (manufacturer/internal serial, status, expiry) for serial-managed inventory; empty in JIVO_OIL_HANADB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SerialNumberDetails --top 5
./sapb1 query SerialNumberDetails --count
./sapb1 query SerialNumberDetails --select "DocEntry,ItemCode,SerialNumber,Status" --top 10
# Serials for a specific item (shape of a useful filter once populated)
./sapb1 query SerialNumberDetails --filter "ItemCode eq 'FG00001'"
```

## Key fields
Recon profiled no populated key fields — the entity set holds 0 rows in JIVO_OIL_HANADB (JIVO oil SKUs are batch-managed, not serial-managed). Standard SAP fields include DocEntry, ItemCode, SerialNumber, MfrSerialNo, Status and ExpirationDate.

## Connections
- Domain: [[inventory-warehouse-2]]
- [[Items]] via ItemCode — the serial-managed item master
- [[Warehouses]] via WhsCode — warehouse currently holding the serial
