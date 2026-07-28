---
entity: ReturnRequest
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 32
---
# ReturnRequest
Customer return-request documents (RMA-style pre-approval before a Return is posted); lightly used (32 rows). Live rows in JIVO_OIL_HANADB: 32.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ReturnRequest --top 5
./sapb1 query ReturnRequest --count
./sapb1 query ReturnRequest --select "DocNum,DocDate,CardName,DocTotal" --top 10
# Open return requests = RMAs approved but goods not yet received back:
./sapb1 query ReturnRequest --filter "DocumentStatus eq 'bost_Open'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Request internal key |
| DocNum | Request document number |
| DocDate | Posting date |
| CardCode | Customer code |
| CardName | Customer name |
| DocTotal | Requested return value |
| DocCurrency | Document currency |
| DocumentStatus | Open/closed status |
| SalesPersonCode | Responsible sales employee |
| AddressForReturn | Pickup/return address |
| Comments | Free-text remarks |
| DocumentLines | Items to be returned |

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode
- [[Items]] via DocumentLines.ItemCode
- [[Warehouses]] via DocumentLines.WarehouseCode
- [[Returns]] via their DocumentLines.BaseEntry pointing back at the request
- [[SalesPersons]] via SalesPersonCode
