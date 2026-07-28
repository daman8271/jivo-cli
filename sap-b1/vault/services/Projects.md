---
entity: Projects
domain: projects
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# Projects
Financial project codes (OPRJ) used to tag transactions and documents for project-level P&L reporting. Live rows in JIVO_OIL_HANADB: 0 — no project codes are defined, so fields could not be inferred live.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Projects --top 5
./sapb1 query Projects --count
./sapb1 query Projects --select "Code,Name,ValidFrom,ValidTo" --top 10
```
Useful filter — only currently active project codes:
```bash
./sapb1 query Projects --filter "Active eq 'tYES'" --top 10
```

## Key fields
Set is empty in JIVO_OIL_HANADB, so no fields could be inferred from live data (run `./sapb1 fields Projects` once rows exist). Standard B1 Service Layer schema (OPRJ) for reference:

| Field | Meaning |
|---|---|
| Code | Project code (key) |
| Name | Project description |
| ValidFrom | Validity start date |
| ValidTo | Validity end date |
| Active | Active flag (tYES/tNO) |

## Connections
- Domain: [[projects]]
- [[ChartOfAccounts]] via ProjectCode — G/L accounts can default a project code
- [[JournalEntries]] via JournalEntryLines.ProjectCode tagging postings
- [[Invoices]] via DocumentLines.ProjectCode on A/R invoice rows
- [[Orders]] via DocumentLines.ProjectCode on sales order rows
