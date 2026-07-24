---
title: Read-Only Guardrails
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, read-only, safety]
status: binding
---

# Read-Only Guardrails (BINDING)

This is the safety law governing **the whole Zepto seller-portal study and any Zepto CLI generated
from it**. It is not advice — it is a hard contract. During study and at every runtime of a derived
CLI, the only network effects allowed against Zepto are **HTTP `GET` pure-reads** and **the one
`POST` Login** that mints a session JWT. Everything else Zepto's frontend can do — enqueue a report,
upload a ledger, approve a PO amendment, dispute a debit note, pay an invoice, book/pause a campaign,
change a budget, edit catalog, activate a user — is **WRITE or EXPORT** and is **out of scope**,
enumerated so a future CLI can be checked against this list, never fired.

The corpus this study was built from is a static on-disk JS bundle + capture set; **no writes were
ever sent** while producing the section notes. That property must survive into any tool built on top.

## Why this is stricter than "just be careful"

Zepto exposes **741 distinct endpoints** across its backends (deduped in
`captures/js/endpoints-raw.json`). Their inferred verbs and read/write posture:

| Dimension | Breakdown (from the bundle constant maps) |
|---|---|
| HTTP method | 270 `GET` · 103 `POST` · 13 `PUT` · 3 `DELETE` · **352 `UNKNOWN`** |
| Read/write posture | 263 `READ` · 41 `READ_FILE` · 82 `WRITE` · 59 `EXPORT` · **296 `UNKNOWN`** |

Two facts make a naive "only touch what looks safe" approach unacceptable:

1. **~47% of methods and ~40% of the read/write labels are `UNKNOWN`** — inferred from a minified
   constant name, not proven from a live request. An `UNKNOWN` verb is treated as **potentially
   mutating** and is therefore **denied by default**. Never GET-probe an endpoint on the theory that
   "it's probably a read" — many Zepto mutations are modelled as `POST`/`PUT` on paths whose
   constant name (`SUBMIT_*`, `ACKNOWLEDGE_*`, `ACTIVATE_*`, `UPLOAD_*`) already tells you they
   write.
2. **Auth is a single bearer-less JWT that works across every Zepto backend and the WAF is not
   enforced** (see [[Auth-and-Access]]). There is no per-host permission wall and no WAF challenge
   catching a stray write — the only thing standing between the tool and a real mutation on JIVO's
   live seller account (Jivo Wellness Pvt. Ltd., Manufacturer/STANDARD,
   `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, ads `brand_id
   b3550d5d-fc71-47b0-af4f-f221f909b936`, login `ecom1@jivo.in`) is **this allowlist**.

## The one allowed write: Login

Login is the sole state-changing call permitted, exactly as every jivo-cli portal CLI treats it. It
`POST`s credentials to the Zepto identity backend and returns the JWT used (header
`authorization: <jwt>`, **no** `Bearer` prefix) for all subsequent reads. It creates a session, not
business data. Nothing else in the `POST`/`PUT`/`DELETE` space is ever fired.

## Concrete guardrails a Zepto read-only CLI MUST enforce

**G1 — HTTP method allowlist (deny-by-default).**
The HTTP client hard-codes an allowlist of exactly two shapes:
- `GET` — any read.
- `POST` — **only** to the single Login endpoint.
Every other method (`POST` to anything but Login, `PUT`, `PATCH`, `DELETE`, `UNKNOWN`) is refused
**in the transport layer**, before a socket opens. This is a code-level guard, not a convention: a
request object that isn't `GET` or the one Login `POST` throws instead of sending.

**G2 — Endpoint allowlist.**
Beyond the method gate, the reachable surface is an explicit allowlist of READ / READ_FILE paths
enumerated in the section notes and rolled up in [[Zepto-Endpoints]]. A path not on that allowlist is
not callable, even with a `GET`. New endpoints are added only after being classified READ in a note.

**G3 — No write/export verbs, ever.** The following classes are permanently excluded, matching the
`WRITE`/`EXPORT`/`READ_FILE`-that-triggers-generation labels in each section note:
- **No upload** — no ledger/recon upload, no ASN upload, no invoice/document upload, no
  `ads-bff/api/v1/reports/uploads`.
- **No schedule / enqueue / generate** — no `POST api/v1/reports/request`, no `.../retry`, no
  report scheduling. (See "Report generation" below — this is the subtle one.)
- **No approve / acknowledge / submit / confirm** — no PO amendment approval, no ASN submit, no
  RTV confirm, no `.../acknowledge` on receivable-vendor invoices.
- **No dispute / adjust** — no debit-note dispute, no ledger adjustment.
- **No pay / settle** — no payment initiation, no settlement action.
- **No campaign mutation** — no campaign/booking create, no keyword add/remove, no pause/resume,
  no budget or bid change, no wallet top-up, no creative upload/publish.
- **No identity/access mutation** — no activate/disable user, no role change, no KYC/onboarding
  submit, no subscription change.

**G4 — Report generation is side-effecting; poll + download only.**
The Vendor Reports Queue ([[Vendor-Reports-Queue]]) is an async export inbox. Requesting a report is
**not** a read: `POST api/v1/reports/request` with a `{reportType, reportPayload}` body **creates a
new report row** (SALES / INVENTORY / ads / etc.) and consumes queue/rate budget on the live account.
Therefore a read-only surface must:
- **NEVER enqueue** — `POST .../reports/request` and `.../reports/{id}/retry` are excluded by G1
  (method) and G3 (verb).
- **ONLY consume rows already generated by the portal UI** — `GET api/v1/reports` (list/poll the
  queue) and `GET api/v1/reports/{id}/download` (pull a presigned file). Both are pure reads.
This is exactly how the existing `zepto-cli` runs its SALES / INVENTORY / ads pulls today: it lists
the queue and downloads finished rows; it does **not** enqueue from the read-only path. The
capture-confirmed wiring lives in `captures/vendor/23-sales-list.txt` /
`23-sales-download.txt` (the safe legs) vs `23-sales-request.txt` (the excluded generate leg).
A read-only CLI treats `download` as its terminal action and never triggers generation.

**G5 — Stop on first `401` / `403` / `429`.**
Probes and runtime reads halt immediately on an auth or rate signal — no retry storms, no
credential-guessing, no walking adjacent paths after a refusal. This is how every section probe was
run (e.g. the Vendor Reports probe fired one `GET`, got `401 Token expired`, and stopped; 0
endpoints were upgraded to PROVEN). A `403` in particular may mean the endpoint is a write the server
gates differently — back off, do not escalate.

**G6 — JWT hygiene: `0600` + redacted.**
The Zepto JWT is a cross-backend credential (one token, all hosts, WAF not enforced) — treat it as a
live secret:
- Store it in a file with `0600` permissions (owner read/write only), never in shell history, args,
  env dumps, or committed config.
- **Redact it in all output** — logs, error messages, `--verbose`/`--debug` traces, and captures.
  The token's `emailId`/`exp` may be surfaced for diagnostics; the raw token string is never printed.
- Assume it may be **expired** — the study token's `exp` was Jul 13 2026, already dead at study time.
  Handle expiry as G5 (stop), not as a prompt to re-mint via any path but Login.

**G7 — No mutation even in "dry-run" or "test" framing.** A request that would write is refused
regardless of flags, comments, or intent. There is no `--force`, `--yes`, or `--write` escape hatch
in a read-only CLI; if such a flag is ever proposed it violates this note.

## How this maps onto the section notes

Every section note ([[Purchase-Orders]], [[ASN]], [[RTV]], [[Payments]], [[Ledger-Recon-Upload]],
[[Receivables]], [[Invoicing]], [[Ads-Campaigns-Booking-Keywords]], [[Ads-Billing-Wallet]],
[[Users-Access]], [[KYC-Onboarding]], … the full set in [[00-Zepto-Atlas]]) carries an explicit
**"Out of scope (writes) — never expose in a read-only CLI"** table listing that section's WRITE /
EXPORT / upload / schedule / approve endpoints as DOCUMENTED-FROM-BUNDLE-ONLY. Those tables are the
per-section instance of G3; this note is the global rule; [[Zepto-Endpoints]] is the consolidated
allowlist (READ/READ_FILE) vs excluded-list (WRITE/EXPORT/UNKNOWN) roll-up a CLI is validated
against.

## Connections

- Index: [[00-Zepto-Atlas]]
- Consolidated endpoint ledger (allowlist vs excluded): [[Zepto-Endpoints]]
- Auth model (single JWT, WAF-not-enforced, the Login write): [[Auth-and-Access]]
