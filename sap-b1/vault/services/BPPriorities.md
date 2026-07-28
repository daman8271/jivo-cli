---
entity: BPPriorities
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# BPPriorities
Defines priority levels that can be assigned to business partners for segmentation/service ranking (empty in JIVO). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BPPriorities --top 5
./sapb1 query BPPriorities --count
./sapb1 query BPPriorities --select "PriorityCode,PriorityDescription" --top 10
# look up one priority level by key
./sapb1 query BPPriorities --filter "PriorityCode eq 1" --top 5
```
## Key fields
| Field | Meaning |
|---|---|
| PriorityCode | Priority level key |
| PriorityDescription | Priority level name |
## Connections
- Domain: [[system-other-1]]
- [[BusinessPartners]] via Priority → PriorityCode — priority assigned to a partner
