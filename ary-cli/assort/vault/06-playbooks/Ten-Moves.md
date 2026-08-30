---
type: playbook
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high on moves 1–2 and on every prohibition · medium on the sizing of the prize
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

**₹73.02 L of proven repeat demand exposed · ₹18.84 L of gross profit it earned when it was
on shelf · ₹4–9 L realistically recoverable (ESTIMATED) · no capex, no licence, no new SKU**

The cut: sold on **≥20 separate days** in the last 12 months, **zero stock today**, **≥21
days since the last sale**. Not a wish list — lines that demonstrably sold, repeatedly, and
then stopped.

| | | Status |
|---|---|---|
| SKUs | **864** | VERIFIED |
| Trailing 12m sales | **₹73,02,272** | VERIFIED |
| Average days off shelf | **128 days (4.2 months)** | VERIFIED |
| Gross margin they earned (809 costable, purchase-ledger WAC) | **25.80%** | VERIFIED |
| Gross profit those 809 carried | **₹18,84,464** on ₹69.15 L revenue | VERIFIED |
| Cost of goods to keep them stocked for a year | ₹51,30,972 | VERIFIED |
| **Bought within the last 12 months** | **809 of 864 (94%)** | VERIFIED |
| Average days since the last purchase order | **210** | VERIFIED |
| Never purchased at all | **2** | VERIFIED |

**That 94% is the most persuasive number in this vault.** It is what separates *failed to
reorder* from *deliberately delisted*: ARY was actively buying these lines, on average seven
months ago, and simply stopped. Two of 864 were never bought.

Where it sits:

| Category | SKUs | Trailing sales | Avg days out | Status |
|---|---|---|---|---|
| Confectionery | 292 | ₹23,91,170 | 142 | VERIFIED |
| Personal Care | 171 | ₹10,20,582 | 122 | VERIFIED |
| Drinks | 44 | ₹4,52,266 | 125 | VERIFIED |
| General Items | 52 | ₹3,94,169 | 143 | VERIFIED |
| Dry Fruits | 15 | ₹3,55,970 | 151 | VERIFIED |
| Footwear | 7 | ₹3,42,062 | 98 | VERIFIED |

**Why ₹4–9 L and not ₹18.84 L.** ESTIMATED, and the assumptions are stated: (a) these lines
were on shelf for only part of the year, so the trailing figure is not an annual run rate;
(b) shoppers substitute — on the one category where substitution has been measured, **47% of
every rupee lost on an out-of-stock top-10 snack came back on another snack**, so the uplift
must be booked net. Do not promise the gross number to anyone.

**What it costs.** No capex, no licence, no new category. It does consume working capital —
₹51.31 L of goods a year on these lines (VERIFIED), recycling as they sell.

→ [[Availability]] · [[Catalogue-Shape]] · [[Open-Questions]]

## 2 · Stop buying winter wear and mark the rack down

**₹16.41 L of cash locked in stock · a cash release and a LOSS CRYSTALLISATION · days ·
blocker: one human decision (see [[Open-Questions]] #4)**

Winter Wear is **not** a failing category — it does ₹42.62 L a year. The failure is
over-carry: on 30-Aug-2026 ARY holds more winter stock than it can sell in a season, and last
October it bought ₹9.52 L more on top.

| | | Status |
|---|---|---|
| Winter Wear on hand, at cost | **₹16,41,366** (3,782 units) | VERIFIED |
| …at selling value | ₹21,39,299 | VERIFIED |
| Sold in the whole Jun–Aug 2026 summer quarter | **₹1,86,345** | VERIFIED |
| Sold in Aug-2026 alone | ₹81,289 across 43 bills | VERIFIED |
| Purchased in Oct-2025 | **₹9,51,752 across 13 bills** | VERIFIED |
| Whole Oct–Dec 2025 sell-through | ₹23,87,856 | VERIFIED |
| 12m category sales | ₹42,62,224 | VERIFIED |

The ageing is where the loss lives:

| Stock bucket | SKUs | Units | Cost on hand | Status |
|---|---|---|---|---|
| Sold within 3 months | 43 | 1,157 | ₹6,33,327 | VERIFIED |
| **No sale for 3–6 months** | 75 | 1,188 | **₹5,38,565** | VERIFIED |
| **No sale for 6+ months** | 162 | 1,162 | **₹4,07,346** | VERIFIED |
| **Never sold** | 33 | 275 | **₹62,129** | VERIFIED |

**₹10,07,840 — 61% of the pile — has not sold in three months or more.** Named lines:
*Boys Long Coat 42 Cm*, 49 units, ₹93,100 at cost, **last sold 4-Dec-2025**; *Sm Jacket*,
181 units, ₹59,730, **last sold 14-Dec-2025**.

Two things this move is not. It is **not upside** — marking down releases cash and books a
loss that is already real; anyone presenting it as revenue is double-counting. And the
diagnosis is **not late ordering**: an earlier lane proposed pulling the winter buy forward
into August, which would add stock to a pile that already exceeds a season's sales.

⚠️ The group is mis-filed like everything else here — *Hemant Track Suit 42 Summer Boy*
(₹40,600 on hand, last sold 15-Jul-2025) sits inside "Winter Wear". Mark down by **last sale
date**, never by group name. See [[Data-Quality-Traps]].

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
reconstructed — on the strict oral/systemic definition it is 21 SKUs and ₹22,324; the larger
figure presumably folded in topicals and the nasal spray. Either is defensible; quoting one
without its definition is not.

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
| `probe` was blind to punctuation | `probe sugar-free` now returns **24 SKUs / ₹68,825**; it returned 0 before | VERIFIED |
| Stock valued `SUM(Quantity) × MAX(PurchaseCost)` | negative book stock now reads **−₹17,18,208** over 887 rows, row-wise | VERIFIED |

Still open, and each has already produced a wrong finding:

- **`probe` still gives false ZEROS — on the house's own spelling.** `probe paracetamol`
  returns **0** while ARY sells *Paracitamol 500 Mg* (**₹590 across 56 bills**). Same class:
  `probe bandage` returns **0** while `probe bandaid` returns the Dettol SKU (**₹4,457**).
  Probe **stems**, not words. A single correctly-spelled zero is not proof of absence.
- **The punctuation fix introduced false POSITIVES.** `probe pan-d` normalises to `pand` and
  returns 2 SKUs / ₹950 — *Meiji Hello Panda Biscuits* and *Pandol*, a vegetable. Never read
  the verdict row without reading the SKUs beneath it.
- **`probe` takes ONE word, and a multi-word term silently returns zero.** `probe ors
  electral` → **0**. `probe ors` → **29 SKUs / ₹28,069** (VERIFIED). Under zsh an unquoted
  variable does not word-split either, so a scripted zero looks exactly like a real gap.
  **This is the most dangerous failure mode in the project.**
- `ary audit uncounted` is a filtered exception list read as a census.
- `assort/research/coverage/*.json` substring matching is garbage in both directions.

The probe non-determinism report is **NOT REPRODUCED** — three identical runs give
byte-identical output. Do not repeat that claim.

→ [[Data-Quality-Traps]] · [[Fleet-Method]]

---

## Do not do these — each is already killed by evidence

- **Do not add ANY SKU until move 1 holds a quarter.** 51.28% of the working range is empty
  (VERIFIED). A new category on an unreplenished shelf is a new empty shelf.
- **Do not "add" things ARY already sells.** Every one of these was called a new category by
  a name-match: toys **421 SKUs / ₹4,66,640**; electricals **123 SKUs**; Mamaearth **16 SKUs
  / ₹38,668** (it is written "Mama Earth"); intimate wash **2 SKUs / ₹10,048**; the ₹99–199
  sunscreen rung **14 SKUs / ₹19,829**; Korean noodles **5 Geki/Nissin SKUs / ₹44,640**, all
  already at Ary Pos. All VERIFIED today.
- **Do not "add" insecticides** — and note *why* the lane missed them: `probe insecticide`
  returns **0** because ARY files them by brand. 28 mosquito SKUs are catalogued, 4 selling
  (All Out combo ₹4,515, Good Knight refill ₹1,530, All Out refill ₹1,510) (VERIFIED).
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

**First aid and unlicensed devices.** Sized at roughly ₹2.20 L revenue / ₹65k GM, and half of
it is not an assortment question at all — it is move 1 again. Three thermometers have sat
active in the catalogue since before Apr-2023 and have **never once been ordered in 9,284
purchase bills**, and **instrument purchase lines, all time, = 0** (VERIFIED). ARY *has*
bought wound care: **17 SKUs, 142 purchase lines, ₹2,02,880 at cost, last band-aid order
6-Jul-2026** (VERIFIED). Only the never-listed instruments — oximeter, glucometer, nebuliser,
BP monitor, mobility aids, sterile dressings — are a genuine decision.

**Pharmacy Rx: do NOT build on standalone economics.** The gap is certain — across all
21,479 SKUs there is not one chronic-disease molecule, none has ever been purchased, and
allopathic sales run **₹4.46 per resident per year** (ESTIMATED: ₹22,324 VERIFIED ÷ the 5,000
campus headcount, which is not measured in FR8HODBNEW). The economics are not: ~₹2.66 L of GM
against a mandatory registered pharmacist at ₹2.16–3.00 L/yr, before rent, shrink and
capital. **And the software blocker is real** — `ProductChildMaster` holds 111,253 rows of
which **26 carry a batch/expiry value (0.023%), all dated 2017–2018** (VERIFIED). The schema
*can* hold batch and expiry; it has been unused for eight years, which is the same finding
operationally and a different fact. Only a Trust-shared licence and pharmacist changes the
verdict. → [[Pharmacy]]

## Still needs a human, not an agent

1. **Who owns replenishment?** Move 1 has no owner. This is the actual reason the shelf is empty.
2. Which winter-wear lines get marked down, and how far?
3. Does Akal Hospital's dispensary already retail to residents? Moves the device case ±50%.
4. Will the Trust share a pharmacy licence and pharmacist?
5. Write off or close Talwandi Sabo? Warehouses 14 and 17 are inactive, 400 km away, and
   still hold live stock that distorts every store-wide availability statistic.

Full list and status: [[Open-Questions]].

## See also

- [[Availability]] — the finding this playbook is built on: the exclusion SQL, the
  out-of-stock definition, and why the retail-warehouse read is an artefact
- [[Verify-Pass-2026-08-30]] — the 106 refuted claims; read it before quoting anything older
- [[Data-Quality-Traps]] — the category tree, the probe false zeros, and why `SaleDetail`
  has no `Amount` column
- [[Below-Cost-Leak]] — the other thing losing money today, and the only one fixable in hours
- [[Stock-Variance]] — why book stock and the shelf disagree, and where the 887 negative rows are
- [[Seasonality]] — the Oct–Dec winter window move 2 is sized against
- [[Pharmacy]] — the one REAL_GAP that survives, and the pharmacist arithmetic that kills it
- [[Institutional]] — the channel this playbook deliberately stopped recommending
- [[Fleet-Method]] — why these moves must never be summed
- [[00-ARY-Atlas]] — everything else measured
