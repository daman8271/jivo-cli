---
entity: BankChargesAllocationCodes
domain: banking-payments
readable: true
methods: ["GET BankChargesAllocationCodes", "GET BankChargesAllocationCodes(id)", "POST BankChargesAllocationCodes", "PATCH BankChargesAllocationCodes(id)", "DELETE BankChargesAllocationCodes(id)", "POST BankChargesAllocationCodes(id)/SetDefaultBankChargesAllocationCode"]
rows_oil: 0
---
# BankChargesAllocationCodes
Master list of allocation codes that map bank charges/fees to G/L expense accounts on payments. Empty in JIVO_OIL_HANADB; key fields inferred from SAP B1 schema (live table returned no rows). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BankChargesAllocationCodes --top 5
./sapb1 query BankChargesAllocationCodes --count
./sapb1 query BankChargesAllocationCodes --select "Code,Name,AllocationAccount,IsDefault" --top 10
# The default allocation code (the one payments pick automatically):
./sapb1 query BankChargesAllocationCodes --filter "IsDefault eq 'tYES'"
```
## Key fields
| Field | Meaning |
|---|---|
| Code | Allocation code key |
| Name | Code description |
| AllocationAccount | G/L account for charges |
| IsDefault | Default code flag |
## Connections
- Domain: [[banking-payments]]
- [[ChartOfAccounts]] via AllocationAccount — expense account the bank fee posts to
