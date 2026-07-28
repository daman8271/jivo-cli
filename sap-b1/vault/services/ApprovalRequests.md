---
entity: ApprovalRequests
domain: administration-setup-3
readable: true
methods: [GET, PATCH]
rows_oil: 57184
---
# ApprovalRequests
Tracks live document-approval workflow requests — which draft/document is awaiting whose sign-off, at which stage, and its decision status. Live rows in JIVO_OIL_HANADB: 57184.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ApprovalRequests --top 5
./sapb1 query ApprovalRequests --count
./sapb1 query ApprovalRequests --select "Code,ObjectType,Status,CreationDate" --top 10
# Everything still waiting for sign-off:
./sapb1 query ApprovalRequests --filter "Status eq 'arsPending'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Request numeric key |
| ApprovalTemplatesID | Triggering approval template |
| CurrentStage | Stage now awaiting approval |
| ObjectType | Document object type code |
| ObjectEntry | Posted document DocEntry |
| DraftEntry | Awaiting draft DocEntry |
| DraftType | Draft's object type |
| IsDraft | Still a draft flag |
| OriginatorID | Requesting user ID |
| Status | Pending/approved/rejected state |
| CreationDate | Request creation date |
| CreationTime | Request creation time |
| Remarks | Free-text request remarks |

## Connections
- Domain: [[administration-setup-3]]
- [[ApprovalTemplates]] via ApprovalTemplatesID — template that fired this request
- [[ApprovalStages]] via CurrentStage — stage the request sits at
- [[Users]] via OriginatorID — user who originated the document
- [[Drafts]] via DraftEntry — draft held pending approval
