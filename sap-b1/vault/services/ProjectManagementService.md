---
entity: ProjectManagementService
domain: projects
readable: false
methods: [GetSubprojectsList, GetSubproject, AddSubproject, UpdateSubproject, DeleteSubproject]
rows_oil: null
---
# ProjectManagementService
RPC-style service for managing subprojects nested under project-management projects (list, fetch, add, update, delete).

## Operations
- `GetSubprojectsList` — list subprojects of a PM project
- `GetSubproject` — fetch one subproject
- `AddSubproject` — create a subproject
- `UpdateSubproject` — modify a subproject
- `DeleteSubproject` — remove a subproject

Entity sets are the read path in the CLI — this RPC service is not queryable via `./sapb1 query`; browse its catalogued operations with `./sapb1 ops ProjectManagementService`. The Add/Update/Delete operations are out of scope under our standing READ-ONLY rule.

## Connections
- Domain: [[projects]]
- [[ProjectManagements]] — the parent PM projects whose subprojects this service manages
