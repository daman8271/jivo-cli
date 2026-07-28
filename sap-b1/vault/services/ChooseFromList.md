---
entity: ChooseFromList
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 26
---
# ChooseFromList
UI configuration for the B1 client's Choose-From-List dialogs — which columns show per object lookup. Live rows in JIVO_OIL_HANADB: 26.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ChooseFromList --top 5
./sapb1 query ChooseFromList --count
./sapb1 query ChooseFromList --select "ObjectName,ChooseFromList_Lines" --top 10
# CFL setup for a specific object lookup:
./sapb1 query ChooseFromList --filter "contains(ObjectName,'Item')" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| ObjectName | Object the dialog looks up |
| ChooseFromList_Lines | Column visibility/order lines |

## Connections
- Domain: [[administration-setup-3]]
- No related entities recorded in recon — pure B1-client UI configuration per lookup object.
