---
entity: Messages
domain: system-other-1
readable: true
methods: [GET, POST]
rows_oil: 149242
---
# Messages
Internal B1 messaging/alert inbox (system alerts and user messages with recipients and attachments). Live rows in JIVO_OIL_HANADB: 149,242 — a heavy alert stream (latest sampled messages are "Document generation approved" notices to internal user 35).

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Messages --top 5
./sapb1 query Messages --count
./sapb1 query Messages --select "Code,Subject,User,Priority" --orderby "Code desc" --top 10
# High-priority messages only (Priority enum verified live; values pr_Low/pr_Normal/pr_High):
./sapb1 query Messages --filter "Priority eq 'pr_High'" --select "Code,Subject,User" --top 10
```
At 149k rows, always narrow with `--select`/`--filter`/`--orderby "Code desc"` — never `--all`. The catalog also exposes a POST action `GetMessage` per message — out of scope under our read-only rule (plain GET by key covers it).

## Key fields
| Field | Meaning |
|---|---|
| Code | Message numeric key (ascending = newer) |
| Subject | Message subject line |
| Text | Message body text |
| User | Sender internal user code |
| Priority | pr_Low / pr_Normal / pr_High |
| Attachment | Attachment reference |
| RecipientCollection | Recipient users collection |
| MessageDataColumns | Structured alert data columns |

## Connections
- Domain: [[system-other-1]]
- [[Users]] via User and RecipientCollection.UserCode — sender and recipient internal users
- [[AlertManagements]] via alert rules — configured alerts generate these inbox messages (recon lists this relation as "Alerts"; the catalog service is AlertManagements)
