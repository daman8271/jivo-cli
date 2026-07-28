---
entity: UserTablesMD
domain: administration-setup-4
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 59
---
# UserTablesMD
Metadata registry of custom user-defined tables (UDTs) added to the company database schema. Live rows in JIVO_OIL_HANADB: 59.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UserTablesMD --top 5
./sapb1 query UserTablesMD --count
./sapb1 query UserTablesMD --select "TableName,TableDescription,TableType" --top 10
# UDTs that enforce SAP authorization checks:
./sapb1 query UserTablesMD --filter "ApplyAuthorization eq 'tYES'" --select "TableName,TableDescription"
```

## Key fields
| Field | Meaning |
|---|---|
| TableName | UDT name (without @) |
| TableDescription | Human-readable table description |
| TableType | UDT type (no-object/document/etc.) |
| Archivable | Rows can be archived |
| ArchiveDateField | Date field used for archiving |
| ApplyAuthorization | Authorization checks enforced |
| DisplayMenu | Shown in B1 menu |

## Connections
- Domain: [[administration-setup-4]]
- [[UserFieldsMD]] via TableName — custom fields defined on this UDT
- [[UserObjectsMD]] via TableName — user-defined objects (UDOs) built on this UDT
