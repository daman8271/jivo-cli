---
entity: PurchaseRequests
domain: purchasing
readable: true
methods: ["GET PurchaseRequests(id)", "GET PurchaseRequests", "POST PurchaseRequests", "PATCH PurchaseRequests(id)", "DELETE PurchaseRequests(id)", "POST PurchaseRequests(id)/Close", "POST PurchaseRequests(id)/Cancel", "POST PurchaseRequests(id)/Reopen", "POST PurchaseRequests(id)/CreateCancellationDocument"]
rows_oil: 0
---
# PurchaseRequests
Internal purchase requisitions from employees that kick off procurement (unused here). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseRequests --top 5
./sapb1 query PurchaseRequests --count
./sapb1 query PurchaseRequests --select "DocNum,CardCode,DocDate,DocTotal" --top 10
# Open requisitions only (returns nothing today — set is empty):
./sapb1 query PurchaseRequests --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardCode,DocDate,DocTotal"
```
## Key fields
Empty in JIVO_OIL_HANADB — key fields not inferable from live data. As a standard B1 marketing document it carries the usual header:
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code (if known) |
| DocDate | Posting date |
| DocTotal | Requested total |
| DocumentStatus | Open or closed |
## Connections
- Domain: [[purchasing]]
- [[PurchaseQuotations]] via document chain (Target refs) — RFQs raised from the requisition
- [[PurchaseOrders]] via document chain — POs ultimately fulfilling the request
- [[BusinessPartners]] via CardCode — suggested vendor, when specified
- [[Items]] via DocumentLines/ItemCode — requested items, line by line
