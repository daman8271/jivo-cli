---
entity: BarCodes
domain: inventory-warehouse-1
readable: true
methods: ["GET BarCodes", "GET BarCodes(id)", "POST BarCodes", "PATCH BarCodes(id)", "DELETE BarCodes(id)"]
rows_oil: 0
---
# BarCodes
Entity set of item barcodes mapping scannable codes to items and UoMs (empty in JIVO_OIL_HANADB, so fields inferred from SAP B1 standard schema). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BarCodes --top 5
./sapb1 query BarCodes --count
./sapb1 query BarCodes --select "AbsEntry,BarCode,ItemNo,UoMEntry" --top 10
# all barcodes registered for one item
./sapb1 query BarCodes --filter "ItemNo eq 'FG00001'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal barcode record key |
| BarCode | Scannable code value (EAN/UPC) |
| ItemNo | Item the code belongs to |
| UoMEntry | UoM the code applies to |
| FreeText | Free-form remarks |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] via ItemNo — the item each barcode identifies
- [[UnitOfMeasurements]] via UoMEntry — packaging unit the code is printed on
