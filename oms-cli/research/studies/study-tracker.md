# Domain study: tracker

22 paths. **15 publish, 7 exclude.**

Every one of the 12 GET paths that could be probed bare returned **HTTP 403**. Per
skill rule 4 and the study contract, a 403 is a permission wall, not death: all of
them are published, and every response shape below is derived **from the deployed SPA
bundle, not from a live payload**. Each is marked `UNVERIFIED` with the server's exact
wording as the reason.

## Where the response shapes come from

The bundle contains the whole tracker client in one object literal — minified name
`y9`, at offset 1902743–1905980 of `/tmp/oms-rescrape/bundle/index-NnIXJV2m.js` — one
method per endpoint. Each method's consumer (a React page in the same chunk) shows the
initial state type (`useState([])` vs `useState(null)`) and the exact fields rendered.
That is strong evidence for array-vs-object and for field names, and weak evidence for
types. It is not a payload. Where I say "array", the tell is that the page calls
`.filter`/`.map`/`.length` directly on the response with `[]` as the initial state — an
object would throw at first render, so the app would be visibly broken, and it is not.

## The two permission gates — measured, then re-verified live

Re-run 2026-08-04 during this study, bare GET, same token
(`/tmp/oms-rescrape/token.txt`, user `paramjot`, role `admin`):

```
GET /api/tracker/lookups/        -> 403 {"detail":"You do not have access to this tracker page."}
GET /api/tracker/my-queue/       -> 403 {"detail":"You do not have access to this tracker page."}
GET /api/tracker/vendors/        -> 403 {"detail":"You do not have access to this tracker page."}
GET /api/tracker/admin/stages/   -> 403 {"detail":"Tracker administration is restricted to tracker admins."}
```

| gate | server's exact wording | endpoints behind it |
|---|---|---|
| **A — tracker admin** | `Tracker administration is restricted to tracker admins.` | `admin/stages`, `admin/tracker-users`, `admin/users`, `all-invoices`, `all-invoices/export` (measured) · `admin/lookups/{type}` (inferred) |
| **B — tracker page access** | `You do not have access to this tracker page.` | `alerts`, `invoices`, `lookups`, `my-queue`, `reports`, `stage-advanced`, `vendors` (measured) · `invoices/{id}`, `invoices/{id}/jsap` (inferred) |

Gate A is strictly narrower than gate B: an account can hold tracker page access and
still be refused the admin surface. Note that `all-invoices` sits behind gate **A**
despite not living under `/admin/` — the register of every invoice is admin-only.

The credential is a **global `admin`** and fails both. Tracker access is a separate
grant from the app role, held per user, and the CLI cannot manufacture it.

### The SPA disagrees with its own backend (probable backend/frontend defect)

The bundle's tracker page map, at offset 232978 (`xn`) / 233357 (`Sn`) / 233754 (`Dn`):

```js
Sn = { tracker_admin:[Tracker_Entry,Tracker_Queue,Tracker_Invoices,Tracker_Alerts,Tracker_Reports,Tracker_Admin],
       tracker_entry:[Tracker_Entry,Tracker_Queue],
       tracker_user :[Tracker_Queue] }
Dn = (role, isAdmin=false) => (isAdmin || role === 'admin') ? new Set(ALL_PAGES) : new Set(Sn[role] || [])
```

and its one call site, in the sidebar at offset 341804:
`U = s?.toLowerCase() === 'admin'; re = Dn(s, U)`. A global `admin` is granted **every** tracker page in the
sidebar, then every one of those pages' API calls is refused by the server. Reproduction:
log in as `paramjot`, open `/Tracker_Queue`, observe the menu item render and the queue
fail. Neither 403 string exists anywhere in the bundle, so the client has no idea this
gate exists and shows a bare "Failed to load queue" toast. Confidence: high that the
mismatch is real (both halves measured); medium on which side is wrong — the server
requiring a tracker grant looks deliberate, so the frontend's `role === 'admin'`
shortcut is the likely bug.

---

### `/api/tracker/lookups/`

- **command**: `tracker lookups`
- **verdict**: publish
- **description**: The tracker's dropdown reference data — the stage ladder plus every
  picklist an invoice is classified by (category, unit, branch, mode, GST type, GST
  rate). Fetch this first: it is the only way to learn the stage `code` values that
  `my-queue` and `stage-advanced` filter on.
- **params**: none. The call site is `Y.get('/tracker/lookups/')` with no second argument.
- **response**: `object` — **UNVERIFIED** (403: "You do not have access to this tracker
  page."). Shape from the bundle, where the page destructures it as:
  - `stages[]` — `{id, code, name, order, threshold_days, status_choices[], requires_status, can_return, is_terminal, is_active}`
  - `categories[]`, `units[]`, `branches[]`, `modes[]`, `gst_types[]` — each `{id, name}`
  - `gst_rates[]` — `{id, label, rate}` (`rate` is a percentage; the app computes GST as `taxable_value * rate / 100`)
- **evidence**: 403 measured on the bare probe and re-measured live in this study.
  Shape read from bundle offsets 1914400–1915100 (`e.gst_types`, `e.gst_rates`,
  `e.categories`, `e.units`, `e.branches`, `e.modes`) and 1928465 (`e?.stages.find(s => s.code === …)`).
- **traps**: `branches` here is a **tracker lookup table with integer ids**, NOT the
  `branch=OIL|BEVERAGE` tenant selector that `/api/hana/*` demands (API-FACTS §2). Same
  word, unrelated enums. An operator who reads `branch` in a tracker filter and sends
  `OIL` will get nothing.

---

### `/api/tracker/vendors/`

- **command**: `tracker vendors`
- **verdict**: publish
- **description**: The SAP business-partner list the tracker's party autocomplete
  searches — who an invoice can be booked against. Returns both vendors and customers.
- **params**: none.
- **response**: `array` — **UNVERIFIED** (403, gate B). Items: `{card_code, card_name,
  gstin, card_type, state}`. `card_type === 'C'` renders the badge "Customer", anything
  else renders "Vendor".
- **evidence**: 403 measured (bare probe) and re-measured live. Shape from bundle
  offset 1907655 and the combo-box renderer at 1912900–1913300.
- **traps**: name says "vendors", contents include customers — `card_type` is the
  discriminator. Card codes here are SAP `CardCode`s, so they join to SAP B1
  `BusinessPartners`, but which company database they came from is not stated in the
  payload and I could not determine it from the bundle.

---

### `/api/tracker/invoices/`

- **command**: `tracker invoices`
- **verdict**: publish (GET only — see traps, this URL also serves a POST)
- **description**: The invoices the calling user can see in the tracker — the working
  list behind the Invoice Entry desk.
- **params**: **none observed.** The service method accepts an arbitrary filter object
  and stringifies it into the query, but the SPA's only call site passes `{}`
  (`y9.listInvoices()` at offset 1908033). No filter parameter name is sourced, so
  none is published. Rule 2: unproven resolves to excluded.
- **response**: `array` — **UNVERIFIED** (403, gate B). Item fields the UI reads:
  `id, invoice_number, invoice_date, effective_month, party_name, party_code,
  party_gstin, taxable_value, invoice_value, gst_type, gst_type_name, gst_rate,
  gst_rate_label, additional_charge_type, additional_charge_amount, category,
  category_name, unit, unit_name, branch, branch_name, mode, mode_name,
  current_stage_code, days_at_stage, created_by_name, editable, is_locked, is_overdue`.
  `additional_charge_type` is a **closed enum sourced from the app's own constant `v9`**
  (offset 1902575): `DEMURRAGE`, `LABOUR_COST`, `POINT_VALUE`.
- **evidence**: 403 measured (bare). Array inference: `useState([])` then
  `h.filter(e => e.current_stage_code === 'entry')` at offset 1908131.
- **traps**:
  - **Dual-verb URL.** `POST /api/tracker/invoices/` creates an invoice on the same
    path. Only the GET is published; an exclusion list keyed on path alone would kill
    the read too.
  - The endpoint returns more than the entry stage — the SPA filters to
    `current_stage_code === 'entry'` client-side. The server-side scope (own invoices?
    own stages? everything visible?) is **unknown**, and a 403 gave me no way to find out.

---

### `/api/tracker/invoices/{id}/`

- **command**: `tracker invoice-detail`
- **verdict**: publish (GET only — this URL also serves PATCH and DELETE)
- **description**: One tracker invoice in full, including its stage-by-stage timeline —
  who held it, how long, what they said. This is the "why has this invoice not been
  paid" answer.
- **params**: `id` — int, required, positional. Sourced from `id` on any row of
  `tracker invoices` / `tracker my-queue` / `tracker all-invoices`.
- **response**: `object` — **UNVERIFIED** (403 on every list endpoint that could have
  supplied an id, so this was never probed at all). Fields rendered by the detail modal:
  - header: everything in the list row, plus `gst_amount`, `additional_charge_type_display`,
    `current_stage_name`, `current_stage_entered_at`, `status` (`COMPLETED` |
    anything-else-means-in-progress), `created_at`, `updated_at`
  - adjustments: `debit_amount`, `net_invoice_value`, `hold_amount`
  - return trail: `arrived_via_return`, `returned_from`, `returned_by`, `return_reason`
  - `events[]` — `{id, stage_name, event_type, stage_status, hold_type, amount,
    receiving_note, acted_by_name, entered_at, exited_at, days_spent, remarks}`
  - `payment{}` — `{discount_pct, discount_amount, tds_pct, tds_amount, paid_amount,
    open_balance, hold_added_back, status}`
- **evidence**: no probe. Bundle offsets 1922400–1924600 (entry-desk modal) and
  1941800–1943400 (queue modal + timeline).
- **traps**: dual-verb URL — `PATCH` edits and `DELETE` removes on the same path.
  `receiving_note === 'LATE'` renders as "Late (after 6 PM)", so there is a
  received-before-6pm SLA baked into the workflow.

---

### `/api/tracker/invoices/{id}/jsap/`

- **command**: `tracker invoice-jsap`   *(NEW — named to match the shipped `invoice-detail`)*
- **verdict**: publish
- **description**: Whether this tracker invoice has reached **JSAP** (JIVO's internal
  ops platform at `103.89.45.75:5001`, the system `jsap-cli` talks to) and what JSAP's
  approvers did with it — approved, rejected, or still sitting there. Answers "the
  invoice is stuck at JSAP Approval, has JSAP actually seen it?"
- **params**: `id` — int, required, positional. Same source as `invoice-detail`.
- **response**: `object` — **UNVERIFIED**, never probed (no obtainable id). Two shapes,
  discriminated by `available`:
  - `{available: true, status, label, description, doc_entry}` — `status` `'A'` renders
    green, `'R'` renders red, anything else neutral; `doc_entry` is the **SAP B1 draft
    DocEntry** ("draft {doc_entry}" in the UI)
  - `{available: false, reason, detail}` — `reason` ∈ `not_in_jsap`, `no_party_code`,
    `no_draft`, `not_submitted`, `rejection_pending`
  - it can also be literally `null`, which the UI badges "unavailable"
- **evidence**: bundle offsets 1903577 (call site) and 1926239 (`function Nhe({status})`,
  the badge component that reads every field above). No status code — never called.
- **traps**: this is a **cross-system read**. It reaches out of OMS into JSAP and, via
  `doc_entry`, into SAP B1's document drafts. If JSAP is down the endpoint's own error
  behaviour is unknown; the SPA only handles a thrown promise by showing "unavailable".
  Do not confuse it with `POST /api/tracker/jsap/sync/`, which is a write and is excluded.

---

### `/api/tracker/my-queue/`

- **command**: `tracker my-queue`
- **verdict**: publish
- **description**: The invoices sitting on *your* desk right now, grouped by the stages
  you are assigned to — the tracker's to-do list.
- **params**: **none.** The brief lists `stage` as observed at the call site; that is a
  **harvest artifact and must not be published**. `extract_calls.py` records 160 chars
  of trailing context, and at offset 1903391 that window runs past the end of
  `myQueue()` into the next method:

  ```js
  async myQueue(){ let{data:e}=await Y.get(`/tracker/my-queue/`); return e },
  async getStageAdvanced(e){ let{data:t}=await Y.get(`/tracker/stage-advanced/`,{params:{stage:e}}); return t },
  ```

  The `my-queue` call has no second argument at all. `stage` belongs to
  `stage-advanced` only. Confidence: high — the call site is unambiguous.
- **response**: `object` — **UNVERIFIED** (403, gate B) — `{invoices: [...], stages: [...]}`:
  - `invoices[]` — the list-row fields plus `rejection_pending`, `is_partially_paid`,
    `arrived_via_return`, `returned_from`, `returned_by`, `return_reason`,
    `open_balance`, `debit_amount`, `net_invoice_value`, `current_stage_entered_at`
  - `stages[]` — `{code, name, count}`, the tabs across the top, i.e. only the stages
    this user is assigned to
- **evidence**: 403 measured (bare) and re-measured live. Shape from
  `r(e.invoices), a(e.stages)` at offset 1928263.
- **traps**: an empty `stages[]` means "this user is assigned to no stage", which is a
  data fact about the account, not evidence the endpoint is broken (rule 5). The SPA
  polls this every 30 s.

---

### `/api/tracker/stage-advanced/`

- **command**: `tracker stage-advanced`
- **verdict**: publish
- **description**: What has already left a given stage — invoices you advanced out of
  it, and where they are now. The "did my work land?" view.
- **params**:
  - `stage` — string, required (the SPA never calls it without one). **Enum is
    server-defined and only three values are sourced in the app's own code**:
    `entry`, `sap_approval`, `jsap_approval` (bundle offsets 1908152, 1928465,
    1928571). Every other valid value is a row in the DB-driven stage table and can
    only be read at runtime from `tracker lookups` → `stages[].code`. Do not send a
    stage code you have not read back from `lookups`, `my-queue` or `admin-stages`.
- **response**: `array` — **UNVERIFIED** (403, gate B). Same invoice-row fields, plus
  `advanced_at` and a `current_stage_name` that is now the *next* stage.
- **evidence**: 403 measured on the bare call (no `stage`) — note the permission check
  fires before any missing-parameter check, so the server never got to tell us whether
  `stage` is mandatory or what it accepts. `params:{stage:e}` at offset 1903473;
  `getStageAdvanced(o)` where `o` is the selected stage `code` at offset 1929247.
- **traps**: `stage` takes a stage **code** (`entry`), not an id and not a name
  ("Invoice Entry"). Unverified whether omitting it is an error or a no-filter default.

---

### `/api/tracker/alerts/`

- **command**: `tracker alerts`
- **verdict**: publish
- **description**: Invoices stuck past their stage's day threshold — who is holding
  them up, by how many days, and whether the reminder email went out.
- **params**: none.
- **response**: `array` — **UNVERIFIED** (403, gate B). Items: `{id, invoice,
  invoice_number, party_name, invoice_value, stage_name, days_stuck, threshold_days,
  over_by, stage_entered_at, notified: [{user, sent_at}]}`.
- **evidence**: 403 measured (bare). Shape from the alerts table at offsets
  1976199–1978900.
- **traps**: `invoice` and `id` are different — `id` is the alert row, `invoice` is the
  tracker-invoice id you pass to `invoice-detail`. `over_by` is a float (rendered
  `.toFixed(1)`). An empty array is the good outcome ("No stuck invoices"), not an
  error. The SPA polls this every 60 s.

---

### `/api/tracker/reports/`

- **command**: `tracker reports`
- **verdict**: publish
- **description**: Turnaround analytics for the whole invoice flow — average days per
  stage, what is pending where, ageing buckets, and who/which vendor/which category is
  the bottleneck.
- **params** — all optional, all read off the SPA's own filter bar (offsets 1970500–1971900):
  - `from` — date `YYYY-MM-DD`
  - `to` — date `YYYY-MM-DD`
  - `branch` — int, a `lookups.branches[].id`
  - `unit` — int, a `lookups.units[].id`
  - `category` — int, a `lookups.categories[].id`
- **response**: `object` — **UNVERIFIED** (403, gate B):
  - `summary{in_progress, completed, overdue, avg_cycle_days}`
  - `pending_by_stage[]` — `{stage_name, count, overdue}`
  - `avg_days_per_stage[]` — `{stage_name, avg_days}`
  - `ageing[]` — `{bucket, count}`
  - `bottleneck_by_person[]`, `bottleneck_by_vendor[]`, `bottleneck_by_category[]` —
    each `{key, avg_days, visits}`
- **evidence**: 403 measured (bare). Keys read from the Excel export builder
  (offset 1969027) and every chart's `dataKey` (offsets 1972800–1974400).
- **traps**: `branch`/`unit`/`category` are **integer lookup ids**, not names and not
  `OIL`/`BEVERAGE`. Sending a string will at best silently filter nothing. The ids
  come from `tracker lookups`, which is itself 403 for this credential — so in
  practice a tracker-less operator cannot even discover them.

---

### `/api/tracker/all-invoices/`

- **command**: `tracker all-invoices`
- **verdict**: publish
- **description**: The full invoice register — every invoice in the tracker regardless
  of whose desk it is on, with its current stage and whether it has breached threshold.
  Admin-only.
- **params** — all optional, from the SPA's filter bar (offsets 1983700–1986200):
  - `party` — string, free-text party-name search
  - `invoice_number` — string
  - `effective_month` — string `YYYY-MM` (an `<input type="month">`)
  - `stage` — string, a stage **code** (options rendered from `lookups.stages[].code`)
  - `status` — string, enum `IN_PROGRESS` | `COMPLETED` (both hard-coded as `<option value>`)
  - `overdue` — string, enum `true` | `false` (sent as strings, not booleans — the
    service does `String(n)` on every value)
  - `category`, `unit`, `branch` — int lookup ids
- **response**: `array` — **UNVERIFIED** (403, gate **A**). Same invoice-row fields as
  `tracker invoices`, plus `current_stage_name` and `status`.
- **evidence**: 403 measured (bare). Array inference: `useState([])` then `n.length`,
  `n.filter(e => e.status === 'COMPLETED')` at offset 1982167.
- **traps**: gate **A** (tracker admin), not gate B, despite the path not containing
  `/admin/`. Unpaginated as far as the bundle shows — the page renders `n.map` over the
  whole response with no page controls, so this could be large; a CLI wrapping it wants
  `--compact`/`--csv` (same class of problem as `sap/addresses/`, API-FACTS §7).

---

### `/api/tracker/all-invoices/export/`

- **command**: `tracker all-invoices-export`
- **verdict**: publish
- **description**: The same invoice register as a downloadable Excel workbook — what
  Accounts actually circulates. Admin-only.
- **params**: identical to `tracker all-invoices` (the SPA passes the same filter object).
- **response**: **binary XLSX, not JSON** — **UNVERIFIED** (403, gate A). The call site
  is `Y.get('/tracker/all-invoices/export/', {params: t, responseType: 'blob'})` and
  the result is handed to `saveAs(..., 'invoice-register.xlsx')`.
- **evidence**: 403 measured (bare). Bundle offset 1905648 and the save at 1982338.
- **traps**: **a command that JSON-decodes this response will fail even when the call
  succeeds.** It must stream to a file. The shipped spec declares `response: {type: object}`,
  which is wrong. Content-type was not observed (403 before any body), so I am inferring
  XLSX from `responseType: 'blob'` + the `.xlsx` filename — confidence high, but it is
  an inference, not a measured header.

---

### `/api/tracker/admin/stages/`

- **command**: `tracker admin-stages`
- **verdict**: publish (GET only — this URL also serves POST)
- **description**: The stage ladder itself — how many desks an invoice passes through,
  in what order, how many days each is allowed before it counts as stuck, and which
  ones demand a status decision. This is the definition of JIVO's invoice workflow.
- **params**: none.
- **response**: `array` — **UNVERIFIED** (403, gate A). Items: `{id, name, code, order,
  threshold_days, status_choices[], requires_status, can_return, is_terminal, is_active}`.
- **evidence**: 403 measured (bare) and re-measured live. Shape from the new-stage
  defaults `Ihe` at offset 1950320 and the stages table at 1952200–1953400.
- **traps**:
  - Dual-verb URL — `POST` creates a stage on the same path.
  - `status_choices` is free text typed by an admin, uppercased and comma-split by the
    client. The form's own placeholder gives the house set — `OK, HOLD, DEBIT, RETURN` —
    and `REJECTED` appears as a fourth value hard-coded in the queue logic. **There is
    no fixed server enum**; treat these five as observed examples, not a closed list.
  - `is_terminal` marks the payment desk; `order <= 5` is where the SPA still allows a
    delete (`Ghe = 5`, offset 1980973).

---

### `/api/tracker/admin/lookups/{type}/`

- **command**: `tracker admin-lookups`
- **verdict**: publish (GET only — this URL also serves POST)
- **description**: One tracker picklist in full, including inactive values and their
  sort order — the editable version of what `tracker lookups` returns read-only.
- **params**:
  - `type` — string, required, positional. **Enum fully sourced** from the app's own
    constant `j9` at offset 1950109: `categories`, `units`, `branches`, `modes`,
    `gst_types`, `gst_rates`. These six and no others.
- **response**: `array` — **UNVERIFIED**, and **never probed** (the probe skips
  parameterised paths). Items are `{id, name, sort_order, is_active}` for five of the
  six types, and `{id, label, rate, sort_order, is_active}` for `gst_rates` — the
  client branches on `type === 'gst_rates'` for exactly this reason.
- **evidence**: no status code for this path. Gate assignment (A, tracker admin) is
  **inferred** from its `/admin/` prefix, from the three sibling `/admin/*` paths that
  measured gate A, and from it being reachable only on the Tracker Config page.
  Confidence high, but unmeasured.
- **traps**: dual-verb URL — `POST /api/tracker/admin/lookups/{type}/` creates a value.
  `gst_rates` returns a different shape from every other type; a command that assumes
  `name` will render blanks for it.

---

### `/api/tracker/admin/tracker-users/`

- **command**: `tracker admin-tracker-users`
- **verdict**: publish (GET only — this URL also serves POST)
- **description**: The accounts that exist purely to work the tracker, and what tracker
  role each holds. This is the roster that decides who gets past the 403 wall.
- **params**: none.
- **response**: `array` — **UNVERIFIED** (403, gate A). Items: `{id, username, name,
  email, phone, role, role_display, is_active}`. `role` enum is the app's own constant
  `Cn` (offset 233559): `tracker_admin` ("Tracker Admin"), `tracker_entry` ("Invoice
  Entry"), `tracker_user` ("Tracker User") — the create form's dropdown is literally
  `Object.entries(Cn)`.
- **evidence**: 403 measured (bare). Shape from the roster table at offsets 1966900–1968000.
- **traps**: dual-verb URL — `POST` creates a tracker user (with a plaintext `password`
  in the body). Deleting one can silently downgrade to a deactivate: the client reads
  `.deactivated` off the DELETE response and says "had history — deactivated instead".
  So `is_active: false` rows are tombstones, not merely disabled staff.

---

### `/api/tracker/admin/users/`

- **command**: `tracker admin-users`
- **verdict**: publish
- **description**: Every OMS user with the tracker stages they are allowed to work —
  the stage-access matrix. Answers "who can act on invoices at the SAP Approval desk?"
- **params**:
  - `search` — string, optional. Sourced from the call site
    `Y.get('/tracker/admin/users/', {params: e ? {search: e} : {}})` at offset 1904664;
    the SPA passes the text typed into its "Search users…" box.
- **response**: `array` — **UNVERIFIED** (403, gate A). Items: `{id, username, name,
  role, stage_ids: [int]}`, where `stage_ids` are `admin-stages[].id`.
- **evidence**: 403 measured (bare). Shape from the access matrix at offsets 1961123–1962600.
- **traps**: this returns **all** OMS users, not only tracker ones — it is the grant
  screen, so it has to. `stage_ids` is the actual permission that gate B checks against;
  an empty `stage_ids` is why a user gets "You do not have access to this tracker page."
  Confidence on that causal link: medium — it is the only stage-grant surface in the
  app, but I could not read either endpoint to confirm.

---

## Excluded — writes, every one of them

RULE 0. These are recorded so the assembler can deny them by normalised path; none is
published, none was probed, and none gets a "warning" wrapper inside `endpoints[]`.

### `/api/tracker/actions/bulk`
- **verdict**: exclude — **write verb** (`POST`). Bulk stage action: advance, return,
  reject, hold, debit a set of invoices at once. Body `{ids[], action|stage_status,
  remarks, hold_type, amount}`; returns `{processed_count, errors[]}`. This is the
  single most consequential write in the domain — it moves money-bearing documents
  between desks.

### `/api/tracker/jsap/sync`
- **verdict**: exclude — **write verb** (`POST`). Pulls JSAP's decisions and
  auto-advances/returns invoices accordingly. Body `{}` or `{invoice_id}`; returns
  `{advanced[], returned[], waiting[]}`. Reads from JSAP but *writes* to OMS.

### `/api/tracker/invoices/{id}/payment`
- **verdict**: exclude — **write verb** (`PATCH`). Records discount %, TDS %, hold
  add-back and paid amount against an invoice at a terminal stage; closes it when
  fully paid.

### `/api/tracker/admin/lookups/{type}/{id}`
- **verdict**: exclude — **write verb** (`PATCH`, `DELETE`). Edit/remove one picklist value.

### `/api/tracker/admin/stages/{id}`
- **verdict**: exclude — **write verb** (`PATCH`, `DELETE`). Edit/remove a workflow stage.

### `/api/tracker/admin/tracker-users/{id}`
- **verdict**: exclude — **write verb** (`PATCH`, `DELETE`). Edit/deactivate a tracker user.

### `/api/tracker/admin/users/{id}/stages`
- **verdict**: exclude — **write verb** (`PUT`). Sets a user's `stage_ids` — this is the
  grant that opens the 403 wall. Precisely the endpoint an agent must never be able to call.

### Dual-verb URLs — publish the GET, deny the write, and do not key the denial on path alone

| path | published | denied on the same URL |
|---|---|---|
| `/api/tracker/invoices/` | GET | POST (create invoice) |
| `/api/tracker/invoices/{id}/` | GET | PATCH (edit), DELETE (remove) |
| `/api/tracker/admin/lookups/{type}/` | GET | POST (add value) |
| `/api/tracker/admin/stages/` | GET | POST (add stage) |
| `/api/tracker/admin/tracker-users/` | GET | POST (create user) |

---

## Domain summary

**What it is.** The OMS tracker is JIVO's expense-invoice workflow: a vendor bill is
keyed in at Head Office, then walks a configurable ladder of desks (`entry` →
`sap_approval` → `jsap_approval` → … → a terminal payment desk), each with a day
threshold, each able to advance, return with remarks, hold, or raise a debit. It exists
to answer "where is this bill and who is sitting on it", and its reports are pure
bottleneck analysis — average days per stage, slowest people, slowest vendors. It is a
separate little application inside OMS with its own users, its own roles, and its own
admin screen, and it reaches sideways into **JSAP** and into SAP B1 document drafts.

**Domain-wide traps.**
1. **Everything here is 403 for a normal OMS admin.** Tracker access is granted per
   user via `stage_ids`, independently of the OMS role. A CLI operator running these
   commands with an ordinary admin login will get 403 on all 15, and that is correct
   behaviour, not a broken command. The command descriptions should say which of the
   two gates applies so the operator knows whether to ask for "tracker access" or
   "tracker admin".
2. **Every response shape in this study is UNVERIFIED.** Read out of the SPA, never
   observed on the wire. Field names are as reliable as minified React can make them;
   *types* are guesses (numeric-looking money fields may well be DRF decimal strings —
   the client wraps almost all of them in `Number(...)`, which hints they arrive as strings).
3. **`branch` is overloaded three ways across this API.** Tracker `branch` = an integer
   lookup id. HANA `branch` = `OIL|BEVERAGE`. `category` in `/api/sap/parties/` =
   `OIL|BEVERAGES|MART`. Nothing about the names warns you.
4. **The brief's `stage` param on `my-queue` is wrong** — a 160-char context window in
   `extract_calls.py` bled into the adjacent `getStageAdvanced`. `my-queue` takes no
   parameters. Worth fixing in the harvester: attribute params only within the same
   call expression, not within N trailing characters.
5. **`all-invoices/export` returns a binary workbook**, not JSON. The shipped spec says
   `type: object` and would break on a successful call.
6. **The permission check fires before parameter validation.** Every 403 here was
   returned before the server looked at the query string, so — unlike the rest of this
   API, where a bare probe makes the server name its own required params (API-FACTS §4)
   — the tracker told us nothing about required parameters. That is why so much of this
   study leans on the bundle.

**Backend defect.** The SPA grants a global `admin` every tracker page
(`Dn(role, role === 'admin')`, offset 234035) and the API then refuses every call that
page makes, with a message the client has never heard of (neither 403 string appears in
the bundle). Result: a broken menu for every OMS admin, and an unhelpful "Failed to
load…" toast. Reproduction: log in as a role-`admin` user without tracker grants, open
`/Tracker_Queue`. Either the sidebar should stop trusting `role === 'admin'`, or the
server should honour it.

**Durable JIVO business truth worth recording as a correction.** *(recommendation, not
yet recorded — and I would want it confirmed against a live tracker-enabled payload
before it is written down, since the whole shape is bundle-derived.)*
> OMS's invoice tracker is a **separate access grant** from the OMS role. Being a
> global OMS `admin` grants no tracker access at all — the tracker checks per-user
> stage assignments (`/api/tracker/admin/users/` → `stage_ids`) and a distinct
> tracker-admin flag. Two different 403 messages distinguish them: "You do not have
> access to this tracker page" = no stage grant; "Tracker administration is restricted
> to tracker admins" = has stages, is not a tracker admin.

---

## What remains UNVERIFIED — explicit list

- **Every response shape and every field name in this study.** All 15 published
  endpoints. Source: the deployed SPA bundle. Not one live payload was seen.
- **Every field's type.** Array-vs-object is well supported; `int` vs `string` for
  money and ids is not.
- **`stage-advanced`: whether `stage` is required**, and the full set of valid codes
  (only `entry`, `sap_approval`, `jsap_approval` are sourced; the rest are DB rows).
- **`tracker invoices`: whether it accepts any filter params at all**, and what it is
  scoped to server-side.
- **`admin/lookups/{type}`, `invoices/{id}`, `invoices/{id}/jsap`: no status code at
  all.** Never probed (parameterised). Their gate assignment is inferred from siblings.
- **`all-invoices/export` content type.** Inferred from `responseType: 'blob'` and the
  `.xlsx` filename, not from a header.
- **Pagination.** No endpoint here shows page controls in the SPA; whether the server
  paginates `all-invoices` anyway is unknown.
- **Which SAP company database `tracker vendors` card codes belong to.** Not stated in
  the payload shape and not determinable from the bundle.
- I did **not** attempt any parameterised live call. Every list endpoint that could
  have supplied a real id returned 403, and rule 2 forbids inventing one.
