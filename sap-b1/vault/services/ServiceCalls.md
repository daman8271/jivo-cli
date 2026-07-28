---
entity: ServiceCalls
domain: service-contracts
readable: true
methods: ["GET ServiceCalls(id)", "GET ServiceCalls", "POST ServiceCalls", "PATCH ServiceCalls(id)", "DELETE ServiceCalls(id)", "POST ServiceCalls(id)/Close"]
rows_oil: 0
---
# ServiceCalls
Customer support tickets (complaints/repair requests) tracked from creation to closure with SLA, technician and solution links — zero rows, the service module is unused at JIVO. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceCalls --top 5
./sapb1 query ServiceCalls --count
./sapb1 query ServiceCalls --select "ServiceCallID,Subject,CustomerCode,Status" --top 10
# open calls only (Status -3 = Open in standard B1)
./sapb1 query ServiceCalls --filter "Status eq -3" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| ServiceCallID | Ticket number |
| Subject | Short problem title |
| CustomerCode | Customer BP code |
| CustomerName | Customer display name |
| ItemCode | Item under service |
| SerialNumber | Serviced unit serial |
| ContractID | Covering service contract |
| Status | Lifecycle status code |
| Priority | Urgency level |
| CallType | Call category code |
| ProblemType | Problem classification code |
| Origin | How call was reported |
| CreationDate | Ticket creation date |
| AssigneeCode | Assigned technician/employee |

## Connections
- Domain: [[service-contracts]]
- [[BusinessPartners]] via CustomerCode — customer raising the call
- [[Items]] via ItemCode — item being serviced
- [[ServiceContracts]] via ContractID — covering warranty/service agreement
- [[ServiceCallStatus]] via Status — lifecycle status code
- [[ServiceCallTypes]] via CallType — call category code
- [[ServiceCallProblemTypes]] via ProblemType — problem classification code
- [[ServiceCallOrigins]] via Origin — reporting-channel code
- [[KnowledgeBaseSolutions]] via SolutionNumber — solutions attached to the call
- [[EmployeesInfo]] via AssigneeCode — assigned technician
