---
entity: PurchaseTaxInvoices
domain: purchasing
readable: true
methods: ["GET PurchaseTaxInvoices(id)", "GET PurchaseTaxInvoices", "POST PurchaseTaxInvoices", "PATCH PurchaseTaxInvoices(id)"]
rows_oil: 0
---
# PurchaseTaxInvoices
Localization-specific incoming tax invoice documents that record VAT/tax details for purchases separately from the A/P invoice (unused in JIVO_OIL_HANADB — 0 rows, so key fields are from standard SAP marketing-document schema, not live data). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseTaxInvoices --top 5
./sapb1 query PurchaseTaxInvoices --count
./sapb1 query PurchaseTaxInvoices --select "DocNum,CardName,DocDate,DocTotal" --top 10
# If rows ever appear, check for any tax invoices from this financial year:
./sapb1 query PurchaseTaxInvoices --filter "DocDate ge '2026-04-01'" --select "DocNum,CardName,DocDate,DocTotal"
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Vendor code |
| CardName | Vendor name |
| DocDate | Posting date |
| DocTotal | Total tax invoice value |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| Comments | Free-text remarks |
## Connections
- Domain: [[purchasing]]
- [[BusinessPartners]] via CardCode — the vendor issuing the tax invoice
- [[PurchaseInvoices]] via base document refs — the A/P invoice the tax document accompanies
- [[Currencies]] via DocCurrency — currency of DocTotal
