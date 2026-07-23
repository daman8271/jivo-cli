---
title: Factory to JSAP Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, factory, jsap, sap, audit, qc, documents, read-only]
---

# Factory to JSAP Connection

> Evidence and contracts in this note are current as of 2026-07-19 and are governed by [[READ_ONLY_LAW]].

## Connection verdict

**Qualified SAP-document and inventory-audit candidates plus a human-governance overlay.** Factory provides record-level plant, QC, GRPO, production, warehouse, barcode, and dispatch facts. JSAP provides SAP source-document lists, physical inventory-audit results, a global QC template, approval reports, documents, tasks, tickets, bills, and people context.

There is **no running federated join** between Factory and JSAP as of 2026-07-19. The strongest deterministic candidates are qualified SAP documents and item/warehouse audit rows. QC templates, tasks, tickets, and people are context edges unless an explicit business identifier is present.

## Why they connect

- Both systems observe SAP-backed plant and document domains, but at different stages and grains.
- Factory shows operational execution; JSAP shows source documents, physical-count discrepancies, approval/governance context, and responsible people.
- JSAP can help explain why a Factory GRPO, inventory, QC, or maintenance exception exists, without becoming a path to approve, upload, edit, or close anything.
- Cross-system identity must be composite because company ids, document numbers, and local user ids can collide.

## Evidence from system A

Factory has **183 verified GET endpoints** across `JIVO_OIL`, `JIVO_MART`, and `JIVO_BEVERAGES` as of 2026-07-19.

- Factory company mapping is Oil `1`, Mart `2`, Beverages `3`, with operational requests scoped by `Company-Code` and company-specific HANA schemas.
- Factory GRPO, Gate, Dispatch, Production, and Warehouse surfaces expose SAP-facing `doc_entry`, `doc_num`, `sap_doc_entry`, `sap_doc_num`, item codes, posting dates, warehouses, vendors/customers, and quantities.
- Factory WMS exposes item-by-warehouse stock and movements; Factory Barcode adds item, batch, box/pallet, scan, transfer, and dispatch lineage.
- Factory QC contains record-level arrival and production inspections. Factory Maintenance contains asset/work-order context, but no JSAP task or ticket foreign key is documented.
- Factory's accounts/users and physical campus masters are shared across company headers, while plant operational records are company-scoped.

## Evidence from system B

JSAP's built CLI has **146 read commands** across 13 groups as of 2026-07-19; **138 returned live data** in the final sweep, while failures/gates remain access states. It is documented in [[JSAP_MAP]] and registered under `CLI/jsap-cli/jsap/modules/`.

- JSAP company ids are **Oil `1` and Beverage `2`**. This conflicts with Factory, where id `2` means Mart and Beverages is `3`. Raw numeric company joins are therefore invalid.
- [[DocumentManagement]] documents `GetGRPO`, `GetPO`, `GetApDraft`, and `GetGR` rows across both JSAP HANA companies. GRPO rows include `databaseName`, `docEntry`, `docNum`, dates, `cardCode`, `cardName`, amount, and attachment link.
- [[InventoryAudit]] exposes item-level count reports with `warehouse`, `itemCode`, item/group names, `systemQty`, `physicalQty`, `diffQty`, `diffValue`, `diffLitre`, unit, and lot/session context.
- [[Reports]] exposes approval/budget documents with explicit `objType`, company, `docEntry`, object name, `cardCode`, `cardName`, date, amount, owner, approver, and stage flow.
- [[QualityCheck]] exposes the current QC **template**, including HANA document object ids, mandatory flags, thresholds, and parameter/sub-parameter structure. It is not a Factory inspection-result feed and takes no company parameter.
- JSAP tasks, tickets, employee hierarchy, bills, [[DocumentHub|Document Hub]], and activity logs can supply ownership or audit context, but their local ids are not Factory ids. Document Hub metadata and already-authorized Preview are the strict-read paths; Download may append an activity row, and confidential unlocks mutate session/audit state.
- Some JSAP receiver/document-file reads return 500, and some permission gates are client-side. These are access/availability caveats, not evidence of empty business data or proof of access entitlement. People context requires an authorized purpose and an allowlist that omits unnecessary phone, email, salary, demographic, and IP fields.
- Some JSAP download handling is not byte-safe. Do not route raw binary into normalized text or retrieval until a tested binary adapter preserves bytes and access controls.

## Join contract table

| Canonical key | Factory field | JSAP field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | `Company-Code`, Factory ids 1/2/3, schema context | `company` 1/2, `databaseName`, company label | Canonical name/code + SAP database + dated alias; never raw numeric equality | **Required and partially proven** |
| `item_key` | `item_code` in WMS, QC, Production, Barcode, receipts | Inventory Audit `itemCode` | Canonical company/database + item name + pack/UOM validation | **Strong candidate** |
| `warehouse_key` | warehouse code, `current_warehouse`, movement warehouses | Inventory Audit `warehouse`; warehouse lookup values | Company/database + location/unit + dated warehouse alias | **Strong candidate** |
| `sap_grpo_key` | GRPO/gate `doc_num`, `sap_doc_num`, possible `doc_entry` | `GetGRPO.databaseName + docEntry + docNum` | Object type = GRPO, company/database, ID kind; prove whether each Factory field is entry or number | **Strong candidate after qualification** |
| `sap_document_key` | generic SAP document fields in Dispatch/Production/WMS | report `objType`, `docEntry`, `objectName`; PO/AP/GR source rows | Object type + company/database + `DocEntry` versus `DocNum` + date | **Candidate; unsafe unqualified** |
| `inventory_audit_key` | item + warehouse + stock snapshot/as-of time | lot/session + `itemCode` + `warehouse` + system/physical quantities | Company/database + lot date + item/UOM + warehouse | **Strong reconciliation candidate** |
| `qc_context_key` | record-level QC inspection, material/item, production run, date | global form/document template, thresholds, parameters | Template version/form id + document object type + effective date; no row equality | **Context only** |
| `person_key` | Factory user id, employee code, email/name where present | JSAP user id, employee code/name/email where present | Explicit role/purpose authorization, field allowlist, verified employee code or email, and retained source-local ids; HTTP 200 alone is not entitlement | **Candidate; sensitive and local ids unsafe** |
| `work_context_key` | maintenance work order, QC/dispatch exception, production run | task, ticket, document, bill, MOM or activity-log id | Explicit reference to qualified document/item/warehouse; text-only similarity stays low-confidence | **Context candidate** |
| `event_time` | posting, inspection, movement, scan, dispatch time | document, audit, approval, task/ticket/activity time | Event type + timezone + extraction time | **Proven shared dimension** |

## Read-only questions unlocked

1. For a qualified Factory GRPO, what JSAP source-document, approval, attachment, or document-dispatch context exists?
2. Which Factory item/warehouse stock positions have a JSAP physical-count discrepancy for the same company and audit lot?
3. Does a Factory QC or production document fall under the currently active JSAP QC template, and which checks were mandatory at that time?
4. Which Factory operational exceptions already have a JSAP task, ticket, bill, document, or accountable employee context?
5. Where do Factory stock and JSAP audit `systemQty` disagree before considering the physical count and audit timestamp?

## Gaps/do-not-assume

- **Never join raw numeric company ids.** Factory id `2` is Mart; JSAP id `2` is Beverage.
- Do not equate `DocEntry` with `DocNum`, or reuse either across document types or databases.
- Do not assume a Factory field named `sap_doc_num` is a JSAP `docEntry`; prove the ID kind from its endpoint and sample.
- Do not treat the JSAP QC template as a Factory inspection result or as company-scoped data.
- Do not join Factory and JSAP local user, task, ticket, session, lot, or work-order integers.
- JSAP's SAP source-document reads cover Oil and Beverage databases; a JSAP Mart company scope is not documented.
- Do not treat JSAP receiver/file 500s or permission quirks as zero documents.
- Do not infer that a task or ticket refers to a Factory record from free text alone.
- Never call `/api/DocumentDispatch/GetLastBundleId?mode=update`; hardcode `mode=select` if that read is required.
- Prefer Document Hub metadata or already-authorized Preview. Exclude Download while it may append an activity row, and never call confidential file/folder unlocks.
- Do not call JSAP company-switch, approval, upload, edit, restore, or other mutation routes. Context retrieval stays read-only.
- Do not expose broad people records merely because the endpoint returns HTTP 200; authorize the purpose and minimize fields first.
- Do not ingest raw file bytes through the current non-byte-safe path.
- No current evidence proves a direct database foreign key or a running federated query.

## Validation checklist

- [ ] Build a company alias table that maps Factory codes to JSAP labels and `databaseName`; reject numeric-only mappings.
- [ ] Classify Factory and JSAP document identifiers by object type and ID kind.
- [ ] Profile GRPO overlap by database, DocNum, DocEntry, party, amount, and date.
- [ ] Profile item/warehouse overlap and validate item names and UOM before inventory reconciliation.
- [ ] Tie every JSAP inventory report to its company, lot, session, and audit date.
- [ ] Version QC-template context by form id and effective date; never back-apply silently.
- [ ] Map people only for an authorized purpose through verified employee code or email; allowlist the minimum fields and preserve source-local ids.
- [ ] Keep raw binary out of normalized text until a tested byte-safe adapter exists.
- [ ] Require an explicit qualified reference before attaching tasks, tickets, bills, or documents to Factory facts.
- [ ] Carry 500, empty, permission-gated, and locked states as visibility metadata.
- [ ] Hardcode `GetLastBundleId` to `mode=select`; use Document Hub metadata/authorized Preview and skip Download and confidential unlocks.
- [ ] Keep all source access read-only and all cross-system mappings in JivoGPT-owned storage.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[FACTORY_HUB]] · [[JSAP_HUB]] · [[FACTORY_MAP]] · [[FACTORY_VERIFICATION]] · [[JSAP_MAP]] · [[DocumentManagement]] · [[DocumentHub]] · [[InventoryAudit]] · [[QualityCheck]] · [[Reports]] · [[READ_ONLY_LAW]]
