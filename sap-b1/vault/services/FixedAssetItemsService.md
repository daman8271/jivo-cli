---
entity: FixedAssetItemsService
domain: fixed-assets
readable: false
methods: [FixedAssetItemsService_GetAssetValuesList, FixedAssetItemsService_GetAssetEndBalance, FixedAssetItemsService_UpdateAssetEndBalance]
rows_oil: null
---
# FixedAssetItemsService
RPC functions to read fixed-asset item planned values and period end balances (and update end balances) per depreciation area.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[fixed-assets]]
- [[Items]] — fixed-asset item masters whose values/balances these functions address
- [[DepreciationAreas]] — depreciation area each value/balance query is scoped to
