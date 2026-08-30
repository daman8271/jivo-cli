---
type: reference
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high
system: ARY / FusionERP8
---

# Data-quality traps — every one of these produced a confident wrong answer, including one in this note

**The most important note in this vault, and the one with the worst track record.** Fourteen
entries below. Thirteen are real traps — a plausible, well-formatted finding that turned out to
be an artefact of a broken field, a broken tool or a broken shell command. The fourteenth was
the old **Trap 3 *in this file***, which was itself a wrong answer about the data and is deleted
here — see [[Verify-Pass-2026-08-30]], which refuted 106 of 293 claims and killed it.

The house rule that survives all of them: **in this database the burden of proof sits on
"missing", never on "covered."** ARY probably has it under a different name — or a different
spelling. The second rule, added 2026-08-30: **a zero is a claim, and a claim needs a second
method.** Every wrong answer below is a zero, an inflation, or an exception list somebody read
as a census.

## Scoreboard

| # | Trap | Status |
|---|---|---|
| 1 | The category tree lies | LIVE — permanent |
| 2 | The diff's AND-match invented 81 "missing" lines | fixed 2026-08-29 |
| 3 | ~~Payment amounts are unusable in every column~~ | **DELETED — the trap was itself false** |
| 4 | The price master is stale and biased HIGH | LIVE — permanent |
| 5 | `probe` was blind to punctuation | fixed 2026-08-30 |
| 6 | `probe` is still blind to ARY's own spelling | **LIVE — no fix exists** |
| 7 | Normalisation made short `probe` terms promiscuous | **LIVE — introduced by the fix** |
| 8 | The shell eats a multi-word `probe` term | **LIVE — the most dangerous of all** |
| 9 | Stock valued `SUM(Qty) × MAX(cost)` | fixed 2026-08-30, 3 sites |
| 10 | `ary audit uncounted` is an exception list read as a census | LIVE — read it correctly |
| 11 | `assort/research/coverage/*.json` is substring garbage | **LIVE — do not use the files** |
| 12 | "Out of stock" measured at the counter | LIVE — measurement choice |
| 13 | `Stock`'s movement buckets are ALL-TIME, not 12-month | LIVE — permanent |
| 14 | "In stock" defined as "it sold that day" is circular | LIVE — method |

## What cannot be answered at all

Re-verified live 2026-08-30 unless marked.

| Limit | Figure | Status | Query |
|---|---|---|---|
| Bills with no identified buyer, 12m | **360,002 of 372,378 = 96.7%** on cash account `00001` | VERIFIED | `SELECT COUNT(*), SUM(CASE WHEN CustomerID='00001'…) FROM SaleHeader WHERE VoucherDate>='2025-09-01' AND <'2026-08-31'` |
| No salesperson on a bill | `SaleHeader` has **no `SalesPersonID` column** — the earlier "99.7% [NONE]" came from a CLI-side label, not a field | VERIFIED | `ary schema columns SaleHeader` → only `UserID`, `AssignUser`, `DeliveredUser`, `PmntUser`, `PrepareUser` |
| No cost price in the master | `StandardCostPrice` set on **41 of 19,494** active SKUs | VERIFIED | `SELECT COUNT(*), SUM(CASE WHEN StandardCostPrice>0…) FROM ProductMaster WHERE IsActive=1` |
| No sale price in the master | `StandardSalePrice` on **562**; `MaxRetailPrice` on **zero** | VERIFIED | same query |
| No ARY↔SAP item map | `ProductCodeSAP` present on every row, **filled on 0** | VERIFIED | same query |
| `ProductMaster.QuantityOnHand` is dead | non-zero on **1** active SKU. On-hand is `Stock.Quantity` | VERIFIED | same query |
| No stock history | `Stock` is a single snapshot. Daily on-hand can be *reconstructed* (Trap 13) but is not stored | VERIFIED | table has no dated row |
| No closed year | `ClosingStock` has 0 rows — the source of the old "22% gross margin" netting artefact | NOT-CHECKED today; VERIFIED in [[Verify-Pass-2026-08-30]] | — |
| Login is `sa` (sysadmin) | read-only comes from the CLI's guard, not the grant | VERIFIED | `ary doctor` |

## ❌ Trap 3 is DELETED — it was itself a wrong answer

**The old Trap 3 said "payment-mode COUNTS are reliable, payment-mode VALUES are not, in any
column. Never quote a rupee split by payment mode."** That is wrong, and it was wrong in the
way this note warns everyone else about: it read a broken aggregate as a broken *field*.

The right column pair is `Amount − ReturnAmount`. It reconciles.

| MOPID | Mode | Tenders | `SUM(Amount)` | `SUM(ReturnAmount)` | **Net = Amount − Return** | **% of value** |
|---|---|---|---|---|---|---|
| 503 | UPI (booked "Paytm") | 213,495 | ₹3,63,75,631 | ₹0 | **₹3,63,75,631** | **47.5%** |
| 1 | Cash | 155,171 | ₹894,22,32,362 | ₹892,12,39,011 | **₹2,09,93,351** | **27.4%** |
| 2 | Credit sale | 10,414 | ₹1,92,50,593 | ₹0 | **₹1,92,50,593** | **25.1%** |
| | **Total** | **379,080** | | | **₹7,66,19,575** | |
| | `SUM(SaleHeader.BillAmount)` | 372,378 bills | | | **₹7,66,19,249** | |
| | **Gap** | | | | **₹326 on ₹7.66 crore** | **0.0004%** |

All VERIFIED, 12-month window 2025-09-01 to 2026-08-31, queried live 2026-08-30. 379,080 tenders
against 372,378 bills — a bill can be split across modes.

### Why the old diagnosis was wrong

The old note diagnosed "MOPID 1 (Cash) carries a scaling or units defect — ₹8,944 crore of
TenderAmount is ₹53,858 per cash transaction." **It is not a scaling defect. It is one bill.**

| Fact | Figure | Status |
|---|---|---|
| Cash `SUM(Amount)`, 12m | ₹894,22,32,362 | VERIFIED |
| …of which **one row**, `SerialNumber 1912106.0015` | **₹890,90,81,003 tendered against a ₹10 bill**, ₹890,90,80,993 returned as change | VERIFIED |
| That single row's share of the cash total | **99.6%** | VERIFIED |
| Cash `SUM(Amount)` excluding it | ₹3,31,51,359 | VERIFIED |

`SELECT TOP 5 p.SerialNumber, p.Amount, p.TenderAmount, p.ReturnAmount, h.BillAmount FROM SalePayment p JOIN SaleHeader h ON h.SerialNumber=p.SerialNumber WHERE p.MOPID=1 AND h.VoucherDate>='2025-09-01' ORDER BY p.Amount DESC`

A cashier keyed a nine-digit number into the *tendered* box on a ₹10 sale and the till dutifully
recorded the change. `Amount` and `TenderAmount` are the cash **presented**; `ReturnAmount` is
the change **given back**. Subtract them and you have what ARY kept. Nothing is broken. UPI and
credit leave `TenderAmount`/`ReturnAmount` at zero because no change is possible on those modes
— which is why the old note's `TenderAmount − ReturnAmount` test attributed 100% of value to
cash "by construction". It was measuring the wrong column, not a wrong database.

> **The corrected rule: payment-mode value IS quotable, from `Amount − ReturnAmount`.**
> UPI is **56.3% of transactions and 47.5% of value**. The digital lane's "42.9% of collections
> value", recorded as *unverifiable*, was simply close and could have been checked.

**Lesson, and it is the same one as Trap 5:** the old trap tested three aggregates, found all
three absurd, and concluded the data was unusable. It never opened the top rows. One `ORDER BY
Amount DESC` would have shown a single fat-finger instead of a systemic defect — and would have
saved a real, quotable figure from being written off. **When an aggregate is 119× reality, look
for one row before you condemn a column.**

## Trap 1 — the category tree lies

Re-tested live 2026-08-30; unchanged.

| Product | Filed under | Status |
|---|---|---|
| Loose Milk | **Mini Meals** | VERIFIED |
| Dahi_Z (curd) | **Others** | VERIFIED |
| Khoya_Z | **Confectionery** | VERIFIED |
| Kala Chana_L | **Atta & Other Flours** | VERIFIED |
| Lobia_L | **Veg Delight** | VERIFIED |
| Loose Desi Ghee | Oil & Ghee | VERIFIED |

The sharpest current example is the **"Frozen" group (ID 128)**, because a whole lane was sized
on it:

| Inside ProductGroupID 128 | SKUs | 12m sales | Status |
|---|---|---|---|
| Paneer (chilled dairy, not frozen) | 4 | **₹5,06,978** | VERIFIED |
| Actual frozen food | 59 | ₹51,904 | VERIFIED |
| **Paneer's share of the group's value** | | **90.7%** | VERIFIED |

`WITH s AS (…12m SaleDetail×SaleHeader by ProductID…) SELECT CASE WHEN p.ProductName LIKE '%Paneer%' THEN 'PANEER' ELSE 'frozen' END, COUNT(DISTINCT p.ProductID), SUM(ISNULL(s.v,0)) FROM ProductMaster p LEFT JOIN s ON s.ProductID=p.ProductID WHERE p.ProductGroupID=128 GROUP BY …`

**Any "frozen" number that does not strip paneer is measuring the dairy counter.**

**Consequence:** `ary assort coverage` groups by `ProductGroupID`, so it reliably reports *what
the operator's tree says* and nothing about whether ARY carries a category. **Never answer "do
we carry X?" from `ProductGroupID`.** The safer axis is **`WarehouseID`**, which is clean:
9/11/15 retail, 12 canteen, 16 Basement/wholesale, 18 fresh produce, 10 back warehouse — that
is how [[Availability]] builds its base, and it sidesteps this trap entirely.

## Trap 2 — the diff's AND-match invented 81 "missing" lines

**Do not use any coverage figure produced before 2026-08-29.** `assort/bin/diff.py` AND-ed the
distinctive words of a researched line, so *"Toor / arhar dal — economy grade, sold loose"*
became `name LIKE '%toor%' AND '%arhar%' AND '%dal%'` and matched nothing — while ARY's SKU is
plainly **"Arhar Daal 1 Kg"**. It reported 81 must-have lines as absent, including toor dal
(12 SKUs, ₹71,949) and almonds (151 SKUs, ₹7,97,032). Fixed with a two-tier verdict —
`specific` / `broad` / `missing` — and a broad single-word fallback before anything is called
missing. Figures NOT-CHECKED today; recorded in full in [[Corrections-Log]].

That fix is what created Trap 11 below: `broad` is now the majority verdict and it means almost
nothing.

## Trap 4 — the price master is stale and biased HIGH

`ProductChildMaster` carries the cost, MRP and selling price. Its cost is **higher** than
reality, directionally and overwhelmingly:

| Comparison, 12m purchase-ledger WAC vs `ProductChildMaster.PurchaseCost` | SKUs | Status |
|---|---|---|
| SKUs comparable on both sides | 5,012 | VERIFIED |
| **Master cost HIGHER than the ledger** | **3,177 (63.4%)** | VERIFIED |
| Master cost LOWER than the ledger | **27 (0.5%)** | VERIFIED |

`WITH wac AS (SELECT ProductID, SUM(Quantity*PurchaseCost)/NULLIF(SUM(Quantity),0) FROM PurchaseDetail…12m…GROUP BY ProductID HAVING SUM(Quantity)>0), pcm AS (SELECT ProductID, MAX(PurchaseCost) FROM ProductChildMaster WHERE PurchaseCost>0 GROUP BY ProductID) SELECT …`

**A margin report built from the master can never surface a below-cost line** — the cost is
inflated on 118 SKUs for every 1 where it is understated. That is exactly why the ₹2.75 lakh
leak in [[Below-Cost-Leak]] went uncaught. **`PurchaseDetail` is the only trustworthy cost
source.** Any margin figure in this vault derived from the price master — the category rates in
[[Institutional]], the tech margins in [[Mobile-Tech]] — must be re-derived before it is acted
on.

### The batch/expiry sub-correction

[[Verify-Pass-2026-08-30]] states *"`ProductChildMaster` = 111,253 rows, **0 real expiry dates,
0 real mfg dates**"*. **That is wrong as stated, and it is corrected here.**

| `ProductChildMaster` | Rows | Status |
|---|---|---|
| Total rows | 111,253 | VERIFIED |
| Batch code in `Field1` | **24** | VERIFIED |
| Mfg date in `Field2` | **26** | VERIFIED |
| Expiry date in `Field3` | **26** | VERIFIED |
| Fill rate | **0.023%**, and every filled row is dated 2017-2018 | VERIFIED |

`SELECT COUNT(*), SUM(CASE WHEN LTRIM(RTRIM(ISNULL(Field1,'')))<>'' THEN 1 ELSE 0 END), … FROM ProductChildMaster` — sample rows: `Gt-08 / 01-Apr-2017 / 31-Mar-2018`, `Rz-14 / 01-Feb-2017 / 31-Jan-2018`.

Batch and expiry live in the untyped `Field1/2/3` columns, not in a dated column — which is why
a scan for date columns returned nothing. **The schema CAN hold batch and expiry. It has simply
been unused since 2018.** The operational conclusion in [[Pharmacy]] is untouched: there is no
working batch/expiry discipline, so the pharmacy blocker is real. But do not repeat the stated
fact — it will not survive a check.

## Trap 5 — `probe` was blind to punctuation (FIXED 2026-08-30)

`probe sugar-free` returned **0** while ARY holds 24 such SKUs written **"Sugar Free"**, and
`probe mamaearth` returned 0 against 16 SKUs written **"Mama Earth"** — precisely the false-gap
class `probe` exists to prevent. **1,116 of 21,479 product names carry a hyphen**, 707 a dot,
708 an ampersand (VERIFIED).

Fixed in `internal/cli/assort.go` (`assortSquash` / `assortSquashSQL`): matching is normalised
on both the term and the column. Re-tested live today:

| Term | SKUs | 12m sales | Status |
|---|---|---|---|
| `sugar-free` / `sugarfree` / `sugar free` | **24 / 24 / 24** | ₹68,825 each | VERIFIED |
| `mamaearth` / `mama earth` | **16 / 16** | ₹38,668 each | VERIFIED |

**Every probe-zero recorded before 2026-08-30 is unsafe if the term was hyphenated or
concatenated. Re-run it.** The determinism half of the same bug report is **NOT REPRODUCED** —
three identical runs give byte-identical output. Do not repeat that claim.

**Lesson: a test that cannot fail is not a test.** The first verdict on this defect was
"not reproducible", reached by probing `anti-dandruff` and `glucose-d` — terms whose *product
names contain the hyphen too*, so they could never expose it.

## Trap 6 — `probe` is still blind to ARY's own spelling (LIVE, no fix)

The punctuation fix does nothing for the house's own typos, and ARY has plenty.

| Probe | SKUs | Result | Status |
|---|---|---|---|
| `probe paracetamol` | **0** | reads as a hard gap | VERIFIED |
| `probe paracitamol` | **2** | `Paracitamol 500 Mg` (Medicare), ₹590, **last sold 2026-08-30 — today** | VERIFIED |

The shop sells paracetamol. The correctly-spelled probe says it does not. Same class: the
subgroup spelled **"Thrermometer"**, and **"Diclowin"**, which no spelling of *diclofenac*
reaches.

> **Probe stems, not words.** `paracit`, `parac`, `bandaid`, `antisept` — not `paracetamol`,
> `bandage`, `antiseptic`. A probe-zero on a single correctly-spelled term is not proof of
> absence.

The vocabulary half of this is worse than the tool half. The device lane declared *"ARY has
never bought a medical device in its history"* on a term list containing **`bandage`** — a
string that appears in **0** of 21,479 product names — while **`bandaid`** returns 1 SKU with
142 purchase lines and ₹2.02 lakh of purchases behind it (VERIFIED: `bandage` 0, `gauze` 0,
`bandaid` 1, `antisept` 14). The same list reported its hits as "all salad dressings"; that
artefact came from the separate term **`dressing`**, which matches Cremica and Veeba condiments
in *Jam & Sauce* (VERIFIED). **A zero-result reported as a false-positive result hid the fact
that the scan never looked at the right word.**

## Trap 7 — the fix made short terms promiscuous (LIVE, introduced 2026-08-30)

Stripping punctuation is not free. `pan-d` normalises to `pand`:

| `probe pan-d` returns | Filed under | Status |
|---|---|---|
| `Meiji Hello Panda Biscuits With Milk 47 Gm` | Confectionery | VERIFIED |
| `Pandol` (a vegetable) | Vegetable / Loki | VERIFIED |
| Verdict row it prints | **2 SKUs, ₹950** | VERIFIED |

A reader who stops at the verdict row concludes ARY stocks the antacid Pan-D. **Never read
`probe`'s verdict row without reading the `THE SKUS` block underneath it.** The verdict row is
a lead; the SKU list is the evidence.

## Trap 8 — the shell eats a multi-word term (LIVE, the most dangerous)

In zsh, an unquoted variable does **not** word-split. This is live and it invalidated a
14-probe molecule sweep before it was caught:

```
t='ors electral'; ./ary assort probe $t    →  0 SKUs,  ₹0          # VERIFIED
./ary assort probe ors                     →  29 SKUs, ₹28,069.20  # VERIFIED
```

The whole string arrives as one term, matches nothing, and prints a clean zero. **A scripted
zero is visually identical to a real gap.** Always `"$@"` / quote each term, and probe one term
per invocation.

## Trap 9 — stock was valued `SUM(Qty) × MAX(cost)` (FIXED 2026-08-30, 3 sites)

`internal/cli/assort.go` priced every unit at the **dearest** warehouse row's cost and applied
it to a **netted** quantity. Measured live today against the correct row-wise
`SUM(Quantity × PurchaseCost)`:

| Aggregate | Old `SUM(Qty)×MAX(cost)` | Correct row-wise | Over-read | Status |
|---|---|---|---|---|
| Negative book stock, all rows (887 rows, −609,946 units) | **−₹127.34 crore** | **−₹17,18,208 (−₹17.18 L)** | **741×** | VERIFIED |
| Negative book stock, grouped per product (281 products) | −₹1,82,15,539 (−₹182.16 L) | −₹13,96,822 (−₹13.97 L) | 13× | VERIFIED |
| Whole `Stock` table | **−₹2,166.68 crore** | **+₹96,90,396 (+₹96.90 L)** | **sign flips** | VERIFIED |

`SELECT SUM(Quantity), MAX(PurchaseCost), SUM(Quantity)*MAX(PurchaseCost), SUM(Quantity*PurchaseCost) FROM Stock [WHERE Quantity<0]`

Two independent errors compound: netting quantity across warehouses (and across
unit-incompatible rows) and then multiplying by the single dearest cost in the set. On the
whole table the netted quantity is **negative** while the true value is **positive ₹96.90
lakh** — the aggregate does not merely mis-size, it inverts. This produced the bogus
"−₹1.56 Cr posted without receipts" P0.

**Two corrections to the record.** (a) The brief circulating as *"−₹1,273 crore"* is a decimal
slip: the live figure is **₹1,27,33,91,199 = −₹127.34 crore**. (b) **Any figure sourced from
`ary stock` or `ary assort` before 2026-08-30 is suspect**, in either direction.

## Trap 10 — `ary audit uncounted` is an exception list read as a census

The command returns only warehouses that **fail** its staleness threshold, plus empty ones. Its
top row today reads *"Ary G Canteen · 8 months since count"*, and it was read as "ARY has not
counted stock in 8 months". Here is the actual census:

| Warehouse | Counts ever | Last physical count | Days ago | Status |
|---|---|---|---|---|
| Ary Pos | 3,194 | 2026-08-25 | **5** | VERIFIED |
| Ary Lite | 8 | 2026-08-24 | **6** | VERIFIED |
| Fruits & Vegetables | 29 | 2026-08-22 | **8** | VERIFIED |
| Ary Warehouse | 68 | 2026-08-22 | **8** | VERIFIED |
| Basement | 7 | 2026-08-22 | **8** | VERIFIED |
| Ary Clothing | 164 | 2026-08-20 | **10** | VERIFIED |
| Ary G Canteen | 9 | 2025-12-29 | 244 | VERIFIED |
| Talwandi Sabo (closed) | 1 | 2023-07-22 | 1,135 | VERIFIED |

`SELECT h.WarehouseID, w.WarehouseName, COUNT(*), MAX(CAST(h.VoucherDate AS date)), DATEDIFF(day, MAX(h.VoucherDate), '2026-08-30') FROM PhysicalStockHeader h LEFT JOIN WarehouseMaster w ON w.WarehouseID=h.WarehouseID GROUP BY …`

**Six of the eight ever-counted warehouses were counted within ten days. The median is eight
days.** Counting discipline at ARY is good; the tool that appeared to say otherwise never shows
the warehouses that pass. Read `uncounted` as "here is the exception list", never as "here are
ARY's warehouses". Related: [[Stock-Variance]], [[Counters]].

## Trap 11 — `assort/research/coverage/*.json` is substring garbage in both directions

**Do not use these files for anything.** They are the raw output of the two-tier diff (Trap 2)
and the broad tier swallowed the corpus.

| Measure across all 46 coverage files | Figure | Status |
|---|---|---|
| Product lines assessed | 2,572 | VERIFIED |
| …marked **`covered`** | **2,322 (90.3%)** | VERIFIED |
| …on a **`broad`** single-word match | **1,607** | VERIFIED |
| …on a `specific` match | 673 | VERIFIED |
| **Sum of `arySales12m` across all lines** | **₹82,66,90,991 = ₹82.67 crore** | VERIFIED |
| ARY's actual 12m retail sales | ₹7,66,19,249 | VERIFIED |
| **Inflation** | **10.8× the entire shop** | VERIFIED |
| Valued lines sharing an identical (sales, SKU-count) pair with another line in the same file | **1,052 of 2,226** | VERIFIED |

Worked examples, each verified against the live catalogue today:

| Line marked **covered** | What actually matched | Status |
|---|---|---|
| *Denture adhesive — cream / powder* (5 SKUs, ₹7,290) | broad match on **`adhesive`** → `Fevicol Adhesive 225 Gm`, `Pidilite Fevicol 100 Gm`, `Camlin Fevicol`, `Quick Bond Rubber Adhesive` — all **Stationary glue** | VERIFIED |
| *Electric toothbrush — rechargeable sonic* (15 SKUs, ₹44,782) | broad match on **`electric`** → `Havells Electric Kettle`, `Kent Electric Kettle`, `Skyline Electric Kettle`, `Hotline Electric Tandoor` — **Cookware** | VERIFIED |
| *Electric toothbrush — battery entry* (108 SKUs, ₹2,63,915) | broad match on **`colgate`** → the entire Colgate **toothpaste** range | VERIFIED |
| *Denture brush / denture box* and *Replacement electric brush heads* (170 SKUs, ₹2,57,546 — **the same figure twice**) | broad match on **`brush`** → 109 Personal Care + 52 House Hold (toilet brushes) + 5 Stationary (paint brushes) | VERIFIED |
| *Banana chips — sweet / jaggery-coated* (18 SKUs, **₹3,62,073**) | broad match on **`banana`** → the **fresh fruit** line. The identical 18 SKUs / ₹3,62,073 is booked against four different lines in three files | VERIFIED |

`grep`/`python3` over `assort/research/coverage/*.json`, then each matched term re-queried:
`SELECT p.ProductName, g.ProductGroupName FROM ProductMaster p LEFT JOIN ProductGroupMaster g ON g.ProductGroupID=p.ProductGroupID WHERE p.ProductName LIKE '%adhesive%'` (etc.)

**Nothing in these files is a coverage measurement.** `matchQuality: broad` means only "some
word in this line's description appears somewhere in some product name" — and 62% of all lines
rest on that. Use `ary assort probe` and read the SKU block. See [[Gap-List]] and
[[Fleet-Method]].

## Trap 12 — where you measure "out of stock" changes the answer

`Stock` rows at the retail counters go negative because transfers from `Ary Warehouse` are not
always posted. Measuring availability there counts posting errors as empty shelves.

| Base: 5,950 retail SKUs that sold in 12m | Out of stock | Status |
|---|---|---|
| **Company-wide `SUM(Stock.Quantity) <= 0`** | **3,051 (51.3%)**, ₹1,44,32,593 of trailing sales | VERIFIED |
| Retail counters only (WH 9/11/15) | 3,211 | VERIFIED |
| Difference caused purely by the measurement choice | **160 SKUs** | VERIFIED |

Worked example — `Maggi Noodles 48 Gm Masala`, live today:

| Warehouse | On hand | Status |
|---|---|---|
| Ary Pos | **−45** | VERIFIED |
| Ary Lite | **−107** | VERIFIED |
| Ary G Canteen | −324 | VERIFIED |
| Ary Warehouse | +2,052 | VERIFIED |
| **Company-wide** | **+1,576** | VERIFIED |

It reads −152 across the retail tills and it is one of the shop's best sellers. **Say
"company-wide `SUM(Stock.Quantity) <= 0`" out loud in any availability claim** — [[Availability]]
does.

Two further rules for any stock query:

- **Exclude warehouses 14 (Talwandi Sabo) and 17 (Girls Canteen Ts).** Both are `LocationID 16`
  = Bathinda and both `IsActive = false`, 400 km from the Baru Sahib shelf (VERIFIED via
  `SELECT WarehouseID, WarehouseName, IsActive, LocationIDs FROM WarehouseMaster`). Talwandi
  Sabo alone still carries **−127,849 units / −₹8,23,199 of negative book stock — 48% of the
  entire company's negative position** (VERIFIED). Including them makes dead SKUs read
  "available".
- **`ary assort probe`'s `per_resident_yr` column hard-codes a 5,000 headcount** (VERIFIED:
  ₹68,825 ÷ 13.77 = 4,998). That denominator is a stated campus figure, never measured in
  FR8HODBNEW, and the cohort split under it was REFUTED — see [[Population]]. Treat every
  `per_resident_yr` as ESTIMATED.

## Trap 13 — `Stock`'s movement buckets are ALL-TIME, not 12-month

`Stock` carries `Pur, PR, Sal, SR, Prod, Cons, TrIn, TrOut` alongside `Quantity`. They look
like period figures. They are lifetime totals.

| Test on ProductID `00BF` | Figure | Status |
|---|---|---|
| `SUM(Stock.Sal)` | **44,268** | VERIFIED |
| `SUM(SaleDetail.Quantity)`, all time | **44,268** — identical | VERIFIED |
| `SUM(SaleDetail.Quantity)`, 12m | **13,059** | VERIFIED |

Reading `Stock.Sal` as "sold this year" over-reads by **3.4×** on this SKU alone.

The useful half: because the buckets are cumulative and every movement document is dated, a
daily on-hand series **can** be rebuilt — today's `Quantity` minus every dated movement on or
after day *D*, across `SaleDetail`, `SaleReturnDetail`, `PurchaseDetail`, `PurchaseReturnDetail`,
`StockTransferDetail` and `StockJournalDetail` (`JournalType` 235=Cons, 236=Sho, 237=Exc,
73=Prod, 238=Was). That reconstruction disagrees with reality on only 0.4% of selling days
(NOT-CHECKED here; VERIFIED by the natural-experiment re-test). **It is the only honest way to
answer an availability question over time in this database.**

## Trap 14 — "in stock" defined as "it sold that day" is circular

The headline natural experiment classified a SKU as available on a day **if it rang a sale that
day**, then measured sales on those days. The classifier and the outcome are built from the
same rows.

| | Status |
|---|---|
| On the 45 days labelled "only 0-4 of the top-10 available", the reconstructed book actually held **6.1 of 10** at Baru Sahib, and 7+ on 20 of those 45 days | VERIFIED by the re-test, NOT-CHECKED here |
| Effect on a non-circular measure (book on-hand > 0) | **₹1.33/bill**, not ₹3.08/bill | VERIFIED by the re-test |
| Month fixed effects alone cut the original gap to ₹1.21/bill — seasonality is **larger** than the effect being attributed to the shelf | VERIFIED by the re-test |

The published *"footfall IDENTICAL, 998 vs 997 bills/day"* is half wrong: 998.0 on the worst 45
days is exact; the best 42 days average **1,265.8** bills/day, and a single outlier
(2025-09-21, 10,297 bills against a ~1,000/day norm) carries most of the gap.

> **Rule: never define availability from the sales table you are about to measure.** Rebuild
> on-hand (Trap 13) or use a neighbour-day proxy, and control for month.

## See also

- [[Verify-Pass-2026-08-30]] — the pass that refuted 106 of 293 claims and killed old Trap 3
- [[Corrections-Log]] — the full record of what this exercise got wrong, kept rather than deleted
- [[Availability]] — the finding these traps nearly destroyed, and the one note whose base is
  built on `WarehouseID` rather than the lying category tree
- [[Below-Cost-Leak]] — why Trap 4 matters in rupees: the leak the price master could never surface
- [[Gap-List]] — the probe method that survives Traps 5-8, and the only gap list worth reading
- [[Fleet-Method]] — why the research fleet's aggregate numbers cannot be summed, of which
  Trap 11 is the mechanism
- [[Pharmacy]] — the one REAL_GAP that survived all of this, and the batch/expiry sub-correction
- [[Population]] — the 5,000 denominator baked into `probe`, and the cohort split that was refuted
- [[Stock-Variance]] — Trap 10's exception list read correctly
- [[00-ARY-Atlas]] — the index, if you arrived here first
