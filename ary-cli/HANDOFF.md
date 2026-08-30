# HANDOFF — ARY expansion. Read this whole file before doing anything.

**From:** the previous Claude session (context window full)
**Date:** 2026-08-31
**Working dir:** `~/jivo-cli/ary-cli`

---

## THE JOB — in Daman's own words. Do not drift from this.

> "What products do 5,000 people need in their life? What do we have and how much more do
> we need? And how should we prioritize which product we should bring first?"

That is the ENTIRE job. Three deliverables:

1. **NEED** — the list of products 5,000 campus residents need, by category
2. **HAVE vs NEED** — for each category: what ARY has, what is missing, how much more is needed
3. **PRIORITY** — a ranked list of which products to bring FIRST, with reasoning

**The previous session drifted.** It produced an "availability, not assortment" thesis, a
presentation website, a vault of findings, and a lot of self-correction. Some of that is
useful raw material (listed below), but **the user did not get his three deliverables and
he is rightly angry.** Give him the simple thing: NEED / HAVE / GAP / PRIORITY, per
category, in a table he can hand to the ARY team.

---

## What already exists that you should USE (do not redo)

| Asset | Where | State |
|---|---|---|
| **The NEED list — deliverable 1 is essentially DONE** | `assort/research/demand/*.json` | 46 categories, 2,572 SKU lines, 1,135 must-have. Each line: name, examples, pack sizes, price band, cohort, essentiality, frequency. Built blind to ARY's catalogue |
| Partial priority output | `assort/research/priority/*.json` | 21 of 46 categories, agent-written, NOT audited — treat as draft |
| Read-only CLI | `./ary` (env: `set -a; . ../connections/ary.env; set +a`) | `ary assort probe <stem>` = name-search all 21,479 SKUs. `ary query "SELECT ..."` = raw SQL. Cannot write, ever |
| Owner's brief | `assort/vault/01-foundations/Owner-Brief.md` | What the owner wants: EVERYTHING stocked, small pilot first, don't invest heavy. Pet food IN, medical devices IN, few elderly people |
| Scope exclusions | Never count as gaps: eggs/meat/fish, tobacco, alcohol (ethics — permanent), LPG, vehicles, newspapers, kirtan instruments; laundry + furnishing out of expansion scope only |
| Verified facts + all corrections | `assort/data/VERIFIED-FACTS.md`, `assort/vault/` | Background. Do not rebuild it |

## What is BROKEN that you must not trust

1. **`assort/research/coverage/*.json` — the HAVE-vs-NEED matching — is unreliable.**
   Two incompatible formats; 9 of 46 categories read exactly 100% covered (permissive
   substring matcher); the specific/broad quality tier carries no information (five files
   book the identical banana figure, two labelled "specific"). **Deliverable 2 must be
   redone properly.** This is the main work remaining.
2. **Name-matching has produced SIX false findings** in this project. ARY's spellings:
   "Paracitamol", "Thrermometer", "Diclowin", "Stiching", "Miada", "Lmk" (a bakery brand —
   probing "gas" matched Gas Stove and invented an LPG business). Rules: probe STEMS not
   words; always read the SKUs block, never the verdict row; in scripts quote args
   (zsh word-splits `$t` and a scripted zero looks identical to a real gap).
3. **ARY's category tree lies** — Loose Milk is under "Mini Meals", curd under "Others".
   Never answer "do we carry X" from ProductGroupID. Names only.
4. **Count PRODUCTS (ProductID), never ProductChildID** — a child is a price-revision row,
   3.17 per product. This error inflated a 51% figure to 75%.
5. **Cost = purchase ledger (`PurchaseDetail`), never `ProductChildMaster`** (stale, biased
   high). Stock value = row-wise `SUM(Quantity*PurchaseCost)`, never `SUM(qty)*MAX(cost)`.
6. Exclude customer `002CM` (Hunger Heroes, a Delhi NGO buying wholesale at 1% margin)
   from anything called "retail".

## Facts you can rely on (each survived three passes of checking)

- Retail: **₹6.96 Cr / 12m, 372,366 bills, ₹187 avg, 1,026 bills/day**
- **6,148 products sold in 12m; 3,147 (51.2%) have zero stock today** — so when you compute
  "what ARY has", distinguish *listed*, *in stock now*, and *actually selling*
- 895 regular sellers (sold ≥20 days) are at zero; 94% were still being purchased
- Hard zeros verified at stem level: chronic-disease medicines (38 stems, 0 SKUs),
  glucometer, BP monitor, pregnancy test, reading glasses, denture care, menstrual cups
- Working SKU economics: a performing line earns ₹14,600–46,300/yr; retail GM ≈ 20–24%
- Fruits & Veg playbook: ~55 SKUs, run-rate in month 2, 172 stock turns — narrow and deep wins

---

## THE PLAN — do this, in order, nothing else

### Step 1 — Rebuild HAVE vs NEED honestly (the main job)

For each of the 46 demand categories, for each of its SKU lines, decide ONE of:
- **HAVE** — ARY sells it and it moved in 12m (name-match at stem level + sales check)
- **LISTED-DEAD** — in the catalogue but no sales / no stock
- **MISSING** — nothing matches after honest stemming

Method that works: for each line take the researcher's `examples` (real brand names) plus
distinctive nouns; stem them; probe/SQL each; READ the matched SKU names before accepting.
Use ONE method for all 46 so the numbers are comparable. Batch by category; verify a sample
by hand in each before accepting the batch.

Output per category: `lines_total / have / listed_dead / missing / completion_%` plus the
missing lines themselves. THIS gives Daman his "what do we have and how much more do we
need".

### Step 2 — Priority (deliverable 3)

Score every MISSING (and LISTED-DEAD must-have) line:

`priority = essentiality × cohort size × margin band × ease` where ease = no licence,
no cold chain, existing supplier reach (supplier list: `assort/vault/` Institutional note —
10+ HP wholesalers, a Chandigarh bulk route, a daily milk route already exist).

Owner's named pilot categories — male grooming, cosmetics, sunscreen — get a bump: his
call. Output: ONE ranked table, top ~100 lines, with per-line: category, line, why, est.
₹/month at ARY's real per-SKU economics, and what it needs (nothing / supplier / licence /
cold chain). Cap total pilot investment ~₹8–10 lakh — owner said small.

### Step 3 — Present it SIMPLY

One page or sheet: 46 rows (category, have, missing, completion %), then the top-100
ranked add list. That's it. No thesis, no dot grids, no corrections essay. The site at
https://jivo-ary.vercel.app exists; replace or extend it ONLY if Daman asks.

---

## House rules

- **READ-ONLY. Never run `sapb1`.** The `ary` CLI cannot write (SELECT-only guard).
- Repo is PUBLIC; `connections/ary.env` is gitignored — keep it out. Commit by pathspec
  (`git add -- ary-cli/`), the index often holds other people's work.
- Every number: carry its query. VERIFIED / ESTIMATED / NOT-CHECKED.
- Daman's style: answer first, short, no jargon, no essays. He says "resumption" to mean
  this whole task. If he pushes back — he's usually right; check before defending.
