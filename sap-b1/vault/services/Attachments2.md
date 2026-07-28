---
entity: Attachments2
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 75526
---
# Attachments2
File-attachment registry linking uploaded files (paths, names, dates in the lines collection) to SAP documents and master records; heavily used here (75k rows). Live rows in JIVO_OIL_HANADB: 75526.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Attachments2 --top 5
./sapb1 query Attachments2 --count
./sapb1 query Attachments2 --select "AbsoluteEntry,Attachments2_Lines" --top 10
# Newest attachment records (keys are sequential):
./sapb1 query Attachments2 --filter "AbsoluteEntry gt 75000" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsoluteEntry | Attachment record key |
| Attachments2_Lines | File lines (path, name, date) |

## Connections
- Domain: [[administration-setup-3]]
- No related entities recorded in recon — documents and master records point here via their AttachmentEntry field.
