---
entity: SelfCreditMemos
domain: system-other-2
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# SelfCreditMemos
Self-invoicing credit memo documents (reverse-charge/self-billing scenarios) with full document lifecycle actions; none issued in this database. Live rows in JIVO_OIL_HANADB: 0.

Document lifecycle actions exposed (all POST — out of scope under our READ-ONLY rule): Close, Cancel, Reopen, CreateCancellationDocument.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SelfCreditMemos --top 5
./sapb1 query SelfCreditMemos --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[BusinessPartners]] via CardCode
- [[CreditNotes]] via base/target document links (BaseEntry/DocEntry)
- [[Invoices]] via base document references (BaseEntry)
