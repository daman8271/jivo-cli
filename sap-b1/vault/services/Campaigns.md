---
entity: Campaigns
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# Campaigns
Marketing campaign records targeting groups of business partners; unused (0 rows) in this company. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Campaigns --top 5
./sapb1 query Campaigns --count
./sapb1 query Campaigns --select "CampaignNumber,CampaignName,Status,StartDate" --top 10
# Campaigns started this year (if ever populated):
./sapb1 query Campaigns --filter "StartDate ge '2026-01-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| CampaignNumber | Campaign number (key) |
| CampaignName | Campaign display name |
| CampaignType | Campaign type/channel |
| TargetGroup | Targeted BP group |
| StartDate | Campaign start date |
| EndDate | Campaign end date |
| Status | Campaign lifecycle status |
| Owner | Owning salesperson/user |
| Remarks | Free-text remarks |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via campaign target rows referencing CardCode
- [[CampaignResponseType]] via ResponseType on target outcomes
- [[SalesPersons]] via Owner
