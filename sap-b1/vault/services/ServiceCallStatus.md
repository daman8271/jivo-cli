---
entity: ServiceCallStatus
domain: service-contracts
readable: true
methods: ["GET ServiceCallStatus(id)", "GET ServiceCallStatus", "POST ServiceCallStatus", "PATCH ServiceCallStatus(id)", "DELETE ServiceCallStatus(id)"]
rows_oil: 3
---
# ServiceCallStatus
Lifecycle status codes for service calls (open/pending/closed) — 3 seed values. Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceCallStatus --top 5
./sapb1 query ServiceCallStatus --count
./sapb1 query ServiceCallStatus --select "StatusId,Name,Active" --top 10
# active status codes only
./sapb1 query ServiceCallStatus --filter "Active eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| StatusId | Status code |
| Name | Status name |
| Description | Longer description |
| Active | Active/inactive flag |

## Connections
- Domain: [[service-contracts]]
- [[ServiceCalls]] via Status — tickets carrying this lifecycle status
