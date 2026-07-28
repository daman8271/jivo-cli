# SAP Business One Service Layer — Administration & Setup (part 4)

Reference for the **Administration & Setup (part 4)** domain: 5 Service Layer
services covering the SAP Business One **users** master, **user-defined table (UDT)
metadata**, and three **Web Client** per-user personalization stores (form settings,
list-view filters, and variant/view groups).

**5 services total — all 5 are readable entities (each exposes a `GET`).** All
descriptions, operations, and field names below come from the bundled
`catalog/services.json` and `raw/service-layer-api-reference.html` (paths shown at
`/b1s/v1/…` exactly as the reference documents them; the `sapb1` CLI handles the
version for you). Nothing here is invented — where the reference does not list a
field, it says so.

Legend:
- **readable ENTITY** — exposes `GET` (collection + by-id); queryable with OData `$select/$filter/$orderby` and the `sapb1 query` tool.
- **function/action Service** — POST-only RPC-style call; not OData-queryable. Invoke by POSTing to the operation path.

> Note: the `Users` **entity** documented here (CRUD over the users master) is
> distinct from the separate `UsersService` RPC service (e.g.
> `UsersService_GetCurrentUser`), which lives in a different domain and is not part
> of this list.

---

## Users

1. **Purpose:** Manage the SAP Business One users master — "the users table of the SAP Business One application. The users table includes the users list, login details, and authorizations." (payload type `User`). (from reference)
2. **Type:** readable ENTITY (also exposes a `Close` action).
3. **Operations:**
   - `GET Users(id)`
   - `GET Users`
   - `POST Users`
   - `PATCH Users(id)`
   - `DELETE Users(id)`
   - `POST Users(id)/Close`
4. **Fields (real, from the reference examples):** `InternalKey` (numeric key), `UserCode`, `UserName`, `UserPassword`. For anything else, query live `$metadata`.

   ```
   GET /b1s/v1/Users?$select=InternalKey,UserCode,UserName&$filter=InternalKey ge 123&$orderby=InternalKey&$top=10
   ```
   ```
   sapb1 query Users --select "InternalKey,UserCode,UserName" --filter "InternalKey ge 123" --orderby InternalKey --top 10
   ```

   The id is the numeric `InternalKey`, so a by-id read looks like `GET /b1s/v1/Users(123)`.
   `POST Users(id)/Close` invokes the `Close` method on a single user by id (e.g. `POST /b1s/v1/Users(123)/Close`).

---

## UserTablesMD

1. **Purpose:** Manage user-defined table (UDT) metadata — create/read/update/delete the definitions of custom tables (name, description, and table type) in the schema. *(inferred — reference text is generic: "This entity enables you to manipulate 'UserTablesMD'."; the "UDT metadata" meaning is inferred from the entity name and the `TableType` example `bott_NoObject`.)*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET UserTablesMD(id)`
   - `GET UserTablesMD`
   - `POST UserTablesMD`
   - `PATCH UserTablesMD(id)`
   - `DELETE UserTablesMD(id)`
4. **Fields (real, from the reference examples):** `TableName` (key), `TableDescription`, `TableType`. For anything else, query live `$metadata`.

   ```
   GET /b1s/v1/UserTablesMD?$select=TableName,TableDescription,TableType&$filter=startswith(TableName, 'a')&$orderby=TableName&$top=10
   ```
   ```
   sapb1 query UserTablesMD --select "TableName,TableDescription,TableType" --filter "startswith(TableName, 'a')" --orderby TableName --top 10
   ```

   The id is the string `TableName`, so a by-id read looks like `GET /b1s/v1/UserTablesMD('UDT01')`.

---

## WebClientFormSettings

1. **Purpose:** Store per-user Web Client form settings — the personalized form configuration (form id, user id) kept for each user in the Web Client. *(inferred — reference text is generic: "This entity enables you to manipulate 'WebClientFormSettings'."; the "per-user Web Client form personalization" meaning is inferred from the entity name and the `FormId`/`UserId` example fields.)*
2. **Type:** readable ENTITY (payload type `WebClientFormSetting`).
3. **Operations:**
   - `GET WebClientFormSettings(id)`
   - `GET WebClientFormSettings`
   - `POST WebClientFormSettings`
   - `PATCH WebClientFormSettings(id)`
   - `DELETE WebClientFormSettings(id)`
4. **Fields (real, from the reference examples):** `Guid` (key), `FormId`, `UserId`. For anything else, query live `$metadata`.

   ```
   GET /b1s/v1/WebClientFormSettings?$select=Guid,FormId,UserId&$filter=startswith(Guid, 'a')&$orderby=Guid&$top=10
   ```
   ```
   sapb1 query WebClientFormSettings --select "Guid,FormId,UserId" --filter "startswith(Guid, 'a')" --orderby Guid --top 10
   ```

   The id is the string `Guid`, so a by-id read looks like `GET /b1s/v1/WebClientFormSettings('abc')`.

---

## WebClientListviewFilters

1. **Purpose:** Store per-user Web Client list-view filters — the saved filter definitions a user applies to a list view (by user id and table name) in the Web Client. *(inferred — reference text is generic: "This entity enables you to manipulate 'WebClientListviewFilters'."; the "saved per-user list-view filter" meaning is inferred from the entity name and the `UserId`/`TableName` example fields.)*
2. **Type:** readable ENTITY (payload type `WebClientListviewFilter`).
3. **Operations:**
   - `GET WebClientListviewFilters(id)`
   - `GET WebClientListviewFilters`
   - `POST WebClientListviewFilters`
   - `PATCH WebClientListviewFilters(id)`
   - `DELETE WebClientListviewFilters(id)`
4. **Fields (real, from the reference examples):** `Guid` (key), `UserId`, `TableName`. For anything else, query live `$metadata`.

   ```
   GET /b1s/v1/WebClientListviewFilters?$select=Guid,UserId,TableName&$filter=startswith(Guid, 'a')&$orderby=Guid&$top=10
   ```
   ```
   sapb1 query WebClientListviewFilters --select "Guid,UserId,TableName" --filter "startswith(Guid, 'a')" --orderby Guid --top 10
   ```

   The id is the string `Guid`, so a by-id read looks like `GET /b1s/v1/WebClientListviewFilters('abc')`.

---

## WebClientVariantGroups

1. **Purpose:** Store per-user Web Client variant (view) groups — grouped view configurations a user keeps for an object, keyed by user id, view type, and object name. *(inferred — reference text is generic: "This entity enables you to manipulate 'WebClientVariantGroups'."; the "per-user view/variant grouping" meaning is inferred from the entity name and the `UserId`/`ViewType`/`ObjectName` example fields.)*
2. **Type:** readable ENTITY (payload type `WebClientVariantGroup`).
3. **Operations:**
   - `GET WebClientVariantGroups(id)`
   - `GET WebClientVariantGroups`
   - `POST WebClientVariantGroups`
   - `PATCH WebClientVariantGroups(id)`
   - `DELETE WebClientVariantGroups(id)`
4. **Fields (real, from the reference examples):** `Guid` (key), `UserId`, `ViewType`, `ObjectName`. Per the reference, `Guid`, `UserId`, `ViewType`, and `ObjectName` are the four mandatory properties on create. For anything else, query live `$metadata`.

   ```
   GET /b1s/v1/WebClientVariantGroups?$select=Guid,UserId,ViewType&$filter=startswith(Guid, 'a')&$orderby=Guid&$top=10
   ```
   ```
   sapb1 query WebClientVariantGroups --select "Guid,UserId,ViewType" --filter "startswith(Guid, 'a')" --orderby Guid --top 10
   ```

   The id is the string `Guid`, so a by-id read looks like `GET /b1s/v1/WebClientVariantGroups('abc')`.
