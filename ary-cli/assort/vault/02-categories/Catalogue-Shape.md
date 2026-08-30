---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high
system: ARY / FusionERP8
---

# Catalogue shape — ARY lists 21,479 lines, half have never traded, and half of what does trade is empty today

**ARY does not have an assortment problem. It has an availability problem.** That thesis
survived the [[Verify-Pass-2026-08-30]] and came out stronger; the evidence for it has moved
to [[Availability]], which is now the note to read first. What is left here is the shape of
the catalogue underneath it — how many lines exist, how few ever trade, and how little the
"dead tail" is actually worth once it is valued correctly.

Three things this note used to say are gone: the Rs 40 lakh of dead stock (an arithmetic
bug, see below), the "add ~1,500 lines to dairy, staples and baby care" prescription
(killed by the verify pass), and the coverage-corpus line-coverage table (the matching
behind it is unreliable in both directions). See [[Corrections-Log]].

## The catalogue, counted

All figures live 2026-08-30, whole catalogue, no channel filter.

| | | Status |
|---|---|---|
| Catalogue lines (`ProductMaster`) | **21,479** | VERIFIED |
| …flagged active | 19,494 | VERIFIED |
| …that have **ever** rung a sale, in the whole history of the books | **10,134 (47%)** | VERIFIED |
| …that have **ever** been purchased | 10,702 (50%) | VERIFIED |
| **…never bought and never sold, ever** | **10,554 (49.1%)** | VERIFIED |
| …holding any stock today | **3,397 (15.8%)** | VERIFIED |
| Sold at least once in the last 12 months (all channels) | 6,230 | VERIFIED |

```sql
-- ary query, all of the above in one pass
WITH ever_sold AS (SELECT DISTINCT ProductID FROM SaleDetail),
ever_bought AS (SELECT DISTINCT pd.ProductID FROM PurchaseDetail pd
  JOIN PurchaseHeader ph ON ph.SerialNumber=pd.SerialNumber
  WHERE ISNULL(pd.IsDeleted,0)=0 AND ISNULL(ph.IsDeleted,0)=0),
st AS (SELECT ProductID, SUM(Quantity) q FROM Stock GROUP BY ProductID)
SELECT COUNT(*), SUM(CASE WHEN es.ProductID IS NOT NULL THEN 1 ELSE 0 END), ...
FROM ProductMaster p LEFT JOIN ever_sold es ON es.ProductID=p.ProductID ...
```

**Half of ARY's catalogue is a row and nothing else.** 10,554 lines have never been bought
and never been sold since the books opened on 2023-04-01. They are not stock, not demand,
not a decision anybody made — they are master data an operator must still price, count and
scroll past.

## The working range, and how much of it is empty

The retail base — the only base worth quoting — is Ary Pos, Ary Clothing and Ary Lite
(warehouses 9, 11, 15), excluding the Hunger Heroes wholesale customer 002CM, canteen menu
items, raw material and fresh produce. **[[Availability]] carries the full exclusion SQL and
owns this finding**; the two figures below are here only to anchor the shape.

| | | Status |
|---|---|---|
| Retail SKUs that sold in the last 12 months | **5,950** | VERIFIED |
| Their trailing 12m sales | Rs 5.83 Cr | VERIFIED |
| **…out of stock right now** | **3,051 (51.3%)** | VERIFIED |
| Trailing sales behind an empty shelf | **Rs 1.44 Cr (24.8% of the base)** | VERIFIED |

Out-of-stock is measured as **company-wide `SUM(Stock.Quantity) <= 0`**, not shelf-level —
counter balances go negative on unposted transfers and would inflate the count. That choice
is load-bearing; [[Availability]] shows the workings.

### Where the emptiness sits — by revenue band

This replaces the "27 of the top 100 sellers are out of stock" line, which the verify pass
**REFUTED** (16 on a raw stock read, only 8 survive a 21-day off-shelf test, and 4 of those
8 are seasonal apparel with three or four selling days all year). The banded view is the
honest version and it says something stronger:

| Band | SKUs | 12m sales | Out of stock | OOS rate | Sales behind an empty shelf | Status |
|---|---|---|---|---|---|---|
| A — top 50% of revenue | 298 | Rs 291.00 L | 43 | **14.4%** | Rs 39.09 L | VERIFIED |
| B — next 30% | 933 | Rs 175.21 L | 270 | **28.9%** | Rs 44.48 L | VERIFIED |
| C — next 15% | 1,744 | Rs 87.44 L | 891 | **51.1%** | Rs 42.81 L | VERIFIED |
| D — last 5% | 2,975 | Rs 29.14 L | 1,847 | **62.1%** | Rs 17.95 L | VERIFIED |

Query: the retail-base CTE above, cumulative `SUM(val) OVER (ORDER BY val DESC)` banded
against `Stock`, `GROUP BY band`.

**298 SKUs earn half the money; 1,231 earn 80%.** The out-of-stock rate climbs cleanly from
14.4% at the top to 62.1% at the bottom — which is what a shop with no replenishment system
looks like: the fastest lines get bought because somebody notices them empty, and nothing
else does.

And the emptiness is not concentrated in the tail's rubbish. **Rs 83.57 lakh of the Rs 1.44
Cr sits in bands A and B** — lines that earn 80% of ARY's retail revenue.

### It is a reordering failure, not a delisting

| | | Status |
|---|---|---|
| Regular sellers off shelf (sold on ≥20 separate days, ≥21 days out) | **864 SKUs** | VERIFIED |
| Their trailing 12m sales | **Rs 73,02,272** | VERIFIED |
| Average days off shelf | 128 days (4.2 months) | VERIFIED |
| **…of which purchased within the last 12 months** | **809 (94%), carrying Rs 69.15 L** | VERIFIED |
| …never purchased at all | 2 | VERIFIED |
| SKUs in the whole catalogue with a reorder level set | **1 of 21,479** | VERIFIED |
| Rows in `ProductROQMaster` | **1** | VERIFIED |

`ary query "SELECT COUNT(*) FROM ProductROQMaster"` → 1.
`... FROM ProductMaster WHERE ReorderInformation=1 OR ReorderLevel>0` → 1.

809 of 864 are lines ARY was actively buying and simply stopped reordering. "Nobody owns
replenishment" is not an inference from the outage — **it is directly observable in the
master data.** One reorder point exists in the entire system.

> Note the direction of the correction: the published brief said 629 SKUs / Rs 50.13 lakh.
> On its own stated filter the answer is **864 SKUs / Rs 73.02 lakh**. The finding is 37%
> bigger than reported, not smaller.

## 🔴 The dead tail is Rs 10.43 lakh, not Rs 1.07 crore

The single largest number ever quoted in this vault's neighbourhood was a valuation bug.

| | | Status |
|---|---|---|
| Catalogue lines that sold nothing in 12 months | **15,249** | VERIFIED |
| **…of which hold any stock at all** | **396 (2.6%)** | VERIFIED |
| Their stock at cost, row-wise `SUM(Quantity × PurchaseCost)` | **Rs 10,42,642** | VERIFIED |
| Everything else — lines holding literally nothing | **14,853 (97.4%)** | VERIFIED |
| For scale: ARY's whole positive stock book | Rs 1.14 Cr | VERIFIED |

**97% of the "13,400-line dead tail" is empty catalogue rows holding zero stock.** There is
no liquidation to run and no cash to release. This is catalogue hygiene — dead lines still
flagged active, still priced, still counted — and it is worth doing for the operator's
attention, not for the money.

### The Rs 40 lakh "Button"

`ary assort` valued stock as `SUM(Quantity) × MAX(PurchaseCost)` in three places — every
unit priced at the dearest warehouse row's cost, applied to a netted quantity. One SKU
carried the whole error:

| Product 08M2 "Button" (Fabrics) | | Status |
|---|---|---|
| Pieces on hand | 21,287 | VERIFIED |
| Dearest `PurchaseCost` row in `Stock` (quantity **zero**) | Rs 190.00 | VERIFIED |
| Cost of the buttons actually on hand | Rs 0.32 – Rs 1.60 | VERIFIED |
| **Old valuation** `SUM(Qty) × MAX(Cost)` | **Rs 40,45,530** | VERIFIED |
| **True value** `SUM(Qty × Cost)` | **Rs 5,256.44** | VERIFIED |

```sql
SELECT s.WarehouseID, s.Quantity, s.PurchaseCost FROM Stock s WHERE s.ProductID='08M2'
-- 18 rows; the Rs 190 and Rs 170 rows all carry Quantity = 0
```

**Rs 40 lakh of "dead stock" was 21,287 shirt buttons worth five thousand rupees.** The bug
is fixed (`internal/cli/assort.go`, 2026-08-30) — but **any stock figure sourced from `ary
stock` or `ary assort` before 2026-08-30 is suspect and must be re-derived.** See
[[Data-Quality-Traps]].

What the real Rs 10.43 lakh is made of: Fabrics Rs 2.11 L (13 lines), Edible Oil & Ghee
Rs 1.66 L (3 lines — one of them 65.8 units of Jivo Canola 15 L), Winter Wear Rs 1.44 L
(30 lines), Confectionery Rs 0.62 L (17 lines), Cooking Consumable Rs 0.53 L (one LMK gas
line), Night Wear Rs 0.52 L. VERIFIED, `GROUP BY ProductGroupName`.

## Narrow and available beats broad and empty

The best evidence for the thesis is inside ARY's own counters. 12 months, by warehouse:

| Counter | SKUs sold | Bills | Sales | **Sales per SKU/yr** | Status |
|---|---|---|---|---|---|
| **Fruits & Vegetables** | **106** | 49,764 | Rs 51.12 L | **Rs 48,226** | VERIFIED |
| Ary G Canteen | 363 | 44,262 | Rs 54.26 L | Rs 14,948 | VERIFIED |
| Ary Clothing | 1,344 | 9,938 | Rs 134.66 L | Rs 10,019 | VERIFIED |
| **Ary Pos** (the main shop) | **5,526** | 232,175 | Rs 438.48 L | **Rs 7,935** | VERIFIED |
| Ary Lite | 364 | 37,308 | Rs 18.91 L | Rs 5,195 | VERIFIED |
| Basement | 98 | **14** | Rs 70.78 L | — | VERIFIED |

`ary query "SELECT d.WarehouseID, COUNT(DISTINCT d.ProductID), COUNT(DISTINCT h.SerialNumber),
SUM(d.Quantity*d.SaleRate) FROM SaleDetail d JOIN SaleHeader h ... WHERE h.VoucherDate>='2025-08-31'
AND h.VoucherDate<'2026-08-31' GROUP BY d.WarehouseID"`

**Fruits & Vegetables earns six times more per listed line than the main shop, on 106 SKUs.**
A narrow range that is genuinely in stock outsells a broad one that is half empty — on the
same campus, the same day, the same customers.

**Basement is not a counter and must never be quoted as one.** 98 SKUs across **14 bills in
a year** is the Hunger Heroes wholesale channel — Rs 69.81 L of that Rs 70.78 L is customer
002CM, at **1.04% gross margin**. An earlier version of this note listed Basement alongside
Fruits & Veg as one of "the two things that worked." That is deleted; see [[Institutional]].

## The benchmark, and the hole underneath every benchmark

`ary assort benchmark`, live 2026-08-30 — ARY's range against BigBasket BB Now metro
category counts pro-rated to 5,000 people:

| | | Status |
|---|---|---|
| Benchmark lines | 8,000 | ESTIMATED (metro counts VERIFIED, pro-rata is an assumption) |
| ARY active SKUs in scope | 14,358 | VERIFIED |
| ARY **selling** SKUs | 4,745 | VERIFIED |
| **Listed vs benchmark** | **1.79×** | ESTIMATED |
| **Selling vs benchmark** | **0.59×** | ESTIMATED |

**ARY lists 1.79× the benchmark range and sells 0.59× of it.** Both halves are true at once,
and that sentence is the whole finding — it is the assortment/availability split stated in
benchmark terms.

### 🔴 Every benchmark in this vault compares a rent-payer to a non-rent-payer

Nobody said this in fifteen research lanes. **ARY pays no rent.** Three rent-shaped accounts
exist in the chart of accounts and all three have never been posted to:

| Account | Group | Transaction lines | Status |
|---|---|---|---|
| Rent Exp (1907) | Indirect Expenses | **0** | VERIFIED |
| Rent Payable (1746) | Provisions | **0** | VERIFIED |
| The Kalgidhar Trust - Rent A/C (3237) | Local Debtors - Baru Sahib | **0** | VERIFIED |

```sql
SELECT a.AccountID, a.AccountName, COUNT(*) FROM TransactionChild t
JOIN AccountMaster a ON a.AccountID=t.AccountID
WHERE t.AccountID IN (1746,3237,1907) GROUP BY a.AccountID, a.AccountName   -- 0 rows
```

No occupancy cost appears anywhere in the expense ledger either — the largest indirect
expenses all-time are Depreciation Rs 44.06 L, Stitching Charges Rs 12.98 L and Electricity
Rs 8.39 L (VERIFIED). ARY occupies Trust premises free.

**So every CSD / DMart / Blinkit comparison in this vault silently benchmarks a business
with no rent against businesses whose entire range strategy is built around paying it.**
Shelf space is cheap here in a way it is not for any of them. Treat the *direction* of a
benchmark as usable and its *prescription* as not: a DMart's reason to cut a slow line does
not apply to a shop whose shelf costs nothing. This is also why the CSD cost-plus pricing
proposal was killed — see [[Verify-Pass-2026-08-30]].

### The benchmark's category rows are not safe to act on

Two independent failures, both documented in [[Data-Quality-Traps]]:

- **"Baby care: 323 benchmark lines, 0 ARY SKUs, NO ARY GROUP EXISTS"** is a mapping
  artefact. ARY files diapers under *Personal Care → Baby Diaper*. Live: **70 diaper SKUs
  listed, 23 ever purchased, 11 sold in 12m, Rs 32,456** (VERIFIED). The gap is real but it
  is a buying gap, not an empty category — see [[Baby-Care]].
- ARY's category tree is unreliable in general (Loose Milk under "Mini Meals", curd under
  "Others"), and `ary_active_skus` inherits that noise on every row.

**The "add ~1,500 lines to dairy, staples and baby care" recommendation that used to close
this section is deleted.** It is directly contradicted by the finding above it: adding range
to a shop where 51.3% of the working range is already empty makes the problem worse. Nothing
gets added until reordering holds for a quarter — [[Ten-Moves]].

## Listed, never ordered, never sold — the pattern in miniature

Re-verified live on the purchase and sale ledgers, not on the category tree:

| | Listed | Ever bought | Ever sold | Status |
|---|---|---|---|---|
| Huggies (every code) | 10 | **0** | **0** | VERIFIED |
| Thermometers (Cipla ×2, Hicks) | 3 | **0** | **0** | VERIFIED |
| Mamaearth / "Mama Earth" | 16 | 16 | 16 | VERIFIED |

The first two rows are the availability failure at SKU scale: a line sits active in the
catalogue for three years and is never once ordered in 9,284 purchase bills. The third row
is the opposite error — Mamaearth was reported as a missing brand by a lane that searched
one word; **all 16 SKUs exist, all 16 have been bought, all 16 have sold.** In this database
the burden of proof sits on "missing", never on "covered."

Also still standing, and worth its own note: [[Mobile-Tech]] — a real cable/charger/earphone
business hidden inside four generic catch-all product codes, invisible to any group-level
report (NOT-CHECKED in this pass; the margin figure there predates the cost-source fix and
should be re-derived from `PurchaseDetail`).

## What this does NOT show

- **Nothing here measures demand.** Rs 1.44 Cr behind an empty shelf is demand that was
  *exposed*, not revenue that was lost — nothing in FR8HODBNEW records what a shopper bought
  instead, or bought nowhere. [[Availability]] carries the substitution evidence, and it is
  large: on an independent availability measure other SKUs recover about 47% of what the
  missing ones lose.
- **Out-of-stock is one instantaneous read** taken 2026-08-30. `Stock` holds no history and
  there is no "discontinued" flag, so "days off shelf" is proxied by days-since-last-sale.
  A SKU management deliberately dropped is indistinguishable from one nobody reordered — the
  94%-purchased-within-12-months test is the best available substitute and it is not proof
  of intent.
- **The benchmark's 8,000 lines are an ESTIMATE** built by pro-rating metro SKU counts to a
  5,000-person population. The 5,000 headcount is itself the stated campus figure, never
  measured in this database, and the verify pass REFUTED the derived 4,600-4,800 variant —
  see [[Population]].
- **A probe zero is not proof of absence.** The punctuation fix landed 2026-08-30, but the
  house's own spelling still defeats it: `paracetamol` returns 0 while ARY sells
  "Paracitamol 500 Mg" (2 SKUs, VERIFIED). Probe stems, not words, and read the SKU block
  under the verdict row. Genuine stem-tested zeros in this catalogue include denture care
  (`dentu`, `polident`, `fixon` — all 0), chikoo/sapota, cold packs and compression
  stockings (VERIFIED).
- **The coverage corpus is not evidence.** The `assort/research/coverage/*.json` line-match
  table that used to close this note has been removed: its substring matching produced
  Fevicol as denture adhesive, Panasonic cells as electric toothbrushes and banana fruit as
  banana chips. Use [[Gap-List]] for probe-verified gaps.

## See also

- [[Availability]] — the core evidence now lives there; read it before quoting any figure here
- [[Verify-Pass-2026-08-30]] — what was refuted on 2026-08-30, and why seven lanes rate LOW
- [[Data-Quality-Traps]] — the stock-valuation bug, the category tree, and the probe's remaining false zeros
- [[Gap-List]] — the gaps that survive a stem-tested probe, as opposed to a name match
- [[Institutional]] — why Basement is a 1.04%-margin wholesale channel and not a counter
- [[Baby-Care]] — the diaper reading, corrected: a buying gap filed under Personal Care
- [[Below-Cost-Leak]] — the other reason the price master cannot be trusted for cost
- [[Ten-Moves]] — nothing is added to this catalogue until reordering holds a quarter
- [[Open-Questions]] — question 1, "who owns replenishment", is the root cause of everything above
