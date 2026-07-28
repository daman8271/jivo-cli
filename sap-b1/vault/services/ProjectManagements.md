---
entity: ProjectManagements
domain: projects
readable: true
methods: [GET, POST, PATCH, DELETE, CancelProject]
rows_oil: 0
---
# ProjectManagements
Full project-management (PM module) projects with stages, tasks, budgets, and status. Live rows in JIVO_OIL_HANADB: 0 — the PM module is unused here, so fields could not be inferred live.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ProjectManagements --top 5
./sapb1 query ProjectManagements --count
./sapb1 query ProjectManagements --select "AbsEntry,ProjectName,ProjectStatus,DueDate" --top 10
```
Useful filter — only projects still in progress (standard B1 status enum):
```bash
./sapb1 query ProjectManagements --filter "ProjectStatus eq 'pmst_Started'" --top 10
```

## Key fields
Set is empty in JIVO_OIL_HANADB, so no fields could be inferred from live data (run `./sapb1 fields ProjectManagements` once rows exist). Standard B1 Service Layer schema for reference:

| Field | Meaning |
|---|---|
| AbsEntry | Internal project key |
| ProjectName | Project display name |
| ProjectStatus | Status enum (started/paused/finished) |
| StartDate | Planned start date |
| DueDate | Planned finish date |
| Owner | Owning employee ID |
| BusinessPartner | Linked customer/vendor code |
| FinancialProject | Linked OPRJ project code |
| ProjectManagements_StagesCollection | Stage/phase lines |

## Connections
- Domain: [[projects]]
- [[Projects]] via FinancialProject — the financial OPRJ code the PM project posts against
- [[BusinessPartners]] via BusinessPartner (CardCode of the customer/vendor)
- [[EmployeesInfo]] via Owner and team-member employee IDs
- [[ProjectManagementTimeSheet]] — time sheet lines book hours against these projects
