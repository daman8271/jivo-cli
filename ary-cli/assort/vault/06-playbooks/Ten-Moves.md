---
type: playbook
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high on move 1 and on every prohibition · medium on move 2 · the sizing of the prize is ESTIMATED
system: ARY / FusionERP8
---

# Four moves — nothing else starts until the shelf ARY already has is refilled

The old ten moves were a range-expansion plan. [[Verify-Pass-2026-08-30]] killed it: **half
the working range is empty right now**, so every "add a category" move was a recommendation
to buy stock for shelves nobody is refilling. What is left is four moves, and three of them
cost nothing but a decision. Read [[Availability]] for the finding and [[Fleet-Method]]
before totalling anything — these are **not additive**.

*(The file keeps its old name so existing links resolve. It is four moves now, not ten.)*

---

## The one fact the whole playbook rests on

Retail only — Hunger Heroes wholesale (customer `002CM`), the canteen till, BOM inputs and
fresh produce excluded by warehouse and `ItemType`, not by the category tree. Stock is
**company-wide `SUM(Stock.Quantity) <= 0`**; measured at the retail counters alone it reads
worse (3,211) but that is unposted-transfer noise, not empty shelves.

| | | Status |
|---|---|---|
| Retail SKUs that sold in the 12m to 30-Aug-2026 | **5,950** | VERIFIED |
| …out of stock right now | **3,051 (51.28%)** | VERIFIED |
| Trailing sales behind an empty shelf | **₹1,44,32,593** | VERIFIED |
| …as a share of the ₹5.83 Cr retail base | 24.8% | VERIFIED |
| SKUs in `ProductMaster` with a reorder level set | **1 of 21,479** | VERIFIED |
| Rows in `ProductROQMaster` | **1** | VERIFIED |

**Nobody owns replenishment.** That is not an inference from the outage — it is directly
observable in the master data, and it is the actual root cause. See [[Open-Questions]] #1.

---

## 1 · Put reorder points on the 864 empty regular sellers

**₹73.02 L of proven repeat demand exposed · ₹17.84 L of gross profit it earned when it was
on shelf · ₹5–9 L realistically recoverable (ESTIMATED) · no capex, no licence, no new SKU**

The cut: sold on **≥20 separate days** in the last 12 months, **zero stock today**, **≥21
days since the last sale**. Not a wish list — lines that demonstrably sold, repeatedly, and
then stopped. **Read as-of 2026-08-30, and it moves daily** — the same SQL rolled one day
forward returns **866 SKUs / ₹73,21,091** (VERIFIED), so quote the date with the number.

| | | Status |
|---|---|---|
| SKUs | **864** | VERIFIED |
| Trailing 12m sales | **₹73,02,272** | VERIFIED |
| Average days since the last sale | **128 days (4.2 months)** | VERIFIED |
| Gross margin they earned (809 costable, 12m purchase-ledger WAC) | **25.80%** | VERIFIED |
| Gross profit those 809 carried | **₹17,84,464** (₹69,15,436 revenue − ₹51,30,972 COGS) | VERIFIED |
| **Bought within the last 12 months** | **809 of 864 (94%)**, avg **190 days** since the last PO | VERIFIED |
| Last bought over 12 months ago | 53, avg 516 days | VERIFIED |
| Never purchased at all | **2** | VERIFIED |

⚠️ **"128 days" and "190 days" are days-since, not measured absence.** FR8HODBNEW stores no
stock history, so nothing here proves a line sat empty for 128 days rather than emptying last
week. [[Availability]] states the same limit.

**That 94% is the most persuasive number in this vault.** It separates *failed to reorder*
from *deliberately delisted*: ARY was actively buying these lines just over six months ago
and simply stopped. (The 210-day mean that used to sit here is the average across all 862
ever-purchased lines, dragged up by the 53 last bought 516 days ago. It is not the 809.)

Where it sits:

| Category | SKUs | Trailing sales | Avg days out | Status |
|---|---|---|---|---|
| Confectionery | 292 | ₹23,91,170 | 142 | VERIFIED |
| Personal Care | 171 | ₹10,20,582 | 122 | VERIFIED |
| Drinks | 44 | ₹4,52,266 | 125 | VERIFIED |
| General Items | 52 | ₹3,94,169 | 143 | VERIFIED |
| Dry Fruits | 15 | ₹3,55,970 | 151 | VERIFIED |
| Footwear | 7 | ₹3,42,062 | 98 | VERIFIED |

**Why ₹5–9 L and not ₹17.84 L.** ESTIMATED, assumptions stated: (a) these lines were on shelf
for only part of the year, so the trailing figure is not an annual run rate; (b) shoppers
substitute — on the one category where substitution has been measured, **~60% of every rupee
lost on an out-of-stock top-10 snack came back on another snack** (season-adjusted: top-10
gain ₹2.42/bill against ₹1.46/bill lost elsewhere; **24% raw**). That is VERIFIED arithmetic
but rests on a **circular classifier** — "in stock" there means "the SKU rang a sale that
day", so it measures *didn't sell*, not *wasn't there* ([[Availability]]). Do not promise the
gross number to anyone.

**What it costs.** No capex, no licence, no new category. ₹51,30,972 is the **annual cost of
goods** on these lines (VERIFIED), *not* the capital required — the capital standing at any
one moment is that divided by inventory turns, and **turns are NOT-CHECKED here**.

**Where to start, and who keys it in.** Sharpest slice: the **89 lines that sold on 100+ of
the year's 354 trading days and are empty today, carrying ₹19,74,398** (VERIFIED).
Confectionery and Personal Care are 463 of the 864 — two buyers' beats. **The `ary` CLI is
read-only**, so every reorder point has to be typed into FusionERP8 by a person; whether
FusionERP8 then produces an actionable reorder report is **NOT-CHECKED**.

⚠️ **Two slices of the 864 are not replenishment failures.** 2 Academy Dress SKUs carry
₹3,79,860 and have been quiet only 40 days (VERIFIED) — a uniform buying cycle. And 7 Winter
Wear SKUs carrying ₹1,58,439 (VERIFIED) sit in **both** this move and move 2; decide those
under move 2.

→ [[Availability]] · [[Catalogue-Shape]] · [[Open-Questions]]

## 2 · Winter wear — mark down the ₹1.56 L that is genuinely dead, and do it in February

**₹16.41 L of cash sitting in stock, of which ₹1.56 L is stale · a cash release and a LOSS
CRYSTALLISATION, never upside · blocker: one human decision (see [[Open-Questions]] #4)**

Winter Wear is **not** a failing category — it does **₹42,62,224** a year (VERIFIED).

| | | Status |
|---|---|---|
| Winter Wear on hand, at cost | **₹16,41,366** (3,782 units, 188 SKUs holding stock) | VERIFIED |
| …at selling value | ₹21,39,299 | VERIFIED |
| Whole Oct–Dec 2025 sell-through | **₹23,87,856** | VERIFIED |
| **Cover: stock at selling value ÷ one season's sell-through** | **0.90 of a season** | VERIFIED |
| Purchased in Oct-2025 | ₹9,51,752 across 13 bills | VERIFIED |

**The over-carry diagnosis is dead.** ARY holds **less** than one season's cover — 0.90 of it
— so "stop buying winter wear" is not supported, and neither is reading last October's
₹9.52 L as buying on top of a pile. The old premise was refuted by two figures printed four
lines apart in its own table.

**And the ageing test was reading the calendar, not the shelf.** Winter Wear sells Oct–Dec, so
measured on 30 August anything that sold through *last* season lands in "3–6 months" or "6+
months" whatever its health. The two lines the old cut named as mark-down candidates — *Boys
Long Coat 42 Cm* (last sold **4-Dec-2025**) and *Sm Jacket* (**14-Dec-2025**) — last sold in
the first weeks of December, at the peak of the season.

Season-aware, by last sale date:

| Last sold | SKUs holding stock | Units | Cost on hand | Status |
|---|---|---|---|---|
| Since Mar-2026 | 107 | 2,361 | ₹11,76,102 | VERIFIED |
| Inside the Oct-25 → Feb-26 season | 50 | 817 | ₹3,09,206 | VERIFIED |
| **Before Oct-2025** | **15** | **329** | **₹93,930** | VERIFIED |
| **Never sold** | **16** | **275** | **₹62,129** | VERIFIED |

**Genuinely stale = ₹1,56,059, or 9.5% of the pile** — not the ₹10.08 L / 61% the old
calendar-clock cut produced on a 92-day / 180-day boundary. (It printed ₹10,07,840; its own
three buckets summed to ₹10,08,040.) That cut also **counted `Stock` rows, not products
holding stock**: its 43 / 75 / 162 / 33 are 41 / 61 / 70 / 16 on hand (VERIFIED), so a reader
told to mark down "162 SKUs" would find 70.

**Timing is the whole move.** This note is dated 30-Aug-2026, one month before the Oct–Dec
window in which the category takes ₹23.87 L. **Do not mark down in September.** Sell the
season, re-cut the table in February on the same season-aware definition, then mark down what
still has not moved. It is **not upside**: it releases cash and books a loss that is already
real.

⚠️ The group is mis-filed like everything else here — *Hemant Track Suit 42 Summer Boy*
(₹40,600 on hand, last sold 15-Jul-2025) sits inside "Winter Wear" and *is* genuinely stale.
Mark down by **last sale date**, never by group name. See [[Data-Quality-Traps]].

→ [[Seasonality]] · [[Stock-Variance]] · [[Open-Questions]]

## 3 · Compliance triage — decide what ARY is licensed to sell

**₹0 to find out · days · blocker: none · this is exposure, never revenue**

Every figure below is small. That is the point: the cost of stopping is near zero, and the
downside of not stopping is a licence, not a margin.

| Exposure | Range | 12m sales | Status |
|---|---|---|---|
| **Allopathic oral/systemic drugs** (strict: tablets, syrups, lozenges — Crocin, Paracitamol, Disprin, Strepsils, Benadryl, D Cold, Cofsils, Avomine) | 21 SKUs listed, **8 selling** | **₹22,324 · 567 units · 498 bills** | VERIFIED |
| …as a share of all bills | 498 of 373,461 | **0.13%** | VERIFIED |
| **Anything regulated as a drug** (adds topical analgesics, antiseptic lotions, Vicks) | 33 SKUs | **₹1,28,100 · 1,832 bills** | VERIFIED |
| **Notified medical devices** (Dettol Bandaid, cotton) | 4 SKUs | ₹5,942 | VERIFIED |
| **Toys — QCO in force** | **421 SKUs** (Toys 219 + Toy & Sports 202) | **₹4,66,640** | VERIFIED |
| Electricals range, for scoping only | 123 SKUs | ₹1,51,593 | VERIFIED |
| Room heaters · irons | 15 · 32 SKUs | ₹71,087 · ₹34,511 | VERIFIED |

**State the definition with the number.** The earlier "45 SKUs / ₹39,672" could not be
reconstructed — on the strict oral/systemic definition it is 21 SKUs and ₹22,324. Quoting a
figure without its definition is not defensible.

Two live corrections to the compliance lane, both of which change what to do:

- **A partial stop is worse than none.** Dropping only Crocin/Disprin/Volini closes a
  fraction of the range and reports the offence closed. Decide the whole line at once.
- **The BIS appliance "escape hatch" belongs to the manufacturer/importer**, not to a
  retailer in Baru Sahib, and room heaters, irons, hair dryers and fans are **not named** in
  the schedule. The ₹2 L penalty is a statutory **floor**, cap 10× goods value. Do not size
  an appliance QCO exposure off the earlier note.

→ [[Pharmacy]] · [[Gap-List]] · [[Verify-Pass-2026-08-30]]

## 4 · Fix the CLI before quoting another number from it

**₹0 · hours · blocker: none · two defects are fixed, three are open**

Fixed on 2026-08-30, both re-tested live today:

| Defect | Evidence it is fixed | Status |
|---|---|---|
| `probe` was blind to punctuation | `probe sugar-free` normalises to `sugarfree` and returns **24 SKUs / ₹68,825**; it returned 0 before | VERIFIED |
| Stock valued `SUM(Quantity) × MAX(PurchaseCost)` | negative book stock now reads **−₹17,18,208** over 887 rows, row-wise | VERIFIED |

Still open, and each has already produced a wrong finding:

- **`probe` still gives false ZEROS — on the house's own spelling.** `probe paracetamol`
  returns **0** while ARY sells *Paracitamol 500 Mg* (**₹590 across 56 bills**). Same class:
  `probe bandage` returns **0** while `probe bandaid` returns the Dettol SKU (**₹4,457**).
  Probe **stems**, not words. A single correctly-spelled zero is not proof of absence.
- **`probe` gives false POSITIVES, and the verdict row hides them.** `probe pand` returns
  2 SKUs / ₹950 — *Meiji Hello Panda Biscuits* and *Pandol*, a vegetable (VERIFIED). Same
  trap, bigger: `probe ors` returns **13 SKUs / ₹8,711.20** of which only **5 are ORS
  (₹8,161.20)** — the rest are *Campus Sporst Shoes*, *Kores Modelling Clay* and *Doms Poster
  Colors*, caught inside "sp**ors**t" and "col**ors**" (VERIFIED). Never read the verdict row
  without the SKUs beneath it.
- **A PHRASE passed as ONE argument silently returns zero.** `probe "ors electral"` → **0**
  and `probe "washing bar"` → **0**, while `probe washing bar soap` → **528 SKUs /
  ₹10,95,964** (VERIFIED). Separate words are ORed correctly (`probe ors paracit` = 15 SKUs /
  ₹9,301.20 = 13 + 2), so the fault is quoting, not multi-word search. Under zsh an unquoted
  variable does not word-split, so `t='ors electral'; probe $t` passes one argument and
  returns a zero indistinguishable from a real gap. **The most dangerous failure mode here.**
- `ary audit uncounted` is a filtered exception list read as a census.
- `assort/research/coverage/*.json` substring matching is garbage in both directions.

The probe non-determinism report is **NOT REPRODUCED** — repeated identical runs give
byte-identical output. Do not repeat that claim.

→ [[Data-Quality-Traps]] · [[Fleet-Method]]

---

## Do not do these — each is already killed by evidence

- **Do not add ANY SKU until move 1 holds a quarter.** 51.28% of the working range is empty
  (VERIFIED). A new category on an unreplenished shelf is a new empty shelf.
- **Do not "add" things ARY already sells.** Each was called a new category by a name-match.
  All re-run today, all VERIFIED; figures marked `probe` come from `ary assort probe`, whose
  12-month window starts one day earlier than the SQL base above. Toys **421 SKUs /
  ₹4,66,640** (group cut); electricals **123 SKUs**; Mamaearth **16 SKUs / ₹38,668**
  (`probe mamaearth` — it is written "Mama Earth"); intimate wash **2 SKUs / ₹10,048**
  (`probe vwash`); sunscreen **14 SKUs / ₹19,829** (`probe sunscreen`; the whole SPF range is
  48 SKUs / ₹88,861 on `probe spf`) — the old "₹99–199 rung" label was never what was
  measured and is deleted; Korean noodles **5 Geki/Nissin SKUs / ₹44,640**.
- **Do not "add" insecticides** — `probe insecticide` returns **0** because ARY files them by
  brand. On a brand-term cut (`Mosquito`, `All Out`, `Good Knight`, `Mortein`, `Odomos`)
  **25 SKUs are catalogued, 5 sold in 12m, ₹8,259** — All Out combo ₹4,515, Good Knight
  refill ₹1,530, All Out refill ₹1,510, Eveready Mosquito Racquet ₹399, Good Knight Combi
  Gold Flash ₹305 (VERIFIED). A wider cut pulling in the *Hit* sprays is larger; state the
  cut with the count. (The old "28 catalogued, 4 selling" matches no cut.)
- **Do not run a dead-tail liquidation.** Real dead stock is **396 lines worth ₹10,42,642**
  (VERIFIED). Of the 15,249 lines that sold nothing in 12 months, **14,853 (97.4%) hold zero
  stock** (VERIFIED) — they are empty catalogue rows, and deleting them releases no cash.
- **Do not grow the institutional channel, and do not bid for EU's "₹2.51 Cr food wallet."**
  Hunger Heroes turns ₹69.81 L at **1.04% gross margin** against retail's 24.42%; EU's figure
  is cooked-meal transfer charges plus staff boarding exactly offset by staff collections.
  (NOT-CHECKED by me — verified by the margin and institutional re-tests; see
  [[Institutional]] and [[Verify-Pass-2026-08-30]].)
- **Do not adopt CSD cost-plus pricing.** It destroys ~₹1.08 Cr of gross profit, and its
  premise — "ARY is ₹2.70 Cr in the hole" — is a single opening-balance line dated
  2023-04-01. (NOT-CHECKED by me; [[Verify-Pass-2026-08-30]].)
- **Do not chase the ₹23 L input-credit recovery.** Total tax on all 16 GSTIN-less suppliers
  over 12 months is ₹1,771 on ₹1.19 Cr, and ~₹1.09 Cr of that is nil-rated fresh produce.
  (NOT-CHECKED by me; [[Verify-Pass-2026-08-30]].)
- **Do not build frozen.** It is not a gap — it is a small, healthy, monthly-restocked
  category at ~24.3% margin doing ~₹52,000 a year on 0.11% of bills, and the canteen sells
  the cooked equivalent at roughly 100:1. (NOT-CHECKED by me; frozen re-test, 2026-08-30.)
- **Do not delist by name.** Dabur Glucose-D sells and sold the day before the audit; the
  ₹40 L "dead" line is *Button*, a tailoring raw material.

## Deferred, and only after move 1 holds a quarter

**First aid and unlicensed devices.** No revenue size is given — the ₹2.20 L / ₹65k GM that
used to stand here had no derivation and is deleted. What is measured: three thermometers
have sat active since before Apr-2023 and have **never once been ordered in 9,284 purchase
bills**, and **instrument purchase lines, all time, = 0** (VERIFIED). ARY's whole medical
wound-care purchase ledger is **5 `Medicare` SKUs, 24 purchase lines, ₹18,204 at cost, last
band-aid order 6-Jul-2026** — Dettol Bandaid 13 lines ₹9,749, Tulip Cotton Ball 4 ₹3,204,
Cotton 10 Gm 3 ₹2,111, Usha Cotton Rolls 2 ₹1,688, Trutip Cotton Ball 2 ₹1,452 (VERIFIED).
⚠️ The "17 SKUs / ₹2,02,880" that stood here was name-match contamination — it swept in
*Fabric Cotton White (Agra)*, tailoring cloth at ₹2,10,582, plus Stayfree pads, cotton buds,
a bath mat and cottonseed oil. Only the never-listed instruments — oximeter, glucometer,
nebuliser, BP monitor, mobility aids, sterile dressings — are a genuine decision.

**Pharmacy Rx: do NOT build on standalone economics.** The gap is certain — across all
21,479 SKUs there is not one chronic-disease molecule, and none has ever been purchased in
the 3.4 years the purchase ledger covers (VERIFIED). Oral/systemic allopathic sales are
**₹22,324 in 12 months** (VERIFIED). **The revenue side cannot be sized from this database**
— the ₹2.66 L of gross margin that used to stand here has no derivation anywhere in the
vault and is deleted, as is the "₹4.46 per resident" figure that divided it by a 5,000
headcount [[Population]] does not support. The cost side is hard: a mandatory registered
pharmacist at **₹2.16–3.00 L/yr** (ESTIMATED), before shrink, expiry write-off and capital.
**And the software blocker is real** — in `ProductChildMaster` the typed `MfgDate` and
`ExpDate` columns hold the `1900-01-01` sentinel in **all 111,253 rows** (VERIFIED). What
exists is **27 rows of free text in the generic `Field1`/`Field2`/`Field3`** (24 / 26 / 26),
dated 2017 to 2019. That is not a schema holding batch and expiry; it is proof nobody has
kept batch discipline in eight years. Only a Trust-shared licence and pharmacist changes the
verdict. → [[Pharmacy]]

## Still needs a human, not an agent

1. **Who owns replenishment?** Move 1 has no owner. This is the actual reason the shelf is empty.
2. Which winter-wear lines get marked down in February, and how far?
3. Does Akal Hospital's dispensary already retail to residents? Moves the device case ±50%.
4. Will the Trust share a pharmacy licence and pharmacist?
5. Write off or close Talwandi Sabo? ⚠️ It does **not** distort the availability statistic:
   warehouse 17 holds **zero** non-zero stock rows, warehouse 14 holds 806 rows at a net
   **negative ₹8,23,199**, and re-running the headline with `WarehouseID NOT IN (14,17)`
   leaves out-of-stock at **3,051 SKUs**, moving the value ₹3,753 (VERIFIED). A write-off
   question, not a measurement one.

Full list and status: [[Open-Questions]].

## See also

- [[Availability]] — the finding this playbook is built on: the exclusion SQL, the
  out-of-stock definition, the substitution measurement and its circular classifier
- [[Verify-Pass-2026-08-30]] — the 106 refuted claims; read it before quoting anything older
- [[Corrections-Log]] — where the claims deleted from this note are recorded
- [[Data-Quality-Traps]] — the category tree, the probe false zeros, and why `SaleDetail`
  has no `Amount` column
- [[Below-Cost-Leak]] — the other thing losing money today, and the only one fixable in hours
- [[Stock-Variance]] — why book stock and the shelf disagree, and where the 887 negative rows are
- [[Seasonality]] — the Oct–Dec winter window move 2 must be timed against
- [[Pharmacy]] — the one REAL_GAP that survives, and why its economics cannot be sized here
- [[Population]] — why the 5,000 headcount is not a measured figure
- [[Institutional]] — the channel this playbook deliberately stopped recommending
- [[Fleet-Method]] — why these moves must never be summed
- [[00-ARY-Atlas]] — everything else measured
