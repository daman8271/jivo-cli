---
entity: ServiceCallProblemSubTypes
domain: service-contracts
readable: true
methods: ["GET ServiceCallProblemSubTypes(id)", "GET ServiceCallProblemSubTypes", "POST ServiceCallProblemSubTypes", "PATCH ServiceCallProblemSubTypes(id)", "DELETE ServiceCallProblemSubTypes(id)"]
rows_oil: 0
---
# ServiceCallProblemSubTypes
Second-level classification of service-call problems, nested under problem types — empty here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceCallProblemSubTypes --top 5
./sapb1 query ServiceCallProblemSubTypes --count
./sapb1 query ServiceCallProblemSubTypes --select "ProblemSubTypeID,Name,Active" --top 10
# active sub-types only
./sapb1 query ServiceCallProblemSubTypes --filter "Active eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| ProblemSubTypeID | Problem sub-type code |
| Name | Sub-type name |
| Description | Longer description |
| Active | Active/inactive flag |

## Connections
- Domain: [[service-contracts]]
- [[ServiceCalls]] via ProblemSubType — tickets classified under this sub-type
- [[ServiceCallProblemTypes]] via parent problem type — top-level code it nests under
