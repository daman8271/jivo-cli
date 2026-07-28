---
entity: ElectronicFileFormatsService
domain: administration-setup-1
readable: false
methods: [GetElectronicFileFormatList]
rows_oil: null
---
# ElectronicFileFormatsService
Lists the electronic file format definitions (e.g. bank/tax file layouts) configured for electronic document generation.

## Operations
- GetElectronicFileFormatList

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; the same data is readable through the [[ElectronicFileFormats]] entity set. Browse this service's operations with `./sapb1 ops ElectronicFileFormatsService`.

## Connections
- Domain: [[administration-setup-1]]
- [[ElectronicFileFormats]] via FormatID — the entity-set twin of this list service
