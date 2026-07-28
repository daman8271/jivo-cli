---
entity: VendorPayments
domain: banking-payments
readable: true
methods: [GET, POST, PATCH]
rows_oil: 14197
---
# VendorPayments
Outgoing payments to vendors (cash/check/transfer) clearing open A/P invoices — the A/P mirror of IncomingPayments. Live rows in JIVO_OIL_HANADB: 14197.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query VendorPayments --top 5
./sapb1 query VendorPayments --count
./sapb1 query VendorPayments --select "DocNum,DocDate,CardName,TransferSum" --top 10
# live (non-cancelled) vendor payments this fiscal year
./sapb1 query VendorPayments --filter "Cancelled eq 'tNO' and DocDate ge '2026-04-01'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal key |
| DocNum | Payment number |
| DocDate | Posting date |
| DueDate | Due date |
| CardCode | Vendor BP code |
| CardName | Vendor name |
| DocType | Vendor / account type |
| CashSum | Cash amount paid |
| TransferSum | Bank-transfer amount |
| TransferAccount | Transfer G/L account |
| TransferDate | Transfer value date |
| BankCode | Paying bank code |
| DocCurrency | Payment currency |
| Cancelled | Cancellation flag |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] via CardCode — the paid vendor
- [[PurchaseInvoices]] — A/P invoices cleared on the payment's invoice lines
- [[HouseBankAccounts]] via BankCode — the paying bank account
- [[ChartOfAccounts]] via TransferAccount — G/L account debited
- [[ChecksforPayment]] via CheckNumber — checks issued by the payment
- [[JournalEntries]] — the JE posted by the payment
- [[Currencies]] via DocCurrency — payment currency
