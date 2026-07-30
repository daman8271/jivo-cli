---
title: Read-Only Guardrails
portal: Swiggy Instamart Brand + Supply Portal
type: meta
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
tags: [swiggy, instamart, guardrails, meta]
read_only: true
---

# Read-Only Guardrails — this platform's instance of the safety law

> **Nothing in JIVO's live Swiggy Instamart account was created, changed, approved, cancelled,
> paid, uploaded, generated or deleted by this study.** No request was ever authored by hand; no
> captured request was ever replayed. Everything below is the concrete, auditable form that claim
> takes on this platform.

## The law that applies here

| Rule | Swiggy-specific meaning |
|---|---|
| **G0** read-only vs live production | JIVO's real Instamart account, with 27 live ad campaigns, live POs against real distributors, and a live product catalogue. |
| **G1** unknown means denied | **18 endpoints** whose HTTP method could not be proven from the minified source are documented in full and wired into nothing. Same rule for UI controls. |
| **G2** never enqueue/generate | Swiggy's whole reporting model is *generate → poll → download presigned S3*. Listing and downloading are reads; **generating is a write** and burns the account's report quota. 8 EXPORT endpoints excluded. |
| **G4-NEW** (AMENDMENT-02) | Click anything that changes what you are **looking at**; never anything that changes what **exists**. |
| **G6** secret hygiene | `captures/scrub.py` runs over the whole capture tree after every pull. |
| **G9** consume, never mint | See the token-refresh block below — the single most important decision in this study. |

## What was clicked, and what was not

Navigation was the primary tool: **170 screenshots across 5 passes**, reached by changing the URL,
which is the purest form of changing only what you are looking at.

**Clicked (view-only):** account-selection tiles (they write `localStorage` and navigate; no API
mutation), PO-status filter tabs (`All POs`, `Open`, `Partially Open`, `Completed`, `Expired`),
`Pending POs` / `Scheduled Appointments` view toggles, `Real Time Summary` / `Detailed View`
toggles, sales-insights sub-tabs, `Reset Filters`, filter dropdown openers (then `Escape`).

**Never clicked, and found on real pages:** `Pick slot/s` and `Club selected POs & Book` (PO
Booking — these book a real delivery appointment), `Download Data` and `Bulk Download` (report
generation → G2), `Report` (opens an issue form), every create/edit route on the sampling,
discounts and catalog remotes, and every confirm-dialog button. Dialogs were **auto-dismissed,
never accepted**, so a modal could neither freeze the automation channel nor be confirmed.

**Never typed into any form field.** No `Enter` pressed in any form.

Controls that could not be classified were screenshotted and recorded as
`UNVERIFIED CONTROL — not exercised`. The filter sweep counted **41 unverified controls** across
13 vendor pages; none was clicked.

Two create-shaped routes were deliberately **not navigated at all** —
`/im-sampling/campaign/create` and `/im-discounts/campaign/create` — because a create screen can
fire a draft-create call on mount, which would be a write. They are logged as NOT_WALKED with
that reason in [[../../COVERAGE-LEDGER|COVERAGE-LEDGER.md]] rather than quietly skipped.

## The transport gate, and how it changed mid-study

**Passes 1–3** ran a strict gate: only `GET`/`POST`, plus a mutating-verb path deny-list. It
aborted **277 requests** before the socket opened. Reviewed honestly, that gate was **wrong in
two ways** and both are recorded rather than buried:

- **150 of the aborts were harmless image GETs.** Cloudinary's delivery path literally contains
  the segment `/upload/` (`media-assets.swiggy.com/swiggy/image/upload/...`), so a verb-token scan
  flagged every product image. Effect: blank images in some pass-1/2/3 screenshots.
- **4 aborts were a page navigation** — `GET /im-catalog/update-requests`, blocked because the
  *route* contains the word "update". That is why that route errored in pass 1. It was re-walked
  successfully afterwards.
- The remaining **123 aborts were all `POST /v1/token/refresh`** — the deliberate block below.
  **No app-fired data POST was ever aborted.**

**AMENDMENT-04** then opened the gate on Daman's explicit decision: every non-GET the
*application itself* fires during passive render passes through, with no method filter and no
mutation deny-list. Pass 4 ran under the open gate, which is why it recovered full response
bodies and the previously-blocked catalog route.

The authorization is scoped to the words **app-fired**, and this study did not exceed it:
**zero requests authored, zero captured POSTs replayed.** With the gate open, the click law above
is the only remaining guard, and it was applied more strictly, not less.

## The two blocks kept, and why

Both remain in force in pass 4 and both are self-preservation rather than mutation policy:

1. **`POST /v1/token/refresh`** (and any token-rotation equivalent). The refresh token is
   **single-use**: letting the app rotate it would invalidate the refresh chain held by JIVO's
   e-com team's own browser session *and* by the production keepalive cron, forcing an OTP
   re-login. That is a state change with a production consequence. Blocked **123 times** across
   the walks — the app attempts it on almost every page load. Identified independently by this
   worker, approved by the lead, and preserved explicitly by AMENDMENT-04.
2. **`/v1/accounts/signOut`** — would log out the human whose session this study borrowed.

## The AMENDMENT-04 audit trail

Because the coded mutation guard is gone, the **record** carries the weight. Every non-GET that
passed through is logged with timestamp, method, full URL, the page that triggered it, the request
**body shape with values redacted per G6**, and the response status:

- **`captures/nonget-allowed.tsv`** — **1,275 rows**, every app-fired non-GET that passed, with a
  `walk_pass` column. Of those, **980 are third-party telemetry** (New Relic, Swiggy analytics,
  Google Maps viewport calls from the sales-insights map) and **295 are real business calls**.
- **`captures/nonget-flagged.tsv`** — the subset whose path suggests state change
  (`create|update|delete|submit|approve|acknowledge|mark-read|pause|activate|pay|upload|generate|schedule|cancel|publish|launch|transition|reassign`).
  These were **not blocked** (Daman ruled no deny-list) but are surfaced so the accepted risk is
  visible rather than discovered later.

  **That file has 0 rows.** Across five walk passes and 1,275 app-fired non-GETs, **not one path
  matching a state-change verb was ever fired.** Every business call was a POST-to-read:
  `account/permissions` (148), `sales/metric` (34), `advertiser/metrics` (15), `campaigns` (12),
  `sales/filters` (9), `advertiser/metrics/report/list` (6), `get_spin_metrics` (6),
  `list_spins` (3), `search_categories` (3), `list_spin_change_requests` (3), `sales/reports` (3),
  `discount/reports` (3), `listAllFCs` (3), plus the vendor-lane search endpoints and
  `batch/list` (1).

Telemetry hosts are retained in the log but tagged, rather than dropped, so the record is complete;
they are excluded from the endpoint allowlist. See [[Telemetry-And-Third-Party]].

### What the account actually experienced, in one line

**295 business reads, 0 writes, 0 state-change-suspect calls, 1 file download of a report a JIVO
user had already generated.** The 132 blocked requests were 123 × token-rotation, 2 × logout-family
and the rest my own earlier false positives (documented above).

## What the read-only CLI may and may not reach

Of **134** catalogued endpoints:

- **exposed:** the **76** `READ`/`READ_FILE` rows whose method was *proven*.
- **never exposed:** all **32** `WRITE`, all **8** `EXPORT`, and all **18** `UNKNOWN`.

Three code-level layers, deny-by-default, in `cli/`:

1. **Transport** — the HTTP client refuses any method other than `GET`/`POST` (Swiggy serves most
   reads over POST, so POST cannot be banned outright), then checks the URL against the allowlist
   and a hard denylist. It throws *before a socket opens*.
2. **Allowlist** (`allowlist.go`, generated from `captures/endpoints-raw.tsv`) — only the **76**
   paths classified `READ`/`READ_FILE` **with a proven method** are reachable, even by `GET`.
   `WRITE`, `EXPORT` and `UNKNOWN` rows are absent by construction.
3. **Tests** — `guardrail_test.go` asserts ~40 write/session/enqueue endpoints are refused
   (including the Swiggy traps `batch/submit`, `get-upload-info-v2`, `fc-appointment/batch-*`,
   `signOut`, `token/refresh`, `initiate-sales-report`) **and** that the proven reads are not
   blocked; `guardrail_coverage_test.go` asserts every wired command passes the guardrail, that the
   command count equals the allowlist size, and that no write builder exists anywhere in the
   source — so a dead command, a drifted allowlist or a smuggled write all fail the build.

### A real hole layer 3 caught

`/api/v1/campaign/{0}` is a legitimate READ (the sampling remote's campaign-detail lookup). Its
`{0}` placeholder also matched the literal segment `batch` — so **`/api/v1/campaign/batch`, a bulk
bid and budget update, was being admitted by the template matcher.** It was caught by
`guardrail_test.go`, not by reading the code.

Fixed by generating an explicit `deniedPaths` set from every non-wired row and consulting it
**before** template matching, so an explicit exclusion always beats a placeholder match. A second
test now asserts a template cannot widen into a prefix match either. This is recorded because it is
precisely the failure a generated allowlist is meant to prevent and very nearly did not.

## Escalation

No CAPTCHA, account lock, "suspicious activity" notice, session invalidation or 2FA challenge
occurred at any point. Had one appeared, the rule was to stop that portal immediately and write
`BLOCKED_ACCOUNT_SIGNAL` with the exact message.

## Connections

- [[Auth-and-Access]] · [[Study-Verification]] · [[00-Swiggy-Instamart-Atlas]]
- [[Swiggy-Instamart-Endpoints]] — the allowlist itself
- [[PO-Booking-Appointments]] — the most write-dangerous page in the study
- [[Sales-Reports]] · [[Vendor-Downloads]] — where generate-vs-download matters most
- [[Telemetry-And-Third-Party]] — hosts deliberately excluded from the audit log
