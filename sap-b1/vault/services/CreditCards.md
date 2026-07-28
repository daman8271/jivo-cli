---
entity: CreditCards
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# CreditCards
Master list of credit-card companies accepted for payment, each mapped to a clearing G/L account. Live rows in JIVO_OIL_HANADB: 1.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CreditCards --top 5
./sapb1 query CreditCards --count
./sapb1 query CreditCards --select "CreditCardCode,CreditCardName,GLAccount" --top 10
# cards that have a clearing G/L account mapped
./sapb1 query CreditCards --filter "GLAccount ne null" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| CreditCardCode | Card company code (key) |
| CreditCardName | Card company name |
| GLAccount | Clearing G/L account |
| CompanyID | Card company tax ID |
| CountryCode | Card company country |
| Telephone | Card company phone |
## Connections
- Domain: [[banking-payments]]
- [[ChartOfAccounts]] via GLAccount — the clearing account for card vouchers
- [[CreditCardPayments]] via DueDateCode — settlement schedules for this card
- [[CreditPaymentMethods]] via CreditCard — payment methods defined per card company
