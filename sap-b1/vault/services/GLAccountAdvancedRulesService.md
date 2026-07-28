---
entity: GLAccountAdvancedRulesService
domain: financials-accounting-1
readable: false
methods: ["GLAccountAdvancedRulesService_GetList"]
rows_oil: null
---
# GLAccountAdvancedRulesService
Lists advanced G/L account determination rules that override default inventory posting accounts by criteria like item group or warehouse.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[GLAccountAdvancedRules]] — the entity set counterpart holding the rule records (query this instead)
- [[ChartOfAccounts]] — the override G/L accounts each rule posts to
- [[ItemGroups]] — a rule criterion (ItemGroup)
- [[Warehouses]] — a rule criterion (Warehouse)
