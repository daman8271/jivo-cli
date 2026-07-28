---
entity: PurchaseQuotations
domain: purchasing
readable: true
methods: ["GET PurchaseQuotations(id)", "GET PurchaseQuotations", "POST PurchaseQuotations", "PATCH PurchaseQuotations(id)", "POST PurchaseQuotations(id)/Close", "POST PurchaseQuotations(id)/Cancel", "POST PurchaseQuotations(id)/Reopen", "POST PurchaseQuotations(id)/CreateCancellationDocument"]
rows_oil: 0
---
# PurchaseQuotations
Vendor RFQ/quotation documents preceding purchase orders (unused here). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseQuotations --top 5
./sapb1 query PurchaseQuotations --count
./sapb1 query PurchaseQuotations --select "DocNum,CardCode,DocDate,DocTotal" --top 10
# Open quotations only (returns nothing today — set is empty):
./sapb1 query PurchaseQuotations --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardCode,DocDate,DocTotal"
```
## Key fields
Empty in JIVO_OIL_HANADB — key fields not inferable from live data. As a standard B1 marketing document it carries the usual header:
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code |
| DocDate | Posting date |
| DocTotal | Quoted total |
| DocumentStatus | Open or closed |
## Connections
- Domain: [[purchasing]]
- [[PurchaseOrders]] via document chain (Target refs) — POs copied from the quotation
- [[PurchaseRequests]] via DocumentLines BaseEntry/BaseType — the internal requisition behind the RFQ
- [[BusinessPartners]] via CardCode — the quoting vendor
- [[Items]] via DocumentLines/ItemCode — quoted items, line by line
