# Study — `shipment v2` + the disappeared shipment sub-resources

Run: `rescrape-all`, 2026-08-22. Bundle downloaded 2026-08-22 (158 chunks).
Scope: `/api/shipment/v2/*`, `/api/shipment/switching`, and the four shipment
document paths published in spec v0.2.0 that are absent from today's bundle.

**Read-only compliance:** every live call in this study was a `GET`. No fabricated
path-segment id or query value was ever sent (see §3 for the one place where that
constraint left a gap open, and the exact probe that would close it).

---

## Operator summary — read this first

1. **`/api/shipment/v2/*` is a brand-new, hand-built planning wizard called
   "New Shipment 2.0"**, mounted at `/platform/amazon/shipment-planning/new-2`,
   with its own sidebar link sitting directly **next to** the old "New Shipment"
   link. Six endpoints: five GETs and one POST.

2. **v2 does NOT supersede v1. It sits on top of it.** Both routes are mounted,
   both sidebar links are rendered, and — decisively — v2's final "Save as draft"
   and "Submit for approval" steps call **v1's** `createDraft` / `submit` from
   `shipmentAPI-*.js`. v2 replaced the *planning screen*, not the *shipment API*.
   **Nothing in v1 may be dropped on the strength of v2 existing.**

3. **A read that v1 does, v2 does as a POST.** v1 computes the truck load with
   `GET /api/shipment/appointments/{id}/items/` (~15 query params). v2 computes it
   with `POST /api/shipment/v2/fill/`. Under the read-only rule the v2 equivalent is
   **unpublishable**, so v1's `appointment-items` is the only publishable way to see
   a computed load. This is a positive reason to **keep** v1's command.

4. **`/api/shipment/switching/` is the "History → Switching" ledger**: every PO this
   planner asked Amazon to move, and where each request stands. Two kinds —
   *PO Switching* (PO is at a sister FC, must move to this truck's FC) and
   *Appointment Switching* (PO is at the right FC but booked on another appointment
   and must be re-slotted). `?switch_state=` on the existing `shipments` endpoint is
   a *filter* on the same concept and is already in v0.2.0.

5. **The four disappeared document paths did not disappear this run — they were
   already absent on 2026-08-03.** They are v0.1.0 heirlooms that were carried into
   v0.2.0 with zero bundle evidence and were never probed. Today they are absent from
   **all 158 chunks**. They were **not replaced** by anything: no chunk in the bundle
   references invoices, PO documents, or attachments as endpoints. But **"absent from
   the bundle" is not "dead"** — see §3, which states precisely what could and could
   not be established.

6. **One recoverable read was wrongly excluded in v0.2.0:**
   `GET /api/shipment/shipments/{id}/switch/verify/` (`switchVerifyCheck`). It was
   dropped as `EXCLUDE_ACTION` because a `POST` shares the path, but the GET is a
   pure read ("Auto-check") returning `{results:[…]}`. Recommend publishing it.

7. **Harvest correction (important, affects the spec).** The harvest normalised three
   v2 paths as parameterised (`…/appointments/{id}`, `…/pos/{id}`,
   `…/fill/options/{id}`). **They are not parameterised.** The `{}` is a
   *query string*, built by a helper `R(e)`. They are collection GETs. Only
   `…/appointments/{id}/lines/` has a real path param. The brief's drift list carries
   the wrong shape for three of the four.

8. **Trailing slashes are load-bearing on this server.** `GET
   /api/shipment/v2/channels` (no slash) returns **301**; with the slash it returns
   403. Every v2 path must be specced with its trailing slash exactly as the app
   builds it.

---

## 1. What is `/api/shipment/v2/*`?

### 1.1 Which UI screen

| Fact | Value | Evidence |
|---|---|---|
| Chunk | `bundle/NewShipmentV2-niuH1T3p.js` (116,726 B) | `ls -la bundle/ \| grep -iE 'shipment'` |
| Route | `/platform/amazon/shipment-planning/new-2` | see command below |
| Sidebar label | **"New Shipment 2.0"** | see command below |
| `<h1>` page title | **"New Shipment 2.0"** | see command below |
| CSS namespace | `ns2-` | same greps |
| Permission gate | `amazon.shipment_planning.view` (same as v1) | `grep -ho 'amazon\.shipment[a-z_.]*' bundle/*.js \| sort -u` |

Route (the lazy component `ur` is `NewShipmentV2`, and `dr` is the v1
`CreateShipment` at sibling path `new`):

```bash
cd /root/.handoff-runs/rescrape-all/scratch/ecom/bundle
python3 /tmp/.../g.py index-Bdcm-waj.js 'jsx\)\(ur' 700 300 5
```
→
```
{path:`/platform/amazon/shipment-planning`,element:...{permission:L.shipmentPlanning,
  children:[ {index:!0,element:(lr)},
             {path:`new`,   element:(dr)},      // v1 CreateShipment
             {path:`new-2`, element:(ur)},      // v2 NewShipmentV2
             {path:`plan-review`,...}, {path:`list`,...}, ... ]
```

Sidebar (both links present, side by side):

```bash
python3 /tmp/.../g.py ShipmentPlanning-C0ayDg1Y.js 'new-2' 300 200 8
```
→
```
N=`/platform/amazon/shipment-planning`,
P=[{to:N,label:`Dashboard`,end:!0},
   {to:`${N}/new`,   label:`New Shipment`,     state:{freshStart:!0}},
   {to:`${N}/new-2`, label:`New Shipment 2.0`},
   {to:`${N}/list`,  label:`All Shipments`}, ...
   {label:`Data`,children:[ {to:`${N}/po-list`,label:`Purchase Orders`},
                            {to:`${N}/soh-doh`,label:`SOH / DOH`},
                            {to:`${N}/sap-sales-analysis`,label:`SAP Sales`},
                            {to:`${N}/record`,label:`History`} ]}, ...]
```

Page heading:

```bash
python3 /tmp/.../g.py NewShipmentV2-niuH1T3p.js '`h1`' 100 300 8
```
→ ``(`h1`,{className:`ns2-title`,children:`New Shipment 2.0`})``

The wizard is a 5-step machine driven entirely by URL search params
(`?channel=&appt=&cap=&review=`):

```bash
python3 /tmp/.../g.py NewShipmentV2-niuH1T3p.js '`channel`' 200 300 12
```
→
```
qt=[{key:`channel`,num:1,label:`Channel`},
    {key:`appointment`,num:2,label:`Appointment`},
    {key:`truck`,num:3,label:`Truck load`},
    {key:`book`,num:4,label:`POs & Express`},
    {key:`review`,num:5,label:`Review & save`}]
```

### 1.2 The full set of `/api/shipment/v2/...` paths

Every `/api/*` string in the chunk — this is the **complete and exhaustive** list,
and it confirms there is no path the harvest missed:

```bash
cd /root/.handoff-runs/rescrape-all/scratch/ecom/bundle
grep -o '/api/[a-z0-9/_{}$-]*' NewShipmentV2-niuH1T3p.js | sort -u
```
→
```
/api/shipment/v2/appointments/${
/api/shipment/v2/appointments/${encode
/api/shipment/v2/channels/
/api/shipment/v2/fill/
/api/shipment/v2/fill/options/${
/api/shipment/v2/pos/${
```
Six paths, nothing else. Same command run over
`CreateShipment-kUDJIfZs.js`, `ShipmentDetail-C_zjX7--.js`,
`ShipmentList-CbZ2S171.js`, `ShipmentPlanning-C0ayDg1Y.js` returns **nothing** —
those screens make all their calls through the imported `shipmentAPI` helpers.

The API object, verbatim (verb is `me`'s argument 1):

```bash
python3 /tmp/.../g.py NewShipmentV2-niuH1T3p.js 'var R=e=>' 0 1400 1
```
→
```js
var R=e=>{let t=new URLSearchParams;
  Object.entries(e||{}).forEach(([e,n])=>{n!=null&&n!==``&&t.set(e,String(n))});
  let n=t.toString(); return n?`?${n}`:``},
z={
  channels:         e     =>me(`GET`, `/api/shipment/v2/channels/`,                      void 0, e),
  appointments:    (e={},t)=>me(`GET`,`/api/shipment/v2/appointments/${R(e)}`,           void 0, t),
  appointmentLines:(e,  t)=>me(`GET`,`/api/shipment/v2/appointments/${encodeURIComponent(e)}/lines/`, void 0, t),
  pos:             (e={},t)=>me(`GET`,`/api/shipment/v2/pos/${R(e)}`,                    void 0, t),
  fillOptions:     (e={},t)=>me(`GET`,`/api/shipment/v2/fill/options/${R(e)}`,           void 0, t),
  fill:            (e,  t)=>me(`POST`,`/api/shipment/v2/fill/`,                          e,      t)
}
```

**Harvest-shape correction.** `R(e)` returns `"?a=b"` or `""`. So
`` `/api/shipment/v2/appointments/${R(e)}` `` resolves to
`/api/shipment/v2/appointments/?channel=…`, **not** `/api/shipment/v2/appointments/{id}`.
Three of the four `{id}`s in the brief's drift list are query strings.

**Correction to the helper table in BRIEF-SHARED.md.** The brief lists
`me(\`VERB\`, path, body, params)`. The 4th argument is **not** params — it is a
request-options object destructured for `{signal}` only:

```bash
python3 /tmp/.../g.py NewShipmentV2-niuH1T3p.js '(async )?function me\(' 400 700 3
```
→ `async function me(e,t,n,{signal:r}={}){let i={method:e,headers:{"Content-Type":`application/json`},signal:r}; n!==void 0&&(i.body=JSON.stringify(n)); … a=await N(`${se}${t}`,i) …}`

Query params therefore *only* ever reach the wire through `R(e)` baked into the
path. `me` has no params channel at all.

Corrected path table:

| # | Verb | Path (exact, with slashes) | Helper key | Publishable |
|---|---|---|---|---|
| 1 | GET | `/api/shipment/v2/channels/` | `channels` | yes |
| 2 | GET | `/api/shipment/v2/appointments/` | `appointments` | yes |
| 3 | GET | `/api/shipment/v2/appointments/{appointment_id}/lines/` | `appointmentLines` | yes |
| 4 | GET | `/api/shipment/v2/pos/` | `pos` | yes |
| 5 | GET | `/api/shipment/v2/fill/options/` | `fillOptions` | yes |
| 6 | POST | `/api/shipment/v2/fill/` | `fill` | **no — write, excluded** |

### 1.3 What each GET returns, and the params the UI actually sends

Every param below is taken from the app's own call site. Nothing is guessed.

```bash
for k in 'z\.channels\(' 'z\.appointments\(' 'z\.appointmentLines\(' 'z\.pos\(' 'z\.fillOptions\(' 'z\.fill\('; do
  python3 /tmp/.../g.py NewShipmentV2-niuH1T3p.js "$k" 350 350 6
done
```

**1 · `GET /api/shipment/v2/channels/` — step 1, channel picker**
- Params: **none.** The call site is `z.channels({signal:e.signal})` — that object is
  `me`'s options arg, not params.
- Returns `{ channels: [ … ] }` (`.then(e=>n(Array.isArray(e?.channels)?e.channels:[]))`).
- Per-channel fields, from the card renderer
  (`python3 g.py NewShipmentV2-niuH1T3p.js 'ns2-chan-card|ns2-chan-name' 400 900 2`):
  `channel`, `open_po_count`, `open_units`, `open_liters`, `upcoming_count`,
  `fc_count`, `next_appointment_time`.
- Error string the UI shows: `"Could not read the channels."`

**2 · `GET /api/shipment/v2/appointments/` — step 2, appointment picker**
- Call site: `z.appointments({channel:e, scope:i, limit:300}, {signal:t.signal})`
- Params: `channel` (a `.channel` value from #1), `scope`, `limit` (UI sends **300**).
- `scope` enum is observed in source, not guessed
  (`python3 g.py NewShipmentV2-niuH1T3p.js 'upcoming' 300 300 8`):
  `G=[{key:`upcoming`,label:`Upcoming`},{key:`past`,label:`Past`},{key:`all`,label:`All`}]`
  → **`upcoming` | `past` | `all`**, default `upcoming`.
- Returns `{ results: [ … ] }`.
- Per-row fields (from `ns2-appt-*` renderer): `appointment_id`, `channel`,
  `destination_fc`, `appointment_time`, `po_count`, `eligible_po_count`, `status`,
  `amazon_unit_count`, `amazon_carton_count`, `open_units`, `open_liters`.
- Error string: `"Could not read the appointments."`

**3 · `GET /api/shipment/v2/appointments/{appointment_id}/lines/` — PO & SKU drawer**
- Call site: `z.appointmentLines(e, {signal:t.signal})` where `e` is the row's
  `appointment_id`. **The only real path param in v2.**
- No query params.
- Returns `{ lines: [ … ], summary: { … } }`.
- `summary`: `po_count`, `line_count`, `eligible_count`, `blocked_count`.
- Per-line: `is_eligible` (the UI's Eligible/Blocked filter is `lines.filter(e=>e.is_eligible)`),
  plus `ineligible_reason`, `po_number`, `asin`/`sku_code`, `product_name`,
  `accepted_qty`, `remaining_qty`, `case_pack`.
- Drawer heading: `"PO & SKU detail"`. Error: `"Could not read this appointment's lines."`

**4 · `GET /api/shipment/v2/pos/` — step 4, "POs & Express" book**
- Call site: `z.pos({channel:e, appointment_id:t, bucket:we}, {signal:n.signal})`
- Params: `channel`, `appointment_id`, `bucket`.
- `bucket` is a **sorted comma-joined set**, built as
  `we = D.size ? [...D].sort().join(`,`) : `none``, with UI default
  `new Set([`with_stock`])`. Member values are observed in source
  (`python3 g.py NewShipmentV2-niuH1T3p.js 'with_stock' 250 250 10`):
  ```
  Ct=[{key:`with_stock`,   label:`With`,    hint:`Cap every line to what is genuinely free in the warehouse today.`},
      {key:`without_stock`,label:`Without`, hint:`Plan the ordered quantity even where there is no stock behind it.`}]
  ```
  → observed wire values: **`with_stock`**, **`without_stock`**,
  **`with_stock,without_stock`** (sorted), and **`none`** when nothing is ticked.
- Returns `{ pos: [ … ], totals: { … }, stock_meta: { … } }`.
- `totals`: `line_count`, `units`, `liters`, `stock_backed_units`.
- Per-PO: `po_number`, `sku_count`, `units`, `liters`, `stock_backed_units`,
  `lines: [ … ]`, `po_status`, `po_record_status`, `claimed_qty`,
  `claimed_shipment_id`, `is_locked`, `item_head`, `sub_category`.
- `stock_meta`: `unavailable`, `stale`, `age_seconds` — the UI surfaces
  *"Live stock could not be read from SAP…"* on `unavailable`, and a staleness
  banner when `stale` or `age_seconds/60 >= 10`.
- Error: `"Could not read the PO book."`

**5 · `GET /api/shipment/v2/fill/options/` — step 3, "what this channel can fill"**
- Call site: `z.fillOptions({channel:e, appointment_id:t}, {signal:n.signal})`
- Params: `channel`, `appointment_id`. Nothing else.
- Returns `{ families: [ … ], item_heads: [ … ]}` (the catch-branch fallback
  `b({families:[],item_heads:[]})` is the shape proof).
- `families[]`: `{ family, packs: [ { asin, … } ] }`.
- `item_heads[]`: keyed by `bucket`, carrying `po_count`
  (`(y?.item_heads||[]).forEach(t=>e.set(t.bucket,t))`, then `ce.get(e.bucket)?.po_count`).
- Bucket vocabulary, observed in source: `Ue=[{key:`premium`,bucket:`PREMIUM`},
  {key:`commodity`,bucket:`COMMODITY`},{key:`other`,bucket:`OTHER`}]` and
  `Mt=[`COMMODITY`,`PREMIUM`,`OTHER`]`.
- Error: `"Could not read what this channel can fill."`

**6 · `POST /api/shipment/v2/fill/` — WRITE, excluded.** Recorded only so the
migration doc can explain the asymmetry. Body observed at the call site:
`{channel, appointment_id, capacity_liters, strategies, families, asins, priority}`.
Strategy vocabulary (`Nt`): `doh`, `with_stock`, `without_stock`, `focus`, `priority`.
Default priority split `We={premium:50,commodity:50,other:0}`. Truck sizes
`Pt=[[1e4,'10_ton'],[15e3,'15_ton'],[18e3,'18_ton'],[21e3,'21_ton']]`, default
capacity `Jt=15e3` litres.

### 1.4 Live verification

All four v2 reads were probed with bare `GET` (no fabricated values). The harvest had
only ever probed `channels`; the other three had been skipped as "parameterised".

```bash
TOK=$(cat /root/.handoff-runs/rescrape-all/scratch/.ecom_token)
for p in /api/shipment/v2/channels/ /api/shipment/v2/appointments/ \
         /api/shipment/v2/pos/ /api/shipment/v2/fill/options/ ; do
  curl -s -o /tmp/b.txt -w '%{http_code} %{size_download} %{content_type}\n' \
    -X GET -H "Authorization: Bearer $TOK" -H 'Accept: application/json' \
    "https://ecom.jivo.in$p"
  head -c 300 /tmp/b.txt
done
```
→ all four: `403 67 application/json` +
`{"detail":"You do not have access to the Amazon Shipment Planner."}`

**All four exist and are routed** (see §3.1 for why the 403 is a positive proof
here, and not merely a gate). `…/appointments/{id}/lines/` was **not** probed: it
needs an `appointment_id`, none has ever been observed on this credential, and the
read-only brief forbids sending an unobserved value. **Existence of `…/lines/` is
established from source only — NOT VERIFIED live.**

Because the gate answers 403 before any validation runs, **no 400 body was
obtainable for any v2 endpoint**. Consequence: for `channel`, `appointment_id`,
`scope`, `limit` and `bucket`, *which params the server requires* is
**NOT VERIFIED**. What is verified is which params the UI always sends. Spec them
as optional-but-documented rather than `required: true`, except the one real path
param on `…/lines/`.

### 1.5 Does v2 supersede v1? — **No. It runs alongside.** Three independent proofs.

**(a) Both routes are mounted and both sidebar links render.** §1.1. `new` → v1
`CreateShipment`; `new-2` → v2. Neither is a redirect (contrast `short-supply`,
which *is* a redirect: `{path:`short-supply`,element:(C,{to:`/platform/amazon/shipment-planning/record`,replace:!0})}`).

**(b) v1's `shipmentAPI` is intact and unshrunk.** The whole chunk is 7,796 bytes and
still exposes every v1 operation. Dumped in full (small file, dumped via bash, not
the `Read` tool):
```bash
python3 -c "import textwrap;s=open('shipmentAPI-Bm5uhztf.js').read();print(len(s));[print(l) for l in textwrap.wrap(s,160)]"
```

**(c) Decisive: v2 persists through v1.** `NewShipmentV2` imports v1's shipments API
(`import{c as ce}from"./shipmentAPI-Bm5uhztf.js"` — head of chunk) and its step-5
"Review & save" calls it:
```bash
python3 /tmp/.../g.py NewShipmentV2-niuH1T3p.js 'ce\.[a-zA-Z]' 200 200 12
```
→ `ce.createDraft({truck_size:…, truck_capacity_liters:…, loaded_items:…, not_loaded_items:…, appointment_id:…, destination_fc:…})`
  (= `POST /api/shipment/shipments/`), `ce.submit(S.id)`
  (= `POST /api/shipment/shipments/{id}/submit/`), and
  `ce.sendSwitchEmail(h.id,{pdfBlob,excelBlob,to,cc,subject,body})`.

**Migration verdict:** v2 is a *new front door onto the same house*. Publish the five
v2 GETs **in addition to** the 25 v0.2.0 shipment endpoints. Do **not** cite v2 as
justification for dropping any v1 endpoint. In particular keep
`shipment appointment-items` — v1's load computation is a GET, v2's is a POST, so v1's
is the only publishable one.

---

## 2. `/api/shipment/switching/` and `/api/shipment/v2/channels/`

### 2.1 `/api/shipment/v2/channels/`

Covered in §1.3 #1. It is step 1 of the v2 wizard: the list of Amazon *channels*
(the `is-${channel.toLowerCase()}` CSS variants and the `ns2-crumb--chan` breadcrumb
show it is a small closed set of named channels), each with its open book
(`open_po_count`, `open_units`, `open_liters`) and appointment outlook
(`upcoming_count`, `fc_count`, `next_appointment_time`). Nothing to do with
"switching" — the name collision is incidental. **No params.**

### 2.2 `/api/shipment/switching/` — the switching ledger

Definition (`shipmentAPI-Bm5uhztf.js`, exported twice, as `s.switching` on the
shipments API and `c.switching` on the po-items API):
```js
o=(e={})=>{let t=new URLSearchParams(Object.entries(e)
     .filter(([,e])=>e!=null&&e!==``)).toString();
   return i(`GET`,`/api/shipment/switching/${t?`?${t}`:``}`)}
```

**Which screen.** The only call site in the whole bundle:
```bash
cd /root/.handoff-runs/rescrape-all/scratch/ecom/bundle
grep -l 'switching' *.js
for f in $(grep -l 'switching(' *.js); do python3 /tmp/.../g.py $f '\.switching\(' 350 320 6; done
```
→ one hit, in **`Record-8P_EMA-e.js`**:
```js
if(typeof c.switching!=`function`)throw Error(`Switching is not available in this build.`);
let e=await c.switching({state:U===`all`?`all`:U, limit:200});
ue({ po:   Array.isArray(e?.po_switches)?e.po_switches:[],
     appt: Array.isArray(e?.appointment_switches)?e.appointment_switches:[],
     summary: e&&typeof e.summary==`object`&&e.summary||{} });
```
`Record-8P_EMA-e.js` is the lazy component `xr`, mounted at:
```bash
python3 /tmp/.../g.py index-Bdcm-waj.js 'jsx\)\(xr' 400 200 3
```
→ `{path:`record`,element:(xr)}` under `/platform/amazon/shipment-planning`
→ **`/platform/amazon/shipment-planning/record`**, sidebar label **"History"**
(nested under the "Data" nav group; the old `short-supply` route now 301s into it).

**Params (both observed at the call site):**

| Param | Type | Observed values | Note |
|---|---|---|---|
| `state` | string | `all`, `waiting`, `email_failed`, `verified`, `rejected` | tab list `ie=[`all`,`waiting`,`email_failed`,`verified`,`rejected`]` |
| `limit` | integer | `200` | the UI hard-codes 200 |

State vocabulary, from source (`python3 g.py Record-8P_EMA-e.js 'switch_state|`waiting`|`verified`' 300 300 10`):
```js
v={waiting:{label:`Waiting`},email_failed:{label:`Email failed`},
   verified:{label:`Verified`},rejected:{label:`Rejected`}},
ie=[`all`,`waiting`,`email_failed`,`verified`,`rejected`]
```
This is the same vocabulary already specced for `shipments.switch_state` in v0.2.0
(minus that endpoint's `any` sentinel) — consistent, and a cross-check that the
existing spec entry is right.

**Response shape:**
`{ po_switches: [ … ], appointment_switches: [ … ], summary: { shipments, waiting, email_failed, verified, rejected } }`
(the summary keys come from `[`waiting`,`email_failed`,`verified`,`rejected`].map(e=>R.summary?.[e])`
plus `R.summary?.shipments` rendered as *"N shipments in switching"*).

Row fields (from the row search predicate + renderer): `po_number`, `asin`,
`product_name`, `from_fc`, `to_fc`, `destination_fc`, `from_appointment_id`,
`to_appointment_id`, `appointment_id`, `shipment_id`, `switch_state`,
`email_sent_at`, `email_to`, `verified_at`, `verified_by`, `switch_kind`,
`units`, `cartons`, `liters`.

### 2.3 What "switching" means operationally

Straight from the screen's own copy
(`python3 g.py Record-8P_EMA-e.js 'Switching' 200 250 8`):

> **Switching** — *"Every PO this planner asked Amazon to move — what was asked, for
> which truck, and where the request stands."*

Two kinds, and the app names both:

| Kind | Source array | The app's own hint |
|---|---|---|
| **PO Switching** (`kind:'fc'`) | `po_switches` | *"PO sits at a sister FC and must be moved to this truck's FC"* |
| **Appointment Switching** (`kind:'appointment'`) | `appointment_switches` | *"PO is already at this FC but booked on another appointment and must be re-slotted"* |

**The workflow, end to end** (assembled from `shipmentAPI-*.js` + `NewShipmentV2` +
`ShipmentList` + `Record`):

1. While planning, the planner pulls a PO that is at the *wrong* FC or on the
   *wrong* appointment. The v2 save button changes label to
   *"Declare switch & save as draft"* (vs plain *"Save as draft"*).
2. Draft is saved via v1 `createDraft`.
3. A switching **request email** is raised to Amazon, with a PDF and an Excel
   attached: `POST /api/shipment/shipments/{id}/switch/email/` (multipart —
   `pdf`, `excel`, `to`, `cc`, `subject`, `body`). Shipment state → `switch_state:
   'waiting'`. **This POST is a write and is excluded.** *It is also a harvest blind
   spot* — it uses the raw fetch, not the `i()` helper, so no lens caught it; it is in
   neither harvest. Worth recording in the harvest known-blindspots note.
4. If sending fails, or the planner deliberately skips the email, state →
   `email_failed`, with the app telling them *"saved to Switching without an email —
   raise the request yourself, then verify it there."*
5. Someone later opens the shipment in **All Shipments** and runs the auto-check:
   **`GET /api/shipment/shipments/{id}/switch/verify/`** → `{results:[…]}`.
   (`ShipmentList-CbZ2S171.js`: `T.switchVerifyCheck(e.id).then(…)`, error string
   *"Auto-check failed."*, rendered as `r?.results||[]`.) **This GET is a read and
   should be published — see §4.**
6. They then accept or reject: `POST /api/shipment/shipments/{id}/switch/verify/`
   with `{action, note}` (`reject` requires a note: *"Add a note explaining why the
   switch is rejected."*). State → `verified` or `rejected`. **Write, excluded.**
7. The **History → Switching** panel (`GET /api/shipment/switching/`) is the ledger
   over all of the above; `GET /api/shipment/shipments/?switch_state=X`
   (`listSwitching`) is the same filter applied to the shipments list.

Live probe of the new read:
```bash
grep '"/api/shipment/switching"' /root/.handoff-runs/rescrape-all/scratch/ecom/probe/run1.jsonl
```
→ `403` + `{"detail":"You do not have access to the Amazon Shipment Planner."}`
Exists and is routed. Response shape **NOT VERIFIED live** — shape above is derived
from the app's own parsing and its fallback objects.

---

## 3. The four disappeared paths

```
/api/shipment/shipments/{id}/invoices
/api/shipment/shipments/{id}/invoices/{invoice}/file
/api/shipment/shipments/{id}/po-documents
/api/shipment/shipments/{id}/po-documents/{document}
```

### 3.1 First, a methodological control — is "403 = exists" actually sound here?

The whole shipment module answers 403, so it matters enormously whether that 403
comes from a *per-view* permission (in which case a 403 proves the URL resolved, i.e.
the endpoint exists) or from a *prefix-level* middleware on `/api/shipment/` (in
which case 403 would be returned for anything under the prefix and would prove
nothing). This had not been controlled for. It is now:

```bash
TOK=$(cat /root/.handoff-runs/rescrape-all/scratch/.ecom_token)
for p in "/api/shipment/v2/channels" "/api/shipment/zzz-control-not-a-real-path/" \
         "/api/shipment/v2/zzz-control/" "/api/auth/feature-flags"; do
  curl -s -o /tmp/b.txt -w '%{http_code}' -X GET \
    -H "Authorization: Bearer $TOK" -H 'Accept: application/json' "https://ecom.jivo.in$p"
  echo " $p : $(head -c 140 /tmp/b.txt | tr -d '\n')"
done
```
→
```
301  /api/shipment/v2/channels                  (no trailing slash → APPEND_SLASH redirect)
404  /api/shipment/zzz-control-not-a-real-path/ Django plain-HTML "<h1>Not Found</h1>"
404  /api/shipment/v2/zzz-control/              Django plain-HTML "<h1>Not Found</h1>"
404  /api/auth/feature-flags                    Django plain-HTML "<h1>Not Found</h1>"
```

Two findings, both important:

- **The 403 is per-view, not a prefix gate.** An unrouted path under
  `/api/shipment/` — including under `/api/shipment/v2/` — returns Django's
  URL-resolution 404, *not* 403. So BRIEF-SHARED.md's "a 403 proves the endpoint
  EXISTS and is routed" is now **empirically controlled and confirmed**, and the
  §1.4 403s on the v2 endpoints are genuine existence proofs.
- **Trailing slashes are mandatory.** Slashless gets a 301, not a 200/403. The spec
  must carry the exact trailing slashes the app builds. (This also explains why
  `probe/run1.jsonl`, which recorded slashless paths, still shows 403s — it followed
  the redirect.)

### 3.2 They were already gone at the last harvest — this is not new drift

```bash
python3 -c "
import json;d=json.load(open('/root/jivo-cli/ecom-cli/research/harvest/reconciled.json'))
[print(k, d[k]['chunks'], d[k]['raw_paths'], d[k]['decision'], '|', d[k]['why'])
 for k in d if 'invoices' in k or 'po-documents' in k]"
```
→ all four:
```
chunks: []   raw_paths: []   decision: PROBE_SKIP_PARAM
why: "shipped in v0.1.0 but the current client no longer calls it - probe before assuming dead"
```
and `"old_command": "shipment shipment-invoices"` etc.

```bash
python3 -c "
import json;d=json.load(open('/root/jivo-cli/ecom-cli/research/evidence/probe-verdicts.json'))
[print(k, d[k]['status'], d[k]['attempts']) for k in d if 'invoices' in k or 'po-documents' in k]"
```
→ all four: `UNPROBED  []`

So: **zero bundle evidence on 2026-08-03, zero probe attempts on 2026-08-03, and yet
published in v0.2.0 anyway.** They are v0.1.0 heirlooms, carried forward twice. Listing
them under "GONE from the bundle this run" in the drift table is misleading — they did
not go anywhere this run. The prior study
`~/jivo-cli/ecom-cli/research/studies/study-shipment.md` already labelled all four
`UNPROBED-orphan` (lines 166-169) and flagged them as at *"a real risk of being
silently dead"* (line 400) — that judgement stands and is reinforced.

A corroborating signal, independent of the bundle: in `spec.yaml` these four are the
**only** shipment paths written **without** a trailing slash, in a module where every
other path has one and where the server 301s slashless URLs (§3.1). That is the
fingerprint of hand-authored or differently-sourced paths, not of harvested ones —
so their *exact spelling* is suspect even if the feature exists.

### 3.3 Were they replaced? — **No. Nothing replaced them.**

Whole-bundle sweep, all 158 chunks:
```bash
cd /root/.handoff-runs/rescrape-all/scratch/ecom/bundle
grep -l 'po-document' *.js   ; # NONE
grep -l 'po_document' *.js   ; # NONE
grep -l '/invoices'   *.js   ; # NONE
grep -l 'attachment'  *.js   ; # vendor-pdf-VfVkerq_.js  (third-party PDF lib, unrelated)
grep -l 'switch/email' *.js  ; # shipmentAPI-Bm5uhztf.js
grep -l 'PO document' *.js   ; # shipmentAPI-Bm5uhztf.js  (error message only, see below)
```
Plus a targeted check of the three chunks the brief named, all clean:
```bash
grep -o 'po_pdf\|po_documents\|poDocument\|pdfKey\|pdf_url\|document_url' \
  CreateShipment-kUDJIfZs.js NewShipmentV2-niuH1T3p.js ShipmentDetail-C_zjX7--.js ShipmentList-CbZ2S171.js
# (no output)
```
And the one chunk whose *name* looked like a candidate is not one — `InvoicedTag-CBRbJU4Q.js`
(1,014 B) is a pure display badge about **SAP** invoicing state on PO lines
(*"Already invoiced in SAP but not dispatched…"*). It makes **no API calls**
(`grep -o '/api/…' InvoicedTag-CBRbJU4Q.js` → nothing) and is unrelated to shipment
invoice documents.

So there is no successor endpoint. The UI simply **stopped having the feature**: no
list, no download, and no upload path for shipment invoices or PO documents exists
anywhere in the current SPA.

**But the server-side concept is demonstrably still alive.** `shipmentAPI-Bm5uhztf.js`
still carries a dedicated error formatter for a PO-document validation the server
performs on draft creation:
```js
if(Array.isArray(n.missing_pos)&&n.missing_pos.length){
  … return `${n.error||`A PO document (PDF) is required for every PO.`} Missing: ${e}.` }
```
i.e. `POST /api/shipment/shipments/` can still fail with `{error, missing_pos:[…]}`
because PO PDFs are missing. The documents therefore still exist as server-side
objects attached to POs; only the *browse and download* surface left the SPA. Which
makes "these endpoints are dead" distinctly *less* likely than bundle-absence alone
would suggest.

### 3.4 What could and could not be established — stated exactly

**Established:**
- The four paths are referenced by **no chunk** in the 2026-08-22 bundle (158/158 swept).
- They were referenced by no chunk in the 2026-08-03 harvest either, and were never
  probed. They entered v0.2.0 with no evidence of any kind.
- **Nothing in the current bundle replaced them.** There is no successor endpoint for
  shipment invoices or PO documents.
- The server still enforces a per-PO PO-document (PDF) requirement, proven by the
  live `missing_pos` error formatter — so the underlying objects are not gone.
- The 403 on this module is per-view and sits *behind* URL resolution (§3.1), so a
  single GET would definitively separate "route exists" (403 JSON) from "route gone"
  (plain-HTML 404). Neither the pk value nor the DB is ever reached: DRF's permission
  class denies before `get_object()`.

**NOT ESTABLISHED — and the reason:**
- **Whether the server still routes any of the four.** Settling it requires putting
  *some* value in the `{id}` path segment. No shipment id has ever been observed on
  this credential (`probe/observed-ids.json` contains no shipment ids, and cannot —
  every listing endpoint 403s). BRIEF-SHARED.md forbids sending an unobserved
  parameter value, and that rule was obeyed. **So these four remain
  routing-unverified, exactly as they were in v0.1.0 and v0.2.0.**
- **Their response shapes and whether they return JSON or a file.** Unknown. The
  v0.1.0 descriptions (*"Download an invoice file for a shipment"*) suggest the two
  leaf paths are file downloads, not JSON — the prior study's "Trap 10". Unverified.
- **Whether the paths are even spelled correctly** (the missing trailing slashes, §3.2).

**A note on the brief's premise.** The brief states these are *"403-gated so we cannot
probe them"*. That premise is not right, and the difference matters: the gate is
per-view and sits behind URL resolution, so a probe **would** be decisive. The blocker
is not the 403 — it is the unobserved-id rule. One authorised GET per path would close
this gap permanently:
```bash
# NOT RUN — requires explicit authorisation to send an unobserved path segment.
# 403 JSON  => route exists, keep publishing (still shape-unverified)
# HTML 404  => route is gone, drop with evidence
TOK=$(cat /root/.handoff-runs/rescrape-all/scratch/.ecom_token)
for p in "/api/shipment/shipments/1/invoices/" "/api/shipment/shipments/1/po-documents/"; do
  curl -s -o /tmp/b.txt -w '%{http_code} ' -X GET -H "Authorization: Bearer $TOK" \
    "https://ecom.jivo.in$p"; echo "$p $(head -c 100 /tmp/b.txt)"
done
```
Recommend the run owner authorise it. Until then, the honest disposition is
**KEEP, relabelled**: retain the four commands (Rule 6 — they have shipped names, and
they cannot be shown dead) with help text along the lines of *"not called by the
current app; existence and response shape unverified; may return a file, not JSON"*
— which is what `study-shipment.md` already recommended in 2026-08 and what this run
found no reason to change.

---

## 4. Proposed command names

Read from the shipped spec so the style is matched, not invented:
```bash
python3 -c "
import yaml;d=yaml.safe_load(open('/root/jivo-cli/ecom-cli/spec.yaml'))
eps=d['resources']['shipment']['endpoints']
[print(f'{k:34s} {v.get(\"method\",\"GET\"):5s} {v[\"path\"]}') for k,v in eps.items()]"
```

**Observed conventions in the shipped `shipment` resource (25 endpoints):**
- Keys are lower-kebab and **derived from the path's distinguishing segments**, not
  from the JS helper names (`getDates` → `appointment-dates`).
- Collection-level sub-resources of `shipments/` take the **`shipments-`** prefix:
  `shipments-stats`, `shipments-deletion-log`, `shipments-pending-approvals`,
  `shipments-doh-auto-fill`.
- Per-instance sub-resources of `shipments/{id}/` take the **singular `shipment-`**
  prefix: `shipment-invoices`, `shipment-invoice-file`, `shipment-po-documents`,
  `shipment-po-document`.
- Sub-resources of `appointments/` take **`appointment-`** (singular):
  `appointment-dates`, `appointment-items`, `appointment-families`,
  `appointment-extra-pos`.
- Top-level nouns keep the bare noun: `record`, `inventory`, `asin-catalog`,
  `po-items`, `fc-switch-group`.

**Proposed names — six new endpoints. Nothing existing is renamed (Rule 6).**

| # | Proposed key | Verb | Path | Params (all observed) |
|---|---|---|---|---|
| 1 | `switching` | GET | `/api/shipment/switching/` | `state` ∈ {all, waiting, email_failed, verified, rejected}; `limit` int (UI: 200) |
| 2 | `v2-channels` | GET | `/api/shipment/v2/channels/` | none |
| 3 | `v2-appointments` | GET | `/api/shipment/v2/appointments/` | `channel`; `scope` ∈ {upcoming, past, all}; `limit` int (UI: 300) |
| 4 | `v2-appointment-lines` | GET | `/api/shipment/v2/appointments/{appointment_id}/lines/` | `appointment_id` path, **required** |
| 5 | `v2-pos` | GET | `/api/shipment/v2/pos/` | `channel`; `appointment_id`; `bucket` ∈ {with_stock, without_stock, "with_stock,without_stock", none} |
| 6 | `v2-fill-options` | GET | `/api/shipment/v2/fill/options/` | `channel`; `appointment_id` |

Plus one **recovery** of a read that v0.2.0 wrongly excluded:

| # | Proposed key | Verb | Path | Params |
|---|---|---|---|---|
| 7 | `shipment-switch-verify` | GET | `/api/shipment/shipments/{id}/switch/verify/` | `id` path, **required** |

**Naming rationale:**
- `switching` — bare top-level noun, exactly like the sibling `record` and
  `inventory`. It is not a sub-resource of `shipments/`, so no prefix.
- `v2-*` — `v2` is a literal path segment, so a path-derived key must carry it; and it
  is *needed* for disambiguation, because `appointments` and `all-appointments` are
  both already taken by v1. It also keeps the pair legible in `--help` and in tab
  completion (`shipment v2-<TAB>` lists exactly the New Shipment 2.0 surface), and it
  telegraphs to an operator that these read the *new* wizard's data, not v1's.
- `v2-appointment-lines` — singular `appointment-` for a per-instance sub-resource,
  matching `appointment-items` / `appointment-families`.
- `v2-fill-options` — the path is `fill/options/`; joined with a hyphen the same way
  `shipments/doh-auto-fill/` became `shipments-doh-auto-fill`.
- `shipment-switch-verify` — singular `shipment-` prefix for a `shipments/{id}/…`
  sub-resource, matching `shipment-invoices` / `shipment-po-document`.

**Spec cautions to carry into the generator:**
- Keep the **trailing slash** on every path above (§3.1: slashless → 301).
- Mark `channel`, `appointment_id`, `scope`, `limit`, `bucket` **not** `required` —
  the UI always sends them but the 403 gate fires before validation, so
  server-side required-ness is **NOT VERIFIED**. Only the two path params are
  provably required.
- Add to each description: *value for `channel` must come from
  `shipment v2-channels`; value for `appointment_id` must come from
  `shipment v2-appointments`; do not synthesise one* — mirroring the existing
  `appointments.date` description's wording.
- Response shapes for all seven are **NOT VERIFIED live** (uniform 403 on this
  credential); they are derived from the app's own response parsing and its
  fallback objects, which is the strongest evidence obtainable here.
- Resource description already says *"Requires the `amazon.shipment_planning.view`
  permission; returns 403 without it"* — confirmed still exact
  (`grep -ho 'amazon\.shipment[a-z_.]*' bundle/*.js | sort -u`) and it covers the
  v2 endpoints too, since the `new-2` route is gated by the same
  `L.shipmentPlanning` as the rest of the subtree.

**Excluded (writes), recorded for the migration doc only:**
`POST /api/shipment/v2/fill/`,
`POST /api/shipment/shipments/{id}/switch/verify/`,
`POST /api/shipment/shipments/{id}/switch/email/` (multipart; **absent from both
harvests** — a blind spot, because it bypasses the `i()` helper and calls the raw
fetch directly).

---

## Appendix — corrections this study makes to run inputs

| Input | Says | Should say |
|---|---|---|
| `BRIEF-SHARED.md` helper table | `me(\`VERB\`, path, body, params)` | `me(VERB, path, body, {signal})` — 4th arg is request options, **not** params. Query params reach the wire only via `R(e)` baked into the path. |
| Drift list | `GET /api/shipment/v2/appointments/{id}` | `GET /api/shipment/v2/appointments/` — collection + query string |
| Drift list | `GET /api/shipment/v2/pos/{id}` | `GET /api/shipment/v2/pos/` — collection + query string |
| Drift list | `GET /api/shipment/v2/fill/options/{id}` | `GET /api/shipment/v2/fill/options/` — collection + query string |
| Drift list | 4 document paths "GONE from the bundle" (implying this run) | Already absent on 2026-08-03 with `chunks: []`; v0.1.0 heirlooms, never probed, never evidenced |
| Brief, §3 framing | the 4 paths are "403-gated so we cannot probe them" | The gate is per-view and sits *behind* URL resolution; a probe **would** be decisive. The real blocker is the unobserved-id rule. |
| `harvest/harvest.json` | 3 v2 paths flagged `has_param: true` | `has_param: false` — the `${…}` is `R(e)`, a query-string builder |
| v0.2.0 spec | `switch/verify` excluded as `EXCLUDE_ACTION` | The GET half (`switchVerifyCheck`) is a publishable read — recover it |
| v0.2.0 spec | 4 document paths written without trailing slashes | Server 301s slashless URLs; spelling is suspect independent of existence |
