---
entity: StockTransferDrafts
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, Cancel, Close, SaveDraftToDocument]
rows_oil: 47115
---
# StockTransferDrafts
Draft (unposted) inter-warehouse stock transfer documents awaiting approval or conversion to actual StockTransfers. Live rows in JIVO_OIL_HANADB: 47,115.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query StockTransferDrafts --top 5
./sapb1 query StockTransferDrafts --count
./sapb1 query StockTransferDrafts --select "DocEntry,DocDate,FromWarehouse,ToWarehouse" --top 10
# Drafts still open (not yet converted or closed)
./sapb1 query StockTransferDrafts --filter "DocumentStatus eq 'bost_Open'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible draft number |
| DocDate | Document date |
| DueDate | Expected transfer date |
| TaxDate | Tax reporting date |
| FromWarehouse | Source warehouse |
| ToWarehouse | Destination warehouse |
| CardCode | Linked partner code |
| CardName | Linked partner name |
| DocumentStatus | Open/closed draft status |
| SalesPersonCode | Responsible salesperson |
| PriceList | Valuation price list |
| Comments | Free-text remarks |
| Series | Numbering series |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[StockTransfers]] via SaveDraftToDocument — the posted document a draft becomes
- [[Warehouses]] via FromWarehouse / ToWarehouse — source and destination depots
- [[BusinessPartners]] via CardCode — partner referenced on the draft
- [[SalesPersons]] via SalesPersonCode — owner of the movement
- [[PriceLists]] via PriceList — pricing basis for the lines
- [[Items]] via StockTransferLines.ItemCode — SKUs being moved
