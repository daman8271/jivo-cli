---
entity: SalesTaxAuthoritiesTypes
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 18
---
# SalesTaxAuthoritiesTypes
Categories of tax authorities (18 types, e.g. CGST/SGST/IGST levels) that group authorities for tax-code assembly. Live rows in JIVO_OIL_HANADB: 18.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesTaxAuthoritiesTypes --top 5
./sapb1 query SalesTaxAuthoritiesTypes --count
./sapb1 query SalesTaxAuthoritiesTypes --select "Numerator,Name,VAT" --top 10
# Only the types flagged as VAT-style (GST) authorities:
./sapb1 query SalesTaxAuthoritiesTypes --filter "VAT eq 'tYES'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| Numerator | Type number (key) |
| Name | Type name |
| VAT | VAT/GST-style flag |
| NfTaxId | Nota-fiscal tax ID |
| TaxCreditControl | Tax credit control flag |
| TaxParamSetId | Tax parameter set link |

## Connections
- Domain: [[sales-ar]]
- [[SalesTaxAuthorities]] via Type (authorities grouped under this type)
