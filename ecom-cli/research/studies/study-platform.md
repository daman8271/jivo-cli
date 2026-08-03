# Domain study — `platform` (61 endpoints)

Evidence: `study/bundles/platform.json` (61 endpoints), cross-read against the raw
probe logs (`probe/probe-run1.jsonl`, `probe-params.jsonl`, `probe-matched.jsonl`),
the SPA bundle (`bundle/*.js`) and the shipped spec (`ecom-cli/spec.yaml` v0.1.0).
No HTTP request was made by me.

Status counts as given: **LIVE 42 · LIVE_NEEDS_PARAMS 3 · LIVE_PARTIAL 1 ·
UNPROBED 14 · DEAD 1**. Recommendation: **publish 46, exclude 15**.

---

## 1. What this domain is, in operator language

This is the **per-platform trading desk**. Every marketplace and quick-commerce
account JIVO sells through — Amazon, Blinkit, Zepto, Swiggy Instamart, BigBasket,
Flipkart, Flipkart Grocery, Zomato, CityMall — gets the same set of screens here,
and this domain is the data behind them. It answers four questions per platform:
*what did we ship them* (primary / POs), *what did they sell to shoppers*
(secondary), *what stock is sitting in their warehouses and how many days will it
last* (SOH/DOH), and *what did we spend on ads and brand fund and what came back*
(ROAS/ACOS/brand fund).

Who opens it: the **e-commerce / key-account team** running each platform day to
day, and **Accounts** when they need the sell-in number behind a platform's
invoices, the open-PO exposure, or the ad spend for a month.

The two cross-platform roll-ups (`primary-summary`, `ads-summary`) are the ones a
manager wants; everything with a slug in the path is one account's detail.

---

## 2. Endpoint table

`{}` in a path is the **platform slug**. `platforms` says which slugs the server
actually accepts — this is the single biggest source of "the command is broken"
reports, so read it before the description.

**Slug values attested by live data this run** (not guessed): `amazon`,
`bigbasket`, `blinkit`, `citymall`, `flipkart`, `flipkart_grocery`, `swiggy`,
`zepto`, `zomato` — all nine appear as keys of `by_platform` in the live 200 from
`/api/platform/primary-overview-total`. `jiomart` is in the shipped enum but is
marked `hidden: true` in the SPA's own platform registry and does **not** appear
in that live payload — see Trap 12. `amazon_mp` exists as a secondary-only
pseudo-slug in the SPA but was never probed.

### 2a. Cross-platform (no slug in the path)

| command | path | what an operator gets | required params | platforms | status |
|---|---|---|---|---|---|
| `platform ads-summary` | `/api/platform/ads-summary` | One ad P&L across every platform. `totals` = `qty_sold`, `impressions`, `ad_spent`, `brand_fund`, `sec_qty`, `sec_value`, `ads_sale`. `breakdowns` splits the same seven figures by `item_head` / `category` / `sub_category` / `item` / `platform`; `platform_item_head` crosses platform × item head. Live sample: ad spend ₹2.02 Cr, brand fund ₹51.0 L, ads sale ₹21.35 Cr against total secondary sale ₹116.43 Cr. | none | all | LIVE |
| `platform meta` | `/api/platform/meta` | **Meta (Facebook/Instagram) ad campaigns — not platform metadata.** `summary` = `reach`, `impressions`, `link_clicks`, `amount_spent`, `cpc`, `cpr`, `cpm`, `ctr`, `campaigns`; `rows` are campaigns (`campaign_name`, `campaign_status`). Live sample: 83 campaigns, ₹12.38 L spent, 23.4 Cr impressions. See Trap 1. | none | n/a | LIVE |
| `platform primary-summary` | `/api/platform/primary-summary` | Sell-in (PO) roll-up across platforms for one month. `summary` by `item_head`, `summary_total`, `details` down to category/sub-category/`per_ltr`, `top_items`, `open_vendor_pending` (per-vendor order vs delivered vs pending + `lead_time_avg`), `by_platform`. Every row carries `done_*`, `order_*`, `pending_*`, `expired_*`, `cancelled_*`, `missed_ltrs`, `projection_*`. | none (defaults to latest; `defaulted_to_latest: true` tells you it did) | all | LIVE |
| `platform primary-overview-total` | `/api/platform/primary-overview-total` | The one-screen sell-in headline: `done_ltrs` / `done_value`, split by `item_heads` (PREMIUM / COMMODITY / OTHER), plus `open_po_total` (`pending_value`, `pending_ltrs`, `pending_qty`, `open_pos`) and the same block per platform. Live sample: 7,926.8 L delivered (≈7.2 t) worth ₹18.02 L, and 347 open POs worth ₹7.64 Cr / 3,85,116 L (≈350 t). | none | all | LIVE |
| `platform primary-summary-version` | `/api/platform/primary-summary-version` | `{"version": "406262"}` — an opaque change token the UI polls to know the primary data was refreshed. | none | all | LIVE |
| `platform secondary-summary-version` *(new)* | `/api/platform/secondary-summary-version` | `{"version": "507467010"}` — same idea for secondary. Different numbering scheme from the primary one; see Trap 14. | none | all | LIVE |
| `platform call-center-targets` | `/api/platform/call-center-targets` | Call-centre channel targets for a month. Shape not observed (the probe got the 400 before any body). | **`month` (1-12) and `year` (YYYY)** — verbatim from the server: `` `month` (1-12) and `year` (YYYY) are required integers. `` | all | LIVE_NEEDS_PARAMS |
| `platform month-targets-dashboard` | `/api/platform/month-targets/dashboard` | **Secondary** monthly targets vs achievement for every platform on one page. Shape not observed. | **`month`, `year`** — verbatim: `` `month` (1–12) and `year` (YYYY) are required. `` | all | LIVE_NEEDS_PARAMS |
| `platform primary-month-targets-dashboard` | `/api/platform/primary-month-targets/dashboard` | **Primary** monthly targets vs achievement for every platform. Shape not observed. | **`month`, `year`** — verbatim: `` `month` (1-12) and `year` (YYYY) are required. `` | all | LIVE_NEEDS_PARAMS |
| `platform bigbasket-sales-explorer` *(new)* | `/api/platform/bigbasket/sales-explorer` | Day-by-day BigBasket sell-out. `daily` rows (`date`, `value`, `ltr`, `qty`) plus item rows (`item_head`, `item`, `category`, `sub_category`, `sku_count`, `qty`, `ltr`, `value`, `avg_*`) and `totals`. **BigBasket is hard-coded into the path** — there is no slug parameter. | none (defaults to a 2-day window; `defaulted_range: true` flags it) | bigbasket only, by path | LIVE |

Observed optional filters for the cross-platform ones (taken from the SPA and from
the `filters` block the server echoes back):
`ads-summary` → `month`, `year`, `date`, `from_date`, `to_date`, `platform` (the
response's own `filters` object names exactly these six).
`meta` → `year`, `month`.
`primary-summary` → `mode` (`DEL MONTH` | `PO MONTH`), `month`, `year`, `slugs`
(comma-joined).
`bigbasket-sales-explorer` → `from_date`, `to_date`, `sales_of` (comma-joined;
observed members `PREMIUM`, `COMMODITY`, `OTHER` from `sales_of_options`).

### 2b. Per-platform, available on every slug

| command | path | what an operator gets | params | platforms | status |
|---|---|---|---|---|---|
| `platform primary` | `/api/platform/{}/primary-dashboard` | Sell-in for one platform: `summary` per item head with `done_*`, `pending_*`, `dp_*`, `expired_*`, `cancelled_*`, `order_*`, `projection_*`, `missed_ltrs`, `remaining_ltrs`; plus detail rows. Source names itself, e.g. `reporting."Amazon PO"`. | `mode` (`DEL MONTH` \| `PO MONTH`, default `DEL MONTH`), `month`, `year`, `channel` (**amazon only**: `ALL` \| `CORE` \| `FRESH` \| `NOW`) | SPA wires all 9 slugs | LIVE |
| `platform secondary` | `/api/platform/{}/sec-dashboard` | Sell-out for one platform: `category_summary` rows with `order_value/ltr/units`, `shipped_value/ltr/units`, `return_value/ltr/units`, `margin_pct`, `margin_value`, `margin_tax_value`, `per_liter_shpd`, `net_realise_shpd`, `projection_ltr`; plus `elapsed_day`, `days_in_month`, `cutoff_month_day`. Largest payload in the domain (163 KB on amazon). | `month` + `year`, **or** `date` (`YYYY-MM-DD`) for a single day | amazon, blinkit, zepto, swiggy, bigbasket, flipkart, flipkart_grocery (SPA set); `amazon_mp` also used by the summary page — **unverified** | LIVE |
| `platform secondary-years` | `/api/platform/{}/sec-dashboard-years` | `{"years": [2026, 2025, 2024], "errors": []}` — which years have secondary data. Check `errors` before trusting `years`. | none | as above | LIVE |
| `platform secondary-monthly` | `/api/platform/{}/sec-monthly-dashboard` | Month-by-month secondary for a year: a `months` calendar (with each month's cut-off day, e.g. `29-JULY` for the current one), `category_values`, `mom_growth`, `notes.messages`. `month_strategy: "excel_month_end"`. | `month`, `year` | SPA renders it only for **amazon** and **flipkart**; other slugs unverified | LIVE |
| `platform drr` | `/api/platform/{}/drr-dashboard` | Daily run-rate: `daily` array (`date`, `ops`, `units`, `ltr`) plus SKU/category roll-ups with `drr_*` and `projection_ltr`, `elapsed_days` vs `days_in_month`. Biggest per-slug payload (191 KB). Echoes `item_head_options` = `ALL/PREMIUM/COMMODITY/OTHER` and `sales_mode_options` = `ORDERED/SHIPPED`. | **amazon/amazon_mp:** `month`, `year`, `item_head`, `sales_mode`, `from_date`, `to_date` (+`source=mp` for amazon_mp). **Others:** `month`, `sales_of`. | drr set = amazon, amazon_mp, blinkit, zepto, swiggy, bigbasket, flipkart, flipkart_grocery | LIVE |
| `platform soh-doh` | `/api/platform/{}/soh-doh-dashboard` | Stock on hand and days on hand at the platform's warehouses, plus `available_dates` (each with a row count) so you can see which snapshot dates exist. Sources both a sales view and an inventory table, named in `source`. | **amazon:** `month`, `year`, `date`. **Others:** `date` only. | SPA set = amazon, blinkit, zepto, swiggy, bigbasket | LIVE |
| `platform pos` | `/api/platform/{}/pos` | Paged PO list: `{data, count, page, page_size}`. Returned `count: 0` for amazon in this run — see Trap 8. | `page`, `page_size` (defaults 0 / 50) | not restricted by the server; **no SPA screen calls it** | LIVE |
| `platform inventory-match` | `/api/platform/{}/inventory-match` | `{"match": …, "inventory_available": true}` — resolves one SKU against the platform's inventory. Called with no SKU it returns `match: null`. | **`sku`** (the SPA always sends it; without it the answer is meaningless, not empty) | not restricted; **no SPA screen calls it** | LIVE |
| `platform stats` | `/api/platform/{}/stats` | `{"inventory": 103, "sells": 0, "openPOs": 0, "activeTrucks": 0}` — the four tiles at the top of a platform's home page. Only `inventory` was populated on amazon; see Trap 9. | none | all | LIVE |
| `platform month-targets` | `/api/platform/{}/month-targets` | **Secondary** monthly targets for one platform. Rows: `id`, `format`, `type` (`B2C`), `item_head`, `month`, `year`, `targets`, `done_ltrs`, `done_value`, `achieved_pct`, `est_ltr`, `est_value`, `est_ltr_pct`, `last_month`, `growth`, `growth_pct`. | `month`, `year` | all | LIVE |
| `platform primary-month-targets` | `/api/platform/{}/primary-month-targets` | **Primary** monthly targets for one platform. Envelope `{data, format, type: "prim", source: "master_po"}`. Returned `data: []` for amazon — see Trap 8. | `month`, `year` | all | LIVE |
| `platform pendency` | `/api/platform/{}/pendency-dashboard` | Open / pending PO exposure for a platform, broken out `by_city` (`pending_units`, `pending_ltrs`, `open_units`, `open_ltrs`, `order_value`, `open_pos`), plus `totals`, `po_month`, `min/max_po_date`. | `scope=all` (default) **or** `from_date`+`to_date`; `status=expired` to switch from pending to expired POs | 200 on blinkit, zepto. **Amazon is refused** — server: `Pendency dashboard is not yet enabled for platform 'amazon'.` SPA set = zepto, swiggy, blinkit, bigbasket, flipkart_grocery, citymall, zomato | LIVE |
| `platform marketplace` | `/api/platform/{}/mp-dashboard` | Amazon **Marketplace (3P)** sales, separate from vendor/1P. `kpi` gives `inclusive` and `exclusive` (of GST) side by side, plus `ltrs` and `quantity`; then splits by `item_head` and `sub_category`. `available: true/false` says whether MP data exists at all. | `month`, `year` | **The SPA always calls it with `amazon`** regardless of the slug in the URL. Other slugs unverified | LIVE |
| `platform mp-dashboard-version` | `/api/platform/{}/mp-dashboard-version` | `{"version": "2026-08-03T11:25:54.544627+00:00"}` — MP refresh token. Note this one is a timestamp while the other two version endpoints are integers. | none | amazon (as above) | LIVE |
| `platform price` | `/api/platform/{}/price-dashboard` | Amazon price-tracking: per-ASIN `mrp`, `asp`, `margin_pct`, `tax_pct`, `cost_without_tax`, `url_price`, `stock_status`, `seller`, and competitor columns `rk_price` / `jm_price` / `svd_price` / `bau_price` / `art_price`. `summary` counts `in_stock`, `out_of_stock`, `missing_url_price`. | `date` (`YYYY-MM-DD`); `upload_dates` lists the snapshots that exist | SPA enables it **only for amazon** | LIVE |
| `platform coupon` | `/api/platform/{}/coupon-dashboard` | Amazon coupon/promo spend for one snapshot date, with `available_dates` (date + row count). | `date` | SPA enables it **only for amazon** | LIVE |
| `platform comparison` | `/api/platform/{}/comparison-dashboard` | Best-month vs current-month per sub-category: `highest` and `current` blocks each with `shipped_ltr`, `shipped_rev`, `rev_after_margin`, `price_per_ltr`, `net_realise`. Answers "which month was our peak and how far below it are we". | `month`, `year` (the SPA sends `year` twice, as `year` **and** `history_year`) | SPA enables it **only for amazon** | LIVE |
| `platform ads` | `/api/platform/{}/ads-dashboard` | Amazon ads (AMS): `summary` with `total_cost`, `sales`, `roas`, `acos`, `impressions`, `clicks`, `ctr`, `cpc`, `purchases`, `units_sold`, `ntb_orders`, `ntb_sales`, `detail_page_views`, `total_sales`; dimension is `portfolio_name`. Source `amazon_ads_master`. | `year`, `month`, `from_date`, `to_date`, `dimension`, `metric` (`ordered` \| `shipped`, amazon only), `date_wise=1`, `month_wise=1` | probed 200 on amazon; SPA only ever calls it with **amazon** | LIVE |
| `platform ads-total-sales` | `/api/platform/{}/ads-total-sales` | The "total sales" denominator behind ads ROAS: `summary_total.shipped_value` plus per-ASIN `sku_details` (`item_head`, `category`, `sub_category`, `per_ltr`, `item`, `asin`, `shipped_value`). | `month`, `year`, `metric`, `date_wise`, `month_wise`, `as_of_date`, `from_date`, `to_date` | probed 200 on amazon | LIVE |

### 2c. Per-platform, but the server restricts which platform

The 400 body is quoted verbatim; that is the server naming its own rule.

| command | path | what an operator gets | platforms — server's own words | status |
|---|---|---|---|---|
| `platform blinkit-ads-dashboard` | `/api/platform/{}/blinkit-ads-dashboard` | Blinkit ads: `ad_spent`, `ads_sale`, `total_sale_basic_rate`, `roas`, `acos`, `impressions`, `direct_qty_sold`, `indirect_qty_sold`, `ads_ltr_sold`, item-wise. Source `blinkit_ads_master`. | `Blinkit Ads Dashboard is available only for Blinkit.` → **blinkit** | LIVE |
| `platform blinkit-brandfund-dashboard` | `/api/platform/{}/blinkit-brandfund-dashboard` | Blinkit brand-fund accruals: `total_brand_fund` (₹45.85 L in the sample) split by item, sub-category, month, and a daily trend. Source `blinkit_brandfund_master`. | `Blinkit Brand Fund Dashboard is available only for Blinkit.` → **blinkit** | LIVE |
| `platform blinkit-summary-report` *(new)* | `/api/platform/{}/blinkit-summary-report` | The Blinkit one-pager by month: `premium_ltr`, `commodity_ltr`, `total_ltr`, `total_qty`, `brand_fund`, `ads_spend`, `ads_sales_sp`, `ads_qty`, `impressions`, `mrp_sale`, `basic_sale`, `paid_pct`, `organic_pct`, `roas`, `tcos_pct`. The only endpoint that gives paid-vs-organic split. | `Summary monthly report is available only for Blinkit.` → **blinkit** | LIVE |
| `platform zepto-ads-dashboard` | `/api/platform/{}/zepto-ads-dashboard` | Zepto ads, same metric set as Blinkit. Source `zepto_ads_master`. | `Zepto Ads Dashboard is available only for Zepto.` → **zepto** | LIVE |
| `platform zepto-ads-daily-dashboard` | `/api/platform/{}/zepto-ads-daily-dashboard` | Zepto ads **day-by-day** (the trend companion to the above). Source `zeptoads_daily_master`. | `Zepto Daily Ads Dashboard is available only for Zepto.` → **zepto** | LIVE |
| `platform zepto-brandfund-dashboard` | `/api/platform/{}/zepto-brandfund-dashboard` | Zepto brand fund by item / sub-category / month (₹4.98 L in the sample). Source `zepto_brandfund_master`. | `Zepto Brand Fund Dashboard is available only for Zepto.` → **zepto** | LIVE |
| `platform swiggy-ads-dashboard` | `/api/platform/{}/swiggy-ads-dashboard` | Swiggy Instamart ads. Source `swiggy_ads_master`. Note: no `indirect_qty_sold` on Swiggy. | `Swiggy Ads Dashboard is available only for Swiggy.` → **swiggy** | LIVE |
| `platform swiggy-ads-daily-dashboard` | `/api/platform/{}/swiggy-ads-daily-dashboard` | Swiggy ads day-by-day. Source `swiggyads_daily_master`. | `Swiggy Daily Ads Dashboard is available only for Swiggy.` → **swiggy** | LIVE |
| `platform swiggy-brandfund-dashboard` | `/api/platform/{}/swiggy-brandfund-dashboard` | Swiggy brand fund. Sample total ₹1,178 and every row `(Unmapped)` — see Trap 11. Source `swiggy_brandfund_master`. | `Swiggy Brand Fund Dashboard is available only for Swiggy.` → **swiggy** | LIVE |
| `platform bigbasket-ads-dashboard` | `/api/platform/{}/bigbasket-ads-dashboard` | BigBasket ads. Source `bigbasket_ads_master`. | `BigBasket Ads Dashboard is available only for BigBasket.` → **bigbasket** | LIVE |
| `platform bigbasket-ads-daily-dashboard` | `/api/platform/{}/bigbasket-ads-daily-dashboard` | BigBasket ads day-by-day. Source `bigbasketads_daily_master`. Returned all-zero `summary` in this run — see Trap 10. | `BigBasket Daily Ads Dashboard is available only for BigBasket.` → **bigbasket** | LIVE |
| `platform flipkart-ads-dashboard` | `/api/platform/{}/flipkart-ads-dashboard` | Flipkart ads, **dimension is `campaign_name`** not item. Metrics are named differently: `ad_spend`/`revenue`/`roi`/`views` (not `ad_spent`/`ads_sale`/`roas`/`impressions`). Also gives `campaign_budget` and `cvr`. Source `flipkart_ads_master`. | `Flipkart Ads Dashboard is available only for Flipkart.` → **flipkart** | LIVE |
| `platform flipkart-fsn-dashboard` | `/api/platform/{}/flipkart-fsn-dashboard` | Flipkart FSN-level ads with a selectable dimension (`item`, `sub_category`, `category`, `item_head`, `campaign_name`). Adds `direct_units`. Source `consolidated_fsn_report`. | `Flipkart FSN Dashboard is available only for Flipkart.` → **flipkart** | LIVE |
| `platform landing-rate` | `/api/platform/{}/landing-rate` | The monthly landing rate JIVO bills each quick-commerce account at, per SKU: `sku_code`, `sku_name`, `landing_rate`, `basic_rate`, `format`, `month`, `created_at`, `carried_over`. | `Monthly landing rate is only available for blinkit, zepto, swiggy, bigbasket, flipkart_grocery.` (200 confirmed on blinkit + zepto) | LIVE |
| `platform landing-rate-skus` | `/api/platform/{}/landing-rate/skus` | The SKU picker behind the above: `sku_code`, `sku_name`, `has_rate` — i.e. **which SKUs are still missing a landing rate this month**. | same message as `landing-rate` (200 confirmed on blinkit) | LIVE |
| `platform monthly-sales-explorer` *(new)* | `/api/platform/{}/monthly-sales-explorer` | Multi-month sell-out comparison: pick months, get `qty` / `ltr` / `value` per item plus `growth_ltr` / `growth_qty` / `growth_value` %, `selling_days`, and `months_options` listing every month with data (Dec 2024 onward on BigBasket). | `Monthly Sales Explorer is available for bigbasket, blinkit, swiggy, zepto only.` (200 confirmed on bigbasket + blinkit) | LIVE |
| `platform region-doh` | `/api/platform/{}/region-doh-dashboard` | City-level stock cover: `city`, `soh_units`, `soh_ltr`, `units_sold`, `ltr_sold`, `drr_units`, `drr_ltr`, `doh`. The command that answers "which city is about to go out of stock". | **swiggy and zepto only.** 200 on those two; a bare Django 404 page on amazon, bigbasket, blinkit, flipkart_grocery, zomato. See Trap 3. | LIVE_PARTIAL |

Params for the restricted set: the ten `*-ads-dashboard` / `*-ads-daily-dashboard`
/ `*-fsn-dashboard` endpoints all share one UI shell, so they all take
`year`, `month`, `from_date`, `to_date` (+ `dimension` where a dimension picker
exists, + `date_wise=1` / `month_wise=1` toggles).
The three `*-brandfund-dashboard` endpoints take `year`, `month`, `date`.
`blinkit-summary-report` takes `year`.
`landing-rate` takes `mode` (`effective` | `history`), `month` **as `YYYY-MM-01`**,
`search`, `page`, `page_size`; `landing-rate/skus` takes `month` (same format).
`monthly-sales-explorer` takes `months` and `sales_of`, both **comma-joined**.
`region-doh` takes `date` only.

---

## 3. Traps

### Trap 1 — `platform meta` is the Facebook/Instagram ads dashboard, not platform metadata *(observed)*

The shipped v0.1.0 description reads "Platform metadata (slugs, labels, config)".
That is wrong. The live 200 body is:

```
{"summary": {"reach": 182936992.0, "impressions": 234206471.0, "link_clicks": 2159077.0,
             "amount_spent": 1238251.57, "cpc": 0.57, "cpr": 6.77, "cpm": 5.29,
             "ctr": 0.92, "campaigns": 83},
 "rows": [{"campaign_name": "Amazon- Yellow Mustard", "campaign_status": "not_delivering", …}],
 "filter_options": {"years": […], "months": […]}}
```

The SPA chunk that calls it is `MetaDashboard-BDuhtHQG.js`, titled "Meta Ads", and
the SPA's own registry lists `meta` as a platform with `tables: {ads: "meta_data"}`.
Keep the command name `platform meta` (public contract) but **the description must
change**, or an operator asking "what platforms exist" gets ₹12.38 L of Facebook
spend. There is no endpoint in this domain that returns the slug list; the closest
is `by_platform` inside `primary-overview-total`.

### Trap 2 — the platform restriction is a **400, and it reads like a broken command** *(observed)*

Eighteen endpoints are refused for the wrong slug with HTTP 400 and a plain
English sentence, e.g. `["Blinkit Ads Dashboard is available only for Blinkit."]`.
A CLI that surfaces "HTTP 400" without the body makes this look like a bug in the
command. **The body must be printed.** The restriction lists are in the table
above, all taken verbatim from the probe log — none of them are inferred.

Note the two shapes of restriction:
- *fixed list* — `landing-rate` ("only available for blinkit, zepto, swiggy,
  bigbasket, flipkart_grocery"), `monthly-sales-explorer` ("for bigbasket,
  blinkit, swiggy, zepto only"), and the eleven single-platform ones.
- *per-platform enablement* — `pendency-dashboard` says "not yet **enabled** for
  platform 'amazon'", which is a config flag, not a hard list. Do not hard-code a
  pendency platform list; it can change without a deploy.

### Trap 3 — `region-doh` 404s on most slugs, and that 404 is **not** "endpoint dead" *(observed, with a caveat)*

`region-doh-dashboard` returned 200 on `swiggy` and `zepto`, and a bare Django
"Not Found" HTML page on `amazon`, `bigbasket`, `blinkit`, `flipkart_grocery`,
`zomato`. The endpoint is alive — two slugs prove it.

**Caveat I have to state:** the 404 body for region-doh is byte-for-byte the same
generic Django page as the one from a genuinely unrouted path. I cannot tell a
view-raised 404 from a routing 404 by reading the body. The only thing that
separates them here is that region-doh returned 200 for two slugs and
`month-on-month-sale` returned 404 for all seven. Confidence that region-doh is
alive: high (a 200 is a 200). Confidence about *why* the others 404: moderate — I
did not see the server code.

Practical consequence: an operator running `platform region-doh blinkit` gets a
404 and will read it as "no stock data for Blinkit". The right answer is "this
dashboard doesn't exist for Blinkit — use `platform soh-doh blinkit` instead".
The CLI should say that, not pass the 404 through.

### Trap 4 — primary vs secondary: getting these backwards gives a completely wrong sales number *(observed)*

At JIVO, **primary = JIVO → platform (sell-in, the PO)** and **secondary =
platform → consumer (sell-out)**. The payloads confirm it, and they are not
interchangeable:

| | primary | secondary |
|---|---|---|
| commands | `platform primary`, `platform primary-summary`, `platform primary-overview-total`, `platform primary-month-targets`, `platform primary-month-targets-dashboard`, `platform primary-summary-version` | `platform secondary`, `platform secondary-monthly`, `platform secondary-years`, `platform month-targets`, `platform month-targets-dashboard`, `platform secondary-summary-version`, the sales explorers |
| `source` in the live payload | `reporting."Amazon PO"`, `primary_summary`, `master_po` | `amazon_sec_range_master_view`, `SecMaster`, `blinkitSec` / `zeptoSec` / … |
| the money field | `done_value` (delivered), `order_value` (ordered), `pending_value` (open PO) | `shipped_value`, `order_value`, `return_value` |
| exists only here | `open_pos`, `expired_*`, `cancelled_*`, `dp_*`, `missed_ltrs`, `lead_time_avg` | `return_*`, `margin_pct`, `net_realise_shpd`, `per_liter_shpd` |

Three name collisions that catch people:
- **`month-targets` is the SECONDARY target set** (rows carry `"type": "B2C"`),
  while `primary-month-targets` is primary (`"type": "prim"`,
  `"source": "master_po"`). The word "primary" is the only marker; the plain name
  is the secondary one.
- **`order_value` exists on both sides and means different things** — a PO value
  on primary, a consumer order value on secondary.
- `primary-summary` and `primary-overview-total` are both cross-platform sell-in
  but are not the same number: `primary-summary` is one month with detail;
  `primary-overview-total` is the headline plus `open_po_total` across all open
  POs regardless of month. In the same run: `primary-summary` August delivered
  ₹18.93 L against `primary-overview-total` delivered ₹18.02 L. They are close but
  they are **not** equal, so never quote one as a check on the other.

### Trap 5 — quantity fields are **pieces (single bottles), never cartons** *(observed, and the payload proves it)*

This is JIVO correction C-0001 and this domain confirms it directly. From the live
BigBasket sales-explorer rows:

| item | `qty` | `ltr` | litres per unit |
|---|---|---|---|
| CANOLA 1L | 317 | 317 | 1.00 |
| JIVO POMACE 1L | 148 | 148 | 1.00 |
| CANOLA 5L | 23 | 115 | 5.00 |

`qty` divided into `ltr` lands exactly on the pack size. If `qty` were cartons the
ratio would be 20× that. So every quantity field in this domain —
`qty`, `qty_sold`, `sec_qty`, `done_qty`, `order_qty`, `pending_qty`, `units`,
`units_sold`, `shipped_units`, `order_units`, `return_units`, `soh_units`,
`open_units`, `pending_units`, `direct_qty_sold`, `indirect_qty_sold`,
`ads_qty`, `total_qty`, `quantity` — **counts individual bottles/packs**.
The "20 PCS" in an item name is carton configuration; multiplying by it inflates
volume roughly 20×.

**For tonnes, do not convert from units.** Every one of these endpoints ships a
litre field alongside (`ltr`, `ltrs`, `done_ltrs`, `shipped_ltr`, `soh_ltr`,
`ltr_sold`, `pending_ltrs`, `ads_ltr_sold`, `total_ltr`, `premium_ltr`,
`commodity_ltr`). Use it: **tonnes = litres × 0.91 ÷ 1000** for oils. Example from
the live data: `primary-overview-total.open_po_total.pending_ltrs` = 3,85,115.8 L
→ ≈ 350 t of open PO.

Two litre-field gotchas: floats carry noise (`soh_ltr: 130.20000000298` — round
before presenting), and `flipkart_grocery` has an empty inventory table in the SPA
registry, so its litre-based stock figures may be blank rather than zero.

### Trap 6 — money: MRP sale, basic sale and net realisation differ by 2-3× *(observed)*

There is no single "sales" number in this domain. From the live Blinkit summary
report, January 2026:

- `mrp_sale` ₹4,10,17,988 (₹4.10 Cr)
- `basic_sale` ₹1,57,23,602 (₹1.57 Cr)

**2.61× apart.** Quoting the wrong one overstates Blinkit by ₹2.5 Cr in one month.
The same split appears everywhere under different names:

| what you want | field |
|---|---|
| consumer-facing MRP | `mrp_sale`, `mrp`, `url_price` |
| platform selling price / ads revenue | `ads_sale`, `ads_sales_sp`, `revenue`, `sales` |
| JIVO's basic rate (pre-margin, pre-tax) | `basic_sale`, `total_sale_basic_rate`, `basic_rate`, `cost_without_tax` |
| what JIVO actually realises per litre | `net_realise_shpd`, `net_realise`, `rev_after_margin` |
| GST | only `mp-dashboard` gives both sides explicitly: `kpi.inclusive` ₹20,51,693 vs `kpi.exclusive` ₹19,53,993. Everywhere else you have to know which you're holding. |

Always say which one you quoted.

### Trap 7 — ROAS and ACOS in `summary` are **row averages on some platforms and total ratios on others** *(observed arithmetic; formula not confirmed)*

Every ads dashboard declares its own aggregation in `available_metrics`, and for
ROAS/ACOS it says `"agg": "avg"`. Checking the live summaries:

| platform | ad spend | sales | reported ROAS | reported ACOS | does spend/sales = ACOS? |
|---|---|---|---|---|---|
| amazon | 88,09,904 | 9,44,56,927 | 10.7217 | 9.3269 | **yes**, exactly 9.3269 % |
| blinkit | 78,94,931 | 9,49,92,252 | 12.0321 | 12.0777 | **no** (ratio is 8.31 %) |
| swiggy | 2,24,816 | 5,12,868 | 21.1992 | 4.7172 | **no** (ratio is 43.8 %) |
| zepto | 32,71,166 | 1,15,74,131 | 17.9055 | 5.5849 | **no** (ratio is 28.3 %) |

On swiggy and zepto, `acos` is exactly `100 / roas`. On blinkit neither identity
holds. On amazon it is the ratio of totals.

I could not determine the server-side formula from the sample, so: **do not
recompute or re-explain ROAS/ACOS — print the server's number and its label.** And
never sum ROAS or ACOS across rows; the endpoint tells you `agg: "avg"`. Confidence
that these are not comparable across platforms: high (the arithmetic above).
Confidence about the exact per-platform formula: low.

Also note Flipkart renames the same metrics — `ad_spend`/`revenue`/`roi`/`views`
instead of `ad_spent`/`ads_sale`/`roas`/`impressions`. A generic "sum the ads
spend across platforms" loop that keys on `ad_spent` silently drops Flipkart.

### Trap 8 — an empty result here can mean four different things *(observed)*

Four live 200s in this run came back empty, for four different reasons:

| call | body | what it actually means |
|---|---|---|
| `platform pos amazon` | `{"data": [], "count": 0, "page": 0, "page_size": 50}` | Unknown. This endpoint is called by **no screen in the SPA**, so nothing proves it is wired to real data. Do not report "Amazon has no POs" from this. |
| `platform primary-month-targets amazon` | `{"data": [], "format": "AMAZON", "type": "prim", "source": "master_po"}` | No primary target has been **entered** for Amazon. It is a data-entry gap, not zero sales — `platform month-targets amazon` (secondary) returned six populated rows for the same platform. |
| `platform inventory-match amazon` | `{"match": null, "inventory_available": true}` | The call was made **without `sku`**. `inventory_available: true` says inventory exists; `match: null` just says nothing was asked for. |
| `platform bigbasket-ads-daily-dashboard bigbasket` | `summary` all zeros, while `platform bigbasket-ads-dashboard bigbasket` returned ₹35,724 spend / ₹2,16,934 sale for the same account | The **daily** feed is empty while the monthly one is not. Almost certainly a stale upload, not zero advertising. See Trap 10. |

Rule for the guide: distinguish *"the platform has no data"* from *"this dashboard
is not available for this platform"* (Trap 2/3) from *"nobody has uploaded it"*.
They are three different answers and only the middle one is visible in the status
code.

### Trap 9 — `platform stats` is mostly a stub *(observed)*

`{"inventory": 103, "sells": 0, "openPOs": 0, "activeTrucks": 0}` for Amazon —
yet the same run shows Amazon with real secondary sales and, across platforms,
347 open POs in `primary-overview-total`. So `sells: 0` and `openPOs: 0` here are
**not** business facts. Only `inventory` (103, which matches the 103 rows in the
Amazon SOH snapshot for 2026-07-29) is corroborated. Treat `stats` as a UI tile
feed, and answer stock/PO questions from `soh-doh` and `pendency` /
`primary-overview-total`.

### Trap 10 — "daily" ads endpoints are trend companions, not standalone *(observed)*

`bigbasket-ads-daily-dashboard`, `swiggy-ads-daily-dashboard` and
`zepto-ads-daily-dashboard` are wired in the SPA as the `trendApiGet` of their
non-daily sibling — Blinkit and Flipkart and Amazon have no daily sibling at all.
Sources differ (`bigbasketads_daily_master` vs `bigbasket_ads_master`), so they
are **separate uploads that can go stale independently**, which is exactly what
happened to BigBasket in this run (see Trap 8). Never substitute one for the other;
if a monthly figure and a daily figure disagree, that is a feed problem, not a
rounding difference.

### Trap 11 — `(Unmapped)` is a real, common bucket *(observed)*

Swiggy brand fund came back with **100 % of the total** (₹1,178.48) under
`"dimension": "(Unmapped)"`. Amazon's ads-summary has an `(Unmapped)` item head
carrying 4,246 units and ₹1.76 L of ad spend. `(Unmapped)` means the platform's
SKU code did not join to JIVO's item master. It is not a product. Any
"top item" or "which variety" answer must state how much sat in `(Unmapped)`, or
it is quietly wrong. Related: per JIVO correction C-0003, segment on the SAP
fields, never on item-name matching — the item names here (`CANOLA 1+1L`,
`SANO MUSTARD 1L`) are the platform's listing names, not SAP's.

### Trap 12 — the shipped slug enum contains a platform the live data does not *(observed)*

The shipped spec's `platform` enum is `amazon, bigbasket, blinkit, citymall,
flipkart, flipkart_grocery, jiomart, swiggy, zepto, zomato`.

Live evidence this run:
- Nine of those ten appear as `by_platform` keys in the 200 from
  `primary-overview-total`. **`jiomart` does not.**
- The SPA's own registry marks jiomart `hidden: true`, and the folder pages
  explicitly filter jiomart out of primary, secondary and inventory.
- `/api/dashboard/platform-expiry-alerts` (a live 200 harvested for slug values)
  lists seven: amazon, bigbasket, blinkit, flipkart_grocery, swiggy, zepto, zomato.

I would keep `jiomart` in the enum (removing it is a breaking change and it is not
proven refused), but the guide should say it is dormant. Slugs I confirmed by a
200 **in this domain** this run: amazon, bigbasket, blinkit, flipkart, swiggy,
zepto. `citymall`, `flipkart_grocery` and `zomato` are attested by live payloads
elsewhere (the `by_platform` block, and the server naming `flipkart_grocery` in the
landing-rate 400) but I did not personally see a 200 from a slug-parameterised
platform endpoint for them. `amazon_mp` is used by the SPA for `sec-dashboard` and
`drr-dashboard` (`source=mp`) and was **never probed** — I could not verify it.

### Trap 13 — `landing-rate` wants the month as `YYYY-MM-01`, and `carried_over` changes what the number means *(observed)*

The SPA builds the parameter as `` `${month}-01` `` and the live response echoes
`"month": "2026-06-01"` / `"month": "2026-08-01"`. A bare `2026-08` is not what the
UI sends. Also:
- `mode` is `effective` or `history`. `effective` shows the rate in force —
  including rows with `"carried_over": true`, which are **last month's rate still
  applying because nobody set one for this month**. `history` shows what was
  actually entered. Reporting a carried-over rate as "this month's agreed rate" is
  wrong.
- `landing-rate/skus` returns `has_rate: false` per SKU. In this run **all ten
  Blinkit SKUs showed `has_rate: false` for 2026-08** while `landing-rate` returned
  June rates flagged `carried_over: true`. That is the "nobody has set August
  rates yet" signal, and it is the most useful thing in this pair.

### Trap 14 — the three `*-version` endpoints are opaque tokens in three different formats *(observed)*

`primary-summary-version` → `"406262"`; `secondary-summary-version` →
`"507467010"`; `mp-dashboard-version` → `"2026-08-03T11:25:54.544627+00:00"`.
Only the third is a timestamp. These are change-detection tokens the UI polls;
they are not row counts, not record ids, and only the MP one tells you *when*.
Do not parse or compare them across endpoints.

### Trap 15 — "defaulted" flags tell you the server picked the period, not you *(observed)*

`defaulted_to_latest: true` (primary, secondary, drr, comparison, coupon, soh-doh,
mp, primary-summary) and `defaulted_range: true` (sales explorers) mean **no month
was passed and the server chose one**. `bigbasket-sales-explorer` defaulted to a
**two-day** window (2026-08-01 to 2026-08-02) — an operator who runs it bare and
reads ₹9.37 L will think that is a month. Always echo the `from_date`/`to_date`/
`month`/`year` the server reports back, and say when it was defaulted.

Related: `max_date` and `sales_max_date` are often **different** (drr on Amazon:
`max_date` 2026-07-29 while the month has 31 days, `elapsed_days: 29`). A
month-to-date figure is not a month figure — `elapsed_day` vs `days_in_month` is
there so you can say so.

### Trap 16 — target percentages are fractions, and targets are in litres *(observed)*

`month-targets` row for Amazon COMMODITY, July 2026:
`targets: 180000.0`, `done_ltrs: 250736.0`, `achieved_pct: 1.393`.
`250736 / 180000 = 1.3930` — so **`achieved_pct` is a ratio, not a percentage**
(139.3 %, not 1.39 %), and **`targets` is denominated in litres**, matched against
`done_ltrs`, not against `done_value`. Same for `est_ltr_pct` (1.489) and
`growth_pct` (1.0755 = +107.6 % growth). Printing these with a `%` sign unchanged
understates achievement by 100×.

### Trap 17 — two pairs that look interchangeable and are not

- **`platform ads` vs `platform ads-summary`** — the first is Amazon AMS only,
  dimensioned by portfolio; the second is every platform, dimensioned by item
  head/category/item. Different denominators: `ads` reports `sales` ₹9.44 Cr for
  Amazon; `ads-summary` reports `ads_sale` ₹21.35 Cr across all platforms against
  `sec_value` ₹116.43 Cr total. Neither is a subset you can subtract.
- **`platform soh-doh` vs `platform region-doh`** — same idea (days of cover),
  different grain and different availability. `soh-doh` is SKU/warehouse level and
  runs on amazon, blinkit, zepto, swiggy, bigbasket. `region-doh` is **city** level
  and runs on swiggy and zepto only. If someone asks "which city is low", `soh-doh`
  cannot answer it and `region-doh` cannot be asked about Blinkit.

---

## 4. Recommended spec entries

46 endpoints. Command names in **bold** are new (the endpoint has
`SHIPPED_COMMAND_NAME_DO_NOT_RENAME: null`); every other name is the shipped one
and must not change. All are GET. Response type is `object` for all 43 that
returned a live 200; for the three `LIVE_NEEDS_PARAMS` entries the shape was
**not observed** (the server returned 400 before any body) — the shipped spec
declares `object` and I would carry that forward while labelling it unverified.

Shared param types: `platform` = string, positional, required, enum as in the
shipped spec. `month` = int 1-12 (except where noted). `year` = int YYYY.
`date`, `from_date`, `to_date` = string `YYYY-MM-DD`. `page`, `page_size` = int.

| # | command | params (type — observed enum) | response |
|---|---|---|---|
| 1 | `platform ads-summary` — one ad P&L across all platforms | `month` int, `year` int, `date` str, `from_date` str, `to_date` str, `platform` str (all six named in the response's own `filters` block) | object |
| 2 | `platform meta` — **Meta (Facebook/Instagram) ad campaign performance** | `year` int, `month` int | object |
| 3 | `platform primary-summary` — sell-in roll-up across platforms for a month | `mode` str (`DEL MONTH`, `PO MONTH`), `month` int, `year` int, `slugs` str (comma-joined) | object |
| 4 | `platform primary-overview-total` — sell-in headline + open-PO exposure, per platform | `month` int, `year` int | object |
| 5 | `platform primary-summary-version` — change token for the primary data | none | object |
| 6 | **`platform secondary-summary-version`** — change token for the secondary data | none | object |
| 7 | `platform call-center-targets` — call-centre channel targets for a month | `month` int **required**, `year` int **required** | not observed (shipped: object) |
| 8 | `platform month-targets-dashboard` — **secondary** targets vs achievement, all platforms | `month` int **required**, `year` int **required** | not observed (shipped: object) |
| 9 | `platform primary-month-targets-dashboard` — **primary** targets vs achievement, all platforms | `month` int **required**, `year` int **required** | not observed (shipped: object) |
| 10 | **`platform bigbasket-sales-explorer`** — day-by-day BigBasket sell-out (BigBasket is fixed in the path) | `from_date` str, `to_date` str, `sales_of` str comma-joined (`PREMIUM`, `COMMODITY`, `OTHER`) | object |
| 11 | `platform primary` — sell-in (PO) dashboard for one platform | `platform`, `mode` str (`DEL MONTH`, `PO MONTH`), `month` int, `year` int, `channel` str amazon-only (`ALL`, `CORE`, `FRESH`, `NOW`) | object |
| 12 | `platform secondary` — sell-out dashboard for one platform | `platform`, `month` int, `year` int, `date` str | object |
| 13 | `platform secondary-years` — which years have secondary data | `platform` | object |
| 14 | `platform secondary-monthly` — month-by-month secondary for a year | `platform`, `month` int, `year` int | object |
| 15 | `platform drr` — daily run-rate and month projection | `platform`, `month` int, `year` int, `item_head` str (`ALL`, `PREMIUM`, `COMMODITY`, `OTHER`), `sales_mode` str (`ORDERED`, `SHIPPED`), `sales_of` str, `from_date` str, `to_date` str, `source` str (`mp`, amazon_mp only) | object |
| 16 | `platform soh-doh` — stock on hand and days of cover at the platform | `platform`, `date` str, `month` int (amazon), `year` int (amazon) | object |
| 17 | `platform pendency` — open/pending PO exposure by city | `platform`, `scope` str (`all`), `from_date` str, `to_date` str, `status` str (`expired`) | object |
| 18 | `platform region-doh` — city-level days of cover (**swiggy, zepto only**) | `platform`, `date` str | object |
| 19 | `platform marketplace` — Amazon Marketplace (3P) sales, GST-inclusive and exclusive | `platform`, `month` int, `year` int | object |
| 20 | `platform mp-dashboard-version` — change token for the MP dashboard | `platform` | object |
| 21 | `platform price` — Amazon price / stock / competitor tracking | `platform`, `date` str | object |
| 22 | `platform coupon` — Amazon coupon spend for a snapshot date | `platform`, `date` str | object |
| 23 | `platform comparison` — peak month vs current month per sub-category | `platform`, `month` int, `year` int, `history_year` int | object |
| 24 | `platform ads` — Amazon AMS ads by portfolio | `platform`, `year` int, `month` int, `from_date` str, `to_date` str, `dimension` str, `metric` str (`ordered`, `shipped`), `date_wise` int (`1`), `month_wise` int (`1`) | object |
| 25 | `platform ads-total-sales` — the shipped-value denominator behind ads ROAS | `platform`, `month` int, `year` int, `metric` str (`ordered`, `shipped`), `as_of_date` str, `from_date` str, `to_date` str, `date_wise` int, `month_wise` int | object |
| 26 | `platform stats` — the four headline tiles (only `inventory` corroborated) | `platform` | object |
| 27 | `platform pos` — paged PO list (no SPA screen uses it) | `platform`, `page` int, `page_size` int | object |
| 28 | `platform inventory-match` — resolve one SKU against platform inventory | `platform`, **`sku`** str (meaningless without it) | object |
| 29 | `platform month-targets` — **secondary** monthly targets for one platform | `platform`, `month` int, `year` int | object |
| 30 | `platform primary-month-targets` — **primary** monthly targets for one platform | `platform`, `month` int, `year` int | object |
| 31 | `platform landing-rate` — monthly landing rate per SKU (**blinkit, zepto, swiggy, bigbasket, flipkart_grocery**) | `platform`, `mode` str (`effective`, `history`), `month` str **`YYYY-MM-01`**, `search` str, `page` int, `page_size` int | object |
| 32 | `platform landing-rate-skus` — which SKUs still have no landing rate (same five platforms) | `platform`, `month` str **`YYYY-MM-01`** | object |
| 33 | **`platform monthly-sales-explorer`** — multi-month sell-out with growth % (**bigbasket, blinkit, swiggy, zepto**) | `platform`, `months` str comma-joined `YYYY-MM`, `sales_of` str comma-joined | object |
| 34 | `platform blinkit-ads-dashboard` — Blinkit ads (**blinkit only**) | `platform`, `year`, `month`, `from_date`, `to_date`, `date_wise`, `month_wise` | object |
| 35 | `platform blinkit-brandfund-dashboard` — Blinkit brand-fund accruals (**blinkit only**) | `platform`, `year` int, `month` str, `date` str | object |
| 36 | **`platform blinkit-summary-report`** — Blinkit monthly one-pager incl. paid vs organic (**blinkit only**) | `platform`, `year` int | object |
| 37 | `platform zepto-ads-dashboard` — Zepto ads (**zepto only**) | `platform`, `year`, `month`, `from_date`, `to_date` | object |
| 38 | `platform zepto-ads-daily-dashboard` — Zepto ads day-by-day (**zepto only**) | `platform`, `year`, `month`, `from_date`, `to_date` | object |
| 39 | `platform zepto-brandfund-dashboard` — Zepto brand fund (**zepto only**) | `platform`, `year`, `month`, `date` | object |
| 40 | `platform swiggy-ads-dashboard` — Swiggy ads (**swiggy only**) | `platform`, `year`, `month`, `from_date`, `to_date` | object |
| 41 | `platform swiggy-ads-daily-dashboard` — Swiggy ads day-by-day (**swiggy only**) | `platform`, `year`, `month`, `from_date`, `to_date` | object |
| 42 | `platform swiggy-brandfund-dashboard` — Swiggy brand fund (**swiggy only**) | `platform`, `year`, `month`, `date` | object |
| 43 | `platform bigbasket-ads-dashboard` — BigBasket ads (**bigbasket only**) | `platform`, `year`, `month`, `from_date`, `to_date` | object |
| 44 | `platform bigbasket-ads-daily-dashboard` — BigBasket ads day-by-day (**bigbasket only**) | `platform`, `year`, `month`, `from_date`, `to_date` | object |
| 45 | `platform flipkart-ads-dashboard` — Flipkart ads by campaign (**flipkart only**) | `platform`, `year`, `month`, `from_date`, `to_date` | object |
| 46 | `platform flipkart-fsn-dashboard` — Flipkart FSN-level ads, selectable dimension (**flipkart only**) | `platform`, `year`, `month`, `dimension` str (`item`, `sub_category`, `category`, `item_head`, `campaign_name`) | object |

Two spec-level requests that matter more than any single entry:
1. **Attach the platform restriction to the endpoint definition**, not just the
   docs, so the CLI can refuse the wrong pairing locally with the server's own
   sentence instead of surfacing a bare 400. The lists in §2c are verbatim.
2. **Fix the `platform meta` description** (Trap 1) while keeping the name.

---

## 5. Exclusions

15 endpoints, every one with a positive reason.

### 5a. Proven dead — 1

**`platform month-on-month-sale` — `/api/platform/{}/month-on-month-sale`**
*This one is in the shipped v0.1.0 spec, so its removal needs the justification
spelled out.*

- Probed on **seven** slugs: amazon, bigbasket, blinkit, flipkart_grocery,
  swiggy, zepto, zomato. **404 on all seven**, no exceptions.
- The 404 body is Django's URL-resolver page — `<!doctype html><html lang="en">
  <head><title>Not Found</title></head><body><h1>Not Found</h1><p>The requested
  resource was not found on this server.</p></body></html>` — i.e. HTML from the
  router, not a DRF JSON error from a view. That means no route matched, which is
  **slug-independent**: trying an eighth slug would not change it.
- `client_methods` and `client_fn_names` are both **empty** — no code in the
  current SPA bundle calls it. The path survives only as a string.
- Contrast with `region-doh-dashboard`, which produces the *same* HTML for five
  slugs but returns 200 for swiggy and zepto. That 200 is what separates "alive
  but restricted" from "gone"; `month-on-month-sale` has no such 200 anywhere.

Confidence it is dead: **high**. What would change my mind: a 200 from a slug I
did not try. Only `citymall` and `jiomart` were untried, and jiomart is dormant
(Trap 12) — but I did not test them, and I am saying so rather than claiming
exhaustiveness.

The capability is not lost: month-on-month movement is available from
`platform secondary-monthly` (per platform, monthly, with `mom_growth`) and
`platform monthly-sales-explorer` (bigbasket/blinkit/swiggy/zepto, with
`growth_ltr` / `growth_qty` / `growth_value`).

### 5b. Write endpoints — excluded by RULE 0 (ecom is read-only) — 14

All 14 UNPROBED entries in this bundle are writes. **`UNPROBED` here means "we
deliberately never sent it", not "it might be dead"** — each one is POST-only in
`client_methods`, each has a mutating `client_fn_name`, and none is in the shipped
spec. There is no evidence any of them is broken and none should be recorded as
such.

| path | client fn | what it would do |
|---|---|---|
| `/api/platform/{}/landing-rate/add` | `add` | create a landing rate for a SKU |
| `/api/platform/{}/landing-rate/update` | `update` | change an existing landing rate |
| `/api/platform/{}/landing-rate/bulk-upsert` | `bulkUpsert` | mass insert/update landing rates |
| `/api/platform/{}/landing-rate/preview` | `previewBulk` | **POST despite the read-only-sounding name** — see note below |
| `/api/platform/{}/month-targets/add` | `create` | create a secondary monthly target |
| `/api/platform/{}/month-targets/{}/update` | `update` | edit one secondary target row |
| `/api/platform/{}/month-targets/{}/refresh` | `refresh` | recompute one secondary target row |
| `/api/platform/{}/month-targets/refresh` | `refreshPlatform` | recompute a platform's secondary targets |
| `/api/platform/month-targets/refresh` | `refreshDashboard` | recompute the whole secondary targets dashboard |
| `/api/platform/{}/primary-month-targets/add` | `create` | create a primary monthly target |
| `/api/platform/{}/primary-month-targets/{}/update` | `update` | edit one primary target row |
| `/api/platform/{}/primary-month-targets/refresh` | `refreshPlatform` | recompute a platform's primary targets |
| `/api/platform/primary-month-targets/refresh` | `refreshDashboard` | recompute the whole primary targets dashboard |
| `/api/platform/primary-month-targets/set-target` | `setTarget` | set a primary target value |

**`/landing-rate/preview` deserves a specific warning.** "Preview" reads like a
dry run and it is the most likely of the fourteen to get argued into the spec. It
is a POST, so RULE 0 excludes it — and the sibling project's precedent is exactly
this shape: on the factory app a GET that looked inert (`GET
/marketplace/settings/`) turned out to create rows. A POST named "preview" carries
strictly more risk than that, and its behaviour is unverified because we correctly
never sent it. Keep it out.

Also excluded, though not a separate path: the **POST half of
`/api/platform/call-center-targets`** (`save`). The GET half is published as
`platform call-center-targets`; the POST is not, and the CLI must pin that command
to GET so it cannot be talked into the other verb.

---

## Things I could not verify

Stated plainly rather than papered over:

- **Response shape for the three `LIVE_NEEDS_PARAMS` endpoints** —
  `call-center-targets`, `month-targets/dashboard`,
  `primary-month-targets/dashboard`. The probe never got past the 400. I took the
  required-parameter names verbatim from the error body and invented nothing else.
- **The exact ROAS/ACOS formula** on the quick-commerce ads dashboards (Trap 7). I
  can show the numbers do not agree with the obvious ratio; I cannot say what they
  are.
- **`amazon_mp`** as a slug. The SPA uses it for `sec-dashboard` and passes
  `source=mp` to `drr-dashboard`, but it was never probed.
- **Whether `pos` and `inventory-match` return real data on any slug.** Both are
  live and both are dead code in the SPA. Amazon returned an empty page and a null
  match respectively.
- **`citymall`, `zomato`, `flipkart_grocery`, `jiomart` against slug-parameterised
  platform endpoints.** They are attested as platform slugs by live payloads
  (`by_platform` in `primary-overview-total`, the landing-rate 400 naming
  `flipkart_grocery`, `platform-expiry-alerts` naming zomato), but I did not see a
  200 from a `/api/platform/<slug>/...` call for any of them in this run.
- **Whether the eleven single-platform restrictions are hard-coded or config.**
  `pendency` phrases it as "not yet enabled", which suggests config; the others say
  "available only for X", which suggests hard-coded. I did not read the server.
