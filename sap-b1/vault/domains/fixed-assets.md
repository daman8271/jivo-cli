# Fixed Assets

SAP Business One's Fixed Assets module manages capitalized assets from acquisition to retirement. The asset master ([[FixedAssetItemsService]] on the write side, with [[AssetClasses]], [[AssetGroups]] and [[AssetDepreciationGroups]] as classification masters) is depreciated per [[DepreciationAreas]] using [[DepreciationTypes]] (pooled via [[DepreciationTypePools]]), while lifecycle documents — [[AssetCapitalization]], [[AssetTransfer]], [[AssetManualDepreciation]], [[AssetRetirement]] and [[AssetCapitalizationCreditMemo]] — post the value movements to the G/L. In JIVO's oil database this module carries configuration rows (depreciation areas/types) but no live asset transactions via these endpoints.

Part of the [[00-SAP-B1-Atlas]] — 23 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[DepreciationTypes]] **(4 rows)** — Defines fixed-asset depreciation calculation rules (method, rates, period controls, salvage/limits) that asset classes apply to compute periodic depreciation.
- [[AssetClasses]] **(3 rows)** — Asset class master data mapping asset categories to G/L account determinations and depreciation settings per area (3 classes defined).
- [[DepreciationAreas]] **(3 rows)** — Depreciation area definitions (book vs tax valuation views) governing how asset values and depreciation post to the G/L (3 areas defined).
- [[DepreciationTypePools]] **(1 row)** — Pools that bundle depreciation types for group/pooled depreciation calculation (1 pool defined).
- [[AssetCapitalization]] — Asset capitalization documents that record acquisition cost of fixed assets onto the balance sheet (0 rows in JIVO_OIL — fixed-asset module unused).
- [[AssetCapitalizationCreditMemo]] — Credit memo documents that reduce or reverse previously capitalized asset acquisition values (0 rows in JIVO_OIL).
- [[AssetCapitalizationCreditMemoService]] — RPC helper to list and cancel capitalization credit memo documents that reverse asset acquisition values.
- [[AssetCapitalizationService]] — RPC helper to list and cancel asset capitalization documents that put fixed assets on the books.
- [[AssetClassesService]] — RPC helper to enumerate asset class definitions.
- [[AssetDepreciationGroups]] — Grouping master data for reporting depreciation across sets of fixed assets (empty in JIVO_OIL).
- [[AssetDepreciationGroupsService]] — RPC helper to enumerate asset depreciation group definitions.
- [[AssetGroups]] — Fixed-asset group master data used to categorize asset items (empty in JIVO_OIL).
- [[AssetGroupsService]] — RPC helper to enumerate fixed-asset group definitions.
- [[AssetManualDepreciation]] — Documents posting manual (unplanned/extraordinary) depreciation on fixed assets (0 rows in JIVO_OIL).
- [[AssetManualDepreciationService]] — RPC helper to list and cancel manual depreciation postings for fixed assets.
- [[AssetRetirement]] — Asset retirement documents recording disposal, sale, or scrapping of fixed assets off the books (0 rows in JIVO_OIL).
- [[AssetRetirementService]] — RPC helper to list and cancel asset retirement (disposal/sale/scrap) documents.
- [[AssetTransfer]] — Documents transferring fixed assets between asset classes, cost centers, or employees (0 rows in JIVO_OIL).
- [[AssetTransferService]] — RPC helper to list and cancel asset transfer documents that move assets between classes or cost centers.
- [[DepreciationTypePoolsService]] — RPC helper to enumerate depreciation type pool definitions.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[DepreciationAreasService]] — POST-only RPC helper to enumerate depreciation area definitions.
- [[DepreciationTypesService]] — POST-only RPC helper to enumerate depreciation calculation method (type) definitions.
- [[FixedAssetItemsService]] — RPC functions to read fixed-asset item planned values and period end balances (and update end balances) per depreciation area.
