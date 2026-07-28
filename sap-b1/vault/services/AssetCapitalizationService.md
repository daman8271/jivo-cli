---
entity: AssetCapitalizationService
domain: fixed-assets
readable: true
methods: [AssetCapitalizationService_Cancel, AssetCapitalizationService_GetList]
rows_oil: null
---
# AssetCapitalizationService
RPC helper to list and cancel asset capitalization documents that put fixed assets on the books.

## Operations
- `AssetCapitalizationService_Cancel` — cancels a capitalization document (write — out of scope under the read-only rule)
- `AssetCapitalizationService_GetList` — lists capitalization documents

Entity sets are the read path in the CLI — read the documents via [[AssetCapitalization]]. Browse this service's operations with `./sapb1 ops AssetCapitalizationService`.

## Connections
- Domain: [[fixed-assets]]
- [[AssetCapitalization]] — the entity set this service lists and cancels (DocEntry)
