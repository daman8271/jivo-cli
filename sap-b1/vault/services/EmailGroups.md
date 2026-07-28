---
entity: EmailGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# EmailGroups
Email distribution groups for bulk mailing documents/campaigns to business partner contacts; unused here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EmailGroups --top 5
./sapb1 query EmailGroups --count
./sapb1 query EmailGroups --select "Code,Name" --top 10
# If ever populated, find a group by name fragment:
./sapb1 query EmailGroups --filter "contains(Name,'News')" --top 5
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Standard fields are Code (key) and Name (group label); confirm with `./sapb1 fields EmailGroups` once populated.

## Connections
- Domain: [[administration-setup-3]]
- [[BusinessPartners]] — BP contact employees are assigned to an email group for bulk mailing
