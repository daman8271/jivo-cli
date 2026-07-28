---
entity: ShortLinkMappings
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# ShortLinkMappings
GUID-keyed short-link mappings used by the Web Client to shorten/share deep links; empty. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ShortLinkMappings --top 5
./sapb1 query ShortLinkMappings --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled (GUID-keyed) |
## Connections
- Domain: [[system-other-2]]
