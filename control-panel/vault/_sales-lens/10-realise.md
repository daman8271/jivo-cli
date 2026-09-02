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
