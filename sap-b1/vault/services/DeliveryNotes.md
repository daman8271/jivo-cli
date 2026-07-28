---
entity: DeliveryNotes
domain: sales-ar
readable: true
methods: ["GET DeliveryNotes(id)", "GET DeliveryNotes", "POST DeliveryNotes", "PATCH DeliveryNotes(id)", "DELETE DeliveryNotes(id)", "POST DeliveryNotes(id)/Close", "POST DeliveryNotes(id)/Cancel", "POST DeliveryNotes(id)/Reopen", "POST DeliveryNotes(id)/CreateCancellationDocument"]
rows_oil: 2821
---
# DeliveryNotes
Sales delivery notes recording goods shipped to customers (the Orders → DeliveryNotes → Invoices chain). Live rows in JIVO_OIL_HANADB: 2,821.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DeliveryNotes --top 5
./sapb1 query DeliveryNotes --count
./sapb1 query DeliveryNotes --select "DocNum,CardName,DocDate,DocTotal" --top 10
# Deliveries shipped but still open (not yet fully invoiced):
./sapb1 query DeliveryNotes --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardName,DocDate,DocTotal"
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Customer code |
| CardName | Customer name |
| DocDate | Posting date |
| DocDueDate | Promised delivery date |
| DocTotal | Total delivered value |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| SalesPersonCode | Sales employee code |
| NumAtCard | Customer reference number |
| Comments | Free-text remarks |
| Cancelled | Cancellation flag |
| BPL_IDAssignedToInvoice | Branch (business place) ID |
## Connections
- Domain: [[sales-ar]]
- [[Orders]] via DocumentLines BaseEntry/BaseType — the sales order being fulfilled
- [[Invoices]] via document chain (Target refs) — invoices drawn from the delivery downstream
- [[Returns]] via document chain (Base/Target refs) — goods returns that reverse the delivery
- [[BusinessPartners]] via CardCode — the customer receiving the goods
- [[Items]] via DocumentLines/ItemCode — what shipped, line by line
- [[Warehouses]] via DocumentLines/WarehouseCode — stock leaves this warehouse on delivery
- [[SalesPersons]] via SalesPersonCode — sales employee on the document
- [[Currencies]] via DocCurrency — currency of DocTotal
- [[Projects]] via DocumentLines/ProjectCode — project assignment per line
