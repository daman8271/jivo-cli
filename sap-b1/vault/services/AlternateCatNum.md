---
entity: AlternateCatNum
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# AlternateCatNum
Maps a business partner's own catalog numbers to internal item codes so documents can use the partner's part numbers (empty in JIVO). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AlternateCatNum --top 5
./sapb1 query AlternateCatNum --count
./sapb1 query AlternateCatNum --select "ItemCode,CardCode,Substitute" --top 10
# catalog numbers defined for one partner
./sapb1 query AlternateCatNum --filter "CardCode eq 'C00001'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| ItemCode | Internal item code |
| CardCode | Business partner key |
| Substitute | Partner's catalog number |
| DisplayOrder | Sort position |
| Remark | Free-text note |
## Connections
- Domain: [[system-other-1]]
- [[Items]] via ItemCode — the internal item being aliased
- [[BusinessPartners]] via CardCode — partner owning the catalog number
