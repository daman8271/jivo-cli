---
entity: UsersService
domain: administration-setup-2
readable: false
methods: ["UsersService_GetCurrentUser"]
rows_oil: null
---
# UsersService
Returns the profile of the user currently logged in to the Service Layer session.

## Operations
- UsersService_GetCurrentUser

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI; for the full user list read [[Users]] instead. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops UsersService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — the entity set of all user accounts; this service returns the session's own row
