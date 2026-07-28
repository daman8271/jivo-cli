# SAP Business One Service Layer — Administration & Setup (part 2)

Reference for the 40 services in the `administration-setup-2` domain.

**Domain shape (important):** every service in this domain is an **RPC-style function/action Service** — each one exposes only `POST` operations of the form `POST /b1s/v1/<Service>_<Method>` (the API-reference HTML shows them under `/b1s/v1/`; both versions expose the same operations). **None of these 40 services has a `GET` operation, so there are no queryable OData read-entities in this domain** and no `$select`/`$filter` field examples apply. Several services do *read* data, but they do so through `POST` methods (typically `..._GetList` / `..._Get<Thing>List`) whose response shape is defined by a request-payload param object, not by a queryable entity set. Where a method takes a payload, the API reference names the payload type (shown below as `payload: <Type>`); the field structure of those payload/response types is not enumerated in the API reference — **query the live `$metadata` for exact field names** when you need them.

Because there is no readable entity here, the `sapb1 query <Entity>` tool form does not apply. These are invoked as raw POST calls, e.g.:

```
POST https://<host>:50000/b1s/v1/MessagesService_GetInbox
Content-Type: application/json

{ ...payload... }
```

- Services documented: **40**
- Read-entities (GET): **0**

Operation names, methods, and payload type names below are copied verbatim from `catalog/services.json` and `raw/service-layer-api-reference.html`. Nothing is invented.

---

## MaterialRevaluationSNBService

- **Purpose:** Retrieve the list of serial/batch-managed (SNB) material revaluation data, per the `MaterialRevaluationSNBParam` query payload. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST MaterialRevaluationSNBService_GetList` — payload: `MaterialRevaluationSNBParam`

---

## MessagesService

- **Purpose:** Manage the inbox and outbox messages, and send messages (grounded in the API reference: "this service enables to manage the inbox and outbox messages, and to send messages").
- **Type:** function/action Service
- **Operations:**
  - `POST MessagesService_GetInbox`
  - `POST MessagesService_GetOutbox`
  - `POST MessagesService_GetSentMessages`

Note: message *creation* is done via the `Messages` entity (`POST Messages`), which the reference notes is the modern replacement for the old `MessagesService_SendMessage` method.

---

## MobileAppService

- **Purpose:** Read and update settings and data consumed by the SAP Business One mobile apps — server time, technician schedulings/settings, employee full names, Sales-app settings, and Service-app report content. (inferred from operation names/payloads)
- **Type:** function/action Service
- **Operations:**
  - `POST MobileAppService_GetCurrentServerDateTime`
  - `POST MobileAppService_GetDppChangeParams` — payload: `DppChangeParams`
  - `POST MobileAppService_GetTechnicianSchedulings` — payload: `TechnicianSchedulingsParams`
  - `POST MobileAppService_GetEmployeeFullNames` — payload: `EmployeeFullNamesParamsCollection`
  - `POST MobileAppService_GetTechnicianSettings` — payload: `TechnicianSettingsParams`
  - `POST MobileAppService_UpdateTechnicianSettings` — payload: `TechnicianSettings`
  - `POST MobileAppService_GetTechnicianSettingsGroup`
  - `POST MobileAppService_UpdateTechnicianSettingsGroup` — payload: `TechnicianSettingsGroup`
  - `POST MobileAppService_GetSalesAppSetting`
  - `POST MobileAppService_UpdateSalesAppSetting` — payload: `SalesAppSetting`
  - `POST MobileAppService_GetServiceAppReportContent` — payload: `ServiceAppReportParams`
  - `POST MobileAppService_UpdateServiceAppReportContent` — payload: `ServiceAppReportParams,ServiceAppReportContent`
  - `POST MobileAppService_GetServiceAppReport` — payload: `ServiceAppReportParams`
  - `POST MobileAppService_UpdateServiceAppReport` — payload: `ServiceAppReport`

---

## NatureOfAssesseesService

- **Purpose:** Retrieve the list of "Nature of Assessee" setup values (India-localization TDS/withholding-tax classification). (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST NatureOfAssesseesService_GetNatureOfAssesseeList`

---

## NCMCodesSetupService

- **Purpose:** Retrieve the list of NCM (Nomenclatura Comum do Mercosul) code setup entries used in Brazil localization. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST NCMCodesSetupService_GetNCMCodeSetupList`

---

## NFModelsService

- **Purpose:** Retrieve the list of Nota Fiscal (NF) models used in Brazil localization. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST NFModelsService_GetList`

---

## PredefinedTextsService

- **Purpose:** Retrieve the list of predefined texts (reusable boilerplate text snippets configured in the company). (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST PredefinedTextsService_GetPredefinedTextList`

---

## QRCodeService

- **Purpose:** Add or update a QR code. (inferred from operation name)
- **Type:** function/action Service
- **Operations:**
  - `POST QRCodeService_AddOrUpdateQRCode`

---

## QueryService

- **Purpose:** Run OData row-level-filter queries. Per the API reference, Service Layer exposes this query service to fully comply with OData, implemented on the `$crossjoin` capability by separating the QueryPath and QueryOption in the query URL.
- **Type:** function/action Service
- **Operations:**
  - `POST QueryService_PostQuery`

---

## RecurringTransactionService

- **Purpose:** Manage recurring (postings-template) transactions — list available ones, retrieve, execute, and delete them. (grounded in operation names/payloads)
- **Type:** function/action Service
- **Operations:**
  - `POST RecurringTransactionService_GetAvailableRecurringTransactions`
  - `POST RecurringTransactionService_DeleteRecurringTransactions` — payload: `RclRecurringTransactionParamsCollection`
  - `POST RecurringTransactionService_GetRecurringTransaction` — payload: `RclRecurringTransactionParams`
  - `POST RecurringTransactionService_ExecuteRecurringTransactions` — payload: `RclRecurringTransactionParamsCollection,RclRecurringExecutionParams`

---

## ReportFilterService

- **Purpose:** Retrieve the tax report filter list, per the `TaxReportFilterParams` payload. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST ReportFilterService_GetTaxReportFilterList` — payload: `TaxReportFilterParams`

---

## ReportLayoutsService

- **Purpose:** Manage Crystal/print report layouts — add/get/delete layouts, get and set the default report and default layout, update printer and language settings, and add/remove layouts to/from menus. (grounded in operation names/payloads)
- **Type:** function/action Service
- **Operations:**
  - `POST ReportLayoutsService_SetDefaultReport` — payload: `DefaultReportParams`
  - `POST ReportLayoutsService_GetDefaultReport` — payload: `ReportParams`
  - `POST ReportLayoutsService_AddReportLayout` — payload: `ReportLayout`
  - `POST ReportLayoutsService_UpdatePrinterSettings` — payload: `ReportLayout`
  - `POST ReportLayoutsService_DeleteReportLayout` — payload: `ReportLayoutParams`
  - `POST ReportLayoutsService_GetReportLayout` — payload: `ReportLayoutParams`
  - `POST ReportLayoutsService_GetDefaultReportLayout` — payload: `ReportParams`
  - `POST ReportLayoutsService_GetReportLayoutList` — payload: `ReportParams`
  - `POST ReportLayoutsService_UpdateLanguageReport` — payload: `ReportLayout`
  - `POST ReportLayoutsService_AddReportLayoutToMenu` — payload: `ReportLayout,ReportInputParams`
  - `POST ReportLayoutsService_DeleteReportLayoutAndMenu` — payload: `ReportLayoutParams`

---

## ReportTypesService

- **Purpose:** Retrieve the list of report types. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST ReportTypesService_GetReportTypeList`

---

## RetornoCodesService

- **Purpose:** Retrieve the list of Retorno (bank-return) codes used in Brazil localization. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST RetornoCodesService_GetList`

---

## RouteStagesService

- **Purpose:** Retrieve the list of route stages. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST RouteStagesService_GetList`

---

## SBOBobService

- **Purpose:** SBO "business-object bridge" utility service — read/set system permissions, get system and local currency, currency and index rates, compute a due date for a business partner, and format money to string. (grounded in operation names/payloads)
- **Type:** function/action Service
- **Operations:**
  - `POST SBOBobService_GetSystemPermission` — payload: `UserCode,PermissionID`
  - `POST SBOBobService_GetSystemCurrency`
  - `POST SBOBobService_GetDueDate` — payload: `CardCode,RefDate`
  - `POST SBOBobService_GetLocalCurrency`
  - `POST SBOBobService_GetCurrencyRate` — payload: `Currency,Date`
  - `POST SBOBobService_GetIndexRate` — payload: `Index,Date`
  - `POST SBOBobService_Format_MoneyToString` — payload: `InMoney,InPrecision`
  - `POST SBOBobService_SetCurrencyRate` — payload: `RateDate,Currency,Rate`
  - `POST SBOBobService_SetSystemPermission` — payload: `UserCode,PermissionID and Permission`

---

## SectionsService

- **Purpose:** Retrieve the list of sections. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST SectionsService_GetSectionList`

---

## SelfCreditMemoService

- **Purpose:** Handle self-billing credit memos — get approval templates, handle an approval request, and cancel a document (`Cancel2` allows changing some properties before cancelling one document). (grounded in operation descriptions)
- **Type:** function/action Service
- **Operations:**
  - `POST SelfCreditMemoService_GetApprovalTemplates` — payload: `Document`
  - `POST SelfCreditMemoService_HandleApprovalRequest`
  - `POST SelfCreditMemoService_Cancel2` — payload: `Document`

---

## SeriesService

- **Purpose:** Manage document numbering series — add/update/remove series, attach/unattach a series to a document, set default series (per user / current user / all users), rename document menu names, and manage the parallel set of electronic series. (grounded in operation names/payloads)
- **Type:** function/action Service
- **Operations:**
  - `POST SeriesService_AddSeries` — payload: `Series`
  - `POST SeriesService_RemoveSeries` — payload: `SeriesParams`
  - `POST SeriesService_AttachSeriesToDocument` — payload: `DocumentSeriesParams`
  - `POST SeriesService_UnattachSeriesFromDocument` — payload: `DocumentSeriesParams`
  - `POST SeriesService_SetDefaultSeriesForAllUsers` — payload: `DocumentSeriesParams`
  - `POST SeriesService_SetDefaultSeriesForCurrentUser` — payload: `DocumentSeriesParams`
  - `POST SeriesService_SetDefaultSeriesForUser` — payload: `DocumentSeriesUserParams`
  - `POST SeriesService_UpdateSeries` — payload: `Series`
  - `POST SeriesService_GetDefaultSeries` — payload: `DocumentTypeParams`
  - `POST SeriesService_GetDocumentSeries` — payload: `DocumentTypeParams`
  - `POST SeriesService_GetSeries` — payload: `SeriesParams`
  - `POST SeriesService_GetDocumentChangedMenuName` — payload: `DocumentTypeParams`
  - `POST SeriesService_ChangeDocumentMenuName` — payload: `DocumentChangeMenuName`
  - `POST SeriesService_GetElectronicSeries` — payload: `ElectronicSeriesParams`
  - `POST SeriesService_AddElectronicSeries` — payload: `ElectronicSeries`
  - `POST SeriesService_RemoveElectronicSeries` — payload: `ElectronicSeriesParams`
  - `POST SeriesService_UpdateElectronicSeries` — payload: `ElectronicSeries`
  - `POST SeriesService_GetDefaultElectronicSeries` — payload: `SeriesParams`
  - `POST SeriesService_SetDefaultElectronicSeries` — payload: `DefaultElectronicSeriesParams`

---

## ServiceGroupsService

- **Purpose:** Retrieve the list of service groups. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST ServiceGroupsService_GetServiceGroupList`

---

## ShortLinkMappingsService

- **Purpose:** Manipulate short-link mappings; the exposed operation batch-deletes mappings. (grounded: "This entity enables you to manipulate 'ShortLinkMappingsService'.")
- **Type:** function/action Service
- **Operations:**
  - `POST ShortLinkMappingsService_BatchDelete`

---

## StatesService

- **Purpose:** Retrieve the list of states/provinces defined in the company. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST StatesService_GetStateList`

---

## TargetGroupsService

- **Purpose:** Retrieve the list of target groups. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST TargetGroupsService_GetList`

---

## TerminationReasonService

- **Purpose:** Retrieve the list of termination reasons (HR / employee master data). (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST TerminationReasonService_GetList`

---

## TrackingNotesService

- **Purpose:** Retrieve the list of tracking notes. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST TrackingNotesService_GetList`

---

## TransactionCodesService

- **Purpose:** Retrieve the list of transaction codes (journal-entry transaction-code setup). (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST TransactionCodesService_GetList`

---

## TSRExceptionalEventService

- **Purpose:** Retrieve the list of TSR (tax/statutory reporting) exceptional events. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST TSRExceptionalEventService_GetList`

---

## UserMenuService

- **Purpose:** Read and update the per-user favorites menu — the current user's menu and, by parameter, any specified user's menu. (grounded in operation names/payloads)
- **Type:** function/action Service
- **Operations:**
  - `POST UserMenuService_GetCurrentUserMenu`
  - `POST UserMenuService_UpdateCurrentUserMenu` — payload: `Collection(UserMenuItem)`
  - `POST UserMenuService_GetUserMenu` — payload: `UserMenuParams`
  - `POST UserMenuService_UpdateUserMenu` — payload: `UserMenuParams`

---

## UsersService

- **Purpose:** Get the current (logged-in) user's information. (grounded: "get the current user information")
- **Type:** function/action Service
- **Operations:**
  - `POST UsersService_GetCurrentUser`

---

## ValueMappingService

- **Purpose:** Map values between the Business One universe and third-party value sets — get the B1 value mapped to a specific third-party value, get all third-party values for a specific B1 value, and remove one third-party value from a B1 value's mapping. (grounded in operation descriptions)
- **Type:** function/action Service
- **Operations:**
  - `POST ValueMappingService_GetMappedB1Value` — payload: `VM_B1ValuesData`
  - `POST ValueMappingService_GetThirdPartyValuesForB1Value` — payload: `VM_B1ValuesData`
  - `POST ValueMappingService_RemoveMappedValue` — payload: `VM_ThirdPartyValuesData`

---

## WebClientBookmarkTileService

- **Purpose:** Retrieve the list of Web Client bookmark tiles. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientBookmarkTileService_GetList`

---

## WebClientDashboardService

- **Purpose:** Retrieve the list of Web Client dashboards. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientDashboardService_GetList`

---

## WebClientFormSettingService

- **Purpose:** Retrieve the list of Web Client form settings. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientFormSettingService_GetList`

---

## WebClientLaunchpadService

- **Purpose:** Retrieve the list of Web Client launchpad configurations. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientLaunchpadService_GetList`

---

## WebClientListviewFilterService

- **Purpose:** Retrieve the list of Web Client list-view filters. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientListviewFilterService_GetList`

---

## WebClientNotificationService

- **Purpose:** Retrieve the list of Web Client notifications. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientNotificationService_GetList`

---

## WebClientPreferenceService

- **Purpose:** Retrieve the list of Web Client user preferences. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientPreferenceService_GetList`

---

## WebClientVariantGroupService

- **Purpose:** Retrieve the list of Web Client variant groups. (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientVariantGroupService_GetList`

---

## WebClientVariantService

- **Purpose:** Retrieve the list of Web Client variants (saved report/list variants). (inferred)
- **Type:** function/action Service
- **Operations:**
  - `POST WebClientVariantService_GetList`

---

## WorkflowTaskService

- **Purpose:** Work with workflow approval tasks — get the approval-task list and mark a task complete. (grounded in operation names/payloads)
- **Type:** function/action Service
- **Operations:**
  - `POST WorkflowTaskService_Complete` — payload: `WorkflowTaskCompleteParams`
  - `POST WorkflowTaskService_GetApprovalTaskList` — payload: `WorkflowApprovalTaskListParams`
