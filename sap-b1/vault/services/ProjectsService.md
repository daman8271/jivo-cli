---
entity: ProjectsService
domain: projects
readable: false
methods: [GetProjectList]
rows_oil: null
---
# ProjectsService
RPC-style helper returning the list of financial project codes (OPRJ) for lookup/selection.

## Operations
- `GetProjectList` — returns all financial project codes and names

Entity sets are the read path in the CLI — read the same data via [[Projects]] with `./sapb1 query Projects`; browse this service's catalogued operations with `./sapb1 ops ProjectsService`.

## Connections
- Domain: [[projects]]
- [[Projects]] — the OPRJ entity set this helper enumerates (Code)
