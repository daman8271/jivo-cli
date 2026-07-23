---
title: EXIM to JSAP Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connection, exim, jsap, sap, documents, approvals, read-only]
---

# EXIM to JSAP Connection

## Connection verdict

**Candidate SAP document and party edge plus governance context; company mapping is unresolved.** EXIM exposes purchase, GRPO, AP/AR, party, and item facts for Jivo Wellness. JSAP exposes SAP POs, GRPOs, AP drafts, goods returns, budget approvals, bill verification, document handling, and BP reads for JIVO OIL and JIVO BEVERAGE. It can contextualize documents, but does not prove that a given EXIM record belongs to either JSAP company.

No running federated join exists. Until company identity and SAP identifier types are verified, the edge is contextual rather than deterministic.

## Why they connect

- EXIM sees import stock, supplier, PO, optional GRPO, AP/AR, and SAP master data.
- JSAP sees the human and governance trail around purchase/GRPO/AP documents: physical document dispatch, approval status, budget ownership, bill checking, payment state, attachments, and responsible users.
- Both expose business-partner codes and, on some document surfaces, distinct SAP `DocEntry` and `DocNum` values.

## Evidence from system A

System A is EXIM. Its generated manifest contains **65 printed CLI tools** as of 2026-07-19. [[API-INVENTORY]] has 67 read-table rows but duplicates `GET /dc/`, leaving **66 unique read-labelled routes**.

The route `GET /sap_sync/open-grpos/` is an unresolved GET-that-may-refresh conflict. [[sap_sync_open-grpos]] shows real data but also a sync namespace and `open_grpos:[sync]` permission; it must be excluded from safe recipes.

Relevant EXIM fields include:

- `card_code`, `card_name`, vendor codes, item codes, warehouse, and dates in [[parties]], [[CLI/exim/endpoints/stock-status|stock-status]], and [[sap-sync_open-pos]].
- `PO_NUMBER` for purchase orders and nullable `grpo_number` for import stock.
- `DB Primary Key` explicitly described as SAP DocEntry and a separate `Invoice Number` on [[sap-sync_open-ap]].
- AP remarks that may mention a base PO, gate entry, and GRPO; those free-text references are evidence for search, not keys.

EXIM's documented Jivo Wellness scope has no proven mapping to either JSAP company.

## Evidence from system B

System B is JSAP. [[JSAP_MAP]] documents **146 commands, 138 of which returned live data in the final sweep**, and two selectable companies: **JIVO OIL = 1** and **JIVO BEVERAGE = 2**. Failures/gates remain access states. Many reads are company-scoped, while some document-source reads span both HANA schemas and identify each row with `databaseName`.

Strongest JSAP evidence:

- [[DocumentManagement]] documents `GetGRPO`, `GetPO`, `GetApDraft`, and `GetGR` rows with `databaseName`, `docEntry`, `docNum`, `docDate`, `createDate`, `cardCode`, `cardName`, `docTotal`, and attachment link.
- [[Reports]] supports AP-invoice budget lookup by `docEntry` and returns company, object type/name, `cardCode`, `cardName`, date, amount, owner, approver, and status.
- [[BPMaster]] exposes company-scoped `cardCode`, `cardName`, address, state, and GSTIN, but its required BP type/staff filters are ignored and observed results are customer-heavy; vendor coverage must not be assumed.
- [[BillVerification]] keys its purchase-bill workflow by local MRN/voucher `vchNumber`, with supplier reference, dates, account name, status, payment state, and line items. `vchNumber` is not documented as SAP DocEntry or DocNum.
- [[DocumentManagement]] also contains a method trap: `GetLastBundleId` is read-only only with hardcoded `mode=select`; `mode=update` mutates despite GET. [[DocumentHub]] Download may append an activity row, and confidential unlock calls mutate session/audit state.
- Address, GSTIN, owner/approver, attachment, and people fields are sensitive context. Their retrieval and output require role/purpose authorization, a minimal field allowlist, and redaction of unnecessary identifiers; HTTP 200 alone is not proof of entitlement.
- Some JSAP download handling is not byte-safe. Do not route raw binary into normalized text or retrieval until a tested binary adapter preserves bytes and access controls.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | implicit Jivo Wellness scope | `databaseName` or company `1`/`2` | authoritative legal-entity and SAP-schema mapping, dated | **Missing evidence — blocked** |
| `sap_doc_entry_key` | `DB Primary Key` only where explicitly documented as DocEntry | `docEntry` | company/schema, SAP object type, source table, posting date | **Candidate shared field — medium after company proof** |
| `sap_doc_number_key` | `PO_NUMBER`, `Invoice Number`, `grpo_number` | `docNum` | company/schema, exact document type, date; never compare to DocEntry | **Candidate shared field — medium after company proof** |
| `party_key` | `card_code`, `VENDOR_CODE`, `vendor_code` | `cardCode` | company/schema, vendor/customer type, exact code, name/GSTIN check | **Candidate — medium-low** |
| `item_key` | `item_code` / `ItemCode` | item fields only where a JSAP document/line surface exposes them | company/schema, document line, item name, UOM, date | **Candidate — missing broad JSAP item evidence** |
| `approval_context_key` | typed EXIM AP/PO document identity | JSAP `docEntry` + object type + approval/budget status | company, object type, DocEntry, owner/status timestamps | **Context join — medium after key proof** |
| `bill_context_key` | AP invoice number, vendor reference, amount, date | `vchNumber`, supplier reference, account, amount, voucher date | company, vendor, amount tolerance, date; prove identifier semantics | **Semantic/context join — low** |

`DocEntry` and `DocNum` must never be conflated. JSAP returns both in the same source-document row; EXIM separately exposes an AP internal key and invoice number. Store them as different typed fields, together with company and SAP object type.

## Read-only questions unlocked

- For a company-verified EXIM AP or PO, is there a JSAP approval, document-dispatch, or bill-verification context record?
- Which EXIM supplier documents have JSAP attachments or governance history, and which remain unmatched?
- Who owns or approved a matched AP-invoice budget record in JSAP?
- Do EXIM and JSAP party codes agree after company and BP-type validation?

## Gaps/do-not-assume

- Jivo Wellness is not proven to equal JSAP JIVO OIL or JIVO BEVERAGE.
- A number cannot be joined until it is typed as DocEntry, DocNum, PO number, GRPO number, invoice number, vendor reference, or JSAP `vchNumber`.
- Free-text AP remarks mentioning PO/GRPO values are search clues only.
- JSAP BP filters are known to ignore the requested BP type; do not infer vendor completeness from `BPGetCardInfo`.
- JSAP local document-dispatch endpoints can return live 500s; failure is not absence of a business document.
- JSAP approvals, attachments, and bills add context; they do not overwrite EXIM facts or authorize workflow actions.
- Never call `GetLastBundleId?mode=update`; hardcode `mode=select` if needed. Prefer Document Hub metadata or already-authorized Preview, exclude Download while it can log activity, and never unlock confidential content.
- Do not return GSTIN, addresses, employee identities, approver details, or attachment metadata unless the question and caller are authorized; minimize and redact output.
- Do not ingest raw file bytes through the current non-byte-safe path.
- `/sap_sync/open-grpos/` remains excluded and no federated join is running.

## Validation checklist

- [ ] Obtain a dated mapping between EXIM Jivo Wellness and JSAP company/schema values.
- [ ] Build a typed SAP document registry separating DocEntry, DocNum, object type, company, and source.
- [ ] Profile overlap separately for JSAP `JIVO_OIL_HANADB` and `JIVO_BEVERAGES_HANADB`.
- [ ] Validate party codes with BP type, name, and GSTIN; measure JSAP vendor coverage explicitly.
- [ ] Treat JSAP `vchNumber` as local until its SAP semantics are proven.
- [ ] Carry dates, amounts, statuses, and access errors as source-specific context; include attachment metadata only when authorized and necessary.
- [ ] Enforce purpose/role authorization and an output allowlist for BP, people, approval, and attachment fields.
- [ ] Keep raw binary out of normalized text until a tested byte-safe adapter exists.
- [ ] Hardcode `GetLastBundleId` to `mode=select`; use Document Hub metadata/authorized Preview, not Download or confidential unlocks.
- [ ] Query only read-safe routes and keep EXIM `/sap_sync/open-grpos/` excluded.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[JSAP_HUB]] · [[EXIM_MAP]] · [[JSAP_MAP]] · [[DocumentManagement]] · [[DocumentHub]] · [[READ_ONLY_LAW]]
