---
entity: SelfCreditMemoService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# SelfCreditMemoService
Handles self-issued credit memo workflows: fetching approval templates, processing approval requests, and cancellation.

## Operations
- SelfCreditMemoService_GetApprovalTemplates
- SelfCreditMemoService_HandleApprovalRequest
- SelfCreditMemoService_Cancel2

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops SelfCreditMemoService`. HandleApprovalRequest and Cancel2 mutate documents and are out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-2]]
- [[CreditNotes]] via DocEntry — the self-issued credit memos being approved/cancelled
- [[ApprovalTemplates]] via template code — approval templates applicable to self credit memos
- [[ApprovalRequests]] via request ID — approval requests raised for these documents
