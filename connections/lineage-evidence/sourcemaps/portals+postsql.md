# Source map — portals + postsql (+ tankhapay, jivo-scraping-cli, product-identity)

Agent: portals+postsql lineage mapper · Date: 2026-07-30
Scope dirs: `/Users/damanpreetsingh/jivo-cli/portals`, `/postsql`, `/tankhapay`,
`/jivo-scraping-cli`, `/product-identity`

## Headline

None of these five is a SAP window. TankhaPay, Blinkit and Zepto are separate SaaS
products with their own databases that SAP has no connection to at all — **zero
occurrences of the string "SAP" in TankhaPay's entire 726-endpoint inventory or its
vault**. `jivo-scraping-cli` is flat-file marketplace scrape output on the VPS.
`product-identity` is not a data source at all — it is the released join key.
`postsql` is the only one that touches SAP-derived data, and only because two of the
16 Postgres databases hold **manually-refreshed, filtered, days-stale mirrors** of
SAP master data that the Django apps sync in.

---

## 1. Environment notes (things later agents will hit)

- **`hana-sql` default env points at the wrong host.** `connections/hana.env` has
  `HANA_HOST=103.89.45.192 / 30015`, which is **unreachable** from here
  (`nc -z 103.89.45.192 30015` → closed). The working path is
  `./hana-sql/hana-sql -env connections/hana-tunnel.env "<sql>"` (127.0.0.1:13015).
  Without `-env` you get `could not connect to HANA`.
- HANA identifiers are **case-sensitive and must be double-quoted**:
  `SELECT "CardCode" FROM JIVO_OIL_HANADB."OCRD"`. Unquoted `T.TransId` → SQL Error 260.
- `SYS.M_TABLES` (record counts) is slow — a filtered scan took >120 s. `SYS.TABLES`
  returns in seconds. Use `SYS.TABLES` for existence, `SYS.M_TABLES` only when you
  actually need row counts and can wait.
- `tankhapay/` at the repo root is a **byte-identical duplicate** of
  `portals/tankhapay/` (`diff -rq` → only difference is the compiled binary).
  Treat them as one system; don't double-count.
- SAP Service Layer (`sapb1`) was not attempted — HANA direct SQL answered
  everything needed and the brief said not to burn attempts on it.

---

## 2. TankhaPay (`portals/tankhapay`, dup at `tankhapay/`)

### Runtime
Go + cobra, stdlib-only HTTP. **297 read commands across 14 groups.** Four backends,
one JWT (`cli/config.go:26-29`):

| Backend | Host | Reads wired |
|---|---|---|
| business | `https://business.tankhapay.com/api/` | 261 |
| mobapi | `https://mobapi.tankhapay.com/api/` | 26 |
| tpPay | `https://mobapi.tankhapay.com/` | 5 |
| tnd | `https://tnd.tankhapay.com/api/` | 5 |

Auth: headless `POST /api/login`, HS256 JWT (24 h), **every request/response body is
AES-128-ECB + PKCS7 encrypted**. Vendor: Akal Information Systems. Account
`tp_account_id=2719`, user "ravinder singh" (Employer).

### LIVE verification (run 2026-07-30)
```
portals/tankhapay/cli/tankhapay-portal doctor
  ✓ token: ravinder singh (Employer) — valid 18h50m0s
  ✓ live:  dashboard read OK (160 bytes decrypted)

portals/tankhapay/cli/tankhapay-portal dashboard tpay-dashboard-data --set action=get_employee_list
  {"cur_monthyr":"Jul-2026","joining_pending":"7","left_count":"1202",
   "new_employees":"3","today_s_attendance":"248","tot_on_leave":"0",
   "total_employees":"593"}
```

### The decisive SAP comparison
```
hana-sql -env connections/hana-tunnel.env
  "SELECT 'OIL',COUNT(*) FROM JIVO_OIL_HANADB.OHEM UNION ALL
   SELECT 'MART',COUNT(*) FROM JIVO_MART_HANADB.OHEM UNION ALL
   SELECT 'BEV',COUNT(*) FROM JIVO_BEVERAGES_HANADB.OHEM"
→ OIL 17 · MART 1 · BEV 15   (33 employees, all three companies combined)
```
**TankhaPay: 593 active + 1,202 left = 1,795 employee records. SAP: 33.**
SAP B1's HR module (`OHEM` + `HEM1..HEM10`) is present but effectively unused — it is
a stub. There is no SAP payroll/attendance table: a search over all 3,111 tables in
`JIVO_OIL_HANADB` for `%PAYROLL% %SALARY% %ATTEND% %EMPLOY% OATT% OTMS%` returned only
`OHEM`, `HEM1-HEM10`, `OUSR` (SAP login users) and two unrelated
`CRSP*_EMPLOYEES` internal views.

Nor is there a user-table workaround: all 100 `@`-prefixed UDTs in `JIVO_OIL_HANADB`
are e-way-bill, item-variety, licence, QC, budget and chain tables — **none HR**.

### Where payroll *does* touch SAP
`JIVO_OIL_HANADB."OJDT"` contains manually-typed journal entries whose `Memo` mentions
salary, e.g. `TransId 216114 "MAY SALARY AMOUNT"`, `211294 "SALARY MAKE FROM BEV UNIT"`,
`209663 "Salary Ziual Apr 2026"`, `208338 "advance adjusted against april salary"`
(all `TransType 30` = manual JE). So the **GL expense total** is in SAP, typed by hand.
Nothing employee-level, nothing automated, no reference to TankhaPay anywhere.

### Per-group ruling

| Group | Cmds | Backing source (example) | Bucket | Conf | Note |
|---|---:|---|:--:|---:|---|
| Employee-Management | 53 | `business/employee/getEmployeeProfile`, `GetDocumentMasterDetails` | **N** | 96 | KYC, Aadhaar/PAN, bank, UAN/ESIC, family, education, exit, assets — SAP OHEM holds 33 stub rows |
| Attendance | 37 | `business/getAttendancePunchData`, `device/get_business_device`, `livetracking/getEmployeeKilometers`, `livetrack/live_tracking_get_route_distance` | **N** | 97 | biometric punches + GPS route/km. SAP B1 has no such object |
| Reports | 46 | `business/*` report endpoints | **N** | 92 | derived from the native data above |
| Masters-Config | 33 | `business/MasterApi/*` | **N** | 93 | app config (shifts, policies, grades) |
| Org-User-Management | 25 | `business/*` OU / role reads | **N** | 93 | org units 37,2211,38,40,31,1925 — SAP has no equivalent hierarchy |
| Leave-Management | 19 | `business/leave/*` | **N** | 95 | leave balances/applications |
| Approvals | 19 | `approval/GetAllReimbursementClaimsForEmployer`, `travel/getAllTravelExpenseDetails`, `meal/getDetailMealVoucher` | **N** | 94 | approval trails, reimbursement + travel claims, meal vouchers |
| Broadcast-Visitor-Help | 13 | `visitor/visitor_list`, `TpHelpAndSupportApi/GetTickets`, `NotificationApi/GetCampaignsDetails` | **N** | 96 | visitor gate log, support tickets, push campaigns |
| Payouts | 11 | `getPayoutTransactionsDetails`, `imprest/get_imprest_applications_filter`, `piece/getEmployeePieceReport` | **N** | 85 | per-employee payout/imprest/piece-rate. See caveat below |
| Recruit-ATS | 9 | `employee/getCandidateDetails`, `approval/CanditateDetailsForVoucher` | **N** | 96 | candidates/offers never reach SAP |
| Contract-Labour-Inventory | 9 | `contractLabor/getLabourDetails`, `dinventory/getEmpProductList` | **N** | 90 | contractor daily labour + employee-issued assets (uniform/kit), NOT SAP stock |
| Accounts-Taxes | 8 | `get_tds_report_data`, `TpTaxesApi/GetEmpRegimeAndTaxProjection`, `TpInvestmentProofApi/*` | **N** | 88 | employee tax regime, rent/home-loan declarations, investment proofs. TDS *payable* total appears in SAP GL; the declarations do not |
| Training-Performance | 8 | `tnd.tankhapay.com/api/*` | **N** | 95 | separate LMS backend |
| Dashboard | 7 | `dashboard/get_tpay_dashboard_data` | **N** | 95 | derived headline counts |

**Payouts caveat (why 85, not 95):** the monthly salary/PF/ESI/TDS *totals* do end up in
SAP as hand-typed `OJDT` entries. I could not prove whether the accountant derives those
figures from a TankhaPay payroll register or from an offline sheet — there is no code
path or reference in either direction. If you insist on a bucket for "monthly salary GL
total" alone, it is a manual **F** with a human in the loop; everything employee-level is
unambiguously **N**.

**Imprest note for Accounts:** SAP holds employee IMPREST *vendor accounts* (per repo
CLAUDE.md and the savings-audit findings), while TankhaPay holds imprest
*applications/approvals*. Same money, two halves — the SAP side is the balance, the
TankhaPay side is the request trail. Don't double-count.

---

## 3. Blinkit portal (`portals/blinkit`)

Runtime: Go + cobra, `cli/blinkit-partner`. Single host **`https://www.partnersbiz.com`**
(the only base URL in the code). Auth: email-OTP → token. 10 command groups:
`po appointments invoices payments offers assortment reports sales scorecard soh`.
Endpoints read (`cmd_*.go`): `/v1/client-po-details/*`, `/v1/get-po-count/`,
`/v1/get-grn-details/`, `/v1/invoice/details/`, `/v1/charges/`, `/v1/utr/invoices/`,
`/v2/appointment/*`, `/v2/slots/available/`, `/v1/report-requests/`.

The `brands.blinkit.com` ads portal is documented in `vault/ads/` but **is not wired
into the CLI** (only `blinkit-ads-generate.sh` exists for the token).

**Bucket: X** for every group. Data originates in Blinkit's systems (their PO, their
dark-store SOH, their appointment slots, their scorecard, their charge deductions).

*The SAP-side counterpart exists but is a different record:*
`JIVO_MART_HANADB."OCRD"` holds `VENDA000849 BLINK COMMERCE PRIVATE LIMITED` (CardType
S). So the **invoice JIVO raises against a Blinkit PO** is in SAP as an `OINV`/`ORDR`
row; the **PO itself, the appointment, the GRN short-shipment, the marketing/logistics
charge deductions and the dark-store SOH are not**. Reconciling the two is exactly
where the money leaks — that's a downstream analysis, not a lineage question.

---

## 4. Zepto portal (`portals/zepto`)

Runtime: Go + cobra, `cli/zepto-portal`. **407 wired read calls across 25 groups**
(counted: `grep -rhoE '(simpleGet|queryGet|getByID|postRead|downloadGet)\(app' cmd_*.go
| wc -l` → 407). One JWT (`authorization` header, no `Bearer`), **seven** backends
(`config.go` + `client.go`): `fcc.zepto.co.in`, `auth-backend.zepto.co.in`,
`financenew.zepto.co.in`, `scpfin.zepto.co.in`, `brands-onboarding.zepto.co.in`,
`ads-platform.zepto.co.in`, `partner.zepto.co.in`.

Groups: `po asn release-orders rtv catalog stock reports invoicing contracts payments
ledger receivables fbz` (vendor) · `brands creative campaigns wallet brand-analytics
insights engagement` (ads) · `identity users subscription kyc platform` (platform).

**Bucket: X** across the board. Same nuance as Blinkit —
`VENDA000948 ZEPTO/KIRANAKART TECHNOLOGIES PVT LTD VEND` exists in SAP `OCRD`, so
settled billing is reconcilable, but ads spend, wallet, dark-store stock, catalog
health, RTV, amendment requests and SCF receivables have no SAP object.

---

## 5. postsql — 15 live Postgres databases (README says 16)

Server: `103.89.45.76:5432` (profile `jivo`, connects as `postgres`). Read-only
enforced three ways (READ ONLY txn + `default_transaction_read_only` + first-token
allowlist). 27 read commands + an MCP server on `:7779`.

**postsql itself is not a data source — it is a lower-level view of the SAME data the
app CLIs (`oms-cli`, `factory-cli`, `ecom-cli`) serve over HTTPS.** Grepping the whole
repo, no other CLI references `103.89.45.76` or any of these DB names; every other tool
goes through `oms.jivo.in` / `factory.jivo.in` / `ecom.jivo.in` / `exim.jivo.in`.
So: `postsql` gets you the *unaggregated, pre-API* rows, including tables the app APIs
never expose (audit logs, sync logs, soft-deleted rows, backup DBs).

`postsql dbs` (live, 2026-07-30):

| DB | Size | Owning app | Bucket | Evidence |
|---|---|---|:--:|---|
| `test_supabase` | 1400 MB | **e-com BI warehouse** (Supabase: `auth`/`storage`/`realtime` schemas + `public`/`staging`/`reporting`/`master`/`quality`/`raw`) — behind `ecom.jivo.in` | **X** (+1 stale M table) | see below |
| `factory_flow` | 865 MB | **Factory** (`factory.jivo.in`) — Django. `barcode_*`, `gate_core_*`, `production_execution_*`, `warehouse_*`, `grpo_*`, `dispatch_plans_*`, `marketplace_*` | **N + F** | see below |
| `jivo_ecom` | 55 MB | **e-com app** — `amazon_po`, `inventory_master`, `sec_sales_master_daily/range`, `amazon_mp`, `appointment` | **X** | schema |
| `order_management` | 54 MB | **OMS** (`oms.jivo.in`) — Django | **M + F** | see below |
| `oms_backup` | 21 MB | OMS backup copy (same tables, `sap_party_addresses` 17,474 vs live 35,664) | mirror-of-mirror | schema |
| `OMS_TEST` | 14 MB | OMS test/staging copy | copy | schema |
| `jivo_site` | 11 MB | **jivo.in website** — `Visitor`, `VisitorSession`, `AnalyticsEvent`, `CookieConsent`, `DeviceInfo`, `Conversation`, `AIExecution`, `Feedback`, CMS pages | **N** | schema |
| `Ecommerce` | 11 MB | older Django e-com app — `Amazon_purchaseorderheaders/lines`, `Platforms_purchaseorder(items)`, **`Mapping_skumapping`** | **X + bridge** | schema |
| `fs` | 10 MB | **"factory system" v2** — schema-per-domain (`gi` gate-in, `prd` production, `quc`/`qc` quality, `inv`, `ds` dispatch, `per` users, `procurement`, `prs`). Nearly empty (largest table 177 rows) — a rewrite in progress | **N (nascent)** | schema |
| `test_order_management` | 9.7 MB | OMS test copy (32 tables) | copy | schema |
| `test_test_supabase` | 8.7 MB | warehouse test copy (14 tables) | copy | schema |
| `CRM` | 8.4 MB | Django complaints app — `complaints_complaint` + stock Django auth | **N** | schema |
| `postgres` | 8.1 MB | cluster default | — | — |
| `task` | 7.6 MB | **0 tables** — empty shell | **U** | live |
| `po_db` | 7.6 MB | **0 tables** — empty shell | **U** | live |

### 5a. `order_management` — the one real SAP mirror, and it is stale

Smoking guns, all live:

```
postsql --db order_management describe sap_parties
  → card_code, card_name, address, state, main_group, chain, country,
    card_type, category, synced_at            ← literally named sap_*, with synced_at

postsql --db order_management query "SELECT max(synced_at), count(*) FROM sap_parties"
  → 2026-07-28 13:08:22+05:30 · 3,350
postsql --db order_management query "SELECT max(synced_at), count(*) FROM sap_products"
  → 2026-07-28 13:08:10+05:30 · 4,155
```

**It is a FILTERED SUBSET, not a copy.** Live SAP counts via HANA:

| | SAP (OCRD/OITM, all 3 cos) | OMS mirror | coverage |
|---|---:|---:|---:|
| Business partners | 3,390 + 2,183 + 2,930 = **8,503** | 3,350 (OIL 1,169 / BEV 1,244 / MART 937) | **39 %** |
| Items | 2,269 + 1,349 + 2,192 = **5,810** | 4,155 (OIL 1,534 / BEV 1,530 / MART 1,091) | **72 %** |

And it holds only ~10 of OCRD's ~100+ columns — **no `CurrentAccountBalance`, no credit
limit, no payment terms**. So "fetch a party from OMS" ≠ "fetch it from SAP".

**The sync is manual, not scheduled:**
```
postsql --db order_management query "SELECT * FROM sap_sync_schedules"   → 0 rows
postsql --db order_management query
  "SELECT triggered_by,count(*) FROM sap_sync_logs GROUP BY 1 ORDER BY 2 DESC"
  → manual 313 · preshit 24 · Admin 13 · bulk-validation 4 · muskan2 3 · admin 3 · pankaj 1 · tannu 1
runs by month: Mar 139(59 ok) · Apr 16(9) · May 122(59) · Jun 61(54) · Jul 29(27)
last run: 2026-07-28 13:09  → the mirror is ~2 days stale as I write this
```

**The sync source is MSSQL, not HANA.** Failed-run error text:
```
"SAP connection failed: (20009, b'DB-Lib error message 20009 ... Unable to connect:
 Adaptive Server is unavailable or does not exist (103.89.45.75) ...')"
```
`DB-Lib` / "Adaptive Server" = FreeTDS/pymssql. So OMS pulls its SAP master from a
**Microsoft SQL Server at 103.89.45.75** — the same box the DSR portal lives on — while
the books this repo queries are **HANA at 103.89.45.192:30015**. I did **not** establish
what that MSSQL instance is (a legacy SAP B1-on-MSSQL company DB? a staging replica? a
middleware landing zone?). **This is the biggest open question in my scope** and it
matters: if OMS's "SAP" is a different SAP than HANA, the mirror could be wrong as well
as stale. Flagging for a follow-up agent.

**The feeder half.** `orders.sap_doc_number` + `orders.sap_created` (bool),
`sales_orders_logs.sap_doc_entry/sap_doc_num`, `sales_quotation_logs.sap_doc_entry/
sap_doc_num` → OMS creates the sales order/quotation, pushes it to SAP, and stores the
returned DocEntry/DocNum. Classic **F**. What SAP never receives (all
`order_management`-only tables): `order_rate_approvals`, `order_item_approval_mapping`,
`rate_approver_rules`, `audit_log` (13,106 rows), `orders_log`/`order_logs`,
`sales_quotation_logs` (337), `tracker_stage_event`, `tracker_stuck_alert`,
`notifications`, `push_tokens`, `web_push_subscriptions`, `devices_user_device`,
`credit_limit_logs`, `party_product_assignments` (12,889), `user_party_assignments`,
`labels`/`label_nutrition`, `order_template`, `scheme_product`/`order_item_schemes`.
That's the approval trail, the rejected/pending drafts, the rep→party mapping and the
salesman-scheme layer — **none of it exists in SAP**. (Entity-level rulings for OMS
belong to the oms-cli agent; I report the DB-level evidence.)

### 5b. `factory_flow` — heaviest SAP feeder in the estate

52 tables carry `sap_*` columns. Representative:
`barcode_dispatchsession.sap_doc_entry/sap_doc_num/sap_object_type/sap_snapshot/
sap_system_type/sap_dispatch_status`, `barcode_dispatchsapsynclog` (request_payload /
response_payload / attempt_no / status — a full **push** audit trail),
`grpo_grpoposting.sap_doc_entry/num/total`, `dispatch_plans_dispatchplan.
sap_invoice_doc_entry/num`, `production_execution_productionrun.sap_doc_entry/
sap_sync_status/sap_sync_error`, `warehouse_bsttransfer.*`,
`gate_core_salesdispatchgateout.*`, `marketplace_marketplacedispatch.
sap_delivery_note_doc_entry/sap_goods_issue_doc_entry/sap_post_status`,
`grpo_grpoattachment.sap_absolute_entry/sap_attachment_status`.

Pattern is unambiguous **F**: factory event happens → posted to SAP → SAP doc number
written back. The native-only mass is enormous and never leaves: `barcode_barcodeauditlog`
455,969 rows, `barcode_box` 300,544, `barcode_boxmovement` 772,093,
`gate_core_salesdispatchboxscan` 121,706, `barcode_scanlog` 135,206,
`barcode_labelprintlog` 307,704, `warehouse_bstboxscan` 71,550,
`notifications_notification` 66,874. Per-box barcode scan events = **N**, and SAP B1
holds nothing remotely like them. (Detailed rulings → factory-cli agent.)

### 5c. `test_supabase` — marketplace warehouse, with one fossilised SAP table

Everything material is **X** — platform-reported data JIVO did not generate:
`swiggySec` 634,208 rows (store-level sell-out: `STORE_ID`, `AREA_NAME`, `CITY`,
`UNITS_SOLD`, `GMV`), `staging."amazon data"` 470,206, `blinkitSec` 125,194,
`zeptoSec` 50,424, `flipkart_state_sales` 65,981, `bigbasketSec` 19,357,
`jiomartSec` 9,434, plus `*_inventory` (swiggy 89,663 / zepto 45,897 / bigbasket 45,307 /
blinkit 36,160 / amazon 15,721) and ad tables (`amazon_ads` 80,694, `flipkart_ads`
20,063, `blinkit_ads`, `zepto_ads`, `swiggy_ads`, `*_brandfund`, `amazon_coupon`).
**SAP holds none of this** — no dark-store dimension, no ad spend, no GMV-by-store.
SAP only has the primary invoice to `AMAZON`/`FLIPKART`/etc. as A/R.

The one SAP-derived table: **`oitm_master`, 2,014 rows** — a straight OITM dump
(`itemcode, itemname, itmsgrpcod, u_unit, u_sku, u_sub_group, u_islitre,
u_gross_weight, u_mrp, u_shelflife, prchseitem, sellitem, onhand, docentry`).
```
postsql --db test_supabase query "SELECT min(created_at),max(created_at),count(*) FROM oitm_master"
  → 2026-01-07 12:19:40  ·  2026-01-07 12:19:42  ·  2014
```
**One insert batch, 1.6 seconds, on 2026-01-07 — never refreshed since. 6.7 months
stale, and `onhand` is a stock figure.** Anyone treating this as current SAP stock is
wrong. Bucket **M, badly stale**.

Also native to this DB (**N**): `quality.validation_error` 13,226,
`accounts_inventorydohnotification` 3,785, `chatbot_chatmessage`/`chatbot_chatfile`,
`raw.upload_file` 170, `sp_po_document` / `sp_invoice` (PDF blobs in `bytea` — SAP B1
keeps attachments on a Windows file share, not in these DBs),
`month_targets`/`primary_month_targets`, `monthly_landing_rate`, `master_sheet`,
`city_state_mapping` 127,758, `pincode_mapping` 6,194.

### 5d. `jivo_ecom` — the "joined ≠ sourced-from" case

`amazon_po` (11,541 rows) carries `sap_sku_code` + `sap_sku_name` **next to** `sku_code`,
`external_id`, `po_number`, `availability_status`. The PO originates at Amazon Vendor
Central; the `sap_*` columns are a *lookup result*, not a provenance claim. Same for
`inventory_master` (13,762 rows: `asin`, `sellable_on_hand_units`,
`unfilled_customer_ordered_units`, `overall_vendor_lead_time_days` — Amazon's inventory
health feed, not SAP stock). **Bucket X**, with SAP item codes as a join column only.
This is the exact trap the brief warns about.

---

## 6. `jivo-scraping-cli` (`jivo-desk` / `jivo-scrape`)

Python 3, zero deps. **Not a database client at all** — it reads flat files the VPS
scrape pipeline writes (`SOURCES.md`):
`/opt/ecom-intel/platforms/<platform>/result.json` (10 platforms: amazon, amazon-fresh,
amazon-now, bigbasket, blinkit, flipkart, flipkart-minutes, instamart, swiggy-instamart,
zepto), `/opt/ecom-intel/today/` + `today.prev/`,
`/opt/ecom-intel/data/pricematch/daily.csv|history.csv`,
`/root/jivo-drr-panel/build/panel.json`, `/opt/ecom-intel/reviews/*.json`,
`/opt/ecom-intel/baselines/<platform>.json`.

LIVE (`ssh vps`, 2026-07-30):
```
/opt/ecom-intel/platforms/ → 10 platform dirs, as documented
-rw-r--r-- 4637159  Jul 29 07:24  /opt/ecom-intel/platforms/blinkit/result.json
-rw-r--r--    4515  Jul 29 10:11  /opt/ecom-intel/data/pricematch/daily.csv
```
Fresh to yesterday. Commands: `price avail compare match drr today files doctor` +
`product resolve|search|verify|coverage`.

**Bucket X** for all sweep data — competitor and own-listing prices/availability
scraped off public storefronts, per pincode. SAP has no price-observation object at
all. The `product *` subcommands are not a source; they read the identity map (§7).

---

## 7. `product-identity` — the join key, not a data source

Released dataset `2026-07-19.1`, map SHA-256 `ec0998...a7e5b9`, with a detached
`release-attestation.json` that both consumer CLIs (`jivo-desk`,
`jivo-factory-pp-cli`) compile in as a trust anchor and re-verify before loading —
an edited map cannot self-approve; failures exit 6.

Keys it declares non-negotiable:
- marketplace listing = `platform + listing_id`
- factory item = `company_code + sap_schema + item_code` (a bare `FG0000315` is
  explicitly **not** a global identity)
- a human SKU name is display text, **never** a join key

Accounting: 114 price groups · 334 membership rows · 333 distinct listing resolutions
· 151 JIDs · 1,906 observed Factory FG/FB/SL items, of which 266 are bound and 1,640
are explicitly `not_in_price_scraping_scope`. Zero unresolved, zero ambiguous.

What it actually reads (`tools/collect_sources.py:31-53`):
- via `ssh` → `/opt/ecom-intel/tools/pricematch/sku_map.json`, `master_v2.json`,
  `/opt/ecom-intel/bin/jid_registry.json`  (the **X** side)
- via HTTP against the **Factory app** → `/barcode/items/oitm/` (`item_code`) and
  `/production-execution/sap/items/` (`ItemCode`), swept per company
  `JIVO_OIL → JIVO_OIL_HANADB`, `JIVO_MART → JIVO_MART_HANADB`,
  `JIVO_BEVERAGES → JIVO_BEVERAGES_HANADB`  (the **M** side)

So the SAP half of the bridge is fetched through `factory.jivo.in`, which serves its own
OITM mirror — **product-identity never talks to SAP directly.** Describe it as: the
released, attested `platform:listing_id ↔ company:sap_schema:item_code` bridge that
makes X-side and M-side data joinable. It is what lets this whole lineage question be
answered per-SKU instead of per-guess.

**Second, competing bridge found:** `Ecommerce.Mapping_skumapping` in Postgres
(587 rows: `platform, external_sku_code, sap_code, sap_name, category, sub_category,
case_pack, uom`). Nothing reconciles the two. Worth a follow-up — two SKU bridges
disagreeing is a silent-wrong-number generator.

---

## 8. Coverage gaps — stated plainly

1. **The MSSQL "SAP" at 103.89.45.75 is unidentified.** OMS's sync error text proves it
   uses DB-Lib/Adaptive Server against that host, while this repo's books are HANA at
   103.89.45.192. I did not connect to it or determine whether it is a second SAP B1
   company DB, a replica, or a middleware staging DB. Everything I say about the OMS
   mirror's *fidelity* is therefore capped at ~80 confidence.
2. **TankhaPay: I ran `doctor` + one dashboard read only.** I did not live-pull an
   attendance punch row, a payout row or a payroll register — the rulings on those 12
   groups are code + schema evidence (endpoint names + absence of any SAP counterpart),
   not live rows. `dashboard today-attendence-reports` returned `TP-400: {}` (needs
   params I did not work out). The `total_employees:593` / `today_s_attendance:248`
   figures are live.
3. **Blinkit and Zepto: no live calls at all.** Both need a fresh OTP login and I judged
   that out of proportion for an X-by-definition ruling. Evidence is code (base URLs,
   endpoint paths) plus the live SAP `OCRD` check confirming the counterparty cards.
   The Blinkit *ads* portal (`brands.blinkit.com`) is documented but unwired — no CLI
   surface exists for it.
4. **`factory_flow` and `order_management` entity-level rulings are not mine.** I mapped
   the databases and the SAP-touch signature; `factory-cli` and `oms-cli` agents own the
   per-entity calls. Don't let my DB-level M/F/N shorthand override theirs.
5. **`task` and `po_db` are empty (0 tables) — ruled U**, not N. They may be dead, or
   may be pointed at by an app I did not find.
6. **README drift:** `postsql/README.md` says 16 databases; live `dbs` returns 15.
   Doc lost to live.
