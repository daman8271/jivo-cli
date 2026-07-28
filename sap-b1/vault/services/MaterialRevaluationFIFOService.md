---
entity: MaterialRevaluationFIFOService
domain: administration-setup-1
readable: false
methods: [GetMaterialRevaluationFIFO]
rows_oil: null
---
# MaterialRevaluationFIFOService
Retrieves FIFO-layer material revaluation data for adjusting inventory cost of FIFO-managed items.

## Operations
- GetMaterialRevaluationFIFO

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops MaterialRevaluationFIFOService`.

## Connections
- Domain: [[administration-setup-1]]
- [[Items]] via ItemCode — the FIFO-managed item whose cost layers are revalued
- [[Warehouses]] via WarehouseCode — the warehouse holding the FIFO layers
- [[MaterialRevaluation]] via revaluation document lines — the posting document this data feeds
