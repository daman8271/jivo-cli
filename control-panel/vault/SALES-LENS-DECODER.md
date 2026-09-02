---
title: SALES-LENS DECODER — read SAP the way JIVO's sales team does
type: reference
tags: [jivo, control-panel, sales-lens, sap, decoder]
generated: 2026-08-25
source: multi-agent workflow wf_0577d5fd-826 (18 Opus agents, 426 live tool calls); every mapping reconciled against live SAP B1 + the live Control Panel (http://138.252.101.118:9080, login preshit, read-only)
---

> **What this is.** The JIVO **Control Panel** ("god software") is the *sales team's* semantic layer over live SAP B1 — SAP's numbers re-expressed in their language (realise, OIH, DRR, channels, boxes, targets). This decoder lets an AI answer a SALES question the sales team's way, with the exact SAP lineage behind every term. Built by reverse-engineering the live app + SAP, **not** from memory — see the live-verification appendix at the end for the reconciliations.
>
> **Host note:** the app moved to `http://138.252.101.118:9080` (the ARY box); the old `103.89.45.75:9080` in the legacy vault is DEAD. The `jivo` CLI (`control-panel/cli/jivo`) speaks to it; money panels (₹ sales / COGS / expenses / salaries) are blank under the `preshit` login.

# JIVO Sales-Lens Decoder

The **Control Panel** ("god software", live at `http://138.252.101.118:9080`) is a Django **semantic layer the JIVO SALES team runs over live SAP B1**. It re-expresses SAP's invoices, orders, stock and ledgers in the team's own language — litres, boxes, channels, targets, realise — and staples on app-only data (targets, claims, credit locks) that SAP never held. Its centre of gravity is **REALISE — net ₹ per litre earned** (Σ net line value ÷ Σ litres); the app, the API (`/realise/…`) and the KPI are all named for it. **Governing rule: when you answer a SALES question, use the sales-team definitions captured here, not the raw Accounts definitions.** They diverge most on three axes: (1) **REALISE** is a ₹/L *rate*, not the ₹ *turnover total* Accounts means by "sales"; (2) **intercompany** — the Control Panel *includes* JIVO MART / WELLNESS everywhere, the exact mirror of Accounts turnover which *excludes* the ~23 group CardCodes (**C-0005**), so a single Oil→Mart transfer can be ~70% of a day's "sales" or ~75% of the OIH book; (3) **DONE / OIH** are read as **gross-of-returns VOLUME** (litres, boxes, pieces), not net rupees. Everything below was verified live **2026-08-25** against both the Control Panel (login `preshit`) and SAP B1 (`138.252.101.222:50000`, login `manager`); reads only.

## Master glossary

One alphabetized table of every sales-team term across all eight domains (realise · sales-detail · OIH · accounts · targets · inventory · taxonomy · beverages/COGS). Where a name means different things in different feeds, the row says so. `U_*` = a SAP User-Defined Field.

| Term | Meaning (sales lens) | SAP source |
|---|---|---|
| **Aging buckets** (`b0_30 … b121`) | Balance by overdue age: 0–30 = current, 121+ = seriously overdue. Oil derived client-side from `days`; Mart/Bev arrive pre-bucketed from the server. | Age of `OINV` open docs vs `as_of` |
| **Aging Remark / Special Price** | Per-invoice note/price overlay in the Oil & Bev RAW workspaces; write-only, ~0% populated, SAP untouched. | Django overlay (`aging-remark*`) — no SAP field |
| **available / all_wh / onhand** | Component stock in the *selected* warehouses / across *all* warehouses / in the BOM's primary warehouse; `available` drives Balance & Max FG. | `OITW.OnHand` sliced by warehouse set |
| **BAL / BAL W/O OIH / BAL RLZ** | Gap to target: BAL = TGT − DONE; W/O OIH also subtracts the open order book; BAL RLZ = ₹/L still required on the balance. All client-side. | Derived (TGT app-side; DONE from `OINV`/`INV1`; OIH from `ORDR`/`RDR1`) |
| **`bal`** (Oil aging) | Gross unpaid residual of ONE open invoice (always ≥ 0); **Σ `bal` = the aging "Total Outstanding" KPI**. Not the same as `outstanding`. | `OINV` open-document residual |
| **BALANCE / ledger balance** | Party's current net ledger; **positive = DEBIT** (party owes JIVO), negative = credit/advance. | `OCRD.CurrentAccountBalance` (proper ledger via `JDT1`, C-0023) |
| **Balance Due** (Mart/Bev aging) | Customer's net open balance split into 5 age buckets that sum to it; buckets can go negative for advances/CNs. | `BusinessPartners.CurrentAccountBalance`, bucketed by invoice age |
| **BEVERAGES** (segment / dataset) | Juices / wellness-drinks / water business — a **separate company book**, not a toggle over Oil; reported in boxes, with its own sales/OIH/aging. | Whole `JIVO_BEVERAGES_HANADB` company DB |
| **Bilty / Dispatch** | Physical-shipment metadata per invoice (dispatch date, bilty = lorry receipt, transporter, vehicle, driver mobile). "Dispatched" KPI = non-empty bilty. | SAP UDFs on `OINV`: `U_Dipatch_Date`, `U_BiltyDate`, `U_BilltyNumber`, `U_TransporterName`, `U_VehicleNoM`, `U_Mob_No` |
| **Boxes** | Carton count = pieces ÷ pcs-per-box; the headline **beverages** measure (oils use litres). | pieces ÷ `OITM.SalesFactor2` |
| **BRAND** | Product brand tag on beverage lines; only `JIVO` seen live. | Beverage item brand attribute |
| **B2B / B2C** (Mart only) | B2B = customer has a GSTIN on file; B2C = none. Only Mart exposes the split. | `OCRD` GSTIN present / absent |
| **Chain nodes** (PO→SO→GRPO→A/P→A/R) | The intercompany Mart↔Wellness paperwork chain; live rows also carry CN and delivery nodes; partials summed per node before comparison. | `OPOR`→`ORDR`→`OPDN`→`OPCH`→`OINV` (+`ORIN`, `ODLN`) |
| **Channels** (GT / MT / ROI / ECOM / HORECA / CSD / REST) | Go-to-market segments. GT = General Trade, MT = Modern Trade, **ROI = Rest of India (geography, NOT return-on-investment)**, ECOM = E-commerce/q-commerce, HORECA = hotels/restaurants/catering, CSD = Canteen Stores Dept, REST = residual. | Grouped by `OCRD.U_Main_Group` |
| **channel-docs** | Documents behind a Slide-2 channel card: invoices (done) or open SOs (oih); `stock[]` aligns to `warehouses[]`. Needs `--start/--end` or returns empty. | `OINV` (done) / `ORDR`+`RDR1` (oih) |
| **Claim for Services / `cns_rev`** | Money-only credit note (discount, FOC, sample, scheme claim); no quantity. | `ORIN`/`RIN1` service / non-inventory lines |
| **Claims** | Hand-keyed register of customer claims (NSO/TOT/LOTS/QPS/FIXED-BONUS/support…) with a pass/hold workflow; **not a SAP feed**. | None — Django-only (`ref_inv_no` resolves in no SAP company) |
| **CN for Goods / `cng_rev`** | Credit note for physical product returns (carries a returned qty). | `ORIN`/`RIN1` inventory lines |
| **COGS** | Cost of goods sold (net sales − COGS = gross margin). **OTP- + permission-gated; fully blank (HTTP 403) for `preshit`; no CLI command exists.** | `INV1.GrossBuyPrice` × `Quantity` (+ `GrossProfit`, `COGSAccountCode`…); CP `GET /api/cogs/` |
| **Compare Sales / compare-docs** | Month-over-month oil pivot of Litres/Realise by channel/state/territory-owner/product; click a cell to drill to invoices. Oil only; grid and drill are two endpoints. | grid `/realise/api/sales-data/`; drill = `OINV`/`INV1` |
| **Contact Person / territory owner** | Assigned owner from a client-side `main_group × state → owner` territory map (e.g. E-COMMERCE→PRABHU SIR), **not** the raw SAP invoice person UDF (the UI ignores it). | App-side map over `OINV` main_group/state |
| **Credit Lock** | Manager freeze of Total Outstanding & Required Limit for N days (default 30); a Django flag, **not** SAP's `OCRD` freeze. | Django-only |
| **Credit / Payment Terms** | How long a party may take to pay (ADVANCE/CASH, COD, CAD, NET-01…NET-30, LC 60…); drives what counts as overdue. | `OCRD` payment-terms group (`PayTermsGrpCode` → `OCTG`) |
| **CREDIT LIMIT** | Sanctioned ₹ credit ceiling; `0` = no limit set. | `OCRD.CreditLimit` (not `CreditLine`) |
| **Customer Aging** | A/R book split into overdue buckets per company; Oil = flat per-open-invoice feed, Mart/Bev = server pre-bucketed pivots. Ages the *reconciled ledger*, not SAP's unreliable open flag. | `OINV` open A/R + `JDT1` reconciliation, per company DB |
| **CUSTOMER CODE** | The join key for every sales/accounts report — the one clean bridge to Accounts. | `OCRD.CardCode` (e.g. CUSTA000936) |
| **Daily Production** | What actually got produced each day (standard work orders only); rows include upstream PM production (bottle-blowing) alongside FG fills. | `OWOR` (`bopotStandard`): `PlannedQty`/`CmpltQty`/`Status`/`OUSR.U_NAME` |
| **DaysInStock / DaysSinceBilled / DaysSinceMoved** | Age of on-hand lot since production / days since last sold / days since last stock movement. **DaysSinceMoved is the field the non-moving filter uses.** | `ProdDate` / last `OINV` line / last inventory movement |
| **`days` / `tdd` / `ltd`** (Oil aging) | `days` = invoice age (doc-date → as_of); `ltd` = last-txn / due date; `tdd` = days past due. Oil buckets key off `days`. | Derived from `OINV.DocDate` / due date |
| **DONE / DONE L** | ₹ value (DONE) and litres (DONE L) achieved MTD against target; the sales-data aggregate — **gross of CN and INCLUDING intercompany**, unlike Accounts turnover; can go negative when returns exceed sales. | `OINV`/`INV1` net of `ORIN`/`RIN1`, by `DocDate` range (client-side rollup) |
| **DRR** | Daily run rate = DONE ÷ working-days-elapsed; projects month-end. Client-side; depends on the app's (unobservable) working-day calendar. | Derived (app arithmetic + working-day calendar) |
| **FLEX target** | Flat litre goal per salesperson for the month; empty `{}` when not yet set. | Django DB (`flex-targets/`); key `¦person=<NAME>` |
| **Format** (aging group) | Aging grouping band: Oil/Mart = channel (E-COMMERCE/GT/ROI/BRANCH…), **Bev = salesperson name**; company-specific, never compare across books (C-0015). | `U_Main_Group` (Oil/Mart) / `OSLP` salesperson (Bev) |
| **GSTIN** | 15-char GST registration of the party; the **as-billed** GSTIN, not an OCRD tax field. | `INV12.BpGSTN` (C-0014), NOT `OCRD.FederalTaxID` |
| **Hidden sales** (`U_ARNO='H'`) | Real billed invoices flagged hidden and held out of the dashboard 'Done'; an audit view (Oil only). **Distinct from the separate `U_AR_NO` field** — do not conflate. | `OINV` where `U_ARNO='H'`; value = `INV1` taxable |
| **Historical / Avg Realise overlay** | Trailing 12m/6m/3m/last-month ₹/L benchmark — **BROKEN on the live host** (6m and last_month echo the current-range realise). Do NOT present as a trailing benchmark. | Derived (currently period-insensitive; unreliable) |
| **is_fg** | Finished-good-oil filter; the reason non-oil invoices (e.g. 18% GST AKAL bills) never appear in the realise feed. | Filter over `OITM` finished-good items |
| **Last Customer / Last Code** | Who last bought a non-moving item (the chase target). | Party name + `OCRD.CardCode` from the last `OINV` |
| **Ledger origin** (PC / PS / IN…) | Which SAP document type posted a ledger line: PC = A/P invoice, PS = goods-receipt PO, IN = A/R invoice. | `JDT1`/`OJDT` transaction-origin codes (C-0023) |
| **linetotal / line_total** | Net ₹ value of a sale line (the realise numerator); net of line discount, before GST. **For Total Sales/CN sum `INV1.LineTotal` (line taxable base), NOT header `DocTotal − VatSum`** (tax-only invoices break the header sum). | `INV1.LineTotal` |
| **Litres / liter** | Volume sold in litres; `INV1.Quantity` is **PIECES** (C-0001) × parsed pack size (gram packs ÷ 910 by oil density). Beverages use boxes, not litres. | `INV1.Quantity` (pieces) × pack from `OITM.U_SKU`; `U_IsLitre='Y'` |
| **MAIN GROUP / `u_main_group` / `u_chain`** | The party's business bucket, doubling as sales channel (24 live values); inherited onto every sale line from the billed customer. **Not on `OITM`.** | `OCRD.U_Main_Group` / `U_Chain` (C-0015: differs across books) |
| **MATCHED / MISMATCH / INCOMPLETE** | Recon verdict: all chain nodes present & totals agree / present but differ / a node missing. Judged on **normalized tax-inclusive amounts** within ₹1, not on open/closed status (C-0019). | Comparison of summed node `DocTotal`s |
| **measure** | Volume-unit flip: Litres (oil) / Boxes (bev). | App field; unit follows `OITM.U_TYPE` company book |
| **Net Sales** | Total Sales − Total CN; the sales team's realised-sales proxy, ≈ Accounts turnover **only with the intercompany caveat** (CP does not apply the C-0005 exclusion). | Derived (`INV1` taxable − `ORIN` taxable) |
| **NODE target** | Litres (+₹/L) by main_group × state × sales_person × segment; the `seg` (OILS/BEVERAGES) query param is **ignored** by this endpoint. | Django DB (`target-nodes/`) |
| **Non-Moving Stock** | Slow/dead FG not billed for a long time (liquidation queue). **NOT a server flag — a client-side `DaysSinceMoved ≥ N` cut** (default 60; set 0 to see all). | `OITW`/`OITM` in-stock list + last-bill lookup on `OINV`/`INV1` |
| **OIH / Order In Hand** | Open, uninvoiced sales-order book = committed future demand; read as **VOLUME (litres/pieces), not rupees**. FG lines only (`breakdown`), but does **not strip intercompany** (unlike Accounts). Stale/abandoned orders inflate it. | `ORDR` + `RDR1.RemainingOpenQuantity` > 0 (Service-Layer; `OpenQty` returns null) |
| **OIH RLZ** | ₹/L realisation locked inside the open book; gross of returns. Not returned by any `oih/*` endpoint — computed on Slide-2 channel cards. | Σ open ₹ (`RDR1.OpenSum`) ÷ Σ open litres |
| **OIH vs Stock** | Open demand per item vs finished-goods stock per warehouse. Real page is `/realise/oih-vs-stock/` (the `/inventory/` route 404s). | `item_stock` + `item_stock_pcs` in the oih breakdown, over warehouses [GP-FG, BH-EC, BH-PF, BH-BT] |
| **`open_bal`** (Open Payments) | CP's OWN recompute of the unapplied portion — **proven ≠ `ORCT.OpenBal`** (CP 1,132,770 vs SAP 20,104 on the same receipt). Do not conflate. | CP JDT1-based calc, not `ORCT.OpenBal` |
| **Open Payments / Payment on Account** | Customer receipts received but not yet applied to invoices, in a date window; `amount` ties to SAP exactly. | `ORCT` (IncomingPayments, `DocType rCustomer`); `amount` = `CashSum + TransferSum` |
| **`outstanding`** (Oil aging row) | **NOT the invoice's outstanding** — it is the party's whole NET ledger, printed identically on every one of that party's rows. **Never sum this column.** | `BusinessPartners.CurrentAccountBalance` |
| **Payment Done / Remaining** (Credit) | `payment_done` = bank receipts dated on the as-of day; `remaining` = Total Outstanding − Payment Done. | `ORCT` on `as_of` |
| **PCS/BOX** (`pcs_per_box`) | Pieces (bottles) per carton — carton config; the "20 PCS" in item names. Multiplying invoice qty by it inflates volume ~20× (C-0001). | `OITM.SalesFactor2` |
| **Planned vs Completed** | Work-order target qty vs actually produced; Litres = Completed × pack size. | `OWOR.PlannedQty` / `CmpltQty` |
| **Product target** | Litres + ₹/L keyed by `U_TYPE`+`U_Sub_Group` (16 keys); key uses the app's derived Slide-1 taxonomy (OLIVE split by `U_Variety`), never raw OITM. | Django DB (`targets/`) |
| **Production Feasibility / Max FG** | "Can we make this FG, and how many?" — explode the BOM, compare required vs component on-hand. Read-only, nothing consumed; `max_fg` can be negative (component oversold). | `OITT`/`ITT1` BOM vs component `OITW.OnHand` |
| **pulse** | Cheap change-fingerprint heartbeat (polled ~30s); empty string = no signal; carries no data. | Opaque hash of SAP state for the window |
| **QUANTITY** (beverages) | Bottles sold — pieces (C-0001), `MeasureUnit='PCS'`. | `INV1.Quantity` |
| **RATE LIST** | Saved library of Realise-Calculator pricing scenarios, tagged by state; store empty live. | Django app store, not SAP |
| **REALISE** (RLZ; UI typo "RELISE") | Net average selling price per litre (₹/L) = Σ net line value ÷ Σ litres — **JIVO's core price-efficiency KPI and the app's namesake**. A ₹/L *rate*, scheme-diluted — NOT Accounts turnover (a ₹ total). Money-gated for `preshit`. | `INV1.LineTotal` (net of GST) ÷ litres, per `OITM.U_TYPE`+`U_Sub_Group` |
| **Required Credit Limit** | Management target for a party's SAP credit limit = Total Outstanding × 1.02; a target, not read back from SAP. | Derived (`total.value.required_limit`) |
| **RM / PM** | Raw material (loose oil) vs packing material (bottle/cap/label/tape); the binding constraint is usually RM. | BOM component `kind` from `OITT`; `RM…`/`PM…` code prefixes |
| **Sales Flow** | Per-party SAP document chain Quotation→Order→Invoice with open/closed status and creator (OMS software vs named user); blank steps = skipped; default window = yesterday. Open-status **indicative only** (C-0019). | `OQUT`→`ORDR`/`RDR1`→`OINV`; source from `OINV.U_OMS_Order_No` + `OUSR` |
| **Sales Flow `open_pcs` / `open_qty`** | Still-open line qty of one open Order/Quotation; `open_pcs` = single bottles (**Σ `RDR1.RemainingOpenQuantity`**), `open_qty` = litres (pack-expanded). A point-in-time snapshot, never a fixed fact. | `RDR1.RemainingOpenQuantity` (order) / `QUT1` (quotation) |
| **SALES PERSON / `sales_person`** | Mapped salesperson / beat owner (party master, and the OIH owner credited with the whole SO — header-level, every line inherits it). | `OCRD.SalesPersonCode` → `OSLP.SlpName`; OIH owner `ORDR.SlpCode` |
| **Sales vs CN** | Gross billed sales netted against credit notes for one company/range; keeps gross, Goods-CN, Service-CN and Net as separate drillable columns (Oil/Bev only, not Mart). | `OINV`/`INV1` minus `ORIN`/`RIN1`, by `DocDate` |
| **`SALES_REV`** (beverages) | Net sales value (₹) of beverage lines; **same basis as Accounts turnover** (net of GST). Beverages has no realise; **IS visible to `preshit`**. | `Invoices` net of GST (`DocTotal − VatSum`), `Cancelled eq 'tNO'`, by `DocDate` |
| **schema** | Which company book: `jivo_oil` / `jivo_mart` / `jivo_beverages` (the recon endpoint uses `oil` / `beverages` only). | Selects SAP DB `JIVO_OIL_HANADB` / `JIVO_MART_HANADB` / `JIVO_BEVERAGES_HANADB` |
| **SEGMENT** (OILS vs BEVERAGES) | Top business split: oils (litres, ₹/L) vs beverages (boxes, no realise); separate tracks, targets and docs. | OILS = `FG*` oil universe (`U_IsLitre='Y'`); BEVERAGES = Bev book + drink items |
| **SEGMENT override** (targets) | Saved target overrides scoped to one segment; holds only explicit saves — empty `{}` is normal. | Django DB (`segment-targets/`) |
| **SKU** | Pack size of one sellable unit (`1 LTR`, `500 MLS`, `15 KGS`…); a stored UDF, not regexed from the item name. | `OITM.U_SKU` |
| **Status** | Account state: Active / Frozen (credit-locked) / Inactive. | Derived from `OCRD` frozen flags |
| **Stock Available / On-hand** | Live finished-goods sitting in the godowns; a snapshot, no history. Reconciles to SAP `QuantityOnStock`. | `OITW.OnHand` per warehouse (Σ = `Items.QuantityOnStock`) |
| **SUB-GROUP / `u_sub_group`** | The oil/product family (MUSTARD, OLIVE, CANOLA…). **TRAP: the calculator-items and beverages feeds label this `variety`.** | `OITM.U_Sub_Group` (Sales-Dashboard `u_sub_group`; calculator `variety` = mislabel) |
| **TGT** (`target_sale` / `target_realise`) | Monthly target: `target_sale` = `tgt_ltrs` (**LITRES — a misnomer, NOT ₹**) and `target_realise` = `tgt_rate` (₹/L). Django-only; SAP has no sales target. Five grains that **don't foot to each other**. | None — Django DB (`targets/`) |
| **`today_boxes` / `yesterday_boxes`** | Day-over-day carton comparison on the beverages dashboard; today + yesterday = month boxes. | Same invoice lines, bucketed by the last two dates |
| **`total`** (Oil aging row) | Original invoice value (GST-inclusive). | `OINV.DocTotal` |
| **Total Outstanding** (Credit page) | Ledger dues **plus** open-order (OIH) value; Accounts would never fold un-invoiced orders into "outstanding". | `CurrentAccountBalance` + OIH revenue |
| **Total Sales / `sales_rev`** | Gross invoiced value; NET-of-GST like Accounts turnover, but summed at **LINE level** so it captures tax-only/supplementary bases a header sum misses. | Σ `INV1.LineTotal` (taxable) |
| **TYPE / `u_type`** | Oil margin tier: **PREMIUM** (branded, high realise) vs **COMMODITY** (bulk staple) — plus a third value **OTHERS** (seeds/honey/spices/gift packs…). OIH splits open pieces into `premium_pcs`/`commodity_pcs` by this field. Never name-match. | `OITM.U_TYPE` |
| **Value** (₹ stuck) | Rupees tied up in on-hand stock — a display cost × qty heuristic, **NOT** a GL inventory valuation. | `Qty × PricePer` (`OITW.OnHand` × item price/cost) |
| **VARIETY / `u_variety`** | The grade/pressing/brand within a family (POMACE, EXTRA VIRGIN, EXTRA LIGHT, KACCHI GHANI…). Correct only in Sales-Dashboard feeds; calculator/beverages feeds mislabel sub-group as `variety`. | `OITM.U_Variety` |
| **Warehouse / godown code** | Physical stock location (GP-FG, BH-PF, BH-EC…); live Oil now returns 15 warehouses (vault said 5 — treat any hard-coded list as stale). | `OWHS.WhsCode`/`WhsName`; per-warehouse in `OITW` |
| **Wellness–Mart Reconciliation** | Does the intercompany Mart (buyer) ↔ Wellness (seller) paperwork line up? Uses **tax-INCLUSIVE `DocTotal`**, not net turnover. | Cross-schema `MART.OPOR`→`OIL.ORDR`→`MART.OPDN`→`MART.OPCH`→`OIL.OINV` |
| **Work-order status** | Planned / Released / Closed. | `OWOR.Status` → `boposPlanned/Released/Closed` |

## How an AI should use this

The CLI is `control-panel/cli/jivo/jivo` (it self-names `jivo-pp-cli`); invoke as `jivo <group> <sub>`, add `--agent` for JSON + non-interactive output, run `jivo doctor` first. Common sales questions → the command that answers them:

| Sales question | Command |
|---|---|
| Realise / ₹-per-litre and litres vs target this month | `jivo sales data` (DONE + embedded `target_sale`/`target_realise`) |
| Expand one product row into a dimension (litres + linetotal) | `jivo sales drill-down` |
| Trailing-average realise benchmark (⚠ broken — see below) | `jivo sales historical` |
| Sales net of returns for one company | `jivo sales cn --company oil` (or `beverages`) |
| Has it shipped? bilty / transporter / vehicle | `jivo sales dispatch` |
| Document chain for a party (quote→order→invoice) | `jivo sales flow` → `jivo sales flow-open-items` |
| Invoices held out of "Done" (hidden) | `jivo sales hidden` |
| Month-over-month by channel / state / product | `jivo sales compare-docs` (grid via `sales data`) |
| Beverages boxes / day-over-day / customer grading | `jivo sales beverages` → `jivo sales beverages-docs` |
| Open order book (committed future volume) | `jivo oih summary` (per salesperson) · `jivo oih breakdown` (line-level) · `jivo oih rows` · `jivo oih commodity-rows` |
| Who owes us? A/R aging | `jivo accounts aging-oil` · `aging-mart` · `aging-beverages` |
| Customer receipts not yet applied | `jivo accounts open-payments` |
| Customer claims register | `jivo accounts claims` |
| Required credit limit / credit-lock state | `jivo credit` |
| Targets (litres / ₹-per-L) | `jivo targets list` · `channel` · `nodes` · `flex` · `segment` |
| Stock on hand by godown | `jivo inventory stock` |
| Dead / slow-moving stock | `jivo inventory non-moving` → `non-moving-drill` |
| Can we make FG X, and how many? | `jivo inventory production-feasibility` |
| What got produced today? | `jivo inventory daily-production` |
| Intercompany Mart↔Wellness billing recon | `jivo inventory reconciliation` → `reconciliation-ledgers` |
| Customer master (GSTIN, balance, terms, credit) | `jivo masterdata customer-master` |
| Item master (pack size, pcs/box, variety) | `jivo masterdata calculator-items` |
| Cost of goods sold | **No command** — COGS is OTP/permission-gated (403 for `preshit`) |

**Money-gating note (`preshit` login).** The ₹ money panels are blank for this login: OILS **realise ₹** feeds (`sales data`) return empty, and **COGS** (`/api/cogs/`) is a hard 403. The gating is **asymmetric** — everything else returns real numbers to `preshit`: all **volumes** (litres/boxes/pieces), **OIH**, **targets**, **A/R aging ₹**, **open-payments ₹**, **required-credit-limit ₹**, and beverages **`sales_rev`** (net-of-GST turnover). To read oil realise ₹ or COGS you need a money-enabled login.

## Confidence & open questions

Per-domain confidence, with the must-fix each domain flags:

- **Realise** — *high.* Must-fix: the realise grid / DONE is **GROSS of credit notes** (CN not netted) and **INCLUDES intercompany JIVO MART** (~₹19.4M of a ₹27.48M verified Oil day = ~71%); the **Historical/Avg realise overlay is broken** (period-insensitive) — never cite as a trailing benchmark; OIH-backed orders can be months stale; the DONE-as-MTD figure is single-day-proven arithmetic (Oil 2026-08-24, ₹27,479,404 / 149,203 L), not an independent MTD reconciliation.
- **Sales-detail** — *high.* Must-fix: sum **`INV1.LineTotal`, not header `DocTotal − VatSum`** (tax-only invoices, e.g. inv 626080444); Sales-Flow `open_pcs` = **Σ `RDR1.RemainingOpenQuantity`** (`OpenQty` is null); present all open-order line counts as **point-in-time snapshots**; Net Sales ≈ turnover **only** with the intercompany caveat (CP does not apply the C-0005 23-CardCode exclusion); don't conflate `U_ARNO` (hidden = 'H') with `U_AR_NO`; flow open-status indicative only (C-0019).
- **OIH** — *high.* Must-fix: `oih summary`/`breakdown`/`rows` values are **LITRES, not ₹** (override the stale recon vault that mislabels them ₹); **~75% of the 2,052,339 L headline is ONE intercompany Oil→Mart SO** (1726086707, CUSTA000606) — net it out for external demand, and it is what makes PRABHU SIR's 77% share; **FG-only applies to `breakdown` only** (`rows`/`summary` include the BALAJI packaging SO); `summary` vs `breakdown` disagree per-person beyond cache jitter.
- **Accounts** — *high* (~85% on the Oil-only scope of `credit`/`open-payments`). Must-fix: **"Outstanding" is TWO numbers** — gross open-invoice `bal` (Σ = Total Outstanding, ₹82.31 Cr Oil) vs net party ledger `outstanding`/`CurrentAccountBalance` (₹32.45 Cr); **never sum the `outstanding` column**; `open_bal` ≠ `ORCT.OpenBal`; Claims / Credit-Lock / Aging-Remark are Django-only; Mart aging's top "receivable" is intercompany JIVO MART.
- **Targets** — *high* (~85% on the Django-only ruling; write path never executed). Must-fix: **targets are Django-only, not in SAP** (nothing to audit against); `target_sale` is **LITRES, a misnomer** (not ₹); **the five target layers do NOT foot to each other** — never quote "the July target" as one number (2.0 M product / 2.5 M channel-node / 1.3 M flex); the `seg` param on `nodes` is ignored.
- **Inventory** — *high* (medium only on the exact A/P-node mechanism). Must-fix: a recon node amount **≠ posted `OPCH.DocTotal`** (₹768 gap on 608264208, still MATCHED); "non-moving" is a **client-side `DaysSinceMoved ≥ N` cut**, not a server flag; the warehouse list drifted (15 Oil, not 5); `Value` is display cost × qty, not GL valuation; the recon uses tax-INCLUSIVE `DocTotal`.
- **Taxonomy** — *high.* Must-fix: calculator-items `variety` = SAP **`U_Sub_Group`, NOT `U_Variety`** (mislabel); `U_TYPE` has a **third value OTHERS** (not just PREMIUM/COMMODITY); **MAIN_GROUP is a party field** (`OCRD.U_Main_Group`), not on OITM; GSTIN is the **billed `INV12.BpGSTN`** (C-0014), not an OCRD field; **never name-match — read the `U_*` column**.
- **Beverages / COGS** — *high* (COGS documented-only, gated). Must-fix: the beverages feed **SWAPS `variety`/`sub_group`** (feed `variety` = `U_Sub_Group`, feed `sub_group` = `U_Variety`); beverages counted in **BOXES, no ₹/L realise**; **COGS fully gated for `preshit`** (403, no CLI); beverages `sales_rev` = net-of-GST turnover basis (and IS visible); the beverages aging **excludes curated related-party accounts** (BLESSING ADVERTISING, JIVO WELLNESS) but keeps JIVO MART.

Merged open questions across domains:

- **CN netting scope.** The realise grid / DONE is gross of CN — is net-of-returns realise only ever seen via `sales cn`, does the grid ever net a CN dated *later* than its invoice, and does `sales cn` "Total Sales" include hidden (`U_ARNO='H'`) invoices? (samples had zero hidden / zero service-CN, so untested).
- **Intercompany rule not pinned.** CP applies **no** C-0005 23-CardCode exclusion in realise / OIH / flow / dispatch (JIVO MART & WELLNESS included), yet beverages aging *curates out* BLESSING + JIVO WELLNESS while *keeping* JIVO MART — the exact mechanism (CardCode list? UDF flag? main-group?) is unknown, and a residual ~₹20 L gap remains. Any "external sales/demand" answer must net intercompany itself.
- **Historical overlay.** Genuinely broken on the ARY host, or does it need a param my calls omitted? A previously-diverging figure isn't proof it ever computed a real trailing window.
- **CN split & beverages CN.** The Goods-vs-Services CN rule (inventory-line vs service-line on `ORIN`/`RIN1`) is inferred, not verified; beverages `cng_*`/`cns_*` are off ~₹6k vs SAP `CreditNotes` — date basis/scope unconfirmed.
- **OLIVE month gap.** Old lineage flagged a ~30% OLIVE month gap (76.2 M SAP vs 53.0 M app); a day-level recon closes to ₹0.68 once FG-filtered and intercompany-kept, but the OLIVE-*month* sum wasn't reproduced line-by-line, so that warning isn't fully retired.
- **`open_bal` formula.** Proven ≠ `ORCT.OpenBal`; the exact JDT1-based unapplied-portion calc is unconfirmed.
- **OIH endpoint drift.** `summary` vs `breakdown` per-person disagreement (PRINCE 36k vs 79k, TEJPAL 0 vs 33k) is partly cache timing, partly the FG-only-vs-not scope difference; and whether `oih rows`/`commodity-rows --start/--end` actually filter (on `ORDR.DocDate`?) is untested.
- **Targets datastore.** Where the Django target table physically lives is unidentified (not SAP, not the 15-DB Postgres cluster) — targets can't be row-checked against any reachable store; `target_realise` went 0→populated July→Aug (confirm deliberate rollout); whether `save-targets` ever writes back to SAP (ruled Django-only, ~85%).
- **Inventory node & counts.** Exactly which SAP amount CP puts on the A/P recon node (GRPO-linked base vs `OPCH1` sum) is inferred (₹768 gap proves ≠ `OPCH.DocTotal`); a whole-day daily-production doc↔`OWOR` count recon wasn't run (join key needs confirming); the 784,323.58 L Oil litre total wasn't summed line-by-line against an independent SAP litre figure.
- **Taxonomy tails.** How `U_TYPE=OTHERS` is folded (into COMMODITY/PREMIUM or dropped — needs a money login); how many items carry a swapped `U_Sub_Group`/`U_Variety`; the exact GSTIN resolver (which invoice's `BpGSTN`); Mart/Bev `main_group` vocab not sampled (needs `manager`).
- **Beverages tails.** COGS unlocked payload shape (its litre basis for a boxes business) never executed; `brand` only ever `JIVO`; `beverages-docs` node-path drill filters may not be reachable from the CLI.
- **Out of scope here.** DRR's working-day calendar isn't observable via the CLI; the Compare-Sales grid endpoint (`/realise/api/sales-data/`) and the OIH-RLZ ₹ source belong to the sales-data slice and weren't reconciled in this pass; whether `credit`/`open-payments` are strictly Oil-only (no company toggle found, ~85%).

---
## Realise — the core sales dashboard

**What it is.** The Control Panel's biggest screen (Django proc `REPORT_SALES_ANALYSIS`, "v11"), served at `/realise/` and fronted by the shared `/realise/api/*` backend. It re-expresses SAP B1 A/R invoices in the sales team's own language: not "turnover ₹", but **REALISE — the net ₹ actually earned per litre of oil sold**. The whole app is named after this one number. Two slides: Slide-1 = product grid (`u_type × u_sub_group`, realise vs target); Slide-2 = channel cards (GT/MT/ROI/ECOM/HORECA/CSD/REST with TGT/DONE/OIH/BAL). A global OILS⇄BEVERAGES toggle swaps the whole dataset.

**Verification basis.** Live host `http://138.252.101.118:9080` (the ARY box; the old `103.89.45.75` recon host is dead), CLI `control-panel/cli/jivo/jivo` as `preshit` (admin). SAP ground truth via `sapb1` MCP against `JIVO_OIL_HANADB`. **Money is NOT gated for this login on the sales feeds** — `sales data` returns full `line_total`/`realise` ₹ (the money-gate hits COGS/expenses/salary panels only, none of which are in this domain). All figures below pulled live 2026-08-25 (SAP `as_of` 14:02–14:10Z).

**One-line mental model:** `realise = Σ(INV1.LineTotal, net of GST) ÷ Σ(litres)`, over FG-oil invoice lines, by `DocDate` range, **gross of credit notes, and INCLUDING intercompany transfers to JIVO MART.** That last clause is where the sales lens diverges hardest from the Accounts turnover definition.

---

### Term table

| Term | Meaning (sales-team) | SAP lineage | Differs from Accounts / raw SAP | Gotchas & corrections |
|---|---|---|---|---|
| **REALISE / Avg Realise / RLZ** | Net average selling price **per litre** (₹/L) actually earned after discounts & schemes. JIVO's core price-efficiency KPI. | `realise = linetotal ÷ litres` per `u_type|u_sub_group`. `linetotal` = Σ `INV1.LineTotal` (row net, after line discount, **before** GST). | Accounts has no "per-litre" metric; turnover is a ₹ total. Realise is a **rate**, denominated in the team's own litre count. | Diluted by scheme (free) litres — same ₹ over more L. Verified `254.64 = 6,785,912.04 ÷ 26,649` (OLIVE, 08-24). |
| **linetotal / line_total** | Net ₹ value of the sale (the numerator). | `INV1.LineTotal` (net of GST). | Same basis as Accounts' `DocTotal − VatSum`, **but summed gross of CN** (see below). | Reconciled to the rupee: see recon #1/#2. |
| **litres / liter / DONE L** | Volume sold, in litres (the denominator; "DONE L" = MTD litres achieved). | `Σ INV1.Quantity (PIECES) × parsed pack size`. Pack from `OITM.U_SKU`: `"1 LTR"→1`, `"2 LTR"→2`; gram packs converted by oil density **÷ 910** (`"700 GMS" → 0.769 L`, `U_IsLitre='Y'`). | Accounts never computes litres. | **[C-0001]** `INV1.Quantity` is PIECES not cartons — the "20 PCS" in the item name is carton config; multiplying by it inflates ~20×. Verified: FG0000030 `1 LTR`, 3200 L = 3200 pcs; FG0000299 `700 GMS`, 1015.34 L = 1320 pcs × 0.769. |
| **DONE** | ₹ value achieved month-to-date against target. | `sales-data` product `data[]` re-summed for the range = ₹ MTD. | Accounts "turnover" nets CN & excludes intercompany; **DONE does neither** (see recon #2/#4). | Computed **client-side** from the sales-data range aggregate — no dedicated "DONE" field. Feed the month-start→today range to get true MTD. |
| **TGT** | Monthly target — **litres and ₹/L**, per `u_type\|u_sub_group`. | **Django DB only — no SAP object.** `targets/` → `{tgt_ltrs, tgt_rate, source}`. | SAP holds no sales target of any kind. | In `sales-data`, `target_sale` = **target LITRES** (= `tgt_ltrs`), NOT ₹; `target_realise` = `tgt_rate` (₹/L). Name `target_sale` is misleading. Verified MUSTARD 625000 L / ₹145. `source:"default"` = hard-coded fallback; `"saved"` = edited via `save-targets` (WRITE, never call). |
| **DRR (Daily Run Rate)** | Per-day sales pace; projects month-end. | Derived: `DONE ÷ working-days-elapsed`; projected = `DRR × total working days`. | Pure app arithmetic; not in SAP or Accounts. | **Client-side** — no API returns DRR. Depends on the app's working-day calendar (not observable via CLI). |
| **BAL** | Balance still to hit target = `TGT − DONE`. | Derived (TGT app-side − DONE from SAP). | App-only rollup. | Client-side; variants below. |
| **BAL W/O OIH** | Balance needing **fresh** orders = `TGT − DONE − OIH`. | Derived. | App-only. | Subtracts the open order book — see OIH. |
| **BAL RLZ** | The ₹/L you must realise on the remaining balance to still hit the target **value**. | Derived. | App-only. | A required-rate, not an achieved-rate. |
| **OIH (Order In Hand)** | Open, uninvoiced sales orders — committed future volume (L) and value (₹). | `ORDR` + `RDR1.OpenQty` (open sales orders). Confirmed live: Oil has **89 open orders**; `oih rows` = 243 open **lines**. | Accounts doesn't track order book; this is forward-looking, not booked revenue. | `oih rows.open_qty` = open **litres** (pieces×pack). `oih summary` = ₹ per salesperson. **[C-0019]** don't trust SAP `DocStatus 'O'` loosely — but OIH uses `RDR1.OpenQty>0`, which is reliable. Lineage proved it row-for-row (`OpenQty`). |
| **OIH RLZ** | Avg ₹/L already locked inside the order book. | `oih` value ÷ oih litres. | App-only. | Complements BAL RLZ. |
| **Historical / Avg Realise overlay** | Trailing-period benchmark ₹/L (12m/6m/3m/last_month) shown beside current realise. | `historical-realise` → `data["U_TYPE\|SUB"]`, `drill_data["…\|Dim\|Value"]`. | App-only overlay. | ⚠️ **Broken/period-insensitive on the live host** — `6m` and `last_month` both returned values **identical to the current range's realise** (MUSTARD 157.16, OLIVE 251.23, CANOLA 178.14). Do NOT treat as a genuine trailing benchmark until re-verified. See recon #6. |
| **u_type** | Product tier: `COMMODITY` (bulk staple) vs `PREMIUM` (branded). | `OITM.U_TYPE`. | — | **[C-0015]** `U_Main_Group` differs across company books — but `U_TYPE`/`U_Sub_Group` are safe within Oil. Never name-match; use the field. Verified FG0000030 → COMMODITY. |
| **u_sub_group** | Oil variety: MUSTARD, OLIVE, CANOLA, SOYABEAN, SUNFLOWER, BLENDED, GHEE, GROUNDNUT, RICE BRAN, EXTRA VIRGIN OLIVE… | `OITM.U_Sub_Group`. | — | `EXTRA VIRGIN OLIVE` is its **own** sub_group, split out from `OLIVE` (see recon #3 arithmetic). |
| **u_variety** | Finer variety label (e.g. MUSTARD KACCHI GHANI vs PAKKI GHANI). | `OITM.U_Variety`. | — | Present on `channel_rows`, not on the Slide-1 grid rows. |
| **sku** | Pack size string ("1 LTR", "5 LTR", "700 GMS"). | `OITM.U_SKU`. | — | This is the string the litre-parser reads. |
| **u_main_group / main_group** | Sales **channel** on a line: GT / MT / E-COMMERCE / HORECA / CSD… | `OCRD.U_Main_Group` (the customer's channel tag). | — | Commodity-OIH variant keys it `u_main_group`; standard keys it `main_group`. **[C-0015]** cross-company. |
| **u_chain** | Chain/trade type (DISTRIBUTOR, chain…). | `OCRD.U_Chain`. | — | A drill dimension, Pascal-cased `U_Chain`. |
| **is_fg** | "This line is a finished-good oil SKU." | Filter over `OITM` (FG items). | This filter is **why non-oil invoices vanish** (see recon #2). | All 57 rows on 08-24 were `is_fg:true`; the AKAL non-FG invoices were absent. |
| **Variance / Recovery / Rate Impact** | Slide-1 target-vs-actual analytics (litre gap, ₹ recovered, ₹/L rate effect). | Derived from realise + target. | App-only. | Client-side; not separate feeds. |
| **pulse** | Heartbeat fingerprint; dashboard polls ~30s, reloads only when it changes. | Opaque hash of SAP state for the window. | — | Empty string `""` = "no signal / no window". Carries **no data** — never pull with it. `sales pulse` returned `{"pulse":""}` (no start/end supplied). |
| **Channels (GT/MT/ROI/ECOM/HORECA/CSD/REST)** | Go-to-market segments, each with own TGT/DONE/OIH/BAL/realise on Slide-2. | Grouped by `OCRD.U_Main_Group`; docs via `channel-detail-docs` (`metric=done` invoices / `oih` open SOs). | — | ROI = "Rest of India" geography rollup. Per-doc warehouse stock triple `[GP-FG, BH-EC, BH-PF]` (breakdown shows a 4-slot variant). |

---

### Reconciliation results (live, 2026-08-25)

All CP figures from `sales data --start-date 2026-08-24 --end-date 2026-08-24` (Oil). SAP from `sapb1` MCP, `JIVO_OIL_HANADB`.

**#1 — Line/customer trace → `line_total` = INV1.LineTotal (net of GST). RECONCILES.**
WHITE TRADERS (CUSTA000035), 08-24. CP sum of its 4 FG lines = **₹863,621.00** (FG0000030 521,120 / FG0000011 97,713.6 / FG0000038 97,713 / FG0000299 147,074.4).
SAP: its 2 invoices 626080502 + 626080503, `DocTotal − VatSum` = (752,374−35,827.33) + (154,428−7,353.72) = **₹863,620.95**. Δ = ₹0.05 (rounding). ✅

**#2 — Whole-day headline → what the realise feed keeps vs drops. RECONCILES to ₹0.68.**
CP 08-24 channel total = **₹27,479,404.11** / 149,203.12 L, 13 customers.
SAP: 34 non-cancelled Oil invoices on 08-24, net-of-GST = **₹28,779,304.79**.
- CP **includes** intercompany **JIVO MART PVT LTD** (CUSTA000606): CP MART = **₹19,417,600.00** = SAP MART net **exactly**.
- CP **excludes** the non-FG invoices to **AKAL INFORMATION SYSTEMS** (DocNum 726…, 18% GST, ₹1,299,900 net) — 0 AKAL rows in CP.
- Identity: `28,779,304.79 − 1,299,900 = 27,479,404.79` vs CP `27,479,404.11` → **Δ ₹0.68**. ✅
**Lens takeaway:** the sales "DONE" **includes intercompany** and **excludes non-FG lines** — the mirror image of the Accounts rule (**[C-0005]** turnover *excludes* the 23 intercompany CardCodes).

**#3 — Product taxonomy → OITM user fields. RECONCILES.**
CP `u_type/u_sub_group/u_variety/sku` = `OITM.U_TYPE/U_Sub_Group/U_Variety/U_SKU`. FG0000030 → COMMODITY / MUSTARD / MUSTARD KACCHI GHANI / 1 LTR; FG0000029 → …/2 LTR; FG0000011 → …/5 LTR. All exact. Realise identity: OLIVE `254.64 = 6,785,912.04 ÷ 26,649` ✅; OLIVE-by-State drill (HARYANA 6,240,390.48 + DELHI 545,521.56 = 6,785,912.04) sums to the grid row ✅.

**#4 — Credit notes are NOT netted in the core realise grid. FLAG (contradicts vault concept).**
08-24 the grid's total litres (**149,203.12**) equalled the gross invoice-line litres **exactly**. The same-day RND LABORATORIES credit note (DocNum 626082645, a full ₹70,560 / 320 L reversal of invoice 626080511) was **not** removed — RND's invoice line (CANOLA COLD PRESS, 320 L, ₹67,200) is still fully present, no negative appears. So `sales-data`/`realise` is **gross of CN**. CN comparison lives in a **separate** view (`sales cn` / "Sales vs CN"). The vault `REALISE.md` wording "after … credit-notes netted off" is **not** true of this core feed. *(Confidence: high for same-day reversals — litre identity is dispositive; medium as a general rule — a CN dated after its invoice wasn't tested.)*

**#5 — Slide-1 grid is range-scoped, not MTD.** The `data[]` rows carry `month/year` labels but the numbers follow the **requested date range** (a single day here). Proof: grid OLIVE (26,649 L) = day-channel OLIVE (26,650 L) minus the separately-bucketed EXTRA VIRGIN OLIVE (1 L / ₹676.19). To read true "DONE" (MTD), pass `start = month-1st`.

**#6 — Historical/trailing overlay is period-insensitive on this host. FLAG.**
Anchor 2026-08-01..08-24: `historical --period 6m` and `--period last_month` **both** returned MUSTARD 157.16 / OLIVE 251.23 / CANOLA 178.14 — **identical to each other and to the current-range realise** (`sales data` same range: 157.16 / 251.23 / 178.14). A genuine trailing 6-month or last-month average would differ. Treat the overlay as **broken or ignoring `period`** until proven otherwise.

**#7 — OIH source confirmed.** `oih rows` (243 open lines) / `oih summary` (₹ per salesperson, e.g. PRABHU SIR ₹1,573,484). SAP Oil open orders (`DocumentStatus eq 'bost_Open'`) = **89**; INNOVATIVE RETAIL CONCEPTS (CUSTA000496, first oih row) has **15** open orders — consistent with lineage's row-for-row `RDR1.OpenQty` proof.

---

### Open questions

1. **CN netting scope.** The core grid is gross of CN (#4). Where exactly does the sales team see net-of-returns realise — only in `sales cn`, or is there a "net" mode I didn't trigger? Test a CN dated later than its invoice to confirm the grid never nets.
2. **Historical overlay (#6).** Is `historical-realise` genuinely broken on the ARY host, or does it key off something (e.g. a required `refresh`, or `data`-vs-`drill_data` mismatch) my calls didn't set? A previously-diverging figure isn't proof it ever computed a real trailing window here.
3. **Lineage's ~30% OLIVE gap.** The old sourcemap flagged "OLIVE 76.2M SAP vs 53.0M app" and said *don't quote CP realise as SAP*. My aggregate day-recon reconciles to ₹0.68 once you (a) restrict to FG-oil lines and (b) keep intercompany. The old gap was most likely a naive re-aggregation that mishandled the FG filter / intercompany / CN — but I did not reproduce the OLIVE-month sum line-by-line, so I can't fully retire that warning.
4. **Working-day calendar for DRR.** Not observable via CLI; projections depend on it.
5. **Beverages track.** Reconciled the OILS lens only; BEVERAGES runs a separate feed (`sales beverages`) in boxes, not ₹/L realise — out of scope here.

---
## Sales detail — CN, hidden, flow, dispatch, compare

*AI-facing decoder for the JIVO Control Panel "god software" as the **sales team** sees it. Domain: Sales-vs-Credit-Notes, Hidden sales, Sales document Flow, Dispatch details, Compare-Sales. Every number below was pulled LIVE on 2026-08-25 from the Control Panel CLI (`control-panel/cli/jivo/jivo`, base `http://138.252.101.118:9080`, user `preshit`) and cross-checked against LIVE SAP B1 (sapb1 MCP, `JIVO_OIL_HANADB`). Read this to translate a sales-team question into the right SAP entity/column, and to know where the sales lens differs from the Accounts lens.*

**Shape of everything here (verified live):** all five reports are a **single POST** returning a flat/nested row list; **all pivoting, KPIs, filtering, month-bucketing, and drill are done client-side** in the browser from that one payload. The CLI wraps the API JSON under `.data` (POST endpoints) or `.results` (the one GET, `channel-docs`). The Control Panel is a **read-through cache on top of SAP** — never-live-by-a-few-seconds; there is no sales write path.

---

### Term / abbreviation table

| Term (sales-team word) | Plain meaning | Exact SAP lineage (entity · columns · filter) | Differs from Accounts / raw SAP | Gotchas + corrections |
|---|---|---|---|---|
| **Sales vs CN** (`sales cn`) | Gross billed sales netted against credit notes, for one company over a range | `OINV`/`INV1` (sales) minus `ORIN`/`RIN1` (credit notes), by `DocDate` | Accounts "turnover" = same net-of-GST basis but a single figure; the sales page keeps **gross and CN in separate columns** and lets you drill the *gap* | Oil or Beverages only (no Mart). Company param `oil`\|`beverages`. |
| **Total Sales / `sales_rev`** | Gross invoiced value (the top of the funnel) | Σ `INV1.LineTotal` — **line-level, NET of GST (taxable value)** | **Same net-of-GST basis as Accounts**, BUT it sums *line* taxable, so it **includes the taxable base of tax-only / supplementary invoices** that a header `DocTotal−VatSum` sum would score as ~0 (see recon + gotcha) | `sales_qty` is in **Litres** (oil) / **Boxes** (bev), already pack-size-expanded — do NOT re-apply C-0001 here (the app already did). |
| **Total CN** | All credit notes = Goods + Services | `ORIN`/`RIN1` taxable, by `DocDate` | Accounts folds CN into one turnover number; sales splits it | In Litres/Boxes mode only Goods count (services carry no qty). |
| **CN for Goods / `cng_rev`,`cng_qty`** | Credit note for **physical product returns** | `ORIN` lines that are inventory items | — | Has a quantity (returned litres/boxes). |
| **Claim for Services / `cns_rev`** | Money-only CN — **discounts, FOC, samples, scheme claims** | `ORIN` lines that are service/non-inventory | This is where scheme/discount give-backs live; Accounts sees them only as credit memos | **No quantity** → blanked in Litres/Boxes mode. In the 2-day oil sample `cns_rev`=0 (all CN was Goods). |
| **Net Sales** | `Total Sales − Total CN` | derived client-side | ≈ Accounts turnover (both net of GST, both net of returns) | The sales team's "realised sales" proxy for this page. |
| **Hidden sales** (`sales hidden`) | Real billed invoices deliberately **held out of the dashboard "Done"** | `OINV` where **`U_ARNO = 'H'`** (a JIVO user-field on the invoice header), oil only | Accounts turnover **includes** these; the dashboard **"Done" excludes** them. This page is the audit of exactly what's excluded | Oil only. `U_ARNO` normally NULL; `'H'` = hidden. Live extra fields not in old vault: **`combo`**, **`debit_note`** (bool), **`price`** (per-unit). |
| **Realise ₹/L (`REALISE`)** | Net avg selling price per litre — JIVO's core KPI | `value / litres` client-side (`INV1` taxable ÷ parsed-pack litres) | — | Uses **net-of-GST** value; don't feed it GST-inclusive money. |
| **Cost Center** (hidden) | Variety / cost centre | `INV1.OcrCode` (= `CostingCode`, e.g. `MUSTARD`, `CANOLA`, `OLIVE`) | — | It's the *variety* dimension, not a GL cost centre in the Accounts sense. |
| **Sales Flow** (`sales flow`) | The SAP document chain **Quotation → Order → Invoice** per party, per day | `OQUT` → `ORDR`/`RDR1` → `OINV`; source from `OINV.U_OMS_Order_No` + `OUSR` | Accounts never looks at the chain; this is a pure ops/sales view | Blank Quotation/Order = that step was **skipped** (direct order / direct invoice), not missing data. Default window = **yesterday**. |
| **`quotation_no` / `order_no` / `invoice_no`** | SAP doc numbers in the chain | `OQUT.DocNum` / `ORDR.DocNum` / `OINV.DocNum` | — | Empty string when skipped. Note multiple **branch series** live in one company DB (oil DB carries `626…` main, `326…`/`726…` JIVO WELLNESS branch, incl. `JIVO MART`). |
| **`*_open` (quotation/order/invoice_open)** | Whether that doc still has open lines | `bost_Open` on the doc (`RDR1.OpenQty>0` for orders) | **C-0019: SAP DocStatus 'O' is unreliable at JIVO** (manual-JE settlement / on-account) — trust the *open-qty* view, not the flag, for A/R | An **open order** is drillable to line-level open qty. |
| **Source / `*_src`** | Who created the doc: **OMS software** vs a **named SAP user** | `{oms:bool,label,user}` from `U_OMS_Order_No` (OMS/B1i) else `OUSR.U_NAME` | — | `oms:true` = auto B1i integration; else a person keyed it (e.g. MANSI, SUMIT, HARPREET). In the oil sample **0 orders were OMS-sourced** (all hand-keyed). |
| **Open items / OIH residual** (`sales flow-open-items`) | Still-open line qty of one open Order/Quotation | `RDR1.OpenQty` (order) / `QUT1` (quotation) | This is [[OIH]] demand still to fulfil | `open_pcs` = **single bottles** (C-0001); `open_qty` = **litres** (pack-size × pcs). Confirmed live: FG0000451 "200 ML 70 PCS" → 25 000 pcs = 5 000 L. |
| **Dispatch / Bilty** (`sales dispatch`) | How goods physically left the warehouse, per invoice | `OINV` **user-fields**: `U_Dipatch_Date` (sic), `U_BiltyDate`, `U_BilltyNumber` (sic), `U_TransporterName`, `U_VehicleNoM`, `U_Mob_No` | Looks like native app data — it is **SAP UDFs on OINV**, not a separate logistics system | **"Bilty" = the transporter's Lorry Receipt / consignment note.** Field names carry SAP-side typos ("Dipatch", "Billty"). |
| **Dispatched (KPI)** | Invoices that have actually shipped | invoices with a **non-empty `bilty`** | Accounts has no such concept | Empty dispatch/bilty/vehicle = **invoiced-but-not-yet-dispatched**, not missing data. Bilty/dispatch dates can be **later** than the invoice date. |
| **Transporter / Vehicle / Driver** | Freight carrier name, truck reg, driver mobile | `U_TransporterName` / `U_VehicleNoM` / `U_Mob_No` on `OINV` | — | Free-text UDFs (e.g. "Delhi Punjab", `PB08FG0458`, `9186244192`). |
| **Compare Sales** (`sales data` + `sales compare-docs`) | Month-over-month **oil** pivot of Litres / Realise, click any cell to see the invoices | grid from `/realise/api/sales-data/` (other slice); drill = `OINV`/`INV1` | Accounts doesn't pivot MoM by territory-owner | Oil only. Grid and drill are **two different endpoints**. `compare-docs` is scoped to one month × one cell → payload naturally small. |
| **`compare-docs` fields** | Invoices behind one pivot cell | `OINV` header (`doc_num,doc_date,party,state,litres,boxes,taxable`) + `INV1` items (`name,boxes,litres,taxable,rate`) | — | `rate` = ₹/bottle (net); Realise = `taxable/litres` client-side. |
| **`channel-docs`** (`sales channel-docs`) | Docs behind a dashboard channel card — invoices (`done`) or open SOs (`oih`) | `OINV` (`done`) or `ORDR`/`RDR1` (`oih`); `stock[]` positionally aligned to `warehouses[]` | — | **Needs `--start`/`--end`** or returns empty/non-JSON. Narrow channel+seg+day often `count:0` (known gotcha). GET → wrapped under `.results`. Live `warehouses` grown to `["GP-FG","BH-EC","BH-PF","BH-BT"]`. |
| **Contact Person / territory owner** | The assigned owner, NOT the invoice sales-person | client-side **TERRITORY map** of `main_group` + `state` → owner (e.g. `GT\|DELHI→SUNNY JI`, `E-COMMERCE→PRABHU SIR`) | Accounts/SAP `person` UDF is *ignored* by these pages | The raw `person` field IS returned but the UI overrides it with the map — never trust `person` for ownership. |
| **Main Group / channel** | Go-to-market channel: `GT` `MT` `ROI` `E-COMMERCE` `CSD` … | `OCRD.U_Main_Group` (party) / item group | **C-0015: `U_Main_Group` differs across the 3 company books** — don't segment across companies on it | ROI = **Rest of India**, not return-on-investment. |
| **Type (Premium/Commodity)** | Product tier | `OITM.U_TYPE` (`PREMIUM`/`COMMODITY`) | — | Oil only (`has_type:true`); **Beverages has no tier** (`has_type:false`, hides the filter). Never name-match — use `U_TYPE`. |
| **measure (Litres/Boxes)** | Volume unit | app-computed; oil=**Litres**, bev=**Boxes** | — | KPI labels/columns re-render from the API's `measure`. |

---

### Reconciliation results — LIVE Control Panel vs LIVE SAP (all 2026-08-25)

**1. Dispatch → OINV user-fields — EXACT (7/7 fields).**
CP `sales dispatch` row, invoice **626080458**: `{code:CUSTA001102, name:"DWARKA DASS NARINDER KUMAR", dispatch:2026-08-22, biltydate:2026-08-22, bilty:"13181", transporter:"Delhi Punjab", vehicle:"PB08FG0458", mobile:"9186244192"}`.
SAP `Invoices/DocNum 626080458` (Oil): `CardCode CUSTA001102` · `U_Dipatch_Date 2026-08-22` · `U_BiltyDate 2026-08-22` · `U_BilltyNumber "13181"` · `U_TransporterName "Delhi Punjab"` · `U_VehicleNoM "PB08FG0458"` · `U_Mob_No "9186244192"`. **All match.** (Re-confirms the lineage doc's finding on a fresh invoice — freight metadata is SAP UDFs on OINV, not a separate system.)

**2. Hidden-sales count → OINV `U_ARNO='H'` — EXACT.**
CP `sales hidden` for July 2026 returned **75 distinct docs** (187 lines). SAP `Invoices count where U_ARNO eq 'H' and DocDate in July-2026` (Oil) = **75**. Individual doc **626070425** (STAR SALES CORPORATION): CP `status:"Closed", value:6000` ↔ SAP `U_ARNO='H', DocumentStatus bost_Close, DocTotal 6300 / VatSum 300 → taxable 6000`. **Match, incl. the hidden flag and the net-of-GST value.**

**3. Hidden-sales Value → Σ INV1 taxable — EXACT to the rupee.**
CP `sales hidden` July-2026 total **Value = ₹4,45,85,600.89**. SAP Σ(`DocTotal−VatSum`) over the same 75 U_ARNO='H' docs = **₹4,45,85,605.95**. Diff **₹5.06 (0.00%)**. → **Hidden `value` = net-of-GST taxable.**

**4. Sales-vs-CN "Total Sales" → Σ INV1 taxable — EXACT on a clean day.**
CP `sales cn --company oil` for **2026-08-20 alone**: Σ`sales_rev` = **₹1,27,08,672.79**. SAP Σ taxable, Oil, DocDate=2026-08-20, `Cancelled eq 'tNO'` = **₹1,27,08,673.37**. Diff **₹0.58**. → **`sales_rev` = net-of-GST taxable (same basis as Accounts, and as hidden `value`).**

**5. Sales-vs-CN "Total CN" → SAP CreditNotes — RECONCILES (rounding only).**
CP total CN (`cng_rev`) for 2026-08-20..21 = **₹1,40,993.45**. SAP `CreditNotes`, Oil, same window, `Cancelled eq 'tNO'` = 6 credit notes, Σ(`DocTotal−VatSum`) = **₹1,40,994.33**. Diff **₹0.88 (0.0006%)**.

**6. Sales flow open order → ORDR/RDR1 — MATCH.**
CP `sales flow-open-items` order **1726086707** (from a 2026-08-21 flow row, `order_open:true`, keyed by MANSI): party "JIVO MART PVT LTD", 48 open FG lines, `total_pcs 1,331,672` / `total_open 1,547,924 L`. SAP `Orders/DocNum 1726086707` (Oil): `CardCode CUSTA000606 (JIVO MART PVT LTD)`, `DocumentStatus bost_Open`, `DocDate 2026-08-18`. **Header matches; open order confirmed.**

**Tax-only-invoice gotcha (resolved during recon — important lens finding):** over the 2-day window CP `sales_rev` (₹3,30,29,738) exceeded a naive header `Σ(DocTotal−VatSum)` (₹3,13,38,199) by ₹16.9 L. Root cause found live: invoice **626080444** (JIVO WELLNESS) is a **tax-only / supplementary invoice** (`TaxOnly:tYES`) — its header `DocTotal` is just the ₹80,950 IGST, but the line carries `LineTotal = ₹16,19,000` taxable base. Because CP sums **line** taxable (`INV1.LineTotal`), it correctly attributes that ₹16.19 L of goods value; a header-based sum would miss it. **So an AI reconciling CP sales to SAP must sum `INV1.LineTotal`, not header `DocTotal−VatSum`, on days with supplementary/tax-only invoices.**

---

### How the sales lens differs from the Accounts lens (summary)

- **Same money basis, different framing.** CP Total Sales / hidden Value / compare `taxable` are all **net-of-GST taxable** — the same basis as Accounts turnover. The difference is *presentation*: sales keeps gross, Goods-CN, Service-CN, and Net as separate drillable columns and pivots them by channel/state/**territory owner**/product.
- **Line-level, not header-level.** CP sums `INV1.LineTotal`, so it captures tax-only/supplementary invoice bases that a header `DocTotal−VatSum` misses.
- **Hidden (`U_ARNO='H'`) is a first-class sales concept** with its own audit page; the dashboard "Done" excludes it, Accounts turnover does not.
- **Dispatch/bilty/vehicle/driver look native but are SAP UDFs on OINV** — the single biggest "joined-vs-sourced" trap.
- **Ownership is a client-side territory map** (`main_group`+`state`→owner), NOT the SAP `person` UDF.
- **Company coverage is uneven:** CN & Flow = Oil + Beverages; Hidden & Compare = **Oil only**; Dispatch = single range, **no company toggle** (returns the oil DB incl. its Wellness/Mart branch series). None of these five reach the **Mart** company DB.

---

### Open questions (unverified — need a follow-up read)

1. **Does "Sales vs CN" Total Sales include hidden (`U_ARNO='H'`) invoices?** The 2026-08-20/21 sample had **0 hidden invoices**, so this couldn't be tested. Needs a day that has both, or a code read. (The dashboard "Done" excludes hidden; whether the *CN report's* gross does is unconfirmed — confidence that it includes them: ~60%.)
2. **Goods-vs-Services CN split rule.** Inferred to be inventory-line vs service/non-inventory-line on `ORIN`/`RIN1`; not directly verified against an `RIN1` line dump. The live sample had `cns_rev`=0 throughout, so the Services path is untested against SAP.
3. **`debit_note` / `combo` fields** on hidden rows are live but undocumented — meaning and whether debit notes add to or are excluded from Value is unverified (they did not measurably move the July total, which reconciled to ₹5).
4. **Intercompany (C-0005).** CP visibly **includes** intercompany parties (JIVO MART CUSTA000606, JIVO WELLNESS) in oil sales/flow/dispatch — it does **not** apply the 23-CardCode intercompany exclusion. An AI answering "external sales" must exclude them itself; the sales lens does not.
5. **`sales data` (Compare grid) basis** is owned by another slice; only the `compare-docs` drill was verified here.
6. **Money panels blank for `preshit`** did not affect this domain — all five operational endpoints returned full data for this login.

*Sources: CLI `/Users/damanpreetsingh/jivo-cli/control-panel/cli/jivo/jivo sales {cn,hidden,flow,flow-open-items,dispatch,compare-docs,channel-docs}` (live 2026-08-25); SAP via sapb1 MCP `JIVO_OIL_HANADB` (`Invoices`, `CreditNotes`, `Orders`); lineage `connections/lineage-evidence/sourcemaps/control-panel.md` §3(a).*

---
## OIH — Order In Hand (the open order book)

**One line:** OIH is the sales team's name for the *open sales-order book* — confirmed customer
orders that SAP has accepted but not yet invoiced/dispatched. It is "future revenue already
committed." The sales team reads it primarily as a **VOLUME** (litres/pieces), split
**COMMODITY vs PREMIUM**, rolled up per salesperson — not as a rupee figure the way Accounts
would. Everything below is verified live on **2026-08-25 ~14:00–14:05 UTC** against the live
Control Panel (`138.252.101.118:9080`, login `preshit`) and live SAP `JIVO_OIL_HANADB`.

Source of truth behind the lens: **SAP `ORDR` (order header) + `RDR1` (order lines), the line's
open quantity `RDR1.OpenQty`** (Service-Layer `Orders` → `DocumentLines[].RemainingOpenQuantity`).
The Control Panel does NOT invent OIH — it filters SAP open-order lines to finished goods, parses
the litre pack size out of the item name, splits by `OITM.U_TYPE`, and attributes to the SO's
salesperson (`OSLP`). Lineage confirmed field-for-field below.

CLI (all read-only):
```
control-panel/cli/jivo/jivo oih summary        --agent   # ₹→ no; LITRES per salesperson
control-panel/cli/jivo/jivo oih breakdown      --agent   # one row per open FG line, prem/comm litres + pcs
control-panel/cli/jivo/jivo oih rows           --agent   # open litres per item/customer (channel view), date-scoped
control-panel/cli/jivo/jivo oih commodity-rows --agent   # same, filtered to u_type=COMMODITY
```
Endpoints: `GET /realise/api/{order-in-hand,oih-breakdown,order-in-hand-rows,commodity-oih-rows}/`.

### Term table

| Term | Meaning (sales lens) | SAP lineage (verified) | Differs from Accounts / raw SAP | Gotchas + corrections |
|---|---|---|---|---|
| **OIH / Order In Hand** | Open, uninvoiced sales orders = committed future demand | `ORDR`+`RDR1` where `RDR1.OpenQty>0`; header `DocStatus`/`DocumentStatus`='Open' | Accounts has no OIH concept — it counts only *invoiced* turnover (`OINV`). OIH is the pipeline *before* the invoice. | **OIH is line-open-qty driven, not header-status driven** — a line with `OpenQty>0` counts even on a partly-delivered order. Reconciles better than header `DocStatus` (C-0019). |
| **OIH litres** (the headline `oih summary` value; breakdown `premium`+`commodity`; `open_qty`) | Open volume in **LITRES** | `Σ RDR1.OpenQty(pcs) × parsed-pack-litres` per line | Accounts thinks in ₹; the sales team's OIH headline is **volume**. | **VAULT BUG:** `oih-breakdown.md` and `order-in-hand.md` call `premium`/`commodity`/the summary value "₹/value". **They are LITRES.** Proven: 208 pcs × 5 LTR = `commodity` 1040; summary per-person == breakdown litre-sum exactly. |
| **`*_pcs`** (`premium_pcs`, `commodity_pcs`) | Open **pieces** (single bottles/tins) | `RDR1.OpenQty` verbatim (UoM=PCS) | — | C-0001 lives here: `_pcs` is single bottles, NOT cartons. `litres = _pcs × pack_size` (pack parsed from item name: `5 LTR`→×5, `500 MLS`→×0.5, `200 ML`→×0.2, `13 KGS`→×14.286 via oil density). |
| **COMMODITY** | Bulk, low-realisation oils (Kachi Ghani mustard, refined, soyabean) | line item `OITM.U_TYPE = 'COMMODITY'` | Same field Accounts uses; taxonomy is `U_TYPE`, never name-match | Split is **per line/item**, not per order. One SO mixes both (SO 1726086707 has commodity mustard *and* premium olive lines). |
| **PREMIUM** | Branded, higher-realisation oils (olive, cold-press, sesame, ghee) | `OITM.U_TYPE = 'PREMIUM'` | — | `oih commodity-rows` filters to COMMODITY only; premium share = breakdown `premium` sum. |
| **OIH RLZ** | ₹/L realisation *locked inside* the order book | `Σ RDR1 open ₹ ÷ Σ open litres` | Accounts' "realise" (net of GST − CN); OIH RLZ is on *orders* not invoices, and is **gross of returns** (no CN against an open order) | **Not returned by any `oih/*` endpoint** — those are litres+pieces only. RLZ appears on the Slide-2 channel cards (`sales-data`). Compute = OIH₹/OIH-L. |
| **BAL W/O OIH** | Target litres still needed *after* the open book lands = `TGT − DONE − OIH` | Django target − invoiced − OIH litres | Pure sales-planning math; no Accounts equivalent | OIH is *subtracted* from the gap, i.e. treated as good-as-done. If a customer cancels the SO, this over-credits the salesperson. |
| **sales_person** | Owner credited with the OIH | `ORDR.SlpCode → OSLP.SlpName` | Accounts never attributes to a person | Header-level owner; every line of an SO inherits it. Reassigning the SO moves the whole OIH. |
| **main_group** | Channel bucket (GT/MT/ROI/E-COMMERCE/HORECA/CSD/CORPORATE) | party `OCRD.U_Main_Group` | C-0015: `U_Main_Group` differs across company books | breakdown key = `main_group`; **commodity-rows key = `u_main_group`** (same thing, different spelling). |
| **sub_group** | Oil variety (MUSTARD, OLIVE, SOYABEAN, CANOLA, GHEE, RICE BRAN…) | `OITM.U_Sub_Group` | — | 11 varieties live now. Never parse from name — use the field. |
| **OIH vs Stock** | Open demand per item vs finished-goods stock per warehouse | breakdown embeds `item_stock` (litres) + `item_stock_pcs` (pcs) keyed by item, over `warehouses=[GP-FG, BH-EC, BH-PF, BH-BT]` | Ops view, not a ledger view | The `/inventory/oih-vs-stock/` route 404s; the real page is `/realise/oih-vs-stock/` and its data is exactly the `item_stock*` block inside `oih breakdown`. `warehouses` is now **4** wide (vault said 3 — `BH-BT` added). |

### Endpoint field shapes (live)

- **`oih summary`** → `{data: {<PERSON>: <open litres>}}`. Live now: PRABHU SIR 1,573,484 · SUNNY JI
  150,697 · RAMINDER JI 148,888 · PRINCE 36,000 · TANJEET JI 32,031 · RAVINDER CHADHA JI 18,893 ·
  PRESHIT 10,161 · NAZIM 4,945 · SACHIN STEPHEN 1,024 · TARUN 700 · HAPPY 0 · TEJPAL 0. **Values are
  litres.**
- **`oih breakdown`** → `{rows:[{main_group,state,sub_group,packtype,item,customer,so_no,
  sales_person,sku,premium,commodity,premium_pcs,commodity_pcs}], item_stock, item_stock_pcs,
  warehouses, dims}`. `premium`/`commodity` = open litres in that tier; `*_pcs` = open pieces. One
  row per open FG line. 255 rows / 88 SOs now.
- **`oih rows`** → `{data:[{main_group,state,sales_person,card_name,u_type,u_sub_group,item_name,
  sku,open_qty}]}`; `open_qty` = open litres. Accepts `--start/--end` (rarely needed — the open book
  isn't date-bound). 243 rows now.
- **`oih commodity-rows`** → `{data:[{u_type,u_main_group,u_sub_group,state,card_name,item_name,
  open_qty}]}`; COMMODITY only. 92 rows now.

### Reconciliation results (live, 2026-08-25)

**All five checks pass.** SAP = `JIVO_OIL_HANADB` (Oil company).

1. **Line count, SO 1726086707** (JIVO MART, the big intercompany transfer): CP breakdown **47
   rows** = SAP **47 open lines**. Exact.
2. **Open pieces, SO 1726086707:** CP `Σ(_pcs)` = **1,331,672** = SAP `Σ RDR1.OpenQty` = **1,331,672**.
   Exact to the piece.
3. **Individual lines:** `FG0000128 JIVO GOLD 5 LTR` — CP 208 pcs / 1040 L, SAP `OpenQty`=208 (×5
   LTR = 1040 L). `FG0000149 JIVO GOLD 1 LTR` — CP 50,000 pcs / 50,000 L, SAP `OpenQty`=50,000.
   Exact; confirms `litres = pcs × pack`.
4. **Portfolio open-order count:** CP OIH = **88 distinct SOs**; SAP open orders (Oil,
   `DocumentStatus eq 'bost_Open'`) = **89**. Every CP SO is a real SAP open order (zero phantoms).
   The **one** SAP order CP omits is **DocNum 1726086800** (BALAJI MARKETING, DocTotal ₹1, created
   today) — its only line is **PM0000005 "CARTON 1 LTR 12 POUCHES"**, a packaging-material item, not
   a finished good. ⇒ **CP OIH is finished-goods-only**; packaging/non-FG lines are dropped. Gap
   fully explained.
5. **Internal cross-check:** breakdown COMMODITY litres = **1,295,861.99** = `oih commodity-rows`
   total `open_qty` = **1,295,861.99**. Exact. And `oih summary` per-person == breakdown per-person
   litres for 6 people exactly (NAZIM 4945.2, PRABHU 1,573,484, PRESHIT 10,161, RAMINDER 148,887.58,
   RAVINDER 18,893.28, SACHIN 1,024).

**Headline current OIH (Oil), live:** ≈ **2.05 million litres** open
(`oih rows` total 2,053,039 L; `oih breakdown` prem+comm 2,052,339 L — the ~700 L delta is
TARUN's line + live-cache timing between the two calls). Split: **COMMODITY 1,295,862 L (63%) /
PREMIUM 756,477 L (37%)**.

**Materiality flag — intercompany is NOT stripped.** PRABHU SIR's 1,573,484 L (77% of all OIH) is
almost entirely **one order**: SO 1726086707 to **JIVO MART PVT LTD** (CardCode CUSTA000606), an
intra-group Oil→Mart stock transfer worth ₹37.77 cr, carrying **1,547,924 L** of open volume. Per
C-0005 Accounts excludes the 23 intercompany group CardCodes from turnover; **the sales OIH does
not exclude them.** A sales AI must not read PRABHU SIR's OIH as external market demand — it is
mostly an internal pipeline fill. (WAL MART, another large open-order party here, is a genuine
external MT customer, not intercompany.)

### The sales definition vs the Accounts definition (say this out loud)

- **Accounts "turnover"** = `OINV (DocTotal − VatSum) − CreditNotes`, by `DocDate`, `Cancelled='tNO'`,
  intercompany excluded. It is **invoiced ₹, net of GST and returns.**
- **Sales "OIH"** = open `ORDR/RDR1` finished-goods lines, **not yet invoiced**, measured in
  **litres/pieces**, intercompany **included**, no GST/CN concept (an open order has neither). OIH
  and turnover never overlap: the day an OIH line is invoiced it leaves OIH and enters turnover.
- **Realisation:** Accounts realise = net-of-GST-and-CN ₹/L on invoices; **OIH RLZ** = ₹/L implied
  by the still-open order lines (gross, order-priced). Different documents, different numerator.

### Open questions

- **OIH ₹ total / OIH RLZ source.** The four `oih/*` endpoints return only litres+pieces — no rupee
  field. OIH RLZ (₹/L) shown on the Slide-2 channel cards must be computed from `sales-data`
  (`channel_rows` OIH ₹ ÷ OIH litres). Not yet reconciled to `RDR1` open ₹ (`OpenSum`) live —
  worth a follow-up in the sales-data slice.
- **`oih summary` per-person drift.** Summary vs breakdown agree exactly for the big accounts but
  differ for PRINCE (36,000 vs 79,000), TEJPAL (0 vs 33,215), SUNNY/TANJEET (±1,440 swap). Likely a
  server-side cache-timing difference between the two live calls plus header-level reassignment;
  could also be a summary-side filter (e.g. a date or channel scope) the breakdown lacks. Under ~5%
  of total. Not run to ground.
- **Does `oih rows`/`commodity-rows` `start`/`end` actually filter?** Params exist; the open book is
  not naturally date-bound. Untested whether they filter on `ORDR.DocDate` or are inert.
- **Server-side cache TTL.** Lineage notes a cache between SAP and the API (`sales-pulse` polls it).
  OIH numbers are "near-live but cached" — TTL not measured. The exact-to-the-piece SO reconciliation
  suggests the lag is small (minutes), but this is not guaranteed at month-end load.
- **`item_stock` units for OIH-vs-Stock.** `item_stock` is litres and `item_stock_pcs` is pieces per
  the `warehouses=[GP-FG,BH-EC,BH-PF,BH-BT]` array; not independently reconciled to `OITW` stock
  live in this pass (belongs to the stock-available slice).

---
## Accounts — AR aging, open payments, claims, credit

*AI-facing decoder for JIVO's Control Panel (the sales team's "god software") as it re-expresses SAP B1 receivables. Every number below was pulled **live 2026-08-25** via the Control Panel CLI (`control-panel/cli/jivo/jivo`, user `preshit`, base `http://138.252.101.118:9080`) and cross-checked against **live SAP B1** (host `138.252.101.222:50000`, login `manager`) through the `sapb1` MCP. Read-only throughout.*

> **Money-gating note:** `preshit`'s login blanks the *revenue/expense/salary/COGS* panels, but **every A/R panel in this domain returned real ₹** — aging, open-payments, credit and claims are all fully visible to this login. Nothing in this section is "money-gated".

---

### The one thing to get right: "Outstanding" is TWO different numbers

The sales team says **"outstanding"** on three screens and means two incompatible things. Conflating them is the classic error.

| Flavour | Where | What it really is | SAP source | Oil book, live 2026-08-25 |
|---|---|---|---|---|
| **Gross open-invoice balance** | Customer-Aging "Total Outstanding" / "Balance Due", the `bal` column | Σ of the *unpaid residual of each open invoice*, before netting advances/on-account cash/credit notes | `OINV` open docs, balance from `JDT1` reconciliation | **₹82.31 Cr** (Σ `bal`, 4,843 invoices, 336 parties) |
| **Net party ledger** | Credit page `ledger`; Oil-aging `outstanding` column; the accounts team's "ledger balance" | `BusinessPartners.CurrentAccountBalance` — the whole account netted (positive = debit/owes JIVO, negative = advance/credit) | `OCRD.CurrentAccountBalance` / `JDT1` | **₹32.45 Cr** (net, credit-page `total.ledger`) |

The ₹82.31 Cr vs ₹32.45 Cr gap is **not an error** — it is C-0019 made visible. SAP marks invoices `Open` that are already covered by an unapplied on-account receipt or a manual JE, so the gross open-invoice pile is far larger than the netted ledger. **When a salesperson says "party X owes us," ask which screen: aging (gross) or ledger/credit (net).**

---

### Term table

| Term | Meaning (sales-team lens) | SAP lineage (entity · column · filter) | Differs-from-accounts / raw SAP | Gotchas & corrections |
|---|---|---|---|---|
| **Customer Aging** | A/R book split into overdue buckets, per company. Oil = flat per-open-invoice feed the client buckets; Mart/Bev = server pre-bucketed pivots. | `OINV` (open A/R) + `JDT1` (reconciliation) per company DB. Django adds only a `remark` overlay column. | Accounts would read the netted ledger; the aging shows **gross** open-invoice residuals, so its headline is bigger than the ledger. | CP Oil aging = **4,843 rows** but SAP has **13,082** open Oil invoices (`bost_Open`,`tNO`) — CP ages the *reconciled* balance, not SAP's unreliable open flag (**C-0019**, **C-0023** ledger-from-JDT1). |
| **`bal` (Oil)** | Open balance still owed on that one invoice. | Per-`OINV` open residual. | This is the *gross* number the aging totals. | Always ≥ 0 in Oil (0 negative rows on 4,843). Advances/CNs never appear here — they live in `outstanding`. Σ `bal` = the "Total Outstanding" KPI. |
| **`outstanding` (Oil row)** | *Not* the invoice's outstanding — it is the **party's whole net ledger**, printed identically on every one of that party's invoice rows. | `BusinessPartners.CurrentAccountBalance` for the row's `code`. | Same as the accounts "ledger balance"; positive = debit, negative = advance/credit. | **NEVER sum this column** — it repeats per invoice, so Σ over 4,843 rows = ₹6,134 Cr of nonsense. Verified equal to `CurrentAccountBalance` on 4 parties to the paisa (see recon). |
| **`total` (Oil row)** | Original invoice value. | `OINV.DocTotal` (GST-incl). | — | Gross of GST. |
| **Balance Due (Mart/Bev)** | Net open balance of the customer, split into buckets that sum to it. | Customer's `BusinessPartners.CurrentAccountBalance`, bucketed by invoice age. | Here the pivot **is** the net ledger (buckets can go negative for advances/CNs). | Σ of the five buckets = `balance_due`. Bucket `b61_90` etc. can be **negative** (Mart total `b61_90` = −₹63.4 L live). |
| **Aging buckets** `b0_30 / b31_60 / b61_90 / b91_120 / b121` | Balance by overdue age: 0–30 = current, 121+ = seriously overdue. | Age computed from invoice/due date vs `as_of`. | — | Oil buckets are derived **client-side from `days`**; Mart/Bev arrive pre-bucketed from the server. |
| **`days` / `tdd` / `ltd` (Oil)** | `days` = invoice age (doc-date → as_of); `ltd` = last-txn / due date; `tdd` = days past that due date. | Derived from `OINV.DocDate` / due date. | — | Oil main-view buckets key off `days` (invoice age), not strict due-date aging. |
| **Format** | The grouping band in the aging table. | Oil/Mart = channel `U_Main_Group`-style band (`E-COMMERCE, BRANCH, PARENT, ROI, GT, CORPORATE, CALL CENTER, STAFF, REFERENCE, WEBSITE`); **Bev = salesperson name** (`OSLP`). | Accounts groups by GL/party, not by sales "Format". | **C-0015**: `U_Main_Group` differs across company books — a Format band is company-specific, never compare across companies. |
| **B2B / B2C (Mart only)** | B2B = customer has a GSTIN on file; B2C = none. | `OCRD` GSTIN present/absent. | Sales segmentation, not an accounts field. | Only Mart exposes `segment`/`gstin`; Oil & Bev do not. |
| **Open Payments / "Payment on Account"** | Customer receipts **received but not yet applied** to invoices, in a date window. | SAP `ORCT` (IncomingPayments, `DocType rCustomer`); `amount` = `CashSum + TransferSum`. | Accounts sees the same receipts in the ledger; sales isolates the *unapplied* slice. | **`open_bal` is CP's own recomputation, NOT `ORCT.OpenBal`** — sourcemap proved CP `open_bal` 1,132,770 vs SAP `ORCT.OpenBal` 20,104.42 on the same receipt. Do **not** conflate. `amount` *does* tie to `ORCT` exactly (recon below). |
| **Contact Person (Open Payments)** | Assigned territory owner. | **Derived in-browser** from `main_group × state`, not a SAP field. | — | Exists as a filter/drill dimension only; never in the API payload. |
| **Claims** | Hand-keyed register of customer claims (NSO/TOT/LOTS/QPS/FIXED-BONUS/support/advertisement/FOC etc.) with a pass/hold workflow. | **None — Django-only.** Not a SAP feed. | Accounts has no equivalent object; the `ref_inv_no` values resolve in **no** SAP company. | Live: **31 rows, ₹12.72 L, every row on hold, `claim_passed`=0, all `main_group MT`.** `hold_amount = claim_amount − claim_passed`. Grew from 6 rows/₹2.67 L at last recon — it is a living manual ledger. |
| **Required Credit Limit** | How high a party's SAP credit limit must be so pending orders release without a credit block. | `total.value.required_limit`. | A **management target**, not read back from SAP. | `Required Limit = Total Outstanding × 1.02`; verified to the paisa (₹70.96 Cr × 1.02 = ₹72.38 Cr live). |
| **Total Outstanding (Credit page)** | Ledger dues **plus** open-order value. | `ledger (CurrentAccountBalance) + OIH revenue`. | Accounts would never fold un-invoiced orders (OIH) into "outstanding". | Live: ₹32.45 Cr ledger + ₹38.51 Cr OIH = ₹70.96 Cr. OIH = Order-In-Hand (open uninvoiced SOs). |
| **Payment Done / Remaining (Credit)** | `payment_done` = bank receipts (`ORCT`) dated on the as-of day; `remaining` = Total Outstanding − Payment Done. | `ORCT` on `as_of`. | — | Live: payment_done ₹1.99 Cr, remaining ₹68.97 Cr. |
| **Credit Lock** | Manager freezes *Total Outstanding* & *Required Limit* for N days (default 30). | **Django-only** flag. | **Not** SAP's `OCRD` freeze / `frozenFor`. | Live `lock: null` (no freeze active). Ledger/Payment/Remaining stay live even while locked — by design. |
| **Aging Remark / Special Price** | Per-invoice note/price overlay in the Oil & Bev RAW workspaces. | **Django overlay** (`aging-remark*`). SAP untouched. | Invisible to accounts/SAP. | WRITE endpoints — never executed. Overlay is **~0% populated** in practice. Mart has no remark overlay. |
| **Credit Terms / Payment Terms** | How long a party may take to pay (14 values: `ADVANCE/CASH/0 DAYS, COD, CAD, 20% ADVANCE, 45 % ADV, LC 60, NET-01…NET-30`). | `OCRD` payment terms (`customer-master.payment_terms`). | Same field accounts uses. | Drives what counts as "overdue". |

---

### Reconciliations (live Control Panel ↔ live SAP, 2026-08-25)

**1. Open-payment receipt → SAP `ORCT` — RECONCILES (exact on doc/party/amount).**
CP `open-payments 2026-08-20` row `{doc_no 826246676, code CUSTA000352, AT OVERSEAS, amount 656250}` → SAP Oil `IncomingPayments DocNum 826246676` = `CUSTA000352 / AT OVERSEAS / DocDate 2026-08-20 / TransferSum 656250 / DocType rCustomer / Cancelled tNO`. Amount exact. **Caveat:** CP `open_bal` is CP's own figure, **not** `ORCT.OpenBal` (documented mismatch in the sourcemap).

**2. Mart aging top customer → SAP `OCRD` — RECONCILES to the paisa (and flags intercompany).**
CP Mart aging `top_customer = "JIVO MART PVT LTD - DL", value 102,172,535.28` (50.8% of the whole Mart book) → SAP Mart `BusinessPartners CUSTA000874 CurrentAccountBalance = 102172535.28`. Exact. **This is intercompany** (a JIVO group company; note the twin vendor card `VENDA000942`, −₹3.87 Cr) — Mart's single biggest "receivable" is from a sister entity (relate to **C-0005**).

**3. Oil `outstanding` column = SAP net ledger — RECONCILES on 4/4 parties.**
| Party | CP Oil `outstanding` | SAP `CurrentAccountBalance` | CP Σ `bal` (gross open) |
|---|---|---|---|
| CUSTA000352 AT OVERSEAS | −2,592 | −2,592 | 656,250 |
| CUSTA000851 MAHAVIR TRADING | 2 | 2 | 2,127,342 |
| CUSTA000510 SUBHASH CHANDER | −1,214.07 | −1,214.0715 | 2,665,644.93 |
| CUSTA000116 HARINDER SINGH | −289,015.31 | −289,015.31 | 1,143,060 |
Proves `outstanding` = net ledger (repeated per row) while `bal` = gross invoice residual. AT OVERSEAS is the archetype: one ₹6.56 L invoice sits "open" in aging, a ₹6.56 L on-account receipt sits "unapplied" in open-payments (same day, same amount, receipt #2 above), and the net ledger is ≈ 0 — three of this domain's screens describing one settled trade (**C-0019**).

**4. Credit-page `ledger` = SAP net ledger — RECONCILES on 3/3 parties; 2% rule to the paisa.**
`CUSTA000979 SAGAR TRADERS` ledger 11,377 = SAP 11,377 (Required Limit 11,377×1.02 = 11,604.54 ✓); `CUSTA000808 VIRCHAND KHIMJI` 2,327.14 = SAP 2,327.1378; `CUSTA001068 KAILIAN FOODS` 275 = SAP 275. Book-level: `outstanding 709,589,860.20 = ledger 324,521,638.92 + OIH 385,068,221.30`; `required_limit 723,781,657.37 = outstanding × 1.02`; `remaining 689,715,086.22 = outstanding − payment_done 19,874,774`. All internal arithmetic ties.

**5. Oil aging row count ↔ SAP open-invoice count — DOES NOT TIE, by design.**
CP Oil aging = **4,843** open-balance rows; SAP Oil `Invoices` with `DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'` = **13,082**. Expected mismatch: CP ages the reconciled ledger (invoices with a real remaining balance), SAP's `Open` flag is unreliable at JIVO (**C-0019** settled-by-JE / unapplied-on-account stay open; **C-0023** balance from JDT1).

**Live headline book (for reference):** Oil A/R gross ₹82.31 Cr (4,843 inv / 336 parties) · Mart Total Outstanding ₹20.12 Cr (58 cust, current 8.2%, >90d 75.4%) · Bev Total Outstanding ₹58.56 L (358 cust, current 38.7%) · Open-payments 2026-08-20 ₹1.915 Cr on 10 receipts · Claims ₹12.72 L, all held.

---

### Open questions

- **Is `credit` / `open-payments` strictly Oil-only?** Every sampled party resolved in the Oil DB and OIH is an oil-product concept (litres split premium/commodity/canola/olive), so I read both as the **Oil** book — but I did not find a company toggle to prove Mart/Bev are excluded. (Confidence ~85%.)
- **What exactly is CP `open_bal`?** Proven *not* `ORCT.OpenBal`; it appears to be CP's own JDT1-based unapplied-portion calc (sometimes = full receipt, sometimes a fraction). The precise formula is unconfirmed.
- **Oil bucket boundary field.** Oil main-view buckets derive from `days` (invoice age); whether the server pivot instead uses due-date/`tdd` for the boundary is unverified (the default Oil pivot is embedded in a `<script id="aging-data">`, not in the flat API I sampled).
- **Mart/Bev `original` vs `balance_due`.** `original` (e.g. Mart total ₹35.20 Cr) is the pre-payment document value; its exact SAP derivation (Σ `OINV.DocTotal` vs opening ledger) was not separately reconciled.

---
## Targets — product, flex, segment, node, channel

*Sales-lens decoder. Live-verified 2026-08-25 against Control Panel `http://138.252.101.118:9080` (login `preshit`, admin) and SAP B1 Service Layer (`JIVO_OIL_HANADB`). Read-only throughout — no write/`save-targets` endpoint was ever called.*

### Headline: the target layer is the app's OWN data — it is NOT in SAP

This is the single most important fact for a future AI. Everything *else* the Control Panel serves is a re-dressed SAP row (invoices, orders, stock, ledgers). **The five target endpoints are the exception: they read the Django app's own database and have no SAP object behind them at all.** Verified two ways:

- **Lineage recon** (`connections/lineage-evidence/sourcemaps/control-panel.md` §2, §4): the `targets (5)` command group is the only group whose "real source behind Django" is **"Django's own DB. No SAP object."** The recon searched all three HANA company schemas — `SELECT ... FROM SYS.TABLE_COLUMNS WHERE COLUMN_NAME LIKE '%TARGET%' OR '%TGT%'` — and every hit was a stock SAP-internal column (document-flow pointers, workflow fields). SAP's `@BUDGET`/`@BUDGET1` UDT is a **cost-budget** dimension (`U_FIXED_AMOUNT`, `U_MONTH`), not the litre/realise sales target. There is no sales-target table anywhere in SAP.
- **Live behaviour**: `targets list` returns `"source":"default"` on every row (Jul & Aug 2026). The values are hard-coded app defaults, editable only through the gated `POST /realise/api/save-targets/` write path (admin PIN re-auth via `/verify-pin/`). As of 2026-08-25 **no saved override exists in any month I sampled** — every product row is `default`, and `segment` override sets come back empty `{}`.

So: **actuals (DONE) are SAP; targets (TGT) are the app.** The dashboard's whole job is to staple the two together. You cannot query a target from SAP, and you cannot audit a target against SAP — there is nothing to audit it against.

### What the sales team means by a "target"

A target at JIVO is a **monthly volume goal in LITRES**, optionally carrying a **realisation goal in ₹/litre**. It is expressed five different ways at five different grains, and — critically — **those five views are maintained by hand and do NOT foot to each other** (see Reconciliation R3). "Did we hit target?" has no single answer until you say *which* target.

The unit is always **true litres** — the app has already applied the pieces→litres conversion ([C-0001]: `INV1.Quantity` is pieces/bottles, the "20 PCS" in item names is carton config). The `liter`/`litres` fields the app returns = parsed pack-size × pieces, so target litres are directly comparable to them. You never multiply by carton config here.

### Term table

| Term | Meaning | SAP lineage | Differs from the accounts view | Gotchas / corrections |
|---|---|---|---|---|
| **TGT** | The monthly target — litres and/or ₹-value goal, per channel/segment/node/product | **None (Django DB).** No SAP object | Accounts has no concept of a sales target; "turnover" is a backward-looking actual | Five independent grains that don't reconcile (R3). All `source:default` right now |
| **DONE / DONE L** | Achieved value (₹) / achieved volume (litres) month-to-date against TGT | SAP `OINV`/`INV1` net of returns (`ORIN`/`RIN1`), via `sales-data` | DONE L is **litres** — accounts never measures volume | `liter` already = pack-size × pieces ([C-0001]); can go **negative** (Jul PREMIUM\|GHEE = −1,468 L, returns > sales) |
| **BAL / BAL W/O OIH** | Gap left to target: `TGT − DONE`; and `TGT − DONE − OIH` | Derived (TGT from Django, DONE/OIH from SAP) | n/a — a planning measure, not a ledger figure | OIH = open sales-order book (`ORDR`/`RDR1.OpenQty`) |
| **REALISE (₹/L)** | Net avg selling price per litre actually earned, after schemes/CN | `sales-data`: net sales ₹ ÷ litres, from `OINV`/`INV1`/`ORIN` | Accounts turnover = `DocTotal − VatSum − CreditNotes` in **rupees**; realise is **₹ per litre**, a rate not a total | The whole API is named for it (`/realise/api/…`) |
| **`tgt_ltrs` / `target_sale`** | Product-target **litres** for a `U_TYPE\|SUB_GROUP` key | Django DB | — | `target_sale` in the Slide-1 feed is a **misnomer — it is litres, not rupees**. Equals `tgt_ltrs` exactly |
| **`tgt_rate` / `target_realise`** | Product-target **realisation** (₹/L goal) for that key | Django DB | — | Equals `tgt_rate`. In `nodes` it was **0 in July** (litre-only), **populated in August** — the ₹/L target is a recent addition |
| **Product target** (`targets list`) | Litres + ₹/L keyed by `U_TYPE\|U_Sub_Group` (16 keys) | Django DB; key vocab derived from SAP `OITM.U_TYPE`+`U_Sub_Group`(+`U_Variety`) | — | Key taxonomy is the app's **Slide-1 derived** taxonomy, not raw OITM (R1): OLIVE is split into `OLIVE`+`EXTRA VIRGIN OLIVE` by `U_Variety`; premium MUSTARD is relabelled `YELLOW MUSTARD` |
| **FLEX target** (`targets flex`) | Flat litre goal per **salesperson** for the month | Django DB | — | Key format `¦person=<NAME>` (broken-bar `¦` = U+00A6, generic flex-dimension prefix). `¦person=—` (em-dash) = unassigned bucket. **Empty `{}` when not yet set** (Aug 2026 was empty; July had 10 people) |
| **SEGMENT override** (`targets segment`) | Saved target overrides scoped to one segment (OILS/BEVERAGES/PREMIUM/COMMODITY) | Django DB | — | Holds **only explicitly-saved overrides**, never the defaults. **Empty `{}` is normal** and is what I observed for every segment |
| **NODE target** (`targets nodes`) | Litres (+ ₹/L) by **main_group × state × sales_person × segment** | Django DB | — | Two "segment" senses collide: the row's `segment` field = PREMIUM/COMMODITY (= SAP `U_TYPE`); the `seg` **query param** = OILS/BEVERAGES and **is ignored** — OILS and BEVERAGES returned byte-identical rows (R-note). Blank string = "all/unscoped" |
| **CHANNEL target** (`targets channel`) | One litre figure per **main group / channel** | Django DB; channel = SAP `OCRD.U_Main_Group` on the actual side | — | Channel **codes differ from the actuals**: target uses `ECOM`, SAP `U_Main_Group` says `E-COMMERCE`; 7 target channels vs 12 actual main-groups (R4) |
| **Channels: GT / MT / ROI / ECOM / HORECA / CSD / REST** | General Trade / Modern Trade / Rest-of-India / E-Commerce / Hotels-Restaurants-Catering / Canteen Stores Dept / residual | `OCRD.U_Main_Group` (party's governing main group) | Accounts groups by BP/GL, never by go-to-market channel | **ROI = Rest of India, not return-on-investment.** `main_group` values differ across company books ([C-0015]) — do not segment across companies on it |
| **Segment: OILS vs BEVERAGES** | Two reporting tracks (edible oils vs juices/wellness) | `OITM.U_TYPE`/`U_Sub_Group` taxonomy ([never name-match]) | — | The target layer sampled is **OILS/oil-company only**; BEVERAGES has its own feeds and the node `seg=BEVERAGES` filter did not actually scope (open question) |
| **Segment: PREMIUM vs COMMODITY** | Margin tier within OILS | SAP `OITM.U_TYPE` (values `PREMIUM`, `COMMODITY`; SAP also has `OTHERS` + blank which targets ignore) | — | This is the finer `segment` inside a node row, distinct from OILS/BEVERAGES |

### The five endpoints ↔ CLI methods (all GET, read-only)

| CLI | Endpoint | Shape | Live Aug-2026 sample |
|---|---|---|---|
| `targets list` | `GET /realise/api/targets/` | `{key → {tgt_ltrs, tgt_rate, source}}`, key = `U_TYPE\|SUB_GROUP` | 16 keys, all `source:default`; e.g. `COMMODITY\|MUSTARD` 625,000 L @ ₹145 |
| `targets flex` | `GET /realise/api/flex-targets/` | `{¦person=NAME → litres}` | `{}` (not yet set for Aug; Jul had 10 people, 1,295,000 L) |
| `targets segment` | `GET /realise/api/segment-targets/` | `{key → {tgt_ltrs, tgt_rate}}`, only saved overrides | `{}` for OILS and PREMIUM |
| `targets nodes` | `GET /realise/api/target-nodes/` | `[{main_group, state, sales_person, segment, target_ltrs, target_realise}]` | 21 rows; `target_realise` now populated (was 0 in July) |
| `targets channel` | `GET /realise/api/channel-targets/` | `{channel → litres}` | `{GT:400000, ECOM:1285000, MT:170000, ROI:115000, CSD:30809, HORECA:5000, REST:20000}` |

Write counterpart (documented, **never called**): `POST /realise/api/save-targets/` — persists product-target edits; gated behind an admin PIN modal (`/realise/api/verify-pin/`).

### Reconciliation results (live CP vs live SAP)

**R1 — Product-target taxonomy vs SAP OITM (Oil). RECONCILES, with a derivation caveat.**
The 16 Aug-2026 product keys vs distinct `U_TYPE|U_Sub_Group` in `JIVO_OIL_HANADB.OITM` (2,277 items swept live): **13 keys match a real OITM sub-group exactly**. The other 3 are **app-derived Slide-1 labels, not raw OITM values**:
- `PREMIUM|EXTRA VIRGIN OLIVE` — OITM has `PREMIUM|OLIVE` (105 items) and one `PREMIUM|EXTRA VIRGIN`; the app splits OLIVE by `U_Variety='EXTRA VIRGIN'` into a separate bucket. Proof: July line rows carry `PREMIUM|OLIVE` (289 rows) and **never** `EXTRA VIRGIN OLIVE`, yet the Slide-1 rollup shows both (OLIVE 236,716 L + EXTRA VIRGIN OLIVE 27,028 L).
- `PREMIUM|YELLOW MUSTARD` — OITM has no such sub-group; line rows carry `PREMIUM|MUSTARD` (32 rows), which the rollup relabels `YELLOW MUSTARD` (26,655 L).
- `PREMIUM|SLICED OLIVE` (target 0/0) — OITM files SLICED OLIVE under `OTHERS`, not `PREMIUM`; a placeholder key with a zero target.

Ruling: **target keys use the app's derived product taxonomy** (OITM `U_TYPE`+`U_Sub_Group` refined by `U_Variety`), never the raw OITM column. Never name-match a target key straight onto `OITM.U_Sub_Group`.

**R2 — TGT vs DONE, July 2026 OILS product total. RECONCILES.**
Product-target total **2,005,000 L** vs actual DONE **2,189,879 L** = **109.2 % of target**. The Slide-1 realise feed (`sales data`) embeds `target_sale`/`target_realise` per product row, and these equal the `targets` endpoint values field-for-field (e.g. `COMMODITY|MUSTARD` target_sale 625,000 @ target_realise 145; `PREMIUM|CANOLA` 350,000 @ 205). This is the app literally stapling its Django target onto the SAP-derived actual. Actual DONE lineage: `OINV`/`INV1` net of `ORIN`/`RIN1`, litres = pack-size × pieces.

**R3 — Do the four target layers foot to each other? THEY DO NOT. (The headline gotcha.)**
July 2026 totals, same month, same OILS business:

| Layer | July total | Aug total |
|---|---|---|
| Product (`targets list`) | 2,005,000 L | 2,005,000 L |
| Channel (`targets channel`) | 2,541,000 L | 2,025,809 L |
| Nodes (`targets nodes`) | 2,541,000 L | 2,805,809 L |
| Flex (`targets flex`) | 1,295,000 L | (empty) |

- **Product ≠ Channel** by **536,000 L** in July — two independent target-setting exercises over the same goal.
- **Nodes == Channel exactly (2,541,000)** in July — nodes were a clean decomposition of channel targets — **but in Aug they diverge by 780,000 L** (nodes 2,805,809 vs channel 2,025,809), because Aug added premium per-person node rows on top of the commodity figure that the channel target still reflects. Hand-maintained layers drift.
- **Flex (1,295,000)** is lower than all — it covers only the 10 named salespeople and omits the large unassigned house channels (ECOM, MT commodity, etc.).

For a future AI: **never quote "the July target" as one number.** It is 2.0 M (product), 2.5 M (channel/node) or 1.3 M (flex) depending on the lens.

**R4 — Channel target vs actual channel litres, July 2026. Vocab does NOT line up cleanly.**
Target (app) vs actual litres (`sales data`, `OCRD.U_Main_Group`):

| Channel | Target L | Actual L | % |
|---|---|---|---|
| ECOM / E-COMMERCE | 1,300,000 | 1,019,267 | 78 % |
| GT | 685,000 | 617,699 | 90 % |
| MT | 215,000 | 257,621 | 120 % |
| ROI | 256,000 | 214,928 | 84 % |

Caveats: target code `ECOM` ≠ actual `U_Main_Group` value `E-COMMERCE` (the app maps them); **7 target channels but 12 actual main-groups** — `CORPORATE`, `CASH SALE`, `STAFF`, `BRANCH`, `REFERENCE`, `PURCHASE OIL` carry real litres yet have no channel target.

### Open questions

- **Beverages / Mart target scope.** `targets nodes --seg BEVERAGES` returned **byte-identical rows to `--seg OILS`** (21 rows each, Aug), so the `seg` query param appears to be **ignored** by the nodes endpoint — I could not confirm a separate BEVERAGES node set exists, nor any Mart target layer. Needs a login/segment that actually scopes, or reading the server code.
- **Where the Django target table physically lives** is still unidentified (recon could not reach the app's DB host; it is confirmed *not* in SAP and *not* in the 15-DB Postgres cluster). So targets cannot be cross-checked at the row level against any datastore I can reach — only against the API's own output.
- **`target_realise` went from 0 (July nodes) to populated (Aug nodes).** Confirm this is a deliberate rollout of ₹/L node targets, not a data-entry artefact.
- **`preshit` money-gating.** Sales **volume + `line_total`** are visible to this login (used above), so TGT-vs-DONE in litres and ₹ is computable. Only the dedicated money panels (COGS, salaries, expense aggregates) are blank for this login — not relevant to the litre-based target layer.
- Whether the **`save-targets` flow ever writes back to SAP**: recon rules it Django-only (confidence ~85 %, code/doc evidence, write path not executed). No SAP UDT could receive it.

---
## Inventory & production

**Domain:** the Control Panel's *Inventory & Production* slice — how the sales/ops team reads SAP's
stock ledger (`OITW`/`OITM`), bills of material (`OITT`), work orders (`OWOR`) and the cross-company
Mart↔Wellness document flow, re-expressed in the team's own language (litres, boxes, "non-moving",
"can we make it?", "broken chains"). Every figure below was pulled **live 2026-08-25** through the
Control Panel CLI (`control-panel/cli/jivo/jivo`, base `http://138.252.101.118:9080`, login `preshit`)
and cross-checked against **live SAP** via the `sapb1` MCP (as_of `2026-08-25T14:0x:xxZ`, source=server).
Inventory panels are operational, not money-gated, so `preshit` sees them in full.

This slice is **pure SAP-on-SAP** — no Django-only numbers. The lineage sourcemap
(`connections/lineage-evidence/sourcemaps/control-panel.md`) rules the inventory group's nine endpoints
against `OITW`/`OITM`/`OWHS`, `OITT` (BOM), `OWOR`, and cross-schema `JIVO_MART_HANADB.OPOR` ↔
`JIVO_OIL_HANADB.ORDR/OPDN/OPCH/OINV`. My live checks below confirm the stock, feasibility, production
and reconciliation numbers tie to SAP to the rupee/piece (with one instructive ₹768 exception).

### How the sales team's stock lens differs from Accounts
Accounts think in **ledger balances and turnover** (`OINV.DocTotal−VatSum` net of `ORIN`). This slice
never touches turnover — it reads **physical on-hand** (`OITW.OnHand`), converts pieces→**litres** by
parsed pack size, ages stock by **movement date**, and reconciles the **inter-company paperwork chain**
by tax-**inclusive** `DocTotal`. So where Accounts say "sales ex-GST", inventory says "litres in the
godown" and "₹ (incl. GST) stuck / at risk". The reconciliation panel is the one place the two worlds
meet, and it deliberately uses GST-inclusive `DocTotal`, not the net-of-GST turnover figure.

### Term table

| Term | Plain meaning | SAP lineage (entity · column · filter) | Differs from Accounts / raw SAP | Gotchas + corrections |
|---|---|---|---|---|
| **Stock Available / On-hand** | Live finished-goods sitting in the godowns, "how much do we have right now" | `OITW.OnHand` per warehouse (Service Layer `Items.ItemWarehouseInfoCollection[].InStock`), summed = `OITM`/`Items.QuantityOnStock`. Live snapshot, no date param | Accounts never look at physical stock; this is In−Out of the ledger, **not** a valuation | **Live snapshot only, no history.** Vault claimed 5 FG warehouses; **live Oil now returns 15** (see Warehouses). Reconciles to SAP `QuantityOnStock` exactly (see recon). |
| **schema** | Which company book: `jivo_oil` / `jivo_mart` / `jivo_beverages` | Selects SAP DB `JIVO_OIL_HANADB` / `JIVO_MART_HANADB` / `JIVO_BEVERAGES_HANADB` | Same 3 companies Accounts use; default here is **Oil** | Recon endpoint uses a *different* enum: `oil` / `beverages` only (the seller/Wellness side) — no `mart`. |
| **Type (PREMIUM / COMMODITY)** | Oil grade split — branded/high-realise vs bulk staple | `OITM.U_TYPE` | Taxonomy field, correct to use | [C-0015] `U_Main_Group` differs across company books — don't segment across companies. **Never name-match** grade; use `U_TYPE`/`U_Sub_Group`/`U_Variety`. |
| **sub_group / variety / SKU** | Product family (OLIVE, CANOLA, MUSTARD…) / brand-variety / pack size (`1 LTR`) | `OITM.U_Sub_Group`, `U_Variety`, parsed pack size | — | SKU/pack size is parsed from the item, e.g. `1 LTR`; "20 PCS" in the name is carton config, not stock. |
| **Litres** (headline oil metric) | On-hand pieces converted to litres = pack-size × pieces | `OITW.OnHand` (pieces) × parsed litres-per-unit (`OITM.U_IsLitre`/pack size) | Accounts count value, not volume; this is a **volume** headline | **[C-0001] on-hand `qty` is in PIECES (single bottles), not cartons** — the CP already converts; don't re-multiply by the "20 PCS" carton config or you inflate ~20×. Talk in tonnes for RM; litres for FG. |
| **Boxes** | On-hand as cartons = pieces ÷ pcs_per_box | pieces ÷ `pcs_per_box` (Oil/Mart items carry `pcs_per_box`) | UI convenience unit | Beverages KPI is *labelled* "boxes" but the item rows still carry `litres`; **beverage item rows have no `pcs_per_box`** (only Oil/Mart do). |
| **Warehouse / godown code** | Physical stock location (GP-FG, BH-PF, BH-EC, BH-FU, BH-BT…) | `OWHS.WhsCode`/`WhsName`; per-warehouse stock in `OITW` | Same masters Accounts see, but sales think in godown codes | **Live-verified drift:** stock-available Oil now columns **15** warehouses `[GP-FG,BH-PF,BH-EC,BH-FU,BH-BT,BH-SC,BH-FG,BH-WST,PB-JP,BH-JW,BH-GR,DL-PS,BH-PP,DL-J3,PB-PS]` with a `default_warehouses` set of 6 `[GP-FG,BH-PF,BH-EC,BH-FU,BH-BT,BH-SC]` — **not** the vault's old 5. Mart returns 21 whs / 8 default; Beverages 14 / none. `BH-FU` shows on stock but is absent from the production warehouse master. |
| **Non-Moving Stock** | Slow/dead FG that hasn't been billed for a long time (liquidation queue) | Same `OITW`/`OITM` in-stock list + last-bill lookup on `OINV`/`INV1` | Accounts have no "non-moving" concept; this is an ops ageing view | **"Non-moving" is NOT a server flag** — it is a purely client-side `DaysSinceMoved ≥ N` cut (default **60**; set 0 to see all). |
| **DaysInStock** | Age of the on-hand lot since production | days since `ProdDate` of the oldest on-hand lot | — | Lot production date, not first-receipt of the item family. |
| **DaysSinceBilled** | Days since the item was last sold | days since `LastBillDate` (last `OINV`/`INV1` line) | — | Drives the heat colour (>180 hot / >90 warm). Can differ from DaysSinceMoved. |
| **DaysSinceMoved** | Days since last stock movement — **the field the non-moving filter uses** | days since last inventory movement | — | Differs from DaysSinceBilled when the item moved via a non-billing transaction (transfer, etc.). This is *the* definition of "non-moving". |
| **Value (₹ stuck)** | Rupees tied up in that on-hand stock | `Qty × PricePer` (`OITW.OnHand` × item price/cost) | Accounts value at cost in the GL; this is an ops "money parked in dead stock" heuristic | Value here is a display cost×qty, **not** a GL inventory valuation — don't quote it as book value. |
| **Last Customer / Last Code** | Who last bought it (chase target) | party name + `OCRD.CardCode` from the last `OINV` | — | Card code e.g. `CUSTA000606` = `JIVO MART PVT LTD` (intercompany buyer). |
| **Daily Production** | What actually got produced each day (output tracking) | `OWOR` (standard work orders): `DocNum`, `ItemCode`, `Warehouse`, `PlannedQty`, `CmpltQty`, `Status`, `OUSR.U_NAME` | Accounts don't track shop-floor output at all | **Standard work orders only** (`ProductionOrderType=bopotStandard`); rows include upstream **PM production** (PET-bottle blowing, `PM…` items) alongside FG fills — filter by variety/item for FGs. Default page view filters to `BH-PF`. |
| **Planned vs Completed** | Target qty vs actually produced | `OWOR.PlannedQty` / `OWOR.CmpltQty` | — | Litres = Completed × pack size; Boxes = Completed ÷ box size. Reconciles exactly (see recon). |
| **Work-order status** | `Planned` / `Released` / `Closed` | `OWOR.Status` → SL `ProductionOrderStatus` `boposPlanned/boposReleased/boposClosed` | — | CP "Closed" == SAP `boposClosed`. |
| **Production Feasibility / Max FG** | "Can we make this FG, and how many?" before scheduling | Explode `OITT`/`ITT1` BOM; compare `required = per_fg × qty` vs component `OITW.OnHand` in selected warehouses | Nothing Accounts touch — a materials-only planning calc | **Read-only, nothing is consumed; no work order created.** Materials only (no labour/resource). `max_fg` **can be negative** = SAP shows the component oversold in the chosen warehouse. |
| **RM / PM** | Raw material (loose oil) vs packing material (bottle, cap, label, tape) | BOM component `kind` from `OITT`; RM/PM item-code prefixes (`RM…`/`PM…`) | — | The binding constraint is usually the RM loose oil; PM is plentiful. |
| **available / all_wh / onhand** | Stock in **selected** whs / across **all** whs / in the component's primary BOM wh | all from `OITW.OnHand` sliced by warehouse set | — | `available` (selected whs) drives Balance & Max FG; `all_wh` is the whole-company total; widen "Stock from" to fix a negative. |
| **transferable ↪ / elsewhere** | Short here but enough sits in another godown | component short in selection but `all_wh ≥ required` | — | A hint to move stock, not a shortfall. |
| **Wellness–Mart Reconciliation** | Does the inter-company paperwork between **Mart (buyer)** and **Wellness (seller/mfr)** line up? | Cross-schema chain: `JIVO_MART_HANADB.OPOR` → `JIVO_OIL_HANADB.ORDR` → `MART.OPDN` → `MART.OPCH` → `OIL.OINV` (+ `ORIN` CN, `ODLN` delivery) | This is the panel where inventory meets **Accounts** (sidebar groups it under Accounts) | Uses **tax-inclusive `DocTotal`**, *not* net-of-GST turnover. `schema` = seller side (`oil`/`beverages`); **export always `schema=both`** because one PO can span Oil+Bev. Vendor `VENDA000001` = JIVO WELLNESS. |
| **Chain nodes PO→SO→GRPO→A/P→A/R** | Mart PO → Wellness SO → Mart goods-receipt → Mart A/P bill → Wellness A/R invoice (the mirror) | `OPOR`→`ORDR`→`OPDN`→`OPCH`→`OINV`; live rows also carry **CN** (`ORIN`) and **delivery** (`ODLN`) nodes | The A/R is the mirror of the A/P across the two books | Partials are **summed** per node before comparison. **Live: the chain also has `cn`/`cn_docs` and `delivery`/`delivery_docs` nodes the old vault didn't list.** |
| **MATCHED / MISMATCH / INCOMPLETE** | All nodes present & totals agree / all present but totals differ / a node is missing | comparison of summed node `DocTotal`s within **tolerance ₹1.0** | — | [C-0019] SAP `DocStatus 'O'` is unreliable at JIVO — recon doesn't rely on open/closed, it compares **amounts**. "Broken" filter = Mismatch+Incomplete (the accounts work-queue). **The per-node amount is CP's normalized tax-inclusive figure, and can differ from the posted `DocTotal` — see the ₹768 finding.** |
| **Ledger origin (PC/PS/IN…)** | Which SAP document type posted each ledger line | `JDT1`/`OJDT` transaction origin codes: `PC`=A/P invoice, `PS`=goods-receipt PO, `IN`=A/R invoice | [C-0023] party ledger is from `JDT1`, not doc extracts — this tab honours that | Balance(LC)=Debit−Credit; cancellations excluded server-side. |
| **OIH vs Stock** | Committed open orders (Order-In-Hand) vs current stock | **Realise-side**, not inventory: OIH from `ORDR`/`RDR1` open lines, stock from above | — | **`/inventory/oih-vs-stock/` 404s** — the working page lives under `/realise/oih-vs-stock/`. Left in the inventory sidebar only by grouping. See the realise/OIH decoder. |

### Live reconciliations (Control Panel vs SAP, 2026-08-25)

**1. On-hand stock per SKU = SAP `QuantityOnStock` (Oil) — exact, incl. per-warehouse.**
CLI `inventory stock --schema jivo_oil` vs SAP `Items`:

| Item | CP grand_total (units) | SAP QuantityOnStock | Match |
|---|---|---|---|
| FG0000185 (BB ROYAL BLENDED 1 LTR) | 1,043 | 1,043 | ✅ + per-wh exact (BH-BT 982, GP-FG 60, DL-PS 1) |
| FG0000005 (EXTRA LIGHT OLIVE 1 LTR) | 38,225 | 38,225 | ✅ |
| FG0000194 (SOYABEAN 1 LTR POUCH) | 36,722 | 36,722 | ✅ |

CP Oil FG total (derived): **784,323.58 L** across 159 SKUs / 16 sub-groups — PREMIUM 449,770.79 L,
COMMODITY 334,552.79 L. (Litre total is CP-derived via pack-size conversion; the *unit* side is what
reconciles to SAP to the piece above.)

**2. Production feasibility component on-hand = SAP `QuantityOnStock` — exact.**
CLI `inventory production-feasibility --fg-code FG0000149 --qty 1000 --warehouses ALL`: binding component
**RM0000021 LOOSE OIL GOLD available = 11,022 L**, `max_fg = 11,022`. SAP `Items(RM0000021).QuantityOnStock
= 11,022`. ✅ The feasibility engine reads live SAP on-hand and floors by the scarcest component.

**3. Daily production work order = SAP `ProductionOrders` (OWOR) — exact.**
CLI `inventory daily-production --start 2026-08-22 --end 2026-08-22`, doc **826202878** (FG0000030 Mustard
Kachi Ghani 1 LTR): CP planned 1,780 / completed 1,780 / status Closed / wh BH-PF. SAP
`ProductionOrders(826202878)`: PlannedQuantity 1,780, CompletedQuantity 1,780, `boposClosed`,
`bopotStandard`, Warehouse BH-PF. ✅ (Day had 8 closed WOs, all BH-PF, 64,156 units / 100,172 L completed.)

**4. Wellness–Mart recon chain (MATCHED) = SAP `DocTotal` — 4 of 5 nodes exact, A/P off by ₹768.**
CLI `inventory reconciliation --schema oil --date-from 2026-08-18 --date-to 2026-08-24`, chain **PO 826224590**
(status MATCHED, all nodes shown as ₹806,400):

| Node | Doc | CP amount | SAP `DocTotal` | Match |
|---|---|---|---|---|
| PO (Mart, `OPOR`) | 826224590 | 806,400 | 806,400 (`JIVO_MART`, Cancelled tNO) | ✅ |
| SO (Wellness/Oil, `ORDR`) | 1726086749 | 806,400 | 806,400 (`JIVO_OIL`) | ✅ |
| A/R (Wellness/Oil, `OINV`) | 626080463 | 806,400 | 806,400 (`JIVO_OIL`) | ✅ |
| **A/P (Mart, `OPCH`)** | 608264208 | **806,400** | **805,632** (VatSum 38,400; WTApplied 0; RoundingDiff 0) | ⚠️ **₹768 gap** |

The chain is classed **MATCHED** even though SAP's posted A/P `DocTotal` (805,632) is ₹768 below the
GRPO/PO/SO/AR value (806,400). So the recon panel's per-node "amount" is **not** the raw posted
`OPCH.DocTotal` — it is a normalized/base-linked tax-inclusive figure (most likely the GRPO-linked base
value), and MATCHED/MISMATCH is judged on those normalized numbers, not the ledger `DocTotal`. **Take-away
for a future AI: don't expect a recon node amount to equal `SELECT DocTotal FROM OPCH` — it can differ by a
real posting variance while still reading MATCHED.** (Confidence: high on the observed ₹768 gap and the
MATCHED verdict — both live-verified; medium on the exact "GRPO-base" mechanism — not traced to source.)

Recon summary for that window (schema=oil): total 7 chains — matched 4, mismatch 1, incomplete 2,
mismatch_value ₹55.39 Cr (one large MISMATCH chain PO 826224584, "Spread ₹553,877,814").

### Open questions
- **A/P node derivation.** Exactly which SAP amount CP puts on the A/P node (GRPO-linked base vs `OPCH1`
  line sum vs something else) is inferred, not traced — the ₹768 gap on 608264208 proves it isn't
  `OPCH.DocTotal`. Worth a source read of the recon view before quoting node amounts as ledger truth.
- **Litre total reconciliation.** CP's 784,323.58 L Oil FG total is CP-derived (pack-size conversion). I
  reconciled the *unit* side to SAP exactly for 3 SKUs but did not sum all 159 SKUs' litres against an
  independent SAP litre figure (SAP stores pieces, not litres).
- **Daily-production doc↔OWOR edge case.** The lineage vault flagged one row (FG0000441) where the app's
  planned/status disagreed with `OWOR` — possibly the app's `doc` isn't `OWOR.DocNum` for *every* row. My
  live check (826202878) matched exactly, so this looks like a stale/edge artifact, but a whole-day count
  reconciliation (CP row count vs `OWOR` count for a date) wasn't done — the "production day" date field
  in `OWOR` isn't a simple `DocDate`, so the join key needs confirming.
- **Warehouse-count drift.** Live stock returns 15 Oil warehouses (was 5 in the vault) and the production
  master is 31 (was 35). The masters clearly changed since the 2026-07 recon; treat any hard-coded
  warehouse list as stale.
- **Money-gating.** Inventory panels are operational and fully visible to `preshit`; none of this slice is
  money-gated (unlike sales ₹ / COGS / salaries which return empty for this login).

---
## Product & party taxonomy — the sales team language spine

*The cross-cutting vocabulary the JIVO sales team uses to name every product and every party, and exactly how each label maps to a live SAP B1 field. Everything below was verified against the LIVE Control Panel CLI (`control-panel/cli/jivo/jivo`, host `138.252.101.118:9080`, login `preshit`) and LIVE SAP B1 (Service Layer, `JIVO_OIL_HANADB`) on **2026-08-25**. Read-only throughout.*

### The one thing to internalise first
The sales team names **products** with a three-level oil hierarchy — **TYPE → SUB-GROUP → VARIETY**, plus **SKU** (pack size) — and names **parties** with a **MAIN GROUP** (which doubles as the sales *channel*) plus grading/terms/credit fields. Both are SAP User-Defined Fields (`U_*`). **Never name-match** — always read the `U_*` column. Two traps dominate:

1. The Realise-Calculator item feed **mislabels** its `variety` column: its values are SAP **`U_Sub_Group`** (OLIVE, MUSTARD, CANOLA…), *not* SAP `U_Variety`. The Sales-Dashboard feed, by contrast, names the same three fields correctly (`u_type`, `u_sub_group`, `u_variety`). Same word, two different SAP columns depending on which feed you read.
2. **MAIN GROUP** is a *customer/party* attribute (`OCRD.U_Main_Group`), **not** an item attribute — `U_Main_Group` does **not exist on `OITM`** (SAP rejects it: *"Property 'U_Main_Group' of 'Item' is invalid"*). A sale's "channel" is inherited from the **billed customer**, never from the product.

---

### Term table

| Term | Plain meaning | SAP lineage (entity.column, filters) | How the sales lens differs from accounts / raw SAP | Gotchas & corrections | Company scope |
|---|---|---|---|---|---|
| **TYPE** (P / C) | Margin tier of an oil SKU: **PREMIUM** (branded, high realise) vs **COMMODITY** (bulk staples). | `OITM.U_TYPE`. Values live: `PREMIUM`, `COMMODITY`, **`OTHERS`**. CP calculator-items abbreviates to **`P`** / **`C`** chips; Sales-Dashboard feed spells it out in `u_type`. | Accounts never segments on this; it is a *pure sales/margin* axis. Drives the COMMODITY-vs-PREMIUM order-in-hand split. | **Third value `OTHERS` exists** (seeds, honey, spices, tea, coffee, gift packs, dry-fruit, vitamins, drinks, rice, atta) — the "PREMIUM/COMMODITY" shorthand is incomplete. Verified FG0000030 MUSTARD KACHI GHANI = `COMMODITY` = chip `C`; FG0000045/185/441 = `PREMIUM` = `P`. | Oil book (OITM). Mart/Bev keep their own item UDFs — do not assume the same fill. |
| **SUB-GROUP** (a.k.a. calculator "Variety") | The oil / product **family**: MUSTARD, OLIVE, CANOLA, SOYABEAN, SUNFLOWER, GROUNDNUT, RICE BRAN, BLENDED, GHEE, COCONUT, SESAME, COTTON SEED, PALMOLEIN (+ non-oil: SEEDS, HONEY, SPICES, GIFT PACK, DRY FRUITS/NUTS, TEA, COFFEE, VITAMINS…). | `OITM.U_Sub_Group`. Sales-Dashboard `sales-data` → `u_sub_group`; **Realise-Calculator `calculator-items` → `variety`** (mislabeled — see note). | Accounts rarely uses it; it is the sales team's primary product roll-up under TYPE. | **THE label trap:** `calculator-items.variety` = `U_Sub_Group`, NOT `U_Variety`. Verified: FG0000185 → calc `variety`=`BLENDED` = SAP `U_Sub_Group`=`BLENDED` (SAP `U_Variety` is `BB ROYAL`). Also: at least one inverted row exists where `U_Sub_Group`=`EXTRA VIRGIN` and `U_Variety`=`OLIVE` (a swap) — don't assume the pair is always the right way round. | Oil book. |
| **VARIETY** (true grade) | The **grade / pressing / brand within a family**: POMACE, EXTRA VIRGIN, EXTRA LIGHT, CLASSIC, COLD PRESS, REFINED, KACCHI/PAKKI GHANI, YELLOW MUSTARD, DESI GHEE (A2), BB ROYAL, SO OLIVE… | `OITM.U_Variety`. Correctly surfaced **only** in the Sales-Dashboard feeds as `u_variety`. | This is the level accounts/turnover never touch; it is where realise differences live (POMACE vs EXTRA VIRGIN olive are very different ₹/L). | **Do NOT read `U_Variety` from `calculator-items`** — that feed's `variety` is actually the sub-group. Use `sales data`.`channel_month_rows[].u_variety`. Matches the standing rule *"U_Variety = grade within a variety (POMACE/EXTRA LIGHT/EXTRA VIRGIN)"*. | Oil book. |
| **SKU** | Pack size of one sellable unit: `1 LTR`, `5 LTR`, `500 MLS`, `200 MLS`, `15 KGS`, `869 GMS`… | `OITM.U_SKU`. CP calculator-items `sku` and sales feeds `sku` both = `U_SKU` verbatim. | Sales reads it as a clean master field; accounts/turnover never needs it. | It is a stored UDF, **not** parsed from the item name — read `U_SKU`, don't regex the description. Verified FG0000185 `U_SKU`="1 LTR", FG0000441 `U_SKU`="200 MLS" — both match CP `sku`. `—` appears for pack-less items. | Oil book. |
| **PCS/BOX** | Pieces (bottles) per carton — carton config. | `OITM.SalesFactor2` (Service-Layer name; HANA `SalFactor2`). CP calc `pcs_per_box`. `litres_per_pack × pcs_per_box = box_litres`. | Sales uses it to back-solve ₹/L in the Realise Calculator (`Box Value = Ex-GST × Pcs/Box`). | This is the "20 PCS" printed in item names → **carton config only**. Per **[C-0001]** invoice `INV1.Quantity` is in **pieces (single bottles)**, so multiplying by pcs/box inflates volume ~20×. Verified FG0000185 `SalesFactor2`=20, FG0000441=70 = CP `pcs_per_box`. | Oil book. |
| **LITRES / volume** | Saleable litres — the sales team's native quantity for oils. | `litres_per_pack` (per piece) and `box_litres` (per carton) in calculator-items; derived on sale lines as pieces × pack-litres. `OITM.U_IsLitre='Y'`, `U_Unit='OIL'` flag oil items. | Accounts thinks in ₹ (DocTotal−VatSum); sales thinks in **litres** (and beverages in **boxes/units**). | Litres = parsed pack-size × pieces (**[C-0001]**). Beverages are counted in **boxes / units**, never litres or ₹/L (see BEVERAGES). Talk in MT for bulk (litres × 0.91 for oils). | Oil (litres) vs Beverages (boxes). |
| **MAIN GROUP** | The party's **business bucket** — and, for GT/MT/ROI/ECOM/HORECA, the **sales channel**. 24 live values. | **`OCRD.U_Main_Group`** (customer/party UDF). Surfaced as customer-master `main_group`, and on every sale line as `u_main_group`/`main_group` (inherited from the billed customer). **Not on OITM.** | Accounts has no channel concept at all; this *is* the sales org chart. | Live distinct (Oil, n=1177): `GT` 691, `CALL CENTER` 132, `E-COMMERCE` 97, `ROI` 55, `STAFF` 38, `HORECA` 37, `MT` 23, `CORPORATE` 18, `SANGAT`/`REFERENCE` 14, `TRANSPORT` 11, `WEBSITE` 8, `PURCHASE OIL`/`CSD`/`BRANCH` 7, `EXPORT` 6, `CASH SALE`/`BULK OIL` 3, + singletons (`STAFF CUSTOMER`, `JOB WORK`, `FIXED ASSETS`, `EVENTS & EXHIBITIONS`, `CONSUMABLES`, `COMPANY UNIT`). **Mixes real channels with bookkeeping buckets** — filter to true channels before reporting "channel sales". Per **[C-0015]** `U_Main_Group` differs across company books — never segment across Oil/Mart/Bev on it. | `OCRD` per company; **[C-0015]** values differ across books. |
| **CHANNEL** | Go-to-market lane. The app's "four channels" = **GT · MT · ROI · ECOM** (HORECA/CSD/EXPORT are also channel-like main-groups). | Derived from the customer's `U_Main_Group`. Dashboard endpoints take `channel=GT\|MT\|ECOM`. | Sales-only construct; a sale's channel = its **billed customer's** main-group, not the item's. | **GT** = General Trade (distributor→wholesaler→retailer); **MT** = Modern Trade (organised retail); **ROI** = **Rest of India** (geography rollup — *not* return-on-investment); **ECOM** = E-Commerce / q-commerce; **HORECA** = hotels/restaurants/caterers. The vault calls it "4 channels" but `main_group` is a 24-value superset. | All companies (customer-side). |
| **SEGMENT** | Top business split: **OILS** vs **BEVERAGES**. | Not one column — OILS = the `FG*` oil item universe (`U_IsLitre='Y'`); BEVERAGES = a separate data track (beverage items, own endpoints). | Sales runs two parallel tracks (separate targets, docs, aging); accounts just sees invoices. | Oils in litres/₹-per-L; beverages in **boxes/units** with **no ₹/L realise**. Beverages toggle drives a different feed (`beverages-data`). | OILS (Oil book) / BEVERAGES (Bev book + JIVO water/juice items). |
| **REALISE** ("RELISE" in UI) | Net **₹ per litre** actually earned after schemes/discounts/CNs. `Net Sales Value ÷ Volume(L)`. | Computed, not stored: `linetotal ÷ litres` on `sales-data`; calc waterfall backs retailer price down through SS%/Dist%/GST to ex-factory net ÷ (box + scheme litres). The whole app/API (`/realise/…`) is named for it. | **This is the sales team's "sales" metric**, and it differs from the accounts definition. Accounts **turnover** = `Invoices (DocTotal−VatSum) − CreditNotes`, by `DocDate`, `Cancelled='tNO'` (a ₹ total). Sales **realise** = a **₹/L efficiency ratio** (net value ÷ litres), scheme-diluted, ex-factory. Do not equate them. | UI typo "RELISE" everywhere = REALISE. Scheme litres **dilute** realise. Money-gated for `preshit` (the ₹ feeds return empty for this login). | Oil (₹/L). Beverages tracked in boxes, no realise. |
| **CUSTOMER CODE** | The join key for every sales/accounts report. | `OCRD.CardCode`, e.g. `CUSTA000936`. customer-master `code`. | Same key both sides — the one clean bridge. | Sticky first column of the master; every Realise/Accounts report joins on it. | Per company. |
| **GSTIN** | 15-char GST registration of the party. | **As-billed GSTIN — `INV12.BpGSTN`** per **[C-0014]**, *not* `OCRD.LicTradNum`/`FederalTaxID`. | Sales master shows a GSTIN even where the OCRD tax field is blank. | **Verified [C-0014]:** for CUSTA000936 CP shows `03ACHPS3233Q1ZA` while `OCRD.FederalTaxID` is **null** and `BPFiscalTaxIDCollection.TaxId0` holds only the **PAN** (`ACHPS3233Q`). So CP's `gstin` is neither of the OCRD fields — it is the billed GSTIN. GSTIN embeds the PAN → the separate `pan` column is ~0% filled. ~75% of rows carry a GSTIN. | Per company (a party's CardCode/GSTIN differ across books). |
| **SALES PERSON** | Mapped salesperson / beat owner. | `OCRD.SalesPersonCode` → `OSLP.SlpName`. customer-master `sales_person`. | Sales org mapping; accounts ignores it. | Verified CUSTA000936 `SalesPersonCode`=66 → CP `sales_person`="G PURE". ~26% filled (68–69 distinct names live). Also appears on sale lines as a routing tag (e.g. "DELHI GT"). | Per company. |
| **PAYMENT / CREDIT TERMS** | How long a party may take to pay. | `OCRD` payment-terms group (`PayTermsGrpCode`) → `OCTG.PymntGroup` name. customer-master `payment_terms`. | Same source accounts uses, but sales reads it as a *credit-risk grading* input alongside credit limit. | 14 label values live; **dominated by `ADVANCE/CASH/0 DAYS`** (1047/1177), then `COD` 78, `NET-30` 22, `NET-07` 10, other `NET-nn`/`CAD`/`LC 60`/`20% ADVANCE`/`45 % ADV` in ones-twos. `PayTermsGrpCode=-1` resolves to `ADVANCE/CASH/0 DAYS`. | Per company. |
| **CREDIT LIMIT** | Sanctioned ₹ credit ceiling. | `OCRD.CreditLimit` (Service-Layer `CreditLimit`, **not** `CreditLine`). customer-master `credit_limit`. `0` = no limit set. | Feeds the sales "required credit limit" logic (outstanding + 2%). | Verified CUSTA000936 `CreditLimit`=1,334,000 = CP `credit_limit` exactly. | Per company. |
| **BALANCE** | Current outstanding ledger balance (₹). | `OCRD.CurrentAccountBalance` (**not** `Balance`). customer-master `balance`. | Sales reads it as receivables exposure per party. | **Sign convention carries straight through**: positive = **DEBIT** (party owes JIVO), negative = credit/advance. Verified CUSTA000936 `CurrentAccountBalance`=**−938** = CP `balance` **−938**. Per **[C-0019]** SAP open-status is unreliable at JIVO, and party ledgers proper come from `JDT1` (**[C-0023]**), not the header balance. | Per company. |
| **STATUS** | Account state. | Derived from `OCRD` frozen flags → `Active` / `Frozen` (credit-locked) / `Inactive` (filter-only, empty in feed). | Sales reads `Frozen` = credit-locked (a sales action), see credit-lock/unlock. | Live: 1165 `Active`, 12 `Frozen`. `Inactive` supported in UI but not present. | Per company. |
| **RATE LIST** | Saved library of Realise-Calculator pricing scenarios, tagged by state. | App store (Django), not SAP. Read via `masterdata rate-list`. | Pure sales-ops planning artefact; no accounts equivalent. | **Store is empty live** (`rows:[], states:[]`) — nothing saved yet. Scope tags: `GRID`/`ORDER`/`A`/`B`/`BOTH`. | App-level, company-agnostic. |

---

### Reconciliations — LIVE Control Panel vs LIVE SAP (2026-08-25)

All SAP figures from `JIVO_OIL_HANADB` Service Layer; `as_of` server stamp `2026-08-25T14:0x:xxZ`.

1. **Customer-master row count — RECONCILES exactly.** CP `masterdata customer-master` → `count = 1177`. SAP `BusinessPartners` `CardType eq 'cCustomer'` `$count = 1177`. Identical. (The vault's earlier "1,167" was a July snapshot; the master has grown by 10.)

2. **Customer row CUSTA000936 (AMAN TRADING COMPANY) — RECONCILES (4/4 fields).**
   - `main_group` **GT** = `OCRD.U_Main_Group` **GT** ✓
   - `credit_limit` **1,334,000** = `OCRD.CreditLimit` **1,334,000** ✓
   - `balance` **−938** = `OCRD.CurrentAccountBalance` **−938** ✓ (same sign)
   - `sales_person` **G PURE** = `OCRD.SalesPersonCode` **66** → OSLP name ✓

3. **GSTIN source — CONFIRMS [C-0014] (does NOT come from OCRD).** CP `gstin`=`03ACHPS3233Q1ZA`, but SAP `OCRD.FederalTaxID`=**null** and `BPFiscalTaxIDCollection.TaxId0`=**`ACHPS3233Q`** (PAN only, no state code, no full 15-char GSTIN). So the CP GSTIN is the **billed** GSTIN (`INV12.BpGSTN`), not an OCRD field. Reconciles *as a concept*, and pins the lineage.

4. **FG item master count — RECONCILES (close, ~99.5%).** CP `masterdata calculator-items` → **378** items. SAP `Items` `startswith(ItemCode,'FG') and SalesItem eq 'tYES' and Valid eq 'tYES'` = **376** (with `Frozen eq 'tNO'` too = 361; without the Valid filter = 446). CP's picker ≈ "active, sellable FG items" (376) plus ~2 extras (likely a couple of non-`FG`-coded sellable SKUs). Grain matches; the 2-item gap is immaterial.

5. **Item field mappings — RECONCILE (verified per-item).**
   - `pcs_per_box` = `OITM.SalesFactor2`: FG0000185 → 20 = 20 ✓; FG0000441 → 70 = 70 ✓
   - `sku` = `OITM.U_SKU`: FG0000185 → "1 LTR" = "1 LTR" ✓; FG0000441 → "200 MLS" = "200 MLS" ✓
   - `type` (P/C) = `OITM.U_TYPE`: FG0000030 (SAP `COMMODITY`) → chip `C` ✓; FG0000045/185/441 (SAP `PREMIUM`) → `P` ✓
   - `variety` (calc feed) = `OITM.U_Sub_Group` **NOT** `U_Variety`: FG0000185 calc `variety`=`BLENDED` = SAP `U_Sub_Group`=`BLENDED`; SAP `U_Variety`=`BB ROYAL` (**mislabel confirmed**).

6. **Taxonomy vocabulary — pulled live from SAP (376 FG rows).** `U_TYPE` distinct = **PREMIUM, COMMODITY, OTHERS** (three, not two). `U_Sub_Group` = the oil families above + non-oil buckets. `U_Variety` = grade level (POMACE / EXTRA VIRGIN / EXTRA LIGHT / CLASSIC / COLD PRESS / REFINED / KACCHI GHANI / PAKKI GHANI / YELLOW MUSTARD / BB ROYAL / SO OLIVE / DESI GHEE / DESI GHEE A2 / …). One inverted row observed: `U_Sub_Group`=`EXTRA VIRGIN`, `U_Variety`=`OLIVE`.

**Not reconciled (money-gated for this login):** the Sales-Dashboard ₹/realise feeds (`sales data`) and beverages **customer grading** (`sales beverages` → `customer_rows`) returned empty for `preshit` — the ₹ panels are blank for this admin login, and the beverages window sampled had 0 boxes. Field *shapes* were read from the recon vault + the one non-money `channel_month_rows` array that did return (which confirmed `u_type`/`u_sub_group`/`u_variety`/`u_main_group` naming). Realise/turnover **numbers** could not be cross-footed from here.

---

### Open questions

1. **Full `U_TYPE=OTHERS` treatment.** OTHERS (seeds/honey/spices/gift packs/tea/coffee/etc.) is a real third tier on OITM but the sales concept notes only say "PREMIUM/COMMODITY". Does the Realise Dashboard fold OTHERS into COMMODITY, PREMIUM, or drop it? Needs a money-enabled login to see.
2. **Inverted taxonomy rows.** How many items carry a swapped `U_Sub_Group`/`U_Variety` (e.g. sub-group `EXTRA VIRGIN`)? A full OITM sweep + dedupe would quantify; matters for any grouping on sub-group.
3. **Exact GSTIN resolver.** Confirmed CP `gstin` is *not* OCRD; strongly implied `INV12.BpGSTN` (latest billed) per [C-0014], but the precise pick (latest invoice? any invoice? a materialised view?) was not traced in the CP code from here.
4. **The 2-item gap** between CP calculator-items (378) and SAP FG-sellable-valid (376): are there non-`FG`-prefixed sellable SKUs in the picker, or a slightly wider validity window?
5. **`main_group` on Mart/Bev.** `U_Main_Group` values differ across books ([C-0015]); the live distinct set above is Oil-only. The Mart/Bev channel vocabularies were not sampled (needs the `manager` login for those books).
6. **Beverages customer grading rubric.** `customer_rows` carries a per-customer/brand box grading, but the grade bands (what makes an A vs B customer) weren't observable — 0-box window + money gating.

*Sources: `control-panel/cli/jivo/jivo {api,masterdata customer-master,masterdata calculator-items,sales data,sales beverages}` (live, host 138.252.101.118:9080, login preshit); SAP B1 Service Layer `JIVO_OIL_HANADB` via `sapb1_query`/`sapb1_fields` (live, as_of 2026-08-25); recon vault `control-panel/vault/{concepts,pages,api}`; corrections C-0001, C-0014, C-0015, C-0019, C-0023.*

---
## Beverages & COGS (gated surfaces)

*The sales team's BEVERAGES data track (juices / wellness drinks / packaged water — reported in **boxes**, not litres or ₹/L) and the OTP-gated **COGS** surface. Everything below was verified against the LIVE Control Panel CLI (`control-panel/cli/jivo/jivo`, host `138.252.101.118:9080`, login `preshit`) and LIVE SAP B1 Service Layer (`JIVO_BEVERAGES_HANADB`, host `138.252.101.222:50000`, user `manager`, `as_of` server stamp `2026-08-25T14:1x:xxZ`) on **2026-08-25**. Read-only throughout.*

### The three things to internalise first

1. **Beverages is a separate company book, not a segment toggle over Oil.** The BEVERAGES dataset reads **`JIVO_BEVERAGES_HANADB`** — a distinct SAP company DB with its own invoices, credit notes, orders, BP ledger and item master. Its invoice `DocNum`s live in the `62608xxxx` range (verified `626088195` = OM SAI NATH PAPER POINT exists in that DB). Oil figures and Beverages figures are **never** comparable (per the standing SAP rule and **[C-0015]**).

2. **Beverages is counted in BOXES (cartons) and PIECES (bottles) — there is no ₹/L "realise" here.** Oils have realise (₹/litre); beverages do not. The native quantities are `quantity` (pieces/bottles, = `INV1.Quantity`, `MeasureUnit`='PCS') and `boxes` (cartons = `quantity ÷ SalesFactor2`). Per **[C-0001]** the "24 PCS" in an item name is the **carton config** (`OITM.SalesFactor2`), so `boxes = pieces ÷ pcs-per-box`; multiplying instead inflates ~24×.

3. **The beverages feed SWAPS `variety` and `sub_group` (same mislabel as the Realise Calculator).** CP `variety` = SAP **`U_Sub_Group`** (the coarse bucket: `WATER`/`DRINKS`/`GIFT PACK`), and CP `sub_group` = SAP **`U_Variety`** (the flavour: `MINERAL WATER`/`JEERA`/`MOJITO`/`SODA`/`COLA`…). Verified on FG0000324: SAP `U_Sub_Group`="WATER", `U_Variety`="MINERAL WATER"; CP feed shows `variety`="WATER", `sub_group`="MINERAL WATER". **Never name-match; and never trust the feed's field *label*** — read the SAP `U_*` column.

Also note the money-gating is **asymmetric**: OILS realise ₹ feeds return empty for `preshit`, but the **BEVERAGES `sales_rev` IS visible** to this login (it reconciled to SAP net sales to the rupee — see R4). **COGS** is the one surface fully denied to `preshit` (`can_cogs:false`, HTTP 403).

---

### Term table

| Term | Plain meaning | SAP lineage (entity.column, filters) | How the sales lens differs from accounts / raw SAP | Gotchas & corrections | Company scope |
|---|---|---|---|---|---|
| **BEVERAGES** (segment / dataset) | The juices / wellness-drinks / packaged-water business, on its own data track (own sales, docs, OIH, aging). Activated by the OILS⇄BEVERAGES toggle. | Whole **`JIVO_BEVERAGES_HANADB`** company DB. `sales beverages` → `POST /realise/api/beverages-data/`; `sales beverages-docs` → `GET /realise/api/beverages-docs/`. | Accounts just sees a company's invoices; sales runs beverages as a parallel track in **boxes**, with day-over-day and customer grading built in. | Company book, not a column flag. Its item master is a **superset** that also holds oil SKUs (336 FG items: oils + drinks) — filter by the beverage buckets, don't assume every FG here is a drink. | Bev book only. |
| **QUANTITY** (beverages) | Bottles sold — pieces. | `INV1.Quantity` (Service-Layer `DocumentLines.Quantity`), `MeasureUnit`='PCS'. CP feeds `quantity`. | Sales' native unit alongside boxes; accounts thinks in ₹. | **[C-0001]:** pieces, NOT cartons. Verified DocEntry 17175 line `Quantity`=6000, `MeasureUnit`='PCS'. | Bev book. |
| **BOXES** | Cartons sold — the headline beverages measure. | Derived: `quantity ÷ SalesFactor2` (pcs-per-box). `OITM.SalesFactor2` is the carton config. CP feeds `boxes`; `sales cn --company beverages` reports `measure`="Boxes". | This is *the* beverages KPI (targets, day-compare, customer grading all in boxes). No accounts equivalent. | Verified FG0000324 `SalesFactor2`=24 → 6000 pcs ÷ 24 = **250 boxes** = CP `boxes` 250. The "(24 PCS)" in the item name = this factor. | Bev book. |
| **VARIETY** (beverages feed) | Coarse product bucket: `WATER`, `DRINKS`, `GIFT PACK`. | **= SAP `OITM.U_Sub_Group`** (NOT `U_Variety`). Feed key `variety`; CN feed key `product`. | Sales' top beverage roll-up. | **SWAP TRAP** — feed *label* is inverted vs SAP column (see #3 above). Live `U_Sub_Group` beverage buckets: `DRINKS` 84, `WATER` 17, `GIFT PACK` 4 items (rest are oils). CN `product` adds `SERVICE / CLAIM`. | Bev book. |
| **SUB_GROUP** (beverages feed) | The flavour / SKU family within a bucket. | **= SAP `OITM.U_Variety`** (NOT `U_Sub_Group`). Feed key `sub_group`. | The drill level under `variety`. | Same SWAP trap. Live `U_Variety` flavours: `MINERAL WATER` 16, `SODA` 12, `JEERA` 11, `MOJITO` 9, `MANGO`/`GINGER ALE` 6, `IMMUNITY BOOSTER` 5, `COLA` 4, `TONIC WATER`/`ENERGY DRINK` 2, `SHIKANJI`/`HEALTHY COLA` 1… (plus oil grades, since the master is shared). | Bev book. |
| **SALES_REV** (beverages) | Net sales value (₹) of beverage lines. | **`Invoices` net of GST = `DocTotal − VatSum`**, by `DocDate`, `Cancelled eq 'tNO'`. Surfaced by `sales cn --company beverages` as `sales_rev` (line-level, grouped customer×item). | **Same basis as accounts turnover** (net of GST) — unlike oils, where the sales metric is realise (₹/L). Beverages has **no realise**; it uses boxes + net ₹. | **NOT money-gated for `preshit`** (contrast: oils realise ₹ is empty). Reconciled to SAP to ₹30 on ₹73.7 L (R4). Companion cols `cng_qty/cng_rev` (credit-note gross) and `cns_rev` do **not** tie cleanly to SAP CNs — see open questions. | Bev book. |
| **today_boxes / yesterday_boxes** | Day-over-day carton comparison on the beverages dashboard. | Same invoice lines, bucketed by the last two dates in the selected window; `today_items`/`yesterday_items` give the per-SKU split. | A sales-ops "did we ship more today than yesterday" glance; accounts has nothing like it. | Internally consistent: `today_boxes + yesterday_boxes = month_rows.boxes = Σ(beverages-docs.boxes)` (R2). On a partial day `today_boxes` is mid-accrual. | Bev book. |
| **BEVERAGES OIH** | Open (uninvoiced) beverage sales orders, in boxes. | Open `Orders` in the Bev book, rolled to `oih_rows` `{variety, sub_group, item, customer, brand, ym, quantity, boxes}`; also `oih` per line in `data`. | Sales' forward order book in cartons; a sales/pipeline construct, not an accounts number. | Same SWAP labels apply. `INDERPREET SINGH IMPREST JWPL1329` and similar IMPREST/JWPL names appear as "customers" — internal/related accounts, not trade. | Bev book. |
| **BRAND** | Product brand tag on every beverage line. | Beverage item brand attribute; feed key `brand`. | Sales grouping; accounts ignores it. | Only value observed live = **`JIVO`**. Whether other brands ever appear is unverified. | Bev book. |
| **A/R AGING — balance_due** (beverages) | What a beverage customer owes, aged into buckets. | **`OCRD.CurrentAccountBalance`** (the ledger balance), aged into `b0_30/b31_60/b61_90/b91_120/b121` by open-invoice dates. `accounts aging-beverages` → `GET /realise/api/customer-aging-beverages/`. | Sales reads it as receivables exposure per salesperson band. Note it uses the **ledger balance, not the open-invoice sum** — which is the *correct* choice: header "open" invoices are unreliable at JIVO (**[C-0019]**; ledger proper is JDT1, **[C-0023]**). | **Per-customer ties to `CurrentAccountBalance` exactly** (R5). BUT the CP total **excludes curated related-party accounts** — BLESSING ADVERTISING (₹3.17 Cr) and JIVO WELLNESS DL/HR/PB (₹78 L) are dropped, so CP's ₹58.6 L ≠ the all-positive-ledger ₹4.74 Cr. Positive = party owes JIVO. | Bev book. |
| **FORMAT** (aging group) | The band the aging pivots on. | Here = **salesperson / ASM name** (`OSLP` via `OCRD.SalesPersonCode`), e.g. "NAVNEET SINGH", "GAGANDEEP SINGH FACTORY". A synthetic **"WRITTEN OFF"** band also exists. | Same "Format" slot that Mart aging uses for channel-format; beverages reuses it for the salesperson. | 46 format groups / 358 customers live. "WRITTEN OFF" customers are **bucketed, not dropped** — don't read them as live receivable. | Bev book. |
| **COGS** | Cost of goods sold — landed cost basis for gross margin (net sales − COGS). | Line-level in SAP: `INV1.GrossBuyPrice` × `Quantity` = line cost; `GrossProfit`, `GrossProfitTotalBasePrice`, `COGSAccountCode`, `COGSCostingCode` sit on every invoice line. CP surface = **`GET /api/cogs/`** (top-level, not under `/realise/`), returns `cogs.total_cogs_display`, `cogs_per_liter_display`, `total_liter_display`. | The P&L view accounts/finance guard; sales normally never sees it. | **OTP-GATED + permission-gated. Fully blank for `preshit`** (`can_cogs:false` → HTTP 403 `{"error":"Permission denied"}`). **No CLI command exists** (not in the 7 interfaces). Document only — never attempt to bypass the OTP. | Reads any company book (per-company cost). |
| **ROI** (channel) | **Rest of India** — the geography channel bucket for business outside the core metros/focus regions. **Not** return-on-investment. | Customer attribute `OCRD.U_Main_Group='ROI'` (a party/channel value, inherited onto sale lines). One of the four sales channels (GT · MT · ROI · ECOM). | Pure sales org/geography construct; accounts has no channel concept. | **Disambiguation trap:** in this codebase `ROI` = Rest of India everywhere. In the Oil book `U_Main_Group='ROI'` has 55 customers; per **[C-0015]** main-group values differ across company books, so don't carry the Oil count to Bev. | Customer-side, per company. |

---

### Reconciliations — LIVE Control Panel vs LIVE SAP (2026-08-25)

All SAP figures from `JIVO_BEVERAGES_HANADB` Service Layer; server `as_of` `2026-08-25T14:1x:xxZ`.

1. **Beverages document count — RECONCILES exactly.** Window 2026-08-24…-25: CP `sales beverages-docs` returned **24** documents; SAP `Invoices` `DocDate ge '2026-08-24' and DocDate lt '2026-08-26' and Cancelled eq 'tNO'` `$count` = **24**. Identical.

2. **Day-over-day boxes — RECONCILES (internal + SAP anchor).** CP `beverages-data` (same 2-day window): `today_boxes` **3127** + `yesterday_boxes` **6000** = **9127** = `month_rows.boxes` **9127** = Σ(`beverages-docs.boxes`) **9127** (and Σ`quantity` **189193** pcs). SAP anchor: CP doc `626088195` = SAP DocNum 626088195, CardName **OM SAI NATH PAPER POINT**, DocDate 2026-08-24, `DocTotal` **25000**. ✓

3. **Pieces ↔ boxes (C-0001) — RECONCILES.** SAP `Invoices(DocEntry=17175)` line: `ItemCode`=FG0000324, `Quantity`=**6000**, `MeasureUnit`=**'PCS'**, item `SalesFactor2`=**24** → 6000 ÷ 24 = **250 boxes** = CP `boxes` **250** for that doc. Confirms `boxes = pieces ÷ pcs-per-box`, not a stored box count.

4. **Net sales revenue — RECONCILES to the rupee.** Window 2026-08-01…-25: CP `sales cn --company beverages` Σ`sales_rev` = **₹7,373,413.80** (90,266 boxes, 268 rows). SAP `Invoices` net of GST (`Σ DocTotal − Σ VatSum`, `Cancelled eq 'tNO'`, 269 invoices) = **₹7,373,383.12**. Δ = **₹30.68 (0.0004%)** — rounding. **So beverages `sales_rev` = net-of-GST invoice value (the accounts turnover basis), and it IS visible to `preshit`.**

5. **A/R aging — RECONCILES per customer to the ledger; aggregate differs by design.** CP `accounts aging-beverages`: `total_outstanding` **₹5,856,345.51**, 358 customers, top = GAGANDEEP SINGH ₹736,611. Per-customer `balance_due` = SAP `OCRD.CurrentAccountBalance` **exactly**: ORGC000001 GAGANDEEP **736,611** = 736,610.9999 ✓; CUSTA000606 JIVO MART **614,879** = 614,878.9998 ✓; CUSTA000680 B S A ENGINEERING **426,205** = 426,204.9989 ✓. It is the **ledger** balance, not the open-invoice sum (GAGANDEEP's 164 "open" invoices sum ₹46.9 L of open amount, but the ledger — and CP — say ₹7.37 L; the rest are **[C-0019]** stale-opens). The CP **total** (₹58.6 L) does NOT equal the SAP all-positive-ledger sum (**₹4.74 Cr**, 209 customers) because CP **excludes** four curated related-party accounts — **CUSTA000175 BLESSING ADVERTISING ₹3.17 Cr**, and **JIVO WELLNESS PVT LTD DL/HR/PB (CUSTA000001/2/3) ₹38.5 L + ₹20.2 L + ₹19.5 L** — confirmed absent from the aging customer list (while JIVO MART and AKAL ROZGAR are kept).

6. **COGS — NOT reconcilable from this login (money-gated).** `GET /api/cogs/` is `can_cogs:false` for `preshit` → HTTP 403; there is no CLI command. **SAP source identified live** for whoever holds the permission: invoice-line `GrossBuyPrice` (₹2.8364 on DocEntry 17175) × `Quantity`, with `GrossProfit`/`GrossProfitTotalBasePrice`/`COGSAccountCode`/`COGSCostingCode` on each `INV1` line (line 17175: cost basis ₹17,018.40, GrossProfit ₹6,791.40 on LineTotal ₹23,809.80). Documented only — not verified against the `/api/cogs/` payload.

---

### Open questions

- **CN credit-note columns don't tie.** CP `sales cn` beverages `cng_rev` **₹94,684.25** / `cng_qty` 2039 boxes / `cns_rev` ₹920 vs SAP `CreditNotes` net-of-GST **₹100,603.79** (9 CNs, same window). Sales_rev reconciles to the rupee but the credit-note side is off ~₹6k — date basis or scope (service CNs? posting date?) of `cng_*`/`cns_*` is unconfirmed.
- **The aging exclusion rule is not pinned.** JIVO MART (intercompany) is *kept* but JIVO WELLNESS (parent) and BLESSING ADVERTISING are *dropped* — is there an explicit CardCode exclusion list, a UDF flag, or a main-group filter behind it? Not determined. A residual ~₹20 L gap between (all-positive-ledger minus the top-4 excluded) ≈ ₹79 L and CP's ₹58.6 L is unaccounted — likely more excluded mid-size related accounts and/or negative-balance customers included in the pivot.
- **COGS unlocked payload shape** (`total_cogs_display`, `cogs_per_liter_display`, `total_liter_display`, `opt_missing`) is from client JS only — never executed (no OTP, no `can_cogs`). COGS-per-litre for a boxes-only business implies it re-derives litres from pack size; the litre basis it uses is unverified.
- **`brand` only ever `JIVO`** in live beverages data — whether other brands exist in the Bev book is unconfirmed.
- **`beverages-docs` node filters** (`f_customer`, `f_variety`, …) are documented in the recon but the CLI exposes only `--f-brand`/`--f-ym`; node-path drill filters may not be reachable from the CLI.

---

# Appendix — Live verification scorecard (2026-08-25)
Every domain was re-checked by an independent adversarial agent against live SAP. Confidence is **high** across all eight. Below: each domain's reconciliations (✓ = CP figure tied to SAP live) and the caution FLAGs an AI must respect.

## realise  —  confidence: **high**
| ✓ | Metric | Control Panel | SAP live | Note |
|---|---|---|---|---|
| ✓ | line_total = SAP net-of-GST (WHITE TRADERS, Oil, 2026-08-24) | ₹863,621.00 (sum of 4 FG lines) | ₹863,620.95 (invoices 626080502+626080503, DocTotal−VatSum) | Δ ₹0.05 rounding. Proves CP line_total = INV1.LineTotal (net of GST). |
| ✓ | Whole-day realise-feed total (Oil, 2026-08-24) | ₹27,479,404.11 / 149,203.12 L | ₹28,779,304.79 net (34 invoices) − ₹1,299,900 non-FG AKAL = ₹27,479,404.79 | Δ ₹0.68. Establishes CP INCLUDES intercompany JIVO MART (₹19,417,600 exact) and EXCLUDES non-FG lines — the mirror image of Accounts turnover [C-0005]. |
| ✓ | Realise identity + taxonomy (PREMIUM OLIVE, 2026-08-24) | 254.64 ₹/L = 6,785,912.04 ÷ 26,649 | OITM.U_TYPE/U_Sub_Group/U_Variety/U_SKU match (FG0000030/29/11); OLIVE-by-State drill sums to grid row | realise = linetotal/litres exactly; taxonomy is OITM user fields, never name-matched. |
| ⚑ | Credit-note netting in the core realise grid | grid litres 149,203.12 = gross invoice litres (CN not removed) | same-day RND CN 626082645 (₹70,560 / 320 L full reversal) still present as gross | FLAG: sales-data/realise is GROSS of CN — contradicts vault REALISE concept. CN comparison is a separate view (sales cn). High confidence for same-day reversals. |
| ⚑ | Historical trailing-realise overlay (period sensitivity) | 6m and last_month both = 157.16/251.23/178.14 (MUSTARD/OLIVE/CANOLA) | identical to current-range realise from sales data | FLAG: overlay is period-insensitive / broken on live host 138.252.101.118 — not a genuine trailing benchmark. |
| ✓ | OIH source = SAP open sales orders | 243 open oih lines; oih summary ₹ per salesperson | Oil open orders (bost_Open) = 89; INNOVATIVE RETAIL CONCEPTS (CUSTA000496) = 15 open | Consistent with lineage's row-for-row RDR1.OpenQty proof; open_qty = open litres. |

**Caution flags (must respect):**
- PRESERVE the two reconciles:false warnings as explicit cautions in the final doc: (a) the realise grid / DONE is GROSS of credit notes (CN not netted — RND CN 626082645 ₹70,560 verified NOT subtracted from the 2026-08-24 Oil feed), and (b) the Historical/Avg realise overlay is period-insensitive/broken on the live host and must NOT be presented as a trailing benchmark. These are correctly-identified defects, not decoder errors — do not silently drop them or imply the grid is CN-netted.
- OIH staleness caveat: open sales orders that back OIH can be months old and still 'open' (all 15 INNOVATIVE RETAIL CONCEPTS open orders are dated 2026-05-28, ~3 months stale). The doc must frame OIH as committed-but-not-guaranteed future volume, not a firm pipeline, and note that stale/abandoned orders inflate it.
- Scope-honesty on DONE: the whole-day reconciliation (₹27,479,404 / 149,203 L) is proven for a SINGLE day (Oil, 2026-08-24), not a full-month MTD sweep. State the DONE-as-MTD claim as the same arithmetic extended over a date range, evidenced at the single-day grain — do not overstate it as an independently reconciled MTD figure.
- State the intercompany direction explicitly: CP realise INCLUDES intercompany JIVO MART (CUSTA000606 = ₹19,417,600 of the ₹27.48M day total, ~71%), the exact mirror of Accounts turnover which EXCLUDES the 23 group CardCodes [C-0005]. Any figure comparing CP 'sales' to Accounts 'turnover' must reconcile this ~₹19.4M/day intercompany gap or it will look like a discrepancy.

## sales-detail  —  confidence: **high**
| ✓ | Metric | Control Panel | SAP live | Note |
|---|---|---|---|---|
| ✓ | Dispatch → OINV freight user-fields (inv 626080458, Oil) | code CUSTA001102 · bilty 13181 · biltydate/dispatch 2026-08-22 · transporter 'Delhi Punjab' · vehicle PB08FG0458 · mobile 9186244192 | CardCode CUSTA001102 · U_BilltyNumber 13181 · U_BiltyDate/U_Dipatch_Date 2026-08-22 · U_TransporterName 'Delhi Punjab' · U_VehicleNoM PB08FG0458 · U_Mob_No 9186244192 | Exact 7/7 fields; confirms bilty/transporter/vehicle/driver are SAP UDFs on OINV, not a separate logistics system. |
| ✓ | Hidden-sales doc count → OINV U_ARNO='H' (July-2026, Oil) | 75 distinct docs (187 lines) | 75 header docs | Exact. Doc 626070425 also matched incl. the 'H' flag + Closed status. |
| ✓ | Hidden-sales Value → Σ INV1 taxable (July-2026, Oil, 75 docs) | ₹4,45,85,600.89 | ₹4,45,85,605.95 (Σ DocTotal−VatSum) | Diff ₹5.06 (0.00%). Proves hidden 'value' = net-of-GST taxable. |
| ✓ | Sales-vs-CN Total Sales → Σ INV1 taxable (2026-08-20, Oil, clean day) | ₹1,27,08,672.79 Σ sales_rev | ₹1,27,08,673.37 taxable | Diff ₹0.58 on a day with no tax-only invoices. sales_rev = net-of-GST line taxable, same basis as Accounts. |
| ✓ | Sales-vs-CN Total CN → SAP CreditNotes (2026-08-20..21, Oil) | ₹1,40,993.45 (cng_rev) | ₹1,40,994.33 (6 CNs, Σ DocTotal−VatSum) | Diff ₹0.88 (0.0006%), rounding only. |
| ✓ | Sales flow open order → ORDR/RDR1 (order 1726086707, Oil) | party 'JIVO MART PVT LTD' · order_open true · 48 open lines · 1,331,672 open pcs | CardCode CUSTA000606 JIVO MART · bost_Open · DocDate 2026-08-18 | Header matches; open order confirmed. open_pcs=bottles, open_qty=litres (C-0001). |
| ✓ | Tax-only invoice basis check (inv 626080444, 2026-08-21, Oil) | CN sales_rev includes the ₹16.19L base (line-level sum) | TaxOnly:tYES — header DocTotal ₹80,950 = IGST only; line INV1.LineTotal ₹16,19,000 taxable base | Explains why a 2-day naive header sum was ₹16.9L short. AI must sum INV1.LineTotal, not header DocTotal−VatSum, on days with supplementary/tax-only invoices. |

**Caution flags (must respect):**
- Sales Flow open_pcs = Σ RDR1.RemainingOpenQuantity (Service Layer open-qty field). The 'OpenQty' property returns null on the Service Layer — do not cite it. Verified Σ = 1,331,672 on order 1726086707.
- Live open orders drift: the sample order shows 47 open lines live vs the decoder's '48'. Present all open-order line counts / open pcs / open litres as point-in-time snapshots, never as fixed facts.
- Keep the tax-only rule prominent and confirmed: sum INV1.LineTotal (line taxable base), NOT header DocTotal−VatSum, for Total Sales/sales_rev/CN — proven live on inv 626080444 (header net = 0 vs line base ₹16,19,000, TaxOnly='tYES').
- Net Sales / sales_rev 'same basis as Accounts turnover' needs the intercompany caveat: Accounts turnover excludes the ~23 intercompany group CardCodes (C-0005) and nets CreditNotes. Verified open order is to intercompany party JIVO MART (CUSTA000606). Doc must state whether the CP excludes intercompany; if not, the two metrics diverge on group-billing days.
- Distinguish OINV.U_ARNO (hidden flag = 'H', drives the 75-doc July hidden set) from the separate OINV.U_AR_NO field — do not conflate them.
- Sales Flow open/closed status inherits C-0019 (SAP open-status is unreliable at JIVO — docs settled by manual JE stay 'open'). Label flow open-status as indicative, not a settlement fact.

## oih  —  confidence: **high**
| ✓ | Metric | Control Panel | SAP live | Note |
|---|---|---|---|---|
| ✓ | SO 1726086707 open line count (CP breakdown vs SAP open lines) | 47 rows | 47 open lines | Exact. Live 2026-08-25, JIVO_OIL_HANADB. The big JIVO MART intercompany transfer order. |
| ✓ | SO 1726086707 total open pieces (CP Σ_pcs vs SAP Σ RDR1.OpenQty) | 1,331,672 | 1,331,672 | Exact to the piece — confirms CP _pcs = RDR1.OpenQty and litres = pcs × parsed pack size. |
| ✓ | Individual lines FG0000128 / FG0000149 open qty | 208 pcs (1040 L) / 50,000 pcs (50,000 L) | OpenQty 208 / OpenQty 50,000 | Exact; 208×5 LTR=1040 L proves premium/commodity fields are LITRES, not ₹ as the vault claims. |
| ✓ | Portfolio open-order count (CP OIH SOs vs SAP Oil open orders) | 88 SOs | 89 open orders | Gap of 1 fully explained: SAP order 1726086800 (BALAJI, ₹1, created today) is packaging-only (line PM0000005 CARTON), and CP OIH is finished-goods-only. Zero phantom SOs in CP. |
| ✓ | COMMODITY litres: breakdown commodity-sum vs commodity-rows total | 1,295,861.99 | 1,295,861.99 (internal) | Exact internal cross-check between two OIH endpoints. |
| ✓ | oih summary per-person vs breakdown per-person litres | 6 people exact (PRABHU 1,573,484; RAMINDER 148,887.58; RAVINDER 18,893.28; PRESHIT 10,161; NAZIM 4,945.2; SACHIN 1,024) | same (breakdown litre-sum) | Confirms summary values are LITRES. Minor drift on PRINCE/TEJPAL/SUNNY/TANJEET (<5% of total), likely cache-timing/attribution between the two live calls — flagged as open. |
| ✓ | Headline total OIH volume (Oil, live) | oih rows 2,053,039 L / oih breakdown 2,052,339 L | n/a (litre conversion is CP-side; validated per-SO above) | ~700 L delta between the two endpoints = one line + live-cache timing. Split COMMODITY 1,295,862 L (63%) / PREMIUM 756,477 L (37%). PRABHU SIR 77% of total is mostly the single JIVO MART intercompany SO (1,547,924 L). |

**Caution flags (must respect):**
- LITRES, not ₹: the final doc must state plainly that oih breakdown premium/commodity, oih rows open_qty, and oih summary per-person values are all LITRES (pcs x parsed pack size), and must explicitly override the stale recon vault, which mislabels them ₹ in concepts/OIH.md, api/oih-breakdown.md ('premium/commodity are ₹/value') and api/order-in-hand.md ('₹ or litres per card context'). Proven: FG0000128 shows 1040 (=208 pcs x 5 LTR), not ₹166,400.
- FG-only is endpoint-specific: correct the reconciliation note that calls the ~700 L rows-vs-breakdown delta 'one line + live-cache timing'. It is deterministic — oih breakdown is strictly FG-only (drops packaging → 88 SOs), but oih rows and oih summary INCLUDE the BALAJI packaging carton SO 1726086800 (PM0000005, 700 L, u_type blank, credited to TARUN). Do not generalise 'OIH counts only finished-goods lines' to all three endpoints.
- Intercompany dominates the headline: flag prominently that ~75% of the 2,052,339 L OIH (1,547,924 L) is a SINGLE intercompany Oil→Mart sales order (1726086707, CardCode CUSTA000606 JIVO MART PVT LTD), which OIH does not strip (unlike Accounts turnover, C-0005). Any reading of OIH as external 'committed demand' must net this out; it also makes PRABHU SIR's 77% share almost entirely this one transfer.
- Secondary caveat to carry: oih summary and oih breakdown disagree per-person beyond cache jitter (PRINCE 36,000 vs 79,000; TEJPAL 0 vs 33,215; plus TARUN 700 packaging in summary only), so the two endpoints are not interchangeable for per-owner OIH — the decoder already flags this 'open' but the cause is at least partly the FG-only-vs-not scope difference, not timing.

## accounts  —  confidence: **high**
| ✓ | Metric | Control Panel | SAP live | Note |
|---|---|---|---|---|
| ✓ | Open-payment receipt CP → SAP ORCT (doc/party/amount) | doc_no 826246676, CUSTA000352 AT OVERSEAS, amount 656,250 (2026-08-20) | Oil IncomingPayments DocNum 826246676, TransferSum 656,250, DocType rCustomer, Cancelled tNO | Exact on doc/party/amount. Caveat: CP open_bal is CP's own figure, not ORCT.OpenBal. |
| ✓ | Mart aging top customer balance_due → SAP OCRD CurrentAccountBalance | JIVO MART PVT LTD - DL = 102,172,535.28 (50.8% of Mart book) | Mart BP CUSTA000874 CurrentAccountBalance = 102,172,535.28 | Exact to the paisa. Flags intercompany: Mart's #1 receivable is a sister JIVO entity (twin vendor card VENDA000942 = -3.87 Cr); relate to C-0005. |
| ✓ | Oil aging 'outstanding' column = SAP net ledger (4 parties) | AT OVERSEAS -2,592; MAHAVIR 2; SUBHASH -1,214.07; HARINDER -289,015.31 | CurrentAccountBalance -2,592 / 2 / -1,214.0715 / -289,015.31 | Proves 'outstanding' = net party ledger repeated per invoice row (never sum it); 'bal' is the separate gross invoice residual. |
| ✓ | Credit-page 'ledger' = SAP net ledger + 2% rule (3 parties) | SAGAR 11,377; VIRCHAND 2,327.14; KAILIAN 275; required_limit=ledger×1.02 | CurrentAccountBalance 11,377 / 2,327.1378 / 275 | Book arithmetic also ties: outstanding 709,589,860.20 = ledger 324,521,638.92 + OIH 385,068,221.30; required_limit = ×1.02; remaining = − payment_done 19,874,774. |
| ⚑ | Oil aging row count vs SAP open-invoice count | 4,843 open-balance rows (336 parties) | 13,082 invoices with bost_Open + Cancelled tNO | Expected mismatch by design: CP ages the reconciled ledger (real remaining balance), SAP's Open flag is unreliable at JIVO (C-0019 settled-by-JE/unapplied-on-account stay open; C-0023 balance from JDT1). |

**Caution flags (must respect):**
- Credit-page company totals are stale/scoped, not live whole-book: the decoder states Oil 'Total Outstanding = ₹32.45 Cr ledger + ₹38.51 Cr open-order = ₹70.96 Cr' as a live figure, but live SAP gives Σ Oil customer CurrentAccountBalance = ₹107.32 Cr and open-order DocTotal = ₹48.69 Cr. Re-stamp all three (₹32.45/₹38.51/₹70.96 Cr) as 'as-of <date>, CP-computed, not SAP-reproducible' and explicitly warn a future AI not to equate ₹32.45 Cr with Oil's net receivable.
- Intercompany must be called out on any Oil receivable/outstanding total: ~₹103 Cr of the ₹107.32 Cr Oil customer ledger is intercompany JIVO cards (WELLNESS PB/DL/HR/ISD, JIVO MART) — C-0005. Whatever filter yields the credit-page ₹32.45 Cr, the doc must state whether intercompany is in or out, because the two numbers differ ~3x.
- 'OIH' is not a real SAP B1 table — the open-order component of Total Outstanding maps to ORDR (Sales Orders). Rename 'OIH' to ORDR and note the component is likely the open/undelivered residual (live full open-order DocTotal is ₹48.69 Cr, above the claimed ₹38.51 Cr).
- Aging 'Total Outstanding' ₹82.31 Cr must be labeled a CP reconciled-ledger aggregate, not Σ(OINV.DocTotal−PaidToDate): live open invoices carry PaidToDate=0 even when settled by JE (C-0019), so the naive SAP sum will not match; do not present it as a SAP-reproducible number.
- Preserve exactly (verified paisa-accurate, high value): per-row 'outstanding' = OCRD.CurrentAccountBalance repeated per invoice (never sum); credit-page 'ledger' = CurrentAccountBalance; Open Payments = ORCT with amount = CashSum+TransferSum; SAP open-invoice count 13,082 vs 4,843 CP rows is a by-design C-0019/C-0023 mismatch.

## targets  —  confidence: **high**
| ✓ | Metric | Control Panel | SAP live | Note |
|---|---|---|---|---|
| ✓ | Product-target taxonomy keys vs SAP OITM U_TYPE\|U_Sub_Group (Oil) | 16 keys (Aug 2026) | 13 exact matches in OITM; 3 are app-derived | 13/16 match raw OITM. The 3 that don't are app-derived Slide-1 labels: EXTRA VIRGIN OLIVE = OLIVE split by U_Variety='EXTRA VIRGIN'; YELLOW MUSTARD = PREMIUM MUSTARD relabelled; SLICED OLIVE sits under OTHERS in OITM (target 0). Proven via line rows which carry PREMIUM\|OLIVE/PREMIUM\|MUSTARD but never the derived labels. Never name-match a target key to OITM.U_Sub_Group. |
| ✓ | TGT vs DONE, July 2026 OILS product total (litres) | TGT 2,005,000 L / DONE 2,189,879 L = 109.2% | DONE from OINV/INV1 net of ORIN/RIN1 (sales-data feed) | Slide-1 feed embeds target_sale/target_realise identical to the targets endpoint (e.g. COMMODITY\|MUSTARD 625,000@145, PREMIUM\|CANOLA 350,000@205) — app staples Django target onto SAP actual. GHEE actual was -1,468 L (returns > sales). |
| ⚑ | Internal footing of the 4 target layers (same month, OILS) | Jul: product 2,005,000 / channel 2,541,000 / nodes 2,541,000 / flex 1,295,000 L | n/a — targets are app-only, no SAP counterpart | HEADLINE GOTCHA: layers are hand-maintained and independent. Product≠Channel by 536,000 L in July. Nodes==Channel exactly in July but DIVERGE by 780,000 L in Aug (nodes 2,805,809 vs channel 2,025,809). Flex covers only 10 named salespeople. 'The month's target' is 2.0M / 2.5M / 1.3M depending on lens. |
| ⚑ | Channel target codes vs actual OCRD.U_Main_Group values, July 2026 | 7 target channels; ECOM 78% GT 90% MT 120% ROI 84% achieved | 12 actual main-groups in OINV/OCRD | Vocab mismatch: target code 'ECOM' vs actual value 'E-COMMERCE' (app maps them). 5 actual main-groups (CORPORATE, CASH SALE, STAFF, BRANCH, REFERENCE, PURCHASE OIL) carry real litres but have no channel target. |

**Caution flags (must respect):**
- Channel reconciliation: 'ECOM'↔'E-COMMERCE' and ROI-as-geography are correct, but '12 actual main-groups in OINV/OCRD' is wrong at the master level — Oil OCRD has 24 distinct U_Main_Group values. Either scope it to 'main-groups that billed in July' or correct to 24. The 'carry litres but no channel target' list also says '5' while naming 6, and omits many untargeted groups (CALL CENTER, SANGAT, TRANSPORT, WEBSITE, EXPORT, BULK OIL, etc.).
- SLICED OLIVE is a REAL OITM U_Sub_Group (FG0000190/FG0000284) sitting under U_TYPE=OTHERS (U_Variety=BLACK OLIVE), not an invented app label — the target key PREMIUM|SLICED OLIVE (tgt_ltrs=0) mismatches OITM only on U_TYPE (PREMIUM vs OTHERS). Keep the accurate 'sits under OTHERS in OITM (target 0)' wording and drop any implication the sub-group itself is app-derived.
- YELLOW MUSTARD is a real OITM U_Variety (7 items, under both PREMIUM and COMMODITY MUSTARD), not a pure 'PREMIUM MUSTARD relabel' — describe it as PREMIUM|MUSTARD carved by U_Variety='YELLOW MUSTARD', exactly parallel to EXTRA VIRGIN OLIVE = OLIVE carved by U_Variety='EXTRA VIRGIN'.
- Flex and segment layers are month-dependent and currently empty ({} for Aug 2026) — the 'flex = 10 salespeople / 1,295,000 L' figure is a July snapshot; don't state it as a standing property. This month flex/segment contribute 0 to the layer comparison.
- The exact DONE litre totals (e.g. July OILS 2,189,879 L) come from the app feed and were not independently recomputed against SAP in this pass; the OINV/INV1-net-of-ORIN/RIN1 lineage and C-0001 pieces rule ARE verified — present the mechanism as verified and the specific totals as app-sourced (medium confidence).

## inventory  —  confidence: **high**
| ✓ | Metric | Control Panel | SAP live | Note |
|---|---|---|---|---|
| ✓ | On-hand stock per SKU, Oil FG (FG0000185) | 1,043 units (BH-BT 982, GP-FG 60, DL-PS 1) | QuantityOnStock 1,043; per-warehouse InStock identical | Exact 3-way match incl per-warehouse. Also FG0000005=38,225 and FG0000194=36,722 both exact. CP stock endpoint = SAP QuantityOnStock summed across the 15 FG warehouses. |
| ✓ | Production feasibility binding component (RM0000021 LOOSE OIL GOLD) | available 11,022 L, max_fg 11,022 | Items(RM0000021).QuantityOnStock 11,022 | Exact. Feasibility engine reads live SAP on-hand and floors FG output by the scarcest component (loose oil). |
| ✓ | Daily production work order 826202878 (FG0000030 Mustard 1L, 2026-08-22) | planned 1,780 / completed 1,780 / Closed / BH-PF | ProductionOrders(826202878): PlannedQuantity 1,780, CompletedQuantity 1,780, boposClosed, bopotStandard, BH-PF | Exact. Confirms CP daily-production = OWOR standard work orders; status/qty/warehouse all tie. |
| ✓ | Wellness-Mart recon MATCHED chain PO 826224590 - PO/SO/A-R nodes | 806,400 each | Mart OPOR 806,400; Oil ORDR 806,400; Oil OINV 806,400 (all Cancelled tNO) | 4 of 5 nodes tie to SAP DocTotal exactly across two company DBs (PO, SO, A/R verified; GRPO implied). |
| ⚑ | Wellness-Mart recon MATCHED chain - A/P node (Mart OPCH 608264208) | 806,400 | PurchaseInvoices(608264208).DocTotal 805,632 (VatSum 38,400, WTApplied 0, RoundingDiff 0) | Rs768 gap yet CP still classes the chain MATCHED. So the recon per-node 'amount' is a CP-normalized/base-linked tax-inclusive figure, NOT the posted OPCH.DocTotal. High confidence on the gap+verdict (live-verified); medium on the exact GRPO-base mechanism (not traced to source). |

**Caution flags (must respect):**
- Chain-node identity: the decoder's 'Chain nodes' glossary and recon SAP-source must state the chain is keyed ONLY by the Mart PO DocNum (e.g. 826224590); seller-side SAP docs carry different DocNums (verified: Oil SO = DocNum 1726086749, not 826224590; Oil Orders/Invoices queried by 826224590 return 0 rows). Anyone told to 'find the chain by that DocNum in the seller book' will get nothing.
- Recon node amount is CP-normalized, NOT the posted DocTotal: Mart A/P OPCH 608264208 posted 805,632 but CP shows 806,400 and still MATCHED. Make explicit that 'MATCHED' (tolerance Rs1.0 on normalized amounts) can conceal a real posted-value gap (here Rs768), so it is not evidence the postings tie.
- Name the seller entity: recon schema=oil seller = legal entity 'JIVO WELLNESS PVT LTD' (Oil DB); the intercompany pair (C-0005) is Mart vendor VENDA000001 <-> Oil-side customer CUSTA000606 'JIVO MART PVT LTD'. State the Wellness=Oil-DB mapping so the reader doesn't mistake 'Wellness' for a separate/Beverages book.

## taxonomy  —  confidence: **high**
| ✓ | Metric | Control Panel | SAP live | Note |
|---|---|---|---|---|
| ✓ | Customer-master row count (Oil) | 1177 | 1177 | CP masterdata customer-master count = SAP BusinessPartners CardType eq 'cCustomer' $count, exact match (vault's old 1167 was a July snapshot). |
| ✓ | Customer CUSTA000936 fields (main_group/credit_limit/balance/sales_person) | GT / 1334000 / -938 / G PURE | U_Main_Group GT / CreditLimit 1334000 / CurrentAccountBalance -938 / SalesPersonCode 66 | All four fields match including balance sign (negative = advance). |
| ✓ | GSTIN source (C-0014) | 03ACHPS3233Q1ZA | OCRD.FederalTaxID = null; BPFiscalTaxIDCollection.TaxId0 = ACHPS3233Q (PAN only) | Confirms C-0014: CP gstin is the billed GSTIN (INV12.BpGSTN), NOT an OCRD field. |
| ✓ | FG item master count | 378 | 376 (FG + SalesItem + Valid) | ~99.5% match; CP picker = active sellable FG items. Without Valid filter SAP=446; with +Frozen='tNO'=361. 2-item gap immaterial. |
| ✓ | pcs_per_box = OITM.SalesFactor2 | FG0000185=20, FG0000441=70 | SalesFactor2 20 / 70 | Exact per-item match; this is carton config, not a volume multiplier [C-0001]. |
| ✓ | sku = OITM.U_SKU | FG0000185='1 LTR', FG0000441='200 MLS' | U_SKU '1 LTR' / '200 MLS' | Stored UDF, verbatim match — not parsed from item name. |
| ✓ | type (P/C) = OITM.U_TYPE | FG0000030=C, FG0000045/185/441=P | U_TYPE COMMODITY / PREMIUM | P=PREMIUM, C=COMMODITY confirmed. Note SAP also has a third value OTHERS for non-oil SKUs. |
| ⚑ | calculator-items 'variety' field mapping | FG0000185 variety='BLENDED' | U_Sub_Group='BLENDED'; U_Variety='BB ROYAL' | MISLABEL: calculator-items.variety is actually SAP U_Sub_Group, NOT U_Variety. The sales-data feed names u_variety correctly. Key trap for any future AI. |
| ⚑ | Sales realise / turnover ₹ figures | empty (money-gated) | not cross-footed | sales-data ₹ feeds and beverages customer-grading returned empty for login 'preshit' — money panels blank for this login; only non-money channel_month_rows confirmed the u_type/u_sub_group/u_variety/u_main_group naming. |

## beverages-cogs  —  confidence: **high**
| ✓ | Metric | Control Panel | SAP live | Note |
|---|---|---|---|---|
| ✓ | Beverages document count (window 2026-08-24..25) | 24 docs (sales beverages-docs) | 24 invoices (Cancelled eq 'tNO') | Exact match. CP doc 626088195 = SAP DocNum 626088195 (OM SAI NATH PAPER POINT, DocTotal 25000). |
| ✓ | Day-over-day boxes (internal + SAP anchor) | today 3127 + yesterday 6000 = 9127 boxes = month_rows.boxes = sum docs boxes | anchored to SAP invoice 626088195 (2026-08-24, DocTotal 25000) | Internally consistent; box measure derived from pieces, confirmed against SAP. |
| ✓ | Pieces vs boxes (C-0001) on line DocEntry 17175 | boxes 250 | Quantity 6000 PCS / SalesFactor2 24 = 250 | Confirms boxes = pieces / pcs-per-box; item FG0000324 (500ML, 24 PCS). C-0001 holds for beverages. |
| ✓ | Net sales revenue 2026-08-01..25 | sales_rev Rs 7,373,413.80 (90,266 boxes) | net of GST (DocTotal-VatSum) Rs 7,373,383.12 (269 invoices) | Delta Rs 30.68 (0.0004%), rounding. Beverages sales_rev = accounts turnover basis (net of GST) AND is visible to preshit (money-gate does NOT apply to beverages sales rupees). |
| ✓ | A/R aging balance_due per customer | GAGANDEEP 736,611; JIVO MART 614,879; B S A 426,205 | OCRD.CurrentAccountBalance 736,610.99 / 614,878.99 / 426,204.99 | Per-customer ties to the LEDGER balance exactly (3/3), not the open-invoice sum (GAGANDEEP open-invoices=Rs 46.9L but ledger=Rs 7.37L; stale-opens per C-0019). CP uses the correct ledger figure. |
| ⚑ | A/R aging TOTAL outstanding | Rs 5,856,345.51 / 358 customers | all-positive-ledger sum Rs 47,425,603 / 209 customers | By design: CP excludes curated related-party accounts - BLESSING ADVERTISING (Rs 3.17 Cr) and JIVO WELLNESS DL/HR/PB (Rs 78 L) confirmed absent from the aging list; JIVO MART and AKAL ROZGAR kept. Aggregate not directly comparable; per-customer values are correct. |
| ⚑ | COGS | blank - HTTP 403 (can_cogs:false for preshit), no CLI command | line-level INV1.GrossBuyPrice x Quantity (e.g. 2.8364 x 6000 = Rs 17,018.40 cost on DocEntry 17175) | Not visible to this login (money-gated, OTP-gated). SAP source identified live but /api/cogs/ payload never executed - documented only, not reconciled. |
| ⚑ | Beverages credit-note columns (cng/cns) | cng_rev Rs 94,684.25 / cng_qty 2039 boxes / cns_rev Rs 920 | CreditNotes net of GST Rs 100,603.79 (9 CNs, same window) | Off ~Rs 6k while sales_rev ties to the rupee; credit-note column date basis/scope (service CNs? posting date?) unconfirmed - open question. |

**Caution flags (must respect):**
- A/R aging exclusions are by CardCode, not name: exclude BLESSING ADVERTISING CUSTA000175 (Rs 3.17 Cr) and JIVO WELLNESS DL/HR/PB, but KEEP JIVO MART CUSTA000606 (Rs 614,879) and AKAL ROZGAR CUSTA000236 — a name-match would wrongly drop the kept JIVO MART card (a zero-balance 'JIVO MART HARYANA' CUSTA000827 and a zero-balance 'BLESSING...B SAHIB' CUSTA000041 also exist).
- ROI channel note is correct (Rest-of-India, OCRD.U_Main_Group, not return-on-investment) but the '(GT/MT/ROI/ECOM)' set is NOT exhaustive: live U_Main_Group also carries BRANCH and CALL CENTRE — phrase as 'includes' not 'the four'.
- COGS must stay documented-only: SAP source (INV1.GrossBuyPrice x Quantity = 17,018.40 on DocEntry 17175) is confirmed, but CP /api/cogs is money/OTP-gated (403, can_cogs:false for preshit) — never present a CP COGS number as delivered/reconciled.
- Credit-note cng/cns columns must remain flagged approximate/not-reconciled (decoder's own ~Rs 6k gap); do not upgrade them to exact SAP figures.
- Keep the VARIETY/SUB_GROUP swap explicit and correct: feed 'variety' -> OITM.U_Sub_Group (coarse WATER/DRINKS), feed 'sub_group' -> OITM.U_Variety (fine flavour) — verified live; never name-match the flavour to U_Variety expecting the coarse bucket.

---

# Appendix — New-CLI opportunities
Full build list: `control-panel/cli/NEW-CLI-BUILD-LIST.md`. Diff of ~60 documented Control Panel endpoints vs 41 implemented `jivo` commands → **7 missing reads** we can add, **16 write/action endpoints** flagged (need owner go-ahead; the panel is a separate Django app, not covered by SAP RULE 0).

**Read commands we can build now (priority order):**

| Command | Endpoint | Effort | Value |
|---|---|---|---|
| `jivo inventory production-plan` | `/inventory/production/api/plan/` | low-medium | HIGHEST-value gap; live-verified 200 (FG0000149 qty 1, full materials[]). Multi-SKU/basket production feasibility with s |
| `jivo sales cogs (or top-level cogs)` | `/api/cogs/` | low | Margin lens: total COGS, COGS per litre, total litres — pairs with realise (Rs/L) for margin. OTP-gated + requires can_c |
| `jivo accounts export-aging-detail` | `/realise/api/export-aging-detail/` | medium (binary xlsx blob) | Collections: server-built .xlsx of every open document + its remarks for the filtered parties, aged to a date. Server-si |
| `jivo sales health (or fold into doctor)` | `/realise/api/health/` | low | Live-verified 200: {sap_connected:true, message:'SAP Connected', username:'preshit', role:'admin'}. SAP-link liveness +  |
| `jivo sales export-xlsx` | `/realise/api/export-xlsx/` | medium | Generic xlsx builder, but the CLIENT assembles the rows — from a CLI you'd feed it data you already fetched. Low CLI val |
| `jivo sales export-excel` | `/realise/api/export-excel/` | medium | Main Realise grid to xlsx from client-built layout_rows. Low CLI value (same reason as export-xlsx). Does not mutate dat |
| `jivo sales calculator-export` | `/realise/api/realise-calculator/export/` | medium | Renders realise-calculator plans to xlsx. Needs plans the client already built -> low CLI value. Does not mutate data. |
