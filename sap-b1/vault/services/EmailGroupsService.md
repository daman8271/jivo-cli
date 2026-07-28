---
entity: EmailGroupsService
domain: administration-setup-1
readable: false
methods: [GetList]
rows_oil: null
---
# EmailGroupsService
Lists email groups used to batch-send documents or campaigns to sets of business partner contacts.

## Operations
- GetList

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops EmailGroupsService`.

## Connections
- Domain: [[administration-setup-1]]
- [[BusinessPartners]] via contact persons' email group assignment — groups collect BP contacts for mailing
