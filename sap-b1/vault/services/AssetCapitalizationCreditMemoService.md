---
entity: AssetCapitalizationCreditMemoService
domain: fixed-assets
readable: true
methods: [AssetCapitalizationCreditMemoService_Cancel, AssetCapitalizationCreditMemoService_GetList]
rows_oil: null
---
# AssetCapitalizationCreditMemoService
RPC helper to list and cancel capitalization credit memo documents that reverse asset acquisition values.

## Operations
- `AssetCapitalizationCreditMemoService_Cancel` — cancels a capitalization credit memo (write — out of scope under the read-only rule)
- `AssetCapitalizationCreditMemoService_GetList` — lists capitalization credit memos

Entity sets are the read path in the CLI — read the documents via [[AssetCapitalizationCreditMemo]]. Browse this service's operations with `./sapb1 ops AssetCapitalizationCreditMemoService`.

## Connections
- Domain: [[fixed-assets]]
- [[AssetCapitalizationCreditMemo]] — the entity set this service lists and cancels (DocEntry)
