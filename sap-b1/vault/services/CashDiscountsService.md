---
entity: CashDiscountsService
domain: administration-setup-1
readable: false
methods: [CashDiscountsService_GetCashDiscountList]
rows_oil: null
---
# CashDiscountsService
Lists cash discount definitions applied via payment terms for early-payment incentives.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[CashDiscounts]] — the cash discount definition records this RPC lists (Code)
- [[PaymentTermsTypes]] — payment terms reference a cash discount code (DiscountCode)
