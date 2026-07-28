---
entity: AssetTransferService
domain: fixed-assets
readable: true
methods: [AssetTransferService_Cancel, AssetTransferService_GetList]
rows_oil: null
---
# AssetTransferService
RPC helper to list and cancel asset transfer documents that move assets between classes or cost centers.

## Operations
- `AssetTransferService_Cancel` — cancels a transfer document (write — out of scope under the read-only rule)
- `AssetTransferService_GetList` — lists transfer documents

Entity sets are the read path in the CLI — read the documents via [[AssetTransfer]]. Browse this service's operations with `./sapb1 ops AssetTransferService`.

## Connections
- Domain: [[fixed-assets]]
- [[AssetTransfer]] — the entity set this service lists and cancels (DocEntry)
