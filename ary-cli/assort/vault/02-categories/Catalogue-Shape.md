---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Catalogue shape — the answer to the brief

**ARY does not have an assortment problem. It has an availability problem.** It lists
1.79x the benchmark range and sells 0.59x of it. Both halves are true at once, and together
they are the whole finding.

## The catalogue is mostly fiction

| | |
|---|---|
| Active SKUs | 19,481 |
| Sold at least once in 12 months | **6,197** |
| Never sold in 12 months | **13,284 (68%)** |
| Sold exactly one bill | 537 |
| Sold under ₹1,000 in the year | 1,722 |

Revenue concentration:

| Band | SKUs | Sales | Share |
|---|---|---|---|
| Top 50% of revenue | **252** | ₹3.77 Cr | 50.0% |
| To 80% | 856 (cum. 1,108) | ₹2.27 Cr | 30.0% |
| To 95% | 1,764 (cum. 2,872) | ₹1.13 Cr | 15.0% |
| Last 5% | 3,325 | ₹0.38 Cr | 5.0% |

**252 SKUs earn half the money. 1,108 earn 80%.**

Important nuance — `ary assort dead --by-group`: the 13,284 non-selling SKUs hold almost
**no stock**. The top 20 dead groups lock only ~₹4.3 lakh at cost. This is a **catalogue
hygiene** problem (dead lines still flagged active, still priced, still counted), **not**
trapped working capital. Do not report it as crores of dead inventory.

## Procurement failure, not market gap

Three independent execution lanes reached the same conclusion by different routes, and it
is the most important structural finding in the exercise.

### Baby care — my §18 correction needs its own correction

The babycare lane challenged my conclusion, and it is **partly right**. Verified:

| Diaper SKUs by pack class | SKUs listed | **Ever purchased** | 12m sales |
|---|---|---|---|
| Small pack (2-9 pieces) | 37 | **14** | ₹28,358 |
| **Monthly / bulk pack** (42s, 50s, Baby Dry) | **2** | **0** | **₹0** |
| Other / unspecified | 27 | 6 | ₹5,766 |
| **Total Pampers + Huggies + MamyPoko** | **66** | **20** | **₹34,124** |

And the whole baby probe (diaper, wipes, baby, Cerelac, Lactogen, formula):
**247 SKUs listed across 11 groups, 80 sold, ₹2.07 lakh, ₹41/resident/year.**

**Every single Huggies code has zero purchases and zero sales. Both monthly-pack codes have
never been bought once.** ARY only ever procures 2-9 piece emergency packs.

**Where both readings stand:**
- **My §18 finding holds on volume.** 425 diaper packs a year is genuinely tiny — nobody
  should build a baby aisle expecting a large infant base.
- **The lane is right on cause.** A parent who needs a month of nappies cannot buy them at
  ARY at any price, because the monthly pack has never been ordered. The 425 packs are
  emergency top-ups, not a household's supply.
- **Which effect dominates is not resolvable from this data.** Small campus infant base
  and unstocked bulk packs produce the same 425-pack signal. **The cheap test is to order
  the two existing monthly-pack codes once** and see whether they move — ₹5,000 of stock
  answers a question no amount of analysis can.

### Mobile accessories — a real business hidden in four codes

The lane found ARY already sells **₹2.16 lakh a year of cables, chargers, earphones and
TWS at a verified 41-43% gross margin**, through **four generic catch-all product codes**.
My own probe found ₹99,713 on 14 named SKUs; the lane found more by including the generic
codes. Either way the "₹2,690 Mobile group" figure that started this investigation was
never the business — it was a mis-classification. **An unmanaged, growing, high-margin
category exists and nobody can see it because it has no SKUs.**

### The q-commerce benchmark puts it beyond doubt

> ARY already carries the SKU breadth of an entire Blinkit city network outside India's top
> eight metros — **19,481 active lines against Blinkit's ~20,000 for a whole tier-3 city** —
> on 6.7% of one DMart store's revenue.

### ⭐ What this means for the brief

The user asked for **every product people need that ARY doesn't have.** The honest answer,
now supported by five independent lines of evidence:

**ARY does not have an assortment problem. It has an availability problem.**

- 19,481 active SKUs, matching a whole city's q-commerce network — but **only 6,197 sold**
- 252 SKUs earn half the revenue; 1,108 earn 80%
- Every Huggies code, both monthly diaper packs, all 3 medical devices, all 8 active hand
  tools, 42 of 47 LED/battery SKUs: **listed, never ordered, never sold**
- The two things that did work (Fruits & Veg, Basement) were **narrow ranges kept in stock**,
  not broad ones
- The categories that look "missing" by group tag (mobile, dairy) are mostly **mis-filed
  or unordered**, not absent

**Adding thousands more SKUs to a catalogue where 68% of the existing ones never sell would
make the problem worse, not better.** The work is: order what is already listed, delete what
will never sell, and add *narrow* new ranges one at a time — which is exactly what ARY's own
two successes did.

## The benchmark table — what ARY should carry

`ary assort benchmark` — ARY's live range against an external SKU-line benchmark
(BigBasket BB Now metro category counts, pro-rated to a 5,000-person population by the
q-commerce lane; metro counts VERIFIED live, the pro-rata ESTIMATED).

| Category | Benchmark lines | ARY active | ARY **selling** | selling vs benchmark | listed vs benchmark | Verdict |
|---|---|---|---|---|---|---|
| **Baby care** | 323 | **0** | **0** | **0.0%** | 0.00× | **NO ARY GROUP EXISTS** |
| **Bakery, cakes & dairy** | 864 | 225 | **92** | **10.6%** | 0.26× | **severe range gap** |
| Gourmet & world food | 210 | 235 | 45 | 21.4% | 1.12× | severe range gap |
| **Foodgrains, oil & masala** | 1,913 | 1,274 | **451** | **23.6%** | 0.67× | **severe range gap** |
| **Fruits & vegetables** | 271 | 167 | 132 | 48.7% | 0.62× | range gap |
| Beverages | 438 | 934 | 271 | 61.9% | 2.13× | adequate |
| Snacks & branded foods | 1,992 | 4,095 | 1,371 | 68.8% | 2.06× | adequate |
| Kitchen, garden & pets | 308 | 901 | 243 | 78.9% | **2.93×** | over-listed, under-stocked |
| Cleaning & household | 795 | 2,766 | 866 | 108.9% | **3.48×** | over-listed, under-stocked |
| Beauty & hygiene | 886 | 3,747 | 1,236 | 139.5% | **4.23×** | over-listed, under-stocked |
| Eggs, meat & fish | 0 | 0 | 0 | — | — | **structural zero, excluded** (vegetarian institution) |
| **TOTAL** | **8,000** | **14,344** | **4,707** | **58.8%** | **1.79×** | |

### The answer, in one line

**ARY lists 1.79× the benchmark range and sells 0.59× of it.** Both halves of that sentence
are true simultaneously, and they are the whole problem.

### Two different jobs, and confusing them is why this looked like one question

**Job 1 — ADD range, in three categories only.** These are genuinely short of lines, and
the shortfall is not a listing artefact:

- **Baby care: 323 benchmark lines, no ARY product group at all.** The 247 baby SKUs that
  exist are scattered across 11 other groups with 80 selling. Worst relative gap in the
  business.
- **Bakery, cakes & dairy: 92 selling lines against 864.** ARY lists only 225 — it has not
  even *listed* the range, so this is a real buying gap, not an availability one. Dairy's
  sub-benchmark alone is 294 lines against ARY's 41. This is the largest verified depth gap.
- **Foodgrains, oil & masala: 451 selling against 1,913** on 1,274 listed. The core township
  basket, and the single biggest absolute shortfall — 1,462 lines. Masalas & spices alone
  benchmarks 649 lines.
- **Fruits & vegetables: 132 selling against 271** — and this is ARY's *best* counter, at 172
  stock turns a year. The benchmark says it could carry twice the lines and ARY is the only
  fresh source for 5,000 people. Strong candidate: proven demand, proven operation.

**Job 2 — DELETE range, in three categories.** These carry 2.9× to 4.2× the benchmark in
listings while selling a fraction:

- **Beauty & hygiene: 3,747 listed against an 886 benchmark — 4.23×** — with 1,236 selling.
- **Cleaning & household: 2,766 listed against 795 — 3.48×.**
- **Kitchen, garden & pets: 901 against 308 — 2.93×.**

Those three hold **7,414 listed SKUs where the benchmark says 1,989.** That is ~5,400 lines
of catalogue an operator must price, count and shelve for no return — and it is precisely
the shelf and attention that Job 1's missing dairy, staples and baby lines need.

**So the two jobs pay for each other.** Delete ~5,400 dead lines from over-listed
categories, add ~1,500 real lines to dairy, staples and baby care. Net catalogue shrinks,
net revenue grows. That is the opposite of "carry every product", and it is what the data
says.

**One methodological caution:** the benchmark's pro-rata from metro SKU counts is an
ESTIMATE, and category boundaries between BigBasket's tree and ARY's do not map cleanly
(§22 — ARY's tree is unreliable, so `ary_active_skus` here inherits that noise). Treat the
*direction and magnitude* as sound — 4× over-listed in beauty, 10× under-sold in dairy are
too large to be mapping error — and re-derive any single category before acting on its
exact number.

## The coverage corpus, read honestly

`ary assort research`, after the §33 fix split solid line-level matches from broad commodity
matches. 12 categories diffed so far, worst line-coverage first:

| Category | Lines | **Line match** | Commodity only | Dormant | **Missing** | Line coverage |
|---|---|---|---|---|---|---|
| **medical-devices** | 58 | **6** | 43 | 7 | 2 | **11.5%** |
| **oralcare** | 54 | 14 | 37 | 2 | 1 | **21.4%** |
| **frozen** | 51 | 11 | 39 | 1 | 0 | **27.0%** |
| dryfruits | 57 | 18 | 38 | 1 | 0 | 33.3% |
| **dairy** | 52 | 19 | 32 | 1 | 0 | 34.9% |
| beverages-hot | 54 | 21 | 32 | 1 | 0 | 36.6% |
| bakery | 52 | 21 | 31 | 0 | 0 | 44.2% |
| femcare | 48 | 20 | 22 | 6 | 0 | 46.9% |
| oils | 46 | 24 | 22 | 0 | 0 | 51.5% |
| beverages-cold | 48 | 25 | 21 | 2 | 0 | 54.3% |
| fruits | 52 | 28 | 20 | 3 | 1 | 60.6% |
| confectionery | 46 | 29 | 17 | 0 | 0 | 65.8% |

**How to read this.** "Missing" is now almost always **zero** — because ARY genuinely has
something under nearly every commodity heading. The signal has moved into the middle column:
**"commodity only" means ARY sells *something* in that line but not the pack, grade or brand
the research says it should carry.** Medical devices at 6 line-matches out of 58, and frozen
at 11 of 51, are the real depth gaps — consistent with §23 (medical devices: 3 SKUs, zero
sales) and §32 (bakery/dairy 92 selling lines against a benchmark of 864).

**Genuinely missing, with no match at all** — the four the corpus can defend:

| Category | Line | Essentiality |
|---|---|---|
| **oralcare** | **Denture cleansing tablets / soak powder** | **must-have** |
| fruits | Chikoo / Sapota | should-have |
| medical-devices | Instant single-use cold pack | should-have |
| medical-devices | Compression / varicose vein stockings | nice-to-have |

Denture care is the notable one: a must-have line with no match anywhere in 21,466 SKUs, on
a campus with resident elderly staff and a 100-bed hospital. Cold packs and compression
stockings fit the same cohort, and the sports injuries of 2,600 students.

**The tool now shows its own uncertainty**, which is the point. `ary assort gaps --state
commodity` lists every weak match with the term that produced it, so a buyer can see that
"Period-pain OTC tablet" matched only on the word `tablet`, and that "Pregnancy test kit"
matched only on `basic` — neither of which proves anything. Those are exactly the lines
§36 confirmed as true zeros by direct probe.

## See also

- [[Gap-List]] — the probe-verified gaps that survive scrutiny
- [[Data-Quality-Traps]] — why the group tag cannot answer "do we carry this"
- [[Ten-Moves]] — moves 6 and 7 act on this
