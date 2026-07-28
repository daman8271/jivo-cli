---
entity: InventoryOpeningBalances
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# InventoryOpeningBalances
Documents that load initial on-hand stock quantities and values at go-live (empty — opening stock loaded another way). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query InventoryOpeningBalances --top 5
./sapb1 query InventoryOpeningBalances --count
./sapb1 query InventoryOpeningBalances --select "DocumentEntry,DocumentNumber,DocumentDate,Remarks" --top 10
# Any opening-balance docs since go-live (sanity check that it stays empty):
./sapb1 query InventoryOpeningBalances --filter "DocumentDate ge '2020-01-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| DocumentEntry | Internal document key |
| DocumentNumber | Visible document number |
| DocumentDate | Posting date |
| Series | Numbering series |
| Remarks | Free-text remarks |
| JournalRemark | Journal entry memo |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] via ItemCode on opening-balance lines
- [[Warehouses]] via WarehouseCode on opening-balance lines
- [[ChartOfAccounts]] via the opening-balance offset account
