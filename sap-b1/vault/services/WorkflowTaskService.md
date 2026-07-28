---
entity: WorkflowTaskService
domain: administration-setup-2
readable: false
methods: ["WorkflowTaskService_Complete", "WorkflowTaskService_GetApprovalTaskList"]
rows_oil: null
---
# WorkflowTaskService
Retrieves and completes workflow approval tasks assigned to users in document approval processes.

## Operations
- WorkflowTaskService_Complete
- WorkflowTaskService_GetApprovalTaskList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI; for approval-process data read [[ApprovalRequests]] instead. The Complete operation is a write and stays out of scope under our standing READ-ONLY rule. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WorkflowTaskService
```

## Connections
- Domain: [[administration-setup-2]]
- [[ApprovalRequests]] — the approval requests whose pending tasks this service lists and completes
- [[Users]] — the user accounts approval tasks are assigned to
