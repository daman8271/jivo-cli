# Domain study: sap + service-layer

11 paths. 8 publish (all GET), 3 exclude (all writes). Every 200 below was
re-fetched live on 2026-08-04 with the rescrape token; every parameter finding
is a live A/B against the bare call, not a reading of the shipped spec.

**Safety note up front.** `/api/service-layer/invoice/`, `/api/sap/approve-sales-order/`
and `/api/sap/sync/{id}/` were **not called, not probed, not touched**. The
first posts a real A/R invoice into SAP B1. They appear here only in the
exclusion list.

---

### `/api/sap/addresses/`

- **command**: `sap addresses` *(shipped — MCP `sap_addresses`)*
- **verdict**: publish
- **description**: Every ship-to and bill-to address SAP holds for JIVO's
  customers — the delivery addresses and GSTINs an order or invoice is raised
  against. Mirrors SAP's `CRD1` for all three company databases.
- **params**:
  | name | type | required | source | effect |
  |---|---|---|---|---|
  | `card_code` | string | no | live `sap/parties` payload | **works** — exact match. `CUSTA000001` → 20 rows / 7 KB (vs 35,722 rows / 11.8 MB bare). Unknown code → `[]`, HTTP 200 |
  | `address_type` | string `S`\|`B` | no | live payload (`address_type` field) | **works** — `B` → 17,661 rows |
  | `category`, `state`, `city`, `gst_number`, `search`, `limit`, `page`, `page_size`, `offset` | — | — | tested | **silently ignored**, byte-identical 11,798,113-byte body every time |
- **response**: `array` of objects. Keys: `id`, `card_code`, `address_name`,
  `address_type` (`S` ship-to / `B` bill-to), `gst_number`, `full_address`,
  `state`, `city`, `zip_code`, `country`, `category`, `synced_at`.
- **evidence**: bare 200, 35,722 rows, 11,798,113 bytes (probe + my own re-fetch,
  identical). `?card_code=CUSTA000001` 200, 20 rows, 7,052 bytes.
  `?address_type=B` 200, 17,661 rows. Cross-checked against HANA `CRD1`:
  Oil 12,869 = 12,869 · Beverages 11,420 = 11,420 · Mart 11,433 vs 11,432.
- **traps**:
  - **The brief says `category` was observed at the call site. It was not.** The
    app calls `getAddresses: async () => (await Y.get('/sap/addresses/')).data`
    with no params at all; the `category` annotation is bleed from the adjacent
    `getProductVarieties` in the same minified object. `category` is accepted
    and ignored — which is worse than rejected, because a CLI flag wired to it
    would return the full 35,722 rows and look like it worked.
  - **11.8 MB unpaginated and there is no pagination.** `card_code` is the only
    lever that makes this usable. A `--card-code` flag is not a nicety here, it
    is the difference between a 7 KB answer and a 12 MB one. `--compact`/`--csv`
    still needed for the unfiltered case.
  - One row is **stale**: `id 24226` (CUSTA000912, "BETOND LETTUCE SALADS
    HYDERABAD", MART) carries `synced_at 2026-07-20` while every other row
    carries today's sync stamp. It no longer exists in SAP — the sync log says
    `records_processed 35721`, the endpoint returns 35,722. The mirror inserts
    and updates but never deletes.
  - `category` is present as a *field* on every row even though it cannot be
    used as a *filter*. Filter client-side.

---

### `/api/sap/approve-sales-order/`

- **command**: none — not published
- **verdict**: **exclude**
- **exclusion reason**: write verb
- **description**: Pushes an OMS order into SAP B1 as a live sales order and
  then flips the OMS order to status 9. This is the button that turns an
  internal order into a real SAP document.
- **params**: not documented — this endpoint must not be reachable from the CLI.
- **response**: n/a — never called.
- **evidence**: harvested method `POST`, GET-capable **False**. App source:
  `Y.post('/sap/approve-sales-order/', {order_id: e.id})`, then
  `r?.DocNum ?? r?.doc_num ?? r?.DocEntry`, then
  `uB.UpdateStatus(e.id, 9, …)`. Listed under writes in API-FACTS §5.
- **traps**: the response reads back a `DocNum`, so it *looks* like a lookup at
  a glance. It is not. It creates the document.

---

### `/api/sap/branches/`

- **command**: `sap branches` *(shipped — MCP `sap_branches`)*
- **verdict**: publish
- **description**: JIVO's SAP branch/plant master (`OBPL`) — the DELHI /
  FACTORY / PUNJAB / HARYANA … posting locations, one set per SAP company. This
  is what `BPLId` means on an invoice.
- **params**: none. `?category=OIL` returns the byte-identical 3,666-byte body,
  i.e. ignored.
- **response**: `array` of 22 objects. Keys: `id`, `bpl_id`, `bpl_name`,
  `category`, `is_active`, `created_at`, `updated_at`.
- **evidence**: bare 200, 22 rows, 3,666 bytes. HANA `OBPL` counts:
  Oil 8 = 8 · Beverages 6 = 6 · Mart 8 = 8. Exact.
- **traps**:
  - **`bpl_id` is not unique and is not a key.** `bpl_id` 1 = DELHI in Oil,
    DELHI in Beverages *and* DELHI in Mart — three different SAP branches with
    the same number, because `BPLId` is scoped to a company database. The key is
    `(category, bpl_id)`; `id` is OMS's own surrogate. Any join on `bpl_id`
    alone produces a 3× fan-out.
  - `is_active` is **true for exactly one of 22 rows** — `OIL / bpl_id 2 /
    FACTORY`. Every other branch, in every company, is `false`. So this flag is
    not "branch is open for business", it is closer to "the branch OMS currently
    posts to". Do not present it as an SAP status. (Confidence that the flag is
    OMS-local rather than mirrored: high — `OBPL` has no matching single-active
    row — but I did not read the OMS server code, so the exact semantics are
    inferred.)
  - Branch names differ in case between companies (`Punjab` in Beverages,
    `PUNJAB` in Oil and Mart). Case-insensitive matching only.

---

### `/api/sap/logs/`

- **command**: `sap logs` *(shipped — MCP `sap_logs`)*
- **verdict**: publish
- **description**: The run history of the SAP→OMS mirror — every time somebody
  pulled parties, products, addresses or branches down from SAP, how many rows
  moved, how long it took, and what broke. This is the endpoint that answers
  "how stale is the party list?" and "why did last night's sync fail?".
- **params**:
  | name | type | required | source | effect |
  |---|---|---|---|---|---|
  | `limit` | int | no | probed | **works**, uncapped. Default 50. `limit=100000` → 851 rows = the entire history |
  | `sync_type` | string | no | live payload | **works**. Observed values: `ALL`, `PARTY`, `PARTY_ADDRESS`, `PRODUCT`, `BRANCH` |
  | `status` | string | no | live payload | **works**. Observed values: `SUCCESS`, `FAILED`, `STARTED` |
  | `page`, `page_size`, `offset`, `triggered_by` | — | — | tested | ignored |
- **response**: `array`. Keys: `id`, `sync_type`, `status`, `records_processed`,
  `records_created`, `records_updated`, `error_message`, `started_at`,
  `completed_at`, `triggered_by`, `duration` (seconds, float).
- **evidence**: bare 200, 50 rows, ~13.6 KB. `?limit=100000` 200, **851 rows**
  (ids 1–851, 2026-03-03 → 2026-08-04), 702,676 bytes. `?status=FAILED` 200,
  50 rows, all `FAILED`, ids 24–805 — proving the filter is real and not just
  the default page. `?sync_type=PARTY` 200, 50 rows, all `PARTY`.
- **traps**:
  - **The default is a silent 50-row cap.** Without `limit` you are looking at
    roughly the last three days, not the history. `status=FAILED` without
    `limit` returns the *oldest-reachable* 50 failures, not the recent ones —
    always pair a filter with `limit`.
  - `triggered_by` is **free text, not an enum**: 823 `manual`, 13 `Admin`,
    10 `preshit`, 3 `admin`, 1 `live-key-migration`, 1 empty. It does not
    identify a user reliably and it is not filterable.
  - **There is no scheduled sync.** All 851 runs are operator-initiated. The
    OMS SAP mirror is only as fresh as the last human who pressed the button.
  - **17 runs are stuck in `STARTED` with `completed_at: null` forever** (latest
    2026-07-28). No timeout, no reaper. A naive "is a sync running?" check on
    `status == STARTED` will always say yes.

---

### `/api/sap/parties/`

- **command**: `sap parties` *(shipped — MCP `sap_parties`)*
- **verdict**: publish
- **description**: Every **customer** SAP knows about, across all three JIVO
  companies — the party list an order is raised against. Mirrors `OCRD` where
  `CardType='C'`. Vendors are not here.
- **params**:
  | name | type | required | source | effect |
  |---|---|---|---|---|---|
  | `search` | string | no | app source: `Y.get('/sap/parties/', {params:{search:a}})` | **works** — case-insensitive substring over `card_code` **and** `card_name`. `RAJ MANDIR` → 8 rows; `CUSTA000104` → 3 rows |
  | `main_group` | string | no | live payload | **works** — `GT` → 2,088 rows (689 Oil + 858 Bev + 541 Mart) |
  | `state` | string | no | live payload | **works** — `DL` → 1,252 rows |
  | `category`, `card_code`, `card_type`, `chain`, `limit`, `page`, `page_size`, `offset` | — | — | tested | **ignored**, byte-identical 620,913-byte body |
- **response**: `array` of 3,358 objects. Keys: `id`, `card_code`, `card_name`,
  `state`, `main_group`, `card_type`, `category`, `synced_at`.
- **evidence**: bare 200, 3,358 rows, 620,913 bytes. Filtered calls as above.
  HANA `OCRD` where `CardType='C'`: Oil **1172 = 1172** · Beverages
  **1247 = 1247** · Mart **939 = 939**. Exact, all three.
- **traps**:
  - **`card_code` is NOT unique — 3,358 rows carry only 1,254 distinct codes.**
    The same code is a different business partner in each company. Worst case
    observed: `CUSTA000025` is **"HARPREET SINGH CASH SALE"** in OIL but
    **"CASH SALE FACTORY"** in BEVERAGES and MART. 306 codes have materially
    different names across companies. The key is `(category, card_code)`. A
    command that de-duplicates on `card_code`, or joins to anything on
    `card_code` alone, will merge distinct parties and silently triple rows.
  - **`category` is a field but not a filter here.** To get one company's
    parties use `/api/sap/parties/category/`, not `?category=` on this path —
    the latter returns all 3,358 rows and looks successful.
  - **Fewer fields than the category endpoint.** This one omits `address`,
    `chain` and `country`, which `parties/category/` returns. The "list all"
    command is the *thinner* payload, which is the opposite of the usual shape.
  - Customers only (`card_type` = `C` for all 3,358). If an operator asks for a
    vendor/supplier, this endpoint cannot answer — that is C-0009 territory in
    ecom, and OMS has no vendor mirror at all.

---

### `/api/sap/parties/category/`

- **command**: `sap party-categories` *(shipped — MCP `sap_party-categories`)*
- **verdict**: publish
- **description**: The customer list for **one** SAP company — Oil, Beverages
  or Mart — with the full address and chain fields. This is the correct way to
  ask "who are our Oil customers?".
- **params**:
  | name | type | required | positional | source | effect |
  |---|---|---|---|---|---|---|
  | `category` | string | **yes** | no | live `GET /api/auth/categories/` → `[{id:2,category:"BEVERAGES"},{id:3,category:"MART"},{id:1,category:"OIL"}]` | required; case-insensitive (`oil` works) |
  | `search` | — | — | — | tested | ignored |
- **response**: `object` — `{"success": true, "data": [ … ]}`. **Not an array**,
  unlike its sibling. Row keys: `id`, `card_code`, `card_name`, `address`,
  `state`, `main_group`, `chain`, `country`, `card_type`, `category`,
  `synced_at`. The app unwraps `.data?.data || []`.
- **evidence**: bare → **400** `{"success":false,"message":"category query
  parameter is required"}`. `?category=OIL` 200 / 1,172 rows / 283,978 B ·
  `?category=BEVERAGES` 200 / 1,247 / 310,532 B · `?category=MART` 200 / 939 /
  226,014 B. The three partition `sap/parties` exactly: 1172+1247+939 = 3358,
  and every `id` is a subset with no overlap.
- **traps**:
  - **An invalid category is a silent 200 with zero rows, not a 400.**
    `?category=OILS` → `{"success":true,"data":[]}` HTTP 200. A typo returns
    "no customers" rather than an error. The CLI **must** validate the enum
    client-side against `OIL|BEVERAGES|MART`; relying on the server to reject a
    bad value will hand operators a confident empty answer.
  - **`BEVERAGES`, plural.** The `hana` layer's `branch` enum spells it
    `BEVERAGE`, singular. Passing `BEVERAGE` here gets the silent empty 200
    above. See the domain summary.
  - Response shape differs from `sap/parties` (object-wrapped vs bare array).
    The generator must not assume one shape for both.

---

### `/api/sap/product-varieties/`

- **command**: `sap product-varieties` *(shipped — MCP `sap_product-varieties`)*
- **verdict**: publish
- **description**: The distinct **sub-group** values on JIVO's SAP item master —
  CANOLA, MUSTARD, OLIVE, ATTA (FLOUR), CAPS, and the GL-coded expense heads.
  This is the list you segment the range by. Despite the name, it is **not**
  the grade/variety list.
- **params**:
  | name | type | required | source | effect |
  |---|---|---|---|---|---|
  | `category` | string `OIL`\|`BEVERAGES`\|`MART` | no | app source: `Y.get('/sap/product-varieties/', {params: e ? {category:e} : void 0})`; values from `/api/auth/categories/` | **works**. Echoed back in the response |
- **response**: `object` — `{"category": "<echoed, '' when omitted>", "count":
  int, "varieties": [str], "sub_groups": [str]}`. **`varieties` and `sub_groups`
  are byte-identical arrays** — the API itself ships both keys for the same
  list, which is the backend admitting the `varieties` name is legacy.
- **evidence**: bare 200, `count: 114`. `?category=OIL` → 86 ·
  `?category=BEVERAGES` → 53 · `?category=MART` → 49. Each list is **set-equal
  to the distinct `sub_group` values of `/api/sap/products/` for that
  category** (verified by set comparison, exact match, zero symmetric
  difference). It is **not** equal to the distinct `variety` values —
  `sap/products` carries 236 distinct `variety` values against 114 `sub_group`.
- **traps**:
  - **The name is wrong and it matters for correction C-0003.** C-0003 says
    segment the range on `OITM.U_TYPE` and `U_Sub_Group`. This endpoint is
    `U_Sub_Group` — so it *is* the correct segmentation axis, but only if you
    know that. An operator who reads "product-varieties" and reaches for
    `sap/products.variety` instead has picked `U_Variety` (the grade: POMACE,
    EXTRA LIGHT, EXTRA VIRGIN, COLD PRESS) and will get a different, finer cut.
    Both fields are real; they are not the same question.
  - The 114 values are not clean master data — they include GL-coded fixed-asset
    strings like `1204007-BLOWING MACHINE (SIDEL) (FA0000025)` and near-duplicate
    spellings (`REPAIR & MAINTENANCE-PLANT & MACHINERY` vs
    `REPAIR AND MAINTENANCE - PLANT AND MACHINERY`). Do not present this as a
    tidy product taxonomy.
  - `category` is optional here, unlike on `parties/category/`. Omitting it
    unions all three companies and echoes `"category": ""`.

---

### `/api/sap/products/`

- **command**: `sap products` *(shipped — MCP `sap_products`)*
- **verdict**: publish
- **description**: JIVO's SAP item master as OMS sees it — sellable goods and
  packing/raw materials with their tax rate, pack config, on-hand qty, brand,
  and the SAP segmentation fields (`type` = `U_TYPE`, `sub_group` =
  `U_Sub_Group`, `variety` = `U_Variety`).
- **params**:
  | name | type | required | source | effect |
  |---|---|---|---|---|---|
  | `category` | string `OIL`\|`BEVERAGES`\|`MART` | no | `/api/auth/categories/` | **works** (undocumented in the shipped spec). OIL 1,442 · BEVERAGES 647 · MART 548. Case-insensitive |
  | `search` | string | no | probed; same param name the app uses on `sap/parties` | **works**. Substring on **`item_name` only** |
  | `brand` | string | no | live payload (`brand` field) | **works**. `SANO` → 116 rows, matching the payload's own brand tally exactly |
  | `type`, `sub_group`, `variety`, `item_code`, `is_active`, `tax_rate`, `limit`, `page`, `page_size` | — | — | tested | ignored |
  - `category` and `search` compose (AND): `?category=OIL&search=OLIVE` → 176 rows.
- **response**: `array` of 2,637 objects. Keys: `id`, `item_code`, `item_name`,
  `category`, `sal_factor2`, `tax_rate`, `is_deleted`, `variety`, `type`,
  `sub_group`, `sal_pack_unit`, `brand`, `on_hand`, `synced_at`, `created_at`,
  `is_active`.
- **evidence**: bare 200, 2,637 rows, 1,010,130 bytes. Category splits as above
  (549,720 / 248,947 / 211,465 bytes). `?search=POMACE` → 123 rows, **all 123
  contain "POMACE" in `item_name`, 0 in `item_code`, 0 in `sub_group`** — so
  search is name-only. HANA `OITM` totals: Oil 2,270 · Beverages 2,192 ·
  Mart 1,349.
- **traps**:
  - **`search` is item-name matching, which correction C-0003 explicitly
    forbids for segmentation.** `search=POMACE` returns 123 rows while the
    `variety = POMACE` population is 110 — the two answers differ, and the
    name-based one is the wrong one. Use `sub_group`/`type`/`variety` from the
    payload, client-side. `search` is for "find me this item", never for
    "how much of this variety".
  - **`item_code` is not unique — 2,637 rows, 1,747 distinct codes.** Same
    reason as parties: one code per company database. Key on
    `(category, item_code)`.
  - **This is a filtered subset of the SAP item master, not a copy.** Verified
    for Mart: all 548 OMS rows exist in Mart's valid+unfrozen `OITM`, and the
    256 rows OMS drops are exactly the `SL*` (services, 250) and `FA*` (fixed
    assets, 6) prefixes. So an item can exist in SAP and be genuinely absent
    here. I could **not** reduce this to a single SAP flag predicate — no
    boolean combination of `validFor`/`frozenFor`/`SellItem`/`InvntItem`
    reproduces the observed set (nearest miss: Oil 1,440 vs 1,442 observed).
    Stated as a set-membership fact, not as a rule. Confidence in the
    membership: high (exact diff). In the underlying predicate: low.
  - `type` (`U_TYPE`) is **blank or null on 1,732 of 2,637 rows**, and blank in
    two flavours (`''` and `' '`). All 647 Beverages rows are blank or
    `COMMODITY`. Any PREMIUM/COMMODITY/OTHERS split computed from this endpoint
    is a split of a minority of the range — say so when quoting it.
  - `on_hand` is a mirrored snapshot from the last sync, not live stock. For
    live stock the answer is `hana/product-stock/` — which is currently 502
    (`name 'unique_schemas' is not defined`, API-FACTS §3).

---

### `/api/sap/quotation-log/{id}/`

- **command**: `sap quotation-log` *(shipped — MCP `sap_quotation-log`)*
- **verdict**: publish
- **description**: For one OMS order, the SAP document that was actually created
  when it was pushed — the SAP doc number and doc entry, and when the push
  happened. This is the link between "ORD-20260804-0009" in OMS and a real
  document in SAP.
- **params**:
  | name | type | required | positional | source |
  |---|---|---|---|---|---|
  | `id` | int | yes | yes | OMS **order id**, e.g. `id` from `/api/orders/quotation-overview/` or `/api/orders/list/`. App source: `getQuotationLog(e.id)` where `e` is an order row |
- **response**: `object` —
  `{"success": true, "data": {"order_id": "2392", "sap_doc_num": "1726076971",
  "sap_doc_entry": 29554, "created_at": "2026-07-31T06:30:56.590096+00:00"}}`.
  Note `order_id` and `sap_doc_num` come back as **strings**, `sap_doc_entry` as
  an **int**.
  Not found → HTTP **404** `{"success":false,"message":"Quotation log not found"}`.
- **evidence**: **live parameterised calls.** Pulled 1,898 order rows from
  `/api/orders/quotation-overview/`, then called this endpoint for 43 real order
  ids: **39 × 200, 4 × 404**. `id=999999` → clean 404, no crash.
  Then resolved the returned doc numbers against HANA (see traps).
- **traps**:
  - **It is not a quotation log. It records a sales ORDER.** All 40 sampled
    `sap_doc_num` values were matched against `ORDR` and `OQUT` in all three
    company databases: **40/40 hit `ORDR` (21 Oil, 19 Beverages), 0/40 hit
    `OQUT` in any company.** Spot-checked pairwise too — order 2392 →
    `JIVO_OIL_HANADB.ORDR` DocEntry 29554 / DocNum 1726076971 / CardCode
    CUSTA000451, matching the OMS order's own card code; order 2528 →
    `JIVO_BEVERAGES_HANADB.ORDR` DocEntry 9803 / DocNum 1726088020 /
    CUSTA001216, likewise. Never describe this output as a quotation.
  - **`sap_doc_num` / `sap_doc_entry` here are a DIFFERENT document from the
    `doc_num` / `doc_entry` on the same order in `/api/orders/quotation-overview/`.**
    Order 2392: quotation-overview says `doc_num 232607218, doc_entry 15746`;
    quotation-log says `1726076971 / 29554`. Only the quotation-log pair
    resolves to a real SAP document. Do not present them as the same number.
  - **`DocEntry` alone does not identify the document** — DocEntry 9803 exists
    in Beverages *and* Mart with different DocNums and card codes. You need
    `(company, DocEntry)` or `(DocNum, DocEntry)` together. This is why the
    company must be reported alongside the number.
  - Most orders have no log: the app only calls this when the order's
    `status_display` contains completed/billing/billed/quotation/approved/
    accepted. A 404 means "never pushed to SAP", not "endpoint broken" — the
    command should say so rather than erroring out.

---

### `/api/sap/sync/{id}/`

- **command**: none — not published
- **verdict**: **exclude**
- **exclusion reason**: write verb
- **description**: Triggers a SAP→OMS mirror pull. The `{id}` is the **sync
  type**, not a row id — `all`, `product`, `party`, `party_address`, `branch`
  (inferred from the `sync_type` values in `/api/sap/logs/`). A run rewrites up
  to 43,257 rows and takes ~2.5 minutes.
- **params**: not documented — must not be reachable from the CLI.
- **response**: n/a — never called.
- **evidence**: harvested method `POST`, GET-capable **False**. App source:
  `syncData: async e => (await Y.post('/sap/sync/${e}/')).data`. Listed under
  writes in API-FACTS §5.
- **traps**: the read side (`sap/logs`) is the safe way to answer every question
  an operator might reach for this to answer.

---

### `/api/service-layer/invoice/`

- **command**: none — not published
- **verdict**: **exclude**
- **exclusion reason**: write verb — the most dangerous endpoint in this API
- **description**: POSTs a complete A/R Invoice document, `DocumentLines` and
  all, straight into SAP Business One through the Service Layer. It posts, it
  does not draft. There is no undo from outside SAP.
- **params**: not documented — must not be reachable from the CLI.
- **response**: n/a — never called.
- **evidence**: harvested method `POST`, GET-capable **False**, flags
  `branch-scoped`, `write-intent-keyword`. App source, read from the bundle:
  ```js
  let r = Q6(`/api/service-layer/invoice/`, qfe(e.branch));
  o(`POST ${r} → submitting document…`);
  let i = await X6(r, { method:`POST`, body: JSON.stringify(e.payload) });
  ```
  with `o(...)` narrating *"Awaiting SAP — posting the invoice (this can take
  10–30s)"* and throwing *"SAP rejected the invoice."* on error.
- **traps**:
  - **This is exactly the endpoint API-FACTS §1 warns about.** `X6`'s method
    defaults to GET and the URL lives in a local (`let r = …`), so any lens that
    infers the verb from the call site will label a real SAP document post as a
    readable GET. Method inference must fail closed. It is excluded here by
    normalised path, not by verb inference.
  - **Its `branch` value is spelled differently from every other branch-scoped
    endpoint.** `qfe = e => $6(e)==='BEVERAGE' ? 'BEVERAGES' : 'OIL'` — the
    service-layer call sends **`BEVERAGES`** (plural) while `/api/hana/*`
    demands **`BEVERAGE`** (singular, per the server's own 400 body). API-FACTS
    §2 currently lists `service-layer/*` in the same row as `hana/*` with values
    `OIL, BEVERAGE`; that row is wrong for service-layer. Read from the app's
    source only — I did not and will not call the endpoint to confirm what the
    server accepts.

---

## Domain summary

**What this domain is.** Two different things wearing one prefix. Seven of the
eight published endpoints are a **read-only mirror** of SAP Business One master
data that lives inside OMS's own database — parties, products, addresses,
branches — refreshed by an operator pressing a button, with `sap/logs` as the
audit trail of those refreshes. The eighth, `sap/quotation-log`, is the
**link table** from an OMS order to the SAP document it became. Everything that
writes into SAP — the invoice post, the sales-order approval, the sync trigger —
is excluded.

**Which SAP companies OMS's `sap/` layer reaches: all three, and this is
verified by exact row-count identity, not inference.**

| OMS endpoint | SAP table | Oil | Beverages | Mart |
|---|---|---|---|---|
| `sap/parties` (3,358) | `OCRD` `CardType='C'` | **1172 = 1172** | **1247 = 1247** | **939 = 939** |
| `sap/branches` (22) | `OBPL` | **8 = 8** | **6 = 6** | **8 = 8** |
| `sap/addresses` (35,722) | `CRD1` | **12869 = 12869** | **11420 = 11420** | 11433 vs 11432 (+1 stale) |
| `sap/products` (2,637) | `OITM` (filtered) | 1442 of 2270 | 647 of 2192 | 548 of 1349 |

Left column is a live `GET` on 2026-08-04; right column is
`SELECT COUNT(*)` against `JIVO_OIL_HANADB` / `JIVO_BEVERAGES_HANADB` /
`JIVO_MART_HANADB` the same hour. Three of the four are exact to the row.

So OMS's `category` → SAP company map is: `OIL` → `JIVO_OIL_HANADB`,
`BEVERAGES` → `JIVO_BEVERAGES_HANADB`, `MART` → `JIVO_MART_HANADB`.

**But the reach splits by direction, and that is the finding.** The *read
mirror* covers all three companies. The *transactional* path does not:

- Live HANA reads (`/api/hana/*`, 14 endpoints) reject anything but
  `branch ∈ {OIL, BEVERAGE}` — the server says so in its own 400 body. **No
  route to Mart.**
- The SAP order push recorded by `sap/quotation-log` lands in Oil or Beverages
  only: 40 sampled `sap_doc_num` values → 21 `JIVO_OIL_HANADB.ORDR`,
  19 `JIVO_BEVERAGES_HANADB.ORDR`, **0 Mart**.
- `/api/service-layer/invoice/` is branch-scoped to the same two.

**One line for an operator: OMS can *look at* all three SAP companies, but it
can only *write into* Oil and Beverages. Mart is read-only from OMS.** This is
the opposite shape from ecom, where correction C-0008 records a mirror that is
Mart-*only*. Each JIVO app sees a different slice and no app sees the same one.

**How the mirror is actually fed — from the server's own error text.** 60 of the
72 failed sync runs in `sap/logs` name their source:
`SAP connection failed (103.89.45.75:1433/Jivo_All_Branches_Live)`. So OMS does
not read HANA for its mirror; it reads a **SQL Server database
`Jivo_All_Branches_Live` on 103.89.45.75:1433** — the same host as the DSR
portal's SQL Server. That consolidated "all branches" replica is why OMS can see
Mart while its HANA layer cannot. Another failure —
`relation "sap_products" does not exist` — names the destination as Postgres
tables `sap_products`, `sap_parties`, etc. Both facts are quoted from the API's
own responses; I did not connect to either database to confirm.

### Traps that apply across the whole domain

1. **`category` (`OIL`/`BEVERAGES`/`MART`) ≠ `branch` (`OIL`/`BEVERAGE`).**
   Singular vs plural, and `MART` exists only as a category. Substituting one
   for the other on `parties/category/` yields a **silent 200 with zero rows**.
2. **A wrong enum value is a 200, not a 400.** `?category=OILS` →
   `{"success":true,"data":[]}`. Validate client-side. This is the single most
   likely way an operator gets a confidently wrong answer out of this domain.
3. **Neither `card_code` nor `item_code` nor `bpl_id` is unique.** All three are
   scoped to a company database. Every key in this domain is
   `(category, <code>)`. Observed worst case: `CUSTA000025` is two different
   businesses in Oil vs Beverages/Mart.
4. **Filters are undeclared and asymmetric.** The shipped spec declares one
   param across eight endpoints; live testing found ten working ones. Worse,
   **the same param name works on one endpoint and is silently ignored on its
   sibling** — `category` filters `products` but not `parties`; `search`
   filters `parties` but not `parties/category/`; `card_code` filters
   `addresses` but not `parties`. Every ignored param returns a byte-identical
   full-size body, so it looks like it worked.

   | endpoint | works | ignored |
   |---|---|---|
   | `sap/addresses` | `card_code`, `address_type` | `category`, `state`, `city`, `gst_number`, `search`, all pagination |
   | `sap/branches` | — | `category` |
   | `sap/logs` | `limit`, `sync_type`, `status` | `page`, `page_size`, `offset`, `triggered_by` |
   | `sap/parties` | `search`, `main_group`, `state` | `category`, `card_code`, `card_type`, `chain`, all pagination |
   | `sap/parties/category` | `category` (**required**) | `search` |
   | `sap/product-varieties` | `category` | — |
   | `sap/products` | `category`, `search`, `brand` | `type`, `sub_group`, `variety`, `item_code`, `is_active`, `tax_rate`, all pagination |

5. **No pagination anywhere except `sap/logs`.** `page`, `page_size`, `limit`,
   `offset` are ignored by parties, products and addresses. `sap/addresses`
   ships **11.8 MB in one response** and the only way to cut it is
   `card_code` or `address_type`. `sap/products` is 1.0 MB, cut by `category`.
   `sap/parties` is 0.6 MB, cut by `search`/`main_group`/`state`.
6. **`search` on `sap/products` matches item names only** — the exact practice
   correction C-0003 prohibits for segmentation. Segment on the payload's
   `type` / `sub_group` fields client-side.
7. **The mirror is only as fresh as the last manual sync**, and it never deletes
   (one address row in the payload no longer exists in SAP).

### Backend defects worth reporting to the OMS team

- **17 sync runs stuck in `STARTED` forever** with `completed_at: null`
  (`/api/sap/logs/?status=STARTED&limit=100000`). No timeout, no reaper. Latest
  2026-07-28.
- **72 of 851 sync runs failed (8.5%)**, 60 of them
  `SAP connection failed … 103.89.45.75:1433/Jivo_All_Branches_Live`. Two are
  Python bugs shipped to production — `name 'transaction' is not defined` and
  `relation "sap_products" does not exist` — and two are a data-quality break,
  `['"18%" value must be a decimal number.']`, where a tax rate arrived as the
  string `18%`.
- **The mirror never deletes.** `sap/addresses` returns 35,722 rows while the
  sync that populated it reports `records_processed: 35721`; the extra row
  (`id 24226`) is a Mart address last seen 2026-07-20. Reproduce:
  `GET /api/sap/addresses/` and filter for `synced_at` older than the latest
  `PARTY_ADDRESS` run in `GET /api/sap/logs/`.
- **`/api/service-layer/invoice/` sends `branch=BEVERAGES` while
  `/api/hana/*` demands `branch=BEVERAGE`.** Two spellings of one company
  inside one API. Read from the app source, not confirmed server-side (the
  endpoint is a write and was not called).

### Durable JIVO business truth — correction candidate

> **OMS's SAP mirror covers all three SAP companies, but OMS can only write
> into two.** `/api/sap/{parties,parties/category,products,product-varieties,
> addresses,branches}` mirror Oil, Beverages **and** Mart, keyed by
> `category ∈ {OIL, BEVERAGES, MART}` → `JIVO_OIL_HANADB`,
> `JIVO_BEVERAGES_HANADB`, `JIVO_MART_HANADB`. Everything transactional —
> `/api/hana/*`, `/api/service-layer/*`, and the SAP sales orders recorded in
> `sap/quotation-log` — reaches **Oil and Beverages only**; Mart is read-only
> from OMS. Codes are not unique across companies: key on `(category, code)`.
>
> Evidence: live GET vs HANA `COUNT(*)` on 2026-08-04 — parties 1172/1247/939 =
> `OCRD CardType='C'` exactly; branches 8/6/8 = `OBPL` exactly; addresses
> 12869/11420/11433 vs `CRD1` 12869/11420/11432. 40 sampled
> `sap/quotation-log.sap_doc_num` → 21 Oil `ORDR`, 19 Beverages `ORDR`, 0 Mart,
> 0 `OQUT`. `/api/hana/*` 400 body: `branch is required and must be one of:
> OIL, BEVERAGE`.
>
> Contrast with **C-0008**: ecom's SAP mirror is Mart-only. OMS's is all three.
> The two apps do not see the same books, and neither sees "JIVO".

### What I could not verify

- **The exact SAP-side predicate behind `/api/sap/products/`.** The set of rows
  is verified (for Mart, exactly the valid+unfrozen `OITM` minus the `SL*` and
  `FA*` prefixes), but no boolean combination of
  `validFor`/`frozenFor`/`SellItem`/`InvntItem` reproduces it — Oil is off by 2,
  Beverages by 13. Membership: high confidence. Rule: low.
- **`sap/branches.is_active` semantics.** One of 22 rows is true
  (`OIL/2/FACTORY`). `OBPL` has no matching flag, so I believe it is OMS-local
  routing state, not SAP status — but I did not read the OMS server code.
- **Whether `/api/service-layer/invoice/` actually accepts `branch=BEVERAGES`.**
  Read from the app's minified source only. Not called, and it should never be.
- **`sync_type` values accepted by `POST /api/sap/sync/{id}/`.** Inferred from
  the `sync_type` column of `sap/logs` (`ALL`, `PARTY`, `PARTY_ADDRESS`,
  `PRODUCT`, `BRANCH`), lowercased by convention. Never probed — it is a write.
- **Whether `/api/sap/logs/` filters compose** (e.g. `sync_type` + `status`
  together). Each was verified alone; I did not test the pair.

### Incident note — a SAP sync ran during this session; it was not mine

At **09:19:33 UTC**, mid-study, a full `ALL` sync appeared in `/api/sap/logs/`
(id 847, 43,257 records, `triggered_by: "manual"`) followed by its four child
runs. Reporting it per the study contract, with the check I ran:

- I issued **no POST of any kind** and never touched `/api/sap/sync/`.
- **Controlled test:** I then issued `GET /api/sap/branches/`,
  `GET /api/sap/parties/`, `GET /api/sap/products/` and waited 25 s — **no new
  log row**. I replayed the exact unknown-param probes that ran nearest the
  event (`parties?page=2`, `?page=1&page_size=5`, `?limit=5&offset=10`,
  `?category=OIL`, `?card_code=…`, `addresses?card_code=…`,
  `product-varieties?category=OIL`) and waited 20 s — **no new log row**. Max
  log id stayed 851 across both tests.
- The run is a well-formed `ALL` composite, the shape a human gets from the
  "Sync All" button, and the log shows 130 prior `ALL` runs at all hours
  including a burst three hours before my session started.

Conclusion: **GET requests on this domain do not trigger syncs** — verified —
and the 09:19 run was an operator at JIVO (14:49 IST, working hours).
Confidence ~97%; the residual is that `triggered_by` does not identify a caller,
so I cannot name the human who pressed it.
