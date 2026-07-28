---
entity: PartnersSetups
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# PartnersSetups
Setup list of sales-opportunity partners (external firms cooperating on deals) referenced from opportunity records; empty in this database. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PartnersSetups --top 5
./sapb1 query PartnersSetups --count
./sapb1 query PartnersSetups --select "PartnerCode,PartnerName" --top 10
# find a partner firm by name fragment:
./sapb1 query PartnersSetups --filter "contains(PartnerName,'Distrib')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| PartnerCode | Partner firm's key |
| PartnerName | Partner firm's name |

## Connections
- Domain: [[business-partners-crm]]
- [[SalesOpportunities]] via PartnerCode — opportunity partner lines reference these firms
