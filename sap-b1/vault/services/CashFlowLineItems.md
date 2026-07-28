---
entity: CashFlowLineItems
domain: inventory-warehouse-1
readable: true
methods: [GET]
rows_oil: 31
---
# CashFlowLineItems
Read-only hierarchy of cash-flow statement line items used to classify postings for cash-flow reporting. Live rows in JIVO_OIL_HANADB: 31.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CashFlowLineItems --top 5
./sapb1 query CashFlowLineItems --count
./sapb1 query CashFlowLineItems --select "LineItemID,LineItemName,ParentArticle,Level" --top 10
# Only line items still active for classification:
./sapb1 query CashFlowLineItems --filter "ActiveLineItem eq 'tYES'" --top 31
```

## Key fields
| Field | Meaning |
|---|---|
| LineItemID | Internal numeric key |
| LineItemName | Line item display name |
| ParentArticle | Parent line item ID |
| Level | Depth in the hierarchy |
| Drawer | Top-level statement section |
| ActiveLineItem | Whether item is active |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[ChartOfAccounts]] via cash-flow line item assignment on account postings
