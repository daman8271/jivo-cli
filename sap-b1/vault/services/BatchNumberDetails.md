---
entity: BatchNumberDetails
domain: inventory-warehouse-1
readable: true
methods: ["GET BatchNumberDetails", "GET BatchNumberDetails(id)", "PATCH BatchNumberDetails(id)"]
rows_oil: 17257
---
# BatchNumberDetails
Master records of batch numbers per item with manufacturing/expiry dates and status — the traceability backbone for batch-managed oil stock (17,257 batches live). Live rows in JIVO_OIL_HANADB: 17257.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BatchNumberDetails --top 5
./sapb1 query BatchNumberDetails --count
./sapb1 query BatchNumberDetails --select "ItemCode,Batch,ManufacturingDate,ExpirationDate" --top 10
# shelf-life watch: batches expiring in the next quarter
./sapb1 query BatchNumberDetails --filter "ExpirationDate lt '2026-10-01' and Status eq 'bdsStatus_Released'" --select "ItemCode,Batch,ExpirationDate" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal batch record key |
| ItemCode | Batch-managed item code |
| ItemDescription | Item description snapshot |
| Batch | Batch number string |
| AdmissionDate | Date batch entered stock |
| ManufacturingDate | Production date |
| ExpirationDate | Shelf-life expiry date |
| Status | Released / locked status |
| SystemNumber | Internal system serial |
| BatchAttribute1 | Free batch attribute 1 |
| BatchAttribute2 | Free batch attribute 2 |
| Details | Free-form notes |
| U_BaseEntry | UDF: source document entry |
| U_CardCode | UDF: linked partner code |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] via ItemCode — the batch-managed item each batch belongs to
- [[BusinessPartners]] via U_CardCode — partner tagged on the batch (custom field)
