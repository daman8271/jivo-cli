# Domain study: orders

33 paths. **25 publish, 8 exclude** (all 8 exclusions are write verbs).

Credential used for every live call: `paramjot` — role `admin`, company `Jivo
Wellness`, category `OIL`, user id **62**. Every call below was a `GET`. Nothing
was created; no write verb was issued at any point.

**Four paths in this domain serve a GET *and* a write on the identical URL**
(`flow-config`, `notifications`, `party-flow-config`, `staff-products`). Each is
published as a **GET-only** endpoint and the write verb is listed separately in
§ Excluded. An exclusion list keyed on path alone would kill four working reads —
the assembler must key on **(path, method)**.

---

## Published endpoints

### `/api/orders/addresses/`

- **command**: `orders addresses`
- **verdict**: publish
- **description**: The bill-to and ship-to addresses SAP holds for one trading
  party — what the order screen offers when a salesman picks where to invoice
  and where to deliver.
- **params**:
  - `card_code` — string, **required**, query. Source: server's own 400 body
    `{"error":"card_code is required"}`. Values observed live in
    `/api/orders/list/` payloads (`CUSTA000844`, `CUSTA001216`, `CUSTA000636`).
  - `category` — string, optional, query. Enum **`OIL` | `BEVERAGES` | `MART`**.
    Source: the app's own call site (`params:{card_code:e, ...t?{category:t}:{}}`)
    for the param name; the enum from `GET /api/auth/categories/` (API-FACTS §2)
    and confirmed live — all three return 200 with **distinct** address sets.
    This is the `category` enum, **not** the `branch` enum: `BEVERAGES` (plural)
    and `MART` exists here.
- **response**: `object` — `{bill_to: [...], ship_to: [...]}`, and an
  `is_fallback` bool that only appears when both lists come back empty. Address
  row: `id`, `full_address`, `gst_number`, `address_type` (`B`/`S`),
  `address_name`, `category`.
- **evidence**: bare → 400 (brief). Live:
  `?card_code=CUSTA000636` → 200, 45,363 B, 105 bill_to + 105 ship_to;
  `&category=OIL` → 200, 14,985 B, 35+35; `&category=BEVERAGES` → 15,409 B,
  35+35; `&category=MART` → 15,059 B, 35+35;
  `?card_code=CUSTA001216&category=OIL` → 200, 47 B,
  `{"bill_to":[],"ship_to":[],"is_fallback":false}`.
- **traps**:
  - Without `category` the response is the **union of all three SAP companies**
    for that party — 105+105 rows and 45 KB for a single CSD party, with the
    same street address repeated once per category. An operator asking "what is
    ILAHI's billing address" gets three answers unless `category` is passed.
  - A party can exist in one category only. `CUSTA001216` has BEVERAGES
    addresses and nothing under OIL — an empty result is a real answer, not an
    error.

### `/api/orders/branch/`

- **command**: `orders branch`
- **verdict**: publish
- **description**: The SAP *business place* (BPL) list — the legal
  billing entity an order is raised against. One row for this credential:
  BPL 2, FACTORY, category OIL.
- **params**: none. The app calls it bare.
- **response**: `array` of `{bpl_id (string), bpl_name, category}`.
- **evidence**: bare → 200, 1 row, 54 B (brief, re-confirmed live).
- **traps**:
  - **`orders branch` has nothing to do with the `--branch` tenant flag.** The
    `branch` query parameter that every `/api/hana/*` endpoint demands takes
    `OIL` | `BEVERAGE` and selects a SAP company database (API-FACTS §2). *This*
    endpoint returns SAP `OBPL` business-place rows keyed by `bpl_id`. Same
    English word, two unrelated things. If the CLI ever grows a global
    `--branch` flag for the hana domain, this command must not inherit it.
  - The single row is filtered to the caller's category (`OIL`). A
    BEVERAGES-category user would very likely see a different row. Not verified —
    I have one credential.

### `/api/orders/dashboardW/`

- **command**: `dashboard summary`
- **verdict**: publish
- **description**: The order-book KPI block on the OMS home screen — how many
  orders exist, what they are worth, and how much of that value is completed,
  rejected or still pending approval.
- **params**:
  - `year` — int, optional, query. Source: app call site
    `` `/orders/dashboardW/?year=${e}&month=${n}` ``. Values: calendar years
    (the app offers the last 5).
  - `month` — int, optional, query. Source: same call site. `0` = all months
    (the app's "All Months" option maps to `0`); `1`–`12` = a month.
- **response**: `object`. Keys: `filter{year,month}`, `total_orders`,
  `total_revenue`, `completed_revenue`, `rejected_revenue`, `pending_revenue`,
  `today_orders`, `this_month_orders`, `status_counts{...11 status names...}`,
  `accepted_orders`, `rejected_orders`, `reviewed_orders`,
  `pending_review_orders`, `user_counts`.
- **evidence**: bare → 200, 573 B, `filter{year:2026,month:0}`,
  `total_orders 2163`. Live `?year=2026&month=8` → 200, 554 B,
  `filter{year:2026,month:8}`, `total_orders 40`.
- **traps**:
  - The **server default is `month:0` = whole year**, not the current month.
    Bare gives the year-to-date book (2,163 orders); the operator asking "how
    many orders this month" needs `--month`.
  - `status_counts` is keyed by **display name** (`"Billing Rejected"`), while
    `orders list --status` takes the **code** (`BILLING_REJECTED`). Two different
    vocabularies for the same eleven states.

### `/api/orders/dashboardW/charts/`

- **command**: `dashboard charts`
- **verdict**: publish
- **description**: Every chart series behind the OMS dashboard in one call —
  monthly sales, state-wise orders, manager league table, status mix, top
  parties, category split, and the state × item sales grid.
- **params**:
  - `line_year` — int, optional, query. Source: app call site
    `` ?line_year=${e}&year=${e}&month=${n} ``. Drives the monthly line chart's
    year independently of the KPI filter.
  - `year` — int, optional, query. Same source.
  - `month` — int, optional, query. Same source; `0` = all months.
  - `status` — string, optional, query. Enum **`completed` | `pending` |
    `rejected` | `all`**. Source: the app's own `<select>` in the state-wise
    report (`<option value="completed">Completed Orders</option>` … ). All four
    confirmed live.
- **response**: `object`. Keys: `filter{line_year,year,month}`,
  `monthly_sales[12]{month,label,revenue,count}`,
  `statewise_orders[]{state,orders,sales}`,
  `manager_performance[]{manager_id,manager_name,orders,sales}`,
  `manager_state_performance[]{…,state}`,
  `status_distribution[11]{status,label,count}`,
  `decision_distribution[]`, `top_parties[25]{card_code,card_name,category,count,completed_count,revenue}`,
  `category_sales[]{category,count,total_sales}`,
  `state_item_sales[]{state,products[]}`, `highest_sales_order{order_number,amount}`.
- **evidence**: bare → 200, 268,382 B. Live
  `?line_year=2026&year=2026&month=8&status=completed` → 200, **19,735 B**.
  `status` sweep at `month=0`: `completed` 268,382 B / 19 states,
  `pending` 66,113 B / 4, `rejected` 118,637 B / 11, `all` 293,618 B / 22.
- **traps**:
  - **287 KB by default.** The bare call is byte-identical in size to
    `status=completed`, so `completed` is the server default. Nearly all of the
    payload is `state_item_sales`, which nests a per-item array under every
    state. A command that pretty-prints this whole object is unusable; it needs
    `--compact` or a series selector.
  - `status` filters **`state_item_sales` only** — the other ten series are
    unchanged. It is not a global dashboard filter.
  - `filter` in the response echoes `line_year`/`year`/`month` but **not**
    `status`, so the output does not record which slice it is.

### `/api/orders/dispatches/`

- **command**: `orders dispatches`
- **verdict**: publish
- **description**: The named dispatch-from locations an order can ship out of.
  One row today: Factory - Bahadurgarh.
- **params**: none. The app calls it bare.
- **response**: `array` of `{id, name, code}`.
- **evidence**: bare → 200, 1 row, 58 B (brief, re-confirmed live:
  `[{"id":4,"name":"Factory - Bahadurgarh","code":"FAC-BGH"}]`).
- **traps**:
  - **`dispatch_from_id` on an order does NOT point here.** Order 2530's detail
    reads `dispatch_from_id: 2, dispatch_from_name: "FACTORY"` — that is the
    **BPL id from `orders branch`**, not `dispatches.id` (which is 4). Verified
    on four orders (2530, 2528, 2493, 1570), all `dispatch_from_id: 2`. Joining
    order detail to this list on `id` produces a wrong or empty answer.

### `/api/orders/flow-config/`  *(dual-verb: GET + POST — GET only)*

- **command**: `orders flow-config`
- **verdict**: publish (GET). The `POST` on this same URL is excluded — see
  § Excluded.
- **description**: The global approval-flow rulebook — which of the three gates
  (rate approval, billing, auditor) an order has to pass, and which price
  conditions force a rate approval.
- **params**:
  - `flow_type` — string, optional, query. Enum **`ASM` | `BILLING`**. Source:
    the app's call site (`getOrderFlowConfig:async(e='ASM')=>…{params:{flow_type:e}}`,
    so `ASM` is also the client default) **and** the endpoint's own response,
    which publishes `flow_options:[{code:"ASM"},{code:"BILLING"}]`. Both
    confirmed live.
- **response**: `object` — `flow_type`, `flow_label`, `flow_options[]{code,label}`,
  `rate_approval_enabled`, `billing_enabled`, `auditor_enabled`,
  `rate_conditions[]`, `condition_options[]{code,label}`, `updated_at`,
  `updated_by`.
- **evidence**: bare → 200, 808 B (`flow_type: ASM`, i.e. the **server** default
  is also ASM). Live `?flow_type=ASM` → 200, 808 B, all three gates enabled;
  `?flow_type=BILLING` → 200, 818 B, `billing_enabled: false`,
  `rate_approval_enabled: true`, `auditor_enabled: true` — a genuinely different
  configuration, so the param works.
- **traps**:
  - The five `rate_conditions` codes are self-documenting in
    `condition_options` (`BASIC_GT_MARKET` = "Price List (Basic) > Basic Price
    and Basic Price != 0", etc.). Print the labels, not the codes.
  - Per-party overrides live at `orders party-flow-config` and win over this.
    Answering "does party X need auditor approval" from this endpoint alone is
    wrong for the 2 parties that carry an override.

### `/api/orders/list/`

- **command**: `orders list`
- **verdict**: publish
- **description**: The working order queue — the orders still moving through
  creation, rate approval, billing and rejection. **Not** the full order book;
  see the trap.
- **params**:
  - `status` — string, optional, query. Read from the app's own query builder
    (`e!=null&&r.push(\`status=${e}\`)`). **Accepts a comma-separated list** —
    the app does `lt(e).join(',')` before calling. Values observed live in the
    endpoint's own payload: `CREATED`, `RATE_APPROVAL`, `AUDITOR_APPROVAL`,
    `BILLING`, `APPROVED`, `REJECTED`, `BILLING_REJECTED`, `COMPLETED`; the app
    additionally hard-codes `AUDITOR_APPROVAL`, `RATE_APPROVAL`, `APPROVED` as
    literals. (`orders status` names 11 states; `DRAFT`, `NEED_APPROVAL` and
    `BILLING_PENDING` codes were not observed and are not documented as accepted
    values.)
  - `billing` — bool, optional, query. The app only ever emits the literal
    `billing=true`; it omits the param otherwise.
  - `approval_pending` — bool, optional, query. Same — only ever `true`.
- **response**: `array` of `{id, order_number, order_type, employee_id,
  card_code, card_name, total_amount, status, status_display, sap_doc_number,
  items_count, created_by (display name), created_at, delivery_date, is_foc}`.
- **evidence** (all live, all 200):

  | call | rows | bytes |
  |---|---|---|
  | bare | 263 | 100,453 |
  | `?status=AUDITOR_APPROVAL` | 1 | 400 |
  | `?status=RATE_APPROVAL` | 6 | 2,313 |
  | `?status=APPROVED` | 2 | 774 |
  | `?status=RATE_APPROVAL,APPROVED` | **8** | 3,086 |
  | `?status=COMPLETED` | **1,898** | 731,957 |
  | `?billing=true` | 45 | 17,499 |
  | `?approval_pending=true` | 263 | 100,453 |
  | `?status=RATE_APPROVAL&approval_pending=true` | 6 | 2,313 |
  | `?status=BILLING&billing=true` | 44 | 17,132 |

- **traps**:
  - **The bare call is not "all orders".** It returns 263 rows while
    `dashboard summary` reports `total_orders: 2163` and `?status=COMPLETED`
    alone returns 1,898. The intersection of the bare list and the completed
    list is **2 rows**. So the default silently omits ~1,896 completed orders.
    The shipped description "All orders (admin-wide)" is wrong and will make an
    agent under-report the book by 7×. I did **not** determine the exact
    server-side default predicate — it is not a date window (bare spans
    2026-04-18 → 2026-08-04, ids 5 → 2530) and it is not "no SAP doc number"
    (5 bare rows have one). Recording the fact, not a guess at the rule.
  - **`billing=true` is a queue selector, not a status filter.** It returns 45
    rows spanning `BILLING`(2) + `BILLING_REJECTED`(41) + `APPROVED`(2) — one
    more `BILLING_REJECTED` than the bare list contains. Combining it with
    `status` gives 44, which is neither an intersection nor a union. The three
    params are not orthogonal; do not document them as composable filters.
  - **`approval_pending=true` alone is a no-op** — byte-identical to bare
    (100,453 B). The app only ever sends it *with* a status.
  - The CLI must **omit** `billing`/`approval_pending` when false rather than
    send `billing=false`. Django reads `request.GET.get('billing')` as the
    string `"false"`, which is truthy. I did **not** test `false` — it is not an
    observed value (rule 2) — so this is a reasoned precaution, not a measured
    one.
  - `sap_doc_number` here is `""` when absent; the detail endpoint returns
    `null`. And 732 KB / 1,898 rows for `--status COMPLETED` needs `--compact`.

### `/api/orders/notifications/`  *(dual-verb: GET + POST — GET only)*

- **command**: `orders notifications`
- **verdict**: publish (GET). The `POST` on this same URL is *mark all as read* —
  excluded, see § Excluded.
- **description**: Unread order-status alerts for whoever the token belongs to —
  "your order moved to Billing", "rate approval rejected".
- **params**: none observed. The app calls it bare (it re-reads it every 30 s).
- **response**: `array` — **UNVERIFIED shape**. Live it is `[]`. The app's own
  handler defensively unwraps `data`, `data.data`, `data.results` *and*
  `data.notifications`, so it is not certain the non-empty payload is a bare
  array. The only field the app touches is `is_read` (it counts `!e.is_read`)
  and `id`/`order_id` (used by the click handler).
- **evidence**: bare → 200, `[]`, 2 B (brief, re-confirmed live).
- **traps**:
  - Zero rows is a **data fact**: this admin has no unread order alerts right
    now. Not a permission wall, not an empty feature. Do not encode it.
  - The GET and the "mark all read" POST share this URL exactly. Keying the
    write denial on the path would delete the read.

### `/api/orders/notifications/history/`

- **command**: `orders notifications-history`  *(NEW — no shipped name)*
- **verdict**: publish
- **description**: The full notification feed for the current user, paged —
  including alerts already read, which the live `orders notifications` call
  drops.
- **params**:
  - `limit` — int, optional, query. Source: app call site
    `params:{limit:20, offset:n, filter:r}`. The app sends `20`.
  - `offset` — int, optional, query. Same source; the app pages by
    `offset + len(results)` and stops when `next_offset` is null.
  - `filter` — string, optional, query. Enum **`all` | `unread`**. Source: the
    app's own filter buttons, `[\`all\`,\`unread\`].map(e=>…onClick:()=>ye(e))`,
    with `useState('all')` as the default. Both confirmed live.
- **response**: `object` — `{results: [], count: 0, unread_count: 0,
  next_offset: null}`. The `results` **row** shape is UNVERIFIED (empty for this
  user); from the app's consumers a row carries at least `id`, `is_read`,
  `order_id`, `title`, `message`/`body`, `order_number`.
- **evidence**: bare → 200, 60 B. Live `?limit=5&offset=0&filter=all` → 200,
  same body; `?filter=unread` → 200, same body.
- **traps**: paginate on `next_offset`, not on `count`; the app never trusts
  `count` for paging.

### `/api/orders/orderdetailsbyid/{id}/`

- **command**: `orders detail`
- **verdict**: publish
- **description**: One complete order — every line item with its variety, rate
  and scheme, the bill-to/ship-to it will invoice against, the rate-approval
  chain with who is holding it, and the SAP push state.
- **params**:
  - `id` — int, **required, positional**. Source: `id` field of
    `/api/orders/list/` rows.
- **response**: `object`. **Verified live** (8 orders fetched).
  - header: `id`, `order_number`, `card_code`, `card_name`, `bill_to_id`,
    `bill_to_address`, `ship_to_id`, `ship_to_address`, `dispatch_from_id`,
    `dispatch_from_name`, `company`, `po_number`, `is_foc`, `remarks`,
    `total_amount`, `status`, `status_display`, `created_by` (**int user id**),
    `created_by_name`, `created_at`, `delivery_date`, `sap_created` (bool),
    `sap_doc_number`, `quotation_cancelled`, `approved_by`, `approved_at`,
    `rejected_by`, `rejected_at`, `rejection_reason`, `reject_reason`,
    `updated_at`, `items_count`, `party_state`, `vareity_cost` *(sic)*.
  - `items[]`: `id`, `item_code`, `item_name`, `category`, `brand`, `variety`,
    `variety_type`, `sub_group`, `item_type`, `qty`, `pcs`, `boxes`, `ltrs`,
    `price_list_basic`, `basic_price`, `last_purchase_price`, `tax_rate`,
    `total`, `scheme_id`, `scheme_name`, `scheme_item_code`, `scheme`,
    `schemes[]`, `qty_scheme`, `is_scheme_visible`,
    `approval_approvers[]{id,name}`, `order`.
  - `rate_approvals[]`: `id`, `approver` (user id), `approver_name`, `status`
    (`PENDING` observed), `remarks`, `approved_at`, `created_at`.
  - `vareity_cost`: `{commodity_price, premium_total, other_total}`.
- **evidence**: **live parameterised calls** — ids taken from
  `/api/orders/list/`. `2530` → 200, 2,938 B, 3 items, 2 rate approvals;
  `2528` → 200, 2,977 B; `2493` → 200, 1,729 B; `1570` → 200, 10,683 B,
  16 items; `2392`, `2190`, `2189`, `2169` → 200 each.
- **traps**:
  - **`sap_doc_number` is broken on this endpoint — it is `null` for every
    order, including ones that demonstrably have a SAP document.** Order 2392:
    `orders list` says `sap_doc_number: 232607218` and `quotations overview`
    says `doc_num: 232607218 / doc_entry: 15746`, but the detail returns
    `sap_doc_number: null` with `sap_created: true`. Reproduced on 2190, 2189,
    2169 (all null in detail, all with a doc number in the other two endpoints);
    null on all 8 orders fetched. **Use `sap_created` for "is it in SAP" and
    take the document number from `orders list` or `quotations overview`.**
  - The field is spelled **`vareity_cost`** — a backend typo. Any consumer must
    match that spelling exactly. It splits the order total by `variety_type`:
    verified on order 2530, commodity 29,436 + premium 48,051.40 + other 0 =
    77,487.40 = `total_amount`.
  - `created_by` is an **int user id** here but a **display name string** in
    `orders list`. Same field name, different type, across two endpoints.
  - Line quantities follow JIVO's usual convention and correction **C-0001**:
    on order 2530, `MUSTARD KACHI GHANI 1 LTR 20 PCS` has `qty 200`,
    `boxes 10`, `pcs 20`, `ltrs 200` — **`qty` is bottles, `boxes` is cartons,
    `pcs` is the carton pack size, not a count.** Multiplying `qty` by `pcs`
    inflates volume 20×.

### `/api/orders/ordersbyuser/{user_id}/`

- **command**: `orders by-user`
- **verdict**: publish
- **description**: Every order one salesman or manager has raised — the feed
  behind "View Orders" and the drafts screen.
- **params**:
  - `user_id` — int, **required, positional**. Source: `id` field of
    `/api/auth/users/list/` rows (52 users, live).
- **response**: `array`. **Verified live.** Row: `id`, `order_number`,
  `order_type`, `card_code`, `card_name`, `total_amount`, `status`,
  `status_display`, **`status_name`**, `created_by`, **`created_by_name`**,
  `created_at`, `delivery_date`, `is_foc`.
- **evidence**: **live parameterised calls** — user ids from
  `/api/auth/users/list/`, cross-checked against `created_by` names in
  `orders list`. `10` (tanjeet, manager) → 200, 137 rows, 49,193 B;
  `33` (mansi, billing) → 200, **365 rows**, 133,493 B; `3` (prince, manager)
  → 200, 120 rows, 42,520 B.
- **traps**:
  - **The row shape is not the same as `orders list`.** It gains `status_name`
    and `created_by_name`, and it **loses `sap_doc_number`, `items_count` and
    `employee_id`**. A shared row formatter across the two commands will print
    blank columns.
  - Unlike `orders list`, this returns the user's **whole** history including
    completed orders (mansi: 365 rows vs 60 of her orders visible in the bare
    list). It is the more complete of the two views, per user.
  - Drafts are only reachable here — the app filters this response client-side
    on `status_display == "draft"` to build the drafts screen. There is no
    server-side draft filter.

### `/api/orders/parties/`

- **command**: `orders parties`
- **verdict**: publish
- **description**: The trading parties **assigned to the calling user** — the
  party dropdown a salesman sees when raising an order. Not a master list.
- **params**: none. The app calls it bare.
- **response**: `array` — live `[]`. Row shape **UNVERIFIED**; the app's
  consumer reads `value`/`card_code` and a name field.
- **evidence**: bare → 200, `[]`, 2 B.
- **traps**:
  - **Why it is empty, established by a second endpoint, not assumed:**
    `GET /api/auth/users/62/parties/` (user 62 = `paramjot`, the credential in
    use) returns `{"user":{"id":62,"username":"paramjot"},"parties":[],
    "card_codes":[],"total_assigned":0}`. By contrast user 33 (`mansi`) has
    `total_assigned: 20` and user 10 (`tanjeet`) has 24. So this endpoint is
    **assignment-scoped to the caller**, the admin role does **not** bypass the
    assignment table, and `[]` means "paramjot has been assigned zero parties" —
    a data fact about one user, not a property of the endpoint. Per the contract
    this must **not** become a constraint on the command. A salesman's token
    will return rows.
  - Do not describe this as a party master. The party master is
    `sap parties` / `sap parties-category`.

### `/api/orders/party-flow-config/`  *(dual-verb: GET + POST + DELETE — GET only)*

- **command**: `orders party-flow-config`
- **verdict**: publish (GET). The `POST` and `DELETE` on this same URL are
  excluded — see § Excluded.
- **description**: The parties that have been carved out of the global approval
  flow and given their own rules — today, 2 of them.
- **params**: none. The app calls it bare.
- **response**: `object` — `{success, data[], flow_options[], condition_options[]}`.
  A `data` row: `card_code`, `card_name`, `category`, `flow_type`, `flow_label`,
  `rate_approval_enabled`, `billing_enabled`, `auditor_enabled`,
  `rate_conditions[]`, `updated_at`, `updated_by`.
- **evidence**: bare → 200, 1,197 B, 2 rows (re-confirmed live; row 0 =
  `CUSTA000486` WAL MART INDIA PVT LTD, category OIL, flow BILLING).
- **traps**:
  - Rows here **override** `orders flow-config` for those card codes. Any
    "which approvals does this order need" answer has to check this first.
  - The rows are in `data`, not at the top level — unlike the sibling
    `flow-config`, which returns its config bare. Two shapes for two neighbours.

### `/api/orders/party-products/{card_code}/`

- **command**: `orders party-products`
- **verdict**: publish
- **description**: The SKUs a given party is allowed to order and the rate each
  one carries for them — the product picker on the order screen.
- **params**:
  - `card_code` — string, **required, positional**. Source: `card_code` field of
    `/api/orders/list/` rows and of `/api/auth/users/{id}/parties/`.
- **response**: `array`. **Verified live.** Row: `item_code`, `item_name`,
  `category`, `brand`, `variety`, `sub_group`, `basic_rate` (float),
  `tax_rate`, `sal_factor2` (units per carton), `sal_pack_unit` (litres per
  unit, as a string), `combo_scheme_id`, `combo_scheme_name`.
- **evidence**: **live parameterised calls** — card codes from
  `/api/orders/list/`. `CUSTA000844` → 200, 67 rows, 18,729 B;
  `CUSTA000636` → 200, 24 rows, 6,932 B.
- **traps**:
  - This is **not** gated on the caller's own assignments. `paramjot` has zero
    assigned parties yet gets 67 rows for `CUSTA000844`. It is a lookup by card
    code, which is exactly why it works when `orders parties` returns `[]`.
  - The 67 rows for `CUSTA000844` match `total_assigned: 67` from
    `GET /api/auth/parties/CUSTA000844/products/` — the same party-product
    assignment table, exposed twice.
  - `basic_rate` is the **party-specific** rate. It is not the price list. Both
    parties above returned BEVERAGES SKUs first, so the list spans categories —
    filter on `category` client-side if the operator asked about oil.

### `/api/orders/products/`

- **command**: `orders products`
- **verdict**: publish
- **description**: The product list the order screen loads for the current user.
- **params**: none. The app calls it bare.
- **response**: `array` — live `[]`. Row shape **UNVERIFIED**.
- **evidence**: bare → 200, `[]`, 2 B.
- **traps**:
  - Zero rows is a data fact for this credential, not a constraint. **Why is
    inferred, not proven**: `orders parties` is provably assignment-scoped
    (paramjot `total_assigned: 0`), this endpoint is loaded on the same Create
    Order screen alongside it, and the party-product assignment table demonstrably
    has rows (67 for `CUSTA000844`). Most likely it is the union of products
    across the caller's assigned parties, hence empty for a user with none.
    **I could not verify this — I have one credential and it has no
    assignments.** Do not encode the emptiness either way.

### `/api/orders/quotation-overview/`

- **command**: `quotations overview`
- **verdict**: publish
- **description**: Every order that has been pushed to SAP as a sales quotation,
  with its SAP document number and whether it has since been cancelled.
- **params**: none. The app calls it bare. (`?branch=OIL` was tried and is
  ignored — see traps.)
- **response**: `object` — `{success, data[], sap_error}`. A `data` row: `id`,
  `order_number`, `card_code`, `card_name`, `created_at`, `doc_num`,
  `doc_entry`, `quotation_cancelled`, `quotation_cancelled_at`,
  `quotation_cancelled_by`, `quotation_status`.
- **evidence**: bare → 200, **1,898 rows / 590,698 B** (re-confirmed live).
  1,582 of the 1,898 rows carry a `doc_num`; 0 are cancelled.
- **traps**:
  - **`quotation_status` is `"UNKNOWN"` on all 1,898 rows, and the response
    carries the reason in its own `sap_error` field:**
    `"SalesOrderService.get_quotation_status() missing 1 required positional
    argument: 'branch'"`. The open/closed badge feature is dead server-side (see
    § Backend defects). Never report `quotation_status` as a business answer.
  - 590 KB unpaginated. Needs `--compact`/`--csv`.
  - Row count (1,898) is exactly the `COMPLETED` count from
    `orders list --status COMPLETED`. This endpoint is effectively the completed
    book — the slice the bare `orders list` omits.

### `/api/orders/quotation-status/`

- **command**: `quotations status`
- **verdict**: publish — but see the defect. It is a live GET returning 200; it
  is not dead, it is broken downstream.
- **description**: Asks SAP whether specific quotations are still open or have
  been closed/converted.
- **params**:
  - `order_ids` — string, optional, query. Comma-separated order ids. Source:
    the app's call site `params:{order_ids:e.join(',')}`. Values from
    `/api/orders/list/` and `/api/orders/quotation-overview/`.
- **response**: `object` — `{success, statuses{}}`, plus an `error` string when
  `success` is false.
- **evidence**: bare → 200, `{"success":true,"statuses":{}}`. **Live with real
  ids**: `?order_ids=2530,2528,2529` → 200, `{"success":true,"statuses":{}}`;
  `?order_ids=2392,2190,2189,2169,2168` (five orders that provably have SAP doc
  numbers) → 200,
  `{"success":false,"statuses":{},"error":"SalesOrderService.get_quotation_status()
  missing 1 required positional argument: 'branch'"}`;
  adding `&branch=OIL` → identical error.
- **traps**:
  - **The endpoint returns HTTP 200 while failing.** The failure is in the body
    (`success:false`). A CLI that only checks the status code will report an
    empty result as a successful "no quotations found". It must surface
    `success` and `error`.
  - **`branch=OIL` does not fix it** — the missing argument is missing inside
    the view, not from the request. Verified.
  - Passing ids that have no SAP quotation returns `success:true` with an empty
    `statuses` map — indistinguishable from the broken case unless you read
    `success`.

### `/api/orders/schemes/`

- **command**: `orders schemes`
- **verdict**: publish
- **description**: The live sales schemes — the "buy N boxes, get 1 free"
  promotions a salesman can attach to an order line, by state.
- **params**:
  - `state_code` — string, optional, query. **Not in the shipped spec.** Source:
    the app's own call site, `getSchemeProducts:async e=>(await
    Y.get('/orders/schemes/',{params:e?{state_code:e}:void 0}))`. Values from
    the endpoint's own payload (`UP`, `HR`, …) and from
    `/api/auth/states/`.
- **response**: `array` of `{scheme_id, scheme_name, state_code}`.
- **evidence**: bare → 200, 72 rows, 5,338 B. Live `?state_code=UP` → 200,
  **4 rows**, 342 B — a real filter, previously undocumented.
- **traps**:
  - Scheme names encode the offer in free text ("( GN ) 1 LTR PER BOX PER 1 PCS
    CANOLA 1 LTR"). There is no structured qty/free-qty here — that is in
    `orders schemes-manage`.
  - Schemes are **state-scoped**. Quoting a scheme without its state is
    meaningless; the same product carries different schemes in UP and HR.

### `/api/orders/schemes/manage/`

- **command**: `orders schemes-manage`  *(NEW — no shipped name)*
- **verdict**: publish (the path segment is "manage", but the `GET` is a plain
  read; the writes are on `/api/orders/create-scheme/` and
  `/api/orders/schemes/{id}`, both excluded)
- **description**: The full scheme table behind the scheme admin screen — each
  scheme joined to the SKU it applies to, its pack size, its state, and whether
  it is switched on.
- **params**:
  - `state_code` — string, optional, query. Source: app call site
    `getSchemesForManage` (`...e?.state_code?{state_code:e.state_code}:{}`).
  - `search` — string, optional, query. Same source.
  - `include_inactive` — string `"true"`, optional, query. Same source; the app
    emits the literal string `'true'`.
- **response**: `object` — `{success, data[], total}`. A `data` row:
  `scheme_id`, `scheme_name`, `is_active`, `state_code`, `state_name`,
  `product_id`, `item_code`, `item_name`, `sal_factor2`, `sal_pack_unit`.
- **evidence**: bare → 200, 72 rows, 17,823 B. Live
  `?state_code=UP&include_inactive=true` → 200, 4 rows, 1,116 B;
  `?search=CANOLA` → 200, 15 rows, 3,824 B. All three params work.
- **traps**:
  - Bare returns 72 rows — the same count as `orders schemes`. Since
    `include_inactive=true` on UP also returned 4 (same as active-only), **I
    could not demonstrate that any inactive scheme currently exists**, so I
    cannot confirm what `include_inactive` changes. Documented, not asserted.
  - `item_code`/`item_name` here is the **scheme's own SKU** (what gets given
    free), which is why the name reads "COLD PRESS 1 LTR (NIRMAL RISHI) 20 PCS"
    against a scheme called "1 LTR PER BOX PER 1 PCS CANOLA 1 LTR".

### `/api/orders/staff-products/`  *(dual-verb: GET + POST — GET only)*

- **command**: `orders staff-products`
- **verdict**: publish (GET). The `POST` on this same URL saves staff product
  rates — excluded, see § Excluded.
- **description**: The SKUs and rates set up for staff/employee orders (the
  `STAFF` order type), for the calling user.
- **params**: **none.** The brief lists `flow_type` as observed at the call
  site; that is a **false attribution** — see § Traps across the domain. The
  app's `getStaffProducts` sends no params at all.
- **response**: `array` — live `[]`. Row shape **UNVERIFIED**; from the app's
  consumer a row has at least `id`, `item_code`, `category`.
- **evidence**: bare → 200, `[]`, 2 B. Live `?flow_type=ASM` → 200, `[]` —
  unchanged, consistent with the param not existing (though an empty result
  cannot prove that).
- **traps**:
  - Zero rows is a data fact. Same assignment family as `orders parties`, which
    is provably empty for user 62. **Inferred, not proven**, for the same reason
    as `orders products`.
  - Every order visible to this credential has `order_type: "PARTY"` (263/263
    in `orders list`). Staff orders exist as a concept in the app but none are
    in this data set.

### `/api/orders/status/`

- **command**: `orders status`
- **verdict**: publish
- **description**: The eleven states an order can be in, with their ids — the
  lifecycle master.
- **params**: **none.** The brief lists `mode` as observed at the call site;
  that is a **false attribution** from the neighbouring `status-tracking`.
  **Disproved live**: `?mode=auditor` and `?mode=billing` both return the same
  335-byte body as the bare call. The app's `getOrdersStatus` sends no params.
- **response**: `array` of `{id, name}`. Full contents, verified live:
  1 Order Created · 2 Rate Approval · 3 Billing · 4 Need Approval ·
  5 Billing Pending · 6 Approved · 7 Rejected · 8 Billing Rejected ·
  9 Completed · 10 Auditor Approval · 11 Draft.
- **evidence**: bare → 200, 11 rows, 335 B; `?mode=auditor` → 200, 335 B,
  byte-identical; `?mode=billing` → 200, 335 B.
- **traps**:
  - These are **display names**, not the codes `orders list --status` takes.
    "Billing Rejected" ↔ `BILLING_REJECTED`, "Order Created" ↔ `CREATED`,
    "Rate Approval" ↔ `RATE_APPROVAL`. The mapping is by convention, and I only
    verified 8 of the 11 codes against live data — `Need Approval`,
    `Billing Pending` and `Draft` never appeared, so their codes are unknown.
    Do not have the CLI generate codes from these names.
  - `status_id` in `orders logs` refers to **this** table.

### `/api/orders/status-tracking/`

- **command**: `orders status-tracking`
- **verdict**: publish
- **description**: The approval queue for one gate — what the auditor, the
  billing desk, or the rate approver is currently sitting on.
- **params**:
  - `mode` — string, **required**, query. Enum **`auditor` | `billing` |
    `rate_approver`**. Source: the server's own 400 body,
    `{"error":"mode must be auditor, billing, or rate_approver"}` — the server
    named the enum verbatim.
- **response**: `array`.
- **evidence**: bare → 400 with the enum. Live: `?mode=auditor` → 200, `[]`;
  `?mode=billing` → 200, `[]`; `?mode=rate_approver` → 200, `[]`. All three
  accepted, all three empty for this credential.
- **traps**:
  - **`mode` here and `mode` on `orders status` are not the same thing** —
    `orders status` has no `mode` at all (disproved above). Do not share a flag
    definition between them.
  - Three empty queues is a data fact: a global admin sits in nobody's approval
    queue. The queue is per-approver, and `orders list --status
    AUDITOR_APPROVAL` does return the 1 order that is genuinely waiting. So
    "empty" here does not mean "nothing is pending" — it means "nothing is
    pending **for you**". That distinction will burn an operator.
  - The app itself treats an empty `rate_approver` queue as a miss and falls
    back to `orders list --status APPROVED`.

### `/api/orders/stock-check/`

- **command**: `orders stock-check`
- **verdict**: publish
- **description**: Every order's line items with required quantity set against
  the stock actually available for that SKU — the "can we actually ship this"
  view.
- **params**: none. The app calls it bare.
- **response**: `array` of `{id, order_number, date, customer, order_type,
  dispatch_from, status, items[]}`; `items[]` = `{item_code, item_name,
  category, required_qty, available_stock}`.
- **evidence**: bare → 200, **1,900 orders / 4,592 line items / 1,062,456 B**
  (re-confirmed live). Statuses present: Completed 1,896, Rejected 3,
  Billing Rejected 1.
- **traps**:
  - **1.06 MB in one unpaginated response, and 99.8% of it is already-completed
    orders.** As a "can we ship this" tool it is nearly useless in its default
    form — the orders that still need a stock decision are not in it. Any
    command must filter client-side and offer `--compact`/`--csv`.
  - **`dispatch_from` is rendered inconsistently by the backend**: 1,240 rows
    say `"FACTORY"` and 660 say `"2"` — the name for some rows, the raw BPL id
    for others, in the same response. Do not group on it.
  - `status` here is the **display name** ("Billing Rejected"), a third
    vocabulary alongside `orders list`'s codes and `orders status`'s master.
  - `required_qty` is in pieces (bottles), consistent with correction C-0001.

### `/api/orders/web-push/public-key/`

- **command**: `orders web-push-key`  *(NEW — no shipped name)*
- **verdict**: publish
- **description**: The VAPID public key the browser needs to register for OMS
  push notifications. Infrastructure, not business data.
- **params**: none.
- **response**: `object` — `{public_key: "<base64url>"}`.
- **evidence**: bare → 200, 104 B.
- **traps**: no operator value — it exists only so a browser service worker can
  subscribe. Published for completeness because it is a live, harmless GET, not
  because anyone will run it. Its write counterpart
  (`web-push/subscribe/`) is excluded.

### `/api/orders/{id}/orderlogs/`

- **command**: `orders logs`
- **verdict**: publish
- **description**: The status-change audit trail for one order — who moved it,
  to what, when, and with what remark. This is what drives the tracking
  timeline.
- **params**:
  - `id` — int, **required, positional**. Source: `id` field of
    `/api/orders/list/` rows.
  - **`order_ids` is NOT a param of this endpoint.** The brief lists it as
    observed at the call site; that is a **false attribution** from the
    adjacent `getQuotationStatus`. The app's `getOrderLogs` sends no query
    params.
- **response**: `array` of `{id, status_id, status_name, remarks, created_at}`.
  **Verified live.**
- **evidence**: **live parameterised call** — id from `/api/orders/list/`.
  `GET /api/orders/2530/orderlogs/` → 200, 108 B, 1 row:
  `[{"id":11991,"status_id":3,"status_name":"Billing","remarks":"",
  "created_at":"2026-08-04T08:29:39.685382Z"}]`.
- **traps**:
  - `status_id` joins to `orders status`, and `status_name` is the **display
    name**, not the code.
  - Order 2530 was created and is sitting in Billing, yet has only **one** log
    row — the creation transition is not logged separately. Do not present the
    log as a complete history; it records status changes the workflow wrote,
    which may start mid-lifecycle.
  - `created_at` here is UTC with a `Z`; `created_at` on the order header in
    `orders list` has **no timezone suffix** at all. Same field name, different
    serialisation, in the same domain.

---

## Excluded — writes. RULE 0, no exceptions, not even if asked.

Eight paths. None was probed, in any form, at any point.

| path | verb(s) | command it would have been | exclusion reason |
|---|---|---|---|
| `/api/orders/create/` | POST | — | write verb — creates a sales order (also used for "save draft", with `is_draft:true`) |
| `/api/orders/create-scheme/` | POST | — | write verb — creates a sales scheme |
| `/api/orders/{id}/update-status/` | POST | — | write verb — moves an order through the approval flow (`{status, reason}`) |
| `/api/orders/{id}/cancel-quotation/` | POST | — | write verb — cancels the SAP sales quotation |
| `/api/orders/{id}/delete-draft/` | DELETE | — | write verb — deletes a draft order |
| `/api/orders/schemes/{id}/` | PATCH, DELETE | — | write verb — edits/deletes a scheme (DELETE takes `?hard=true`) |
| `/api/orders/notifications/{id}/` | PATCH | — | write verb — marks one notification read |
| `/api/orders/web-push/subscribe/` | POST, DELETE | — | write verb — registers/removes a push subscription |

### Dual-verb paths — publish the GET, deny the write, key on (path, method)

These four paths appear **both** above (published, GET) and here (denied, write
verb). They are the same URL. Denying by path alone removes four working reads,
including the two approval-flow config commands an operator actually needs.

| path | published verb | denied verb(s) | what the write does |
|---|---|---|---|
| `/api/orders/flow-config/` | **GET** → `orders flow-config` | POST | overwrites the global approval-flow rulebook |
| `/api/orders/notifications/` | **GET** → `orders notifications` | POST | marks **all** notifications read |
| `/api/orders/party-flow-config/` | **GET** → `orders party-flow-config` | POST, DELETE | adds / removes a per-party flow override |
| `/api/orders/staff-products/` | **GET** → `orders staff-products` | POST | saves staff product rates (`{products, removed_products}`) |

---

## Domain summary

**What this domain is.** This is JIVO's order book and the approval machinery
around it: a salesman picks a party and its allowed SKUs, the order goes through
up to three gates (rate approval → billing → auditor), and on completion it is
pushed into SAP B1 as a sales quotation. `orders/*` covers the whole of that —
the queue, one order in full, its audit trail, the party/product/address lookups
the order screen needs, the schemes attached to lines, who approves what, and
the dashboard that reports on all of it. 2,163 orders exist; 1,898 are complete
and 1,582 of those carry a SAP document number.

### Traps that apply across the whole domain

1. **Three vocabularies for one lifecycle.** `orders list --status` takes codes
   (`BILLING_REJECTED`); `orders status`, `dashboard summary.status_counts`,
   `orders logs.status_name` and `orders stock-check.status` all use display
   names ("Billing Rejected"). Nothing in the API maps between them. Only 8 of
   the 11 codes were observed live — `Need Approval`, `Billing Pending` and
   `Draft` have no confirmed code, so the CLI must not derive codes from names.

2. **The brief's "params observed at the call site" is contaminated by
   proximity, and three of them are wrong.** These are minified neighbours, not
   real params:
   - `mode` on `/api/orders/status/` — **disproved live** (`?mode=auditor`
     returns a byte-identical body); it belongs to `status-tracking`.
   - `order_ids` on `/api/orders/{id}/orderlogs/` — belongs to the adjacent
     `getQuotationStatus`.
   - `flow_type` on `/api/orders/staff-products/` — belongs to the adjacent
     `getOrderFlowConfig`.

   Conversely the brief **misses** real, working params the app does send:
   `state_code` on `orders schemes` (72 → 4 rows), and `state_code` / `search` /
   `include_inactive` on `orders schemes-manage`. Read the service module, not
   the harvest's param field.

3. **Reads and writes share URLs.** Four paths here (§ Dual-verb) serve a GET
   and a mutation on the identical URL. Any denial keyed on path alone is both
   unsafe-adjacent and destructive.

4. **Payload sizes are a design constraint, not a detail.** `orders stock-check`
   1.06 MB, `orders list --status COMPLETED` 732 KB, `quotations overview`
   590 KB, `dashboard charts` 287 KB, `orders addresses` 45 KB for one party.
   All unpaginated. Every one of these needs `--compact`/`--csv` to be usable,
   and `dashboard charts --month` cuts 287 KB to 20 KB.

5. **Empty ≠ scoped.** `orders parties`, `orders products`, `orders
   staff-products` and all three `orders status-tracking` modes return `[]` for
   this credential. For `parties` the cause is **proven**: user 62 has
   `total_assigned: 0` per `/api/auth/users/62/parties/`, while users 33 and 10
   have 20 and 24. These are data facts about one user and must not become
   constraints on the commands.

6. **Two different "branch"es.** `orders branch` returns SAP business places
   (`bpl_id`). The `branch` query param the hana domain demands takes
   `OIL`|`BEVERAGE` and picks a company database. Unrelated.

### Backend defects — reproductions for the OMS team

1. **`get_quotation_status()` is missing its `branch` argument.** Every
   quotation status lookup in OMS is dead.
   ```
   GET /api/orders/quotation-status/?order_ids=2392,2190,2189,2169,2168
   -> 200 {"success":false,"statuses":{},
           "error":"SalesOrderService.get_quotation_status() missing 1 required
                    positional argument: 'branch'"}
   ```
   The same error surfaces in `GET /api/orders/quotation-overview/` as
   `sap_error`, which is why all 1,898 of its rows read
   `quotation_status: "UNKNOWN"`. Adding `&branch=OIL` does **not** help — the
   argument is missing inside the view. This is the same class of defect as
   `/api/sku/pending/` (`getFGItems() missing 1 required positional argument:
   'branch'`, API-FACTS §3): a `branch` refactor that did not reach every
   caller. **Note the HTTP status is 200** — the failure is only in the body.

2. **`orderdetailsbyid` never returns `sap_doc_number`.** Null on all 8 orders
   fetched, including four (2392, 2190, 2189, 2169) where `orders list` and
   `quotations overview` both report a real document number. `sap_created: true`
   is set correctly. Reproduction:
   ```
   GET /api/orders/list/?status=COMPLETED    -> 2392 sap_doc_number 232607218
   GET /api/orders/quotation-overview/       -> 2392 doc_num 232607218, doc_entry 15746
   GET /api/orders/orderdetailsbyid/2392/    -> sap_doc_number null, sap_created true
   ```

3. **`stock-check` renders `dispatch_from` two ways in one response** — 1,240
   rows `"FACTORY"`, 660 rows `"2"`.

4. **Field name typo shipped in the API**: `vareity_cost` on the order detail.

5. **Type drift on `created_by`**: an int user id in `orderdetailsbyid`, a
   display-name string in `orders list`. And `created_at` carries a `Z` in
   `orderlogs` but no timezone in `orders list`.

### Durable JIVO business truth worth recording as a correction

- **An OMS order line's `qty` is in PIECES (single bottles); `boxes` is cartons
  and `pcs` is the carton pack size, not a count.** Verified on order 2530:
  `MUSTARD KACHI GHANI 1 LTR 20 PCS` → `qty 200, boxes 10, pcs 20, ltrs 200`.
  This is correction **C-0001** (SAP `INV1.Quantity`) holding in OMS too;
  multiplying `qty` by `pcs` inflates volume 20×.
- **OMS carries SAP's variety tagging through unchanged**, so correction
  **C-0003** applies here: use `variety_type` (`COMMODITY`/`PREMIUM`/`OTHERS`,
  = `OITM.U_TYPE`) and `variety`/`sub_group` (= `U_Sub_Group`), never
  item-name matching. Order 2530 proves it: `COLD PRESS 5 LTR` and
  `COLD PRESS 1 LTR` are both tagged `variety: CANOLA, variety_type: PREMIUM`
  with no "canola" in the name. The header's `vareity_cost` splits the order
  total on exactly this field — commodity 29,436 + premium 48,051.40 + other 0
  = 77,487.40 = `total_amount`.
- **`orders list` bare is the working queue, not the order book.** 263 rows vs
  2,163 orders. Anyone answering "how many orders do we have" from the bare list
  under-reports by 7×. The completed book is `--status COMPLETED` (1,898) or
  `quotations overview`.

### What I did not verify

- The exact server-side predicate behind `orders list`'s 263-row default. I
  proved it is incomplete; I did not work out the rule, and I did not guess one.
- Row shapes for `orders parties`, `orders products`, `orders staff-products`
  and `orders notifications` — all `[]` for this credential. Marked UNVERIFIED.
- Whether `orders products`/`orders staff-products` are assignment-scoped. Only
  `orders parties` is **proven** so; the other two are inferred from the same
  screen and the same assignment table, and I say so rather than assert it.
- What `include_inactive=true` changes on `orders schemes-manage` — no inactive
  scheme appeared in any slice I fetched.
- Whether `billing=false` / `approval_pending=false` are safe to send. Not
  observed values, so not sent (rule 2). The CLI should omit the params instead.
- `Need Approval`, `Billing Pending` and `Draft` status **codes** — never seen
  in live data.
- Anything about a non-admin or non-OIL credential. Every finding scoped to this
  user is labelled as such.

### Live calls made (all GET, nothing created)

Roughly 60 requests across: `orders/list/` (9 param combinations),
`orders/orderdetailsbyid/{2530,2528,2493,1570,2392,2190,2189,2169}/`,
`orders/2530/orderlogs/`, `orders/ordersbyuser/{10,33,3}/`,
`orders/party-products/{CUSTA000844,CUSTA000636}/`, `orders/addresses/`
(6 card_code × category combinations), `orders/status/` (3),
`orders/status-tracking/` (3 modes), `orders/schemes/` + `schemes/manage/` (3),
`orders/quotation-status/` (3), `orders/quotation-overview/` (2),
`orders/notifications/history/` (2), `orders/flow-config/` (2),
`orders/dashboardW/` (2), `orders/dashboardW/charts/` (5),
`orders/stock-check/`, `orders/party-flow-config/`, `orders/staff-products/`,
`orders/dispatches/`, `orders/branch/`, and — to source ids and prove the
assignment finding — `auth/users/list/`, `auth/users/{62,33,10}/parties/`,
`auth/parties/CUSTA000844/products/`.
