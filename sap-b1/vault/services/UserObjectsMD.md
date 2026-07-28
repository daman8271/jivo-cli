---
entity: UserObjectsMD
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 27
---
# UserObjectsMD
Metadata of 27 user-defined objects (UDOs) — custom business objects built on user tables with their own forms, menus, and services. Live rows in JIVO_OIL_HANADB: 27.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UserObjectsMD --top 5
./sapb1 query UserObjectsMD --count
./sapb1 query UserObjectsMD --select "Code,Name,ObjectType,TableName" --top 10
# Document-style UDOs (custom transactional objects, vs plain master data):
./sapb1 query UserObjectsMD --filter "ObjectType eq 'boud_Document'" --select "Code,Name,TableName,MenuCaption" --top 30
```

## Key fields
| Field | Meaning |
|---|---|
| Code | UDO code (key) |
| Name | UDO display name |
| ObjectType | Master data or document |
| TableName | Backing user table |
| LogTableName | Change-log table |
| ExtensionName | Owning addon/extension |
| MenuCaption | Menu entry text |
| MenuUID | Menu unique id |
| FatherMenuID | Parent menu node |
| CanDelete | Delete allowed yes/no |
| CanCancel | Cancel allowed yes/no |
| CanClose | Close allowed yes/no |
| ManageSeries | Numbering series enabled |
| ApplyAuthorization | Hooked into permission tree |

## Connections
- Domain: [[administration-setup-3]]
- [[UserTablesMD]] via TableName (each UDO sits on a user table)
- [[UserFieldsMD]] via the backing table's UDFs
- [[UserPermissionTree]] via ApplyAuthorization → permission node
