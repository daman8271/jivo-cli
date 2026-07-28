# SAP Business One Service Layer — Administration & Setup (part 1)

Reference for the 40 services in the `administration-setup-1` domain. Every
operation below is copied verbatim from `catalog/services.json`; every
description and payload/return-type name is taken from
`raw/service-layer-api-reference.html`. Nothing here is invented — where the
reference gives no field list, the entry says so.

## How to read this domain

Unlike the transactional domains (`Orders`, `Invoices`, `BusinessPartners`,
…), almost every entry here is a **named function / action service**, not a
`$select`-able OData entity collection. You invoke them by their RPC-style
endpoint name — `POST /b1s/v1/<ServiceName>_<MethodName>` — usually with a
typed JSON payload in the request body. Only three services expose a `GET`
operation (`AccrualTypesService`, `AttributeGroupsService`, `CompanyService`);
even those `GET`s are function invocations that return a complex-type
structure, **not** entity collections you can filter with `$filter`/`$select`.

Consequences for this doc:

- The API-reference HTML carries only the generic template line *"This API
  enables you to invoke the interfaces defined on '<Service>'."* plus a
  per-operation *"Invoke the method '<X>' on this service…"*. Where that is the
  only text, the plain-English purpose is marked **(inferred)** — it is
  reasoned from the operation name, not lifted from a descriptive sentence.
- Where the HTML does name the JSON payload type or return structure (e.g.
  `CompanyInfo`, `ExternalReconciliation`, `GetChangeLogParams`), that name is
  reproduced as grounding — it is real, from the reference.
- These function services have **no queryable `$metadata` entity fields**. For
  any field-level detail, query the live `$metadata` (or inspect the returned
  complex type). This doc never guesses field names.

**Version note:** the reference HTML shows examples on `/b1s/v1/…`; the same
function endpoints are also served on `/b1s/v1/…`. Examples below use `v1` to
match the `sapb1` CLI convention.

**CLI note:** the `sapb1` CLI is **read-only and GET-only** (`sapb1 query` does
`GET /b1s/v1/<EntitySet>`). It cannot execute the `POST` function/action calls
in this domain. The verified, offline-capable CLI equivalent for exploring any
service here is `sapb1 ops <ServiceName>`, which prints that service's
catalogued operations from the embedded schema.

---

## AccrualTypesService

(1) **Purpose:** Retrieve the list of accrual (deferred charge) types defined in the company. (inferred)
(2) **Type:** readable — has a GET op (function-style GET, returns a list; not an OData entity collection)
(3) **Operations:**
- `GET AccrualTypesService_GetAccrualTypeList`
- `POST AccrualTypesService_GetAccrualTypeList`

(4) **Read example:**
```
GET /b1s/v1/AccrualTypesService_GetAccrualTypeList
```
CLI (offline op inspection — the CLI cannot invoke this function directly):
```
sapb1 ops AccrualTypesService
```
fields: query live `$metadata` (function returns a complex-type list; field names are not in the HTML reference)

---

## ApprovalRequestsService

(1) **Purpose:** Retrieve approval requests — the full list, only open ones, or all requests. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ApprovalRequestsService_GetApprovalRequestList`
- `POST ApprovalRequestsService_GetOpenApprovalRequestList`
- `POST ApprovalRequestsService_GetAllApprovalRequestsList`

---

## ApprovalStagesService

(1) **Purpose:** Retrieve the list of approval stages configured in the approval workflow. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ApprovalStagesService_GetApprovalStageList`

---

## ApprovalTemplatesService

(1) **Purpose:** Retrieve the list of approval process templates. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ApprovalTemplatesService_GetApprovalTemplateList`

---

## AttributeGroupsService

(1) **Purpose:** Retrieve the list of item attribute groups. (inferred)
(2) **Type:** readable — has a GET op (function-style GET, returns a list; not an OData entity collection)
(3) **Operations:**
- `GET AttributeGroupsService_GetList`
- `POST AttributeGroupsService_GetList`

(4) **Read example:**
```
GET /b1s/v1/AttributeGroupsService_GetList
```
CLI (offline op inspection):
```
sapb1 ops AttributeGroupsService
```
fields: query live `$metadata` (function returns a complex-type list; field names are not in the HTML reference)

---

## BPOpeningBalanceService

(1) **Purpose:** Create / post opening balances for business partners. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST BPOpeningBalanceService_CreateOpenBalance`

---

## BranchesService

(1) **Purpose:** Retrieve the list of company branches. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST BranchesService_GetBranchList`

---

## BrazilBeverageIndexersService

(1) **Purpose:** Retrieve the list of Brazil beverage tax indexers (localization). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST BrazilBeverageIndexersService_GetList`

---

## BrazilFuelIndexersService

(1) **Purpose:** Retrieve the list of Brazil fuel tax indexers (localization). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST BrazilFuelIndexersService_GetList`

---

## CashDiscountsService

(1) **Purpose:** Retrieve the list of cash-discount definitions. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST CashDiscountsService_GetCashDiscountList`

---

## CertificateSeriesService

(1) **Purpose:** Retrieve the list of certificate series (e.g. withholding / document certificate numbering). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST CertificateSeriesService_GetCertificateSeriesList`

---

## ChangeLogsService

(1) **Purpose:** Retrieve object change-history logs and compute the differences between logged versions. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ChangeLogsService_GetChangeLog` — payload `GetChangeLogParams` (JSON)
- `POST ChangeLogsService_GetChangeLogDifferences` — payload `ShowDifferenceParams` (JSON)

---

## CockpitsService

(1) **Purpose:** Manage user/template cockpits (dashboards) — list them and publish a cockpit definition. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST CockpitsService_GetCockpitList`
- `POST CockpitsService_PublishCockpit` — payload `Cockpit` (JSON)
- `POST CockpitsService_GetUserCockpitList`
- `POST CockpitsService_GetTemplateCockpitList`

---

## CompanyService

(1) **Purpose:** Read and update core company configuration — company info, administration/system-initialization settings, posting/finance periods, feature status, path administration, and login/logoff logging. (grounded: `GetCompanyInfo` returns the `CompanyInfo` structure; `GetAdminInfo` returns the `AdminInfo` structure of system-initialization/financial/banking definitions.)
(2) **Type:** readable — has GET ops (function-style GETs returning complex structures; not OData entity collections)
(3) **Operations:**
- `GET CompanyService_GetCompanyInfo` — returns the `CompanyInfo` data structure (initial company parameters; defaults vary by country localization)
- `POST CompanyService_GetCompanyInfo` — as above
- `POST CompanyService_UpdateCompanyInfo` — payload `CompanyInfo` (JSON)
- `GET CompanyService_GetAdminInfo` — returns the `AdminInfo` data structure (administration properties for system initialization, financials, banking)
- `POST CompanyService_GetAdminInfo` — as above
- `POST CompanyService_UpdateAdminInfo` — payload `AdminInfo` (JSON)
- `POST CompanyService_CreatePeriod` — payload `PeriodCategory` (JSON)
- `GET CompanyService_GetPeriods`
- `POST CompanyService_GetPeriod` — payload `PeriodCategoryParams`; returns the `PeriodCategory` data structure
- `POST CompanyService_UpdatePeriod` — payload `PeriodCategory` (JSON)
- `POST CompanyService_GetFinancePeriods` — payload `PeriodCategoryParams` (JSON)
- `POST CompanyService_GetFinancePeriod` — payload `FinancePeriodParams` (JSON)
- `POST CompanyService_UpdateFinancePeriod` — payload `FinancePeriod` (JSON)
- `POST CompanyService_RemoveFinancePeriod` — payload `FinancePeriodParams` (JSON)
- `POST CompanyService_CreatePeriodWithFinanceParams` — payload `PeriodCategory` (JSON)
- `GET CompanyService_GetFeaturesStatus`
- `POST CompanyService_GetFeaturesStatus`
- `GET CompanyService_GetPathAdmin`
- `POST CompanyService_GetPathAdmin`
- `POST CompanyService_UpdatePathAdmin` — payload `PathAdmin` (JSON)
- `POST CompanyService_RoundDecimal` — payload `DecimalData` (JSON)
- `POST CompanyService_GetItemPrice` — payload `ItemPriceParams` (JSON)
- `POST CompanyService_GetAdvancedGLAccount` — payload `AdvancedGLAccountParams` (JSON)
- `POST CompanyService_LogLoginAction` — payload `UserAccessLog` (JSON)
- `POST CompanyService_LogLogoffAction` — logs a logoff action (note: the reference's description text for this operation is mislabeled/copy-pasted from another method; treat the payload as the logoff/access-log input and confirm against live `$metadata`)

(4) **Read example:**
```
GET /b1s/v1/CompanyService_GetCompanyInfo
```
CLI (offline op inspection):
```
sapb1 ops CompanyService
```
fields: query live `$metadata` — `GetCompanyInfo` returns the `CompanyInfo` complex type and `GetAdminInfo` the `AdminInfo` complex type; individual field names are not enumerated in the HTML reference.

---

## CountiesService

(1) **Purpose:** Retrieve the list of counties (localization address administration). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST CountiesService_GetCountyList`

---

## CountriesService

(1) **Purpose:** Retrieve the list of countries defined in the system. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST CountriesService_GetCountryList`

---

## CreditLinesService

(1) **Purpose:** Retrieve a credit line and the list of valid credit lines. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST CreditLinesService_GetCreditLine`
- `POST CreditLinesService_GetValidCreditLineList` — (note: the reference's description text for this operation is mislabeled/copy-pasted from `GetApprovalTemplates`; verify the real payload against live `$metadata`)

---

## CycleCountDeterminationsService

(1) **Purpose:** Retrieve the list of cycle-count determination rules. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST CycleCountDeterminationsService_GetList`

---

## DepartmentsService

(1) **Purpose:** Retrieve the list of company departments. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST DepartmentsService_GetDepartmentList`

---

## DeterminationCriteriasService

(1) **Purpose:** Retrieve the list of determination criteria (rule sets used by SAP B1 determination logic). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST DeterminationCriteriasService_GetList`

---

## DNFCodeSetupService

(1) **Purpose:** Retrieve the DNF (official/reporting) code setup list. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST DNFCodeSetupService_GetDNFCodeSetupList`

---

## ElectronicCommunicationActionService

(1) **Purpose:** Drive a single Electronic Communication (ECM) action — get it, update its status, confirm successful communication, or report an error and continue/stop. (inferred; grounded by payload types below)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ElectronicCommunicationActionService_GetAction` — payload `ECMCodeParams` (JSON)
- `POST ElectronicCommunicationActionService_UpdateAction` — payload `ECMActionStatusData` (JSON)
- `POST ElectronicCommunicationActionService_ConfirmSuccessOfCommunication` — payload `ECMCodeParams` (JSON)
- `POST ElectronicCommunicationActionService_ReportErrorAndContinue` — payload `ECMCodeParams` (JSON)
- `POST ElectronicCommunicationActionService_ReportErrorAndStop` — payload `ECMCodeParams` (JSON)

---

## ElectronicCommunicationActionsService

(1) **Purpose:** Full CRUD plus document-linked lookup and logging for Electronic Communication (ECM) actions. (inferred; grounded by payload types below)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ElectronicCommunicationActionsService_GetEcmAction` — payload `EcmActionParams` (JSON)
- `POST ElectronicCommunicationActionsService_AddEcmAction` — payload `EcmAction` (JSON)
- `POST ElectronicCommunicationActionsService_UpdateEcmAction` — payload `EcmAction` (JSON)
- `POST ElectronicCommunicationActionsService_DeleteEcmAction` — payload `EcmAction` (JSON)
- `POST ElectronicCommunicationActionsService_GetEcmActionByDoc` — payload `EcmActionDocParams` (JSON)
- `POST ElectronicCommunicationActionsService_GetEcmActionLogList` — payload `EcmAction` (JSON)
- `POST ElectronicCommunicationActionsService_GetEcmActionLog` — payload `EcmActionLogParams` (JSON)
- `POST ElectronicCommunicationActionsService_AddEcmActionLog` — payload `EcmActionLog` (JSON)

---

## ElectronicFileFormatsService

(1) **Purpose:** Retrieve the list of electronic file formats (EFM). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ElectronicFileFormatsService_GetElectronicFileFormatList`

---

## EmailGroupsService

(1) **Purpose:** Retrieve the list of email groups. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST EmailGroupsService_GetList`

---

## EmploymentCategoryService

(1) **Purpose:** Retrieve the list of employment categories (HR administration). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST EmploymentCategoryService_GetEmploymentCategoryList`

---

## EnhancedDiscountGroupsService

(1) **Purpose:** Retrieve the list of enhanced discount groups. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST EnhancedDiscountGroupsService_GetList`

---

## ExceptionalEventService

(1) **Purpose:** Retrieve the list of exceptional events (localization reporting). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ExceptionalEventService_GetExceptionalEventList`

---

## ExtendedTranslationsService

(1) **Purpose:** Retrieve the list of extended (multi-language) translations. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ExtendedTranslationsService_GetExtendedTranslationList`

---

## ExternalCallsService

(1) **Purpose:** Send, update, and retrieve external (integration) calls. (inferred; grounded by payload types below)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ExternalCallsService_SendCall` — payload `ExternalCall` (JSON)
- `POST ExternalCallsService_UpdateCall` — payload `ExternalCall` (JSON)
- `POST ExternalCallsService_GetCall` — payload `ExternalCallParams` (JSON)

---

## ExternalReconciliationsService

(1) **Purpose:** Perform, retrieve, cancel, and list external (bank/account) reconciliations. (inferred; grounded by payload types below)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST ExternalReconciliationsService_Reconcile` — payload `ExternalReconciliation` (JSON)
- `POST ExternalReconciliationsService_GetReconciliation`
- `POST ExternalReconciliationsService_CancelReconciliation` — payload `ExternalReconciliationParams` (JSON)
- `POST ExternalReconciliationsService_GetReconciliationList`

---

## GovPayCodesService

(1) **Purpose:** Retrieve the list of government payment codes (localization). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST GovPayCodesService_GetList`

---

## GTIsService

(1) **Purpose:** Import GTI (global/tax indexer) data. (inferred; grounded by payload type below)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST GTIsService_Import` — payload `GTIParams` (JSON)

---

## IndiaHsnService

(1) **Purpose:** Retrieve the list of India HSN (Harmonized System Nomenclature) codes (localization). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST IndiaHsnService_GetList`

---

## InternalReconciliationsService

(1) **Purpose:** Work with internal reconciliations — fetch open transactions, cancel a reconciliation, and request/approve a cancellation. (inferred; grounded by payload types below)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST InternalReconciliationsService_GetOpenTransactions` — payload `InternalReconciliationOpenTransParams` (JSON)
- `POST InternalReconciliationsService_Cancel` — payload `InternalReconciliationParams` (JSON)
- `POST InternalReconciliationsService_RequestApproveCancellation` — payload `InternalReconciliationParams` (JSON)

---

## IntrastatConfigurationService

(1) **Purpose:** Retrieve the Intrastat configuration list (EU trade reporting). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST IntrastatConfigurationService_GetList`

---

## KPIsService

(1) **Purpose:** Retrieve the list of KPIs (key performance indicators). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST KPIsService_GetList`

---

## LicenseService

(1) **Purpose:** Retrieve the SAP Business One installation number (licensing). (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST LicenseService_GetInstallationNumber`

---

## MaterialGroupsService

(1) **Purpose:** Retrieve the list of material groups. (inferred)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST MaterialGroupsService_GetMaterialGroupList`

---

## MaterialRevaluationFIFOService

(1) **Purpose:** Retrieve material revaluation data under FIFO valuation. (inferred; grounded by payload type below)
(2) **Type:** function/action Service
(3) **Operations:**
- `POST MaterialRevaluationFIFOService_GetMaterialRevaluationFIFO` — payload `MaterialRevaluationFIFOParams` (JSON)

---

## Coverage

40 of 40 services in `administration-setup-1` documented. Read/GET-capable
services: `AccrualTypesService`, `AttributeGroupsService`, `CompanyService` (3).
All other services are POST-only function/action services. No field names were
invented — the HTML reference exposes typed JSON payload/return-type names
(reproduced above) but no `$metadata`-style field enumerations, so field detail
must be pulled from the live `$metadata`.
