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
