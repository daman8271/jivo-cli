---
entity: CreditPaymentMethods
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# CreditPaymentMethods
Setup of credit-card payment methods (installments, amount ranges) per card company. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CreditPaymentMethods --top 5
./sapb1 query CreditPaymentMethods --count
./sapb1 query CreditPaymentMethods --select "PaymentMethodCode,Name,NumOfPayments" --top 10
# installment methods (more than a single payment)
./sapb1 query CreditPaymentMethods --filter "NumOfPayments gt 1" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| PaymentMethodCode | Method code (key) |
| Name | Method name |
| CreditCard | Card company code |
| MinimumAmount | Minimum eligible amount |
| MaximumAmount | Maximum eligible amount |
| NumOfPayments | Installment count |
## Connections
- Domain: [[banking-payments]]
- [[CreditCards]] via CreditCard — the card company this method belongs to
- [[CreditCardPayments]] via DueDateCode — the settlement schedule applied
