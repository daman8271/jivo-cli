# Study: `hana` domain

14 paths. **12 publish, 2 exclude** (both excluded for a backend crash that fires
on 100% of calls with every valid `branch`, not for policy).

Every endpoint in this domain is a `GET` that runs a live `SELECT` against one of
JIVO's SAP Business One HANA company databases. Nothing here writes — including
`next-doc-number/`, which was specifically tested for that and cleared (see its
entry and Domain summary §3).

**Two corrections to the shipped spec that apply to all 14:**

1. **Every one of them requires `branch`**, which the shipped spec declares on
   none of them and the shipped CLI cannot send. All 14 shipped commands are
   dead today. This is the whole point of the rescrape.
2. **Every 200 in this domain returns a top-level JSON *array*.** The shipped
   spec declares `type: object` on all 14. Wrong on all 14. Verified live on all
   12 publishable paths, including the single-row ones (`customer-details/`,
   `item-price/`, `salesperson-details/`, `next-doc-number/` all return a
   one-element list, and the app itself reads `Array.isArray(e) && e[0]`).

---

## The `branch` parameter — shared contract for all 14

- **name**: `branch`
- **type**: string
- **required**: true — on every path in this domain, without exception
- **positional**: no (`--branch` flag; it is a tenant selector, not a subject)
- **enum**: `OIL`, `BEVERAGE`
- **where the values came from**: the server's own 400 body, verbatim —
  `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
- **validation is strict and case-sensitive.** Verified live:
  `branch=oil` → 400, `branch=BEVERAGES` → 400, `branch=MART` → 400, all with
  the same message. There is no default and no fallback.
- **`branch` is NOT `category`.** `category` (used by `/api/sap/parties/category/`
  and `/api/auth/*`) is `OIL | BEVERAGES | MART`. Note the plural, and note that
  `MART` has no `branch` equivalent — **OMS's HANA layer cannot reach JIVO Mart
  at all.** A CLI that reuses one enum for both will silently produce 400s.

---

### `/api/hana/address/`

- **command**: `hana address`
- **verdict**: publish
- **description**: Every bill-to and ship-to address SAP holds for one customer,
  with the GSTIN registered against each — this is where you find which GST
  number an invoice to a given branch of a party must carry.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - `card_code` — string, required, not positional. SAP `CardCode`.
    Source: server 400 (`card_code is required`) and the app's own call site,
    ``X6(Q6(`/api/hana/address/?card_code=${encodeURIComponent(o.CardCode)}`,n))``
    at bundle offset 1599547. Values fed from `hana all-customers`.
- **response**: `array` of objects. Keys: `Address` (the address *name*/code, not
  a street), `AdresType` (**`B`** = bill-to, **`S`** = ship-to — the app splits on
  exactly these two literals), `CardCode`, `City`, `State`, `Country`,
  `GSTRegnNo`, `GSTType`.
- **evidence**: 400 bare; 400 with branch only; **200 live** —
  `?branch=OIL&card_code=CUSTA000636` → 70 rows (35 `B` + 35 `S`);
  `?branch=BEVERAGE&card_code=CUSTA000636` → 70 rows;
  `?branch=OIL&card_code=CUSTA001041` → 5 rows vs `BEVERAGE` → 2 rows.
- **traps**:
  - `Address` is SAP's address *identifier* (e.g. `THE AREA MANAGER CANTEEN
    STORE DEPT BATHINDA`), not a postal line. There is no street field here.
  - `GSTRegnNo` is frequently `null` (both rows sampled for `CUSTA001041`).
    Absence in this endpoint is not evidence a party is unregistered.
  - Genuinely branch-sensitive — `CUSTA001041` has a different *number* and a
    different *set* of addresses under OIL and BEVERAGE, because it is a
    different party in each (see Domain summary §2).

### `/api/hana/all-customers/`

- **command**: `hana all-customers`
- **verdict**: publish
- **description**: The whole customer master of one SAP company — card code,
  name, state, trade channel, price list and how many sales orders are still open
  against them. This is the party lookup that feeds every other command here.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - No other parameter. Bare + branch is a 200.
- **response**: `array`. Keys: `CardCode`, `CardName`, `State1` (2-letter state),
  `U_Chain` (trade channel — `DISTRIBUTOR`, `RETAILER`, `AMAZON`, `BIG BASKET`,
  `SINGLE SHOPS`, `CSD`…), `U_Main_Group`, `ListNum` (SAP price list — **this is
  the value `hana item-price --price-list` wants**), `OpenOrders`.
- **evidence**: 400 bare; **200 live** — OIL 1172 rows / 175 KB,
  BEVERAGE 1247 rows / 185 KB.
- **traps**:
  - Unpaginated, ~180 KB per branch. Needs `--compact`/`--csv` to be usable.
  - `ListNum` is almost always `1`: OIL 1167/1172 are `1`, 2 are `4`, 3 are `-1`;
    BEVERAGE is 1247/1247 `1`. **Price list 1 is empty in SAP** — see
    `item-price/` and Domain summary §4.
  - `OpenOrders` here equals `Num_of_Open_SalesOrder` on `open-parties/`
    (both 55 for `CUSTA000636` under OIL). Two endpoints, one number.

### `/api/hana/batch-details/`

- **command**: `hana batch-details`
- **verdict**: publish
- **description**: The individual manufacturing batches of one FG item sitting in
  one warehouse, with production and expiry dates and the quantity in each — this
  is what you read to pick FEFO stock or to check what is about to expire.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - `item_code` — string, required, not positional. Source: server 400
    (`item_code and whs_code are required`) + app call site at offset 1608675.
    Values from `hana fg-items`.
  - `whs_code` — string, required, not positional. Source: same server 400 + same
    call site. **Values from `hana inventory-details` (`WhsCode`)** or from an SO
    line's `WhsCode`. Observed: `BH-BT`, `BH-FG`, `DL-PS`, `BH-GR`, `GP-FG`.
- **response**: `array`. Keys: `SysNumber`, `BatchNum`, `ItemCode`, `ItemName`,
  `WhsCode`, `PrdDate`, `ExpDate`, `InDate`, `Quantity`, `BaseType`, `BaseNum`,
  `BaseEntry`.
- **evidence**: 400 bare; 400 with branch only; **200 live** —
  `?branch=OIL&item_code=FG0000400&whs_code=BH-BT` → 2 rows;
  `?branch=BEVERAGE&item_code=FG0000328&whs_code=BH-FG` → 3 rows;
  `?branch=OIL&item_code=FG0000400&whs_code=GP-FG` → **0 rows, still 200**.
- **traps**:
  - A valid item/warehouse pair with no batch stock returns `[]` with a 200, not
    a 404. Empty is "none in that warehouse", not "bad input".
  - `Quantity` is in **pieces (single bottles/pouches)**, per correction C-0001 —
    not cartons, despite `20 PCS` appearing in `ItemName`.
  - Dates come back as `2026-05-02T00:00:00` here but as
    `2026-08-01 00:00:00` (space, no `T`) on `hana so`. Two formats in one
    domain; do not write one date parser.

### `/api/hana/customer-details/`

- **command**: `hana customer-details`
- **verdict**: publish
- **description**: The one-line master record for a customer in one SAP company —
  legal name, state, trade channel, and the default bill-to and ship-to addresses
  that will be stamped on their documents.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - `card_code` — string, required, not positional. Source: server 400
    (`card_code is required`) + app call site at offset 1600151.
- **response**: `array` of **exactly one** object (the app reads
  `Array.isArray(t) && t[0]`). Keys: `CardCode`, `CardName`, `State1`, `U_Chain`,
  `BillToDef`, `ShipToDef`.
- **evidence**: 400 bare; 400 with branch only; **200 live** — 1 row for
  `CUSTA000636` under both branches (byte-identical), 1 row for `CUSTA001041`
  under both (**different party name in each** — see traps).
- **traps**:
  - Array-of-one, not an object. A CLI that prints `.CardName` off the top level
    prints nothing.
  - `CUSTA001041` is `HIMJYOTI TRADERS` (UP) under OIL and `RAKESH KUMAR` (DL)
    under BEVERAGE. **Same code, different company.** Never carry a card code
    from one branch to the other. Domain summary §2.
  - I did **not** verify what an unknown `card_code` returns — I only ever sent
    codes harvested from `all-customers`. Assume `[]`, do not rely on it.

### `/api/hana/fg-items/`

- **command**: `hana fg-items`
- **verdict**: publish
- **description**: The finished-goods catalogue of one SAP company — every `FG*`
  item with its brand, variety, sub-group, pack size and total stock on hand
  across all warehouses. The starting point for any stock or item question.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - No other parameter. Bare + branch is a 200.
- **response**: `array`. Keys: `ItemCode`, `ItemName`, `U_Brand`, `U_Variety`,
  `U_Sub_Group`, `U_SKU`, `TotalQty`.
- **evidence**: 400 bare; **200 live** — OIL 443 rows / 75 KB,
  BEVERAGE 336 rows / 58 KB. Every `ItemCode` in both begins `FG`.
- **traps**:
  - **`TotalQty` includes zero-stock items** — 222 of 443 OIL rows and 265 of 336
    BEVERAGE rows have `TotalQty` 0. This is a catalogue with stock attached, not
    a stock report. Filtering it as if it were one drops nothing useful but
    reading it as one over-counts the range.
  - `TotalQty` is in **pieces**, per C-0001. `FG0000328` shows 481,779 — that is
    bottles, not cartons and not litres. Convert before quoting (memory: talk in
    tonnes; litres × 0.91 for oils).
  - Cross-checked and exact: `fg-items` `TotalQty` for `FG0000328` (BEVERAGE) =
    481779.0 = the sum of `inventory-details` for the same item
    (421683 + 60000 + 96). The two endpoints agree.
  - Segment on `U_Sub_Group` / `U_Variety`, **never on `ItemName`** — correction
    C-0003. `FG0000013` is literally named `REFINED OIL 1000 MLS` under OIL and
    `REFINED OIL 1000 MLS CSD` under BEVERAGE.
  - 328 item codes exist in both branches; **117 of them carry a different
    `ItemName`** and 266 a different `TotalQty`. Item codes are as branch-local
    as card codes.

### `/api/hana/freight-masters/`

- **command**: `hana freight-masters`
- **verdict**: publish
- **description**: The additional-expense codes SAP will let you put on a
  document in this company — freight inward/outward, ocean freight, marine
  insurance, TCS. Ten or eleven rows; it is a picklist, not a report.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - No other parameter.
- **response**: `array`. Keys: `ExpnsCode` (int), `ExpnsName`.
- **evidence**: 400 bare; **200 live** — OIL 11 rows / 497 B,
  BEVERAGE 10 rows / 438 B.
- **traps**:
  - `ExpnsCode` is **not stable across branches**. Code 2 is
    `FREIGHT INWARD DRCT` under OIL and `FREIGHT INWARD` under BEVERAGE; OIL has
    a code 9 (`BST`) that BEVERAGE does not. Resolve the name in the branch you
    are working in.

### `/api/hana/inventory-details/`

- **command**: `hana inventory-details`
- **verdict**: publish
- **description**: Where one FG item is physically sitting — one row per
  warehouse with the quantity in it. The per-warehouse breakdown behind
  `fg-items`' `TotalQty`.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - `item_code` — string, required, not positional. Source: server 400
    (`item_code is required`) + app call sites at offsets 1607959, 1613216,
    1632301, 1660297.
- **response**: `array`. Keys: `WhsCode`, and a column literally named
  **`SUM(Quantity)`** — parentheses and all. The app defends against this with
  ``e[`SUM(Quantity)`] ?? e.Quantity ?? e.OnHand ?? …``.
- **evidence**: 400 bare; 400 with branch only; **200 live** —
  `?branch=OIL&item_code=FG0000400` → 1 row (`BH-BT`, 15);
  `?branch=BEVERAGE&item_code=FG0000328` → 3 rows;
  `?branch=OIL&item_code=FG0000328` → **`[]`, 200**.
- **traps**:
  - The `SUM(Quantity)` key name will break naive struct tags, dot-paths and
    `jq .SUM(Quantity)`. It needs quoting everywhere.
  - Warehouses with no stock are absent, not zero-valued.
  - `FG0000328` is a real, catalogued OIL item that returns `[]` here — it has no
    stock in the Oil company. Empty is a data fact, not an error.
  - Quantities are **pieces** (C-0001).

### `/api/hana/item-price/`

- **command**: `hana item-price`
- **verdict**: publish
- **description**: What one item costs on one SAP price list. In practice this
  reports 0 or null for almost every real customer, because JIVO's default price
  list is empty — read the traps before you quote a rate off this.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - `item_code` — string, required, not positional. Source: server 400
    (`item_code and price_list are required`) + app call site at offset 1669157.
  - `price_list` — integer-as-string, required, not positional. Source: same
    server 400. **Values are the `ListNum` column of `hana all-customers`** —
    the app computes it as ``R8(e.selectedParty?.ListNum, 1)``, i.e. the selected
    party's `ListNum`, defaulting to `1`. Observed `ListNum` values: `1` (1167 of
    1172 OIL parties, 1247 of 1247 BEVERAGE), `4` (2 OIL parties), `-1` (3 OIL).
- **response**: `array` of one object. Keys: `ItemCode`, `PriceList` (echoed int),
  `Price` (number **or `null`**).
- **evidence**: 400 bare; 400 with branch only; **200 live** —
  `OIL FG0000400 price_list=1` → `[{"ItemCode":"FG0000400","PriceList":1,"Price":null}]`;
  `OIL FG0000150 price_list=1` → `Price: 0.0`;
  `OIL FG0000150 price_list=4` → `Price: 250.0`;
  `BEVERAGE FG0000328 price_list=1` → `Price: 0.0`.
  Cross-checked against HANA `ITM1`/`OPLN` directly (read-only, `hana_query`).
- **traps**:
  - **Price list 1 is completely empty in both companies.** Confirmed in HANA:
    `JIVO_OIL_HANADB.ITM1 WHERE PriceList=1` → 2272 rows, 297 `NULL`, 1975 zero,
    `MAX(Price) = 0`. `JIVO_BEVERAGES_HANADB` → 2192 rows, 102 `NULL`, 2090
    zero, `MAX(Price) = 0`. And ~99.6% of OMS parties carry `ListNum=1`. So
    **called the way the app calls it, this endpoint returns 0 or null for
    essentially every real customer.** That is not a bug in the endpoint — the
    SAP price-list master is unmaintained. JIVO's actual rates live in the OMS
    rate-approval flow (`auth/party-product/update-rate`, `orders/*`), not here.
  - `Price: null` and `Price: 0.0` both occur and mean the same thing (no price
    row / a zero price row). A CLI that prints `0` for null is lying by a
    rounding.
  - The only price lists with real content in Oil are 4 = `JIVO MART`
    (248 priced items), 3 = `SAI TRADERS LUDHIANA` (32), 5 = `LUHARI PRICE LIST`
    (22), 2 = `Jagraon` (6). They are customer-specific, not a rate card.
  - `price_list=-1` appears as a party `ListNum` but I did **not** probe it.
    Unverified.

### `/api/hana/next-doc-number/`

- **command**: `hana next-doc-number`
- **verdict**: publish
- **description**: The next unused document number in SAP's numbering series for
  a document type — what the invoice screen shows in its "Doc No." box before
  anything is saved. A display hint, not a booking.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - `doc_type` — string, required, not positional. Source: server 400
    (`doc_type is required`). **Only one value is observed: `13`**, read
    verbatim out of the app at bundle offset 1595601 —
    ``X6(Q6(`/api/hana/next-doc-number/?doc_type=13`,n))``. `13` is SAP B1's
    `ObjType` for an A/R Invoice. No other value has been seen anywhere, so `13`
    is the CLI's default and the only value this study vouches for.
- **response**: `array` of one object, single key `NextNumber` (int). Observed:
  `[{"NextNumber":624082201}]` (OIL), `[{"NextNumber":624102001}]` (BEVERAGE).
  The app reads `Array.isArray(e) ? e[0]?.NextNumber : ''`.
- **evidence**: 400 bare; 400 with branch only; **200 live, one call per branch,
  no more** — plus a before/after read of SAP HANA to settle the reservation
  question (below).
- **Does it reserve a number? No — proven, not assumed.** Confidence **~97%**.
  Method: I snapshotted `SUM(NextNumber)` over *every* A/R-invoice numbering
  series in both companies, took a control snapshot 16 s later with no call in
  between, made exactly **one** OMS call per branch, and re-read the same sum.

  | when | OIL `ObjectCode=13` (664 series) | BEVERAGE (467 series) |
  |---|---|---|
  | 09:17:37 baseline | `320752394452` | `225040168017` |
  | 09:17:53 control (no call) | `320752394452` | `225040168017` |
  | 09:18:03–04 **OMS call made** | — | — |
  | 09:18:09 after | `320752394452` | `225040168017` |

  Byte-identical across all 664 + 467 series. The endpoint is a pure read of
  `NNM1`. The residual 3%: the control window was ~16 s of a quiet Tuesday
  morning, so I have ruled out concurrent office activity only by observation,
  not by locking; and I read the aggregate, not the OMS backend's source.
  **Recommended treatment anyway: keep it in the read-only CLI, but document it
  as "reads SAP's numbering series" and do not build any loop, watch or retry
  that hammers it.** If the CLI grows a `--watch`, exclude this path from it.
- **traps**:
  - **The number returned is not the number the invoice will get.** It is the
    `NextNumber` of the *lowest-numbered unlocked series* for `ObjType 13` —
    OIL series 6 `HR_D0824`, BEVERAGE series 90 `HR_B1024`
    (`MIN(Series) WHERE Locked='N'` matches both exactly, verified in HANA).
    JIVO runs 664 A/R-invoice series in Oil and 467 in Beverages (state-wise GST
    series), **529 and 393 of which have never issued a document**
    (`NextNumber = InitialNum`). The series an invoice actually lands in depends
    on where it is billed from. Treat this as a UI placeholder.
  - Only `doc_type=13` is verified. Other SAP `ObjType` values are presumably
    accepted, but none has been observed being sent — do not invent one. Because
    the read-only nature is now proven, sending another value is not *dangerous*,
    it is just *unverified*.

### `/api/hana/open-parties/`

- **command**: `hana open-parties`
- **verdict**: publish
- **description**: The customers who still have sales orders open in one SAP
  company, with a count each — the shortlist of who is owed goods right now.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - No other parameter.
- **response**: `array`. Keys: `CardCode`, `CardName`, `Num_of_Open_SalesOrder`.
- **evidence**: 400 bare; **200 live** — OIL 58 rows / 5.4 KB,
  BEVERAGE 31 rows / 2.8 KB.
- **traps**:
  - This is the subset of `all-customers` where `OpenOrders > 0`; the counts are
    identical (`CUSTA000636` = 55 OIL / 41 BEVERAGE in both endpoints). Don't
    call both.
  - "Open" means SAP `ORDR.DocStatus = 'O'`, not "recent". Verified against HANA:
    `CUSTA000636` has 55 open and **668 closed** non-cancelled orders in Oil.

### `/api/hana/product-so/`

- **command**: `hana product-so`
- **verdict**: **exclude**
- **exclusion reason**: proven dead
- **description** (for when it is fixed): which open sales orders are demanding a
  given FG item — the demand side of a stock question, per item rather than per
  party.
- **params** (unreachable, recorded for the fix): `branch` (required),
  `item_code` (required — server 400 `item_code is required`, and the app's call
  site ``Y.get(`/hana/product-so/`, {params:{item_code:e}})`` at offset 807624).
- **response**: `UNVERIFIED` — never returned a body. The app expects an array
  (`Array.isArray(t.data) ? t.data : []`).
- **evidence**: 400 bare; 400 with branch only; **HTTP 500 on every call with a
  valid branch and a real item code**, both branches. Exact reproduction:

  ```
  GET /api/hana/product-so/?branch=OIL&item_code=FG0000400        -> 500
  GET /api/hana/product-so/?branch=BEVERAGE&item_code=FG0000330   -> 500
  ```

  Django debug page, `TypeError`:
  `Queries.get_sales_orders_for_product() takes 1 positional argument but 2 were given`
  at `C:\LiveProjects\OMS\Backend\hana\services\services.py`, line 23, in
  `syncSalesOrderByProduct`, raised from `hana.views.GetProductSalesOrderView`
  (`hana/views.py` line 70). Django 5.2.10, Python 3.14.3, `DEBUG = True`.
- **traps**: it is *not* the `item_code` that is wrong — the item codes used came
  straight out of `fg-items` and out of live SO lines. The view now passes
  `branch` down to a `Queries` method that was never given a `branch` parameter.
  It is the branch refactor, half-applied. **Re-publish the moment the OMS team
  fixes that one signature** — nothing else about the endpoint is in doubt.

### `/api/hana/product-stock/`

- **command**: `hana product-stock`
- **verdict**: **exclude**
- **exclusion reason**: proven dead
- **description** (for when it is fixed): live stock across the whole finished-
  goods range in one company, in one call.
- **params** (unreachable): `branch` (required). Notably the app's own call site
  — ``getProductStock: async () => (await Y.get(`/hana/product-stock/`)).data``
  at offset 806963 — sends **no** `branch`, so this feature is broken in the SPA
  too, and would 400 even if the 502 were fixed.
- **response**: `UNVERIFIED` — never returned a body.
- **evidence**: 400 bare (`branch is required…`); **HTTP 502 on both branches**,
  reconfirmed live during this study. Exact reproduction:

  ```
  GET /api/hana/product-stock/?branch=OIL
  GET /api/hana/product-stock/?branch=BEVERAGE
  -> 502 {"error":"Unable to fetch product stock from HANA.",
          "detail":"name 'unique_schemas' is not defined"}
  ```

  A Python `NameError`. Unlike `product-so/` this one is caught and wrapped, so
  there is no traceback and no file/line.
- **traps**: `hana fg-items` already returns `TotalQty` per item for the whole FG
  range and works today — that is the operator's substitute until this is fixed.

### `/api/hana/salesperson-details/`

- **command**: `hana salesperson-details`
- **verdict**: publish
- **description**: Resolves a SAP salesperson code to a name — the lookup that
  turns the `SlpCode` on a sales order into "who owns this account".
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - `slp_code` — integer-as-string, required, not positional. Source: server 400
    (`slp_code is required`) + the app's call site at offset 1600235,
    ``/api/hana/salesperson-details/?slp_code=${encodeURIComponent(String(e))}``
    where `e = xe.SlpCode ?? 0`. **The observable source is the `SlpCode` field
    on `hana so` rows** — that is exactly where the app gets it. Observed values:
    `107` (OIL), `45` (BEVERAGE), and `0` (the app's own fallback).
- **response**: `array` of one object. Keys: `SlpCode` (int), `SlpName`.
- **evidence**: 400 bare; 400 with branch only; **200 live** —
  `?branch=OIL&slp_code=107` → `[{"SlpCode":107,"SlpName":"RAVINDER SINGH"}]`;
  `?branch=BEVERAGE&slp_code=45` → `[{"SlpCode":45,"SlpName":"SACHIN STEPHEN"}]`;
  `?branch=OIL&slp_code=0` → `[]` with a 200.
- **traps**:
  - `slp_code=0` — the app's own default when a sales order has no salesperson —
    is a valid request returning `[]`. Not an error.
  - Salesperson codes are branch-local like everything else here; 107 in Oil and
    107 in Beverages are not the same person unless you check.
  - There is **no list endpoint for salespeople** in this domain. The only way to
    enumerate them is to pull `hana so` for parties and collect distinct
    `SlpCode`. Worth saying in the command's help.

### `/api/hana/so/`

- **command**: `hana so`
- **verdict**: publish
- **description**: The sales orders still open against one customer, header *and*
  every line — quantities, rates, warehouse, tax code and what is still
  undelivered. The richest endpoint in the domain.
- **params**:
  - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: server 400.
  - `card_code` — string, required, not positional. Source: server 400
    (`card_code is required`) + two app call sites,
    ``Y.get(`/hana/so/`, {params:{card_code:e}})`` at offset 807492 and
    ``/api/hana/so/?card_code=${encodeURIComponent(e.CardCode)}`` at 1596613.
- **response**: `array` of order headers, each with a **nested `lines` array**.
  - header keys: `DocEntry`, `DocNum`, `DocDate`, `DocDueDate`, `CardCode`,
    `CardName`, `NumAtCard` (customer's own PO reference), `DocStatus`,
    `DocTotal`, `VatSum`, `DiscSum`, `Comments`, `SlpCode`, `ShipToCode`,
    `PayToCode`, `BPL_Id`.
  - line keys: `LineNum`, `ItemCode`, `Dscription`, `Quantity`, `OpenQty`,
    `Price`, `PriceBefDi`, `DiscPrcnt`, `LineTotal`, `VatPrcnt`, `VatGroup`,
    `WhsCode`, `TaxCode`, `ShipDate`, `AcctCode`, `Project`, `OcrCode`,
    `LineStatus`.
- **evidence**: 400 bare; 400 with branch only; **200 live** —
  `?branch=OIL&card_code=CUSTA000636` → 55 orders / 179 lines / 90 KB;
  `?branch=BEVERAGE&card_code=CUSTA000636` → 41 orders / 54 KB;
  `?branch=BEVERAGE&card_code=CUSTA000151` → `[]` with a 200.
  Cross-checked against HANA: `ORDR` for that party has exactly 55 open (OIL) and
  41 open (BEVERAGE) non-cancelled orders, and `RDR1` has exactly 179 lines under
  the 55 — the API returns all of them, no line filtering.
- **traps**:
  - **Open orders only.** `DocStatus` is `'O'` on every row returned; the same
    party has **668 closed** orders in Oil that this endpoint will never show.
    This is not an order-history command and must not be described as one.
  - `LineNum` is **not contiguous** — a BEVERAGE order came back with only
    `LineNum: 2`, and HANA confirms `RDR1` genuinely holds one row for it. SAP
    keeps the original numbering after lines are deleted during entry. Do not
    treat a gap as a dropped line, and do not use `LineNum` as an index.
  - `Quantity`/`OpenQty` are **pieces** (C-0001). `Price` is per piece.
  - `DocNum` is a 10-digit series number (`1726086500`), not a small counter.
  - Dates are `YYYY-MM-DD HH:MM:SS` with a space here, but ISO-with-`T` on
    `batch-details/`.
  - `OcrCode` is a cost centre carrying the variety (`MUSTARD`) — useful, but
    segment on the item master's `U_Sub_Group` (C-0003), not on this.

---

# Domain summary

**What this domain is.** `hana` is the only part of OMS that reads JIVO's SAP
books live, rather than a mirror — 14 thin `SELECT`s over the SAP Business One
HANA database: the customer master, the finished-goods catalogue with stock,
per-warehouse and per-batch inventory, open sales orders, price lists,
salespeople, freight expense codes and SAP's next document number. It is what an
Accounts or order-desk operator reaches for when they need the figure SAP itself
would show, not what an app cached. 12 of the 14 work today; 2 are crashed.

## 1. Nothing in this domain works without `--branch`, and the CLI must reject a missing one locally

All 14 paths 400 without it. `OIL | BEVERAGE`, case-sensitive, no default. The
generated CLI should make `--branch` a required flag on every `hana` command and
fail before the HTTP call, so an operator gets a usable message instead of the
server's. **`MART` is not a branch** — OMS's HANA layer has no route to the JIVO
Mart company at all, even though `MART` is a valid `category` elsewhere in this
same API. And no HANA figure should ever be quoted without naming its branch;
these are two separate sets of books.

## 2. Trap that will bite hardest: card codes and item codes are branch-LOCAL

This is the finding I would put at the top of the command help. Of the 1165 card
codes present in both branches, **298 (25.6%) belong to a different party in each**:

| CardCode | OIL | BEVERAGE |
|---|---|---|
| `CUSTA000874` | RAKESH BROTHER (PB) | MANJEET GENERAL STORE (PB) |
| `CUSTA000875` | DIVISHA NATURAL FLAVOURS AND FRAGRANCES EXPORTS (DL) | RINKU SHARMA (PB) |
| `CUSTA000876` | MANJEET GENERAL STORE (PB) | MAAN SINGH (UP) |
| `CUSTA001041` | HIMJYOTI TRADERS (UP) | RAKESH KUMAR (DL) |

Note `MANJEET GENERAL STORE` is `…876` in Oil and `…874` in Beverages — the two
company masters drifted apart and the codes shifted against each other. Item
codes have the same disease: of 328 FG codes in both, 117 carry a different
`ItemName`. **Resolve a code in the branch you intend to use it in. Never join
OIL and BEVERAGE on `CardCode` or `ItemCode`.** (Some of the 298 are only
spelling drift — `NANDNI` vs `NANDINI` — but many are unrelated businesses, and
you cannot tell which without looking.)

## 3. `next-doc-number/` was tested for write behaviour and cleared

Because a "next number" endpoint is the classic thing that quietly increments, I
did not take it on trust. I read `SUM(NextNumber)` across all 664 (Oil) and 467
(Beverages) A/R-invoice numbering series directly from HANA read-only, took a
no-call control, made **exactly one** OMS call per branch, and re-read. All three
snapshots identical. It is a pure read of `NNM1`. Confidence ~97%; the gap is
that the control window was short and I never saw the backend source.

Two things follow. First, it is safe to publish. Second, **the number it returns
is a placeholder, not a booking** — it is the next number of the lowest unlocked
series, and JIVO runs hundreds of state-wise GST series per company (529 of Oil's
664 have never issued a document). The invoice will get whatever series it is
actually billed under. Do not let a command imply otherwise, and keep this path
out of any future `--watch`/polling feature.

## 4. `item-price/` answers 0 for almost everybody, and that is SAP's data, not a bug

Price list `1` is **empty in both companies** — Oil: 2272 `ITM1` rows,
`MAX(Price) = 0`; Beverages: 2192 rows, `MAX(Price) = 0`. And 1167 of 1172 Oil
parties and 1247 of 1247 Beverages parties carry `ListNum = 1`. Since the app
derives `price_list` from the party's `ListNum`, `hana item-price` returns `0` or
`null` for essentially every real customer. The only populated lists in Oil are
customer-specific (4 = `JIVO MART`, 248 items; 3 = `SAI TRADERS LUDHIANA`, 32;
5 = `LUHARI PRICE LIST`, 22; 2 = `Jagraon`, 6). **JIVO's selling rates do not
live in SAP price lists** — they live in the OMS rate-approval flow. A command
that presents this as "the price" will mislead. Say "SAP price-list price" and
warn on 0/null.

## 5. Backend defects (the OMS team's, with reproductions)

| endpoint | code | server said | where |
|---|---|---|---|
| `/api/hana/product-stock/?branch=OIL` (and `BEVERAGE`) | 502 | `{"error":"Unable to fetch product stock from HANA.","detail":"name 'unique_schemas' is not defined"}` | caught; no traceback |
| `/api/hana/product-so/?branch=OIL&item_code=FG0000400` (and `BEVERAGE`/`FG0000330`) | 500 | `TypeError: Queries.get_sales_orders_for_product() takes 1 positional argument but 2 were given` | `hana\services\services.py:23` in `syncSalesOrderByProduct`, from `hana.views.GetProductSalesOrderView` (`hana/views.py:70`) |

Both are the **same half-finished refactor**: `branch` was threaded through the
views but two `Queries` methods were never updated to accept it. It is the same
bug as `/api/sku/pending/` (`SalesOrderService.getFGItems() missing 1 required
positional argument: 'branch'`) recorded in API-FACTS §3. Three known casualties;
there may be more on paths nobody has called.

`product-so/` also confirms **`DEBUG = True` in production** independently of the
`/api/sku/pending/` finding — it returns a full Django debug page to an
authenticated caller, leaking the internal origin `http://127.0.0.1:8001`, the
deployment path `C:\LiveProjects\OMS\Backend`, the venv path, Django 5.2.10 and
Python 3.14.3. That is a security finding for the OMS team, not a CLI concern.

Both are excluded as **proven dead** rather than published-with-a-warning. A 403
is a permission wall over a working endpoint and gets published `UNVERIFIED`; a
deterministic `NameError`/`TypeError` on 100% of calls with every valid parameter
is a command that cannot succeed for anyone. Shipping it would recreate exactly
the failure this rescrape exists to fix. **Both should be re-published
unchanged the day those two signatures are fixed** — nothing else about them is
in doubt.

## 6. Shape and formatting traps that apply across the domain

- **All 12 live endpoints return arrays.** Four of them (`customer-details/`,
  `item-price/`, `salesperson-details/`, `next-doc-number/`) return an array of
  exactly one object. The shipped spec says `object` on all 14.
- **Empty is a 200, everywhere.** `inventory-details` for a real item with no
  stock, `batch-details` for a real item/warehouse pair, `so` for a party with
  nothing open, `salesperson-details` for `slp_code=0` — all `[]` with a 200.
  Per the study contract, that is a data fact and must not become a constraint.
- **`inventory-details` has a column literally named `SUM(Quantity)`.**
- **Two date formats in one domain**: `2026-08-01 00:00:00` on `so`,
  `2026-05-02T00:00:00` on `batch-details`.
- **Size**: `all-customers` ~180 KB and `so` up to ~90 KB for one party, both
  unpaginated. `--compact`/`--csv` is not a nicety here.
- **Every quantity is in pieces**, per correction C-0001.

## 7. Durable JIVO truths worth recording as corrections

1. **A SAP card code or item code is only meaningful inside one company
   database.** 25.6% of the card codes shared between OMS's OIL and BEVERAGE
   branches point at a different party in each, and 36% of shared FG item codes
   carry a different name. Never join or carry a code across branches/companies.
   *Evidence*: `GET /api/hana/all-customers/?branch=OIL` vs `?branch=BEVERAGE`,
   1165 shared codes, 298 with different `CardName`.
2. **JIVO's SAP price lists are not the rate card.** Price list 1 — which
   ~99.6% of parties are on — is entirely empty in both Oil and Beverages
   (`MAX(Price) = 0` over 2272 and 2192 `ITM1` rows). Selling rates come from the
   OMS rate-approval flow, not from SAP. Any "price from SAP" answer built on
   `ITM1`/`OPLN` for list 1 is 0 by construction.
3. **`hana so` is open orders only** — a party with 55 open orders in Oil has 668
   closed ones this endpoint will never return. Not an order-history source.

## 8. What I could not verify

- **Unknown-key behaviour.** I only ever sent card codes, item codes, warehouse
  codes, salesperson codes and price lists harvested from a live payload or the
  app source. I do not know what `card_code=NOPE` returns — probably `[]`, but I
  did not check and the CLI should not claim to know.
- **`price_list=-1`.** It appears as a real `ListNum` on 3 Oil parties. Never probed.
- **`doc_type` other than `13`.** Never observed being sent anywhere, so never
  sent. The read-only nature is proven, so other values are not *dangerous*, just
  unverified.
- **Response shapes for `product-so/` and `product-stock/`.** Marked `UNVERIFIED`;
  they have never returned a body to anyone, including the SPA.
- **Whether `branch` affects anything beyond schema selection** (row-level
  filtering, permissions). Every difference I saw is explained by "two different
  SAP companies", but I did not test a party the credential is not assigned to.
- **Pagination or filtering parameters.** None of these endpoints advertises any,
  none of the app's call sites sends any, and I did not guess at names. If
  `all-customers`/`so` accept a `limit`, I do not know it.
