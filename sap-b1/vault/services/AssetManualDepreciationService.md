---
entity: AssetManualDepreciationService
domain: fixed-assets
readable: true
methods: [AssetManualDepreciationService_Cancel, AssetManualDepreciationService_GetList]
rows_oil: null
---
# AssetManualDepreciationService
RPC helper to list and cancel manual depreciation postings for fixed assets.

## Operations
- `AssetManualDepreciationService_Cancel` — cancels a manual depreciation document (write — out of scope under the read-only rule)
- `AssetManualDepreciationService_GetList` — lists manual depreciation documents

Entity sets are the read path in the CLI — read the documents via [[AssetManualDepreciation]]. Browse this service's operations with `./sapb1 ops AssetManualDepreciationService`.

## Connections
- Domain: [[fixed-assets]]
- [[AssetManualDepreciation]] — the entity set this service lists and cancels (DocEntry)
