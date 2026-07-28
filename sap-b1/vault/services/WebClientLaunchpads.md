---
entity: WebClientLaunchpads
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 2
---
# WebClientLaunchpads
Per-user Web Client home-screen (launchpad) layout and theme settings — 2 users have customized launchpads. Live rows in JIVO_OIL_HANADB: 2.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientLaunchpads --top 5
./sapb1 query WebClientLaunchpads --count
./sapb1 query WebClientLaunchpads --select "Guid,UserId,ThemeId,DisplayQuickView" --top 10
./sapb1 query WebClientLaunchpads --filter "DisplayQuickView eq 'tYES'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| Guid | Launchpad unique identifier (key) |
| UserId | Owning SAP user |
| ThemeId | Selected UI theme |
| DisplayQuickView | Quick-view panel toggle |
| NotificationShowDays | Notification retention (days) |
| WebClientLaunchpadGroups | Tile groups on home screen (collection) |
## Connections
- Domain: [[system-other-2]]
- [[Users]] via UserId
- [[WebClientBookmarkTiles]] via tiles inside WebClientLaunchpadGroups (Guid)
