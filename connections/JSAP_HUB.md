---
title: JSAP Connection Hub
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connector-hub
tags: [jivogpt, connections, jsap, sap, governance, read-only]
---

# JSAP Connection Hub

JSAP is both a SAP/business-document lens and the human-governance overlay: dashboards, inventory audits, dispatch/receive documents, users, reports, BP master, QC, tasks, tickets, hierarchy, bills, Document Hub, and metadata.

## Current connector profile

| Property | Current evidence |
|---|---|
| Command surface | 146 commands across 13 groups |
| Verification | 138 commands returned live data in the final sweep |
| Company scope | id `1` = JIVO Oil; id `2` = JIVO Beverage |
| Backends | JSAP application database plus SAP HANA-backed reads |
| Authentication | Three-step session bootstrap, then session-cookie requests |

JSAP permits guarded POST-to-read calls because several read views use POST for filters. Method alone is not the safety test; every registered command must satisfy the read-only registry and behavioral checks.

## Canonical fields

| Canonical field | JSAP candidates | Qualification required |
|---|---|---|
| `company_key` | company id and database name | Use JSAP-specific mapping; never reuse Factory numeric ids |
| `sap_schema` | `databaseName`/company database | Preserve on all SAP-derived keys |
| `item_key` | `itemCode` and item text | Company/database, description, pack, and date |
| `party_key` | `cardCode`, `cardName` | Tenant/database and normalized-name validation |
| `document_key` | `docEntry`, `docNum`, document type/date | Company/database, object type, source, and id kind |
| `warehouse_key` | warehouse code/location fields | Retain source context |
| `person_key` | employee/user ids, employee code, hierarchy fields | Purpose-limit and minimize personal data |
| `work_key` | task, ticket, bill, inventory session, Document Hub ids | Module, company, and source-qualified |

## Five connection edges

| Other connector | Best connection | Note |
|---|---|---|
| EXIM | SAP parties/documents plus approvals, bills, reports, and audit context | [[EXIM__JSAP]] |
| Factory | GRPO, QC, inventory audit, SAP docs, employees, and maintenance context | [[FACTORY__JSAP]] |
| OMS | Parties, orders, invoices, SAP logs, approvals, bills, and document history | [[OMS__JSAP]] |
| Ecom | Channel exceptions versus reports, tasks, tickets, MOMs, and owners | [[ECOM__JSAP]] |
| jivo-desk | Price/availability/DRR exceptions versus tracked work and decisions | [[JIVO_DESK__JSAP]] |

## Safe adapter contract

1. Use only commands admitted by the JSAP read-only registry, including guarded POST-to-read entries.
2. Stamp company/database, group/command, access state, event time, and extraction time.
3. Preserve `DocEntry` and `DocNum` as different id kinds and qualify them by object type.
4. Minimize user, hierarchy, task, ticket, bill, and document metadata to the fields needed for the question.
5. Attach existing work context to operational facts; never create, update, approve, comment, download-with-side-effect, or transition anything.

## Exclusions and open evidence gaps

- Exclude `GET /api/DocumentDispatch/GetLastBundleId?mode=update`; its `mode=update` behavior is mutating despite the verb.
- Document Hub Download may append an activity record. Prefer Preview for strict read-only ingestion and exclude Download until behavior is proven harmless.
- Confidential-document unlock paths are forbidden.
- Some download handling is not byte-safe; binary content should not enter the normalized text pipeline without a tested adapter.
- JSAP exposes personal and potentially sensitive business data. Answers need field minimization, authorization-aware access, and citation without unnecessary disclosure.
- Numeric company id `2` means Beverage here but Mart in Factory.

## Evidence anchors

[[JSAP_MAP]] · [[JSAP_CLI_PLAN]] · [[CLI/jsap-cli/README|JSAP CLI README]] · [[DATA_SOURCES]] · [[READ_ONLY_LAW]]

---
Linked: [[/README|README]] · [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[FACTORY_HUB]] · [[OMS_HUB]] · [[ECOM_HUB]] · [[JIVO_DESK_HUB]]
