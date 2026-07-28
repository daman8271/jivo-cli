---
entity: Queue
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# Queue
Service-module queues for routing incoming service calls to technician teams; empty here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Queue --top 5
./sapb1 query Queue --count
./sapb1 query Queue --select "QueueID,Description" --top 10
# Look up one queue by its id (if queues are ever defined):
./sapb1 query Queue --filter "QueueID eq 'Q1'" --top 5
```
Set is empty here — confirm live field names with `./sapb1 fields Queue` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| QueueID | Queue string id (key) |
| Description | Queue display name |
| QueueMembers | Technician users in queue |

(No key fields captured in recon — the set is empty; fields above are the standard Service Layer schema.)

## Connections
- Domain: [[administration-setup-3]]
- [[ServiceCalls]] via Queue (call routed to queue id)
- [[Users]] via QueueMembers → user code
