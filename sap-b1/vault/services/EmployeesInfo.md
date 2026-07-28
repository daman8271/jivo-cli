---
entity: EmployeesInfo
domain: hr-resources
readable: true
methods: [GET, POST, PATCH, DELETE, Cancel, Close]
rows_oil: 17
---
# EmployeesInfo
The HR employee master data (OHEM): 17 employees with personal, org-assignment (department/branch/position), bank, cost and role details. Live rows in JIVO_OIL_HANADB: 17.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EmployeesInfo --top 5
./sapb1 query EmployeesInfo --count
./sapb1 query EmployeesInfo --select "EmployeeID,EmployeeCode,FirstName,Department" --top 10
# only currently active employees
./sapb1 query EmployeesInfo --filter "Active eq 'tYES'" --select "EmployeeID,FirstName,Department,Branch" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| EmployeeID | Internal employee key |
| EmployeeCode | Employee code |
| ExternalEmployeeNumber | External/payroll employee number |
| FirstName | Employee first name |
| Department | Department assignment |
| Branch | Branch assignment |
| BPLID | Business place (branch) ID |
| EmployeeType | Employee type/role classification |
| Active | Active flag (tYES/tNO) |
| CostCenterCode | Linked cost center code |
| ApplicationUserID | Linked B1 application user |
| DateOfBirth | Date of birth |
| CreateDate | Record creation date |
| EmployeeCosts | Employee cost lines |

## Connections
- Domain: [[hr-resources]]
- [[EmployeePosition]] via Position — job position assigned to the employee
- [[EmployeeRolesSetup]] via EmployeeRolesInfoLines.RoleID — roles tagged on the employee
- [[EmployeeStatus]] via StatusOfEmployee — employment status of the employee
- [[Departments]] via Department — org department assignment
- [[BusinessPlaces]] via BPLID — branch/business place assignment
- [[Users]] via ApplicationUserID — linked SAP B1 application user
- [[ProfitCenters]] via CostCenterCode — cost center the employee is charged to
- [[SalesPersons]] via SalesPersonCode — linked sales employee record
