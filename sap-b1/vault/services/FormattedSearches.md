---
entity: FormattedSearches
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 38
---
# FormattedSearches
Formatted Search (FMS) definitions that attach user queries or valid-value lists to specific form fields to auto-populate or validate them in the B1 client. Live rows in JIVO_OIL_HANADB: 38.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query FormattedSearches --top 5
./sapb1 query FormattedSearches --count
./sapb1 query FormattedSearches --select "Index,FormID,ItemID,QueryID" --top 10
# All FMS wired onto one form (e.g. FormID '139' = sales order):
./sapb1 query FormattedSearches --filter "FormID eq '139'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Index | FMS record key |
| FormID | Target B1 form ID |
| ItemID | Target form item/field |
| ColumnID | Target grid column |
| FieldID | Bound database field |
| QueryID | Attached user query |
| Action | Behavior (query/valid values) |
| Refresh | Auto-refresh trigger mode |
| ForceRefresh | Always re-run flag |
| ByField | Refresh-trigger field |
| ByFieldEx | Extended trigger field |
| FieldIDs | Multiple trigger fields |
| UserValidValues | Inline valid-value list |

## Connections
- Domain: [[administration-setup-3]]
- [[UserQueries]] via QueryID — the saved query an FMS executes
