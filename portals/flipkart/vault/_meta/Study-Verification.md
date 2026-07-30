---
title: Study Verification
portal: Flipkart (Seller Hub + Vendor Hub)
type: meta
status: PASS
date: 2026-07-30
read_only: true
---

# Flipkart Portal Study — Completeness Verification

Adversarial self-audit of the finished study at `portals/flipkart/`. Run by `captures/verify.py`
(4 structural checks) plus the live-walk evidence check below. No writes were fired against any
Flipkart surface; this note inspects on-disk artifacts and the walk transcripts only.

## Check 1 — File presence (PASS)

**38 vault notes present.** 30 section notes (incl. the documented-only `Marketplace-Seller-API-unused`) + 5 top-level (`00-Flipkart-Atlas`,
`Flipkart-Endpoints`, `Flipkart-Pages-and-Routes`, `Flipkart-Data-Model`, `Flipkart-Data-Inventory`)
+ 3 `_meta` (`Auth-and-Access`, `Read-Only-Guardrails`, `Study-Verification`). All expected
top-level notes present; no stubs (every section note carries its full endpoint tables).

## Check 2 — Broken wikilinks (PASS)

Extracted every `[[target]]` (aliases stripped, fenced + inline code removed) and resolved against
real note filenames: **0 broken links.** Two drift links were remediated during the run —
`[[COE]]` (a section with 0 matched endpoints → removed from the Atlas nav) and `[[COVERAGE-LEDGER]]`
(the ledger lives outside `vault/` at `portals/flipkart/COVERAGE-LEDGER.md` → converted to a plain
path reference). Re-scan after remediation: **0 broken.**

## Check 3 — Endpoint coverage (PASS)

`captures/endpoints-raw.tsv`: **968 distinct endpoint paths.** Every one appears verbatim in
`Flipkart-Endpoints.md` → **968/968 indexed, 0 missing (100%).** Re-verified by string-matching each
raw path against the rendered markdown.

## Check 4 — Guardrail audit (PASS)

Scanned every section note's **"Read-safe endpoints (allowlist)"** table against the classification:
**0 WRITE / EXPORT / UNKNOWN paths appear in any read allowlist.** WRITE/EXPORT rows live only in
"Out of scope" tables; UNKNOWN rows live only in "UNKNOWN" tables. The 216 read-safe endpoints
(137 READ + 79 READ_FILE) are the only ones the Phase-8 CLI may wire.

## Verdict — PASS

| Check | Result |
|---|---|
| Files | PASS — 38/38 notes, no stubs |
| Wikilinks | PASS — 0 broken (2 drift links remediated) |
| Endpoint coverage | PASS — 968/968 (100%) |
| Guardrails | PASS — 0 write/export/unknown in any allowlist |
| Live-walk evidence | PASS — 37 distinct screenshots, 0 mutations, lead auditor 18/18 |

## Check 5 — Live-walk evidence (PASS)

A read-only browser walk of **both** portals ran this session (headless Chrome on `HO-IT-PC10`,
navigation-only, no clicks, write-verb/auth requests aborted before the socket — Amendment-02
method). **37 distinct, non-trivial section screenshots** filed (`captures/vendorhub-walk/` = 13,
`captures/seller-walk/` = 24), all referenced from [[Flipkart-Live-Walk]] (0 orphans, 0 dangling,
0 byte- or content-duplicates). 0 login-redirects; the gate aborted 2 app-fired write requests.
Amendment-04 non-GET audit: **122 reads, 0 mutations, 15 telemetry** (`captures/nonget-*.tsv`).
The lead's auditor `monitor/audit.py` reports **18/18**.

## Honesty ledger — VERIFIED vs stated-gap

**VERIFIED live this session (browser walk + read-only GET):** all 6 gurvinder vendors enumerated;
JIVO MART's 3 active/0 suspended users, roles, 2 warehouses; **JIVO MART POs — 1 open (₹6.49 L,
3.3K units), ~750 completed (75 pages), ~570 cancelled (57 pages)**; 319 FK-warehouse dimension;
payments ₹0. Seller Hub JIVOMART — **listings 152 active / 26 blocked / 70 inactive / 182 archived**;
**73 requested + 3 scheduled reports**, 5 categories; **Upcoming Payment ₹3.9 L, payouts BLOCKED on
Ads dues**; impressions 1L–1.9L; ₹13 L weekly sales-loss flag; 4/4 GSTINs not e-invoicing.
0 × 401/403/429 across both walks — sessions healthy throughout.

**Stated gaps (not hidden, not padded):**
1. **8 of 9 vendor entities are PENDING_AUTH** — the walk was scoped to the selected vendor
   (JIVO MART); reading the others needs `POST /select-vendor` (not authored) or a walk after the
   app selects each. All 9 are named.
2. **Seller Ads campaign count NOT_REACHABLE** — the Ads page errored on the live walk; historical
   260 (JIVO Jul) kept as UNVERIFIED-today.
3. **Per-category report *type* enumeration: PENDING** — 5 categories + counts VERIFIED; the full
   type list per category needs the Type/Sub-Type dropdown opened (a future click-to-open pass) or
   `getReportsV2` (a POST).
4. **422 endpoints are UNKNOWN** — method/posture unresolved from the minified bundle; per G1
   documented but denied, never wired. The correct honest outcome, not a coverage miss.
5. **7 lazy chunks are hard-404** on the CDN — confirmed dead after a rotated-retry escalation.

A fabricated number would be the one unrecoverable failure; none appears here. Every figure carries
its source and a VERIFIED / UNVERIFIED-today / PENDING_AUTH / NOT_REACHABLE tag.

## Connections
[[00-Flipkart-Atlas]] · [[Flipkart-Endpoints]] · [[Flipkart-Data-Inventory]] · [[Read-Only-Guardrails]]
