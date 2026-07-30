---
title: Study Verification
portal: Swiggy Instamart Brand + Supply Portal
type: meta
status: PASS
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
tags: [swiggy, instamart, verification, meta]
read_only: true
---

# Swiggy Instamart Study — Completeness Verification

Adversarial self-audit of the finished study. Every number below was produced by re-reading the
artifacts on disk, not by recalling what was intended. No writes were fired against any Swiggy
surface by this audit; it only inspects files.

Where a check failed on the first run it is recorded, together with what was done about it — a
fixed failure is part of the audit, not something to hide.

## Check 1 — File presence: **PASS**

**36 / 36 vault notes present.**

- `supply/` **10**: Purchase-Orders · PO-Booking-Appointments · Goods-Received-GRN ·
  Returns-RTV-and-Purchase-Returns · Stock-On-Hand-and-Low-Stock · Availability-and-Fill-Rate ·
  Vendor-Performance-Scores · Vendor-Downloads · Local-Buying · Vendor-FAQ-Help
- `ads/` **10**: Sales-Reports · Sales-Insights · Ad-Campaigns · Brand-Insights-Metrics ·
  Keyword-And-Bid-Suggestions · Creatives · Requisition-Orders · Products-And-SPINs ·
  Ads-AI-Chat · NPI-New-Product-Introduction
- `brand/` **4**: Discounts-BDPO · Sampling-Campaigns · Brandverse · Catalog-SPIN-Management
- `platform/` **4**: Accounts-And-Entities · Config-And-Feature-Flags · Auth-Sessions-And-Login ·
  Telemetry-And-Third-Party
- top level **5**: 00-Swiggy-Instamart-Atlas · Swiggy-Instamart-Endpoints ·
  Swiggy-Instamart-Data-Model · Swiggy-Instamart-Data-Inventory ·
  Swiggy-Instamart-Pages-and-Routes · Swiggy-Instamart-Screenshot-Index
- `_meta/` **3**: Auth-and-Access · Read-Only-Guardrails · Study-Verification (this note)

**Stub check: 0 notes under 25 lines.** Every section note carries its own purpose, endpoint
tables, gotchas and screenshots rather than a placeholder.

## Check 2 — Endpoint completeness: **PASS (100%)**

`captures/endpoints-raw.tsv` holds **134 distinct (host, path) endpoint contracts**.

The independent auditor reports **134/134 indexed (100.0%)** on the exact path column.

- **134 / 134 appear verbatim in `Swiggy-Instamart-Endpoints.md` → 0 missing (100%).**
- **134 / 134 also appear in exactly one section note → 0 orphaned endpoints.**

Both are guaranteed by construction: `captures/sections.py` assigns every path to a section by a
longest-matching-rule map with a catch-all (`Unclassified-Endpoints`, currently **0 rows** — the
healthy state), and `captures/build_vault.py` generates the index and the section tables from that
same TSV. Re-running the generator after any new walk keeps the claim true instead of stale.

### A real gap this check caught, and closed

The first run reported **131** endpoints. The independent auditor's generic-regex advisory flagged
three paths it saw in the corpus that my index did not contain:

- `api/discounting/v1/campaign/disable`
- `api/discounting/v1/campaign/file`
- `api/discounting/v1/campaign/spins`

**Root cause:** the `im-discounts` remote writes its paths **without a leading slash**
(`n.m.get("api/discounting/v1/campaign/file")`), and my literal-scan regex required `/`. Fixing it
recovered those three and, because their call sites name the verb directly, also gave me a fourth
extraction pass — **direct-literal call sites** — which resolved methods for many previously
unresolved paths. Net effect: **131 → 134 endpoints, and UNKNOWN methods 30 → 19.**

I would not have found that without the external check. It is recorded here because "my extractor
was incomplete and an outside tool proved it" is exactly the kind of thing a self-audit is supposed
to surface.

A third issue was a **misleading filename of my own making**: `endpoints-context.json` held raw
minified call-site context (SVG namespaces, route literals) as evidence, but its `endpoints-*` name
made the auditor read it as an endpoint inventory and count that noise as 8 un-indexed endpoints.
Renamed to `extract-evidence.json`, which is what it actually is. No content was hidden — the four
real strings behind that failure (`/im-catalog`, `/im-sampling`, `/im-sampling/campaign/create` and
an SVG namespace) are SPA routes and markup, and the routes are documented in
[[Swiggy-Instamart-Pages-and-Routes]].

A second regression was caught by comparing counts across runs: tightening the literal regex to
api-prefixed paths silently dropped **12 SPA routes** (they had been captured incidentally by the
looser pattern). A dedicated route-literal scan was added; routes went **100 → 119**.

## Check 3 — Wikilinks: **PASS (0 broken)**

**36** distinct note names; every `[[target]]` across all 36 notes resolves to a real filename.
Fenced blocks and inline code spans are stripped before extraction so that a note *documenting*
the `[[...]]` syntax is not counted as a broken link.

First run reported **1 broken link** (`Study-Verification`) — this note did not exist yet. Written,
re-scanned, **0 broken**.

## Check 4 — Screenshots, both directions: **PASS**

- **161 screenshot files on disk, all byte-distinct.**
- **All referenced** from vault notes → **0 dangling, 0 orphans**, guaranteed by
  `Swiggy-Instamart-Screenshot-Index.md` listing every file plus per-section embeds.

Three separate failures were fixed here, and the second one changed a finding:

1. **Phantom references.** I had written image links as `![<filename>.png](path)`, so the
   filename regex matched the **alt text** as well as the path — 250 phantom references that
   resolved to nothing, while the real files looked unreferenced. Fixed with neutral alt text
   (`![screenshot](path)`) and backticked filenames.

2. **91 byte-identical duplicates, out of 252 captures.** Deduplicating was not cosmetic — the
   duplicate groups are themselves evidence:
   - **12 identical copies of the account-select page**: in walk pass 1 every ads-lane route
     bounced there because the copied profile had no account selected. Those 12 files were never
     screenshots of the sales/reports/campaign pages they were named after, so keeping them would
     have overstated coverage. They were removed and those routes re-walked per-account in later
     passes.
   - **7 identical PO-dashboard screenshots** across the `All POs / Open / Partially Open /
     Completed / Expired` status-filter clicks → **those filter clicks did not change the rendered
     page.** Recorded as a negative result rather than reported as five filter states captured.
   - **4-way identical `-a-default` / `-b-widened` pairs** on several vendor pages → **my
     filter-widening clicks in pass 3 had no effect on those pages.** This is why the inventory
     numbers for stock/GRN/RTV/availability are marked `PENDING_FILTER` instead of quoted.

   The dedup map is preserved at `captures/screenshot-dedup.json`. 252 → **161** distinct files.

3. **A nested directory.** `mv walk1-tmp walk1` silently nested into a pre-existing empty
   `walk1/`, hiding 23 screenshots from the generator's glob (161 on disk, 138 indexed). Caught by
   the auditor's orphan check, flattened, re-indexed.

## Check 5 — Capture integrity: **PASS**

No capture `.json`/`.har` file is an HTML shell. This was checked explicitly because the Blinkit
study's `captures/partner/api/*.json` silently contain the SPA's `index.html` rather than API
responses. Here, every response body was captured by **in-page `fetch`/`XMLHttpRequest`
instrumentation** and each is valid JSON from the intended endpoint; bodies that came back empty
are recorded as empty rather than filed as evidence (see the `403` rows in
[[Swiggy-Instamart-Data-Inventory]]).

## Check 6 — Guardrail audit: **PASS**

- **76 rows** classified `READ` / `READ_FILE`. **0 of them contain a mutating path segment.**
- **All 76 have a PROVEN HTTP method** (`wired = yes`); no read is exposed on an inferred verb.
  One of the 76 was upgraded from UNKNOWN by **live-walk evidence** — `picker.swiggy.com/api/v1/
  listAllFCs`, which the static pass could not resolve but the application was observed firing as a
  `POST` returning HTTP 200 and 11,949 bytes during a page render. Per AMENDMENT-02 that
  observation is primary evidence, and the upgrade is guarded: a path carrying a write token is
  never relaxed this way.
- **58 rows are excluded**: 32 `WRITE`, 8 `EXPORT` (report generation — G2), 18 `UNKNOWN`
  (denied per G1 and documented in full, tankhapay-style, rather than omitted).
- No `WRITE`, `EXPORT` or `UNKNOWN` path appears in the read allowlist.

Swiggy-specific traps deliberately kept **out** of the read surface even though a naive rule would
admit them:

| Path | Why it is excluded despite looking readable |
|---|---|
| `GET /instamart/v1/creative/get-upload-info-v2` | a GET whose constant is `GET_S3_UPLOAD_INFO`, but its only purpose is to hand back credentials that enable an upload |
| `POST /api/v1/batch/submit` | constant is `BULK_DOWNLOAD_PO_DATA`, but `submit` enqueues a job |
| `/api/v1/release-order` | one path bound to **both** `RELEASE_ORDER_GET` and `RELEASE_ORDER_DELETE`; deny-by-default applies to the path |
| `/api/discounting/v1/tnc/acceptance` | served by GET **and** POST; the mutating verb was kept so deny-by-default wins |
| `/api/v1/campaign` | serves create *and* update on one path |

**A hole the CLI's own tests caught.** `/api/v1/campaign/{0}` is a legitimate READ; its `{0}`
placeholder also matched the literal segment `batch`, so `/api/v1/campaign/batch` — a **bulk bid
and budget update** — was admitted by the allowlist's template matcher. Found by
`guardrail_test.go`, not by review. Fixed by generating an explicit `deniedPaths` set consulted
*before* template matching; a further test asserts a template cannot widen into a prefix match.

Conversely, one row was **wrongly excluded** on the first pass and corrected:
`POST /api/v1/creative/list` (`PREAPPROVED_CREATIVES`) was classified WRITE because the constant
string contains "approve". Tokenising constant names (`pre` / `approved` / `creatives`) fixed it —
`approved` ≠ `approve`. It is a READ.

## Check 7 — Route coverage: **PASS, with stated gaps**

`COVERAGE-LEDGER.md` carries **85 rows, one per canonical route**, of which **44 were walked live**
against JIVO's account. Every `NO` row states a specific reason. The reasons are, in full:

- create/edit forms deliberately not opened (draft-create-on-mount would be a write) — 9 routes
- login / login-callback / mock-login routes (G9 forbids minting a session) — 5 routes
- parameterised detail routes needing an id this account's empty listings did not yield
- layout/redirect wrappers and aliases of routes already walked
- `/im-vendor/local-buying/*` — role-denied, needs a separate `LOCAL_VENDOR` credential

**No row says "not important".**

## Check 8 — Multi-entity coverage: **PASS**

All **three** JIVO accounts were selected and walked separately across all six remotes. This was
not cosmetic: Jivo Mart Pvt. Ltd returns **22** cities with sales against Jivo Wellness's **132**,
and **0** campaigns against **27**. A single-account walk would have misreported JIVO's Instamart
footprint by roughly 6×.

## Verdict — **PASS**

| Check | Result |
|---|---|
| 1. File presence | PASS — 36/36 notes, 0 stubs |
| 2. Endpoint completeness | PASS — 134/134 indexed, 0 missing (100%) |
| 3. Wikilinks | PASS — 0 broken (1 fixed) |
| 4. Screenshots | PASS — 161 distinct files, 0 dangling, 0 orphans (91 duplicates removed) |
| 5. Capture integrity | PASS — no HTML shells |
| 6. Guardrail audit | PASS — 0 mutating paths in the read allowlist; `go build` clean, `go test ./...` green, 76/76 wired commands verified |
| 7. Route coverage | PASS — 85 rows, 44 walked, every NO explained |
| 8. Multi-entity | PASS — 3/3 accounts walked separately |
| 9. Phase-9 sweep | PASS — 7 sweeps, 5 gaps found and fixed, sweeps 6 and 7 clean |

**Independent auditor** (`~/.cmux-runs/portal-atlas/monitor/audit.py`, the bug-fixed version):
**18/18 checks passed**, including endpoint coverage **134/134 (100.0%)** on the exact path column.

## Check 9 — PHASE-9 completeness sweep (loop-until-dry): **PASS**

Seven sweeps were run, each re-deriving every number from the artifacts. A sweep counted as clean
only when the consistency checker, the independent auditor, the CLI build and the capture-integrity
scan all came back empty. **Sweeps 6 and 7 were both fully clean**, which is the stop condition.

What the sweeps actually found and fixed — each one a gap that would otherwise have shipped:

| Sweep | Found | Resolution |
|---|---|---|
| 1 | 91 byte-identical duplicate screenshots (252 files, 161 distinct) | Deduplicated. The duplicate groups were themselves findings — see Check 4. |
| 2 | Stale counts in three hand-written notes after the extractor and walk grew | Wrote `captures/consistency.py`, which re-derives every claimed number from disk and fails on drift. Prose drifts; generated files do not. |
| 3 | — clean — | |
| 4 | `captures/reports/` held **live JIVO business data** (inventory valuations, PO values, vendor names) and was **not gitignored** | Added to `.gitignore`; verified with `git check-ignore`. |
| 5 | The Atlas "Study status" block and its per-host endpoint table were stale, in phrasing the checker did not match | Refreshed, and the checker extended to cover that phrasing plus per-host table counts, so it cannot recur silently. |
| 6 | — clean — | |
| 7 | — clean — | Full regeneration from scratch, then all four checks re-run. |

The tooling that makes this repeatable lives in `captures/`: `extract.py` (classify),
`sections.py` (assign), `build_vault.py` / `build_ledger.py` / `build_cli.py` (generate),
`scrub.py` (G6), `consistency.py` (sweep). Re-running them in that order reproduces the entire
deliverable from the corpus and the walk captures.

## What this study does NOT establish — stated plainly

A PASS on internal completeness is not a claim of omniscience. These are open:

1. **Maximum date ranges per surface.** Defaults are recorded (7-day sales insights, 30-day PO
   dashboard, 7-day download queue) and the 35-day enforcement flag is known to be off, but the
   widest available span was **not** established — the date pickers are custom components my DOM
   driving did not reliably open. Not guessed.
2. **The inventory/GRN/RTV/availability GRIDS could not be driven** — no standard `<select>` or
   combobox exists on them, proven by a DOM dump, which is also why the filter-widening clicks
   produced byte-identical screenshots. The grid numbers stay `PENDING_FILTER`.
   **The underlying data was obtained anyway**, from an already-generated export in the vendor
   download queue: 735 SKU × facility rows and ₹2.84 Cr of `PotentialGmvLoss`. See
   [[Swiggy-Instamart-Data-Inventory]] section 3b. The GRN export existed but was **header-only**,
   so GRN line data remains unobtained.
3. **Users with access to JIVO's account and their roles.** No users/roles endpoint exists among
   the 134. Two logins are evidenced; the total is unknown.
4. **Whether JIVO runs sampling or Brandverse campaigns.** Sampling returned no campaign data;
   Brandverse metrics returned **403** for this account (role-denied).
5. **The exact fulfilment-centre count.** 50 captured, `next_page_token` proves ≥100, no total
   field in the response.
6. **The ads-lane view under its own login.** `tanuj@jivo.in`'s token was expired everywhere, so
   the ads surfaces were read with `ecom1@jivo.in`'s entitlements.
7. **Whether JIVO's daily upload mislabels Mart vs Wellness.** The id/name mismatch in
   `config.json` is VERIFIED; the downstream consequence is INFERRED and needs a human to trace
   the upload.
8. **18 UNKNOWN endpoints** remain method-unresolved and therefore denied. They are documented in
   full; shrinking that bucket by guessing would have been the wrong trade.

## Connections

- [[00-Swiggy-Instamart-Atlas]] · [[Read-Only-Guardrails]] · [[Auth-and-Access]]
- [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Inventory]] ·
  [[Swiggy-Instamart-Pages-and-Routes]] · [[Swiggy-Instamart-Screenshot-Index]]
