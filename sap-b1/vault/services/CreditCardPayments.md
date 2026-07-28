---
entity: CreditCardPayments
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# CreditCardPayments
Setup table defining credit-card due-date/settlement schedules used when clearing card vouchers. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CreditCardPayments --top 5
./sapb1 query CreditCardPayments --count
./sapb1 query CreditCardPayments --select "DueDateCode,DueDateName,DueDateDay" --top 10
# schedules that settle in more than one installment
./sapb1 query CreditCardPayments --filter "PaymentsNo gt 1" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| DueDateCode | Schedule code (key) |
| DueDateName | Schedule name |
| DueDateNumOfMonths | Months until settlement |
| DueDateDay | Settlement day of month |
| PaymentsNo | Number of installments |
## Connections
- Domain: [[banking-payments]]
- [[CreditCards]] — card companies whose vouchers settle on these DueDateCode schedules
- [[CreditPaymentMethods]] via DueDateCode — payment methods referencing a settlement schedule
