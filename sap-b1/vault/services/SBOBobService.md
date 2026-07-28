---
entity: SBOBobService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# SBOBobService
Utility 'bridge of business objects' functions: system/local currency, exchange and index rates, due-date calculation, permissions, and money formatting.

## Operations
- SBOBobService_GetSystemPermission
- SBOBobService_GetSystemCurrency
- SBOBobService_GetDueDate
- SBOBobService_GetLocalCurrency
- SBOBobService_GetCurrencyRate
- SBOBobService_GetIndexRate
- SBOBobService_Format_MoneyToString
- SBOBobService_SetCurrencyRate
- SBOBobService_SetSystemPermission

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops SBOBobService`. The Set* operations mutate rates/permissions and are out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-2]]
- [[Currencies]] via currency code — system/local currency and exchange-rate lookups
- [[Users]] via UserCode — system permission checks per user
- [[PaymentTermsTypes]] via payment terms — due-date calculation follows payment terms
