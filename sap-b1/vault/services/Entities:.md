---
entity: "Entities:"
domain: system-other-1
readable: true
methods: [GET]
rows_oil: null
---
# Entities:
Service-document root that lists all entity sets exposed by the Service Layer (metadata/discovery endpoint, not business data).
## Operations
- GET Entities
- GET Entity(id)

Function service — entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops Entities:` (and discover readable sets with `./sapb1 entities`).
## Connections
- Domain: [[system-other-1]]
