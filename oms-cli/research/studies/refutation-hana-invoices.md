# Adversarial refutation — `study-hana.md` and `study-invoices.md`

Written 2026-08-04 by an independent verifier whose brief was to **disprove**
these two studies. Every live call below was a `GET` issued with the
`/tmp/oms-rescrape/token.txt` credential (user 62, `paramjot`); no write verb was
sent and none of the forbidden paths was touched. `/api/hana/next-doc-number/`
was **not** re-called with a valid `doc_type` — claim 4 was attacked from
evidence and from read-only HANA instead (see there for why that turned out to be
the stronger attack anyway).

**Score: 2 REFUTED/UNPROVEN out of 7 claim-groups.** One of them — `invoices
skus-pending` — will ship broken and should be fixed before generation. Nothing
that would violate RULE 0 was found: no published GET in either domain creates
anything, verified with a before/after snapshot.

---

### "**11 publish · 6 exclude**" — `/api/sku/pending/` — **verdict: publish** … "Publish the command with the 500 documented. It is a real endpoint with a real purpose"

- **verdict**: **REFUTED** — the *verdict is wrong*; the endpoint should be
  **excluded** (reason: proven dead). I am not saying delete the research: keep
  the write-up, keep the shipped name `invoices skus-pending` reserved,
  re-publish the day the OMS team fixes it. I am saying do not register a command.
- **evidence**: re-verified live today, three forms, all fail identically:

  ```
  GET /api/sku/pending/                  -> 500, 97,669 bytes
  GET /api/sku/pending/?branch=OIL       -> 500, 98,136 bytes
  GET /api/sku/pending/?branch=BEVERAGE  -> 500, 98,211 bytes
  exception_value: SalesOrderService.getFGItems() missing 1 required positional
                   argument: 'branch'
  ```

  This is the **same failure class, from the same half-applied `branch`
  refactor**, that the sibling study excluded as *proven dead*:

  | endpoint | code | cause | study verdict |
  |---|---|---|---|
  | `/api/hana/product-so/` | 500 | `TypeError: Queries.get_sales_orders_for_product() takes 1 positional argument but 2 were given` | **exclude — proven dead** |
  | `/api/hana/product-stock/` | 502 | `NameError: name 'unique_schemas' is not defined` | **exclude — proven dead** |
  | `/api/sku/pending/` | 500 | `TypeError: SalesOrderService.getFGItems() missing 1 required positional argument: 'branch'` | **publish** |

  Two studies, one body of evidence, opposite verdicts. They cannot both be
  right. `study-hana` states the correct rule and states it well: *"a
  deterministic NameError/TypeError on 100% of calls with every valid parameter
  is a command that cannot succeed for anyone. Shipping it would recreate exactly
  the failure this rescrape exists to fix."* By that rule — and by the study
  contract's *"Unproven resolves to excluded"* — `/api/sku/pending/` is excluded.

  The invoices study is also internally inconsistent about it: the entry carries
  **both** `verdict: publish` **and** an `exclusion reason: n/a` line, and the
  header tally says *"Three shipped commands are broken upstream"* while shipping
  one of the three.
- **impact if the study is wrong**: the generated CLI ships `invoices
  skus-pending`, a command that can **never** return data — 19% of the `hana`
  surface being dead on arrival is the stated reason this rescrape exists, and
  this reintroduces the same defect in the invoices domain. Worse, the only thing
  it *can* return is the 97 KB Django debug page, so publishing it turns the CLI
  into a one-command exfiltration tool for the production settings table (HANA
  host `20.20.45.192` + all three company schemas, Postgres host `20.20.45.75`,
  the GST e-invoice NIC usernames, the SMB attachment shares,
  `ALLOWED_HOSTS=['*']`, `CORS_ALLOW_ALL_ORIGINS=True`). A dead command is a
  regression; a dead command that prints secrets on every invocation is a
  liability.

---

### `/api/invoice/all/` — "**exclusion reason**: proven dead"

- **verdict**: **UNPROVEN (label only — the exclusion decision itself is
  CONFIRMED)**. The route is not dead. It is alive, it is a live DRF view, and it
  returns a typed, deliberate 400. "Proven dead" is the wrong word for it and the
  wrong word matters, because a generator that reads *proven dead* as *delete and
  forget* will drop the name reservation the study explicitly asked for.
- **evidence**: reconfirmed live, six param names, one identical body every time:

  ```
  GET /api/invoice/all/                       -> 400 {"error":"Warehouse Code is a required parameter."}
  ?warehouse= ?whs_code= ?warehouse_code=
  ?WarehouseCode= ?WhsCode=   (all with BH-BT) -> 400, identical body
  ```

  Independent corroboration for the study's "it was never in the SPA" claim,
  which it only asserted: `harvest/inventory.json` carries a
  `shipped_not_harvested` list with **exactly one entry — `/api/invoice/all`**.
  The path reached the brief from the shipped spec alone; no lens ever saw the
  app call it. That plus the `OPTIONS` view names (*"Invoice Log List"* vs
  *"Invoice Log List wo Whs"*) makes "superseded by `/api/invoice/logs/all/`" the
  right reading, and makes not registering a command the right call — a shipped
  command that cannot succeed is not a capability anyone loses.
- **impact if the study is wrong**: low, and it is a labelling risk rather than a
  functional one. The study contract's exclusion taxonomy (`write verb | auth
  mutator | proven dead | unsafe`) has no slot for *alive but with an unresolvable
  contract*, so the study picked the nearest word. Recommend the generator record
  it as `unresolved-contract`, keep `invoices all` reserved, and point operators
  at `invoices logs`. If it silently vanishes instead, the next rescrape
  re-discovers this route from the spec and burns another afternoon on the same
  eleven param names.

---

### "12 publish, 2 exclude" (hana) and the remaining 10 publish verdicts (invoices) — is every `publish` genuinely GET-readable and genuinely not a write?

- **verdict**: **CONFIRMED**
- **evidence**: every published path re-called live today. All eleven reachable
  `hana` publishes returned `200` with a **top-level JSON array** (`address` 70,
  `all-customers` 1172, `batch-details` 2, `customer-details` 1, `fg-items` 336
  BEV, `freight-masters` 10 BEV, `inventory-details` 3, `item-price` 1,
  `open-parties` 32 BEV, `salesperson-details` 1, `so` 57). `next-doc-number` was
  deliberately not re-called; the harvest records it `methods=['GET']` and the
  app reads it as an array, so the array claim carries.

  The invoices publishes: `logs/all` 200/23 rows array; `history/{id}` see claim
  5; `credit-limit/cards` bare **byte-identical** to `?company=1` (1172 rows,
  176,607 B) and `?company=2` → 1247 rows / 182,989 B, matching
  `hana/all-customers` per branch exactly; `credit-limit/flow` bare → typed 400,
  and across all 23 ids **2 × 200, 21 × 404** exactly as claimed, with `company`
  inert (`sha256` identical for omitted / `1` / `2` on both id 33 and id 20);
  `sku/all` `[]`; `legal/item` 1 row; `legal/uom`, `legal/nutrition` `[]`;
  `legal/item-nutrition` `{"nutritional_facts":[]}`.

  **The RULE 0 test that mattered — no published GET is a `get_or_create`.**
  Snapshotted `sku/all`, `legal/item`, `legal/uom`, `legal/nutrition`,
  `legal/item-nutrition`; then issued `GET /api/sku/FG0000032|FG0000386|FG0000400/`
  (all 404 `{"detail":"No SKU matches the given query."}`); then re-snapshotted.
  **Byte-identical before and after**, and `legal/item` still holds exactly its
  one row `id:1 "Kachi Ghani Mustard Oil Pouch" created_at 2026-07-27` — i.e.
  neither my probes nor the original study's created anything. The factory
  failure mode does not recur here.

  **No wrongly-excluded read found.** All six invoices exclusions are POST /
  PATCH / multipart in `harvest/inventory.json`. No harvested GET-capable path in
  either domain is absent from its study (hana 14/14, invoices 17/17 against the
  briefs, and the briefs match the harvest). `/api/service-layer/invoice/` — the
  POST that puts a document into SAP B1 — is *not* orphaned: `study-sap.md` owns
  and excludes it.
- **impact if the study is wrong**: n/a — it is not.

---

### "the hana required-param table" — `branch` + `card_code` / `item_code` / `whs_code` / `price_list` / `slp_code` / `doc_type`

- **verdict**: **CONFIRMED** — I could not break it. One addition below.
- **evidence**: all 14 paths called bare → **all 14** returned the identical
  `400 {"error":"branch is required and must be one of: OIL, BEVERAGE"}` (64
  bytes each). All 14, including `product-so` and `product-stock`.

  Branch-only → the server names its own next requirement on the nine that have
  one (`card_code is required` ×3, `item_code and whs_code are required`,
  `item_code is required` ×2, `item_code and price_list are required`,
  `doc_type is required`, `slp_code is required`); the other four
  (`all-customers`, `fg-items`, `freight-masters`, `open-parties`) 200 on branch
  alone, so nothing is missing from their row either.

  Attacking the AND-requirements — is any listed param secretly optional?

  ```
  batch-details ?branch=OIL&item_code=FG0000400   -> 400 item_code and whs_code are required
  batch-details ?branch=OIL&whs_code=BH-BT        -> 400 item_code and whs_code are required
  item-price    ?branch=OIL&item_code=FG0000150   -> 400 item_code and price_list are required
  item-price    ?branch=OIL&price_list=4          -> 400 item_code and price_list are required
  ```

  Both are genuinely conjunctive. No listed param is optional; no unlisted param
  is required (every listed set produced a 200).

  Enum strictness also holds: `branch=oil`, `branch=Oil`, `branch=BEVERAGES`,
  `branch=MART`, `branch=` all → the same 400.
- **impact if the study is wrong**: n/a. Two additions the generator should carry:
  1. **NEW TRAP the study missed — a repeated `branch` takes the LAST value.**
     `GET /api/hana/fg-items/?branch=OIL&branch=BEVERAGE` returned **336 rows
     starting `PET BOTTLE 250 ML …`** — the Beverages catalogue. Django's
     `QueryDict.get()` wins last. A CLI that appends a default `--branch` before
     the operator's own, or that lets a config default and a flag both reach the
     query string, will silently answer for the wrong SAP company and give no
     hint. Given the domain's own headline rule is *"never quote a HANA figure
     without its branch"*, the query builder must emit exactly one `branch` key.
  2. **Row counts in the study are already stale — do not fixture them.**
     `open-parties?branch=BEVERAGE` is **32** now (study: 31);
     `so?branch=OIL&card_code=CUSTA000636` is **57 orders / 190 lines** now
     (study: 55 / 179). The *invariants* all still hold exactly: for both
     branches, `{CardCode: OpenOrders>0}` from `all-customers` is set-equal and
     value-equal to `{CardCode: Num_of_Open_SalesOrder}` from `open-parties`, and
     `hana so` returned `DocStatus='O'` on 57/57 rows. Ship the invariants, not
     the counts.

---

### "`hana product-stock` and `hana product-so` are **proven dead**" (a removal)

- **verdict**: **CONFIRMED** — the removal is justified. Neither ever returned
  200, on either branch, in any of my attempts.
- **evidence**: `product-stock` — **three independent passes × two branches = six
  calls**, every one `502`, byte-identical body:

  ```
  GET /api/hana/product-stock/?branch=OIL       -> 502 (×3)
  GET /api/hana/product-stock/?branch=BEVERAGE  -> 502 (×3)
  {"error":"Unable to fetch product stock from HANA.",
   "detail":"name 'unique_schemas' is not defined"}
  ```

  `product-so` — three calls with item codes taken live from `fg-items`,
  including the **first row of the OIL catalogue** so it cannot be blamed on a
  stale code:

  ```
  ?branch=OIL&item_code=FG0000386       -> 500, 103,522 bytes
  ?branch=OIL&item_code=FG0000400       -> 500, 103,522 bytes
  ?branch=BEVERAGE&item_code=FG0000328  -> 500, 103,607 bytes
  <title>TypeError at /api/hana/product-so/</title>
  exception_value: Queries.get_sales_orders_for_product() takes 1 positional
                   argument but 2 were given
  frames: C:\LiveProjects\OMS\Backend\hana\services\services.py
          C:\LiveProjects\OMS\Backend\hana\views.py
  ```

  Both also 400 correctly without `branch`, so the routes exist and the crash is
  downstream of parameter validation — it is not reachable by any parameter
  choice.
- **impact if the study is wrong**: it is not wrong, but note what the removal
  costs. These are two *shipped* command names disappearing because of someone
  else's bug. Recommend the generator does not let them vanish silently — either
  keep the names registered with a hard-coded "known broken upstream, tracked,
  server says `<message>`" and a non-zero exit, or record them in a
  `known-broken` section of the CLI docs. `hana fg-items` is the working
  substitute for `product-stock`; there is **no** substitute for `product-so`.

---

### "`next-doc-number` does **NOT** reserve a document number — proven, not assumed. Confidence ~97%"

- **verdict**: **CONFIRMED — with a methodology critique. The conclusion is
  right; the proof the study presents is not the proof that establishes it.**
  The real proof was sitting unused in the study's own data. Raise confidence to
  ~99% for the risk that matters (burning a SAP invoice number); the study's
  broader phrasing *"the endpoint is a pure read of `NNM1`"* remains overstated.
- **evidence**: I did not make another OMS call. I read SAP HANA read-only:

  ```sql
  SELECT "Series","SeriesName","InitialNum","NextNumber","Locked"
    FROM "JIVO_OIL_HANADB"."NNM1"  WHERE "ObjectCode"='13' AND "Locked"='N'
  -- Series 6  HR_D0824  InitialNum 624082201  NextNumber 624082201   <- MIN unlocked
  SELECT ... FROM "JIVO_BEVERAGES_HANADB"."NNM1" WHERE "ObjectCode"='13' AND "Series"=90
  -- Series 90 HR_B1024  InitialNum 624102001  NextNumber 624102001   <- MIN unlocked

  SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OINV"       WHERE "Series"=6   -- 0
  SELECT COUNT(*) FROM "JIVO_BEVERAGES_HANADB"."OINV" WHERE "Series"=90  -- 0
  SELECT MAX("DocDate") FROM "JIVO_OIL_HANADB"."OINV"                    -- 2026-08-04
  ```

  Read at **09:40 UTC**, ~22 minutes after the study's window:

  | | OIL ObjectCode 13 | BEVERAGE ObjectCode 13 |
  |---|---|---|
  | series total | 664 | 467 |
  | never issued a document | 529 | 393 |
  | `MIN(Series) WHERE Locked='N'` | 6 | 90 |
  | `SUM(NextNumber)` | **320752394452** | **225040168017** |

  Those two sums are **byte-identical to all three of the study's 09:17–09:18
  snapshots**, extending its 16-second window to 22+ minutes and across every
  call the study and I made. But that is still the weak evidence. The decisive
  facts are these:

  1. **The exact series `next-doc-number` returns has never issued a single
     document in its life.** OIL returned `624082201`; that is series 6, whose
     `NextNumber` still equals its `InitialNum` and which has **zero** rows in
     `OINV`. Same for BEVERAGE `624102001` / series 90 / zero rows.
  2. **The SPA calls this endpoint on every invoice-screen load** — a `useEffect`
     firing `` X6(Q6(`/api/hana/next-doc-number/?doc_type=13`,n)) `` whenever the
     branch changes (`harvest/harvest-literals.json` @1876). Over the whole life
     of OMS, that counter has advanced by **exactly zero**.
  3. Oil's newest `OINV.DocDate` is today — the company is invoicing normally,
     just never into series 6. So the counter is static because reads don't touch
     it, not because the system is idle in a way that would also hide an
     increment.

  **Where the study's own method is weaker than it claims** — the reviewer should
  not accept it at face value:
  - It measured a counter that **never moves**. Because the returned series is
    unused and the sum is frozen, an unchanged 16-second control is exactly what
    you would see whether or not the endpoint reserved. As designed, the
    experiment had almost no diagnostic power; its correct answer is partly luck.
  - It compared an **aggregate**. `SUM()` over 664 series cannot see a
    compensating ±1 pair. SAP series don't decrement, so this is theoretical, but
    the study's wording *"byte-identical across all 664 + 467 series"* describes a
    per-series comparison it did not actually show.
  - It records `NextNumber = InitialNum` on 529 / 393 series as colour under
    *traps* and **never connects it to the reservation question** — which is the
    one piece of evidence in the whole write-up that actually settles it.
  - It proves the endpoint does not increment **SAP's `NNM1`**. It does not prove
    it writes nothing anywhere; an OMS-side reservation in the backend's own
    Postgres (`20.20.45.75`, per the leaked settings) would be invisible to this
    test. **I could not close that gap** — that host is not the cluster the
    `postsql` tool reaches (`103.89.45.76`, and its login now fails). Call it
    unknown, not cleared.
- **impact if the study is wrong**: this was the right claim to be frightened of
  — a reserving endpoint wrapped in a CLI would burn a numbering series, and
  numbering gaps in a GST invoice series are an audit problem, not an
  inconvenience. It is not wrong. **What would falsify it, for whoever checks
  next:** `JIVO_OIL_HANADB.NNM1.NextNumber` for `Series=6` moving off `624082201`
  without a matching new `OINV` row in series 6 (same for Beverages series 90 /
  `624102001`). Two queries, no OMS call needed. Run them before anyone adds a
  `--watch`, a retry loop or a shell-completion hook that touches this path — the
  study's instruction to keep it out of any polling feature should be carried
  into the generator as a hard rule, not a comment.

---

### "`invoices history` — **publish, and LIFT patch 0003**" / "the response is an `array` (the shipped spec said `object` — wrong)"

- **verdict**: **CONFIRMED, and stronger than the study showed.** The study
  evidenced 4 ids. I did all 23.
- **evidence**: every `id` from a live `GET /api/invoice/logs/all/`
  (`44,21,40,41,51,47,43,34,35,33,37,48,52,49,20,50,36,45,42,39,46,38,53`) →
  **23/23 HTTP 200, 23/23 top-level JSON `list`**, 1–19 rows each (879 B – 31,179 B).
  Zero non-200. Invented ids `0`, `999`, `999999` → `404
  {"error":"Invoice log not found"}` — a typed application error from a live
  view, which is what distinguishes "route exists, row doesn't" from "route
  missing" and is exactly why the 2026-07-19 verify was wrong.

  The `created_by` type trap is real and worth keeping: `logs/all` gives
  `55, 21` (**int**), `history/33` gives `"Harpreet"`, `"Warehouse Operations"`,
  `null` (**str/None**).

  One correction to the study's own record: its largest history was id 20 at 15
  rows. **Id 36 is bigger — 19 rows / 31,179 bytes** — so the "bounced 15 times"
  colour in the domain summary understates the worst case.
- **impact if the study is wrong**: it is not. Lifting patch 0003 is safe. If it
  *had* been wrong the CLI would ship a command that 404s on every invoice, so a
  4-id sample was thin for a claim that flips a shipped patch — 23/23 is the
  evidence that should go in the record.

---

### "**`status=ALL` returns an empty array, not everything.** … Verified live: `?status=ALL` -> 200, `[]`, 2 bytes"

- **verdict**: **CONFIRMED** — and the trap is worse than the study describes.
- **evidence**: all eight values from the app's own tab list, live today:

  | `status=` | rows |
  |---|---|
  | PENDING | 5 |
  | APPROVED | 0 |
  | POSTED_TO_SAP | 14 |
  | REJECTED | 0 |
  | EDITED | 0 |
  | ERROR | 4 |
  | CL_RAISED | 0 |
  | **ALL** | **0** (200, `[]`, 2 bytes) |
  | *(no `status` param)* | **23** |

  5 + 14 + 4 = 23, so the real statuses partition the table exactly and nothing
  is hidden behind `ALL`.
- **impact if the study is wrong**: it is not — but the mitigation needs to be
  wider. **NEW, related trap the study missed: unknown query parameters are
  silently ignored, with no 400.** `?branch=OIL`, `?branch=BEVERAGE` and
  `?company=2` on `/api/invoice/logs/all/` each returned output with the **same
  `sha256` as the bare call** (23 rows). So the endpoint fails in two opposite
  and equally silent ways: a wrong *value* (`ALL`) returns **nothing**, a wrong
  *param name* returns **everything**. Neither errors. The generated command must
  validate `--status` client-side against the seven real values, translate
  `ALL`/absent into "send no `status`", and never forward an unrecognised flag as
  a query param. (Incidentally this also confirms the study's claim that the
  endpoint takes no `branch` — the 23 `branch: OIL` rows are the whole table, not
  a filtered view.)

---

### "did either study assert a param listed in `CORRECTION-params.md` as wrongly-credited?"

- **verdict**: **CONFIRMED clean — neither study is contaminated.**
- **evidence**: grepped both studies for every param in the correction's
  "was wrongly credited" column — `mode`, `flow_type`, `order_ids`, `stage`, and
  a `category` or `search` asserted as an endpoint parameter. **Zero hits in
  either file.** This is structural rather than lucky: all six wrongly-credited
  entries sit on `/api/orders/*`, `/api/sap/*` and `/api/tracker/*` paths, none
  of which is in the `hana` or `invoices` brief. The correction is live risk for
  `study-orders`, `study-sap` and `study-tracker`; it is a non-event here.
- **impact if the study is wrong**: n/a.

---

## What will ship broken if nothing changes

1. **`invoices skus-pending`** — a registered command that returns HTTP 500 and
   97 KB of Django debug HTML on 100% of invocations, and leaks HANA/Postgres
   hosts, SAP schema names, GST e-invoice usernames and SMB paths every time it
   runs. Exclude it, on the same "proven dead" grounds the sibling study applied
   to `hana product-so` and `hana product-stock`. **This is the one thing in
   these two studies that must change before generation.**
2. **A duplicated `branch` query key** silently answering for the wrong SAP
   company. Emit exactly one `branch` parameter; last-value-wins is the server's
   behaviour and it is invisible to the operator.
3. **`--status` handling on `invoices logs`.** `ALL` must be translated to "send
   nothing", and unrecognised flags must be refused client-side rather than
   forwarded — the API answers a typo'd param name with the full table and a 200.
4. **Row counts encoded as fixtures.** Two of the study's counts drifted within
   hours (`open-parties` BEVERAGE 31→32; `so`/`CUSTA000636` 55→57). Assert the
   cross-endpoint invariants instead; those held exactly.
5. **`invoices all`** — if the generator reads *proven dead* as *forget*, the
   name reservation and the "use `invoices logs` instead" pointer are lost, and
   the next rescrape re-derives the same dead end from the shipped spec.

## What I could not close

- Whether `/api/hana/next-doc-number/` writes anything to the **OMS backend's own
  Postgres** (`20.20.45.75`). It provably does not touch SAP's `NNM1`; that is
  the risk operators care about, and it is settled. The wider claim "pure read"
  is not established, and the `postsql` tool points at a different cluster
  (`103.89.45.76`) whose login now fails.
- The missing parameter of `/api/invoice/all/`. I re-ran six of the study's
  eleven names and stopped for the same reason it did — every further name would
  be an invented value, which rule 2 forbids. Only the OMS team's `views.py`
  settles it.
- Whether `/api/invoice/logs/all/` is row-scoped by the credential's category.
  All 23 rows are `branch: OIL` and this token's category is `OIL`; `branch` and
  `company` params are ignored, so I could not separate "this is the whole table"
  from "this is the OIL slice" without a second credential. The study calls it a
  data fact; that is the honest reading but it is unproven either way.
