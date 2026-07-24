---
title: Ledger (Recon & Upload)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, ledger]
status: studied
---

# Ledger (Recon & Upload)

The **Ledger (Recon & Upload)** section is Zepto's **accounts-receivable reconciliation** surface —
where JIVO (Jivo Wellness Pvt. Ltd., Manufacturer, STANDARD tier, `manufacturer_id
946950b7-1ce2-4bdf-a7c4-37499e3f5f34`) compares **its own books** against **Zepto's ledger**, works
the differences down to a closing balance, and — at the end of a cycle — signs off a reconciliation
**statement**. It has two halves that share one page: a **Recon** half (working listings, closing
balances, the signed-off statement, an "external view" the vendor can toggle on) and an **Upload**
half (the vendor uploads its own ledger extract as an attachment, Zepto ingests it, and a
reconciliation is triggered against Zepto's side). The whole section is served by `fcc.zepto.co.in`
under two path families — `vendor/api/v1/ledger-recon/*` (recon) and `vendor/api/v1/ledger-upload/*`
(upload) — plus one cross-service `api/v1/reconciliation/inventory/reports` call, all under the
single Zepto JWT (header `authorization: <jwt>`, **no** `Bearer` prefix) that works across every Zepto
backend. The endpoint contracts below were read out of the vendor micro-frontend bundle (remote
`vendor(635)`, chunk `captures/js/vendor/3539.64ab07c46b8741b5.js`) as the named API-constant object
`LEDGER_RECONCILIATION={GET_LEDGER_UPLOADS, GET_LEDGER_UPLOAD_COUNT, GET_LEDGER_SUMMARY, GET_UPLOAD_URL,
GET_PRESIGNED_URL, GET_TEMPLATE, CREATE_LEDGER, BULK_DOWNLOAD, TRIGGER_RECON, GET_RECON_STATEMENT,
SIGN_OFF_STATEMENT, SAVE_SIGNED_COPY, GET_VENDOR_LEDGER_LISTING, GET_ZEPTO_LEDGER_LISTING,
GET_RECON_WORKINGS_LISTING, GET_CLOSING_BALANCES, GET_EXTERNAL_VIEW_STATUS, TOGGLE_EXTERNAL_VIEW,
GET_RECON_USER_DATA}` — the constant *names* (e.g. `GET_*` vs `CREATE_*`/`TRIGGER_*`/`SIGN_OFF_*`) are
what fix each endpoint's read/write classification below.

## SPA routes

The section is mounted under both the bare and the `/vendor`-prefixed shells; `/reconciliation` and
`/accounts-receivable/ledger` are the two entry points, with the recon sub-page under each:

- `/accounts-receivable/ledger`
- `/reconciliation`
- `/reconciliation/ledger`
- `/vendor/accounts-receivable/ledger`
- `/vendor/reconciliation`
- `/vendor/reconciliation/ledger`

## Backend host

- `fcc.zepto.co.in` — the vendor reconciliation + ledger service. Two path families,
  `vendor/api/v1/ledger-recon/*` and `vendor/api/v1/ledger-upload/*`, plus the cross-cutting
  `api/v1/reconciliation/inventory/reports` (report-generation). Single JWT auth; WAF headers
  (`waf-enabled`, `x-aws-waf-token`, `x-proxy-target: brand-analytics`) appear in sibling captures
  but were **not enforced** as of the last verified capture. The public edge fronts these paths with a
  **bifrost/kong** gateway that rewrites the `vendor/` service prefix — see the probe note below.

## What the page shows

The Recon half is a working-list → closing-balance → statement funnel:
- **Recon workings listing** (`GET_RECON_WORKINGS_LISTING`, `ledger-recon/working/filter`) — the
  filtered list of reconciliation line-items/workings (the diffs between the two ledgers).
- **Closing balances** (`GET_CLOSING_BALANCES`, `ledger-recon/working/closing-balances`) — the netted
  closing balance the workings roll up to.
- **Recon statement** (`GET_RECON_STATEMENT`, `ledger-recon/statement/details`) — the reconciliation
  statement document details for the cycle, which the vendor then **signs off** and **saves a signed
  copy** of (both writes; see out-of-scope).
- **External view** (`GET_EXTERNAL_VIEW_STATUS` / `TOGGLE_EXTERNAL_VIEW`,
  `ledger-recon/external-view/*`) — a status flag + toggle that exposes/hides the vendor-facing
  external view of the recon.
- **Recon user data** (`GET_RECON_USER_DATA`, `ledger-recon/recon-user-data`) — the acting user's
  recon context/permissions.

The Upload half is the vendor's own-ledger ingest queue:
- **Ledger uploads list / count / summary** (`GET_LEDGER_UPLOADS`, `GET_LEDGER_UPLOAD_COUNT`,
  `GET_LEDGER_SUMMARY`; `ledger-upload/{list,count,summary}`) — the queue of uploaded ledger files
  with a headline count + summary tiles.
- **Vendor & Zepto ledger listings** (`GET_VENDOR_LEDGER_LISTING`, `ledger-upload/vendor`;
  `GET_ZEPTO_LEDGER_LISTING`, `payment/ledger/zepto`) — the two sides of the reconciliation: the
  vendor's uploaded ledger vs Zepto's system ledger.
- **Bulk download** (`BULK_DOWNLOAD`, `ledger-upload/bulk-download`) — pull the uploaded/reconciled
  ledger back as a file.
- The **upload itself** (`GET_UPLOAD_URL` → `CREATE_LEDGER` → `TRIGGER_RECON`, plus `GET_TEMPLATE` /
  `GET_PRESIGNED_URL`) is the write flow — see out-of-scope. `GET_UPLOAD_URL`, `GET_PRESIGNED_URL` and
  `GET_TEMPLATE` (`attachment/*`) are the upload plumbing and are **not** part of this section's
  endpoint extract; they surface under [[Platform-Common]] (attachment service).

## API endpoints (reads)

Base = `https://fcc.zepto.co.in/` + path. Constants from the bundle object `LEDGER_RECONCILIATION`
(chunk `3539.64ab07c46b8741b5.js`). Method column: `GET` where the bundle wires a GET; "GET (to
confirm)" where the constant is named `GET_*` (a read) but the exact verb was not directly observed
(several list/summary constants in this map read via a GET with query params). "documented (not
probed)" = wiring confirmed in the bundle, not live-verified this session — see probe note.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/vendor/api/v1/ledger-recon/external-view/status` | External-view toggle **status** (`GET_EXTERNAL_VIEW_STATUS`). **documented (not probed)** — probe returned bifrost `404 path-not-found`. | READ |
| GET | `/vendor/api/v1/ledger-recon/recon-user-data` | Acting user's **recon context/permissions** (`GET_RECON_USER_DATA`). **documented (not probed)** — probe `404`. | READ |
| GET (to confirm) | `/vendor/api/v1/ledger-recon/statement/details` | Reconciliation **statement details** for the cycle (`GET_RECON_STATEMENT`). | READ |
| GET | `/vendor/api/v1/ledger-recon/working/closing-balances` | Netted **closing balances** of the recon workings (`GET_CLOSING_BALANCES`). **documented (not probed)** — probe `404`. | READ |
| GET | `/vendor/api/v1/ledger-recon/working/filter` | **Recon workings listing** (filtered diff line-items) (`GET_RECON_WORKINGS_LISTING`). | READ |
| GET (to confirm) | `/vendor/api/v1/ledger-upload/count` | **Count** of ledger uploads (`GET_LEDGER_UPLOAD_COUNT`). | READ |
| GET (to confirm) | `/vendor/api/v1/ledger-upload/list` | **List** of uploaded ledger files (`GET_LEDGER_UPLOADS`). **documented (not probed)** — probe `404`. | READ |
| GET (to confirm) | `/vendor/api/v1/ledger-upload/summary` | Ledger-upload **summary** tiles (`GET_LEDGER_SUMMARY`). **documented (not probed)** — probe `404`. | READ |
| GET | `/vendor/api/v1/ledger-upload/vendor` | **Vendor's own** uploaded ledger listing (`GET_VENDOR_LEDGER_LISTING`). **documented (not probed)** — probe `404`. | READ |
| GET (to confirm) | `/vendor/api/v1/payment/ledger/zepto` | **Zepto's system** ledger listing — the other side of the recon (`GET_ZEPTO_LEDGER_LISTING`). Present in the same constant map; not part of the 16-endpoint section extract but documented here as the recon counterpart. | READ |
| GET | `/vendor/api/v1/ledger-upload/bulk-download` | **Bulk download** the uploaded/reconciled ledger as a file (`BULK_DOWNLOAD`; read effect, no state change). | READ (file) |

## Out of scope (writes)

Never expose in a read-only CLI; documented from the bundle only, never called. Classification is
pinned by the constant *name* (`CREATE_*`/`TRIGGER_*`/`SIGN_OFF_*`/`SAVE_*`/`TOGGLE_*`/`REQUEST_*`).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST (to confirm) | `/api/v1/reconciliation/inventory/reports` | **Generate** an inventory-reconciliation report (`REQUEST_REPORTS`) — enqueues an async report job. Sibling of the `brand-analytics-web/*` vendor/city-level recon listings (those live under [[Stock-View-Inventory]]). Mutates the report queue. | EXPORT (report-generation) |
| POST (to confirm) | `/vendor/api/v1/ledger-recon/external-view/toggle` | **Toggle** the external-view flag on/off (`TOGGLE_EXTERNAL_VIEW`). State-changing. | WRITE |
| POST (to confirm) | `/vendor/api/v1/ledger-recon/statement/sign-off` | **Sign off** the reconciliation statement (`SIGN_OFF_STATEMENT`) — commits the vendor's acceptance of the cycle. State-changing. | WRITE |
| POST/PUT (to confirm) | `/vendor/api/v1/ledger-recon/statement/save-signed-copy` | **Save the signed copy** of the statement (`SAVE_SIGNED_COPY`) — uploads/attaches the signed document. State-changing (upload). | WRITE |
| POST (to confirm) | `/vendor/api/v1/ledger-upload/create` | **Create** a ledger upload (`CREATE_LEDGER`) — registers the vendor's uploaded ledger extract. State-changing (create/upload). | WRITE |
| POST (to confirm) | `/vendor/api/v1/ledger-upload/trigger-recon` | **Trigger reconciliation** against the uploaded ledger (`TRIGGER_RECON`) — kicks off the recon compute. State-changing. | WRITE |

## Real data seen (evidence)

- **Wiring is bundle-confirmed, not invented.** All 16 section endpoints resolve to the named
  `LEDGER_RECONCILIATION` constant object in `captures/js/vendor/3539.64ab07c46b8741b5.js`; the
  `GET_*` vs `CREATE_*`/`TRIGGER_*`/`SIGN_OFF_*`/`SAVE_*`/`TOGGLE_*`/`REQUEST_*` naming is the source
  of the read/write split above. The recon-inventory sibling `REQUEST_REPORTS` sits in the same file
  next to `GET_VENDOR_LEVEL_LISTING`/`GET_CITY_LEVEL_LISTING` (`brand-analytics-web/api/v1/
  reconciliation/inventory/{vendor,city}-level-listing`).
- **Auth shape.** Same single Zepto JWT as every vendor section — `authorization` header, **no**
  `Bearer` prefix; token identity `emailId ecom1@jivo.in`, `roleName "External Super Ads Admin"`,
  `category External`; captured token `exp = 1783967399` (Mon Jul 13 2026), so **expired** at study
  time (2026-07-24).
- **Probe result — 0 PROVEN.** Six read-only GET probes were fired against the pure-read endpoints
  (`closing-balances`, `external-view/status`, `ledger-upload/{list,summary,vendor}`,
  `recon-user-data`), ~1 req/s. Every one returned **HTTP 404** — bifrost/kong `"path not found"` /
  `"no Route matched"` — i.e. the public edge rewrites the `vendor/` service prefix and these
  upstreams are not mounted for an unauthenticated/expired session; no probe reached a 2xx and none
  hit a 401/403/429/WAF stop. All endpoints therefore remain **documented (not probed to 2xx)**.
  Transcript: `captures/vendor/ledger-probes.txt`. A fresh JWT + live SPA session would be needed to
  verify the listings/balances/statement reads live and capture their row schemas.
- **Response schemas uncaptured.** No `captures/vendor/*ledger*.json` bodies exist, so exact filter
  keys (date window / cycle / facility), the closing-balance shape, the statement document fields,
  and the upload-queue row schema still want a live (read-only) capture — flagged inline.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no create, no trigger-recon, no sign-off, no toggle, no
report-generation):

- `zepto ledger recon workings [--filter …]` → `GET ledger-recon/working/filter` — the recon
  workings/diff listing. Pure READ.
- `zepto ledger recon balances` → `GET ledger-recon/working/closing-balances` — netted closing
  balance. Pure READ.
- `zepto ledger recon statement` → `GET ledger-recon/statement/details` — the recon statement (read
  only; **never** `sign-off` / `save-signed-copy`). Pure READ.
- `zepto ledger recon external-view` → `GET ledger-recon/external-view/status` (status only; **never**
  `toggle`). Pure READ.
- `zepto ledger uploads list [--offset --limit]` / `zepto ledger uploads count` /
  `zepto ledger uploads summary` → `GET ledger-upload/{list,count,summary}`. Pure READ.
- `zepto ledger vendor-ledger` / `zepto ledger zepto-ledger` → `GET ledger-upload/vendor` /
  `GET payment/ledger/zepto` — the two sides of the recon. Pure READ.
- `zepto ledger download [--out FILE]` → `GET ledger-upload/bulk-download` — pull the reconciled
  ledger file. Pure READ (file).

Explicitly **excluded** from the read-only surface: `ledger-upload/create` (create),
`ledger-upload/trigger-recon` (trigger), `ledger-recon/statement/sign-off` (sign-off),
`ledger-recon/statement/save-signed-copy` (save signed copy), `ledger-recon/external-view/toggle`
(toggle), and `reconciliation/inventory/reports` (report-generation) — all state-changing. A strict
read-only CLI must only **consume** recon/upload data already produced by the portal UI, never create,
trigger, sign, toggle, or enqueue.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- **Tightest siblings** — the money lane this recon settles against: [[Payments]] (settlements/UTR),
  [[Receivables]] (AR / non-trade vendor), and [[Invoicing]] (the invoices whose amounts feed the
  ledger). The recon statement reconciles what these three report.
- The `reconciliation/inventory/reports` generate call and its `brand-analytics-web` vendor/city
  listings belong to [[Stock-View-Inventory]]; any bulk export lands in [[Vendor-Reports-Queue]].
- Upload plumbing (`attachment/get-upload-url`, `get-presigned-url`, `get-template`) is shared
  platform infra documented under [[Platform-Common]].
