# Domain study — `sap` (JIVO ecom's mirror of SAP Business One)

Bundle: `study/bundles/sap.json` · 17 endpoints · LIVE 13, LIVE_NEEDS_PARAMS 1,
UNPROBED 2, BROKEN_UPSTREAM 1.
Evidence: the bundle's live probes, the SPA bundle in `ecom-rescrape/bundle/`,
and (for the company question and the broken endpoint only) read-only metadata
queries against JIVO's HANA database run 2026-08-03.

---

## 0. THE ANSWER TO THE COMPANY QUESTION — read this before any number leaves here

**This mirror is Jivo Mart's books by default, not Oil's, and it can never see
Beverages.**

Concretely:

| | |
|---|---|
| **Default company for every endpoint in this domain** | `JIVO_MART_HANADB` (Mart) |
| **Second company, reachable on 4 endpoints only, via `source=oil`** | `JIVO_OIL_HANADB` (Oil) |
| **Beverages (`JIVO_BEVERAGES_HANADB`)** | **not reachable at all — no parameter, no endpoint, nothing** |

The four endpoints that accept `source`: `sap sales-analysis`,
`sap inventory-overview`, `sap inventory-finished-goods`,
`sap inventory-warehouse-comparison`. Every other endpoint in this domain is
Mart-only with no way to switch.

### How I know (verified, not inferred)

1. **The SPA only ever offers two companies.** `PlatformSapDashboard-bUN0KEtA.js`
   defines the picker as `[{value:'mart',label:'Mart'},{value:'oil',label:'Oil'}]`
   and validates the URL parameter as `n === 'oil' || n === 'mart'`. The reports
   domain builds its SAP view name as
   `` sap:${kind}:${jmSource === 'oil' ? 'oil' : 'mart'} `` — same two, no third.
2. **The live payload says so.** `/api/sap/inventory-finished-goods` returned
   `"source": "mart", "sources": ["mart", "oil"]`.
3. **Row-for-row match against live HANA.** Every scale figure in the probes is
   the exact Mart table count, and none of them is Oil's or Beverages':

   | ecom endpoint | rows it reported | `JIVO_MART_HANADB` | Oil | Beverages |
   |---|---|---|---|---|
   | `/api/sap/items` | 1,349 | `OITM` = **1,349** | 2,270 | 2,192 |
   | `/api/sap/distributors` | 1,247 | `OCRD` where `CardType='S'` = **1,247** | — | — |
   | `/api/sap/sales-invoices` | 25,157 | `OINV` = **25,157** | — | — |
   | `/api/sap/inventory-overview` | 47,908 | `OITW` = **47,908** | — | — |

4. **Invoice-level proof.** The three rows in the live `/api/sap/sales-invoices`
   sample exist in Mart and nowhere else. DocEntry 37594 → DocNum 708260104,
   `CUSTA000661` DEL DEEPAK BHARDWAJ, DocTotal 9,640, VatSum 459.0465 — an exact
   match in `JIVO_MART_HANADB.OINV`. Oil has no DocEntry 37594 at all, and Oil's
   DocEntry 37603 is a completely different document (DocNum 724111299,
   DEL RAJU EAST, ₹18,119) — so this is not a coincidence of numbering.

Confidence: **~99%** for the four source-aware endpoints and for the four
endpoints cross-checked by row count. For the remaining Mart-only endpoints
(`distributor-*`, `platform-*`, `stock-by-warehouse`, `sales-invoices/{}`) it is
a strong inference from the same backend connection rather than a per-endpoint
check — I did not verify each one individually.

**What this means for an operator:** a number from this domain is a *Jivo Mart*
number. It is not a JIVO group total, and it is not comparable with an Oil
figure from `sapb1`/`hana-sql`. If somebody asks "what did we sell", this domain
cannot answer it — it can only answer "what did Mart sell", and only partially
(see Trap 4).

---

## 1. What this domain is, in operator language

This is the e-commerce team's window into the accounting system. It reads Jivo
Mart's SAP books directly and answers four kinds of question: *what stock do we
have and where*, *what have we invoiced and to whom*, *who are the parties we
trade with*, and *what stock is sitting with our marketplace distributors*.

The people who open it are the e-commerce planners deciding whether a PO can be
filled, and Accounts staff checking a marketplace distributor's balance or a
month's billing. It is a read-only copy of what SAP already knows — nothing here
originates in the ecom app.

Its blind spot is the thing Accounts cares about most: there is **no credit
note / sales return endpoint anywhere in it**, so JIVO's own definition of
turnover cannot be computed from this domain (Trap 4).

---

## 2. Endpoint table

Command names in **bold** are the shipped v0.1.0 names and must not change.

| command | path | what an operator gets | required params | status |
|---|---|---|---|---|
| **sap distributor-inventory** | `/api/sap/distributor-inventory` | One marketplace distributor's stock, costed FIFO: every price lot (`lot_source`, `lot_date`, `rate`, `remaining_qty`, `lot_value`) per `sap_code`, a `movements` block per item (`opening_qty`, `purchased_qty`, `delivered_qty`, `returned_qty`, `net_qty`, `on_hand_qty`, `short_qty`), and `totals` (`on_hand_qty`, `fifo_value`, `skus`, `layers`, `short_flags`). Also `card_code`, `card_name`, `as_of_month`. | none required, but see Trap 12 — **always pass `card_code`** | LIVE |
| **sap distributor-invoices** | `/api/sap/distributor-invoices/{card_code}` | A/R invoices raised on one party. Probe returned `{"data":[],"count":0,"page":0,"page_size":50}` for a *vendor* code — see Trap 3. | `card_code` in the path | LIVE |
| **sap distributor-orders** | `/api/sap/distributor-orders/{card_code}` | Sales orders for one party. Same empty-for-a-vendor result. | `card_code` in the path | LIVE |
| **sap distributors** | `/api/sap/distributors` | **The Mart vendor master, 1,247 rows** — `CardCode`, `CardName`, `CardType`, `GroupCode`, phones, `Email`, address, `State`, `Currency`, `Balance`, `CreditLine`, `GSTIN`, `Active`, `CreateDate`, `UpdateDate`. Sample rows are `CardType: "S"`, `Active: "N"` service vendors like "10M ANALYTICS" and "360MARCOM SOLUTIONS PRIVATE LIMITED". See Trap 2. | none (paged) | LIVE |
| **sap distributor** | `/api/sap/distributors/{card_code}` | One party in full: the master row plus `addresses[]` (bill-to `AdresType:"B"` / ship-to `"S"`) and `contacts[]` (`Name`, `Tel1`, `Email`, `Position`, `Active`). | `card_code` in the path | LIVE |
| **sap inventory-finished-goods** | `/api/sap/inventory-finished-goods` | Finished-goods stock as a grid: every item (`ItemCode`, `ItemName`, `SubGroup`, `Variety`, `IsLitre`, `SalPackUn`, `Price`) with a `warehouses{}` map of quantities across 13 named warehouses, plus `grand_total` per item, `column_totals` per warehouse, and an overall `grand_total`. `group` was `"FINISHED"`. | none; `source` selects Oil or Mart | LIVE |
| **sap inventory-overview** | `/api/sap/inventory-overview` | Stock per item **per warehouse** — 47,908 rows unfiltered. Each row: `ItemCode`, `ItemName`, `GroupName`, `UOM`, `WhsCode`, `WhsName`, `City`, `OnHand`, `Committed`, `Available`, `OnOrder`, `MinStock`, `MaxStock`, `StockValue`, `IsLitre`, `SalPackUn`, `Litres`. Plus a `summary` (`total_skus`, `total_units_on_hand`, `total_stock_value`, `total_litres_on_hand`, `litre_coverage_pct`, `items_zero_stock`, `items_below_min`) and a `filters` block listing the valid warehouses and groups. | none, but **filter it** — see Trap 9 | LIVE |
| **sap inventory-warehouse-comparison** | `/api/sap/inventory-warehouse-comparison` | One line per warehouse: `WhsCode`, `WhsName`, `Inactive`, `items`, `on_hand`, `stock_value`, `zero_stock`. The fastest "where is our stock" answer — e.g. Bhakharpur Finished INTRANSIT held 13,874 units worth ₹53.57 lakh. | none; `source` selects Oil or Mart | LIVE |
| **sap items** | `/api/sap/items` | The Mart item master, 1,349 rows: `ItemCode`, `ItemName`, `Barcode`, `GroupCode`, `InStock`, `Committed`, `OnOrder`, `Available`, `PurchaseUOM`, `SalesUOM`, `LastPurchasePrice`, `Currency`, `Active`. Company-wide stock, not per warehouse. | none (paged) | LIVE |
| **sap platform-distributors** | `/api/sap/platform-distributors/{platform}` | **The customer side** — the SAP accounts that a marketplace bills through. `CardType: "C"`, with `Chain` and `MainGroup` ("E-COMMERCE"), `Balance`, `CreditLine`, `GSTIN`, `Active`. For `amazon`: AMAZON `CUSTA000873`, AMAZON (B2C -MAY-JULY) `CUSTA000912` (balance ₹34.07 lakh), AMAZON B2C `CUSTA000883`. | `platform` in the path (only `amazon` proven) | LIVE |
| **sap platform-distributor** | `/api/sap/platform-distributors/{platform}/{card_code}` | Detail for one of the above. Response shape **unverified** — never probed. | `platform`, `card_code` | UNPROBED |
| **sap platform-sales-invoices** | `/api/sap/platform-sales-invoices/{platform}` | Invoices for one marketplace. Response shape **unverified** — never probed. | `platform` | UNPROBED |
| **sap sales-analysis** | `/api/sap/sales-analysis` | Sales lines aggregated for a date range, with a `filters` block driving the dashboard's dropdowns. This is the endpoint behind the SAP dashboard's Value / Litre / Quantity views. Shape not captured (the probe stopped at validation). | **`from_date`** — the live 400 says verbatim ``["`from_date` must be YYYY-MM-DD."]`` | LIVE_NEEDS_PARAMS |
| **sap sales-invoices** | `/api/sap/sales-invoices` | Every A/R invoice header in the Mart books — 25,157 rows. `DocEntry`, `DocNum`, `DocDate`, `DocDueDate`, `TaxDate`, `CardCode`, `CardName`, `DocTotal`, `VatSum`, `DiscSum`, `PaidToDate`, `BalanceDue`, `DocStatus`, `CANCELED`, `Comments`, `JrnlMemo`, `SlpCode`, `CreateDate`, `UpdateDate`. | none, but **filter it** | LIVE |
| **sap sales-invoice** | `/api/sap/sales-invoices/{card_code}` | *Not one invoice* — all invoices for one **customer code**. See Trap 14. | `card_code` in the path | LIVE |
| **sap stock-by-warehouse** | `/api/sap/stock-by-warehouse` | `ItemCode`, `ItemName`, `WhsCode`, `OnHand`, `Committed`, `OnOrder`, `Available` — the per-warehouse rows for one item. Called with no item it returns 89 KB of everything. | `item_code` (the SPA always sends it) | LIVE |
| ~~sap sales-invoice-lines~~ | `/api/sap/sales-invoice-lines/{DocEntry}` | **Broken upstream. Excluded.** See §5. | — | BROKEN_UPSTREAM |

---

## 3. Traps

### Trap 1 — Mart, not Oil, and never Beverages *(observed; see §0)*
Covered in full above. The one-line version: **every number here is Jivo Mart's
unless you passed `source=oil`, and Beverages does not exist in this domain.**

### Trap 2 — `sap distributors` is the **vendor** master. It is not a list of distributors. *(observed)*
The 1,247 rows are exactly `JIVO_MART_HANADB.OCRD` where `CardType = 'S'`
(verified count). The sample rows are `"CardType": "S"`, `"Active": "N"` and are
named "10M ANALYTICS", "11 SEVEN GROUP", "360MARCOM SOLUTIONS PRIVATE LIMITED" —
marketing agencies and service suppliers, i.e. **people JIVO pays**, not people
who sell JIVO's oil.

The actual marketplace distributors are on the *other* side of the ledger and
live in `sap platform-distributors` (`CardType: "C"`, `MainGroup: "E-COMMERCE"`),
and the seven named e-commerce distributors are hard-coded in the SPA:
`CUSTA000907` SUSTAINQUEST, `CUSTA000927` ANTIZE FOODS, `CUSTA000900` BABA
LOKENATH TRADERS, `CUSTA000354` CHIRAG ENTERPRISES MUMBAI, `CUSTA000906` EVARA
ENTERPRISES, `CUSTA000592` KNOWTABLE ONLINE SERVICES, `CUSTA000048` R K
WORLDINFOCOM.

**`sap distributors` and `sap platform-distributors` are opposite sides of the
books and must never be substituted for one another.**

### Trap 3 — an empty `data: []` here usually means "wrong kind of party", not "no business" *(observed)*
`distributor-invoices/VENDA000526`, `distributor-orders/VENDA000526` and
`sales-invoices/VENDA000526` all returned `{"data": [], "count": 0}`. That is
because `VENDA000526` is a **vendor** (10M ANALYTICS, `CardType: "S"`) and all
three endpoints read A/R (customer) documents. A vendor has no A/R invoices by
definition.

So: empty result → check the CardCode's type before reporting "no invoices".
A `VEND…` code on a customer endpoint is a category error, and the API answers it
with a cheerful, entirely truthful, completely useless zero.

### Trap 4 — **turnover cannot be computed from this domain** *(observed)*
JIVO defines turnover as invoices net of GST **minus credit notes**, excluding
cancelled. This domain exposes invoices. It exposes **no credit-note endpoint at
all** — there is no `sap credit-notes`, and nothing in the 17 paths reads `ORIN`.
Mart's books contain **4,444 credit-note documents** (live count), and none of
them is visible here.

Also, `sales-invoices`' 25,157 rows are the *entire* `OINV` table, cancelled
documents included — the `CANCELED` field is present so you can drop them, but
nothing drops them for you.

**Therefore:** summing `DocTotal − VatSum` from `sap sales-invoices` gives gross
billing including cancellations and before returns. It is not turnover, and it
must not be presented as turnover. For turnover, use `hana_turnover` / the SAP
tools, and state the company.

### Trap 5 — `DocTotal` is **GST-inclusive**; net = `DocTotal − VatSum` *(verified arithmetically)*
On the live rows: 9,640.00 − 459.0465 = 9,180.95, and 5% of 9,180.95 = 459.05 ✓.
Second row: 6,941.00 − 330.5255 = 6,610.47, 5% = 330.52 ✓. So `VatSum` is the tax
*inside* `DocTotal`, exactly as in SAP.

`sap sales-invoices` is the only endpoint in this domain that exposes an invoice
total. (Note the contrast with the `reports` domain, where the Amazon PO money
fields are GST-**exclusive** — do not add the two together without adjusting.)

### Trap 6 — the field names are **raw HANA columns**, not SAP Service Layer names *(observed)*
Anyone who knows the `sapb1` CLI will reach for the wrong names here:

| here (HANA) | in `sapb1` (Service Layer) |
|---|---|
| `CANCELED` — one L, upper case, `'N'`/`'Y'` | `Cancelled` — two Ls, `'tNO'`/`'tYES'` |
| `DocStatus` — `'O'` / `'C'` | `DocumentStatus` — `'bost_Open'` / `'bost_Close'` |
| `Balance` | `CurrentAccountBalance` |
| `CreditLine` | `CreditLimit` |
| `OnHand` | `QuantityOnStock` |
| `MinStock` | `MinInventory` |

`Balance` really is the ledger balance: `CUSTA000912` reads 3,407,276.9292 in the
ecom payload and 3,407,276.9292 in `OCRD."Balance"` — identical. So JIVO's sign
rule applies unchanged: **positive = DEBIT (they owe JIVO), negative = CREDIT
(JIVO owes them).**

### Trap 7 — quantities are **pieces (single bottles)**, never cartons *(observed, and it is correction C-0001)*
`PurchaseUOM` and `SalesUOM` are `"PCS"`; `inventory-overview` rows carry
`"UOM": "PCS"`. The "20 PCS" in an item name like `COLD PRESS 1 LTR 20 PCS` is
the carton configuration and **must not be multiplied in** — doing so inflates
volume roughly 20×.

`SalPackUn` is the *litres per piece*, not the pack count: 0.5 for
`MAKKI ATTA 500 GMS 20 PCS`, 1.0 for a 1 LTR item. Litres = pieces × `SalPackUn`,
and for JIVO's tonnage convention, oil litres × 0.91 → kg.

### Trap 8 — `Litres` and `total_litres_on_hand` are **partial by construction** *(observed)*
Only items flagged `IsLitre: "Y"` get a `Litres` value. The `summary` block admits
this with `litre_units_total`, `litre_units_covered` and `litre_coverage_pct`. A
"total litres in stock" figure taken from here is therefore a floor, not a total —
quote the coverage percentage alongside it or don't quote it.

### Trap 9 — `inventory-overview` is item × warehouse, and its API default is "everything, including every zero" *(observed)*
47,908 rows = exactly Mart's `OITW` row count. Most are zero (`inventory-warehouse-comparison`
shows warehouses with 1,349 items of which 1,344 are zero-stock).

The SPA **always** sends `stock_state`, defaulting to `in`
(`PlatformSapInventory-DsKqShCV.js`: `r.stock_state = e.stock_state === 'low' ? 'low' : 'in'`),
so the dashboard never shows the zeros. A CLI that mirrors the raw API default
does. Anything published here should default to filtering, or at minimum warn.

Same shape of problem, smaller: `stock-by-warehouse` with no `item_code` returns
89 KB of every item in every warehouse; the SPA never calls it that way.

### Trap 10 — `Available` goes negative and that is correct *(observed)*
`COLD PRESS 1 LTR 20 PCS` at BH-FG: `OnHand` 60, `Committed` 5,600, `OnOrder`
3,500, `Available` −5,540. `Available = OnHand − Committed`. A negative number is
an oversold position, not a data error, and it is the single most useful field in
the payload for "can we fill this PO".

### Trap 11 — `inventory-finished-goods` totals are in **bottles**; the dashboard's rupee and litre views are computed in the browser *(observed)*
The API returns quantities. `PlatformSapInventoryDashboard-CWJH5Sdz.js` converts
client-side — `× SalPackUn` for litres, `× Price` for value. So `grand_total` and
`column_totals` straight out of the API are **piece counts**, even though the same
labels in the UI may be showing rupees. Anything printing `grand_total` as money
is wrong by a factor of the price.

Also note that page hard-codes `source = 'mart'` and offers no switch, which is a
second reason a naive reading defaults to Mart.

### Trap 12 — calling `distributor-inventory` with no `card_code` silently answers about **one** distributor *(observed; the default rule is not verified)*
The probe sent no parameters and got back `card_code: "CUSTA000907"`
(SUSTAINQUEST), `as_of_month: "2026-06-01"`. The SPA always passes a code
(`getDistributorInventory: (e, t={}) => X('/api/sap/distributor-inventory', {card_code: e, ...t})`)
and defaults its picker to SUSTAINQUEST.

Two hazards: (a) an operator who forgets `card_code` gets one distributor's FIFO
stock and no warning that it is not all of them; (b) `as_of_month` came back as
**June 2026** on a probe run on **3 August 2026** — two months stale. Whether that
is "latest month with data" or a fixed cut-off **I could not determine** from the
evidence; treat `as_of_month` as authoritative and always print it.

### Trap 13 — `source=oil` on `sales-analysis` defaults to an **intercompany** customer *(observed)*
`PlatformSapDashboard-bUN0KEtA.js`:

```js
E = ['ANTIZE FOODS…','BABA LOKENATH…','CHIRAG ENTERPRISES MUMBAI','KNOWTABLE…',
     'EVARA ENTERPRISES','R K WORLDINFOCOM PVT LTD','SUSTAINQUEST PRIVATE LIMITED']
D = ['JIVO MART PVT LTD']
function O(source){ return source === 'oil' ? [...D] : [...E] }
```

So switching the dashboard to Oil sets the default `cardname` filter to
**JIVO MART PVT LTD** — i.e. the Oil view is measuring **Oil selling to Mart**,
which is an intercompany transfer, not a market sale. JIVO's correction C-0005
requires intercompany parties to be excluded from sales figures and named when
they appear. An "Oil sales" number lifted from this dashboard without checking
`cardname` is an internal transfer figure.

### Trap 14 — `sap sales-invoice` (singular) is not one invoice *(observed)*
`/api/sap/sales-invoices/{x}` is `getCustomerSalesInvoices` — `{x}` is a
**CardCode**, and it returns that customer's invoice list. Its neighbour
`sap sales-invoice-lines/{x}` takes a **DocEntry**. Two adjacent commands, two
different identifier types, near-identical names. Passing a DocEntry to
`sap sales-invoice` will return an empty list and look like "no invoices".

### Trap 15 — `sales-analysis` is a **bulk** endpoint; a small page size silently truncates the analysis *(observed)*
The SPA sets `page_size = 1e5` (`var P = 1e5` in `PlatformSapDashboard`) and pulls
the whole range in one request, because the totals are computed client-side. A CLI
that defaults to 50 rows and then sums them produces a confidently wrong total.
Anything summing this endpoint must page to exhaustion or pass a large
`page_size`.

### Trap 16 — the `platform` slug enum is only proven for `amazon` *(observed for amazon; the rest inferred)*
`/api/sap/platform-distributors/amazon` returned 200. No other slug was probed.
The SPA's slug universe is `amazon`, `amazon_mp`, `bigbasket`, `blinkit`,
`callcenter`, `citymall`, `flipkart`, `flipkart_grocery`, `jiomart`, `meta`,
`swiggy`, `zepto`, `zomato` — but **whether this endpoint serves any of them
beyond `amazon` is not verified**, and a 404 on one of them would mean "no SAP
accounts mapped for that platform", not "endpoint broken".

---

## 4. Recommended spec entries

All GET. Response type is `object` for every one (from `live_response.top_type`).
Parameter names below were taken from the live 400 bodies and from the SPA's own
API client — none is invented. Where the SPA never revealed a filter name I say so.

| command | description (operator-facing) | params |
|---|---|---|
| `sap distributor-inventory` | FIFO stock and month movements held by one marketplace distributor (Mart books). | `card_code` (string, **always pass it**; observed values: `CUSTA000907`, `CUSTA000927`, `CUSTA000900`, `CUSTA000354`, `CUSTA000906`, `CUSTA000592`, `CUSTA000048`) |
| `sap distributor-invoices` | A/R invoices raised on one party. | path `card_code` (string, required); `page` (int), `page_size` (int) |
| `sap distributor-orders` | Sales orders placed by one party. | path `card_code` (string, required); `page` (int), `page_size` (int) |
| `sap distributors` | The Mart **vendor** master with ledger balances (1,247 rows). | `page` (int), `page_size` (int) — echoed by the response. No other filter name was observed for this path. |
| `sap distributor` | One party in full — master row, addresses, contacts. | path `card_code` (string, required) |
| `sap inventory-finished-goods` | Finished-goods stock per item across all warehouses, in **pieces**. | `source` (enum: `mart` \| `oil`; default `mart`) |
| `sap inventory-overview` | Stock per item per warehouse with value, min/max levels and litres. | `source` (`mart`\|`oil`), `search` (string), `status` (string — values not observed), `stock_state` (enum: `in` \| `low`), `warehouse` (comma-separated), `warehouse_code` (comma-separated), `group` (comma-separated), `is_litre` (`Y`), `page`, `page_size`. Valid `warehouse`/`group` values come back in the response's `filters` block. |
| `sap inventory-warehouse-comparison` | One line per warehouse: item count, units on hand, stock value, zero-stock count. | `source` (`mart`\|`oil`) |
| `sap items` | The Mart item master with company-wide stock (1,349 rows). | `page`, `page_size` |
| `sap platform-distributors` | The SAP **customer** accounts a marketplace bills through, with balances. | path `platform` (string; only `amazon` verified); `search` (string), `page`, `page_size` |
| `sap platform-distributor` | Detail for one marketplace customer account. **Response shape unverified — never probed.** | path `platform`, path `card_code` |
| `sap platform-sales-invoices` | Invoices for one marketplace. **Response shape unverified — never probed.** | path `platform`; `page`, `page_size` |
| `sap sales-analysis` | Sales lines for a date range, filtered by group/chain/location/party. | **`from_date` (required, `YYYY-MM-DD`)**, `to_date` (`YYYY-MM-DD`), `source` (`mart`\|`oil`), `main_group`, `chain`, `location`, `sub_group`, `cardname`, `page`, `page_size`. Only `from_date`'s requirement is proven — the 400 stopped at the first error, so **whether `to_date` is also mandatory was not observed**. Valid values for the five filters come back in the response's `filters` block. |
| `sap sales-invoices` | A/R invoice headers from the Mart books (25,157 rows, cancelled included). | `page`, `page_size`. The SPA calls this only via the `sales-analysis` page, so no date-filter parameter name was observed on this path. |
| `sap sales-invoice` | All invoices for **one customer code** (not one invoice). | path `card_code` (string, required); `page`, `page_size` |
| `sap stock-by-warehouse` | Per-warehouse stock rows for one item. | `item_code` (string — the SPA always sends it; omitting it returns everything) |

---

## 5. Exclusions

### `sap sales-invoice-lines` — `/api/sap/sales-invoice-lines/{DocEntry}` — **BROKEN UPSTREAM, exclude**

**Symptom.** Deterministic HTTP 500 on every DocEntry tried (the bundle records
4 × 500, no other code). Response body, byte for byte:

```
{"detail":"SAP HANA error: (260, 'invalid column name: T1.UnitMsr: line 4 col 28 (at pos 115)')"}
```

**Reproduction.** Pull any DocEntry from a live `/api/sap/sales-invoices`
response and request its lines:

```
GET /api/sap/sales-invoices                 →  DocEntry 37594, 37603, 37601 …
GET /api/sap/sales-invoice-lines/37594      →  500
GET /api/sap/sales-invoice-lines/37603      →  500
GET /api/sap/sales-invoice-lines/37601      →  500
```

**It is DocEntry-independent.** The failure is in the SQL text, which HANA rejects
at parse time — before the `DocEntry` value is ever used. Every DocEntry will
fail. There is no "good" DocEntry to find.

**Root cause (verified against the live schema, not guessed).** I listed the
columns matching `%UNIT%MSR%` in `JIVO_MART_HANADB`:

| table | columns that exist |
|---|---|
| `INV1` (invoice lines) | `unitMsr`, `unitMsr2` |
| `OITM` (item master) | `BuyUnitMsr`, `CntUnitMsr`, `SalUnitMsr` |
| `OINV` (invoice headers) | *(none)* |

**No table has a column called `UnitMsr`.** HANA quotes identifiers
case-sensitively, so `T1.UnitMsr` cannot resolve anywhere. The fix depends on
what `T1` is aliased to in that query:

* if `T1` is `INV1` → the column is `"unitMsr"` (lower-case *u*);
* if `T1` is `OITM` → the intended column is almost certainly `"SalUnitMsr"`.

The error is at *line 4, col 28* — the `SELECT` list — so this is a one-token
fix in the column list. The shape of the mistake (a capitalised `UnitMsr` that
would have resolved fine on case-insensitive SQL Server) suggests a query ported
to HANA without re-casing. That last sentence is inference; the column inventory
above is verified.

**For the ecom team:** correct the identifier casing in the
`sales-invoice-lines` query and the endpoint should come straight back. Until
then it returns 500 for every invoice, and there is **no other way in this domain
to see what was on an invoice** — `sales-invoices` is headers only. That makes
this the highest-value fix in the domain.

### Nothing else is excluded

* No POST/PATCH/DELETE endpoint exists anywhere in this bundle — all 17 are GET.
  RULE 0 excludes nothing here.
* No endpoint is DEAD. Not one 404 was recorded in the domain.
* `sap platform-distributor` and `sap platform-sales-invoices` are **UNPROBED, and
  are still published** — both are in the shipped v0.1.0 spec, both have a
  `SHIPPED_COMMAND_NAME_DO_NOT_RENAME`, and "never probed" is not evidence of
  death. They ship with their response shape marked unverified.
