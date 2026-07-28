---
entity: IndiaHsnService
domain: administration-setup-1
readable: false
methods: [GetList]
rows_oil: null
---
# IndiaHsnService
Lists India HSN (Harmonized System of Nomenclature) codes used for GST classification of items — directly relevant to JIVO's Indian GST setup.

## Operations
- GetList

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops IndiaHsnService`.

## Connections
- Domain: [[administration-setup-1]]
- [[Items]] via the item's Chapter ID / HSN code — every GST-relevant item carries an HSN classification
