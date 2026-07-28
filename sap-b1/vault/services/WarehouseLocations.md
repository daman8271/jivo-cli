---
entity: WarehouseLocations
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 5
---
# WarehouseLocations
Location master for warehouses carrying Indian statutory/tax identity (GSTIN, PAN, state) plus custom e-way-bill/transport credentials per location. Live rows in JIVO_OIL_HANADB: 5.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WarehouseLocations --top 5
./sapb1 query WarehouseLocations --count
./sapb1 query WarehouseLocations --select "Code,Name,State,GSTIN" --top 10
# Locations registered in a given state
./sapb1 query WarehouseLocations --filter "State eq 'PB'"
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Location key |
| Name | Location display name |
| City | Location city |
| State | Indian state code |
| Country | Country code |
| GSTIN | GST registration number |
| GstType | GST registration type |
| PANNumber | Income-tax PAN |
| TINNumber | Legacy TIN number |
| Street | Street address |
| ZipCode | Postal PIN code |
| U_Contact_No | Custom contact phone (UDF) |
| U_Contact_Persion | Custom contact person (UDF) |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[Warehouses]] via Location — warehouses assigned to each statutory location
