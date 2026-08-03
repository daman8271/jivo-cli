# ecom.jivo.in — API facts, verified 2026-08-03

Everything here was observed live or read out of the shipped SPA bundle on
2026-08-03. Nothing is remembered from the July build. Where a fact could not
be established it says so; an unverified claim is worse than a gap.

## Shape of the app

| | |
|---|---|
| Host | `https://ecom.jivo.in` — SPA and API are the **same origin** |
| API prefix | `/api/` (paths in the client already carry it) |
| Backend | Django REST Framework |
| Frontend | React, bundled by **rolldown** (not the plain Vite/rollup layout the factory app uses) |
| Chunks | 152 JS chunks reachable from `index.html`, closed after 5 fetch rounds |
| Auth | SimpleJWT bearer. `POST /api/auth/login` mints, `POST /api/auth/refresh` rotates. **There is no `/api/auth/token/refresh`** — that path 404s |
| Tenancy | **Single tenant.** No `Company-Code` header, no per-company database. The scoping dimension here is the *platform slug*, not a company |

### There is no frozen endpoint registry

The factory app declares its whole API in one frozen constant. **Ecom does
not.** Its surface lives in two hand-written service modules:

| Module | Size | Role |
|---|---|---|
| `assets/api-<hash>.js` | 43 KB, imported by 81 chunks | every domain except shipment |
| `assets/shipmentAPI-<hash>.js` | 7.5 KB | the shipment domain |

So the registry-first harvest in the skill does **not** apply here. The
equivalent high-precision lens is to parse those two modules, because each
endpoint is one object entry whose *helper function is its HTTP verb*:

| helper | verb | how it was resolved from source |
|---|---|---|
| `X(path, params)` | **GET** | `X = we(Ce(path, params))`; `Ce` builds the URL, `we` calls `fetch(url, {cache:'no-store'})` with **no** `method`, so GET |
| `Z(path, body)` | POST | `method:'POST'`, JSON body |
| `Te(path, form)` | POST | multipart upload |
| `Ee(path, body)` | POST | export, returns a blob |
| `i(VERB, path)` (shipmentAPI) | explicit | the verb is the first argument |

That yields a *precise* verb per call site rather than an inferred one, which
is what RULE 0 turns on: only GET entries may ever be published.

### The extraction trap here is different from factory's

Rolldown rewrites **every** string literal to a backtick template, so factory's
"literals get dropped, templates get captured" bias cannot occur. The bias that
does occur is **nested templates**:

```js
`/api/shipment/inventory/${e ? `?warehouse=${encodeURIComponent(e)}` : ``}`
```

Two failures came out of this and both pointed at deleting working endpoints:

1. A naive `` `[^`]*` `` regex closes the outer literal at the first inner
   backtick and truncates the path to `/api/shipment/inventory/${e`.
2. A normaliser that collapses every `${...}` to `{}` turns it into
   `/api/shipment/inventory/{}` — inventing a path parameter, marking the
   endpoint unprobeable, and reporting the real collection root
   `/api/shipment/inventory` as "shipped but no longer called".

Six paths hit this. `research/scripts/normalise.py` handles it and carries a
self-test proving both directions. **Run that self-test before trusting any
diff computed from it.**

## Platform slugs — the scoping dimension

**The authoritative list is the `platforms` array on `GET /api/auth/me`.** All
ten, read live on 2026-08-03:

```
amazon  bigbasket  blinkit  citymall  flipkart
flipkart_grocery   jiomart  swiggy    zepto     zomato
```

That matches spec v0.1.0 exactly. Corroborating per-slug evidence from the
probe:

| slug | independent evidence |
|---|---|
| `amazon` | 200 on `/api/platform/amazon/stats` |
| `bigbasket` | 200 on its own ads dashboards |
| `blinkit` | 200 on its own ads/brandfund dashboards |
| `flipkart` | 200 on `flipkart-ads-dashboard`, `flipkart-fsn-dashboard` |
| `flipkart_grocery` | named by the server in a 400 body as valid for landing-rate |
| `swiggy` | 200 on its own ads/brandfund dashboards |
| `zepto` | 200 on its own ads/brandfund dashboards |
| `zomato` | listed by `/api/dashboard/platform-expiry-alerts` |
| `citymall`, `jiomart` | in `/api/auth/me` `platforms` only — no route was exercised against them this run |

**Do not take the slug list from `/api/dashboard/platform-expiry-alerts`.** It
reports only 7, because it lists platforms that currently *have expiry data*.
That is a **data** fact, not a **routing** fact, and conflating the two is how
a working platform gets reported as unsupported. `/api/auth/me` is the
routing-level answer.

## Platform-scoped routes are restricted, and the server says how

This is the single most important operational fact in this document.

Probing every `/api/platform/{slug}/...` route with one slug (`amazon`) returns
**17 × 400 and 2 × 404**. Read naively that is 19 dead endpoints. It is not.
Each 400 body names the platforms the route is actually for:

```
["Blinkit Ads Dashboard is available only for Blinkit."]
["Monthly landing rate is only available for blinkit, zepto, swiggy,
  bigbasket, flipkart_grocery."]
["Monthly Sales Explorer is available for bigbasket, blinkit, swiggy, zepto only."]
["Pendency dashboard is not yet enabled for platform 'amazon'."]
```

Re-probed against the platform each body named, **all 17 return 200**.

| route (`/api/platform/{slug}/…`) | available for |
|---|---|
| `bigbasket-ads-dashboard`, `bigbasket-ads-daily-dashboard` | bigbasket |
| `blinkit-ads-dashboard`, `blinkit-brandfund-dashboard`, `blinkit-summary-report` | blinkit |
| `flipkart-ads-dashboard`, `flipkart-fsn-dashboard` | flipkart |
| `swiggy-ads-dashboard`, `swiggy-ads-daily-dashboard`, `swiggy-brandfund-dashboard` | swiggy |
| `zepto-ads-dashboard`, `zepto-ads-daily-dashboard`, `zepto-brandfund-dashboard` | zepto |
| `landing-rate`, `landing-rate/skus` | blinkit, zepto, swiggy, bigbasket, flipkart_grocery |
| `monthly-sales-explorer` | bigbasket, blinkit, swiggy, zepto |
| `pendency-dashboard` | blinkit, zepto, swiggy, bigbasket (not amazon) |
| `region-doh-dashboard` | **swiggy, zepto only** — 404 on amazon, blinkit, bigbasket, flipkart_grocery, zomato |

### Two kinds of 404, and they mean opposite things

- **Routing 404** — Django's plain HTML `<h1>Not Found</h1>` from the URL
  resolver. Slug-independent. The route does not exist. → dead.
- **View-level 404** — raised inside the view, so it *varies by slug*.
  → the endpoint is alive, just not for that platform.

`region-doh-dashboard` is the second kind and a single-slug probe would have
killed a working endpoint. `month-on-month-sale` is the first kind, 404 on all
six slugs tried, and is the only genuinely dead endpoint found this run.

## The Amazon Shipment Planner is gated off this credential

All 19 shipment endpoints probed return **403**:

```
{"detail":"You do not have access to the Amazon Shipment Planner."}
```

The gate is the permission **`amazon.shipment_planning.view`**, read from the
SPA's own permission map (`assets/permissions-<hash>.js`):

```js
{shipmentPlanning:`amazon.shipment_planning.view`, pricing:`pricing.view`, …}
```

The operator credential (`dp605702@jivo.in`) holds 144 permissions including
`view_shipment`, `dispatch.view`, `admin.dispatch.manage` and
`platform.amazon.access` — but **not** `amazon.shipment_planning.view`, and
`is_superuser` is `false`, so the superuser bypass in that same module does not
apply.

**A 403 is proof the endpoint exists and is routed.** It is the opposite of
proof of death. All shipment endpoints are carried forward and marked gated.
What cannot be verified from here is their response shape — that is recorded as
unverified rather than guessed.

`/api/reports/live/data` and `/api/reports/live/reports` also 403, with DRF's
generic `"You do not have permission to perform this action."` — a different,
server-side-only gate that the SPA's permission map does not name.

## Endpoints that need a parameter — the server names it

A bare GET returning 400 is a useful result: the body names the requirement
verbatim, with no value guessed.

| endpoint | required |
|---|---|
| `/api/dashboard/category-platform-breakdown` | `name` |
| `/api/dashboard/category-sku-breakdown` | `name` |
| `/api/dashboard/state-sales/detail` | `state` |
| `/api/platform/call-center-targets` | `month` (1–12), `year` (YYYY), integers |
| `/api/platform/month-targets/dashboard` | `month`, `year` |
| `/api/platform/primary-month-targets/dashboard` | `month`, `year` |
| `/api/reports/amazon-po/matrix` | `month`, `year` |
| `/api/reports/columns` | `view` (rejects empty: `Unknown report view: ''`) |
| `/api/reports/raw` | `view` |
| `/api/sap/sales-analysis` | `from_date`, format `YYYY-MM-DD` |

## Broken: `/api/sap/sales-invoice-lines/{DocEntry}`

Deterministic 500 on **every** DocEntry tried (37594, 37603, 37601 — all taken
from a live `/api/sap/sales-invoices` response):

```
{"detail":"SAP HANA error: (260, 'invalid column name: T1.UnitMsr:
 line 4 col 28 (at pos 115)')"}
```

The backend's SQL selects a column that does not exist on that table. This is a
server-side defect, not a client or credential problem. Excluded from the spec
as `KNOWN_BROKEN` with the reason recorded, so it can be published the day it
is fixed. Reported in `FINDINGS-FOR-ECOM-TEAM-2026-08.md`.

## Probe safety — what was done and what was proven

- **GET only.** No other verb was ever sent to this host.
- **No invented parameter values.** Every substituted value came from a live
  200 payload or from a 400 body in which the server itself named the legal
  set. Paths whose parameter had no observed value were **skipped**, not
  guessed (13 of them, mostly shipment routes behind the 403 gate).
- **46 client-side write endpoints** (`/add`, `/update`, `/delete`,
  `/bulk-upsert`, `/preview`, `/refresh`, `/mark-read`, `/approve`, …) were
  never probed at all and are excluded from the spec. Probing them buys nothing
  — they could not be published either way — and a bare GET to an action route
  is the exact shape that created six production rows on the factory app.
- **Creation check.** Six collections were byte-snapshotted before and after
  the parameterised sweep; none changed. Responses were scanned for
  `created_at`/`updated_at` inside the probe window; the only same-day
  timestamps found (09:24:42 and 05:27:42) predate the probe by hours and
  belong to normal business activity. **Nothing was created.** This is evidence
  of absence, not proof — a create that returns no timestamp would be invisible
  — and it does not license loosening any of the above.
- **Concurrency.** 4 workers. **Zero** transport failures (`http: 0`) across
  89 requests, so the serial reprobe pass had nothing to recover. Recorded
  explicitly because a failure to measure is not a measurement.
