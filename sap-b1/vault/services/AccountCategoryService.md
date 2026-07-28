---
entity: AccountCategoryService
domain: financials-accounting-1
readable: true
methods: ["AccountCategoryService_GetCategoryList"]
rows_oil: null
---
# AccountCategoryService
Returns the list of G/L account categories (drawer/level groupings) used to classify accounts in the chart of accounts.

## Operations
- `AccountCategoryService_GetCategoryList` (GET)
- `AccountCategoryService_GetCategoryList` (POST)

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. Entity sets are the read path in the CLI: query [[AccountCategory]] for the same category records. Browse this service's operations with `./sapb1 ops AccountCategoryService`.

## Connections
- Domain: [[financials-accounting-1]]
- [[AccountCategory]] — the entity set counterpart holding the category records (query this instead)
- [[ChartOfAccounts]] — accounts reference these categories for drawer/level grouping
