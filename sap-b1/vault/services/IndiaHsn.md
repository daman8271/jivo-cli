---
entity: IndiaHsn
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 517
---
# IndiaHsn
India GST HSN code master (chapter/heading/sub-heading) assigned to items for tax classification. Live rows in JIVO_OIL_HANADB: 517 codes.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query IndiaHsn --top 5
./sapb1 query IndiaHsn --count
./sapb1 query IndiaHsn --select "AbsEntry,ChapterID,Heading,SubHeading,Description" --top 10
# The olive-oil HSN codes (chapter 1509 family) — verified live, returns AbsEntry 21 & 24:
./sapb1 query IndiaHsn --filter "contains(Description,'olive')" --select "AbsEntry,SubHeading,Description" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | HSN record key |
| ChapterID | GST chapter number |
| Chapter | Chapter description |
| Heading | 4-digit heading |
| SubHeading | Sub-heading digits |
| Description | Goods description text |

## Connections
- Domain: [[system-other-1]]
- [[Items]] via ChapterID/HSN assignment — item master tax classification points at an HSN entry (AbsEntry)
