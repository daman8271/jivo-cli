---
entity: SalesTaxCodes
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 23
---
# SalesTaxCodes
The 23 combined tax codes (jurisdiction stacks) applied on document lines to compute GST/tax on sales and purchases. Live rows in JIVO_OIL_HANADB: 23.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesTaxCodes --top 5
./sapb1 query SalesTaxCodes --count
./sapb1 query SalesTaxCodes --select "Code,Name,Rate,ValidForAR" --top 10
# Active codes usable on A/R (sales) documents:
./sapb1 query SalesTaxCodes --filter "ValidForAR eq 'tYES' and Inactive eq 'tNO'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Tax code (key) |
| Name | Tax code name |
| Rate | Combined rate percentage |
| ValidForAR | Usable on sales docs |
| ValidForAP | Usable on purchase docs |
| Inactive | Inactive flag |
| IsItemLevel | Item-level tax flag |
| Freight | Applies to freight |
| SalesTaxCodes_Lines | Stacked authority lines |

## Connections
- Domain: [[sales-ar]]
- [[SalesTaxAuthorities]] via SalesTaxCodes_Lines.STACode (jurisdiction stack)
- [[Invoices]] via DocumentLines.TaxCode
- [[Orders]] via DocumentLines.TaxCode
