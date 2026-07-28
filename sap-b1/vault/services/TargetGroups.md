---
entity: TargetGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# TargetGroups
CRM marketing-campaign target group definitions for segmenting business partners; unused here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TargetGroups --top 5
./sapb1 query TargetGroups --count
./sapb1 query TargetGroups --select "TargetGroupCode,TargetGroupName,Type" --top 10
# Find a target group by (partial) name (if ever populated):
./sapb1 query TargetGroups --filter "contains(TargetGroupName,'Retail')" --top 10
```
Set is empty here — confirm live field names with `./sapb1 fields TargetGroups` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| TargetGroupCode | Target group code (key) |
| TargetGroupName | Target group name |
| Type | Group type (BP/lead) |

(No key fields captured in recon — the set is empty; fields above are the standard Service Layer schema.)

## Connections
- Domain: [[administration-setup-3]]
- [[Campaigns]] via target group code (consumed by the Campaign Generation Wizard)
- [[BusinessPartners]] via segmentation into target groups
