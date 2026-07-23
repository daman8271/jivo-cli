---
title: OMS to JSAP Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, oms, jsap, sap, workflow-context, read-only]
---

# OMS ↔ JSAP

Evidence below is repository-verified as of 2026-07-19 unless a narrower date is stated.

## Connection verdict

**Shared SAP-key candidates plus workflow context.** OMS exposes customer orders, parties, finished goods, HANA sales orders, invoices, and SAP logs. JSAP exposes company-qualified SAP source documents, BP and inventory reads, budget approvals, bill verification, reports, tasks, tickets, and document history. The edge is useful, but every SAP document match must be composite and every workflow match must remain contextual.

There is no running federated join between OMS and JSAP as of 2026-07-19. Matching names or raw numeric ids are not sufficient evidence.

## Why they connect

- Both systems surface SAP-shaped business identifiers such as `CardCode`, item code, `DocEntry`, and `DocNum`.
- OMS explains the commercial/order side; JSAP can explain an existing approval, bill, task, ticket, document bundle, or responsible person around a record.
- JSAP source-document and report reads can help determine whether an OMS-visible SAP-related event has related governance context, provided database/company and document type are known.

## Evidence from system A — OMS

- [[OMS_VERIFICATION]] records 73 GET entries in the OMS spec/manifest/MCP registry but **72 registered runtime endpoint commands as of 2026-07-19**; the nonexistent live `invoices history` route is not callable from the runtime tree.
- [[OMS_Orders]] exposes OMS `id`, `order_number`, `card_code`, item-level `item_code`, order dates/statuses, and `sap_doc_number`. The exact identifier kind of `sap_doc_number` must be profiled before treating it as `DocNum` or `DocEntry`.
- [[OMS_Stock]] exposes HANA sales-order headers with both `DocEntry` and `DocNum`, `CardCode`, `DocDate`, and lines with `ItemCode`, `OpenQty`, and `WhsCode`.
- [[OMS_SAP_Sync]] exposes party and product masters through `card_code` and `item_code`, with row category values such as MART, OIL, and BEVERAGES. Repeated codes across categories mean bare code equality is insufficient.
- OMS local companies are Jivo Wellness id `1` and Jivo Mart id `2`. Some HANA surfaces do not expose a database/schema field, leaving a key qualifier missing.
- The verification pass used a Wellness admin account. All 14 tracker reads returned `403`; non-admin role behavior and Jivo Mart were not exercised, so those states remain unverified rather than empty.

## Evidence from system B — JSAP

- [[JSAP_MAP]] records a 146-command read-only CLI as of 2026-07-19 across documents, reports, BP master, inventory audit, bills, tasks, tickets, hierarchy, and Document Hub; 138 commands returned live data in the final sweep, while failures/gates remain access states.
- [[DocumentManagement]] exposes source documents with `databaseName`, `docEntry`, `docNum`, `docDate`, `cardCode`, and `cardName`; the endpoint family supplies the document type such as PO, GRPO, AP Draft, or Goods Return.
- [[Reports]] exposes budget records with `objType`, `company`, `companyId`, `docEntry`, `objectName`, `cardCode`, dates, approval owner/approver, and stage flow. [[InventoryAudit]] exposes `itemCode`, warehouse, system quantity, physical quantity, and differences.
- JSAP company ids are strictly local: `1` = JIVO OIL and `2` = JIVO BEVERAGE. Those values collide with OMS meanings and must never be joined numerically.
- A JSAP SAP document key requires **database/company + SAP object type + `DocEntry`**. `DocNum` is a separate identifier and must never be silently equated with `DocEntry`.
- [[DocumentManagement]] documents `GetLastBundleId?mode=select` as read-only, while `mode=update` mutates the counter despite using GET. [[DocumentHub]] documents that Download may append an activity-log row; confidential file/folder unlocks are POST state changes and are forbidden.
- JSAP can expose names, email/phone, salary/demographic fields, audit IPs, attachment metadata, and file streams. Return only purpose-authorized fields, and never route raw binary into normalized text without a tested byte-safe adapter.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | OMS id `1` Wellness / `2` Mart; category MART/OIL/BEVERAGES | JSAP id `1` Oil / `2` Beverage; `databaseName` | Dated cross-system company and database alias table; raw numeric equality forbidden | Proven collision; no direct join |
| `sap_docentry_key` | HANA `DocEntry`; OMS order field only if proven to be DocEntry | `docEntry` | Canonical company, SAP database/schema, object type, id kind=`DocEntry` | Shared field shape; candidate equality, medium |
| `sap_docnum_key` | HANA `DocNum`; possibly `sap_doc_number` after profiling | `docNum` / document `docId` only when its kind is proven | Same company/database and object type; id kind=`DocNum`; never compare to DocEntry | Candidate join; low to medium |
| `party_key` | `card_code` / `CardCode` | `cardCode` | Company/database, BP type, normalized case/whitespace, and live overlap profiling | Proven shared business field; candidate equality, medium |
| `item_key` | `item_code` / `ItemCode` | Inventory Audit `itemCode` | Company/database, item name, pack, UOM, and as-of date | Proven shared business field; candidate equality, medium |
| `warehouse_key` | `WhsCode`, `warehouse_code`, dispatch branch | Inventory Audit `warehouse`; document branch | Company/database plus a validated warehouse alias table | Candidate join; low |
| `oms_order_key` | OMS `id` and `order_number` | No structured OMS-order reference in current JSAP task/ticket schemas | Explicit external reference in an existing JSAP record or a JivoGPT-owned context edge | Missing direct field; context only |
| `workflow_context_key` | order/invoice status, user, date, party, amount | budget/task/ticket/bill ids, status, owner, assignee, dates | Deterministic SAP key preferred; otherwise semantic retrieval with human confirmation | Context join; low to medium |

## Read-only questions unlocked

1. For a company/database-qualified SAP party, what does OMS show about orders while JSAP shows about BP, approval, or existing work context?
2. Does a qualified OMS HANA `DocEntry` have a JSAP record of the same object type, and what approval stage or owner does JSAP report?
3. Which mapped items have OMS demand/stock evidence and a related JSAP inventory-audit variance?
4. Is an OMS order or invoice exception already referenced by an existing JSAP task, ticket, bill-verification record, document bundle, or MoM?
5. Are unmatched records caused by company/database scope, object-type mismatch, access gating, or genuinely missing context?

## Gaps/do-not-assume

- Never join raw company ids: OMS `1`/`2` and JSAP `1`/`2` name different companies.
- Never join `DocEntry` to `DocNum`. Even like-for-like document ids require database/company and object type.
- Do not assume OMS `sap_doc_number` is DocEntry or DocNum until its live values and generating endpoint are profiled.
- Do not assume an OMS A/R sales flow matches a JSAP A/P invoice, PO, GRPO, Goods Return, budget, or voucher merely because the numbers match.
- Do not treat task/ticket text similarity as a durable foreign key. Require an explicit source reference or label it semantic context.
- Do not call JSAP `GetLastBundleId` with `mode=update`; do not unlock confidential content; and treat Document Hub Download as read-with-possible-side-log.
- Minimize personal and attachment fields to the authorized question; HTTP 200 is not entitlement. Do not ingest raw file bytes through the current non-byte-safe path.
- Do not turn a role-gated, empty, 404, or 500 JSAP/OMS response into a zero-valued business fact.

## Validation checklist

- [ ] Create an explicit OMS-to-JSAP company/database mapping; prove it with sampled rows, not labels alone.
- [ ] Normalize documents as `source + company + database/schema + object_type + id_kind + raw_id`.
- [ ] Profile `sap_doc_number`, `DocEntry`, and `DocNum` separately and publish collision/unmatched counts.
- [ ] Validate `CardCode` and item-code overlap by company/database, name, pack, and UOM.
- [ ] Require existing JSAP tasks/tickets to contain an explicit source reference before promoting a context edge to deterministic.
- [ ] Record event dates, query dates, access state, and provenance from both connectors.
- [ ] Use `GetLastBundleId` only with hardcoded `mode=select`; skip confidential unlock paths.
- [ ] Avoid Document Hub Download in zero-side-effect mode; use metadata/activity reads and already-authorized preview where appropriate.
- [ ] Enforce purpose/role authorization and a minimal output allowlist; keep raw binary out until a byte-safe adapter is tested.
- [ ] Never approve, create, update, assign, upload, sync, or write back through either source.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[OMS_HUB]] · [[JSAP_HUB]] · [[OMS_VERIFICATION]] · [[OMS_Orders]] · [[OMS_Stock]] · [[OMS_SAP_Sync]] · [[JSAP_MAP]] · [[DocumentManagement]] · [[Reports]] · [[InventoryAudit]] · [[DocumentHub]] · [[READ_ONLY_LAW]]
