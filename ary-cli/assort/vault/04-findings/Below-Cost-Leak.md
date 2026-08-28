---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Below-cost leak — Rs 2.75 lakh a year going out the door NOW

**The only finding in this vault that is losing money today.** 27 SKUs sold below what ARY
paid for them, costed off the purchase ledger rather than the price master — which is exactly
why nobody had caught it.

`ary assort leak` was built to make this repeatable.

## The finding

This is the most immediately actionable finding in the entire exercise, and it is verified
on both sides of the ledger.

### The numbers

12 months to 21-Aug-2026, from `PurchaseDetail` and `SaleDetail`:

| | Loose Milk | Milk_Z (bulk twin) |
|---|---|---|
| Litres **bought** | 20,311 | 8,127 |
| **Average purchase cost** | **₹54.78/L** | ₹46.02/L |
| Litres **sold** | 16,105 | 8,127 |
| **Sale rate charged** | **₹47.00/L flat** — min ₹47, max ₹47 | ₹47.00 flat |
| Revenue | ₹7,56,944 | ₹3,81,969 |
| Purchase cost | ₹10,39,029 | ₹3,74,037 |
| **Result** | **−₹7.78/L · ≈ −₹1.25 lakh a year** | +₹0.98/L, essentially break-even |

The selling price has **zero variance across every single transaction** — 16,105 litres all
at exactly ₹47.00. It is a hard-coded price that nobody has revisited.

### The cause: the purchase cost rose 22% and the price never moved

Monthly average purchase cost for loose milk:

| Month | ₹/L | Month | ₹/L |
|---|---|---|---|
| 2025-04 | 46.00 | 2025-11 | 54.84 |
| 2025-05 | 45.00 | 2025-12 | 55.00 |
| 2025-06 | 45.00 | 2026-01 | 55.00 |
| 2025-07 | 55.00 | 2026-02 | 55.00 |
| 2025-08 | 51.67 | 2026-03 | 55.00 |
| 2025-09 | 45.00 | 2026-05 | 54.71 |
| 2025-10 | 50.00 | **2026-08** | **55.00** |

Cost went from **₹45 to a settled ₹55** — a 22% rise, held steady since December 2025.
**The retail price has been ₹47.00 throughout.** ARY has been selling milk at ₹8 below cost
for at least nine months.

### Why it was invisible

- `ProductChildMaster` still carries the **old** figures — cost ₹38.83, price ₹52.41 — so
  every margin report built from the price master shows loose milk at a healthy **+35%**.
  The real cost only appears on the purchase documents. **This is exactly why §25's
  category margins carry a medium-confidence caveat.**
- The loss is buried inside "Mini Meals", which is where Loose Milk is filed (§22).
- At ₹1.25 lakh a year it is 0.17% of revenue — invisible in a P&L, and precisely the kind
  of thing only a per-SKU cost-versus-price check finds.

### What to do, and the one judgement call

Mechanically the fix is a price revision to about ₹58-60/L. **But the decision is not purely
commercial**: milk at a subsidised price to a captive population of boarding children, at a
charitable trust's shop, may well be deliberate. Nobody in the data can say.

**So this is reported, not recommended.** Someone at ARY should confirm whether the ₹47 is
policy or neglect. If it is policy, it should be recorded as a subsidy — currently it is
absorbed silently and shows up as a healthy margin in every report. If it is neglect, it has
cost about ₹1.25 lakh and is still running.

**One methodological point worth carrying forward:** `ProductChildMaster` prices can be
badly stale. Any margin figure in this document derived from it (§25 category margins,
§34 tech margins) should be re-checked against `PurchaseDetail` before being acted on. The
purchase ledger is the truth; the price master is a hope.

### The below-cost problem is systematic, not one SKU

Sweeping **every** SKU where the 12-month weighted-average sale rate is below the 12-month
weighted-average purchase cost (units sold > 20):

| Product | Units sold | Purchase cost | Sale rate | Per unit | **12m loss** |
|---|---|---|---|---|---|
| **Am Lower** | 1,512 | ₹197.41 | ₹106.52 | **−₹90.89** | **−₹1,37,432** |
| **Loose Milk** | 16,105 | ₹51.16 | ₹47.00 | −₹4.16 | **−₹66,951** |
| Led Light | 33 | ₹580.50 | ₹105.30 | −₹475.20 | −₹15,682 |
| Red Label Tea 22 g | 75 | ₹206.44 | ₹17.33 | −₹189.10 | −₹14,183 |
| Girlish Woolen Pajami | 46 | ₹414.29 | ₹138.43 | −₹275.86 | −₹12,690 |
| **Dahi_Z** | 3,515 | ₹72.67 | ₹69.82 | −₹2.85 | −₹10,025 |
| **Desi Ghee 1 Ltr** | 200 | ₹458.08 | ₹411.61 | −₹46.47 | −₹9,294 |
| **Rajdhani Daliya 1 Kg** | 4,050 | ₹36.86 | ₹34.87 | −₹1.99 | −₹8,049 |
| Steel Fork | 36 | ₹161.03 | ₹10.00 | −₹151.03 | −₹5,437 |
| **Pumpkin_Z** | 2,600 | ₹13.19 | ₹11.23 | −₹1.96 | −₹5,088 |
| Abro Lower | 394 | ₹279.64 | ₹268.23 | −₹11.41 | −₹4,496 |
| Sauce Pan With Lid | 23 | ₹552.46 | ₹420.00 | −₹132.46 | −₹3,047 |
| **Mausambi_Z** | 974 | ₹65.68 | ₹63.10 | −₹2.58 | −₹2,511 |
| Shubh Diwali Diya | 72 | ₹61.15 | ₹29.17 | −₹31.99 | −₹2,303 |
| + 11 more (Ginger_Z, Paneer_Z, containers, candles, kadai, Jivo Olive Oil…) | | | | | −₹8,600 |

**Total: 27 SKUs, ≈ −₹3.06 lakh a year.** Split by plausibility:

| | SKUs | 12m |
|---|---|---|
| Plausible real below-cost selling | 22 | **−₹2.56 lakh** |
| Sale rate below *half* the cost — likely a pricing or pack error | 5 | −₹0.50 lakh |

**Not a unit-conversion artefact.** `ProductMaster` shows all eight of the worst offenders
at `ConversionFactor 1.000` with matching primary and alternate units (Loose Milk Ltr/Kgs,
the rest Pcs/Pcs). So the extremes — Steel Fork bought at ₹161 and sold at ₹10, Red Label
Tea at ₹206 vs ₹17 — are genuine pricing errors or single-versus-case confusion at the till,
not measurement noise.

**The pattern to notice:** the institutional bulk twins are *all* here — Dahi_Z, Pumpkin_Z,
Mausambi_Z, Ginger_Z, Paneer_Z, Golden Apple_Z, plus Loose Milk and Rajdhani Daliya. Each
loses ₹1-4 per unit on large volume. That is consistent with §25's finding that the
institutional channel runs at 7.2% gross margin: **parts of it are below zero.** Before ARY
chases the ₹4-5 crore mess opportunity (§16), it needs a costed price list — winning more
volume at negative margin makes the business worse.

**Highest-value single action here:** "Am Lower" — 1,512 units at −₹90.89 each,
**−₹1.37 lakh, the largest single leak found anywhere in this exercise.** One SKU, one price
correction.

### ⭐ Why no report at ARY could ever have caught this

`ary assort leak` puts the price master's cost next to the real purchase cost. Every single
leaking SKU shows the same defect:

| Product | Real purchase cost | Sale rate | **Price master says cost is** |
|---|---|---|---|
| Am Lower | ₹197.41 | ₹106.62 | **₹340.00** |
| Loose Milk | ₹51.98 | ₹47.00 | **₹65.00** |
| Red Label Tea 22 g | ₹206.44 | ₹17.33 | **₹454.92** |
| Desi Ghee 1 Ltr | ₹471.18 | ₹414.80 | **₹553.57** |
| Dahi_Z | ₹73.12 | ₹69.98 | **₹90.00** |
| Rajdhani Daliya 1 Kg | ₹37.33 | ₹35.14 | **₹39.00** |
| Pumpkin_Z | ₹13.56 | ₹11.33 | **₹19.00** |
| Shubh Diwali Diya | ₹61.15 | ₹29.17 | **₹600.00** |
| At Fabric Kurta Pajama | ₹144.55 | ₹112.02 | **₹300.00** |

**The master cost is HIGHER than reality on every row.** A margin report built from
`ProductChildMaster` therefore compares the selling price against an inflated cost — and
still shows these as loss-making, or shows a *different* loss than the real one. Either way
the figures are unusable, which is why nobody has acted on them.

**Two conclusions:**
1. **Cost data at ARY is unreliable in both directions.** `StandardCostPrice` is populated
   on 41 of 19,481 SKUs; `ProductChildMaster` is populated but wrong. **The purchase ledger
   is the only trustworthy cost source**, which is what `ary assort leak` uses.
2. **Any margin figure in this document derived from the price master carries this risk** —
   §25's category margins and §34's tech margins included. Re-derive from `PurchaseDetail`
   before acting on a single category.

`ary assort leak` is now a standing command, so this check can be run any week rather than
rediscovered. On the tighter default (min 20 units, weighted properly) it reports **21 SKUs
and −₹2.75 lakh** — the earlier −₹3.06 lakh figure used a slightly looser cost average.
Either way the ranking is the same and **"Am Lower" at −₹1.35 lakh is the single biggest
leak in the business.**

## See also

- [[Data-Quality-Traps]] — the price master shows a HIGHER cost on every leaking row
- [[Institutional]] — the bulk twins are all here; price the mess before chasing its volume
- [[Pricing-Fairness]] — this is also the evidence that ARY does not exploit its market
- [[Ten-Moves]] — move 0
