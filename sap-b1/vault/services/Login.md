---
entity: Login
domain: system-other-1
readable: false
methods: [POST]
rows_oil: null
---
# Login
Authenticates a user against a company database and opens a Service Layer session (returns B1SESSION cookie).

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

The `sapb1` CLI handles session login internally from `.env` credentials — never call this endpoint by hand.
## Connections
- Domain: [[system-other-1]]
