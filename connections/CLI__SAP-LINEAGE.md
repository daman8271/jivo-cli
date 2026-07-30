# JIVO CLI ↔ SAP LINEAGE — FINAL REPORT

**Question answered:** *"When I fetch data from OMS-CLI, is that the same as fetching it from SAP,
or does it hold data from a different source? Which CLIs are already covered by SAP and which are
genuinely new?"*

Date: 2026-07-30 · 21 agents · 14 systems · ~1,500 commands surveyed · 226 entities ruled
Method: 8 source-map agents → 3 SAP ground-truth probes → 5 domain adjudicators → 5 adversarial
verifiers. **Where a verifier refuted an adjudication, the verifier's verdict is what appears below.**

---

## 1. THE HEADLINE

**No CLI in this repo is a pure SAP window, and only one is close.** Of 226 entities ruled:

| Bucket | Count | % of entities |
|---|---:|---:|
| **N** — native, never reaches SAP | 107 | 47.3% |
| **M** — SAP mirror / live SAP read | 77 | 34.1% |
| **X** — external (marketplace, govt, scraped) | 17 | 7.5% |
| **U** — undetermined | 16 | 7.1% |
| **F** — feeder (originates here, posts into SAP) | 9 | 4.0% |

**Read that percentage correctly.** It counts *entities in the matrix below*, one row each,
weighted equally. It is **not** query volume and **not** rupees. A single M entity — `OINV` /
`OCRD` — is probably 80% of what Accounts actually asks in a week, while dozens of the N rows are
low-frequency operational tables. **Per-entity share is not "share of what Daman queries".** Nobody
measured query volume; nobody could. The entity list is also not a census — it is what 21 agents
reached, so unreachable systems (TankhaPay, Blinkit, Zepto) are under-represented in entity count
relative to their command surface (13, 1 and 1 rows against 297, 38 and 407 commands).

**Direct answer for OMS-CLI:** fetching an *order* from OMS is **NOT** the same as fetching it from
SAP. OMS **originates** the order and pushes a stripped-down copy into SAP as a Sales Quotation
(OQUT → converted to ORDR). Verified: all 221 `sales_quotation_logs.sap_doc_num` with
status=SUCCESS resolve in `JIVO_OIL_HANADB.OQUT`, 214 of them created by integration user `B1i`
(1,351 Oil + 731 Bev quotations). But 7 of OMS's 73 commands (`sap parties`, `sap addresses`,
`sap products`, `sap branches`, `quotations status`, the 14 `hana *` commands) are pure SAP —
**and the mirrored ones are structurally broken:** `sap_parties` holds 3,350 rows over only 1,251
distinct `card_code`, because it flattens all three company books into one un-namespaced column
with **no company field**. `CUSTA000912` appears three times as three different parties. A
card_code lookup in OMS returns the wrong party roughly two times in three.

---

## 2. SYSTEM VERDICTS — the answer Daman asked for

| CLI | verdict | % of surface redundant with SAP | the one thing you can ONLY get here |
|---|---|---|---|
| **control-panel `jivo`** | **Almost entirely a SAP window with a calculator bolted on** | 16 of 24 entities = **67%** / ~71% of 42 commands | The claims register with its hold/pass approval trail and the required-credit-limit lock — but it holds **6 claims, ₹2.67 L, all on hold**, and the ageing-remark overlay is **0% populated on 4,617 rows**. Thin. |
| **exim** | **Half SAP window, half the only import system JIVO has** | ~46% of entities / 22 of 65 commands | **Tanks (32 vessels, 13.5 lakh L capacity, 8.56 lakh L held) and the 9-stage import lot lifecycle.** SAP has ZERO `%TANK%` tables and no in-transit object. Also the DGFT licence register. |
| **factory-cli** | **Split down the middle: live SAP window on one side, the entire physical plant on the other** | ~38% of entities / ~20% of 185 commands | **301,821 barcode cartons, 791,851 box movements, 143,236 scans, 10,740 QC lab readings.** SAP has no serial object (`OSRN`=0 in all 3 companies) and no scan concept. |
| **oms-cli** | **Its own order system with a stale SAP mirror bolted on** | ~35% of entities / 24 of 73 commands | **13,383 party↔product entitlements with a negotiated `basic_rate` per distributor.** SAP's equivalent (`OSPP`) holds 22 rows in Oil — all with CardCode `*3`, a wildcard, so SAP has **zero** party-specific prices. |
| **jsap-cli** | **Mostly governance, but its budget catalogue IS SAP** | ~29% of entities / ~30 of 146 commands | **The A/P budget-approval trail** — stage, approver, rejection, comments — living in custom HANA tables the Service Layer cannot see. And it is **enforced by SAP**: `SBO_SP_TRANSACTIONNOTIFICATION` refuses postings with *"Budget Not Approved for this Entry"*. |
| **ecom-cli** | **Almost entirely its own / external data** | ~14% of entities / 17 of 138 commands | **Marketplace sell-out at dark-store grain** — `swiggySec` 634,208 rows with STORE_ID, AREA_NAME, GMV. SAP cannot tell you which Swiggy store sold a bottle. |
| **dsr-cli** | **Almost entirely its own data — zero SAP code path** | **0% of the 71 commands**; 1 of 20 entities (an unexposed 2023 fossil) | **27,026,680 GPS breadcrumbs, 426,055 geotagged selfie punches, 2,128,151 retailer visits, 127,395 outlets.** `SAPID` is NULL on **all** 127,395 retailers and all 333 items. There is no SAP bridge and never has been. |
| **portals/tankhapay** | **Entirely its own data** | 0% | **1,795 employees, biometric attendance, payroll, leave.** SAP's `OHEM` = 17/1/15 hollow stubs with `SUM(salary) = 0.00` in every company. There is no attendance/payroll/leave table anywhere in 9,244 SAP tables. |
| **portals/blinkit** | **Entirely external** | 0% | Blinkit PO/GRN/appointment/charge-deduction/scorecard. SAP has **zero** Blinkit A/R in Oil and Mart; 6 invoices in Beverages only. |
| **portals/zepto** | **Entirely external** | 0% | Zepto ads, RTV, catalog health, FBZ receivables, dark-store stock. SAP has the money (237 Mart A/R invoices, ₹4.91 cr) and nothing else. |
| **jivo-scraping (`jivo-desk`)** | **Entirely external** | 0% | Daily price + availability sweeps across 10 platforms × pincode, with competitor prices. **No ERP on earth holds this.** |
| **postsql** | **A transport, not a source** | n/a | Audit logs, sync logs, soft-deleted rows, rejected drafts and the `oms_backup`/`OMS_TEST` copies that no app API exposes. |
| **product-identity** | **Infrastructure, not a source** | n/a | The attested platform-listing ↔ SAP-item bridge. **NOT VERIFIED by anyone in this exercise.** |
| **sapb1 / hana-sql** | **IS SAP** | 100% | Service Layer and HANA are the **same store** — 5/5 entity counts matched exactly in the same minute. Do not treat them as two sources. |

---

## 3. GENUINELY NEW DATA — ranked by business value

Only **UPHELD N** verdicts appear here. Anything refuted, unproven, or refuted-into-F is excluded
(that means TankhaPay imprest and reimbursement approvals are **not** on this list — see §6).

1. **Distributor entitlement + negotiated basic rate** (OMS, 13,383 rows / 1,103 parties). SAP's
   `OSPP` = 22 wildcard rows. This is the price book and it exists nowhere else.
2. **Barcode carton lineage** (factory: 301,821 boxes, 791,851 movements, 489,604 audit rows,
   143,236 scans). Only traceability JIVO has. `OSRN` = 0 in all three companies.
3. **Retailer/outlet universe + secondary sales visits** (DSR: 127,395 outlets, 2,128,151 visits,
   685,564 sold lines). SAP has 33 partners tagged RETAILER.
4. **Inbound QC** (factory: 1,136 inspections, 10,740 per-parameter lab readings, 46 rejected, 46
   return-to-vendor). SAP's QC stub is 6 abandoned rows in `@QC_O`.
5. **Import lot lifecycle + tanks** (EXIM: 9 stages, 32 tanks, 8.56 lakh L, 1,480 field-level audit
   rows). SAP inventory begins at the GRPO.
6. **Payroll / attendance / leave / employee master** (TankhaPay: 1,795 people, GPS punches).
7. **Field-force GPS + attendance** (DSR: 27.0 M breadcrumbs, 426,055 selfie punches).
8. **Order & budget approval trails** (OMS 380 log rows + 187 rate-approver rules; JSAP 1,440
   `tbl_Draft_Approvals` incl. **174 rejections**). SAP approves 7 sales orders in 22 months.
9. **Sales targets** (three unreconciled stores: DSR 581, control-panel, ecom 61+47+5). SAP's
   `OBGT` is a decaying *cost* budget with visible junk amounts.
10. **Intercompany carton rail Oil→Mart** (3,075 transfers, 76,498 lines, **0 SAP documents ever**).
11. **Gate + weighbridge + arrival slips + CoA/CoQ photos** (factory: 667 arrivals, 1,720
    weighments, 1,179 certificate scans).
12. **Beats / journey plans** (DSR: 4,882 beats, 182,151 beat-shop rows). No SAP route object.
13. **Salesperson hierarchy** (DSR 1,809 / JSAP 227). `OCRD.U_UNE_RSM/ASM/SO/SR/ZONE` exist and are
    **0% populated across 3,390 partners** — the classic schema-only trap.
14. **Vendor-invoice desk tracker** (OMS, 8 stages ending "Save in SAP") — but only **13 rows in
    production**. Schema is real; usage is not.
15. **SKU bridge + realisation/margin model** (ecom `master_sheet` 834 rows).
16. **Marketplace-facing app state**: DOH alerts, upload/validation audit, chatbot, RBAC across 8
    separate identity stores.
17. **PET bottle blowing + make-vs-buy** (factory, 8 runs, no CLI surface).
18. **Trade schemes / gift issuance to named retailers** (DSR, 34,236 gifts, 423,785 scheme lines).
19. **Physical stock counts** (JSAP). SAP's `OINC`/`OIQR`/`ODPS` = **0 rows in all three companies**
    — JIVO's book stock has never been reconciled to a count through SAP.
20. **Field-level UI audit trails** (OMS 13,347 rows) and **integration run logs** (OMS
    `sap_sync_logs` 367 runs, `sap_sync_schedules` **0 rows** — every mirror is hand-cranked).

---

## 4. THE FULL MATRIX

Sorted by system, then bucket (M → F → N → X → U). Evidence: `live` = rows seen · `code` = source
read · `schema` = object existence confirmed · `doc` = markdown claim only (weakest).

| system | entity | bucket | conf | evidence | SAP object | verdict / operator advice |
|---|---|:--:|---:|:--:|---|---|
| control-panel | Dispatch & freight fields (bilty, transporter, vehicle, driver, mobile, dispatch date) | M | 93 | live | OINV U_BilltyNumber/U_TransporterName/U_VehicleNoM/U_Dipatch_Date | ANTI-TRAP: looks native, is a SAP user field. But driver name on 1.6% and LR on 0.14% of Oil invoices — SAP cannot tell you who drove |
| control-panel | Credit notes / sales returns | M | 95 | live | ORIN/RIN1 | Ask SAP. Turnover = Invoices net GST − CreditNotes |
| control-panel | Hidden sales (excluded from headline Done) | M | 97 | live | OINV.U_ARNO='H' | The "hidden" flag is itself a SAP field |
| control-panel | Sales document flow (Quote→Order→Invoice, OMS-vs-human source) | M | 95 | live | OQUT/ORDR/OINV + OUSR | Ask SAP |
| control-panel | Order In Hand (open uninvoiced value/litres) | M | 97 | live | ORDR + RDR1.OpenQty | Reproduced row-for-row. Ask SAP |
| control-panel | A/R ageing books Oil / Mart / Beverages | M | 97 | live | OINV + JDT1 open items | Rows are SAP's; buckets are the app's arithmetic |
| control-panel | Open payments / on-account receipts | M | 96 | live | ORCT | App's `open_bal` ≠ `ORCT.OpenBal` — do not conflate |
| control-panel | FG stock on hand by SKU × warehouse | M | 96 | live | OITW/OITM/OWHS | Ask SAP |
| control-panel | Non-moving stock + drill (DaysSinceMoved) | M | 92 | code | OITW/OINM/OITM | Derived cut over SAP data |
| control-panel | Daily production (work orders) | M | 96 | live | OWOR + OUSR | Verified DocNum 726202786 field-for-field |
| control-panel | Production plan / feasibility / manufacturable-FG catalogue | M | 93 | live | OITT/ITT1 + OITW + OWHS | Read-only feasibility; creates nothing |
| control-panel | Wellness↔Mart intercompany reconciliation chains | M | 70 | live | Mart OPOR/OPDN/OPCH ↔ Oil ORDR/ODLN/OINV | UNPROVEN — verifier could not re-run the chain (app unreachable in that pass) |
| control-panel | Realise-calculator item master | M | 96 | live | OITM + U_SKU/U_Variety/SalFactor2 | Ask SAP |
| control-panel | Beverages sales track | M | 88 | schema | JIVO_BEVERAGES_HANADB OINV/ORDR/OITM | Ruled by symmetry with the verified Oil track |
| control-panel | Sales-pulse change fingerprint | M | 85 | doc | (hash of SAP state) | Derived signal, no facts |
| control-panel | Sales / realisation analytics (litres, ₹/L realise by type & sub-group) | M | 82 | live | OINV/INV1 − ORIN/RIN1 + OITM U_TYPE/U_Sub_Group | UNPROVEN: naive SAP re-aggregation diverges ~30% (OLIVE 76.2M SAP vs 53.0M app). **Do not quote a control-panel realise figure as a SAP figure** |
| control-panel | Sales targets (product / channel / segment / flex / nodes) | N | 85 | live | none | Django store; SAP has no litre or ₹ sales target |
| control-panel | Claims register with hold/pass workflow | N | 96 | live | none | Genuinely native — but **6 rows / ₹2.67 L / all held / 2 parties**. `ref_inv_no` values exist in NO SAP company |
| control-panel | A/R ageing remarks + special-price overlay | N | 90 | live | none | **0 of 4,617 rows populated.** An unused feature, not "unrecoverable business memory" |
| control-panel | Required-credit-limit lock + 2% buffer + closing remark | N | 82 | live | none (OCRD.frozenFor is a different thing) | 2% rule verified to the paisa. No lock active; 0/162 remarks populated |
| control-panel | Saved rate lists / realise-calculator what-if scenarios | N | 85 | code | none | UNPROVEN — store was empty at capture; field shape is a page-JS reconstruction |
| control-panel | App users / Realise roles / per-report RBAC | N | 97 | doc | none (OUSR is unrelated) | Django auth |
| control-panel | COGS / margin card | U | 40 | live | unknown | OTP-gated, never probed. Could be M (OITM cost) or N (maintained sheet). **Not checked** |
| control-panel | OIH vs Stock page | U | 90 | doc | n/a | HTTP 404 — feature not built server-side |
| dsr-cli | `sap_sales_log` — frozen SAP A/R extract, 8,009 rows | M | 95 | live | OINV+INV1 of the **pre-2024 MSSQL SAP** | Reconciles 1,918/1,918 against `Jivo_All_Branches_Live` (still online, 68,070 invoices 2019-08→2024-10). **Its FG codes mean DIFFERENT products in today's HANA — never join to live SAP.** Not exposed by any `dsr` command |
| dsr-cli | Primary sales, 2026-05 onward (12,560 lines) | N | 92 | live | partially OINV for the JIVO-seller subset | **REFUTED from M.** 820 of 1,483 rows in the ruled window have a SUPER STOCKIST as seller selling to sub-distributors SAP has never invoiced (72% in 2026-07). The M subset is exactly `from_retailerid=9771 AND numeric bill_number` |
| dsr-cli | Retailer / outlet universe (127,395) | N | 98 | live | none (OCRD has 33 RETAILER) | `SAPID` NULL on all 127,395. `erpId` is not a CardCode |
| dsr-cli | Distributor master | N | 88 | live | OCRD partially, name-match only | Duplication is the finding |
| dsr-cli | Salesperson master + org hierarchy (1,809) | N | 97 | live | OSLP (155, flat) | `OCRD.U_UNE_RSM/ASM/SO/SR` exist and are 0/3,390 populated |
| dsr-cli | Beats / journey plans / beat-shop map (4,882 / 182,151) | N | 98 | live | none | Zero `%BEAT%` tables in any schema |
| dsr-cli | GPS attendance punches + selfies (426,055) | N | 99 | live | none | Zero `%ATTEND%` tables |
| dsr-cli | GPS breadcrumb trail (27,026,680) | N | 99 | live | none | Largest table in the fleet |
| dsr-cli | Secondary sales visits (2,128,151) + product lines (685,564) | N | 97 | live | none (OINV is JIVO→customer only) | Distributor→retailer leg has no SAP object |
| dsr-cli | Promoter / merchandiser activity (185,696) | N | 97 | live | none | |
| dsr-cli | Trade schemes / gift issuance (34,236 / 423,785) | N | 90 | live | scheme COST may land as ORIN credit notes | Per-retailer issuance is native; the ₹ may overlap — unreconciled |
| dsr-cli | Targets + precomputed sales aggregates | N | 98 | live | none | |
| dsr-cli | Retailer + distributor channel stock declarations (585,626 / 18,767) | N | 85 | live | none (OITW = JIVO warehouses only) | ~8 C&F / drop-ship warehouses exist in SAP; still not distributor stock |
| dsr-cli | Product catalogue (`tbl_item`, 333 SKUs) | N | 94 | live | OITM (2,269) — same products, separate catalogue | `SAPID` 100% NULL. Match by NAME only |
| dsr-cli | Geography hierarchy (state/zone/area/subarea) | N | 93 | live | OCST partially | |
| dsr-cli | Travel allowance (km rates, distance matrices, TA reports) | N | 90 | live | settled reimbursement lands as a payment | Calculation is native |
| dsr-cli | Portal users / roles / page permissions (87 users) | N | 99 | live | none | |
| dsr-cli | API exception + report-SQL logs (8,543,865 / 952,160) | N | 99 | live | none | Telemetry |
| dsr-cli | Amazon e-com register (13,387 sales / 113,547 settlement lines) | X | 94 | live | none | Amazon MTR schema. **DEAD since 2023-04-30** |
| dsr-cli | Primary sales pre-2026-05 (~11,077 lines) | U | 75 | live | mostly pre-dates SAP go-live | 6,784 JIVO-seller / 838 super-stockist / 3,455 unattributed. No document key. Reconcile against the legacy MSSQL SAP, not HANA |
| ecom-cli | `sap sales-invoices` / `-lines` / `sales-analysis` / platform-sales-invoices | M | 80 | code | OINV/INV1 | UNPROVEN — token 401 all session, backend source on app server. Path params are SAP DocEntry |
| ecom-cli | `sap distributors` / `distributor-orders` | M | 75 | code | OCRD/ORDR | UNPROVEN — `{code}` documented as CardCode; local `distributors` table has 1 row and no CardCode column |
| ecom-cli | `sap items` → `oitm_master` (2,014 rows) | M | 97 | live | OITM | **FROZEN 2026-01-07 12:19:40→12:19:42, one 1.6-sec batch, 204 days stale. Its `onhand` has been wrong since January.** Never read stock from here |
| ecom-cli | `sap stock-by-warehouse` / inventory-* → `warehouse_inventory` | M | 94 | live | OITW | 110 rows, `last_synced_at` 2026-05-17→05-18. **73 days stale, sync dead.** `distributor_inventory` and `in_transit_inventory` = 0 rows |
| ecom-cli | SKU bridge `master_sheet` (834) + realisation / distributor-margin model | N | 92 | live | OITM ItemCode is the only SAP part | JOIN-KEY TRAP: `sku_sap_code` is decoration on an uploaded Excel row |
| ecom-cli | Sales targets (month 61 / primary 47 / call-centre 5) + landing rates (420) | N | 85 | live | none | |
| ecom-cli | Inventory DOH alerts / notifications (3,785) | N | 94 | live | none | threshold/severity/is_read/resolved_at |
| ecom-cli | `product_batches` (78) | N | 96 | live | not OBTN | Every `batch_number` is the literal string `LIVE`; a listing flag |
| ecom-cli | File-upload ingest audit + data-quality (178 uploads / 13,226 errors) | N | 96 | live | none | |
| ecom-cli | In-app chatbot conversations (29 / 392 messages) | N | 97 | live | none | |
| ecom-cli | Pincode ↔ city ↔ state (6,194 / 127,758) + platform city universe | N | 93 | live | CRD1.ZipCode exists, no reference master | |
| ecom-cli | ecom app users / groups / permissions / feature flags | N | 94 | schema | none | |
| ecom-cli | Edit / approval audit trail (`sp_audit_log`) | N | 95 | schema | none | Table is EMPTY in this instance |
| ecom-cli | Shipment planning: truck loads, driver/vehicle, approvals, rejections | N | 60 | live | none | **REFUTED evidence**: `shipments`=1 row, `truck_dispatches`=1, `sp_shipments`=0, `sp_audit_log`=0. The "58 rows" cited was `shipment_items`, a line table. Bucket probably right; confidence collapses |
| ecom-cli | Marketplace secondary sell-out — dark-store grain | X | 96 | live | none | `swiggySec` 634,208 rows w/ STORE_ID/AREA_NAME/GMV; `blinkitSec` 142,038 |
| ecom-cli | Platform inventory SOH/DOH inside marketplace warehouses | X | 96 | live | none | swiggy 93,487 / zepto 47,781 / blinkit 37,933 |
| ecom-cli | Marketplace purchase orders (`total_po` 8,848 + `total_po_zbs` 40,977) | X | 92 | live | none | **3,635 of 40,977 name JIVO MART PVT LTD** — a JIVO company, not a distributor |
| ecom-cli | Amazon Vendor Central POs + inventory health (470,206 staged rows) | X | 92 | schema | none | `sap_sku_code` is a lookup, not provenance |
| ecom-cli | Amazon B2C consumer GST invoices (`amazon_mp`, 8,597) | X | 90 | live | Mart OINV holds a consolidated A/R | **The "₹60 L unexplained gap" does not exist** — `invoice_date` is TEXT `dd/MM/yy` and sorted lexically. Parsed properly, May-26 ties to 2.1%, April to 1.4% |
| ecom-cli | Marketplace ad campaign performance & spend DETAIL (85,985 amazon_ads) | X | 95 | live | none | |
| ecom-cli | Brand-fund / trade-spend attribution by city/SKU/offer (1,521) | X | 88 | live | net may be inside platform A/P or an ORIN | Attribution dimension is not in SAP |
| ecom-cli | Coupons & promotions (2,171) | X | 93 | live | none | |
| ecom-cli | Delivery appointments / slot booking / GRN short-supply / scorecard | X | 95 | live | none | |
| ecom-cli | Competitor & own price / availability scrapes (`reporting.price`) | X | 88 | live | none | rk/jm/svd/bau/art competitor price columns |
| ecom-cli | Meta (Facebook/Instagram) ad campaigns (`meta_data`, 354) | X | 95 | live | none | Not "metadata" — Meta Ads |
| ecom-cli | Is `/api/sap/*` a live proxy or the frozen local tables? | U | 50 | live | n/a | **OPEN — highest-risk item in the estate.** `doctor` returns HTTP 401; backend source not in repo. A stale answer looks identical to a fresh one |
| ecom-cli | `sustain_dist` — "distributor primary offtake by SAP item code" (42 rows) | U | 90 | live | not reconcilable | Per-unit rates match SAP to 0.2–1.4%; quantities diverge in BOTH directions (5,488 vs 29,488). June total ₹2.59 cr vs SAP ₹4.06 cr (63.8%). **Downgraded from M@90** |
| ecom-cli | Generic table browser (`tables data`, ~41 tables) | U | 80 | live | per-table | Inherits the bucket of whatever table is chosen — **including `oitm_master`** |
| exim | Open A/R invoices (Beverages company) | M | 99 | live | OINV DocStatus='O' | 1,168 rows / **₹7,09,68,752.14 paisa-exact**. Cleanest M in the estate. SCOPE TRAP: EXIM reads Beverages; SAP has 12,837 open Oil invoices EXIM never shows |
| exim | Open purchase orders | M | 99 | live | OPOR/POR1 | PO 220426102 PENDING_QTY 0.491 == `POR1.OpenQty`. `OPEN_VALUE` is just qty×price |
| exim | Open A/P invoices | M | 98 | live | OPCH | "DB Primary Key" IS `OPCH.DocEntry` (verified 48578). 171 rows vs 15,934 in SAP — never count with it |
| exim | Vendor ledger balances / balance sheet | M | 98 | live | OCRD.Balance | Byte-identical on sampled vendors |
| exim | Customer / vendor voucher ledger | M | 97 | live | OJDT/JDT1 | Verified VoucherNo 726303912 → OJDT TransId 222946 |
| exim | Customer aging (invoice-level buckets) | M | 93 | live | OINV + OSLP | n=5,002 exactly matches Beverages OINV since FY24 |
| exim | RM / factory inventory by warehouse | M | 97 | live | OITW/OITM grouped | EXIM only rounds |
| exim | Finished-goods inventory | M | 90 | code | OITW/OITM | Ruled by shape-symmetry with the verified sibling |
| exim | Monthly production planning + planned months | M | 99 | live | OFCT/FCT1 | The 7 JSON keys ARE the complete column list of `OFCT`. 24 rows both sides |
| exim | RM/FG item master mirror | M | 94 | live | OITM | STALE (last PRD sync 2026-07-18, manual) and a SUBSET: 22 RM vs SAP 64, 318 FG vs 442 |
| exim | Business-partner mirror (`parties`) | M | 96 | live | OCRD | 138 rows vs SAP's 2,220 Oil vendors (6%). Last PARTY sync 2026-06-12 |
| exim | Domestic-contract PO identity (po_number, po_date, vendor) | M | 88 | live | OPOR | 35/35 PO numbers resolve; but vendor agrees 40/47, item 36/47 |
| exim | Open GRPOs endpoint (documented, NOT wired into the CLI) | M | 85 | schema | OPDN | UNPROVEN — **deliberately not called**: GET with a SAP-refresh side effect. Use `hana-sql` on `OPDN WHERE DocStatus='O'` (356 rows) instead |
| exim | **Transit-shortage / debit register** (per-truck load vs unload, tolerance, chargeback) | **F** | 95 | live | ORPC/RPC1 "SHORTAGE CHARGES" | **REFUTED from N.** SAP holds 544 lines / 164 docs / **₹38,56,015.29** — raised against the **TRANSPORTER**, not the supplier. 18 of EXIM's 63 vehicles match with **penny-identical amounts** (RJ47GA7522 44,638.69 both sides). SAP never gets load/unload MT or the tolerance |
| exim | Import stock lots + 9-stage lifecycle (IN_CONTRACT→…→COMPLETED) | N | 95 | live | none | `OIPF` landed costs exist (525 Oil) but 0 with a BoL, 0 non-INR — it is domestic freight costing, not imports |
| exim | Field-level stock audit trail (`stock-logs`, 1,480 rows) | N | 97 | live | none | old→new per field + free-text note |
| exim | Tanks: master, capacity, level, utilisation, in/out logs | N | 97 | live | none | **Zero `%TANK%` tables and zero `%TANK%` columns in any JIVO schema.** 324 ATC1 filenames matching TANK are all "R.K. TANKER SERVICES" the transporter |
| exim | Tank item master (51 codes, parallel SAP-lookalike namespace) | N | 97 | live | none | RM0EL, RM00CN, RM00CPC… return 0 rows from OITM |
| exim | DGFT Advance Authorisation + DFIA licence register | N | 90 | live | none (@UTL_LICENSE is add-on config) | CAVEAT: the licence's own closure docs ARE in SAP as attachments — "CLOSURE DOCS - 0511015224 - ADV LIC (250 MTS)" |
| exim | Domestic-contract negotiated terms + logistics overlay | N | 90 | live | none | Round negotiated figures vs SAP's executed values. All 4 fields agree on only 10/35 POs |
| exim | Our-Rates pricing engine (commodity margin, packing margin, pack sizes) | N | 86 | live | none (OPLN/ITM1 hold different numbers) | Soya Refined 3.00, Cottonseed 2.00; Pouch 10.00, Tin 14.00 |
| exim | Sync run log (342 runs) | N | 98 | live | none | **All 342 `triggered_by='Manual'` — there is no cron.** Also leaks the architecture: MSSQL linked server `HANADB112` → HANA |
| exim | App users (12 @exim.com) + 49-resource permission map | N | 96 | live | none | |
| exim | Director inventory rollup (finished + at-factory + in-transit) | N | 90 | live | partly OITW | ~87% of the rollup is non-SAP |
| exim | CBIC customs exchange rates (23 currencies × import/export leg) | X | 96 | live | none (ORTT has 1 rate, no legs, no notification) | Notification 22/2026. Duty is assessed at these, not at SAP's rate. **Never substitute** |
| exim | Daily commodity market prices (13 oils, 2,385 rows) | X | 80 | code | none | UNPROVEN — `/daily-price/fetch/` classified as a write, not called. Google Sheet claim is from a SPA-bundle string read |
| exim | `jivo-rate` consumer pack rates | U | 60 | live | NOT price lists 1/3/4 | Proven not-from-SAP; upstream unidentified |
| exim | RM stock & valuation aggregates (`items get-rm` total_qty / rate) | U | 80 | live | reconciles to NOTHING | `total_qty = total_in − total_out` internally, but no SAP month-end matches. **NEVER quote as SAP stock** (RM0000003: EXIM 132,814 vs SAP 177,809) |
| factory-cli | Item master (FG/PM/RM) | M | 96 | live | OITM | `/production-execution/sap/items/` returns raw SAP casing, no renaming |
| factory-cli | Stock on hand by item × warehouse | M | 96 | live | OITW | No stock mirror exists anywhere in `factory_flow` — must be live |
| factory-cli | Inventory movement ledger | M | 93 | live | OINM/OITL | Leaks SAP semantics: reference=DocNum, doc_num=TransNum, created_by=DocEntry |
| factory-cli | A/R sales invoice (the dispatch source doc) | M | 92 | live | OINV/INV1 | `gate_core_salesdispatchgateout` 801/801 born with a `sap_doc_num` = reference, not creation |
| factory-cli | Inventory transfer document | M | 97 | live | OWTR/WTR1 | Row reproduced verbatim incl. Comments. **B1i created 0 of 11,800** |
| factory-cli | Open sales orders backlog | M | 90 | live | ORDR/RDR1 | |
| factory-cli | Batch master + expiry | M | 90 | live | OBTN/OBTQ | **CORRECTED:** `ExpDate` populated on 6,152/17,505 Oil (35%), 810/2,113 Bev (38%), **0/10,076 Mart**. SAP cannot answer an expiry question for Mart at all |
| factory-cli | Production orders + component shortfall | M | 97 | live | OWOR/WOR1 | 7,858 Oil orders live to 2026-07-29. B1i created **zero** — all named humans |
| factory-cli | Vendor master (`po vendors`, 215) | M | 96 | live | OCRD | Returns 2 fields vs OCRD's ~200 |
| factory-cli | Warehouse master + item-group master | M | 97 | live | OWHS (58 Oil) / OITB | |
| factory-cli | Posting config: GL accounts, tax codes, branches, SAC, projects, locations | M | 85 | live | OACT / **OSTC** / OBPL / **OSAC** / OLCT | **CORRECTED:** `OVTG`=0 and **`OPRJ`=0 in all three companies** — the 18 "projects" have NO SAP home. Counts match MART, not Oil |
| factory-cli | Inventory ageing report | M | 92 | live | OITW/OINM/OITM + U_* | days_age computed app-side |
| factory-cli | Sales-planning-vs-requirement | M | 95 | live | HANA proc `SALES PLANNING VS REQUIREMENT_WEEKLY` | **ONLY materialised SAP copy in the app DB. Oil last refreshed 2026-06-16 (44 d), Bev 2026-06-04 (56 d), Mart NEVER** |
| factory-cli | `PRODUCTION_RELEASE_OIL` (Oil-only) | M | 97 | live | custom HANA view over OWOR+OITM | View definition read. Returns `U_BATCH_NO`/`U_MFG`/`U_EXP_DATE` which are **0-populated on all 7,858 orders** — those columns come back blank |
| factory-cli | Bill of materials | M | 90 | live | OITT/ITT1 | Schema-level only; no payload matched |
| factory-cli | Posted GRPO read-back + POs being received | M | 93 | live | OPDN/OPOR | Mixed population — 413 of them were fed in by the app |
| factory-cli | Received-vs-billed reconciliation | M | 80 | code | OPDN vs OPCH | UNPROVEN — endpoint not sampled (401) |
| factory-cli | **Material GRPO posting** (QC-approved receipt → SAP) | **F** | 97 | live | writes OPDN, reads OPOR | 265 postings / 232 with a SAP doc num. **BROKEN: last SAP doc 2026-07-15 10:04; 33 consecutive FAILED since 2026-07-16** ("Attachments folder not defined" → "file uploader authentication failed"). Two weeks of factory receipts exist only in the app |
| factory-cli | **Service / freight GRPO posting** | **F** | 94 | live | OPDN (service) | 158/158 pushed — but **dormant since 2026-06-15**, six-plus weeks. Freight is still being booked in SAP, just not through this pipe |
| factory-cli | **Marketplace fulfilment → Mart delivery notes** | **F** | 93 | live | ODLN (Mart) | **REFUTED from N.** 13 B1i-created ODLN rows, comments literally "MARKETPLACE FLIPKART BULK DELIVERY NOTE · 48 ORDERS"; app has exactly 48 dispatch rows carrying DocEntry 12222. Only 50 of 2,116 dispatches ever posted; module is 10 days old |
| factory-cli | Barcode carton master + box movements + audit log | N | 97 | live | none (`OSRN`=0 all 3) | 301,821 boxes / 791,851 movements / 489,604 audit rows. `U_carton`/`U_cartonpc` are defined on all 32 SAP line tables and **100% empty** |
| factory-cli | Barcode scan events (all families) | N | 97 | live | none | 143,233 + 126,610 + 71,710, growing daily |
| factory-cli | Label print events (308,699) | N | 96 | live | none | |
| factory-cli | Pallets + pallet movements + loose stock | N | 96 | live | none (OPKG/OSHP/OBIN=0) | `barcode_palletmovement.sap_transfer_doc_entry` populated on **0 of 7,120** |
| factory-cli | Scan-to-ship dispatch session | N | 95 | live | would be ODLN if enabled | 185 sessions, all `sap_update_status='NOT_CONFIGURED'`, sync log 0 rows. **Dormant since 2026-06-26** |
| factory-cli | Intercompany carton transfer Oil→Mart | N | 96 | live | none | 3,075 transfers, **0 with a SAP doc num**, `sap_enabled` false on every row. Mart's de-facto FG intake rail |
| factory-cli | Native bin / zone / cell WMS layer (2,468 locations) | N | 93 | live | none (OBIN/OBBQ=0 all 3) | SAP's finest grain is the warehouse |
| factory-cli | Production-run MES detail (segments, OEE, downtime, waste, energy/manpower costing) | N | 94 | live | none | REFINEMENT: `WOR1.U_WASTAGE_QUANTITY` non-zero on 737 of 51,104 Oil lines — a small genuine overlap |
| factory-cli | Production run → SAP receipt | N | 94 | live | OIGN (B1i=0) | 86 runs, 14 carry a `sap_doc_entry` holding only **5 distinct values**; `sap_receipt_doc_entry` NULL on all 86. A push path exists in code and has **never succeeded** |
| factory-cli | BOM request / material issue | N | 95 | live | OIGE (B1i=0) | Single GROUP BY row: `NOT_ISSUED / [] / 72`. Not one has produced a goods issue |
| factory-cli | FG receipt into SAP | N | 92 | live | OIGN | 3 rows, `sap_receipt_doc_entry` NULL on all |
| factory-cli | Production release / approval gate (`PRODUCTIONORDERSYNC`) | N | 95 | live | lives IN JIVO_OIL_HANADB, is not a SAP object | 2,499 rows, `SAPSTATUS='PENDING'` on **all** of them. **"In the SAP database" ≠ "in SAP" — the Service Layer cannot see this** |
| factory-cli | Line clearance sign-offs + machine checklists | N | 93 | live | none | |
| factory-cli | Inbound QC inspection (2-signature chemist + QA manager) | N | 96 | live | @QC_I 19 / @QC_O 6 abandoned | 1,136 inspections, 10,740 parameter readings. Only `sap_*` column across all 17 QC tables is `sap_code` (an item reference) |
| factory-cli | Material arrival slips + CoA / CoQ photos | N | 94 | live | none | `quality_control_arrivalslipattachment` (1,179) has **no sap_* column at all** — while the GRPO module provably DOES push files into SAP. Absence here is meaningful |
| factory-cli | Gate vehicle arrival + weighbridge weighment | N | 96 | live | none | 667 arrivals / 1,720 weighments. `U_Total_Gross_Wt` is defined and **zero on all 11,248 Oil GRPOs** |
| factory-cli | FG gate-out / docking / gatepass / truck photos | N | 94 | live | none | `emptyvehiclegatein` 817/817 **blank** `sap_doc_num` (a verifier's own counter-claim, tested and withdrawn) |
| factory-cli | Docking scan exceptions (partial-scan / skip approvals) | N | 94 | live | none | `sap_doc_num` here is a comma-joined LIST of invoices — a pointer |
| factory-cli | Dispatch plan / bilty / freight / driver (10-stage pipeline) | N | 90 | live | pointer to OINV only | Dormant feeder found: `dispatch_plans_transporterapinvoiceposting` exists with SAP columns and **0 rows** |
| factory-cli | Vehicle / driver / transporter master (512 / 490 / 48) | N | 94 | live | none | Only SAP hits are `U_DriverName` free text and `@SERVER.U_Driver` (a DB driver string) |
| factory-cli | PET bottle blowing + make-vs-buy costing | N | 88 | live | none | 8 runs, **no CLI surface at all**. Ruled from table/column names |
| factory-cli | Maintenance CMMS + EHS (work permits, safety fines, fire, asset photos) | N | 92 | live | none | Sparsely populated; ruled on schema shape |
| factory-cli | Person gate-in (visitors, labour, contractors) + photos | N | 97 | live | none | |
| factory-cli | Notifications / FCM push log (66,874) | N | 97 | live | none | |
| factory-cli | Factory app users / roles / departments / 871-string permission model | N | 95 | live | none (OUSR unrelated) | Backs every created_by/reviewed_by audit field |
| jsap-cli | SAP purchase documents (`po`, `grpo`, `apdraft`, `gr`) | M | 97 | live | OPOR / OPDN / ODRF / ORPD | Rows stamped with `databaseName`. **TWO TRAPS: (a) filtered subset — 10,626 GRPOs vs 15,781 in SAP; (b) documented "Open GRPOs" but every sampled row is `DocStatus='C'`.** SAP has 356 genuinely open GRPOs in Oil |
| jsap-cli | Business partner master + 10 lookup masters | M | 95 | live | OCRD/CRD1, @CHAIN(46), @MAIN_GROUP, OCRG, OCST, OCTG, OPLN | `bpmaster chains` returns exactly SAP's `@CHAIN` |
| jsap-cli | GL account list + budget-vs-actual by branch | M | 97 | live | OACT + JDT1 | **CORRECTED:** the budget-head tagging is SAP's too — `JDT1.OcrCode3` on real posted lines (Factory 1,135 lines / ₹19.30 cr FY26). 100% M with nothing app-side |
| jsap-cli | **Budget head / sub-budget catalogue** | **M** | 98 | live | OPRC dim 3 "Budget" / dim 4 "Sub Budget" | **REFUTED from N.** JSAP's 16 heads are SAP's 16 **ACTIVE** dim-3 cost centres, 16/16 exact — including the active/inactive cut. Prior pass checked `@BUDGET` (a 1-row stub) and never looked at `ODIM`/`OPRC` |
| jsap-cli | Inventory master dropdowns (units, locations, warehouses, item groups, sub-groups) | M | 90 | live | OWHS / OITB / @ITEM_SUBGRP | 17 `JsGet*` stored procedures live **inside the SAP schema** — these screens literally render SAP |
| jsap-cli | SAP document attachment registry / file | M | 95 | live | OATC 76,062 / ATC1 128,739 | The index is queryable; the ~202k files sit on a Windows share. Streaming path UNPROVEN (75) |
| jsap-cli | **A/P invoice budget approval workflow + trail** | **F** | 93 | live | ODRF → OPCH via `draftKey`; trail in `tbl_Draft_Approvals` / `js_budget_approval_workflow` | **SAP ENFORCES IT:** `SBO_SP_TRANSACTIONNOTIFICATION` blocks postings with *"Budget Not Approved for this Entry"*. Corrections: budget attribution DOES survive into `JDT1.OcrCode3`; `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` (29,212) is a truncate-reload whose content is stale to 2026-03-26 — the live twin is the 86-row lowercase table. The ₹393,750 vs ₹425,250 "8% gap" = 18% GST − 10% TDS |
| jsap-cli | Bill-verification vouchers + maker/checker/payment trail (971 bills) | N | 75 | live | none | **These are not JIVO's books** — Baru Sahib / Akal institutional supply. Line items ("Gs Pillow") match 0 rows in OITM in all 3 schemas. N-vs-X (keyed vs imported from Marg/Busy) genuinely **unsettled** |
| jsap-cli | Helpdesk tickets + timeline + comments + attachments | N | 97 | live | OSCL=0, OCLG=0 all 3 | |
| jsap-cli | Task register + progress updates + hierarchy scoping | N | 97 | live | OCLG=0 | |
| jsap-cli | Employee / HO org hierarchy + salary + custom fields + audit log (227) | N | 96 | live | OHEM 17/1/15 stubs, `SUM(salary)=0.00` | >90% of the org chart does not exist in SAP |
| jsap-cli | Sales hierarchy H1→H4 | N | 88 | live | OSLP flat 155; U_UNE_* 0/3,390 | OPEN: is this the same population as DSR's 1,809? A third copy exists in control-panel |
| jsap-cli | Document Hub (folders, versions, activity, confidentiality PIN, backups) | N | 93 | live | none (OATC is a different store) | |
| jsap-cli | Inventory-audit sessions | N | 93 | live | none | Live: **one** session named "abc" from 2025-11-19 |
| jsap-cli | Physical stock count + per-item variance | N | 96 | live | **OINC=0, OIQR=0, ODPS=0 in all three companies** | Carries SAP ItemCode but the count NEVER posts. Textbook joined-≠-sourced-from. **JIVO's book stock is never reconciled to a count via SAP** |
| jsap-cli | QC form template + parameter/sub-parameter tree | N | 90 | live | @QC_O is a different 6-row object | `hanaId: '202'` is an unresolved reference |
| jsap-cli | Permission-scoping catalogues (states, branches, varieties, approvals) | N | 72 | live | OCST partially | Real SAP state codes mixed with synthetic ones (`Centr_z5`) — seeded-copy vs proxy undetermined |
| jsap-cli | JSAP users, roles, effective permissions | N | 92 | live | OUSR = 55, different population | `/UserManagement/AllUsers` is HTML-scraped; no JSON endpoint |
| jsap-cli | IT-standards register / client-project portfolio / MoM | N | 78 | live | OPRJ=0 | All three endpoints live and **EMPTY** — bucket assigned to rows nobody has seen |
| jsap-cli | Physical-bill courier dispatch bundles | N | 72 | code | none | **UNPROVEN — HTTP 500 in all three audits. Nobody has ever seen a row.** U is equally defensible |
| jsap-cli | BP uniqueness checks (contactuid / addressuid / pans) | U | 55 | code | OCPR / OCRD.LicTradNum if implemented | 404/empty on this deployment |
| oms-cli | **Sales order object → SAP Sales Quotation** | **F** | 95 | live | OQUT → ORDR (BaseType 23) | **221/221 SUCCESS doc nums resolve in Oil OQUT**, 214 by `B1i`. **BUT the feed went dark: last B1i quotation Oil 2026-07-25, Bev 2026-07-24, while SAP kept creating 32–46 hand-keyed orders/day.** `sap_doc_entry` in the log is WRONG (says 14584, SAP says 15280) — join on `sap_doc_num` only |
| oms-cli | Quotation open/closed status read-back | M | 88 | live | OQUT.DocStatus | `orders` has 33 columns and none is `quotation_status`, so it must read SAP live — inference, endpoint uncallable |
| oms-cli | Live HANA passthrough (14 `hana *` commands) | M | 70 | code | OITW/OBTN/ORDR/OCRD/OSLP/ONNM | UNPROVEN. `next-doc-number` and `batch-details` are only meaningful against live SAP, but OMS's other "SAP" surfaces are ingested copies, not proxies |
| oms-cli | `sap_parties` mirror (3,350 rows) | M | 96 | live | OCRD | **STRUCTURALLY BROKEN: 3,350 rows over 1,251 distinct card_codes — all three companies flattened with NO company column.** `CUSTA000912` = 3 different parties. No balance, no credit limit, no payment terms. 2 days stale, manual |
| oms-cli | `sap_party_addresses` mirror (35,664) | M | 90 | live | CRD1 (35,701) | Same company-merge defect |
| oms-cli | `branches` mirror (22) | M | 97 | live | OBPL 8+8+6 | Exact |
| oms-cli | `sap_products` mirror + `on_hand` (4,155) | M | 95 | live | OITM / OITW | **RESOLVED:** RM0000052 on_hand 294,992.5245 == SAP `SUM(OITW.OnHand)` to 4 decimals. Fidelity confirmed despite the unidentified MSSQL upstream. Still 2 days stale, manual, `sap_sync_schedules`=0 rows |
| oms-cli | GST e-invoice IRN + e-way bill | M | 94 | live | @UTL_MDEXTH 17,695 (IRN on 15,623) / @UTL_ST_EWAYDT 1,333 | **OVERTURNED from X.** SAP IS the IRN system of record. Prior agent checked `@UTL_EWAY`/`@AUTL_EWAY` (0 rows) — the wrong tables. OMS holds 24 rows; SAP holds 17,695. Reachable **only by direct HANA SQL** |
| oms-cli | A/R invoice module (SAP order → batch pick → post) | U | 80 | live | reads ORDR; claims to write OINV | **REFUTED from F.** All 6 BaseEntry values resolve to real Oil orders — but the SAP invoices against them were created **two months earlier by named humans** (HARPREET, SUMIT), 2 base orders were never invoiced, and zero B1i OINV exist since 2026-04. 19 rows over 5 days. Reads like a UAT run |
| oms-cli | Party ↔ product entitlement + negotiated `basic_rate` | N | 97 | live | **OSPP = 22 rows, all CardCode `*3` (a wildcard) — SAP has ZERO party-specific prices** | 13,383 rows / 1,103 parties / 56 items. Not recoverable from SAP any other way: CUSTA000019 has no invoice lines for those items at all |
| oms-cli | Order approval workflow, rate approvals, status timeline, notifications | N | 96 | live | **OWDD ObjType 17 (SALES ORDER) = 7 requests in 22 months** vs 17,250 stock transfers | SAP is demonstrably not running this queue. NEVER generalise "approvals aren't in SAP" beyond sales orders |
| oms-cli | Sales schemes / free-goods quantity | N | 93 | live | none | TRAP: `U_SchemeAgst` is on 85,819 of 96,900 INV1 lines but has **41 distinct values, all product categories** (OLIVE, CANOLA, MUSTARD). It's a costing tag. `SALES_ANALYSIS.SchemeQty` = 0 on all 1,299 rows |
| oms-cli | SAP-sync run history (`sap_sync_logs`, 367 runs) | N | 96 | live | none | `sap_sync_schedules` = **0 rows**; 313 of 367 runs `triggered_by='manual'`. **Read this before trusting any OMS mirror.** Last sync 2026-07-28 (not 07-16) |
| oms-cli | Inbound vendor-invoice tracker (8-stage, ends "Save in SAP") | N | 88 | live | none | Production `order_management` holds **13 invoices / 68 stage events**. Schema is real; the module is essentially unused |
| oms-cli | SKU images + label artwork / nutrition | N | 95 | live | `OITM.PicturName` on 1 of 2,269 items | 96 label PDFs with nutrition JSON |
| oms-cli | Field-level UI audit log (13,347 rows) | N | 95 | live | none (ADOC covers SAP docs only) | |
| oms-cli | Device fingerprints, push tokens, session state | N | 97 | schema | none | |
| oms-cli | App users, roles, page permissions, territory scoping | N | 96 | live | OUSR is a different population | **SECURITY: `GET /api/auth/users/list/` returns pbkdf2 password HASHES to any authenticated caller, and they are cached in `~/.local/share/oms-pp-cli/data.db`** |
| oms-cli | Dashboard KPIs and chart series | N | 85 | code | none | Aggregates over OMS's own order population — **will NOT tie to SAP turnover** |
| oms-cli | Dispatch-from locations | U | 55 | live | OWHS? | 4 seed rows (WH-DEL/WH-GGN/WH-NOI/FAC-BGH) that match no OWHS code, while push payloads use SAP's `GP-FG`. Dev-instance artefact — **do not rule without a production call** |
| portals/blinkit | Blinkit seller-portal ops (PO, GRN, appointments, invoices, charges, UTR, offers, assortment, SOH, scorecard) | X | 94 | code | none; counterparty VENDA000849 (a **vendor**) | **SAP has ZERO Blinkit A/R in Oil and Mart; 6 invoices in Beverages only.** No live portal call (OTP). The `brands.blinkit.com` ADS portal is documented but **not wired into any CLI** |
| portals/zepto | Zepto seller-portal ops (PO, ASN, RTV, catalog health, dark-store stock, contracts, payments, ledger, FBZ, ads, KYC) | X | 93 | code | CUSTA000722 A/R 237 invoices ₹4.91 cr (Mart only, nothing since 2026-06-18) | 407 read commands over 7 hosts, 0 SAP references. No live call (OTP) |
| portals/tankhapay | Employee master (593 active / 1,795 total) | N | 85 | live | OHEM 17/1/15, `SUM(salary)=0.00` | App half INHERITED — portal unreachable. SAP half is mine |
| portals/tankhapay | Attendance, biometric punches, shifts, GPS km | N | 90 | schema | none | Zero attendance tables in 9,244 SAP tables. 57 ATC1 attendance attachments exist as PDFs |
| portals/tankhapay | Payroll run + per-employee payout + piece-rate | N | 93 | live | `5630001` has ONE distinct ShortName across 1,648 lines | Only 25 of 1,648 salary lines point at a named employee account (15 people). No per-employee payroll in SAP |
| portals/tankhapay | Leave applications, balances, policies, holidays | N | 95 | schema | none | Only 2 LEAVE-named attachments in all of Oil |
| portals/tankhapay | Recruitment / ATS | N | 92 | schema | none | GAP: nobody swept ATC1 for offer letters / CVs |
| portals/tankhapay | Training / LMS / performance (separate `tnd` backend) | N | 92 | code | none | 4th backend confirmed in `config.go:29` |
| portals/tankhapay | HR masters, org units, roles, app config | N | 93 | live | ODPT=0, OPOS=0 all 3 | SAP has no designation list |
| portals/tankhapay | Contract-labour headcount + employee-issued assets | N | 90 | live | `@ZIA_ASSET_ISSUE_I/O` exist with **0 rows** | Built, never used. Contractor *payments* land as ordinary vendor A/P |
| portals/tankhapay | Employee tax regime / rent / home-loan / investment proofs / Form 16 | N | 92 | live | `2133004 TDS ON SALARY` aggregate only | |
| portals/tankhapay | Visitor gate log, broadcasts/campaigns, help-desk tickets | N | 94 | live | OCLG=0, OSCL=0 all 3 | |
| portals/tankhapay | HR reports & dashboards (53 commands) | N | 85 | live | none | Derived; figures INHERITED, not re-verified |
| portals/tankhapay | **Imprest applications + approval trail** | **F** | 72 | live | attached to OVPM as documents | **REFUTED from N — AND IT CONFLICTS.** The finance verifier upheld N@94; the HR verifier found 239 IMPREST-named ATC1 files hanging off 1,923 employee payments across 263 employees, with filenames like *"Request for Advance Salary Approval - Hardeep (Driver)"*. But they are Gmail print-to-PDF, so **TankhaPay origin is unproven** — the approval may be a parallel email process. Rule 1 gives F; treat the provenance as open |
| portals/tankhapay | **Reimbursement claims, travel, meal vouchers, approval hierarchy** | **F** | 70 | live | attached to OVPM as documents | Same refutation, same conflict. 785 CLAIM- / 1,766 EXPENSE- / 171 CONVEYANCE-named Oil attachments, per-employee per-month ("Neha April Conveyance"). Not queryable as data |
| postsql | Raw Postgres access to 15 live DBs (21 commands + MCP) | U | 93 | live | n/a | **A transport, not a source.** Its bucket is whatever DB you point it at. Adds audit_log, sap_sync_logs, soft-deleted rows and backup copies the app APIs never expose |
| postsql | `jivo_site` — website visitors, sessions, analytics, consent, chatbot, AI executions (40 tables) | N | 96 | schema | none | |
| postsql | `CRM` — customer complaints (Django) | N | 85 | schema | OSCL=0 (Service Calls unused) | Tiny; may be abandoned |
| postsql | `Ecommerce.Mapping_skumapping` — a SECOND platform↔SAP SKU bridge (587 rows) | N | 88 | live | none | **Competes with `product-identity` v1 and nothing reconciles them.** Two disagreeing SKU bridges is a silent-wrong-number generator |
| postsql | `fs` — factory system v2 (gate-in 177 rows, production 0) | U | 70 | live | some tables carry `sap_code` | Too empty to characterise |
| postsql | `task` / `po_db` — 0 tables | U | 60 | live | n/a | Dead, or backing an app nobody found |
| jivo-scraping (`jivo-desk`) | Daily price + availability sweeps, 10 platforms × pincode; price-match; DRR panel | X | 88 | live | **none — SAP has no price-observation object of any kind** | Files on the VPS, fresh to 2026-07-29. The one dataset SAP could never in principle contain |
| product-identity | Released listing↔SAP-item bridge (7.8 MB map, attested release 2026-07-19.1) | U | 50 | code | OITM ItemCode qualified by company schema | **NOT A DATA SOURCE — infrastructure.** And **NOT VERIFIED by anyone**: the release, the 333 resolutions and the 1,906 Factory items were never opened in the verify pass. Its SAP half is fetched *through* factory.jivo.in, inheriting that app's lag |
| SAP only (no CLI) | SAP-native document approval requests (OWDD 57,741 / WDD1 57,752) | M | 97 | live | OWDD/WDD1 | **Overturns the domain prior:** SAP DOES retain approvals incl. 1,000 rejections and 1,671 pending, live to 2026-07-29. Reachable via `sapb1 query ApprovalRequests`. But it holds *state*, not *history* — `OWDD_LOG`/`WDD1_LOG` = 0 |
| SAP only (no CLI) | SAP-native change log — who changed which document/BP/item and when | M | 96 | live | ADOC 43,054 / ADO1 188,592 / ACRD 18,311 / AITM 11,286 | **REAL TOOLKIT GAP: a repo-wide grep for `ADOC` returns ZERO hits in any CLI or doc.** Cheapest high-value addition available |
| SAP only (no CLI) | Vendor + customer onboarding portal (`ZVENDOR_PORTAL` 49 / `ZCUST_PORTAL` 17) | F | 92 | live | creates OCRD; lives IN the SAP schema, is not a SAP object | **Cleanest F evidence in the business:** APPROVED 44+12 carry a `SAP_CARD_CODE`; REJECTED 3+3 and PENDING 2+2 carry none. GSTIN, PAN, TDS/LDC, MSME, FSSAI, bank accounts, attachments, full review trail. **No CLI in this repo reads it** |
| SAP only (no CLI) | WhatsApp approval notification + action log (`JIVO_WA_MESSAGE_LOG` 5,941 / `JIVO_WA_SENT` 641) | N | 92 | live | none | SENT 5,918 / FAILED 23, but only **4 distinct phones and 3 approvers** — a narrow pilot. 38 of 641 reference approvals SAP no longer has |
| SAP only (no CLI) | Credit-limit change requests (`tbl_customerLimit`, 35 rows) | U | 88 | live | claims to target OCRD.CreditLine | **REFUTED from F.** 0 of 17 `NewLimit` values match `OCRD.CreditLine` **or** `DebtLine`; no procedure or view anywhere depends on the table; dead since 2025-05-09; `CurrentLimit` is 0 or 10 on every row. No push path found → U, not F |
| SAP only (no CLI) | Bill of Entry / Bill of Lading on the A/P invoice | M | 98 | live | OPCH.U_LRNUmber (789/15,934), U_BOEDate (757), U_InvRevEntry (182) | The ONE import fact SAP holds. Hand-typed and dirty (`5976233)`, `6720426,6815125`). 413 ATC1 filenames also carry assessed BoE copies |
| SAP only (no CLI) | General ledger, journal entries, chart of accounts | M | 97 | live | OJDT 132,621 / JDT1 513,596 / OACT 1,424 | JDT1 also carries the full cost-centre grid (ProfitCode, OcrCode2 month, OcrCode3 budget, OcrCode4 sub-budget, OcrCode5 salary category) |
| SAP only (no CLI) | Party ledger balances (customer + vendor outstanding) | M | 97 | live | OCRD.Balance | `DebtLine` is set to 10 for everyone by a hard-coded procedure — it is NOT a meaningful per-party limit |
| SAP only (no CLI) | Vendor / outgoing payments (OVPM 14,356 / VPM2 11,469) | M | 96 | live | OVPM | **No app CLI exposes it** — but `sapb1 query VendorPayments` works and is documented |
| SAP only (no CLI) | SAP drafts — pending pre-posted documents (ODRF 47,609, 3,803 open) | M | 97 | live | ODRF | Second overturn of "pending never reaches SAP" |
| SAP only (no CLI) | SAP budget module (OBGT 164 / BGT1 1,968 / OBGS 267, Oil) | M | 85 | live | OBGT/BGT1/OBGS | **MISSED by phase 2 entirely.** A GL *cost* budget. Decaying: FY2026 has 4 rows and several amounts are visible junk (₹5,555 cr on freight) |
| SAP only (no CLI) | Employee imprest / advance LEDGER — balances and movements per person | M | 96 | live | 402 employee GL accounts + 510 employee BP cards + `REPORT_EMP_IMP` | 2,041 JDT1 lines / 317 employees, live to 2026-07-23. **242 accounts also carry the employee's bank account + IFSC.** TankhaPay has the request; SAP has the money |
| SAP only (no CLI) | Advertising & platform-charge MONEY (A/P to Amazon/Flipkart/Meta/Google/Blinkit/Zepto/Swiggy) | M | 95 | live | OPCH | Amazon Seller Services 213 inv / ₹5.67 cr; Flipkart 164 / ₹2.63 cr; Blink 19 / ₹2.46 cr. **Meta also has 58 invoices in Mart — 326 total, not 268** |
| SAP only (no CLI) | Marketplace & distributor counterparty ledgers and balances | M | 94 | live | OCRD + OINV | **CORRECTION:** R K WORLDINFOCOM is 1,296 invoices / ₹93.6 cr since 2025-04, not "505 / ₹31 cr". And BigBasket (CUSTA000496) has 206 Oil + 65 Mart invoices — SAP DOES sell to BigBasket and Zepto directly |
| SAP only (no CLI) | JIVO-owned e-commerce / FBF / dropship warehouse stock | M | 95 | live | OITW at DL-EC, GP-ECM, FBF-HR, KT-FBF, DP-* | Stops "platform inventory is X" being misread as "JIVO has no e-com stock in SAP" |
| SAP only (no CLI) | Monthly salary + statutory COST by GL / department / budget head | M | 60 | live | 5630001 + 2161001-12 + EPF/ESIC/TDS/gratuity | **UNPROVEN.** 1,648 lines, dimensioned, live to 2026-06-30 — but if an accountant re-keys a TankhaPay total, this is a **manual F**, and TankhaPay was unreachable so nobody compared the numbers. "Not F because there is no automation" is not evidence |
| none (gap) | Purchase requisition / indent / pre-PO approval stage | N | 99 | live | **OPRQ=0, PRQ1=0, OPQT=0, ODPO=0 in all three companies** | SAP's purchase trail begins at the PO. Whatever runs indent-to-PO is N or F, never M — and no CLI here owns it |

---

## 5. SURPRISES — things that contradict the repo docs or common assumption

1. **SAP's books start ~Oct 2024.** Earliest `OINV` 2024-09-30, `ORDR` 2024-10-01, `OJDT` 2024-08-01
   (opening batch). **Every M ruling needs a date window.** The pre-2024 SAP (MSSQL,
   `Jivo_All_Branches_Live`, 68,070 invoices 2019-08→2024-10) is **still online** on the DSR box.
2. **76% of SAP is empty** — 3,111 tables in Oil, 746 populated. A table existing proves nothing.
3. **SAP's approval engine is live and rich** (`OWDD` 57,741, 1,000 rejections) — the whole fleet
   assumed "SAP doesn't keep approvals". It does, for purchase and inventory. It does **not** for
   sales orders (7 requests in 22 months).
4. **`U_OMS_Order_No` is operator-typed garbage.** 6,253 of 14,736 Oil orders carry it, but only
   **746 distinct values**, dominated by `4563` ×750, `1234` ×639, `123` ×225, `1111` ×161.
   `U_OMS_REF` is populated on exactly **1 row** ever. **There is no field in SAP that joins an OMS
   order to a SAP document.**
5. **The OMS→SAP quotation feed went dark.** Last `B1i` quotation: Oil 2026-07-25 (1), Bev
   2026-07-24 (2), against 8–30/day before. SAP kept creating 32/46/42 hand-keyed orders on
   07-27/28/29. Nobody has explained why.
6. **The factory GRPO feeder has been down 15 days.** Last SAP doc 2026-07-15 10:04; 33 consecutive
   FAILED postings since ("Attachments folder not defined" → "file uploader authentication failed").
7. **`OPRJ` (projects) = 0 rows in all three companies** — yet factory's posting-config endpoint
   serves 18 "projects". They have no SAP home.
8. **JSAP created its own tables INSIDE the SAP HANA schema** — `JS_SYNC_BUDGET_APPROVAL_WORKFLOW`
   (29,212), `tbl_Draft_Approvals` (1,440), `PRODUCTIONORDERSYNC` (2,499), `ZVENDOR_PORTAL` (49),
   `JIVO_WA_MESSAGE_LOG` (5,941). **"In the SAP database" ≠ "in SAP"** — the Service Layer and
   `sapb1` cannot see any of them. Only direct HANA SQL reaches them.
9. **And SAP enforces the JSAP budget feeder.** `SBO_SP_TRANSACTIONNOTIFICATION` — SAP B1's own
   posting hook — reads `tbl_Draft_Approvals` and refuses expense postings with *"Budget Not
   Approved for this Entry"*.
10. **JSAP's budget catalogue IS SAP** (`OPRC` dimension 3, literally named "Budget", 16/16 exact
    including the active/inactive cut). Phase 2 ruled it N because it checked a 1-row stub UDT.
11. **`OINC`/`OIQR`/`ODPS` = 0 in all three companies.** JIVO's book stock has never been
    reconciled to a physical count through SAP's own mechanism.
12. **EXIM reads TWO SAP company databases** — A/R from Beverages, everything else from Oil.
    Undocumented anywhere before this exercise.
13. **`OSPP` (BP special prices) holds 22 rows in Oil and all of them use CardCode `*3`, a
    wildcard.** SAP has literally **zero** party-specific prices. OMS has 13,383.
14. **`OCRD.U_UNE_RSM/ASM/SO/SR/ZONE/AREA` exist and are 0% populated across 3,390 partners.**
    Anyone grepping SAP columns would wrongly conclude SAP holds the sales hierarchy.
15. **Bilty / transporter / vehicle / driver ARE SAP user fields** on `OINV` — the reverse trap.
    But driver name is on 1.6% of Oil invoices and LR number on 0.14%.
16. **`ecom.oitm_master` is frozen in a 1.6-second batch on 2026-01-07** and its `onhand` column has
    been wrong for 204 days. It will answer a stock question confidently and incorrectly.
17. **The ₹60 lakh Amazon "gap" was a text-sort artifact.** `invoice_date` is TEXT `dd/MM/yy`; a
    `>= '2026-05-01'` filter matched nothing and MIN/MAX sorted lexically. Parsed properly the
    months tie to 1.4–2.1%.
18. **The DSR "primary sales are a SAP mirror" reversal was itself reversed.** 55% of rows in the
    ruled window (72% in July) have a **super-stockist** as seller, selling to sub-distributors SAP
    has never invoiced (`DEEPAK TRADING COMPANY PATIALA` = 0 SAP invoices ever).
19. **The transit-shortage register IS in SAP** — as A/P credit memos against the **transporter**,
    not the supplier. ₹38.56 lakh, 544 lines, with truck numbers embedded in the line description
    and **penny-identical amounts** on 18 matched vehicles.
20. **`factory-cli/DATA-MODEL.md` says "0 GRPOs have ever been posted".** 232 are posted and five
    were resolved in SAP. Doc loses to live, again.
21. **`postsql/README.md` claims 16 databases; live `postsql dbs` returns 15.**
22. **`sap-b1/README.md` line 59 is wrong about where `sapb1` reads `.env`** (current directory, not
    the binary's), which produces a misleading "missing config" error.
23. **The launch briefing's claim that the SAP Service Layer was unreachable was false** — a tunnel
    on `127.0.0.1:15000` works. And `connections/hana.env` **hangs silently**; you must pass
    `-env connections/hana-tunnel.env`.
24. **SECURITY (out of scope, raise anyway):** OMS `GET /api/auth/users/list/` returns every user's
    pbkdf2 password hash to any authenticated caller, and those hashes sit in the local SQLite
    cache. Separately, `@SERVER` (HANA user + password), `OLCT.U_CID/U_SECRET` and
    `ZCUST_USERS.PASSWORD` store credentials inside the production SAP database.
25. **Two competing SKU bridges exist and nothing reconciles them** — `product-identity` v1 (333
    listing resolutions, SHA-256 attested) and `Ecommerce.Mapping_skumapping` (587 rows).

---

## 6. COVERAGE GAPS — blunt

**Systems that could not be reached at all:**
- **TankhaPay** — no built binary, OTP/login required. All 13 HR entity rulings rest on endpoint
  names + code + the SAP-side absence proof. **Not one HR row was ever read.** The 593/248/1,795
  figures are inherited from a single earlier dashboard call.
- **Blinkit and Zepto portals** — OTP login. Zero live calls in the entire exercise. 445 commands
  ruled X from code and counterparty checks alone.
- **factory-cli, oms-cli, ecom-cli app APIs** — every stored JWT expired. All app-side evidence is
  Postgres + code + a frozen 2026-07-13 capture. **No live app API call succeeded anywhere.**
- **control-panel** — unreachable in the mapping and adjudication passes; reachable in one verify
  pass, which is how the claims register and 0%-populated ageing remarks got tested.
- **DSR web portal** — no app credential exists.

**Entities that are UNPROVEN and must not be treated as answered:**
- Whether ecom `/api/sap/items` and `/api/sap/stock-by-warehouse` proxy SAP live or serve the frozen
  local tables (204 d / 73 d stale). **Highest-risk open item.** A stale answer looks identical.
- ecom `sap sales-invoices` / `sales-analysis` / `distributors` — M by inference from path
  parameters and negative space, never a row.
- OMS `hana *` passthrough — M by endpoint semantics, never called.
- Control-panel realise analytics — inputs proven SAP, but a naive re-aggregation diverges ~30%.
- Wellness↔Mart reconciliation, received-vs-billed, JSAP attachment streaming, EXIM open-GRPOs,
  daily commodity prices, control-panel rate lists, JSAP courier bundles (HTTP 500 in **three**
  audits — nobody has ever seen a row).
- Monthly salary cost M-vs-manual-F. Nobody compared a TankhaPay payroll total to SAP's.

**Entities never examined by anyone:**
- **`product-identity`** — the attested map, its 333 resolutions and 1,906 Factory items were never
  opened in the verify pass. U@50 is a non-claim.
- **control-panel `COGS`** — OTP-gated, never probed. Could be M or N.
- **Blinkit ads portal (`brands.blinkit.com`)** — documented in the vault, wired into **no CLI**.
  Blinkit ad spend has no command surface anywhere in the repo.
- **JSAP's own application database** — never inspected. Likely MSSQL on 103.89.45.75. Every JSAP N
  is "proven not in SAP", not "observed in its home store".
- **The control-panel Django database** — never located. Not in the Postgres cluster, engine unknown.
  Same negative-space caveat.
- **The MSSQL "SAP" at 103.89.45.75** that OMS actually syncs from (proven by a DB-Lib error). Not
  the HANA at 103.89.45.192 this repo queries. Whether it is a SAP B1-on-MSSQL company DB, a replica
  or middleware is **unknown** — though a value match (OMS `on_hand` 294,992.5245 == SAP OITW to 4
  decimals) shows the numbers are SAP's whatever the pipe.
- **ATC1 attachment content.** ~202k scanned files sit on a Windows share outside the database.
  Several rulings turn on filenames only; nobody opened a file. This is how imprest/reimbursement
  flipped to F on 70–72 confidence.

**Rulings that rest on doc evidence only (weakest tier):** control-panel `sales-pulse` (M@85),
control-panel required-credit-limit lock (partly), JSAP courier bundles, OMS device telemetry,
several TankhaPay module rulings.

**Known conflict left standing:** the finance verifier upheld TankhaPay imprest/reimbursement
approvals as **N@94**; the HR verifier refuted them to **F@70–72** on ATC1 filenames. Rule 1 gives
the refuter the verdict, so they appear as F — but the HR verifier itself states it cannot prove
TankhaPay is the origin rather than a parallel email approval chain. **They are excluded from the
genuinely-new-data list for that reason.**

**Methodological limit that applies to everything:** integration direction was inferred from
`UserSign`/`B1i` in most cases. An integration authenticating as a named SAP user would be invisible
to that test. "Zero B1i rows" is evidence of absence only if every integration logs in as `B1i`.

---

## 7. RECOMMENDED NEXT PROBES — ranked

1. **Get a fresh ecom token and diff `sap items --json` against `oitm_master`'s frozen `onhand`.**
   If they match, the endpoint is serving January stock. One call settles the estate's biggest risk.
2. **Fix or escalate the factory GRPO feeder.** 33 consecutive failures since 2026-07-16; two weeks
   of receipts are app-only. The error text names the cause (attachment folder / uploader auth).
3. **Find out why the OMS→SAP quotation feed stopped on 2026-07-24/25.** Compare OMS order counts to
   SAP `ORDR` for the last week.
4. **Add an `ADOC` reader to `sapb1`.** Nothing in this repo can answer "who changed this invoice and
   when", and SAP has 43,054 header + 188,592 line change records.
5. **Expose `ZVENDOR_PORTAL` / `ZCUST_PORTAL` read-only.** Rejected and pending vendor applications
   are invisible to every tool Accounts has.
6. **Identify the MSSQL at 103.89.45.75** that OMS calls "SAP".
7. **Reconcile the two SKU bridges** (`product-identity` v1 vs `Ecommerce.Mapping_skumapping`).
8. **Open five ATC1 imprest/conveyance PDFs** and settle whether TankhaPay is their origin. That
   flips two F rulings back to N — or confirms a manual feeder nobody has documented.
9. **Fix the OMS mirror's company collision** — `sap_parties` needs a company column, or the mirror
   should be dropped in favour of `hana-sql`.
10. **Build the TankhaPay binary and pull one payroll register**, then compare its monthly total to
    SAP `5630001`. Settles M-vs-manual-F on the largest unproven money entity.
11. **Sweep ATC1 for offer letters / CVs** before calling recruitment a clean N.
12. **Enumerate all 58 Oil warehouse codes** against DSR's channel-stock parties to close the last
    "is there a virtual distributor warehouse" doubt.

---

## 8. WHAT DAMAN SHOULD ACTUALLY DO

- **Ask SAP (`sapb1` / `hana-sql`) for:** every balance, invoice, order, receipt, payment, journal,
  stock figure, batch, production order, transfer, BOM, GL, budget head, approval state, and the
  IRN/e-way record. Every app copy of these is a lossy, stale subset of the same rows.
- **Never quote as SAP numbers:** EXIM `items get-rm` stock aggregates, ecom `oitm_master.onhand`,
  ecom `warehouse_inventory`, OMS `sap_parties` (wrong party 2 times in 3), control-panel realise
  headline figures, JSAP document counts, DSR `sap_sales_log` joins to live SAP.
- **The apps you cannot replace:** DSR (field force, outlets, GPS, secondary sales), factory-cli
  (cartons, scans, QC, gate, MES), EXIM (imports, tanks, licences), TankhaPay (all of HR), OMS
  (distributor entitlement + rates, order approval), the marketplace stack (everything).
- **Three things are silently broken right now:** the factory GRPO feeder (15 days), the OMS→SAP
  quotation feed (6 days), the ecom stock sync (73 days). Nobody was watching any of them.
