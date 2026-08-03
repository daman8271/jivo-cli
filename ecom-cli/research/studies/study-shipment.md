# Domain study — `shipment` (Amazon Shipment Planner)

Bundle: `study/bundles/shipment.json` · 34 endpoints · probe verdicts: **17 GATED (403), 17 UNPROBED**
Evidence also read: the SPA's own `shipmentAPI-DKVOXJWL.js` and the nine page chunks that
call it, plus the shipped `ecom-cli/spec.yaml` v0.1.0.

---

## ⚠ READ THIS BEFORE USING ANYTHING BELOW

**This domain could not be functionally verified from this session. Not one shipment
endpoint returned a payload.**

Every single one of the 17 endpoints that could be probed returned **HTTP 403** with the
body:

```json
{"detail":"You do not have access to the Amazon Shipment Planner."}
```

The gate is one permission string, read verbatim out of the SPA's own permission map
(`bundle/permissions-Cn6rO7mi.js`):

```js
var e = { shipmentPlanning: `amazon.shipment_planning.view`, ... };
function t(e,t){ if(e.is_superuser===true) return true;
                 let n = e.permissions; return n.includes(`*`) || n.includes(t) || <wildcard match> }
```

Our probing credential (`dp605702@jivo.in`, from `me.json`) holds **144 permissions**
including `view_shipment`, `view_shipmentitem`, `view_shipmentauditlog`, `dispatch.view`
and `admin.dispatch.manage` — but **not** `amazon.shipment_planning.view`, and
`is_superuser` is `false`, so neither bypass applies.

Three consequences, and they govern everything in this file:

1. **A 403 is proof the endpoint exists and is routed.** It is the opposite of proof of
   death. Django/DRF ran the URL resolver, matched a view, instantiated it, and then the
   permission class refused. All 17 GETs here are published and alive. 22 of the 26
   endpoints I recommend publishing are already in the shipped v0.1.0 spec and must stay.

2. **I have no response payloads for this domain — zero bytes of real data.** Every
   `live_response` in the bundle is `null`. Every response shape below is therefore
   marked **UNVERIFIED**, and where I say anything about a field I say exactly where it
   came from: the SPA's client code reading a key off the response (inferred, good
   evidence, not proof) or nothing at all (in which case I say "not observed").
   **Do not let a spec author turn any shape in this file into a confident
   `response_path`.** The safest spec entry for this whole domain is `response: {type: object}`
   with no `response_path`, exactly as v0.1.0 already has it.

3. **Parameter names below are trustworthy where I quote them**, because I read them out
   of the SPA bundle's literal URL templates and `URLSearchParams` builders — that is
   source, not a guess. Enum *values* are trustworthy only where I quote a literal from
   the same source. Anything else says "not observed".

### What a human with `amazon.shipment_planning.view` must run to verify this domain

Give this list to whoever holds Shipment Planner access (Prabhu's team / the Amazon
dispatch operator). It uses the **already-shipped v0.1.0 CLI binary**, so it can be run
today, before any regeneration. Every command below is a GET.

```bash
cd ecom-cli
export JIVO_ECOM_TOKEN=<their token>          # or: ./jivo-ecom-pp-cli auth login

# 0. confirm the gate is actually open for them
./jivo-ecom-pp-cli account me --json | grep -o 'amazon.shipment_planning.view'
#    -> must print the permission. If it prints nothing, stop; they are gated too.

# 1. the eight no-parameter endpoints — these settle 8 of 17 shapes in one pass
for c in appointment-dates appointment-commits asin-catalog po-shipment-lookup \
         po-short-supply shipments-stats shipments-pending-approvals shipments-deletion-log; do
  echo "=== $c"; ./jivo-ecom-pp-cli shipment $c --json | head -c 2000; echo
done

# 2. the list endpoints the SPA always calls with a filter
./jivo-ecom-pp-cli shipment all-appointments --json | head -c 2000    # SPA sends no_paginate=true
./jivo-ecom-pp-cli shipment po-items --json          | head -c 2000    # SPA sends no_paginate=true&po_status=PENDING
./jivo-ecom-pp-cli shipment record --json            | head -c 2000    # SPA sends status=<one of the enum below>
./jivo-ecom-pp-cli shipment shipments --json         | head -c 2000    # SPA sends status= / switch_state=
./jivo-ecom-pp-cli shipment inventory --json         | head -c 2000    # SPA sends warehouse=GP-FGM etc.
./jivo-ecom-pp-cli shipment shipments-doh-auto-fill --json | head -c 2000

# 3. the id-parameterised ones. Take a real appointment id from step 2's
#    all-appointments output and a real shipment id from shipments; DO NOT invent ids.
APPT=<appointment_id from all-appointments>
SHIP=<id from shipments>
./jivo-ecom-pp-cli shipment appointment-extra-pos "$APPT" --json | head -c 2000
./jivo-ecom-pp-cli shipment appointment-items     "$APPT" --json | head -c 2000
./jivo-ecom-pp-cli shipment shipment              "$SHIP" --json | head -c 2000

# 4. the four "shipped but the current UI no longer calls them" endpoints — the whole
#    point of this step is to learn whether they 200 or 404. Either answer is useful.
./jivo-ecom-pp-cli shipment shipment-invoices     "$SHIP" --json ; echo "exit=$?"
./jivo-ecom-pp-cli shipment shipment-po-documents "$SHIP" --json ; echo "exit=$?"
#    then, only if the two above return a list with ids in it:
./jivo-ecom-pp-cli shipment shipment-invoice-file "$SHIP" <invoice_id_from_above>  ; echo "exit=$?"
./jivo-ecom-pp-cli shipment shipment-po-document  "$SHIP" <document_id_from_above> ; echo "exit=$?"

# 5. the three endpoints that are NOT yet in the CLI (raw curl until they are printed)
B=https://ecom.jivo.in ; H="Authorization: Bearer $JIVO_ECOM_TOKEN"
curl -s -H "$H" "$B/api/shipment/appointments/$APPT/families/"      | head -c 1500; echo
curl -s -H "$H" "$B/api/shipment/fc-switch-group/?fc=DED3"          | head -c 1500; echo
curl -s -H "$H" "$B/api/shipment/po-appointments/?pos=<a,real,po,list>" | head -c 1500; echo
```

**Nothing in that list writes.** Every line is a GET. It is safe to hand to an operator.

What comes back should be pasted into a follow-up so the spec's response shapes can be
filled in from data instead of from the client code.

---

## 1. What this domain is, in operator language

This is the tool that decides **what physically goes on the next truck to Amazon.**

Amazon books JIVO a delivery slot ("appointment") at one of its fulfilment centres, against
a set of purchase orders. Someone in the Amazon e-commerce / dispatch team has to work out
which of those POs and which SKUs can actually be loaded — is there stock in the Gupta
Godown, does it fit in a 10- or 15-tonne truck, which items are running out at Amazon's end
and should be prioritised — then save that as a draft shipment, get it approved, and
dispatch it. This domain is every screen in that flow: the appointment calendar, the PO
list, the stock view, the auto-planner, the draft/approval queue, the dispatch record, and
the "switching" flow used when Amazon wants stock redirected to a sister FC.

Who opens it: the Amazon dispatch operator and whoever approves shipments. Accounts will
occasionally want `shipments-stats` or `record` to reconcile what was actually dispatched
against invoices. **It is Amazon-only** — nothing here covers Blinkit, Zepto, Swiggy,
BigBasket, Flipkart, JioMart, Citymall or Zomato.

---

## 2. Endpoint table

Command names in **bold** are the shipped v0.1.0 names — **contractual, do not rename.**
Three rows have no shipped name and get a new one in the existing style.

Status key: `GATED` = 403, proven routed, payload unseen. `UNPROBED-param` = never probed
because it needs a real id and inventing one is forbidden. `UNPROBED-orphan` = shipped in
v0.1.0, no longer called by the current SPA, and not probeable from here.

| command | path (emit the trailing slash — see Trap 1) | what an operator gets | required params | status |
|---|---|---|---|---|
| **shipment appointment-dates** | `/api/shipment/appointments/dates/` | The calendar of dates that have Amazon appointments, with per-date counts. Client reads `dates`, `counts`, `cancelled`, `channels`, `planned` off the response. | none | GATED |
| **shipment appointments** | `/api/shipment/appointments/?date=` | The appointments booked on one date. Client treats the response as an **array** and reads `appointment_id`, `destination_fc`, `po_count`, `is_primary`, `amazon_unit_count`, `amazon_carton_count`. | `date` (**required**, see Trap 2) | GATED |
| **shipment all-appointments** | `/api/shipment/all-appointments/?…` | The full appointment register, not scoped to one date — the list page's data. SPA always sends `no_paginate=true`. | none | GATED |
| **shipment appointment-commits** | `/api/shipment/appointment-commits/` | What JIVO has committed to Amazon per appointment (the units/cartons promised). Feeds the "commit caps" the planner will not exceed. | none | GATED |
| **shipment appointment-extra-pos** | `/api/shipment/appointments/{id}/extra-pos/` | Extra POs that could be added onto this appointment's truck. Client reads `extra_pos`, `switch_pos`, `channel`. | `id` (appointment id) | UNPROBED-param |
| `shipment appointment-families` *(new)* | `/api/shipment/appointments/{id}/families/` | The product families (and their ASINs) on this appointment, used to focus a plan on one family. Client reads `families[]`, each with `family` and `asins[] {asin, item, item_head}`. | `id` (appointment id) | UNPROBED-param |
| **shipment appointment-items** | `/api/shipment/appointments/{id}/items/?…` | **The auto-planner itself.** Given an appointment and a truck size, returns the line-by-line load plan. This is the most parameter-heavy endpoint in the CLI — 12 observed query params, listed in §4. | `id` + `truck_size` (see Trap 3) | UNPROBED-param |
| **shipment asin-catalog** | `/api/shipment/asin-catalog/` | The ASIN reference list the planner matches against. Client reads `dashboards.asin[]` — note the odd nesting. | none | GATED |
| **shipment inventory** | `/api/shipment/inventory/?warehouse=` | Live SAP warehouse stock for the planner. Client reads `results[]` (rows with `WhsCode`, `ItemCode`, `ItemName` — SAP column names, not the app's), plus `summary` and `warehouses[]`. | none; `warehouse` optional (see Trap 4) | GATED |
| **shipment po-items** | `/api/shipment/po-items/?…` | Every Amazon PO line available to ship — the PO list screen. Client reads `results` or a bare array. SPA sends `no_paginate=true` and `po_status=PENDING`. | none | GATED |
| **shipment po-shipment-lookup** | `/api/shipment/po-shipment-lookup/` | A lookup of what is already committed per PO/FC, so the planner does not double-promise the same stock. Client uses it as a **dictionary keyed by an FC key**, not a list. | none | GATED |
| **shipment po-short-supply** | `/api/shipment/po-short-supply/` | POs that were short-supplied. Client's error fallback is `{count: 0, total_short_units: 0}`, which suggests those two fields — see Trap 9. | none | GATED |
| `shipment po-appointments` *(new)* | `/api/shipment/po-appointments/?pos=` | Given a comma-separated list of PO numbers, which appointments they sit on. Client reads `appointments` and treats it as an **object/map**, not a list. | `pos` (comma-joined PO numbers) | GATED |
| `shipment fc-switch-group` *(new)* | `/api/shipment/fc-switch-group/?fc=` | For one fulfilment centre, the sister FCs stock may legally be switched to, and that FC's channel. Client reads `channel` and `fcs[]`. | `fc` (an FC code) | GATED |
| **shipment shipments** | `/api/shipment/shipments/?status=` or `?switch_state=` | The shipment list — drafts, pending approval, approved, dispatched. Client treats the response as an **array**. | none; `status` / `switch_state` optional (enums in §4) | GATED |
| **shipment shipment** | `/api/shipment/shipments/{id}/` | One shipment in full. **This same path also serves PATCH and DELETE in the SPA — publish GET only, see Trap 7.** | `id` (shipment id) | UNPROBED-param |
| **shipment shipments-stats** | `/api/shipment/shipments/stats/` | Headline counts for the shipment dashboard. Client reads it as a plain object and falls back to `{}`. | none | GATED |
| **shipment shipments-pending-approvals** | `/api/shipment/shipments/pending-approvals/` | The approval queue. Client treats the response as an **array**. | none | GATED |
| **shipment shipments-deletion-log** | `/api/shipment/shipments/deletion-log/?limit=` | Who deleted which draft shipment and when — the audit trail behind the "Deleted" tab. | none; `limit` optional (int) | GATED |
| **shipment shipments-doh-auto-fill** | `/api/shipment/shipments/doh-auto-fill/?…` | The **DOH-driven** planner: instead of planning against one appointment, it fills a truck with whatever Amazon is closest to running out of. Client reads `commit_caps` (map of appointment id → `{units, cartons}`) and `appointments`. | none, but the SPA always sends `truck_size` (see §4) | GATED |
| **shipment record** | `/api/shipment/record/?status=` | The dispatch record — what actually went out, per shipment, with per-line `planned_qty`, `case_pack`, `planned_liters` and a `not_loaded` flag. Client reads `results[]`. | none; `status` optional (enum in §4) | GATED |
| **shipment shipment-invoices** | `/api/shipment/shipments/{id}/invoices` | Invoices attached to a shipment. **Shipped in v0.1.0; the current SPA no longer calls it; unverifiable from here.** | `id` | UNPROBED-orphan |
| **shipment shipment-invoice-file** | `/api/shipment/shipments/{id}/invoices/{invoice}/file` | Download one invoice file. Same orphan caveat. Likely returns a **file, not JSON** — see Trap 10. | `id`, `invoice` | UNPROBED-orphan |
| **shipment shipment-po-documents** | `/api/shipment/shipments/{id}/po-documents` | PO documents (the PDFs Amazon requires per PO) attached to a shipment. Same orphan caveat. | `id` | UNPROBED-orphan |
| **shipment shipment-po-document** | `/api/shipment/shipments/{id}/po-documents/{document}` | One PO document. Same orphan caveat; likely a file. | `id`, `document` | UNPROBED-orphan |

**Count: 25 endpoints recommended for publication** — 22 carried forward from v0.1.0 unchanged,
plus 3 new GETs the current SPA calls that v0.1.0 missed. 9 excluded (§5).

---

## 3. Traps

Each trap says where the evidence came from. "SPA source" means I read the literal in the
minified bundle — that is source, not inference. "Inferred" means I reasoned from client
code and could not confirm against a payload.

### Trap 1 — the whole `/api/shipment/` family is trailing-slash; the rest of the app is not. This breaks exact-match denylists.

**Evidence (SPA source, `shipmentAPI-DKVOXJWL.js`):** every shipment template ends in `/`
before any query string —

```
/api/shipment/appointment-commits/        /api/shipment/shipments/${e}/approve/
/api/shipment/appointments/dates/         /api/shipment/shipments/${e}/items/${t}/
/api/shipment/appointments/?date=${e}     /api/shipment/shipments/deletion-log/${e?`?limit=${e}`:``}
```

Meanwhile in the *rest* of this app there is no trailing slash at all: `/api/auth/me`,
`/api/upload/ads-master`, `/api/notifications/${e}/mark-read`, `/api/uploads/${e}`. The split
is per Django app — the shipment app is on DRF routers, the rest is on plain paths.

**Why it matters, and it matters a lot:** the bundle's *normalised* paths drop the trailing
slash (`/api/shipment/shipments/{}/approve`), and that is the form a denylist will be
written in. A denylist entry `/api/shipment/shipments/{id}/approve` **does not exact-match**
the literal the app uses, `/api/shipment/shipments/12/approve/`. If the CLI's write-blocker
matches on exact path strings, it will let the slash-terminated form through. **Any
denylist for this domain must be slash-insensitive, or must carry both forms.**

Second-order: my probe sent the *no-slash* form and got 403, not 404 — so the request
reached the view. But `urllib` follows redirects, so I cannot tell whether the no-slash form
resolves directly or via a Django `APPEND_SLASH` 301. **Emit the trailing slash, as the SPA
does.** (Confidence the slash form works: high — it is what the running app uses.
Confidence about the no-slash form: unknown. Note that an `APPEND_SLASH` redirect silently
drops a POST body, which is one more reason to match the SPA exactly.)

### Trap 2 — `date` on `shipment appointments` looks optional and is not.

**Evidence (SPA source):** the template is `` `/api/shipment/appointments/?date=${e}` `` — the
query string is **not** conditional. Every other optional param in this file is written as
`` ${e?`?x=${e}`:``} ``; this one is not. The SPA has no code path that calls it without a
date. Treat `date` as required. Its format is not observed (the calendar builds it from
`year`/`month`/`day` parts, but I did not extract the join). **Do not guess a date format —
run the verification list above and read one back from `appointment-dates`.**

### Trap 3 — `shipment appointment-items` is not a listing, it is a planning *run*, and its 12 parameters change the answer.

**Evidence (SPA source, verbatim `URLSearchParams` builder):**

```js
getItems:(e,t,n,r=null,a={})=>{ let o=new URLSearchParams({truck_size:t});
  n && o.set(`truck_capacity_liters`,String(n));
  r && (o.set(`priority_premium_pct`,…), o.set(`priority_commodity_pct`,…), o.set(`priority_other_pct`,…));
  a.strict && o.set(`priority_strict`,`1`);
  o.set(`maximize_fill`, a.maximizeFill===false?`0`:`1`);
  a.respectStock===false && o.set(`respect_stock`,`0`);
  a.extraAppointmentIds?.length && o.set(`appointment_ids`, …join(`,`));
  a.selectedPos?.length && o.set(`selected_pos`, …join(`,`));
  a.productFamily && (o.set(`product_family`,…), o.set(`family_asins`, …join(`,`)));
  o.set(`commit_caps_json`, JSON.stringify({<apptId>:{units,cartons}}));
  return i(`GET`,`/api/shipment/appointments/${e}/items/?${o.toString()}`) }
```

`truck_size` is **always** set — it is the one unconditional param, and it is what decides
how much fits. An operator who runs this command bare will either get an error or an
implicit default they did not choose, and will read the result as "this is what's on the
appointment" when it is really "this is what one particular truck configuration would
load". Two operators running the same appointment with different `truck_size` get different
line lists, and neither is wrong. **Present this command as "plan a truck", never as "list
the items on an appointment".** `maximize_fill` defaults to `1` in the SPA; `respect_stock`
defaults on (only ever set to `0` explicitly) — meaning by default the plan will not
promise stock that is not there.

### Trap 4 — `warehouse` on `shipment inventory` is a SAP warehouse code, and there are only four. Omitting it means ALL, not "the default".

**Evidence (SPA source, `InventoryView-Bw0D5ewQ.js`), verbatim map:**

```js
b={"GP-FGM":`Gupta Godown Finished Goods`,
   "BH-FGM":`Jivo Mart · Sonipat`,
   "GP-FG" :`Gupta Godown Basement Finished Godown`,
   "BH-EC" :`Bhakharpur Finished E-Commerce`}
```

and the component signature `w({warehouse: e = 'ALL', …})` with
`s = String(e).toUpperCase() === 'ALL'`. So `ALL` is a real accepted value and the
component's own default. `GP-FGM` is additionally hardcoded elsewhere as the Amazon
planning warehouse (`u = 'GP-FGM'` in `shipmentAPI`, and tooltips read *"Available to plan
at GP-FGM"*). These are the observed enum; there may be more warehouses in SAP that the SPA
does not name. **Note "BH-FGM = Jivo Mart · Sonipat" — that is a different SAP company
(Mart, not Oil). Do not add stock across those two codes and call it one number.**

### Trap 5 — "10 tonnes" means 10,000 **litres**, and the app converts litres to tonnes at 1:1. For oil that is wrong by ~9%.

**Evidence (SPA source, two independent places):**

```js
// CreateShipment: the truck picker
at=[{value:`10_ton`,label:`10 Tonnes`,capacity:1e4},
    {value:`15_ton`,label:`15 Tonnes`,capacity:15e3},
    {value:`custom`,…}]                       // capacity is fed to truck_capacity_liters

// shipmentAPI: the label helper
function n(e,t){ let n=Number(t||0); if(n>0){ let e=n/1e3; return `${…} ton` } … }

// Record page: the dispatch summary
tonnes = items.reduce((a,t)=> a + Number(t.planned_liters||0)/1e3, 0).toFixed(2)
```

Every one of these divides **litres by 1,000 and prints "ton"**. That is only true if
1 litre = 1 kg. JIVO's own settled rule is **litres × 0.91 for oils**. So a "15 Tonnes"
truck is a 15,000-litre truck ≈ **13.65 tonnes** of edible oil, and any tonnage this domain
reports is **over-stated by roughly 9-10% for oil lines**. Also note the truck picker only
ever offers `10_ton` and `15_ton` in the UI (`at.filter(e => e.value !== 'custom')`);
`custom` exists but is reached from a separate "manual capacity in litres" input with a
minimum of 100 L. **When reporting anything from this domain in tonnes, say "litres ÷ 1000
as the app computes it" and give the litre figure too.**

### Trap 6 — quantities here are **pieces (single bottles)**, and cartons are derived, not stored.

**Evidence (SPA source, `Record-uhJVTCfL.js`):**

```js
units   = Σ planned_qty
cartons = Σ planned_qty / max(case_pack, 1)
```

`planned_qty` is the piece count; the carton count is computed on the fly by dividing by
`case_pack`. This lines up exactly with the standing JIVO correction (**C-0001**: quantities
are in PIECES, not cartons; the "20 PCS" in an item name is carton configuration only).
`commit_caps_json` carries **both** (`{units, cartons}`) which is precisely where someone
will mix them up. **State the unit on every quantity this domain returns.** Fields observed
by name: `planned_qty` (pieces), `case_pack` (pieces per carton), `planned_liters` (litres),
`amazon_unit_count` (pieces), `amazon_carton_count` (cartons), `total_short_units` (pieces),
`sap_available` (pieces — see Trap 8).

### Trap 7 — two published GET paths also serve destructive verbs. The CLI must pin the method.

**Evidence (SPA source):**

- `/api/shipment/shipments/` — `list` is a **GET**, `createDraft` is a **POST** to the *same
  path*.
- `/api/shipment/shipments/{id}/` — `get` is a **GET**, `update` is a **PATCH**, and
  `deleteDraft` is a **DELETE**, all on the *same path*.

The bundle's `client_methods` for these two rows read `["GET","POST"]` and
`["DELETE","GET","PATCH"]`. A generator that keys a spec entry off the *path* rather than
the *method* will happily produce a `shipment shipments --method POST` escape hatch, or a
`--delete` flag. **These two entries must be GET-pinned with no method override, and the
generator's "verb inference from path" must not fire on them.** Related and worse:
`DELETE /api/shipment/shipments/{id}/` deletes a draft shipment, and the app keeps a
`deletion-log` precisely because that has happened.

### Trap 8 — `sap_available` is **not** SAP stock. It is stock minus other people's reservations.

**Evidence (SPA source, `CreateShipment-jeq_xTG5.js`, verbatim tooltip):**

> `Available to plan at GP-FGM = on hand − reserved by other active shipments`

and the "nothing free" branch:

> `Nothing free at GP-FGM right now. You can still pick this line — the plan will short-supply it unless stock lands first.`

So `sap_available: 0` on a PO line means **"nothing free to promise"**, not "no stock in the
warehouse". An operator reconciling this against SAP's `OITW` on-hand will find a
difference every time, and will be right that they differ and wrong about why. There is a
sibling field `planned_reserved` used for sorting in `InventoryView`, which is presumably the
reserved half — **inferred, not observed.**

### Trap 9 — an empty result here can mean four different things, and they are different answers.

For this domain, "the command printed nothing" resolves to one of:

1. **403 — you are not allowed to see it.** The default outcome for most of JIVO right now,
   including this session. If the CLI swallows a 403 into an empty list, an operator will
   report "there are no pending approvals" when the truth is "you cannot see approvals".
   **The CLI must surface the 403 body verbatim, not normalise it to empty.**
2. **Genuinely no rows** — no appointments on that date, no drafts pending.
3. **404 the SPA expects.** Elsewhere in this app the client explicitly catches 404 and
   substitutes an empty payload with an `unavailable: true` marker (seen on `/api/notifications`).
   I did **not** find that pattern on any shipment endpoint, but the app-wide habit exists.
4. **A filter you did not know you sent.** `po-items` is always called by the SPA with
   `po_status=PENDING`; `all-appointments` with `no_paginate=true`; `record` with a `status`.
   If the CLI copies the SPA's defaults silently, "no rows" may just mean "no *pending* rows".
   **Recommendation: the CLI should send no defaults the operator did not ask for, and the
   help text should name the filters the UI uses so the two can be compared.**

Trap 9 evidence for the `po-short-supply` shape is weak and I want that on the record: the
only thing I have is the SPA's *error fallback* `.catch(() => ({count: 0, total_short_units: 0}))`.
That tells me the client expects those two keys; it is **not** proof the success payload has
them or has only them. Marked inferred.

### Trap 10 — two of the four orphan endpoints almost certainly return a file, not JSON.

`shipment-invoice-file` (`…/invoices/{invoice}/file`) and `shipment-po-document`
(`…/po-documents/{document}`) are named like downloads, and the v0.1.0 spec's own
description says *"Download an invoice file for a shipment"*. The spec declares
`response: {type: object}` for both, which is very likely wrong — a PDF is not JSON. I could
not verify this (403 gate + no observable id + the SPA no longer calls them). **Flag for the
human verifier in step 4 of the command list: check the `Content-Type`.** If it is not JSON,
the CLI needs a binary/`--output <file>` path for these two, not a JSON printer.

### Trap 11 — `status` and `switch_state` are two different, independent state machines on the same shipment.

**Evidence (SPA source, two verbatim maps in `ShipmentList-G11ipdat.js`):**

```js
z = { draft, pending_approval, approved, rejected, dispatched, in_transit, delivered }   // status
V = { waiting, email_failed, verified, rejected }                                         // switch_state
```

`rejected` appears in **both** and means different things: shipment rejected at approval vs.
Amazon rejecting the FC switch. A shipment can be `status=draft` **and**
`switch_state=waiting` at once — the SPA's tooltip says *"its rows stay locked until the
switch is verified and it ships"*. So "how many drafts are stuck?" has two answers depending
on which field you filter. Also `record` uses a **third** vocabulary for the *line* status:
`{shipped, short, not_loaded}` (`h` map in `Record-uhJVTCfL.js`). Three status vocabularies,
one domain. **Always name which one you filtered.**

### Trap 12 — the four orphan endpoints are neither alive nor dead, and must not be reported as either.

`shipment-invoices`, `shipment-invoice-file`, `shipment-po-documents`, `shipment-po-document`
are in the shipped v0.1.0 spec, have **zero** call sites in the current SPA bundle
(`raw_paths: []`, `client_methods: []`), and were not probed (the 403 gate applies, and there
is no observable id anyway). Per the carry-forward rule they stay published. **But they carry
a real risk of being silently dead** — Amazon's PO-document requirement did move into the
draft-creation flow (`missing_pos` / *"A PO document (PDF) is required for every PO"* error
handling now lives in `shipmentAPI`'s error formatter), which is consistent with the
document endpoints having been superseded. Label them in the CLI help as
**"shipped, not called by the current UI, unverified"** so a human checks rather than an
operator trusting an empty answer.

---

## 4. Recommended spec entries

Response type for **every** entry below is `object` **(UNVERIFIED — no payload was ever
seen; taken from the v0.1.0 spec's existing declaration, not from data).** Where the SPA's
client code reads the response as an array I say so, because that contradicts the shipped
declaration and a human should settle it.

Enum values in `«guillemets»` are literals read out of the SPA bundle. Anything else is
`not observed`.

| # | command | method + path | params | notes |
|---|---|---|---|---|
| 1 | `shipment all-appointments` | GET `/api/shipment/all-appointments/` | `no_paginate` (bool, SPA sends `true`) — **not observed as a declared param, inferred from the URL builder** | shipped |
| 2 | `shipment appointment-commits` | GET `/api/shipment/appointment-commits/` | none | shipped |
| 3 | `shipment appointments` | GET `/api/shipment/appointments/` | `date` (string, **required**, format not observed) | shipped |
| 4 | `shipment appointment-dates` | GET `/api/shipment/appointments/dates/` | none | shipped |
| 5 | `shipment appointment-extra-pos` | GET `/api/shipment/appointments/{id}/extra-pos/` | `id` (string, required, positional) | shipped |
| 6 | `shipment appointment-families` **(new)** | GET `/api/shipment/appointments/{id}/families/` | `id` (string, required, positional) | new; name matches `appointment-extra-pos` / `appointment-items` style |
| 7 | `shipment appointment-items` | GET `/api/shipment/appointments/{id}/items/` | `id` (string, req, positional); `truck_size` (string, **effectively required**, enum «`10_ton`», «`15_ton`», «`custom`»); `truck_capacity_liters` (int, litres, required when `truck_size=custom`, SPA minimum 100); `priority_premium_pct` / `priority_commodity_pct` / `priority_other_pct` (int, must total 100 — SPA blocks confirm otherwise); `priority_strict` (enum «`1`»); `maximize_fill` (enum «`0`»,«`1`», SPA default «`1`»); `respect_stock` (enum «`0`»; omitted means on); `appointment_ids` (comma-joined ids); `selected_pos` (comma-joined PO numbers); `product_family` (string); `family_asins` (comma-joined ASINs); `commit_caps_json` (JSON string, `{apptId:{units,cartons}}`) | shipped; **all 12 param names are verbatim SPA source** |
| 8 | `shipment asin-catalog` | GET `/api/shipment/asin-catalog/` | none | shipped; client reads `dashboards.asin[]` (inferred) |
| 9 | `shipment fc-switch-group` **(new)** | GET `/api/shipment/fc-switch-group/` | `fc` (string, required — SPA URL-encodes it and sends `''` when unset) | new |
| 10 | `shipment inventory` | GET `/api/shipment/inventory/` | `warehouse` (string, optional; observed enum «`GP-FGM`», «`BH-FGM`», «`GP-FG`», «`BH-EC`», «`ALL`»; SPA default `ALL`) | shipped |
| 11 | `shipment po-appointments` **(new)** | GET `/api/shipment/po-appointments/` | `pos` (string, required, comma-joined PO numbers) | new; client reads `appointments` as a **map** |
| 12 | `shipment po-items` | GET `/api/shipment/po-items/` | `no_paginate` (bool, SPA sends `true`); `po_status` (string, observed value «`PENDING`»; other values not observed) | shipped; client reads `results ?? <bare array>` |
| 13 | `shipment po-shipment-lookup` | GET `/api/shipment/po-shipment-lookup/` | none | shipped; client uses response as a **dict keyed by FC**, not a list |
| 14 | `shipment po-short-supply` | GET `/api/shipment/po-short-supply/` | none | shipped; `count` / `total_short_units` inferred from an error fallback only |
| 15 | `shipment record` | GET `/api/shipment/record/` | `status` (string, optional; observed enum «`draft`», «`pending_approval`», «`approved`», «`dispatched`»; SPA sends **empty string** for "all"; the UI's `deleted` tab does **not** call this endpoint) | shipped; client reads `results[]` |
| 16 | `shipment shipments` | GET `/api/shipment/shipments/` | `status` (string, optional; observed enum «`draft`», «`pending_approval`», «`approved`», «`rejected`», «`dispatched`», «`in_transit`», «`delivered`»; «`approved`» confirmed passed by the Approvals page); `switch_state` (string, optional; observed enum «`waiting`», «`email_failed`», «`verified`», «`rejected`», plus the wildcard «`any`» the SPA sends) | shipped; **GET-pinned, see Trap 7**; client treats response as an **array** |
| 17 | `shipment shipments-deletion-log` | GET `/api/shipment/shipments/deletion-log/` | `limit` (int, optional) | shipped |
| 18 | `shipment shipments-doh-auto-fill` | GET `/api/shipment/shipments/doh-auto-fill/` | `truck_size` (enum as #7, SPA always sends it); `truck_capacity_liters` (int, litres); `fc` (string); `priority_strict` (enum «`1`»); `maximize_fill` (enum «`0`»,«`1`»); `priority_premium_pct` / `priority_commodity_pct` / `priority_other_pct` (int) | shipped; **all param names verbatim SPA source** |
| 19 | `shipment shipments-pending-approvals` | GET `/api/shipment/shipments/pending-approvals/` | none | shipped; client treats response as an **array** |
| 20 | `shipment shipments-stats` | GET `/api/shipment/shipments/stats/` | none | shipped |
| 21 | `shipment shipment` | GET `/api/shipment/shipments/{id}/` | `id` (string, required, positional) | shipped; **GET-pinned, see Trap 7** |
| 22 | `shipment shipment-invoices` | GET `/api/shipment/shipments/{id}/invoices` | `id` (string, req, positional) | shipped-orphan; label **"not called by the current UI, unverified"** |
| 23 | `shipment shipment-invoice-file` | GET `/api/shipment/shipments/{id}/invoices/{invoice}/file` | `id`, `invoice` (string, req, positional) | shipped-orphan; **response may be a file, not JSON — Trap 10** |
| 24 | `shipment shipment-po-documents` | GET `/api/shipment/shipments/{id}/po-documents` | `id` (string, req, positional) | shipped-orphan; label as above |
| 25 | `shipment shipment-po-document` | GET `/api/shipment/shipments/{id}/po-documents/{document}` | `id`, `document` (string, req, positional) | shipped-orphan; **may be a file — Trap 10** |

**Group description** — keep v0.1.0's, it is accurate and it is the only line in the shipped
spec that warns an operator about the gate:

> `Amazon Shipment Planner (read-only). Requires Shipment Planner access; returns 403 without it.`

I would extend it by one clause so the operator knows *which* permission to ask for:

> `Amazon Shipment Planner (read-only). Requires the amazon.shipment_planning.view permission; every command returns 403 without it. Amazon only — no other platform.`

---

## 5. Exclusions

Ten endpoints, each with a positive reason. **None of these is excluded for being dead** —
nothing in this domain was proven dead.

| # | endpoint | verb(s) | reason |
|---|---|---|---|
| 1 | `/api/shipment/shipments/manual-plan/` | POST | **Write endpoint.** Creates a hand-built shipment plan. RULE 0. |
| 2 | `/api/shipment/shipments/{id}/submit/` | POST | **Write endpoint.** Submits a draft into the approval workflow — visible to other people, triggers approval. RULE 0. |
| 3 | `/api/shipment/shipments/{id}/approve/` | POST | **Write endpoint, and an authorisation act.** Approving a shipment on someone's behalf is the single worst thing this CLI could do. RULE 0. |
| 4 | `/api/shipment/shipments/{id}/reject/` | POST | **Write endpoint.** Body `{reason}`. Rejects a shipment. RULE 0. |
| 5 | `/api/shipment/shipments/{id}/dispatch/` | POST | **Write endpoint, and physically irreversible in the real world** — this is the step that says the truck left. RULE 0. |
| 6 | `/api/shipment/shipments/{id}/items/{item}/` | PATCH | **Write endpoint.** Edits a planned line's quantity/SKU. RULE 0. |
| 7 | `/api/shipment/appointment-commits/manual-import/` | POST | **Write endpoint.** Body `{rows}` — bulk-imports appointment commitments. RULE 0. |
| 8 | `/api/shipment/fc-channel/` | POST | **Write endpoint.** Body `{fc, channel}` where channel ∈ «`CORE`», «`FRESH`», «`NOW`» (verbatim, `dt=[\`CORE\`,\`FRESH\`,\`NOW\`]`). Sets the channel for a fulfilment centre — a master-data change affecting every future plan. RULE 0. |
| 9 | `/api/shipment/shipments/{id}/switch/verify/` | GET **and** POST | **Action-shaped route.** The POST (`{action, note}`) verifies or rejects an FC switch — a write. The GET (`switchVerifyCheck`) is a genuine read. Excluded because publishing a GET on a path whose sibling verb is a state-changing action is exactly the shape that goes wrong: one method-inference bug and the CLI fires the POST. **This is the one exclusion I would ask a human to reconsider deliberately** — if they want the check, it should be added by hand with the method hard-pinned, never by a generator. |
| 10 | `/api/shipment/shipments/{id}/switch/email/` | POST (multipart) | **Write endpoint, and it sends external email.** **Not in the bundle** — found separately in `shipmentAPI-DKVOXJWL.js` (`sendSwitchEmail`), which builds a `FormData` with `pdf`, `excel`, `to`, `cc`, `subject`, `body` and posts it. It emails Amazon a switching request with attachments. Must be on the denylist even though the bundle does not list it. RULE 0. |

**Also note, not an exclusion but a method restriction:** `/api/shipment/shipments/` and
`/api/shipment/shipments/{id}/` **are** published — GET only. Their POST (`createDraft`),
PATCH (`update`) and DELETE (`deleteDraft`) siblings must be unreachable from the CLI. See
Trap 7.

---

## Confidence summary

| claim | confidence | what would settle it |
|---|---|---|
| All 17 probed endpoints exist and are routed | **~99%** | A 403 from a DRF permission class requires a resolved view. |
| The gate is `amazon.shipment_planning.view` | **~95%** | Read verbatim from the SPA's permission map, and our 144-permission credential lacks exactly that string. Not confirmed server-side — the backend could gate on something else that happens to correlate. |
| The 12 query-param names on `appointment-items` and the 8 on `doh-auto-fill` | **~97%** | Verbatim from the SPA's `URLSearchParams` builders. Residual risk: the backend may ignore some of them. |
| The observed enum values (`10_ton`, `GP-FGM`, `PENDING`, the status/switch_state sets, `CORE/FRESH/NOW`) | **~95%** | Verbatim literals. They may not be exhaustive — the backend may accept more. |
| Any statement about a **response shape** | **~40-60%, all marked UNVERIFIED** | Every one comes from client code reading a key. Only the verification command list above settles these. |
| The four orphan endpoints still exist | **unknown — I did not check and could not** | Steps 4 of the verification list. |
| Tonnage from this domain over-states oil weight by ~9% | **~90%** | The ÷1000 is verbatim in three places; the 0.91 factor is JIVO's own settled rule. Not confirmed against a dispatched truck's actual weighbridge slip. |
