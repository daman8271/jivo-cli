---
entity: PaymentBlocks
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# PaymentBlocks
Reason codes for blocking documents/partners from the payment wizard. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PaymentBlocks --top 5
./sapb1 query PaymentBlocks --count
./sapb1 query PaymentBlocks --select "AbsEntry,PaymentBlockDescription" --top 10
# find a block reason by keyword
./sapb1 query PaymentBlocks --filter "contains(PaymentBlockDescription,'hold')" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal key |
| PaymentBlockDescription | Block reason text |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] — partners carrying a payment-block code
- [[VendorPayments]] — outgoing payments excluded when a block applies
