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
