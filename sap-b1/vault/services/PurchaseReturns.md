---
entity: PurchaseReturns
domain: purchasing
readable: true
methods: ["GET PurchaseReturns(id)", "GET PurchaseReturns", "POST PurchaseReturns", "PATCH PurchaseReturns(id)", "POST PurchaseReturns(id)/Close", "POST PurchaseReturns(id)/Cancel", "POST PurchaseReturns(id)/Reopen", "POST PurchaseReturns(id)/CreateCancellationDocument"]
rows_oil: 107
---
# PurchaseReturns
Records goods returned to vendors (A/P return documents), reversing received quantities and vendor liability from purchase delivery notes. Live rows in JIVO_OIL_HANADB: 107.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseReturns --top 5
./sapb1 query PurchaseReturns --count
./sapb1 query PurchaseReturns --select "DocNum,CardName,DocDate,DocTotal" --top 10
# Only still-open returns (not yet fully closed against the vendor):
./sapb1 query PurchaseReturns --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardName,DocDate,DocTotal"
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
| DocTotal | Total return value |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| Comments | Free-text remarks |
| BPL_IDAssignedToInvoice | Branch (business place) ID |
| ContactPersonCode | Vendor contact person |
| ControlAccount | A/P control G/L account |
| DocumentLines | Returned item lines |
## Connections
- Domain: [[purchasing]]
- [[BusinessPartners]] via CardCode — the vendor the goods go back to
- [[Items]] via DocumentLines/ItemCode — what was returned, line by line
- [[Warehouses]] via DocumentLines/WarehouseCode — stock leaves this warehouse on return
- [[PurchaseDeliveryNotes]] via DocumentLines BaseEntry/BaseType — the goods receipt the return reverses
- [[PurchaseInvoices]] via document chain (Base/Target refs) — returns offset already-invoiced receipts downstream
- [[ChartOfAccounts]] via ControlAccount — A/P control account posted on the return
- [[Projects]] via DocumentLines/ProjectCode — project cost assignment per line
- [[Currencies]] via DocCurrency — currency of DocTotal
- [[BusinessPlaces]] via BPL_IDAssignedToInvoice — issuing branch/business place
