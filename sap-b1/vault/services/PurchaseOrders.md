---
entity: PurchaseOrders
domain: purchasing
readable: true
methods: ["GET PurchaseOrders(id)", "GET PurchaseOrders", "POST PurchaseOrders", "PATCH PurchaseOrders(id)", "POST PurchaseOrders(id)/Close", "POST PurchaseOrders(id)/Cancel", "POST PurchaseOrders(id)/Reopen", "POST PurchaseOrders(id)/CreateCancellationDocument"]
rows_oil: 4168
---
# PurchaseOrders
Purchase orders — commitments to vendors that start the procurement chain (PO → goods receipt → A/P invoice). Live rows in JIVO_OIL_HANADB: 4,168.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseOrders --top 5
./sapb1 query PurchaseOrders --count
./sapb1 query PurchaseOrders --select "DocNum,CardName,DocDate,DocTotal" --top 10
# POs still open (goods not fully received / not closed):
./sapb1 query PurchaseOrders --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardName,DocDueDate,DocTotal"
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code |
| CardName | Vendor name |
| DocDate | Posting date |
| DocDueDate | Requested delivery date |
| TaxDate | Tax point date |
| DocTotal | Order total |
| VatSum | Total tax amount |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| Cancelled | Cancellation flag |
| NumAtCard | Vendor's reference number |
| Series | Numbering series |
## Connections
- Domain: [[purchasing]]
- [[PurchaseDeliveryNotes]] via DocumentLines Base/Target refs — goods receipts drawn from this PO
- [[PurchaseInvoices]] via document chain — vendor bills that close the PO
- [[PurchaseQuotations]] via DocumentLines BaseEntry/BaseType — the RFQ the PO was copied from
- [[BusinessPartners]] via CardCode — the vendor being ordered from
- [[Items]] via DocumentLines/ItemCode — ordered items, line by line
- [[Warehouses]] via DocumentLines/WarehouseCode — destination warehouse per line
- [[SalesPersons]] via SalesPersonCode — buyer/owner assigned to the document
- [[Projects]] via DocumentLines/ProjectCode — project cost assignment per line
