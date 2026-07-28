---
entity: PaymentCalculationService
domain: banking-payments
readable: false
methods: ["PaymentCalculationService_GetPaymentAmount"]
rows_oil: null
---
# PaymentCalculationService
RPC helper that computes the payable amount for a document (applying cash discounts and payment terms).
## Operations
- `PaymentCalculationService_GetPaymentAmount`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity sets: document totals and open balances come from [[Invoices]], and the discount/terms rules from [[PaymentTermsTypes]]. Browse this service's operations with `./sapb1 ops PaymentCalculationService`.
## Connections
- Domain: [[banking-payments]]
- [[Invoices]] — documents whose payable amount it computes
- [[PaymentTermsTypes]] — cash-discount and due-date rules applied
