---
entity: ActivityRecipientLists
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# ActivityRecipientLists
Named recipient distribution lists used to notify multiple users about a CRM activity; empty here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ActivityRecipientLists --top 5
./sapb1 query ActivityRecipientLists --count
./sapb1 query ActivityRecipientLists --select "Code,Name" --top 10
# Look up a distribution list by name (if ever populated):
./sapb1 query ActivityRecipientLists --filter "contains(Name,'Sales')" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Code | List numeric code (key) |
| Name | Distribution list name |
| ActivityRecipientCollection | Member users collection |

## Connections
- Domain: [[business-partners-crm]]
- [[Activities]] via recipient lists attached to activity notifications
- [[Users]] via ActivityRecipientCollection member user codes
