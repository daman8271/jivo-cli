# SAP Business One Service Layer — Projects

Reference for the **Projects** domain: 6 Service Layer services covering the Project
Management module — its configuration lookups (subproject types, stages, areas,
priorities, activities, tasks), subproject CRUD, project documents, and time sheets —
plus the legacy financial-dimension **Projects** entity/service used to tag
transactions with a project code.

**6 services total — 3 are readable entities (have a `GET`), 3 are POST-only
function/RPC services.** All descriptions, operations, and field names below come
from the bundled `catalog/services.json` and `raw/service-layer-api-reference.html`
(paths shown at `/b1s/v1/…` exactly as the reference documents them; the `sapb1`
CLI handles the version for you). Nothing here is invented — where the reference
does not list a field, it says so.

Legend:
- **readable ENTITY** — exposes `GET` (collection + by-id); queryable with OData `$select/$filter/$orderby` and the `sapb1 query` tool.
- **function/action Service** — POST-only RPC-style call; not OData-queryable. Invoke by POSTing to the operation path.

> Note on the two "project" concepts: **Projects / ProjectsService** are the classic
> lightweight financial-tracking dimension (a `Code` + `Name` you attach to
> documents). **ProjectManagements / ProjectManagementService /
> ProjectManagementConfigurationService / ProjectManagementTimeSheet** are the full
> Project Management module (project documents, subprojects, stages, time sheets).
> They are unrelated object families that happen to share the word "project".

---

## ProjectManagementConfigurationService

1. **Purpose:** Manage the configuration lookups of the Project Management module — subproject types, stage types, areas, priorities, activities, and tasks (get/add/update/delete each). *(inferred — reference text is generic: "This API enables you to invoke the interfaces defined on 'ProjectManagementConfigurationService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ProjectManagementConfigurationService_GetSubprojectTypes`
   - `POST ProjectManagementConfigurationService_AddSubprojectTypes`
   - `POST ProjectManagementConfigurationService_UpdateSubprojectTypes`
   - `POST ProjectManagementConfigurationService_DeleteSubprojectTypes`
   - `POST ProjectManagementConfigurationService_GetStageTypes`
   - `POST ProjectManagementConfigurationService_AddStageTypes`
   - `POST ProjectManagementConfigurationService_UpdateStageTypes`
   - `POST ProjectManagementConfigurationService_DeleteStageTypes`
   - `POST ProjectManagementConfigurationService_GetAreas`
   - `POST ProjectManagementConfigurationService_AddAreas`
   - `POST ProjectManagementConfigurationService_UpdateAreas`
   - `POST ProjectManagementConfigurationService_DeleteAreas`
   - `POST ProjectManagementConfigurationService_GetPriorities`
   - `POST ProjectManagementConfigurationService_AddPriorities`
   - `POST ProjectManagementConfigurationService_UpdatePriorities`
   - `POST ProjectManagementConfigurationService_DeletePriorities`
   - `POST ProjectManagementConfigurationService_GetActivities`
   - `POST ProjectManagementConfigurationService_AddActivities`
   - `POST ProjectManagementConfigurationService_UpdateActivities`
   - `POST ProjectManagementConfigurationService_DeleteActivities`
   - `POST ProjectManagementConfigurationService_GetTasks`
   - `POST ProjectManagementConfigurationService_AddTasks`
   - `POST ProjectManagementConfigurationService_UpdateTasks`
   - `POST ProjectManagementConfigurationService_DeleteTasks`

These are RPC calls, not a queryable table. Each `Get*` returns the current list; the
`Add*` / `Update*` / `Delete*` variants mutate it.

---

## ProjectManagementService

1. **Purpose:** Manage subprojects inside a Project Management project document — list, read, add, update, and delete individual subprojects. *(inferred — reference text is generic: "This API enables you to invoke the interfaces defined on 'ProjectManagementService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ProjectManagementService_GetSubprojectsList`
   - `POST ProjectManagementService_GetSubproject`
   - `POST ProjectManagementService_AddSubproject`
   - `POST ProjectManagementService_UpdateSubproject`
   - `POST ProjectManagementService_DeleteSubproject`

RPC-style; not OData-queryable. To read/manage the parent project documents as a
table, use the **ProjectManagements** entity below.

---

## ProjectsService

1. **Purpose:** Returns the list of (financial-dimension) projects — the `Code`/`Name` project master used to tag transactions. *(inferred — reference text is generic: "This API enables you to invoke the interfaces defined on 'ProjectsService'." / op: "Invoke the method 'GetProjectList' on this service.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ProjectsService_GetProjectList`

For a queryable version of the same project master, use the **Projects** entity below.

---

## ProjectManagements

1. **Purpose:** Manage Project Management project documents — the top-level project records of the Project Management module (payload type `PM_ProjectDocumentData`). (from reference: "This entity enables you to manipulate 'ProjectManagements'.")
2. **Type:** readable ENTITY (also exposes a `CancelProject` action).
3. **Operations:**
   - `GET ProjectManagements(id)`
   - `GET ProjectManagements`
   - `POST ProjectManagements`
   - `PATCH ProjectManagements(id)`
   - `DELETE ProjectManagements(id)`
   - `POST ProjectManagements(id)/CancelProject` — "Invoke the method 'CancelProject' on this EntitySet with the specified id." (cancels the project)
4. **Fields (real, from the reference examples):** `AbsEntry` (key), `Owner`, `ProjectName`, `ProjectStatus`, `ProjectType`, `BusinessPartner`, `StartDate`, `DueDate` — also seen in the reference payload: `AllowSubprojects`, `AttachmentEntry`, `BusinessPartnerName`, `ClosingDate`, `ContactPerson`, `FinancialProject`, `Industry`, `Reason`, `RiskLevel`, `SalesEmployee`, `Territory`. For anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ProjectManagements?$select=AbsEntry,Owner,ProjectName,ProjectStatus&$filter=ProjectStatus eq 'pst_Started'&$top=20
   ```
   ```
   sapb1 query ProjectManagements --select "AbsEntry,Owner,ProjectName,ProjectStatus" --filter "ProjectStatus eq 'pst_Started'" --top 20
   ```

   Cancel a project (action, not a read):
   ```
   POST /b1s/v1/ProjectManagements(123)/CancelProject
   ```

---

## ProjectManagementTimeSheet

1. **Purpose:** Manage Project Management time sheets — the records of hours logged against a project's activities (payload type `PM_TimeSheetData`, with a `PM_TimeSheetLineDataCollection` of lines). (from reference: "This entity enables you to manipulate 'ProjectManagementTimeSheet'.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET ProjectManagementTimeSheet(id)`
   - `GET ProjectManagementTimeSheet`
   - `POST ProjectManagementTimeSheet`
   - `PATCH ProjectManagementTimeSheet(id)`
   - `DELETE ProjectManagementTimeSheet(id)`
4. **Fields (real, from the reference examples):** `AbsEntry` (key), `DocNumber`, `TimeSheetType`, `UserID`, `DateFrom`, `DateTo` — the line collection `PM_TimeSheetLineDataCollection` carries `ActivityType`, `Date`, `StartTime`, `EndTime`. For anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ProjectManagementTimeSheet?$select=AbsEntry,DocNumber,TimeSheetType&$filter=AbsEntry ge 2&$top=20
   ```
   ```
   sapb1 query ProjectManagementTimeSheet --select "AbsEntry,DocNumber,TimeSheetType" --filter "AbsEntry ge 2" --top 20
   ```

---

## Projects

1. **Purpose:** Manage the (financial-dimension) project master — the lightweight `Code`/`Name` projects used to tag and report on transactions by project (payload type `Project`). (from reference: "This entity enables you to manipulate 'Projects'.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET Projects(id)`
   - `GET Projects`
   - `POST Projects`
   - `PATCH Projects(id)`
   - `DELETE Projects(id)`
4. **Fields (real, from the reference examples):** `Code` (key), `Name`, `ValidFrom`, `ValidTo`. For anything else, query live `$metadata`.

   ```
   GET /b1s/v1/Projects?$select=Code,Name,ValidFrom&$filter=startswith(Code, 'a')&$top=20
   ```
   ```
   sapb1 query Projects --select "Code,Name,ValidFrom" --filter "startswith(Code, 'a')" --top 20
   ```

   The id is the string `Code`, so a by-id read looks like `GET /b1s/v1/Projects('PRJ01')`.

---
