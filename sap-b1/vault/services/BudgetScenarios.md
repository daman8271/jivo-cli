---
entity: BudgetScenarios
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 267
---
# BudgetScenarios
Named budget scenarios (main/optimistic/pessimistic per fiscal year) that budget amounts are recorded against. Live rows in JIVO_OIL_HANADB: 267.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BudgetScenarios --top 5
./sapb1 query BudgetScenarios --count
./sapb1 query BudgetScenarios --select "Numerator,Name,StartofFiscalYear,BasicBudget" --top 10
# Scenarios for the current Indian fiscal year (starts 1 April):
./sapb1 query BudgetScenarios --filter "StartofFiscalYear ge '2025-04-01'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| Numerator | Scenario key |
| Name | Scenario display name |
| StartofFiscalYear | Fiscal year start date |
| BasicBudget | Base scenario reference |
| InitialRatioPercentage | Percent of base budget |
| RoundingMethod | Amount rounding rule |
| Project | Linked project code |
| DistributionRule | Linked distribution rule |
| U_UNE_FRDT | Custom from-date (UDF) |
| U_UNE_TODT | Custom to-date (UDF) |

## Connections
- Domain: [[financials-accounting-1]]
- [[Budgets]] via Numerator = BudgetScenario — budget rows are recorded against a scenario
- [[Projects]] via Project — optional project scoping of a scenario
- [[DistributionRules]] via DistributionRule — optional cost-accounting distribution link
