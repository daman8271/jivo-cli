---
title: jivo-desk to JSAP Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, jivo-desk, jsap, workflow-context, read-only]
---

# jivo-desk ↔ JSAP

Evidence below is repository-verified as of 2026-07-19 unless a narrower date is stated.

## Connection verdict

**Workflow/context edge only.** jivo-desk produces market observations and source-health evidence; JSAP contains existing human-work and document context. JivoGPT may ask whether a price, availability, DRR, or freshness exception is already represented in JSAP, but the current systems expose no durable shared fact key.

There is no running federated join between jivo-desk and JSAP as of 2026-07-19. The edge must remain semantic unless an existing JSAP record explicitly cites the jivo-desk artifact or a JivoGPT-owned context link is created internally.

## Why they connect

- jivo-desk identifies operational exceptions: unexpected price, OOS listing, pincode gap, price-match exposure, DRR risk, stale sweep, partial fallback, or missing source.
- JSAP can show whether an existing ticket, task, MoM, document, report, owner, or timeline already discusses the exception.
- Linking the evidence to existing accountability context helps explain and route questions without making JivoGPT a write path.

## Evidence from system A — jivo-desk

- [[DESK_CLI]] documents eight operational read commands plus an exact product group as of 2026-07-19 with a common JSON envelope and explicit freshness.
- Normalized sweep rows preserve `platform + listing_id` and exact bridge enrichment where mapped. They still contain no JSAP task/ticket ID, and a qualified Factory company is not automatically a JSAP company.
- Operational `--sku` is exact. `product search` can retrieve text candidates but cannot establish a JSAP context edge.
- `price`, `avail`, and `compare` still read current live/last-good structured rows when a historical `--date` is requested. `match` has dated history; `drr` is a fixed monthly snapshot with its own `as_of` and window.
- Source path, mtime, missing state, partial state, and last-good fallback are first-class evidence for an exception fingerprint.

## Evidence from system B — JSAP

- [[JSAP_MAP]] records 146 read-only commands as of 2026-07-19; 138 returned live data in the final sweep, while failures/gates remain access states.
- [[Tickets]] exposes existing ticket id, title, description, project, priority, status, requester, assignee, attachments, and timeline. [[TaskManager]] exposes existing task id/name/description, project/module, owner/assignee, priority, dates, progress, and status. [[docs/jsap/Dashboards|Dashboards]] exposes existing MoMs with date, attendees, agenda, notes, and status.
- Those schemas currently have no structured jivo-desk source path, marketplace SKU, platform slug, pincode, or observation id. Text and date overlap therefore provide semantic candidates only.
- [[DocumentHub]] exposes file/folder metadata, versions, activity logs, and already-authorized preview. Download may append a `Download` activity row; a confidential item that is not already authorized requires a forbidden PIN-unlock state change.
- JSAP company ids are local (`1` Oil, `2` Beverage). jivo-desk has no company dimension, so no company join exists.
- [[DocumentManagement]] warns that `GetLastBundleId` mutates when `mode=update`; only hardcoded `mode=select` is a read.
- JSAP can expose names, email/phone, salary/demographic fields, audit IPs, attachment metadata, and raw file streams. Return only purpose-authorized fields, and never send raw binary through normalized text ingestion without a tested byte-safe adapter.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | No company field | JSAP local `company`/`CompanyId` | Explicit company attribution from external evidence; raw ids cannot fill the gap | Missing evidence |
| `exception_key` | JivoGPT-owned fingerprint of command, source path, row, platform, geography, and true snapshot | No structured field | Keep the fingerprint inside JivoGPT; an existing JSAP record must cite it exactly to be deterministic | Missing direct field |
| `item_key` | exact listing/product key and qualified Factory bindings | task/ticket/MoM/document free text | Released product bridge plus an exact existing JSAP reference; text alone is insufficient | Desk identity exact; JSAP edge semantic |
| `platform_key` | jivo-desk `platform` | project/title/description/notes text only | Dated platform aliases and exact existing text/reference | Semantic candidate; low |
| `geography_key` | listing `pincode`; sometimes absent in price-match | free text only | Normalized pincode/state plus exact existing reference | Missing structured field; low |
| `observed_at` | source mtime, true snapshot date, price-match date, DRR `as_of`/window | task/ticket/MoM/document created, due, update, or action dates | Timezone, event versus ingestion semantics, and a justified search window | Context alignment; medium |
| `owner_key` | No owner in sweep facts | assignee/requester/owner/user ids and names | Owner comes only from the matched existing JSAP context, never from the market row | Context output, not a join key |
| `artifact_key` | source path/file name and file mtime | Document Hub `fileId`, `fileName`, version, activity | Exact filename/content reference and date; metadata access state | Candidate artifact join; low |

## Read-only questions unlocked

1. Is a current-file price/availability or panel-`as_of` DRR exception already mentioned in an existing JSAP ticket, task, or MoM, with requested date kept separate from actual source time?
2. If so, what is the existing status, priority, owner/assignee, due date, and latest recorded action?
3. Does Document Hub already contain an unconfidential, authorized report whose filename and date explicitly match the jivo-desk artifact?
4. Is the apparent exception actually explained by a stale sweep, partial fallback, current-row substitution for a historical request, or missing pincode grain?
5. Which exception candidates have no existing JSAP context, without creating any new source-system record?

## Gaps/do-not-assume

- jivo-desk `product search` candidates cannot join to JSAP text by themselves; operational identities are exact but JSAP still needs an explicit reference.
- Historical `price`, `avail`, and `compare` requests still return current structured sweep rows; use true dated sources where available.
- jivo-desk platform labels are not a JSAP dimension. Text mentions can be ambiguous or stale.
- JSAP company ids cannot supply jivo-desk company scope; jivo-desk has no such field.
- A nearby task/ticket date or similar title is not proof of causality. Preserve semantic score and require confirmation.
- Do not create a task, ticket, comment, MoM, or attachment from JivoGPT. Only existing records may be read.
- Do not unlock confidential files or folders. Report `locked`/`access_not_granted` and stop.
- Treat Document Hub Download as read-with-possible-side-log; prefer metadata and already-authorized preview when zero side effects are required.
- Never call `GetLastBundleId` with `mode=update`.
- Minimize personal and attachment fields to the authorized question; HTTP 200 alone is not entitlement. Do not ingest raw file bytes through the current non-byte-safe path.

## Validation checklist

- [ ] Define a JivoGPT-owned exception fingerprint containing raw provenance and true observation time.
- [ ] Build product and platform alias registries before semantic retrieval; retain all raw labels.
- [ ] Search existing JSAP context using exact source ids/references first, then bounded semantic candidates.
- [ ] Require human confirmation before marking a semantic task/ticket/MoM candidate as related.
- [ ] Separate current sweep, dated price-match, dated review, and fixed DRR-panel evidence.
- [ ] Record matched, unmatched, ambiguous, stale, partial, missing, locked, and access-gated states.
- [ ] Use Document Hub metadata first and do not issue confidential unlock calls.
- [ ] Skip Download in strict zero-side-effect mode because it may create an activity log.
- [ ] Enforce purpose/role authorization and a minimal output allowlist; keep raw binary out until a byte-safe adapter is tested.
- [ ] Keep all new context edges inside JivoGPT; never write them back to JSAP or jivo-desk source files.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[JIVO_DESK_HUB]] · [[JSAP_HUB]] · [[DESK_CLI]] · [[JSAP_MAP]] · [[Tickets]] · [[TaskManager]] · [[docs/jsap/Dashboards|Dashboards]] · [[DocumentHub]] · [[DocumentManagement]] · [[READ_ONLY_LAW]]
