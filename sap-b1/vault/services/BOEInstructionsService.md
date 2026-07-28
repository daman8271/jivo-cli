---
entity: BOEInstructionsService
domain: banking-payments
readable: false
methods: ["BOEInstructionsService_GetBOEInstructionList"]
rows_oil: null
---
# BOEInstructionsService
RPC helper that lists bill-of-exchange bank instruction codes.
## Operations
- `BOEInstructionsService_GetBOEInstructionList`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity set: query [[BOEInstructions]] directly. Browse this service's operations with `./sapb1 ops BOEInstructionsService`.
## Connections
- Domain: [[banking-payments]]
- [[BOEInstructions]] — the entity set holding the instruction codes (query this instead)
