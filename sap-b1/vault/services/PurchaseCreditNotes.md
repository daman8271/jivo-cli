---
entity: PurchaseCreditNotes
domain: purchasing
readable: true
methods: ["GET PurchaseCreditNotes(id)", "GET PurchaseCreditNotes", "POST PurchaseCreditNotes", "PATCH PurchaseCreditNotes(id)", "DELETE PurchaseCreditNotes(id)", "POST PurchaseCreditNotes(id)/Close", "POST PurchaseCreditNotes(id)/Cancel", "POST PurchaseCreditNotes(id)/Reopen", "POST PurchaseCreditNotes(id)/CreateCancellationDocument"]
rows_oil: 1517
---
# PurchaseCreditNotes
A/P credit notes — vendor credits reversing purchase invoices for returns or price corrections. Live rows in JIVO_OIL_HANADB: 1,517.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseCreditNotes --top 5
./sapb1 query PurchaseCreditNotes --count
./sapb1 query PurchaseCreditNotes --select "DocNum,CardName,DocDate,DocTotal" --top 10
# Credits still open (not yet fully applied against payables):
./sapb1 query PurchaseCreditNotes --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardName,DocDate,DocTotal"
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code |
| CardName | Vendor name |
| DocDate | Posting date |
| DocDueDate | Value/due date |
| TaxDate | Tax point date |
| DocTotal | Credit total |
| VatSum | Total tax amount |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| Cancelled | Cancellation flag |
| NumAtCard | Vendor's credit reference |
| Series | Numbering series |
## Connections
- Domain: [[purchasing]]
- [[BusinessPartners]] via CardCode — the vendor issuing the credit
- [[PurchaseInvoices]] via DocumentLines BaseEntry/BaseType — the A/P invoice being reversed
- [[Items]] via DocumentLines/ItemCode — credited items, line by line
- [[Warehouses]] via DocumentLines/WarehouseCode — warehouse affected by returned stock
- [[SalesPersons]] via SalesPersonCode — buyer/owner assigned to the document
- [[Projects]] via DocumentLines/ProjectCode — project cost assignment per line
- [[BusinessPlaces]] via BPL_IDAssignedToInvoice — issuing branch/business place
