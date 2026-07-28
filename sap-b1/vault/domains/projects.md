# Projects

Two flavours of 'project' in SAP B1: lightweight financial project codes ([[Projects]] — stamped on document lines and journal entries via ProjectCode for P&L segmentation; the endpoint reads fine but reports 0 rows at JIVO) and the full project-management module ([[ProjectManagements]] with stages/tasks and [[ProjectManagementTimeSheet]] for labour booking — unused here). The RPC services cover both plus module configuration.

Part of the [[00-SAP-B1-Atlas]] — 6 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[ProjectManagementTimeSheet]] **(1 row)** — Employee time sheets recording hours worked per period against project-management projects/activities.
- [[ProjectManagements]] — Full project-management (PM module) projects with stages, tasks, budgets, and status. Live rows in JIVO_OIL_HANADB: 0 — the PM module is unused here, so fields could not be inferred live.
- [[Projects]] — Financial project codes (OPRJ) used to tag transactions and documents for project-level P&L reporting. Live rows in JIVO_OIL_HANADB: 0 — no project codes are defined, so fields could not be inferred live.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[ProjectManagementConfigurationService]] — RPC-style configuration service for project-management master setup data: subproject types, stage types, areas, priorities, activity types, and task types used by PM projects.
- [[ProjectManagementService]] — RPC-style service for managing subprojects nested under project-management projects (list, fetch, add, update, delete).
- [[ProjectsService]] — RPC-style helper returning the list of financial project codes (OPRJ) for lookup/selection.
