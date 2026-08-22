# Study — the four NEW live GET endpoints in `platform` and `reports`

Run: rescrape-all, 2026-08-22. Domain agent: platform+reports new endpoints.
READ-ONLY throughout: every request below is a GET. No non-GET verb was issued.

Endpoints in scope (all confirmed live 200 today):

| # | path | proposed command | verdict |
|---|---|---|---|
| 1 | `GET /api/platform/overall-pendency` | `platform overall-pendency` | PUBLISH |
| 2 | `GET /api/platform/{platform}/blinkit-campaigns-optimization` | `platform blinkit-campaigns-optimization` | PUBLISH (heavy) |
| 3 | `GET /api/platform/{platform}/blinkit-sale-target` | `platform blinkit-sale-target` | PUBLISH |
| 4 | `GET /api/reports/amazon-po/sku-pendency/summary` | `reports amazon-po-sku-pendency-summary` | PUBLISH (zero params) |

Shell convention used in every command below:

```bash
T=$(cat /root/.handoff-runs/rescrape-all/scratch/.ecom_token)   # never printed
BUNDLE=/root/.handoff-runs/rescrape-all/scratch/ecom/bundle
```

---

# PART A — Operator meaning, screen by screen

## 1. `platform overall-pendency` — "OVERALL PENDENCY"

**One sentence:** Every Amazon/q-commerce purchase order that has been placed on
JIVO and not yet fully delivered, rolled up by product (or category / sub-category)
across all eight platforms at once — the group-level answer to "how much have the
platforms asked for that we still owe them?"

**Screen:** `https://ecom.jivo.in/pendency` — a top-level route, NOT under
`/platform/<slug>/`. Reached from the main Dashboard's pendency panel via a button
whose own tooltip is *"Open Overall Pendency — SKU-wise across all platforms"*.
The page's own subtitle is the tightest definition available:
**"Open POs not yet delivered · all months · every platform"**.

Evidence:
```bash
grep -oE 'path:`[a-z0-9/_:-]*`,element:[^}]{0,60}wr\b' $BUNDLE/index-Bdcm-waj.js
#  -> path:`/pendency`,element:(0,z.jsx)(W,{children:(0,z.jsx)(wr
grep -oE '[a-zA-Z$_]{1,3}=\(0,R.lazy\)\(\(\)=>b\(\(\)=>import\(`\./OverallPendencyDashboard-BOrolRjU\.js`\)' $BUNDLE/index-Bdcm-waj.js
#  -> wr=(0,R.lazy)(...OverallPendencyDashboard-BOrolRjU.js...)
grep -oE '.{500}Open POs not yet delivered.{700}' $BUNDLE/OverallPendencyDashboard-BOrolRjU.js
#  -> h2 `OVERALL PENDENCY`, p.opend-sub `Open POs not yet delivered · all months · every platform`
grep -rn --include=*.js -oE '.{160}`/pendency`.{160}' $BUNDLE | grep -v 'path:`/pendency`,element'
#  -> Dashboard-B-XMNQ9W.js: title:`Open Overall Pendency — SKU-wise across all platforms`
```

### Field meanings — and the two that lie

Column headers come from the page's own Excel-export column spec, which is the
app's authoritative naming:

```bash
grep -oE 'key:`pending_ltrs`,header:`Pending LTRS`,format:`money`\},.{400}' $BUNDLE/OverallPendencyDashboard-BOrolRjU.js
grep -oE '.{500}Open POs not yet delivered.{700}' $BUNDLE/OverallPendencyDashboard-BOrolRjU.js
```

| field | UI header | what it actually is |
|---|---|---|
| `label` | Item / Category / Sub Category | the group key; which one depends on `group_by` |
| `item_head` | Item Head | PREMIUM / COMMODITY / OTHER — **or the synthetic `MIXED`**, see trap T-3 |
| `items` | (not shown) | count of distinct items folded into this group |
| `platform_count`, `platform_slugs`, `platform_names` | Platforms | which platforms have open pendency on this group |
| `platforms[]` | (expand row) | the same six measures split per platform; no second API call, it is nested in the row |
| **`open_units`** | **Open PO Units** | **⚠ NOT "units still open". This is the quantity ORIGINALLY ORDERED.** See trap T-1. |
| **`open_ltrs`** | **Open PO LTRS** | litres of the originally-ordered quantity. Exported with `format:'money'`, which is a UI bug, not a unit change. |
| **`pending_units`** | **Pending Units** | the real outstanding number: ordered − received |
| `pending_ltrs` | Pending LTRS | litres of that outstanding quantity |
| **`pending_value`** | **Pending Value** | **⚠ GST-INCLUSIVE rupees.** 1.05 × the pre-tax value the per-platform screen shows. See trap T-2. |
| `open_pos` | Open POs | **distinct** PO count — never summable across rows. Trap T-4. |
| `totals.rows` | (footer) | count of underlying PO *lines*, not of returned rows |
| `totals.groups` | (footer) | count of returned rows — this is `len(rows)` |
| `min_po_date` / `max_po_date` | (unused by UI) | `DD-MM-YYYY` window of the PO dates in scope. Useful freshness stamp for a CLI. |
| `max_date` | (unused by UI) | **always `null` in every one of the ~20 responses observed today. Dead field.** |
| `undated_rows` | (unused by UI) | PO lines with no date; `0` in every response observed |
| `by_head[]` | 3 stat tiles | per-item-head roll-up. `open_pos` inside it double-counts, trap T-4. |
| `available_platforms[]` | platform picker | `{slug, name}` — the authoritative slug list for the `platforms` param |
| `error` | inline banner | the UI reads `z.error`, so a **200 can carry an error string in the body**. A CLI must check it. |

The UI reads only five keys off the payload; everything else is CLI-only surface:
```bash
grep -oE '(z|B)\.[a-z_]+' $BUNDLE/OverallPendencyDashboard-BOrolRjU.js | sort -u
# -> B.pending_ltrs  z.available_platforms  z.by_head  z.error  z.rows  z.totals
```

---

## 2. `platform blinkit-campaigns-optimization` — "Campaigns Optimization"

**One sentence:** The whole month of Blinkit ad-spend raw data — every keyword-day
of Product Booster, every creative-day of Recommendation Ads, and every
city-item-day of Brand Fund — dumped in one response so the browser can compute
ROAS, keyword efficiency and city demand client-side.

**Screen:** `https://ecom.jivo.in/platform/blinkit/blinkit-campaigns-optimization`,
nav path **Blinkit › Marketing › Campaigns Optimization**. Blinkit-only in the nav
(`e === 'blinkit'` guard). Panel titles: *"Where the keyword money is going"*,
*"Which creative placement earns its spend"*, *"City demand"*, *"Daily sales and
spend"*, *"Campaign by day"*, *"SKU by day"*, *"Month-to-date budget and claimables"*.

Evidence:
```bash
grep -oE '.{250}blinkit-campaigns-optimization.{250}' $BUNDLE/PlatformLayout-DZoZNbjI.js
#  -> "blinkit-campaigns-optimization":`Campaigns Optimization` ; group `Marketing` ;
#     childPaths under  e===`blinkit`&&...  Marketing accordion
grep -oE 'title:`[^`]{4,60}`' $BUNDLE/PlatformBlinkitCampaignsOptimization-B32l52Wb.js | sort -u
grep -oE 'children:`[A-Z][^`]{12,130}`' $BUNDLE/PlatformBlinkitCampaignsOptimization-B32l52Wb.js
#  -> `Blinkit · Marketing`, `Campaigns Optimization`, `Loading Blinkit campaign data…`
```

### The one thing a CLI author must know first

**⚠ TRAP T-5 — the `{platform}` path segment is IGNORED by the server.** The UI
hardcodes the slug (`be = 'blinkit'`), and the server does not validate it: any
slug returns the identical Blinkit payload, byte for byte.

```bash
for p in blinkit zepto; do
  curl -s -H "Authorization: Bearer $T" \
    "https://ecom.jivo.in/api/platform/$p/blinkit-campaigns-optimization" -o bco-$p.json
done
md5sum bco-blinkit.json bco-zepto.json
# 14c4833a54a77b03bb09e376dd4e01b9  bco-blinkit.json
# 14c4833a54a77b03bb09e376dd4e01b9  bco-zepto.json   <-- identical, 2,747,172 bytes each
grep -oE 'be=[^,;]{0,60}' $BUNDLE/PlatformBlinkitCampaignsOptimization-B32l52Wb.js
# -> be=`blinkit`
```
Compare `blinkit-sale-target`, which *does* validate (§3). A CLI should pin the
path segment to `blinkit` and refuse other slugs itself, or the operator will
believe they are looking at Zepto ad data when they are not.

### Top-level keys — and how heavy each is

```bash
curl -s -H "Authorization: Bearer $T" \
  'https://ecom.jivo.in/api/platform/blinkit/blinkit-campaigns-optimization' -o bco.json
jq -r 'to_entries|map("\(.key)\t\(.value|type)\t\(if (.value|type)=="array" then (.value|length|tostring)+" items" else "" end)")|.[]' bco.json
python3 -c "import json;d=json.load(open('bco.json'));[print(f'{k:20s} {len(json.dumps(v)):>9,} bytes') for k,v in d.items()]"
```

| key | type | rows (current month) | bytes | share | what it is |
|---|---|---|---|---|---|
| `skuMaster` | array | 13 | 2,083 | 0.1% | the SKU dictionary: `{sku, brand, size, itemCode, litres, category, basicPrice, note}`. `basicPrice` is pre-GST (e.g. Extra Light 1L = 497.1428571). Everything else joins to this. |
| `brandFund` | array | 6,782 | 653,352 | 23.8% | city × item × day brand-fund accrual: `{date, city, itemId, qty, brandFund}`. Feeds the "City demand" panel. |
| `productBooster` | array | 12,800 | 2,207,763 | **80.4%** | keyword × campaign × day Product Booster ads: `{date, campaign, keyword, cpm, budget, impressions, sales, qty, spend}`. The single biggest cost in the payload. |
| `recommendationAds` | array | 1,058 | 201,261 | 7.3% | creative-asset × campaign × day Recommendation Ads, same 9 fields but `asset` instead of `keyword`. UI abbreviates these two as **PB** and **RA**. |
| `momHistory` | array | **0** | 2 | 0% | plumbed into the derived model but **never rendered anywhere in this build**, and empty in every live call. Dead. |
| `mtdSpend` | array | **0** | 2 | 0% | would feed the *"Month-to-date budget and claimables"* panel (`campaign, campaignId, impressions, budget, claimables, consumed`). Panel is `.length > 0`-gated, so it never renders today. **Shape is NOT VERIFIED against live data** — known only from the UI's column spec. |
| `coverage` | object | — | 83 | 0% | `{from, to, keywordRows, assetRows}` — echoes the applied window and the PB/RA row counts. The one cheap thing to read before pulling the payload. |

Field-name warning inside `productBooster` / `recommendationAds`: `sales` is the
platform-**reported** sales figure, which the UI immediately discards and
recomputes. It keeps the raw value as `salesReported` and overwrites `sales` with
`qty × skuMaster.basicPrice`:
```bash
grep -oE '.{120}\.get\([a-zA-Z]{1,3}[,)].{150}' $BUNDLE/PlatformBlinkitCampaignsOptimization-B32l52Wb.js | head -3
# -> o=e=>{let t=i(e.campaign);return{...e,sku:t,salesReported:S(e.sales),sales:se(a.get(t),e.qty)}}
```
So the API's `sales` and the screen's "Sales (Basic)" are **different numbers**. A
CLI passing through `sales` verbatim will not reconcile with the dashboard.

---

## 3. `platform blinkit-sale-target` — "Daily & Targets"

**One sentence:** Blinkit's litre-wise monthly target sheet — target vs
month-to-date achievement vs run-rate projection per SKU, with up to twelve
prior month-close columns beside it — plus a two-day daily sales comparison at
the top.

**Screens (two routes, same component, same endpoint):**
- `https://ecom.jivo.in/platform/blinkit/blinkit-sale-target` — nav **Blinkit › Marketing › Daily & Targets**
- `https://ecom.jivo.in/sale-target/blinkit` — from the Marketing hub; breadcrumb **Home › Marketing › Daily & Targets · Blinkit**; non-blinkit slugs client-redirect to `/expense`

Evidence:
```bash
grep -oE '.{250}blinkit-sale-target.{250}' $BUNDLE/PlatformLayout-DZoZNbjI.js
#  -> "blinkit-sale-target":`Daily & Targets`, group `Marketing`, under e===`blinkit`
grep -oE '.{160}\bUn\b,\{\}\).{60}' $BUNDLE/index-Bdcm-waj.js
#  -> path:`/sale-target/:slug`,element:...(Un)   [Un = SaleTargetDashboardPage-C5L-CPsE.js]
head -c 858 $BUNDLE/SaleTargetDashboardPage-C5L-CPsE.js
#  -> d={blinkit:l}; if(!f) redirect `/expense`; breadcrumb `Daily & Targets · ` + platform name
```

### Response shape

```bash
curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target' -o bst.json
jq 'to_entries|map({k:.key,t:(.value|type)})' bst.json
jq '{daily_keys:(.daily|keys),targets_keys:(.targets|keys)}' bst.json
```

Top level: `slug, as_on, compare_date, max_date, month, year, month_label,
days_in_month, elapsed_days, editable, daily{current,compare}, targets{...}`.

`daily.current` / `daily.compare`: `{date, label, rows[], by_head[], total}` where
each row is `{item, item_head, category, ltrs, sales_exc, qty}`.
**`sales_exc` = sales EXCLUSIVE of GST** (UI header "Sale Exclusive"). `ltrs` and
`qty` differ for multipacks (CANOLA 5L: qty 70, ltrs 350).

`targets`: `{available_close_months[], close_months[], sections[], grand_total, prev_month_label}`.
`sections[]` is one block per item head — observed titles *"Blinkit Premium Litre
Vise Target"* and *"Blinkit Commodity Litre Vise Target"* — each with `rows[]`
and a `total`, in the same measure shape as `grand_total`:

| field | UI header | meaning |
|---|---|---|
| `target_ltr` | Target LTR | the saved monthly litre target. **`null` when no target was ever saved for that month** (observed: Jul-26 grand total `target_ltr: null`). |
| `done_ltr` / `done_value` | Done LTR | month-to-date achieved litres / value, cut off at `as_on` |
| `projection_ltr` | (run rate) | `done_ltr ÷ elapsed_days × days_in_month`. Verified: 80778/21×31 = 119243.714 = reported value. |
| `closes{YYYY-MM: ltr}` | one column per close month | the achieved litres of each **selected** prior month |
| **`growth_pct`** | (growth) | **⚠ a FRACTION (0.0369 = "4%"), and it is relative to whichever close month the CALLER selected.** Trap T-6. |
| **`achieved_pct`** | Target Achieved | **⚠ a FRACTION.** `done_ltr ÷ target_ltr`; `null` when `target_ltr` is null. |
| `editable` (top level) | footnote | whether the reporting month is still open for target entry. `false` triggers *"<month> has closed — targets already saved for it are read-only."* Informational only for a read-only CLI. |

Both percent fields are multiplied by 100 at render time:
```bash
grep -oE '.{160}\*100.{80}' $BUNDLE/PlatformBlinkitSaleTargetDashboard-CwyBd7yW.js
# -> function T(e){... `${Math.round(Number(e)*100)}%`}   function E(e){... `${(Number(e)*100)...}%`}
```

---

## 4. `reports amazon-po-sku-pendency-summary` — Shipment-Planner "open book"

**One sentence:** The 46-metric health card for Amazon's open PO book — fill rate,
acceptance rate, expiry clock, and the two reconciliation leaks ("dispatched but
not invoiced" / "billed but not moved") — totalled and split by fulfilment centre
and by Amazon channel.

**Screen:** the index panel of
`https://ecom.jivo.in/platform/amazon/shipment-planning`, which is
**permission-gated in the UI** (`<Gate permission={PERMS.shipmentPlanning}>`).
It is NOT the page that owns the row-level `amazon-po/sku-pendency` report — that
is `/platform/amazon/primary/sku-pendency` (`variant: primary`), which calls
`amazonSkuPendency` + `amazonSkuPendencyOptions` and **never** calls the summary.

```bash
grep -oE 'amazonSkuPendency[A-Za-z]*\(' $BUNDLE/SkuPoPendency-mBzq5vij.js $BUNDLE/SPDashboard-BHa8jXNE.js | sort | uniq -c
#  1 SPDashboard-BHa8jXNE.js:amazonSkuPendencySummary(
#  1 SkuPoPendency-mBzq5vij.js:amazonSkuPendency(
#  1 SkuPoPendency-mBzq5vij.js:amazonSkuPendencyOptions(
grep -oE 'path:`[a-z0-9/_:-]*`,element:[^}]{0,80}' $BUNDLE/index-Bdcm-waj.js | grep -iE 'shipment|sku-pendency'
#  -> path:`primary/sku-pendency`,element:...(sr,{variant:`primary`
#  -> path:`/platform/amazon/shipment-planning`,element:...(G,{permission:L.shipmentPlanning,...
#  -> path:`sku-pendency`,element:...(sr,{variant:`planner`
grep -oE 'lr=\(0,R.lazy\)\(\(\)=>b\(\(\)=>import\(`\./[A-Za-z0-9_-]+\.js`\)' $BUNDLE/index-Bdcm-waj.js
#  -> lr = SPDashboard-BHa8jXNE.js  (the index child of shipment-planning)
```

**Notable:** the *UI screen* is permission-gated and all 19 `/api/shipment/*`
endpoints 403 on this credential, but this `reports/*` endpoint returns **200**.
The gate is client-side / on the shipment API only, not on this report.

### The metrics, in the app's own words

Tooltips lifted verbatim from the tiles that render them:
```bash
grep -oE 'label:`[^`]{2,50}`,value:`[^`]{0,60}`,sub:`[^`]{0,90}`,title:`[^`]{0,400}`' $BUNDLE/SPDashboard-BHa8jXNE.js
grep -oE 'label:`[^`]{2,50}`,value:[^,]{0,80},title:`[^`]{0,400}`' $BUNDLE/SPDashboard-BHa8jXNE.js
```

| field(s) | tile | definition (app's own tooltip, verbatim where quoted) |
|---|---|---|
| `lines`, `outstanding_lines` | — | all PO lines vs the still-outstanding subset (496 vs 376 today) |
| `requested_units`, `accepted_units`, `received_units`, `cancelled_units` | — | ordered / committed / delivered / cancelled |
| `remaining_units`, `remaining_ltrs` | — | accepted − received, over **all** lines |
| **`open_units`, `open_ltrs`** | **Open book** | *"Everything still to ship, counting outstanding lines only — the same set this tile opens. Including fully-invoiced lines would state a number the list it opens cannot account for."* **⚠ This is NOT the same quantity as the row report's `open_qty`/`open_ltrs` columns.** Trap T-7. |
| `invoiced_units`, `invoiced_ltrs` | Un-invoiced share | how much of the accepted quantity is on a SAP invoice |
| `short_units`, `short_ltrs`, `short_invoice_rate_pct` | Short invoiced | *"Billed, but not for every accepted unit. The gap between what was shipped and what was billed."* |
| `leak_lines`, `leak_units`, `leak_ltrs` | **Dispatched, not invoiced** | *"Goods have physically left but no invoice covers them. Measured as accepted minus invoiced, not as the short-invoice figure — a line with no invoice at all has a shortfall of zero by that definition, and it is the worst case here."* |
| `billed_not_moved_lines/_ltrs` | Billed, not moved | *"Fully invoiced but still in the warehouse — the mirror image of the leak, and a physical-stock question."* |
| `expiring_3d/7d/14d_lines/_ltrs` | Expiring ≤7 days | *"Outstanding litres against the clock. Lines with no expiry date are excluded rather than assumed safe."* |
| `undated_lines` | No expiry date | *"Excluded from every expiry figure above, because they can be neither counted as urgent nor assumed safe."* |
| `decision_lines` | **Awaiting our decision** | *"Accepted 0 and remaining 0 — a line still awaiting an accept/reject decision, not a finished one. The only figure here that is entirely within our control."* |
| `blank_litre_lines` | Missing litre value | *"No stated litre value in the master sheet, so these lines contribute nothing to any litre total above — every litre figure understates by this much."* Drives trap T-9. |
| `multi_invoice_lines` | Split across invoices | *"Billed across more than one invoice — where reconciliation against SAP usually goes wrong."* |
| `fill_rate_pct` | Fill rate | *"Received against accepted — what was actually delivered of what was promised."* |
| `cancel_rate_pct` | Cancellation rate | *"Amazon cancels what is not shipped in time, so this measures our own fulfilment, not their demand."* |
| `acceptance_rate_pct`, `acceptance_gap_units` | Acceptance rate | *"Accepted against requested — how much of what Amazon asked for was committed to."* |
| `delivery_shortfall_ltrs` | Delivery shortfall | *"The litres version of fill rate."* (= accepted − delivered litres) |
| `invoiced_share_pct`, `uninvoiced_share_pct` | Un-invoiced share | *"How much of what was committed is still unbilled."* |

`by_fc[]` (11 FCs today: DED5 DED3 HHS1 HNR4 HHR7 HDL2 HBA4 HCC6 HMV4 HAD1 HKA2)
and `by_channel[]` (CORE, NOW, FRESH, and a literal `"-"` for lines with no
channel) carry the **exact same 46 metrics** plus a `fc` / `channel` key.
Panels are titled *"By FC — open book"* and *"By channel — open book"*, and
clicking one hands `{fulfillment_center: …}` / `{channel: …}` to the *row* report,
not back to this endpoint.

```bash
jq -r '((.by_fc[0]|keys)-(.total|keys))|@json' sp-summary.json   # -> ["fc"]
jq -r '((.total|keys)-(.by_fc[0]|keys))|@json' sp-summary.json   # -> []
```

**⚠ `"-"` channel gotcha:** its `fill_rate_pct` is `null`, not `0`. Any CLI that
formats percentages must survive nulls in `by_channel`.

---

# PART B — Query parameters

## 1. `overall-pendency` — 3 params, all optional, all server-validated

Source of truth is the params memo in the dashboard:
```bash
grep -oE '.{900}group_by:k\}\}\),\[e,d,k\]\)' $BUNDLE/OverallPendencyDashboard-BOrolRjU.js
# L = useMemo(() => ({
#      ...e ? {platforms: e.join(`,`)} : {},
#      ...d === `ALL` ? {} : {item_head: d},
#      ...k === `item` ? {} : {group_by: k}
#    }), [e, d, k])
grep -oE 'S=\[[^]]{0,400}\]' $BUNDLE/OverallPendencyDashboard-BOrolRjU.js
# S=[{key:`ALL`,label:`All`},{key:`PREMIUM`,...},{key:`COMMODITY`,...},{key:`OTHER`,...}]
grep -oE 'C=\[[^]]{0,600}\]' $BUNDLE/OverallPendencyDashboard-BOrolRjU.js
# C=[{key:`item`,label:`Item`},{key:`category`,label:`Category`},{key:`sub_category`,label:`Sub Category`}]
```

| param | type | required | legal values (source) | notes |
|---|---|---|---|---|
| `platforms` | comma-joined string | no | the 8 slugs in the response's own `available_platforms[].slug`: `amazon, swiggy, zepto, blinkit, bigbasket, flipkart_grocery, citymall, zomato` | omitted entirely when all are selected (`q = e => s(e.length === G.length ? null : e)`). The picker forbids deselecting the last one, so the UI never sends an empty value. |
| `item_head` | string enum | no | `ALL` \| `PREMIUM` \| `COMMODITY` \| `OTHER` (array `S`) | `ALL` is the default and is omitted rather than sent |
| `group_by` | string enum | no | `item` \| `category` \| `sub_category` (array `C`) | `item` is the default and is omitted rather than sent |

**A bare call returns 200 with no params** — nothing is required:
```bash
curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/overall-pendency' \
  -o op-bare.json -w '%{http_code} %{size_download}\n'
# 200 47945
```

All values verified live:
```bash
for g in item category sub_category; do
  curl -s -H "Authorization: Bearer $T" \
    "https://ecom.jivo.in/api/platform/overall-pendency?group_by=$g" \
    | jq -c '{group_by,group_label,groups:.totals.groups,rows:.totals.rows,row0_label:.rows[0].label}'
done
# item         -> {"group_by":"item","group_label":"Item","groups":81,"rows":2716,"row0_label":"MUSTARD 1L"}
# category     -> {"group_by":"category","group_label":"Category","groups":14,"rows":2716,"row0_label":"MUSTARD"}
# sub_category -> {"group_by":"sub_category","group_label":"Sub Category","groups":31,"rows":2716,"row0_label":"MUSTARD KACCHI GHANI"}

for h in ALL PREMIUM COMMODITY OTHER; do
  curl -s -H "Authorization: Bearer $T" \
    "https://ecom.jivo.in/api/platform/overall-pendency?item_head=$h" \
    | jq -c '{item_head,groups:.totals.groups,pending_units:.totals.pending_units,by_head:[.by_head[].item_head]}'
done
# ALL       -> groups 81, pending_units 768351, by_head [COMMODITY,PREMIUM,OTHER]
# PREMIUM   -> groups 41, pending_units 264459
# COMMODITY -> groups 24, pending_units 498827
# OTHER     -> groups 16, pending_units   5065        (41+24+16 = 81 ✓)

curl -s -H "Authorization: Bearer $T" \
  'https://ecom.jivo.in/api/platform/overall-pendency?platforms=blinkit,zepto&group_by=category&item_head=PREMIUM' \
  | jq -c '{platforms_selected,group_by,item_head,totals}'
# {"platforms_selected":["zepto","blinkit"],"group_by":"category","item_head":"PREMIUM",
#  "totals":{"pending_units":75316,...,"open_pos":179,"rows":568,"groups":3}}
```

**The server states the `item_head` enum itself.** `MIXED` appears in row output
(see T-3) but is rejected as input:
```bash
curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/overall-pendency?item_head=MIXED'
# HTTP 400  ["`item_head` must be PREMIUM, COMMODITY, OTHER or ALL."]
```
That is a server-confirmed enum, not an inference. A CLI should carry exactly
those four values and no fifth.

## 2. `blinkit-campaigns-optimization` — 2 params, both optional, both narrow server-side

```bash
grep -oE '.{250}m\.get\(be,\{from:.{350}' $BUNDLE/PlatformBlinkitCampaignsOptimization-B32l52Wb.js
# initial load:  m.get(be, {from: u.firstOfMonth, to: u.max})
# widening load: m.get(be, {from: N,               to: u.max})
grep -oE 'Se=[^,;]{0,60}' $BUNDLE/PlatformBlinkitCampaignsOptimization-B32l52Wb.js   # -> Se=6
```

| param | type | required | source / bounds | notes |
|---|---|---|---|---|
| `platform` (path) | string | yes syntactically, **ignored semantically** | UI hardcodes `blinkit` | trap T-5 |
| `from` | `YYYY-MM-DD` | no | UI default = 1st of the current month; earliest the UI will ever ask for is the 1st of the month `Se-1 = 5` months back (a rolling 6-month window) | a free date, from a bounded picker, not an enum |
| `to` | `YYYY-MM-DD` | no | UI default = last day of the current month (`new Date(y, m+1, 0)`) | |

**Bare call = current calendar month.** Confirmed by the payload's own `coverage`
echo, which came back `2026-08-01 → 2026-08-31` with no params sent.

**They narrow server-side — this is the answer to "what can a CLI do about 2.7 MB":**
```bash
for r in "from=2026-08-01&to=2026-08-31" "from=2026-08-01&to=2026-08-05" "from=2026-03-01&to=2026-08-31"; do
  curl -s -H "Authorization: Bearer $T" \
    "https://ecom.jivo.in/api/platform/blinkit/blinkit-campaigns-optimization?$r" -o t.json \
    -w '%{http_code} %{size_download} ' ; \
  jq -c '{coverage,pb:(.productBooster|length),bf:(.brandFund|length),ra:(.recommendationAds|length)}' t.json
done
# 200 2747172  coverage 2026-08-01..2026-08-31  pb 12800  bf  6782  ra 1058
# 200  742811  coverage 2026-08-01..2026-08-05  pb  3526  bf  1591  ra  295
# 200 9955787  coverage 2026-03-01..2026-08-31  pb 35511  bf 46711  ra 2250
```
Timings on the same box: 0.42 s / 0.74 s / 1.34 s total, TTFB 0.25 / 0.48 / 1.02 s.
A 6-month pull is **9.96 MB**. There is no page/limit param and no server-side
section selector — narrowing is by date only.

## 3. `blinkit-sale-target` — 3 params (+1 cache bypass), all optional

```bash
grep -oE 'L=\(0,y.useMemo\)\(\(\)=>\{let e=\{\}.{500}' $BUNDLE/PlatformBlinkitSaleTargetDashboard-CwyBd7yW.js
# L = useMemo(() => { let e = {};
#       r && (e.date = r);
#       m && (e.compare_date = m);
#       D && (e.close_months = D.join(`,`) || `none`);
#       return e }, [r, m, D])
grep -oE 'queryFn:\(\)=>.{150}' $BUNDLE/PlatformBlinkitSaleTargetDashboard-CwyBd7yW.js
# ... d.get(x, L) ...   and the refresh button: d.get(x, {...L, nocache: 1})
grep -oE 'type:`date`.{300}' $BUNDLE/PlatformBlinkitSaleTargetDashboard-CwyBd7yW.js
# <input type=date value=V max={max_date} ...>   (no min)
```

| param | type | required | source / legal values | notes |
|---|---|---|---|---|
| `platform` (path) | string | yes, **and enforced** | `blinkit` only | non-blinkit → HTTP 400 `["Sale & Target is available only for Blinkit."]` |
| `date` | `YYYY-MM-DD` | no | date picker, `max = response.max_date`, no min | this is the **as-on cutoff**: it drives `month`/`year`/`month_label`, MTD `done_ltr`, `elapsed_days`, `editable`, AND which daily row is shown |
| `compare_date` | `YYYY-MM-DD` | no | second date picker, same `max`; UI auto-defaults it to `date − 1 day` | the "Compare with" daily column |
| `close_months` | comma-joined `YYYY-MM` | no | keys from the response's own `targets.available_close_months[].key` (12 today: `2026-07` … `2025-08`), **or the literal `none`** | `none` is emitted by the UI when the multiselect is cleared (`D.join(',') || 'none'`) |
| `nocache` | `1` | no | the refresh button only (`{...L, nocache: 1}`), tooltip *"Re-read the latest data, skipping the server cache"* | verified 200, same 9,626-byte body |

All verified live:
```bash
curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target?close_months=2026-07,2026-06' \
  | jq -c '{cm:[.targets.close_months[].key],gt_closes:(.targets.grand_total.closes|keys)}'
# {"cm":["2026-07","2026-06"],"gt_closes":["2026-06","2026-07"]}

curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target?close_months=none' \
  | jq -c '{cm:[.targets.close_months[].key],gt_closes:.targets.grand_total.closes,growth:.targets.grand_total.growth_pct,prev:.targets.prev_month_label}'
# {"cm":[],"gt_closes":{},"growth":null,"prev":null}

curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target?date=2026-08-15&compare_date=2026-08-14' \
  | jq -c '{as_on,compare_date,max_date,elapsed_days,gt_done:.targets.grand_total.done_ltr}'
# {"as_on":"2026-08-15","compare_date":"2026-08-14","max_date":"2026-08-21","elapsed_days":15,"gt_done":58671}
#   (vs done 80778 / elapsed 21 on the bare call — `date` really is an MTD cutoff)

curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target?date=2026-07-31' \
  | jq -c '{month,month_label,elapsed_days,editable,target:.targets.grand_total.target_ltr,done:.targets.grand_total.done_ltr,ach:.targets.grand_total.achieved_pct,cm:[.targets.close_months[].key],prev:.targets.prev_month_label}'
# {"month":7,"month_label":"Jul-26","elapsed_days":31,"editable":false,"target":null,"done":115000,
#  "ach":null,"cm":["2026-06","2026-05","2026-04","2026-03","2026-02","2026-01"],"prev":"Jun"}

curl -s -o /dev/null -w '%{http_code} %{size_download}\n' -H "Authorization: Bearer $T" \
  'https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target?nocache=1'
# 200 9626

curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/zepto/blinkit-sale-target'
# ["Sale & Target is available only for Blinkit."]   (HTTP 400)
```
Note from the last one: moving `date` into a closed month flips `editable` to
`false`, drops that month out of `close_months`, and can leave `target_ltr` /
`achieved_pct` as `null` (no target was ever saved for Jul-26).
The UI itself resets the close-months selection whenever `date` crosses a month
boundary (`t.slice(0,7) !== V.slice(0,7) && O(null)`), so a CLI should not carry
`--close-months` across a `--date` change without warning.

## 4. `amazon-po/sku-pendency/summary` — ZERO parameters

The API client method takes no arguments at all:
```bash
grep -oE '.{400}amazonSkuPendency.{500}' $BUNDLE/api-iSyJGyvG.js
# amazonSkuPendency:        (e={}) => X(`/api/reports/amazon-po/sku-pendency`, e),
# amazonSkuPendencyOptions: ()     => X(`/api/reports/amazon-po/sku-pendency/filter-options`),
# amazonSkuPendencySummary: ()     => X(`/api/reports/amazon-po/sku-pendency/summary`),
```
Note the contrast on that one line: the sibling row report takes a params object;
the summary is a **zero-arg** lambda. Verified: it ignores even the filter names
its sibling honours, returning a byte-identical body.

```bash
for q in "" "?fulfillment_center=DED5" "?channel=CORE"; do
  curl -s -H "Authorization: Bearer $T" \
    "https://ecom.jivo.in/api/reports/amazon-po/sku-pendency/summary$q" -o s.json -w '%{http_code} %{size_download} '
  jq -c '{lines:.total.lines,req:.total.requested_units,n_fc:(.by_fc|length),n_ch:(.by_channel|length)}' s.json
done
# 200 15254 {"lines":496,"req":252536,"n_fc":11,"n_ch":4}
# 200 15254 {"lines":496,"req":252536,"n_fc":11,"n_ch":4}
# 200 15254 {"lines":496,"req":252536,"n_fc":11,"n_ch":4}
```
(Both values used are observed: `DED5` from this endpoint's own `by_fc[].fc`,
`CORE` from its own `by_channel[].channel`; the param names come from
`SPDashboard`'s `onOpen` handlers. No unobserved value was sent.)

**A CLI must expose no flags on this command.** Publishing `--fulfillment-center`
here would silently lie: it returns the unfiltered total.

---

# PART C — `overall-pendency` vs the per-platform `pendency-dashboard`

**Verdict: SAME METRIC, DIFFERENT GRAIN AND WIDER PLATFORM REACH.
`overall-pendency` does not supersede `platform pendency` — it is the group-level
roll-up of the identical numbers, plus Amazon, minus the per-platform cuts.**

## The volume numbers agree EXACTLY, on all 7 platforms the old route serves

```bash
jq -r '.available_platforms[].slug' op-bare.json > slugs.txt
while read s; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/overall-pendency?platforms=$s" \
    | jq -r --arg s "$s" '"\($s)\tOP\topen_u=\(.totals.open_units)\tpend_u=\(.totals.pending_units)\tpend_l=\(.totals.pending_ltrs)\topen_pos=\(.totals.open_pos)\trows=\(.totals.rows)"'
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/$s/pendency-dashboard?scope=all" \
    | jq -c '.totals // .'
done < slugs.txt
```

| platform | `overall-pendency` pending_units / pending_ltrs / open_pos / rows | `pendency-dashboard?scope=all` same four | agree? |
|---|---|---|---|
| amazon | 200,064 / 443,598.8 / 56 / 496 | HTTP 400 `["Pendency dashboard is not yet enabled for platform 'amazon'."]` | n/a |
| swiggy | 350,601 / 380,218.0 / 223 / 1270 | 350,601 / 380,218.0 / 223 / 1270 | **exact** |
| zepto | 92,944 / 88,930.4 / 68 / 301 | 92,944 / 88,930.4 / 68 / 301 | **exact** |
| blinkit | 25,188 / 33,728.0 / 114 / 447 | 25,188 / 33,728.0 / 114 / 447 | **exact** |
| bigbasket | 53,816 / 63,600.0 / 13 / 150 | 53,816 / 63,600.0 / 13 / 150 | **exact** |
| flipkart_grocery | 41,564 / 41,564.0 / 18 / 26 | 41,564 / 41,564.0 / 18 / 26 | **exact** |
| citymall | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | **exact** |
| zomato | 4,174 / 8,470.0 / 7 / 26 | 4,174 / 8,470.0 / 7 / 26 | **exact** |

And the 8 per-platform pulls of `overall-pendency` sum precisely to the unfiltered
call: pending_units 768,351 ✓, open_pos 499 ✓, rows 2,716 ✓ (groups do **not** sum:
152 vs 81, because a product appears on several platforms).

## Where they DISAGREE: money, by exactly 5%

`overall-pendency` publishes `pending_value`; `pendency-dashboard` publishes
`order_value` on each `by_sku` / `by_po` / `by_city` / `by_warehouse` /
`by_distributor` row and no value at all in `totals`. **These are not the same
money.**

```bash
for s in blinkit zepto swiggy bigbasket zomato flipkart_grocery; do
  pd=$(curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/$s/pendency-dashboard?scope=all" | jq '[.by_sku[].order_value]|add')
  op=$(curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/overall-pendency?platforms=$s" | jq '.totals.pending_value')
  python3 -c "print('$s', 'order_value_sum=$pd', 'pending_value=$op', 'ratio=%.6f'%(float('$op')/float('$pd')))"
done
```

| platform | Σ `by_sku[].order_value` | `overall-pendency.pending_value` | ratio |
|---|---|---|---|
| blinkit | 8,522,754.12 | 8,948,890.258 | 1.050000 |
| zepto | 21,071,414.84 | 22,124,985.582 | 1.050000 |
| swiggy | 68,168,704.79 | 71,578,101.9495 | 1.050014 |
| bigbasket | 11,686,658.84 | 12,280,491.30 | 1.050813 |
| zomato | 2,573,347.40 | 2,702,013.9325 | 1.050000 |
| flipkart_grocery | 7,405,599.05 | 7,775,879.00 | 1.050000 |

Also at row level: blinkit MUSTARD 1L `order_value` 1,202,282.20 →
`pending_value` 1,262,396.31 = exactly ×1.05.

**Business truth to record: `overall-pendency.pending_value` is GST-inclusive;
`pendency-dashboard.*.order_value` is the basic (pre-tax) value.** The 1.05 factor
matches India's 5% GST on edible oil. Two platforms come out marginally above 1.05
(swiggy 1.050014, bigbasket 1.050813) — a mix effect or a per-line rounding, **not
fully explained; flagged NOT VERIFIED as to cause**, but the gap is quantified
(bigbasket is ₹9.5 lakh over a flat 5%, on a ₹1.17 crore base).

A CLI must never present the two as interchangeable, and a group-level
"pendency value" quoted from `overall-pendency` is ~5% higher than the same
number quoted from any platform's pendency screen.

## What each one still uniquely gives you

| | `platform overall-pendency` | `platform pendency` (`{platform}/pendency-dashboard`) |
|---|---|---|
| platforms | **8**, incl. amazon | 7; amazon 400s |
| grain | item / category / sub_category, with a nested per-platform split | `by_po`, `by_sku`, `by_city`, `by_warehouse`, `by_distributor` |
| PO identity | none — no PO numbers at all | `by_po[].po_number`, `po_date`, `po_expiry_date`, `distributor`, `location` |
| date filter | none | `scope=all` \| `from_date`+`to_date`, plus `po_month`/`year`/`defaulted_to_latest` in the response |
| item head filter | yes (`item_head`) | no |
| money | `pending_value`, GST-inclusive | `order_value` per row, pre-tax |
| extras | `by_head[]`, `available_platforms[]` | `format`, `status_mode`, `defaulted_to_latest` |

Keep both. Neither is redundant.

## Side finding — the shipped spec's platform enum for `platform pendency` is STALE

`~/jivo-cli/ecom-cli/spec.yaml` declares:
> `"This endpoint is served ONLY for: blinkit, zepto, swiggy, bigbasket"`,
> `enum: [blinkit, zepto, swiggy, bigbasket]`

The app's own gate set is **seven**, and all seven return 200 today:
```bash
grep -oE 'S=new Set\(\[[^]]{0,200}\]\)' $BUNDLE/PlatformPendencyDashboard-WE4i01HO.js
# S=new Set([`zepto`,`swiggy`,`blinkit`,`bigbasket`,`flipkart_grocery`,`citymall`,`zomato`])
```
`flipkart_grocery`, `citymall` and `zomato` should be added to that enum this run
(see the table above — all three returned real `totals`). Not a rename; an enum
widening on an existing command. Also worth carrying into the spec: this endpoint
returns a `scope` param the UI always sends as `all` when no range is picked, which
is already documented, and `from_date`/`to_date` as a pair, also already documented.

---

# PART D — Traps, ranked by how much money a wrong reading costs

### T-1 · `overall-pendency.open_units` means ORDERED, not OPEN
`open_units` is the originally-requested quantity; `pending_units` is what is
actually still owed. They are identical on all 7 q-commerce platforms — so the
error is invisible — and diverge **only on Amazon**, which is the largest single
line in the book:

```
amazon            open_u=252536  pend_u=200064   <-- 26% apart
swiggy            open_u=350601  pend_u=350601
zepto             open_u= 92944  pend_u= 92944
blinkit           open_u= 25188  pend_u= 25188
bigbasket         open_u= 53816  pend_u= 53816
flipkart_grocery  open_u= 41564  pend_u= 41564
citymall          open_u=     0  pend_u=     0
zomato            open_u=  4174  pend_u=  4174
```
Cross-checked against the Amazon report: `overall-pendency` amazon `open_units`
252,536 **=** `sku-pendency/summary.total.requested_units` 252,536, and
`pending_units` 200,064 **=** 252,536 − 52,472 (`received_units`). Confirmed:
`open_*` = requested, `pending_*` = requested − received.
A CLI must label `open_units` "Ordered (PO) units" and default any "pendency"
figure to `pending_*`.

### T-2 · `pending_value` is GST-inclusive; `order_value` is not (5%)
Quantified in Part C. Same book, two numbers, 5% apart.

### T-3 · `item_head: "MIXED"` is output-only
When `group_by` is `category` or `sub_category`, a group can span heads and the row
reports `item_head: "MIXED"`. The UI never shows it (the Item Head cell is rendered
only under `k === 'item'`), so it exists purely in the payload — and it is
**rejected as a filter value** (HTTP 400, Part B). A CLI table renderer will show
it; a CLI flag enum must not accept it.
```bash
curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/platform/overall-pendency?group_by=category' \
  | jq -c '[.rows[].item_head]|unique'
# ["COMMODITY","MIXED","OTHER","PREMIUM"]
```

### T-4 · `open_pos` is a distinct-PO count and is NOT summable
```bash
jq '{totals_open_pos:.totals.open_pos, sum_rows_open_pos:([.rows[].open_pos]|add),
     totals_pending_units:.totals.pending_units, sum_rows_pending_units:([.rows[].pending_units]|add)}' op-bare.json
# {"totals_open_pos":499,"sum_rows_open_pos":2716,
#  "totals_pending_units":768351,"sum_rows_pending_units":768351}
```
Units sum correctly. PO counts do not: summing `rows[].open_pos` gives 2,716 (the
line count) because one PO carries many items. `by_head[].open_pos` sums to 866,
also ≠ 499. Only `totals.open_pos` is the true distinct-PO count. Any CLI footer
that totals a column must exclude `open_pos`.

### T-5 · `blinkit-campaigns-optimization` ignores its own `{platform}` segment
Byte-identical payload for `blinkit` and `zepto` (md5 match, Part A §2). The CLI
must pin the segment, not accept the standard 10-slug enum.

### T-6 · `growth_pct` is whatever month YOU asked for
The close-months multiselect tooltip says it outright: *"Pick which closed months
appear as columns. Growth is measured from the newest one."* So the same underlying
month yields wildly different "growth":
```bash
for cm in 2026-07 2026-02 none; do
  curl -s -H "Authorization: Bearer $T" \
    "https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target?close_months=$cm" \
    | jq -c '{gt_growth:.targets.grand_total.growth_pct,gt_proj:.targets.grand_total.projection_ltr,gt_closes:.targets.grand_total.closes,prev:.targets.prev_month_label}'
done
# 2026-07 -> growth 0.03690  proj 119243.71  closes {"2026-07":115000}  prev "Jul"   ->  +4%
# 2026-02 -> growth 0.92864  proj 119243.71  closes {"2026-02": 61828}  prev "Feb"   -> +93%
# none    -> growth null     proj 119243.71  closes {}                  prev null
```
Formula (verified on grand total, both sections and a row): `growth_pct =
projection_ltr ÷ closes[newest selected key] − 1`. Grand total:
119,243.714/115,000 − 1 = 0.036902 ✓. PREMIUM section: 58,582.619/58,341 − 1 =
0.004141 ✓. Row CANOLA 1L: 13,499.762/13,859 − 1 = −0.025921 ✓.
**A CLI must print `prev_month_label` next to `growth_pct` or the number is
meaningless**, and must handle `null` when `close_months=none`.

### T-7 · The word "open" means three different things across these two products
Cross-checked with the row report, whose dataset-wide `totals` block is returned
alongside page 0:
```bash
curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/reports/amazon-po/sku-pendency' -o sp-rows.json
jq '{count,page,page_size,totals}' sp-rows.json
curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/reports/amazon-po/sku-pendency/summary' -o sp-summary.json
jq '.total' sp-summary.json
```

| quantity | value | definition |
|---|---|---|
| `overall-pendency` amazon `open_units` | 252,536 | ORDERED (= summary `requested_units`) |
| `overall-pendency` amazon `pending_units` | 200,064 | requested − received |
| `summary.total.remaining_units` | 192,812 | accepted − received, over **all 496** lines |
| **`summary.total.open_units`** | **170,071** | accepted − received, over the **376 outstanding** lines only — i.e. it equals the row report's `remaining_qty` total, *not* its `open_qty` total |
| row report `totals.remaining_qty` | 170,071 | ← exact match to the line above |
| row report `totals.open_qty` | 156,234 | *"Ordered QTY less Invoiced QTY … Floored at zero"* — **no field in the summary equals this** |

Same for litres: `summary.total.open_ltrs` 373,170.6 == row report
`totals.remaining_ltrs` 373,170.6, while `summary.total.remaining_ltrs` is
429,887.6 and the row report's own `open_ltrs` total is 357,851.6.

So: **the summary's `open_units`/`open_ltrs` are a different metric from the row
report's identically-named `open_qty`/`open_ltrs` columns.** The summary's tile is
labelled "Open book" and its tooltip explains the outstanding-lines restriction;
the row report's tooltip explains the ordered-minus-invoiced definition. Both
names are `open_*`. A CLI must not let an operator diff one against the other.

Column tooltips, verbatim from the row report's column spec:
```bash
grep -oE '\{key:`[a-z_0-9]+`,label:`[^`]+`[^}]{0,400}\}' $BUNDLE/SkuPoPendency-mBzq5vij.js
# open_qty  -> "Ordered QTY less Invoiced QTY — units still to be invoiced, on every row,
#               not only part-invoiced ones. Floored at zero: a line billed beyond what it
#               ordered is over-invoiced..."
# open_ltrs -> "Ordered LTR less Invoiced LTR — the two columns to the left, subtracted."
```

### T-7b · "Remaining QTY" is the label on TWO different fields
In the same row-report column spec, `remaining_qty` → label **"Remaining Qty"**
(*"Accepted units not yet received by Amazon"*) and `invoiced_short_qty` → label
**"Remaining QTY"** (*"Accepted units not yet on a SAP invoice. Only set where the
line is part-invoiced."*). They are shown in different variants (`primaryOnly` /
`plannerOnly`) so the UI never collides, but a CLI that renders by label will.
Same duplication for `remaining_ltrs` / `invoiced_short_ltrs` ("Remaining LTR").

### T-8 · Litres are NOT derivable from the item label, and `ltrs ÷ units` is not the pack size
`overall-pendency` row "MUSTARD 1L" reports amazon `open_units` 42,720 but
`open_ltrs` 52,720 — impossible for a 1 L pack. The Amazon row report explains it:
```bash
jq '[.results[]|select(.item=="MUSTARD 1L")]|.[0]' sp-rows.json
# {"sku_code":"B09HKPSS96","item":"MUSTARD 1L","sap_sku_code":"FG0000275",
#  "per_liter":2.0,"has_stated_litre":true, "requested_qty":10000,"total_order_liters":20000, ...}
```
`per_liter: 2.0` on an ASIN filed under the "MUSTARD 1L" item — a 2-pack listing.
Litres come from a per-ASIN master, not from the item name. Never infer volume
from `label`.

### T-9 · The two products disagree on litres for the "OTHER" head, by exactly 148.2 L
```
overall-pendency amazon open_ltrs           561,043.8
summary.total.order_ltrs                    560,895.6
                                    diff =      148.2
overall-pendency amazon by_head OTHER open_ltrs = 148.2   (exact match)
```
Units agree (both 252,536, OTHER contributing 335). Mechanism confirmed: the Amazon
report zeroes litres for lines the master has no stated litre value for, and counts
them in `blank_litre_lines` (= 9 today; amazon OTHER `open_pos` = 9 as well):
```bash
jq '[.results[]|select(.has_stated_litre==false)]|{n:length,sample:(.[0]|{sku_code,item,item_head,per_liter,requested_qty,total_order_liters})}' sp-rows.json
# {"n":1,"sample":{"sku_code":"B0F9YVR47L","item":"PUNJABI JEERA 160ML","item_head":"OTHER",
#                  "per_liter":0.16,"requested_qty":10,"total_order_liters":0}}
```
`per_liter` is populated (0.16) yet `total_order_liters` is 0 — the Amazon report
honours `has_stated_litre`, `overall-pendency` does not. The gap is 0.026% of
Amazon litres; the 9-line / 9-PO coincidence is strong but only **page 0 of the row
report was inspected**, so the full line-by-line attribution is **NOT VERIFIED**.

### T-10 · `_pct` suffix means two different scales in the same API
| endpoint | field | example | scale |
|---|---|---|---|
| `blinkit-sale-target` | `growth_pct`, `achieved_pct` | 0.0369, 0.4488 | **fraction 0–1** (UI multiplies by 100) |
| `sku-pendency/summary` | `fill_rate_pct`, `acceptance_rate_pct`, `invoiced_share_pct`, `uninvoiced_share_pct`, `cancel_rate_pct`, `short_invoice_rate_pct` | 21.39, 97.13, 39.26, 60.74, 0.0, 7.58 | **percent 0–100** |
A CLI must format these per-endpoint, not per-suffix.

### T-11 · `overall-pendency` can return an error string inside a 200
The UI reads `z.error` and renders it as a banner (`U = R.error?.message || z.error || ''`).
Not observed today, but a CLI must check the body's `error` key before trusting
`rows`.

### T-12 · Dead / always-empty fields to not build UI around
- `overall-pendency.max_date` — `null` in every response observed today (~20 calls, all param combinations). Never read by the UI.
- `blinkit-campaigns-optimization.momHistory` — `[]` in every call; plumbed into the derived model and **rendered nowhere**.
- `blinkit-campaigns-optimization.mtdSpend` — `[]` in every call; its panel is `.length > 0`-gated. Shape **NOT VERIFIED** live.
- `overall-pendency.undated_rows` — `0` in every response observed.

---

# PART E — Proposed command names

Naming derived from the shipped spec, read directly:
```bash
python3 - <<'EOF'
import yaml
d=yaml.safe_load(open('/root/jivo-cli/ecom-cli/spec.yaml'))
for res in ('platform','reports'):
    for name,e in d['resources'][res]['endpoints'].items():
        print(f"{res:9s} {name:38s} {e['method']:5s} {e['path']}")
EOF
```

Conventions observed in the shipped 46 `platform` + 15 `reports` commands:
1. Group-level `platform` routes (no `{platform}` segment) take the plain path
   tail: `ads-summary`, `meta`, `call-center-targets`, `primary-overview-total`,
   `primary-summary-version`, `month-targets-dashboard`.
2. Platform-branded per-platform routes keep the full tail verbatim:
   `blinkit-ads-dashboard`, `blinkit-brandfund-dashboard`, `blinkit-summary-report`,
   `swiggy-brandfund-dashboard`, `flipkart-fsn-dashboard`.
3. `reports` flattens the sub-path with hyphens: `amazon-po-sku-pendency`,
   `amazon-po-sku-pendency-filter-options`, `amazon-po-summary`, `appointment-summary`.

| endpoint | proposed command | why |
|---|---|---|
| `GET /api/platform/overall-pendency` | **`platform overall-pendency`** | rule 1. No collision with the existing `platform pendency`. |
| `GET /api/platform/{platform}/blinkit-sale-target` | **`platform blinkit-sale-target`** | rule 2, exactly like its three `blinkit-*` siblings. |
| `GET /api/platform/{platform}/blinkit-campaigns-optimization` | **`platform blinkit-campaigns-optimization`** | rule 2. |
| `GET /api/reports/amazon-po/sku-pendency/summary` | **`reports amazon-po-sku-pendency-summary`** | rule 3; mirrors the shipped `amazon-po-sku-pendency-filter-options`. |

Nothing existing is renamed. Excluded by the read-only rule:
`POST /api/platform/{platform}/blinkit-sale-target/set-target`.

## CLI shape notes to carry into the spec

- **`platform overall-pendency`** — flags `--platforms` (repeatable/CSV, enum = the
  8 slugs), `--item-head` (enum `ALL|PREMIUM|COMMODITY|OTHER`, server-validated),
  `--group-by` (enum `item|category|sub_category`). All optional. Default table
  should lead with `pending_*`, not `open_*` (T-1), and must not total `open_pos` (T-4).
- **`platform blinkit-campaigns-optimization`** — **mark heavy**: 2.7 MB default,
  up to ~10 MB over the UI's 6-month window. Recommend
  `--section skuMaster|brandFund|productBooster|recommendationAds|momHistory|mtdSpend|coverage`
  as a **client-side** selector (the server has none) plus `--from`/`--to`
  (`YYYY-MM-DD`) which **do** narrow server-side. Default to `--section coverage`
  for a cheap "what's in there" probe, and pin the path slug to `blinkit` (T-5).
- **`platform blinkit-sale-target`** — flags `--date`, `--compare-date`
  (`YYYY-MM-DD`), `--close-months` (CSV of `YYYY-MM` keys, or the literal `none`),
  `--nocache`. Path slug pinned to `blinkit` (server enforces). Print
  `prev_month_label` beside `growth_pct` (T-6); render `*_pct` as ×100 (T-10).
- **`reports amazon-po-sku-pendency-summary`** — **no flags at all** (T: Part B §4).
  Three output sections (`total`, `by_fc`, `by_channel`) sharing one 46-metric
  schema; a `--section total|by-fc|by-channel` client-side selector is reasonable.
  Render `*_pct` as-is (already 0–100). Tolerate `null` in `by_channel` (the `"-"`
  channel).

---

# Verification ledger

| claim | verified how | status |
|---|---|---|
| all 4 endpoints live 200 | direct GETs, this run | VERIFIED |
| `overall-pendency` params + enums | UI memo `L`, arrays `S`/`C`, plus server's own 400 message | VERIFIED (server-stated) |
| `overall-pendency` ≡ `pendency-dashboard` volumes, 7 platforms | side-by-side GETs, 4 measures each | VERIFIED exact |
| `pending_value` = 1.05 × `order_value` | 6 platforms + 1 row-level check | VERIFIED; the >1.05 residual on swiggy/bigbasket **NOT EXPLAINED** |
| `blinkit-campaigns-optimization` ignores `{platform}` | md5 of two full payloads | VERIFIED |
| `from`/`to` narrow server-side | 3 windows, byte counts + `coverage` echo | VERIFIED |
| `blinkit-sale-target` params `date`/`compare_date`/`close_months`/`nocache` | 6 live calls incl. `none` and a prior month | VERIFIED |
| `growth_pct` = projection ÷ newest selected close − 1 | arithmetic on grand total, section total, and one row | VERIFIED |
| summary takes zero params | zero-arg lambda in api chunk + 3 byte-identical GETs | VERIFIED |
| summary `open_*` ≠ row-report `open_*` | exact equality to `remaining_*` instead | VERIFIED |
| 148.2 L OTHER-head litre gap | arithmetic + `has_stated_litre:false` row | mechanism VERIFIED, full line attribution **NOT VERIFIED** (page 0 only, 1 of 9 blank-litre lines seen) |
| `mtdSpend` row shape | UI column spec only; array empty in every live call | **NOT VERIFIED** |
| `momHistory` purpose | absent from all render paths | dead in this build; purpose **NOT VERIFIED** |
| `max_date` on `overall-pendency` | `null` in ~20 responses, unread by UI | believed dead; **cannot prove** it is never populated |
| shipped `platform pendency` enum is too narrow | app's gate set + 7 live 200s | VERIFIED |

Read-only compliance: every request in this study is a GET. No parameter value was
sent that was not either present in a live payload or written in the app's own
source (dates were taken from the app's own picker bounds: `max_date` for
sale-target, `firstOfMonth`/`min`/`max` for campaigns-optimization). The
`set-target` POST was never called.
