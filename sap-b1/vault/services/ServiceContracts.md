---
entity: ServiceContracts
domain: service-contracts
readable: true
methods: ["GET ServiceContracts(id)", "GET ServiceContracts", "POST ServiceContracts", "PATCH ServiceContracts(id)", "DELETE ServiceContracts(id)", "POST ServiceContracts(id)/Cancel", "POST ServiceContracts(id)/Close"]
rows_oil: 0
---
# ServiceContracts
Customer service/warranty agreements defining coverage periods and SLA terms against which service calls are logged — empty, not used in this oil-trading database. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceContracts --top 5
./sapb1 query ServiceContracts --count
./sapb1 query ServiceContracts --select "ContractID,CustomerCode,StartDate,EndDate" --top 10
# contracts still in force today
./sapb1 query ServiceContracts --filter "EndDate ge '2026-07-23'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| ContractID | Contract number |
| CustomerCode | Customer BP code |
| CustomerName | Customer display name |
| ContractType | Customer/item/serial coverage type |
| TemplateName | Source contract template |
| StartDate | Coverage start date |
| EndDate | Coverage end date |
| Status | Approved/frozen/terminated |
| Renewal | Auto-renewal flag |
| ResponseTime | SLA response time |
| ResolutionTime | SLA resolution time |
| PartsCoverage | Parts covered flag |
| LaborCoverage | Labor covered flag |
| Remarks | Free-text notes |

## Connections
- Domain: [[service-contracts]]
- [[BusinessPartners]] via CustomerCode — covered customer
- [[ContractTemplates]] via TemplateName — blueprint the contract was created from
- [[ServiceCalls]] via ContractID — tickets logged against the contract
- [[Items]] via covered-item lines — items/serials under coverage
