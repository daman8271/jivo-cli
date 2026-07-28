---
entity: LicenseService
domain: administration-setup-1
readable: false
methods: [GetInstallationNumber]
rows_oil: null
---
# LicenseService
Returns the SAP B1 installation number for license administration.

## Operations
- GetInstallationNumber

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops LicenseService`.

## Connections
- Domain: [[administration-setup-1]]
