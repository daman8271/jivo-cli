---
entity: TransportationDocument
domain: system-other-2
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# TransportationDocument
Brazil-localization transportation documents (CT-e freight docs) linking freight to sales/delivery documents; unused here. Live rows in JIVO_OIL_HANADB: 0.

Lifecycle action exposed (POST — out of scope under our READ-ONLY rule): CancelTransportationDocument.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TransportationDocument --top 5
./sapb1 query TransportationDocument --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[DeliveryNotes]] via linked freight document lines (DocEntry)
- [[Invoices]] via linked freight document lines (DocEntry)
