# SAP Business One Service Layer — HR & Employees

Reference for the **HR & Employees** (`hr-resources`) domain: 11 Service Layer
services covering employee master data (`EmployeesInfo`) plus the HR lookup tables
that feed it — ID types, positions, role setups, statuses, and transfers.

**11 services total — 6 are readable entities (have a `GET`), 5 are POST-only
function services.** Every description, operation, and field name below comes from
the bundled `catalog/services.json` and `raw/service-layer-api-reference.html`
(paths shown at `/b1s/v1/…` exactly as the reference documents them; the `sapb1`
CLI handles the version for you). Nothing here is invented — where the reference
does not list a field, it says so.

Legend:
- **readable ENTITY** — exposes `GET` (collection + by-id); queryable with OData `$select/$filter/$orderby` and the `sapb1 query` tool.
- **function/action Service** — POST-only RPC-style call; not OData-queryable. Invoke by POSTing to the operation path.

> Note: every entity/service description in the reference for this domain is the
> generic boilerplate ("This entity enables you to manipulate 'X'." /
> "This API enables you to invoke the interfaces defined on 'X'."), so the
> plain-English purposes below are marked *(inferred)*. Operations and field names
> are verbatim from the reference and are **not** inferred.

---

## EmployeeIDTypeService

1. **Purpose:** Invokes the interfaces defined on `EmployeeIDTypeService` — returns the list of employee ID-type lookup values. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'EmployeeIDTypeService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST EmployeeIDTypeService_GetList` — "Invoke the method 'GetList' on this service."

For a queryable table, use the **EmployeeIDType** entity below.

---

## EmployeePositionService

1. **Purpose:** Invokes the interfaces defined on `EmployeePositionService` — returns the list of employee positions. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'EmployeePositionService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST EmployeePositionService_GetList` — "Invoke the method 'GetList' on this service."

For a queryable table, use the **EmployeePosition** entity below.

---

## EmployeeRolesSetupService

1. **Purpose:** Invokes the interfaces defined on `EmployeeRolesSetupService` — returns the list of employee role-setup definitions. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'EmployeeRolesSetupService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST EmployeeRolesSetupService_GetEmployeeRoleSetupList` — "Invoke the method 'GetEmployeeRoleSetupList' on this service."

For a queryable table, use the **EmployeeRolesSetup** entity below.

---

## EmployeeStatusService

1. **Purpose:** Invokes the interfaces defined on `EmployeeStatusService` — returns the list of employee-status lookup values. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'EmployeeStatusService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST EmployeeStatusService_GetList` — "Invoke the method 'GetList' on this service."

For a queryable table, use the **EmployeeStatus** entity below.

---

## EmployeeTransfersService

1. **Purpose:** Invokes the interfaces defined on `EmployeeTransfersService` — returns the list of employee transfers. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'EmployeeTransfersService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST EmployeeTransfersService_GetEmployeeTransferList` — "Invoke the method 'GetEmployeeTransferList' on this service."

For a queryable table, use the **EmployeeTransfers** entity below.

---

## EmployeeIDType

1. **Purpose:** Manage the **employee ID-type** lookup values (the kinds of identification documents recorded against an employee). *(inferred — reference text: "This entity enables you to manipulate 'EmployeeIDType'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET EmployeeIDType(id)`
   - `GET EmployeeIDType`
   - `POST EmployeeIDType`
   - `PATCH EmployeeIDType(id)`
   - `DELETE EmployeeIDType(id)`
4. **Fields (real, from the reference examples):** `IDType` (key; string-valued, addressed as `EmployeeIDType('test')`) — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/EmployeeIDType?$select=IDType&$filter=startswith(IDType, 'a')&$top=20
   ```
   ```
   sapb1 query EmployeeIDType --select "IDType" --filter "startswith(IDType, 'a')" --top 20
   ```

---

## EmployeePosition

1. **Purpose:** Manage the **employee position** lookup table (job positions that can be assigned to employees). *(inferred — reference text: "This entity enables you to manipulate 'EmployeePosition'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET EmployeePosition(id)`
   - `GET EmployeePosition`
   - `POST EmployeePosition`
   - `PATCH EmployeePosition(id)`
   - `DELETE EmployeePosition(id)`
4. **Fields (real, from the reference examples):** `PositionID` (key), `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/EmployeePosition?$select=PositionID,Name,Description&$filter=PositionID ge 2&$top=20
   ```
   ```
   sapb1 query EmployeePosition --select "PositionID,Name,Description" --filter "PositionID ge 2" --top 20
   ```

---

## EmployeeRolesSetup

1. **Purpose:** Manage the **employee role-setup** definitions (named roles that can be assigned within HR). *(inferred — reference text: "This entity enables you to manipulate 'EmployeeRolesSetup'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET EmployeeRolesSetup(id)`
   - `GET EmployeeRolesSetup`
   - `POST EmployeeRolesSetup`
   - `PATCH EmployeeRolesSetup(id)`
   - `DELETE EmployeeRolesSetup(id)`
4. **Fields (real, from the reference examples):** `TypeID` (key), `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/EmployeeRolesSetup?$select=TypeID,Name,Description&$filter=TypeID ge 1&$top=20
   ```
   ```
   sapb1 query EmployeeRolesSetup --select "TypeID,Name,Description" --filter "TypeID ge 1" --top 20
   ```

---

## EmployeesInfo

1. **Purpose:** Manage **employee master records** — the core HR entity holding each employee's identity, job, and organizational assignment. *(inferred — reference text: "This entity enables you to manipulate 'EmployeesInfo'.")*
2. **Type:** readable ENTITY (also exposes `Cancel` and `Close` actions).
3. **Operations:**
   - `GET EmployeesInfo(id)`
   - `GET EmployeesInfo`
   - `POST EmployeesInfo`
   - `PATCH EmployeesInfo(id)`
   - `DELETE EmployeesInfo(id)`
   - `POST EmployeesInfo(id)/Cancel` — "Invoke the method 'Cancel' on this EntitySet with the specified id."
   - `POST EmployeesInfo(id)/Close` — "Invoke the method 'Close' on this EntitySet with the specified id."
4. **Fields (real, from the reference examples):** `EmployeeID` (key), `FirstName`, `LastName`, `JobTitle`, `Branch`, `Department`, `WorkCountryCode`, `Remarks` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/EmployeesInfo?$select=EmployeeID,LastName,FirstName&$filter=EmployeeID ge 123&$orderby=EmployeeID&$top=20
   ```
   ```
   sapb1 query EmployeesInfo --select "EmployeeID,LastName,FirstName" --filter "EmployeeID ge 123" --top 20
   ```

   Cancel / Close an employee record (actions, not reads):
   ```
   POST /b1s/v1/EmployeesInfo(123)/Cancel
   POST /b1s/v1/EmployeesInfo(123)/Close
   ```

---

## EmployeeStatus

1. **Purpose:** Manage the **employee status** lookup values (e.g. active / inactive and user-defined statuses). *(inferred — reference text: "This entity enables you to manipulate 'EmployeeStatus'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET EmployeeStatus(id)`
   - `GET EmployeeStatus`
   - `POST EmployeeStatus`
   - `PATCH EmployeeStatus(id)`
   - `DELETE EmployeeStatus(id)`
4. **Fields (real, from the reference examples):** `StatusId` (key), `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/EmployeeStatus?$select=StatusId,Name,Description&$filter=StatusId ge 1&$top=20
   ```
   ```
   sapb1 query EmployeeStatus --select "StatusId,Name,Description" --filter "StatusId ge 1" --top 20
   ```

---

## EmployeeTransfers

1. **Purpose:** Manage **employee transfer** records (movements of an employee, with start/end date-times and a processing status). *(inferred — reference text: "This entity enables you to manipulate 'EmployeeTransfers'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET EmployeeTransfers(id)`
   - `GET EmployeeTransfers`
   - `POST EmployeeTransfers`
   - `PATCH EmployeeTransfers(id)`
   - `DELETE EmployeeTransfers(id)`
4. **Fields (real, from the reference examples):** `TransferID` (key), `TransStartDate`, `TransStartTime`, `TransEndDate`, `TransEndTime`, `Status` (e.g. `ets_Processing`), `Comment` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/EmployeeTransfers?$select=TransferID,TransStartDate,TransStartTime&$filter=TransferID ge 1&$orderby=TransferID&$top=20
   ```
   ```
   sapb1 query EmployeeTransfers --select "TransferID,TransStartDate,TransStartTime" --filter "TransferID ge 1" --top 20
   ```
