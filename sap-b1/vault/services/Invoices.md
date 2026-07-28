---
entity: Invoices
domain: sales-ar
readable: true
methods: [GET, POST, PATCH]
rows_oil: 30306
---
# Invoices
A/R invoices — the core customer billing documents (30.3k rows); end of the Orders→DeliveryNotes→Invoices sales chain and the primary revenue record. Live rows in JIVO_OIL_HANADB: 30306.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Invoices --top 5
./sapb1 query Invoices --count
./sapb1 query Invoices --select "DocNum,DocDate,CardName,DocTotal" --top 10
# Open (still unpaid/uncredited) A/R invoices = outstanding receivables:
./sapb1 query Invoices --filter "DocumentStatus eq 'bost_Open'" --top 10
```
The CLI also has a dedicated shortcut: `./sapb1 invoices --top 10`.

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Invoice internal key |
| DocNum | Invoice document number |
| DocDate | Posting date |
| DocDueDate | Payment due date |
| CardCode | Customer code |
| CardName | Customer name |
| DocTotal | Invoice total (incl. tax) |
| VatSum | Total tax amount |
| DocCurrency | Document currency |
| DocumentStatus | Open/closed status |
| SalesPersonCode | Responsible sales employee |
| NumAtCard | Customer PO reference |
| PaymentGroupCode | Payment terms code |
| DocumentLines | Item lines collection |

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode
- [[Items]] via DocumentLines.ItemCode
- [[Warehouses]] via DocumentLines.WarehouseCode
- [[SalesPersons]] via SalesPersonCode
- [[DeliveryNotes]] via DocumentLines.BaseEntry (base delivery)
- [[Orders]] via DocumentLines.BaseEntry (base order)
- [[Currencies]] via DocCurrency
- [[Projects]] via DocumentLines.ProjectCode
- [[ChartOfAccounts]] via ControlAccount / line account codes
