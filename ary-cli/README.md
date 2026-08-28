# `ary` — read-only CLI for ARY (FusionERP8)

ARY is **Akal Rozgar Yojana, a unit of Jivo Wellness Pvt Ltd** (PAN `AACCJ4223F`)
— retail + distribution running on **FusionERP8**, three GST registrations, eleven
selling counters/warehouses, ~21k SKUs, ₹22.8 Cr of billing since April 2023.

This CLI reads its SQL Server database (`FR8HODBNEW` on `138.252.101.118`) directly.
**It cannot write.** Every statement passes a single-SELECT guard *and* runs inside a
transaction that is always rolled back — proven refused: `UPDATE`, `DELETE`, `DROP`,
`INSERT`, `TRUNCATE`, `EXEC`, `EXEC xp_cmdshell`, a comment-prefixed `EXEC`, and a
`SELECT 1; DROP TABLE …` batch (exit code 5 on all eight).

## Setup

```bash
set -a; . ../connections/ary.env; set +a     # gitignored — this repo is PUBLIC
./ary doctor
```

`ary` reads `ARY_HOST/ARY_USER/ARY_PASSWORD/ARY_DATABASE` and falls back to the
`DSR_*` names, so the existing `connections/ary.env` works unchanged. It also
auto-loads `./.env`, `./ary.env`, `./connections/ary.env`, a `.env` next to the
binary, and `~/.ary/.env`. No credential is compiled in; with no login it fails
closed with instructions.

On Windows use `ary.exe` the same way, or `connections\ary-connect.cmd` (which
strips the single quotes `cmd`'s `for /f` leaves behind — see that file's notes).

## Start here

```bash
ary doctor                  # reachable? and how fresh is every module?
ary locations               # the 3 registrations + GSTINs
ary warehouses              # the 11 counters, their SKUs and book stock
```

`doctor` is the command to run before quoting any figure: it prints the last
document date per module. Sales, purchases and transfers currently stop at
**2026-08-21** because an internal physical stock audit is in progress — that is
expected, not a broken feed. Accounting is live to today.

## Command map

| Group | What it answers |
|---|---|
| `doctor` | reachability, server, privileges, per-module freshness |
| `locations` `warehouses` | the three registrations; the eleven counters + book stock |
| `masters …` | decode tables: staff, payment-modes, units, taxes, principals, states, customer-types, voucher-types, brands, product-groups |
| `products …` | `list` `get` `count` `children` (per-location price/margin/expiry) `expiring` `sap-gap` |
| `customers …` | `list` `get` `count` `credit` (CRM flag vs real balance) `dormant` |
| `sales …` | `summary` `net` (bills − returns) `daily` `monthly` `bills` `bill` `by-product` `by-warehouse` `by-customer` `by-staff` `payment-mix` `returns` |
| `purchases …` | `summary` `monthly` `bills` `bill` `by-supplier` `by-product` `returns` `orders` |
| `stock …` | `summary` (on-hand + every movement bucket) `list` `value` `negative` `dead` `movement` `transfers` `journals` |
| `audit …` | `counts` `count` `variance` `shortage` (`--kind shortage\|excess\|wastage`) `uncounted` |
| `accounts …` | `list` `get` `groups` `outstanding` (bill-wise) `ageing` |
| `ledger …` | `list` `get` (double entry) `statement` (windowed, with opening) `trial` |
| `assort …` | the expansion question: `probe` (does ARY carry this?) `leak` (sold below cost?) `coverage` `taxonomy` `dead` `wallet` `velocity` `headroom` `benchmark` (live SQL) · `research` `gaps` `priority` `sweep` (research corpus) |
| `query` `peek` `count` `schema` | the escape hatch — still SELECT-only |

Every command takes `--json`, `--csv`, `--compact`, `--select cols`, `-n/--limit`,
`--timeout`. Date filters are `--from` (inclusive) / `--to` (**exclusive**).

## `assort` — does ARY carry everything the 5,000 need?

Baru Sahib is a closed township: about **5,000 people live there and ARY is their only
shop**. Anything ARY does not stock is either done without or bought 30-50 km away in
town. So the useful question is not "what did we sell" but "what should be on the shelf
and is not". `ary assort` answers both halves, and keeps them separate on purpose.

**Live SQL — what we have.** Always current, no corpus needed.

```bash
ary assort coverage            # the table to read first: per category, SKUs listed vs
                               # moving, sales, and spend per resident per YEAR
ary assort velocity            # 252 SKUs make 50% of revenue; 13,284 active SKUs make none
ary assort wallet              # ₹/resident/month, by counter and by category
ary assort taxonomy            # department → group → subgroup, with what actually sold
ary assort dead --by-group     # the listing tail, and whether it ties up any money
ary assort headroom            # per counter: turns, SKUs not moving, shelf to reclaim
ary assort leak                # SKUs sold BELOW what ARY paid — costed off the purchase ledger
ary assort probe <terms...>    # does ARY carry this? name-search across EVERY group
ary assort benchmark           # range vs an external SKU-line benchmark — the one table
ary assort benchmark --spend   # the ₹/resident/year capture axis instead
```

### `benchmark` — the table that answers "what should we carry?"

Compares ARY's live range against a sourced external benchmark (BigBasket BB Now metro
category counts pro-rated to 5,000 people; the metro counts verified live, the pro-rata
estimated). It reports three numbers per category — benchmark lines, what ARY **lists**,
and what ARY actually **sells** — because those diverge violently:

```
TOTAL (structural zeros excluded)   8,000 benchmark   14,344 listed   4,707 selling
                                    listed 1.79x the benchmark, selling 0.59x of it
```

Both halves are true at once, which splits the work into two opposite jobs:

- **ADD** — baby care (323 benchmark lines, *no ARY product group at all*), bakery &
  dairy (92 selling against 864), foodgrains & masala (451 against 1,913), fruits & veg
  (132 against 271, on the best-turning counter in the business).
- **DELETE** — beauty & hygiene lists **4.23×** the benchmark, cleaning & household
  **3.48×**, kitchen & pets **2.93×**. Those three hold 7,414 listed SKUs where the
  benchmark says 1,989.

A row with `addressable: 0` is a **structural zero** — eggs, meat and fish at a vegetarian
Sikh institution — and is excluded from totals rather than reported as a gap.

### `leak` — the check that found ₹2.75 lakh a year going out the door

`leak` costs every SKU off the **purchase ledger**, not the price master, because the price
master is wrong. Verified live 2026-08-28:

```
Am Lower      real cost ₹197.41   sold ₹106.62   →  −₹1.35 L/yr   price master says ₹340.00
Loose Milk    real cost  ₹51.98   sold  ₹47.00   →  −₹0.68 L/yr   price master says  ₹65.00
Red Label Tea real cost ₹206.44   sold  ₹17.33   →  −₹0.14 L/yr   price master says ₹454.92
```

**The master cost is higher than reality on every leaking row**, so a margin report built
from `ProductChildMaster` can never surface these. Loose milk's purchase cost went ₹45 → ₹55
over the year while its retail price stayed hard-coded at ₹47.00 across all 16,105 litres,
with zero variance — and the price master still showed a healthy +35% margin.

Read the two buckets differently: a sale rate below **half** the cost is usually a pricing or
single-versus-case error at the till; a small negative on large volume is a cost rise nobody
passed on. Note that the institutional bulk twins (`Dahi_Z`, `Pumpkin_Z`, `Mausambi_Z`,
`Ginger_Z`, `Paneer_Z`) are all in the list — so **a bulk price list has to be costed before
chasing more institutional volume.**

### Use `probe`, not `coverage`, to decide whether a category is missing

`coverage` groups by `ProductGroupID`, and **ARY's category tree cannot be trusted for that
question.** Verified live 2026-08-28: Loose Milk is filed under *Mini Meals*, curd under
*Others*, khoya under *Confectionery*, fresh peas under *Fruits*, kala chana under *Atta &
Other Flours*. Name-searching every dairy word finds ₹64.8 L of 12-month sales spread over
**14 groups**, with under 15% of it inside "Dairy Products". The group tag once understated
mobile accessories by **37×**.

`probe` searches product names across all 21,466 SKUs and reports where the matches
actually live:

```bash
ary assort probe paracetamol crocin dolo calpol      # 3 SKUs, 1 sold, ₹502 in 12 months
ary assort probe digene gelusil pantop omez         # 0 SKUs — a true zero
ary assort probe milk dahi curd paneer --sold-only
```

Read it as: **matched and selling** = ARY has it, wherever it is filed · **matched, not
sold** = listed, not stocked · **no match** = a real gap. Every "missing category" claim in
the research corpus should be re-tested this way before anyone buys stock against it.

### The vault — the written findings, linked

The narrative record lives in `assort/vault/`, in the same Atlas style as
`sap-b1/entry-vault/`: **26 notes, 122 wikilinks, no broken links.**

```
assort/vault/00-ARY-Atlas.md      <- START HERE. The hub; links everything.
  01-foundations/   Business-Shape · Population · Seasonality · Counters
                    Data-Quality-Traps        <- read before quoting any number
  02-categories/    Catalogue-Shape · Gap-List · Institution-Range
                    Pharmacy · Mobile-Tech · Baby-Care
  03-channels/      Institutional · JIVO-Own-Brand · Services · Digital-Identity
  04-findings/      Below-Cost-Leak · Growth-Decomposition · Pricing-Fairness
                    Stock-Variance · Basket-And-Footfall · Duplicate-Bill
  05-corrections/   Corrections-Log · Fleet-Method
  06-playbooks/     Ten-Moves · Open-Questions
```

`assort/data/VERIFIED-FACTS.md` is the raw single-file record the vault was split from —
46 numbered sections, every one carrying its query. Keep it: the vault is the readable
form, that file is the audit trail.

`per_resident_yr` is the number that makes a gap visible: it is the category's annualised
sales divided by the resident headcount, so it sits next to what an Indian household
actually spends on that category in a year. The Medicare group came out at **₹63 per
resident per year** — and `probe` then showed the real position is far starker: three
paracetamol SKUs in the whole catalogue, one of which sold, **₹502 in twelve months**.

The headcount is a **stated** figure, not a queried one. Override it with `--residents`.
Sales here are **gross of sale returns** (0.8-3.7% a year); `ary sales net` is the netted view.

**Research corpus — what people need.** These read JSON under `assort/research/`, written
by the assortment research runs. The research is done **blind to ARY's catalogue** on
purpose: an ideal-assortment list built while looking at our own shelf just reproduces our
own shelf.

```bash
ary assort research                          # what the corpus holds, and coverage % by category
ary assort gaps --state missing              # no name matches at all — the real finding
ary assort gaps --state commodity            # ARY is in the line, but not this pack or grade
ary assort gaps --state dormant              # listed but sold nothing in 12 months
ary assort gaps                              # everything that is NOT a solid line-level match
ary assort priority --p P0                   # the build order, sized in ₹/month
ary assort priority --by-category            # category totals, worst-covered first
ary assort sweep                             # the intelligence lanes
ary assort sweep --lane population           # one lane's findings, with VERIFIED/ESTIMATED per row
ary assort sweep --recommendations           # every lane's actions, ranked
```

Corpus location resolves as `$ARY_ASSORT_DIR`, else `./assort`, else `assort/` next to the
binary. To refill it after a research run:

```bash
python3 assort/bin/harvest.py --list         # what the workflow journals hold
python3 assort/bin/harvest.py <run-id> …     # write demand/ + sweep/ into assort/research/
python3 assort/bin/diff.py                   # diff demand/ against live ARY -> coverage/
python3 assort/bin/diff.py dairy --min-sales 10000
```

`diff.py` fills `coverage/` deterministically in SQL rather than with an agent, so it is
reproducible and costs nothing. It matches each researched SKU line by **name across every
product group** (never by ARY's category tag — see the `probe` note above), ANDing the
line's own qualifiers so a single generic word cannot mark a whole category covered: `milk`
alone matches 389 ARY SKUs. A line only counts as covered above a `--min-sales` floor
(default ₹5,000/yr) — without it, "Amul Taaza" turning ₹308 in a year would mark fresh milk
covered for 5,000 people.

`harvest.py` reads the workflow **journals**, not a run's final return value, so a run that
dies half way still yields everything its agents had already produced.

Every `priority` figure is an **ESTIMATE** built from a stated penetration assumption
against ~5,000 residents, and the assumption travels with the row so it can be argued
with. Every `sweep` finding carries VERIFIED / ESTIMATED / NOT-CHECKED — read that column
before quoting the number. The plan behind all of it is `assort/PLAN.md`.

## Figures this CLI is careful about

- **Net sales, not gross.** ARY has no bill cancellation — the only reversal is a
  sale-return document. `ary sales net` subtracts them and shows both halves.
- **On-hand comes from `Stock.Quantity`**, which the database's own arithmetic
  confirms on 104,221 of 104,221 rows. `ProductMaster.QuantityOnHand` is dead
  (non-zero on one SKU) and is never used.
- **Negative stock is reported, never netted away.** `ary stock value` shows
  positive valuation and the negative rows side by side, because averaging them
  hides what is actually on the floor.
- **Variance comes from `Stock`, not `TempStockTable`** — the latter is a stale
  report cache whose shortage figures are orders of magnitude too small.
- **Balances are DEBIT-positive**, matching how JIVO reads SAP.
- **`ledger statement` is windowed on purpose** (opening balance + the window's
  lines): `Cash` carries 561,552 lines and `Sales A/C` 1,088,340, so an unbounded
  running balance cannot finish inside a timeout.

## Known gaps

- **No ARY↔SAP item mapping.** `ProductCodeSAP` is present on all 21,466 SKUs and
  empty in every one (`ary products sap-gap` proves it live).
- **The login is `sa`, a sysadmin.** The guard is what prevents writes, not the
  grant. A dedicated read-only login would be better; `doctor` says so out loud.
- **No MCP server yet** — this is a terminal tool. `dsr-cli/internal/mcp` is the
  pattern to copy when ARY needs to be readable from Claude Desktop.
- Ageing is by **document date**; `RefMaster.DueDate` is populated unevenly.

## Layout

```
ary-cli/
  main.go                  entry point
  internal/config/         env + .env resolution (fails closed, no baked creds)
  internal/db/             SELECT-only guard + always-rolled-back transaction
  internal/render/         table / JSON / CSV output
  internal/cli/            root.go, domain.go (shared helpers), one file per module
  study/schema/            live column + row-count dumps (tables.csv, columns.csv)
  study/specs/             schema-notes.md — the verified facts and the traps
```

Every domain file's header comments record what was verified live and when. Read
`study/specs/schema-notes.md` before writing a new query against this database —
it is the difference between a right number and a plausible one.
