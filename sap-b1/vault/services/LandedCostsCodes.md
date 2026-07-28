---
entity: LandedCostsCodes
domain: purchasing
readable: true
methods: ["GET LandedCostsCodes(id)", "GET LandedCostsCodes", "POST LandedCostsCodes", "PATCH LandedCostsCodes(id)", "DELETE LandedCostsCodes(id)"]
rows_oil: 24
---
# LandedCostsCodes
Master list of landed-cost types (freight, customs, agency charges, etc.) with allocation method and G/L account. Live rows in JIVO_OIL_HANADB: 24.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query LandedCostsCodes --top 5
./sapb1 query LandedCostsCodes --count
./sapb1 query LandedCostsCodes --select "Code,Name,AllocationBy" --top 10
# Cost types allocated by cash value before customs (JIVO's dominant method):
./sapb1 query LandedCostsCodes --filter "AllocationBy eq 'ab_CashValueBeforeCustoms'" --select "Code,Name,LandedCostsAllocationAccount"
```
## Key fields
| Field | Meaning |
|---|---|
| Code | Cost type code |
| Name | Cost type name |
| AllocationBy | Allocation method |
| LandedCostsAllocationAccount | Allocation G/L account |
## Connections
- Domain: [[purchasing]]
- [[LandedCosts]] via cost lines LandedCostCode — documents that use these cost types
- [[ChartOfAccounts]] via LandedCostsAllocationAccount — G/L account the cost posts to
