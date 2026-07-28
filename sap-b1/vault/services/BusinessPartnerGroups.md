---
entity: BusinessPartnerGroups
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 47
---
# BusinessPartnerGroups
Customer/vendor grouping catalog (47 groups) used to segment business partners for reporting and defaults. Live rows in JIVO_OIL_HANADB: 47.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BusinessPartnerGroups --top 5
./sapb1 query BusinessPartnerGroups --count
./sapb1 query BusinessPartnerGroups --select "Code,Name,Type" --top 10
# Customer groups only (bbpgt_CustomerGroup / bbpgt_VendorGroup):
./sapb1 query BusinessPartnerGroups --filter "Type eq 'bbpgt_CustomerGroup'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Group numeric code (key) |
| Name | Group display name |
| Type | Customer or vendor group |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via GroupCode
