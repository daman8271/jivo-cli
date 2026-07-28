---
entity: ValueMappingCommunication
domain: system-other-2
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# ValueMappingCommunication
Defines the communication channels/partners that value mappings apply to in EDI exchanges; unused. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ValueMappingCommunication --top 5
./sapb1 query ValueMappingCommunication --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[ValueMapping]] via communication channel assignment (mapping ID)
