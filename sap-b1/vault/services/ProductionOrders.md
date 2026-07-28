---
entity: ProductionOrders
domain: production-mrp
readable: true
methods: ["GET ProductionOrders(id)", "GET ProductionOrders", "POST ProductionOrders", "PATCH ProductionOrders(id)", "POST ProductionOrders(id)/Cancel"]
rows_oil: 7683
---
# ProductionOrders
Manufacturing work orders that plan and track production of an item (BOM components, quantities, dates, status) in JIVO's oil plant. Live rows in JIVO_OIL_HANADB: 7683.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ProductionOrders --top 5
./sapb1 query ProductionOrders --count
./sapb1 query ProductionOrders --select "DocumentNumber,ItemNo,PlannedQuantity,ProductionOrderStatus" --top 10
# open (released) work orders only
./sapb1 query ProductionOrders --filter "ProductionOrderStatus eq 'boposReleased'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsoluteEntry | Internal document key |
| DocumentNumber | Work order number |
| ItemNo | Item being produced |
| ProductDescription | Produced item description |
| PlannedQuantity | Quantity planned to make |
| CompletedQuantity | Quantity actually completed |
| RejectedQuantity | Quantity rejected/scrapped |
| ProductionOrderStatus | Planned/released/closed status |
| ProductionOrderType | Standard, special, or disassembly |
| PostingDate | Order posting date |
| DueDate | Planned completion date |
| StartDate | Planned start date |
| Warehouse | Receiving warehouse code |
| Project | Linked project code |

## Connections
- Domain: [[production-mrp]]
- [[Items]] via ItemNo — the finished good being produced
- [[Warehouses]] via Warehouse — warehouse receiving the output
- [[Projects]] via Project — cost/project assignment
- [[BusinessPartners]] via CustomerCode — customer a make-to-order run is for
- [[Orders]] via origin document link — sales order that triggered the work order
