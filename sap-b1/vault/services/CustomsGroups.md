---
entity: CustomsGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# CustomsGroups
Customs duty groups defining import duty rates and the G/L allocation/expense accounts for landed-cost customs on imported items. Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CustomsGroups --top 5
./sapb1 query CustomsGroups --count
./sapb1 query CustomsGroups --select "Code,Name,Customs,Total" --top 10
# Groups that actually levy duty:
./sapb1 query CustomsGroups --filter "Total gt 0" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Group numeric key |
| Name | Group display name |
| Number | Group reference number |
| Customs | Customs duty rate % |
| Purchase | Purchase tax rate % |
| Other | Other charges rate % |
| Total | Combined effective rate % |
| CustomsAllocationAccount | Duty allocation G/L account |
| CustomsExpenseAccount | Duty expense G/L account |
| PortAddress | Entry port address |
| PortState | Entry port state |
| Locked | Locked-against-changes flag |

## Connections
- Domain: [[administration-setup-3]]
- [[ChartOfAccounts]] via CustomsAllocationAccount / CustomsExpenseAccount — G/L accounts for landed-cost duty postings
- [[Items]] via the item master's CustomsGroupCode — imported items assigned to this group
