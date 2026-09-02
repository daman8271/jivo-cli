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
