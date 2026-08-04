# Adversarial refutation — `study-account.md` and `study-tracker.md`

Written 2026-08-04 against the live `https://oms.jivo.in` API, GET only, with the
`paramjot` token at `/tmp/oms-rescrape/token.txt` and against the deployed bundle
`/tmp/oms-rescrape/bundle/index-NnIXJV2m.js` via `peek.py`/`str.find`.

**Headline.** Both studies survive on every claim I was sent to break. Their
*internal* reasoning is sound and, in the tracker's case, better supported than
the study itself argued. What does not survive is their **denominator**: both were
harvested from the SPA's call sites, and the server's own URLconf — which this API
hands out unauthenticated on any 404 — lists **five routed `account` paths that
appear in neither study**, including two working reads and three writes that are
absent from the RULE 0 denylist.

**Method note that changes everything downstream.** `DEBUG = True` in production
means a bogus path returns Django's technical-404 page, and that page prints
`Using the URLconf defined in OMS.urls, Django tried these URL patterns, in this
order:` — the authoritative route list. That is a free, exact denominator for
every domain in this rescrape, and it is available without a token. It was not
used by either study.

**One rule-2 deviation of my own, disclosed:** I sent `?category=NONSENSE_VALUE_X`
to two proven-read filter endpoints to test whether the value is validated. It is a
query filter on a GET, not an entity key, so it cannot create anything. Every other
value I sent was observed.

---

## Claim 1 — the tracker 403 basis

### "Every one of the 12 GET paths that could be probed bare returned HTTP 403. Per skill rule 4 and the study contract, a 403 is a permission wall, not death: all of them are published"

- **verdict**: **CONFIRMED** — and the study understated its own case.
- **evidence**: The parent's hypothesis was that a nonexistent tracker path might
  also 403, which would drain 403 of all existence information. It does not.
  Same token, same host, same second:

  ```
  GET /api/tracker/definitely-not-a-real-endpoint/  -> 404  Django "Page not found" HTML
  GET /api/tracker/zzzz-bogus-404-probe/            -> 404  Django "Page not found" HTML
  GET /api/tracker/admin/definitely-not-real/       -> 404  Django "Page not found" HTML
  GET /api/auth/definitely-not-a-real-endpoint/     -> 404  Django "Page not found" HTML
  GET /api/definitely-not-a-real-domain/            -> 404  Django "Page not found" HTML

  GET /api/tracker/lookups/       -> 403 {"detail":"You do not have access to this tracker page."}
  GET /api/tracker/my-queue/      -> 403 {"detail":"You do not have access to this tracker page."}
  GET /api/tracker/admin/stages/  -> 403 {"detail":"Tracker administration is restricted to tracker admins."}
  ```

  Absent routes 404 with HTML; gated routes 403 with JSON. On this API **403 is
  decisive evidence of existence.**

  Stronger still: the 404 page enumerates the URLconf. It lists **exactly 22
  tracker routes**, and they are exactly the 22 paths in the study — no more, no
  fewer, with the study's own `{id}`/`{type}` positions matching the server's
  `<int:pk>` / `<str:kind>` converters:

  ```
  tracker-lookups · tracker-vendors · tracker-invoices · tracker-invoice-detail
  tracker-invoice-payment · tracker-invoice-jsap · tracker-jsap-sync · tracker-my-queue
  tracker-stage-advanced · tracker-bulk-action · tracker-reports · tracker-alerts
  tracker-all-invoices · tracker-all-invoices-export · tracker-admin-stages
  tracker-admin-stage · tracker-admin-lookups · tracker-admin-lookup
  tracker-admin-users · tracker-admin-user-stages · tracker-admin-tracker-users
  tracker-admin-tracker-user
  ```

  **The tracker domain's coverage is provably complete: 22 routed, 22 studied,
  15 published + 7 excluded.** This is the only domain in the rescrape whose
  denominator has been checked against the server.

  I also closed one of the study's own open items. It marked
  `admin/lookups/{type}` as "no status code at all… gate assignment inferred from
  siblings, confidence high but unmeasured". Probed with a value from the app's own
  constant `j9`:

  ```
  GET /api/tracker/admin/lookups/categories/ -> 403 {"detail":"Tracker administration is restricted to tracker admins."}
  GET /api/tracker/admin/lookups/gst_rates/  -> 403 {"detail":"Tracker administration is restricted to tracker admins."}
  ```

  Gate **A**, measured, as inferred. That line in the study can be upgraded.

- **weakness worth naming**: the study *asserted* rule 4 rather than *testing* it
  on this server. The reasoning was right, but it was borrowed authority, not
  evidence, until now. Every future study in this rescrape should run the
  bogus-path control before publishing anything on a 403.
- **impact if the study were wrong**: 15 commands shipping against routes that do
  not exist, each failing with an unexplained error. It is not wrong.

---

## Claim 2 — the bundle-derived shapes

### "The bundle contains the whole tracker client in one object literal — minified name `y9`, at offset 1902743–1905980 … one method per endpoint"

- **verdict**: **CONFIRMED**. Spot-checked 13 separate assertions; 13 held.
- **evidence**: `y9` begins at 1902743 exactly and runs to 1905981. Verified
  verbatim, among others:
  - `v9=[{value:'DEMURRAGE'…},{value:'LABOUR_COST'…},{value:'POINT_VALUE'…}]`
    at 1902575 — the `additional_charge_type` enum, as claimed.
  - `async myQueue(){let{data:e}=await Y.get('/tracker/my-queue/');return e},`
    immediately followed by
    `async getStageAdvanced(e){…Y.get('/tracker/stage-advanced/',{params:{stage:e}})…}`.
    The study quoted this correctly, character for character.
  - `exportAllInvoices(…){…Y.get('/tracker/all-invoices/export/',{params:t,responseType:'blob'})}`
    and, at 1982338, `saveAs(await y9.exportAllInvoices(i),'invoice-register.xlsx')`.
  - `adminGetUsers(e=''){…{params:e?{search:e}:{}}}` — the lone `search` param.
  - `j9=[{kind:'categories'},{kind:'units'},{kind:'branches'},{kind:'modes'},{kind:'gst_types'},{kind:'gst_rates'}]`
    at 1950109 — six kinds, as claimed.
  - `my-queue` consumer: `let e=await y9.myQueue(); r(e.invoices), a(e.stages)`
    at 1928263, polling `setInterval(H,3e4)` — the `{invoices, stages}` shape and
    the 30 s poll, both as claimed.
  - Reports export builder at 1969027 names `summary`, `pending_by_stage`,
    `avg_days_per_stage`, `bottleneck_by_person`, `bottleneck_by_vendor`,
    `bottleneck_by_category`, `ageing` — the study's six report keys, exactly.
  - Alerts row at 1978440 renders `stage_name`, `days_stuck`, `threshold_days`,
    `over_by.toFixed(1)` — including the float claim.
  - `Cn={tracker_admin:'Tracker Admin',tracker_entry:'Invoice Entry',tracker_user:'Tracker User'}`
    at ~233559 — the tracker role enum, as claimed.
  - `all-invoices` filter bar: `overdue` is a `<select>` whose `<option value>`s are
    the **strings** `"true"`/`"false"`. The study's "sent as strings, not booleans"
    is right, and it matters — the service strips boolean `!1` but not the string
    `"false"`, so a CLI passing a real bool would silently drop the filter.
- **the one thing I expected to break, and why it did not**: `listInvoices` has
  **four** occurrences in the bundle (1856384, 1869398, 1902860, 1908033), and the
  study claims "the SPA's only call site passes `{}`". Two of the four belong to a
  *different* service object — `Y7`, the e-invoice client, calling
  `einvoice/invoices/` with `company_db`/`search`/`limit`. Only 1902860 (the `y9`
  definition) and 1908033 (`y9.listInvoices()`, bare) are the tracker's. The study
  is right, and right for the right reason.
- **two cosmetic inaccuracies, neither shippable**:
  1. The server names the `admin/lookups` path segment **`kind`**
     (`admin/lookups/<str:kind>/`), not `type`. The study and the shipped spec both
     say `type`. It is positional, so nothing breaks, and rule 3 forbids the
     rename — but the operator doc should mention the server's name.
  2. The study cites the lookups destructure at "offsets 1914400–1915100"; the
     actual `gst_types`/`gst_rates` references sit at 1914161/1914250. The fields
     are real, the window is off by ~250 bytes.
- **impact if the study were wrong**: 15 commands with invented field names, which
  would surface only when a tracker-enabled operator finally ran one. It is not
  wrong at the level I could check.

---

## Claim 3 — flipping `response: object` to `array`

### "The shipped spec declares `type: object` for all 73 endpoints; the probe shows many are arrays" — applied to the tracker with no live payload

- **verdict**: **CONFIRMED**, at high confidence for array-vs-object and **low
  confidence for scalar field types** (which the study itself says).
- **the exact scope of the flip**: the shipped spec has **14** tracker endpoints,
  all `response: type: object`. The study publishes 15 (the 14 shipped names
  unchanged, plus `tracker invoice-jsap` as new) and reclassifies **9 of the 14** —
  8 to `array`, 1 (`all-invoices-export`) to binary XLSX. Five stay `object`
  (`lookups`, `invoice-detail`, `invoice-jsap`, `my-queue`, `reports`).
- **evidence**: every one of the 8 array claims has an independent tell in the
  bundle — the consumer either initialises state with `useState([])` and assigns
  the awaited response straight into it, or calls an array method on the response
  itself. An object would throw on first render.

  | endpoint | the tell |
  |---|---|
  | `vendors` | `C.filter(t=>t.card_name…).slice(0,50)` on the response state |
  | `invoices` | `y9.listInvoices()` → `h.filter(e=>e.current_stage_code==='entry')` |
  | `stage-advanced` | `[C,w]=useState([])`; `getStageAdvanced(o).then(w)` |
  | `alerts` | `useState([])`; `e.forEach(e=>t.set(e.stage_name,…))` |
  | `all-invoices` | `useState([])`; `r(await y9.adminAllInvoices(e))`, then `.filter`/`.length` |
  | `admin-stages` | `.then(e=>n(e.sort((a,b)=>a.order-b.order)))` and `e.filter(e=>e.is_active)` |
  | `admin-users` | `useState([])`; `n.map(n=>…n.stage_ids…)` |
  | `admin-lookups` | `useState([])`; `r.length` used as the next `sort_order` |

  `admin-tracker-users` is the weakest of the eight — `useState([])` then a bare
  `.then(n)` — but its table maps over the state.
- **how confident should we be, plainly**: high on array-vs-object; the client
  would be visibly broken otherwise. But that argument rests on an assumption
  nobody in this rescrape can test: **that the tracker pages work for someone.**
  No credential we can reach has tracker access, so "the app would be broken" is
  unfalsifiable from here. If the tracker module were half-abandoned and its pages
  broken for everyone, the inference collapses.
- **what would falsify it**: one live payload from a tracker-enabled account —
  `curl` any of the 15 with a token holding `stage_ids`, or a
  `tracker_admin`-role login. That single call settles all 15 at once. Nothing
  short of it will.
- **impact if the study were wrong**: a CLI that JSON-decodes an array as an object
  (or the reverse) errors on every successful call — the failure lands on the
  first tracker-enabled operator, not on us. The one that would bite hardest is
  `all-invoices-export`: the shipped spec's `type: object` would make a command
  try to JSON-decode an XLSX blob. The study is right to flip it; note it is an
  inference from `responseType:'blob'` + the `.xlsx` filename, not a measured
  `Content-Type`.

---

## Claim 4 — the account study's auth boundary

### "`GET /api/auth/users/{id}/parties/` also returns 200 with no token" and the study's per-endpoint 401 labels

- **verdict**: **CONFIRMED in both directions**, 18/18 endpoints matching the
  study's labels — **plus a third unauthenticated endpoint the study missed.**
- **evidence**: full sweep with **no `Authorization` header**:

  ```
  200  auth/categories/            200  auth/users/list/          (68066 B)
  200  auth/companies/             200  auth/users/3/parties/     (2815 B)
  200  auth/roles/                 200  auth/users/21/parties/    (5681 B)
  200  auth/states/                200  auth/users/3/       <-- NOT IN THE STUDY
  200  auth/mainGroup/

  401  auth/profile/               401  admin/devices/
  401  auth/users/3/page-permissions/   401  admin/devices/analytics/
  401  auth/parties/CUSTA000593/products/  401  admin/devices/11/
  401  devices/me/                 401  ui-config/labels/
                                   401  ui-config/admin/labels/
  ```

  The `{id}/parties/` claim holds, and holds on **two** users, not the one the
  study verified. Every endpoint the study marked as requiring auth does require
  it — no false positives, no false negatives.
- **the new finding — a third open endpoint**: `GET /api/auth/users/{id}/`
  returns **200 with no token**, and its 23-field payload includes
  `password: "pbkdf2_sha256$1000000$…"`. The study excluded this path entirely as
  "write verb (PUT)" and therefore never tested it. It is the same leak as
  `users/list/`, addressable one user at a time, and it is **not** in the study's
  security write-up. The remediation list in the study ("put `users/list` and
  `users/{id}/parties` behind authentication") is therefore incomplete —
  `users/{id}` must be on it.
- **a fourth exposure, worse in kind**: `DEBUG = True` leaks to anonymous callers.
  With no token at all:
  - any 404 returns the **complete URLconf** for the matched app;
  - `GET /api/auth/parties/CUSTA000593/users/` returns a **116 KB technical-500
    page** with 11 frames of local variables and a 227-row settings dump.
    Django redacts `SECRET_KEY`/`*PASSWORD*`, and no password hashes appear in
    that page, but these do: `DEBUG: True`, `ALLOWED_HOSTS: ['103.89.45.75',
    '127.0.0.1', '10.0.2.2', 'localhost', '192.168.1.240', '*']`,
    `CORS_ALLOW_ALL_ORIGINS: True`, and the app database at
    `postgresql://postgres@20.20.45.75:5432/order_management`.

  API-FACTS §3 recorded `DEBUG` as an inference from one authenticated traceback on
  `/api/sku/pending/`. It is broader than that: it is unauthenticated, and it is on
  every route.
- **impact if the study were wrong**: in the "too strict" direction, commands
  demanding a token that is not needed — harmless. In the "too loose" direction, a
  published security finding that does not reproduce, aimed at the OMS team. It
  reproduces, and it is larger than reported.

---

## Claim 5 — `category` silently ignored on `users/{id}/parties/`

### "The `category` filter does not work on this endpoint… asking for BEVERAGES or MART returns the same 15 OIL rows. Confidence: high"

- **verdict**: **CONFIRMED**, by byte-identical MD5 rather than by row count.
- **evidence**:

  ```
  users/3/parties/                            md5=3a067ee5…  2815 B  total=15
  users/3/parties/?category=OIL               md5=3a067ee5…  2815 B  total=15
  users/3/parties/?category=BEVERAGES         md5=3a067ee5…  2815 B  total=15
  users/3/parties/?category=MART              md5=3a067ee5…  2815 B  total=15
  users/3/parties/?category=NONSENSE_VALUE_X  md5=3a067ee5…  2815 B  total=15
  ```

  Five query strings, one identical response body. The param is not merely
  ignored — it is **not validated either**, so a garbage value is as accepted as a
  real one.

  Control, same param name, sibling endpoint:

  ```
  CUSTA001139/products/                            md5=7430b510…  3677 B  total=13
  CUSTA001139/products/?category=OIL               md5=093f8dcd…   412 B  total=1
  CUSTA001139/products/?category=BEVERAGES         md5=03351aab…  3432 B  total=12
  CUSTA001139/products/?category=MART              md5=addee0be…   168 B  total=0
  CUSTA001139/products/?category=NONSENSE_VALUE_X  md5=addee0be…   168 B  total=0
  ```

  The control varies correctly on `OIL` and `BEVERAGES`, which is decisive. One
  small caveat the study did not note: on the control, `MART` and a nonsense value
  return **identical bytes**, so that endpoint's validation is also loose — it
  just happens to filter correctly on values that match rows.
- **impact if the study were wrong**: a `--category` flag on `account user-parties`
  that appears to work and silently returns unfiltered data. The study's
  recommendation — document it as ignored, or omit it — is correct. Omitting it is
  safer; a documented-but-dead flag still gets used.

---

## Claim 6 — the publish / exclude verdicts

### 6a. Dual-verb paths: "the GET must survive and the write must not"

- **verdict**: **CONFIRMED**.
- **evidence**: authenticated GETs on both flagged paths return 200 and real data:

  ```
  GET auth/users/3/page-permissions/   -> 200 {"success":true,"data":{"user_id":3,"extra_pages":[]}}
  GET auth/users/21/page-permissions/  -> 200 {"…","extra_pages":["Party_Product_Assignment","Party_Assignment","Add_Scheme","Sap_Sync"]}
  GET ui-config/admin/labels/          -> 200 {"success":true,"message":"UI labels fetched.","data":[{"id":1,"field_key":"price_list",…}]}
  GET ui-config/labels/                -> 200 {"price_list":"Price List"}
  ```

  The bundle confirms both write verbs exist on the same URLs
  (`Y.put('/auth/users/'+e+'/page-permissions/',{extra_pages:t})` at 806535). Both
  studies key their exclusions on **path + verb** and both say so explicitly. The
  tracker study's five dual-verb rows are likewise correct against the URLconf.
- Neither study renamed anything. All 14 shipped tracker command names and all 10
  shipped account command names are preserved verbatim; the 6 new names
  (`tracker invoice-jsap`, `account devices|device|device-analytics|
  ui-label-config|ui-labels`) follow the shipped house style.

### 6b. "`/api/auth/users/{id}/` (PUT) — verdict: exclude — write verb"

- **verdict**: **REFUTED.** *This claim is wrong. It does not mean delete anything
  — it means a working read was silently dropped.*
- **evidence**: the server routes this path as `[name='user-detail']`, and:

  ```
  GET /api/auth/users/3/   -> 200, 785 B, {"success":true,"data":{id,name,username,…23 fields}}
  GET /api/auth/users/62/  -> 200, 3988 B
  ```

  It is a **dual-verb path** — GET retrieves one user, PUT edits them — of exactly
  the class the study correctly identified twice elsewhere. Here it saw only the
  SPA's `updateUser` (`Y.put('/auth/users/'+e+'/')`, bundle @806400) and excluded
  the whole path. The SPA never GETs it, so the call-site harvest could not see it.
- **impact**: a **silent regression** — one working read (`account user`, the
  single-user detail that `account users` currently forces a 68 KB full-table
  fetch to answer) never reaches the CLI. And because it was never tested, its
  unauthenticated password-hash leak went unreported. Both consequences flow from
  the same mistake.

### 6c. The account study's denominator

- **verdict**: **REFUTED — the study is incomplete.** *Again: not "delete
  something", but "five routed paths were never seen."*
- **evidence**: the server's URLconf for the three apps this study covers lists
  **34** routes (auth 25, devices + admin/devices 6, ui-config 3). The study covers
  **29**. The five it never mentions:

  | routed path | Django url name | what I measured | class |
  |---|---|---|---|
  | `auth/parties/<str:card_code>/users/` | `party-users` | **500** `TypeError: Object of type UserRole is not JSON serializable when serializing dict item 'role' … 'users' … 'data'` — on both card codes tried | missed **read**, proven dead |
  | `devices/me/` | `device-me` | **200** `{"success":true,"message":"Devices retrieved","data":[]}`; 401 unauthenticated | missed **read**, working |
  | `auth/party-product/add/` | `add-product-to-party` | not probed (write) | missed **write** — absent from the denylist |
  | `auth/users/<int:user_id>/delete/` | `delete-user` | not probed (write) | missed **write** — absent from the denylist |
  | `devices/update/` | `device-update` | not probed (write) | missed **write** — absent from the denylist |

  None of the five appears anywhere in the bundle (`str.find` returns nothing for
  `devices/me`, `devices/update`, `party-product/add`, `/delete/`, or the
  `parties/{cc}/users/` template). **They are routed but never called by the SPA**,
  which is precisely why a call-site harvest cannot see them, and why API-FACTS §5
  is also missing all three writes.

  `auth/parties/{card_code}/users/` is the reverse of `account user-parties` —
  "which salespeople own this customer". It is a genuinely useful read and it is
  100% broken in production: the view builds `data.users[].role` and hands Django
  a `UserRole` model instance instead of a string. Verdict for it should be
  **exclude — proven dead**, with the traceback recorded for the OMS team.

  `devices/me/` returns `[]` for `paramjot`, who has 0 rows in the device registry
  (`admin/devices/?search=paramjot` → `total: 0`), so "the caller's own devices" is
  consistent — but I never saw a non-empty payload, so the shape beyond the
  envelope is **UNVERIFIED**. Confidence on the semantics: medium-high.
- **impact**: two reads missing from the CLI (one of which should be excluded as
  dead, with a reason), and — the part that matters for RULE 0 — **three write
  paths that no denylist in this rescrape currently names.** If the assembler's
  safety model is "deny everything in `excluded[]`", these three are outside it.
  `auth/users/{id}/delete/` in particular deletes an OMS login.

---

## Claim 7 — state codes and the duplicate channel

### "JIVO's state codes are NOT ISO — Bihar `BH`, Kerala `KR`, Goa `GO`, Telangana `TE`"

- **verdict**: **CONFIRMED in direction, REFUTED as an enumeration.** *The rule is
  right; the list of exceptions is incomplete, and this is going into operator
  docs.*
- **evidence**: live `GET /api/auth/states/`, 27 rows, compared against ISO
  3166-2:IN:

  | JIVO | ISO | state | in the study? |
  |---|---|---|---|
  | `KR` | `KL` | Kerala | yes |
  | `GO` | `GA` | Goa | yes |
  | `BH` | `BR` | Bihar | yes |
  | `TE` | `TG` | Telangana | yes (study wrote ISO `TS`; ISO is `TG`, `TS` is the informal form) |
  | `UK` | `UT` | Uttarakhand | **no** |
  | `OD` | `OR` | Odisha | **no** |
  | `DB` | `DH` | Dadra & Nagar Haveli and Daman & Diu | **no** |

  Two the study did *not* claim, and which a careless reader might assume are also
  wrong, in fact **match** ISO: Andhra Pradesh `AP` and Chhattisgarh `CT`.
  Confirmed independently: ids 18, 19, 20 are absent (range 1–30, 27 rows), and the
  list is sorted alphabetically by name, both as the study says.
- **calibration**: my ISO codes are from memory, not a fetched authority. High
  confidence on `KL`, `GA`, `BR`, `TG`, `UT`, `OR`; **medium** on `DH` for the
  merged UT. Anyone publishing the table should check `DH` against a source.
- **impact**: the study's stated purpose for this trap is "joining to a GST state
  code table on `code` will silently drop rows". An operator who reads the
  four-item list will conclude Uttarakhand and Odisha are safe to join on. They are
  not. **Six or seven exceptions, not four** — or better, state the rule without
  the enumeration: *no* JIVO state code should be assumed ISO.

### "`CALL CENTER` (8) and `CALL CENTRE` (28) are the same channel entered twice"

- **verdict**: **CONFIRMED.**
- **evidence**: live `GET /api/auth/mainGroup/` returns both
  `{"id":8,"name":"CALL CENTER"}` and `{"id":28,"name":"CALL CENTRE"}`. After
  normalising `CENTRE`→`CENTER`, `CALL CENTER` is the only duplicated name in the
  27-row master. Id 27 is absent (range 1–28, 27 rows), as the study says.
- **impact if wrong**: an operator-facing claim of a master-data defect that the
  OMS team would bounce. It is real.

---

## Claim 8 — the wrongly-credited params

### CORRECTION-params: "If your study asserted any param in the 'was wrongly credited' column, drop it"

- **verdict**: **CONFIRMED — both studies are clean.**
- **evidence**: the tracker study drops `stage` from `my-queue` and says why. I
  verified the correction itself against the bundle rather than taking it on
  trust — the two methods are genuinely adjacent and `myQueue()` genuinely takes
  no argument:

  ```js
  async myQueue(){ let{data:e}=await Y.get(`/tracker/my-queue/`); return e },
  async getStageAdvanced(e){ let{data:t}=await Y.get(`/tracker/stage-advanced/`,{params:{stage:e}}); return t },
  ```

  The other five wrongly-credited params (`mode` on `orders/status`, `category` on
  `sap/addresses`, `flow_type` on `orders/staff-products`, `order_ids` on
  `orders/{id}/orderlogs`, `category` on `sap/parties`) fall in neither study's
  domain; neither study asserts any of them. Each study's remaining `mode`
  references are to `orders/status-tracking/`, where `mode` genuinely belongs.
- **impact if wrong**: a CLI flag the app never sends, silently ignored — the
  `category`-on-`user-parties` failure mode, deliberately reintroduced.

---

## Summary table

| # | claim | verdict |
|---|---|---|
| 1 | tracker 403s are a permission wall, not death | CONFIRMED (bogus paths 404; URLconf proves all 22 exist) |
| 2 | tracker shapes read correctly out of the bundle | CONFIRMED (13/13 spot-checks) |
| 3 | shipped `response: object` is wrong for 9 of 14 tracker endpoints | CONFIRMED, falsifiable only by one tracker-enabled payload |
| 4 | account auth boundary as reported | CONFIRMED + a third open endpoint the study missed |
| 5 | `category` silently ignored on `users/{id}/parties/` | CONFIRMED (byte-identical, 5 query strings) |
| 6a | dual-verb GETs survive, writes excluded | CONFIRMED |
| 6b | `auth/users/{id}` is write-only | **REFUTED** — GET works; a read was dropped |
| 6c | the account study covers its domain | **REFUTED** — 29 of 34 routed paths; 2 reads + 3 writes missed |
| 7 | state codes are not ISO / `CALL CENTER` duplicate | CONFIRMED in direction; enumeration incomplete (6–7, not 4) |
| 8 | wrongly-credited params dropped | CONFIRMED |

## What would ship broken, in priority order

1. **Three write paths outside every denylist** — `auth/party-product/add/`,
   `auth/users/{id}/delete/`, `devices/update/`. Add them to `excluded[]` and to
   API-FACTS §5 before the assembler runs.
2. **`account user` (`GET /api/auth/users/{id}/`) missing** — a working read
   excluded on a wrong verb assumption.
3. **`devices/me/` missing**; **`auth/parties/{cc}/users/` missing** and should be
   recorded as `exclude — proven dead` with its 500 traceback.
4. **The state-code trap is under-enumerated** — publish the rule, not the
   four-item list.
5. **Two security findings are under-reported to the OMS team**: the password-hash
   leak also reaches `GET /api/auth/users/{id}/` unauthenticated, and `DEBUG=True`
   exposes the full URLconf on any 404 and a settings-plus-locals dump on any 500,
   to anonymous callers.
6. **The harvest method has a structural blind spot** — it can only see what the
   SPA calls. The Django technical-404 page hands out the exact route list for
   free, unauthenticated, per app. Every other domain in this rescrape should be
   diffed against it before the spec is emitted.
