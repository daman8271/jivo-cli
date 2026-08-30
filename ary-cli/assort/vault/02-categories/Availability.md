---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high
system: ARY / FusionERP8
---

# Availability — half the working range is empty, and nobody owns replenishment

**ARY is not short of things to sell. It is short of the things it already sells.** This
note replaces the assortment brief: it measures what is off the shelf, proves the cause is
a failure to reorder rather than a decision to delist, and rebuilds the snack "natural
experiment" that was the brief's causal evidence — which does not survive contact with
seasonality. Read [[Verify-Pass-2026-08-30]] for what else was refuted, [[Catalogue-Shape]]
for why adding SKUs makes this worse, and [[Ten-Moves]] for what to do.

## The headline

**Definition, stated out loud because it is load-bearing: "out of stock" means
company-wide `SUM(Stock.Quantity) <= 0` read on 2026-08-30.** Retail base = sold between
2025-08-31 and 2026-08-31 at warehouses 9 (Ary Pos), 11 (Ary Clothing), 15 (Ary Lite),
excluding customer `002CM` (Hunger Heroes wholesale), `ItemType` 165/567 (raw material and
service charges), every `RestMenuChild` canteen menu line, and the Vegetable/Fruits groups.

| | | Status |
|---|---|---|
| Retail SKUs that sold in 12 months | **5,950** | VERIFIED |
| …out of stock right now | **3,051 — 51.28%** | VERIFIED |
| Their trailing 12m sales | **Rs 1,44,32,593 (Rs 1.44 Cr)** | VERIFIED |
| Retail base sales, same filter | Rs 5,82,79,566 | VERIFIED |
| Share of the retail base sitting behind an empty shelf | **24.8%** | VERIFIED |

> `WITH b AS (SELECT d.ProductID, SUM(d.Quantity*d.SaleRate) val, COUNT(DISTINCT CAST(h.VoucherDate AS date)) days_sold, MAX(CAST(h.VoucherDate AS date)) last_sale FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber=d.SerialNumber JOIN ProductMaster p ON p.ProductID=d.ProductID LEFT JOIN ProductGroupMaster g ON g.ProductGroupID=p.ProductGroupID WHERE h.VoucherDate>='2025-08-31' AND h.VoucherDate<'2026-08-31' AND d.WarehouseID IN (9,11,15) AND h.CustomerID<>'002CM' AND p.ItemType=164 AND d.ProductID NOT IN (SELECT ProductID FROM RestMenuChild) AND g.ProductGroupName NOT IN ('Vegetable','Fruits') GROUP BY d.ProductID), st AS (SELECT ProductID, SUM(Quantity) q FROM Stock GROUP BY ProductID) SELECT COUNT(*), SUM(CASE WHEN ISNULL(st.q,0)<=0 THEN 1 ELSE 0 END), CAST(SUM(CASE WHEN ISNULL(st.q,0)<=0 THEN b.val ELSE 0 END) AS decimal(18,0)) FROM b LEFT JOIN st ON st.ProductID=b.ProductID`
> — this `b` CTE is the base for every figure in this note.

**The read is not an artefact of a stale `Stock` table.** Out-of-stock rate rises
monotonically with time since last sale, which is what a live stock table must do:

| Last sold | SKUs | Out of stock | Rate | Status |
|---|---|---|---|---|
| Within 7 days | 1,520 | 85 | **5.6%** | VERIFIED |
| 8–30 days ago | 959 | 326 | 34.0% | VERIFIED |
| 1–3 months ago | 966 | 596 | 61.7% | VERIFIED |
| 3–6 months ago | 1,108 | 855 | 77.2% | VERIFIED |
| 6–12 months ago | 1,397 | 1,189 | **85.1%** | VERIFIED |

Every one of the 5,950 base SKUs has a `Stock` row (0 missing), so no zero in this table is
manufactured by the join. VERIFIED.

## The 864 regular sellers ARY stopped reordering

Narrow to lines with proven repeat demand that are genuinely off the shelf — **sold on ≥20
separate days in the year, and not sold for ≥21 days:**

| Cut | SKUs | Trailing 12m sales | Avg days off shelf | Status |
|---|---|---|---|---|
| **≥20 selling days** | **864** | **Rs 73,02,272** | **128.3** | VERIFIED |
| ≥25 selling days | 706 | Rs 67,34,905 | 121.4 | VERIFIED |
| ≥30 selling days | 577 | Rs 60,14,948 | 117.3 | VERIFIED |
| ≥40 selling days | 423 | Rs 52,80,961 | 110.5 | VERIFIED |
| ≥20, excl. Bakery/Dairy/Frozen/Sweets | 854 | Rs 72,05,507 | 129 | VERIFIED |

The perishable exclusion removes 10 SKUs and Rs 0.97 L. **"Shelf-stable" is doing no work
in this finding** — drop the word.

**89 of the 864 sold on 100 or more of the year's 354 trading days and are empty today,
carrying Rs 19,74,398.** VERIFIED. These are not long-tail lines.

### It is a reordering failure, not a delisting decision

This is the most persuasive number in the note and the brief did not have it:

| | SKUs | Trailing sales | Avg days since last purchase | Status |
|---|---|---|---|---|
| **Purchased within the last 12 months** | **809 (94%)** | **Rs 69,15,436** | **190** | VERIFIED |
| Last purchased over 12 months ago | 53 | Rs 3,83,836 | 516 | VERIFIED |
| Never purchased | 2 | Rs 3,000 | — | VERIFIED |

> `LEFT JOIN (SELECT pd.ProductID, MAX(CAST(ph.VoucherDate AS date)) last_pur FROM PurchaseDetail pd JOIN PurchaseHeader ph ON ph.SerialNumber=pd.SerialNumber WHERE ISNULL(pd.IsDeleted,0)=0 AND ISNULL(ph.IsDeleted,0)=0 GROUP BY pd.ProductID) lp ON lp.ProductID=b.ProductID`

ARY was actively buying 94% of these lines a few months ago and simply stopped. Nobody
decided to drop them.

### Where it concentrates

| Group | SKUs empty | Trailing sales | Avg days out | Status |
|---|---|---|---|---|
| **Confectionery** | **292** | **Rs 23,91,170** | 142 | VERIFIED |
| **Personal Care** | **171** | **Rs 10,20,582** | 122 | VERIFIED |
| Drinks | 44 | Rs 4,52,266 | 125 | VERIFIED |
| General Items | 52 | Rs 3,94,169 | 143 | VERIFIED |
| Academy Dress | 2 | Rs 3,79,860 | 40 | VERIFIED |
| Dry Fruits | 15 | Rs 3,55,970 | 151 | VERIFIED |
| Footwear | 7 | Rs 3,42,062 | 98 | VERIFIED |
| Toiletories | 36 | Rs 1,89,804 | 141 | VERIFIED |

**Confectionery and Personal Care alone are 463 of the 864 SKUs and 46.7% of the value.**
Two groups, one buyer's beat each — this is a small, tractable list, not a store-wide
overhaul.

### Named lines, so the finding is not abstract

Sold on ≥60 separate days, empty for ≥21 days, ordered by trailing value:

| Line | Group | Trailing | Selling days | Days off shelf | Last purchased | Status |
|---|---|---|---|---|---|---|
| White Suit 40 Cm | Academy Dress | Rs 2,94,800 | 110 | 23 | 2026-02-12 | VERIFIED |
| Campus Sports Shoes 06 Art-677 | Footwear | Rs 2,53,710 | 98 | 40 | 2026-02-08 | VERIFIED |
| **Lays Magic Masala 55 Gm** | Confectionery | Rs 1,39,840 | **177** | **109** | 2026-02-24 | VERIFIED |
| Sunil Badam 250 Gm | Dry Fruits | Rs 98,560 | 118 | 26 | 2026-07-12 | VERIFIED |
| **Jivo Wheatgrass Pet 250 Ml** | Soft Drinks | Rs 76,755 | 64 | **204** | 2025-10-23 | VERIFIED |
| Aashirvaad Atta 10 Kg | Atta & Flours | Rs 72,275 | 109 | 57 | 2026-05-18 | VERIFIED |
| Lays Chilli Lemon 55 Gm | Confectionery | Rs 67,540 | 169 | 162 | 2026-02-24 | VERIFIED |
| **Jivo Mustard Oil 1 Ltr Pouch** | Oil & Ghee | Rs 66,500 | 146 | **144** | 2025-08-29 | VERIFIED |
| Jivo Pista 250 Gm Salted | Dry Fruits | Rs 64,750 | 100 | 91 | 2026-01-06 | VERIFIED |
| Kurkure Sizzlin Hot 78 Gm | Confectionery | Rs 44,720 | 179 | 52 | 2026-06-24 | VERIFIED |

**Two of JIVO's own products are on that list.** Jivo Mustard Oil 1 L pouch sold on 146 days
of the year, has been off the shelf 144 days, and was last bought on 2025-08-29 — a year
ago, from a group company.

## Nobody owns replenishment — it is directly observable

The root cause does not have to be inferred from the outage. It is in the master data:

| | Value | Status |
|---|---|---|
| Rows in `ProductROQMaster` | **1** | VERIFIED |
| SKUs with `ReorderInformation=1 OR ReorderLevel>0` | **1** | VERIFIED |
| Total SKUs | 21,479 | VERIFIED |

> `SELECT (SELECT COUNT(*) FROM ProductROQMaster), (SELECT COUNT(*) FROM ProductMaster), (SELECT COUNT(*) FROM ProductMaster WHERE ReorderInformation=1 OR ReorderLevel>0)`

**One SKU in 21,479 has a reorder point.** FusionERP8 has the field. ARY has never used it.
There is no system that could tell anyone the shelf is empty, and no person whose job it is
to look. That is the finding — the 51.28% is its symptom.

## The natural experiment, rebuilt

The brief's causal evidence was: *"on the 42 best days 8 of the top-10 snack SKUs were on
shelf and the shop sold Rs 12.55 of snacks per bill; on the 45 worst days 0-4 were available
and it sold Rs 9.47. Footfall IDENTICAL — 998 vs 997 bills/day."*

The arithmetic reproduces. The claim does not. Top-10 snacks by 12m value in
`ProductGroupID=113, SubGroupID IN (746,547)` are `00BF, 00BD, 00BM, 00BS, 00BC, 00BN, 00BE,
0FYL, 00BJ, 0FYJ` (VERIFIED). Banding the 354 trading days by how many of those ten rang a
sale that day:

| Top-10 selling that day | Days | Bills/day | Snack Rs/bill | Status |
|---|---|---|---|---|
| 1 | 5 | 1,137.6 | 9.77 | VERIFIED |
| 2 | 6 | 1,009.3 | 8.85 | VERIFIED |
| 3 | 10 | 946.7 | 10.78 | VERIFIED |
| **4** | **24** | **987.5** | **9.47** | VERIFIED |
| 5 | 41 | 1,013.3 | 10.45 | VERIFIED |
| 6 | 105 | 990.2 | 10.88 | VERIFIED |
| 7 | 119 | 1,061.1 | 11.49 | VERIFIED |
| **8** | **42** | **1,265.8** | **12.55** | VERIFIED |
| 9 | 2 | 1,258.0 | 11.12 | VERIFIED |

**The published sentence stitches together three different day-sets.** Rs 12.55 comes from
the 42 days at exactly 8 (footfall **1,265.8**/day). Rs 9.47 comes from the 24 days at
exactly 4 (footfall 987.5/day). The "998" is the mean of the whole 0–4 band, which is 45
days and rings Rs 9.70/bill. **The 42 best days carried 28% more footfall than the days they
were compared against, and no definition returns 997.** The "footfall IDENTICAL" claim is
refuted.

### Three defects, in order of size

**1. The classifier is circular.** "In stock" was defined as "the SKU rang a sale that day",
so the availability measure and the outcome are built from the same rows. It measures
*didn't sell*, not *wasn't there*. Nothing in FR8HODBNEW stores stock history, so no direct
correction is available from a single `Stock` snapshot.

**2. The bands are seasonally confounded — by more than the effect being measured.**

| Month | Bills | Snack Rs/bill | Days at n=8 | Days at n≤4 | Status |
|---|---|---|---|---|---|
| 2025-09 | 31,248 | **14.12** | 6 | 3 | VERIFIED |
| 2025-10 | 32,932 | 12.88 | 8 | 0 | VERIFIED |
| 2025-11 | 29,809 | 11.56 | 0 | 3 | VERIFIED |
| 2025-12 | 29,255 | 12.13 | 5 | 11 | VERIFIED |
| 2026-01 | 15,078 | 8.76 | 0 | 0 | VERIFIED |
| 2026-02 | 22,776 | 13.05 | 6 | 0 | VERIFIED |
| 2026-03 | 31,040 | 11.03 | 12 | 7 | VERIFIED |
| 2026-04 | 37,085 | 11.11 | 5 | 0 | VERIFIED |
| 2026-05 | 41,388 | 10.42 | 0 | 0 | VERIFIED |
| 2026-06 | 38,563 | 9.50 | 0 | 5 | VERIFIED |
| 2026-07 | 29,576 | **8.33** | 0 | 12 | VERIFIED |
| 2026-08 | 33,628 | 10.55 | 0 | 4 | VERIFIED |

Monthly snack spend swings Rs 8.33 → Rs 14.12 per bill, a Rs 5.79 range against a Rs 3.08
claimed effect. **31 of the 42 best days sit in the four richest snack months; 23 of the 45
worst days sit in Dec-25 and Jul-26.** See [[Seasonality]].

Removing month effects (bill-weighted deviation of each band from its own month's rate):

| Band | Days | Bills | Raw Rs/bill | Within-month deviation | Status |
|---|---|---|---|---|---|
| n=8 (published "best") | 42 | 53,164 | 12.55 | **−0.02** | VERIFIED |
| n=5–7 | 267 | 274,304 | 11.10 | +0.17 | VERIFIED |
| n≤4 (published "worst") | 45 | 44,910 | 9.70 | **−1.00** | VERIFIED |

**Season-adjusted, the gap is Rs 0.98/bill, not Rs 3.08 — and the good days are not above
their own month at all.** The whole effect is that bare-shelf days run Rs 1.00 below their
month's norm.

**3. Substitution is large, and was never measured.** Splitting the same days into the
top-10 and the rest of the snack shelf, after removing month effects:

| Band | Top-10 deviation | Other snack SKUs' deviation | Status |
|---|---|---|---|
| n=8 | **+0.94** | **−0.97** | VERIFIED |
| n=5–7 | +0.06 | +0.11 | VERIFIED |
| n≤4 | **−1.48** | **+0.48** | VERIFIED |

Between the worst and best bands the top-10 gain Rs 2.42/bill while the rest of the snack
shelf loses Rs 1.45/bill. **About 60% of the "lost" rupees are recovered elsewhere in the
same category.** Raw (unadjusted) the substitution reads 24%. Either way the shopper mostly
buys a different packet, not nothing. VERIFIED.

And the whole-bill average is *higher* on bare-shelf days (Rs 246.69) than on full-shelf
days (Rs 238.65) — VERIFIED, unadjusted. That is mostly seasonal mix, but it is the opposite
of what the brief implies, and it is the reason the snack effect cannot be extrapolated to
the till.

### What the snack shelf is actually worth

| | Value | Status |
|---|---|---|
| 12m bills / trading days | 372,378 / 354 | VERIFIED |
| 12m snack sales (group 113, subgroups 746+547) | Rs 41,47,393 | VERIFIED |
| Snack gross margin, purchase-ledger WAC | **19.92%** (Rs 41.43 L rev, Rs 33.18 L COGS) | VERIFIED |
| **Published uplift** | Rs 5.26 L gross / Rs 56,014 GM | REFUTED |
| **Corrected uplift** — 44,910 bare-shelf bills × Rs 0.98 | **~Rs 44,000 gross / ~Rs 8,800 GM** | ESTIMATED (assumes the bare days would have run at their own month's norm) |

**A 92% cut.** The natural experiment is real, directionally right, and far too small to
carry the replenishment case on its own. The case rests on the 864 SKUs and the empty
`ProductROQMaster`, not on this.

## What the whole prize is worth

| | Value | Status |
|---|---|---|
| Trailing sales exposed by the 864 empty regular sellers | Rs 73,02,272 | VERIFIED |
| …of which costable against the purchase ledger (809 SKUs) | Rs 69,15,436 | VERIFIED |
| Gross margin on those 809 lines | **25.80%** | VERIFIED |
| Gross profit at stake if every rupee returned | Rs 17.84 L | VERIFIED (arithmetic on the two rows above) |
| Realistic recovery after ~60% substitution | **Rs 5–9 L of gross profit** | ESTIMATED — substitution measured only on the snack shelf, applied here by assumption |

**No capital is required.** These are lines ARY already lists, already knows how to buy, and
was buying six months ago.

## What this does NOT show

- **`Stock` is a snapshot with no history.** "Days off shelf" is proxied by days since last
  sale. I cannot prove a line was empty for all 128 days rather than emptied last week. The
  94%-purchased-in-12m test and the 5.6%→85.1% recency gradient both point the same way, but
  neither establishes intent, and neither is stock history.
- **Rs 1.44 Cr and Rs 73.02 L are demand *exposed*, not revenue *lost*.** The one place
  substitution could be measured, it ate ~60% of the effect.
- **Do not measure this at the retail warehouses alone.** Shelf-only stock reads 3,211 out
  of stock and 25 of the top 100 — an unposted-transfer artefact, not an empty shelf.
  VERIFIED: Maggi Noodles 48 Gm Masala reads −45 at Ary Pos and −107 at Ary Lite while 2,052
  units sit in Ary Warehouse. Company-wide `SUM(Stock.Quantity)` is the only defensible
  read. See [[Data-Quality-Traps]].
- **The top-100 claim is gone.** On company-wide stock, 16 of the top 100 read zero, and only
  8 have also been quiet ≥21 days — of which Sardar Blazer 30 Cm, Sardar Blazer 48 Cm and
  Nursing Purple Uniform sold on 3–4 days in the entire year. The honest sentence is "a
  handful of top-100 lines, and one that matters: Lays Magic Masala 55 Gm, 177 selling days,
  109 days empty." VERIFIED.
- **Nothing here measures what a shopper bought instead, or walked out without.** No basket
  counterfactual exists in this database — see [[Basket-And-Footfall]] for the only basket
  structure that does.

## Claims deleted from the brief

Each was tested against live data on 2026-08-30 and failed. They survive only in
[[Corrections-Log]] and [[Verify-Pass-2026-08-30]].

| Deleted claim | What is true | Status |
|---|---|---|
| Rs 1.51 Cr behind an empty shelf | Rs 1.44 Cr (4.6% high) | VERIFIED |
| 27 of the top 100 sellers out of stock | 16 raw; 8 genuinely quiet; 3 of those sold on 3–4 days all year | VERIFIED |
| 629 SKUs / Rs 50.13 L of repeat demand | 864 SKUs / Rs 73.02 L — the error runs the *other* way; no threshold yields the published pair | VERIFIED |
| "Footfall IDENTICAL — 998 vs 997 bills/day" | 1,265.8 on the best days vs 987.5 on the compared worst days | VERIFIED |
| "Same traffic, different shelf, 25% less spend" | Three different day-sets, seasonally confounded; season-adjusted gap Rs 0.98/bill | VERIFIED |
| Snack uplift Rs 5.26 L gross / Rs 56,014 GM | ~Rs 44,000 gross / ~Rs 8,800 GM | ESTIMATED |
| Snack gross margin 10.65% | 19.92% on purchase-ledger WAC | VERIFIED |

## See also

- [[Verify-Pass-2026-08-30]] — the corrections log this note is built on; read it before quoting any other figure in this vault
- [[Catalogue-Shape]] — why adding SKUs to a catalogue with 51% of its working range empty makes this worse, not better
- [[Ten-Moves]] — reorder points on the 864 is move A1, and every category-add stays invalid until it holds a quarter
- [[Data-Quality-Traps]] — the unposted-transfer artefact that inflates any warehouse-level stock read, and the category tree that cannot answer "do we carry this"
- [[Seasonality]] — the Rs 8.33–14.12 monthly snack swing that swamped the natural experiment
- [[Basket-And-Footfall]] — the fresh basket breaks as a set; the same logic applies to a bare snack shelf
- [[Open-Questions]] — question 1, "who owns replenishment", is the only one that has to be answered by a human
