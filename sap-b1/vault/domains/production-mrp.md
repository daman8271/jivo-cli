# Production & MRP

Manufacturing at the oil plant: [[ProductionOrders]] (7.7k live) plan and track making finished SKUs from bill-of-material components (BOMs themselves live in [[ProductTrees]] under System & Other). The resource layer models machine/labour capacity: [[Resources]] masters grouped by [[ResourceGroups]], daily availability in [[ResourceCapacities]] (19k rows), and custom attributes via [[ResourceProperties]]. The RPC-side services mirror these masters for write operations we never use.

Part of the [[00-SAP-B1-Atlas]] — 9 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[ResourceCapacities]] **(19,003 rows)** — Per-day capacity ledger for each resource and warehouse — available/committed/consumed capacity entries driving production scheduling.
- [[ProductionOrders]] **(7,683 rows)** — Manufacturing work orders that plan and track production of an item (BOM components, quantities, dates, status) in JIVO's oil plant.
- [[ResourceProperties]] **(64 rows)** — Master list of tag-like property definitions that can be flagged on resources for classification and filtering.
- [[Resources]] **(7 rows)** — Master data for production resources (machines/labor lines) with costs, group, default warehouse, and optional linked item — 7 resources in the oil plant.
- [[ResourceGroups]] **(1 row)** — Categorizes production resources into groups with default cost-component names and rates (machine vs labor).

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[ResourceCapacitiesService]] — RPC-style function service to fetch lists of resource capacity records, optionally filtered.
- [[ResourceGroupsService]] — RPC-style function service returning the list of production resource groups.
- [[ResourcePropertiesService]] — RPC-style function service returning the list of resource property definitions.
- [[ResourcesService]] — RPC-style function service returning the list of production resources (machines/labor).
