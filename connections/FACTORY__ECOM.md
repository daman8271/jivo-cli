---
title: Factory to Ecom Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, factory, ecom, sap, marketplace, inventory, read-only]
---

# Factory to Ecom Connection

> Evidence and contracts in this note are current as of 2026-07-19 and are governed by [[READ_ONLY_LAW]].

## Connection verdict

**Operational supply-to-market connection with two different join modes.** Factory's SAP item, warehouse, and dispatch fields can form qualified shared-key candidates with Ecom's SAP reads. Factory stock/dispatch versus Ecom marketplace sales, inventory, DOH, state, and platform measures is a reconciliation join, not row-level equality.

There is **no running federated join** between Factory and Ecom as of 2026-07-19. The connection is a read-only normalization and validation contract for a future JivoGPT-owned view.

## Why they connect

- Factory records what JIVO made, stored, transferred, barcoded, and dispatched across Oil, Mart, and Beverages.
- Ecom records what marketplaces, distributors, SAP sales views, inventory dashboards, shipments, states, cities, and platforms report downstream.
- Factory's Oil-to-Mart barcode transfers and Mart dispatch activity supply the business context for downstream Ecom availability and sell-through, but they are not marketplace order foreign keys.
- Both systems expose SAP item, warehouse, and sales-document fields in selected surfaces; dashboard SKU labels require a separate semantic bridge when the code is absent.

## Evidence from system A

Factory has **183 verified GET endpoints** across `JIVO_OIL`, `JIVO_MART`, and `JIVO_BEVERAGES` as of 2026-07-19.

- [[FACTORY_MAP]] distinguishes shared-campus data from company-scoped operations. Warehouse, WMS, Production, Barcode, Dispatch, QC, GRPO, and most dashboards must carry the Factory company code.
- Jivo Oil is the manufacturing source; Jivo Mart is the distribution arm. Factory Barcode records Oil-to-Mart transfers with `item_code`, barcode lineage, quantities, source/destination companies, and dates.
- Factory WMS exposes item-by-warehouse stock, movements, transfers, sales-order backlog, and SAP references. Core fields include `item_code`, warehouse code, `on_hand`, `committed`, `available`, and event date.
- Factory Dispatch exposes SAP bill `doc_num`, dispatch-plan ids, `sap_doc_num`, company-scoped gate/docking records, scan sessions, litres/quantities, and dispatch timestamps.
- Factory production release and FG receipt records expose SAP item codes, production `doc_entry` / `doc_num`, quantities, batches, and receiving warehouse.
- Shared campus masters must not be attributed to one company, while the operational facts above must not be aggregated across Factory companies without an explicit company dimension.

## Evidence from system B

Ecom has **138 registered GET commands** as of 2026-07-19: **137 current SPA GETs plus one retained legacy `month-on-month-sale` route** that is no longer present in the current SPA bundle. This split is documented in [[ECOM_CLI_ENDPOINT_GAP]] and represented in `CLI/ecom-cli/spec.yaml` and the registered Cobra command tree.

The current Ecom MCP is a code-orchestration bridge around the Cobra CLI and local helpers, not 138 separately typed MCP tools.

- Ecom's SAP group exposes item master, finished-goods inventory, stock by warehouse, inventory comparison, distributors, distributor orders/invoices, platform distributors, and sales invoices.
- The retained Ecom notes prove these SAP and dashboard endpoint families exist, but do not retain a reproducible response sample for the exact row fields. Treat the declared item, warehouse, invoice, and nullable dashboard-code shapes as unverified until a redacted probe is preserved and cited.
- Dashboard product labels are not directly joinable to Factory `item_code` without a dated product bridge, whether a particular response carries a code or not.
- Ecom exposes marketplace dimensions including platform slug, state, city, pincode mappings, sales units/value, PO and appointment views, inventory/DOH, ads, and shipment planning.
- The current Ecom account/profile and CLI root expose platforms and permissions but no canonical company selector or company key. A Jivo Mart versus Jivo Wellness company switch is therefore **not proven** for this connection.
- Amazon Shipment Planner is 403-gated for the verified account, and SAP sales-invoice lines currently fail upstream with a HANA 500. Both are access/availability states, not zero data.

## Join contract table

| Canonical key | Factory field | Ecom field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | `Company-Code`, `company_code`, source/destination company | no canonical company field or switch proven | External dated alias/tenant table; source system; never raw numeric id | **Missing on Ecom side** |
| `item_key` | `item_code` in WMS, Barcode, Production, receipts | declared SAP item field; marketplace/dashboard product identifier or label | Preserve a redacted response sample first; then require company/database + item name + pack/UOM and a semantic alias where no stable code exists | **Candidate; Ecom row shape not yet retained** |
| `warehouse_key` | warehouse code, `current_warehouse`, transfer from/to | declared SAP warehouse field | Preserve a response sample, then require company/database + warehouse alias + stock grain + unit | **Candidate; Ecom row shape not yet retained** |
| `sap_sales_document_key` | `doc_num`, `sap_doc_num`, dispatch `documents[]` | declared SAP invoice entry/number fields | Preserve a response sample; require object type, company/database, and exact id kind | **Candidate; unsafe and unverified unqualified** |
| `barcode_or_batch_key` | box/pallet barcode, `batch_number` | no equivalent proven in current Ecom read surfaces | Explicit bridge table required | **Missing direct key** |
| `platform_key` | no marketplace platform on core Factory records | platform slug and platform-distributor mapping | Dated alias registry; optional distributor/CardCode bridge | **Ecom-proven, Factory context only** |
| `geography_key` | warehouse/site/branch context | state, city, pincode, distributor geography | Dated warehouse-to-geography mapping; pincode as string | **Semantic candidate** |
| `supply_reconciliation_key` | item + warehouse + stock/dispatch quantity + date | item/SKU + platform/distributor + inventory/sales/PO quantity + period | Qualified product + unit/pack conversion + platform + geography + as-of/event time | **Reconciliation only** |
| `observed_at` | production, movement, scan, dispatch timestamp | report period, declared transaction date, or data-version time where returned | Preserve response evidence; then require event type + timezone + source freshness | **Factory proven; Ecom conditional on response evidence** |

## Read-only questions unlocked

1. Which qualified Factory finished goods have stock or recent dispatch evidence but weak Ecom availability or sell-through?
2. Do Jivo Mart Factory dispatch quantities reconcile directionally with Ecom primary sales or SAP invoice views for the same item and period?
3. Which Ecom out-of-stock or low-DOH items have recent Oil production or Oil-to-Mart transfer evidence?
4. Which Factory warehouses map to Ecom SAP warehouse stock, and where do their snapshots disagree after timing and units are aligned?
5. Which Ecom platform/state demand concentrations are unsupported by recent Factory supply or dispatch evidence?

## Gaps/do-not-assume

- Do not claim a direct Factory-to-marketplace order foreign key or a running federated database.
- Do not assign Ecom facts to Jivo Mart merely because Ecom is an e-commerce system; Ecom has no proven canonical company switch in the current CLI/profile.
- Do not join raw numeric company ids across systems.
- Do not equate `DocEntry` with `DocNum`, or reuse a document number across object types, companies, or SAP databases.
- Do not join Factory `item_code` to a dashboard label when a stable Ecom product code is missing or unproven. Product name and pack must pass a controlled bridge.
- Do not compare stock, sales, dispatch, PO, DOH, or litres without matching grain, units, time window, platform, and geography.
- Do not treat Ecom Shipment Planner 403 responses or SAP line-query 500 responses as empty business facts.
- The retained Ecom legacy route is part of the 138-command runtime count but not one of the 137 current SPA GETs.
- Factory shared-campus masters and company-scoped operational records must remain separately attributed.

## Validation checklist

- [ ] Establish a canonical company/tenant registry; leave Ecom company unresolved until proven.
- [ ] Profile Factory-versus-Ecom SAP item-code overlap by company/database, name, and pack.
- [ ] Build and review the semantic product alias table for Ecom rows without a proven stable product code.
- [ ] Validate warehouse-code equivalence and stock units before any quantity comparison.
- [ ] Resolve every document number to object type, ID kind, company, and SAP database.
- [ ] Define platform and geography aliases with dated provenance.
- [ ] Compare supply and demand only at an explicit item × geography/warehouse × period grain.
- [ ] Carry source status and freshness, including 403 and upstream-error states.
- [ ] Publish matched, conflicting, and unmatched counts for every materialized view.
- [ ] Keep all source calls read-only and all derived writes inside JivoGPT-owned storage.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[FACTORY_HUB]] · [[ECOM_HUB]] · [[FACTORY_MAP]] · [[FACTORY_VERIFICATION]] · [[ECOM_MAP]] · [[ECOM_APP_SURVEY]] · [[ECOM_CLI_ENDPOINT_GAP]] · [[READ_ONLY_LAW]]
