---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high
system: ARY / FusionERP8
---

# Institutional — one NGO earns nothing; the campus accounts out-earn the counter

"Institutional" is not one channel. **Hunger Heroes, a Delhi NGO, turns Rs 63.90 lakh at
1.22% gross margin. The ten campus institution accounts turn Rs 51.25 lakh, and the
Rs 36.77 lakh of that which can be costed earns 28.23% — above the retail counter's
24.53%.** The earlier versions of this note collapsed the two and told
the reader to drop both; that was wrong. This replaces the 2026-08-29 note and the first
2026-08-30 rewrite in full. See [[Verify-Pass-2026-08-30]], [[Duplicate-Bill]].

## The finding, in one table

12 months to 2026-08-30, cost from the **purchase ledger** (`PurchaseDetail.PurchaseCost`,
quantity-weighted per SKU over the same window) — not from `ProductChildMaster`, which is
stale and biased high ([[Data-Quality-Traps]]).

A margin can only be struck on revenue that has a purchase-ledger cost. **That "costable"
share differs by channel, so the two revenue columns are not the same thing and must not be
added across rows.**

| Channel | Bills (costable) | Billed | Costable rev | Cover | COGS | Gross profit | GM% | Status |
|---|---|---|---|---|---|---|---|---|
| Walk-in retail (`00001`) | 361,017 (315,119) | Rs 566.06 L | Rs 479.24 L | 84.7% | Rs 361.66 L | **Rs 117.58 L** | **24.53%** | VERIFIED |
| Other named accounts | 12,428 (11,411) | Rs 124.33 L | Rs 87.70 L | 70.5% | Rs 62.19 L | Rs 25.51 L | 29.09% | VERIFIED |
| *— of which 10 campus institutions* | *4,207* | *Rs 51.25 L* | *Rs 36.77 L* | *71.7%* | *Rs 26.39 L* | ***Rs 10.38 L*** | ***28.23%*** | VERIFIED |
| **Hunger Heroes (`002CM`)** | **11 real + 1 duplicate** | **Rs 63.90 L** | **Rs 63.90 L** | 100% | **Rs 63.12 L** | **Rs 0.78 L** | **1.22%** | VERIFIED |
| Katebaa Rural Services (`00240`) | 4 | Rs 8.00 L | Rs 8.00 L | 100% | Rs 8.04 L | **−Rs 0.04 L** | **−0.53%** | VERIFIED |

> `WITH pur AS (SELECT pd.ProductID, SUM(pd.Quantity*pd.PurchaseCost)/NULLIF(SUM(pd.Quantity),0) wac FROM PurchaseDetail pd JOIN PurchaseHeader ph ON ph.SerialNumber=pd.SerialNumber WHERE ph.VoucherDate>='2025-08-31' AND ph.VoucherDate<'2026-08-31' GROUP BY pd.ProductID HAVING SUM(pd.Quantity)>0) SELECT <channel>, COUNT(DISTINCT h.SerialNumber), COUNT(DISTINCT CASE WHEN pur.wac IS NOT NULL THEN h.SerialNumber END), SUM(d.Quantity*d.SaleRate), SUM(CASE WHEN pur.wac IS NOT NULL THEN d.Quantity*d.SaleRate END), SUM(d.Quantity*pur.wac) FROM SaleHeader h JOIN SaleDetail d ON d.SerialNumber=h.SerialNumber LEFT JOIN pur ON pur.ProductID=d.ProductID WHERE h.VoucherDate>='2025-08-31' AND h.VoucherDate<'2026-08-31' GROUP BY <channel>`

**The reconciliation.** The four rows are the whole shop: 373,461 bills, Rs 7,68,20,330
billed including the duplicate, Rs 762.29 L excluding it. Costable revenue is Rs 638.84 L.
**Rs 123.45 L — 16.2% of what the shop billed — has no purchase-ledger cost and carries no
margin in this note** (VERIFIED; Rs 86.82 L of it retail, Rs 36.63 L other-named). Hunger
Heroes and Katebaa are costed on 100% of theirs, which makes the row-to-row comparison
generous to them, not harsh.

### On a like-for-like tax basis

Retail `SaleRate` is tax-**inclusive** on 86% of its value (`IncludeInRate=1`); Hunger
Heroes' is tax-**exclusive** on 94%; `PurchaseCost` is tax-exclusive on 95%. Net the GST out
of revenue and the ranking does not change:

| Channel | Revenue net of GST | GM% ex-tax | Status |
|---|---|---|---|
| Walk-in retail | Rs 420.44 L | **13.98%** | VERIFIED |
| Other named accounts | Rs 77.23 L | 19.48% | VERIFIED |
| — of which 10 campus institutions | Rs 32.12 L | **17.84%** | VERIFIED |
| Hunger Heroes | Rs 63.48 L | **0.57%** | VERIFIED |
| Katebaa | Rs 8.00 L | −0.53% | VERIFIED |

> same query, revenue as `SUM(d.Quantity*d.SaleRate - CASE WHEN d.IncludeInRate=1 THEN ISNULL(d.TaxAmount,0)+d.TaxAmount1+d.TaxAmount2+d.TaxAmount3+d.TaxAmount4 ELSE 0 END)`

Both bases agree on the two things that matter: **the NGO earns ~zero, and the campus
institution accounts earn more than the counter** (28.23% vs 24.53% gross; 17.84% vs 13.98%
ex-tax).

## Hunger Heroes: a Delhi NGO, and one of its twelve bills is a duplicate

Ledger group *Zomato Debtors* — not a campus body, not the langar, not a boarding kitchen.
It buys at the Basement counter (warehouse 16).

**Twelve bills are on file for the 12 months; only eleven are real.** Serials
`2002751.0001` and `2002752.0001` are identical to the paisa on the same 59 lines, keyed one
minute apart on 2026-05-11 (18:54, 18:56), with no offsetting sale return — see
[[Duplicate-Bill]]. **Every figure in this note excludes `2002752.0001`.** With it the
customer reads Rs 69.81 L / Rs 0.72 L GP / 1.03%; without it Rs 63.90 L / Rs 0.78 L / 1.22%,
eleven bills averaging **Rs 5.81 lakh** (VERIFIED — the query above plus
`AND h.SerialNumber<>2002752.0001`).

| Line | Revenue | COGS | Gross profit | GM% | Status |
|---|---|---|---|---|---|
| Rice 1 Kg | Rs 5,66,664 | Rs 5,58,600 | Rs 8,064 | +1.42% | VERIFIED |
| **Loose Milk** | Rs 5,44,016 | Rs 6,01,998 | **−Rs 57,982** | **−10.66%** | VERIFIED |
| Rice_L | Rs 4,48,800 | Rs 4,42,200 | Rs 6,600 | +1.47% | VERIFIED |
| Atta 1 Kg | Rs 4,26,700 | Rs 4,23,500 | Rs 3,200 | +0.75% | VERIFIED |
| Milk_Z | Rs 3,81,969 | Rs 3,74,037 | Rs 7,932 | +2.08% | VERIFIED |

### The below-cost block is mostly already closed

15 of the 96 SKUs sold below cost over the year — **Rs 13.17 L of revenue losing Rs 92,387**
(ex-duplicate, VERIFIED). But **eight of the fifteen, carrying Rs 74,923 of that loss — 81% —
last transacted on 2026-05-11 and have not sold since**: Loose Milk, Desi Ghee 1 Ltr, Rajdhani
Daliya, Tata Salt, Elaichi Black, Black Pepper Sabat, Nutri 1 Kg, Amchur Powder. Only seven
still appear on current bills — Dahi_Z −7,971, Pumpkin_Z −4,632, Mausambi_Z −2,439, Ginger_Z
−1,620, Paneer_Z −439, Golden Apple_Z −324, Mix Dal_L −40 — **Rs 17,464 of live bleed**
(VERIFIED: per-SKU rev/COGS/`MAX(h.VoucherDate)` off the WAC query, `WHERE cogs>rev`, split
on `lastsale>='2026-06-01'`).

**The prize from repricing is ~Rs 0.17 lakh a year, not Rs 1.08 lakh.** See
[[Below-Cost-Leak]].

### The loose-milk loss stopped on its own

Loose Milk bought 17,739.1 L @ Rs 52.01/L; sold 11,574.8 L @ **Rs 47.00 flat**, of which
**100% went to Hunger Heroes and nought to campus residents**, losing Rs 57,982 (VERIFIED).

> `SELECT c.CustomerName, SUM(d.Quantity), SUM(d.Quantity*d.SaleRate) FROM SaleHeader h JOIN SaleDetail d ON d.SerialNumber=h.SerialNumber JOIN ProductMaster p ON p.ProductID=d.ProductID LEFT JOIN CustomerMaster c ON c.CustomerID=h.CustomerID WHERE p.ProductName='Loose Milk' AND h.VoucherDate>='2025-08-31' AND h.VoucherDate<'2026-08-31' GROUP BY c.CustomerName` → **one row**.

From June 2026 the milk line moved to `Milk_Z`, bought at Rs 46.02/L against the same
Rs 47.00 sale price — **+2.08%** (8,127 L, VERIFIED). Loose Milk has had no sale since May
2026 while still being bought for the shelf. Nobody recorded that the bleed had stopped.

### The customer is growing, not stopping

Five bills between 2026-06-23 and 2026-08-03 billed **Rs 28.19 L** against Rs 63.90 L for the
whole trailing year (VERIFIED:
`SELECT COUNT(DISTINCT h.SerialNumber), SUM(d.Quantity*d.SaleRate) FROM SaleHeader h JOIN SaleDetail d ON d.SerialNumber=h.SerialNumber WHERE h.CustomerID='002CM' AND h.VoucherDate>='2026-06-01'`).
A quarter at that rate annualises to **~Rs 113 L** (ESTIMATED — straight-line off five
bills). This is a live, accelerating account priced at cost.

## The campus institution accounts

Ten named campus accounts, 12 months. **Every one earns a real margin — 21% to 56%.**

| Account | Bills | Billed | Cover | GM% | Provisions | Status |
|---|---|---|---|---|---|---|
| Akal Academy | 1,934 | Rs 25.97 L | 80.3% | 29.01% | Rs 2.12 L | VERIFIED |
| Kalgidhar Trust (enquiry) | 982 | Rs 9.58 L | 69.2% | 27.15% | Rs 0.52 L | VERIFIED |
| University Students | 220 | Rs 5.16 L | **7.5%** | 41.18% | Rs 0 | VERIFIED |
| Akal Catering Services (Mess) | 152 | Rs 4.26 L | 81.6% | 23.12% | Rs 0.26 L | VERIFIED |
| Akal De-Addiction Ward | 634 | Rs 2.32 L | 92.8% | 24.85% | Rs 0.04 L | VERIFIED |
| Eternal University | 41 | Rs 0.99 L | 91.6% | 28.47% | Rs 0.10 L | VERIFIED |
| Akal Hospital | 60 | Rs 0.78 L | 79.0% | 31.01% | Rs 0.03 L | VERIFIED |
| Akal Nursing College | 41 | Rs 0.77 L | 78.0% | 24.13% | Rs 0.06 L | VERIFIED |
| Gurmat Camp | 28 | Rs 0.73 L | 75.0% | 56.29% | Rs 0 | VERIFIED |
| Apple A Day | 115 | Rs 0.68 L | 86.2% | 21.08% | Rs 0.28 L | VERIFIED |
| **Total** | **4,207** | **Rs 51.25 L** | **71.7%** | **28.23%** | **Rs 3.41 L** | VERIFIED |

**Read the cover column before the GM column.** University Students' 41.18% rests on
Rs 0.39 L of Rs 5.16 L — 7.5% of its revenue — and is the one margin here that is not
reliable. The other nine are costed on 69–93%.

### What they buy — and the classification behind it

| Bucket | `ProductGroupMaster.ProductGroupName` in | Value | Share | Status |
|---|---|---|---|---|
| Apparel, fabric, uniform, home furnishing | Fabrics, Academy Dress, Winter Wear, Unstiched Suits, Womens Wear, Ladies Ethnic Wear, Mens Wear, Night Wear, Under Garment, Kakars, Thermals, Kids Wear, Footwear, Bag & Purses, Accessories, Home Furnishing | **Rs 26.17 L** | **51.1%** | VERIFIED |
| Everything else (snacks, soft drinks, canteen food, fruit, dry fruit, electricals, crockery) | the remaining 50 groups | Rs 21.67 L | 42.3% | VERIFIED |
| **Mess provisions** | Rice & Other Grains, Atta & Other Flours, Pulses, Dairy Products, Vegetable, Oil & Ghee, Edible Oil & Ghee, Tea & Coffee, Spices, Salt & Sugar | **Rs 3.41 L** | **6.6%** | VERIFIED |
| **Total** | | **Rs 51.25 L** | 100% | VERIFIED |

> `SELECT g.ProductGroupName, SUM(d.Quantity*d.SaleRate) FROM SaleHeader h JOIN SaleDetail d ON d.SerialNumber=h.SerialNumber JOIN ProductMaster p ON p.ProductID=d.ProductID LEFT JOIN ProductGroupMaster g ON g.ProductGroupID=p.ProductGroupID WHERE h.CustomerID IN ('00003','00004','0029M','0000A','001JH','00007','00009','0006D','0016L','002BE') AND h.VoucherDate>='2025-08-31' AND h.VoucherDate<'2026-08-31' GROUP BY g.ProductGroupName` — the buckets are that result classified by hand. The previous version published Rs 25.52 L / Rs 19.56 L / Rs 6.17 L on a basket it never printed and that does not reproduce.

**Provisions are a small share, not nil — 6.6%, unevenly spread.** Akal Academy alone buys
Rs 2.12 L of them, plus Rs 1.30 L of Fruits and Rs 1.16 L of Oil & Ghee (VERIFIED).
University Students and Gurmat Camp buy none.

**Rs 19.95 lakh — 38.9% — rings at the Ary Clothing counter** (warehouse 11) and Rs 2.14 L at
Fruits & Vegetables (warehouse 18), VERIFIED. The verify pass reported Rs 15.06 L on a
narrower account set.

**The campus mess (`0000A`) buys Rs 25,845 of staples in a year — Rs 2,154 a month**
(VERIFIED, the ten groups above: Spices 11,810 + Dairy Products 4,450 + Tea & Coffee 4,199 +
Salt & Sugar 3,100 + Atta 1,310 + Vegetable 586 + Pulses 280 + Rice 70 + Oil & Ghee 40).

**Katebaa Rural Services' Rs 8.00 L is 100% turban fabric** — Fabric Spun White Rs 4,66,609
and Fabric Spun Navy Blue Rs 3,33,459, both at the Ary Clothing counter (VERIFIED). It is
not a second bulk food buyer. See [[Institution-Range]].

## Eternal University's "Rs 2.51 Cr" is not a food wallet ARY can bid for

EU's 17th Annual Report 2024-25 (external, **NOT-CHECKED against FR8HODBNEW**) books
Rs 196.00 L of "mess meal charges" — a transfer charge for **cooked meals**, "consumable
items" being booked separately — and Rs 55.00 L of faculty boarding exactly offset by staff
collections. **Both sides of the old ratio were the wrong thing.** ARY's own EU account is
Rs 99,483.50 in 12 months, of which **Rs 5,809 is edible fats** (3 × Jivo Mustard Oil 5 Ltr
Rs 2,759 + Loose Desi Ghee Rs 2,000 + 1 × Jivo Canola Oil 5 Ltr Cold Press Rs 950 + Minchy's
Kachi Ghani 500 Ml Rs 100) against Rs 19,888 of stoles (K Mark 12,847 + Ss 7,041), Rs 12,250
of kurtis, Rs 10,575 of curtains and Rs 9,584 of trousers and shirts — VERIFIED, per-SKU
`SUM(d.Quantity*d.SaleRate)` for `CustomerID='00007'`.

## The campus sells to ARY as well as buying from it

The four in-house units sit in **Local Creditors – Baru Sahib**. ARY buys from them.

| Unit | Ledger lines | ARY owes (credit) | First | Last | Status |
|---|---|---|---|---|---|
| Akal Modi Khana – Baru Sahib | 9 | Rs 2,48,240 | 2026-06-08 | 2026-08-27 | VERIFIED |
| Akal Dairy – Baru Sahib | 83 | Rs 88,479 | 2026-06-03 | 2026-08-30 | VERIFIED |
| Akal Catering Mess | 64 | Rs 68,066 | 2026-06-03 | 2026-08-30 | VERIFIED |
| Akal Bakery – Baru Sahib | 126 | Rs 67,689 | 2026-06-03 | 2026-08-30 | VERIFIED |
| **Total** | **282** | **Rs 4,72,474** | 2026-06-03 | current | VERIFIED |

The campus runs its own dairy, bakery, provision store and catering mess, and ARY became
their *customer* three months ago. **This says nothing about the size of campus food demand
or who serves it** — the ledger records only what ARY bought.

## The bulk pricing tier serves exactly one customer

61 SKUs carry `_Z` / `_L` bulk suffixes and turned **Rs 36.81 lakh at 2.45% gross margin —
Rs 90,152 of gross profit** (ex-duplicate). Every rupee went to Hunger Heroes: **zero to
walk-in retail, zero to any campus body** (VERIFIED — `GROUP BY h.CustomerID` over
`ProductName LIKE '%\_Z' ESCAPE '\' OR LIKE '%\_L' ESCAPE '\'` returns one row, `002CM`).

## What this note no longer claims

Deleted, not softened; each survives only in [[Corrections-Log]] and
[[Verify-Pass-2026-08-30]].

- **"Institutional earns nothing and should not be grown."** Only the NGO earns nothing; the
  ten campus accounts earn 28.23%, above retail.
- **"Every campus body buys uniform cloth and tuck-shop snacks, not provisions."** Provisions
  are 6.6% of the ten accounts and Rs 2.12 L at Akal Academy alone.
- **"There is no unserved institutional food market here."** The creditor ledger cannot carry
  that; it measures ARY's purchases and nothing else.
- **"Every rupee moved from the counter to this channel destroys about 23 paise."** The
  spread is 23 pp gross / 13 pp ex-tax, and nothing in this database shows the two channels
  compete for the same rupee or the same stock.
- **"It consumes the buying, the counter and the working capital of a Rs 7.68 Cr shop."**
  Never sized: 11 documents against 373,461 bills, with no picking, counter or credit cost
  measured anywhere.
- **"Repricing the 15 below-cost lines recovers Rs 1.08 lakh."** Rs 0.92 L on the
  ex-duplicate year, of which only Rs 0.17 L is still being lost.
- Also gone, from the 2026-08-29 version: **"Rs 2.51 Cr of EU food spend, ARY has 1.1% of
  it"**; **"a Rs 4–5 crore institutional gap"**; **"institutional 7.2% GM vs retail 31.0%"**
  (both `ProductChildMaster` artefacts); **"retail is ~77% saturated with Rs 2.3 Cr of
  headroom"** (rests on the split [[Population]] refutes); **"Hunger Heroes feeds ~300–330
  people on campus"** (it is a Delhi NGO); **"Katebaa is a second bulk food buyer"** (turban
  fabric).

## What this does NOT show

- **Why the NGO is priced at cost.** Nothing in FR8HODBNEW records an agreement, a subsidy
  policy or a Trust instruction. A deliberate charitable price and an unmanaged one look
  identical here. **That is a question for a human** — [[Open-Questions]].
- **Whether the Trust would pay a normal margin.** Never tested; ARY has never quoted one.
- **Any measure of campus food spend, or who else serves it.** ARY's ledger sees only what
  ARY billed and bought.
- **What the Rs 123.45 L of non-costable revenue earns.** 16.2% of what the shop billed has
  no purchase-ledger cost in this window; its margin is unknown, not zero.
- **Costs below the gross line.** No rent account exists (ARY occupies Trust premises free),
  so 1.22% and 28.23% are both before every cost of serving.
- **Whether the duplicate bill was ever corrected.** ARY has no cancellation document and no
  offsetting sale return exists ([[Duplicate-Bill]]).

## The conclusion

**Split the two.** The ten campus institution accounts are Rs 51.25 L at 28.23% gross
(17.84% ex-tax), better than the counter's 24.53% (13.98%). Nothing here argues for dropping
them.

**Hunger Heroes is the problem, and it is growing.** Rs 63.90 L at 1.22% earned Rs 0.78 L
last year and is running at ~Rs 113 L annualised. The decision is a price, and the price is a
human question this database cannot answer. The narrow, costless piece inside it is the
**seven still-live below-cost SKUs — Rs 0.17 lakh a year**; repricing a named credit customer
is a conversation, not a system change.

The alternative use of the same effort — 3,051 out-of-stock retail SKUs ([[Availability]])
— works on a 24.53% gross / 13.98% ex-tax base.

## See also

- [[Duplicate-Bill]] — the Rs 5.91 L double-key on this customer, excluded from every figure here
- [[Availability]] — the alternative use of the same effort
- [[Below-Cost-Leak]] — the seven lines still worth repricing, and the loose-milk history
- [[Verify-Pass-2026-08-30]] — the refutations that made this rewrite necessary
- [[Population]] — why the "Rs 2.3 Cr retail headroom" built on a headcount split is void
- [[Institution-Range]] — where the campus bodies' money actually goes: dastar, patka, uniform
- [[Pricing-Fairness]] — the right answer to "is a Trust shop exploiting a captive market"
- [[Open-Questions]] — question 1 for the Trust: is the NGO price a policy or an oversight
- [[Ten-Moves]] — move 1 has been rewritten
- [[00-ARY-Atlas]] — the index
