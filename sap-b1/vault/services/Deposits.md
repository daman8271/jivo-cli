---
entity: Deposits
domain: banking-payments
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# Deposits
Bank deposits of received checks/cash/credit vouchers into house bank accounts. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Deposits --top 5
./sapb1 query Deposits --count
./sapb1 query Deposits --select "DepositNumber,DepositDate,BankCode,TotalLC" --top 10
# deposits made this fiscal year
./sapb1 query Deposits --filter "DepositDate ge '2026-04-01'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| DepositNumber | Deposit document number |
| AbsEntry | Internal key |
| DepositType | Checks / cash / vouchers |
| DepositDate | Date of deposit |
| DepositAccount | Target G/L account |
| BankCode | House bank code |
| BankAccountNum | House bank account |
| BankBranch | Bank branch |
| TotalLC | Total in local currency |
| TotalFC | Total in foreign currency |
| DepositCurrency | Deposit currency |
| JournalRemarks | JE remark text |
| Series | Numbering series |
| VoucherAccount | Voucher clearing account |
## Connections
- Domain: [[banking-payments]]
- [[HouseBankAccounts]] via BankCode + BankAccountNum — the receiving bank account
- [[ChartOfAccounts]] via DepositAccount / VoucherAccount — G/L accounts hit
- [[IncomingPayments]] — source receipts whose checks/cash get deposited
- [[JournalEntries]] — the JE posted by the deposit
- [[Currencies]] via DepositCurrency — deposit currency
