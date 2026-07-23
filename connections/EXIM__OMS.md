---
title: EXIM to OMS Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connection, exim, oms, sap, read-only]
---

# EXIM to OMS Connection

## Connection verdict

**Candidate SAP master-key spine plus stock/document reconciliation; no proven direct or federated join.** Both systems were observed under a Jivo Wellness label and both expose SAP-derived items, parties, warehouses, and documents. That is stronger than name-only similarity, but it does not prove the same tenant, HANA schema, extraction time, or identifier namespace.

The safest first edge is not document equality. EXIM supports two different stock grains: `warehouse + category + company + as_of` from the inventory view, and `item + company + as_of` across warehouses from the RM master. OMS must be aggregated to the matching grain before either reconciliation; party and document lookups come only after key profiling.

## Why they connect

- EXIM covers supplier-side imports, raw materials, inventory, purchase documents, receivables/payables, and planning.
- OMS covers customer-side parties, quotations, orders, HANA stock, batches, invoice preparation/review, and SAP logs.
- Both expose FG item codes, business-partner codes, warehouse codes, and SAP document identifiers, allowing candidate joins and cross-stage reconciliation.

## Evidence from system A

System A is EXIM. As of 2026-07-19 it has **65 printed CLI tools**. [[API-INVENTORY]] has 67 read-table rows but repeats `GET /dc/`, leaving **66 unique read-labelled routes**.

The apparent GRPO read `GET /sap_sync/open-grpos/` remains unsafe: its sync namespace and `open_grpos:[sync]` permission conflict with its data-returning response, and [[sap_sync_open-grpos]] says it may refresh from SAP. It is excluded from safe recipes until that side effect is disproved.

Relevant EXIM evidence includes:

- SAP-synced RM/FG `item_code`, `item_name`, pack, brand, variety, and category in [[items_rm]] and [[items_fg]].
- `card_code` / `card_name` on [[parties]] and vendor codes on stock and open-PO views.
- `PO_NUMBER`, `VENDOR_CODE`, `ItemCode`, warehouse, quantities, and dates on [[sap-sync_open-pos]].
- Separate internal and display document fields on open AP: `DB Primary Key` is described as SAP DocEntry, while `Invoice Number` is the invoice document number in [[sap-sync_open-ap]].
- Warehouse/category inventory and planning views in [[sap-sync_inventory]], [[sap-sync_finished-inventory]], and [[sap-sync_monthly-planning]].

## Evidence from system B

System B is OMS. [[OMS_MAP]] records that the 2026-07-19 recon account was scoped to **Jivo Wellness (id 1)**, while cross-company parity was not observed. [[OMS_VERIFICATION]] records **73 spec/manifest/MCP GET entries but 72 registered runtime endpoint commands** because invoice history is unregistered against a missing backend route; visibility is also role-dependent.

OMS exposes:

- `item_code`, `item_name`, category, pack, `warehouse_code`, stock, demand, and leftover values on the HANA stock view in [[OMS_Stock]].
- `ItemCode`, `ItemName`, brand, variety, subgroup, SKU text, and `TotalQty` on the HANA FG master.
- `CardCode` / `CardName` on open parties and customers, and lower-case `card_code` on OMS orders in [[OMS_Orders]].
- Both `DocEntry` and `DocNum` on HANA sales orders, with `ItemCode` and `WhsCode` at line level in [[OMS_Stock]] and [[OMS_Invoices]].
- OMS-local `id` and `order_number` for workflow records; those are not SAP `DocEntry` or `DocNum`.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | implicit Jivo Wellness scope | login company `Jivo Wellness`, id `1` | verify same legal entity, SAP schema, and effective dates | **Candidate — medium, not proven** |
| `item_key` | `item_code` / `ItemCode`, `item_name` | `item_code` / `ItemCode`, `item_name` / `ItemName` | company/schema, item name, pack/UOM, active flag, extract date | **Candidate shared field — medium** |
| `party_key` | `card_code`, `vendor_code`, `VENDOR_CODE` | `CardCode`, `card_code` | company, BP role/customer-vendor type, exact code; name as check | **Candidate shared field — medium** |
| `warehouse_key` | `WAREHOUSE` / `Warehouse` | `warehouse_code` / `WhsCode` | company/schema, exact code, item, UOM, as-of time | **Candidate shared field — medium** |
| `sap_doc_entry_key` | `DB Primary Key` where explicitly documented as DocEntry | `DocEntry` | company, SAP object/document type, source table | **Candidate — low across different document families** |
| `sap_doc_number_key` | `Invoice Number`, `PO_NUMBER`, `grpo_number` | `DocNum` or explicit order/invoice document number | company, document type, posting date; never compare to DocEntry | **Candidate — low** |
| `warehouse_category_stock_key` | warehouse + category + `Total` | OMS item/warehouse stock aggregated through a validated item-to-category map | same company/schema, category definition, warehouse, UOM, exclusions, and exact as-of time | **Reconciliation join — medium-low** |
| `item_all_warehouse_stock_key` | RM-master item + `total_qty` without warehouse grain | OMS item stock aggregated across the explicitly matching warehouse set | same company/schema, item, warehouse-set definition, UOM, exclusions, and exact as-of time | **Reconciliation join — medium-low** |
| `planning_demand_key` | month/category planning and import/open-PO quantities | open-order item quantities and pending demand | company, item bridge, month/date window, status, UOM | **Semantic join — medium-low** |

SAP `DocEntry` and `DocNum` must never be conflated. OMS exposes both in the same sales-order row, demonstrating that they are distinct fields; EXIM also separates an AP internal key from its invoice number.

## Read-only questions unlocked

- Do EXIM and OMS expose the same active item and party codes inside a verified Jivo Wellness scope?
- Which warehouse/category totals disagree after category mapping, UOM, and as-of alignment?
- Which item totals disagree only after OMS warehouses are explicitly aggregated to the all-warehouse grain used by the EXIM RM master?
- Do imported/open-PO quantities plausibly cover OMS open-order demand for the same validated item and period?
- Which OMS parties or items are missing from EXIM's SAP-synced masters, and vice versa?

## Gaps/do-not-assume

- A shared “Jivo Wellness” label is not proof of the same SAP company database.
- Matching code fields are candidates, not evidence that current values share one namespace.
- EXIM purchase/AP documents and OMS sales-order/invoice documents are different SAP object types; numeric equality alone is meaningless.
- OMS role-gated empty results are not business zeroes.
- Extract times and stock grains differ; a difference is a reconciliation result, not permission to overwrite either source.
- No running federated join exists, and `/sap_sync/open-grpos/` remains excluded.

## Validation checklist

- [ ] Confirm the legal entity and SAP schema behind both Jivo Wellness scopes.
- [ ] Profile exact item, party, and warehouse overlap with names, pack/UOM, and active/deleted flags.
- [ ] Store separate typed fields for `DocEntry`, `DocNum`, OMS local order id, OMS `order_number`, PO number, invoice number, and GRPO number.
- [ ] Define metric grain and common as-of time before stock comparison.
- [ ] Compare only like document types and retain source-system provenance.
- [ ] Publish unmatched, one-to-many, and collision counts rather than silently dropping rows.
- [ ] Keep all reads on registered safe surfaces and exclude `/sap_sync/open-grpos/`.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[OMS_HUB]] · [[EXIM_MAP]] · [[OMS_MAP]] · [[READ_ONLY_LAW]]
