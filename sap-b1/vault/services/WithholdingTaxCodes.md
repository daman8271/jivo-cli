---
entity: WithholdingTaxCodes
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 22
---
# WithholdingTaxCodes
India TDS/TCS withholding-tax codes (22 active) with rates, sections, and the AP/AR G/L accounts they post to. Live rows in JIVO_OIL_HANADB: 22.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WithholdingTaxCodes --top 5
./sapb1 query WithholdingTaxCodes --count
./sapb1 query WithholdingTaxCodes --select "OfficialCode,Rate,Section,Inactive" --top 10
```
Useful filter — only the codes still in use (skip retired TDS sections):
```bash
./sapb1 query WithholdingTaxCodes --filter "Inactive eq 'tNO'" --top 25
```

## Key fields
| Field | Meaning |
|---|---|
| OfficialCode | Official statutory code |
| Rate | Withholding percentage rate |
| Category | Invoice/payment category |
| Account | Withholding posting account |
| BaseType | Base amount type |
| BaseAmount | Base percentage applied |
| Section | India IT Act section (194C, …) |
| Location | Business location scope |
| Currency | Threshold currency |
| EffectiveFrom | Rate effective-from date |
| Inactive | Retired-code flag |
| APTDSAccount | AP-side TDS G/L account |
| ARTDSAccount | AR-side TDS G/L account |
| ReturnType | TDS return form type |

## Connections
- Domain: [[financials-accounting-2]]
- [[ChartOfAccounts]] via Account / APTDSAccount / ARTDSAccount posting accounts
- [[Currencies]] via Currency on thresholds
- [[WTaxTypeCodes]] via the withholding type code classifying each code
