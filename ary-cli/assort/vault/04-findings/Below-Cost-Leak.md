---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: medium
system: ARY / FusionERP8
---

# Below-cost leak — Rs 1.34 lakh a year net of returns, and nine tenths of it is sold off-campus

`ary assort leak` finds real below-cost selling, but its headline is gross: it nets no sale
returns and counts a bill [[Duplicate-Bill]] flags as double-keyed. Net of both the leak is
**Rs 1.34 lakh, not Rs 2.40 lakh**, and it goes almost entirely to the Delhi NGO of
[[Institutional]] and ARY's own Delhi parent. What reaches a campus buyer is **-Rs 12,465**,
a catalogue defect of the kind [[Data-Quality-Traps]] lists, not a price. The milk-subsidy
reading is deleted (§3).

## 1. What the tool reports, and the two things it leaves out

`ary assort leak`, live 2026-08-30 (12-month window, min 20 units, purchase-ledger cost):
24 SKUs, **-Rs 2,40,010.68** — 21 "plausible" (-Rs 2,10,835.41) and 3 under half cost
(-Rs 29,175.27). VERIFIED · `ary assort leak`.

That is gross. On the tool's own definition (revenue − purchase WAC × units):

| Basis | SKUs | Window loss | Status |
|---|---|---|---|
| As the tool prints it | 24 | -Rs 2,40,010.68 | VERIFIED |
| Net of sale returns | 24 | **-Rs 1,49,315.89** | VERIFIED |
| Net of returns **and** the bill [[Duplicate-Bill]] flags (`2002752.0001`) | 24 | **-Rs 1,33,702.40** | VERIFIED, conditional on that bill being a duplicate |

> Query: the tool's own `pur`/`sal` CTEs with sale movement re-expressed as `SaleDetail UNION ALL
> -SaleReturnDetail`, joined to their headers over the same 12-month window, optionally
> `AND d.SerialNumber <> 2002752.0001`. The same 24 SKUs qualify on every basis.

Returns matter because of one SKU: `SaleReturnDetail` gives back **837 Am Lower units — 831 of
them from the parent `0000L`** — plus 5 units across four other lines, and nothing else.

| Product | Units 12m (net) | Cost | Sale rate | Gross loss | Net loss | Status |
|---|---|---|---|---|---|---|
| **Am Lower** | 1,510 → **673** | Rs 173.26 | Rs 107.60 → **Rs 161.21** | -Rs 99,141.85 | **-Rs 8,107.17** | VERIFIED |
| Loose Milk | 13,605.20 | Rs 52.01 | Rs 47.00 | -Rs 68,153.05 | -Rs 68,153.05 | VERIFIED |
| The other 22 SKUs (largest, Red Label Tea 22 Gm, -Rs 14,182.67) | | | | -Rs 72,715.78 | -Rs 73,055.67 | VERIFIED |

Ex-duplicate, Loose Milk falls to 11,574.80 L and **-Rs 57,982.09** (VERIFIED — the figure
[[Institutional]] already carries), the whole Rs 15,613 gap between the last two basis rows.
All 24 carry `ConversionFactor 1.000`, but **22 of 24 — not all 24 — have `UnitID =
AlternateUnitID`**: **Loose Milk is Ltr / Kgs**, **Mix Dal_L is Kgs / Pcs** (VERIFIED ·
`ProductMaster` joined twice to `UnitMaster`). Milk is the largest line here, so the unit
disclaimer cannot rule out a litres-versus-kilos artefact on it. NOT-CHECKED whether one exists.

## 2. Who the loss actually goes to

The 24 SKUs split by the customer on the bill, on real margin — revenue less the 12-month
purchase WAC on the units taken, net of returns, ex the flagged duplicate:

| Buyer | SKUs | Net units | Net margin | Share | Status |
|---|---|---|---|---|---|
| **Hunger Heroes NGO, Delhi (`002CM`)** | 11 | 22,912.40 | **-Rs 90,766.58** | 67.9% | VERIFIED |
| **Jivo Wellness Pvt Ltd - Delhi, the parent (`0000L`)** | 1 | 277 | **-Rs 30,470.71** | 22.8% | VERIFIED |
| Walk-in campus retail (`00001`) | 13 | 1,186.50 | -Rs 9,830.48 | 7.4% | VERIFIED |
| Other named accounts — all on-campus | 10 | 114 | -Rs 2,634.63 | 2.0% | VERIFIED |
| **Total** | | | **-Rs 1,33,702.40** | | VERIFIED |

> Query: the §1 movement CTE grouped by `SaleHeader.CustomerID` / `SaleReturnHeader.CustomerID`.
> Keeping the duplicate bill moves only the NGO row, to -Rs 1,06,380.07 and -Rs 1,49,315.89.

**90.7% of the leak is sold off-campus** (91.7% with the duplicate bill left in). The previous
version apportioned each SKU's *average* per-unit gap to every buyer's units; that is not a
margin and is deleted — it billed walk-in retail -Rs 56,878 for Am Lower units that sold at
Rs 229, and billed the parent for 831 units it had returned.

On Basement-counter cost — the right basis here, 100% costable — the NGO's **11 leak SKUs lose
Rs 81,562.11 on Rs 14.75 L of revenue while its other 85 SKUs earn +Rs 1,66,144.11 on
Rs 55.06 L (3.02%)**; the channel as a whole earns **+Rs 84,582.00 on Rs 69.81 L = 1.21%**
(VERIFIED · NGO sales costed at each SKU's 12m warehouse-16 WAC, split by leak-list
membership). Removing these lines does **not** rescue the channel — it moves it from 1.21% to
3.02%, against the counter's ~24.5% ([[Institutional]], NOT-CHECKED here). "The wholesale
channel is break-even because of these lines" is deleted.

## 3. 🔴 REVERSED — the milk is not a subsidy for boarding children

The previous version said the Rs 47.00 price "may well be deliberate… milk at a subsidised
price to a captive population of boarding children." **Wrong, and deleted.**

| Fact | Value | Status |
|---|---|---|
| Loose Milk sold 12m | 13,605.20 L over **7 bills**, all `002CM`, all at the Basement counter — of which `2002752.0001` (2,030.40 L) is the flagged duplicate, leaving 11,574.80 L over 6 | VERIFIED · [[Duplicate-Bill]] |
| Sold to walk-in campus retail, 12m and **ever** | **0 litres, 0 bills** | VERIFIED |
| The only non-NGO milk bill in the database | 5 L to one named individual, 2023-06-17, Rs 45.00 | VERIFIED |
| Milk_Z (the bulk twin) sold 12m | 8,127 L over 5 bills, 100% `002CM` | VERIFIED |

> Query: `SaleDetail` × `SaleHeader` on ProductIDs `07M9` / `0GDA`, grouped by CustomerID,
> windowed and all-time.

**The Rs 52.01 cost is a two-streams-one-SKU error.** `07M9` is bought on two streams that
never meet: the **NGO stream** into Basement (WH 16) — 10,800 L in the window at Rs 45 → Rs 65,
12m WAC **Rs 50.19**, all sold to `002CM`; and the **campus stream** into Ary Warehouse
(WH 10) — 6,939.05 L at Rs 54.20 – 55.00 bought every month, transferred to G Canteen / Apple
A Day / Ary Pos and consumed as a kitchen input, **0 L ever sold**. On the Basement stream
alone the milk loss is **-Rs 43,335.08**, and **-Rs 36,867.88** ex-duplicate (VERIFIED ·
`PurchaseDetail` × `PurchaseHeader` on `07M9`, split by `WarehouseID`).

Month-matching the NGO's milk against that month's Basement price, **12-month window only**
(the previous version's table was all-time, summed to 22,105 L against §1's 13,605.20 L, and
omitted two sale months):

| Month | Litres sold | Basement cost that month | Sold at | Gross profit | Status |
|---|---|---|---|---|---|
| 2025-09 | 2,500 | Rs 45.00 | Rs 47.00 | **+Rs 5,000** | VERIFIED |
| 2025-10 | 2,500 | Rs 45.00 | Rs 47.00 | **+Rs 5,000** | VERIFIED |
| 2025-12 | 1,500 | **no Basement purchase that month** | Rs 47.00 | **not matchable** | VERIFIED |
| **2026-05** | **7,105.20** (5,074.80 ex-duplicate) | **Rs 61.97** | Rs 47.00 | **-Rs 1,06,362.68** (-Rs 75,968.21 ex-dup) | VERIFIED |

On 2026-05-07 ARY bought 2,800 L at Rs 65.00 into Basement; on 2026-05-11 it invoiced 7,105.20 L
to the NGO at Rs 47.00 across four bills, two of which are the identical pair [[Duplicate-Bill]]
flags. **It has not recurred**: Loose Milk has not sold since 2026-05-11, and from 2026-06-23 the
NGO is supplied on `0GDA Milk_Z` — 8,127 L bought at Rs 46.02, sold at Rs 47.00, **+2.08%**
(VERIFIED). Nine months of Rs 8-below-cost milk never happened.

## 4. Which SKUs survive every cost basis

A 12-month WAC prices old stock at what was bought in the window; an all-time WAC blends three
years against a 12-month sale rate; month-matching prices each month's sales at that month's
purchases — **but only units sold in a month that also had a purchase**. Only SKUs negative on
all three are kept (min 20 units sold):

| Product | Units 12m | Off-campus | 12m WAC | All-time WAC | Month-matched | Matched units | Status |
|---|---|---|---|---|---|---|---|
| Loose Milk | 13,605.20 | 100% | -Rs 68,153 | -Rs 29,773 | -Rs 1,00,920 | 13,605.20 (100%) | VERIFIED |
| Dahi_Z | 3,114.70 | 100% | -Rs 9,792 | -Rs 4,924 | -Rs 24,977 | 2,694.70 (87%) | VERIFIED |
| Desi Ghee 1 Ltr | 175 | 100% | -Rs 9,867 | -Rs 6,493 | -Rs 10,112 | 150 (86%) | VERIFIED |
| Rajdhani Daliya 1 Kg | 3,450 | 100% | -Rs 7,576 | -Rs 4,701 | -Rs 6,234 | 3,000 (87%) | VERIFIED |
| Pumpkin_Z | 2,400 | 100% | -Rs 5,344 | -Rs 1,844 | -Rs 6,560 | 2,000 (83%) | VERIFIED |
| Golden Apple_Z | 630 | 100% | -Rs 391 | -Rs 6,026 | -Rs 2,516 | 535 (85%) | VERIFIED |
| Ginger_Z | 480 | 100% | -Rs 1,796 | -Rs 907 | -Rs 1,916 | 400 (83%) | VERIFIED |
| Mix Dal_L | 236 | 100% | -Rs 40 | -Rs 40 | -Rs 89 | 187 (79%) | VERIFIED |
| Red Label Tea 22 Gm | 75 | 0% | -Rs 14,183 | -Rs 14,183 | -Rs 6,286 | **32 (43%)** | VERIFIED |
| Shubh Diwali Diya | 72 | 0% | -Rs 2,303 | -Rs 2,438 | -Rs 138 | **3 (4%)** | VERIFIED |
| **10 SKUs** | | **8 of 10** | **-Rs 1,19,445** | **-Rs 71,329** | **-Rs 1,59,748** | | VERIFIED |

> Query: three P&L passes over the same 12-month `SaleDetail` × `SaleHeader` rows — cost from the
> 12m `PurchaseDetail` WAC, the all-time WAC, and a per-`ProductID`×month join to that month's
> purchase WAC. Off-campus = `002CM` + `0000L` units over total units.

**These columns are not an error bar, and the previous version's "Rs 0.71–1.60 lakh" range is
deleted.** The denominators differ: month-matching prices 100% of the milk but only 3 of Shubh
Diwali Diya's 72 units, so that SKU's place on the list is decided by 3 units — the
min-20-units rule is applied to the 12-month sale quantity, never to the matched quantity.
All three also cost Loose Milk on the blended two-stream price of §3; on the Basement stream
alone and **on this note's own 12-month basis the month-matched milk figure is -Rs 96,362.68
on 12,105.20 matched litres** (VERIFIED; -Rs 65,968.21 ex-duplicate). The previous version's
-Rs 78,863 is the *all-time* figure, importing +Rs 17,500 earned on 10,000 L before the window
began. Every other row is single-stream.

The reverse test matters as much. All-time WAC alone throws up **55 SKUs and -Rs 2,16,064.74**,
led by produce — Potato -Rs 34,318.75, Onion -Rs 14,036.53, Garlic -Rs 5,666.02, Cherry
-Rs 4,922.73 — and **every one is positive month-matched**: +Rs 25,839.16, +Rs 32,466.15,
+Rs 5,155.81, +Rs 1,828.03 (VERIFIED, same passes). A commodity whose price moves cannot be
tested against a three-year average. Do not open a produce investigation.

## 5. The campus residue is a catalogue problem, not a pricing one

The 13 leak SKUs that reach a campus buyer, on the margin those buyers were **actually** charged
(revenue less cost, net of returns) — not an apportioned SKU average. The last column counts the
distinct cost/MRP pairs the price master holds under that one ProductID:

| Product | Campus units | 12m WAC | All-time WAC | Price-master children (cost range) | Status |
|---|---|---|---|---|---|
| **Am Lower** | 396 | **+Rs 22,364** | **+Rs 50,328** | **52** (Rs 56.17 – 340.00) | VERIFIED |
| Red Label Tea 22 Gm | 75 | -Rs 14,183 | -Rs 14,183 | 4 (Rs 8.14 – 454.92) | VERIFIED |
| Girlish Woolen Pajami | 46 | -Rs 12,690 | +Rs 1,038 | 21 (Rs 48.00 – 414.29) | VERIFIED |
| Shubh Diwali Diya | 72 | -Rs 2,303 | -Rs 2,438 | 14 (Rs 7.50 – 600.00) | VERIFIED |
| At Fabric Kurta Pajama | 65.50 | -Rs 2,130 | -Rs 1,962 | 16 (Rs 55.00 – 300.00) | VERIFIED |
| Harish Hand Towel 14 X 21 | 36 | -Rs 1,260 | +Rs 972 | 4 (Rs 22.00 – 110.00) | VERIFIED |
| Sz Candles | 199 | -Rs 879 | +Rs 5,426 | 47 (Rs 9.00 – 250.00) | VERIFIED |
| Knife 12, Scissor, Shyam Crown., Shakkar, Rk Container, Sbe Party Popper | 411 | -Rs 1,384 | +Rs 13,860 | 22 / 29 / 7 / 8 / 95 / 13 | VERIFIED |
| **Total** | | **-Rs 12,465** | **+Rs 53,041** | | VERIFIED |

> Query: the §1 movement CTE restricted to `CustomerID NOT IN ('002CM','0000L')`, costed at the
> 12m and all-time `PurchaseDetail` WAC; children as `COUNT(*) FROM ProductChildMaster GROUP BY ProductID`.

**On an all-time cost basis 9 of the 13 are outright profitable** and campus-wide these lines
are **+Rs 53,041**, not a loss. The four still negative total **-Rs 18,668**; the two largest
are pack-mixers, from the purchase ledger:

- **Red Label Tea 22 Gm** — 30 units at **Rs 8.14** (2025-09-04, the real sachet), then 12 at
  **Rs 453.69** and 12 at **Rs 454.92** (a case keyed as pieces); it sells between Rs 10 and
  Rs 560. One SKU, two pack sizes; the "average" is neither. VERIFIED.
- **Shubh Diwali Diya** — one voucher, 2025-09-19 19:04, at **Rs 600.00, Rs 60.00 and Rs 7.50**
  simultaneously. VERIFIED.

**Am Lower is not the biggest leak in the business, and there is no price to correct.**

1. **1,108 of its 1,510 gross units went to `0000L Jivo Wellness Pvt Ltd - Delhi`** on four
   identical 277-unit invoices (2025-09-21, 2025-11-08, 2025-12-25, 2026-03-02; four lines
   each, rates Rs 56.17–122.22) — and **three were reversed in full** by matching 277-unit
   returns at the same rates (2025-09-21 17:16, 36 min after the invoice; 2025-12-24;
   2026-03-02 13:05, 32 min *before* that day's invoice). The parent net kept **277 units** —
   a recurring bill-and-reverse cycle, possibly a stock movement booked as a sale rather than
   four sales. VERIFIED · `SaleDetail`/`SaleReturnDetail`, `0BPC`, `CustomerID='0000L'`.
   **NOT-CHECKED: what the cycle is for.**
2. **The window is wrong.** 295 units were bought in the 12 months; 1,510 sold, mostly from
   2023 lots. On the all-time WAC of **Rs 102.64** the campus units make **+Rs 50,328**
   (VERIFIED). The previous version's "+Rs 7,491" is the SKU total *including the parent's
   units*, printed under a "campus lines" heading.
3. **The SKU is 52 different garments** — one voucher (`14530.0015`, 2025-08-29 13:24) bought
   ChildIDs `001A`/`001C`/`001B` at Rs 340, Rs 290 and Rs 220 in the same minute. VERIFIED.

**There is no evidence that ARY sells anything to a campus resident below cost** — the conclusion [[Pricing-Fairness]] reaches from the MRP side, by a different route.

## 6. Why no report at ARY could ever have caught this

| Test | Result | Status |
|---|---|---|
| SKUs with both a purchase ledger and a price-master row | **10,696** | VERIFIED |
| …master cost more than 5% **ABOVE** the real all-time WAC | **4,678 (43.7%)** | VERIFIED |
| …master cost more than 5% **BELOW** it | **33 (0.3%)** | VERIFIED |
| `ProductMaster.StandardCostPrice` populated | **41 of 21,479 SKUs** | VERIFIED |

> Query: `MAX(ProductChildMaster.PurchaseCost)` per ProductID against
> `SUM(Quantity*PurchaseCost)/SUM(Quantity)` over the whole `PurchaseDetail` ledger. The previous
> version's 10,641 and 4,644 reproduce on neither this query nor five variants of it.

The mechanism is **not** a price-revision history. `ProductChildMaster` children are
**concurrent variants of one code**: one Am Lower voucher bought three ChildIDs at
Rs 340 / 290 / 220 in the same minute, and nine distinct Am Lower ChildIDs sold in 2026-04 alone
(VERIFIED). `MAX(PurchaseCost)` therefore returns the dearest *variant*, not the dearest
historical price — Loose Milk 20 children from Rs 0.01 to Rs 65.00, Am Lower 52 from Rs 56.17 to
Rs 340.00 (VERIFIED). Either way, a margin report built on the master compares today's price
against the worst cost under that code. **The purchase ledger is the only trustworthy cost
source** — see [[Data-Quality-Traps]].

## What this does NOT show

- **It does not show money leaving the campus shop.** On real margin the 13 campus-selling
  lines are -Rs 12,465 on a 12-month WAC and **+Rs 53,041** on an all-time WAC — a wholesale
  finding, not a retail one.
- **The Rs 1.34 lakh rests on a judgement this CLI cannot make:** it excludes `2002752.0001`
  because [[Duplicate-Bill]] flags it. If Accounts rules it real, the leak is Rs 1.49 lakh.
- **Neither cost basis is the accounting truth.** `ClosingStock` has 0 rows — no year has ever
  been closed at ARY. And nothing separates a sachet from a case sharing a ProductID, so
  multi-pack SKUs are unmeasurable per unit, not necessarily loss-making.
- **Two figures carried over, not re-derived here (NOT-CHECKED):** the tax-basis reading of
  Hunger Heroes at **-0.39%** against [[Institutional]]'s +1.03%, and that only 9.8% of the
  parent's Rs 11.42 lakh is costable — so do not quote a margin for `0000L`.
- **`ary assort leak`'s own `--help` still prints the refuted version.** `internal/cli/assort.go`
  lines 486–494 still say milk cost "rose from Rs 45 to Rs 55… across all 16,105 litres", that
  "the price master still carried the old Rs 38.83 cost", that "27 SKUs were leaking about
  Rs 3.06 lakh a year", and that "a subsidised price to a captive population may be deliberate."
  The query is sound; the help text is not.
- **The question that decides the milk is not in the database.** Is the NGO's Rs 47.00
  contractual? Every milk line from 2025-05-23 to 2026-05-11 is Rs 47.00 — unchanged for twelve
  months while Basement cost went Rs 45 → Rs 65 (VERIFIED · `SaleDetail` grouped by `SaleRate`
  on `07M9`). Equally consistent with a fixed-price agreement and with nobody repricing;
  FR8HODBNEW holds no contract. Ask whoever owns the Hunger Heroes account.

## See also

- [[Duplicate-Bill]] — `2002752.0001`: 2,030.40 L of the milk in §3 and Rs 15,613 of the §1 total
- [[Institutional]] — the NGO channel that owns 68% of this leak; already excludes the duplicate
- [[Pricing-Fairness]] — "ARY does not overcharge campus residents", from the MRP side
- [[Data-Quality-Traps]] — the master is high on 4,678 SKUs, low on 33; one ProductID holding 52 garments belongs on that list
- [[Verify-Pass-2026-08-30]] and [[Corrections-Log]] — why these claims were re-tested, and where the deleted ones are kept
- [[Availability]] — the larger money question: a price on an empty shelf earns nothing either way
