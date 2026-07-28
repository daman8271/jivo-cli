---
entity: StockTransfers
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE, Cancel, Close]
rows_oil: 11668
---
# StockTransfers
Posted inventory transfer documents moving stock between warehouses (the core inter-branch/depot movement document). Live rows in JIVO_OIL_HANADB: 11,668.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query StockTransfers --top 5
./sapb1 query StockTransfers --count
./sapb1 query StockTransfers --select "DocEntry,DocDate,FromWarehouse,ToWarehouse" --top 10
# Recent transfers this fiscal year
./sapb1 query StockTransfers --filter "DocDate ge '2026-04-01'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible transfer number |
| DocDate | Posting date |
| DueDate | Expected arrival date |
| TaxDate | Tax reporting date |
| FromWarehouse | Source warehouse |
| ToWarehouse | Destination warehouse |
| CardCode | Linked partner code |
| CardName | Linked partner name |
| DocumentStatus | Open/closed status |
| SalesPersonCode | Responsible salesperson |
| PriceList | Valuation price list |
| JournalMemo | Journal entry memo |
| TransNum | Linked journal transaction |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[Warehouses]] via FromWarehouse / ToWarehouse — depots stock moves between
- [[BusinessPartners]] via CardCode — partner referenced on the transfer
- [[SalesPersons]] via SalesPersonCode — owner of the movement
- [[PriceLists]] via PriceList — pricing basis for the lines
- [[Items]] via StockTransferLines.ItemCode — SKUs being moved
- [[StockTransferDrafts]] via SaveDraftToDocument — the draft a posted transfer came from
- [[JournalEntries]] via TransNum — inventory G/L posting created
