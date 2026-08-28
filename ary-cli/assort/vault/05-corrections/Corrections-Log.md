---
type: reference
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Corrections log — what this exercise got wrong

Every one of these was plausible, well-formatted, and would have cost money. They are kept
because the *pattern* is the lesson: in this database a confident finding is usually an
artefact until it has been checked directly against the live catalogue.

House rule: **the burden of proof sits on "missing", never on "covered".**

## The baby-care and per-resident errors

**(a) The per-resident metric was overstated, because a Delhi NGO is inside it.**

`ary customers get 002CM`: **Hunger Heroes is at "Green Park Main, New Delhi, Delhi
110016"** — an outside food-charity organisation, not a resident. In FY26-27 to date it is
**₹50.97 lakh on NINE bills = 14.41% of all revenue** (verified independently: my query
returns 14.41%, the research lane 14.53%).

So the honest resident figure is **~₹1,290 per resident per month, not ₹1,493** — the
earlier number divided institutional charity sales by the residential population. The
₹1,259 figure in §1 above carries the same defect. **Corrected: strip 002CM and the other
institutional accounts before quoting any per-resident number.**

**(b) Baby care is NOT the opportunity I flagged in §6. There are almost no babies.**

Verified: **425 diaper packs in 12 months** (Pampers L-7 81, M-8 80, Happy Skin S 62,
L-5 23, plus tail). At ~7 pants a pack that is ~3,000 pants a year — **8 pants a day,
i.e. one to two children in nappies on the entire campus.** Infant formula: 13 packs.
Combined baby-specific spend ₹38,002 a year.

Baby *toiletries* do sell — Himalaya and Johnson's baby soap, shampoo, talc, oil and
lotion total ~₹1.5 lakh a year — but in India those are bought by adults as gentle
toiletries, so they are not evidence of an infant base.

**The residential cohort is boarding children aged 5-18 and students aged 18-25, not
families with infants.** My "no diapers or formula on a campus with married staff
families" line in the original PLAN.md was a plausible inference that the data refutes.
Recorded so nobody acts on it.

## The category tree

Testing the tree against reality:

| Product | Filed under |
|---|---|
| Loose Milk | **Mini Meals** |
| Dahi_Z (curd) | **Others** |
| Khoya_Z | **Confectionery** |
| Loose Desi Ghee | Oil & Ghee |
| Peas (Fresh Matar)_Z | **Fruits** |
| Kala Chana_L | **Atta & Other Flours** |
| Lobia_L | **Veg Delight** |
| Mixed Daal 1 Kg | **Rice & Other Grains** |
| Nutri 1 Kg (soya chunks) | General Items |

Name-searching every dairy word (milk, dahi, paneer, curd, butter, cheese, khoya, ghee)
across all groups, 12-month sales, shows where dairy actually sits:

| Filed under | SKUs | 12m sales |
|---|---|---|
| Confectionery | 128 | ₹19.39 L |
| Oil & Ghee | 4 | ₹16.16 L |
| Mini Meals | 2 | ₹11.39 L |
| **Dairy Products** | **10** | **₹9.54 L** |
| Others | 1 | ₹2.45 L |
| Chinese Items | 1 | ₹1.88 L |
| Drinks | 19 | ₹1.45 L |
| + 7 more groups | 47 | ₹2.55 L |

**"Dairy Products" holds under 15% of the dairy-word sales.** (The name search
over-captures in the other direction — much of that Confectionery figure is milk chocolate
and milk sweets, not chiller dairy — so neither number alone is the truth.)

**Consequence:** `ary assort coverage`, which groups by `ProductGroupID`, is a reliable
measure of **what the operator's own tree says**, but it is NOT a reliable measure of
whether ARY carries a category. My §6 statements "Dairy 41 SKUs / ₹186 per resident" and
"Frozen 57 SKUs" understate real coverage by an unknown amount.

The `ary assort probe` command (§ below) was added to answer the question the group tag
cannot. **Every "missing category" conclusion in the research corpus must be re-tested with
`probe` before anyone buys stock against it.** This is the same trap as JIVO correction
C-0016: a blank usually means the value lives somewhere else.

## 81 false "missing" verdicts from my own tool

**Do not use any coverage figure produced before this section was written.**

The first run of `assort/bin/diff.py` reported **81 "must-have" SKU lines ARY has nothing
for**, including these:

| Reported "missing" | What `ary assort probe` actually finds |
|---|---|
| Toor / arhar dal — economy grade | **12 SKUs, 6 selling, ₹71,949** in 12 months |
| Almonds — everyday grade | **151 SKUs** (almond+badam), 48 selling, **₹7,97,032** |
| Cashew — whole grade W240/W320 | present |
| Raw peanuts / moongphali | present |
| Chikki — peanut, til, dry-fruit | present |

**Cause:** the diff matched each researched line by AND-ing the distinctive words in its
description. "Toor / arhar dal — economy grade, sold loose" became
`name LIKE '%toor%' AND '%arhar%' AND '%dal%'` — which matches nothing, because ARY's SKU
is called plainly **"Arhar Daal 1 Kg"**. The AND was added to stop the opposite failure
(a single generic word like `milk` matches 389 SKUs and marked all 52 dairy lines covered),
and it overcorrected.

**Fix applied:** a two-tier verdict. Specific AND-groups are tried first; before any line is
declared missing, single distinctive words are tried as a **broad commodity fallback**. Each
result now carries `matchQuality`:

- **`specific`** — the line's own qualifiers all appear in one product name. Strong.
- **`broad`** — only the commodity word matched. **ARY is in this line, but this exact pack,
  grade or brand is unproven.**
- **`missing`** — nothing matches, specific or broad. This is now a real finding.

**Why this is recorded rather than quietly fixed:** the false list was plausible,
well-formatted, and would have sent a buyer to source arhar dal and almonds that ARY already
sells ₹8.7 lakh of. It is the same trap as JIVO correction **C-0016** (a blank usually means
the value lives elsewhere) and the same trap as §22 (ARY's category tree). **In this database
the default assumption must be that ARY probably has it under a different name** — the burden
of proof is on "missing", not on "covered".

**Standing rule for anyone using this toolkit:** before acting on any `missing` verdict,
re-check it with `ary assort probe <commodity words>`. That command queries the live
catalogue directly and has been right every time the diff was wrong.

## The institutional headline, qualified

This is the most important caveat in the document, and it changes how the institutional
opportunity should be pitched.

The ledger holds these accounts, and their group placement is the finding:

| Account | Ledger group | Side |
|---|---|---|
| **Akal Dairy - Baru Sahib** | Local **Creditors** - Baru Sahib | ARY owes them |
| **Akal Modi Khana - Baru Sahib** | Local **Creditors** - Baru Sahib | ARY owes them |
| **Akal Bakery - Baru Sahib** | Local **Creditors** - Baru Sahib | ARY owes them |
| **Akal Catering Mess** | Local **Creditors** - Baru Sahib | ARY owes them |
| Akal Academy · Akal Hospital · Eternal University · Akal Nursing College · Akal De-Adiction Ward · Akal Mahila Mandal | Local **Debtors** - Baru Sahib | they owe ARY |

("Modi Khana" is the gurdwara/institutional provision store — the langar stores.)

### What ARY buys from them, and when it started

| Unit | Vouchers | ARY purchases (credit) | First txn | Last txn |
|---|---|---|---|---|
| **Akal Modi Khana** | 7 | **₹2,42,640** | 2026-06-08 | 2026-08-14 |
| **Akal Dairy** | 73 | ₹77,726 | 2026-06-03 | 2026-08-17 |
| **Akal Bakery** | 115 | ₹54,706 | 2026-06-03 | 2026-08-21 |
| **Akal Catering Mess** | 56 | ₹31,641 | 2026-06-03 | 2026-08-21 |
| **Total** | 251 | **₹4,06,713** | — | current |

**All four relationships began in June 2026 — under three months ago — and all four are
live to the last day of data.** In one quarter ARY has bought ₹4.07 lakh from the campus's
own dairy, bakery, langar stores and catering mess.

### Why this matters, in both directions

**Against the §16 thesis:** the campus is not an unserved buyer waiting for a supplier. It
already operates its own dairy, bakery, provision store and catering mess. Eternal
University's ₹2.51 Cr of mess spend is very likely flowing largely to **those in-house
units**, not leaking to an outside market ARY could win. **"₹4-5 crore of unserved
institutional wallet" is too strong a claim** and should not be presented as a clean
addressable gap.

**For it, and this is the more interesting reading:** ARY has just spent one quarter
becoming a *customer* of those units. That is a working commercial relationship, opened
recently, on 251 vouchers. The realistic prize is therefore **not "displace the mess"** —
it is:

1. **Two-way trade.** ARY buys their dairy and bread for retail; they buy ARY's staples,
   spices, oil and vegetables for the mess. ARY already runs the purchasing muscle (§27:
   ₹6.36 Cr of purchases, ten HP suppliers, a daily milk route) that four small in-house
   units cannot each replicate.
2. **Consolidated procurement for the campus.** The gap is not that the mess buys nothing —
   it is that Akal Academy places **2,055 petty bills at ₹1,299** and the Trust **1,045 at
   ₹969** (§15). Those are thousands of small purchases that a single supply contract could
   absorb at better prices for the Trust and better margin for ARY.

**Revised, defensible version of §16:** the institutional opportunity is real but it is a
**procurement-consolidation and two-way-trade opportunity**, not a virgin market. The
₹2.51 Cr figure is a VERIFIED measure of *what the campus spends on food*, not of what ARY
can capture. **Anyone quoting ₹4-5 crore should stop and read this section first.**

**What would settle it:** ask the Trust what Akal Dairy, Akal Bakery and Akal Modi Khana
actually supply and at what scale, and whether Eternal University's ₹1.96 Cr of mess meal
charges is paid to those units or to outside vendors. One conversation; it is the single
highest-value unanswered question in this exercise.

## See also

- [[Data-Quality-Traps]] — the same material organised as traps to avoid
- [[Fleet-Method]] — the research fleet's own aggregation failure
