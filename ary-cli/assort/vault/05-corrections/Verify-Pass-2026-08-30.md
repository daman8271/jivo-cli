---
type: correction-log
stage: verify + priority (the two stages that had never run)
ran: 2026-08-30
agents: 38 (15 lane-verifiers, 21 category sizers, critic, synthesis)
result: 293 claims tested, 106 REFUTED, 91 load-bearing
---

# The verify pass — what survived, 2026-08-30

> **Read this before quoting ANY figure from this vault or from the published brief.**
> Seven of fifteen research lanes now rate LOW. The published brief at
> <https://jivo-ary.vercel.app> is materially wrong and must not be shown until rebuilt.

## The finding that replaces the brief

**ARY is not short of things to sell. It is short of the things it already sells.**

VERIFIED live 2026-08-30, retail only (Hunger Heroes wholesale, canteen menu items,
BOM and fresh produce excluded — all of which are zero-stock by design):

| | |
|---|---|
| Retail SKUs that sold in 12m | 5,953 |
| **…out of stock RIGHT NOW** | **3,049 (51.2%)** |
| Trailing sales behind an empty shelf | **Rs 1.51 Cr** |
| Of the top 100 sellers, out of stock | **27** |

Narrowed to shelf-stable regular sellers (sold on >=20 separate days, off shelf >=21 days):
**629 SKUs carrying Rs 50.13 lakh of proven repeat demand, empty for an average of
four months.** Concentration: Confectionery 290 SKUs / Rs 24.16 L / avg 138 days out;
Personal Care 170 / Rs 10.13 L / 120 days.

Natural experiment (snacks sizer, VERIFIED): on the 42 best days 8 of the top-10 snack
SKUs were on shelf and the shop sold **Rs 12.55 of snacks per bill**; on the 45 worst days
0-4 were available and it sold **Rs 9.47**. Footfall was IDENTICAL — 998 vs 997 bills/day.
Same traffic, different shelf, 25% less spend.

## Sizing verdict — 21 categories

| Verdict | Count |
|---|---|
| **AVAILABILITY_NOT_ASSORTMENT** | **18** |
| REAL_GAP | 2 (pharmacy-Rx, medical devices) |
| FALSE_GAP | 1 (frozen — tested and failed, 53:1 to the canteen) |

**The fleet's raw recommendations summed to Rs 13.3 Cr. Grounded: Rs 53 lakh revenue,
Rs 9.8 lakh gross margin — a 96% cut.** Never sum them; they are non-additive.

## 🔴 The biggest customer sells at cost — nobody had checked

VERIFIED on purchase-ledger weighted-average cost, live 12m:

| Channel | Sales | GM% |
|---|---|---|
| Walk-in retail | Rs 476.65 L | **24.42%** |
| Other named accounts | Rs 95.38 L | **26.52%** |
| **Hunger Heroes (Delhi NGO, 002CM)** | **Rs 69.81 L** | **1.04%** |

Rs 69.81 lakh of revenue earning **Rs 0.73 lakh** of gross profit. Line detail:
Loose Milk **-10.49%**, Atta 1 Kg +0.54%, Paneer_Z -0.25%, Rice 1 Kg +1.54%.

**The `wallet` lane's whole strategy — "retail is saturated, grow institutional,
Rs 4.2 Cr of headroom" — is a recommendation to grow the channel that earns 1%.**

**And the loose-milk loss is NOT a subsidy for boarding children.** VERIFIED: all
13,605 litres and all -Rs 67,094 of it go to Hunger Heroes. **Zero litres to campus
residents.** Any earlier framing of it as a charitable subsidy is wrong.

## ❌ Corrections to things this vault and the brief assert

1. **The institutional food case is dead.** EU's "Rs 2.51 Cr" = Rs 196 L of *cooked-meal
   transfer charges* (its own statement books "consumable items 22.50" separately) plus
   Rs 55 L of staff boarding *exactly offset by staff collections*. ARY's EU account is
   stoles, kurtis, curtains and trousers against Rs 3,709 of edible oil. **Both sides of
   the ratio are the wrong thing.** Also Rs 15.06 L of the "Rs 49.47 L institutional food"
   is booked on the Ary Clothing counter.
2. **🔴 FusionERP8 CANNOT hold batch/expiry — an earlier "correction" saying it can is
   WRONG and is hereby reversed.** VERIFIED: `ProductChildMaster` = 111,253 rows,
   **0 real expiry dates, 0 real mfg dates** (all 1900-01-01 sentinel). Only MatrixID 3
   "Food Products" defines Batch No/Mfg Date/Exp Date — and it covers **49 SKUs (0.25%)**.
   MatrixID 4 "General Products" covers **19,054 of 19,494 active SKUs and defines none
   of them.** Benadryl's 22 "children" are nine years of *price revisions*, one per cost
   change (cost 73.05 -> 69.17 -> ... -> 83.01, MRP 90 -> 99 -> 108), never two live at once.
   **The pharmacy blocker is REAL. Restore the vendor question and the capex line.**
3. **Gross margin is not 22%.** That was a sales-minus-purchases netting artefact
   (`ClosingStock` has 0 rows — no year has ever been closed). On purchase-ledger WAC:
   **retail 24.42%**, other named 26.52%, Hunger Heroes 1.04%.
4. **Population 4,600-4,800 / permanent 1,700-2,300 was REFUTED** (it converts a rupee
   ratio into a headcount ratio) **and then consumed by every sizing lane anyway.** The
   verify and size passes never talked to each other on their one shared input.
5. **The BIS appliance "escape hatch" belongs to the manufacturer/importer**, not to a
   retailer in Baru Sahib. And room heaters, irons, hair dryers and fans are NOT named in
   the schedule. Penalty gloss was inverted: Rs 2 L is a statutory FLOOR, cap is 10x goods value.
6. **The IMS Act infant P0 is empty.** All 9 formula SKUs: **0 stock, 7 of 9 never sold
   ever**, other 2 last sold Aug/Sep 2024. The live exposure is allopathic drugs —
   **45 active SKUs, Rs 39,672 / 613 bills**, incl. Avomine (Schedule H) and Benadryl.
   The lane's "stop selling Crocin/Disprin/Volini" closes **18% by value** and reports
   the offence closed. A false all-clear is worse than the original finding.
7. **Trap 3 in `Data-Quality-Traps.md` is itself false.** Payment-mode amounts DO
   reconcile with the right column pair (`Amount - ReturnAmount`, not `TenderAmount`):
   UPI 3,63,75,631 + Cash 2,09,93,351 + Credit 1,92,50,593 = **Rs 7,66,19,575 vs
   `SUM(BillAmount)` Rs 7,66,19,249 — Rs 326 apart on Rs 7.66 Cr.** Fix the trap.
8. **No rent account exists** — ARY occupies Trust premises free. Every CSD/DMart/Blinkit
   benchmark compares a rent-payer to a non-rent-payer and no lane said so.

## 🔧 Tool defects that produced wrong findings (fix before trusting output)

- **`ary assort probe` is NON-DETERMINISTIC** — different results for identical terms in
  one session — and **silently returns zero when any term contains a hyphen**. Probe is
  the mandated anti-false-gap guard. **Every "probe returned zero" verdict is unsafe,
  including the ones used to CONFIRM the two real gaps.** Fix first.
- `internal/cli/assort.go:103` values stock as `SUM(Quantity) x MAX(PurchaseCost)`.
  Negative book stock reads **-Rs 1.82 Cr** that way vs **-Rs 14.13 L row-wise**. That one
  line produced the "-Rs 1.56 Cr sales posted without receipts" P0.
- `ary audit uncounted` is a filtered exception list read as a census — produced
  "8 months since last count" when 6 of 8 warehouses were counted within 10 days.
- `assort/research/coverage/*.json` substring matching is garbage in both directions:
  Fevicol as denture adhesive, Panasonic cells as electric toothbrushes, "Concord Kadai"
  as beta-blockers, banana FRUIT as banana chips.
- **My own workflow script truncated its evidence payload** (`.slice(0,180000)`), so the
  synthesiser received only 5 of 21 sizings. Re-run synthesis with a per-category digest.

## What to do, in order (from the synthesis)

**A. Losing money today**
1. **Reorder points on the 629 shelf-stable regular sellers that are empty.** Rs 50.13 L of
   proven demand exposed; Rs 4-9 L of gross profit recoverable (ESTIMATED — nothing in the
   data measures substitution). **No capital needed.** Every category-add is invalid until
   this holds. **Nobody owns replenishment today — that is the actual root cause.**
2. **Stop buying winter wear; mark down the rack.** **Rs 16.41 L at cost on hand
   30-Aug-2026** against Rs 0.2-0.4 L of August sales. Apparel total **Rs 47.28 L**.
   This is a cash release and a loss crystallisation — do NOT book it as upside.
3. **Compliance triage** — allopathic drugs (45 SKUs, Rs 39,672), notified devices without
   MD-42 (333 bills), toys QCO (421 SKUs, Rs 4.65 L, present tense), appliance QCO 1-Oct.
4. **Fix the CLI defects above** before trusting another number from it.
5. **Flag the non-resident block** — Rs 91.64 L / 12.0% across 5 accounts, 35 bills.
   Flagging only 002CM+Basement leaves Rs 19.36 L inside retail, incl. ARY's own Delhi parent.

**B. Later, only after A1 holds a quarter** — first aid / unlicensed medical devices
(~Rs 2.20 L rev, Rs 65k GM). ARY has **never bought a medical device in its history**
(every purchase-ledger hit on thermomet/oximet/glucomet/bandage is a salad dressing) while
selling 1,824 loose band-aids a year at 41% margin.

**Pharmacy Rx: DO NOT BUILD on standalone economics.** Rs 2.66 L of GM against a mandatory
dedicated registered pharmacist at Rs 2.16-3.00 L/yr. Contribution **-Rs 0.34 L to +Rs 0.50 L**
before rent, shrink and capital. The gap is real (49 of 51 lines are hard zeros); the
economics are not. Only a Trust-shared licence/pharmacist changes it.

## Things NOT to do (each already killed by evidence)

- Do not add ANY SKU until A1 holds a quarter. 51.2% of the working range is empty.
- Do not adopt CSD cost-plus pricing — destroys ~Rs 1.08 Cr of gross profit. Its premise
  ("ARY is Rs 2.70 Cr in the hole") is a **single opening-balance line dated 2023-04-01**.
- Do not run a dead-tail liquidation. Real dead stock is **Rs 10.43 L over 397 lines**, not
  Rs 1.07 Cr — 96% of the "13,400-line dead tail" is empty catalogue rows holding nothing.
  And Rs 40 L of the largest figure quoted is **"Button", a tailoring raw material**.
- Do not chase the Rs 23 L input-credit recovery. Total tax on all 16 GSTIN-less suppliers
  over 12 months is **Rs 1,771 on Rs 1.19 Cr**; ~Rs 1.09 Cr is nil-rated fresh produce.
- Do not bid for EU's "Rs 2.51 Cr food wallet" (see correction 1).
- Do not "add" toys (421 SKUs, Rs 4.65 L), electricals (312 SKUs), insecticides (Rs 32,753),
  Mamaearth (**16 SKUs, Rs 36,983** — the lane searched one word, it is "Mama Earth"),
  intimate wash (V Wash, 82 units/yr), the Rs 99-199 sunscreen rung (already the LARGEST
  unit band) or Korean noodles at Ary Lite (100% already at Ary Pos; the "imbalance" was
  two Bingo CHIP SKUs with "Korean" in the name). **All exist. All called new by a name-match.**
- Do not delist the 12 "dead" Glucose SKUs by name — Dabur Glucose-D sells Rs 11,591 and
  sold the day before the audit. Delist the Heinz listings only.
- Do not cut perishables in the winter window — they hold up BEST (Dry Fruits 82.6% of
  term, Vegetable 66.3%). What collapses is Confectionery 23.2%, Bakery 18.4%, Stationary 20.2%.

## Still open — needs a human, not an agent

1. Who owns replenishment? (A1 has no owner — the actual reason the shelf is empty)
2. Will the Trust share a pharmacy licence + pharmacist? Only thing that makes Rx viable.
3. Does Akal Hospital's dispensary already retail to residents? Moves B1 +/-50%.
4. Which winter-wear lines get marked down, and how far?
5. The Baru Sahib academic calendar — never obtained; the seasonality lane used a *plains*
   CBSE calendar showing a 9-day break to explain a 23-30 day trough.
6. Write off or close Talwandi Sabo? It distorts every store-wide inventory statistic.
7. Is each till a separately licensable FSSAI premises?
