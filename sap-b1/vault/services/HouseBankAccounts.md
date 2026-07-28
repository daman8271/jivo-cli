---
entity: HouseBankAccounts
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 5
---
# HouseBankAccounts
The company's own bank accounts with G/L mappings, check numbering, and payment-series defaults. Live rows in JIVO_OIL_HANADB: 5.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query HouseBankAccounts --top 5
./sapb1 query HouseBankAccounts --count
./sapb1 query HouseBankAccounts --select "BankCode,AccNo,AccountName,GLAccount" --top 10
# accounts held at a specific bank
./sapb1 query HouseBankAccounts --filter "Country eq 'IN'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsoluteEntry | Internal key |
| BankCode | Bank code |
| AccNo | Account number |
| AccountName | Account display name |
| Branch | Bank branch |
| GLAccount | Mapped G/L account |
| GLInterimAccount | Interim clearing account |
| IBAN | IBAN number |
| BICSwiftCode | SWIFT/BIC code |
| NextCheckNo | Next check number |
| Country | Bank country |
| IncomingPaymentSeries | Default receipt series |
| OutgoingPaymentSeries | Default payment series |
| JournalEntrySeries | Default JE series |
## Connections
- Domain: [[banking-payments]]
- [[Banks]] via BankCode — the bank master this account belongs to
- [[ChartOfAccounts]] via GLAccount / GLInterimAccount — ledger mapping
- [[IncomingPayments]] via BankCode — receipts landing in this account
- [[VendorPayments]] via BankCode — outgoing payments drawn from it
- [[Deposits]] via BankCode + BankAccountNum — deposits into this account
- [[Countries]] via Country — bank country
