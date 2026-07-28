---
entity: PaymentTermsTypes
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 29
---
# PaymentTermsTypes
Payment-terms definitions (net days, installments, credit limits, default price list) assigned to business partners. Live rows in JIVO_OIL_HANADB: 29.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PaymentTermsTypes --top 5
./sapb1 query PaymentTermsTypes --count
./sapb1 query PaymentTermsTypes --select "GroupNumber,PaymentTermsGroupName,NumberOfAdditionalDays" --top 10
# terms granting net-30 or longer
./sapb1 query PaymentTermsTypes --filter "NumberOfAdditionalDays ge 30" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| GroupNumber | Terms group key |
| PaymentTermsGroupName | Terms name |
| StartFrom | Due-date baseline start |
| NumberOfAdditionalDays | Net days added |
| NumberOfAdditionalMonths | Months added |
| NumberOfInstallments | Installment count |
| CreditLimit | Default credit limit |
| GeneralDiscount | Default discount percent |
| DiscountCode | Cash-discount code |
| DunningCode | Dunning-term code |
| PriceListNo | Default price list |
| NumberOfToleranceDays | Grace days tolerated |
| BaselineDate | Baseline date rule |
| OpenReceipt | Open-incoming-payment flag |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] via PayTermsGrpCode → GroupNumber — terms assigned to partners
- [[PriceLists]] via PriceListNo — default price list for the terms
- [[CashDiscounts]] via DiscountCode — early-payment discount scheme
- [[DunningTerms]] via DunningCode — dunning behavior for overdue items
