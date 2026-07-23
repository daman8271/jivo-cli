---
title: Factory to OMS Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, factory, oms, sap, inventory, dispatch, read-only]
---

# Factory to OMS Connection

> Evidence and contracts in this note are current as of 2026-07-19 and are governed by [[READ_ONLY_LAW]].

## Connection verdict

**Strong operational join candidate, not an implemented join.** Factory observes production, company-scoped warehouse stock, barcodes, batches, dispatch plans, and SAP-linked plant documents. OMS observes orders, quotations, parties, HANA warehouse stock, open sales orders, batches, invoices, and SAP logs. Their strongest candidate spine is a qualified SAP item, warehouse, and document model; their stock and demand measures are reconciliation fields rather than interchangeable facts.

There is **no running federated join** between the two systems in JivoGPT as of 2026-07-19. A valid implementation must read both connectors independently, normalize into JivoGPT-owned storage, preserve provenance, and report unmatched records.

## Why they connect

- Factory covers the physical make-store-scan-dispatch stages immediately upstream of OMS order, stock-check, quotation, and invoice views.
- Both systems expose SAP-style finished-good codes, warehouse codes, document identifiers, quantities, dates, and batches.
- Factory can explain whether goods were produced, transferred, available, scanned, or dispatched; OMS can explain open demand, party allocation, quotation status, and invoice workflow.
- The same-looking numbers do not prove one shared database. The safe output is a qualified candidate join or a time-bounded reconciliation, never an inferred write-back or status transition.

## Evidence from system A

Factory's verified read surface is **183 GET endpoints** across `JIVO_OIL`, `JIVO_MART`, and `JIVO_BEVERAGES`; the count is present in `CLI/factory-cli/spec.yaml` and verified in [[FACTORY_VERIFICATION]].

- [[FACTORY_MAP]] proves that the campus identity, gate, person, vehicle, driver, and selected notification surfaces are shared, while Dispatch, QC, GRPO, Warehouse/WMS, Production, Maintenance, Barcode, and Dashboards are company-scoped through the `Company-Code` header.
- Factory company ids are Oil `1`, Mart `2`, and Beverages `3`. Operational requests use the canonical header codes, and the CLI includes company scope in its cache key.
- Factory WMS exposes item-by-warehouse facts such as `item_code`, warehouse code, `on_hand`, `committed`, `available`, `stock_value`, stock status, movement references, and batch-expiry rows.
- Factory production and receipt surfaces expose `item_code`, production `doc_entry` / `doc_num`, planned or produced quantities, `sap_doc_entry`, posting dates, and receiving warehouse.
- Factory Barcode exposes `item_code`, `batch_number`, `current_warehouse`, box/pallet identifiers, dispatch sessions, and Oil-only production-release rows with `doc_entry`, `doc_num`, and production quantities.
- Factory Dispatch and Gate expose SAP-facing `doc_num` / `sap_doc_num`, dispatch-plan ids, `documents[]`, bill values, company codes, gate entries, and dispatch timestamps. These fields do not state by themselves whether a number is a sales order, A/R invoice, GRPO, or another SAP object.

## Evidence from system B

OMS has **73 GET entries in its spec, generated manifest, and MCP registry, but only 72 registered runtime endpoint commands** as of 2026-07-19. [[OMS_VERIFICATION]] and `CLI/oms-cli/internal/cli/invoices.go` show why: `/api/invoice/history/{id}/` exists in the SPA-derived spec but is absent from the deployed backend, so `invoices history` is deliberately unregistered.

- [[OMS_Stock]] documents `hana/product-stock` rows with `item_code`, `warehouse_code`, `warehouse_stock`, `pending_required_qty`, `left_over_stock`, and product/category/pack fields.
- OMS open-sales-order reads expose SAP `DocEntry`, `DocNum`, `CardCode`, `BPL_Id`, dates, status, and lines containing `ItemCode`, `OpenQty`, `WhsCode`, price, and line status.
- OMS order reads expose the local `order_number`, `card_code`, `company`, line `item_code`, dispatch-from fields, quantities, status history, and an optional `sap_doc_number`.
- OMS quotation reads provide an explicit local-to-SAP bridge: OMS order id plus quotation `doc_num` / `doc_entry`; `sap/quotation-log/{order_id}` repeats the mapping as `sap_doc_num` and `sap_doc_entry`.
- OMS SAP masters expose `item_code`, `card_code`, `category`, addresses, branches, and sync timestamps. The same party code can recur under `OIL`, `MART`, and `BEVERAGES`, so category is part of the key.
- OMS was live-studied under a Jivo Wellness company-1 login. Cross-company parity and a canonical Jivo Mart switch were not proven. Some HANA reads appear SAP-wide and accept no company parameter, but that does not prove company-independent semantics.

## Join contract table

| Canonical key | Factory field | OMS field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | `Company-Code`, `company_code`, Factory company id | order `company`, SAP `category`, branch/BPL context, login company | Dated alias map; canonical code/name; source system; never raw numeric equality | **Required qualifier; mapping partly proven** |
| `item_key` | `item_code` in WMS, Barcode, Production, QC, FG receipts | `item_code` or `ItemCode` in product stock, masters, orders, HANA SO lines | Canonical company + SAP database/schema + item name + pack/UOM validation | **Strong candidate** |
| `warehouse_key` | warehouse code, `current_warehouse`, movement from/to warehouse | `warehouse_code`, `WhsCode`, dispatch-from code | Company/database + dated warehouse alias + unit/grain | **Strong candidate** |
| `sap_document_key` | `doc_entry`, `doc_num`, `sap_doc_entry`, `sap_doc_num`, `documents[]` | `DocEntry`, `DocNum`, `sap_doc_entry`, `sap_doc_num`, `sap_doc_number` | SAP object type, company/database, `DocEntry` versus `DocNum`, source endpoint | **Candidate; unsafe unqualified** |
| `oms_order_key` | no proven OMS order id; Factory has dispatch-plan and SAP bill ids | local `id`, `order_number` | Must first resolve OMS order to a qualified SAP document; do not match local integers | **Missing direct key** |
| `party_key` | customer/vendor names and SAP-facing document context; stable Factory card code not proven across all target surfaces | `card_code` / `CardCode`, category | Company/category + exact normalized code; names are validation only | **OMS-proven, Factory bridge incomplete** |
| `batch_key` | `batch_number`, box/pallet lineage | HANA batch-detail rows | Item + warehouse + company/database + batch text + as-of date | **Candidate; live equality unprofiled** |
| `stock_reconciliation_key` | item × warehouse `on_hand`, `committed`, `available`, timestamp | item × warehouse `warehouse_stock`, `pending_required_qty`, `left_over_stock` | Qualified item/warehouse + unit conversion + event/as-of time + source status | **Semantic reconciliation only** |
| `event_time` | production, posting, movement, scan, dispatch dates | order, quotation, SO, invoice, sync dates | Timezone + event type + freshness timestamp; never compare undated snapshots | **Proven shared dimension** |

## Read-only questions unlocked

1. For a qualified item and warehouse, does Factory's available stock cover OMS open-order demand at the same as-of time?
2. Which OMS shortage items have recent Factory production, FG-receipt, barcode, or intercompany-transfer evidence?
3. Which Factory-dispatched SAP documents have a corresponding OMS order, quotation, or invoice context after document type and company are resolved?
4. Which OMS orders remain open even though Factory shows matching item quantities scanned or dispatched?
5. Do batch-aware OMS availability results agree with Factory barcode/batch lineage for the same item, warehouse, company, and date?

## Gaps/do-not-assume

- Do not claim the two APIs share a database or that a live federated query exists.
- Do not join numeric company ids. The verified OMS login calls company id `1` Jivo Wellness, while Factory id `1` is Jivo Oil; the collision is already concrete, not hypothetical.
- Do not equate `DocEntry` with `DocNum`, or reuse either across SAP object types, companies, or databases.
- Do not equate OMS `order_number` with a Factory dispatch-plan, gate, invoice, or GRPO number without an explicit SAP-document bridge.
- Do not treat Factory available stock and OMS left-over stock as the same metric. Their demand, warehouse, timing, and unit rules differ.
- Do not infer Jivo Mart behavior from the OMS Jivo Wellness login. OMS company switching and cross-company parity remain unverified.
- OMS invoice history is dead on the deployed backend and unregistered at runtime; it cannot support an audit trail until the route ships and is re-verified.
- Role-gated or empty OMS queues are visibility states, not zero business activity.

## Validation checklist

- [ ] Build a dated company alias table from Factory codes and OMS category/company values; reject raw numeric joins.
- [ ] Profile exact item-code overlap per canonical company/database and publish matched, conflicting-name, and unmatched counts.
- [ ] Validate warehouse-code overlap and units before comparing quantities.
- [ ] Classify every document field as object type plus `DocEntry` or `DocNum` before matching.
- [ ] Test a sample from OMS order → quotation log → qualified SAP document → Factory dispatch evidence.
- [ ] Test batch matches only with item, warehouse, company, and event date included.
- [ ] Preserve both event time and extraction/as-of time in every reconciliation.
- [ ] Mark access state (`live`, `empty`, `403-gated`, `404-dead`, `upstream-error`) beside every contributing read.
- [ ] Report unmatched rows and confidence; never silently inner-join them away.
- [ ] Confirm all connector calls remain read-only and write only to JivoGPT-owned storage.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[FACTORY_HUB]] · [[OMS_HUB]] · [[FACTORY_MAP]] · [[FACTORY_VERIFICATION]] · [[OMS_MAP]] · [[OMS_VERIFICATION]] · [[OMS_Stock]] · [[OMS_Orders]] · [[OMS_Sales_Quotation]] · [[READ_ONLY_LAW]]
