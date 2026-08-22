# Adversarial refutation — `oms/probe/verdicts.json`

Run: 2026-08-22, read-only. Every request below was a **GET** against
`https://oms.jivo.in` with the session bearer. No parameter value was invented:
every value used is either observed in a prior response or a literal in the app's
own JS bundle. Probe harness: `oms/refute/probe26.py` (GET-only by construction).

**Token status:** valid (`GET /api/orders/dashboard/` → 200).

## Control: what a genuinely dead path looks like on this server

```
$ GET /api/          # the bundle's own baseURL literal (Ea = `https://oms.jivo.in/api`)
404  text/html; charset=utf-8  5887 b
'<!DOCTYPE html>...<title>Page not found at /api/</title>...'
```

So on this Django box **unrouted → HTML 404**. Any `application/json` reply — 200,
400, 403, 405 — means the URL resolved and a view ran. This is the yardstick used
throughout.

---

## Claim 1 — "diff.json's 26 GONE commands are FALSE; every one is still live"

**Verdict: CONFIRMED — and now on 26/26, not a 6-endpoint spot-check.**

The prior file tested 6. I tested all 26. Every single one is routed: 18 returned
`200`, 8 returned an application-level `400 {"error": "<param> is required"}`.
Zero HTML 404s. Nothing has been removed from OMS; no shipped command should be
dropped.

Command:
```
python3 /root/.handoff-runs/rescrape-all/scratch/oms/refute/probe26.py < gone25.txt
# plus /api/admin/devices/353/ using an id observed in /api/admin/devices/
```

### Full 26-endpoint alive/dead table

| # | shipped cmd | path | GET status | verdict | evidence (trimmed body) |
|---|---|---|---|---|---|
| 1 | `account my-devices` | `/api/devices/me/` | 200 (609 b) | ALIVE (200) | `{"success":true,"message":"Devices retrieved","data":[{"device_id":"5364643f-6740-4884-9efe-4c49` |
| 2 | `account devices` | `/api/admin/devices/` | 200 (17159 b) | ALIVE (200) | `{"success":true,"message":"Devices retrieved","data":{"results":[{"id":353,"device_id":"41b23718` |
| 3 | `account device-analytics` | `/api/admin/devices/analytics/` | 200 (2295 b) | ALIVE (200) | `{"success":true,"message":"Analytics retrieved","data":{"cards":{"total_devices":375,"active_dev` |
| 4 | `account device` | `/api/admin/devices/353/` | 200 (728 b) | ALIVE (200) | `{"success":true,..."Device retrieved"...}` |
| 5 | `orders dashboard` | `/api/orders/dashboard/` | 200 (438 b) | ALIVE (200) | `{"total_orders":2468,"total_revenue":"14739181184.38","today_orders":14,"this_month_orders":345,` |
| 6 | `orders dashboard-charts` | `/api/orders/dashboard/charts/` | 200 (265261 b) | ALIVE (200) | `{"filter":{"year":2026,"month":0,"line_year":2026},"monthly_sales":[{"month":"2026-01","label":"` |
| 7 | `orders product-filters` | `/api/orders/product-filters/` | 200 (55 b) | ALIVE (200) | `{"categories":[],"brands":[],"varieties":[],"types":[]}` |
| 8 | `orders template-parties` | `/api/orders/templates/parties/` | 200 (2 b) | ALIVE (200) | `[]` |
| 9 | `orders template-orders` | `/api/orders/templates/orders/` | 400 (33 b) | ALIVE (400 needs param) | `{"error":"card_code is required"}` |
| 10 | `orders by-item` | `/api/orders/orders-by-item/` | 400 (33 b) | ALIVE (400 needs param) | `{"error":"item_code is required"}` |
| 11 | `sap sync-status` | `/api/sap/status/` | 200 (374 b) | ALIVE (200) | `{"success":true,"data":{"counts":{"products":4169,"parties":3381,"addresses":36582,"branches":22` |
| 12 | `sap schedules` | `/api/sap/schedules/` | 200 (26 b) | ALIVE (200) | `{"success":true,"data":[]}` |
| 13 | `hana series` | `/api/hana/series/` | 400 (64 b) | ALIVE (400 needs param) | `{"error":"branch is required and must be one of: OIL, BEVERAGE"}` |
| 14 | `hana warehouse-details` | `/api/hana/warehouse-details/` | 400 (64 b) | ALIVE (400 needs param) | `{"error":"branch is required and must be one of: OIL, BEVERAGE"}` |
| 15 | `hana vendor-states` | `/api/hana/vendor-states/` | 400 (64 b) | ALIVE (400 needs param) | `{"error":"branch is required and must be one of: OIL, BEVERAGE"}` |
| 16 | `hana state-chain` | `/api/hana/state-chain/` | 400 (64 b) | ALIVE (400 needs param) | `{"error":"branch is required and must be one of: OIL, BEVERAGE"}` |
| 17 | `hana invoice-drafts` | `/api/hana/invoice-drafts/` | 400 (64 b) | ALIVE (400 needs param) | `{"error":"branch is required and must be one of: OIL, BEVERAGE"}` |
| 18 | `invoices all` | `/api/invoice/all/` | 400 (51 b) | ALIVE (400 needs param) | `{"error":"Warehouse Code is a required parameter."}` |
| 19 | `invoices crystal` | `/api/invoice/crystal/` | 400 (30 b) | ALIVE (400 needs param) | `{"error":"docNum is required"}` |
| 20 | `einvoice health` | `/api/einvoice/health/` | 200 (174 b) | ALIVE (200) | `{"ok":true,"missing_credentials":[],"public_key_found":true,"public_key_path":"./secrets/Product` |
| 21 | `einvoice companies` | `/api/einvoice/companies/` | 200 (195 b) | ALIVE (200) | `{"results":[{"label":"OIL","company_db":"JIVO_OIL_HANADB"},{"label":"BEVERAGE","company_db":"JIV` |
| 22 | `einvoice invoices` | `/api/einvoice/invoices/` | 200 (4989 b) | ALIVE (200) | `{"company_db":"JIVO_OIL_HANADB","results":[{"docentry":78862,"docnum":626000001,"cardname":"HARP` |
| 23 | `einvoice logs` | `/api/einvoice/logs/` | 200 (26175 b) | ALIVE (200) | `{"count":59,"totals":{"SUCCESS":47,"FAILED":12,"SKIPPED":0},"results":[{"id":59,"docentry":10001` |
| 24 | `legal uoms` | `/api/legal/uom/` | 200 (2 b) | ALIVE (200) | `[]` |
| 25 | `legal nutrition` | `/api/legal/nutrition/` | 200 (2 b) | ALIVE (200) | `[]` |
| 26 | `legal item-nutrition` | `/api/legal/item-nutrition/` | 200 (24 b) | ALIVE (200) | `{"nutritional_facts":[]}` |

**Truly dead: 0 of 26.** Needs-a-param: 8 (#9, #10, #13–#19). Live-200: 18.

### Why the harvester lost them (root cause, confirmed)

Two independent bugs in `harvest/harvest_oms.py`, both of which also cost real
new endpoints (see Claim 3):

1. **Relative paths with no leading slash.** The whole e-invoice family is called
   as `Y.get(\`einvoice/health/\`)` — no `/`. Both of the harvester's scanners
   (`s.find('`/')` and the `["'](/[a-z]...` regex) require a leading `/`, so every
   `einvoice/…` and `ewaybill/…` call site was invisible. That alone explains
   rows #20–#23.
2. **Prefix list too short.** `API_PREFIXES` omits `/invoice`, `/legal`, `/sku`,
   `/devices`, `/admin`, `/service-layer`. Those paths only survived when the
   literal happened to carry `/api` inline. That explains #1–#4, #18, #19, #24–#26.
3. **Prefix *variables*** (the EXIM-sibling bug) is present too but benign here:
   `var T7=\`/legal/item/\`, E7=\`/legal/uom/\`, D7=\`/legal/nutrition/\`,
   xhe=\`/legal/item-nutrition/\`` and calls like ``Y.patch(`${T7}${e}/`)``.
   All resolve to already-shipped paths (the `${VAR}${id}/` forms are PATCH/DELETE).
4. `/api/orders/dashboard/` etc. were missed for reason 2's sibling: the harvester
   *did* see `/orders/...` literals, but the diff keyed on a normalisation that
   dropped them. Regardless — live, see #5/#6.

---

## Claim 2 — "34 of the 44 new paths are WRITES"

**Verdict: REFUTED on the arithmetic (minor), CONFIRMED on the substance.**

Recount of `harvest/diff.json` `new` (n=44) by resolved verb:

| bucket | n |
|---|---|
| pure write verb at the axios call site (POST/PUT/PATCH/DELETE) | 29 |
| no verb resolved by the harvester | 11 |
| GET | 4 |

Resolving the 11 verbless ones from the bundle's own fetch wrappers
(`I6 = (e,t) => Y.request({url, method: t?.method || \`GET\`, ...})`,
`L6 = (e,t,n=\`POST\`) => multipart`, `lpe = DELETE`):

```
/api/invoice/pending/            I6(...,{method:`POST`})           WRITE
/api/invoice/{}/update-status/   I6(...,{method:`PATCH`})          WRITE
/api/invoice/{}/delete/          I6(...,{method:`DELETE`})         WRITE
/api/invoice/credit-limit/request/  L6(...) multipart              WRITE
/api/legal/upload/               N6() url + L6(ohe,t,`POST`)       WRITE
/api/sku/upload/                 N6() url + L6(ume,r,`POST`)       WRITE
/api/service-layer/invoice/      R6(...) url + I6(r,{method:`POST`}) WRITE
/api/auth/refresh/               Ta.post(`${Ea}/auth/refresh/`)    token exchange
/api/invoice/reserved-batches/   I6(`...`)  → default GET          READ
/api/invoice/used-sales-orders/  I6(`...`)  → default GET          READ
/api/einvoice/irn/{}/qr.png      `qrImageUrl:e=>` → <img src>      READ (GET)
```

True split of the 44: **36 writes, 1 token exchange, 7 reads** — not 34/6.
The verdicts file's own list of 6 reads silently omits `qr.png`, which it
excluded on a premise that is itself false (Claim 6).

**GET/POST-pair hunt (the specific attack asked for): nothing lost.** I re-extracted
every `Y.<verb>(\`…\`)` call site with a real template-literal parser (handles
nested `${}`) and cross-checked all 29 write-bucketed paths for a GET call site
elsewhere in the bundle. **0 matches.** The harvester *does* union verbs per path
(`["DELETE","PATCH"]`, `["DELETE","POST"]` appear), so a same-literal GET/POST pair
would have shown up. The only real GET/POST pairs in the app are
`/api/einvoice/irn/from-invoice/{}/` and `/api/ewaybill/from-invoice/{}/` —
and both were missed *entirely*, not mis-bucketed (Claim 3).

---

## Claim 3 — "the genuinely new READ surface is 6 endpoints, 4 callable"

**Verdict: REFUTED. The new read surface is 19 paths, 13 of them proven live-200 on
this credential.** The harvest never saw the e-invoice / e-way-bill API family.

Full inventory:
* **7 reads inside the harvest's own 44** — the file's 6, plus `qr.png` (see Claim 6).
* **12 GET paths the harvest never recorded at all** — listed below.
* 4 + 9 = **13 proven live-200** (vs the file's claim of 4).

Method: parsed every `Y.get|post|put|patch|delete(\`…\`)` and every `I6/N6/L6/R6`
call site in `bundle/index-5JVFWPwg.js`, normalised, and diffed against
`harvest/harvest.json` ∪ the 106 shipped `pp:path` values.

Result: **39 literal axios paths the harvest never recorded, 23 of them GET.**
Stripping the 11 already shipped in the CLI (`/admin/devices/` ×3, `/auth/mainGroup/`,
`/einvoice/{health,companies,invoices,logs}/`, `/orders/dashboardW/*` ×3), **12 are
genuinely new READ paths**, none of which appear anywhere in `verdicts.json`. The
table below lists 11 of them plus `qr.png` (which the harvest *did* see, inside the
44, but which the verdicts file wrongly excluded); the 12th missed path,
`/api/einvoice/gstin/{gstin}/sync/`, is called out separately underneath:

| path | verb evidence (bundle) | live status |
|---|---|---|
| `/api/einvoice/heartbeat/` | ``Y.get(`einvoice/heartbeat/`)`` | **200** `{"status_code":200,"text":"e-Invoice Vital:-22-08-2026 14:58:30"}` |
| `/api/einvoice/irn/{irn}/` | ``getByIrn:async e=>Y.get(`einvoice/irn/${e}/`)`` | **200** (NIC replies `2283 IRN details cannot be provided as it is generated more than 2 days prior`) |
| `/api/einvoice/irn/by-doc/` | ``Y.get(`einvoice/irn/by-doc/`,{params:{doctype,docnum,docdate}})`` | **400** bare → `{"error":"Missing query params: doctype, docnum, docdate"}`; **200** with observed values |
| `/api/einvoice/irn/rejected/` | ``Y.get(`einvoice/irn/rejected/`,{params:{date:e}})`` | **400** bare → `{"error":"Query param 'date' (dd/mm/yyyy) is required."}`; **200** with `date=13/08/2026` |
| `/api/einvoice/irn/from-invoice/{docentry}/` | ``previewFromInvoice … Y.get(`einvoice/irn/from-invoice/${e}/`,{params:r})``, `r` = `{company_db, id_type}` | **200**, 1402 b — full NIC invoice payload preview |
| `/api/einvoice/gstin/{gstin}/` | ``getGstin:async e=>Y.get(`einvoice/gstin/${e}/`)`` | **200** `{"Gstin":"06AACCJ4223F1Z0","TradeName":"JIVO WELLNESS PVT. LTD.",…}` |
| `/api/einvoice/ewb/{irn}/` | ``getByIrn:async e=>Y.get(`einvoice/ewb/${e}/`)`` | **200** (NIC `4005 Eway Bill details are not found`) |
| `/api/einvoice/irn/{irn}/qr.png` | ``qrImageUrl:e=>`/api/einvoice/irn/${e}/qr.png` `` | **200 image/png, 5223 b** — a real QR |
| `/api/ewaybill/from-invoice/{docentry}/` | ``previewFromInvoice … Y.get(`ewaybill/from-invoice/${e}/`,{params:n})``, `n` = `{company_db, mode}` | **200**, 436 b `{"docentry":10001,…,"mode":"ewb_by_irn","irn":…}` |
| `/api/ewaybill/gstin/{gstin}/` | ``gstinDetails:async e=>Y.get(`ewaybill/gstin/${e}/`)`` | **502** — `{"error":"All e-Way Bill hosts unreachable: ['https://api.ewaybillgst.gov.in/v1.03']"}` → view ran, upstream NIC down |
| `/api/ewaybill/{ewbNo}/` | ``getByNumber:async e=>Y.get(`ewaybill/${e}/`)`` | UNTESTED — no EWB number observed in any readable response |
| `/api/ewaybill/transporter/{id}/` | ``transporterDetails:async e=>Y.get(`ewaybill/transporter/${e}/`)`` | UNTESTED — no transporter id observed |

Plus one **deliberately not called**: `/api/einvoice/gstin/{gstin}/sync/`
(``syncGstin:async e=>Y.get(`einvoice/gstin/${e}/sync/`)``). It is a GET, but the
name is a sync trigger — EXCLUDED under the owner's read-only rule, untested.

Observed values used (all from real responses): IRN
`0000aaaa1111…7777bbbb`, `docentry=10001`, `company_db=JIVO_BEVERAGES_HANADB`,
`doc_no=626000002`, `docdate=13/08/2026`, GSTIN `06AACCJ4223F1Z0` — the first four
from `GET /api/einvoice/logs/`, the last two from
`GET /api/einvoice/irn/from-invoice/10001/?company_db=JIVO_BEVERAGES_HANADB`.

New **write** paths the harvest also missed (never call): `/api/devices/register/`,
`/api/einvoice/{token,irn,irn/validate,irn/cancel,logs/retry,qr}/`,
`/api/ewaybill/{token,generate,cancel,close,reject,update-part-b,extend-validity,update-transporter}/`,
POST halves of both `from-invoice/{}` routes, and `${T7|E7|D7}${id}/` PATCH/DELETE.

**Broad sweep for other missed prefixes:** I also scanned every string and template
literal in all `bundle/*.js` for API-path-shaped tokens regardless of prefix or
verb proximity. 88 candidates, all noise (exceljs MIME types, `xl/*.xml` OOXML part
names, npm module ids). No raw `fetch()` API calls exist — the only `fetch(` in the
bundle is `fetch(e.href, …)` inside a vendored polyfill. So the missed surface is
exactly the relative-path e-invoice/e-way-bill family plus the short prefix list.

---

## Claim 4 — parameters

### 4a. `branch` enum is `BEVERAGE` (singular) — **CONFIRMED**, with a twist

```
GET /api/hana/inventory-report/?branch=OIL        → 200  46312 b
GET /api/hana/inventory-report/?branch=BEVERAGE   → 200  16634 b
GET /api/hana/inventory-report/?branch=BEVERAGES  → 400  {"error":"branch is required and must be one of: OIL, BEVERAGE"}
GET /api/hana/pending-dispatch/?branch=BEVERAGES  → 400  same
```

Singular confirmed for every Django-side endpoint. **But the plural does exist in
this app** — the bundle carries both mappings side by side:

```js
z6 = e => String(e||``).trim().toUpperCase()===`BEVERAGE` ? `BEVERAGE` : `OIL`
dpe = e => z6(e)===`BEVERAGE` ? `BEVERAGES` : `OIL`     // plural!
R6 = (e,t) => `${e}${e.includes(`?`)?`&`:`?`}branch=${encodeURIComponent(t)}`
B6 = `OIL`;  V6 = e => R6(e, B6)                        // hardcodes branch=OIL
```

`dpe` (plural `BEVERAGES`) is used for exactly one path — `R6('/api/service-layer/invoice/', dpe(branch))`,
a POST. So: **singular for every read; plural only on the SAP service-layer write.**
Do not generalise either way.

### 4b. `/api/hana/inventory-report/` — **CONFIRMED**

Call site: ``getInventoryReport:async(e,t)=>(await Y.get(`/hana/inventory-report/`,{params:{branch:e,...t?.length?{warehouses:t.join(`,`)}:{}}})).data``

```
GET /api/hana/inventory-report/?branch=OIL&warehouses=BH-BT        → 200 21434 b (1 warehouse echoed)
GET /api/hana/inventory-report/?branch=OIL&warehouses=BH-BT,BH-PF  → 200 24611 b (2 warehouses echoed)
```
`warehouses` = comma-joined codes, optional, genuinely filters. Codes observed in
the endpoint's own `warehouses[]` block.

### 4c. `/api/hana/pending-dispatch/` — **CONFIRMED, with a live caveat the file missed**

Call site: ``{params:{branch:e,...t?.from?{from_date:t.from}:{},...t?.to?{to_date:t.to}:{}}}``

```
GET /api/hana/pending-dispatch/?branch=OIL                                   → 200 280845 b  75 orders / 248 lines / 63 invoices
GET /api/hana/pending-dispatch/?branch=OIL&from_date=2026-05-28&to_date=2026-05-28 → 200 34129 b  15 orders / 34 lines
GET /api/hana/pending-dispatch/?branch=BEVERAGE                              → 502
   {"error":"Unable to fetch pending sales orders from HANA.",
    "detail":"HANA query failed: (260, 'invalid column name: T0.U_OMS_REF: …"}
```
Dates are `yyyy-mm-dd` and filter correctly. **`branch=BEVERAGE` is server-side
broken today** (bad column in the HANA SQL). The verdicts file asserts
`branch: OIL|BEVERAGE` with no caveat — a CLI flag that advertises BEVERAGE will
hand the user a 502.

### 4d. `/api/invoice/used-sales-orders/` `card_code` — **REFUTED**

The real call site carries **two** params, and the file names the wrong one:

```js
I6(`/api/invoice/used-sales-orders/?card_code=${encodeURIComponent(e.CardCode)}&branch=${encodeURIComponent(n||``)}`)
```

```
GET /api/invoice/used-sales-orders/                             → 200 7626 b  card_code:""
GET /api/invoice/used-sales-orders/?card_code=CUSTA000496       → 200 7637 b  card_code echoed, SAME rows (+11 b = the echo)
GET /api/invoice/used-sales-orders/?card_code=CUSTA000496&branch=OIL → 200 4036 b  DIFFERENT, smaller row set
GET /api/invoice/used-sales-orders/?branch=BEVERAGE             → 200 3652 b  the complement (4036 + 3652 ≈ 7626 + echo)
```

**`card_code` is decorative** — echoed in the response, does not filter.
**`branch` is the real filter** and the verdicts file does not mention it at all.

### 4e. `/api/invoice/reserved-batches/` `"params": {}` — **REFUTED**

```js
I6(`/api/invoice/reserved-batches/?branch=${encodeURIComponent(n)}`)
```
```
GET /api/invoice/reserved-batches/                 → 200 274 b  2 rows (both ERROR)
GET /api/invoice/reserved-batches/?branch=OIL      → 200 274 b  2 rows
GET /api/invoice/reserved-batches/?branch=BEVERAGE → 200  36 b  {"success":true,"data":[],"total":0}
```
It takes `branch` and it filters. The file records no params.

---

## Claim 5 — "403 proves `/api/tracker/stage-decisions/` and `stage-export/` exist"

**Verdict: the "exists/routed" half is CONFIRMED. The verb corroboration is REFUTED.**

Direct test of the exact question asked — a route the bundle proves is **POST-only**,
hit with GET:

```js
async bulkAction(e){ let{data:t} = await Y.post(`/tracker/actions/bulk/`, e); return t }
```
```
GET /api/tracker/actions/bulk/     → 403 {"detail":"You do not have access to this tracker page."}
```

Identical body to the two "proven routed" endpoints. Django/DRF runs
`initial()` (permissions) **before** method dispatch, so the tracker page-permission
gate short-circuits every verb. The 403 is verb-agnostic: it would look exactly the
same on a POST-only, PUT-only or GET route.

The whole tracker family is gated for this credential:

```
403 "You do not have access to this tracker page."      my-queue, invoices, reports, alerts,
                                                        lookups, vendors, stage-advanced,
                                                        stage-decisions, stage-export, actions/bulk
403 "Tracker administration is restricted to tracker admins."  all-invoices, admin/stages,
                                                               admin/users, admin/tracker-users
```

So: 403 ≠ HTML 404, therefore both paths **are routed** (that part stands). But the
only evidence that they are GET is the bundle source — which, to be fair, is clear:

```js
async getStageDecisions(e,t,n=!1){ let{data:r} = await Y.get(`/tracker/stage-decisions/`,
   {params:{stage:e, ...t?{decision:t}:{}, ...n?{include_resolved:1}:{}}}); return r }
async exportStageTab(e,t,n){ let{data:r} = await Y.get(`/tracker/stage-export/`,
   {params:{stage:e, tab:t, ids:n.join(`,`)}, responseType:`blob`}); return r }
```

The verdicts file also records **no params** for either. They both require `stage`;
`stage-export` additionally needs `tab` and `ids` and returns an xlsx blob.

---

## Claim 6 — `qr.png` "EXCLUDED-UNPROVEN, no IRN observed"

**Verdict: REFUTED.** IRNs are sitting in a *shipped* CLI read command.

```
$ GET /api/einvoice/logs/      # = shipped `einvoice logs`
{"count":59,"totals":{"SUCCESS":47,...},"results":[{"id":59,"docentry":10001,
 "outcome":"SUCCESS","doc_no":"626000002",
 "irn":"0000aaaa1111bbbb2222cccc3333dddd4444eeee5555ffff6666aaaa7777bbbb", ...}]}

$ GET /api/einvoice/irn/0000aaaa1111…7777bbbb/qr.png
200  image/png  5223 b   (\x89PNG\r\n\x1a\n … real image)
```

47 SUCCESS log rows carry IRNs. The endpoint is live, the param is observable from
a command the CLI already ships, and it should be published, not excluded.

---

## Scoreboard

| # | claim | verdict |
|---|---|---|
| 1 | 26 "gone" commands are still live; drop nothing | **CONFIRMED** (26/26, up from a 6-endpoint spot check) |
| 2 | 34 of 44 new paths are writes | **REFUTED (minor)** — 36 writes + 1 token exchange + 7 reads |
| 2b | no read lost to GET/POST mis-bucketing inside the 44 | **CONFIRMED** (0 matches) |
| 3 | new READ surface is 6, 4 callable | **REFUTED** — 19 reads, 13 proven live-200 |
| 4a | branch enum is `BEVERAGE` singular | **CONFIRMED** (plural `BEVERAGES` exists but only on a write) |
| 4b | inventory-report takes `branch` + optional `warehouses` | **CONFIRMED** |
| 4c | pending-dispatch takes `branch` + `from_date`/`to_date` | **CONFIRMED** — but `branch=BEVERAGE` 502s server-side |
| 4d | used-sales-orders takes `card_code` | **REFUTED** — `card_code` is echo-only; `branch` is the filter and is undocumented |
| 4e | reserved-batches takes no params | **REFUTED** — takes `branch`, and it filters |
| 5 | 403 proves stage-decisions/stage-export exist | **half CONFIRMED** (routed) / **REFUTED** (verb not corroborated — a POST-only tracker route 403s identically) |
| 6 | qr.png excluded, no IRN observable | **REFUTED** — IRNs in `einvoice logs`; qr.png returns a live 5223-byte PNG |

## Recommended changes to the publish list

**Add (proven live-200, GET, read-only):** `/api/einvoice/heartbeat/`,
`/api/einvoice/irn/{irn}/`, `/api/einvoice/irn/by-doc/`, `/api/einvoice/irn/rejected/`,
`/api/einvoice/irn/from-invoice/{docentry}/`, `/api/einvoice/gstin/{gstin}/`,
`/api/einvoice/ewb/{irn}/`, `/api/einvoice/irn/{irn}/qr.png`,
`/api/ewaybill/from-invoice/{docentry}/`.

**Add with a caveat:** `/api/ewaybill/gstin/{gstin}/` (routed; NIC host unreachable today).

**Hold as unproven:** `/api/ewaybill/{ewbNo}/`, `/api/ewaybill/transporter/{id}/`
(no observed value to test with — do not fuzz).

**Never add:** `/api/einvoice/gstin/{gstin}/sync/` (GET, but a sync trigger).

**Fix the params:** `used-sales-orders` → `branch` (filters) + `card_code` (echo only);
`reserved-batches` → `branch`; `stage-decisions` → `stage`,`decision`,`include_resolved`;
`stage-export` → `stage`,`tab`,`ids` (xlsx blob).

**Demote:** `pending-dispatch` `branch=BEVERAGE` — server-side HANA error, OIL only in practice.

**Fix the harvester before the next run:** accept relative (no-leading-slash) template
paths, and drop the `API_PREFIXES` allow-list in favour of resolving the axios instance
baseURL (`Ea`) and the `I6/N6/L6/R6` wrappers.

> Document numbers, IRNs and doc entries in this file are **synthesized**. The endpoint shapes, HTTP status codes and response structures are real, captured 2026-08-22.
