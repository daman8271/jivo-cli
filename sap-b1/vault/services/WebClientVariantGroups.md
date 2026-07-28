---
entity: WebClientVariantGroups
domain: administration-setup-4
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 3
---
# WebClientVariantGroups
Groups saved view variants (per user and object/view) in the SAP B1 Web Client, tracking each user's default variant. Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientVariantGroups --top 5
./sapb1 query WebClientVariantGroups --count
./sapb1 query WebClientVariantGroups --select "Guid,UserId,ObjectName,DefaultVariant" --top 10
# All view variants a specific user has saved in the Web Client:
./sapb1 query WebClientVariantGroups --filter "UserId eq 1" --select "ObjectName,ViewId,DefaultVariant"
```

## Key fields
| Field | Meaning |
|---|---|
| Guid | Unique variant group ID |
| UserId | Owning user's internal key |
| ObjectName | B1 object the view targets |
| ViewId | Web Client view identifier |
| ViewType | Kind of view (list/detail) |
| DefaultVariant | User's default variant GUID |

## Connections
- Domain: [[administration-setup-4]]
- [[Users]] via UserId — matches the user's InternalKey in Users
