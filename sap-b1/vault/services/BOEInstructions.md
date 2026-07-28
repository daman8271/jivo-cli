---
entity: BOEInstructions
domain: banking-payments
readable: true
methods: ["GET BOEInstructions", "GET BOEInstructions(id)", "POST BOEInstructions", "PATCH BOEInstructions(id)", "DELETE BOEInstructions(id)"]
rows_oil: 0
---
# BOEInstructions
Setup table of instruction codes sent to the bank with bills of exchange (e.g. collection/discount instructions). Empty in JIVO_OIL_HANADB; key fields inferred from schema. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BOEInstructions --top 5
./sapb1 query BOEInstructions --count
./sapb1 query BOEInstructions --select "AbsoluteEntry,Code,Description" --top 10
# Look up one instruction code:
./sapb1 query BOEInstructions --filter "Code eq 'COLL'"
```
## Key fields
| Field | Meaning |
|---|---|
| AbsoluteEntry | Internal numeric key |
| Code | Instruction code |
| Description | Instruction description |
## Connections
- Domain: [[banking-payments]]
- [[BillOfExchangeTransactions]] via instruction code — BOEs carrying this bank instruction
- [[Banks]] — bank receiving the instruction
