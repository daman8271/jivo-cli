# SAP Business One Service Layer — Service & Contracts

Reference for the **Service & Contracts** domain: 16 Service Layer services covering
the Service module (service calls, their lookup dimensions, the knowledge base) and
the Contracts module (service contracts and contract templates).

**16 services total — 10 are readable entities (have a `GET`), 6 are POST-only
function services.** All descriptions, operations, and field names below come from
the bundled `catalog/services.json` and `raw/service-layer-api-reference.html`
(paths shown at `/b1s/v1/…` exactly as the reference documents them; the `sapb1`
CLI handles the version for you). Nothing here is invented — where the reference
does not list a field, it says so.

Legend:
- **readable ENTITY** — exposes `GET` (collection + by-id); queryable with OData `$select/$filter/$orderby` and the `sapb1 query` tool.
- **function/action Service** — POST-only RPC-style call; not OData-queryable. Invoke by POSTing to the operation path.

---

## ServiceCallOriginsService

1. **Purpose:** Invokes the interfaces defined on `ServiceCallOriginsService` — returns the list of service-call origins (how a call was raised). *(inferred — reference text is generic: "This API enables you to invoke the interfaces defined on 'ServiceCallOriginsService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ServiceCallOriginsService_GetServiceCallOriginList`

To read origins as a queryable table, use the **ServiceCallOrigins** entity below instead.

---

## ServiceCallProblemSubTypesService

1. **Purpose:** Invokes the interfaces defined on `ServiceCallProblemSubTypesService` — returns the list of service-call problem sub-types. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'ServiceCallProblemSubTypesService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ServiceCallProblemSubTypesService_GetServiceCallProblemSubTypeList`

For a queryable table, use the **ServiceCallProblemSubTypes** entity below.

---

## ServiceCallProblemTypesService

1. **Purpose:** Invokes the interfaces defined on `ServiceCallProblemTypesService` — returns the list of service-call problem types. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'ServiceCallProblemTypesService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ServiceCallProblemTypesService_GetServiceCallProblemTypeList`

For a queryable table, use the **ServiceCallProblemTypes** entity below.

---

## ServiceCallSolutionStatusService

1. **Purpose:** Invokes the interfaces defined on `ServiceCallSolutionStatusService` — returns the list of solution-status values used when resolving a service call. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'ServiceCallSolutionStatusService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ServiceCallSolutionStatusService_GetServiceCallSolutionStatusList`

For a queryable table, use the **ServiceCallSolutionStatus** entity below.

---

## ServiceCallStatusService

1. **Purpose:** Invokes the interfaces defined on `ServiceCallStatusService` — returns the list of service-call status values (open, closed, etc.). *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'ServiceCallStatusService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ServiceCallStatusService_GetServiceCallStatusList`

For a queryable table, use the **ServiceCallStatus** entity below.

---

## ServiceCallTypesService

1. **Purpose:** Invokes the interfaces defined on `ServiceCallTypesService` — returns the list of service-call types. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'ServiceCallTypesService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST ServiceCallTypesService_GetServiceCallTypeList`

For a queryable table, use the **ServiceCallTypes** entity below.

---

## ContractTemplates

1. **Purpose:** Manage service-contract templates — reusable blueprints used to create new service contracts. *(inferred — reference text: "This entity enables you to manipulate 'ContractTemplates'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET ContractTemplates(id)`
   - `GET ContractTemplates`
   - `POST ContractTemplates`
   - `PATCH ContractTemplates(id)`
   - `DELETE ContractTemplates(id)`
4. **Fields (real, from the reference example):** `TemplateName`, `TemplateIsDeleted`, `TemplateIsRenewal` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ContractTemplates?$select=TemplateName,TemplateIsDeleted,TemplateIsRenewal&$filter=startswith(TemplateName, 'a')&$top=20
   ```
   ```
   sapb1 query ContractTemplates --select "TemplateName,TemplateIsDeleted,TemplateIsRenewal" --filter "startswith(TemplateName, 'a')" --top 20
   ```

---

## KnowledgeBaseSolutions

1. **Purpose:** Manage knowledge-base solutions in the Service module — reusable, documented fixes agents attach to service calls. (from reference: "It represents the knowledge base solutions in the Service module.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET KnowledgeBaseSolutions(id)`
   - `GET KnowledgeBaseSolutions`
   - `POST KnowledgeBaseSolutions`
   - `PATCH KnowledgeBaseSolutions(id)`
   - `DELETE KnowledgeBaseSolutions(id)`
4. **Fields (real, from the reference examples):** `SolutionCode` (key), `ItemCode`, `Status`, `Owner` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/KnowledgeBaseSolutions?$select=SolutionCode,ItemCode,Status,Owner&$filter=SolutionCode ge 123&$top=20
   ```
   ```
   sapb1 query KnowledgeBaseSolutions --select "SolutionCode,ItemCode,Status,Owner" --filter "SolutionCode ge 123" --top 20
   ```

---

## ServiceCallOrigins

1. **Purpose:** Manage the service-call **origin** lookup values (the channel a call came in through). *(inferred — reference text: "This entity enables you to manipulate 'ServiceCallOrigins'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET ServiceCallOrigins(id)`
   - `GET ServiceCallOrigins`
   - `POST ServiceCallOrigins`
   - `PATCH ServiceCallOrigins(id)`
   - `DELETE ServiceCallOrigins(id)`
4. **Fields (real, from the reference example):** `OriginID`, `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ServiceCallOrigins?$select=OriginID,Name,Description&$filter=OriginID ge 1&$top=20
   ```
   ```
   sapb1 query ServiceCallOrigins --select "OriginID,Name,Description" --filter "OriginID ge 1" --top 20
   ```

---

## ServiceCallProblemSubTypes

1. **Purpose:** Manage the service-call **problem sub-type** lookup values (a finer classification under a problem type). *(inferred — reference text: "This entity enables you to manipulate 'ServiceCallProblemSubTypes'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET ServiceCallProblemSubTypes(id)`
   - `GET ServiceCallProblemSubTypes`
   - `POST ServiceCallProblemSubTypes`
   - `PATCH ServiceCallProblemSubTypes(id)`
   - `DELETE ServiceCallProblemSubTypes(id)`
4. **Fields (real, from the reference example):** `ProblemSubTypeID`, `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ServiceCallProblemSubTypes?$select=ProblemSubTypeID,Name,Description&$filter=ProblemSubTypeID ge 1&$top=20
   ```
   ```
   sapb1 query ServiceCallProblemSubTypes --select "ProblemSubTypeID,Name,Description" --filter "ProblemSubTypeID ge 1" --top 20
   ```

---

## ServiceCallProblemTypes

1. **Purpose:** Manage the service-call **problem type** lookup values (the top-level classification of a reported problem). *(inferred — reference text: "This entity enables you to manipulate 'ServiceCallProblemTypes'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET ServiceCallProblemTypes(id)`
   - `GET ServiceCallProblemTypes`
   - `POST ServiceCallProblemTypes`
   - `PATCH ServiceCallProblemTypes(id)`
   - `DELETE ServiceCallProblemTypes(id)`
4. **Fields (real, from the reference example):** `ProblemTypeID`, `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ServiceCallProblemTypes?$select=ProblemTypeID,Name,Description&$filter=ProblemTypeID ge 1&$top=20
   ```
   ```
   sapb1 query ServiceCallProblemTypes --select "ProblemTypeID,Name,Description" --filter "ProblemTypeID ge 1" --top 20
   ```

---

## ServiceCalls

1. **Purpose:** Manage service calls in the Service module — the records that track service and support activities you provide to customers. (from reference: "Service calls are used to manage service and support activities that you provide to your customers.")
2. **Type:** readable ENTITY (also exposes a `Close` action).
3. **Operations:**
   - `GET ServiceCalls(id)`
   - `GET ServiceCalls`
   - `POST ServiceCalls`
   - `PATCH ServiceCalls(id)`
   - `DELETE ServiceCalls(id)`
   - `POST ServiceCalls(id)/Close` — "Invoke the method 'Close' on this EntitySet with the specified id." (closes an open service call)
4. **Fields (real, from the reference examples):** `ServiceCallID` (key), `Subject`, `CustomerCode` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ServiceCalls?$select=ServiceCallID,Subject,CustomerCode&$filter=CustomerCode eq 'C20000'&$top=20
   ```
   ```
   sapb1 query ServiceCalls --select "ServiceCallID,Subject,CustomerCode" --filter "CustomerCode eq 'C20000'" --top 20
   ```

   Close a call (action, not a read):
   ```
   POST /b1s/v1/ServiceCalls(123)/Close
   ```

---

## ServiceCallSolutionStatus

1. **Purpose:** Manage the **solution-status** lookup values used when recording how a service call was resolved. *(inferred — reference text: "This entity enables you to manipulate 'ServiceCallSolutionStatus'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET ServiceCallSolutionStatus(id)`
   - `GET ServiceCallSolutionStatus`
   - `POST ServiceCallSolutionStatus`
   - `PATCH ServiceCallSolutionStatus(id)`
   - `DELETE ServiceCallSolutionStatus(id)`
4. **Fields (real, from the reference example):** `StatusId`, `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ServiceCallSolutionStatus?$select=StatusId,Name,Description&$filter=StatusId ge 1&$top=20
   ```
   ```
   sapb1 query ServiceCallSolutionStatus --select "StatusId,Name,Description" --filter "StatusId ge 1" --top 20
   ```

---

## ServiceCallStatus

1. **Purpose:** Manage the **status** lookup values a service call can be in (e.g. open / closed and user-defined statuses). *(inferred — reference text: "This entity enables you to manipulate 'ServiceCallStatus'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET ServiceCallStatus(id)`
   - `GET ServiceCallStatus`
   - `POST ServiceCallStatus`
   - `PATCH ServiceCallStatus(id)`
   - `DELETE ServiceCallStatus(id)`
4. **Fields (real, from the reference example):** `StatusId`, `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ServiceCallStatus?$select=StatusId,Name,Description&$filter=StatusId ge 1&$top=20
   ```
   ```
   sapb1 query ServiceCallStatus --select "StatusId,Name,Description" --filter "StatusId ge 1" --top 20
   ```

---

## ServiceCallTypes

1. **Purpose:** Manage the service-call **type** lookup values (the kind/category of a service call). *(inferred — reference text: "This entity enables you to manipulate 'ServiceCallTypes'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET ServiceCallTypes(id)`
   - `GET ServiceCallTypes`
   - `POST ServiceCallTypes`
   - `PATCH ServiceCallTypes(id)`
   - `DELETE ServiceCallTypes(id)`
4. **Fields (real, from the reference example):** `CallTypeID`, `Name`, `Description` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ServiceCallTypes?$select=CallTypeID,Name,Description&$filter=CallTypeID ge 1&$top=20
   ```
   ```
   sapb1 query ServiceCallTypes --select "CallTypeID,Name,Description" --filter "CallTypeID ge 1" --top 20
   ```

---

## ServiceContracts

1. **Purpose:** Manage the service-contracts table in the Service module — add, retrieve by key, update, and remove service contracts (SLA/warranty agreements with customers). (from reference: "This object enables you to do the following: Add a service contract; retrieve a service contract by its key; update a service contract; remove a service contract.")
2. **Type:** readable ENTITY (also exposes `Cancel` and `Close` actions).
3. **Operations:**
   - `GET ServiceContracts(id)`
   - `GET ServiceContracts`
   - `POST ServiceContracts`
   - `PATCH ServiceContracts(id)`
   - `DELETE ServiceContracts(id)`
   - `POST ServiceContracts(id)/Cancel` — "Invoke the method 'Cancel' on this EntitySet with the specified id."
   - `POST ServiceContracts(id)/Close` — "Invoke the method 'Close' on this EntitySet with the specified id."
4. **Fields (real, from the reference examples):** `ContractID` (key), `CustomerCode`, `CustomerName` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/ServiceContracts?$select=ContractID,CustomerCode,CustomerName&$filter=ContractID ge 123&$top=20
   ```
   ```
   sapb1 query ServiceContracts --select "ContractID,CustomerCode,CustomerName" --filter "ContractID ge 123" --top 20
   ```

   Cancel / close a contract (actions, not reads):
   ```
   POST /b1s/v1/ServiceContracts(123)/Cancel
   POST /b1s/v1/ServiceContracts(123)/Close
   ```

---

### Notes on grounding

- Field lists are the exact identifiers that appear in the reference's own `$select=` examples. They are a **useful subset**, not the full property set — run `sapb1 fields <Entity>` or `GET /b1s/v1/$metadata` for the complete schema.
- The six `…Service` entries are POST-only RPC operations returning a list; they have **no** `GET` and cannot be filtered/ordered. When you need a queryable table of the same data, use the matching entity (`ServiceCallOrigins`, `ServiceCallProblemTypes`, `ServiceCallStatus`, etc.).
- `ServiceCalls/Close`, `ServiceContracts/Cancel`, and `ServiceContracts/Close` are state-changing POST actions — they are not readable and are listed only for completeness.
