# SAP Business One Service Layer — System & Other (part 1)

Reference for the services in the `system-other-1` domain of the SAP Business One Service Layer. This domain groups the session-management calls (`Login`/`Logout`/`B1Sessions`) together with a broad set of setup / master-data entities — geography and localization tables, alerts and messages, Brazil fiscal indexers, India HSN, KPIs, cockpits, inventory determination setups, and more.

**Two kinds of resource:**
- **readable ENTITY** — an OData entity set supporting `GET`/`GET(id)` plus (usually) `POST`/`PATCH`/`DELETE`. Queryable with `$select`/`$filter`/`$top`/`$orderby`/`$skip`. 36 of these here.
- **function/action Service** — an endpoint that wraps a named action (typically `POST`). No queryable field set. 3 of these here (`Login`, `Logout`, `B1Sessions` — the last is a placeholder with no operations).

**Conventions in this doc**
- Operations are copied verbatim from `catalog/services.json` (never invented).
- Field names come from the real `$select` / example-payload text in the API-reference HTML (never invented). Where the HTML gives no fields, the doc says "query live `$metadata`".
- The one-line purpose is tagged `(inferred)` when it comes from the resource name / domain knowledge rather than a specific HTML sentence — for many of these entities the HTML's own description is only the generic "This entity enables you to manipulate 'X'.".
- Examples use base path `/b1s/v1` (the CLI default). The HTML shows the same routes under `/b1s/v2`; both are valid.

> **Note:** The domain's service list contains an `Entities:` separator label between `Logout` and `AdditionalExpenses`; it is not a service and is not documented below. That leaves **39 real services**.

---

## Login

1. **Purpose:** Log in to the Service Layer with the specified credentials, opening a session (returns a `B1SESSION` cookie).
2. **Type:** function/action Service
3. **Operations:**
   - `POST Login`
4. **Example payload fields (real, from HTML):** `CompanyDB`, `UserName`, `Password`
   - `POST /b1s/v1/Login` with body `{ "CompanyDB": "SBODEMOUS", "UserName": "manager", "Password": "1234" }`

## Logout

1. **Purpose:** Log out and close the current Service Layer session.
2. **Type:** function/action Service
3. **Operations:**
   - `POST Logout`

## B1Sessions

1. **Purpose:** Placeholder entity that exists only to let the Service Layer work with WCF; per the HTML it "has no practical usage and does not support CURD [CRUD]".
2. **Type:** function/action Service (no operations exposed in the catalog)
3. **Operations:** _(none)_

## AdditionalExpenses

1. **Purpose:** Manage additional expenses for transporting freight or delivering services, such as delivery fees and tax deposits.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET AdditionalExpenses(id)`
   - `GET AdditionalExpenses`
   - `POST AdditionalExpenses`
   - `PATCH AdditionalExpenses(id)`
   - `DELETE AdditionalExpenses(id)`
4. **Fields (real, from HTML):** `Name`, `ExpenseAccount`, `RevenuesAccount`, `FixedAmountExpenses`, `FixedAmountRevenues`, `DistributionMethod`
   - `GET /b1s/v1/AdditionalExpenses?$select=Name,ExpenseAccount,RevenuesAccount&$top=20`
   - `sapb1 query AdditionalExpenses --select Name,ExpenseAccount,RevenuesAccount --top 20`

## AlertManagements

1. **Purpose:** Manage saved-query alerts — the message that fires (on a schedule / frequency) to a set of internal recipients. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET AlertManagements(id)`
   - `GET AlertManagements`
   - `POST AlertManagements`
   - `PATCH AlertManagements(id)`
   - `DELETE AlertManagements(id)`
   - `POST AlertManagements(id)/GetAlertManagement`
   - `POST AlertManagements(id)/GetAlertManagementList`
4. **Fields (real, from HTML):** `Code`, `Name`, `Type`, `Priority`, `Active`, `QueryID`
   - `GET /b1s/v1/AlertManagements?$select=Code,Name,Priority&$filter=Active eq 'tYES'&$top=20`
   - `sapb1 query AlertManagements --select Code,Name,Priority --filter "Active eq 'tYES'" --top 20`

## AlternateCatNum

1. **Purpose:** Manage the alternative catalog numbers in the Business Partners module (a business partner's own item/substitute numbers).
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET AlternateCatNum(id)`
   - `GET AlternateCatNum`
   - `POST AlternateCatNum`
   - `PATCH AlternateCatNum(id)`
   - `DELETE AlternateCatNum(id)`
4. **Fields (real, from HTML):** `ItemCode`, `CardCode`, `Substitute`, `DisplayBPCatalogNumber` — composite key `AlternateCatNum(ItemCode='...',CardCode='...',Substitute='...')`
   - `GET /b1s/v1/AlternateCatNum?$select=ItemCode,CardCode,Substitute&$filter=CardCode eq 'C20000'&$top=20`
   - `sapb1 query AlternateCatNum --select ItemCode,CardCode,Substitute --filter "CardCode eq 'C20000'" --top 20`

## BPPriorities

1. **Purpose:** Manage business-partner priority codes and their descriptions. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BPPriorities(id)`
   - `GET BPPriorities`
   - `POST BPPriorities`
   - `PATCH BPPriorities(id)`
   - `DELETE BPPriorities(id)`
4. **Fields (real, from HTML):** `Priority`, `PriorityDescription`
   - `GET /b1s/v1/BPPriorities?$select=Priority,PriorityDescription&$top=20`
   - `sapb1 query BPPriorities --select Priority,PriorityDescription --top 20`

## BrazilBeverageIndexers

1. **Purpose:** Manage Brazil beverage-group fiscal indexer codes (localization tax setup). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BrazilBeverageIndexers(id)`
   - `GET BrazilBeverageIndexers`
   - `POST BrazilBeverageIndexers`
   - `DELETE BrazilBeverageIndexers(id)`
4. **Fields (real, from HTML):** `BeverageGroupCode`, `BeverageTableCode`, `BeverageCommercialBrandCode`
   - `GET /b1s/v1/BrazilBeverageIndexers?$select=BeverageGroupCode,BeverageTableCode,BeverageCommercialBrandCode&$top=20`
   - `sapb1 query BrazilBeverageIndexers --select BeverageGroupCode,BeverageTableCode,BeverageCommercialBrandCode --top 20`

## BrazilFuelIndexers

1. **Purpose:** Manage Brazil fuel fiscal indexer codes (localization tax setup). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BrazilFuelIndexers(id)`
   - `GET BrazilFuelIndexers`
   - `POST BrazilFuelIndexers`
   - `DELETE BrazilFuelIndexers(id)`
4. **Fields (real, from HTML):** `FuelID`, `FuelGroupCode`, `FuelCode`, `Description`
   - `GET /b1s/v1/BrazilFuelIndexers?$select=FuelID,FuelGroupCode,FuelCode&$top=20`
   - `sapb1 query BrazilFuelIndexers --select FuelID,FuelGroupCode,FuelCode --top 20`

## BrazilMultiIndexers

1. **Purpose:** Manage Brazil multi-reference fiscal indexers (indexers built from other indexer references). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BrazilMultiIndexers(id)`
   - `GET BrazilMultiIndexers`
   - `POST BrazilMultiIndexers`
   - `DELETE BrazilMultiIndexers(id)`
   - `POST BrazilMultiIndexers(id)/GetIndexerTypeList`
4. **Fields (real, from HTML):** `ID`, `IndexerType`, `Code`, `Description`, `FirstRefIndexerCode`, `SecondRefIndexerCode`
   - `GET /b1s/v1/BrazilMultiIndexers?$select=ID,IndexerType,Code,Description&$top=20`
   - `sapb1 query BrazilMultiIndexers --select ID,IndexerType,Code,Description --top 20`

## BrazilNumericIndexers

1. **Purpose:** Manage Brazil numeric-value fiscal indexers. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BrazilNumericIndexers(id)`
   - `GET BrazilNumericIndexers`
   - `POST BrazilNumericIndexers`
   - `DELETE BrazilNumericIndexers(id)`
   - `POST BrazilNumericIndexers(id)/GetIndexerTypeList`
4. **Fields (real, from HTML):** `IndexerType`, `Code`, `Description`
   - `GET /b1s/v1/BrazilNumericIndexers?$select=IndexerType,Code,Description&$top=20`
   - `sapb1 query BrazilNumericIndexers --select IndexerType,Code,Description --top 20`

## BrazilStringIndexers

1. **Purpose:** Manage Brazil string-value fiscal indexers. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BrazilStringIndexers(id)`
   - `GET BrazilStringIndexers`
   - `POST BrazilStringIndexers`
   - `DELETE BrazilStringIndexers(id)`
   - `POST BrazilStringIndexers(id)/GetIndexerTypeList`
4. **Fields (real, from HTML):** `IndexerType`, `Code`, `Description`
   - `GET /b1s/v1/BrazilStringIndexers?$select=IndexerType,Code,Description&$top=20`
   - `sapb1 query BrazilStringIndexers --select IndexerType,Code,Description --top 20`

## BusinessPlaces

1. **Purpose:** Manage a company's business locations (business places / branches).
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BusinessPlaces(id)`
   - `GET BusinessPlaces`
   - `POST BusinessPlaces`
   - `PATCH BusinessPlaces(id)`
   - `DELETE BusinessPlaces(id)`
4. **Fields (real, from HTML):** `BPLID`, `BPLName`, `BPLNameForeign`, `Address`, `VATRegNum`, `Industry`
   - `GET /b1s/v1/BusinessPlaces?$select=BPLID,BPLName,VATRegNum&$top=20`
   - `sapb1 query BusinessPlaces --select BPLID,BPLName,VATRegNum --top 20`

## CashDiscounts

1. **Purpose:** Manage cash-discount schemes (discount lines granted for early payment by number of days). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET CashDiscounts(id)`
   - `GET CashDiscounts`
   - `POST CashDiscounts`
   - `PATCH CashDiscounts(id)`
   - `DELETE CashDiscounts(id)`
4. **Fields (real, from HTML):** `Code`, `Name`, `ByDate`, and per-line `DiscountLines` (`LineId`, `NumOfDays`, `Discount`)
   - `GET /b1s/v1/CashDiscounts?$select=Code,Name,ByDate&$top=20`
   - `sapb1 query CashDiscounts --select Code,Name,ByDate --top 20`

## ClosingDateProcedure

1. **Purpose:** Read the period closing-date procedure definitions (baseline date and closing-date codes). (inferred)
2. **Type:** readable ENTITY (read-only — only `GET`/`GET(id)` in the catalog)
3. **Operations:**
   - `GET ClosingDateProcedure(id)`
   - `GET ClosingDateProcedure`
4. **Fields (real, from HTML):** `ClosingDateNum`, `ClosingDateCode`, `BaselineDate`
   - `GET /b1s/v1/ClosingDateProcedure?$select=ClosingDateNum,ClosingDateCode,BaselineDate&$top=20`
   - `sapb1 query ClosingDateProcedure --select ClosingDateNum,ClosingDateCode,BaselineDate --top 20`

## Cockpits

1. **Purpose:** Manage user cockpit (dashboard/workbench) definitions. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Cockpits(id)`
   - `GET Cockpits`
   - `POST Cockpits`
   - `PATCH Cockpits(id)`
   - `DELETE Cockpits(id)`
4. **Fields (real, from HTML):** `AbsEntry`, `Code`, `Name`, `Description`, `CockpitType`, `UserSignature`
   - `GET /b1s/v1/Cockpits?$select=AbsEntry,Code,Name&$top=20`
   - `sapb1 query Cockpits --select AbsEntry,Code,Name --top 20`

## Counties

1. **Purpose:** Manage county/region records (county code, name, state, country and tax zone — used in localization). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Counties(id)`
   - `GET Counties`
   - `POST Counties`
   - `PATCH Counties(id)`
   - `DELETE Counties(id)`
4. **Fields (real, from HTML):** `AbsId`, `Code`, `Name`, `Country`, `State`, `TaxZone`
   - `GET /b1s/v1/Counties?$select=AbsId,Code,Name,Country&$filter=Country eq 'BR'&$top=20`
   - `sapb1 query Counties --select AbsId,Code,Name,Country --filter "Country eq 'BR'" --top 20`

## Countries

1. **Purpose:** Manage the settings of each country, such as country code, country name and address format.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Countries(id)`
   - `GET Countries`
   - `POST Countries`
   - `PATCH Countries(id)`
   - `DELETE Countries(id)`
4. **Fields (real, from HTML):** `Code`, `Name`, `CodeForReports`
   - `GET /b1s/v1/Countries?$select=Code,Name,CodeForReports&$top=50`
   - `sapb1 query Countries --select Code,Name,CodeForReports --top 50`

## CustomsDeclaration

1. **Purpose:** Manage customs declaration documents (customs broker / terminal, declaration number and dates). (inferred)
2. **Type:** readable ENTITY (no `DELETE` in the catalog)
3. **Operations:**
   - `GET CustomsDeclaration(id)`
   - `GET CustomsDeclaration`
   - `POST CustomsDeclaration`
   - `PATCH CustomsDeclaration(id)`
4. **Fields (real, from HTML):** `CCDNum`, `Date`, `CustomsBroker`, `CustomsTerminal`, `DocNum`, `SupplyNum`
   - `GET /b1s/v1/CustomsDeclaration?$select=CCDNum,Date,CustomsBroker&$top=20`
   - `sapb1 query CustomsDeclaration --select CCDNum,Date,CustomsBroker --top 20`

## CycleCountDeterminations

1. **Purpose:** Read/update cycle-count determination setups per warehouse (how often stock is counted). (inferred)
2. **Type:** readable ENTITY (no `POST`/`DELETE` in the catalog — read + `PATCH` only)
3. **Operations:**
   - `GET CycleCountDeterminations(id)`
   - `GET CycleCountDeterminations`
   - `PATCH CycleCountDeterminations(id)`
4. **Fields (real, from HTML):** `WarehouseCode`, `CycleBy`, `CycleCountDeterminationSetupCollection`
   - `GET /b1s/v1/CycleCountDeterminations?$select=WarehouseCode,CycleBy&$top=20`
   - `sapb1 query CycleCountDeterminations --select WarehouseCode,CycleBy --top 20`

## Departments

1. **Purpose:** Manage company department records (code, name, description). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Departments(id)`
   - `GET Departments`
   - `POST Departments`
   - `PATCH Departments(id)`
   - `DELETE Departments(id)`
4. **Fields (real, from HTML):** `Code`, `Name`, `Description`
   - `GET /b1s/v1/Departments?$select=Code,Name,Description&$top=50`
   - `sapb1 query Departments --select Code,Name,Description --top 50`

## DeterminationCriterias

1. **Purpose:** Read/update determination-criteria definitions (rule criteria, with an active flag). (inferred)
2. **Type:** readable ENTITY (no `POST`/`DELETE` in the catalog — read + `PATCH` only)
3. **Operations:**
   - `GET DeterminationCriterias(id)`
   - `GET DeterminationCriterias`
   - `PATCH DeterminationCriterias(id)`
4. **Fields (real, from HTML):** `DmcId`, `DeterminationCriteria`, `IsActive`
   - `GET /b1s/v1/DeterminationCriterias?$select=DmcId,DeterminationCriteria,IsActive&$top=20`
   - `sapb1 query DeterminationCriterias --select DmcId,DeterminationCriteria,IsActive --top 20`

## DynamicSystemStrings

1. **Purpose:** Modify a field name and format in the interface to match the terms used in your company (per-form/item/column string overrides).
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET DynamicSystemStrings(id)`
   - `GET DynamicSystemStrings`
   - `POST DynamicSystemStrings`
   - `PATCH DynamicSystemStrings(id)`
   - `DELETE DynamicSystemStrings(id)`
4. **Fields (real, from HTML):** `FormID`, `ItemID`, `ColumnID`, `ItemString` — composite key `DynamicSystemStrings(FormID='139',ItemID='230',ColumnID='-1')`
   - `GET /b1s/v1/DynamicSystemStrings?$select=FormID,ItemID,ColumnID,ItemString&$top=20`
   - `sapb1 query DynamicSystemStrings --select FormID,ItemID,ColumnID,ItemString --top 20`

## EmploymentCategorys

1. **Purpose:** Manage employment category codes used in HR employee records. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET EmploymentCategorys(id)`
   - `GET EmploymentCategorys`
   - `POST EmploymentCategorys`
   - `PATCH EmploymentCategorys(id)`
   - `DELETE EmploymentCategorys(id)`
4. **Fields (real, from HTML):** `Code`, `Description`
   - `GET /b1s/v1/EmploymentCategorys?$select=Code,Description&$top=50`
   - `sapb1 query EmploymentCategorys --select Code,Description --top 50`

## ExceptionalEvents

1. **Purpose:** Manage exceptional-event codes (e.g. localization/reporting event definitions). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET ExceptionalEvents(id)`
   - `GET ExceptionalEvents`
   - `POST ExceptionalEvents`
   - `PATCH ExceptionalEvents(id)`
   - `DELETE ExceptionalEvents(id)`
4. **Fields (real, from HTML):** `Code`, `Description`
   - `GET /b1s/v1/ExceptionalEvents?$select=Code,Description&$top=50`
   - `sapb1 query ExceptionalEvents --select Code,Description --top 50`

## FactoringIndicators

1. **Purpose:** Define keys that can be recorded in certain journal entries and used as selection criteria in various reports.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET FactoringIndicators(id)`
   - `GET FactoringIndicators`
   - `POST FactoringIndicators`
   - `PATCH FactoringIndicators(id)`
   - `DELETE FactoringIndicators(id)`
4. **Fields (real, from HTML):** `IndicatorCode`, `IndicatorName`
   - `GET /b1s/v1/FactoringIndicators?$select=IndicatorCode,IndicatorName&$top=50`
   - `sapb1 query FactoringIndicators --select IndicatorCode,IndicatorName --top 50`

## Holidays

1. **Purpose:** Manage holiday sets — the collection of holiday dates plus weekend rules used by calendars/scheduling. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Holidays(id)`
   - `GET Holidays`
   - `POST Holidays`
   - `PATCH Holidays(id)`
   - `DELETE Holidays(id)`
4. **Fields (real, from HTML):** `HolidayCode`, `WeekendFrom`, `WeekendTO`, `IgnoreWeekend`, and per-date `HolidayDates` (`StartDate`, `EndDate`, `Remarks`)
   - `GET /b1s/v1/Holidays?$select=HolidayCode,WeekendFrom,WeekendTO&$top=20`
   - `sapb1 query Holidays --select HolidayCode,WeekendFrom,WeekendTO --top 20`

## IndiaHsn

1. **Purpose:** Manage India HSN (Harmonized System of Nomenclature) codes used for GST classification. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET IndiaHsn(id)`
   - `GET IndiaHsn`
   - `POST IndiaHsn`
   - `PATCH IndiaHsn(id)`
   - `DELETE IndiaHsn(id)`
4. **Fields (real, from HTML):** `AbsEntry`, `Chapter`, `Heading`, `SubHeading`, `Description`
   - `GET /b1s/v1/IndiaHsn?$select=AbsEntry,Chapter,Heading,Description&$top=20`
   - `sapb1 query IndiaHsn --select AbsEntry,Chapter,Heading,Description --top 20`

## InternalReconciliations

1. **Purpose:** Create and read internal reconciliations that match open transactions against a business partner or G/L account. (inferred)
2. **Type:** readable ENTITY (read a single record + `POST`; no collection `GET`, `PATCH` or `DELETE` in the catalog)
3. **Operations:**
   - `GET InternalReconciliations(id)`
   - `POST InternalReconciliations`
4. **Fields (real, from HTML):** `ReconNum`, `ReconDate`, `CardOrAccount`, and per-row `InternalReconciliationOpenTransRows` (`ShortName`, `ReconcileAmount`, `CreditOrDebit`)
   - `GET /b1s/v1/InternalReconciliations(1)?$select=ReconNum,ReconDate,CardOrAccount`
   - `sapb1 get InternalReconciliations 1 --select ReconNum,ReconDate,CardOrAccount`

## KPIs

1. **Purpose:** Manage KPI definitions and their line values used in cockpits/dashboards. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET KPIs(id)`
   - `GET KPIs`
   - `POST KPIs`
   - `PATCH KPIs(id)`
   - `DELETE KPIs(id)`
4. **Fields (real, from HTML):** `KPICode`, `KPIName`, `KPIType`, and per-line `KPI_ItemLines` (`KPILineNumber`, `KPIValue1` …)
   - `GET /b1s/v1/KPIs?$select=KPICode,KPIName,KPIType&$top=20`
   - `sapb1 query KPIs --select KPICode,KPIName,KPIType --top 20`

## LegalData

1. **Purpose:** Manage legal/fiscal document data attached to source documents (fiscal number, series, printer details, tax detail lines). (inferred)
2. **Type:** readable ENTITY (no `DELETE` in the catalog)
3. **Operations:**
   - `GET LegalData(id)`
   - `GET LegalData`
   - `POST LegalData`
   - `PATCH LegalData(id)`
4. **Fields (real, from HTML):** `DocEntry`, `SourceObjectType`, `SourceObjectEntry`, `DocumentNumber`, `FiscalNumber`, `FiscalSeries`
   - `GET /b1s/v1/LegalData?$select=DocEntry,SourceObjectType,DocumentNumber&$top=20`
   - `sapb1 query LegalData --select DocEntry,SourceObjectType,DocumentNumber --top 20`

## LengthMeasures

1. **Purpose:** Define the length and width measure units that are used for item records.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET LengthMeasures(id)`
   - `GET LengthMeasures`
   - `POST LengthMeasures`
   - `PATCH LengthMeasures(id)`
   - `DELETE LengthMeasures(id)`
4. **Fields (real, from HTML):** `UnitCode`, `UnitDisplay`, `UnitName`, `UnitLengthinmm`
   - `GET /b1s/v1/LengthMeasures?$select=UnitCode,UnitDisplay,UnitName&$top=50`
   - `sapb1 query LengthMeasures --select UnitCode,UnitDisplay,UnitName --top 50`

## LocalEra

1. **Purpose:** Manage local-era (calendar era) definitions — era name, code and start date (localization, e.g. Japan/Thailand). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET LocalEra(id)`
   - `GET LocalEra`
   - `POST LocalEra`
   - `PATCH LocalEra(id)`
   - `DELETE LocalEra(id)`
4. **Fields (real, from HTML):** `Code`, `EraName`, `StartDate`
   - `GET /b1s/v1/LocalEra?$select=Code,EraName,StartDate&$top=50`
   - `sapb1 query LocalEra --select Code,EraName,StartDate --top 50`

## Manufacturers

1. **Purpose:** Define manufacturers used in the Item master data.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Manufacturers(id)`
   - `GET Manufacturers`
   - `POST Manufacturers`
   - `PATCH Manufacturers(id)`
   - `DELETE Manufacturers(id)`
4. **Fields (real, from HTML):** `Code`, `ManufacturerName`
   - `GET /b1s/v1/Manufacturers?$select=Code,ManufacturerName&$top=50`
   - `sapb1 query Manufacturers --select Code,ManufacturerName --top 50`

## MaterialRevaluation

1. **Purpose:** Update items' price (average or standard price only), revaluate the stock, and create journal entries accordingly.
2. **Type:** readable ENTITY (also supports `Cancel`/`Close` document actions)
3. **Operations:**
   - `GET MaterialRevaluation(id)`
   - `GET MaterialRevaluation`
   - `POST MaterialRevaluation`
   - `PATCH MaterialRevaluation(id)`
   - `DELETE MaterialRevaluation(id)`
   - `POST MaterialRevaluation(id)/Cancel`
   - `POST MaterialRevaluation(id)/Close`
4. **Fields (real, from HTML):** `DocNum`, `DocDate`, `Reference1`, `Comments`, and per-line `MaterialRevaluationLines` (`ItemCode`, `Price`, `RevalType`)
   - `GET /b1s/v1/MaterialRevaluation?$select=DocNum,DocDate,Reference1&$top=20`
   - `sapb1 query MaterialRevaluation --select DocNum,DocDate,Reference1 --top 20`

## Messages

1. **Purpose:** Manage messages; you can also query the combination of Inbox, Outbox and to-send messages via OData query options.
2. **Type:** readable ENTITY (no `PATCH`/`DELETE`; adds a `GetMessage` action)
3. **Operations:**
   - `GET Messages(id)`
   - `GET Messages`
   - `POST Messages`
   - `POST Messages(id)/GetMessage`
4. **Fields (real, from HTML):** `Code`, `User`, `Priority`, `Subject`, `Text`, and `RecipientCollection` (`UserCode`, `SendInternal`)
   - `GET /b1s/v1/Messages?$select=Code,User,Priority&$top=20`
   - `sapb1 query Messages --select Code,User,Priority --top 20`

## NatureOfAssessees

1. **Purpose:** Manage India TDS "Nature of Assessee" codes (assessee type classification). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET NatureOfAssessees(id)`
   - `GET NatureOfAssessees`
   - `POST NatureOfAssessees`
   - `PATCH NatureOfAssessees(id)`
   - `DELETE NatureOfAssessees(id)`
4. **Fields (real, from HTML):** `AbsEntry`, `Code`, `Description`, `AssesseeType`
   - `GET /b1s/v1/NatureOfAssessees?$select=AbsEntry,Code,Description&$top=50`
   - `sapb1 query NatureOfAssessees --select AbsEntry,Code,Description --top 50`

## NFModels

1. **Purpose:** Manage Brazil Nota Fiscal (NF) model definitions used in fiscal document numbering. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET NFModels(id)`
   - `GET NFModels`
   - `POST NFModels`
   - `PATCH NFModels(id)`
   - `DELETE NFModels(id)`
4. **Fields (real, from HTML):** `AbsEntry`, `NFMCode`, `NFMName`, `NFMDescription`
   - `GET /b1s/v1/NFModels?$select=AbsEntry,NFMName,NFMDescription&$top=50`
   - `sapb1 query NFModels --select AbsEntry,NFMName,NFMDescription --top 50`

## POSDailySummary

1. **Purpose:** Manage point-of-sale (fiscal printer) daily summary / Z-report records (counters and totalizers per equipment and date). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET POSDailySummary(id)`
   - `GET POSDailySummary`
   - `POST POSDailySummary`
   - `PATCH POSDailySummary(id)`
   - `DELETE POSDailySummary(id)`
4. **Fields (real, from HTML):** `AbsEntry`, `Date`, `EquipmentNo`, `OperationCounter`, `CounterPosition`, and per-line `POSTotalizerCollection` (`Code`, `Description`, `Number`)
   - `GET /b1s/v1/POSDailySummary?$select=AbsEntry,Date,EquipmentNo&$top=20`
   - `sapb1 query POSDailySummary --select AbsEntry,Date,EquipmentNo --top 20`
