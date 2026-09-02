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
