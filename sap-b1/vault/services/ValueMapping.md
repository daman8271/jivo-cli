---
entity: ValueMapping
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# ValueMapping
EDI/interface value-mapping table translating internal codes to external partner codes for electronic communication; unused. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ValueMapping --top 5
./sapb1 query ValueMapping --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[ValueMappingCommunication]] via communication channel assignment (mapping ID)
