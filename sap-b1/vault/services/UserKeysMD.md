---
entity: UserKeysMD
domain: administration-setup-3
readable: true
methods: [GET, POST, DELETE]
rows_oil: 0
---
# UserKeysMD
Metadata of user-defined unique key indexes on user tables; none defined here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UserKeysMD --top 5
./sapb1 query UserKeysMD --count
./sapb1 query UserKeysMD --select "TableName,KeyName,Unique" --top 10
# Keys defined on a specific user table (if ever populated):
./sapb1 query UserKeysMD --filter "TableName eq 'JIVO_MASTER'" --top 10
```
Set is empty here — confirm live field names with `./sapb1 fields UserKeysMD` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| TableName | Host user table |
| KeyName | Index/key name |
| Unique | Uniqueness enforced yes/no |
| ElementsOfUserKey | Fields making up the key |

(No key fields captured in recon — the set is empty; fields above are the standard Service Layer schema.)

## Connections
- Domain: [[administration-setup-3]]
- [[UserTablesMD]] via TableName
- [[UserFieldsMD]] via ElementsOfUserKey → field names
