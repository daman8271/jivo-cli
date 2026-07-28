---
entity: PaymentReasonCodeService
domain: banking-payments
readable: false
methods: ["PaymentReasonCodeService_GetPaymentReasonCodeList"]
rows_oil: null
---
# PaymentReasonCodeService
RPC helper that lists payment reason codes attached to bank-transfer payments for regulatory reporting.
## Operations
- `PaymentReasonCodeService_GetPaymentReasonCodeList`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here; entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops PaymentReasonCodeService`.
## Connections
- Domain: [[banking-payments]]
