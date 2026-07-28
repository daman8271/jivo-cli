---
entity: PaymentBlocksService
domain: banking-payments
readable: false
methods: ["PaymentBlocksService_GetPaymentBlockList"]
rows_oil: null
---
# PaymentBlocksService
RPC helper that lists payment block reason codes used to hold documents from the payment wizard.
## Operations
- `PaymentBlocksService_GetPaymentBlockList`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity set: query [[PaymentBlocks]] directly. Browse this service's operations with `./sapb1 ops PaymentBlocksService`.
## Connections
- Domain: [[banking-payments]]
- [[PaymentBlocks]] — the entity set holding the block reason codes (query this instead)
