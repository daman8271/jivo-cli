---
entity: Relationships
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# Relationships
Catalog of relationship types used to map connections between business partners and contacts in the relationship map; unused here. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Relationships --top 5
./sapb1 query Relationships --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[BusinessPartners]] via relationship-map entries (CardCode)
