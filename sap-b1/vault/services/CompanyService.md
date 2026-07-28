---
entity: CompanyService
domain: administration-setup-1
readable: true
methods: [CompanyService_GetCompanyInfo, CompanyService_GetAdminInfo, CompanyService_GetPeriods, CompanyService_GetPeriod, CompanyService_GetFinancePeriods, CompanyService_GetFinancePeriod, CompanyService_GetFeaturesStatus, CompanyService_GetPathAdmin, CompanyService_RoundDecimal, CompanyService_GetItemPrice, CompanyService_GetAdvancedGLAccount, CompanyService_CreatePeriod, CompanyService_UpdateCompanyInfo, CompanyService_UpdateAdminInfo, CompanyService_UpdatePeriod, CompanyService_UpdateFinancePeriod, CompanyService_RemoveFinancePeriod, CompanyService_CreatePeriodWithFinanceParams, CompanyService_UpdatePathAdmin, CompanyService_LogLoginAction, CompanyService_LogLogoffAction]
rows_oil: null
---
# CompanyService
Exposes company-wide configuration: company/admin settings, posting periods, feature toggles, and utility calls like item price lookup and decimal rounding.

## Operations
GET-exposed (read-shaped):
- `CompanyService_GetCompanyInfo`
- `CompanyService_GetAdminInfo`
- `CompanyService_GetPeriods`
- `CompanyService_GetFeaturesStatus`
- `CompanyService_GetPathAdmin`

POST-only RPCs (parameterised reads and writes — the write side is off-limits under our read-only rule):
- `CompanyService_GetPeriod`
- `CompanyService_GetFinancePeriods`
- `CompanyService_GetFinancePeriod`
- `CompanyService_RoundDecimal`
- `CompanyService_GetItemPrice`
- `CompanyService_GetAdvancedGLAccount`
- `CompanyService_CreatePeriod`
- `CompanyService_UpdateCompanyInfo`
- `CompanyService_UpdateAdminInfo`
- `CompanyService_UpdatePeriod`
- `CompanyService_UpdateFinancePeriod`
- `CompanyService_RemoveFinancePeriod`
- `CompanyService_CreatePeriodWithFinanceParams`
- `CompanyService_UpdatePathAdmin`
- `CompanyService_LogLoginAction`
- `CompanyService_LogLogoffAction`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops CompanyService`.

## Connections
- Domain: [[administration-setup-1]]
- [[Items]] — `GetItemPrice` looks up a price for an ItemCode
- [[PriceLists]] — the price lookup resolves against a PriceList number
- [[ChartOfAccounts]] — `GetAdvancedGLAccount` returns the determined G/L account (AcctCode)
- [[Currencies]] — company local/system currency configuration lives in CompanyInfo
