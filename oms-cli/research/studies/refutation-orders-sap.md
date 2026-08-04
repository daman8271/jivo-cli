# Adversarial refutation — study-orders.md and study-sap.md

Verified 2026-08-04 against the live `https://oms.jivo.in` API (GET only, ~330
requests) and against SAP HANA (`JIVO_OIL_HANADB` / `JIVO_BEVERAGES_HANADB` /
`JIVO_MART_HANADB`, read-only). No write verb was issued. None of the forbidden
paths was touched.

**Headline: 4 REFUTED, 1 UNPROVEN, 1 right-answer-wrong-method, plus 1 pipeline
hazard that belongs to neither study. Two of the refutations will ship broken if
they are not fixed** — one silently cripples `orders list --status`, one tells
operators a real SAP document does not exist. Both are fixable by editing the
study text. **None of them means deleting an endpoint.**

The bulk of both studies survived a hostile re-measurement. Where numbers moved,
they moved by live data drift (the order book grew 2,163 → 2,165 during the gap),
not by error.

---

## 1. Publish / exclude verdicts

### "33 paths. **25 publish, 8 exclude** (all 8 exclusions are write verbs)." (orders)
- **verdict**: CONFIRMED
- **evidence**: All 25 published paths re-fetched live. Every one returned 200,
  or a 400 that names its own required param (`orders/addresses/` →
  `{"error":"card_code is required"}`; `orders/status-tracking/` →
  `{"error":"mode must be auditor, billing, or rate_approver"}`). None is a
  write. Coverage checked against `briefs/brief-orders.md`: all 33 brief paths
  are accounted for (the 9 that appear "missing" to a grep are the brief's `{}`
  placeholder vs the study's `{id}`/`{card_code}`/`{user_id}`).
  Exclusions checked against the harvest rather than by probing: in
  `harvest-calls.json` every one of the 8 is **write-verb-only** —
  `/orders/create/` POST, `/orders/create-scheme/` POST,
  `/orders/{}/cancel-quotation/` POST, `/orders/{}/delete-draft/` DELETE,
  `/orders/{}/update-status/` POST, `/orders/notifications/{}/` PATCH,
  `/orders/schemes/{}/` DELETE+PATCH, `/orders/web-push/subscribe/` DELETE+POST.
  **No GET appears on any of them.** Nothing was wrongly excluded.
- **impact if the study is wrong**: n/a.

### "11 paths. 8 publish (all GET), 3 exclude (all writes)." (sap)
- **verdict**: CONFIRMED
- **evidence**: All 8 published paths re-fetched live, all 200 except
  `sap/parties/category/` bare → 400 (its documented required param). All 11
  brief paths covered. `/sap/approve-sales-order/` and `/sap/sync/{}/` are
  POST-only in the harvest. `/api/service-layer/invoice/` — see the warning below.
- **impact if the study is wrong**: n/a.

### ⚠️ Not a study error, but it will ship broken: `/api/service-layer/invoice/` is absent from `harvest-calls.json`
- **verdict**: CONFIRMED HAZARD (against the pipeline, not the study)
- **evidence**: `/api/service-layer/invoice/` and `/api/orders/list/` are both
  **absent from `harvest-calls.json` entirely** (they appear only in
  `harvest-literals.json`). This is exactly the shape-B / shape-C extraction
  bias API-FACTS §1 predicts. The sap study excludes the invoice POST correctly,
  but it does so by reading the bundle by hand — **the exclusion cannot be
  derived from the harvest, because the harvest never recorded the call.**
- **impact**: an assembler that builds its write-denylist by iterating
  `harvest-calls.json` will not deny the single most dangerous endpoint in this
  API — the one that POSTs a live A/R invoice into SAP B1. The denylist must be
  seeded from the studies' `excluded[]` lists and from API-FACTS §5, never from
  the harvest.

---

## 2. Dual-verb paths

### "Four paths in this domain serve a GET *and* a write on the identical URL (`flow-config`, `notifications`, `party-flow-config`, `staff-products`) … the assembler must key on **(path, method)**."
- **verdict**: CONFIRMED
- **evidence**: all four GETs live and working —
  `orders/flow-config/` 200 / 808 B (`flow_type: ASM`, three gates enabled);
  `orders/notifications/` 200 / `[]`;
  `orders/party-flow-config/` 200 / 1,197 B / 2 rows (CUSTA000486 WAL MART INDIA
  PVT LTD and CUSTA000606 JIVO MART PVT LTD, both OIL, both flow BILLING —
  `card_name` is present, as the study says);
  `orders/staff-products/` 200 / `[]`.
  The harvest independently confirms the verb pairs and confirms the set is
  exactly four in this domain: `flow-config` GET+POST, `notifications` GET+POST,
  `party-flow-config` GET+POST+DELETE, `staff-products` GET+POST. Both the
  study (§ intro and § Dual-verb) and API-FACTS §5 state the (path, method)
  requirement explicitly.
- **impact if the study is wrong**: n/a — it is right.

### ⚠️ REFUTED: API-FACTS §5's dual-verb list is INCOMPLETE — it omits a fifth GET
- **verdict**: REFUTED (the *enumeration* is wrong; do not delete anything)
- **evidence**: `harvest-calls.json` shows `/auth/users/{}/page-permissions/`
  carries **GET and PUT on the identical URL**. It is not in API-FACTS §5's
  dual-verb list, and its PUT is not in API-FACTS §5's write list either
  (§5 lists `auth/users/{id}` PUT, which is a different path). `study-account.md`
  caught it independently (line 780: "GET published, **PUT excluded**"), so the
  account study is fine — API-FACTS is not.
  Full harvested dual-verb set: `orders/flow-config/`, `orders/notifications/`,
  `orders/party-flow-config/`, `orders/staff-products/`,
  **`auth/users/{}/page-permissions/`**, `tracker/admin/lookups/{}/`,
  `tracker/admin/stages/`, `tracker/admin/tracker-users/`, `tracker/invoices/`,
  `tracker/invoices/{}/`, `ui-config/admin/labels/`.
- **impact if the study is wrong**: if the assembler builds its denylist from
  API-FACTS §5's dual-verb list rather than from each study's `excluded[]`, it
  will path-key `auth/users/{id}/page-permissions/` and **silently kill a
  published read** — the "which admin screens can this user see" command. There
  is a second trap in the same row: a denylist that normalises
  `auth/users/{id}` (PUT) as a *prefix* kills it too.

---

## 3. The orders/list claims

### "bare … 263 rows … `dashboard summary` reports `total_orders: 2163` … `?status=COMPLETED` alone returns 1,898 … The intersection of the bare list and the completed list is **2 rows**."
- **verdict**: CONFIRMED (numbers drifted up with live data; the shape is exact)
- **evidence**: live now — bare 263 rows / 100,443 B; `?status=COMPLETED`
  **1,900** rows; `dashboard summary.total_orders` **2,165**. Intersection of the
  two id sets = **exactly 2** (ids `1570`, `2493`). Union 2,161 of 2,165.
  `status_counts` sums to 2,165, matching `total_orders`. The study's 263 /
  1,898 / 2,163 is the same measurement two hours earlier. The shipped baseline
  spec's description — `"All orders (admin-wide). Filter by status/stage."`
  (`/tmp/base/oms-cli/oms-spec.yaml:107`) — is confirmed wrong.
- **addendum the study missed**: bare is not complete for the *non-completed*
  statuses either. `?status=REJECTED` returns **207** rows while bare contains
  only **204** REJECTED, and bare holds 40 BILLING_REJECTED against
  `status_counts`' 41. So bare drops 4 open-book orders as well as ~1,898
  completed ones. Does not change the verdict; makes the trap stronger.

### "**Accepts a comma-separated list** — the app does `lt(e).join(',')` before calling."
- **verdict**: CONFIRMED — this was the claim I most expected to break, and it held
- **evidence**: `?status=RATE_APPROVAL` → 6 rows, all `RATE_APPROVAL`.
  `?status=APPROVED` → 2 rows, all `APPROVED`.
  `?status=RATE_APPROVAL,APPROVED` → **8 rows = 6 RATE_APPROVAL + 2 APPROVED**,
  3,086 B. `?status=APPROVED,RATE_APPROVAL` → byte-identical 8 rows, so it is
  order-independent — a real `IN`-list, not a string match that happens to work.
  A single-value exact match would have returned 0.
- **impact if the study is wrong**: n/a.

### "**`approval_pending=true` alone is a no-op** — byte-identical to bare."
- **verdict**: CONFIRMED
- **evidence**: bare and `?approval_pending=true` both 100,443 B with identical
  status histograms. `?status=RATE_APPROVAL&approval_pending=true` → 2,313 B,
  byte-identical to `?status=RATE_APPROVAL` alone. The param never changes a result.

### ⚠️ REFUTED: "**`billing=true` is a queue selector, not a status filter.** … Combining it with `status` gives 44, which is neither an intersection nor a union."
- **verdict**: REFUTED — the headline ("queue selector") is right; the stated
  *mechanism* is wrong, and the real mechanism is more dangerous
- **evidence**: `billing=true` does not compose with `status` at all — **it makes
  the server discard `status` entirely.** Six query strings, two independent runs,
  all returning the byte-identical 17,888-byte body (`sha256 ec46bea041d5…`):

  | query | bytes | sha |
  |---|---|---|
  | `?billing=true` | 17,888 | `ec46bea041d5` |
  | `?status=BILLING&billing=true` | 17,888 | `ec46bea041d5` |
  | `?status=COMPLETED&billing=true` | 17,888 | `ec46bea041d5` |
  | `?status=REJECTED&billing=true` | 17,888 | `ec46bea041d5` |
  | `?status=DRAFT&billing=true` | 17,888 | `ec46bea041d5` |
  | `?billing=true&approval_pending=true` | 17,888 | `ec46bea041d5` |

  Control, same session: `?status=COMPLETED` → 732,713 B, `?status=REJECTED` →
  78,722 B, `?status=DRAFT` → 2 B. `status` alone unquestionably filters.
  The study's 44-vs-45 was one row of drift between two calls, read as a rule.
- **impact if the study is wrong**: the study's *advice* ("do not document them
  as composable filters") happens to yield safe CLI behaviour, so nothing
  crashes. But an operator who runs `orders list --status COMPLETED --billing`
  gets the 46-row billing queue and will read it as "completed orders in
  billing". The CLI must either reject `--status` together with `--billing`, or
  print that `--status` was ignored. As written, the study does not tell the
  generator that.

### ⚠️ REFUTED: "Only 8 of the 11 codes were observed live — `Need Approval`, `Billing Pending` and `Draft` have no confirmed code" / "Nothing in the API maps between them."
- **verdict**: REFUTED — the mapping is published live, on an endpoint this same
  study publishes and called five times
- **evidence**: `GET /api/orders/dashboardW/charts/` → `status_distribution`
  carries all eleven `{status, label, count}` triples, in the exact order of
  `orders status`' ids 1–11 and with labels identical to
  `dashboard summary.status_counts`' keys:

  ```
  CREATED/Order Created · RATE_APPROVAL/Rate Approval · BILLING/Billing ·
  NEED_APPROVAL/Need Approval · BILLING_PENDING/Billing Pending ·
  APPROVED/Approved · REJECTED/Rejected · BILLING_REJECTED/Billing Rejected ·
  COMPLETED/Completed · AUDITOR_APPROVAL/Auditor Approval · DRAFT/Draft
  ```

  This is a live payload, so under contract rule 2 all eleven are *observed*
  values. Sent to the server they behave as real filters, not ignored params:
  `?status=DRAFT`, `?status=NEED_APPROVAL`, `?status=BILLING_PENDING` and
  `?status=DRAFT,NEED_APPROVAL,BILLING_PENDING` each return `[]` (2 B) — **not**
  the 263-row bare body an ignored param returns. Zero rows because those
  buckets are currently empty (`status_distribution` counts them 0), not because
  the codes are unknown.
- **impact if the study is wrong**: **this is the silent regression.**
  `orders list --status` ships with an 8-value enum instead of 11, and the
  generator is told the three vocabularies cannot be mapped when the API maps
  them itself. `DRAFT` is the expensive one: the study elsewhere says "Drafts are
  only reachable [via `ordersbyuser`] … There is no server-side draft filter."
  There is one — `orders list --status DRAFT`. A whole capability would ship
  missing, and `dashboard charts` would ship without the code↔label table being
  documented as the authoritative status map.

---

## 4. The undocumented filters, and the silently-ignored-sibling trap

### "the same param name works on one endpoint and is silently ignored on its sibling — `category` filters `products` but not `parties`; `search` filters `parties` but not `parties/category/`; `card_code` filters `addresses` but not `parties`."
- **verdict**: CONFIRMED — every pair reproduced byte-for-byte
- **evidence**: SHA-256 of each body (first 12 hex), same session:

  | call | rows | bytes | sha |
  |---|---|---|---|
  | `sap/parties/` bare | 3,358 | 620,913 | `495878c07899` |
  | `sap/parties/?category=OIL` | 3,358 | 620,913 | `495878c07899` ← **identical** |
  | `sap/parties/?card_code=CUSTA000001` | 3,358 | 620,913 | `495878c07899` ← **identical** |
  | `sap/parties/?card_type=C` | 3,358 | 620,913 | `495878c07899` ← **identical** |
  | `sap/parties/?search=RAJ MANDIR` | 8 | 1,558 | `01348eba96ec` |
  | `sap/parties/?main_group=GT` | 2,088 | 380,829 | `41cee3a66397` |
  | `sap/parties/?state=DL` | 1,252 | 230,872 | `3e2e92873c54` |
  | `sap/products/` bare | 2,637 | 1,010,130 | `cb7128c22876` |
  | `sap/products/?category=OIL` | 1,442 | 549,720 | `f4501d547c30` |
  | `sap/products/?brand=SANO` | 116 | 44,369 | `adf46eab6e1f` |
  | `sap/products/?search=POMACE` | 123 | 46,972 | `2d82c71fe220` |
  | `sap/products/?variety=POMACE` | 2,637 | 1,010,130 | `cb7128c22876` ← **identical** |
  | `sap/products/?sub_group=OLIVE` | 2,637 | 1,010,130 | `cb7128c22876` ← **identical** |
  | `sap/products/?type=COMMODITY` | 2,637 | 1,010,130 | `cb7128c22876` ← **identical** |
  | `sap/products/?category=OIL&search=OLIVE` | 176 | 68,225 | `f65cad5e27eb` |
  | `sap/addresses/` bare | 35,722 | 11,798,113 | `c55a3c1605d5` |
  | `sap/addresses/?card_code=CUSTA000001` | 20 | 7,052 | `1dd69cae5c48` |
  | `sap/addresses/?category=OIL` | 35,722 | 11,798,113 | `c55a3c1605d5` ← **identical** |
  | `sap/addresses/?state=DL` | 35,722 | 11,798,113 | `c55a3c1605d5` ← **identical** |
  | `sap/branches/?category=OIL` | 22 | 3,666 | identical to bare |
  | `sap/parties/category/?category=OIL&search=…` | 1,172 | 283,978 | identical to `?category=OIL` |
  | `sap/logs/?page=2` / `?offset=100` / `?triggered_by=manual` | 50 | 13,682 | identical to bare |
  | `sap/logs/?limit=100000` | 851 | 702,676 | ids 1–851 |
  | `sap/logs/?status=FAILED` / `?sync_type=PARTY` | 50 / 50 | 28,969 / 13,557 | real filters |

  Every "works" and every "ignored" verdict in the study's § Traps table 4 is
  reproduced exactly, including the study's own byte figures. The
  `?variety=` / `?sub_group=` / `?type=` trio is the worst of them: those are
  the three fields correction **C-0003** tells operators to segment on, and all
  three are accepted-and-discarded.
- **impact if the study is wrong**: n/a — it is right, and this is the single
  most valuable finding in the sap study.

### "The shipped spec declares one param across eight endpoints; live testing found ten working ones."
- **verdict**: CONFIRMED, with a counting caveat
- **evidence**: the shipped baseline (`oms-cli-baseline-20260804-1426.tar.gz` →
  `oms-cli/oms-spec.yaml`) declares, across the eight `/api/sap/` paths, exactly
  one query param (`category` on `parties/category/`) plus one positional path
  param (`id` on `quotation-log/{id}/`). Confirmed. "Ten" counts **distinct
  param names** (`card_code`, `address_type`, `limit`, `sync_type`, `status`,
  `search`, `main_group`, `state`, `category`, `brand`); there are **13 working
  (endpoint, param) pairs**. Both readings are defensible; the generator needs
  the 13, not the 10.
  While there: the baseline declares `type: object` for **all 73** endpoints
  (`grep -c 'type: object'` = 73, `type: array` = 0) and `name: branch` **zero**
  times — API-FACTS §2 and contract rule 6 both independently confirmed.

### "`sap/logs`: whether the filters compose … I did not test the pair."
- **verdict**: gap now closed — they DO compose
- **evidence**: `?sync_type=PARTY&status=FAILED&limit=100000` → 200, 12 rows,
  6,553 B. Honest disclosure by the study; the answer is AND.

---

## 5. The three-company coverage claim

### "the read mirror covers all three companies … verified by exact row-count identity, not inference."
- **verdict**: CONFIRMED — independently reproduced against HANA, and it is
  stronger than the study claims
- **evidence**: live OMS GET vs `SELECT COUNT(*)` in the same hour:

  | OMS | SAP table | Oil | Beverages | Mart |
  |---|---|---|---|---|
  | `sap/parties` per `category` | `OCRD` `CardType='C'` | 1172 = **1172** | 1247 = **1247** | 939 = **939** |
  | `sap/branches` per `category` | `OBPL` | 8 = **8** | 6 = **6** | 8 = **8** |
  | `sap/addresses` per `category` | `CRD1` | 12869 = **12869** | 11420 = **11420** | 11433 vs **11432** |

  `sap/parties/category/` returns 1,172 / 1,247 / 939 = 3,358 = the whole
  `sap/parties` body, a clean partition. The one extra address is exactly the row
  the study named: `id 24226`, `CUSTA000912`, "BETOND LETTUCE SALADS HYDERABAD",
  MART, `synced_at 2026-07-20` — and it is the *only* row in 35,722 not stamped
  `2026-08-04`. The never-deletes finding is exact.
  The `sap/products` subset claim is also exact, and better than stated:
  Mart `OITM` valid+unfrozen by prefix = FG 430, SC 57, PM 45, RM 10, CG 6,
  **SL 250, FA 6** (804 total); OMS mirrors FG 430, SC 57, PM 45, RM 10, CG 6 =
  **548**, i.e. 804 − SL(250) − FA(6) = 548, matching per prefix, to the row.
  Uniqueness traps verified: 3,358 parties carry 1,254 distinct `card_code`;
  2,637 products carry 1,747 distinct `item_code`; `bpl_id 1` = DELHI in all
  three companies; `CUSTA000025` = "HARPREET SINGH CASH SALE" in OIL but
  "CASH SALE FACTORY" in BEVERAGES and MART. All exact.
- **impact if the study is wrong**: n/a.

### "40 sampled `sap_doc_num` values → 21 Oil `ORDR`, 19 Beverages `ORDR`, **0 Mart**, 0 `OQUT`."
- **verdict**: CONFIRMED as to the conclusion — but the **sampling is biased and
  cannot carry it**. I replaced the sample with population evidence.
- **evidence, on the sampling**: the study's 43 ids gave a 39/43 = 91 % hit rate.
  I drew 90 ids **stratified across the whole id range (1 → 2499)** and got
  14/90 = **15.6 %**. The study's ids came from the recent end of
  `quotation-overview`, where a quotation-log row almost always exists. Presented
  as "43 real order ids", that reads as a random draw. It is not one. Across my
  own 220 sampled orders the 404 rate was 77/220 = 35 %.
- **evidence, on the conclusion (population, not sample)**: four independent
  population-level facts, any one of which is stronger than n=40 —
  1. `JIVO_MART_HANADB.OQUT` contains **0 rows, all time** (Oil 1,692;
     Beverages 733). No OMS quotation has ever reached Mart.
  2. The DocNum band my 138 distinct `sap_doc_num` values occupy
     (1726076786–1726088021) contains **288 Oil `ORDR` + 476 Beverages `ORDR` +
     0 Mart `ORDR`**, and **0 `OQUT` in any company** — so quotation-log numbers
     are `ORDR`-only, at n=138 rather than n=40.
  3. Mart's **all-time maximum** `ORDR.DocNum` is 1,725,031,645 — *below the
     entire band*. Mart's numbering has never entered the range OMS writes into.
  4. OMS's own aggregate says so: `dashboardW/charts` → `category_sales` =
     `[{OIL, 3183}, {BEVERAGES, 1417}]`, **no MART row**, and all 313
     `top_parties` are OIL (170) or BEVERAGES (143). **OMS raises zero Mart
     orders in the first place.**
- **impact**: the correction is safe to record. But fact 4 changes what it should
  *say*. The proximate truth is "**no Mart order exists in OMS at all**"; the
  capability limit ("can only write into Oil and Beverages") rests on the
  `/api/hana/*` 400 body and the `qfe` source function, which is good evidence
  but is a different claim. The correction should carry both, or an operator will
  read "Mart is read-only from OMS" as a permission story when it is currently
  also a usage story.

### ⚠️ REFUTED: "**Only the quotation-log pair resolves to a real SAP document.**"
- **verdict**: REFUTED — both pairs resolve. The `quotation-overview` numbers are
  real SAP sales quotations.
- **evidence**: four orders, `quotation-overview`'s `(doc_num, doc_entry)`
  matched against `OQUT` in all three companies. **4/4 hit, DocEntry included:**

  | OMS order | quotation-overview | resolves to |
  |---|---|---|
  | 2392 | `232607218 / 15746` | **Oil** `OQUT` DocEntry 15746, DocNum 232607218, CUSTA000451, 2026-07-30, DocTotal 4,788,000, DocStatus `O` |
  | 2169 | `232607252 / 1256` | **Bev** `OQUT` DocEntry 1256, DocNum 232607252, CUSTA001141 |
  | 2189 | `232607253 / 1259` | **Bev** `OQUT` DocEntry 1259, DocNum 232607253, ORGC000001 |
  | 2190 | `232607254 / 1261` | **Bev** `OQUT` DocEntry 1261, DocNum 232607254, CUSTA000339 |

  Order 2392 in full: `quotation-overview` → `OQUT` 15746 (the quotation, still
  open, ₹47.88 L); `sap/quotation-log` → `ORDR` 29554 / DocNum 1726076971, same
  CardCode CUSTA000451, same DocTotal, one day later. Two real documents, one
  transaction. (They are not linked in SAP — `RDR1` DocEntry 29554 has
  `BaseType -1` — so the order was raised independently of the quotation.)
  The study's other half is correct and confirmed: `sap/quotation-log` returns an
  `ORDR`, not an `OQUT`, so the endpoint *name* is wrong. That finding stands.
- **impact if the study is wrong**: as written, a CLI would tell an operator that
  the doc number on `quotations overview` — the number on 1,582 of 1,900 rows,
  the one the OMS screen shows them — is not a real SAP document. It is. It is
  the sales quotation, findable in SAP B1 under that exact DocNum. This is the
  refutation most likely to produce a confidently wrong answer to Accounts.
- **additional trap the study missed**: `doc_num` is **not unique across
  companies** either, exactly like `card_code`/`item_code`/`bpl_id`. DocNum
  `232607218` is Oil `OQUT` DocEntry 15746 (CUSTA000451) **and** Beverages
  `OQUT` DocEntry 1201 (ORGC000024) — two different documents. The study's own
  `(category, code)` rule applies to document numbers and it does not say so.

### "60 of the 72 failed sync runs name their source: `SAP connection failed (103.89.45.75:1433/Jivo_All_Branches_Live)`."
- **verdict**: UNPROVEN as stated — the count is wrong; the conclusion is right
- **evidence**: `sap/logs?limit=100000` → 851 runs, 762 SUCCESS / 72 FAILED /
  17 STARTED (all three counts exact). Of the 72 failures, **64** mention the
  host `103.89.45.75` and only **23** carry the database name
  `Jivo_All_Branches_Live`; the other 41 are the bare DB-Lib 20009 form, which
  names the host but not the database. Neither number is 60.
  The substantive conclusion survives untouched: 23 messages name
  `103.89.45.75:1433/Jivo_All_Branches_Live` verbatim, the error family is
  DB-Lib/TDS (SQL Server, not HANA), and a separate failure names the
  destination as Postgres (`relation "sap_products" does not exist`). Every other
  logs finding is exact: `triggered_by` = 823 manual / 13 Admin / 10 preshit /
  3 admin / 1 live-key-migration / 1 empty; 17 stuck `STARTED` with
  `completed_at: null`, latest `2026-07-28T05:27:29Z`; the `'18%'` decimal break;
  `name 'transaction' is not defined`.
- **impact if the study is wrong**: nothing ships broken — but "60" appears in a
  section headed "from the server's own error text", which sets an accuracy
  expectation the number does not meet. Change it to 64 (host) or 23 (database).

---

## 6. `orders quotation-status` returns 200 with `success:false`

### "**The endpoint returns HTTP 200 while failing** … which is why all 1,898 of its rows read `quotation_status: UNKNOWN`."
- **verdict**: CONFIRMED, exactly, including the `&branch=OIL` disproof
- **evidence**:
  ```
  GET /api/orders/quotation-status/?order_ids=2392,2190,2189,2169,2168
    -> HTTP 200 {"success":false,"statuses":{},
        "error":"SalesOrderService.get_quotation_status() missing 1 required
                 positional argument: 'branch'"}
  ...&branch=OIL                          -> HTTP 200, identical error
  ?order_ids=2392                         -> HTTP 200, identical error
  ?order_ids=2530,2528,2529 (no SAP doc)  -> HTTP 200 {"success":true,"statuses":{}}
  bare                                    -> HTTP 200 {"success":true,"statuses":{}}
  ```
  And `GET /api/orders/quotation-overview/` → 200, **1,900 rows, every single one
  `quotation_status: "UNKNOWN"`** (`Counter({'UNKNOWN': 1900})`), with the
  identical message in the response's own `sap_error` field. 1,582 rows carry a
  `doc_num`, 0 are cancelled — both figures unchanged from the study.
  Bonus check the study asserted but did not prove: the `quotation-overview` id
  set is **exactly equal** to the `?status=COMPLETED` id set (1,900 = 1,900,
  symmetric difference 0), not merely equal in count.
- **impact if the study is wrong**: n/a. The "surface `success` and `error`, do
  not trust the status code" instruction is correct and necessary.

---

## 7. CORRECTION-params compliance, and the `mode` disproof

### "If your study asserted any param in the 'was wrongly credited' column, drop it."
- **verdict**: CONFIRMED — neither study asserts a single one
- **evidence**: all six wrongly-credited pairs checked against both studies.
  `mode` on `/api/orders/status/` → the orders study calls it "a **false
  attribution**" and disproves it. `order_ids` on `/api/orders/{id}/orderlogs/` →
  "**NOT a param of this endpoint**". `flow_type` on
  `/api/orders/staff-products/` → "**false attribution**", params documented as
  none. `category` on `/api/sap/addresses/` → "The brief says `category` was
  observed at the call site. **It was not.**" `category` on `/api/sap/parties/` →
  listed as ignored, with `search` (the genuine one) kept. `stage` on
  `/api/tracker/my-queue/` is outside both studies. Zero contamination.

### "**Disproved live**: `?mode=auditor` and `?mode=billing` both return the same 335-byte body as the bare call."
- **verdict**: CONFIRMED — reproduced, and extended to the third enum value
- **evidence**: `GET /api/orders/status/` bare, `?mode=auditor`, `?mode=billing`
  and `?mode=rate_approver` all return 200 / **335 bytes** / SHA-256
  `9b7d9c0f0643…` — four byte-identical bodies. The param has no effect. By
  contrast `orders/status-tracking/` bare → 400 naming the same enum, so the
  three values genuinely are real *there*. The disproof holds; the two `mode`s
  must not share a flag definition.

---

## Other study claims spot-checked (all CONFIRMED, no action)

- `orders/addresses`: `?card_code=CUSTA000636` → 105 bill_to + 105 ship_to;
  with `&category=OIL`/`BEVERAGES`/`MART` → 35 + 35 each. The bare call is the
  union of all three SAP companies, exactly as claimed. `is_fallback` appears
  only when both lists are empty (`CUSTA001216&category=OIL` →
  `{"bill_to":[],"ship_to":[],"is_fallback":false}`).
- `dispatch_from_id` trap: orders 2530, 2528, 2493, 1570 all report
  `dispatch_from_id: 2` / `"FACTORY"` = the `bpl_id` from `orders branch`
  (`"2"`, a **string** there), while `orders dispatches` has `id: 4`. Joining on
  `id` is wrong. Confirmed on all four.
- `sap_doc_number` null on `orderdetailsbyid`: orders 2392, 2190, 2189, 2169 →
  `null` with `sap_created: true`, while `orders list` and `quotation-overview`
  both carry the number. Confirmed on all four.
- `vareity_cost` typo present, `variety_cost` absent, on all four orders checked.
- `created_by` type drift: int (54, 40, 33, 5) on detail vs display-name string
  on `orders list`. Confirmed.
- `orders schemes`: bare 72 rows → `?state_code=UP` 4 rows. Confirmed.
- `sap/quotation-log/999999/` → clean **404**
  `{"success":false,"message":"Quotation log not found"}`, no crash. Confirmed.
- `sap/branches.is_active` true for exactly 1 of 22 rows (`OIL / bpl_id 2 /
  FACTORY`). Confirmed.
- `sap/parties/category/?category=BEVERAGE` (singular) → **HTTP 200,
  `{"success":true,"data":[]}`**; `?category=oil` → the full 1,172 rows. The
  silent-empty-on-bad-enum trap is real and reproduced. Client-side enum
  validation is mandatory.
- `sap/products.type` blank or null on **1,732 of 2,637** rows. Confirmed.
- No GET in this session created anything: `sap/logs` max id was 851 before and
  after ~330 requests; `orders/schemes` stayed 72 rows and
  `orders/schemes/manage/` stayed 17,823 B across repeated calls.

---

## Summary table

| # | claim | verdict |
|---|---|---|
| 1 | orders 25 publish / 8 exclude; sap 8 / 3 | CONFIRMED |
| 1b | `/api/service-layer/invoice/` absent from `harvest-calls.json` | CONFIRMED HAZARD |
| 2 | four dual-verb GETs work; key on (path, method) | CONFIRMED |
| 2b | API-FACTS §5 dual-verb list omits `auth/users/{id}/page-permissions/` | **REFUTED** |
| 3a | bare 263 vs 2,165 total vs 1,900 COMPLETED, overlap 2 | CONFIRMED |
| 3b | `status` is comma-separated | CONFIRMED |
| 3c | `approval_pending=true` is a no-op | CONFIRMED |
| 3d | `billing=true` "gives 44, neither intersection nor union" | **REFUTED** — it discards `status` |
| 3e | 3 of 11 status codes unknown / nothing maps the vocabularies | **REFUTED** — all 11 published |
| 4 | ten working filters; siblings silently ignore | CONFIRMED (13 pairs, 10 names) |
| 5a | read mirror covers all three companies, exact vs HANA | CONFIRMED |
| 5b | quotation-log reaches Oil+Bev, zero Mart | CONFIRMED — but sampling biased; use population evidence |
| 5c | "only the quotation-log pair resolves to a real SAP document" | **REFUTED** |
| 5d | "60 of 72 failed runs name their source" | **UNPROVEN** — 64 host / 23 database |
| 6 | quotation-status 200 with `success:false` | CONFIRMED |
| 7 | no wrongly-credited param asserted; `mode` disproof | CONFIRMED |
