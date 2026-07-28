---
entity: ServiceCallSolutionStatus
domain: service-contracts
readable: true
methods: ["GET ServiceCallSolutionStatus(id)", "GET ServiceCallSolutionStatus", "POST ServiceCallSolutionStatus", "PATCH ServiceCallSolutionStatus(id)", "DELETE ServiceCallSolutionStatus(id)"]
rows_oil: 3
---
# ServiceCallSolutionStatus
Status codes for knowledge-base solutions (e.g. internal, review, published) — 3 seed values. Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceCallSolutionStatus --top 5
./sapb1 query ServiceCallSolutionStatus --count
./sapb1 query ServiceCallSolutionStatus --select "StatusId,Name,Active" --top 10
# active solution-status codes only
./sapb1 query ServiceCallSolutionStatus --filter "Active eq 'tYES'" --top 10
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
- [[KnowledgeBaseSolutions]] via Status — solutions carrying this publication status
