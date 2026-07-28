---
entity: AlertManagements
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 13
---
# AlertManagements
Configures automatic internal alerts (query-based or predefined) with schedules and recipient lists for notifying users of business events. Live rows in JIVO_OIL_HANADB: 13.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AlertManagements --top 5
./sapb1 query AlertManagements --count
./sapb1 query AlertManagements --select "Code,Name,Type,Active" --top 10
# only alerts that are currently switched on
./sapb1 query AlertManagements --filter "Active eq 'tYES'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| Code | Alert key |
| Name | Alert name |
| Type | Predefined or query-based |
| Active | Alert enabled flag |
| QueryID | Backing user query |
| Priority | Alert priority level |
| FrequencyType | Schedule frequency unit |
| FrequencyInterval | Runs per interval |
| DayOfExecution | Scheduled run day |
| ExecutionTime | Scheduled run time |
| LastExecutionDate | Last run date |
| NextExecutionDate | Next run date |
| SaveHistory | Keep alert history |
| Param | Predefined-alert parameter |
## Connections
- Domain: [[system-other-1]]
- [[UserQueries]] via QueryID — the saved query a query-based alert executes
- [[Users]] via AlertManagementRecipientCollection.UserCode — internal users who receive the alert
