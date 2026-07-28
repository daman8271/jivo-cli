---
title: Architecture
type: reference
tags: [jivo, control-panel, architecture]
---
# Architecture — Jivo Group Control Panel

See also: [[00-INDEX]] (map of content).

## Overview
"Jivo Group — Control Panel" is an **internal Django ERP/analytics dashboard** for JIVO Wellness, layered on top of **SAP Business One** as the system of record. It reads sales, order-book, receivables, inventory and production data out of SAP and presents it as KPI dashboards and drill-downs.

- **Base:** `http://103.89.45.75:9080` (plain HTTP, internal IP).
- **Access used for recon:** logged in as `preshit` = **Admin**. ⚠️ **LIVE PRODUCTION — treat as READ-ONLY.**

## Tech stack
- **Backend:** Django on the dev **WSGIServer** (CPython 3.14) — not a hardened prod gateway.
- **Rendering:** each route serves a **server-rendered HTML shell**; the shell then hydrates itself with **AJAX calls to `/…/api/` JSON endpoints**. The page is a thin skeleton + a fat client-side fetch layer.
- **No SPA framework / no public API contract** — endpoints are internal AJAX helpers keyed to each page's JS.

## Auth model — session cookie + CSRF
- **Authentication:** Django **session cookie** (`sessionid`). Log in once; the cookie jar carries every request. If a call returns the login HTML instead of JSON → the session died → re-authenticate.
- **CSRF:** state-changing **POST** calls require `X-CSRFToken: <csrftoken cookie>` in addition to the session cookie (Django's cookie-to-header CSRF).
- **XHR gate:** **GET** read endpoints require the header `X-Requested-With: XMLHttpRequest`; without it the server returns 403/404 (they are AJAX-only, not directly browsable).
- **Extra gates:** [[cogs]] (`/api/cogs/`) is **OTP-gated** (`param_type` + `otp`); credit lock/unlock and some admin actions sit behind a PIN ([[verify-pin]]).

## The three call patterns
1. **POST-JSON (read):** `Content-Type: application/json` + `X-CSRFToken`; body carries the query, usually a date range — e.g. [[sales-data]] `{start_date,end_date,refresh?}`, [[sales-cn]], [[dispatch-details]], [[drill-down]], [[export-xlsx]].
2. **GET-XHR (read):** header `X-Requested-With: XMLHttpRequest`, no body — e.g. [[customer-master]], [[claims]], [[oih-breakdown]], [[health]].
3. **GET-query (read):** GET-XHR **plus URL query params** — e.g. [[targets]] `?month=&year=`, [[flex-targets]] `?seg=`, [[order-in-hand-rows]] `?…`, [[inventory-stock-available-data]] `?schema=`, [[inventory-daily-production-data]] `?start=&end=`.

## Endpoint namespacing
- **`/realise/api/*` — the shared Realise API.** One namespace serves **three UI areas at once**: Control Panel (`/`, home JS sets `API='/realise'`), **Sales** (`/realise/…`) and **Accounts** pages. This is the largest surface (~50 endpoints): sales, targets, order-in-hand, aging, claims, rate-list, exports. See [[00-INDEX]] area A.
- **`/inventory/<page>/api/*` — per-page inventory APIs.** Each inventory screen owns its own sub-namespace, e.g. `stock-available/api/data/`, `production/api/{plan,feasibility,fg-list,warehouses}/`, `reconciliation/api/{data,ledgers}/`. See [[00-INDEX]] area B.
- **`/api/*` — top-level, privileged.** [[cogs]] (OTP-gated COGS/margin) and [[users]] admin write. See [[00-INDEX]] area C.

## Read-only posture (recon discipline)
This is a **live production ERP**. The vault documents mutating endpoints but they are **never executed**: `save-targets`, `save-closing-remark`, `rate-list/save`+`delete`, `realise-calculator/upload`+`order-upload`, the `aging-remark*` family, `credit-lock`/`credit-unlock`, `verify-pin`, `/api/users/save`+`delete`, and `/api/cogs` (OTP). POST *read* endpoints are sampled with the **smallest possible date range** (a single day) to learn schema without pulling months of data. See [[users]], [[save-targets]], [[credit-lock-unlock]], [[aging-remark]], [[rate-list-save]], [[rate-list-delete]], [[verify-pin]].

## Known quirks
- `/inventory/oih-vs-stock/` nav link **404s** at source — documented in [[oih-vs-stock]].
- [[beverages-data|Beverages]] runs on a **separate data track** from oils (own endpoints); see [[segments-oils-beverages]].
