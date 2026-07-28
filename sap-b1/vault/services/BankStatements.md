---
entity: BankStatements
domain: banking-payments
readable: true
methods: ["GET BankStatements", "GET BankStatements(id)", "POST BankStatements", "PATCH BankStatements(id)", "DELETE BankStatements(id)"]
rows_oil: 0
---
# BankStatements
Electronic bank statements imported for bank-statement processing and reconciliation. Empty in JIVO_OIL_HANADB (reconciliation evidently done outside BSP); key fields inferred from SAP B1 schema. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BankStatements --top 5
./sapb1 query BankStatements --count
./sapb1 query BankStatements --select "InternalNumber,StatementNumber,StatementDate,EndingBalance" --top 10
# Statements imported this year:
./sapb1 query BankStatements --filter "StatementDate ge '2026-01-01'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| InternalNumber | Internal statement key |
| BankAccountKey | House bank account key |
| StatementNumber | Bank's statement number |
| StatementDate | Statement date |
| StartingBalance | Opening balance |
| EndingBalance | Closing balance |
| Currency | Statement currency |
| Status | Processing status |
## Connections
- Domain: [[banking-payments]]
- [[HouseBankAccounts]] via BankAccountKey — company account the statement belongs to
- [[Banks]] via the house account's bank code — issuing bank
- [[Currencies]] via Currency — statement currency
