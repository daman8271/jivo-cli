---
entity: NFTaxCategoriesService
domain: financials-accounting-1
readable: false
methods: ["NFTaxCategoriesService_GetList"]
rows_oil: null
---
# NFTaxCategoriesService
Lists Nota Fiscal tax categories used in the Brazil localization for electronic invoice tax classification.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[NFTaxCategories]] — the entity set counterpart holding the category records (query this instead)
- [[SalesTaxCodes]] — Brazilian tax codes classified under these Nota Fiscal categories
