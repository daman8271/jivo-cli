---
entity: SalesTaxAuthorities
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 40
---
# SalesTaxAuthorities
Tax-authority definitions (40 rows, GST jurisdictions/components) holding rates and posting accounts that combine into tax codes. Live rows in JIVO_OIL_HANADB: 40.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesTaxAuthorities --top 5
./sapb1 query SalesTaxAuthorities --count
./sapb1 query SalesTaxAuthorities --select "Code,Name,Type,Rate" --top 10
# Only the authorities that actually levy tax (non-zero rate):
./sapb1 query SalesTaxAuthorities --filter "Rate gt 0" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Authority code (key) |
| Name | Authority name |
| Type | Authority type link |
| Rate | Tax rate percentage |
| AOrRTaxAccount | A/R tax posting account |
| AOrPTaxAccount | A/P tax posting account |
| DeferredTaxAccount | Deferred tax account |
| NonDeductiblePrecent | Non-deductible percentage |
| MinTaxableAmount | Minimum taxable amount |
| MaxTaxableAmount | Maximum taxable amount |
| InclInPrice | Tax included in price |
| Exempt | Exemption flag |

## Connections
- Domain: [[sales-ar]]
- [[SalesTaxAuthoritiesTypes]] via Type
- [[SalesTaxCodes]] via SalesTaxCodes_Lines (authority stacked into codes)
- [[ChartOfAccounts]] via AOrRTaxAccount / AOrPTaxAccount / DeferredTaxAccount
