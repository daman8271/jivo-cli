---
type: index
system: ARY / FusionERP8
source: FR8HODBNEW (live, read-only)
mined: 2026-08-29
window: 12 months to 2026-08-21
---

# ARY Atlas — the only shop for 5,000 people

> **Start here.** This vault answers one question: *ARY is the only shop for the ~5,000
> people who live at Baru Sahib — what should it sell that it doesn't?*
>
> The answer turned out not to be a list of products. See [[Catalogue-Shape]].

## The finding, in three lines

**ARY does not have an assortment problem. It has an availability problem.** It lists
**1.79×** the benchmark range and sells **0.59×** of it — 19,481 active SKUs, 6,197 selling,
matching a whole tier-3 city's q-commerce network. Meanwhile **₹3.06 lakh a year** goes out
the door on 27 lines sold below what ARY paid ([[Below-Cost-Leak]]).

Adding thousands more SKUs to a catalogue where 68% never sell would make it worse.

## The rules this vault is built on

- Every number was measured against the live books, and the note carries the query.
- **VERIFIED / ESTIMATED / NOT-CHECKED** are labelled separately. A well-structured
  explanation is not evidence.
- **The burden of proof sits on "missing", never on "covered."** Four times in this exercise
  a confident finding was an artefact of a broken field — [[Data-Quality-Traps]].
- Read-only. Nothing here was produced by writing to any JIVO system; zero `sapb1` calls
  across ~280 research agents.
- What this exercise got wrong is kept, not deleted — [[Corrections-Log]].

## Read these first

- **[[Owner-Brief]]** — what ARY is actually trying to do, in the owner's own terms. This
  outranks any inference elsewhere in the vault.

- **[[Ten-Moves]]** — the ranked build order. Start at move 0; it is losing money today.
- **[[Open-Questions]]** — six things no agent can answer. They gate most of the ten moves.
- **[[Data-Quality-Traps]]** — read before quoting any number from this database.

## Foundations — what ARY is

- **[[Owner-Brief]]** — the ask, the six-step method, the shelf-replacement arithmetic
- **[[Business-Shape]]** — revenue by year, the books, and the resolved question of whether
  ARY is profitable (it is: ~₹76 lakh/yr, ~11.6% net)
- **[[Population]]** — who the 5,000 are, and why the cohort is flat to shrinking
- **[[Seasonality]]** — January empties the township; one 27-day window carries the year
- **[[Counters]]** — eleven counters, three switched off with live populations behind them

## Categories — what is on the shelf

- **[[Catalogue-Shape]]** — the benchmark table and the availability finding
- **[[Gap-List]]** — probe-verified gaps, not diff-derived
- **[[Institution-Range]]** — dastar, patka, the Five Ks. No retail benchmark contains these
- **[[Pharmacy]]** — 26 strips of paracetamol in a year, and the blocker nobody would guess
- **[[Mobile-Tech]]** — a real ₹1.58 lakh business at 40% margin, hidden in three SKU codes
- **[[Baby-Care]]** — a gap that turned out to be an empty shelf

## Channels — who buys

- **[[Institutional]]** — the largest number in the vault, and its largest caveat
- **[[JIVO-Own-Brand]]** — ARY is a 5,000-person consumer test market nobody is reading
- **[[Services]]** — tailoring is already a business, unmanaged
- **[[Digital-Identity]]** — UPI is 55.7% of tenders; 96% of bills are anonymous

## Findings — what the data surfaced

- **[[Below-Cost-Leak]]** 🔴 — the only finding losing money *now*
- **[[Growth-Decomposition]]** — 89.8% of growth came from two NEW counters, not the store
- **[[Pricing-Fairness]]** — ₹300/yr above MRP. ARY does not exploit its captive market
- **[[Stock-Variance]]** — 4.1% of sales, and both halves are huge
- **[[Basket-And-Footfall]]** — two customers, two peaks, one basket
- **[[Duplicate-Bill]]** — flagged for Accounts, not acted on

## Method — and what it got wrong

- **[[Corrections-Log]]** — five errors, each plausible enough to have cost money
- **[[Fleet-Method]]** — ~280 agents, and why their aggregate number is worse than useless

## The instrument

This vault is re-derivable, not a one-off. `ary assort` — 13 commands built for these
questions:

```bash
ary assort probe <words>    # does ARY carry this? name-search across EVERY group
ary assort leak             # SKUs sold below what ARY paid, off the purchase ledger
ary assort benchmark        # range vs an external SKU-line benchmark
ary assort coverage         # per category: listed vs moving, ₹/resident/yr
ary assort velocity         # 252 SKUs = 50% of revenue; 13,284 = none
ary assort wallet           # capture per resident, by counter and category
ary assort headroom         # turns, dead range, shelf to reclaim
ary assort gaps --state missing    # from the research corpus
```

Full command map and the research-corpus workflow: `ary-cli/README.md`.
The raw single-file record every note here was split from: `assort/data/VERIFIED-FACTS.md`.
The published brief: <https://jivo-ary.vercel.app>

## What is still running

The research fleet has **~90 of ~145 agents unfinished** at the last quota wall, including
**every `verify` lane** — so nothing in the research corpus has been adversarially
challenged. Findings marked VERIFIED here were checked by hand against the live database and
do not depend on it. Figures sourced from research lanes carry a single pair of eyes.

Corpus state: `ary assort research`.
