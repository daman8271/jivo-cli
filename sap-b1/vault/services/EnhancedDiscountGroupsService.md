---
entity: EnhancedDiscountGroupsService
domain: administration-setup-1
readable: false
methods: [GetList]
rows_oil: null
---
# EnhancedDiscountGroupsService
Lists enhanced discount group rules that grant percentage discounts to business partners by item, item group, or property.

## Operations
- GetList

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops EnhancedDiscountGroupsService`.

## Connections
- Domain: [[administration-setup-1]]
- [[BusinessPartners]] via CardCode — the BP (or BP group) the discount rule applies to
- [[Items]] via ItemCode — discount object when the rule targets a single item
- [[ItemGroups]] via ItemGroup number — discount object when the rule targets a whole item group
