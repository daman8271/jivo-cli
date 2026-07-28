---
entity: PaymentReasonCodes
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# PaymentReasonCodes
Localization reason codes attached to payments for bank-file/reporting purposes. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PaymentReasonCodes --top 5
./sapb1 query PaymentReasonCodes --count
./sapb1 query PaymentReasonCodes --select "AbsEntry,ReasonCode,Description" --top 10
# look up a specific reason code
./sapb1 query PaymentReasonCodes --filter "ReasonCode eq '001'" --top 5
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal key |
| ReasonCode | Reason code value |
| Description | Reason description |
## Connections
- Domain: [[banking-payments]]
- [[IncomingPayments]] — receipts tagged with a reason code
- [[VendorPayments]] — outgoing payments tagged with a reason code
