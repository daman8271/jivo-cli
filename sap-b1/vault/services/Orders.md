---
entity: Orders
domain: sales-ar
readable: true
methods: [GET, POST, PATCH]
rows_oil: 14583
---
# Orders
Customer sales orders (14.6k rows) — commitments to deliver goods, the starting document of the sales fulfilment chain. Live rows in JIVO_OIL_HANADB: 14583.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Orders --top 5
./sapb1 query Orders --count
./sapb1 query Orders --select "DocNum,DocDate,CardName,DocTotal" --top 10
# Open, not-cancelled orders = the live order book awaiting delivery:
./sapb1 query Orders --filter "DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'" --top 10
```
The CLI also has a dedicated shortcut: `./sapb1 orders --top 10`.

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Order internal key |
| DocNum | Order document number |
| DocDate | Posting date |
| DocDueDate | Requested delivery date |
| CardCode | Customer code |
| CardName | Customer name |
| DocTotal | Order total amount |
| DocCurrency | Document currency |
| DocumentStatus | Open/closed status |
| Cancelled | Cancellation flag |
| SalesPersonCode | Responsible sales employee |
| NumAtCard | Customer PO reference |
| Comments | Free-text remarks |
| DocumentLines | Item lines collection |

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode
- [[Items]] via DocumentLines.ItemCode
- [[Warehouses]] via DocumentLines.WarehouseCode
- [[SalesPersons]] via SalesPersonCode
- [[DeliveryNotes]] via their DocumentLines.BaseEntry pointing back at the order
- [[Invoices]] via their DocumentLines.BaseEntry pointing back at the order
- [[Currencies]] via DocCurrency
- [[Projects]] via DocumentLines.ProjectCode
