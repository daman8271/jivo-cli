---
title: Read-Only Guardrails
portal: Flipkart
type: meta
read_only: true
created: 2026-07-30
updated: 2026-07-30
---

# Flipkart — Read-Only Guardrails (this platform's instance of the safety law)

This study obeyed the mission GUARDRAILS (G0–G10) and Amendments 01–04. Flipkart-specific application:

## What was and wasn't done to the live account

- **Reads fired:** plain `GET` only, against PROVEN-READ Vendor-Hub endpoints, using the existing
  production session (consumed, never minted — G9). 0 × 401/403/429; the session stayed healthy.
- **Never fired:** any `POST`/`PUT`/`PATCH`/`DELETE`. In particular the Flipkart WRITE/EXPORT
  surfaces below were catalogued but never called.
- **No browser clicks:** a read-only browser walk of both portals WAS run this session
  (navigation-only, Amendment-02) — 37 distinct section pages. Zero clicks were made, so the click
  law's forbidden set never came into play; the route interceptor also **aborted 2 app-fired write
  requests** (verbs "edit"/"delete") before the socket opened. Amendment-04 non-GET audit:
  `captures/nonget-allowed.tsv` (122 reads), `nonget-flagged.tsv` (0 mutations), `nonget-telemetry.tsv` (15).

## Flipkart write/export surfaces held OUT OF SCOPE (never wired)

- **Report enqueue = WRITE (G2):** `GET napi/metrics/bizReport/report/generateReport`,
  `POST fed-ads/downloadV2`, `POST fed-ads/download/table`, `POST vendor/analytics/report`,
  `POST vendor/analytics/sales-report`. Each **creates a report-request row / burns queue quota**,
  so despite "download"-ish names they are EXPORTs, not reads. JIVO's own runbook warns Vendor-Hub
  throttles after ~8 report triggers/2 h — **this study fired zero triggers.**
- **Uploads:** `vendor-p/document-service/.../upload`, `vendor/feeds/upload-feed-file`,
  `vendor/qc-norms/upload-*`, `triton/v1/feed/processor/upload`, `napi/sfx/processBulkStockUpdateFile`.
- **Catalog/listing mutations:** `napi/createProductV2/*`, `napi/edit-product/*`,
  `listings/v3/update*`, `vendor/cataloging/create-fsn`.
- **Identity/access:** `vendor/user-management/user-activation/activate` + `/suspend`,
  `change-password`, `update-user`, `/login`, `/select-vendor`.
- **Money/ops:** `napi/fkgrowthcapital/*Application`, self-ship dispatch/label, returns
  approve/reject.

The full partition is in [[Flipkart-Endpoints]] (READ allowlist vs WRITE/EXPORT vs UNKNOWN).

## G1 — UNKNOWN is denied

**422 endpoints are UNKNOWN** (method/read-vs-write not resolvable from the minified bundle). Per
G1 they are treated as potentially-mutating and are **documented but never wired** into the CLI.
They are listed in every section note's "UNKNOWN" table so the complete surface is visible and the
excluded part is explicit — the tankhapay standard (enumerate what you hold out).

## Amendment-04 audit trail

The transport gate opened for **application-fired** non-GETs during a walk. Worker B walked both
portals read-only (navigation-only, no clicks) and authored no request itself, so every non-GET was
fired by the app on render. Audit: **`captures/nonget-allowed.tsv` = 122 reads** (GraphQL `query`
ops + POST-reads, structure-preserving redaction keeps operationName/op-type/keys per G6),
**`nonget-flagged.tsv` = 0 mutations**, **`nonget-telemetry.tsv` = 15** analytics beacons. All
GraphQL POSTs were verified `query` type by operationName + response shape. No click = no mutation.

## Three-layer guardrail in the CLI (Phase 8)

The generated `cli/flipkart-portal` enforces read-only in code:
1. **Transport:** the HTTP client refuses any method other than `GET` — throws before a socket opens.
2. **Allowlist:** only paths classified READ/READ_FILE in [[Flipkart-Endpoints]] are reachable.
3. **Tests:** `guardrail_test.go` asserts no write/export/unknown path is wired;
   `guardrail_coverage_test.go` asserts every wired command maps to a READ row.

## Connections
[[00-Flipkart-Atlas]] · [[Auth-and-Access]] · [[Flipkart-Endpoints]] · [[Study-Verification]]
