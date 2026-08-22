# REFUTATION — `study-shipment-v2.md`

Adversarial re-audit, 2026-08-22. Target:
`/root/.handoff-runs/rescrape-all/scratch/ecom/studies/study-shipment-v2.md`

**Read-only compliance:** every live call below was a `GET`. No POST/PUT/PATCH/DELETE
was issued against `ecom.jivo.in`. No unobserved *parameter value* was sent. The only
unobserved *path segments* sent were the study's own already-documented routing
controls (`zzz-control…`), which are unrouted and therefore cannot reach a view.

**Token state:** VALID.
```
curl -s -o b.txt -w '%{http_code} %{size_download}\n' -H "Authorization: Bearer $T" \
  'https://ecom.jivo.in/api/auth/me'
→ 200 3695   {"user":{"id":35,"email":"dp605702@jivo.in",...
```

**Headline:** the study is largely sound and unusually careful about its own limits,
but it ships **one enum that is flatly wrong** and would have put bad allowed-values
into the CLI, plus one invented field attribution. It also never states the sharpest
limitation of its own live evidence: on this server a 403 fires *before* method
dispatch, so the 403s prove routing and prove **nothing about the verb**.

---

## A. REFUTED

### A-1. `bucket` enum on `GET /api/shipment/v2/pos/` — **REFUTED**

**Claim** (study §1.3 #4 and §4 table row 5):
> `bucket` is a sorted comma-joined set, built as `we = D.size ? [...D].sort().join(',') : 'none'`,
> with UI default `new Set(['with_stock'])`. … observed wire values: **`with_stock`**,
> **`without_stock`**, **`with_stock,without_stock`** (sorted), and **`none`**.

**Verdict: REFUTED.** The study read `we` off the correct memo but bound it to the
**wrong Set**. `we` is derived from `D`; `D` is initialised to `new Set(['open'])`,
not `new Set(['with_stock'])`. The `with_stock` Set is a *different* state variable
(`xe`) in the same component, and it never reaches any GET.

Command:
```bash
cd /root/.handoff-runs/rescrape-all/scratch/ecom/bundle
python3 g.py NewShipmentV2-niuH1T3p.js '\[D,[A-Za-z$_]+\]=' 200 300 6
```
Output (trimmed, @66777 — the PO-book component's state block):
```js
[C,w]=useState(()=>new Set),[E,ne]=useState(()=>new Set),
[D,O]=useState(()=>new Set(`open`)),           //  <-- D, the bucket set
...
[xe,Se]=useState(()=>new Set([`with_stock`])), //  <-- xe, a DIFFERENT set
we=useMemo(()=>D.size?[...D].sort().join(`,`):`none`,[D]);
z.pos({channel:e,appointment_id:t,bucket:we},{signal:n.signal})
```

`D` is fed by the chip component `Ye`, whose vocabulary is `Je`:
```bash
python3 g.py NewShipmentV2-niuH1T3p.js 'key:`open`' 400 800 4
```
```js
var Je=[
 {key:`open`,      label:`Open`,      hint:`Every line not yet fully invoiced — the working book…`},
 {key:`full`,      label:`Invoiced`,  hint:`Every accepted unit is already on a SAP invoice.`},
 {key:`short`,     label:`Partial`,   hint:`Billed, but not for every accepted unit…`},
 {key:`dispatched`,label:`Dispatched`,hint:`The units have physically left the warehouse…`}];
function Ye({value:e,busy:t,onChange:n,extra:r}){ … `aria-label`:`Pendency buckets` … }
```
And the wiring, @76943:
```js
jsx(Ye,{value:D, busy:v, onChange:O, …})        // pendency buckets  -> bucket=
jsx(wt,{value:xe,busy:R, onChange:Se})          // stock rules       -> NOT a query param
```

`xe` is consumed only as `stockRules` on the fill dialog, i.e. it reaches the wire
only inside the body of the **excluded POST**:
```bash
python3 -c "…scan identifier 'xe' in 66700..92000…"
→ @86322  jsx(qe,{channel:e,apptId:t,capacity:n,busy:R,stockRules:xe,…onRun:He…})
→ @74452  z.fill({channel:e,appointment_id:t||void 0,capacity_liters:n,
                  strategies:r.strategies,families:…,asins:…,priority:…})
```

**The truth instead:**
`bucket` = **pendency bucket**, multi-select, sorted and comma-joined.
Member values: **`open` | `full` | `short` | `dispatched`**.
Default wire value: **`open`**. Empty selection sends the literal **`none`**.
Legal multi-values are the sorted joins, e.g. `full,open`, `dispatched,open`,
`full,open,short`, `dispatched,full,open,short`.

`with_stock` / `without_stock` are **strategy** values on the excluded
`POST /api/shipment/v2/fill/`, never on `GET /api/shipment/v2/pos/`.

**Impact: high.** Shipping the study's table verbatim would give the CLI a
`--bucket` flag whose entire allowed-value list is wrong, and whose documented
default is wrong.

---

### A-2. `switch_kind` as a `/api/shipment/switching/` row field — **REFUTED (attribution)**

**Claim** (study §2.2): row fields "from the row search predicate + renderer" include
`switch_kind`.

**Verdict: REFUTED as stated.** `switch_kind` appears **zero times** in the only chunk
that consumes `/api/shipment/switching/`.
```bash
cd …/bundle
grep -o '\bswitch_kind\b' Record-8P_EMA-e.js | wc -l      → 0
grep -l 'switch_kind' *.js
→ PlanReview-CIIGZFyB.js  SwitchingModal-CH1YjZiE.js
  CreateShipment-kUDJIfZs.js  NewShipmentV2-niuH1T3p.js
```
In every one of those it is a field the client **writes**, not one it reads:
```js
// NewShipmentV2 @93038 — building switchDetails for the createDraft POST
t.push({po_number:n.po,asin:n.asin,…,home_fc:r,switch_to_fc:e,switch_kind:`fc`,…})
// NewShipmentV2 @93777
p=t.filter(…).map(e=>({po_number:…,from_fc:…,to_fc:…,switch_kind:e.switch_kind||`fc`,
   from_appointment_id:…,from_appointment_time:…,to_appointment_id:…,to_appointment_time:…,units:…}))
```
The "kind" in the History screen is a **client-side prop**, not a response field:
```js
// Record @21581
jsx(w,{kind:`fc`,         title:`PO Switching`,          hint:`PO sits at a sister FC…`,rows:Q.po,…})
jsx(w,{kind:`appointment`,title:`Appointment Switching`, hint:`PO is already at this FC…`,rows:Q.appt,…})
```
It is *plausible* the ledger echoes `switch_kind`, but the study's cited evidence does
not support it. Note the study's switching field list is in fact a **mix** of the read
consumer (Record) and the write payload (NewShipmentV2) — it should say so.

---

### A-3. "the old `short-supply` route now 301s into it" — **REFUTED (minor)**

Study §2.2. It is a client-side React-Router `<Navigate replace>`, not an HTTP 301.
The study states it correctly in §1.5(a) and incorrectly in §2.2.
```bash
python3 g.py index-Bdcm-waj.js 'short-supply' 300 300 3
→ jsx(E,{path:`short-supply`,element:jsx(C,{to:`/platform/amazon/shipment-planning/record`,replace:!0})}),
  jsx(E,{path:`record`,element:jsx(xr,{})})
```

---

### A-4. Field lists are incomplete (not wrong) — **PARTIAL**

- Appointment rows: the search predicate also reads **`pos`**, which the study omits.
  `String(t.appointment_id…)||String(t.destination_fc…)||String(t.status…)||String(t.pos…)`
- Switching rows: the renderer also reads **`from_appointment_time`** and
  **`to_appointment_time`** (`Record` @4344), which the study omits.

---

## B. UNTESTABLE / SOURCE-ONLY — no live 200 anywhere in this study

**Zero 200 responses were obtained for any of the seven proposed endpoints.** Every
response field, container key, default and enum in the study is derived from minified
client code. That is the strongest evidence obtainable on this credential, and the
study does say so in §4 — but three things are weaker than the study presents them:

### B-1. **Every verb is source-only, and the 403 cannot corroborate it** — NEW FINDING

The study never flags this. On this server the permission denial fires **before DRF
selects a handler**, so a 403 is returned even for a method the view does not
implement. Proof, obtained today on this very surface:

```bash
T=$(cat /root/.handoff-runs/rescrape-all/scratch/.ecom_token)
curl -s -o b.txt -w '%{http_code}' -X GET -H "Authorization: Bearer $T" \
  'https://ecom.jivo.in/api/shipment/v2/fill/'
→ 403   {"detail":"You do not have access to the Amazon Shipment Planner."}
```
`/api/shipment/v2/fill/` is **POST-only** in the bundle, yet a GET to it returns 403,
not 405. Therefore the 403s in study §1.4 prove **routing only**. The GET/POST split
across all six v2 paths rests entirely on argument 1 of `me(...)` in minified source.

That source evidence is unambiguous and I re-read it verbatim (§C-1), and the failure
mode is benign in the read-only direction — a GET command against a POST-only route
would 405, never write. But it should be recorded as source-only, and it means
"we probed it and got 403" must **not** be written up as verb confirmation.

### B-2. Server-side required-ness — NOT VERIFIED
The gate answers 403 before validation, so no 400 body exists for any v2 path.
`channel`, `appointment_id`, `scope`, `limit`, `bucket`, `state` must be specced
optional. (Study says this correctly, §4.)

### B-3. Genuinely untestable paths (no observed id)
`probe/observed-ids.json` contains **no shipment id and no appointment id**:
```bash
cat …/scratch/ecom/probe/observed-ids.json
→ keys: platform_slug_from_expiry_alerts, dashboard_table, chatbot_conversation_id,
        upload_id, notification_id, sap_card_code, sap_doc_entry
```
Therefore **UNTESTABLE**, exactly as the study says:
- `GET /api/shipment/v2/appointments/{appointment_id}/lines/` — the only v2 path with
  a real path param. Existence source-only; **it is the one v2 path with no live
  routing proof at all.**
- `GET /api/shipment/shipments/{id}/switch/verify/`
- `GET /api/shipment/shipments/{id}/invoices`
- `GET /api/shipment/shipments/{id}/invoices/{invoice}/file`
- `GET /api/shipment/shipments/{id}/po-documents`
- `GET /api/shipment/shipments/{id}/po-documents/{document}`

---

## C. CONFIRMED

### C-1. The v2 API object and all six verbs — **CONFIRMED, verbatim**
```bash
python3 g.py NewShipmentV2-niuH1T3p.js 'appointmentLines' 900 900 2
```
```js
var R=e=>{let t=new URLSearchParams;Object.entries(e||{}).forEach(([e,n])=>{n!=null&&n!==``&&t.set(e,String(n))});
          let n=t.toString();return n?`?${n}`:``},
z={channels:e=>me(`GET`,`/api/shipment/v2/channels/`,void 0,e),
   appointments:(e={},t)=>me(`GET`,`/api/shipment/v2/appointments/${R(e)}`,void 0,t),
   appointmentLines:(e,t)=>me(`GET`,`/api/shipment/v2/appointments/${encodeURIComponent(e)}/lines/`,void 0,t),
   pos:(e={},t)=>me(`GET`,`/api/shipment/v2/pos/${R(e)}`,void 0,t),
   fillOptions:(e={},t)=>me(`GET`,`/api/shipment/v2/fill/options/${R(e)}`,void 0,t),
   fill:(e,t)=>me(`POST`,`/api/shipment/v2/fill/`,e,t)}
```
Five GETs, one POST. **Nothing the study calls a GET is a POST.** The single POST is
correctly identified and excluded. Exhaustiveness re-checked with a wider character
class than the study used — still exactly six:
```bash
grep -o '/api/[a-zA-Z0-9/_{}$.-]*' NewShipmentV2-niuH1T3p.js | sort -u
→ /api/shipment/v2/appointments/${R
  /api/shipment/v2/appointments/${encodeURIComponent
  /api/shipment/v2/channels/
  /api/shipment/v2/fill/
  /api/shipment/v2/fill/options/${R
  /api/shipment/v2/pos/${R
```
Whole-bundle sweep — only two chunks touch `/api/shipment` at all:
```bash
grep -l '/api/shipment' *.js  → NewShipmentV2-niuH1T3p.js  shipmentAPI-Bm5uhztf.js
```
`CreateShipment`, `ShipmentDetail`, `ShipmentList`, `ShipmentPlanning`, `Record`,
`PlanReview`, `SwitchingModal`, `InvoicedTag` contain **no `/api/` string whatsoever**.

### C-2. `me()` signature correction to BRIEF-SHARED.md — **CONFIRMED**
```bash
python3 g.py NewShipmentV2-niuH1T3p.js 'function me\(' 300 600 3
```
```js
async function me(e,t,n,{signal:r}={}){let i={method:e,headers:{"Content-Type":`application/json`},signal:r};
  n!==void 0&&(i.body=JSON.stringify(n)); … a=await N(`${se}${t}`,i) …}
```
The 4th argument is request options destructured for `{signal}` only. There is no
params channel. The brief's `me(VERB, path, body, params)` is wrong; the study's
correction is right.

### C-3. Harvest-shape correction (3 of 4 `{id}` are query strings) — **CONFIRMED, and now live-proven**
Harvest rows:
```
['GET'] has_param=True  /api/shipment/v2/appointments/{}     raw=['/api/shipment/v2/appointments/{}']
['GET'] has_param=True  /api/shipment/v2/pos/{}              raw=['/api/shipment/v2/pos/{}']
['GET'] has_param=True  /api/shipment/v2/fill/options/{}     raw=['/api/shipment/v2/fill/options/{}']
['GET'] has_param=True  /api/shipment/v2/appointments/{}/lines  raw=['…/lines/']
```
Note the first three have **no trailing slash after `{}`** — the fingerprint of
`${R(e)}` being a query string. The live probes settle it: the bare collection forms
resolve (403), they do not 404.

### C-4. Live status of every probeable path — **CONFIRMED (re-tested today)**
```bash
T=$(cat /root/.handoff-runs/rescrape-all/scratch/.ecom_token)
for p in … ; do curl -s -o b.txt -w '%{http_code}' -X GET -H "Authorization: Bearer $T" \
   -H 'Accept: application/json' "https://ecom.jivo.in$p"; done
```
```
/api/shipment/v2/channels/       403  {"detail":"You do not have access to the Amazon Shipment Planner."}
/api/shipment/v2/channels        301  location: /api/shipment/v2/channels/
/api/shipment/switching/         403  {"detail":"You do not have access to the Amazon Shipment Planner."}
/api/shipment/switching          301  location: /api/shipment/switching/
/api/shipment/v2/appointments/   403  {"detail":"You do not have access to the Amazon Shipment Planner."}
/api/shipment/v2/pos/            403  {"detail":"You do not have access to the Amazon Shipment Planner."}
/api/shipment/v2/fill/options/   403  {"detail":"You do not have access to the Amazon Shipment Planner."}
/api/shipment/v2/fill/           403  {"detail":"You do not have access to the Amazon Shipment Planner."}
```
The 403 detail is **the Shipment-Planner one** in every case, not a JWT/auth error.
The four paths the brief said were "NOT probed" — three were probeable as collections
and are now 403-confirmed twice over; the fourth (`…/lines/`) remains untestable.

### C-5. The "403 is per-view, not a prefix gate" control — **CONFIRMED (reproduced)**
```bash
for p in "/api/shipment/zzz-control-not-a-real-path/" "/api/shipment/v2/zzz-control/" "/api/auth/feature-flags"; do …
```
```
/api/shipment/zzz-control-not-a-real-path/  404  text/html  <h1>Not Found</h1>
/api/shipment/v2/zzz-control/               404  text/html  <h1>Not Found</h1>
/api/auth/feature-flags                     404  text/html  <h1>Not Found</h1>
```
Unrouted paths under both `/api/shipment/` **and** `/api/shipment/v2/` return Django's
URL-resolution 404. So 403 ⇒ the URL resolved to a view. Study §3.1 is sound.
Caveat B-1 still applies: it resolved to *a* view, not necessarily to a GET handler.

### C-6. Trailing slashes are load-bearing — **CONFIRMED**
Slashless → `301` with `Location:` the slashed form (measured above). Every v2 path in
the bundle carries its trailing slash, including `…/lines/` and `…/fill/options/`
(the query string is appended after the slash by `R(e)`). The study's spec caution is
correct and must be honoured.

### C-7. v2 is an ADDITION, not a REPLACEMENT — **CONFIRMED, three ways**
Routes (`index-Bdcm-waj.js` @85272) — both mounted, neither a redirect:
```js
jsxs(E,{path:`/platform/amazon/shipment-planning`,element:jsx(G,{permission:L.shipmentPlanning,…}),children:[
  jsx(E,{index:!0,element:jsx(lr,{})}),
  jsx(E,{path:`new`,  element:jsx(dr,{})}),   // v1 CreateShipment
  jsx(E,{path:`new-2`,element:jsx(ur,{})}),   // v2 NewShipmentV2
  … ]})
```
Sidebar (`ShipmentPlanning-C0ayDg1Y.js` @3304) — both links, side by side:
```js
{to:`${N}/new`,label:`New Shipment`,icon:r,state:{freshStart:!0},onClick:k},
{to:`${N}/new-2`,label:`New Shipment 2.0`,icon:y},
```
Decisive — v2 persists through v1's API. Import head of `NewShipmentV2`:
```
import{c as ce}from"./shipmentAPI-Bm5uhztf.js"
```
and (`shipmentAPI` exports `s as c`, where `s` is the shipments API object):
```js
@88805  ce.createDraft({truck_size:…,truck_capacity_liters:…,loaded_items:…,
                        not_loaded_items:…,appointment:null,appointment_id:…,
                        destination_fc:…,commitment_snapshot:…})
@94518  await ce.sendSwitchEmail(h.id,{pdfBlob:i,excelBlob:o,to:…,cc:…,subject:…,body:…})
@95361  await ce.submit(S.id)
```
**Nothing in v1 may be dropped because v2 exists.** Confirmed. (Study's `createDraft`
body rendering omits `appointment:null` and `commitment_snapshot`; immaterial, it is
an excluded POST.)

### C-8. `/api/shipment/switching/` definition, params and response parse — **CONFIRMED**
`shipmentAPI-Bm5uhztf.js` (dumped in full, 7,796 B, via bash not `Read`):
```js
o=(e={})=>{let t=new URLSearchParams(Object.entries(e).filter(([,e])=>e!=null&&e!==``)).toString();
           return i(`GET`,`/api/shipment/switching/${t?`?${t}`:``}`)}
```
Sole call site, `Record-8P_EMA-e.js` @8360:
```js
if(typeof c.switching!=`function`)throw Error(`Switching is not available in this build.`);
let e=await c.switching({state:U===`all`?`all`:U,limit:200});
ue({po:Array.isArray(e?.po_switches)?e.po_switches:[],
    appt:Array.isArray(e?.appointment_switches)?e.appointment_switches:[],
    summary:e&&typeof e.summary==`object`&&e.summary||{}});
```
State vocabulary @1395: `ie=[`all`,`waiting`,`email_failed`,`verified`,`rejected`]`.
Summary keys @20907: `R.summary?.shipments` + `[waiting,email_failed,verified,rejected]`.
Screen: `Record` = `xr` = `{path:'record'}` under `/platform/amazon/shipment-planning`,
sidebar label **"History"** nested in the **"Data"** group. All confirmed.

### C-9. Channel / appointments / pos / fillOptions call sites — **CONFIRMED**
```js
z.channels({signal:e.signal}).then(e=>n(Array.isArray(e?.channels)?e.channels:[]))
   .catch(… `Could not read the channels.` …)                            // no params
z.appointments({channel:e,scope:i,limit:300},{signal:t.signal})
   .then(e=>c(Array.isArray(e?.results)?e.results:[]))
   .catch(… `Could not read the appointments.` …)
z.appointmentLines(e,{signal:t.signal}).then(i)
   .catch(… `Could not read this appointment's lines.` … i({lines:[],summary:{}}))
z.pos({channel:e,appointment_id:t,bucket:we},{signal:n.signal})
   .catch(… `Could not read the PO book.` … m({pos:[],totals:{}}))
z.fillOptions({channel:e,appointment_id:t},{signal:n.signal})
   .catch(… `Could not read what this channel can fill.` … b({families:[],item_heads:[]}))
```
`scope` enum @14814: `G=[{key:`upcoming`},{key:`past`},{key:`all`}]`, default `upcoming`.
`item_heads` keyed by `bucket` @32907: `(y?.item_heads||[]).forEach(t=>e.set(t.bucket,t))`
with `Ue=[{key:`premium`,bucket:`PREMIUM`},{key:`commodity`,bucket:`COMMODITY`},
{key:`other`,bucket:`OTHER`}]` and `Mt=[`COMMODITY`,`PREMIUM`,`OTHER`]`.
**Note:** this response-side `bucket` (PREMIUM/COMMODITY/OTHER) is a *third*, unrelated
use of the word — distinct from the `pos` query param (A-1) and from the stock rules.
The study got this one right; it got the query param wrong.

Every claimed response field name was checked for presence in the chunk. **All 50
appear.** No field was invented — the only bad claim is the `switch_kind` attribution
(A-2) and the `bucket` enum (A-1).

### C-10. `switchVerifyCheck` is a genuine, publishable GET — **CONFIRMED**
```js
// shipmentAPI
switchVerifyCheck:e=>i(`GET`,`/api/shipment/shipments/${e}/switch/verify/`),
switchVerify:(e,t,n=``)=>i(`POST`,`/api/shipment/shipments/${e}/switch/verify/`,{action:t,note:n}),
// ShipmentList @2082
T.switchVerifyCheck(e.id).then(e=>{t||i(e)}).catch(e=>{t||p(w(e,`Auto-check failed.`))})
… let h=r?.results||[];
```
And the prior run's exclusion reason, confirmed verbatim:
```bash
python3 -c "…reconciled.json…"
→ /api/shipment/shipments/{}/switch/verify | chunks ['shipmentAPI-DKVOXJWL.js']
  | EXCLUDE_ACTION | action-shaped route; not probed (rule 1) | old_cmd None
```
Study §6 stands. Routing still UNTESTABLE (no observed shipment id).

### C-11. The four document paths — **CONFIRMED in every particular**
Absent from all 158 chunks:
```bash
for pat in 'po-document' 'po_document' '/invoices' 'attachment' 'PO document'; do grep -l "$pat" *.js; done
→ po-document : (none)   po_document : (none)   /invoices : (none)
  attachment  : vendor-pdf-VfVkerq_.js  (third-party PDF lib)
  PO document : shipmentAPI-Bm5uhztf.js (error string only)
```
Already absent and unprobed at the 2026-08-03 run:
```
reconciled.json  → all four: chunks [] raw_paths [] PROBE_SKIP_PARAM
                   "shipped in v0.1.0 but the current client no longer calls it - probe before assuming dead"
probe-verdicts.json → all four: UNPROBED  []
```
Server-side concept still alive (`shipmentAPI`, verbatim):
```js
if(Array.isArray(n.missing_pos)&&n.missing_pos.length){ …
  return `${n.error||`A PO document (PDF) is required for every PO.`} Missing: ${e}.` }
```
Trailing-slash anomaly in the shipped spec — confirmed, these four are the **only**
shipment paths written without one:
```
shipment-invoice-file      GET  /api/shipment/shipments/{id}/invoices/{invoice}/file
shipment-invoices          GET  /api/shipment/shipments/{id}/invoices
shipment-po-document       GET  /api/shipment/shipments/{id}/po-documents/{document}
shipment-po-documents      GET  /api/shipment/shipments/{id}/po-documents
  (all other 21 shipment paths end in '/')
```
**Verdict on the study's disposition (KEEP, relabelled): endorsed.** They are absent
from the bundle but cannot be shown dead, and the probe that would settle it needs an
unobserved id. Do **not** remove them on this run's evidence.

### C-12. `switch/email` harvest blind spot — **CONFIRMED**
`sendSwitchEmail` bypasses the `i()` helper and calls the raw fetch:
```js
let u=await e(`${t}/api/shipment/shipments/${n}/switch/email/`,{method:`POST`,body:l})
```
It is absent from `harvest.json` (37 shipment rows, none matching `switch/email`).
Worth recording as a known lens blind spot. It is a POST — excluded regardless.

### C-13. Misc — **CONFIRMED**
- `<h1 className="ns2-title">New Shipment 2.0</h1>` @113631.
- `qt=[{key:`channel`,num:1,…},{`appointment`,2},{`truck`,3},{`book`,4},{`review`,5}]` @110113.
- Sole permission string: `grep -ho 'amazon\.shipment[a-z_.]*' *.js | sort -u` →
  `amazon.shipment_planning.view`. Single value, gates the whole subtree incl. `new-2`.
- PO/Appointment switching hints quoted verbatim correctly (Record @21581).
- `SwitchingModal-CH1YjZiE.js` (21,834 B), a chunk the study never names, makes **no**
  API calls — no gap.
- Prior probe record, confirming only two v2/switching paths were ever probed and both
  slashless (they followed the 301):
  ```
  {"path":"/api/shipment/switching","http":403,…}
  {"path":"/api/shipment/v2/channels","http":403,…}
  ```

---

## D. Recommendation for the read-only CLI

**Publish (5) — routed, live-403-confirmed today, verb unambiguous in source:**

| key | verb | path | params |
|---|---|---|---|
| `switching` | GET | `/api/shipment/switching/` | `state` ∈ {all, waiting, email_failed, verified, rejected}; `limit` int (UI 200) |
| `v2-channels` | GET | `/api/shipment/v2/channels/` | none |
| `v2-appointments` | GET | `/api/shipment/v2/appointments/` | `channel`; `scope` ∈ {upcoming, past, all}; `limit` int (UI 300) |
| `v2-pos` | GET | `/api/shipment/v2/pos/` | `channel`; `appointment_id`; **`bucket` ∈ {open, full, short, dispatched}**, sorted comma-joined multi-select, default `open`, literal `none` when empty |
| `v2-fill-options` | GET | `/api/shipment/v2/fill/options/` | `channel`; `appointment_id` |

**Publish with an explicit "routing not live-verified" note (2):**

| key | verb | path | why weaker |
|---|---|---|---|
| `v2-appointment-lines` | GET | `/api/shipment/v2/appointments/{appointment_id}/lines/` | the only v2 path never reached live; parent collection is proven, source is explicit |
| `shipment-switch-verify` | GET | `/api/shipment/shipments/{id}/switch/verify/` | recovers a read wrongly excluded as `EXCLUDE_ACTION`; shares its path with a POST — the CLI must send GET only |

**EXCLUDE (writes):** `POST /api/shipment/v2/fill/`,
`POST /api/shipment/shipments/{id}/switch/verify/`,
`POST /api/shipment/shipments/{id}/switch/email/`.

**Must-fix before generating:** the `bucket` enum (A-1). Ship `open|full|short|dispatched`.

**Must-carry cautions:**
1. Trailing slash on all seven paths — slashless is a 301.
2. Every param optional except the two path params — required-ness unverified.
3. Every response field/shape marked derived-from-client-source, **not verified live**.
4. Verbs are source-derived; the 403 does not corroborate them (B-1).
5. `switch_kind` on the switching ledger: drop it, or mark it inferred from the write
   payload rather than the read consumer.
6. Do not drop any v1 shipment endpoint on the strength of v2 (C-7). Keep
   `appointment-items` — v1's load computation is the only publishable one.
7. Keep the four document commands, relabelled as unverified (C-11).
