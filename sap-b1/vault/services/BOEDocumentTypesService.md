---
entity: BOEDocumentTypesService
domain: banking-payments
readable: false
methods: ["BOEDocumentTypesService_GetBOEDocumentTypeList"]
rows_oil: null
---
# BOEDocumentTypesService
RPC helper that lists bill-of-exchange document type definitions.
## Operations
- `BOEDocumentTypesService_GetBOEDocumentTypeList`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity set: query [[BOEDocumentTypes]] directly. Browse this service's operations with `./sapb1 ops BOEDocumentTypesService`.
## Connections
- Domain: [[banking-payments]]
- [[BOEDocumentTypes]] — the entity set holding the type definitions (query this instead)
