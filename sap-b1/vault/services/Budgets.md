---
entity: Budgets
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 164
---
# Budgets
Per-account annual budget amounts and balances by scenario and fiscal year for budget-vs-actual control. Live rows in JIVO_OIL_HANADB: 164.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Budgets --top 5
./sapb1 query Budgets --count
./sapb1 query Budgets --select "AccountCode,BudgetScenario,TotalAnnualBudgetDebitLoc,BudgetBalanceDebitLoc" --top 10
# All budget rows in the main scenario (Numerator 1 in BudgetScenarios):
./sapb1 query Budgets --filter "BudgetScenario eq 1" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| Numerator | Internal budget row key |
| AccountCode | Budgeted G/L account |
| BudgetScenario | Scenario numerator reference |
| DivisionCode | Distribution method used |
| StartofFiscalYear | Fiscal year start date |
| ParentAccountKey | Parent account in hierarchy |
| ParentAccPercent | Percent of parent budget |
| TotalAnnualBudgetDebitLoc | Annual debit budget (local) |
| TotalAnnualBudgetCreditLoc | Annual credit budget (local) |
| BudgetBalanceDebitLoc | Remaining debit balance |
| BudgetBalanceCreditLoc | Remaining credit balance |
| BudgetLines | Monthly budget line collection |

## Connections
- Domain: [[financials-accounting-1]]
- [[ChartOfAccounts]] via AccountCode = Code — the G/L account each budget row controls
- [[BudgetScenarios]] via BudgetScenario = Numerator — the scenario/fiscal year the amounts belong to
- [[BudgetDistributions]] via DivisionCode — how the annual amount is spread across months
