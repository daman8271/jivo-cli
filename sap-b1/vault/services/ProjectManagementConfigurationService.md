---
entity: ProjectManagementConfigurationService
domain: projects
readable: false
methods: [GetSubprojectTypes, AddSubprojectTypes, UpdateSubprojectTypes, DeleteSubprojectTypes, GetStageTypes, AddStageTypes, UpdateStageTypes, DeleteStageTypes, GetAreas, AddAreas, UpdateAreas, DeleteAreas, GetPriorities, AddPriorities, UpdatePriorities, DeletePriorities, GetActivities, AddActivities, UpdateActivities, DeleteActivities, GetTasks, AddTasks, UpdateTasks, DeleteTasks]
rows_oil: null
---
# ProjectManagementConfigurationService
RPC-style configuration service for project-management master setup data: subproject types, stage types, areas, priorities, activity types, and task types used by PM projects.

## Operations
- `GetSubprojectTypes` / `AddSubprojectTypes` / `UpdateSubprojectTypes` / `DeleteSubprojectTypes` — subproject type setup
- `GetStageTypes` / `AddStageTypes` / `UpdateStageTypes` / `DeleteStageTypes` — project stage type setup
- `GetAreas` / `AddAreas` / `UpdateAreas` / `DeleteAreas` — project area setup
- `GetPriorities` / `AddPriorities` / `UpdatePriorities` / `DeletePriorities` — priority level setup
- `GetActivities` / `AddActivities` / `UpdateActivities` / `DeleteActivities` — activity type setup
- `GetTasks` / `AddTasks` / `UpdateTasks` / `DeleteTasks` — task type setup

Entity sets are the read path in the CLI — this RPC service is not queryable via `./sapb1 query`; browse its catalogued operations with `./sapb1 ops ProjectManagementConfigurationService`. The Add/Update/Delete operations are out of scope under our standing READ-ONLY rule.

## Connections
- Domain: [[projects]]
- [[ProjectManagements]] — PM projects consume these setup types (stage types, areas, priorities, activity/task types)
