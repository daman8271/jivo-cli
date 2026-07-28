---
entity: RouteStagesService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# RouteStagesService
Lists production routing stages used to sequence operations in production orders.

## Operations
- RouteStagesService_GetList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops RouteStagesService`.

## Connections
- Domain: [[administration-setup-2]]
- [[Resources]] via resource code — stages sequence resource operations
- [[ProductionOrders]] via routing stage ID — production order lines reference route stages
