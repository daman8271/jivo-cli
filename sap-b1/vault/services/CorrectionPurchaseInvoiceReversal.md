---
entity: CorrectionPurchaseInvoiceReversal
domain: purchasing
readable: true
methods: ["GET CorrectionPurchaseInvoiceReversal(id)", "GET CorrectionPurchaseInvoiceReversal", "POST CorrectionPurchaseInvoiceReversal", "PATCH CorrectionPurchaseInvoiceReversal(id)", "POST CorrectionPurchaseInvoiceReversal(id)/Close", "POST CorrectionPurchaseInvoiceReversal(id)/Cancel", "POST CorrectionPurchaseInvoiceReversal(id)/Reopen", "POST CorrectionPurchaseInvoiceReversal(id)/CreateCancellationDocument"]
rows_oil: 0
---
# CorrectionPurchaseInvoiceReversal
Reverses a correction purchase invoice, restoring the original A/P invoice state. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CorrectionPurchaseInvoiceReversal --top 5
./sapb1 query CorrectionPurchaseInvoiceReversal --count
./sapb1 query CorrectionPurchaseInvoiceReversal --select "DocNum,CardCode,DocDate,DocTotal" --top 10
# Open reversals only (returns nothing today — set is empty):
./sapb1 query CorrectionPurchaseInvoiceReversal --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardCode,DocDate,DocTotal"
```
## Key fields
Empty in JIVO_OIL_HANADB — key fields not inferable from live data. As a standard B1 marketing document it carries the usual header:
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code |
| DocDate | Posting date |
| DocTotal | Reversal total |
| DocumentStatus | Open or closed |
## Connections
- Domain: [[purchasing]]
- [[CorrectionPurchaseInvoice]] via base document refs — the correction being undone
- [[PurchaseInvoices]] via document chain — the original A/P invoice restored
- [[BusinessPartners]] via CardCode — the vendor on the reversed correction
