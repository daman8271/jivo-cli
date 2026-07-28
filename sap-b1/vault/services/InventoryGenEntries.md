---
entity: InventoryGenEntries
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH]
rows_oil: 7892
---
# InventoryGenEntries
Goods Receipt documents that increase stock without a purchase order — e.g. production output or manual stock additions; heavily used (7.9k docs). Live rows in JIVO_OIL_HANADB: 7892.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query InventoryGenEntries --top 5
./sapb1 query InventoryGenEntries --count
./sapb1 query InventoryGenEntries --select "DocEntry,DocNum,DocDate,JournalMemo" --top 10
# Goods receipts posted this month:
./sapb1 query InventoryGenEntries --filter "DocDate ge '2026-07-01'" --select "DocNum,DocDate,JournalMemo" --top 20
```

Also exposes `Close`, `Cancel`, `Reopen`, `CreateCancellationDocument` document actions (write — out of scope under our READ-ONLY rule).

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| DocDate | Posting date |
| DocDueDate | Document due date |
| CardCode | Business partner code |
| CardName | Business partner name |
| DocCurrency | Document currency |
| Comments | Free-text remarks |
| TaxDate | Tax/document date |
| Series | Numbering series |
| DocumentLines | Item lines received |
| JournalMemo | Journal entry memo |
| Reference2 | Secondary reference field |
| BPL_IDAssignedToInvoice | Branch/business place ID |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] via ItemCode on DocumentLines
- [[Warehouses]] via WarehouseCode on DocumentLines
- [[BusinessPartners]] via CardCode
- [[ChartOfAccounts]] via AccountCode on DocumentLines
- [[JournalEntries]] via the journal posting created on add
