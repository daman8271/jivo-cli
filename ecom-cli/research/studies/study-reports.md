# Domain study — `reports` (Amazon PO lifecycle, delivery appointments, raw report views)

Bundle: `study/bundles/reports.json` · 16 endpoints · LIVE 10,
LIVE_NEEDS_PARAMS 3, GATED 2, UNPROBED 1.
Evidence: the bundle's live probes plus the SPA bundle in
`ecom-rescrape/bundle/` (`AmazonReportPage-BLx9otoW.js`, `Reports-C5n-R5Ns.js`,
`SkuPoPendency-3UpTl4Uw.js`, `AmazonBilling-BiLIzb_-.js`,
`AmazonDashboard-DrkflwCw.js`, `AmazonNewPoDashboard-BQx-Ys_W.js`,
`api-De44ElJm.js`).

---

## 1. What this domain is, in operator language

This is the Amazon vendor desk. Amazon sends JIVO purchase orders; this domain
tracks each one from the moment it lands to the moment the truck is booked into
Amazon's warehouse — what Amazon asked for, what we accepted, what we actually
delivered, what got cancelled, what is still owed, which invoice covers it, and
which lorry carried it.

The people who live in it are the Amazon key-account and dispatch team, deciding
today what to load and what is about to expire. Accounts uses two corners of it:
the billing view (PO → invoice → dispatch, all in one row) and the money totals.

There is also a general-purpose report reader (`reports raw` / `reports columns`)
that can pull any of the underlying master tables — including two SAP views —
which is a much wider door than the Amazon-only endpoints suggest.

---

## 2. Endpoint table

Command names in **bold** are shipped v0.1.0 names and must not change. Names in
*italics* are new and follow the existing `reports <slug>` style.

| command | path | what an operator gets | required params | status |
|---|---|---|---|---|
| **reports amazon-po** | `/api/reports/amazon-po` | The master Amazon PO sheet at **line level** — 10,247 rows. Per row: `po_number`, `order_date`, `expiry_date`, `status`, `availability_status`, `sku_code` (ASIN), `sku_name`, `external_id` (EAN), `sap_sku_code` / `sap_sku_name`, `item` (short name), `category`, `sub_category`, `item_status`, `po_status`, `fulfillment_center`, `vendor`, `case_pack`, `requested_qty` / `accepted_qty` / `received_qty` / `cancelled_qty` / `remaining_qty`, the same in boxes and litres, `cost_price`, `total_requested_cost` / `total_accepted_cost` / `total_received_cost` / `total_cancelled_cost`, `total_order_amt_exclusive`, `days_to_expiry`, `po_window`. Plus a `totals` block. | none — but **must be filtered**, see Trap 1 | LIVE |
| *reports amazon-po-billing* | `/api/reports/amazon-po/billing` | **PO → invoice → truck, joined.** One row per PO (`po_number`, `order_date`, `fulfillment_center`, `channel`, `status`) containing `lines[]` per ASIN (`sap_item_code`, `accepted`, `billed`, `shipped`, `shippable`, `fully_billed`) and inside each line `invoices[]` with `doc_num`, `doc_date`, `qty`, `type`, `amount` and a `dispatch` block (`vehicle`, `bilty_no`, `transporter`, `dispatch_date`, `dispatched`). Carries `last_sync`. 102 KB unfiltered. | none — but **must be filtered** | LIVE |
| **reports amazon-po-filter-options** | `/api/reports/amazon-po/filter-options` | The legal filter values, straight from the data: `asins[]`, `fulfillment_centers[]`, `po_statuses[]`, `item_statuses[]`, `months[]` (`{value,label}`), `years[]`, `channels[]`, `item_heads[]`. Run this before filtering anything. | none (takes no parameters at all) | LIVE |
| **reports amazon-po-matrix** | `/api/reports/amazon-po/matrix` | A done-vs-pending cross-tab for one month (the SPA renders `done_value`, `pending_value`, `dp_value`, `done_ltrs`, `pending_ltrs`, `dp_ltrs` with a grand total). Shape not captured — the probe stopped at validation. | **`month` and `year`** — live 400: `{"error":"month and year are required"}` | LIVE_NEEDS_PARAMS |
| **reports amazon-po-new-po** | `/api/reports/amazon-po/new-po` | Today's fresh POs, pre-summarised: `item_head_summary[]` (`count_of_po`, `unit_order`, `order_ltr`, `order_value`), `channel_summary` split premium/commodity, `po_summary[]` per PO with premium/commodity litres, `details[]` at line level, `totals`, and `filter_options.order_dates[]` listing every date that has POs. | none — **but it defaults to today only**, see Trap 9 | LIVE |
| *reports amazon-po-sku-pendency* | `/api/reports/amazon-po/sku-pendency` | What is still owed, per PO line: `requested_qty`, `accepted_qty`, `received_qty`, `cancelled_qty`, **`remaining_qty`**, the litre equivalents, `remaining_ltrs`, plus `has_invoice` and `is_dispatched` booleans and `core_fresh_now`. This is the "what do we still have to ship" list. | none | LIVE |
| *reports amazon-po-sku-pendency-options* | `/api/reports/amazon-po/sku-pendency/filter-options` | `categories[]` (20), `sub_categories[]` (43), `channels[]` = `CORE`, `FRESH`, `NOW`, `fulfillment_centers[]` (14). | none | LIVE |
| **reports amazon-po-summary** | `/api/reports/amazon-po/summary` | The whole-dataset scoreboard: `total_rows` 10,247, `unique_pos` 720, `unique_fcs` 22, `mov_pending_count` 1,028, `expiring_soon_count` 148, `total_order_value` ₹62.52 crore, `total_requested_qty` 15,86,657, `total_received_qty` 8,75,172, `fill_rate_pct` 55.2. Plus breakdowns by status, category, FC, item head, state and sub-category, `classification_kpis` (premium / commodity / others) and an `expiry_urgent[]` list. | none — **and it accepts none**, see Trap 3 | LIVE |
| **reports appointment** | `/api/reports/appointment` | Amazon delivery appointments: `appointment_id`, `status`, `appointment_time`, `creation_date`, `pos` (the PO number), `destination_fc`, `pro`, `month`, `year`. | none | LIVE |
| **reports appointment-filter-options** | `/api/reports/appointment/filter-options` | `pos_numbers[]` and `destination_fcs[]`. | none | LIVE |
| **reports appointment-summary** | `/api/reports/appointment/summary` | Appointment scoreboard: `total_rows` 716, `unique_appointments` 384, `unique_fcs` 20, `confirmed_count` 4, `closed_count` 396, `cancelled_count` 316, `today_count`, `this_week_count`; breakdowns by status, FC, day, PRO, SKU (`asin`, `product_name`, `total_qty`) and item head; `mom_trend[]` month over month. | none — accepts none | LIVE |
| **reports columns** | `/api/reports/columns` | The column list (`key`, `type`) for one report view — the thing you call *before* `reports raw` so you know what you are about to pull. | **`view`** — live 400: `["Unknown report view: ''"]` | LIVE_NEEDS_PARAMS |
| **reports raw** | `/api/reports/raw` | Rows from any report view: `{rows, count}`. The widest door in the domain — it reaches inventory, primary PO, total PO, the secondary-sales masters, and two SAP views. | **`view`** — live 400: `["Unknown report view: ''"]` | LIVE_NEEDS_PARAMS |
| *reports live-reports* | `/api/reports/live/reports` | Presumably the list of live reports. **403 for our credential — shape unverified.** | unknown | GATED |
| *reports live-data* | `/api/reports/live/data` | Presumably rows for a live report. **403 for our credential — shape unverified.** | unknown | GATED |
| ~~reports export~~ | `/api/reports/export` | POST, returns an .xlsx blob. **Excluded by RULE 0** — see §5. | — | UNPROBED (write) |

---

## 3. Traps

### Trap 1 — `reports amazon-po` counts **lines, not POs**, and most of them are cancelled *(observed)*
10,247 rows cover only **720 POs** (`summary.total_rows` vs `summary.unique_pos`).
And the status split is:

| status | rows |
|---|---|
| CANCELLED | 6,279 |
| COMPLETED | 2,924 |
| PENDING | 842 |
| MOV | 186 |
| *(blank)* | 12 |
| EXPIRED | 4 |

**61% of the rows are cancelled.** So `total_order_value` ₹62.52 crore is the
value of everything Amazon ever asked for including everything it then withdrew,
and `fill_rate_pct` 55.2 (= 8,75,172 ÷ 15,86,657, verified) is dragged down by
those same cancelled lines. Any headline taken unfiltered from this endpoint
describes an all-time superset, not current business.

### Trap 2 — the money here is **GST-exclusive**, the opposite of the `sap` domain *(verified arithmetically)*
`cost_price` 714.29 × 1.05 = **750.00** exactly. Billing `amount` 3,809.52 × 1.05
= **4,000.00** exactly; 57,142.86 × 1.05 = **60,000.00** exactly. And
`total_requested_cost` 294,287.48 = 412 × 714.29 exactly, so the totals are built
from the same net rate. The field name `total_order_amt_exclusive` says it
outright.

Meanwhile in the `sap` domain `DocTotal` is GST-**inclusive**. **The two domains'
rupee figures are on different bases and must never be added or compared without
adjusting.** (The 1.05 assumes the 5% edible-oil slab, which the SAP invoices in
the sibling domain independently confirm at exactly 5%.)

### Trap 3 — the `summary` and `filter-options` endpoints accept **no parameters at all** *(observed)*
In `api-De44ElJm.js` they are declared zero-argument:
`amazonPOSummary: () => X('/api/reports/amazon-po/summary')`,
`amazonPOFilterOptions: () => …`, `appointmentSummary: () => …`,
`appointmentFilterOptions: () => …`, `amazonSkuPendencyOptions: () => …`.

So there is **no such thing as "this month's fill rate" from
`reports amazon-po-summary`** — the number is always all-time, and passing
`month`/`year` will be ignored rather than refused. A month figure has to be
built from `reports amazon-po` with `month`/`year` filters, or from
`reports amazon-po-matrix`.

### Trap 4 — `remaining_qty` is measured against **accepted**, not requested *(verified on the payload)*
SUNFLOWER 1L: requested 12,000, accepted 12,000, received 10,230,
`remaining_qty` 1,770 → 12,000 − 10,230 ✓.
MUSTARD 1L: 1,800 / 1,800 / 1,201 → 599 ✓.

But `fill_rate_pct` in the summary is `received ÷ requested`. So "pendency" and
"fill rate" have **different denominators**, and on a PO where Amazon requested
more than we accepted they will tell different stories. Neither is wrong; they
answer different questions.

Also `accepted_qty` can be 0 on a live PO (`status: "Unconfirmed"`,
`availability_status: "AC - Accepted: In stock"` — the two "accepted"s are
unrelated fields).

### Trap 5 — one row carries **three different product identifiers** *(observed)*
`sku_code` = the Amazon **ASIN** (`B093BMGPQC`), `external_id` = the **EAN
barcode** (`8908000258723`), `sap_sku_code` = the **SAP ItemCode** (`FG0000071`).
`item` is a short internal label ("EXTRA VIRGIN 1L") and `sap_sku_name` is the
SAP description. Matching this data to SAP goes through `sap_sku_code`; matching
it to Amazon goes through `sku_code`. Using the wrong one silently matches
nothing.

### Trap 6 — the category master contains a **misspelt duplicate** *(observed)*
`sku-pendency/filter-options` returns both `"SEASAME OIL"` and `"SESAME OIL"` in
`categories[]`, and both again in `sub_categories[]`. Filtering on one **misses
the rows tagged with the other**. Any sesame-oil total from this domain must
query both spellings, and should say so.

(Related, and consistent with JIVO's correction C-0003: `category` /
`sub_category` are the product taxonomy, while `item_head` is the
PREMIUM / COMMODITY / OTHERS classification. They are not interchangeable
groupings.)

### Trap 7 — the three FC lists **disagree with each other** *(observed)*
| source | fulfillment centres |
|---|---|
| `reports amazon-po-summary` | `unique_fcs`: **22** |
| `reports appointment-summary` | `unique_fcs`: **20** |
| `reports amazon-po-sku-pendency-options` | **14** listed: DED3, DED5, HBA4, HBL4, HCC2, HCC6, HDL2, HHS1, HHY7, HKA2, HKR2, HMU5, HNR4, HPN6 |

And the appointment summary's `fc_breakdown` contains **HCC5**, which is not in
the 14. So "which Amazon FCs do we serve" has three different answers depending
on which endpoint you ask — because each list is the distinct values present in
*that* dataset, not a master list. Say which endpoint an FC list came from.

### Trap 8 — `appointment` rows are **appointment × PO**, and `pos` is a PO number *(observed)*
716 rows, 384 unique appointments. Appointment `993448004986` appears three
times, once each for `pos` `1G9KK47R`, `7L94426U`, `7HR3JM2Q` — one delivery slot
covering three POs. So `status_breakdown` (396 Closed + 316 Cancelled + 4
Confirmed = 716) counts **rows**, not appointments, and "we have 316 cancelled
appointments" is wrong — 316 is cancelled *lines*.

The field name `pos` reads like "point of sale" or a plural. The SPA labels it
**"PO Number"**. It is a single PO number.

`confirmed_count: 4` is also a live-now figure (only future, un-closed slots), not
a historical total — 396 of the 716 are `Closed`.

### Trap 9 — `reports amazon-po-new-po` shows **one day** by default *(observed)*
The live response came back `selected_date: "2026-08-03"`, `date_from`
`2026-08-03`, `date_to` `2026-08-03`, `channel: "ALL"` — the probe day. An
operator asking "what POs came in this week" and running this bare gets today,
and today may legitimately be empty.

Second hazard: **the request parameter names differ from the response field
names.** The SPA sends `order_date_from` / `order_date_to`
(`AmazonNewPoDashboard-BQx-Ys_W.js`) but the response echoes `date_from` /
`date_to`. Sending `date_from` will probably be ignored, not refused.
`filter_options.order_dates[]` in the response lists every date that actually has
POs — use it to pick a real date rather than guessing.

### Trap 10 — two different **error body shapes** in one domain *(observed)*
`amazon-po/matrix` 400 → `{"error":"month and year are required"}` — a JSON
**object**.
`columns` and `raw` 400 → `["Unknown report view: ''"]` — a JSON **array**
(standard DRF field errors).
A CLI that parses one shape will print an unhelpful blank for the other. Handle
both.

### Trap 11 — the `reports raw` `view` enum: not observed live, but the SPA computes it deterministically *(SPA source; unverified against the API)*
The task brief said the legal values were not observed, and that is true of the
live probes — the only live evidence is the 400 `["Unknown report view: ''"]`.
**But the SPA does not take `view` from the user; it derives it**, in
`Reports-C5n-R5Ns.js`:

```js
function h({kind, platform, amazonMode, jmSource}) {
  return kind === 'inventory'  ? 'all_platform_inventory'
       : kind === 'primary'    ? 'master_po'
       : kind === 'total_po'   ? 'total_po'
       : kind === 'secondary'  ? (platform === 'amazon'
                                    ? (m.find(x => x.value === amazonMode) || m[0]).view
                                    : platform === 'amazon_mp'
                                      ? 'amazon_mp_master_view'
                                      : 'SecMaster')
       : (kind === 'jm_primary' || kind === 'jm_inventory')
                               ? `sap:${kind}:${jmSource === 'oil' ? 'oil' : 'mart'}`
       : null
}
// m = [{value:'range', view:'amazon_sec_range_master_view'},
//      {value:'daily', view:'amazon_sec_daily_master_view'}]
```

Which makes the complete set the SPA can ever send:

| `view` | reached by |
|---|---|
| `all_platform_inventory` | Inventory |
| `master_po` | Primary |
| `total_po` | Total PO |
| `amazon_sec_range_master_view` | Secondary → Amazon → Range |
| `amazon_sec_daily_master_view` | Secondary → Amazon → Daily |
| `amazon_mp_master_view` | Secondary → Amazon MP |
| `SecMaster` | Secondary → any other platform *(note the CamelCase — it is not snake_case like the rest)* |
| `sap:jm_primary:mart` / `sap:jm_primary:oil` | JM Primary |
| `sap:jm_inventory:mart` / `sap:jm_inventory:oil` | JM Inventory |

**Status of this list: derived from the shipped SPA, not confirmed by a live
call.** None of these eleven strings was sent to the API during the probe, so a
backend whose registry has drifted could still answer
`["Unknown report view: '…'"]`. To promote them to verified, either make one
live `GET /api/reports/columns?view=master_po` and see a column list, or read the
backend's report-view registry. **Do not extend this list by guessing** — a value
outside it has no evidence behind it at all.

### Trap 12 — `reports raw`'s `platform` filter takes the **display label**, not the slug *(SPA source)*
Same file: `platform` is built as `_.map(p => le[p]).join(',')` where

```js
le = {amazon:'AMAZON', blinkit:'BLINKIT', zepto:'ZEPTO', swiggy:'SWIGGY',
      bigbasket:'BIG BASKET', flipkart:'FLIPKART',
      flipkart_grocery:'FLIPKART GROCERY', zomato:'ZOMATO', citymall:'CITY MALL'}
```

So it is `BIG BASKET` **with a space**, not `bigbasket`; `CITY MALL`, not
`citymall`. Sending the slug will filter to nothing and look like "no data".
The SPA also **omits** `platform` entirely for the two `jm_*` (SAP) views.

### Trap 13 — `reports raw` can reach the SAP mirror, and it carries the Oil/Mart split *(SPA source)*
The `sap:jm_primary:*` and `sap:jm_inventory:*` views are the same Jivo Mart /
Jivo Oil pair documented in the `sap` domain study — `jmSource` is
`'oil'` or `'mart'` and nothing else, and Beverages is unreachable. A `reports
raw` pull of `sap:jm_primary:mart` is a **Jivo Mart** figure. Everything in the
`sap` study's company section applies verbatim here.

### Trap 14 — `item_head` filter says `OTHER`, the summary says `others` *(observed)*
`AmazonReportPage-BLx9otoW.js` offers the static filter options
`PREMIUM` / `COMMODITY` / `OTHER`, while `amazon-po/summary` returns
`classification_kpis.{premium, commodity, others}` and a separate
`item_head_breakdown[]`. Singular in the filter, plural in the response. Do not
feed one into the other.

### Trap 15 — `amazon-po-billing` is deeply nested and has a staleness stamp *(observed)*
The shape is PO → `lines[]` → `invoices[]` → `dispatch{}`, three levels deep in
102 KB. A flat table cannot represent it without exploding rows. It also returns
`last_sync` — this data comes from a sync, so **print `last_sync` with any answer
drawn from it**; a stale sync here looks exactly like "not yet invoiced".

It is nonetheless the most valuable endpoint in the domain for Accounts: it is the
only place where an Amazon PO, the SAP invoice number that billed it (`doc_num`,
`doc_date`), and the truck that carried it (`vehicle`, `bilty_no`, `transporter`,
`dispatch_date`) appear in one record.

### Trap 16 — litres are litres, quantities are pieces *(observed; consistent with correction C-0001)*
`requested_qty` 412 with `case_pack` 1.0 gives `requested_boxes` 412; SUNFLOWER 1L
requested 12,000 gives `total_order_liters` 12,000. So `requested_qty` is
**eaches/bottles**, `requested_boxes = requested_qty ÷ case_pack`, and
`total_order_liters = qty × per_liter`. Never multiply by a pack count in a
product name. For JIVO's tonnage convention, oil litres × 0.91 → kg.

### Trap 17 — the two `GATED` endpoints exist; a 403 is not a 404 *(observed)*
See §4/§5 below. `/api/reports/live/data` and `/api/reports/live/reports` returned
403 with DRF's generic `{"detail":"You do not have permission to perform this
action."}`. They are routed and alive; our credential simply lacks the
permission, and unlike the shipment gate **the SPA's permission map does not name
which permission it is** — I could not determine it from the bundle. They must be
published with their response shape marked unverified, and an operator who hits
403 should be told "your account lacks a permission", not "this report does not
exist".

---

## 4. Recommended spec entries

All GET, all `object` responses (from `live_response.top_type`), except the two
GATED ones whose type is unknown. Every parameter below came from a live 400 body
or from the SPA's own call sites — none is invented.

| command | description (operator-facing) | params |
|---|---|---|
| `reports amazon-po` | The full Amazon PO sheet, one row per PO line, with quantities, litres and net values. | `po_number` (string), `asin` (string), `fulfillment_center` (string), `month` (from `filter-options.months`), `year` (from `filter-options.years`), `channel` (enum: `CORE`\|`FRESH`\|`NOW`), `po_status` (from `filter-options.po_statuses`), `item_status` (from `filter-options.item_statuses`), `item_head` (enum: `PREMIUM`\|`COMMODITY`\|`OTHER`), `page`, `page_size`, `sort_by` (observed value: `expiry_date`), `helper` (observed value: `INCLUDE`) |
| `reports amazon-po-billing` | Each Amazon PO joined to the SAP invoice that billed it and the vehicle that carried it. | `search` (string), `billing_status` (string — the SPA's options include a "Fully billed" choice; the wire values were not observed), `fulfillment_center` (string), `channel` (`CORE`\|`FRESH`\|`NOW`), `page`, `page_size` |
| `reports amazon-po-filter-options` | The legal filter values for the PO sheet, taken from the live data. | none |
| `reports amazon-po-matrix` | Done-vs-pending cross-tab for one month. | **`month` (required)**, **`year` (required)**, `fc` (string), `channel` (string) |
| `reports amazon-po-new-po` | POs received on a given date (defaults to today), summarised by item head and channel. | `order_date_from` (`YYYY-MM-DD`), `order_date_to` (`YYYY-MM-DD`), `channel` (observed default `ALL`) |
| `reports amazon-po-sku-pendency` | What is still to be shipped per PO line, with invoice and dispatch flags. | `search`, `category`, `sub_category`, `channel` (`CORE`\|`FRESH`\|`NOW`), `fulfillment_center`, `have_invoice` (`1`), `dispatched` (`1`), `only_invoiced` (`1`), `page`, `page_size` |
| `reports amazon-po-sku-pendency-options` | The legal categories, sub-categories, channels and FCs for the pendency list. | none |
| `reports amazon-po-summary` | All-time Amazon PO scoreboard — value, fill rate, status/FC/category breakdowns, urgent expiries. | none (accepts none) |
| `reports appointment` | Amazon delivery appointments, one row per appointment × PO. | `appointment_id` (string), `pos` (PO number), `destination_fc` (string), `status` (enum: `Confirmed`\|`Closed`\|`Cancelled`), `appointment_time_from` (datetime), `appointment_time_to` (datetime), `page`, `page_size`, `status_exact` (observed value: `confirmed`) |
| `reports appointment-filter-options` | PO numbers and destination FCs present in the appointment data. | none |
| `reports appointment-summary` | Appointment scoreboard with status, FC, daily, PRO, SKU and month-over-month breakdowns. | none (accepts none) |
| `reports columns` | The column list for a report view — call this before `reports raw`. | **`view` (required)**. See Trap 11 for the eleven values the SPA can send and their (unverified) status. |
| `reports raw` | Rows from any report view, including two SAP views. | **`view` (required)**, `page`, `page_size`, `date_from` (`YYYY-MM-DD`), `date_to` (`YYYY-MM-DD`), `platform` (comma-separated **display labels**, e.g. `AMAZON,BIG BASKET` — see Trap 12) |
| `reports live-reports` | The live-reports list. **Response shape unverified — 403 for our credential.** | none observed |
| `reports live-data` | Rows for a live report. **Response shape unverified — 403 for our credential.** | takes a params object; no parameter name was observed |

**On publishing the two GATED commands.** They should ship, with the description
saying plainly that access needs a permission our credential does not hold, and
with the CLI turning a 403 into "your ecom account lacks permission for live
reports" rather than a raw stack. To verify them someone needs to (a) grant the
missing permission to the CLI's service account and re-probe, or (b) capture a
successful call from a browser session belonging to a user who already has it —
a DRF `PermissionDenied` gives no clue which permission is missing, and the SPA
does not name it.

---

## 5. Exclusions

### `/api/reports/export` — **write endpoint, excluded by RULE 0. Not dead.**
The SPA calls it with **POST only** (`exportRows: e => Ee('/api/reports/export', e)`,
where `Ee` is the blob-POST helper; the harvest recorded
`client_methods: ["POST"]` and `harvest_decision: "EXCLUDE_WRITE"`). It takes
`{view, columns[], labels[], filename, filters[], date_from, date_to, platform}`
and returns an `.xlsx` blob the browser downloads.

It is almost certainly harmless in practice — it generates a file, it does not
mutate business data — **but ecom is read-only in this toolkit and RULE 0 draws
the line at the HTTP verb, not at our guess about side effects.** It was never
probed, so we have no evidence about what it does server-side. Excluded as a
write endpoint; not excluded as dead. Anyone who wants an export can pull the
same rows through `reports raw` and format them locally.

### Nothing is excluded as dead or broken
No 404 and no 5xx was recorded anywhere in this domain — 16 of 16 endpoints are
routed and responding. The two 403s (`live/data`, `live/reports`) are
**published**, not excluded: a permission gate is evidence the endpoint exists.
The three 400s (`amazon-po/matrix`, `columns`, `raw`) are **published**, not
excluded: they are telling us, correctly, which parameter we forgot.
