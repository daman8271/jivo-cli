---
entity: PurchaseDeliveryNotes
domain: purchasing
readable: true
methods: ["GET PurchaseDeliveryNotes(id)", "GET PurchaseDeliveryNotes", "POST PurchaseDeliveryNotes", "PATCH PurchaseDeliveryNotes(id)", "POST PurchaseDeliveryNotes(id)/Close", "POST PurchaseDeliveryNotes(id)/Cancel", "POST PurchaseDeliveryNotes(id)/Reopen", "POST PurchaseDeliveryNotes(id)/CreateCancellationDocument"]
rows_oil: 11183
---
# PurchaseDeliveryNotes
Goods Receipt POs — records physical receipt of goods against purchase orders, updating inventory. Live rows in JIVO_OIL_HANADB: 11,183.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseDeliveryNotes --top 5
./sapb1 query PurchaseDeliveryNotes --count
./sapb1 query PurchaseDeliveryNotes --select "DocNum,CardName,DocDate,DocTotal" --top 10
# Receipts still open (received but not yet fully invoiced):
./sapb1 query PurchaseDeliveryNotes --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardName,DocDate,DocTotal"
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
| DocTotal | Receipt total value |
| VatSum | Total tax amount |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| Cancelled | Cancellation flag |
| NumAtCard | Vendor's delivery reference |
| Series | Numbering series |
## Connections
- Domain: [[purchasing]]
- [[PurchaseOrders]] via DocumentLines BaseEntry/BaseType — the PO this receipt fulfils
- [[PurchaseInvoices]] via document chain (Target refs) — the vendor bill that follows the receipt
- [[BusinessPartners]] via CardCode — the delivering vendor
- [[Items]] via DocumentLines/ItemCode — received items, line by line
- [[Warehouses]] via DocumentLines/WarehouseCode — stock enters this warehouse
- [[SalesPersons]] via SalesPersonCode — buyer/owner assigned to the document
- [[Projects]] via DocumentLines/ProjectCode — project cost assignment per line
