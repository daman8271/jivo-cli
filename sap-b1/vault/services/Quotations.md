---
entity: Quotations
domain: sales-ar
readable: true
methods: [GET, POST, PATCH]
rows_oil: 1690
---
# Quotations
Sales quotations — price offers to customers that can be copied to sales orders; 1.7k issued. Live rows in JIVO_OIL_HANADB: 1690.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Quotations --top 5
./sapb1 query Quotations --count
./sapb1 query Quotations --select "DocNum,DocDate,CardName,DocTotal" --top 10
# Open quotations = offers still on the table, not yet won or closed:
./sapb1 query Quotations --filter "DocumentStatus eq 'bost_Open'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Quotation internal key |
| DocNum | Quotation document number |
| DocDate | Posting date |
| DocDueDate | Offer validity date |
| CardCode | Customer code |
| CardName | Customer name |
| DocTotal | Quoted total amount |
| DocCurrency | Document currency |
| DocumentStatus | Open/closed status |
| SalesPersonCode | Responsible sales employee |
| Comments | Free-text remarks |
| DocumentLines | Quoted item lines |

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode
- [[Items]] via DocumentLines.ItemCode
- [[SalesPersons]] via SalesPersonCode
- [[Orders]] via their DocumentLines.BaseEntry pointing back at the quotation (copy-to)
- [[Currencies]] via DocCurrency
