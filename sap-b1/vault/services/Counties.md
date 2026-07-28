---
entity: Counties
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# Counties
Lookup of counties/districts within states used in addresses and tax jurisdiction determination (empty in JIVO). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Counties --top 5
./sapb1 query Counties --count
./sapb1 query Counties --select "AbsId,Code,Name,State" --top 10
# counties within India, if any were defined
./sapb1 query Counties --filter "Country eq 'IN'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsId | Internal record key |
| Code | County code |
| Name | County name |
| State | Parent state code |
| Country | Parent country code |
| TaxZone | Tax jurisdiction zone |
## Connections
- Domain: [[system-other-1]]
- [[Countries]] via Country — parent country of the county
- [[States]] via State — parent state of the county
- [[BusinessPlaces]] via County — branch addresses referencing a county
