# SAP Business One Service Layer — System & Other (part 2)

Reference for the 22 services in the `system-other-2` domain. Operations are copied verbatim from `catalog/services.json`; descriptions and field names are taken from the official API reference HTML (`raw/service-layer-api-reference.html`). Where the HTML only says "This entity enables you to manipulate 'X'", the plain-English purpose is marked **(inferred)**.

All 22 services expose a `GET` collection op, so every one is a **readable ENTITY**. A few also carry action ops (noted per service). Base URL in examples: `/b1s/v1` (the reference HTML uses `/b1s/v2`; both are valid on modern releases).

---

## PredefinedTexts

1. **Purpose:** Predefined free-text templates that can be dropped into documents/rows. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET PredefinedTexts(id)`
   - `GET PredefinedTexts`
   - `POST PredefinedTexts`
   - `PATCH PredefinedTexts(id)`
   - `DELETE PredefinedTexts(id)`
4. **Fields:** `Numerator`, `TextCode`, `Text`

```
GET /b1s/v1/PredefinedTexts?$select=Numerator,TextCode,Text&$top=20
```
```
sapb1 query PredefinedTexts --select Numerator,TextCode,Text --top 20
```

---

## ProductTrees

1. **Purpose:** Bills of materials — a completed product described by its parts and raw materials.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET ProductTrees(id)`
   - `GET ProductTrees`
   - `POST ProductTrees`
   - `PATCH ProductTrees(id)`
   - `DELETE ProductTrees(id)`
4. **Fields:** `TreeCode`, `TreeType`, `Quantity`, `ItemCode`, `ProductTreeLines`

```
GET /b1s/v1/ProductTrees?$select=TreeCode,TreeType,Quantity&$top=20
```
```
sapb1 query ProductTrees --select TreeCode,TreeType,Quantity --top 20
```

---

## Relationships

1. **Purpose:** The relationships list from which a relationship definition can be associated with a partner in a sales opportunity.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Relationships(id)`
   - `GET Relationships`
   - `POST Relationships`
   - `PATCH Relationships(id)`
   - `DELETE Relationships(id)`
4. **Fields:** `RelationshipCode`, `RelationshipDescription`

```
GET /b1s/v1/Relationships?$select=RelationshipCode,RelationshipDescription&$top=20
```
```
sapb1 query Relationships --select RelationshipCode,RelationshipDescription --top 20
```

---

## RouteStages

1. **Purpose:** Route stages used to build multi-step routes (e.g. logistics/transport routing). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET RouteStages(id)`
   - `GET RouteStages`
   - `POST RouteStages`
   - `PATCH RouteStages(id)`
   - `DELETE RouteStages(id)`
4. **Fields:** `InternalNumber`, `Code`, `Description`

```
GET /b1s/v1/RouteStages?$select=InternalNumber,Code,Description&$top=20
```
```
sapb1 query RouteStages --select InternalNumber,Code,Description --top 20
```

---

## Sections

1. **Purpose:** Section master records used to categorize/group other entities. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Sections(id)`
   - `GET Sections`
   - `POST Sections`
   - `PATCH Sections(id)`
   - `DELETE Sections(id)`
4. **Fields:** `AbsEntry`, `Code`, `Description`, `ECode`

```
GET /b1s/v1/Sections?$select=AbsEntry,Code,Description&$top=20
```
```
sapb1 query Sections --select AbsEntry,Code,Description --top 20
```

---

## SelfCreditMemos

1. **Purpose:** A request for payment that also records the cost in a profit-and-loss statement (self-billing credit memo).
2. **Type:** readable ENTITY (with action ops)
3. **Operations:**
   - `GET SelfCreditMemos(id)`
   - `GET SelfCreditMemos`
   - `POST SelfCreditMemos`
   - `PATCH SelfCreditMemos(id)`
   - `POST SelfCreditMemos(id)/Close`
   - `POST SelfCreditMemos(id)/Cancel`
   - `POST SelfCreditMemos(id)/Reopen`
   - `POST SelfCreditMemos(id)/CreateCancellationDocument`
4. **Fields:** `DocEntry`, `DocNum`, `DocType`, `CardCode`, `DocumentLines`

```
GET /b1s/v1/SelfCreditMemos?$select=DocEntry,DocNum,DocType&$top=20
```
```
sapb1 query SelfCreditMemos --select DocEntry,DocNum,DocType --top 20
```

---

## ShortLinkMappings

1. **Purpose:** Short-link mappings resolving a short GUID to its origin/source link. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET ShortLinkMappings(guid)`
   - `GET ShortLinkMappings`
   - `POST ShortLinkMappings`
   - `PATCH ShortLinkMappings(guid)`
   - `DELETE ShortLinkMappings(guid)`
4. **Fields:** `Guid`, `Origin`, `SrcLink`, `OwnerCode`, `CreateDate`, `CreateTime`

```
GET /b1s/v1/ShortLinkMappings?$select=Guid,Origin,SrcLink&$top=20
```
```
sapb1 query ShortLinkMappings --select Guid,Origin,SrcLink --top 20
```

---

## States

1. **Purpose:** State/province master records tied to a country, used in addresses. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET States(id)`
   - `GET States`
   - `POST States`
   - `PATCH States(id)`
   - `DELETE States(id)`
4. **Fields:** `Code`, `Country`, `Name`

```
GET /b1s/v1/States?$select=Code,Country,Name&$filter=Country eq 'IN'&$top=20
```
```
sapb1 query States --select Code,Country,Name --filter "Country eq 'IN'" --top 20
```

---

## Teams

1. **Purpose:** The list of teams from which team memberships of an employee can be selected; an employee can be a Member or a Leader of more than one team.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Teams(id)`
   - `GET Teams`
   - `POST Teams`
   - `PATCH Teams(id)`
4. **Fields:** `TeamID`, `TeamName`, `Description`, `TeamMembers`, `EmployeeID`, `RoleInTeam`

```
GET /b1s/v1/Teams?$select=TeamID,TeamName,Description&$top=20
```
```
sapb1 query Teams --select TeamID,TeamName,Description --top 20
```

---

## TerminationReason

1. **Purpose:** Reason codes for termination (e.g. employee termination reasons). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET TerminationReason(id)`
   - `GET TerminationReason`
   - `POST TerminationReason`
   - `PATCH TerminationReason(id)`
   - `DELETE TerminationReason(id)`
4. **Fields:** `ReasonID`, `Name`, `Description`

```
GET /b1s/v1/TerminationReason?$select=ReasonID,Name,Description&$top=20
```
```
sapb1 query TerminationReason --select ReasonID,Name,Description --top 20
```

---

## TrackingNotes

1. **Purpose:** Tracking-note documents recording customs/CCD movement details for items. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET TrackingNotes(id)`
   - `GET TrackingNotes`
   - `POST TrackingNotes`
   - `PATCH TrackingNotes(id)`
   - `DELETE TrackingNotes(id)`
4. **Fields:** `TrackingNoteNumber`, `CCDNumber`, `Date`, `BPCode`, `CountryOfOrigin`, `TrackingNoteItemCollection`

```
GET /b1s/v1/TrackingNotes?$select=TrackingNoteNumber,CCDNumber,Date&$top=20
```
```
sapb1 query TrackingNotes --select TrackingNoteNumber,CCDNumber,Date --top 20
```

---

## TransportationDocument

1. **Purpose:** Transportation/shipping document header with carrier and dispatch details. (inferred)
2. **Type:** readable ENTITY (with action op)
3. **Operations:**
   - `GET TransportationDocument(id)`
   - `GET TransportationDocument`
   - `POST TransportationDocument`
   - `PATCH TransportationDocument(id)`
   - `POST TransportationDocument(id)/CancelTransportationDocument`
4. **Fields:** `TranspDocNumber`, `NextNumber`, `PostDate`, `CarrierCode`, `DocType`, `ItemCode`

```
GET /b1s/v1/TransportationDocument?$select=TranspDocNumber,NextNumber,PostDate&$top=20
```
```
sapb1 query TransportationDocument --select TranspDocNumber,NextNumber,PostDate --top 20
```

---

## TSRExceptionalEvents

1. **Purpose:** Exceptional-event codes for TSR (transport/SAF-T style reporting) documents. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET TSRExceptionalEvents(id)`
   - `GET TSRExceptionalEvents`
   - `POST TSRExceptionalEvents`
   - `PATCH TSRExceptionalEvents(id)`
4. **Fields:** `Code`, `Description`

```
GET /b1s/v1/TSRExceptionalEvents?$select=Code,Description&$top=20
```
```
sapb1 query TSRExceptionalEvents --select Code,Description --top 20
```

---

## ValueMapping

1. **Purpose:** Maps a B1 object value to a third-party system value (integration value mapping). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET ValueMapping(id)`
   - `GET ValueMapping`
   - `POST ValueMapping`
   - `PATCH ValueMapping(id)`
   - `DELETE ValueMapping(id)`
4. **Fields:** `AbsEntry`, `ObjectId`, `ObjectAbsEntry`, `ThirdPartySystemId`, `ThirdPartyValue`

```
GET /b1s/v1/ValueMapping?$select=AbsEntry,ObjectId,ThirdPartyValue&$top=20
```
```
sapb1 query ValueMapping --select AbsEntry,ObjectId,ThirdPartyValue --top 20
```

---

## ValueMappingCommunication

1. **Purpose:** Communication/sync records for value mappings against a third-party system. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET ValueMappingCommunication(id)`
   - `GET ValueMappingCommunication`
   - `POST ValueMappingCommunication`
   - `PATCH ValueMappingCommunication(id)`
4. **Fields:** `AbsEntry`, `ThirdPartySystemId`, `ObjectId`, `CommunicationType`, `StartDate`, `StartTime`

```
GET /b1s/v1/ValueMappingCommunication?$select=AbsEntry,ThirdPartySystemId,ObjectId&$top=20
```
```
sapb1 query ValueMappingCommunication --select AbsEntry,ThirdPartySystemId,ObjectId --top 20
```

---

## WebClientBookmarkTiles

1. **Purpose:** Web Client bookmark tiles pinned by a user on the launchpad. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET WebClientBookmarkTiles(id)`
   - `GET WebClientBookmarkTiles`
   - `POST WebClientBookmarkTiles`
   - `PATCH WebClientBookmarkTiles(id)`
   - `DELETE WebClientBookmarkTiles(id)`
4. **Fields:** `Guid`, `Title`, `SubTitle`

```
GET /b1s/v1/WebClientBookmarkTiles?$select=Guid,Title,SubTitle&$top=20
```
```
sapb1 query WebClientBookmarkTiles --select Guid,Title,SubTitle --top 20
```

---

## WebClientDashboards

1. **Purpose:** Per-user Web Client dashboard definitions. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET WebClientDashboards(id)`
   - `GET WebClientDashboards`
   - `POST WebClientDashboards`
   - `PATCH WebClientDashboards(id)`
   - `DELETE WebClientDashboards(id)`
4. **Fields:** `Guid`, `UserId`, `Content`

```
GET /b1s/v1/WebClientDashboards?$select=Guid,UserId,Content&$top=20
```
```
sapb1 query WebClientDashboards --select Guid,UserId,Content --top 20
```

---

## WebClientLaunchpads

1. **Purpose:** Per-user Web Client launchpad configuration (layout/theme). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET WebClientLaunchpads(id)`
   - `GET WebClientLaunchpads`
   - `POST WebClientLaunchpads`
   - `PATCH WebClientLaunchpads(id)`
   - `DELETE WebClientLaunchpads(id)`
4. **Fields:** `Guid`, `UserId`, `ThemeId`

```
GET /b1s/v1/WebClientLaunchpads?$select=Guid,UserId,ThemeId&$top=20
```
```
sapb1 query WebClientLaunchpads --select Guid,UserId,ThemeId --top 20
```

---

## WebClientNotifications

1. **Purpose:** Web Client user notifications keyed to a business object. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET WebClientNotifications(id)`
   - `GET WebClientNotifications`
   - `POST WebClientNotifications`
   - `PATCH WebClientNotifications(id)`
   - `DELETE WebClientNotifications(id)`
4. **Fields:** `Guid`, `ObjectKey`, `ActivityDate`

```
GET /b1s/v1/WebClientNotifications?$select=Guid,ObjectKey,ActivityDate&$top=20
```
```
sapb1 query WebClientNotifications --select Guid,ObjectKey,ActivityDate --top 20
```

---

## WebClientPreferences

1. **Purpose:** Per-user Web Client UI preferences (e.g. per-table settings). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET WebClientPreferences(id)`
   - `GET WebClientPreferences`
   - `POST WebClientPreferences`
   - `PATCH WebClientPreferences(id)`
   - `DELETE WebClientPreferences(id)`
4. **Fields:** `Guid`, `UserId`, `TableName`

```
GET /b1s/v1/WebClientPreferences?$select=Guid,UserId,TableName&$top=20
```
```
sapb1 query WebClientPreferences --select Guid,UserId,TableName --top 20
```

---

## WebClientVariants

1. **Purpose:** Saved Web Client view/filter variants per user, with ordering. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET WebClientVariants(id)`
   - `GET WebClientVariants`
   - `POST WebClientVariants`
   - `PATCH WebClientVariants(id)`
   - `DELETE WebClientVariants(id)`
4. **Fields:** `Guid`, `Order`, `UserId`

```
GET /b1s/v1/WebClientVariants?$select=Guid,Order,UserId&$top=20
```
```
sapb1 query WebClientVariants --select Guid,Order,UserId --top 20
```

---

## WeightMeasures

1. **Purpose:** Defines the weight-measure units used for item records.
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET WeightMeasures(id)`
   - `GET WeightMeasures`
   - `POST WeightMeasures`
   - `PATCH WeightMeasures(id)`
   - `DELETE WeightMeasures(id)`
4. **Fields:** `UnitCode`, `UnitDisplay`, `UnitName`

```
GET /b1s/v1/WeightMeasures?$select=UnitCode,UnitDisplay,UnitName&$top=20
```
```
sapb1 query WeightMeasures --select UnitCode,UnitDisplay,UnitName --top 20
```
