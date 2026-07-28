# RECIPE — Jivo Group Control Panel: access + endpoint ground truth

**App:** "Jivo Group — Control Panel" — internal Django ERP/analytics dashboard for JIVO Wellness.
**Base:** `http://103.89.45.75:9080`  (HTTP, internal IP). Stack: Django + WSGIServer/CPython 3.14, server-rendered HTML shells + `/…/api/` JSON (AJAX). Auth: Django session cookie.
**Role:** logged in as `preshit` = **Admin**. ⚠️ **LIVE PRODUCTION SYSTEM — READ-ONLY ONLY.**

## Auth + how to call (all verified working)
```bash
bash ~/software/recon/login.sh        # refresh session cookie jar (recon/cookies.txt)
. ~/software/recon/jio.sh             # load helpers
jget  /realise/api/customer-master/                                   # GET (XHR header)
jpost /realise/api/sales-data/ '{"start_date":"2026-07-01","end_date":"2026-07-22"}'  # POST (JSON+CSRF)
jhead /realise/api/targets/?month=7&year=2026                         # status/size probe
```
- GET reads need header `X-Requested-With: XMLHttpRequest` (else 403/404). POST reads need `Content-Type: application/json` + `X-CSRFToken: <csrftoken cookie>`.
- If a call returns HTML/login page → session died → rerun `login.sh`.
- **Quote URLs with `?`/`&`** (zsh globs them otherwise).

## ⛔ READ-ONLY DISCIPLINE — NEVER call these (mutating). Document them, never execute:
`save-targets/  save-closing-remark/  rate-list/save/  rate-list/delete/  realise-calculator/upload/  realise-calculator/order-upload/  aging-remark/  aging-remark-upload-oil/  aging-remark-upload-beverages/  aging-remark-clear-oil/  aging-remark-clear-beverages/  credit-lock/  credit-unlock/  verify-pin/  /api/users/save/  /api/users/delete/`
Also **`/api/cogs/`** is OTP-gated (needs `param_type`+`otp`) — do NOT attempt to bypass; document only.
For POST *read* endpoints, use the **smallest** date range (e.g. a single day) to sample schema — do not pull months of data.

## Endpoint inventory (62 endpoints)

### A. Shared Realise API — `/realise/api/…` (used by Control Panel `/` AND Sales `/realise/` AND Accounts pages; home JS sets `API='/realise'`)
READ — POST(JSON): `sales-data/`{start_date,end_date,refresh?} · `sales-cn/` · `hidden-sales/` · `sales-flow/` · `sales-flow/open-items/` · `dispatch-details/` · `compare-docs/` · `open-payments/` · `drill-down/` · `historical-realise/` · `beverages-data/` · `export-xlsx/`(file)
READ — GET(XHR): `customer-master/` · `customer-aging-oil-ar/` · `customer-aging-mart/` · `customer-aging-beverages/` · `claims/` · `rate-list/`(+`?id=`) · `realise-calculator/items/` · `targets/?month=&year=` · `flex-targets/`(+`?seg=`) · `segment-targets/?segment=` · `target-nodes/?month=&year=&seg=` · `channel-targets/?month=&year=` · `channel-detail-docs/?…` · `oih-breakdown/` · `order-in-hand/` · `order-in-hand-rows/?…` · `commodity-oih-rows/?…` · `sales-pulse/?dataset=` · `beverages-docs/?…` · `health/` · `export-excel/` · `export-aging-detail/`
WRITE (skip): `save-targets/ save-closing-remark/ rate-list/save/ rate-list/delete/ realise-calculator/upload/ realise-calculator/order-upload/ aging-remark/ aging-remark-upload-oil/ aging-remark-upload-beverages/ aging-remark-clear-oil/ aging-remark-clear-beverages/ credit-lock/ credit-unlock/ verify-pin/`

### B. Inventory API — `/inventory/<page>/api/…`
`stock-available/api/data/?schema=` (GET) · `non-inventory/api/data/` + `non-inventory/api/drill/` (GET) · `production/api/plan/?items=` + `production/api/feasibility/?fg_code=` + `production/api/fg-list/` + `production/api/warehouses/` (GET) · `daily-production/api/data/?start=&end=` (GET) · `reconciliation/api/data/?…` + `reconciliation/api/ledgers/?…` (GET)

### C. Top-level — `/api/…`
`/api/cogs/?param_type=&otp=` (OTP-gated COGS — document only) · `/api/users/save/` `/api/users/delete/` (admin write — skip)

## Page → recon HTML file map (recon/pages/) & sidebar labels
| Route | File | Sidebar label |
|---|---|---|
| `/` | home.html | Control Panel |
| `/realise/` | realise.html | Sales (Sales Channel Dashboard) — 25 fetches, biggest |
| `/realise/compare-sales/` | realise__compare-sales.html | Compare Sales |
| `/realise/sales-cn/` | realise__sales-cn.html | Sales vs CN |
| `/realise/hidden-sales/` | realise__hidden-sales.html | Hidden Sales |
| `/realise/sales-flow/` | realise__sales-flow.html | Sales Doc Flow |
| `/realise/dispatch-details/` | realise__dispatch-details.html | Dispatch Details |
| `/realise/realise-calculator/` | realise__realise-calculator.html | Realise Calculator |
| `/realise/rate-list/` | realise__rate-list.html | Rate List |
| `/realise/customer-aging/` | realise__customer-aging.html | Customer Aging |
| `/realise/required-credit-limit/` | realise__required-credit-limit.html | Required Credit Limit |
| `/realise/open-payments/` | realise__open-payments.html | Open Payments |
| `/realise/claims/` | realise__claims.html | Claims |
| `/realise/customer-master/` | realise__customer-master.html | Customer Master |
| `/inventory/stock-available/` | inventory__stock-available.html | Stock Available |
| `/inventory/non-inventory/` | inventory__non-inventory.html | Non Moving Stock |
| `/inventory/oih-vs-stock/` | (404) | OIH vs Stock — nav link 404s; note in docs |
| `/inventory/production/` | inventory__production.html | Production Plan |
| `/inventory/daily-production/` | inventory__daily-production.html | Daily Production |
| `/inventory/reconciliation/` | inventory__reconciliation.html | Wellness–Mart Recon |
| `/realise/customer-master/` (Master Data) | realise__customer-master.html | Customer Master |
| `/users/` | users.html | Users (Admin) |

## Domain concepts to define (concepts/)
REALISE (₹/L avg realisation), OIH (Order In Hand), OIH RLZ, BAL / BAL W/O OIH / BAL RLZ, TGT/DONE/DONE L, COGS, P&L metrics, DRR; channels **GT** (General Trade) / **MT** (Modern Trade) / **ROI** (Rest of India) / **ECOM** (E-Commerce); segments **OILS** vs **BEVERAGES**; Main Group / sub-group drill; Wellness-Mart reconciliation.
