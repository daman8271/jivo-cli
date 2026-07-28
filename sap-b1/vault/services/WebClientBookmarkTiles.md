---
entity: WebClientBookmarkTiles
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 10
---
# WebClientBookmarkTiles
User-saved bookmark tiles on the SAP B1 Web Client home screen linking to views/URLs — 10 tiles saved. Live rows in JIVO_OIL_HANADB: 10.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientBookmarkTiles --top 5
./sapb1 query WebClientBookmarkTiles --count
./sapb1 query WebClientBookmarkTiles --select "Guid,Title,SubTitle,Endpoint" --top 10
./sapb1 query WebClientBookmarkTiles --filter "contains(Title,'Order')" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| Guid | Tile unique identifier (key) |
| Title | Tile title text |
| SubTitle | Tile subtitle text |
| Endpoint | Target entity/endpoint the tile opens |
| BindType | How the tile binds (list/object/URL) |
| UrlTarget | External URL target |
| Info | Extra tile info text |
## Connections
- Domain: [[system-other-2]]
- [[WebClientLaunchpads]] via launchpad group tile assignment (Guid)
