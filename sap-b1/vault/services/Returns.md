---
entity: Returns
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1976
---
# Returns
Goods-return documents reversing deliveries back into stock (~2k rows), typically followed by A/R credit memos. Live rows in JIVO_OIL_HANADB: 1976.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Returns --top 5
./sapb1 query Returns --count
./sapb1 query Returns --select "DocNum,DocDate,CardName,DocTotal" --top 10
# Returns posted this fiscal year (FY starts 1 April):
./sapb1 query Returns --filter "DocDate ge '2026-04-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Return internal key |
| DocNum | Return document number |
| DocDate | Posting date |
| CardCode | Customer code |
| CardName | Customer name |
| DocTotal | Returned goods value |
| DocCurrency | Document currency |
| DocumentStatus | Open/closed status |
| SalesPersonCode | Responsible sales employee |
| AddressForReturn | Pickup/return address |
| Comments | Free-text remarks |
| DocumentLines | Returned item lines |

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode
- [[Items]] via DocumentLines.ItemCode
- [[Warehouses]] via DocumentLines.WarehouseCode (stock returns here)
- [[DeliveryNotes]] via DocumentLines.BaseEntry (base delivery being reversed)
- [[CreditNotes]] via their DocumentLines.BaseEntry pointing back at the return
- [[SalesPersons]] via SalesPersonCode
