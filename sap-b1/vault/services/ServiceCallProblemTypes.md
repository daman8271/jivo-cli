---
entity: ServiceCallProblemTypes
domain: service-contracts
readable: true
methods: ["GET ServiceCallProblemTypes(id)", "GET ServiceCallProblemTypes", "POST ServiceCallProblemTypes", "PATCH ServiceCallProblemTypes(id)", "DELETE ServiceCallProblemTypes(id)"]
rows_oil: 0
---
# ServiceCallProblemTypes
Top-level classification of what kind of problem a service call reports — empty here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceCallProblemTypes --top 5
./sapb1 query ServiceCallProblemTypes --count
./sapb1 query ServiceCallProblemTypes --select "ProblemTypeID,Name,Active" --top 10
# active problem types only
./sapb1 query ServiceCallProblemTypes --filter "Active eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| ProblemTypeID | Problem type code |
| Name | Problem type name |
| Description | Longer description |
| Active | Active/inactive flag |

## Connections
- Domain: [[service-contracts]]
- [[ServiceCalls]] via ProblemType — tickets classified under this type
- [[ServiceCallProblemSubTypes]] via parent problem type — nested second-level codes
