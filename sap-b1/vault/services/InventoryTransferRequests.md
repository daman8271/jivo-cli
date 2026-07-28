---
entity: InventoryTransferRequests
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH]
rows_oil: 1282
---
# InventoryTransferRequests
Requests to move stock between warehouses (e.g. plant to depot), later fulfilled by actual StockTransfers; 1.3k requests in use. Live rows in JIVO_OIL_HANADB: 1282.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query InventoryTransferRequests --top 5
./sapb1 query InventoryTransferRequests --count
./sapb1 query InventoryTransferRequests --select "DocNum,DocDate,FromWarehouse,ToWarehouse" --top 10
# Transfer requests still open (not yet fulfilled by a stock transfer):
./sapb1 query InventoryTransferRequests --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,DocDate,FromWarehouse,ToWarehouse" --top 20
```

Also exposes `Cancel`, `Close`, `SaveDraftToDocument` document actions (write — out of scope under our READ-ONLY rule).

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| DocDate | Posting date |
| DueDate | Requested transfer date |
| CardCode | Business partner code |
| CardName | Business partner name |
| FromWarehouse | Source warehouse code |
| ToWarehouse | Destination warehouse code |
| DocumentStatus | Open or closed |
| Comments | Free-text remarks |
| PriceList | Price list applied |
| SalesPersonCode | Responsible sales employee |
| BPLID | Branch/business place ID |
| StockTransferLines | Item lines to move |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Warehouses]] via FromWarehouse / ToWarehouse
- [[Items]] via ItemCode on StockTransferLines
- [[BusinessPartners]] via CardCode
- [[StockTransfers]] via base-document reference when the request is fulfilled
- [[PriceLists]] via PriceList
- [[SalesPersons]] via SalesPersonCode
