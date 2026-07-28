---
entity: BEMReplicationPeriods
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH]
rows_oil: 2
---
# BEMReplicationPeriods
Tracks Budget/Enterprise Management replication periods and their sync status to external planning systems. Live rows in JIVO_OIL_HANADB: 2.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BEMReplicationPeriods --top 5
./sapb1 query BEMReplicationPeriods --count
./sapb1 query BEMReplicationPeriods --select "AbsEntry,ScopeName,StartDate,Status" --top 10
# Only periodically replicated scopes:
./sapb1 query BEMReplicationPeriods --filter "Periodic eq 'tYES'"
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal entry key |
| ScopeKey | Replication scope key |
| ScopeName | Replication scope name |
| StartDate | Period start date |
| Status | Replication sync status |
| UpdateDate | Last update date |
| LastRepId | Last replication run ID |
| Periodic | Recurring replication flag |

## Connections
- Domain: [[financials-accounting-1]]
