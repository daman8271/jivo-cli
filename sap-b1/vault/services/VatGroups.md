---
entity: VatGroups
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# VatGroups
VAT/tax group definitions with rates and posting accounts for input/output tax; reports 0 via this endpoint (India GST setup lives in tax-code tables). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query VatGroups --top 5
./sapb1 query VatGroups --count
```
(Reports 0 rows via this endpoint in JIVO_OIL — the India GST configuration is held in the localized tax-code tables instead, e.g. [[TaxCodeDeterminationsTCD]].)

## Key fields
_No rows exposed via this endpoint in JIVO_OIL_HANADB — field-level recon not captured._

## Connections
- Domain: [[financials-accounting-2]]
- [[ChartOfAccounts]] via the input/output tax posting accounts on group lines
- [[SalesTaxCodes]] via tax codes composed from these groups
