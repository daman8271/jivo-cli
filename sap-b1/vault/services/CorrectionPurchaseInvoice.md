---
entity: CorrectionPurchaseInvoice
domain: purchasing
readable: true
methods: ["GET CorrectionPurchaseInvoice(id)", "GET CorrectionPurchaseInvoice", "POST CorrectionPurchaseInvoice", "PATCH CorrectionPurchaseInvoice(id)", "POST CorrectionPurchaseInvoice(id)/Close", "POST CorrectionPurchaseInvoice(id)/Cancel", "POST CorrectionPurchaseInvoice(id)/Reopen", "POST CorrectionPurchaseInvoice(id)/CreateCancellationDocument"]
rows_oil: 0
---
# CorrectionPurchaseInvoice
Localization document that corrects a posted A/P invoice (amount/tax/line fixes without a full credit-and-rebill). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CorrectionPurchaseInvoice --top 5
./sapb1 query CorrectionPurchaseInvoice --count
./sapb1 query CorrectionPurchaseInvoice --select "DocNum,CardCode,DocDate,DocTotal" --top 10
# Open corrections only (returns nothing today — set is empty):
./sapb1 query CorrectionPurchaseInvoice --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardCode,DocDate,DocTotal"
```
## Key fields
Empty in JIVO_OIL_HANADB — key fields not inferable from live data. As a standard B1 marketing document it carries the usual header:
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code |
| DocDate | Posting date |
| DocTotal | Corrected document total |
| DocumentStatus | Open or closed |
## Connections
- Domain: [[purchasing]]
- [[PurchaseInvoices]] via base document refs — the posted A/P invoice being corrected
- [[BusinessPartners]] via CardCode — the vendor on the corrected invoice
