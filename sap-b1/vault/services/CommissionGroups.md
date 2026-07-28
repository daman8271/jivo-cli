---
entity: CommissionGroups
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# CommissionGroups
Commission percentage groups assignable to BPs, items or salespeople for commission calculation. Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CommissionGroups --top 5
./sapb1 query CommissionGroups --count
./sapb1 query CommissionGroups --select "CommissionGroupCode,CommissionGroupName,CommissionPercentage" --top 10
# Groups that actually pay a commission:
./sapb1 query CommissionGroups --filter "CommissionPercentage gt 0" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| CommissionGroupCode | Group numeric code (key) |
| CommissionGroupName | Group display name |
| CommissionPercentage | Commission percent rate |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via CommissionGroupCode
- [[SalesPersons]] via CommissionGroup on the salesperson
- [[Items]] via CommissionGroup on the item master
