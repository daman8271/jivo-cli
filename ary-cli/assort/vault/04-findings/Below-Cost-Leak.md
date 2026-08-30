---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high
system: ARY / FusionERP8
---

# Below-cost leak — Rs 2.40 lakh a year, and three quarters of it never touches the campus

`ary assort leak` still finds real below-cost selling, but the story in the previous version
of this note was wrong in its most quoted line. **Rs 1.79 lakh of the Rs 2.40 lakh goes to two
buyers who are not on the campus at all** — the Delhi NGO of [[Institutional]] and ARY's own
Delhi parent. The campus residue is Rs 0.61 lakh and **every rupee of it is a costing
artefact**, which is the same class of defect [[Data-Quality-Traps]] catalogues and which
[[Verify-Pass-2026-08-30]] found running through this whole vault.

**The milk subsidy reading is deleted.** All 13,605 litres go to the NGO; none reach a
boarding child. See §3.

## 1. What the tool reports today

`ary assort leak`, run live 2026-08-30 on the rebuilt binary (12-month window, min 20 units,
purchase-ledger cost — never the price master):

| Bucket | SKUs | Window loss | Status |
|---|---|---|---|
| Plausible real below-cost selling | 21 | **-Rs 2,10,835.41** | VERIFIED · `ary assort leak` |
| Sale under HALF cost — pricing / pack error | 3 | -Rs 29,175.27 | VERIFIED · same run |
| **Total** | **24** | **-Rs 2,40,010.68** | VERIFIED |

The ten largest lines:

| Product | Group | Units 12m | Purchase cost | Sale rate | Window loss | Status |
|---|---|---|---|---|---|---|
| Am Lower | Mens Wear | 1,510 | Rs 173.26 | Rs 107.60 | **-Rs 99,141.85** | VERIFIED |
| Loose Milk | Mini Meals | 13,605.20 | Rs 52.01 | Rs 47.00 | **-Rs 68,153.05** | VERIFIED |
| Red Label Tea 22 Gm | Tea & Coffee | 75 | Rs 206.44 | Rs 17.33 | -Rs 14,182.67 | VERIFIED |
| Girlish Woolen Pajami | Winter Wear | 46 | Rs 414.29 | Rs 138.43 | -Rs 12,689.52 | VERIFIED |
| Desi Ghee 1 Ltr | Oil & Ghee | 175 | Rs 471.18 | Rs 414.80 | -Rs 9,867.04 | VERIFIED |
| Dahi_Z | Others | 3,114.70 | Rs 73.12 | Rs 69.98 | -Rs 9,792.00 | VERIFIED |
| Rajdhani Daliya 1 Kg | Rice & Other Grains | 3,450 | Rs 37.33 | Rs 35.14 | -Rs 7,576.00 | VERIFIED |
| Pumpkin_Z | Vegetable | 2,400 | Rs 13.56 | Rs 11.33 | -Rs 5,344.00 | VERIFIED |
| Mausambi_Z | Fruits | 894 | Rs 66.29 | Rs 63.20 | -Rs 2,760.30 | VERIFIED |
| Shubh Diwali Diya | Decoratives | 72 | Rs 61.15 | Rs 29.17 | -Rs 2,303.08 | VERIFIED |

Every one of the 24 carries `ConversionFactor 1.000` with matching primary and alternate
units, so none of this is a litres-versus-kilos artefact.

## 2. Who the loss actually goes to — the question nobody had asked

Splitting the same 24 SKUs' units by the customer on the bill:

| Buyer | SKUs | Units | Share of the loss | Status |
|---|---|---|---|---|
| **Hunger Heroes NGO, Delhi (`002CM`)** | 11 | 26,342.80 | **-Rs 1,06,380.08 (44.3%)** | VERIFIED |
| **Jivo Wellness Pvt Ltd - Delhi, the parent (`0000L`)** | 1 | 1,108 | **-Rs 72,747.79 (30.3%)** | VERIFIED |
| Walk-in campus retail (`00001`) | 13 | 1,195.50 | -Rs 56,877.80 (23.7%) | VERIFIED |
| Other named accounts — all on-campus (ARY and canteen staff, Kalgidhar Trust, Akal Academy, Akal Hospital, Eternal University) | 10 | 116 | -Rs 4,005.02 (1.7%) | VERIFIED |

> Query: the `leak` CTE re-run with `SaleDetail` joined to `SaleHeader.CustomerID`; the four
> rows sum to -Rs 2,40,010.69 against the tool's -Rs 2,40,010.68.

**74.6% of the leak is sold off-campus.** That is the headline, and it lines up exactly with
[[Institutional]]: on 12-month purchase-ledger cost the NGO channel turns **Rs 69.81 lakh at
1.03% gross margin** against walk-in campus retail's **24.55%** (VERIFIED; costable revenue
Rs 480.62 L of Rs 567.56 L, 84.7%). Priced on Basement-counter cost alone — the right basis
for that channel, and 100% costable — the NGO earns **Rs 84,582 of gross profit in a year**,
and **the 11 below-cost lines give back Rs 81,562 of it**. The wholesale channel is a
break-even channel because of the lines in this note.

## 3. 🔴 REVERSED — the milk is not a subsidy for boarding children

The previous version of this note said the Rs 47.00 milk price "may well be deliberate…
milk at a subsidised price to a captive population of boarding children." **That is wrong and
it is deleted.**

| Fact | Value | Status |
|---|---|---|
| Loose Milk sold 12m | 13,605.20 L over **7 bills**, all `002CM`, all at the Basement counter | VERIFIED |
| Loose Milk sold to walk-in campus retail, 12m | **0 litres, 0 bills** | VERIFIED |
| Loose Milk sold to walk-in campus retail, **ever** | **0 litres** | VERIFIED |
| The only non-NGO milk bill in the whole database | 5 L to one named individual, 2023-06-17, Rs 45.00 | VERIFIED |
| Milk_Z (the bulk twin) sold 12m | 8,127 L over 5 bills, 100% `002CM` | VERIFIED |

> Query: `SaleDetail` × `SaleHeader` on ProductIDs `07M9` / `0GDA`, grouped by CustomerID,
> both windowed and all-time.

### And the Rs 52.01 cost is itself a two-streams-one-SKU error

`07M9 Loose Milk` is bought on **two separate streams that never meet**:

| Stream | Bought into | 12m volume | Cost | Where it goes | Status |
|---|---|---|---|---|---|
| NGO stream | Basement (WH 16) | 10,800 L | Rs 45.00 → Rs 65.00 | Sold to `002CM` | VERIFIED |
| Campus stream | Ary Warehouse | 6,939.05 L | **Rs 54.20 - Rs 55.00, bought every single month** | Transferred to G Canteen / Apple A Day / Ary Pos and **consumed as a kitchen input - 0 litres ever sold** | VERIFIED |

The tool blends the two into Rs 52.01. The Rs 55 milk is never sold to anybody, so it cannot
lose money on a sale. Costed on the Basement stream alone the milk loss is **-Rs 43,335**, not
-Rs 68,153 (VERIFIED).

### The loss is one transaction, and ARY had already fixed it

Month-matching the NGO's milk against that month's Basement purchase price:

| Month | Litres | Cost that month | Sold at | Gross profit | Status |
|---|---|---|---|---|---|
| 2025-04 | 2,500 | Rs 47.00 | Rs 48.00 | **+Rs 2,500** | VERIFIED |
| 2025-05 · 06 · 08 · 09 · 10 | 2,500 each | Rs 45.00 | Rs 47.00 | **+Rs 5,000 each** | VERIFIED |
| **2026-05** | **7,105.20** | **Rs 61.97** | Rs 47.00 | **-Rs 1,06,362.68** | VERIFIED |

On 2026-05-07 ARY bought 2,800 L at **Rs 65.00**; on 2026-05-11 it invoiced 7,105.20 L to the
NGO at Rs 47.00 across four bills. That single week is the whole milk leak. **It has not
recurred**: Loose Milk has not been sold since 2026-05-11, and from 2026-06-23 the NGO has
been supplied on `0GDA Milk_Z` — 8,127 L bought at Rs 46.02 and sold at Rs 47.00, **+2.08%**
(VERIFIED). Nine months of Rs 8-below-cost milk never happened.

## 4. Which SKUs survive every cost basis

A 12-month purchase WAC prices units sold from old stock at whatever was bought in the
window. An all-time WAC blends three years of price history against a 12-month sale rate.
Neither is right on its own, so all three tests were run and only the intersection kept
(min 20 units):

| Product | Units | Off-campus | 12m WAC | All-time WAC | Month-matched | Status |
|---|---|---|---|---|---|---|
| Loose Milk | 13,605.20 | **100%** | -Rs 68,153 | -Rs 29,773 | -Rs 1,00,920 | VERIFIED |
| Dahi_Z | 3,114.70 | **100%** | -Rs 9,792 | -Rs 4,924 | -Rs 24,977 | VERIFIED |
| Desi Ghee 1 Ltr | 175 | **100%** | -Rs 9,867 | -Rs 6,493 | -Rs 10,112 | VERIFIED |
| Pumpkin_Z | 2,400 | **100%** | -Rs 5,344 | -Rs 1,844 | -Rs 6,560 | VERIFIED |
| Rajdhani Daliya 1 Kg | 3,450 | **100%** | -Rs 7,576 | -Rs 4,701 | -Rs 6,234 | VERIFIED |
| Golden Apple_Z | 630 | **100%** | -Rs 391 | -Rs 6,026 | -Rs 2,516 | VERIFIED |
| Ginger_Z | 480 | **100%** | -Rs 1,796 | -Rs 907 | -Rs 1,916 | VERIFIED |
| Mix Dal_L | 236 | **100%** | -Rs 40 | -Rs 40 | -Rs 89 | VERIFIED |
| Red Label Tea 22 Gm | 75 | 0% | -Rs 14,183 | -Rs 14,183 | -Rs 6,286 | VERIFIED |
| Shubh Diwali Diya | 72 | 0% | -Rs 2,303 | -Rs 2,438 | -Rs 138 | VERIFIED |
| **10 SKUs** | | **8 of 10** | **-Rs 1,19,445** | **-Rs 71,329** | **-Rs 1,59,748** | VERIFIED |

All three columns cost Loose Milk on the blended two-stream price of §3, so all three
overstate it; on the Basement stream alone its month-matched figure is **-Rs 78,863**
(VERIFIED). Every other row is single-stream — the ten `_Z` bulk SKUs are bought into
Basement and nowhere else — so no other line carries that error.

**The defensible size of the leak is Rs 0.71-1.60 lakh a year, not Rs 2.75 lakh, and eight of
the ten SKUs sell only to the Delhi NGO.** The two that reach campus are both proven
pack-mixing errors (§5).

The reverse test matters as much. Costing everything on an all-time WAC throws up 55 SKUs and
-Rs 2.16 lakh, led by fresh produce — Potato -Rs 34,319, Onion -Rs 14,037, Garlic -Rs 5,666,
Cherry -Rs 4,923. **Every one of those is positive when the month is matched**: Potato
**+Rs 25,839**, Onion **+Rs 32,466**, Garlic +Rs 5,156, Cherry +Rs 1,828 (VERIFIED). A
commodity whose price moves cannot be tested against a three-year average. Do not open a
produce investigation on that list.

## 5. The campus residue is a catalogue problem, not a pricing one

All 13 campus lines, ranked. "Campus loss" apportions the tool's own SKU-level per-unit gap
to the units that went to a campus buyer — it is **not** the margin those buyers were actually
charged, which is the point of the Am Lower worked example below. The last two columns show
how many distinct cost/MRP pairs the price master holds under that one ProductID:

| Product | Campus loss | Price-master children | Their cost range | Status |
|---|---|---|---|---|
| Am Lower | -Rs 26,394 | **52** | Rs 56.17 – Rs 340.00 | VERIFIED |
| Red Label Tea 22 Gm | -Rs 14,183 | 4 | Rs 8.14 – Rs 454.92 | VERIFIED |
| Girlish Woolen Pajami | -Rs 12,690 | 21 | Rs 48.00 – Rs 414.29 | VERIFIED |
| Shubh Diwali Diya | -Rs 2,303 | 14 | Rs 7.50 – Rs 600.00 | VERIFIED |
| At Fabric Kurta Pajama | -Rs 2,130 | 16 | Rs 55.00 – Rs 300.00 | VERIFIED |
| Harish Hand Towel 14 X 21 | -Rs 1,260 | 4 | Rs 22.00 – Rs 110.00 | VERIFIED |
| Sz Candles | -Rs 755 | 47 | Rs 9.00 – Rs 250.00 | VERIFIED |
| Knife 12 | -Rs 535 | 22 | Rs 5.00 – Rs 60.00 | VERIFIED |
| Scissor 5604 | -Rs 187 | 29 | Rs 7.68 – Rs 170.00 | VERIFIED |
| Shakkar 500 Gm | -Rs 170 | 8 | Rs 22.00 – Rs 60.00 | VERIFIED |
| Rk Container | -Rs 126 | **95** | Rs 1.20 – Rs 350.00 | VERIFIED |
| Shyam Crown. | -Rs 85 | 7 | Rs 6.00 – Rs 45.72 | VERIFIED |
| Sbe Party Popper | -Rs 64 | 13 | Rs 18.00 – Rs 57.14 | VERIFIED |
| **Total** | **-Rs 60,883** | | | VERIFIED |

**13 of 13 are a single ProductID standing in for many physically different goods.** Two
worked examples, from the purchase ledger:

- **Red Label Tea 22 Gm** was bought 30 units at **Rs 8.14** (Sep-2025, the real sachet) and
  24 units at **Rs 453.69 / Rs 454.92** (Sep-2025, a case keyed as pieces). It sells between
  **Rs 10 and Rs 560**. One SKU, two pack sizes, and the "average" is neither. VERIFIED.
- **Shubh Diwali Diya** was bought on one voucher, 2025-09-19, at **Rs 600.00, Rs 60.00 and
  Rs 7.50** simultaneously. VERIFIED.

**Am Lower is not the biggest leak in the business, and there is no price to correct.**
Three independent facts kill it:

1. **1,108 of its 1,510 units (73%) went to `0000L Jivo Wellness Pvt Ltd - Delhi`** — ARY's own
   parent — on 4 bills at **Rs 63.25** each. Strip that intra-group clearance and the 402
   units sold on campus went out at **Rs 229.83** against a Rs 173.26 cost, a **+24.6%**
   margin, right on the retail norm. VERIFIED.
2. **The window is wrong.** 295 units were bought in the 12 months; 1,510 were sold, mostly
   from 2023 lots that cost Rs 65-128. On the all-time purchase WAC of **Rs 102.64** the SKU
   makes **+Rs 7,491**. VERIFIED.
3. **The SKU is 52 different garments.** Its price-master children run Rs 56.17/MRP 80 to
   Rs 340/MRP 499, and a single 2025-08-29 voucher bought at Rs 340, Rs 290 and Rs 220 at
   once. VERIFIED.

**9 of the 13 campus lines are outright profitable on an all-time cost basis** — Am Lower
+Rs 7,491, Rk Container +Rs 8,955, Sz Candles +Rs 5,581, Scissor 5604 +Rs 1,674, Knife 12
+Rs 1,659, Sbe Party Popper +Rs 1,648, Girlish Woolen Pajami +Rs 1,038, Harish Hand Towel
+Rs 972, Shakkar 500 Gm +Rs 317 (VERIFIED). The four that stay negative total **-Rs 18,668**,
and their two largest lines are the two pack-mixers just shown. **There is no evidence that ARY
sells anything to a campus resident below cost**, which is the conclusion [[Pricing-Fairness]]
reaches from the MRP side, by a completely different route.

## 6. Why no report at ARY could ever have caught this — this part survives

`ary assort leak` puts the price master's cost beside the real purchase cost. The master is
wrong in one direction, systematically:

| Test | Result | Status |
|---|---|---|
| SKUs with both a purchase ledger and a price-master row | 10,641 | VERIFIED |
| …master cost more than 5% **ABOVE** the real all-time WAC | **4,644 (43.6%)** | VERIFIED |
| …master cost more than 5% **BELOW** it | **33 (0.3%)** | VERIFIED |
| `ProductMaster.StandardCostPrice` populated | **41 of 21,479 SKUs** | VERIFIED |

> Query: `MAX(ProductChildMaster.PurchaseCost)` per ProductID against
> `SUM(Quantity*PurchaseCost)/SUM(Quantity)` over the whole `PurchaseDetail` ledger.

The mechanism is now known, and it is not corruption: **`ProductChildMaster` holds one row per
price revision**, so `MAX(PurchaseCost)` returns the dearest cost ever recorded for that code
— Loose Milk 20 children from Rs 0.01 to Rs 65.00, Am Lower 52 from Rs 56.17 to Rs 340.00. Any
margin report built on it compares today's selling price against the worst cost in the SKU's
history. **The purchase ledger is the only trustworthy cost source.** That conclusion, and the
instruction to re-derive every category margin from `PurchaseDetail`, both stand — see
[[Data-Quality-Traps]].

## What this does NOT show

- **It does not show money leaving the campus shop.** The three-basis survivors are Rs 0.71-1.60
  lakh, 8 of 10 sell only to the Delhi NGO, and the campus residue dissolves under §5. This is
  a **wholesale pricing** finding, not a retail one.
- **Neither cost basis is the accounting truth.** `ClosingStock` has 0 rows — no year has ever
  been closed at ARY — so there is no valuation to reconcile against. Everything here is
  ledger arithmetic, and the spread between the three bases (Rs 0.71 L to Rs 1.60 L on the same
  ten SKUs) is the honest error bar.
- **Multi-pack SKUs make per-unit costing unmeasurable, not necessarily loss-making.** Red Label
  Tea and Shubh Diwali Diya may be perfectly priced; nothing in FR8HODBNEW can separate the
  sachet from the case, because they share a ProductID.
- **The NGO's margin is quoted before tax.** A parallel lane reports Hunger Heroes at **-0.39%**
  on a like-for-like tax basis rather than the +1.03% here. NOT-CHECKED — not re-derived in this
  note. If it holds, the wholesale channel is loss-making before these SKUs are counted.
- **The Delhi-parent channel has no measurable margin.** Only 9.8% of its Rs 11.42 lakh of
  12-month revenue is costable from a 12-month purchase; the -Rs 72,748 above is Am Lower alone,
  and even that is contested by §5. Do not quote a gross margin for `0000L`.
- **`ary assort leak` is unchanged and still points at the right rows** — but its single
  12-month WAC is not a verdict. Read the channel and the price-master children before acting
  on any line it prints.

## See also

- [[Institutional]] — the NGO channel that owns 44% of this leak, at 1.03% gross margin
- [[Pricing-Fairness]] — reaches "ARY does not overcharge campus residents" from the MRP side;
  §5 here is the cost-side half of the same answer, and it deletes the milk-subsidy corollary
- [[Data-Quality-Traps]] — the price master is high on 4,644 SKUs and low on 33; one ProductID
  holding 52 garments belongs on that list
- [[Verify-Pass-2026-08-30]] — why the milk framing, the Rs 2.75 lakh figure and the "largest
  single leak" claim all had to be re-tested
- [[Availability]] — the far larger money question: half the working range is empty, and a
  price on an empty shelf earns nothing either way
- [[Corrections-Log]] — where the deleted claims are kept
