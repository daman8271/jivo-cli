---
entity: ChangeLogsService
domain: administration-setup-1
readable: false
methods: [ChangeLogsService_GetChangeLog, ChangeLogsService_GetChangeLogDifferences]
rows_oil: null
---
# ChangeLogsService
Retrieves the audit change-log history and field-level differences for a given object instance.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[Users]] — who made each logged change (UserName)
