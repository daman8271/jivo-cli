---
entity: PickLists
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, PUT]
rows_oil: 3598
---
# PickLists
Warehouse pick-and-pack lists (3.6k) that allocate and track picking of ordered items ahead of delivery. Live rows in JIVO_OIL_HANADB: 3598.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PickLists --top 5
./sapb1 query PickLists --count
./sapb1 query PickLists --select "Absoluteentry,Name,PickDate,Status" --top 10
# Pick lists released to the floor but not yet picked/closed:
./sapb1 query PickLists --filter "Status eq 'ps_Released'" --select "Absoluteentry,PickDate,OwnerName" --top 20
```

Also exposes a `GetReleasedAllocation` action (POST — out of scope under our READ-ONLY rule).

## Key fields
| Field | Meaning |
|---|---|
| Absoluteentry | Internal pick list key |
| Name | Picker/list name |
| OwnerCode | Owner employee code |
| OwnerName | Owner employee name |
| PickDate | Scheduled pick date |
| Status | Pick list status |
| Remarks | Free-text remarks |
| ObjectType | Base object type |
| PickListsLines | Lines being picked |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Orders]] via base document reference on PickListsLines
- [[DeliveryNotes]] via the deliveries created from picked lines
- [[Items]] via ItemNo on PickListsLines
- [[Warehouses]] via the picking warehouse on lines
- [[EmployeesInfo]] via OwnerCode
