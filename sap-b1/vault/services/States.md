---
entity: States
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 98
---
# States
Master list of states/provinces per country including Indian GST state codes and union-territory flags, used in BP and document addresses — 98 rows. Live rows in JIVO_OIL_HANADB: 98.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query States --top 5
./sapb1 query States --count
./sapb1 query States --select "Code,Name,Country,GSTCode" --top 10
./sapb1 query States --filter "Country eq 'IN'" --top 40
```
## Key fields
| Field | Meaning |
|---|---|
| Code | State code (key with Country) |
| Name | State/province name |
| Country | Owning country code |
| GSTCode | Indian GST state code |
| IsUnionTerritory | Union territory flag |
## Connections
- Domain: [[system-other-2]]
- [[Countries]] via Country
- [[BusinessPartners]] via BPAddresses.State
