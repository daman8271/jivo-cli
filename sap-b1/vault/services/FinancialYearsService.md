---
entity: FinancialYearsService
domain: financials-accounting-1
readable: false
methods: ["FinancialYearsService_GetFinancialYearList"]
rows_oil: null
---
# FinancialYearsService
Lists fiscal years defined for fixed-asset depreciation and financial reporting.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[FinancialYears]] — the entity set counterpart holding the fiscal year records (query this instead)
- [[DepreciationAreas]] — depreciation runs are computed per fiscal year in each area
- Posting periods — fiscal years align with the company's posting periods (no PostingPeriods entity set in this catalog)
