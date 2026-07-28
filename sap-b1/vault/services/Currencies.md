---
entity: Currencies
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 6
---
# Currencies
Currency master (INR plus 5 others) with rounding rules and payment tolerance settings used across all documents. Live rows in JIVO_OIL_HANADB: 6.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Currencies --top 5
./sapb1 query Currencies --count
./sapb1 query Currencies --select "Code,Name,Decimals,Rounding" --top 10
# Inspect the local currency setup:
./sapb1 query Currencies --filter "Code eq 'INR'"
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Currency code (key) |
| Name | Currency name |
| DocumentsCode | Symbol printed on documents |
| InternationalDescription | ISO / international name |
| Decimals | Decimal places used |
| Rounding | Rounding rule |
| RoundingInPayment | Payment rounding rule |
| MaxIncomingAmtDiff | Incoming payment tolerance |
| MaxOutgoingAmtDiff | Outgoing payment tolerance |

## Connections
- Domain: [[financials-accounting-1]]
- [[ChartOfAccounts]] via AcctCurrency = Code — accounts can be pinned to one currency
- [[BusinessPartners]] via Currency = Code — each BP carries a default transaction currency
