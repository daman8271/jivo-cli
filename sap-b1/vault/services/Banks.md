---
entity: Banks
domain: banking-payments
readable: true
methods: ["GET Banks", "GET Banks(id)", "POST Banks", "PATCH Banks(id)", "DELETE Banks(id)"]
rows_oil: 65
---
# Banks
Master catalog of banks (codes, SWIFT/IBAN, country, outgoing-check defaults) referenced by house bank accounts and business partner bank details; 65 banks defined. Live rows in JIVO_OIL_HANADB: 65.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Banks --top 5
./sapb1 query Banks --count
./sapb1 query Banks --select "BankCode,BankName,CountryCode,SwiftNo" --top 10
# Indian banks only:
./sapb1 query Banks --filter "CountryCode eq 'IN'" --select "BankCode,BankName,SwiftNo"
```
## Key fields
| Field | Meaning |
|---|---|
| AbsoluteEntry | Internal numeric key |
| BankCode | Bank short code |
| BankName | Bank display name |
| CountryCode | Bank's home country |
| SwiftNo | SWIFT/BIC code |
| IBAN | Default IBAN |
| AccountforOutgoingChecks | G/L account for outgoing checks |
| BranchforOutgoingChecks | Branch used for outgoing checks |
| NextCheckNumber | Next check number counter |
| DefaultBankAccountKey | Default house account key |
| PostOffice | Post-office bank flag |
| DigitalPayments | Digital-payments enabled flag |
## Connections
- Domain: [[banking-payments]]
- [[Countries]] via CountryCode — bank's home country
- [[ChartOfAccounts]] via AccountforOutgoingChecks — G/L account behind outgoing checks
- [[HouseBankAccounts]] via BankCode — company accounts held at this bank
