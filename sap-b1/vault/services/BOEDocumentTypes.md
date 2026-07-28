---
entity: BOEDocumentTypes
domain: banking-payments
readable: true
methods: ["GET BOEDocumentTypes", "GET BOEDocumentTypes(id)", "POST BOEDocumentTypes", "PATCH BOEDocumentTypes(id)", "DELETE BOEDocumentTypes(id)"]
rows_oil: 0
---
# BOEDocumentTypes
Setup table of bill-of-exchange document type codes. Empty in JIVO_OIL_HANADB — BOE unused; key fields inferred from schema. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BOEDocumentTypes --top 5
./sapb1 query BOEDocumentTypes --count
./sapb1 query BOEDocumentTypes --select "AbsoluteEntry,Code,Description" --top 10
# Look up one document type by code:
./sapb1 query BOEDocumentTypes --filter "Code eq 'BOE1'"
```
## Key fields
| Field | Meaning |
|---|---|
| AbsoluteEntry | Internal numeric key |
| Code | Document type code |
| Description | Type description |
## Connections
- Domain: [[banking-payments]]
- [[BillOfExchangeTransactions]] via document type — BOE documents classified by this type
