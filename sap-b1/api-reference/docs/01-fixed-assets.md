# SAP Business One Service Layer — Fixed Assets Domain

Grounded reference for the **Fixed Assets** domain (23 services). Sourced from the
Service Layer catalog (`catalog/services.json`) and the official API-reference HTML
(`raw/service-layer-api-reference.html`). Operation names and field names are copied
verbatim from those sources — nothing here is invented.

**Two kinds of object in this domain:**

- **Readable entities** (11) — plain entity sets with full CRUD (`GET`, `POST`, `PATCH`,
  sometimes `DELETE`). These are queryable with `$select`/`$filter`/`$top` and with
  `sapb1 query`.
- **Function/action services** (12) — the `...Service` endpoints. They are RPC-style:
  each `POST` invokes a named method (`Cancel`, `GetList`, `GetAssetValuesList`, …) with a
  JSON params payload. Their `GetList` also has a `GET` form, but they are not general
  queryable entity sets.

The reference HTML labels every entity generically ("This entity enables you to
manipulate '<Name>'") and every service generically ("This API enables you to invoke the
interfaces defined on '<Name>'"). Where a one-line purpose goes beyond that generic text
it is marked **(inferred)**. Paths below use `/b1s/v1/`; the reference HTML shows the same
routes under `/b1s/v1/` — the version segment is a base-URL setting, not part of the name.

---

## AssetCapitalization

**Purpose:** Fixed-asset acquisition document — capitalizes an asset onto the books (posts acquisition cost/quantity). (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET AssetCapitalization(id)`
- `GET AssetCapitalization`
- `POST AssetCapitalization`
- `PATCH AssetCapitalization(id)`

**Real fields:** `DocEntry`, `DocNum`, `Series`, `AssetValueDate`, `DocumentDate`, `PostingDate` (line collection: `AssetDocumentLineCollection` → `AssetNumber`, `Quantity`, `TotalLC`)

**Example:**
```
GET /b1s/v1/AssetCapitalization?$select=DocEntry,DocNum,Series&$top=20
```
```
sapb1 query AssetCapitalization --select "DocEntry,DocNum,Series" --top 20
```

---

## AssetCapitalizationCreditMemo

**Purpose:** Credit memo against an asset capitalization — reverses/corrects an acquisition posting. (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET AssetCapitalizationCreditMemo(id)`
- `GET AssetCapitalizationCreditMemo`
- `POST AssetCapitalizationCreditMemo`
- `PATCH AssetCapitalizationCreditMemo(id)`

**Real fields:** `DocEntry`, `DocNum`, `Series`, `AssetValueDate`, `DocumentDate`, `PostingDate` (line collection: `AssetDocumentLineCollection` → `AssetNumber`, `Quantity`, `TotalLC`)

**Example:**
```
GET /b1s/v1/AssetCapitalizationCreditMemo?$select=DocEntry,DocNum,Series&$top=20
```
```
sapb1 query AssetCapitalizationCreditMemo --select "DocEntry,DocNum,Series" --top 20
```

---

## AssetClasses

**Purpose:** Asset-class master data — groups fixed assets and carries default depreciation-area/type and useful-life settings per class. (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET AssetClasses(id)`
- `GET AssetClasses`
- `POST AssetClasses`
- `PATCH AssetClasses(id)`
- `DELETE AssetClasses(id)`

**Real fields:** `Code`, `Description`, `AssetType` (child `AssetClassCollection` → `DepreciationAreaID`, `DepreciationTypeID`, `UseLife`, `AccountDetermination`, `ActiveStatus`, `LineNumber`)

**Example:**
```
GET /b1s/v1/AssetClasses?$select=Code,Description,AssetType&$top=20
```
```
sapb1 query AssetClasses --select "Code,Description,AssetType" --top 20
```

---

## AssetDepreciationGroups

**Purpose:** Asset depreciation-group master data. (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET AssetDepreciationGroups(id)`
- `GET AssetDepreciationGroups`
- `POST AssetDepreciationGroups`
- `PATCH AssetDepreciationGroups(id)`
- `DELETE AssetDepreciationGroups(id)`

**Real fields:** `Code`, `Description`, `Group`

**Example:**
```
GET /b1s/v1/AssetDepreciationGroups?$select=Code,Description,Group&$top=20
```
```
sapb1 query AssetDepreciationGroups --select "Code,Description,Group" --top 20
```

---

## AssetGroups

**Purpose:** Asset-group master data. (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET AssetGroups(id)`
- `GET AssetGroups`
- `POST AssetGroups`
- `PATCH AssetGroups(id)`
- `DELETE AssetGroups(id)`

**Real fields:** `Code`, `Description`

**Example:**
```
GET /b1s/v1/AssetGroups?$select=Code,Description&$top=20
```
```
sapb1 query AssetGroups --select "Code,Description" --top 20
```

---

## AssetManualDepreciation

**Purpose:** Manual depreciation document — posts a manually entered depreciation amount to an asset. (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET AssetManualDepreciation(id)`
- `GET AssetManualDepreciation`
- `POST AssetManualDepreciation`
- `PATCH AssetManualDepreciation(id)`

**Real fields:** `DocEntry`, `DocNum`, `Series`, `AssetValueDate`, `PostingDate`, `DepreciationArea` (line collection: `AssetDocumentLineCollection` → `AssetNumber`, `GLAccount`, `TotalLC`, `Remarks`)

**Example:**
```
GET /b1s/v1/AssetManualDepreciation?$select=DocEntry,DocNum,Series&$top=20
```
```
sapb1 query AssetManualDepreciation --select "DocEntry,DocNum,Series" --top 20
```

---

## AssetRetirement

**Purpose:** Asset retirement/disposal document — removes a fixed asset from the books. (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET AssetRetirement(id)`
- `GET AssetRetirement`
- `POST AssetRetirement`
- `PATCH AssetRetirement(id)`

**Real fields:** `DocEntry`, `DocNum`, `Series`, `AssetValueDate`, `DocumentDate`, `PostingDate` (line collection: `AssetDocumentLineCollection` → `AssetNumber`, `Quantity`, `TotalLC`)

**Example:**
```
GET /b1s/v1/AssetRetirement?$select=DocEntry,DocNum,Series&$top=20
```
```
sapb1 query AssetRetirement --select "DocEntry,DocNum,Series" --top 20
```

---

## AssetTransfer

**Purpose:** Asset transfer document — moves value/quantity from one fixed asset to another (e.g. `AssetNumber` → `NewAssetNumber`). (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET AssetTransfer(id)`
- `GET AssetTransfer`
- `POST AssetTransfer`
- `PATCH AssetTransfer(id)`

**Real fields:** `DocEntry`, `DocNum`, `Series`, `AssetValueDate`, `DocumentDate`, `DocumentType`, `DepreciationArea` (line collection: `AssetDocumentLineCollection` → `AssetNumber`, `NewAssetNumber`)

**Example:**
```
GET /b1s/v1/AssetTransfer?$select=DocEntry,DocNum,Series&$top=20
```
```
sapb1 query AssetTransfer --select "DocEntry,DocNum,Series" --top 20
```

---

## DepreciationAreas

**Purpose:** Depreciation-area master data — defines a valuation view (posting of depreciation, retirement method, area type). (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET DepreciationAreas(id)`
- `GET DepreciationAreas`
- `POST DepreciationAreas`
- `PATCH DepreciationAreas(id)`
- `DELETE DepreciationAreas(id)`

**Real fields:** `Code`, `Description`, `PostingOfDepreciation`, `AreaType`, `RetirementMethod`

**Example:**
```
GET /b1s/v1/DepreciationAreas?$select=Code,Description,PostingOfDepreciation&$top=20
```
```
sapb1 query DepreciationAreas --select "Code,Description,PostingOfDepreciation" --top 20
```

---

## DepreciationTypePools

**Purpose:** Depreciation-type-pool master data. (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET DepreciationTypePools(id)`
- `GET DepreciationTypePools`
- `POST DepreciationTypePools`
- `PATCH DepreciationTypePools(id)`
- `DELETE DepreciationTypePools(id)`

**Real fields:** `Code`, `Description`

**Example:**
```
GET /b1s/v1/DepreciationTypePools?$select=Code,Description&$top=20
```
```
sapb1 query DepreciationTypePools --select "Code,Description" --top 20
```

---

## DepreciationTypes

**Purpose:** Depreciation-type master data — defines a depreciation method and its calculation parameters (straight-line %, salvage %, period controls, validity). (inferred)

**Type:** readable ENTITY

**Operations:**
- `GET DepreciationTypes(id)`
- `GET DepreciationTypes`
- `POST DepreciationTypes`
- `PATCH DepreciationTypes(id)`
- `DELETE DepreciationTypes(id)`

**Real fields:** `Code`, `Description`, `DepreciationMethod`, `IsActive`, `DeterminationCriteria`, `ValidFrom` (also `StraightLinePercentage`, `SalvagePercentage`, `ValidTo`, `CalculationBase`)

**Example:**
```
GET /b1s/v1/DepreciationTypes?$select=Code,Description,DepreciationMethod&$filter=IsActive eq 'tYES'&$top=20
```
```
sapb1 query DepreciationTypes --select "Code,Description,DepreciationMethod" --filter "IsActive eq 'tYES'" --top 20
```
> `IsActive` filter value shown as a placeholder enum; confirm the exact enum via live `$metadata` before relying on it.

---

## AssetCapitalizationCreditMemoService

**Purpose:** Action service over asset-capitalization credit memos — cancel one, or fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `POST AssetCapitalizationCreditMemoService_Cancel` — invokes `Cancel` with an `AssetDocumentParams` JSON payload
- `GET AssetCapitalizationCreditMemoService_GetList`
- `POST AssetCapitalizationCreditMemoService_GetList`

---

## AssetCapitalizationService

**Purpose:** Action service over asset-capitalization documents — cancel one, or fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `POST AssetCapitalizationService_Cancel` — invokes `Cancel` with an `AssetDocumentParams` JSON payload
- `GET AssetCapitalizationService_GetList`
- `POST AssetCapitalizationService_GetList`

---

## AssetClassesService

**Purpose:** Action service over asset-class master data — fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `GET AssetClassesService_GetList`
- `POST AssetClassesService_GetList`

---

## AssetDepreciationGroupsService

**Purpose:** Action service over asset depreciation groups — fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `GET AssetDepreciationGroupsService_GetList`
- `POST AssetDepreciationGroupsService_GetList`

---

## AssetGroupsService

**Purpose:** Action service over asset groups — fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `GET AssetGroupsService_GetList`
- `POST AssetGroupsService_GetList`

---

## AssetManualDepreciationService

**Purpose:** Action service over manual-depreciation documents — cancel one, or fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `POST AssetManualDepreciationService_Cancel` — invokes `Cancel` with an `AssetDocumentParams` JSON payload
- `GET AssetManualDepreciationService_GetList`
- `POST AssetManualDepreciationService_GetList`

---

## AssetRetirementService

**Purpose:** Action service over asset-retirement documents — cancel one, or fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `POST AssetRetirementService_Cancel` — invokes `Cancel` with an `AssetDocumentParams` JSON payload
- `GET AssetRetirementService_GetList`
- `POST AssetRetirementService_GetList`

---

## AssetTransferService

**Purpose:** Action service over asset-transfer documents — cancel one, or fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `POST AssetTransferService_Cancel` — invokes `Cancel` with an `AssetDocumentParams` JSON payload
- `GET AssetTransferService_GetList`
- `POST AssetTransferService_GetList`

---

## DepreciationAreasService

**Purpose:** Action service over depreciation areas — fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `POST DepreciationAreasService_GetList`

---

## DepreciationTypePoolsService

**Purpose:** Action service over depreciation-type pools — fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `GET DepreciationTypePoolsService_GetList`
- `POST DepreciationTypePoolsService_GetList`

---

## DepreciationTypesService

**Purpose:** Action service over depreciation types — fetch a list. (inferred)

**Type:** function/action Service

**Operations:**
- `POST DepreciationTypesService_GetList`

---

## FixedAssetItemsService

**Purpose:** Value-lookup service for fixed-asset items — read an asset's period values / end balance and update the end balance. (inferred)

**Type:** function/action Service

**Operations:**
- `POST FixedAssetItemsService_GetAssetValuesList` — invokes `GetAssetValuesList` with a `FixedAssetValuesParams` JSON payload
- `POST FixedAssetItemsService_GetAssetEndBalance` — invokes `GetAssetEndBalance` with a `FixedAssetValuesParams` JSON payload
- `POST FixedAssetItemsService_UpdateAssetEndBalance` — invokes `UpdateAssetEndBalance` with a `FixedAssetValuesParams,FixedAssetEndBalance` JSON payload

> Payload example bodies in the reference show `{ "FixedAssetValuesParams": {} }` (and, for
> update, `{ "FixedAssetEndBalance": {}, "FixedAssetValuesParams": {} }`) — query live
> `$metadata` for the concrete params fields.
