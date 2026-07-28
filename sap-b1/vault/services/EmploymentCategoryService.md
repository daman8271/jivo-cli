---
entity: EmploymentCategoryService
domain: administration-setup-1
readable: false
methods: [GetEmploymentCategoryList]
rows_oil: null
---
# EmploymentCategoryService
Lists HR employment categories used to classify employees for payroll and reporting.

## Operations
- GetEmploymentCategoryList

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops EmploymentCategoryService`.

## Connections
- Domain: [[administration-setup-1]]
- [[EmployeesInfo]] via the employee's employment category code — categories classify employee master records
