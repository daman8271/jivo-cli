---
entity: ContractTemplates
domain: service-contracts
readable: true
methods: ["GET ContractTemplates(id)", "GET ContractTemplates", "POST ContractTemplates", "PATCH ContractTemplates(id)", "DELETE ContractTemplates(id)"]
rows_oil: 0
---
# ContractTemplates
Reusable blueprints defining coverage, duration and SLA terms from which customer service contracts are created — empty in JIVO_OIL_HANADB (fields listed from standard SAP B1 schema; live sample unavailable). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ContractTemplates --top 5
./sapb1 query ContractTemplates --count
./sapb1 query ContractTemplates --select "TemplateName,ContractType,Duration,Renewal" --top 10
# auto-renewing templates only
./sapb1 query ContractTemplates --filter "Renewal eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| TemplateName | Template identifier |
| Description | Template description |
| ContractType | Customer/item/serial coverage type |
| Renewal | Auto-renewal flag |
| Duration | Contract length value |
| DurationType | Length unit (months/years) |
| ResponseTime | SLA response time |
| ResponseUnit | Response time unit |
| ResolutionTime | SLA resolution time |
| ResolutionUnit | Resolution time unit |
| PartsCoverage | Parts covered flag |
| LaborCoverage | Labor covered flag |
| TravelCoverage | Travel covered flag |
| Remarks | Free-text notes |

## Connections
- Domain: [[service-contracts]]
- [[ServiceContracts]] via TemplateName — contracts instantiated from the template
