---
entity: ItemImages
domain: inventory-warehouse-1
readable: true
methods: [GET, PATCH, DELETE]
rows_oil: null
---
# ItemImages
Attachment-style endpoint to fetch or replace the picture stored on an item master record (keyed by ItemCode, no collection listing).

## Operations
- `GET ItemImages(id)` — fetch the image for one item
- `PATCH ItemImages(id)` — replace the image (write — out of scope)
- `DELETE ItemImages(id)` — remove the image (write — out of scope)

Not a listable entity set — there is no collection to query. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops ItemImages` (from `~/sap-b1/cli`).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] via ItemCode key (the picture on the item master)
