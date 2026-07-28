---
entity: SalesPersons
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 155
---
# SalesPersons
Master list of 155 sales employees with commission settings, referenced by every sales document via SalesPersonCode. Live rows in JIVO_OIL_HANADB: 155.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesPersons --top 5
./sapb1 query SalesPersons --count
./sapb1 query SalesPersons --select "SalesEmployeeCode,SalesEmployeeName,Active,Mobile" --top 10
# Only the currently active (non-retired) sales employees:
./sapb1 query SalesPersons --filter "Active eq 'tYES'" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| SalesEmployeeCode | Sales employee code (key) |
| SalesEmployeeName | Sales employee name |
| CommissionForSalesEmployee | Commission percentage |
| CommissionGroup | Commission group code |
| EmployeeID | Linked HR employee ID |
| Email | Email address |
| Mobile | Mobile number |
| Telephone | Landline number |
| Active | Active/inactive flag |
| Locked | Locked-from-use flag |
| Remarks | Free-text remarks |

## Connections
- Domain: [[sales-ar]]
- [[EmployeesInfo]] via EmployeeID
- [[BusinessPartners]] via default SalesPersonCode on the customer master
- [[Orders]] via SalesPersonCode
- [[Invoices]] via SalesPersonCode
