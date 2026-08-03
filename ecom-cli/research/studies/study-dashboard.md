# Domain study — `dashboard` (35 endpoints)

Evidence: `bundles/dashboard.json` (harvest + live probe, 2026-08-03) plus the
shipped SPA bundle at `ecom-rescrape/bundle/` — `api-De44ElJm.js` (the API
client), `Dashboard-Ci-nVmGI.js`, `StateSalesMap-ddq0BR5f.js`,
`RealiseDashboard-Swjb6XJE.js`, `PenetrationReport-D-5IXm27.js`,
`PaginatedTable-C4rt_G6C.js`, `DistributorLeadTimeReport-j325ZCaA.js`,
`useDashboardData-9fTMrSwQ.js`. No HTTP request was made.

Probe status counts: **28 LIVE, 3 LIVE_NEEDS_PARAMS, 4 UNPROBED.**
Recommended: **publish 33, exclude 2** (both writes).

---

## 1. What this domain is

This is the **company-wide view across every online channel at once** — Amazon,
Blinkit, Swiggy Instamart, Zepto, BigBasket, Flipkart, Flipkart Grocery,
JioMart, Zomato and CityMall added together. Everything else in the ecom app is
"tell me about one platform"; this is "tell me about the business."

It answers four kinds of question. **How much did we sell and where** — litres
by oil category, by SKU, by state and city, month on month and year on year.
**What are we actually netting** — the `realise-*` family, ₹ per litre after
distributor commission, ads spend and brand fund. **Where are we about to get
hurt** — POs expiring in the next 1–5 days, fill rate against what the platforms
ordered, distributor lead-time slabs, cities where a SKU sells but has no stock.
And **what is in the raw data** — a generic browser over the 44 upload tables
that feed all of it.

Who opens it: the e-commerce head and the key-account managers for the sales and
fill-rate numbers; Accounts for realisation and PO value; whoever is chasing an
upload that did not land, for the table browser.

---

## 2. Endpoint table

`platform` is optional almost everywhere. **Omitting it means all platforms
combined** — every live response in this bundle came back with `"platform":
null` and totals that span the whole business. Pass a slug to narrow.

| command | path | what an operator gets | required params | status |
|---|---|---|---|---|
| `dashboard latest-month` | `/api/dashboard/latest-month` | Which month the dashboard considers "current": `month`, `year`, `month_label` ("AUGUST"), `source_date`, `defaulted`, `source`. Call this first if you don't know what period the other endpoints will default to. | — | LIVE |
| `dashboard category-breakdown` | `/api/dashboard/category-breakdown` | Litres for the month split PREMIUM vs COMMODITY, each with `categories[]` (OLIVE, GROUNDNUT, MUSTARD, SUNFLOWER, CANOLA, SESAME OIL) and `sub_categories[]` (JIVO POMACE, EXTRA LIGHT, MUSTARD KACCHI GHANI, YELLOW MUSTARD…), plus `total_ltrs` per head. All quantities in **litres**. | — | LIVE |
| `dashboard category-litres` | `/api/dashboard/category-litres` | One head only (`head`, default `premium`): `total_ltrs` and a flat `categories[]` of `{category, ltrs}`. A thinner slice of `category-breakdown`. | — | LIVE |
| `dashboard category-trend` | `/api/dashboard/category-trend` | Monthly series (6 by default): `{month, year, label "Jul '26", premium_ltrs, commodity_ltrs, total_ltrs}`. | — | LIVE |
| `dashboard category-platform-breakdown` | `/api/dashboard/category-platform-breakdown` | One category or sub-category split across platforms. Response not observed (400 without `name`); the SPA reads `platforms[]` with `ltrs` and `units` per platform. | **`name`** (verbatim from the 400: `"name is required."`) | LIVE_NEEDS_PARAMS |
| `dashboard category-sku-breakdown` | `/api/dashboard/category-sku-breakdown` | The SKUs inside one category, per platform, over the last N months. Response not observed; the SPA reads `skus[]` (each with `code`) and `months[]`. | **`name`** (verbatim: `"name is required."`) | LIVE_NEEDS_PARAMS |
| `dashboard top-skus` | `/api/dashboard/top-skus` | Ranked SKUs for the month: `name`, `head` (PREMIUM/COMMODITY), `code`, `brand`, `ltrs`, `prev_ltrs`, `delta_pct`, `is_new`; plus `top_riser` and `top_faller` and the comparison period (`prev_month`, `prev_year`). Litres. | — | LIVE |
| `dashboard secondary-yoy-growth` | `/api/dashboard/secondary-yoy-growth` | Sell-out for one anchor month across 2024/2025/2026, per platform. Each year holds `actual` (litres), `value` (₹), `units` (pieces), `growth_pct`, `projection`, `max_date`, `source` (the table it came from), `has_data`. Also a `totals` block per year. | — | LIVE |
| `dashboard state-sales` | `/api/dashboard/state-sales` | The India map: `states[]` with `units`, `value` and `by_platform{}`, `cities[]`, `total_units`/`mapped_units`, `total_value`/`mapped_value`, `pct_mapped`, and `filter_options` (brands, categories, sub_categories, items). 56 KB. | — | LIVE |
| `dashboard state-sales-export` | `/api/dashboard/state-sales/export` | The same thing flattened to one row per state × city × SKU × platform: `state, city, sku_code, item, format, order_ltrs, deliver_ltrs, sales, ltr_sold, units, orders`. **1,779 rows / 349 KB on a bare call — filter before you fetch.** | — | LIVE |
| `dashboard state-sales-detail` | `/api/dashboard/state-sales/detail` | Drill-down inside one state. Response not observed. | **`state`** (verbatim: `"state is required."`) | LIVE_NEEDS_PARAMS |
| `dashboard state-sales-detail-cities` | `/api/dashboard/state-sales/detail/cities` | Cities (or items) inside one state: `rows[]` plus `total{litres, units, value, orders, rows}` and `dimension`. | `state` — see trap T4 | LIVE (0 rows bare) |
| `dashboard state-sales-detail-city-skus` | `/api/dashboard/state-sales/detail/city-skus` | Top SKUs inside one city: `rows[]` plus the same `total{}` block. | `state` **and** `city` — see trap T4 | LIVE (0 rows bare) |
| `dashboard state-sales-detail-options` | `/api/dashboard/state-sales/detail/options` | Pick-lists for the drill-down: `skus[]`, `cities[]`. Returned both empty on a bare call. | not observed; almost certainly `state` | LIVE (empty bare) |
| `dashboard realise-overview` | `/api/dashboard/realise-overview` | This month vs last month: `value` (delivered value ₹), `ltrs` (delivered litres), `commission`, `ads_spent`, `brand_fund`, each also split `premium{}` / `commodity{}`. **The ₹/L figure is not in this payload** — see trap T6. | — | LIVE |
| `dashboard realise-breakdown` | `/api/dashboard/realise-breakdown` | The same five measures per category (or per sub-category), `rows[]` + `total{}`. Sample: MUSTARD ₹4,43,440 on 2,800 L, commission ₹20,437, ads ₹67,935, brand fund ₹4,191. | — | LIVE |
| `dashboard realise-trend` | `/api/dashboard/realise-trend` | 12-month series of the same measures, one point per month with a `label`. | — | LIVE |
| `dashboard realise-waterfall` | `/api/dashboard/realise-waterfall` | A per-litre bridge, and the **only** endpoint that returns ₹/L ready-made: `gross_rate` 238.75 → `tax_and_margin` 11.37 → `commission` 12.63 → `net_realise` 214.75, plus `realise_exclusive` 227.38 and `available: true`. | — | LIVE |
| `dashboard fulfilment-health` | `/api/dashboard/fulfilment-health` | Fill rate over a rolling window: `window{start, end, window_days 30, lag_days 7}`, `total{ordered_ltrs, filled_ltrs, missed_ltrs, fill_rate, miss_rate, po_count}` and the same `by_platform[]`. Litres. | — | LIVE |
| `dashboard lead-time-report` | `/api/dashboard/lead-time-report` | Distributor lead-time slabs in **litres**: `rows[]` by vendor and `platform_rows[]` by platform, each with `d7` / `d8_15` / `d15p` / `total`; plus `grand_total`, `slabs[]` labels and `filter_options{formats, months, years}`. | — | LIVE |
| `dashboard primary-po-litres` | `/api/dashboard/primary-po-litres` | Delivered litres per platform for the current month, plus an `errors[]` array. **Amazon was missing and erroring at probe time** — see trap T7. | — | LIVE |
| `dashboard platform-expiry-alerts` | `/api/dashboard/platform-expiry-alerts` | POs expiring in the next **1–5 days**, per platform: `po_count`, `total_litrs`, `total_units`, `total_order_units`; plus a `pendency` block (`pending_ltrs`, `pending_qty`, `pending_value` ₹14.17 Cr at probe, `pending_ltrs_premium`, `pending_ltrs_commodity`, `open_pos`). Mind trap T8 on `total_units`. | — | LIVE |
| `dashboard expiry-alerts-pos` | `/api/dashboard/platform-expiry-alerts/{platform}/pos` | The individual POs behind one platform's alert: `po_number`, `sku_name`, `item`, `days_to_expiry`, `expiry_date`, `po_status`, `location` (FC code), `total_litrs`, `total_units`, `total_order_units`. | `platform` slug in the path | LIVE |
| `dashboard expiry-alerts-po-items` | `/api/dashboard/platform-expiry-alerts/{platform}/pos/{po}/items` | Line items of one expiring PO. The SPA reads `items[]` and renders `po_status` and `location`. Never probed (no PO number was on hand) — carried forward from v0.1.0. | `platform` slug + PO number in the path | UNPROBED |
| `dashboard expiry-alerts` | `/api/dashboard/expiry-alerts/{table}` | Data-freshness alerts for **one upload table** — not a platform. Returns `{alerts: []}`; each alert carries a `table` field. The row shape could not be observed (the probe returned zero alerts). See trap T9. | a **table name** in the path | LIVE (empty) |
| `dashboard inventory-charts` | `/api/dashboard/inventory-charts` | Current stock on hand across platforms: `platform_totals[]` (`platform`, `total_qty`, `sku_count`), `city_distribution[]` (`city`, `qty`), `top_products[]` (`product`, `qty`, `platform`). **No period, no as-of date, and the unit of `qty` is not stated** — trap T10. | — | LIVE |
| `dashboard penetration-report` *(new)* | `/api/dashboard/penetration-report` | Distribution gap analysis: one row per city × item × platform with `sec_qty`, `sec_ltr`, `inv_qty`, `inv_ltr` and a `status` of `live` / `selling` / `stocked` / `inactive`; plus a `summary` (counts, `cities`, `items`, `universe_total`, `universe_source`, `cities_pending`, `covered_pct`, `pending_pct`) and `inventory_window{from, to}`. **2,492 rows / 21 KB on a bare call — page it.** | — | LIVE |
| `dashboard penetration-report-options` *(new)* | `/api/dashboard/penetration-report/options` | The pick-lists for the above: `formats[]` (7 observed), `item_heads[]` (COMMODITY, OTHER, PREMIUM), `categories[]` (33 observed), `sub_categories[]`, `years[]`. Call this before filtering. | — | LIVE |
| `tables counts` | `/api/dashboard/table-counts` | Row counts for all 44 upload tables in one object. The fastest "did the upload land?" check. | — | LIVE |
| `tables count` | `/api/dashboard/table-count/{table}` | `{table, count}` for one table. `all_platform_inventory` = 235,635 rows. | `table` | LIVE |
| `tables columns` | `/api/dashboard/table-columns/{table}` | `{columns: [...], sample: {…one real row…}}`. The sample row is the cheapest way to learn what a column means. | `table` | LIVE |
| `tables data` | `/api/dashboard/table-data/{table}` | Paged raw rows: `{data: [...], count, max_date}`. Supports search, date filtering, sorting and column filters. | `table` | LIVE |
| `tables distinct` | `/api/dashboard/table-distinct/{table}/{column}` | `{values: [...]}` — the distinct values in one column, for building a filter. Never probed (no column value was on hand); carried forward from v0.1.0. | `table`, `column` | UNPROBED |

---

## 3. Traps

### T1 — Omitting `platform` means *all platforms*, and the payload says so quietly
Every bare probe came back with `"platform": null` and business-wide totals.
`fulfilment-health` bare returned `ordered_ltrs` 16,15,499.06 L across
`po_count` 1,241 POs spanning CITY MALL, AMAZON, SWIGGY, FLIPKART GROCERY and
ZEPTO. An operator who reads "48.4% fill rate" without checking `platform` is
reading the whole company, not their account. **Always echo back which platform
(or "all platforms") a number came from.** Observed slugs, from the SPA's own
registry: `blinkit`, `zepto`, `jiomart` (marked hidden), `amazon`, `bigbasket`,
`swiggy`, `flipkart`, `flipkart_grocery`, `zomato`, `citymall`, plus
`amazon_mp`.

### T2 — `source` silently changes what data you are looking at
`category-*`, `top-skus` and the `realise-*` family take a `source`. The SPA's
own helper (`RealiseDashboard-Swjb6XJE.js`) reads:

> `E(e) = e ? (amazon|amazon_mp|flipkart ? "Secondary" : "Primary") : "Mixed"`

so with **no platform**, realise returns `"source": "mixed"` — primary
(PO/delivered) data for the q-commerce platforms *plus* secondary (sell-out)
data for Amazon, Amazon MP and Flipkart, added together. Confirmed live:
`realise-overview` bare returned `"source": "mixed"`, while `realise-waterfall`
bare returned `"source": "primary"`. **Two endpoints on the same screen
defaulted to different data sources.** Never compare a realise number to a
category number without checking both `source` fields.

### T3 — `state-sales`: `value` is not rupees
Live payload: `"metric": "units"`, `"metric_unit": "units"`, and MAHARASHTRA
came back as `{"units": 6628.0, "value": 6628.0}`. `value` mirrors whatever
`metric` is set to — the SPA reads it as `Number(e.value ?? e.units ?? 0)`.
Same for `total_value` / `mapped_value`. Read `metric`, `metric_label` and
`metric_unit` before you put a ₹ sign on anything. Observed `metric` values:
`litres`, `units`, `value`.

Also on this endpoint: `pct_mapped` is **the share of the metric that could be
attributed to a state at all** (the SPA legend reads "`{pct_mapped}`% of
`{metric}` mapped to a state"). `total_*` is everything; `mapped_*` is only what
landed on the map. Quoting the map total as company sales understates it.

### T4 — `.../detail/cities` and `.../detail/city-skus` returning zero rows is a *data* answer, not a broken endpoint
Both returned HTTP 200 with `rows: []` and `total` all zeros. The echo tells you
exactly why: `"state": null` on cities, `"state": null, "city": ""` on
city-skus. Nothing matched because no state was named. The SPA always calls them
with a state already chosen — `{...opts, state}` for cities, `{...opts, state,
city, limit: 10}` for city-skus. **These are healthy endpoints that need a
scope.** Do not report them as empty or dead. `state-sales/detail/options`
returned `{skus: [], cities: []}` for the same reason (inferred — the SPA never
calls it, so I could not confirm which param it wants).

### T5 — Two endpoints on `state-sales/detail*` are defined but unused by the app
`getStateSalesDetail` and `getStateSalesDetailOptions` exist in
`api-De44ElJm.js` and are called by **no page in the bundle**. They are live on
the server (`detail` returns a clean 400 naming `state`), so they are worth
publishing, but their parameter surface beyond `state` is **not observed** and
nobody in the office is exercising them.

### T6 — Realisation: the ₹/L number the business quotes is computed in the browser, not returned by the API
`realise-overview`, `-breakdown` and `-trend` return **five raw measures**
(`value`, `ltrs`, `commission`, `ads_spent`, `brand_fund`) and no per-litre
figure. The SPA derives it:

```
realise ₹/L = (value − commission − ads_spent − brand_fund) / ltrs
totalExpense = commission + ads_spent + brand_fund
```

A CLI that prints the raw fields and calls it "realisation" is printing
something else. Two more sharp edges in the same file:

* The KPI cards labelled **"Premium Realise (₹/L)"** and **"Commodity Realise
  (₹/L)"** use a *different* formula — `value / ltrs`, with **no deductions at
  all**. So on the live screen "Realise" means net for the overall row and gross
  for the premium/commodity rows. If you reproduce those splits, say which one
  you computed.
* The SPA labels `value` as **"Delivered Value"** and `ltrs` as **"Delivered
  Litres"** — these are delivered, not ordered.

**GST: I could not verify it.** Nothing in the payload or the SPA says whether
`value` is GST-inclusive. `realise-waterfall` is the only endpoint that touches
tax, and it lumps it: `gross_rate 238.75 − tax_and_margin 11.37 = realise_exclusive
227.38 − commission 12.63 = net_realise 214.75` (arithmetic checks out exactly).
What "tax_and_margin" contains is not documented anywhere I could see. **Do not
state a realisation figure as net-of-GST without asking Accounts.**

### T6b — Realisation read mid-month is nonsense
At probe time (3rd of August) `realise-overview` `current` held `value`
₹19,01,269 on 7,947.8 L but `ads_spent` ₹38,77,786 — ads for the month are
already booked while only three days of sales have landed. Apply the SPA's own
formula and you get **−₹263/L**. The same call's `previous` (full July) gives a
sane **₹178/L** on ₹23.06 Cr and 10.86 lakh litres. Meanwhile `realise-waterfall`
for the *same* month returned `net_realise` ₹214.75/L, because it uses a
completely different method and does not subtract ads or brand fund. **Three
plausible "realisation" numbers for August 2026 exist in this domain and they
disagree by hundreds of rupees a litre.** Quote the closed month, name the
endpoint, and show the formula.

### T7 — `primary-po-litres` was silently dropping Amazon
The live payload carries `errors: [{"source": "amazon_po", "error": "name
'month_num' is not defined"}]` — a Python `NameError` in the backend. The
`platforms[]` array came back with ZEPTO, FLIPKART GROCERY, BLINKIT, SWIGGY and
ZOMATO and **no Amazon row at all**, and HTTP 200. An operator totalling that
list gets a number missing the largest channel. Several endpoints here carry an
`errors[]` array (`category-*`, `realise-*`, `platform-expiry-alerts`,
`primary-po-litres`, `state-sales*`, `penetration-report`) and it is **empty on
all of them except this one**. Any command in this domain must surface a
non-empty `errors[]` prominently, not swallow it.

### T8 — `total_units` on the expiry endpoints is ₹, except on Amazon where it is units
The SPA drawer header order is `Order value` ← `total_units`, `Order units` ←
`total_order_units`, `Order litres` ← `total_litrs`, and the row renders
`isAmazon ? "—" : "₹" + total_units`. The live data agrees: SWIGGY
`total_units` 91,81,708.49 against `total_order_units` 46,317; AMAZON
`total_units` 35,567 = `total_order_units` 35,567. **`total_units` is order
value in rupees on every platform except Amazon, where it is a unit count.**
The name lies, and summing the column across platforms adds rupees to bottles.
`total_order_units` is pieces (single bottles, per correction C-0001);
`total_litrs` is litres.

### T8b — "Expiry" on `platform-expiry-alerts` means the PO expires, not the oil
The SPA subtitle reads "Unique POs expiring in **1–5 days** · per platform" and
the row fields are `days_to_expiry`, `expiry_date`, `po_status` (`PENDING`),
`location` (an FC code like `DED5`). This is a purchase order about to lapse
unfulfilled, not stock nearing its best-before date. The window is fixed at 1–5
days; I saw no parameter to widen it.

### T8c — `sku_name` and `item` disagree on the expiry PO rows
In the live `expiry-alerts-pos/amazon` payload one row has `sku_name` "sano
Sunflower Oil 5 Ltr Pet Bottle…" mapped to `item` "YELLOW MUSTARD 1L", and
another has `sku_name` "Jivo Pomace Olive Oil 5 Litre Tin…" mapped to `item`
"YELLOW MUSTARD 5L". `sku_name` is the marketplace listing title;`item` is the
internal SKU label, and on this endpoint they were **not consistent with each
other**. I could not determine which one is authoritative. Quote the PO number
and both fields; do not silently pick one.

### T9 — `expiry-alerts/{…}` takes a **table name**, and the shipped spec has it wrong
The v0.1.0 spec documents this path parameter as `{platform}`. The SPA proves it
is a table: `useDashboardData-9fTMrSwQ.js` calls `getExpiryAlerts(table)` once
per entry in a table list and then filters the results with `alert.table`.
`Dashboard-Ci-nVmGI.js` supplies that list — `master_po`, `total_po_zbs`,
`total_po`, `amazon_sec_daily`, `amazon_sec_daily_master_view`,
`amazon_sec_range`, `bigbasketSec`, `blinkitSec`, `flipkart_grocery_master`,
`flipkartSec`, `flipkart_secondary_all`, `swiggySec`, `zeptoSec`,
`amazon_price_data`, `amazon_inventory`, `bigbasket_inventory`,
`blinkit_inventory`, `swiggy_inventory`, `zepto_inventory`. The probe called
`/api/dashboard/expiry-alerts/amazon` and got `{"alerts": []}` — **a false
empty**, because `amazon` is not a table name. Fix the parameter name and
description; the command name `dashboard expiry-alerts` is a public contract and
must not change.

### T10 — `inventory-charts` has no period and no stated unit
The SPA calls it with **no arguments at all** (`getInventoryCharts: () => X(path)`)
and the payload echoes no `month`, `year` or as-of date. You cannot ask it for a
past month, and it will not tell you how fresh it is. The quantity fields are
bare `total_qty` and `qty`. **Inferred, not verified:** they are bottles — the
underlying `all_platform_inventory` table, sampled via `tables columns`, has
`soh_unit: 12` alongside `soh_ltr: 24.0` for an "EXTRA LIGHT 2L" row, i.e. 12
bottles × 2 L. If the CLI prints these, label them "qty (unit not stated by the
API)".

### T11 — `fulfilment-health`'s window ends a week ago, and its two rates do not add up
`window` came back `{start: 2026-06-27, end: 2026-07-27, window_days: 30,
lag_days: 7}` on a call made on 2026-08-03. It is a 30-day window ending **seven
days before today**, deliberately, so recent POs get a chance to be fulfilled.
It is not "this month" and it is not "as of today". And `fill_rate` 48.4 +
`miss_rate` 18.1 = 66.5, not 100 — because `filled_ltrs` 7,81,976.9 +
`missed_ltrs` 2,93,039.2 is well short of `ordered_ltrs` 16,15,499.06. Roughly a
third of ordered litres is neither filled nor missed. **Do not present
`100 − fill_rate` as the miss rate.**

### T12 — `category-breakdown` and `category-trend` disagree by 21 litres on the same month, same source
Both returned `"source": "primary"` for August 2026. `category-breakdown` gives
premium `total_ltrs` 4,446.8 (OLIVE 1,184.0); `category-trend`'s August point
gives `premium_ltrs` 4,467.8, as does `realise-overview` `current`, and
`realise-breakdown` lists OLIVE at 1,205.0 L. The gap is **entirely in OLIVE:
1,205.0 − 1,184.0 = 21.0 L**, which is exactly the 7,947.8 vs 7,926.8 total gap
(`realise-waterfall` also reports 7,926.8). I could not determine which is
right. Small in absolute terms, but it means **two endpoints will give an
operator two different olive numbers for the same month**, and olive is a
premium line where per-litre value is high. Reconcile before quoting.

### T13 — Mid-month comparisons in `top-skus` and `secondary-yoy-growth` look like a collapse
`top-skus` on the 3rd of the month returned MUSTARD 1L at 2,340 L against
`prev_ltrs` 2,04,020 L, i.e. `delta_pct` −98.9%, and every SKU in the list was
similarly down 80–99%. That is three days versus a full month, not a crash.
Likewise `secondary-yoy-growth` returned `has_data: false` for 2026 on Amazon
while 2024 and 2025 had full months. `top_riser` was `null` for the same reason.
Always print the period on both sides of a delta.

### T14 — `secondary-yoy-growth` puts three different quantities in one object
Each year holds `actual` (litres, matching the top-level `"metric": "ltrs"`),
`value` (rupees) and `units` (pieces). Amazon 2024: `actual` 1,28,916.55 L,
`value` ₹3.18 Cr, `units` 43,560. `growth_pct` is computed off `actual`.
Grabbing `value` when the caller asked for growth in litres is a one-character
mistake with a 250× error in it. Each row also carries a `source` naming the
table it came from (e.g. `amazon_sec_range_master_view`) — useful for
provenance.

### T15 — Litres everywhere, pieces where it says units; nothing here is in cartons or tonnes
`ltrs`, `total_ltrs`, `sec_ltr`, `inv_ltr`, `order_ltrs`, `deliver_ltrs`,
`ltr_sold`, `d7`/`d8_15`/`d15p` (the SPA renders these as "`{n}` L") — all
**litres**. `units`, `sec_qty`, `inv_qty`, `total_order_units`, `soh_unit` —
**pieces, i.e. single bottles** (correction C-0001; the "20 PCS" in an item name
is carton configuration and multiplying by it inflates volume ~20×). **No
endpoint in this domain returns tonnes.** To talk in tonnes, multiply litres by
0.91 for oils and say you did it — e.g. July 2026's 10,86,842.85 L ≈ **989 MT**,
and `fulfilment-health`'s 16,15,499.06 ordered litres ≈ **1,470 MT**. Both of
those conversions are mine, derived, not from the payload.

### T16 — The web dashboard can be showing inflated numbers; the API never is
`api-De44ElJm.js` implements a "business mode": when enabled, the browser walks
every API response and multiplies each numeric field by `1 + percent/100`
(default **30%**) for every platform except the one selected, skipping fields
whose name looks like an identifier (id, sku, asin, month, year, pct, rate,
price…). It is applied to `/api/dashboard/state-sales`,
`/api/dashboard/platform-expiry-alerts`, `/api/dashboard/category-*`,
`top-skus`, `fulfilment-health` and `secondary-yoy-growth`. It is off by default
and gated behind a feature flag, and **it does not touch the server** — the API
returns true numbers. But if an operator says "the dashboard shows X and your
CLI shows Y", check whether business mode is on before hunting for a bug.

### T17 — Two things named "penetration status" that are not the same
`penetration-report` rows carry `status` with four values and the SPA spells out
what each means: `live` = "Selling & in stock", `selling` = "Sales, no stock",
`stocked` = "Stock, no sales", `inactive` = "No movement". "Selling" therefore
means **selling but out of stock** — the alarming one, not the healthy one.
The `summary.universe_source` also changes the denominator of `covered_pct`:
`india` = all Indian cities/towns (Census 2011 reference), `uploaded` = the
official operating list in `platform_city_universe`, `mixed` = uploaded where
available else derived from all-time history, anything else = derived from that
platform's own sales/inventory history. **Coverage % is not comparable across
two calls with different `universe_source`.**

### T18 — Response sizes worth knowing before you fetch
`state-sales/export` 1,779 rows / **349 KB**; `penetration-report` 2,492 rows /
21 KB (and it takes `page` / `page_size`); `state-sales` 56 KB;
`table-data` returns whatever `page_size` you ask for (the SPA's own export
passes `page_size: 200000`). Default any command over these to a page, and make
the operator opt in to the full pull.

### T19 — `tables data` can return an error inside a 200
`PaginatedTable-C4rt_G6C.js` does `if (t.error) throw Error(t.error)` on the
`table-data` response — so a successful HTTP status can still carry an `error`
key instead of rows. Check for it.

---

## 4. Recommended spec entries

Response type is `object` for **every** endpoint below (from
`live_response.top_type`), except the two UNPROBED ones where it is unverified.
Shipped command names are reproduced exactly and must not be renamed.

Shared optional params, observed in the SPA request builders. Arrays are sent as
**repeated query params** (`Ce()` in `api-De44ElJm.js` appends one entry per
element); `null` and `""` are dropped entirely.

| param | type | observed values |
|---|---|---|
| `platform` | string | `blinkit`, `zepto`, `jiomart`, `amazon`, `bigbasket`, `swiggy`, `flipkart`, `flipkart_grocery`, `zomato`, `citymall`, `amazon_mp`. Omit = all platforms. |
| `month` / `year` | int | e.g. `8` / `2026` |
| `source` | string | `primary`, `secondary` (server also answers `mixed` when no platform is given) |
| `item_head` | string | `PREMIUM`, `COMMODITY`, `OTHER`; the SPA sends `""` for "all" |

**Category and SKU mix**

1. `dashboard category-breakdown` — Premium vs commodity litres for a month, by category and sub-category. Params: `month` int, `year` int, `source` enum, `platform` enum. → object
2. `dashboard category-litres` — Litres by category for one head only. Params: `head` string (observed `premium`; `commodity` inferred from the sibling endpoint's shape, not observed), `month`, `year`, `platform`. → object
3. `dashboard category-trend` — Monthly premium/commodity litre series. Params: `month`, `year`, `months` int (SPA sends `6`), `source`, `platform`. → object
4. `dashboard category-platform-breakdown` — One category split across platforms. Params: **`name` string (required)**, `head` string, `dimension` string (observed `category`, `sub_category`), `month`, `year`, `source`. No example `name` value is given here on purpose — read one from `category-breakdown` first. → shape unverified (400 at probe)
5. `dashboard category-sku-breakdown` — SKUs inside one category, per platform, over N months. Params: **`name` string (required)**, `head`, `dimension`, `platform`, `months` int (SPA sends `3`), `month`, `year`, `source`. → shape unverified (400 at probe)
6. `dashboard top-skus` — Top SKUs by litres with month-on-month movement. Params: `month`, `year`, `limit` int (SPA sends `10`, and `1000` for the YoY view), `source`, `compare_months` int (SPA sends `1`), `platform`. → object

**Geography**

7. `dashboard state-sales` — State and city sales map with platform split. Params: `metric` enum `litres|units|value`, `month`, `year`, or `months` int[] + `year`, or `from_month`/`from_year`/`to_month`/`to_year` for a range; `platform`, `brand` string[], `category` string[], `sub_category` string[], `item` string[], `item_head` enum. → object
8. `dashboard state-sales-export` — Flat state × city × SKU × platform rows. Same params as `state-sales`. Large: filter first. → object
9. `dashboard state-sales-detail` — Drill-down inside one state. Params: **`state` string (required)**; others not observed. → shape unverified (400 at probe)
10. `dashboard state-sales-detail-cities` — Cities (or items) inside one state. Params: **`state` string** plus the `state-sales` filter set. Returns 200 with zero rows if `state` is omitted. → object
11. `dashboard state-sales-detail-city-skus` — Top SKUs inside one city. Params: **`state` string, `city` string**, `limit` int (SPA sends `10`), plus the `state-sales` filter set. Returns 200 with zero rows if either is omitted. → object
12. `dashboard state-sales-detail-options` — SKU and city pick-lists for the drill-down. Params: not observed; likely `state`. → object

**Realisation (finance-sensitive — see traps T6, T6b)**

13. `dashboard realise-overview` — Delivered value, litres, commission, ads spend and brand fund for a month vs the one before. Params: `platform`, `month`, `year`, `item_head` enum, `category` string. → object
14. `dashboard realise-breakdown` — The same measures per category or sub-category. Params: `platform`, `month`, `year`, `item_head`, `group_by` enum `category|sub_category`, `category` string (when grouping by sub-category). → object
15. `dashboard realise-trend` — 12-month series of the same measures. Params: as `realise-overview` plus `months` int (SPA sends `12`). → object
16. `dashboard realise-waterfall` — Per-litre bridge from gross rate to net realise. Params: not observed (the SPA defines the call but no page uses it); `platform`, `month`, `year` are echoed in the response so they are accepted. → object

**Supply and fulfilment**

17. `dashboard fulfilment-health` — Fill rate and missed litres over a 30-day window ending 7 days back. Params: `platform`. → object
18. `dashboard lead-time-report` — Distributor lead-time litres in 7 / 8–15 / 15+ day slabs, by vendor and by platform. Params: `platform` **CSV string** (not repeated params — this endpoint alone takes `a,b,c`), `month` CSV string, `year` string, `item_head` enum with `""` for all. → object
19. `dashboard primary-po-litres` — Delivered litres per platform for the current month. Params: none observed; the response echoes `month` and `year`. **Check `errors[]`.** → object
20. `dashboard platform-expiry-alerts` — POs expiring in 1–5 days per platform, plus month pendency. Params: none (the SPA calls it bare). → object
21. `dashboard expiry-alerts-pos` — The individual expiring POs for one platform. Path param: `platform` enum. → object
22. `dashboard expiry-alerts-po-items` — Line items of one expiring PO. Path params: `platform` enum, `po` string (PO number, URL-encoded by the SPA). → unverified (never probed; no PO number was on hand)
23. `dashboard expiry-alerts` — Data-freshness alerts for one **upload table**. Path param: `table` — same enum as the table browser below. → object

**Distribution and stock**

24. `dashboard inventory-charts` — Current stock on hand by platform, city and product. Params: none. No period, no as-of date. → object
25. `dashboard penetration-report` *(new command)* — City × item × platform coverage with a live/selling/stocked/inactive status. Params: `month`, `year`, `page` int, `page_size` int, `platform` string[], `item_head` string[], `category` string[], `sub_category` string[], `status` enum `live|selling|stocked|inactive`, `search` string, `group_by` enum `city|sku`, `sort` string, `dir` enum `asc|desc`, `city` string, `item` string, `nocache` int. → object
26. `dashboard penetration-report-options` *(new command)* — Pick-lists for the penetration report. Params: none. → object

**Table browser**

The `{table}` enum below is the **observed** set: the 44 integer-valued keys of
the live `/api/dashboard/table-counts` response. This is the only safe source
for these values.

```
all_platform_inventory        amazon_ads                    amazon_coupon
amazon_inventory              amazon_mp                     amazon_price_data
amazon_sec_city               amazon_sec_daily              amazon_sec_daily_master_view
amazon_sec_range              amazon_sec_range_margins      amazon_sec_range_master_view
bigbasketSec                  bigbasket_ads                 bigbasket_inventory
bigbasket_sec_range           blinkitSec                    blinkit_ads
blinkit_brandfund             blinkit_inventory             citymallSec
citymall_inventory            fk_grocery                    flipkartSec
flipkart_ads                  flipkart_grocery_master       flipkart_secondary_all
jiomartSec                    jiomart_inventory             master_po
prim_master_po                swiggySec                     swiggy_ads
swiggy_brandfund              swiggy_inventory              test_master_po
total_po                      total_po_zbs                  zeptoSec
zepto_ads                     zepto_brandfund               zepto_inventory
zomatoSec                     zomato_inventory
```

Note the names are case-sensitive and inconsistent (`blinkitSec` camelCase vs
`bigbasket_sec_range` snake_case) — pass them through verbatim. Seven were empty
at probe time (`citymallSec`, `citymall_inventory`, `fk_grocery`,
`prim_master_po`, `test_master_po`, `zomatoSec`, `zomato_inventory` — all 0
rows); `test_master_po` is self-evidently scratch. The three biggest are
`swiggySec` 6,50,791 rows, `all_platform_inventory` 2,35,635 and `blinkitSec`
1,42,527.

27. `tables counts` — Row counts for all 44 tables. Params: `tables` **CSV string** (optional filter; the SPA joins its list with commas). → object
28. `tables count` — Row count for one table. Path param: `table` enum. → object
29. `tables columns` — Column names plus one real sample row. Path param: `table` enum. → object
30. `tables data` — Paged raw rows. Path param: `table` enum. Query params: `page` int (0-based), `page_size` int, `search` string, `search_columns` CSV string, `date_column` string, `sort_by` string, `sort_dir` enum `asc|desc`, `max_date` int (`1` = only rows on the table's latest date), `year`, `month`, `date`, `column_filters` **JSON string** of `[{"column": "...", "values": ["..."]}]`. → object
31. `tables distinct` — Distinct values in one column. Path params: `table` enum, `column` string (take it from `tables columns`). Query param: `search` string. → unverified (never probed; no column value was on hand)

**Housekeeping**

32. `dashboard latest-month` — Which month the dashboard treats as current. Params: none. → object

---

## 5. Exclusions

| endpoint | reason |
|---|---|
| `POST /api/dashboard/table-row/{table}` (`updateTableRow`) | **Write endpoint.** The SPA only ever POSTs it, it is new since v0.1.0, and it edits a single row in a production upload table. RULE 0 — ecom is read-only. Never probed and must never be published. |
| `POST /api/dashboard/table-rows/{table}` (`updateTableRows`) | **Write endpoint**, bulk version of the above. Same reasoning, higher blast radius. Never probed, never published. |

Nothing else in this bundle is excluded. In particular:

* `dashboard expiry-alerts-po-items` and `tables distinct` are **UNPROBED but
  published** — both are GETs shipped in v0.1.0 that could not be probed only
  because no PO number and no column value were on hand at harvest time
  (`probe/probe-params-audit.json` records both as "no observed value for its
  parameter"). Per the brief, carry them forward; do not infer they are dead.
* `dashboard expiry-alerts` returned `{"alerts": []}` and is **published** — the
  empty result is a bad probe value (a platform slug where a table name was
  required, T9), not a dead endpoint.
* `state-sales/detail/cities`, `.../city-skus` and `.../options` returned zero
  rows and are **published** — they were called without a state (T4).
* `dashboard state-sales-detail` and `dashboard state-sales-detail-options` are
  **published** despite no page in the SPA calling them (T5); both are routed
  and answering.
* No endpoint in this domain was `BROKEN_UPSTREAM`, `DEAD` or `GATED`.
