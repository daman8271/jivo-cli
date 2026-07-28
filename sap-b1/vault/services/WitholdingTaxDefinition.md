---
entity: WitholdingTaxDefinition
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# WitholdingTaxDefinition
Withholding-tax definition master (rate tiers/effective settings) backing withholding tax codes (empty via this endpoint). Note SAP's own "Witholding" spelling in the service name. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WitholdingTaxDefinition --top 5
./sapb1 query WitholdingTaxDefinition --count
```
(Empty via this endpoint in JIVO_OIL — `--count` returns 0; the live TDS/TCS setup is readable through [[WithholdingTaxCodes]].)

## Key fields
_No rows exposed via this endpoint in JIVO_OIL_HANADB — field-level recon not captured._

## Connections
- Domain: [[financials-accounting-2]]
- [[WithholdingTaxCodes]] via the definition backing each code's rate tiers
