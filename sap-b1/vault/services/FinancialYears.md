---
entity: FinancialYears
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 3
---
# FinancialYears
Defines fiscal years (start/end dates and assessment year) used for period control and India TCS accumulation. Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query FinancialYears --top 5
./sapb1 query FinancialYears --count
./sapb1 query FinancialYears --select "Code,Description,StartDate,EndDate" --top 10
```
Useful filter — the current (2025–26 onward) India fiscal years:
```bash
./sapb1 query FinancialYears --filter "StartDate ge '2025-04-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal entry number (key) |
| Code | Fiscal year code |
| Description | Fiscal year label |
| StartDate | Year start date |
| EndDate | Year end date |
| AssessYear | India income-tax assessment year |
| TCSAccumulationBase | TCS accumulation base setting |

## Connections
- Domain: [[financials-accounting-2]]
- PostingPeriods via period date ranges falling inside the fiscal year (no PostingPeriods service exists in the Service Layer catalog)
