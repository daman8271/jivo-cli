---
entity: UserFieldsMD
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 5572
---
# UserFieldsMD
Metadata of all user-defined fields (UDFs) added to system and user tables — 5,572 custom fields, a major map of this installation's customizations. Live rows in JIVO_OIL_HANADB: 5572.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UserFieldsMD --top 5
./sapb1 query UserFieldsMD --count
./sapb1 query UserFieldsMD --select "TableName,FieldID,Name,Description" --top 10
# Every UDF bolted onto the Items master (OITM) — the customization map for products:
./sapb1 query UserFieldsMD --filter "TableName eq 'OITM'" --select "FieldID,Name,Description,Type" --top 50
```
Note: single-record GET uses a composite key — `UserFieldsMD(TableName='OITM',FieldID=1)`.

## Key fields
| Field | Meaning |
|---|---|
| TableName | Host table (key part 1) |
| FieldID | Field number (key part 2) |
| Name | UDF name (U_ prefix in DB) |
| Description | Human-readable label |
| Type | Data type (alpha/number/date…) |
| SubType | Type refinement |
| Size | Storage size |
| EditSize | UI edit length |
| DefaultValue | Default on new records |
| Mandatory | Required yes/no |
| LinkedTable | Linked user table |
| LinkedSystemObject | Linked system object type |
| LinkedUDO | Linked user-defined object |
| ValidValuesMD | Dropdown valid values list |

## Connections
- Domain: [[administration-setup-3]]
- [[UserTablesMD]] via TableName (UDFs on @-prefixed user tables)
- [[UserObjectsMD]] via LinkedUDO
