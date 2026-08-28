# ARY expansion — brief for whoever runs this next

> **You are Claude Code, opened by someone on the ARY side who wants to expand the range.**
> Read this file, then `assort/vault/00-ARY-Atlas.md`. Do not start querying until you have
> read both — this database has traps that produce confident wrong answers, and they are
> documented.

---

## The job

ARY is the only shop for ~5,000 people on a closed campus at Baru Sahib. The owner wants
**everything those people need to be buyable at ARY**, so nobody has to arrange anything
elsewhere. Monopoly, so the goal is completeness, not competing.

**The method, in six steps** (this is the owner's own, and it is sound):

1. Capture what 5,000 people living together need, **by cohort** — students, staff, families
2. Turn that into **categories of daily life**
3. For each category, list what ARY already has
4. **Sub-categorise: what are the genuinely best products people use in real life outside?**
5. Compare against ARY's shelf → the add list
6. **Add on priority, as a small pilot.** Measure in 1-2 months, let results decide

**Step 7 — did it work? — is the one ARY cannot answer today.** See "The measurement
problem" below. Do not let anyone skip it.

---

## Before you query anything: four traps

Each of these produced a confident, well-formatted, **wrong** answer during the first pass.
Full record in `assort/vault/01-foundations/Data-Quality-Traps.md`.

**1. The category tree lies.** Loose Milk is filed under *Mini Meals*, curd under *Others*,
khoya under *Confectionery*. The "Mobile" group tag understated mobile accessories by
**37×**. Never answer "do we carry X?" from `ProductGroupID`.

```bash
ary assort probe paracetamol crocin dolo    # searches NAMES across all 21,466 SKUs
```

**2. Pass single words to `probe`, never phrases.** `"washing bar"` returns zero;
`washing bar soap` returns 528 SKUs and ₹10.7 lakh.

**3. Read every probe result for contamination.** `stick` catches lipstick. `candle`
catches decorative candles. **`Lmk` is an ARY bakery brand**, and probing `gas` caught
Gas Stove and Gas Lighter — which produced a phantom "₹4.80 lakh LPG business" that does
not exist. Five false positives happened this way. **Check what actually matched before
quoting a number.**

**4. The price master is wrong, and biased HIGH.** `ProductChildMaster` shows a cost
*higher* than reality on every loss-making line, so margin reports can never surface one.
Cost comes from `PurchaseDetail` — what ARY actually paid.

```bash
ary assort leak     # this is what found ₹2.75 lakh/yr going out the door
```

**The standing rule: in this database the burden of proof sits on "missing", never on
"covered."** ARY probably has it under a different name.

---

## The arithmetic that sizes everything

Active SKUs by how often they actually sell, 12 months:

| Band | SKUs | 12m sales | % of revenue |
|---|---|---|---|
| 20+ bills/month | **828** | ₹3.84 Cr | **46.9%** |
| 4-20 bills/month | 1,411 | ₹2.06 Cr | 25.2% |
| 1-4 bills/month | 1,686 | ₹1.21 Cr | 14.8% |
| under 1 bill/month | 2,455 | ₹1.07 Cr | 13.1% |
| **never sold** | **13,101** | **₹0** | **0.00%** |

**2,239 SKUs earn 72% of revenue. 13,101 earn nothing.**

Two things follow, and they decide the whole plan:

- **Shelf space is not the constraint.** 13,101 lines can be delisted at zero revenue cost.
  What is scarce is **operator attention** — someone must price, count and reorder every
  line — and **working capital per line**.
- **A new line must clear ₹14,600-46,300/year** to deserve its place. That sizes a pilot:
  500 new lines × ₹15,000 = ₹75 lakh potential, a 10% lift. Assume half land → ~₹37 lakh
  revenue, ~₹11 lakh gross profit at the 31% retail margin, on ~₹8-10 lakh of opening
  stock.

**Keep the pilot small. The owner's instruction is explicitly not to invest heavily.**

---

## What is ruled out — never report these as gaps

| Ruled out | Why |
|---|---|
| **Eggs, meat, fish · tobacco · alcohol** | **Ethics.** Vegetarian Sikh institution. Permanent, not open to revisiting |
| LPG / gas | Campus already has a station; a gas agency is an oil-company distributorship, not a category |
| Automotive / vehicles | ARY cannot handle live vehicles |
| Newspapers | A daily paper already reaches the campus |
| Kirtan instruments | Owner's call |
| Laundry · home furnishing | Out of **expansion scope** by the owner's call. Both are still sold — laundry ₹17.4 L/yr, furnishing ₹12.0 L/yr. Scope only, not off the shelf |

A benchmark that counts a ruled-out category makes ARY look worse than it is.

**Back IN, after the owner's correction:** pet food (people on campus keep pets) and
medical devices.

**Scale DOWN:** elderly and mobility aids — there are not many elderly residents. Cover it
lightly.

---

## The measurement problem — read this before promising results

**96% of bills are booked to one anonymous walk-in account.** So if you add 500 SKUs you
will see total sales move, and nothing else. You will not know who bought, whether it
cannibalised an existing line, or which cohort responded.

**ARY already owns something like the Visa dataset** — 1.09 million transactions across a
closed 5,000-person population with no leakage to competitors, which is a cleaner panel
than any card network has. **The cardholder column is blank.**

Filling it in is what turns "we added products" into "we know what 5,000 people buy and we
can prove what a shelf change did." Two things make it cheaper than it sounds:

- A campus wallet spendable only at ARY is a **closed-system PPI** — no RBI authorisation,
  no escrow
- **FusionERP8 already ships a wallet data model that has never been used** — loyalty
  points, visit counts and CRM limits sit empty on all 3,514 customers

The credit book already proves the model works: 3,089 student and staff accounts, 75% of
outstanding under 90 days, near-zero bad debt in the dormant tail.

---

## How to actually run it

```bash
cd ~/jivo-cli/ary-cli
set -a; . ../connections/ary.env; set +a
./ary doctor                 # reachable? how fresh is each module?
```

**The CLI is read-only and cannot be made to write** — every statement passes a
SELECT-only guard inside a transaction that is always rolled back.

```bash
ary assort coverage          # per category: listed vs moving, ₹/resident/year
ary assort benchmark         # range vs an external SKU-line benchmark
ary assort velocity          # how concentrated sales are
ary assort headroom          # per counter: turns, dead range, shelf to reclaim
ary assort leak              # SKUs sold below what ARY paid
ary assort probe <words>     # does ARY carry this, wherever it is filed?
ary assort dead --by-group   # the listing tail
ary assort research          # what the research corpus holds
ary assort gaps --state missing
```

Full command map: `README.md`. Everything measured so far: `assort/vault/`.
Published brief: <https://jivo-ary.vercel.app>

---

## Where to start, if you want one answer

Run these four and read them together. They are the whole argument in about ten minutes:

```bash
ary assort leak                 # money going out the door today
ary assort benchmark            # lists 1.79x the benchmark, sells 0.59x
ary assort velocity             # 828 SKUs carry half the business
ary assort coverage             # which categories are actually thin
```

Then `assort/vault/06-playbooks/Ten-Moves.md` for the ranked build order, and
`Open-Questions.md` for the six things that need a person rather than a query.

---

## House rules

- **Read-only, always.** Never run `sapb1`. Zero write calls were made building any of this
  and that must hold.
- **Label every number** VERIFIED (query recorded) / ESTIMATED (assumption stated) /
  NOT-CHECKED.
- **Never total the research lanes' recommendations.** They sum to ₹13.3 Cr against a
  ₹7.55 Cr business — see `assort/vault/05-corrections/Fleet-Method.md`.
- **This repo is public.** `connections/ary.env` is gitignored and stays that way.
- **Keep what you get wrong.** `Corrections-Log.md` exists because five confident findings
  were refuted by the data, and the pattern is more useful than any single fact.
