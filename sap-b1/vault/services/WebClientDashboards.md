---
entity: WebClientDashboards
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# WebClientDashboards
Stores user-created analytical dashboards in the Web Client; none created. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientDashboards --top 5
./sapb1 query WebClientDashboards --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[WebClientLaunchpads]] via dashboard tile placement on launchpad groups
