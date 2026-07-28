---
entity: DistributionRulesService
domain: financials-accounting-1
readable: false
methods: ["DistributionRulesService_GetDistributionRuleList"]
rows_oil: null
---
# DistributionRulesService
Lists distribution rules that allocate revenues and expenses across profit/cost centers by percentage.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[DistributionRules]] — the entity set counterpart holding the rule records (query this instead)
- [[ProfitCenters]] — the centers each rule distributes amounts to (CenterCode per rule line)
- [[Dimensions]] — the dimension each rule belongs to (InWhichDimension)
