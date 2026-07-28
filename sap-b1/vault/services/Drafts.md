---
entity: Drafts
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 47115
---
# Drafts
Holds unfinished/pending marketing documents of any type (orders, invoices, etc.) saved as drafts before posting; 47k drafts in JIVO_OIL suggests heavy draft-approval workflow. Live rows in JIVO_OIL_HANADB: 47115.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Drafts --top 5
./sapb1 query Drafts --count
./sapb1 query Drafts --select "DocEntry,DocObjectCode,CardName,DocTotal" --top 10
# Open draft A/R invoices still waiting to be posted:
./sapb1 query Drafts --filter "DocObjectCode eq 'oInvoices' and DocumentStatus eq 'bost_Open'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Draft internal key |
| DocNum | Draft document number |
| DocObjectCode | Target document type (oOrders, oInvoices…) |
| DocDate | Document posting date |
| DocDueDate | Delivery/payment due date |
| CardCode | Business partner code |
| CardName | Business partner name |
| DocTotal | Document total amount |
| DocCurrency | Document currency |
| DocumentStatus | Open/closed draft status |
| SalesPersonCode | Responsible sales employee |
| Comments | Free-text remarks |
| CreationDate | When draft was created |
| DocumentLines | Item lines collection |

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode
- [[Items]] via DocumentLines.ItemCode
- [[Warehouses]] via DocumentLines.WarehouseCode
- [[SalesPersons]] via SalesPersonCode
- [[Currencies]] via DocCurrency
- [[Projects]] via DocumentLines.ProjectCode
