---
entity: Industries
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# Industries
Master list of industry classifications assignable to business partners for CRM segmentation and reporting. Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Industries --top 5
./sapb1 query Industries --count
./sapb1 query Industries --select "IndustryCode,IndustryName,IndustryDescription" --top 10
# look up one industry by name:
./sapb1 query Industries --filter "IndustryName eq 'Retail'" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| IndustryCode | Numeric industry key |
| IndustryName | Short industry name |
| IndustryDescription | Longer free-text description |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via Industry — partners carry an industry code for segmentation
