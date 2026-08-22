# Adversarial refutation of `verdicts.json` — factory / ji.jivo.in

Run: 2026-08-22. Method: bounded greps over the ji.jivo.in bundle + **GET-only** live
calls against `https://factory.jivo.in/api/v1`. Every path-parameter value below was read
out of a real response first. No id invented, incremented or guessed. No non-GET issued.
Token was live (a shipped endpoint returned 200), so this is a live refutation, not a
source-only one.

Summary: **6 claims REFUTED, 4 CONFIRMED, 1 partially refuted.** The publish list should
grow from 20 to **31**; 2 of the 20 have the wrong path string; 1 shipped endpoint of the
"454" is dead.

---

## CLAIM 1 — "ji.jivo.in IS factory.jivo.in's frontend, not a separate uncovered app"

**VERDICT: CONFIRMED.**

How I tried to break it: looked for a second API origin in the bundle, and for an SPA on
factory.jivo.in.

```
$ cat scratch/ji_index.html        -> <title>JI</title>, single module /assets/index-JG3vt8Qs.js
$ cat scratch/factory_index.html   -> {"message":"Welcome to the Accounts API", ...}   (187 bytes, JSON, no SPA)
$ grep -ohoE '.{40}baseUrl:"https://factory.jivo.in.{40}' index.js
  mg={baseUrl:"https://factory.jivo.in/api/v1",timeout:3e4}
```

One origin, one registry (`Ne`), IndexedDB `factoryManagementDB`. Nothing else. Confirmed.

---

## CLAIM 2 — the two "proven_live_200_parameterless" paths returned 200 in all 3 companies

**VERDICT: REFUTED. As written in `verdicts.json` both return 301, in all three tenants.**

This is the claim that will silently break generated commands. The prior probe used
`urllib`, which **follows redirects by default**, so a 301 was recorded as a 200 and the
path string that produced the redirect was written into the file as the endpoint.

Registry literals (both carry a trailing slash):

```
$ grep -ohoE '.{60}SALES_DISPATCH_EXPECTED_VEHICLES.{50}' index.js
  SALES_DISPATCH_EXPECTED_VEHICLES:"/gate-core/sales-dispatch/expected-vehicles/"
$ grep -ohoE '.{20}BILTY_GRPO_SUMMARY.{45}' index.js
  BILTY_GRPO_SUMMARY:"/dispatch/bilty-grpo/summary/"
```

Live, redirects NOT followed:

```
[301] /dispatch/bilty-grpo/summary               (JIVO_MART)     -> /api/v1/dispatch/bilty-grpo/summary/
[301] /dispatch/bilty-grpo/summary               (JIVO_OIL)      -> /api/v1/dispatch/bilty-grpo/summary/
[301] /dispatch/bilty-grpo/summary               (JIVO_BEVERAGES)-> /api/v1/dispatch/bilty-grpo/summary/
[301] /gate-core/sales-dispatch/expected-vehicles (JIVO_MART)    -> /api/v1/gate-core/sales-dispatch/expected-vehicles/
[301] /gate-core/sales-dispatch/expected-vehicles (JIVO_OIL)     -> ... /expected-vehicles/
[301] /gate-core/sales-dispatch/expected-vehicles (JIVO_BEVERAGES)-> ... /expected-vehicles/

[200] /dispatch/bilty-grpo/summary/               (JIVO_MART)      946B  {"period":{...},"queue":{"total":67,"ready":64,...
[200] /dispatch/bilty-grpo/summary/               (JIVO_OIL)       940B  ... "total":113 ...
[200] /dispatch/bilty-grpo/summary/               (JIVO_BEVERAGES) 915B  ... "total":173 ...
[200] /gate-core/sales-dispatch/expected-vehicles/ (JIVO_MART)     287B  [{"row_type":"EXPECTED","id":"expected-333-2",...
[200] /gate-core/sales-dispatch/expected-vehicles/ (JIVO_OIL)      345B
[200] /gate-core/sales-dispatch/expected-vehicles/ (JIVO_BEVERAGES)314B
```

**Fix:** both paths need a trailing slash. Note the shipped spec convention agrees —
450 of the 454 shipped paths end in `/` (the 4 exceptions are all `*.csv` exports).

Mitigating detail I checked so the severity is not overstated: Django's `CommonMiddleware`
**does** carry the query string across the APPEND_SLASH redirect, so this is not a
query-drop bug —

```
[301] /dispatch/bilty-grpo/summary?from_date=2026-08-01&to_date=2026-08-22
      -> /api/v1/dispatch/bilty-grpo/summary/?from_date=2026-08-01&to_date=2026-08-22
```

— but it is still a wrong path string, an extra round-trip on every call, and a hard
failure for any HTTP client configured with `CheckRedirect = ErrUseLastResponse`.

---

## CLAIM 3 — the other 18 publish paths are spelled correctly

**VERDICT: CONFIRMED, and the three specifically suspected mismatches are actually
correct-as-written — the *registry literal* is the thing that is wrong, not the file.**

The brief suspected `/raw-material-gatein/.../po-receipts/view`,
`/weighment/.../weighment/view` and `/security-checks/.../security/view` have no trailing
slash. The registry literals indeed have none:

```
$ grep -ohoE '.{40}po-receipts/view.{30}' index.js
  PO_RECEIPTS_VIEW:e=>`/raw-material-gatein/gate-entries/${e}/po-receipts/view`        <- no slash
  PO_RECEIPTS_VIEW:e=>`/finished-goods-gatein/gate-entries/${e}/po-receipts/view/`     <- slash
$ grep -ohoE '.{40}security/view.{30}' index.js
  GATE_ENTRY_SECURITY_VIEW:e=>`/security-checks/gate-entries/${e}/security/view`       <- no slash
$ grep -ohoE '.{40}weighment/view.{20}' index.js
  GET:e=>`/weighment/gate-entries/${e}/weighment/view`                                 <- no slash
```

But the **server** canonicalises the other way — the frontend is relying on APPEND_SLASH:

```
[301] /raw-material-gatein/gate-entries/3707/po-receipts/view   -> .../po-receipts/view/
[200] /raw-material-gatein/gate-entries/3707/po-receipts/view/  application/json  [{"id":1087,"po_number":"220826059",...
[301] /security-checks/gate-entries/3707/security/view          -> .../security/view/
[200] /security-checks/gate-entries/3707/security/view/         application/json  {"id":1207,"vehicle_condition_ok":false,...
[301] /weighment/gate-entries/3707/weighment/view               -> .../weighment/view/
[404] /weighment/gate-entries/3707/weighment/view/              application/json  {"detail":"Weighment not found"}
```

So the *with-slash* form in `verdicts.json` is right for all three. Lesson for the
pipeline: `harvest/tplscan.py::norm()` does `p.rstrip('/')`, so **every** trailing slash
was destroyed at harvest time and re-added by hand afterwards. The re-adding was right 18
times out of 20 and wrong twice (Claim 2). The registry literal is not authoritative for
slash; the server is.

All 20 exactly as `verdicts.json` writes them:

```
[301] /dispatch/bilty-grpo/summary                                 <- WRONG (see Claim 2)
[301] /gate-core/sales-dispatch/expected-vehicles                  <- WRONG (see Claim 2)
[200] /docking-admin/partial-scan-requests/by-sales-dispatch/1205/   (empty body, see Claim 6)
[200] /docking-admin/scan-skip-requests/by-sales-dispatch/1205/      (empty body, see Claim 6)
[200] /gate-core/dispatch-tracking/1057/bills/
[200] /person-gatein/contractor/2/labours-status/
[200] /person-gatein/entry/300/
[200] /person-gatein/labour/2/history/
[200] /person-gatein/visitor/4/history/
[200] /person-gatein/visitors/4/
[200] /raw-material-gatein/gate-entries/3707/po-receipts/view/
[200] /security-checks/gate-entries/3707/security/view/
[200] /vehicle-management/vehicle-entries/3707/
[200] /vehicle-management/vehicles/by-number/DL01LAA3980/history/
[404] /finished-goods-gatein/gate-entries/3707/po-receipts/view/     application/json
[404] /fixed-asset-gatein/gate-entries/3707/fixed-asset/             application/json
[404] /gate-core/bst-outs/by-vehicle-entry/3707/                     application/json
[404] /gate-core/job-work/by-vehicle-entry/3707/                     application/json
[404] /gate-core/sales-dispatch/by-vehicle-entry/3707/               application/json
[404] /weighment/gate-entries/3707/weighment/view/                   application/json
```

---

## CLAIM 4 — a semantic 404 body proves the route exists AND serves GET

**VERDICT: CONFIRMED, with both a positive and a negative control I went looking for.**

The negative control I needed — a path under the same API that Django genuinely does not
route — turned up on its own while hunting for ids:

```
[404] /quality-control/parameter-sets/     (all 3 companies)   Content-Type: text/html
      <!doctype html><html lang="en"><head><title>Not Found</title></head>
      <body><h1>Not Found</h1><p>The requested resource was not found on this server.</p>
```

and two more (from Claim 5):

```
[404] /quality-control/po-items/615/qc/view    text/html   <!doctype html>...Not Found...
[404] /production-planning/summary/            text/html   <!doctype html>...Not Found...
```

A Django URL-resolver 404 is **HTML** and carries no domain vocabulary. All six of the
file's "routed" endpoints answered `application/json` with a bespoke domain message
("Active BST out entry not found", "Fixed asset entry does not exist", …). A URL resolver
cannot produce those strings — a view must have run. A view running on GET also rules out
the POST-only/405 alternative: DRF answers a method mismatch with
`405 {"detail":"Method \"GET\" not allowed."}`, never a 404 with a domain message.

**However — 3 of the 6 were only 404 because the probe reused a RAW_MATERIAL vehicle-entry
id for handlers keyed to other entry types.** With entry-type-matched observed ids from
`/vehicle-management/vehicle-entries/?entry_type=…`, they are outright LIVE-200:

```
$ /vehicle-management/vehicle-entries/?entry_type=FIXED_ASSET&from_date=2026-01-01&to_date=2026-08-22  (JIVO_OIL)
    n=7   ids=[2500, 2338, 2337, 2336, 2093, 1975]
$ ... entry_type=SALES_DISPATCH   n=296  ids=[3693, 3689, 3669, ...]
$ ... entry_type=JOB_WORK         n=14   ids=[2533, 2361, 2339, ...]

[200] /fixed-asset-gatein/gate-entries/2500/fixed-asset/   438B   {"id":7,"items":[{"id":15,"asset_category":{"id":6,"category_name":"Electrical"},"asset_name":"Fan for fire office",...
[200] /gate-core/sales-dispatch/by-vehicle-entry/3693/   87691B   {"id":1199,"entry_no":"DOCK-20260822-0003",...
[200] /gate-core/job-work/by-vehicle-entry/2533/          1076B   {"id":14,"entry_no":"JWIN-20260727-0001",...
```

The remaining three stay 404-only and there is a good reason for each:
`entry_type=FINISHED_GOODS` and `entry_type=BST_OUT` both return **0 rows in all three
tenants**, and `/gate-core/bst-outs/` is empty in all three, so no matching record exists
anywhere to demonstrate against. `/weighment/.../weighment/view/` was retried on two more
observed RAW_MATERIAL ids (3679, 3678) and returned the same semantic 404 — no weighed
entry in reach.

**Action:** promote those three from "routed" to `proven_live_200_detail`, with the
correct id sources recorded.

---

## CLAIM 5 — "34 GET routes in the bundle that the spec does not have"

**VERDICT: REFUTED as a count. It is a floor, not a total, and at least two more
GET-serving routes are provable to exactly the standard the file already uses.**

```
$ python3 (recompute) :
  shipped normalised   : 454
  harvest paths        : 1178   (809 in registry)
  not shipped          : 749
    resolved GET       :  33     <- the "34"
    resolved write-only: 104
    NO verb resolved   : 612     (289 of them registry entries)
```

612 of 749 not-shipped paths had **no verb resolved at all** — `harvest/verbs.py` only
recognises `.get(X.GROUP.KEY` and `.get(\`/literal\``, so anything called through a helper
or a react-query wrapper falls out. `verbs.py`'s own docstring says the count is a floor;
`verdicts.json`'s headline drops that caveat and states 34 as a fact.

Two of the unresolved-verb registry entries are direct structural siblings of endpoints the
file publishes. Probed with the same observed id 3707 the file itself used:

```
[404] /gate-core/bst-ins/by-vehicle-entry/3707/      application/json  {"detail":"Active BST in entry not found"}
[404] /gate-core/bst-returns/by-vehicle-entry/3707/  application/json  {"detail":"Active BST return entry not found"}
```

Same bespoke-JSON-404 signature as `/gate-core/bst-outs/by-vehicle-entry/{}/`, which the
file *does* publish. If bst-outs is publishable, bst-ins and bst-returns are too.

Two other candidates turned out to be **dead registry entries** (frontend code paths that
no longer have a server route) — reported here because they show the discriminator working
in the negative direction, not as additions:

```
[404] /quality-control/po-items/615/qc/view   text/html   (registry key is literally QUALITY_CONTROL.GET)
[404] /production-planning/summary/           text/html   (PRODUCTION_PLANNING.SUMMARY)
```

---

## CLAIM 6 — the 13 "no observed id" exclusions were principled

**VERDICT: REFUTED. 7 of the 13 are live right now; an 8th is routed. Only 4 hold.**

Three separate causes, all of them lazy rather than principled:

**(a) Only JIVO_MART was tried.** The id-harvest loop never iterated tenants.

```
$ /dispatch/bilty-grpo/history/      JIVO_MART      n=0
$ /dispatch/bilty-grpo/history/      JIVO_OIL       n=25   row0 id=430
$ /quality-control/material-types/   JIVO_MART      n=0
$ /quality-control/material-types/   JIVO_OIL       n=149  row0 id=194

[200] /dispatch/bilty-grpo/430/                       (JIVO_OIL)   810B  {"id":430,"dispatch_plan":1890,"dispatch_bill_no":"626000003",...
[200] /quality-control/material-types/194/parameter-sets/ (JIVO_OIL) 258B [{"id":3,"material_type":194,"label":"Default (all vendors)","parameter_count":4,...
```

**(b) The wrong id field was looked for.** The probe searched `('id','doc_entry','docEntry')`;
the UI call sites name different fields outright.

```
$ grep -F 'bilty-grpo/preview/' chunks/*.js
    onClick:()=>n(`/dispatch/bilty-grpo/preview/${t.dispatch_plan_id}`)
    {path:"/dispatch/bilty-grpo/preview/:dispatchPlanId", ...}
$ grep -F 'grpo/fg/preview/' chunks/*.js
    onClick:()=>r(`/warehouse/grpo/fg/preview/${t.vehicle_entry_id}`)
    {path:"/warehouse/grpo/fg/preview/:vehicleEntryId", ...}

/dispatch/bilty-grpo/pending/ (JIVO_MART) n=25 -> row0 dispatch_plan_id=2637
[200] /dispatch/bilty-grpo/preview/2637/  (JIVO_MART) 1780B  {"dispatch_plan_id":2637,"sap_invoice_doc_entry":38445,...
[200] /grpo/fg/preview/3707/              (JIVO_OIL)  1280B  [{"vehicle_entry_id":3707,"entry_no":"GE-2026-8691","entry_status":"QC_COMPLETED","is_ready_for_grpo":true,...
```

`/grpo/fg/preview/{}` takes a **vehicle_entry_id**, not a doc_entry — which is why
`/grpo/fg/pending/` being empty was never actually a blocker; any observed vehicle-entry id
works.

**(c) "No sibling list ships" was asserted without following the chain one hop.**
`/quality-control/material-types/194/parameter-sets/` (unlocked in (a)) hands over
parameter-set id 3, which unlocks both "no sibling list" exclusions:

```
[200] /quality-control/parameter-sets/3/             (JIVO_OIL)  256B  {"id":3,"material_type":194,"label":"Default (all vendors)",...
[200] /quality-control/parameter-sets/3/parameters/  (JIVO_OIL) 1575B  [{"id":1579,"parameter_set":3,"parameter_name":"Appearance","parameter_code":"APPEARANCE",...
```

And two of the four "NOT PROBED" exclusions come straight off
`/quality-control/arrival-slips/` (8 rows, JIVO_MART; row0 `id=589`, `po_item_receipt=615`):

```
$ grep -F 'getBySapItem' chunks/*.js   ->  const s=e?.trim().toUpperCase(); ... i.getBySapItem(s)   (an item CODE, not a pk)
$ /quality-control/material-types/194/ -> sap_items:[{"id":69,"item_code":"PM0000855",...}]

[200] /quality-control/po-items/615/arrival-slip/            (JIVO_MART) 1130B  {"id":589,"po_item_receipt":615,"po_item_code":"PM0000087",...
[200] /quality-control/material-types/by-sap-item/PM0000855/ (JIVO_OIL)   387B  [{"id":194,"code":"PM0000855","name":"10 Ml Bottle",...
[404] /quality-control/arrival-slips/589/inspection/         (JIVO_MART)   33B  {"detail":"Inspection not found"}   <- ROUTED (JSON, bespoke)
```

**Exclusions that survive (4):**

| path | why it genuinely holds |
|---|---|
| `/dispatch/transporter-invoices/{}/` | `/dispatch/transporter-invoices/history/` is 0 rows in **all three** tenants |
| `/goods-return/{}/` | `/goods-return/` is 0 rows in all three tenants |
| `/goods-return/{}/attachments/` | same |
| `/grpo/draft/{}/` | `/grpo/draft/` returns **500** (HTML server error) in all three tenants; no id source anywhere |

Also confirmed while here: the two `docking-admin` `by-sales-dispatch` endpoints return
**200 with a zero-byte body and no Content-Type**, for every id and tenant tried (1205,
1199 × MART, OIL). That is the endpoint's real "no request exists" answer — the UI codes it
as `(await ae.get(...)).data ?? null`. Keep them, but the generated client must tolerate an
empty body or it will throw on JSON decode.

---

## CLAIM 7 — `/gate-core/sales-dispatch/lock` is excluded as write-shaped

**VERDICT: the stated reason is REFUTED; the decision is still defensible on narrower
grounds. Not called either way.**

The stated test — "called with both `.get` and `.patch`" — is not a discriminator, because
the file **publishes three other paths with exactly that shape**:

```
$ grep -F 'fixed-asset-gatein/gate-entries/' chunks/*.js
  getByEntryId:async e=>(await i.get(`/fixed-asset-gatein/gate-entries/${e}/fixed-asset/`)).data,
  create:async(e,t)=>(await i.post(`/fixed-asset-gatein/gate-entries/${e}/fixed-asset/`,t)).data,
  update:async(e,t)=>(await i.put(`/fixed-asset-gatein/gate-entries/${e}/fixed-asset/`,t)).data
```

`ARRIVAL_SLIP_GET` / `ARRIVAL_SLIP_CREATE` are literally the same path under two keys, and
`/quality-control/arrival-slips/{}/inspection/` is `.get` + `.post`. All were probed and
all behave as pure reads (a missing record 404s; nothing is created).

The lock's own call site is a plain read pair, and its consumer is a cached read hook:

```
async getLock(){return(await a.get(n.GATE_CORE.SALES_DISPATCH_LOCK)).data},
async updateLock(s){return(await a.patch(n.GATE_CORE.SALES_DISPATCH_LOCK,s)).data}
function b(){return o({queryKey:a.lock(),queryFn:()=>s.getLock(),staleTime:30*1e3})}
```

That reads as a genuine read of lock state. **But** the real discriminator is not the verb
mix, it is the *shape of the resource*: `/gate-core/sales-dispatch/lock/` is a
**parameterless singleton settings resource** — precisely the shape of the
`/marketplace/settings/?channel=X` `get_or_create` incident, and unlike every detail route
above, which is keyed to a record that either exists or 404s. Source cannot rule out
`get_or_create` on a singleton. **Keep excluded, but restate the reason** — "singleton
settings-shaped resource, get_or_create risk", not "called with .get and .patch".

Registry literal for the record (the file writes it without one): `"/gate-core/sales-dispatch/lock/"`.

---

## CLAIM 8 — "factory-cli already ships 454 of its endpoints"

**VERDICT: REFUTED in detail. At least one shipped path is dead today.**

44 parameterless shipped paths sampled at random (seeds 42 and 7), GET, JIVO_OIL:

```
[404] /dashboards/inventory-age/filter-options/    text/html   <!doctype html>...Not Found...
      confirmed dead in JIVO_OIL, JIVO_MART and JIVO_BEVERAGES
```

Everything else non-200 in the sample was healthy behaviour, not death:

```
[400] /blowing/reports/make-vs-buy/            {"detail":"Query params 'date_from' and 'date_to' are required."}
[400] /blowing/reports/variances/              same
[400] /oms/invoices/pending-count/             {"detail":"whs (warehouse) is required"}
[400] /vehicle-management/vehicle-entries/count/      {"detail":"entry_type query parameter is required"}
[400] /vehicle-management/vehicle-entries/list-by-status/  {"detail":"status query parameter is required"}
[400] /barcode/intercompany/warehouses/        {"error":"company_code is required."}
[403] /marketplace/delivery-notes/summary/     {"code":"WRONG_COMPANY","error":"The marketplace module is not enabled..."}
[504] /barcode/dispatch/sessions/              nginx gateway timeout (10 MB sibling endpoint; slow, not dead)
```

So 1 dead in 44 sampled (~2%). Not a systemic problem, but "454 shipped" is a registry
count, not a liveness count, and the headline reads as if it were the latter.

---

## CLAIM 9 — verb correctness: every one of the 20 is really `.get(...)`

**VERDICT: CONFIRMED.** Including the five `person-gatein` paths that carry **no registry
key at all** (harvest lens `C-template` only) — each has an explicit `.get` call site:

```
getEntry:            async e=>(await t.get(`/person-gatein/entry/${e}/`)).data
getVisitor:          async e=>(await t.get(`/person-gatein/visitors/${e}/`)).data
getVisitorHistory:   async e=>(await t.get(`/person-gatein/visitor/${e}/history/`)).data
getLabourHistory:    async e=>(await t.get(`/person-gatein/labour/${e}/history/`)).data
getContractorLaboursStatus: async e=>(await t.get(`/person-gatein/contractor/${e}/labours-status/`)).data
getByEntryId:        async e=>(await i.get(`/fixed-asset-gatein/gate-entries/${e}/fixed-asset/`)).data
getServiceDetail:    async e=>(await a.get(s.DISPATCH.BILTY_GRPO_DETAIL(e))).data
getServicePreview:   async e=>(await a.get(s.DISPATCH.BILTY_GRPO_PREVIEW(e))).data
getPreview:          async e=>(await r.get(s.GRPO.FG_PREVIEW(e))).data
```

No path in the publish list rests on a registry entry with no resolved verb.

---

## Corrected publish list — 31 endpoints

Trailing slash as the **server** canonicalises it, not as the registry literal spells it.

Corrections to the existing 20:

| # | corrected path | was |
|---|---|---|
| 1 | `/dispatch/bilty-grpo/summary/` | **no slash — 301** |
| 2 | `/gate-core/sales-dispatch/expected-vehicles/` | **no slash — 301** |

Promotions out of `routed_handler_404` into live-200 (3):

| path | observed id | source |
|---|---|---|
| `/fixed-asset-gatein/gate-entries/{}/fixed-asset/` | 2500 | `/vehicle-management/vehicle-entries/?entry_type=FIXED_ASSET&…` (JIVO_OIL) |
| `/gate-core/sales-dispatch/by-vehicle-entry/{}/` | 3693 | `…?entry_type=SALES_DISPATCH&…` (JIVO_OIL) |
| `/gate-core/job-work/by-vehicle-entry/{}/` | 2533 | `…?entry_type=JOB_WORK&…` (JIVO_OIL) |

Additions — 7 formerly excluded, now LIVE-200 (all ids observed):

| path | observed id | source |
|---|---|---|
| `/dispatch/bilty-grpo/{}/` | 430 | `/dispatch/bilty-grpo/history/` **JIVO_OIL** |
| `/dispatch/bilty-grpo/preview/{}/` | 2637 | `/dispatch/bilty-grpo/pending/` field `dispatch_plan_id` |
| `/grpo/fg/preview/{}/` | 3707 | any vehicle-entry id (param is `vehicle_entry_id`) |
| `/quality-control/material-types/{}/parameter-sets/` | 194 | `/quality-control/material-types/` **JIVO_OIL** |
| `/quality-control/parameter-sets/{}/` | 3 | `…/material-types/194/parameter-sets/` |
| `/quality-control/parameter-sets/{}/parameters/` | 3 | same |
| `/quality-control/po-items/{}/arrival-slip/` | 615 | `/quality-control/arrival-slips/` field `po_item_receipt` |
| `/quality-control/material-types/by-sap-item/{}/` | `PM0000855` | `…/material-types/194/` `sap_items[].item_code` (uppercased at the call site) |

Additions — routed (bespoke JSON 404), same standard as the file's own six (3):

| path | evidence |
|---|---|
| `/quality-control/arrival-slips/{}/inspection/` | `{"detail":"Inspection not found"}` on observed id 589 |
| `/gate-core/bst-ins/by-vehicle-entry/{}/` | `{"detail":"Active BST in entry not found"}` on observed id 3707 |
| `/gate-core/bst-returns/by-vehicle-entry/{}/` | `{"detail":"Active BST return entry not found"}` on observed id 3707 |

Still excluded, and now for a reason that holds (5):
`/dispatch/transporter-invoices/{}/`, `/goods-return/{}/`, `/goods-return/{}/attachments/`
(all 0 rows in all three tenants), `/grpo/draft/{}/` (list 500s in all three), and
`/gate-core/sales-dispatch/lock/` (singleton settings-shaped, `get_or_create` risk — reason
restated, decision kept).

Also drop from the shipped spec, or mark dead: `/dashboards/inventory-age/filter-options/`.

## Pipeline defects worth fixing upstream

1. `harvest/tplscan.py::norm()` does `p.rstrip('/')` — trailing slashes are destroyed at
   harvest time and cannot be recovered from the registry literal anyway (the frontend
   relies on APPEND_SLASH). The only authority is the live server: probe both forms and
   record whichever returns 200 without a 301.
2. The probe used `urllib`, which follows redirects silently. Any liveness probe must
   disable redirect-following or a 301 records as a 200 against the wrong path.
3. The id-harvest loop tried only `JIVO_MART`. Iterate all three `Company-Code` tenants
   before declaring a list empty.
4. Id fields were guessed as `('id','doc_entry','docEntry')`. Read the field name off the
   **UI route parameter** (`:dispatchPlanId`, `:vehicleEntryId`) and the navigate call site
   instead.
5. `harvest/verbs.py` resolves a verb for only ~18% of not-shipped paths; the rest are
   silently dropped from the candidate set rather than surfaced as unknown.

> Document numbers, IRNs and doc entries in this file are **synthesized**. The endpoint shapes, HTTP status codes and response structures are real, captured 2026-08-22.
