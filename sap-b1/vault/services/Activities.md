---
entity: Activities
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# Activities
CRM activity log (calls, meetings, tasks, notes) linked to business partners; empty in JIVO_OIL_HANADB (fields from standard schema). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Activities --top 5
./sapb1 query Activities --count
./sapb1 query Activities --select "ActivityCode,CardCode,Subject,ActivityDate" --top 10
# All activities logged against one business partner (if ever populated):
./sapb1 query Activities --filter "CardCode eq 'C00001'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| ActivityCode | Activity number (key) |
| CardCode | Linked business partner |
| ActivityType | Activity type category |
| ActivityDate | Date of activity |
| ActivityTime | Time of activity |
| Subject | Activity subject line |
| ContactPersonCode | Linked contact person |
| HandledBy | Assigned user/salesperson |
| Location | Meeting location code |
| Status | Activity status code |
| StartDate | Scheduled start date |
| EndDuedate | Scheduled end/due date |
| Details | Free-text details |
| DocEntry | Linked document entry |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via CardCode
- [[ActivityTypes]] via ActivityType
- [[ActivityStatuses]] via Status
- [[ActivityLocations]] via Location
- [[Contacts]] via ContactPersonCode
- [[SalesPersons]] via HandledBy
