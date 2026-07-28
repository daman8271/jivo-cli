---
entity: PurchaseInvoices
domain: purchasing
readable: true
methods: ["GET PurchaseInvoices(id)", "GET PurchaseInvoices", "POST PurchaseInvoices", "PATCH PurchaseInvoices(id)", "POST PurchaseInvoices(id)/Close", "POST PurchaseInvoices(id)/Cancel", "POST PurchaseInvoices(id)/Reopen", "POST PurchaseInvoices(id)/CreateCancellationDocument"]
rows_oil: 15858
---
# PurchaseInvoices
A/P invoices — the legally binding vendor bills that create payables and drive vendor payments; the core purchasing ledger. Live rows in JIVO_OIL_HANADB: 15,858.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseInvoices --top 5
./sapb1 query PurchaseInvoices --count
./sapb1 query PurchaseInvoices --select "DocNum,CardName,DocDate,DocTotal" --top 10
# Still-open vendor bills (unpaid / not fully closed payables):
./sapb1 query PurchaseInvoices --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardName,DocDueDate,DocTotal"
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code |
| CardName | Vendor name |
| DocDate | Posting date |
| DocDueDate | Payment due date |
| TaxDate | Tax point date |
| DocTotal | Invoice total |
| VatSum | Total tax amount |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| Cancelled | Cancellation flag |
| NumAtCard | Vendor's reference number |
| PaymentGroupCode | Payment terms code |
## Connections
- Domain: [[purchasing]]
- [[PurchaseDeliveryNotes]] via DocumentLines BaseEntry/BaseType — the goods receipts this bill invoices
- [[PurchaseOrders]] via document chain (Base/Target refs) — the originating commitments
- [[PurchaseCreditNotes]] via document chain — vendor credits that reverse this invoice
- [[BusinessPartners]] via CardCode — the vendor being paid
- [[Items]] via DocumentLines/ItemCode — what was billed, line by line
- [[Warehouses]] via DocumentLines/WarehouseCode — receiving warehouse per line
- [[SalesPersons]] via SalesPersonCode — buyer/owner assigned to the document
- [[Projects]] via DocumentLines/ProjectCode — project cost assignment per line
