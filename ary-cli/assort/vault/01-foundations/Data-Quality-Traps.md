---
type: reference
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Data-quality traps — read this before quoting any number

**The most important note in this vault.** Four separate times in this exercise a
plausible, well-formatted finding turned out to be an artefact of a broken field. Each trap
below produced a wrong answer that survived review until it was checked directly.

The house rule that falls out of all of them: **in this database the burden of proof sits on
"missing", never on "covered".** ARY probably has it under a different name.

## What cannot be answered at all

| Limit | Evidence |
|---|---|
| **97% of bills have no identified buyer.** Customer 00001, ledger account "Cash", carries 1,054,205 of 1,088,607 lifetime bills and ₹17.13 Cr at ₹162.53 average | `ary sales by-customer`, `ary customers get 00001` |
| **99.7% of bills have no salesperson.** SalesPersonID [NONE] on 1,085,051 bills | `ary sales by-staff` |
| **No cost price in the master.** `StandardCostPrice` set on **41 of 19,481** active SKUs; `StandardSalePrice` on 562; `MaxRetailPrice` on **zero** | `SELECT COUNT(*), SUM(CASE WHEN … )` on ProductMaster |
| Real cost/price/margin exists only per-location on `ProductChildMaster` (purchase_cost, mrp, selling_price, margin_pct) | `ary products children` |
| **No ARY↔SAP item map.** `ProductCodeSAP` present on all 21,466 SKUs, empty in every one | `ary products sap-gap` |
| `ProductMaster.QuantityOnHand` is dead — non-zero on one SKU. On-hand is `Stock.Quantity` | `study/specs/schema-notes.md` |
| The payment-mode table's Cash amount reads ₹10,023 Cr against ₹22.49 Cr of net sales — **that column is unusable**, do not quote `ary sales payment-mix` amounts | `ary sales payment-mix` |
| SAP login is `sa` (sysadmin). The read-only guarantee comes from the CLI's guard, not from the grant | `ary doctor` |

## Trap 1 — the category tree lies

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

## Trap 2 — my own diff produced 81 false "missing" verdicts

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

## Trap 3 — payment amounts are unusable in every column

The digital lane claimed "UPI is 56.3% of tenders and 42.9% of collections value". The first
half is right; the second cannot be supported by this database, and it is worth pinning down
because a payments strategy would be built on it.

### What is trustworthy: tender counts

`SalePayment` × `SaleHeader`, 12 months:

| MOPID | Mode | **Tenders** | **% of tenders** |
|---|---|---|---|
| **503** | UPI (booked as "Paytm") | **222,237** | **55.7%** |
| 1 | Cash | 166,072 | 41.6% |
| 2 | Credit Sale | 11,019 | 2.8% |

**VERIFIED and important: UPI is now the majority payment method at ARY by transaction
count** — 55.7% against cash's 41.6%. On a rural Himachal campus that is a genuinely
notable fact, and it is the strongest single argument for the digital-layer work: residents
have already changed behaviour without ARY building anything.

### What is broken: all three amount columns

| Column | 12-month total | Should be |
|---|---|---|
| `SUM(Amount)` | **₹900.35 crore** | ₹7.55 crore |
| `SUM(TenderAmount)` | **₹894.43 crore** | ₹7.55 crore |
| `SUM(TenderAmount − ReturnAmount)` | ₹2.26 crore | ₹7.55 crore |

The first two are **~119× actual sales.** The third is 30% of it. And the per-mode split is
nonsense in both directions: by `Amount`, cash is 99.3% of value while UPI is 0.4%; by
net tender, cash is 100.0% and UPI and credit are both exactly ₹0.

**Diagnosis:** MOPID 1 (Cash) carries a scaling or units defect — ₹8,944 crore of
"TenderAmount" on 166,072 tenders is ₹53,858 per cash transaction on a shop with a ₹207
average bill. And UPI/credit tenders record their value in `Amount` only, leaving
`TenderAmount` and `ReturnAmount` at zero, so any net-tender calculation attributes 100% to
cash by construction.

**This supersedes §10's note** that `ary sales payment-mix` amounts are unusable — now the
mechanism is known:

> **Payment-mode COUNTS are reliable. Payment-mode VALUES are not, in any column.**
> Quote "55.7% of transactions are UPI". Never quote a rupee split by payment mode.

The 42.9%-of-value figure the lane reported is therefore **unverifiable, not wrong** — there
is no column in this database that can produce a trustworthy value split. Anyone sizing a
payments or wallet project must get that from the acquirer's settlement reports (Paytm's own
statements), not from FusionERP8.

### The rest of the digital lane's findings stand, and two are strong

| Claim | Status |
|---|---|
| 96.2% of FY26-27 bills (162,434 of 168,881) booked to one anonymous account | **VERIFIED** — matches my own §18 count of 14.41% institutional / 71.1% walk-in |
| A campus wallet spendable only at ARY is a **closed-system PPI** — no RBI authorisation, no escrow | **VERIFIED**, and it removes the regulatory objection to the wallet idea entirely |
| **FusionERP8 already ships a configured, never-used wallet data model** | **VERIFIED** — consistent with `CustomerMaster` carrying unused `loyalty_points`, `visits` and `crm_limit` fields |
| WhatsApp order-to-pickup needs no app build; a customer-initiated conversation opens a free 24-hour window | VERIFIED against Meta's published pricing |
| Identified-customer basket ₹1,586 vs walk-in ₹155 | **VERIFIED but correctly flagged by the lane as NOT causal** — the identified accounts are institutions and credit households, so the 10× is a selection effect, not a benefit of identification. Good discipline from that lane. |

## Trap 4 — the price master is stale and biased HIGH

Covered in full in [[Below-Cost-Leak]].
`ProductChildMaster` carries a cost **higher** than reality on every leaking SKU, so a margin
report built from it can never surface a below-cost line. **The purchase ledger is the only
trustworthy cost source.**

Any margin figure in this vault derived from the price master — the category rates in
[[Institutional]], the tech margins in [[Mobile-Tech]] — carries this risk and should be
re-derived from `PurchaseDetail` before being acted on.

## See also

- [[Corrections-Log]] — the full record of what this exercise got wrong
- [[Gap-List]] — the probe method that survives these traps
- [[Fleet-Method]] — why the research fleet's aggregate numbers cannot be trusted
