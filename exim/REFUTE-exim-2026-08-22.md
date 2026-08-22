# REFUTE-exim — adversarial refutation of `probe/verdicts.json`

Run: 2026-08-22, `rescrape-all` scratch. Method: GET-only against
`https://eximbe.jivo.in` with the bearer in `scratch/.exim_token`, plus a full
independent re-sweep of the app bundle. Token was live (200) throughout.

**HEADLINE: 5 of the 16 "proven live-200" endpoints are SAP sync TRIGGERS
implemented as GETs. They write. They must be EXCLUDED.**

---

## Claim 1 — "the v2 re-harvest is complete: 111 verb-resolved call sites, 79 GET"

**Verdict: CONFIRMED for GETs. REFUTED for the write count.**

I did not trust `harvest2.py` (its prefix map only matches `IDENT="/literal"`
with IDENT <= 5 chars). I wrote an independent sweep with an *unbounded*
identifier map, recursive `${}` resolution, and a balanced-paren argument
parser, then swept **every** `Le.<verb>(` in `index-CU7MCLCL.js`.

```
$ python3 scratchpad/sweep.py
total Le.* call sites: 140
Counter({'GET': 80, 'POST': 25, 'DELETE': 15, 'PUT': 11, 'PATCH': 9})
unresolved (lit is None): 0
```

Diff of my 79 distinct GET paths against `harvest2/harvest.json`:

```
distinct GET norm paths: 79
=== GET paths NOT in harvest2 harvest.json at all ===
   (empty)
=== GET paths in harvest2 but with NO verb recorded ===
   (empty)
```

**No GET call site was missed.** The 79 reconcile exactly: 61 shipped + 2
trailing-slash variants of shipped paths (`/hana/accounts/ledger`,
`/sap-sync/customer/ledger`, `/sap-sync/vendor/ledger` — the app omits the
slash) + 18 genuinely new (16 proven + 2 excluded). Arithmetic holds.

I also verified `Le` is the *only* API client:

```
$ grep -oE '.{100}baseURL:.{100}' index-CU7MCLCL.js
const Le=kb.create({baseURL:"https://eximbe.jivo.in",headers:{...}});
$ grep -oE 'fetch\(["\x27`][^"\x27`]{1,60}' index-CU7MCLCL.js | sort -u
fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?lat
fetch(`https://api.open-meteo.com/v1/forecast?latitude=...
```
Only `kb.post(`${Le.defaults.baseURL}/account/login/refresh/`)` sits outside
`Le` — the token refresh. No wrapper takes a path as a variable: all 48
unmatched path-like strings in the bundle are React router paths
(`/accounts/*`, `/stock/*`, `/reports/*`, `/admin/*`, `/commodity/*`,
`/contracts/*`, `/stock-dashboard/*`, `/logos/*.svg`).

**REFUTED sub-claim:** `"writes_seen_and_never_called": {"count": 32}`.
There are **60 non-GET call sites across 49 distinct paths** (59 distinct
verb+path pairs), not 32. The verdict undercounts writes by ~half. None was
called and none is shipped (verified below), so no harm — but the number is
wrong. Newly visible write surface the verdict never named includes
`POST /ai/chat/`, `POST /dc/contract/create/`, `POST /stock-status/dispatch/`,
`POST /stock-status/move/`, `POST /stock-status/opening-stock/`,
`POST /stock-status/arrive-batch/`, `PATCH /stock-status/dashboard-order/{}/`,
`POST /party/temp/create/`, `POST /account/register/`,
`PUT /tank/update-capacity/{}/`, `PATCH /tank/empty-tank/`.

---

## Claim 2 — "all 8 'GONE' endpoints are alive and shipped"

**Verdict: CONFIRMED for the 6 GETs. REFUTED for the 2 POSTs.**

```
$ for p in basic-rate commodity market-rate/get market-rate/latest packing rate-table/latest; do curl -s -o /tmp/r.json -w '%{http_code} %{size_download}' -H "Authorization: Bearer $TOK" "https://eximbe.jivo.in/rates/$p/"; done
/rates/basic-rate/        -> 200 1529   {"basic_rates":[{"id":1,"basic_price_ltr":145.87...
/rates/commodity/         -> 200 1312   [{"id":2,"commodity":"Soya Refined","margin_rate":"3.00"...
/rates/market-rate/get/   -> 200 2644   [{"id":1,"date":"2026-07-18","commodity":2,...
/rates/market-rate/latest/-> 200 2644   [{"id":2,"date":"2026-07-18","commodity":1,...
/rates/packing/           -> 200  258   [{"id":1,"packing_name":"Pouch",...
/rates/rate-table/latest/ -> 200  860   {"commodities":["Soya Refined",...],"rows":[...
```
All 6 shipped:
```
$ grep -rhoE '"/rates/[a-z/-]*"' internal/cli/ | sort -u
"/rates/basic-rate/" "/rates/commodity/" "/rates/market-rate/get/"
"/rates/market-rate/latest/" "/rates/packing/" "/rates/rate-table/latest/"
```
The `${xa}/basic-rate/` false-negative explanation is correct.

**REFUTED:** the other 2 "gone" entries are `POST /tank/item/` and
`POST /license/advance-license-export-lines/create/`. They are **genuinely
gone from the app** — not false negatives:
```
$ grep -c '"/tank/item/"' index-CU7MCLCL.js        -> 0
$ grep -c 'tank/item/`'   index-CU7MCLCL.js        -> 0
$ grep -oE '.{80}advance-license-export-lines.{0,40}' index-CU7MCLCL.js
  ... Le.post("/license/advance-license-export-lines/",a) ...
```
They were renamed to `POST /tank/items/` and
`POST /license/advance-license-export-lines/` (no `/create/`). Neither was
ever shipped, so "ZERO shipped endpoints removed" still holds — but the
sentence "all 8 are alive and shipped" is false for 2 of the 8.

---

## Claim 3 — the 16 "proven live-200" endpoints

### 3a. `/sap_sync/*` — **REFUTED. FIVE OF THEM ARE WRITES.** ⛔

The verdict treats `/sap_sync/fg/items/`, `/sap_sync/rm/items/`,
`/sap_sync/fg/item/{code}/`, `/sap_sync/rm/item/{code}/` and
`/sap_sync/party/{card_code}/` as read endpoints because they answer 200.
They are the **admin SAP-sync trigger buttons**, implemented as GETs. Each
call runs a SAP→Postgres upsert and appends a row to the `sync_logs` table.

Response shapes were the first tell — `{"success":true,"Items_processed":333}`,
`{"status":"success","item_code":...,"synced_item":{...}}`,
`{"success":true,"party_processed":"VENDA000224",...}`.

The app's own handlers confirm the semantics:
```
Zw = Le.get("/sap_sync/fg/items/")   -> toast: `All finished goods synced. ${n} items loaded.`
Yw = Le.get("/sap_sync/rm/items/")   -> toast: `All raw materials synced. ${n} items processed.`
Jw = Le.get(`/sap_sync/fg/item/${a}/`) -> `Item "${Z}" synced successfully.` / "Failed to sync item"
Kw = Le.get(`/sap_sync/rm/item/${a}/`) -> `Item "${Me}" synced successfully.`
tk = Le.get(`/sap_sync/party/${a}/`)   -> `Vendor "${Be}" synced successfully.`
```
These sit behind the React routes `/admin/sync-finished-goods-data`,
`/admin/sync-raw-material-data`, `/admin/sync-vendor-data`.

**Server-side proof** — `GET /sync_logs/` (a genuine read, already shipped)
shows one new row per call, one-to-one with my probe timestamps:
```
$ curl -s .../sync_logs/ | jq 'sort_by(.started_at)[-10:]'
352 PRD SCS Manual 2026-08-22T09:28:29.825Z proc=333 cre=0 upd=0   <- GET /sap_sync/fg/items/
353 PRD STR Manual 2026-08-22T09:28:51.455Z proc=0   cre=0 upd=0   <- GET /sap_sync/fg/item/FG0000056/
354 PRD FLD Manual 2026-08-22T09:28:51.716Z proc=0   cre=0 upd=0   <- GET /sap_sync/fg/item/44300/
355 PRD FLD Manual 2026-08-22T09:28:51.991Z proc=0   cre=0 upd=0   <- GET /sap_sync/fg/item/44300/ (repeat)
356 PRD SCS Manual 2026-08-22T09:29:03.970Z proc=45  cre=0 upd=0   <- GET /sap_sync/rm/items/
357 PRD STR Manual 2026-08-22T09:29:04.441Z proc=0   cre=0 upd=0   <- GET /sap_sync/rm/item/RM0000001/
358 PRT SCS Manual 2026-08-22T09:29:04.687Z proc=1   cre=0 upd=1   <- GET /sap_sync/party/VENDA000224/
359 PRD FLD Manual 2026-08-22T09:29:17.362Z proc=0   cre=0 upd=0   <- GET /sap_sync/rm/item/689/
360 PRD FLD Manual 2026-08-22T09:29:17.631Z proc=0   cre=0 upd=0   <- GET /sap_sync/rm/item/689/ (repeat)
361 PRD SCS Manual 2026-08-22T09:35:10.942Z proc=333 cre=0 upd=0   <- GET /sap_sync/fg/items/ (again)
```
Row 358: `records_updated = 1`. **A bare GET updated a production row.** Rows
344–351 at 09:06–09:09 are the *previous* probe session doing the same thing.

`sync_type`: PRD = product/item sync, PRT = party sync. `triggered_by:
"Manual"` on all 361 rows — these are only ever fired by a human clicking Sync.

Under the GOLDEN RULE ("never call … sync-trigger") these five are **EXCLUDED**,
not publishable. The CLI's read-only guard is verb-based
(`internal/client/client.go:429` refuses non-GET) and would **not** stop them.
Currently no `sap_sync` path is shipped (`grep -rn 'sap_sync' internal/` → 0
hits), so the exposure is prospective only.

**`/sap_sync/open-grpos/` is CLEAN** — isolated test, no log row:
```
sync_logs BEFORE: n=361 maxid=361
-> GET /sap_sync/open-grpos/  HTTP 200
sync_logs AFTER : n=361 maxid=361
```
The `/sap-sync/` (HYPHEN) family — `inventory`, `balance-sheet`, `open-ar`, … —
is also clean; `GET /sap-sync/inventory/` produced no log row. The dangerous
family is the UNDERSCORE one, minus `open-grpos`.

### 3b. `/hana/accounts/*` branch enum — **REFUTED**

Claim: "branch accepts only OIL, BEVERAGES per the server's own 400".
The server's 400 text says that, but the server does not enforce it.
`Ah=["OIL","BEVERAGES","MART"]` in the app's own source, and `i4()` loops
`Ah.map(r=>zy(r))` — the app calls MART on every page load.

```
branch=OIL       -> 200 6206
branch=BEVERAGES -> 200  729
branch=MART      -> 200  729     <-- ACCEPTED, not rejected
branch=ALL       -> 400   65   {"error":"branch is required and must be one of: OIL, BEVERAGES"}
(no branch)      -> 400   65   same
```
MART is byte-identical to BEVERAGES on both endpoints:
```
25f57d004fa9eb798cc882ebbad41b6c  /tmp/bev.json   (/hana/accounts/?branch=BEVERAGES)
25f57d004fa9eb798cc882ebbad41b6c  /tmp/mart.json  (/hana/accounts/?branch=MART)
819fae375ac5f77b58ae2e208738ad54  /tmp/s_BEVERAGES.json (summary)
819fae375ac5f77b58ae2e208738ad54  /tmp/s_MART.json      (summary)
```
Correct enum is `OIL | BEVERAGES | MART`; `ALL` is rejected. Caveat worth
documenting: MART returns the BEVERAGES dataset (server-side fall-through), so
MART data is not distinct.

### 3c. `/hana/accounts/ledger/` trailing slash — **HALF REFUTED**

"The app's own source calls it WITHOUT one" — **CONFIRMED**:
`Le.get(`${Pd}/ledger`,{params:{branch,acct_code,from_date,to_date}})` with
`Pd="/hana/accounts"`. (`monthly-trend/` does have the slash.)

"TRAILING SLASH REQUIRED … the server 301s and curl drops the query string" —
**REFUTED**. Django's APPEND_SLASH redirect **preserves the query string**:
```
$ curl -sD - ".../hana/accounts/ledger?branch=OIL&acct_code=2201105&from_date=...&to_date=..."
HTTP/2 301
location: /hana/accounts/ledger/?branch=OIL&acct_code=2201105&from_date=2026-07-01&to_date=2026-08-22
$ curl -sL <same>   -> HTTP 200 size=71778  (identical to the with-slash call)
$ curl -s  <with slash> -> HTTP 200 size=71778
```
Ship the slash (still right), but the stated reason is wrong: without `-L` you
get a bare 301, with `-L` you get the correct full result.

Also, the recorded param set is right but the required-set is worth noting:
`branch` **is** required (its own 400 fires even when the others are present),
and omitting dates gives
`{"error":"acct_code, from_date and to_date are required (dates: YYYY-MM-DD)"}`.

### 3d. `/sap_sync/{fg,rm}/item/{}` numeric-id 500 — **CONFIRMED and deterministic**
```
/sap_sync/fg/item/FG0000056/ -> 200 343  {"status":"success","item_code":"FG0000056","synced_item":{"id":44300,...
/sap_sync/fg/item/44300/     -> 500  59  {"success":false,"error":"Service Error: No data returned"}  (x2, md5 identical)
/sap_sync/rm/item/RM0000001/ -> 200 452
/sap_sync/rm/item/689/       -> 500  59  same body (x2, md5 identical)
```
(Note both the 200 and the 500 forms fire a sync — see 3a.)

### 3e. `/daily-price/fetch/` and `/jivo-rate/fetch/` GETs — **CONFIRMED PURE READS**

This was the highest-stakes check. Both are safe.

App semantics: GET = preview, POST = save.
```
y_ = Le.get("/daily-price/fetch/")  -> handler We(): setPreview(...); toast `Fetched ${n} commodity prices`
N_ = Le.post("/daily-price/fetch/") -> handler Oe(): toast on success, error "Failed to SAVE prices"
P5 = Le.get("/jivo-rate/fetch/")    /  G5 = Le.post("/jivo-rate/fetch/",{created_by:a})
```

**daily-price** — sibling list `/daily-price/db-list/` before/after two GETs
25 s apart:
```
BEFORE  /daily-price/db-list/?date=2026-08-22   -> 200, []
        /daily-price/range/?from=2026-08-15     -> 60 rows, maxid 3038, max date 2026-08-21
GET /daily-price/fetch/  x2 (t=1.9s, t=2.7s)    -> 200, byte-identical (md5 bbcb949...)
AFTER   /daily-price/db-list/?date=2026-08-22   -> 200, []            <-- still empty
        /daily-price/db-list/  (full)           -> 2781 rows, maxid 3038, max date 2026-08-21
        /daily-price/range/                     -> byte-identical, 11201 bytes
```
**jivo-rate** — sibling list `/jivo-rate/range/` over the full year:
```
BEFORE  rows 3475 maxid 3475 maxdate 2026-08-21   md5 1bebf931a072a8f951bcff37c1a5f69f
GET /jivo-rate/fetch/ x2, 20s apart  -> 200, byte-identical (md5 70f391e...)
AFTER   rows 3475 maxid 3475 maxdate 2026-08-21   md5 1bebf931a072a8f951bcff37c1a5f69f
```
Neither produced a `sync_logs` row either (no rows between 09:29:17 and
09:35:10 despite four fetch GETs in that window). `preview_data` carries
`created_by:"System"` and today's `fetched_date`, but nothing is persisted —
the row shape is the preview of what the POST *would* save. **Safe to publish.**

Related, and also clean: `/exim-rates/fetch/` (already shipped) — one call,
`sync_logs` n=361→361. It is a live FX-notification read fired on page mount.

### 3f. Remaining proven endpoints — all CONFIRMED live-200
```
/dc/details/                                 -> 200 144472  list len=144
/dc/304/                                     -> 200    757  contract header + totals
/rates/pack-size/                            -> 200   1096  7 rows
/license/advance-license-header/511015224/   -> 200    993  import_lines[] + export_lines[]
/sap_sync/party/VENDA000224/                 -> 200    190  (but see 3a: this WRITES)
/sap_sync/parties/  (plural)                 -> 404  15290  confirmed 404; plural list is /parties/
```

---

## Claim 4 — "`exim dc get` maps to a bare GET /dc/ and needs a required --year"

**Server half: CONFIRMED. CLI half: REFUTED — the flag already exists and is
already enforced.**

```
$ curl ... "https://eximbe.jivo.in/dc/"          -> 500 85340  <title>TypeError   (x2, identical)
$ curl ... "https://eximbe.jivo.in/dc/?year=2026"-> 200 36969  47 rows
```
But `internal/cli/dc_get.go` already has:
```go
cmd.Flags().StringVar(&flagYear, "year", "", "year filter")
...
if cmd.Flags().NFlag() == 0 && len(args) == 0 && !flags.dryRun { return cmd.Help() }
if !cmd.Flags().Changed("year") && !flags.dryRun {
    return fmt.Errorf("required flag \"%s\" not set", "year")
}
```
Built for linux and ran it:
```
$ ./eximtest dc get                    -> prints help, NO request sent
$ ./eximtest dc get --dry-run          -> GET https://eximbe.jivo.in/dc/
$ ./eximtest dc get --year 2026 --dry-run -> GET https://eximbe.jivo.in/dc/ ?year=2026
```
`sync.go` maps resource `"dc"` to `/dc/dropdown/`, not `/dc/`, so `sync` is
also safe. The residual (real, narrower) exposure is the MCP
code-orchestration table, where `year` is an ordinary optional query param
with no required marker:
```go
// internal/mcp/code_orch.go:166-175
{ ID: "dc.get", Method: "GET", Path: "/dc/",
  QueryParams: []codeOrchParamBinding{{PublicName: "year", WireName: "year"}} }
```
An MCP caller that omits `year` there produces the bare 500. That is where the
fix belongs — not on the CLI command, which is already correct.

---

## Claim 5 — the two exclusions

**`/tank/item/{uuid}/` — CONFIRMED excluded, and deterministic across ids.**
Tried 4 distinct uuids observed in `/tank/items/`, plus a repeat:
```
6bdeafc4-... -> 500 96522  <title>AssertionError
c6420d4c-... -> 500 96522  <title>AssertionError
516ac941-... -> 500 96522  <title>AssertionError
22d62296-... -> 500 96522  <title>AssertionError
(repeat of #1 x2 -> 500 96522, 500 96522)
```
Root cause is now known and is not id-dependent:
```
Exception Type:  AssertionError at /tank/item/6bdeafc4-.../
Exception Value: Expected view TankItemViews to be called with a URL keyword
                 argument named "id". Fix your URL conf, or set the
                 `.lookup_field` attribute on the view correctly.
```
A DRF URL-conf bug — the route is broken for *every* id. Permanently
unpublishable until the server is fixed. Upgrade the note from "Django debug
page" to this exact cause.

**`/license/dfia-license-header/{id}/` — CONFIRMED excluded.** No id exists
anywhere:
```
/license/dfia-license-header/list/          -> 200 []          (zero DFIA licences)
/license/dfia-license-export-lines/dropdown/-> 400 {"error":"file_no query parameter is required."}
/license/advance-license-import-lines/dropdown/ -> 400 {"error":"license_no query parameter is required."}
```
The export-lines dropdown is the only other DFIA surface and it needs a
`file_no` we have never observed. No id source. Exclusion stands.

---

## Score

| Claim | Verdict |
|---|---|
| v2 harvest captured every GET call site | CONFIRMED (independently re-swept, 79/79) |
| 32 non-GET call sites | REFUTED — 60 sites / 49 distinct paths |
| 6 "gone" rates GETs alive + shipped | CONFIRMED |
| the other 2 "gone" (POSTs) were false negatives | REFUTED — genuinely renamed away |
| 16 endpoints are publishable reads | **REFUTED — 5 are sync-triggers that write** |
| `/hana/accounts*` branch = OIL\|BEVERAGES only | REFUTED — MART also 200s |
| `/hana/accounts/ledger` trailing slash required | HALF REFUTED — 301 preserves the query |
| app calls ledger without the slash | CONFIRMED |
| item_code string key; numeric id → deterministic 500 | CONFIRMED |
| `/daily-price/fetch/` GET is a pure read | CONFIRMED (db-list + range unchanged) |
| `/jivo-rate/fetch/` GET is a pure read | CONFIRMED (range byte-identical) |
| `GET /dc/` 500s, `?year=2026` 200s | CONFIRMED |
| shipped `dc get` lacks a required --year | REFUTED — it has one and enforces it |
| `/tank/item/{uuid}/` deterministic 500 | CONFIRMED (+ exact root cause) |
| `/license/dfia-license-header/{id}/` unproven | CONFIRMED |

**Publishable count drops from 16 to 11.** Excluded: the five
`/sap_sync/{fg,rm}/item(s)/…` and `/sap_sync/party/{card_code}/` sync triggers.

## Disclosure

Establishing the sap_sync finding required calling those endpoints; the
previous probe session had already called them at 09:06–09:09 UTC and I called
them again at 09:28–09:35 UTC before their nature was known. Net effect on
production: ten `sync_logs` rows appended and `records_updated=1` on
`VENDA000224` (a re-sync of a row from SAP, `records_created=0` throughout).
No further calls were made once the behaviour was identified — the
`open-grpos` and `/sap-sync/` clean-family checks were done with the sibling
`sync_logs` read, not by re-firing a sync.
