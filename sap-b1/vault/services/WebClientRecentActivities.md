---
entity: WebClientRecentActivities
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 97
---
# WebClientRecentActivities
Per-user usage log of recently opened apps/pages in the SAP B1 Web Client, powering its "recent activities" home-screen tiles. Live rows in JIVO_OIL_HANADB: 97.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientRecentActivities --top 5
./sapb1 query WebClientRecentActivities --count
./sapb1 query WebClientRecentActivities --select "UserId,Title,AppType,Timestamp" --top 10
# one user's recent Web Client activity:
./sapb1 query WebClientRecentActivities --filter "UserId eq 1" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Guid | Row's unique key |
| UserId | SAP user who opened it |
| AppId | Opened app's identifier |
| AppType | App category/type |
| Title | Page/app display title |
| Url | Web Client page URL |
| RecentDay | Day of last access |
| Timestamp | Exact last-access time |
| Count | Number of opens |
| UsageArray | Per-day usage histogram |

## Connections
- Domain: [[business-partners-crm]]
- [[Users]] via UserId — the SAP user whose activity is logged
