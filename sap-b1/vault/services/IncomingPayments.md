---
entity: IncomingPayments
domain: banking-payments
readable: true
methods: [GET, POST, PATCH]
rows_oil: 13759
---
# IncomingPayments
Customer receipts (cash/check/transfer/card) clearing open A/R invoices — a core high-volume ledger. Live rows in JIVO_OIL_HANADB: 13759.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query IncomingPayments --top 5
./sapb1 query IncomingPayments --count
./sapb1 query IncomingPayments --select "DocNum,DocDate,CardName,TransferSum" --top 10
# live (non-cancelled) receipts this fiscal year
./sapb1 query IncomingPayments --filter "Cancelled eq 'tNO' and DocDate ge '2026-04-01'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal key |
| DocNum | Receipt number |
| DocDate | Posting date |
| DueDate | Due date |
| CardCode | Customer BP code |
| CardName | Customer name |
| DocType | Customer / account type |
| CashSum | Cash amount received |
| TransferSum | Bank-transfer amount |
| TransferAccount | Transfer G/L account |
| TransferDate | Transfer value date |
| DocCurrency | Receipt currency |
| BankCode | Receiving bank code |
| Cancelled | Cancellation flag |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] via CardCode — the paying customer
- [[Invoices]] — A/R invoices cleared on the receipt's invoice lines
- [[HouseBankAccounts]] via BankCode / TransferAccount — receiving bank account
- [[ChartOfAccounts]] via TransferAccount — G/L account credited
- [[Projects]] — project dimension on the receipt
- [[Currencies]] via DocCurrency — receipt currency
- [[JournalEntries]] — the JE posted by the receipt
