---
entity: MobileAppService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# MobileAppService
Backend for the SAP B1 Sales and Service mobile apps: server time, technician schedules/settings, and mobile report configuration.

## Operations
- MobileAppService_GetCurrentServerDateTime
- MobileAppService_GetDppChangeParams
- MobileAppService_GetTechnicianSchedulings
- MobileAppService_GetEmployeeFullNames
- MobileAppService_GetTechnicianSettings
- MobileAppService_UpdateTechnicianSettings
- MobileAppService_GetTechnicianSettingsGroup
- MobileAppService_UpdateTechnicianSettingsGroup
- MobileAppService_GetSalesAppSetting
- MobileAppService_UpdateSalesAppSetting
- MobileAppService_GetServiceAppReportContent
- MobileAppService_UpdateServiceAppReportContent
- MobileAppService_GetServiceAppReport
- MobileAppService_UpdateServiceAppReport

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops MobileAppService`. The Update* operations mutate settings and are out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-2]]
- [[EmployeesInfo]] via EmployeeID — technicians and employee full names served to the apps
- [[ServiceCalls]] via service call ID — technician schedulings map to service calls
- [[Users]] via UserCode — per-user mobile app settings
