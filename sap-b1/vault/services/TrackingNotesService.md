---
entity: TrackingNotesService
domain: administration-setup-2
readable: false
methods: ["TrackingNotesService_GetList"]
rows_oil: null
---
# TrackingNotesService
Returns tracking notes (audit/tracking annotations) recorded against documents or service processes.

## Operations
- TrackingNotesService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops TrackingNotesService
```

## Connections
- Domain: [[administration-setup-2]]
- [[ServiceCalls]] — service processes whose tracking annotations this service surfaces
