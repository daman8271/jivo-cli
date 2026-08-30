---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high
system: ARY / FusionERP8
---

# Institutional — the channel that earns nothing, and should not be grown

ARY's institutional business is **Rs 69.81 lakh of revenue producing Rs 0.72 lakh of gross
profit**. Every campus body ARY bills buys uniform cloth, winter wear and tuck-shop snacks,
not provisions — and the campus's own dairy, bakery and langar store are ARY's **creditors**,
not its customers. This note replaces the version dated 2026-08-29 in full; see
[[Verify-Pass-2026-08-30]] for why, and [[Availability]] for what the shop should do instead.

## The finding, in one table

12 months to 2026-08-30, cost from the **purchase ledger** (`PurchaseDetail.PurchaseCost`,
quantity-weighted per SKU over the same window) — not from `ProductChildMaster`, which is
stale and biased high ([[Data-Quality-Traps]]).

| Channel | Bills | Revenue | COGS | Gross profit | GM% | Status |
|---|---|---|---|---|---|---|
| Walk-in retail (`00001`) | 361,017 | Rs 479.24 L | Rs 361.66 L | **Rs 117.58 L** | **24.53%** | VERIFIED |
| Other named accounts | — | Rs 87.70 L | Rs 62.19 L | Rs 25.51 L | 29.09% | VERIFIED |
| **Hunger Heroes (`002CM`)** | **12** | **Rs 69.81 L** | **Rs 69.10 L** | **Rs 0.72 L** | **1.03%** | VERIFIED |
| Katebaa Rural Services (`00240`) | 4 | Rs 8.00 L | Rs 8.04 L | **−Rs 0.04 L** | **−0.53%** | VERIFIED |

> `WITH pur AS (SELECT pd.ProductID, SUM(pd.Quantity*pd.PurchaseCost)/NULLIF(SUM(pd.Quantity),0) wac FROM PurchaseDetail pd JOIN PurchaseHeader ph ON ph.SerialNumber=pd.SerialNumber WHERE ph.VoucherDate>='2025-08-31' AND ph.VoucherDate<'2026-08-31' AND ISNULL(ph.IsDeleted,0)=0 GROUP BY pd.ProductID HAVING SUM(pd.Quantity)>0) SELECT <channel>, SUM(d.Quantity*d.SaleRate), SUM(d.Quantity*pur.wac) FROM SaleHeader h JOIN SaleDetail d ON d.SerialNumber=h.SerialNumber JOIN pur ON pur.ProductID=d.ProductID WHERE h.VoucherDate>='2025-08-31' AND h.VoucherDate<'2026-08-31' GROUP BY <channel>`

**Hunger Heroes is 14.6% of costable retail revenue and 0.61% of its gross profit.**
Every rupee moved from the retail counter to this channel destroys about 23 paise of margin.

### On a like-for-like tax basis it is worse

Retail `SaleRate` is tax-**inclusive** on 86% of its value (`IncludeInRate=1`); Hunger
Heroes' is tax-**exclusive** on 94% of its value; `PurchaseCost` is tax-exclusive on 95%.
The table above therefore flatters retail and is fair to Hunger Heroes. Net all revenue of
the GST inside it and both fall:

| Channel | Revenue net of GST | GM% ex-tax | Status |
|---|---|---|---|
| Walk-in retail | Rs 420.44 L | **13.98%** | VERIFIED |
| Other named accounts | Rs 77.23 L | 19.48% | VERIFIED |
| Hunger Heroes | Rs 69.40 L | **0.43%** | VERIFIED |
| Katebaa | Rs 8.00 L | −0.53% | VERIFIED |

The margin-truth re-test puts Hunger Heroes at −0.39% and Katebaa at −5.8% on its own tax
normalisation; its working was not recoverable, so the figures above are mine. **Both
derivations agree on the only thing that matters: this channel earns zero.**

## What Hunger Heroes actually is

A **Delhi NGO**, ledger group *Zomato Debtors* — not a campus body, not the langar, not a
boarding kitchen. It buys in **twelve bills a year averaging Rs 5.82 lakh**, all at the
Basement counter (warehouse 16).

| Line | Revenue | COGS | Gross profit | GM% | Status |
|---|---|---|---|---|---|
| Rice 1 Kg | Rs 6,61,864 | Rs 6,51,700 | Rs 10,164 | +1.54% | VERIFIED |
| **Loose Milk** | Rs 6,39,444 | Rs 7,07,597 | **−Rs 68,153** | **−10.66%** | VERIFIED |
| Atta 1 Kg | Rs 4,83,850 | Rs 4,81,250 | Rs 2,600 | +0.54% | VERIFIED |
| Rice_L | Rs 4,48,800 | Rs 4,42,200 | Rs 6,600 | +1.47% | VERIFIED |
| Milk_Z | Rs 3,81,969 | Rs 3,74,037 | Rs 7,932 | +2.08% | VERIFIED |
| Atta_L | Rs 3,39,100 | Rs 3,31,120 | Rs 7,980 | +2.35% | VERIFIED |
| Paneer_Z | Rs 2,21,009 | Rs 2,21,572 | −Rs 563 | −0.25% | VERIFIED |
| Dahi_Z | Rs 2,17,964 | Rs 2,27,756 | −Rs 9,792 | −4.49% | VERIFIED |

**15 of the 96 SKUs are sold below cost** — Rs 15.10 L of revenue losing Rs 1.08 L, against
Rs 54.71 L earning Rs 1.80 L. Full costable coverage: all 96 SKUs price off the purchase
ledger. See [[Below-Cost-Leak]].

### The loose-milk loss is not charity to anyone on campus

| | Value | Status |
|---|---|---|
| Loose Milk bought, 12m | 17,739.1 L @ Rs 52.01/L | VERIFIED |
| Loose Milk sold, 12m | 13,605.2 L @ **Rs 47.00 flat** | VERIFIED |
| Litres to campus residents | **0** | VERIFIED |
| Litres to Hunger Heroes | **13,605.2 (100%)** | VERIFIED |
| Loss on the sold litres | **−Rs 68,153** | VERIFIED |

> `SELECT c.CustomerName, SUM(d.Quantity), SUM(d.Quantity*d.SaleRate) FROM SaleHeader h JOIN SaleDetail d ON d.SerialNumber=h.SerialNumber JOIN ProductMaster p ON p.ProductID=d.ProductID LEFT JOIN CustomerMaster c ON c.CustomerID=h.CustomerID WHERE p.ProductName='Loose Milk' AND h.VoucherDate>='2025-08-31' AND h.VoucherDate<'2026-08-31' GROUP BY c.CustomerName` → **one row**.

**One thing did improve on its own.** From June 2026 the milk line moved to `Milk_Z`, bought
at Rs 46.02/L against the same Rs 47.00 sale price — **+2.08%** (8,127 L, VERIFIED). Loose
Milk has had no sale since May 2026 while still being bought at Rs 54–55/L for the shelf.
The bleed on this customer stopped; nobody recorded that it had.

## The campus bodies do not buy food from ARY

Ten named campus institution accounts (Akal Academy, Kalgidhar Trust, University Students,
Akal Catering Services (Mess), De-Addiction Ward, Eternal University, Akal Hospital, Akal
Nursing College, Gurmat Camp, Apple A Day), 12 months:

| What they bought | Value | Share | Status |
|---|---|---|---|
| Apparel, fabric, uniform, home furnishing | **Rs 25.52 L** | **49.8%** | VERIFIED |
| Everything else (snacks, soft drinks, canteen food, electricals, crockery) | Rs 19.56 L | 38.2% | VERIFIED |
| **Mess provisions** (grain, flour, pulses, dairy, veg, oil, tea, spices, sugar) | **Rs 6.17 L** | **12.0%** | VERIFIED |
| **Total** | **Rs 51.25 L** | 100% | VERIFIED |

**Rs 19.95 lakh of it — 38.9% — rings at the Ary Clothing counter** (warehouse 11), and only
Rs 2.14 L at Fruits & Vegetables. The verify pass reported Rs 15.06 L on a narrower account
set; on the ten accounts above it is Rs 19.95 L.

Read at account level the same thing appears:

| Account | Bills | 12m | Avg bill | Top groups | Provisions | Status |
|---|---|---|---|---|---|---|
| Akal Academy | 1,934 | Rs 25.97 L | Rs 1,343 | Winter Wear 5.27 L, Fabrics 3.36 L, Confectionery 2.06 L, Academy Dress 1.59 L | Rs 2.12 L | VERIFIED |
| Kalgidhar Trust (enquiry) | 982 | Rs 9.58 L | Rs 976 | — | Rs 0.52 L | VERIFIED |
| **Akal Catering Services (Mess)** | 152 | **Rs 4.26 L** | Rs 2,802 | wheatgrass juice 0.68 L, maroon fabric 0.38 L, stitching charges 0.27 L, aprons 0.23 L, softy ice cream 0.21 L | **Rs 0.26 L** | VERIFIED |
| Eternal University | 41 | Rs 0.99 L | Rs 2,426 | Winter Wear 0.21 L, Womens Wear 0.12 L, Home Furnishing 0.11 L, Mens Wear 0.10 L | Rs 0.10 L | VERIFIED |
| Akal Hospital | 60 | Rs 0.78 L | Rs 1,304 | bed sheets, curtains, a room heater | Rs 0.03 L | VERIFIED |

**The campus mess buys Rs 25,845 of staples from ARY in a year — Rs 2,154 a month.** It is
not a provisions customer that could be grown; it is a customer for aprons and cold drinks.

**Katebaa Rural Services' Rs 8.00 L is 100% turban fabric** — Fabric Spun White Rs 4.67 L and
Fabric Spun Navy Blue Rs 3.33 L, both at the Ary Clothing counter (VERIFIED). It is not a
second bulk food buyer. See [[Institution-Range]].

## Eternal University's "Rs 2.51 Cr" is not a food wallet ARY can bid for

From EU's 17th Annual Report 2024-25 (an external document, **NOT-CHECKED against
FR8HODBNEW**), read correctly:

| Line | Amount | What it actually is |
|---|---|---|
| "Mess meal charges" | Rs 196.00 L | a **transfer charge for cooked meals** — the statement books "consumable items" separately, so this is not a provisions spend |
| "Boarding & lodging for EU faculty/staff" | Rs 55.00 L | an expenditure **exactly offset by staff collections** on the income side |

**Both sides of the old ratio were the wrong thing.** And ARY's own EU account is not food
either: Rs 99,483.50 in 12 months, of which **Rs 3,709 is edible oil** (VERIFIED — two Jivo
5-litre packs) against Rs 20,987 of stoles, Rs 12,250 of kurtis, Rs 10,575 of curtains and
Rs 9,584 of trousers and shirts.

## The campus sells to ARY, not the other way round

The four in-house units are in **Local Creditors – Baru Sahib**. ARY buys from them.

| Unit | Ledger lines | ARY owes (credit) | First | Last | Status |
|---|---|---|---|---|---|
| Akal Modi Khana – Baru Sahib | 9 | Rs 2,48,240 | 2026-06-08 | 2026-08-27 | VERIFIED |
| Akal Dairy – Baru Sahib | 83 | Rs 88,479 | 2026-06-03 | 2026-08-30 | VERIFIED |
| Akal Catering Mess | 64 | Rs 68,066 | 2026-06-03 | 2026-08-30 | VERIFIED |
| Akal Bakery – Baru Sahib | 126 | Rs 67,689 | 2026-06-03 | 2026-08-30 | VERIFIED |
| **Total** | **282** | **Rs 4,72,474** | 2026-06-03 | current | VERIFIED |

The campus operates its own dairy, bakery, provision store and catering mess, and ARY became
their *customer* three months ago. There is no unserved institutional food market here.

## The bulk pricing tier already exists and serves exactly one customer

61 SKUs carry `_Z` / `_L` bulk suffixes and turned **Rs 38.34 lakh in 12 months at 2.26%
gross margin**. Every rupee of it went to Hunger Heroes — **zero to walk-in retail, zero to
any campus body** (VERIFIED). The machinery for institutional supply is built, tested, and
producing Rs 86,791 of gross profit a year.

## What this note no longer claims

Deleted outright, not softened — each was refuted, and each survives only in
[[Corrections-Log]] and [[Verify-Pass-2026-08-30]]:

- **"Rs 2.51 Cr of EU food spend, ARY has 1.1% of it."** The number is cooked-meal transfer
  charges plus an offset staff-boarding line.
- **"Rs 4–5 crore institutional gap, larger than the whole shop."** Both methods that
  produced it measured the wrong thing.
- **"Institutional first — Rs 29–36 L of gross profit for a purchase-order conversation."**
  At the measured 1.03% GM, Rs 4 Cr of this revenue would earn Rs 4.1 L, not Rs 29–36 L.
- **"Institutional 7.2% GM vs retail 31.0%."** Both were `ProductChildMaster` artefacts.
  The purchase-ledger figures are 1.03% and 24.53%.
- **"Retail is ~77% saturated with Rs 2.3 Cr of headroom."** Rests on the population split
  that [[Population]] refutes.
- **"At 7.2% ARY is not profiteering on the langar."** ARY does not supply the langar at all.
  For the fairness question the right evidence is [[Pricing-Fairness]].
- **"Hunger Heroes feeds ~300–330 people on campus."** It is a Delhi NGO.
- **"Katebaa is a second bulk food buyer."** It buys turban fabric.
- **"The basket needs zero new SKUs to win the mess."** There is no mess business to win.

## What this does NOT show

- **Why the NGO is priced at cost.** Nothing in FR8HODBNEW records an agreement, a subsidy
  policy or a Trust instruction. A deliberate charitable price and an unmanaged one look
  identical in this database. **That is a question for a human**, and it decides whether the
  right action is to reprice or to stop — see [[Open-Questions]].
- **Whether the Trust would pay a normal margin.** Never tested; ARY has never quoted one.
- **Any measure of campus food spend.** ARY's ledger sees only what ARY billed.
- **Costs below the gross line.** No rent account exists (ARY occupies Trust premises free),
  so even the 1.03% is before every cost of serving the channel — picking, the Basement
  counter, credit and the working capital tied up in Rs 5.8 lakh bills.
- **Whether the 12 bills are the whole relationship.** They are 12 documents; a stopped
  customer and a lumpy one look the same at this cadence.

## The conclusion

**Do not grow this channel. Reprice it or let it go.** The Rs 69.81 lakh it turns is the
most expensive revenue in the business: it consumes the buying, the counter and the working
capital of a Rs 7.68 Cr shop to produce Rs 0.72 lakh. The same effort spent on the
**3,051 retail SKUs that are out of stock today** ([[Availability]]) works on a 24.53% base.

The one defensible institutional action is narrow and costs nothing: **the 15 below-cost
lines to Hunger Heroes** — Rs 15.10 L of revenue losing Rs 1.08 L. Repricing those to zero
margin recovers Rs 1.08 lakh with no new SKU, no capital and no conversation about volume.

## See also

- [[Availability]] — where the same effort earns 24.53% instead of 1.03%
- [[Below-Cost-Leak]] — the 15 lines to reprice, and the loose-milk history behind them
- [[Verify-Pass-2026-08-30]] — the 106 refutations that made this rewrite necessary
- [[Population]] — why the "Rs 2.3 Cr retail headroom" built on a headcount split is void
- [[Institution-Range]] — where the campus bodies' money actually goes: dastar, patka, uniform
- [[Pricing-Fairness]] — the right answer to "is a Trust shop exploiting a captive market"
- [[Open-Questions]] — question 1 for the Trust: is the NGO price a policy or an oversight
- [[Ten-Moves]] — move 1 has been rewritten; institutional supply is no longer on the list
- [[00-ARY-Atlas]] — the index
