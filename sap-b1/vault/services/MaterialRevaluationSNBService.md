---
entity: MaterialRevaluationSNBService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# MaterialRevaluationSNBService
Lists material revaluation data for serial- and batch-managed items so inventory value adjustments can be reviewed per serial/batch.

## Operations
- MaterialRevaluationSNBService_GetList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops MaterialRevaluationSNBService`.

## Connections
- Domain: [[administration-setup-2]]
- [[Items]] via ItemCode — the serial/batch-managed items being revalued
- [[SerialNumberDetails]] via ItemCode + serial number — per-serial valuation detail
- [[BatchNumberDetails]] via ItemCode + batch number — per-batch valuation detail
- [[MaterialRevaluation]] via revaluation document entries — the underlying revaluation documents
