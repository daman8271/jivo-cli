---
entity: KnowledgeBaseSolutions
domain: service-contracts
readable: true
methods: ["GET KnowledgeBaseSolutions(id)", "GET KnowledgeBaseSolutions", "POST KnowledgeBaseSolutions", "PATCH KnowledgeBaseSolutions(id)", "DELETE KnowledgeBaseSolutions(id)"]
rows_oil: 0
---
# KnowledgeBaseSolutions
Repository of documented symptoms/causes/solutions technicians attach to service calls for faster resolution — empty in this database (fields from standard schema). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query KnowledgeBaseSolutions --top 5
./sapb1 query KnowledgeBaseSolutions --count
./sapb1 query KnowledgeBaseSolutions --select "SolutionNumber,Subject,Status,ItemCode" --top 10
# solutions documented for a specific item
./sapb1 query KnowledgeBaseSolutions --filter "ItemCode eq 'FG0001'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| SolutionNumber | Solution record number |
| Subject | Short solution title |
| Status | Publication status code |
| Owner | Authoring employee |
| ItemCode | Related item |
| Symptom | Observed problem description |
| Cause | Root-cause description |
| Solution | Fix/resolution text |
| CreationDate | Record creation date |
| UpdateDate | Last update date |

## Connections
- Domain: [[service-contracts]]
- [[ServiceCalls]] via SolutionNumber — tickets the solution was applied to
- [[ServiceCallSolutionStatus]] via Status — publication status code
- [[Items]] via ItemCode — item the solution concerns
- [[EmployeesInfo]] via Owner — authoring employee
