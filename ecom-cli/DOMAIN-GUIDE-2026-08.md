# jivo-ecom-pp-cli — what each domain means, and what will trip you up

Written 2026-08-03 from a live re-survey of `ecom.jivo.in`. Every claim here
was either read out of a live response or read out of the app's own source; the
few that are neither are labelled **unverified** rather than smoothed over.

`ecom.jivo.in` is JIVO's e-commerce and quick-commerce operations dashboard:
sales, inventory, advertising and shipments across Amazon, Blinkit, Swiggy,
BigBasket, Flipkart, Zepto, JioMart, Citymall and Zomato. This CLI is a
**read-only** window onto the same API the dashboard uses.

---

## Read this first — five things that cause wrong answers

**1. The `sap` domain is JIVO MART, not Oil and not the group.**
Verified against HANA row counts: `sap items` 1,349 = Mart's `OITM` (Oil has
2,270, Beverages 2,192); `sap distributors` 1,247 = Mart's `OCRD` with
`CardType='S'`; `sap sales-invoices` 25,157 = Mart's `OINV`;
`sap inventory-overview` 47,908 = Mart's `OITW`. Only
`sap sales-analysis --source oil` reaches Oil. Beverages is unreachable
entirely — no parameter, no endpoint. **An ecom SAP figure read as a group
total is wrong.**

**2. You cannot compute turnover from this CLI.**
JIVO's settled definition is invoices net of GST (`DocTotal − VatSum`) minus
credit notes, excluding cancelled. This domain has **no credit-note endpoint at
all** (Mart's books hold 4,444 `ORIN` documents that are invisible here), and
`sap sales-invoices` returns headers **including cancelled**. `DocTotal` is
GST-inclusive — always subtract `VatSum`, never divide by 1.05: the rate is 5%
on 87.7% of Mart invoices but 12% on 251, 18% on 236 (₹14.39 Cr), zero on 63,
and blended on 2,316. For turnover, use SAP directly.

**3. `sap distributors` is the vendor master.**
`CardType='S'` — ad agencies and suppliers. The actual distributors are on the
customer side, in `sap platform-distributors`. An empty result from
`sap distributor-invoices VENDA…` is a category error, not "no business".

**4. Primary is JIVO → platform; secondary is platform → consumer.**
And the naming does not help you: **`platform month-targets` is the SECONDARY
target set** (`"type": "B2C"` in the payload) while `platform primary-month-targets`
is primary (`"type": "prim"`, `source: master_po`). Confirmed from payload
fields, not names.

**5. Quantities are in pieces — single bottles, never cartons.**
Confirmed from the data: BigBasket rows give CANOLA 1L qty 317 / 317 litres and
CANOLA 5L qty 23 / 115 litres, so the ratios land exactly on pack size. The
"20 PCS" in an item name is carton configuration; multiplying by it inflates
volume roughly 20×. Every endpoint ships a litre field alongside — take tonnes
from **litres × 0.91**, never from unit counts.

---

## The domains

### `dashboard` — cross-platform analytics (28 commands)

Everything aggregated **across all platforms**. Most commands take an optional
`--platform` to narrow; **omitting it means all platforms**, so a total here is
a company-wide total.

The `realise-*` family is about **realisation** — what JIVO actually nets per
litre after platform deductions. Be careful: the ₹/L figure is **not in the
API**. The browser computes `(value − commission − ads_spent − brand_fund) / ltrs`,
and the UI's "Premium Realise ₹/L" tile uses a *different* formula with no
deductions at all. Three endpoints give three different August numbers. Quote
the components, not a derived rate, unless you know which formula you want.
GST treatment of these figures could **not** be verified.

**Traps**

- **`dashboard expiry-alerts --table` takes a TABLE name, not a platform.** A
  platform slug returns `200 {"alerts": []}` — a silent false negative. Valid
  names: `tables counts`.
- **`total_units` on the expiry endpoints is rupees — except on Amazon, where
  it is units.** The SPA labels the same field "Order value" for everyone and
  "Requested units" for Amazon. Summing that column across platforms adds
  rupees to bottles.
- **`state-sales`: `value` is not rupees.** It mirrors whatever `--metric` is
  set to (`litres | value | units`). `pct_mapped` is the share attributable to
  a state, so map totals understate company sales.
- **`primary-po-litres` silently drops Amazon.** The 200 response carries
  `errors: [{"source":"amazon_po","error":"name 'month_num' is not defined"}]`
  — a backend `NameError` — and Amazon is simply absent from `platforms[]`.
  Check `errors[]` before trusting the total. (In the August sample the five
  reported platforms already sum to the group total, so the omitted amount may
  be zero — but that is a coincidence of the month, not a guarantee.)
- `fulfilment-health`'s window **ends seven days back**, and `fill_rate +
  miss_rate ≠ 100`.
- `category-breakdown` and `category-trend` disagree by 21.0 L on OLIVE for
  Aug-26 despite both reporting `source: "primary"`. Unexplained; olive is
  high-value, so reconcile before quoting.
- `state-sales/detail/cities` and `.../city-skus` return **200 with zero rows**
  when called bare. That is a data answer (no state scoped), not a broken
  endpoint — pass `--state`.
- Large: `penetration-report` 2,492 rows, `state-sales/export` 1,779 rows at
  349 KB. Filter first.

### `platform` — per-platform dashboards (46 commands)

Everything scoped to one platform via `--platform`. The ten valid slugs are the
`platforms` array on `account me`: amazon, bigbasket, blinkit, citymall,
flipkart, flipkart_grocery, jiomart, swiggy, zepto, zomato.

**The thing to know: 17 of these commands are served for specific platforms
only**, and the CLI now refuses a wrong pairing locally rather than sending it.

| command | served for |
|---|---|
| `bigbasket-ads-dashboard`, `bigbasket-ads-daily-dashboard` | bigbasket |
| `blinkit-ads-dashboard`, `blinkit-brandfund-dashboard`, `blinkit-summary-report` | blinkit |
| `flipkart-ads-dashboard`, `flipkart-fsn-dashboard` | flipkart |
| `swiggy-ads-dashboard`, `swiggy-ads-daily-dashboard`, `swiggy-brandfund-dashboard` | swiggy |
| `zepto-ads-dashboard`, `zepto-ads-daily-dashboard`, `zepto-brandfund-dashboard` | zepto |
| `landing-rate`, `landing-rate-skus` | blinkit, zepto, swiggy, bigbasket, flipkart_grocery |
| `monthly-sales-explorer` | bigbasket, blinkit, swiggy, zepto |
| `pendency` | blinkit, zepto, swiggy, bigbasket |
| `region-doh` | **swiggy, zepto only** |

`region-doh` is the odd one: it returns a bare 404 for other platforms rather
than the clear 400 message the others use, so it looks dead when it is not.

**Traps**

- **`platform meta` is the Meta (Facebook/Instagram) ads dashboard** —
  campaigns, reach, CPC, CPM, spend. It is not platform metadata, whatever the
  old description said. There is no endpoint that returns the slug list; use
  `account me`.
- `month-targets` = secondary, `primary-month-targets` = primary (see the top
  of this document).
- ROAS/ACOS are row-averages on the quick-commerce platforms but a totals ratio
  on Amazon. The exact formula is **unverified**.
- `jiomart` is a valid slug but marked hidden in the app, and
  `platform stats --platform jiomart` returns 404 while citymall and flipkart
  return 200.

### `sap` — the SAP HANA read layer (16 commands)

Read the five points at the top of this document before using anything here.
Scale: `inventory-overview` 47,908 rows, `sales-invoices` 25,157, `items`
1,349, `distributors` 1,247 — filter before fetching.

**Traps**

- `sales-analysis --source oil` defaults to `cardname = JIVO MART PVT LTD`, so
  the Oil view measures Oil→Mart **intercompany** transfers, which JIVO excludes
  from sales (correction C-0005).
- **Use `--item-head` to segment PREMIUM / COMMODITY / OTHERS** (correction
  C-0003 — never match on item names). It is new in v0.2.0.
- For headline totals pass `--aggregate item_head --page-size 1` and read the
  response's `aggregate[]` block: the **server** aggregates. Paging to
  exhaustion is unnecessary and the 50-row default silently truncates.
- `inventory-overview --status`: empty = all, `Y` = active, `N` = frozen. The
  dashboard sends `Y`, so a bare CLI call returns **more** rows than the UI —
  it includes frozen items.
- `sap sales-invoice-lines` is **removed**: it 500s on every invoice
  (`invalid column name: T1.UnitMsr`). There is no line-item drill-down until
  the backend is fixed.

### `reports` — Amazon PO and appointment reporting (15 commands)

**Traps**

- **`reports raw --platform` takes UPPERCASE display names with spaces** —
  `BIG BASKET`, `FLIPKART GROCERY`, `CITY MALL` — not the lowercase slugs every
  other command uses.
- `--view` is required on `reports raw` and `reports columns`; a bare call
  returns `400 Unknown report view`. The eleven known values were extracted
  from the SPA and include colon-delimited members (`sap:jm_primary:oil`).
  **Never sent to the live API**, so treat them as strong but unconfirmed.
- `reports live-data` and `live-reports` return **403** for this credential and
  the server does not name the permission required. Their response shapes are
  unverified.
- `reports amazon-po` returns 10,247 rows; `amazon-po-billing` 102 KB. Filter.

### `shipment` — the Amazon Shipment Planner (25 commands)

**Nothing in this domain could be verified.** Every endpoint returns
`403 {"detail":"You do not have access to the Amazon Shipment Planner."}` for
the credential used. The gate is the permission `amazon.shipment_planning.view`,
which this account does not hold despite carrying 144 permissions including
`view_shipment`, `dispatch.view` and `admin.dispatch.manage`.

A 403 proves the endpoint exists and is routed, so all 25 are published — but
**every response shape here is unverified** and is marked so in the spec. Do not
treat this section as confirmed until someone with that permission runs it.

What *is* known, from the SPA's source:

- `truck_size` ∈ `10_ton | 15_ton | custom` (capacities 10,000 / 15,000 L;
  custom defaults to 12,000).
- **The app divides litres by 1,000 and prints "ton".** For oil that overstates
  tonnage by about 9% — the correct factor is × 0.91.
- `warehouse` ∈ `GP-FGM | BH-FGM | GP-FG | BH-EC | ALL`.
- Shipment `status` and `switch_state` are two **independent** state machines
  that both contain `rejected`.
- `sap_available` is on-hand **minus other shipments' reservations**, so it will
  never reconcile against SAP on-hand.
- Every `/api/shipment/` path needs a trailing slash; the rest of the API
  rejects one.

### `upload`, `uploads`, `master`, `notifications`, `chatbot`, `account`

The master data an operator actually queries: `upload master-sheet` (907 rows),
`upload pincode-mapping` (6,565), `upload ads-master` (99), `uploads list` (187
upload jobs), `master products` (907), `master fcs` (19 fulfilment centres),
`notifications list` (91).

**Traps**

- **`master products` and `upload master-sheet` are the same 907 rows** in
  different envelopes. They look interchangeable and are not — different
  columns.
- `row_id` is a **Postgres ctid** (`"(28,55)"`) on master-sheet and ads-master,
  but a plain integer on pincode-mapping.
- The upload log can report three different row counts for one job (e.g. 223
  file rows → 0 inserted → 360 updated), and `main_table_name` is a human
  label, not a table.
- `notifications list` bare returns 91, but the SPA calls it with
  `active_only=true&limit=200` — so the bare count may include resolved
  alerts. The client also catches a **404** there and substitutes an empty
  list, so "no notifications" and "endpoint missing" look identical in the UI.
- `pincode-mapping` is dirty: nulls, `CALICT`/`CALICUT` both present, Calicut
  filed under the Andamans. `master fcs` has `fc_name` and `region` null on all
  19 rows.
- `doh` is **not** `soh ÷ drr` — the observed row's arithmetic does not work.
  No formula is given here because none could be verified.
- `format` means sales channel, so 907 rows ≠ 907 products.

**A quiet bonus:** the current dashboard no longer calls `master products` or
`master fcs` at all — 27 API functions are dead in the UI. They are alive on the
server and this CLI reaches them, so some of this data is now easier to get from
the CLI than from the app.

---

## Safety

This CLI is **read-only** and its MCP surface is read-only permanently. All 151
endpoints are GET. The 46 write endpoints the app uses — uploader CRUD, target
edits, shipment approve/reject/dispatch, and a destructive
`POST /api/upload/delete-by-date` that bulk-deletes a named table over a date
range — are excluded by construction, not by convention: both MCP execution
paths refuse a non-GET method before the client is called, and a test proves it.

---

## Where the evidence lives

- `research/API-FACTS-2026-08.md` — what was established and how
- `research/FINDINGS-FOR-ECOM-TEAM-2026-08.md` — eight defects found, with
  reproductions
- `research/studies/` — the per-domain studies and the adversarial verdicts
  that corrected them
- `research/evidence/` — every live probe response
- `research/scripts/` — the tooling that produced all of it
- `MIGRATION-2026-08.md` — what changed from v0.1.0
