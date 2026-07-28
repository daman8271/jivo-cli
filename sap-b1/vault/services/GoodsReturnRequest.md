---
entity: GoodsReturnRequest
domain: purchasing
readable: true
methods: ["GET GoodsReturnRequest(id)", "GET GoodsReturnRequest", "POST GoodsReturnRequest", "PATCH GoodsReturnRequest(id)", "DELETE GoodsReturnRequest(id)", "POST GoodsReturnRequest(id)/Close", "POST GoodsReturnRequest(id)/Cancel", "POST GoodsReturnRequest(id)/Reopen", "POST GoodsReturnRequest(id)/SaveDraftToDocument", "POST GoodsReturnRequest(id)/CreateCancellationDocument"]
rows_oil: 0
---
# GoodsReturnRequest
Request document to return received goods to a vendor before the actual purchase return is posted (unused here). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query GoodsReturnRequest --top 5
./sapb1 query GoodsReturnRequest --count
./sapb1 query GoodsReturnRequest --select "DocNum,CardCode,DocDate,DocTotal" --top 10
# Open return requests only (returns nothing today — set is empty):
./sapb1 query GoodsReturnRequest --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardCode,DocDate,DocTotal"
```
## Key fields
Empty in JIVO_OIL_HANADB — key fields not inferable from live data. As a standard B1 marketing document it carries the usual header:
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code |
| DocDate | Posting date |
| DocTotal | Requested return value |
| DocumentStatus | Open or closed |
## Connections
- Domain: [[purchasing]]
- [[PurchaseReturns]] via document chain (Target refs) — the actual return posted from the request
- [[PurchaseDeliveryNotes]] via DocumentLines BaseEntry/BaseType — the goods receipt being returned against
- [[BusinessPartners]] via CardCode — the vendor the goods would go back to
- [[Items]] via DocumentLines/ItemCode — items requested for return
- [[Warehouses]] via DocumentLines/WarehouseCode — warehouse the stock would leave
