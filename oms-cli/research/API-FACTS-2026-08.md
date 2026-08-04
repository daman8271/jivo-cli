# OMS API — facts established 2026-08-04

Everything below was measured against the live `https://oms.jivo.in` API or read
out of the deployed SPA bundle. Where a fact came from a live call, the status
code is quoted. Where it was read from code, it says so. Nothing here is
inferred from the shipped spec — the shipped spec is what this run was checking.

Credential used: `paramjot` (role `admin`, company `Jivo Wellness`, category
`OIL`, 27 main-groups, 27 states). Some findings are scoped to what this
credential can see; those are marked.

---

## 1. The transport surface is a single axios instance

The whole API surface goes through **one** client. There is no second
transport: `fetch(` appears once (Vite's module preloader), `XMLHttpRequest`
four times (inside axios's own adapter), and the only `.create({` that matters
is axios's.

```js
var Ea = `https://oms.jivo.in/api`.replace(/\/+$/, ``)
var Da = Ea.replace(/\/api$/i, ``)                 // "https://oms.jivo.in", media/asset URLs
var Y  = Ta.create({ baseURL: Ea, headers:{ "Content-Type":`application/json` } })
```

That makes the harvested set a real denominator rather than a sample.

### The /api trap — a `/api/`-anchored harvest undercounts ~3.5x

Because the base URL already carries `/api`, **most call sites use a relative
path with no `/api/` in it**:

```js
Y.get(`/hana/so/`, { params:{ card_code:e } })
Y.delete(`/orders/${e}/delete-draft/`)
```

Measured on this build: a naive `grep '/api/...'` finds 33 templates; the real
surface is 125 paths. Anchor on the client and its verbs, never on the string
`/api/`.

### Three call shapes, and each defeats a different lens

| # | shape | example | seen by |
|---|---|---|---|
| A | literal at the call site | ``Y.get(`/orders/schemes/`)`` | verb-anchored lens |
| B | absolute path through a wrapper | ``X6(Q6(`/api/hana/so/`, br))`` | `/api/`-literal lens |
| C | path in a local or module const | ``let i=`/orders/list/`+q; Y.get(i)`` | **neither** |

Shape B's wrappers all terminate in the same instance:

```js
q6 = e => `${Ea}${/\/api$/i.test(Ea) ? e.replace(/^\/api/i,``) : e}`   // build URL
J6 = e => ({ url:q6(e), baseURL:`` })
X6 = async (e,t) => Y.request({ url:J6(e).url, method:t?.method||`GET`, ... })
Z6 = async (e,t,n=`POST`) => Y.request({ ..., method:n, data:t })       // multipart
Q6 = (e,t) => `${e}${e.includes(`?`)?`&`:`?`}branch=${encodeURIComponent(t)}`
```

Shape C was found the way `harvest.md` predicts: `/api/orders/list/` is
shipped and working, yet came back "not harvested". A shipped, working endpoint
missing from the harvest is the tell of extraction bias, not a quirk of that
endpoint. Chasing it recovered `/api/legal/{item,uom,nutrition,item-nutrition}/`
and `/api/ui-config/labels/` as well.

**`X6`'s method defaults to GET.** Anything that reads the method from an
adjacent options object and falls back to GET will label
`/api/service-layer/invoice/` — which POSTs a document into SAP B1 — as a
readable GET endpoint, because its write happens through a URL held in a local.
Method inference has to fail closed.

---

## 2. `branch` is the tenant selector, it is REQUIRED, and the shipped CLI cannot send it

This is the most consequential finding of the run.

Every `/api/hana/*` endpoint rejects a call that omits `branch`:

```
GET /api/hana/all-customers/          -> 400 {"error":"branch is required and must be one of: OIL, BEVERAGE"}
```

All **14** of them, without exception. The shipped `oms-spec.yaml` declares
`branch` on **none** of them, and `oms-pp-cli` exposes no `--branch` flag, so
every shipped `hana` command fails. Verified by running the shipped binary, not
by reading the spec:

```
$ oms-pp-cli hana fg-items
Error: GET /api/hana/fg-items/ returned HTTP 400: {"error":"branch is required and must be one of: OIL, BEVERAGE"}
```

14 of 73 shipped commands — 19% of the CLI — are dead on arrival. This is the
`Company-Code` failure of the factory rescrape repeating in a different costume:
the commands exist, the help text reads correctly, and not one of them can
succeed. Presence is not correctness.

### `branch` selects a real SAP company database

It is not a filter or a label. Same endpoint, same credential, same second:

| endpoint | `branch=OIL` | `branch=BEVERAGE` |
|---|---|---|
| `hana/all-customers/` | 1172 rows | 1247 rows |
| `hana/fg-items/` | 443 rows — CHAI 250 GMS, COLD PRESS 1 LTR | 336 rows — PET BOTTLE 250 ML MINERAL WATER |
| `hana/open-parties/` | 58 rows | 31 rows |
| `hana/freight-masters/` | 11 rows, `FREIGHT INWARD DRCT` | 10 rows, `FREIGHT INWARD` |

A card code can exist in both with different figures — `CUSTA000636` has 55
open sales orders under OIL and 41 under BEVERAGE. **Quoting a HANA number
without naming its branch is meaningless**, exactly as an SAP figure is
meaningless without its company database.

### `branch` and `category` are DIFFERENT enums — do not substitute one for the other

| param | valid values | source |
|---|---|---|
| `branch` (hana/*, service-layer/*) | `OIL`, `BEVERAGE` | server's own 400 body |
| `category` (sap/parties/category/, auth/*) | `OIL`, `BEVERAGES`, `MART` | live `GET /api/auth/categories/` |

Note the singular/plural split and — more importantly — **`MART` exists as a
category but not as a branch**. OMS's HANA layer reaches Oil and Beverages
only; there is no route to JIVO Mart through it. `GET /api/sap/parties/category/`
does serve MART (verified 200, distinct rows). This mirrors correction
**C-0008** for ecom, where the SAP mirror is Mart-only — each JIVO app sees a
different slice of the three SAP companies, and the slice is never all three.

---

## 3. Live status of the surface

125 distinct paths harvested; 87 GET-capable. 105 probe records, zero
unmeasured (one transport failure recovered on the serial retry pass — it would
otherwise have been indistinguishable from "endpoint absent").

| code | count | meaning |
|---|---|---|
| 200 | 51 | live and readable |
| 400 | 37 | exists, GET works, a required param is missing — the body names it verbatim |
| 403 | 12 | permission-gated for this credential; **exists** |
| 500 | 3 | backend crash |
| 502 | 2 | backend crash reaching HANA |

### The 403s are a permission wall, not death (skill rule 4)

All 12 are `/api/tracker/*`, and the bodies distinguish two separate gates:

```
{"detail":"Tracker administration is restricted to tracker admins."}   admin/stages, admin/tracker-users, admin/users, all-invoices, all-invoices/export
{"detail":"You do not have access to this tracker page."}              alerts, invoices, lookups, my-queue, reports, stage-advanced, vendors
```

The credential is a global `admin` and still fails both, so tracker access is a
**separate grant** from the app role. These endpoints ship, with their response
shapes marked UNVERIFIED.

### Backend defects — these are the OMS team's, not the CLI's

| endpoint | status | server said |
|---|---|---|
| `/api/hana/product-stock/` | 502 | `name 'unique_schemas' is not defined` — a Python `NameError` |
| `/api/sku/pending/` | 500 | `SalesOrderService.getFGItems() missing 1 required positional argument: 'branch'` |
| `/api/invoice/all/` | 400 | `Warehouse Code is a required parameter.` — but no param name accepts it |

`/api/sku/pending/` returns a full Django debug traceback to an authenticated
caller, leaking the internal origin `http://127.0.0.1:8001` and the Django
version. `DEBUG` appears to be on in production. Written up for the OMS team.

`/api/invoice/all/` is shipped as a working command and cannot be called: six
param names observed elsewhere in this same API (`warehouse`, `warehouse_code`,
`whs_code`, `WarehouseCode`, `warehouseCode`, `wh_code`) all return the same
400. The SPA never calls this route, so there is no observed call to copy. The
contract is unresolved — recorded rather than guessed at further.

---

## 4. Required-param contracts, quoted from the server

The bare probe sends no query parameters at all, precisely so the server names
its own requirements instead of us guessing values at it.

| endpoint | required | server's words |
|---|---|---|
| `hana/address/` | `branch`, `card_code` | `card_code is required` |
| `hana/all-customers/` | `branch` | — 200, 1172 rows |
| `hana/batch-details/` | `branch`, `item_code`, `whs_code` | `item_code and whs_code are required` |
| `hana/customer-details/` | `branch`, `card_code` | `card_code is required` |
| `hana/fg-items/` | `branch` | — 200, 443 rows |
| `hana/freight-masters/` | `branch` | — 200, 11 rows |
| `hana/inventory-details/` | `branch`, `item_code` | `item_code is required` |
| `hana/item-price/` | `branch`, `item_code`, `price_list` | `item_code and price_list are required` |
| `hana/next-doc-number/` | `branch`, `doc_type` | `doc_type is required` |
| `hana/open-parties/` | `branch` | — 200, 58 rows |
| `hana/product-so/` | `branch`, `item_code` | `item_code is required` |
| `hana/product-stock/` | `branch` | 502 — backend defect |
| `hana/salesperson-details/` | `branch`, `slp_code` | `slp_code is required` |
| `hana/so/` | `branch`, `card_code` | `card_code is required` |
| `orders/addresses/` | `card_code` | `card_code is required` |
| `orders/status-tracking/` | `mode` | `mode must be auditor, billing, or rate_approver` |
| `sap/parties/category/` | `category` | `category query parameter is required` |
| `invoice/credit-limit/flow/` | `invoice_id` | `invoice_id is a required parameter.` |

Enum values used in follow-up probes came from the server's own error text
(`mode`), a live payload (`category` from `/api/auth/categories/`), or the app's
own constants (`branch`) — never from a guess. `mode=auditor|billing|
rate_approver` all return 200.

---

## 5. Writes — every one of these is an exclusion, never a probe target

RULE 0 is absolute for OMS. The harvest found **38 non-GET call sites**. They
are recorded so the assembler can deny them by normalised path, not so they can
be wrapped.

Order/quotation lifecycle: `orders/create/`, `orders/create-scheme/`,
`orders/{id}/update-status/`, `orders/{id}/cancel-quotation/`,
`orders/{id}/delete-draft/`, `orders/schemes/{id}` (PATCH, DELETE),
`orders/notifications/{id}` (PATCH), `orders/web-push/subscribe/`.

Invoice/SAP: **`service-layer/invoice/` (POST — submits a document into SAP
B1)**, `invoice/pending/`, `invoice/{id}/update-status/`,
`invoice/credit-limit/request/`, `sap/approve-sales-order/`, `sap/sync/{id}/`,
`tracker/jsap/sync/`, `tracker/invoices/{id}/payment/`, `tracker/actions/bulk/`.

User/party administration: `auth/users/create/`, `auth/users/{id}` (PUT),
`auth/assign-parties/`, `auth/assign-parties/bulk-upload/`,
`auth/remove-party/`, `auth/bulk-party/assign-products/`,
`auth/party-product/{bulk-add,remove,update-rate}/`.

Admin/config: `tracker/admin/{lookups,stages,tracker-users}/{id}` (PATCH,
DELETE), `tracker/admin/users/{id}/stages` (PUT), `ui-config/admin/labels/{id}`
(PUT, DELETE), `devices/register/`, `sku/upload/`, `legal/upload/`.

Auth mutators, excluded from publication and from probing:
`auth/login/`, `auth/logout/`, `auth/refresh/`.

**Dual-verb paths**: several paths serve GET *and* a write on the same URL
(`orders/flow-config/`, `orders/notifications/`, `orders/party-flow-config/`,
`orders/staff-products/`, `tracker/invoices/`, `tracker/invoices/{id}`,
`tracker/admin/{lookups/{type},stages,tracker-users}`, `ui-config/admin/labels/`).
The GET is publishable; the write verb on the same path is not. An exclusion
list keyed on path alone would wrongly kill the read.

---

## 6. Auth contract (needed by the MCP token rotator)

```js
Oa = [`/auth/login/`, `/auth/refresh/`, `/auth/logout/`]     // interceptor's no-retry set
Ta.post(`${Ea}/auth/refresh/`, { refresh: e }) -> { access, refresh }
```

- login: `POST /api/auth/login/` `{username, password}` ->
  `{data:{user:{...}, tokens:{access, refresh, token_type:"Bearer", expires_in:86400}}}`
- refresh: **`POST /api/auth/refresh/`** `{refresh}` -> `{access, refresh}`
- access token TTL 24 h; refresh token TTL 7 d (measured from the JWT `exp`).

**Refresh rotation is ON** — the refresh call returns a *new* refresh token. A
rotator that keeps re-presenting the original refresh token will therefore die
after 7 days regardless of how often it runs. That is precisely how the OMS MCP
connector died: both tokens expired (access 2026-07-24, refresh 2026-07-30), so
it could not self-heal and needed a fresh password login to re-seed.

**Security note for the OMS team:** the login response includes the user's
`password` field — the full PBKDF2 hash — in the user object. There is no reason
for a client to receive it.

---

## 7. Traps for whoever writes commands against this API

- **Never quote a HANA figure without its branch.** Two companies, one endpoint.
- **`branch` ≠ `category`.** `BEVERAGE` vs `BEVERAGES`, and `MART` exists only
  as a category.
- **A 0-row 200 is a data fact, not a scoping fact.** `orders/parties/`,
  `orders/products/`, `orders/staff-products/` and `sku/all/` all return `[]`
  for this credential. That is what this user is assigned, not evidence the
  endpoint is empty for everyone. Do not encode it as a constraint.
- **Django trailing slashes.** Every route terminates in `/`. The app always
  sends it.
- **`orders/list/` takes `status`, `billing=true`, `approval_pending=true`** —
  read from the app's own query builder, so safe to send verbatim.
- `sap/addresses/` returns **35,722 rows / 11.8 MB** and `orders/stock-check/`
  **1,900 rows / 1.06 MB** in a single unpaginated response. Any command
  wrapping these needs `--compact`/`--csv` to be usable.
