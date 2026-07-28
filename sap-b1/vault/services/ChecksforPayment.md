---
entity: ChecksforPayment
domain: banking-payments
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# ChecksforPayment
Outgoing checks written to vendors/payees, tracking check number, bank, amount, and print status. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ChecksforPayment --top 5
./sapb1 query ChecksforPayment --count
./sapb1 query ChecksforPayment --select "CheckNumber,BankCode,CheckAmount,CardName" --top 10
# unprinted checks still waiting for a physical print run
./sapb1 query ChecksforPayment --filter "Printed eq 'tNO'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| CheckKey | Internal check key |
| CheckNumber | Printed check number |
| BankCode | Issuing bank code |
| BankName | Issuing bank name |
| Branch | Bank branch |
| AccountNumber | Bank account number |
| CheckDate | Check issue date |
| CardCode | Payee BP code |
| CardName | Payee name |
| CheckAmount | Check amount |
| Currency | Check currency |
| JournalEntryReference | Linked journal entry |
| VendorCode | Vendor BP code |
| Printed | Print status flag |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] via CardCode / VendorCode — the payee partner
- [[VendorPayments]] via CheckNumber — the outgoing payment that issued the check
- [[HouseBankAccounts]] via BankCode + AccountNumber — the drawing bank account
- [[JournalEntries]] via JournalEntryReference — the posted JE
- [[Currencies]] via Currency — check currency
