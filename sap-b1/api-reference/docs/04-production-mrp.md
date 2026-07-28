# SAP B1 Service Layer — Production & MRP

The **9 services** in the `production-mrp` domain. They cover manufacturing
production orders plus the **resource** master (machines / labour / capacity)
that production consumes: the readable resource entities (`Resources`,
`ResourceGroups`, `ResourceProperties`, `ResourceCapacities`) and the four
`*Service_GetList` POST convenience wrappers that return the same data.

Everything documented here is grounded in `catalog/services.json` (exact
operations) and `raw/service-layer-api-reference.html` (descriptions + real
field names from the `$select` / payload examples). **Nothing is invented** —
where the HTML gives no field, it says so.

> **Read-only tool note.** The `sapb1` CLI only ever issues OData `GET` (plus
> `POST /Login` `/Logout`). So the **read entities** below map directly to
> `sapb1 query <Entity>`. The four **`*Service_GetList`** endpoints are `POST`
> functions and are **not** reachable through the read-only CLI — but they
> return the same rows you can already `GET` from the matching entity, so use
> the entity form instead. Not sure a field exists on your DB? Run
> `sapb1 fields <Entity>` (live `GET <Entity>?$top=1`) or query `$metadata`.

---

## ProductionOrders

**(1) Purpose:** Manufacturing production orders — the work orders that turn a
bill-of-materials parent item into finished goods (`ItemNo`, `PlannedQuantity`,
`DueDate`, `Warehouse`, `ProductionOrderStatus` confirm the manufacturing shape).

**(2) Type:** readable ENTITY (has GET).

**(3) Operations** (exactly as in the catalog):
- `GET ProductionOrders(id)`
- `GET ProductionOrders`
- `POST ProductionOrders`
- `PATCH ProductionOrders(id)`
- `POST ProductionOrders(id)/Cancel`

**(4) Real fields** (from HTML `$select` + payload examples): `AbsoluteEntry`
(key), `DocumentNumber`, `Series`, `ItemNo`, `PlannedQuantity`, `DueDate`,
`PostingDate`, `Warehouse`, `ProductionOrderStatus`, `Remarks`.

**Example pair — open production orders for a BOM item:**
```
GET /b1s/v1/ProductionOrders?$select=AbsoluteEntry,DocumentNumber,ItemNo,PlannedQuantity,Warehouse&$top=20&$filter=ItemNo eq 'bom1'
```
```bash
sapb1 query ProductionOrders --select AbsoluteEntry,DocumentNumber,ItemNo,PlannedQuantity,Warehouse --filter "ItemNo eq 'bom1'" --top 20
```

---

## ResourceCapacities

**(1) Purpose:** Per-date available/consumed capacity records for a resource —
how much of a resource is available or booked on a given day (`Code`, `Date`,
`Capacity`, `Warehouse`).

**(2) Type:** readable ENTITY (has GET).

**(3) Operations:**
- `GET ResourceCapacities(id)`
- `GET ResourceCapacities`
- `POST ResourceCapacities`
- `PATCH ResourceCapacities(id)`
- `DELETE ResourceCapacities(id)`

**(4) Real fields** (from HTML `$select` + payload examples): `Id` (key),
`Code` (resource code), `Warehouse`, `Capacity`, `Date`, `Type`, `Action`,
`BaseType`, `BaseEntry`, `Memo`.

**Example pair — capacity rows for resource R01 by date:**
```
GET /b1s/v1/ResourceCapacities?$select=Id,Code,Warehouse,Capacity,Date&$top=20&$filter=Id ge 123
```
```bash
sapb1 query ResourceCapacities --select Id,Code,Warehouse,Capacity,Date --filter "Id ge 123" --top 20
```

---

## ResourceGroups

**(1) Purpose:** Groupings of resources of the same `Type`, carrying up to ten
standard-cost buckets (`Cost1`–`Cost10` / `CostName1`–`CostName10`) shared by
their member resources.

**(2) Type:** readable ENTITY (has GET).

**(3) Operations:**
- `GET ResourceGroups(id)`
- `GET ResourceGroups`
- `POST ResourceGroups`
- `PATCH ResourceGroups(id)`
- `DELETE ResourceGroups(id)`

**(4) Real fields** (from HTML `$select` + payload examples): `Code` (key),
`Name`, `Type`, `NumOfUnitsText`, `Cost1`, `CostName1`.

**Example pair — list resource groups:**
```
GET /b1s/v1/ResourceGroups?$select=Code,Name,Type&$top=20&$filter=Code ge 123
```
```bash
sapb1 query ResourceGroups --select Code,Name,Type --filter "Code ge 123" --top 20
```

---

## ResourceProperties

**(1) Purpose:** The property/attribute master used to tag and classify
resources (the `Property1`…`Property64` flags on `Resources` decode against
these). (inferred — HTML gives only `Code`, `Name` and the generic
"manipulate 'ResourceProperties'" description)

**(2) Type:** readable ENTITY (has GET).

**(3) Operations:**
- `GET ResourceProperties(id)`
- `GET ResourceProperties`
- `PATCH ResourceProperties(id)`

**(4) Real fields** (from HTML `$select` example): `Code` (key), `Name`.
No other fields are shown in the HTML — for the full list query live `$metadata`
(or `sapb1 fields ResourceProperties`).

**Example pair — list resource properties:**
```
GET /b1s/v1/ResourceProperties?$select=Code,Name&$top=20&$filter=Code ge 123
```
```bash
sapb1 query ResourceProperties --select Code,Name --filter "Code ge 123" --top 20
```

---

## Resources

**(1) Purpose:** The resource master — machines, labour and tools consumed by
production, with per-resource costing (`Cost1`–`Cost10`), a `DefaultWarehouse`,
group membership (`Group`), unit-of-measure/capacity settings and an optional
`LinkedItem`.

**(2) Type:** readable ENTITY (has GET). Note the key is a **string** code
(HTML examples use `Resources('abc')`).

**(3) Operations:**
- `GET Resources(id)`
- `GET Resources`
- `POST Resources`
- `PATCH Resources(id)`
- `DELETE Resources(id)`
- `POST Resources(id)/CreateLinkedItem`

**(4) Real fields** (from HTML `$select` + payload examples): `Code` (key),
`VisCode`, `Series`, `Name`, `ForeignName`, `Group`, `Type`, `DefaultWarehouse`,
`Active`, `UnitOfMeasure`, `LinkedItem`, `Cost1`.

**Example pair — active resources whose code starts with "a":**
```
GET /b1s/v1/Resources?$select=Code,Name,Group,DefaultWarehouse,Active&$top=20&$filter=startswith(Code, 'a')
```
```bash
sapb1 query Resources --select Code,Name,Group,DefaultWarehouse,Active --filter "startswith(Code, 'a')" --top 20
```

---

## ResourceCapacitiesService

**(1) Purpose:** POST function wrapper that returns the list of resource
capacities — the same rows served by the `ResourceCapacities` read entity, plus
a filtered variant. (inferred from the operation names + generic HTML text
"This API enables you to invoke the interfaces defined on 'ResourceCapacitiesService'")

**(2) Type:** function/action Service (POST only, no GET).

**(3) Operations:**
- `POST ResourceCapacitiesService_GetList`
- `POST ResourceCapacitiesService_GetListWithFilter` — body: `{ "ResourceCapacityWithFilterParams": { … } }`

**(4)** Function service — no readable fields. For the read-only `sapb1` CLI use
the entity instead: `sapb1 query ResourceCapacities …` (see above).

---

## ResourceGroupsService

**(1) Purpose:** POST function wrapper that returns the list of resource groups —
the same rows served by the `ResourceGroups` read entity. (inferred from the
operation name + generic HTML text "This API enables you to invoke the
interfaces defined on 'ResourceGroupsService'")

**(2) Type:** function/action Service (POST only, no GET).

**(3) Operations:**
- `POST ResourceGroupsService_GetList`

**(4)** Function service — no readable fields. Read-only CLI equivalent:
`sapb1 query ResourceGroups …` (see above).

---

## ResourcePropertiesService

**(1) Purpose:** POST function wrapper that returns the list of resource
properties — the same rows served by the `ResourceProperties` read entity.
(inferred from the operation name + generic HTML text "This API enables you to
invoke the interfaces defined on 'ResourcePropertiesService'")

**(2) Type:** function/action Service (POST only, no GET).

**(3) Operations:**
- `POST ResourcePropertiesService_GetList`

**(4)** Function service — no readable fields. Read-only CLI equivalent:
`sapb1 query ResourceProperties …` (see above).

---

## ResourcesService

**(1) Purpose:** POST function wrapper that returns the list of resources — the
same rows served by the `Resources` read entity. (inferred from the operation
name + generic HTML text "This API enables you to invoke the interfaces defined
on 'ResourcesService'")

**(2) Type:** function/action Service (POST only, no GET).

**(3) Operations:**
- `POST ResourcesService_GetList`

**(4)** Function service — no readable fields. Read-only CLI equivalent:
`sapb1 query Resources …` (see above).
