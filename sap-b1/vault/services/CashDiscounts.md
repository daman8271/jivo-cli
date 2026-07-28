---
entity: CashDiscounts
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# CashDiscounts
Defines cash discount schemes (early-payment discount rules) attachable to payment terms (empty in JIVO). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CashDiscounts --top 5
./sapb1 query CashDiscounts --count
./sapb1 query CashDiscounts --select "Code,Name,DiscByPayment" --top 10
# schemes that also discount freight
./sapb1 query CashDiscounts --filter "DiscByFrieght eq 'tYES'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| Code | Discount scheme key |
| Name | Scheme name |
| DiscByPayment | Discount on partial payment |
| DiscByFrieght | Discount includes freight |
| DiscByTax | Discount includes tax |
## Connections
- Domain: [[system-other-1]]
- [[PaymentTermsTypes]] via DiscountCode — terms that grant this cash discount
