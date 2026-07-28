---
entity: ExternalCallsService
domain: administration-setup-1
readable: false
methods: [SendCall, UpdateCall, GetCall]
rows_oil: null
---
# ExternalCallsService
Sends and tracks calls to external systems/services (e.g. tax authority or e-invoicing endpoints) from within SAP B1.

## Operations
- SendCall
- UpdateCall
- GetCall

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops ExternalCallsService`. Note that SendCall/UpdateCall are write actions and stay out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-1]]
