---
entity: AccountCategory
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 54
---
# AccountCategory
Categories used to group G/L accounts for financial-report templates (P&L / balance sheet drawers). Live rows in JIVO_OIL_HANADB: 54.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AccountCategory --top 5
./sapb1 query AccountCategory --count
./sapb1 query AccountCategory --select "CategoryCode,CategoryName,CategorySource" --top 10
# Look up one report drawer by its name:
./sapb1 query AccountCategory --filter "CategoryName eq 'Operating Expenses'"
```

## Key fields
| Field | Meaning |
|---|---|
| CategoryCode | Unique category code (key) |
| CategoryName | Category display name |
| CategorySource | Report template source |

## Connections
- Domain: [[financials-accounting-1]]
- [[ChartOfAccounts]] via ChartOfAccounts.Category = CategoryCode — each G/L account is assigned to one report category
