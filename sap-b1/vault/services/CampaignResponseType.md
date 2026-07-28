---
entity: CampaignResponseType
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 2
---
# CampaignResponseType
Lookup of possible response outcomes recorded against marketing campaign targets. Live rows in JIVO_OIL_HANADB: 2.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CampaignResponseType --top 5
./sapb1 query CampaignResponseType --count
./sapb1 query CampaignResponseType --select "ResponseType,ResponseTypeDescription,IsActive" --top 10
# Only response types still active for selection:
./sapb1 query CampaignResponseType --filter "IsActive eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| ResponseType | Response type code (key) |
| ResponseTypeDescription | Response outcome description |
| IsActive | Active/selectable flag |

## Connections
- Domain: [[business-partners-crm]]
- [[Campaigns]] via ResponseType recorded on campaign target rows
