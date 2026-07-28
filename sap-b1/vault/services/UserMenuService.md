---
entity: UserMenuService
domain: administration-setup-2
readable: false
methods: ["UserMenuService_GetCurrentUserMenu", "UserMenuService_UpdateCurrentUserMenu", "UserMenuService_GetUserMenu", "UserMenuService_UpdateUserMenu"]
rows_oil: null
---
# UserMenuService
Reads and updates the personalized SAP B1 menu layout for the current or a specified user.

## Operations
- UserMenuService_GetCurrentUserMenu
- UserMenuService_UpdateCurrentUserMenu
- UserMenuService_GetUserMenu
- UserMenuService_UpdateUserMenu

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. The two Update operations are writes and stay out of scope under our standing READ-ONLY rule. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops UserMenuService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — the user accounts whose personalized menu layouts this service manages
