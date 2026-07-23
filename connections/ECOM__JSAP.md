---
title: Ecom to JSAP Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, ecom, jsap, sap, workflow-context, read-only]
---

# Ecom ↔ JSAP

Evidence below is repository-verified as of 2026-07-19 unless a narrower date is stated.

## Connection verdict

**Context join with a small set of company-qualified SAP-key candidates.** Ecom supplies marketplace performance, inventory, distribution, platform reports, and a SAP read layer. JSAP supplies SAP document/governance views plus people, approvals, bills, tasks, tickets, MoMs, inventory audits, and document history. The most dependable current use is to retrieve existing JSAP context for an Ecom exception; direct SAP joins remain conditional.

There is no running federated join between Ecom and JSAP as of 2026-07-19.

## Why they connect

- Ecom can identify channel exceptions such as low availability, inventory imbalance, unusual sales, price movement, delayed POs, or distributor issues.
- JSAP can reveal whether an existing task, ticket, approval, bill-verification item, MoM, document, or responsible person already explains or owns that exception.
- Both expose some SAP-shaped identifiers, but business-document type and company/database scope determine whether equality is meaningful.

## Evidence from system A — Ecom

- [[ECOM_MAP]] and [[ECOM_CLI_ENDPOINT_GAP]] record **138 registered GET commands as of 2026-07-19: 137 current SPA reads and one retained legacy route**.
- The current Ecom MCP is a code-orchestration bridge around the Cobra CLI and local helpers, not 138 separately typed MCP tools.
- [[ECOM_APP_SURVEY]] and the current spec cover platform sales, inventory, price, DRR, reports, state/city/SKU detail, fulfilment, purchase-order views, and upload-history reads.
- Ecom's SAP read layer exposes distributors by `CardCode`, distributor orders/invoices, platform-distributor mappings, item master, finished-goods inventory, stock by warehouse, and sales invoices. The single-sales-invoice route declares its path id as SAP `DocEntry`.
- The current response schema does not establish a universal company/database field for those SAP rows, and current Ecom evidence does not prove a canonical company switch. Route names, permissions, or token identity are not substitutes.
- Marketplace PO identifiers, platform SKU identifiers, SAP `DocEntry`, and source-local row ids are different namespaces unless explicitly documented otherwise.

## Evidence from system B — JSAP

- [[JSAP_MAP]] records 146 read-only commands as of 2026-07-19 across 13 modules; 138 returned live data in the final sweep, while failures/gates remain access states.
- [[DocumentManagement]] exposes SAP source documents with `databaseName`, `docEntry`, `docNum`, `cardCode`, date, and document-type-specific endpoints. [[Reports]] exposes budget `objType`, `docEntry`, `cardCode`, company, owner, approver, and approval flow. [[InventoryAudit]] exposes `itemCode`, warehouse, and quantity differences.
- [[TaskManager]], [[Tickets]], and [[docs/jsap/Dashboards|Dashboards]] expose existing tasks, ticket timelines, owners/assignees, priorities, dates, projects, and MoMs. Current schemas do not define a structured Ecom event id, platform slug, or marketplace SKU foreign key.
- JSAP company ids are local: `1` = JIVO OIL and `2` = JIVO BEVERAGE. They cannot be applied to Ecom without an independently verified mapping.
- JSAP SAP document identity is `database/company + object type + DocEntry`; `DocNum` is separate. Bill-verification `vchNumber` and task/ticket ids are also separate namespaces.
- [[DocumentHub]] Download may create an activity-log row. Confidential file/folder unlock endpoints change session/audit state and are forbidden. `GetLastBundleId` is read-only only with `mode=select`; `mode=update` mutates.
- JSAP can expose names, email/phone, salary/demographic fields, audit IPs, attachment metadata, and raw file streams. Return only purpose-authorized fields, and never send raw binary through normalized text ingestion without a tested byte-safe adapter.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | No canonical company switch proven | JSAP local company `1` Oil / `2` Beverage; `databaseName` | Explicit Ecom-to-SAP-database attribution; never copy JSAP ids into Ecom | Missing evidence |
| `sap_docentry_key` | sales-invoice route id documented as `DocEntry` | `docEntry` | Database/company, matching SAP object type, id kind=`DocEntry`, and date sanity check | Shared field shape; candidate equality, low to medium |
| `sap_docnum_key` | Ecom document/PO number only when explicitly typed as SAP DocNum | `docNum` | Database/company and matching object type; never compare to DocEntry or marketplace PO | Missing for most Ecom rows; candidate only |
| `party_key` | distributor `CardCode` path/row | BP/report/document `cardCode` | Database/company, BP type, normalized case/whitespace, and overlap profiling | Proven shared business field; candidate equality, medium |
| `item_key` | SAP items / finished-goods row identifier; marketplace SKU dimensions | Inventory Audit `itemCode` | Confirm exact Ecom response field, database/company, item name, pack, UOM, and SKU bridge | Candidate join; low |
| `warehouse_key` | stock-by-warehouse / inventory warehouse | Inventory Audit `warehouse`; document branch | Company/database and a validated alias table | Candidate join; low |
| `platform_key` | Ecom platform slug | No structured JSAP platform field | Exact platform reference inside an existing JSAP record or JivoGPT-owned context edge | Missing direct field; semantic only |
| `exception_context_key` | Ecom endpoint, raw row id, dimensions, period/version | task/ticket/MoM/report text, id, status, owner, dates | Explicit source reference preferred; otherwise semantic score and human confirmation | Context join; low to medium |
| `observed_at` | report period, transaction date, version/extraction time | document/task/ticket/bill dates and action timeline | Same timezone, business period, and event-time semantics | Proven time fields; context alignment only |

## Read-only questions unlocked

1. Is a marketplace sales, inventory, distributor, PO, or price exception already described in an existing JSAP task, ticket, MoM, or report, and who owns it?
2. For an explicitly company/database-qualified distributor `CardCode`, what do Ecom and JSAP each show?
3. Does an Ecom SAP sales-invoice `DocEntry` appear in JSAP under the same database and object type, or is the apparent match an A/R versus A/P collision?
4. Do Ecom finished-goods stock signals and JSAP inventory-audit variances align for validated item and warehouse mappings?
5. Are gaps explained by permissions, empty datasets, object-type mismatch, missing company scope, or a genuinely absent record?

## Gaps/do-not-assume

- Do not map JSAP company ids to Ecom. Current Ecom evidence proves no canonical company switch.
- Do not join SAP `DocEntry` without database/company and object type, and never substitute `DocNum`.
- Do not equate an Amazon/platform PO with a SAP PO, a JSAP budget document, or a bill voucher merely because a number matches.
- Do not assume Ecom sales invoices are the same object type as JSAP A/P invoice approvals or bill-verification rows.
- Do not treat task/ticket/MoM text as a deterministic link unless it contains a structured source reference.
- Do not create or update a JSAP task/ticket to resolve an Ecom issue; JivoGPT may only report existing context.
- Do not unlock confidential Document Hub content. Avoid Download when a possible activity side-log violates the requested side-effect posture.
- Do not use JSAP `GetLastBundleId?mode=update`; it mutates despite GET.
- Minimize personal and attachment fields to the authorized question; HTTP 200 alone is not entitlement. Do not ingest raw file bytes through the current non-byte-safe path.

## Validation checklist

- [ ] Establish Ecom SAP database/company provenance before attempting any SAP-key equality join.
- [ ] Normalize documents with object type and id kind; keep `DocEntry`, `DocNum`, marketplace PO, and voucher numbers separate.
- [ ] Profile Ecom SAP item-row field names and validate item/warehouse overlap with JSAP by pack and UOM.
- [ ] Validate distributor `CardCode` coverage separately for each proven database/company.
- [ ] Add structured Ecom provenance to JivoGPT-owned exception records; do not write the reference into JSAP.
- [ ] Promote a JSAP context edge to deterministic only when an existing record carries an exact source id/reference.
- [ ] Record access state, empty/error state, event date, report period, and extraction time.
- [ ] Use Document Hub metadata first; stop at locked/confidential content and skip Download in strict zero-side-effect mode.
- [ ] Enforce purpose/role authorization and a minimal output allowlist; keep raw binary out until a byte-safe adapter is tested.
- [ ] Use only read-listed commands; never upload, refresh, approve, assign, create, update, or delete.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[ECOM_HUB]] · [[JSAP_HUB]] · [[ECOM_MAP]] · [[ECOM_CLI_ENDPOINT_GAP]] · [[ECOM_APP_SURVEY]] · [[JSAP_MAP]] · [[DocumentManagement]] · [[Reports]] · [[InventoryAudit]] · [[TaskManager]] · [[Tickets]] · [[docs/jsap/Dashboards|Dashboards]] · [[DocumentHub]] · [[READ_ONLY_LAW]]
