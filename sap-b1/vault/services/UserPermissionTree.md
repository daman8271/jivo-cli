---
entity: UserPermissionTree
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 28
---
# UserPermissionTree
Custom (addon/UDO) permission-tree nodes that plug extension authorizations into B1's General Authorizations screen. Live rows in JIVO_OIL_HANADB: 28.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UserPermissionTree --top 5
./sapb1 query UserPermissionTree --count
./sapb1 query UserPermissionTree --select "PermissionID,Name,ParentID,IsItem" --top 10
# Leaf permission items only (actual grantable authorizations, not folders):
./sapb1 query UserPermissionTree --filter "IsItem eq 'tYES'" --select "PermissionID,Name,Options" --top 30
```

## Key fields
| Field | Meaning |
|---|---|
| PermissionID | Permission node id (key) |
| Name | Node display name |
| ParentID | Parent node id |
| DisplayOrder | Sort order in tree |
| IsItem | Leaf item vs folder |
| Options | Allowed levels (full/read/none) |
| Levels | Number of permission levels |
| UserPermissionForms | Forms gated by this node |
| UserSignature | Last-modified-by user |

## Connections
- Domain: [[administration-setup-3]]
- [[Users]] via per-user authorization assignments against PermissionID
- [[UserObjectsMD]] via ApplyAuthorization (UDOs register their own nodes here)
