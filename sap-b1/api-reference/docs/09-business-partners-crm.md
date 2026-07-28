# 09 — Business Partners & CRM (SAP Business One Service Layer)

Reference for the **Business Partners & CRM** domain: the customer / vendor / lead
master data plus the CRM layer around it — activities (tasks, calls, meetings),
marketing campaigns, contacts, equipment cards, and the setup/lookup tables that
feed them.

**28 services** documented below — **18 readable entities** (have a `GET`, so you can
`sapb1 query` them) and **10 function/action services** (POST-only method calls, no
`GET` collection).

**Legend**
- **Type: readable ENTITY** → has a `GET` collection; usable with `sapb1 query`.
- **Type: function/action Service** → POST-only method invocation; not queryable.
- Operations are copied **verbatim** from the catalog (`catalog/services.json`).
- Fields shown are the **real** field names taken from the API-reference HTML
  examples. They are a starting subset — run `sapb1 fields <Entity>` for the live,
  complete `$metadata` field list.
- CLI shape: `sapb1 query <Entity> --select "<fields>" --filter "<odata>" --top <N>`

---

<!-- ============ BUSINESS PARTNER MASTER DATA ============ -->

## BusinessPartners

**Purpose:** Business partner master data — customers, vendors and leads: record and
retrieve BP info and schedule BP activities.
**Type:** readable ENTITY

**Operations**
- `GET BusinessPartners(id)`
- `GET BusinessPartners`
- `POST BusinessPartners`
- `PATCH BusinessPartners(id)`
- `DELETE BusinessPartners(id)`

**Fields (real, from HTML examples):** `CardCode`, `CardName`, `CardType`
(`CardType` value `'C'` = customer, shown in the HTML example). Many more fields
exist — run `sapb1 fields BusinessPartners`.

```
GET /b1s/v1/BusinessPartners?$select=CardCode,CardName,CardType&$top=20&$filter=CardType eq 'C'
```
```bash
sapb1 query BusinessPartners --select "CardCode,CardName,CardType" --filter "CardType eq 'C'" --top 20
```

## BusinessPartnersService

**Purpose:** Create opening balances for one or more business partners (invoked with
the payload `OpenningBalanceAccount,BPCodes`).
**Type:** function/action Service

**Operations**
- `POST BusinessPartnersService_CreateOpenBalance`

POST-only method call — not queryable. Invoke `CreateOpenBalance` with a JSON payload
specifying the opening-balance account and the target BP codes.

## BusinessPartnerGroups

**Purpose:** Setup of customer and vendor groups — classifies business partners by
criteria such as sector or size.
**Type:** readable ENTITY

**Operations**
- `GET BusinessPartnerGroups(id)`
- `GET BusinessPartnerGroups`
- `POST BusinessPartnerGroups`
- `PATCH BusinessPartnerGroups(id)`
- `DELETE BusinessPartnerGroups(id)`

**Fields (real, from HTML examples):** `Code`, `Name`, `Type`

```
GET /b1s/v1/BusinessPartnerGroups?$select=Code,Name,Type&$top=20
```
```bash
sapb1 query BusinessPartnerGroups --select "Code,Name,Type" --top 20
```

## BusinessPartnerProperties

**Purpose:** The business-partner property definitions (the named BP property flags).
**Type:** readable ENTITY

**Operations**
- `GET BusinessPartnerProperties(id)`
- `GET BusinessPartnerProperties`
- `PATCH BusinessPartnerProperties(id)`

**Fields (real, from HTML examples):** `PropertyCode`, `PropertyName`

```
GET /b1s/v1/BusinessPartnerProperties?$select=PropertyCode,PropertyName&$top=20
```
```bash
sapb1 query BusinessPartnerProperties --select "PropertyCode,PropertyName" --top 20
```

## BusinessPartnerPropertiesService

**Purpose:** Retrieve the list of business-partner properties via a method call.
**Type:** function/action Service

**Operations**
- `POST BusinessPartnerPropertiesService_GetBusinessPartnerPropertyList`

POST-only method call — invokes `GetBusinessPartnerPropertyList` to return the BP
property list. Not queryable.

## Contacts

**Purpose:** Contacts — the activities carried out with customers and vendors.
**Type:** readable ENTITY

**Operations**
- `GET Contacts(id)`
- `GET Contacts`
- `POST Contacts`
- `PATCH Contacts(id)`
- `DELETE Contacts(id)`

**Fields (real, from HTML examples):** `CardCode`, `Notes`, `ContactDate`, `Activity`,
`Details`

```
GET /b1s/v1/Contacts?$select=CardCode,ContactDate,Notes&$top=20&$filter=CardCode eq 'C0001'
```
```bash
sapb1 query Contacts --select "CardCode,ContactDate,Notes" --filter "CardCode eq 'C0001'" --top 20
```

## Industries

**Purpose:** The industries list — an industry can be associated with a sales
opportunity.
**Type:** readable ENTITY

**Operations**
- `GET Industries(id)`
- `GET Industries`
- `POST Industries`
- `PATCH Industries(id)`
- `DELETE Industries(id)`

**Fields (real, from HTML examples):** `IndustryCode`, `IndustryName`,
`IndustryDescription`

```
GET /b1s/v1/Industries?$select=IndustryCode,IndustryName,IndustryDescription&$top=20
```
```bash
sapb1 query Industries --select "IndustryCode,IndustryName,IndustryDescription" --top 20
```

## CommissionGroups

**Purpose:** Commission groups for a sales employee, an item, or a customer.
**Type:** readable ENTITY

**Operations**
- `GET CommissionGroups(id)`
- `GET CommissionGroups`
- `POST CommissionGroups`
- `PATCH CommissionGroups(id)`
- `DELETE CommissionGroups(id)`

**Fields (real, from HTML examples):** `CommissionGroupCode`, `CommissionGroupName`,
`CommissionPercentage`

```
GET /b1s/v1/CommissionGroups?$select=CommissionGroupCode,CommissionGroupName,CommissionPercentage&$top=20
```
```bash
sapb1 query CommissionGroups --select "CommissionGroupCode,CommissionGroupName,CommissionPercentage" --top 20
```

## Territories

**Purpose:** Territory segmentation (the sales territory tree).
**Type:** readable ENTITY

**Operations**
- `GET Territories(id)`
- `GET Territories`
- `POST Territories`
- `PATCH Territories(id)`
- `DELETE Territories(id)`

**Fields (real, from HTML examples):** `TerritoryID`, `Description`, `LocationIndex`,
`Parent`

```
GET /b1s/v1/Territories?$select=TerritoryID,Description,LocationIndex&$top=20
```
```bash
sapb1 query Territories --select "TerritoryID,Description,LocationIndex" --top 20
```

## AddressService

**Purpose:** Resolve/return the full formatted address for a given `AddressParams`
payload.
**Type:** function/action Service

**Operations**
- `POST AddressService_GetFullAddress`

POST-only method call — invoke `GetFullAddress` with an `AddressParams` JSON payload.
Not queryable.

## CustomerEquipmentCards

**Purpose:** Customer equipment cards — for each serial-managed item sold, a card
tracks the after-sales services provided for that item.
**Type:** readable ENTITY

**Operations**
- `GET CustomerEquipmentCards(id)`
- `GET CustomerEquipmentCards`
- `POST CustomerEquipmentCards`
- `PATCH CustomerEquipmentCards(id)`
- `DELETE CustomerEquipmentCards(id)`

**Fields (real, from HTML examples):** `EquipmentCardNum`, `CustomerCode`,
`CustomerName`, `ItemCode`, `InternalSerialNum`, `InstallLocation`

```
GET /b1s/v1/CustomerEquipmentCards?$select=EquipmentCardNum,CustomerCode,CustomerName,ItemCode&$top=20&$filter=CustomerCode eq 'C0001'
```
```bash
sapb1 query CustomerEquipmentCards --select "EquipmentCardNum,CustomerCode,CustomerName,ItemCode" --filter "CustomerCode eq 'C0001'" --top 20
```

---

<!-- ============ ACTIVITIES / CRM TASKS ============ -->

## Activities

**Purpose:** Business-partner activities — tasks, phone calls, meetings and other
scheduled interactions logged against a BP.
**Type:** readable ENTITY

**Operations**
- `GET Activities(id)`
- `GET Activities`
- `POST Activities`
- `PATCH Activities(id)`
- `DELETE Activities(id)`

**Fields (real, from HTML examples):** `ActivityCode`, `CardCode`, `Notes`,
`ActivityDate`, `StartDate`, `DocType`

```
GET /b1s/v1/Activities?$select=ActivityCode,CardCode,Notes&$top=20&$filter=CardCode eq 'C0001'
```
```bash
sapb1 query Activities --select "ActivityCode,CardCode,Notes" --filter "CardCode eq 'C0001'" --top 20
```

## ActivitiesService

**Purpose:** Work with **recurring (series) activities** — list activities, and get /
update / delete a single instance out of a recurring series, plus fetch the top-N
instances.
**Type:** function/action Service

**Operations**
- `POST ActivitiesService_GetActivityList`
- `POST ActivitiesService_GetSingleInstanceFromSeries`
- `POST ActivitiesService_UpdateSingleInstanceInSeries`
- `POST ActivitiesService_DeleteSingleInstanceFromSeries`
- `POST ActivitiesService_GetTopNActivityInstances`

POST-only method calls — not queryable. `GetSingleInstanceFromSeries`,
`UpdateSingleInstanceInSeries` and `DeleteSingleInstanceFromSeries` take an
`ActivityInstanceParams` / `Activity` payload; `GetTopNActivityInstances` takes an
`ActivityInstancesListParams` payload.

## ActivityTypes

**Purpose:** Activity types — the different kinds of activity you have with BPs (for
example phone calls and meetings).
**Type:** readable ENTITY

**Operations**
- `GET ActivityTypes(id)`
- `GET ActivityTypes`
- `POST ActivityTypes`
- `PATCH ActivityTypes(id)`
- `DELETE ActivityTypes(id)`

**Fields (real, from HTML examples):** `Code`, `Name`

```
GET /b1s/v1/ActivityTypes?$select=Code,Name&$top=20
```
```bash
sapb1 query ActivityTypes --select "Code,Name" --top 20
```

## ActivityStatuses

**Purpose:** Statuses for Task-type activities in the Business Partners module.
**Type:** readable ENTITY

**Operations**
- `GET ActivityStatuses(id)`
- `GET ActivityStatuses`
- `POST ActivityStatuses`
- `PATCH ActivityStatuses(id)`
- `DELETE ActivityStatuses(id)`

**Fields (real, from HTML examples):** `StatusId`, `StatusName`, `StatusDescription`

```
GET /b1s/v1/ActivityStatuses?$select=StatusId,StatusName,StatusDescription&$top=20
```
```bash
sapb1 query ActivityStatuses --select "StatusId,StatusName,StatusDescription" --top 20
```

## ActivityLocations

**Purpose:** Locations where activities with your business partners take place.
**Type:** readable ENTITY

**Operations**
- `GET ActivityLocations(id)`
- `GET ActivityLocations`
- `POST ActivityLocations`
- `PATCH ActivityLocations(id)`

**Fields (real, from HTML examples):** `Code`, `Name`

```
GET /b1s/v1/ActivityLocations?$select=Code,Name&$top=20
```
```bash
sapb1 query ActivityLocations --select "Code,Name" --top 20
```

## ActivityRecipientLists

**Purpose:** Recipient lists for activities — a named list of recipients (with type and
code) that an activity can target.
**Type:** readable ENTITY

**Operations**
- `GET ActivityRecipientLists(id)`
- `GET ActivityRecipientLists`
- `POST ActivityRecipientLists`
- `PATCH ActivityRecipientLists(id)`
- `DELETE ActivityRecipientLists(id)`

**Fields (real, from HTML examples):** `Code`, `Name`, `Active`, `RecipientCode`,
`RecipientType`

```
GET /b1s/v1/ActivityRecipientLists?$select=Code,Name,Active&$top=20
```
```bash
sapb1 query ActivityRecipientLists --select "Code,Name,Active" --top 20
```

## ActivityRecipientListsService

**Purpose:** Retrieve the activity recipient lists via a method call.
**Type:** function/action Service

**Operations**
- `GET ActivityRecipientListsService_GetList`
- `POST ActivityRecipientListsService_GetList`

Method call (`GetList`) exposed over both GET and POST. This is a service method, not
an OData entity — prefer the `ActivityRecipientLists` entity above for `sapb1 query`.

---

<!-- ============ MARKETING CAMPAIGNS ============ -->

## Campaigns

**Purpose:** Marketing campaigns — campaign header, its target business partners, and
discount lines.
**Type:** readable ENTITY

**Operations**
- `GET Campaigns(id)`
- `GET Campaigns`
- `POST Campaigns`
- `PATCH Campaigns(id)`
- `DELETE Campaigns(id)`
- `POST Campaigns(id)/Cancel`

**Fields (real, from HTML examples):** `CampaignNumber`, `CampaignName`,
`CampaignType`, `StartDate`, `ByDate`, `BPCode`

```
GET /b1s/v1/Campaigns?$select=CampaignNumber,CampaignName,CampaignType,StartDate&$top=20
```
```bash
sapb1 query Campaigns --select "CampaignNumber,CampaignName,CampaignType,StartDate" --top 20
```

Note the extra action `POST Campaigns(id)/Cancel` cancels a campaign.

## CampaignsService

**Purpose:** Retrieve the campaigns list via a method call.
**Type:** function/action Service

**Operations**
- `GET CampaignsService_GetList`
- `POST CampaignsService_GetList`

Method call (`GetList`) exposed over both GET and POST. Not an OData entity — prefer
the `Campaigns` entity above for `sapb1 query`.

## CampaignResponseType

**Purpose:** Campaign response types — the possible responses recorded against a
campaign.
**Type:** readable ENTITY

**Operations**
- `GET CampaignResponseType(id)`
- `GET CampaignResponseType`
- `POST CampaignResponseType`
- `PATCH CampaignResponseType(id)`
- `DELETE CampaignResponseType(id)`

**Fields (real, from HTML examples):** `ResponseType`, `ResponseTypeDescription`,
`IsActive`

```
GET /b1s/v1/CampaignResponseType?$select=ResponseType,ResponseTypeDescription,IsActive&$top=20
```
```bash
sapb1 query CampaignResponseType --select "ResponseType,ResponseTypeDescription,IsActive" --top 20
```

## CampaignResponseTypeService

**Purpose:** Retrieve the campaign response-type list via a method call.
**Type:** function/action Service

**Operations**
- `POST CampaignResponseTypeService_GetResponseTypeList`

POST-only method call — invokes `GetResponseTypeList`. Not queryable; prefer the
`CampaignResponseType` entity above.

---

<!-- ============ MOBILE / WEB CLIENT / PARTNER SETUP ============ -->

## MobileAddOnSetting

**Purpose:** Settings for the mobile add-on (mobile-app configuration entries).
**Type:** readable ENTITY

**Operations**
- `GET MobileAddOnSetting(id)`
- `GET MobileAddOnSetting`
- `POST MobileAddOnSetting`
- `PATCH MobileAddOnSetting(id)`
- `DELETE MobileAddOnSetting(id)`

**Fields (real, from HTML examples):** `Code`, `Description`, `Url`

```
GET /b1s/v1/MobileAddOnSetting?$select=Code,Description,Url&$top=20
```
```bash
sapb1 query MobileAddOnSetting --select "Code,Description,Url" --top 20
```

## MobileAddOnSettingService

**Purpose:** Retrieve the mobile add-on settings list via a method call.
**Type:** function/action Service

**Operations**
- `POST MobileAddOnSettingService_GetMobileAddOnSettingList`

POST-only method call — invokes `GetMobileAddOnSettingList`. Not queryable; prefer the
`MobileAddOnSetting` entity above.

## PartnersSetups

**Purpose:** Partner (business-partner relationship) setup records — relationship
definitions between related BPs.
**Type:** readable ENTITY

**Operations**
- `GET PartnersSetups(id)`
- `GET PartnersSetups`
- `POST PartnersSetups`
- `PATCH PartnersSetups(id)`
- `DELETE PartnersSetups(id)`

**Fields (real, from HTML examples):** `PartnerID`, `Name`, `DefaultRelationship`,
`RelatedBP`

```
GET /b1s/v1/PartnersSetups?$select=PartnerID,Name,DefaultRelationship&$top=20
```
```bash
sapb1 query PartnersSetups --select "PartnerID,Name,DefaultRelationship" --top 20
```

## PartnersSetupsService

**Purpose:** Retrieve the partner-setups list via a method call.
**Type:** function/action Service

**Operations**
- `POST PartnersSetupsService_GetList`

POST-only method call — invokes `GetList`. Not queryable; prefer the `PartnersSetups`
entity above.

## WebClientRecentActivities

**Purpose:** Recently-accessed items/views tracked per user in the SAP Business One Web
Client.
**Type:** readable ENTITY

**Operations**
- `GET WebClientRecentActivities(id)`
- `GET WebClientRecentActivities`
- `POST WebClientRecentActivities`
- `PATCH WebClientRecentActivities(id)`
- `DELETE WebClientRecentActivities(id)`

**Fields (real, from HTML examples):** `Guid`, `AppId`, `AppType`, `UserId`,
`ViewType`

```
GET /b1s/v1/WebClientRecentActivities?$select=Guid,AppId,AppType,UserId&$top=20
```
```bash
sapb1 query WebClientRecentActivities --select "Guid,AppId,AppType,UserId" --top 20
```

## WebClientRecentActivityService

**Purpose:** Retrieve the Web Client recent-activity list via a method call.
**Type:** function/action Service

**Operations**
- `POST WebClientRecentActivityService_GetList`

POST-only method call — invokes `GetList`. Not queryable; prefer the
`WebClientRecentActivities` entity above.

---

### Domain summary

| # | Service | Type |
|---|---------|------|
| 1 | BusinessPartners | ENTITY |
| 2 | BusinessPartnersService | action |
| 3 | BusinessPartnerGroups | ENTITY |
| 4 | BusinessPartnerProperties | ENTITY |
| 5 | BusinessPartnerPropertiesService | action |
| 6 | Contacts | ENTITY |
| 7 | Industries | ENTITY |
| 8 | CommissionGroups | ENTITY |
| 9 | Territories | ENTITY |
| 10 | AddressService | action |
| 11 | CustomerEquipmentCards | ENTITY |
| 12 | Activities | ENTITY |
| 13 | ActivitiesService | action |
| 14 | ActivityTypes | ENTITY |
| 15 | ActivityStatuses | ENTITY |
| 16 | ActivityLocations | ENTITY |
| 17 | ActivityRecipientLists | ENTITY |
| 18 | ActivityRecipientListsService | action |
| 19 | Campaigns | ENTITY |
| 20 | CampaignsService | action |
| 21 | CampaignResponseType | ENTITY |
| 22 | CampaignResponseTypeService | action |
| 23 | MobileAddOnSetting | ENTITY |
| 24 | MobileAddOnSettingService | action |
| 25 | PartnersSetups | ENTITY |
| 26 | PartnersSetupsService | action |
| 27 | WebClientRecentActivities | ENTITY |
| 28 | WebClientRecentActivityService | action |

**Totals: 28 services — 18 readable entities, 10 function/action services.**

> Field lists above are the real names present in the API-reference examples and are a
> subset. For the authoritative, complete field list of any entity, query live
> `$metadata`: `sapb1 fields <Entity>`.
