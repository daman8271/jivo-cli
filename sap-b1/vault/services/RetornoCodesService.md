---
entity: RetornoCodesService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# RetornoCodesService
Lists Brazil-localization bank 'retorno' (return-file) codes used to interpret bank statement/payment return files.

## Operations
- RetornoCodesService_GetList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops RetornoCodesService`. Brazil localization — not expected to carry data in an India (JIVO_OIL) company database.

## Connections
- Domain: [[administration-setup-2]]
- [[BankPages]] via bank statement lines — retorno codes classify return-file entries
- [[HouseBankAccounts]] via house bank account — return files arrive per house bank
