---
entity: EnhancedDiscountGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# EnhancedDiscountGroups
Advanced discount-group rules granting BP-specific percentage discounts by item, item group, or property; unused here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EnhancedDiscountGroups --top 5
./sapb1 query EnhancedDiscountGroups --count
# Table is empty here; discover fields once populated:
./sapb1 fields EnhancedDiscountGroups
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Standard shape is an AbsEntry key with the BP/card code, discount basis type, and a lines collection of per-item/group/property discount percentages; confirm with `./sapb1 fields EnhancedDiscountGroups` once populated.

## Connections
- Domain: [[administration-setup-3]]
- [[BusinessPartners]] via the rule's BP card code — who the discount applies to
- [[Items]] via discount lines keyed by item — per-item discount rules
- [[ItemGroups]] via discount lines keyed by item group — per-group discount rules
