---
entity: ProjectManagementTimeSheet
domain: projects
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# ProjectManagementTimeSheet
Employee time sheets recording hours worked per period against project-management projects/activities. Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ProjectManagementTimeSheet --top 5
./sapb1 query ProjectManagementTimeSheet --count
./sapb1 query ProjectManagementTimeSheet --select "AbsEntry,DocNumber,UserCode,DateFrom,DateTo" --top 10
```
Useful filter — time sheets covering a given fiscal period:
```bash
./sapb1 query ProjectManagementTimeSheet --filter "DateFrom ge '2025-04-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal time sheet key |
| DocNumber | Time sheet document number |
| DateFrom | Reporting period start |
| DateTo | Reporting period end |
| UserCode | B1 user login code |
| UserID | Internal user ID |
| OwnerCode | Owning employee code |
| FirstName | Owner first name |
| LastName | Owner last name |
| Department | Owner department code |
| TimeSheetType | Owner type (user/employee) |
| PM_TimeSheetLineDataCollection | Per-day activity/hour lines |
| AttachmentEntry | Linked attachment key |

## Connections
- Domain: [[projects]]
- [[ProjectManagements]] via line-level project references — hours are booked to PM projects/activities
- [[EmployeesInfo]] via OwnerCode (owning employee)
- [[Users]] via UserCode / UserID (B1 login that filed the sheet)
- [[Departments]] via Department (owner's department code)
