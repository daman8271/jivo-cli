# JIVO Accounts Board v2 — multi-page, drill-down to the source

**Written 2026-08-22.** Supersedes nothing: v1 (`jivo-accounts.vercel.app`) keeps
serving untouched until v2 is verified and cut over.

Daman's brief, in his words:

1. Everything super detailed — click any number, see the detailed breakdown of
   **how that number is made**. For every section, not just one.
2. This dashboard is his whole SAP life. It must update **every 30 minutes**.
3. More charts and visuals — seeing beats reading.
4. Lots of pages, all of them opened up and broken down.
5. *(added mid-brief)* **the data must be very accurate.**

---

## 0. What was already broken, found while reading the code

Before any of the below: the live board **had been frozen for 5 hours** when this
plan was written.

| | |
|---|---|
| Symptom | `live-refresh.sh` failing every 2 min since 13:42 IST |
| Cause | commit `52e9843` shipped a **darwin/arm64** `hana-sql` binary; the VPS pulled it at 13:43 and Linux cannot execute a Mach-O — `[Errno 8] Exec format error` |
| Blast radius | every tick failed, the guard correctly refused to publish, so the **last good deployment kept serving** — silently, with no banner, showing 13:42 numbers as if they were live |
| Fixed | built a native linux/amd64 `hana-sql` on the VPS → `/usr/local/bin/hana-sql`; `live-refresh.sh` now prefers it on Linux so a future `git pull` cannot re-break it. Verified: `PUBLISHED (50s build, HTTP 200)`, `generated_at 2026-08-22T18:50:32+05:30` |

**This is the single most important requirement in the plan.** A board that
freezes without saying so is worse than a board that is down, because the
operator acts on stale figures believing they are live. v2 must make this
failure mode *impossible to miss* — see §5.

---

## 1. Four principles the whole build answers to

1. **Every number is a link.** No figure on any page is a dead end. Click it and
   you get the derivation: the formula, each term, where each term came from,
   the exact SQL, what was excluded and why.
2. **Derivation is data, not prose.** The pipeline emits the derivation from the
   *same query that produced the number*. The frontend renders it; it never
   re-derives it. One definition, computed once, server-side. This is what makes
   the drill-down trustworthy rather than a second implementation that drifts.
3. **Never a confident zero.** (v1 rule, kept and hardened.) A section that
   failed renders as failed. A number that could not be computed renders as
   "not computed", never as ₹0 and never as an em-dash that reads like nil.
4. **Freshness is loud.** Stale beyond 30 minutes in working hours is a red
   banner naming the failing section and the log line — not a quiet old number.

---

## 2. Where the numbers stand right now (live, 2026-08-22 18:50 IST)

Pulled live from the deployed `data.json` while writing this — these are the
figures v2 must reproduce exactly on day one, and they are the regression
baseline.

| Book | Trade receivable | Trade payable | Vendor cards |
|---|---:|---:|---:|
| Oil | ₹7.35 Cr | ₹22.68 Cr | 635 |
| Mart | ₹10.30 Cr | ₹1.59 Cr | 82 |
| Beverages | ₹3.84 Cr | ₹1.37 Cr | 161 |

*Trade = `ACCT_KIND`/`KIND` = TRADE, i.e. branch, intercompany and staff
accounts excluded but retained and flagged. Group totals are not eliminated for
intercompany — see §7.*

**The drill-down surface** — every row below is something a human can click into:

| Section | Summary rows (3 books) | Detail rows (3 books) |
|---|---:|---:|
| open-item-list | 5,452 | — |
| vendor-ageing | 896 | — |
| grpo | 429 | 786 |
| transporter | 296 | 500 |
| return-note | 214 | 1,185 |
| cash-sale | 171 | — |
| bank-reco | 135 | 259 |
| bank-accounts | 132 | — |
| provisions | 132 | — |
| goods-return | 127 | 209 |
| customer-ageing | 15 | 1,193 |
| **Total** | **8,003** | **4,128** |

**12,131 clickable rows.** That settles an architecture question: entity pages
cannot be pre-rendered static files. They are one page template resolved from a
query string against a loaded data slice.

---

## 3. Architecture

### 3.1 Why not React/Next

v1 is a single self-contained `index.html` — no CDN, no framework, no build
step — deployed by `vercel deploy --prod` straight from `site/`. That property
is worth keeping: it deploys in seconds, has no dependency surface, no npm
supply chain, and renders instantly on an Accounts phone in office daylight.

v2 stays **real multi-page static HTML + shared ES modules**. Real URLs, real
back button, no hydration, no build step. Client-side routing is used *only*
inside entity pages (`party.html?co=oil&card=VENDA000483`), where 12k static
files would be absurd.

### 3.2 Data layer — the biggest change

`data.json` is **10.7 MB** today, fetched whole every 2 minutes by every open
tab. For a multi-page board that is untenable. Split it:

```
site/data/
  manifest.json                 ~15 KB   build stamp, section status+timings,
                                         hero KPIs with their derivation ids,
                                         freshness state.  Polled every 60 s.
  <section>.<company>.json      33 files loaded on demand, one per page
  derivations.<company>.json    the derivation records (§3.3)
  parties.<company>.json        search index: card, name, group, balance, kind
  history.jsonl                 append-only KPI history (§3.5)
```

Initial page load goes from 10.7 MB to ~15 KB + one slice.

### 3.3 `pipeline/derive.py` — the derivation engine (the heart of the brief)

A declarative registry. Each KPI is one record:

```python
KPI("ar-trade-open",
    label   = "Customers owe JIVO",
    unit    = "INR",
    section = "customer-ageing", column = "EFF_OPEN_INR",
    filter  = "KIND == 'TRADE'",
    formula = "RAW_OPEN − UNAPPLIED_CREDIT = EFF_OPEN",
    terms   = ["RAW_OPEN_INR", "UNAPPLIED_CREDIT_INR", "EFF_OPEN_INR"],
    excludes= ["BRANCH", "INTERCO", "STAFF"],
    sql     = ("sql/customer-ageing.sql", 118, 173),
    caveats = ["C-0019", "C-0005", "C-0023"],
    drill   = ("receivables.html", {"kind": "TRADE"}))
```

The pipeline computes value **and** derivation together and writes both. Every
KPI gets a stable id, so `derivation.html?k=ar-trade-open&co=oil` is a
permanent, shareable URL for "how that number was made".

A derivation page shows, for one number:

- the headline value, big, with its unit and as-of stamp
- the **formula**, rendered as a term-by-term waterfall chart
- a **term table**: each term's value, its SAP column, its source table, and a
  link to the rows that make it up
- **what was excluded** and the amount excluded (branch / intercompany / staff),
  each expandable to the actual card codes — never a silent drop
- the **exact SQL**, syntax-highlighted, with the contributing lines marked
- the **caveats** that apply (`C-00xx` corrections), quoted in full
- the **independent check** (§3.4): same number by a second route, and the delta
- **contributing rows**, sorted by size, each a link to its own entity page

### 3.4 `pipeline/verify.py` — accuracy, made continuous

The v1 README says all 11 queries were adversarially reviewed once and all 11
came back FIXED. That review was a moment in time. v2 makes it a heartbeat.

Every build, each headline is **re-derived by an independent route** and
compared:

| KPI | Primary route | Independent route |
|---|---|---|
| Trade receivable | `customer-ageing.EFF_OPEN_INR` | sum of `open-item-list` customer rows, credit-adjusted |
| Trade payable | `vendor-ageing.ADJ_OPEN` | sum of `open-item-list` vendor rows |
| GRPO unbilled | `grpo.UNBILLED_GROSS` TOTAL row | sum of `grpo` detail rows where `HAS_AP_INVOICE = 0` |
| Net bank | `bank-accounts` TOT_* columns | sum of per-account `BALANCE_L` by category |
| Provisions standing | `provisions.OUTSTANDING_CR_L` | `CREATED_CR − REVERSED_DR` per account |
| Faceted totals | TOTAL row | sum of CLASS rows, and sum of MONTH rows |

Each check writes `{ok, alt_value, delta, delta_pct, method}` into the manifest.
Every headline on every page carries a small **green / amber / red dot**; the dot
is a link to the check. A red dot does not hide the number — it says which two
routes disagree and by how much.

Additional standing checks:

- **Additivity**: group = oil + mart + bev, with the intercompany component
  named separately (C-0005: 23 group CardCodes).
- **Correction compliance**: each of C-0001, C-0005, C-0019, C-0020, C-0021,
  C-0022, C-0023 mapped to the line of SQL or Python that honours it, with a
  test that fails the build if the guard is removed.
- **Term closure**: every derivation's terms must sum to its value within
  0.5 paise, or the build refuses to publish.

### 3.5 History — `data/history.jsonl`

v1 keeps no history, so nothing can trend. Append one line per publish (deduped
to at most one per 30 min) with the hero KPIs and section row counts. That
unlocks sparklines on every KPI card, "moved ₹X since yesterday" deltas, and a
build-health timeline — cheap, and it makes the board tell a story instead of a
snapshot.

---

## 4. Page map

Twenty page templates. Every one reachable from the one above it, every number
on it reachable from the one below.

### Level 0 — Overview (`index.html`)
Masthead, company switch (Oil / Mart / Bev / Group), freshness dot, 8 hero KPI
cards **each with a sparkline and a check dot**, a group-vs-company comparison
bar, section health strip, and "what moved today".

### Level 1 — eleven section pages

| Page | Section | The question |
|---|---|---|
| `receivables.html` | Customer Ageing | who owes us, credit-adjusted |
| `payables.html` | Vendor Ageing | who we owe, aged on due date |
| `open-items.html` | Open Item List | every open document, both sides |
| `grpo.html` | GRPO | goods in, no bill booked |
| `goods-return.html` | Goods Return | stock back to vendors, credited? |
| `return-note.html` | Return Note | customer returns in, credited? |
| `provisions.html` | Provisions | provided / reversed / still standing |
| `cash-sale.html` | Cash Sale | settled in cash, not credit |
| `banks.html` | Bank A/c Wise | position and movement per account |
| `bank-reco.html` | Bank Reconciliation | reconciled vs not, and how stale |
| `transporter.html` | Transporter | dispatch value by transporter |

Each section page carries: its own KPI row (with check dots), 3–5 charts, a
filterable/sortable table, the section's caveats, its SQL, and its
`pipeline/notes/<id>.md` rendered inline — so the trap that makes a naive
version wrong is on the page, not in a repo nobody opens.

### Level 2 — entity pages (the real drill-down)

| Page | Resolves | Shows |
|---|---|---|
| `party.html?co=&card=` | one customer or vendor | ledger position, the raw→adjusted waterfall, bucket chart, every open document, unapplied receipts/payments, open credit notes, 12-month activity, links to each document |
| `document.html?co=&type=&entry=` | one invoice / bill / GRPO / return / payment | header, open amount, what is applied against it, its base document chain (PO → GRPO → A/P invoice), its credit notes, its journal lines |
| `bank-account.html?co=&acct=` | one bank account | 12-month in/out/net series, reco history, unreconciled ageing, dormancy |
| `gl-account.html?co=&acct=` | one provision / GL account | created vs reversed vs standing, ageing of the un-reversed balance, posting history |

### Level 3 — derivation (`derivation.html?k=&co=`)
Described in §3.3. Reachable from **every** number on **every** page.

### Support pages

| Page | Purpose |
|---|---|
| `methodology.html` | the definitions that make the numbers mean something: ledger balance sign convention, turnover net of GST, credit-adjusted ageing, the 23 intercompany CardCodes named, every `C-00xx` correction in full, and what this board **cannot** tell you |
| `health.html` | pipeline health: last N builds, per-section timings, failures with their log lines, freshness clock, guard status, HANA route in use |
| `search.html` | global search across parties and documents, all three books |

---

## 5. The 30-minute guarantee

He asked for 30 minutes. The VPS cron already runs **every 2 minutes**, which is
better — but as §0 proved, "scheduled" is not "working". So v2 guarantees the 30
minutes rather than assuming it:

1. **Preflight, every tick.** Before touching SAP: is the `hana-sql` binary
   executable *on this OS*, is HANA reachable, are all 11 SQL files present. A
   preflight failure is logged as `PREFLIGHT FAIL` and alerts — it does not
   silently fall through to a build failure, which is how today's freeze hid.
2. **A 30-minute floor.** If no successful publish in 30 minutes between 07:00
   and 23:00 IST, force a build ignoring change-detection. If *that* fails,
   write `stale: true` plus the failing reason into `manifest.json`.
3. **The page believes the clock, not the file.** Every page computes staleness
   from `generated_at` against the browser clock. Past 30 minutes in working
   hours: a red masthead banner — *"These numbers are N minutes old. Last build
   failed: <reason>."* The numbers stay on screen; they are just no longer
   presented as live.
4. **`health.html` and a fleet alert.** The health page shows the build
   heartbeat. A second consecutive failure pings the fleet.
5. Cadence gate and `flock` stay as they are — they are correct.

---

## 6. Charts

v1 has two chart types (horizontal bars, ageing stack). v2 adds a small SVG
chart module — no library, validated palette already in the repo
(`#0A7D3F #1D63C4 #C2610A #8B2E9E #0894B0 #B01253`, lightness-band and
colour-blind checked).

| Chart | Where it earns its place |
|---|---|
| **Waterfall** | raw open → credit applied → adjusted → less branch/interco → trade. The single most important chart in the board: it *is* the correction, drawn. |
| **Sparkline** | on every KPI card, from `history.jsonl` |
| **Pareto** | payables/receivables concentration — "8 vendors are 80% of what we owe" |
| **Treemap** | top payables/receivables by size, one glance |
| **Donut** | composition: trade vs branch vs intercompany vs staff |
| **Stacked bar** | ageing buckets (kept from v1, value labels kept — the two lightest ramp steps fail 3:1 on cream) |
| **Line / area** | 12-month bank movement, already in the data as `MONTHLY_*_SERIES` |
| **Scatter** | age vs amount — finds the big old ones instantly |
| **Heatmap** | month × ageing bucket, month × section activity |
| **Meter** | fill %, reconciled %, named-transporter % |
| **Flow (Sankey-lite)** | PO → GRPO → A/P invoice → payment, with the drop-offs |

Rules carried over and enforced: every mark carries a value label, every chart
has a table view behind it, nothing relies on colour alone, no horizontal
overflow at any nesting level.

---

## 7. Honesty carried forward

These stay on the board, stated on the page rather than buried:

- **Group totals include intercompany.** JIVO's inter-book trading is not
  eliminated. Per-company is the figure that means something.
- **`DocStatus` is unreliable** (C-0019). `OCRD.Balance` is ground truth.
- **Bank reconciliation is SAP-side only.** `OBNK.balance` is `0.000000` on all
  259 rows in all three books — SAP holds no bank-supplied closing balance. The
  tie-out is an internal consistency check, not statement-vs-books.
- **`--as-of` is not a point-in-time position.** SAP keeps no history of
  `PaidToDate` or `OCRD.Balance`.
- **Read-only, by construction.** Honours RULE 0. `hana-sql` accepts only
  `SELECT`/`WITH`, refuses 33 mutating keywords, runs in a HANA read-only
  transaction, never commits. v2 adds no write path of any kind.

---

## 8. Build order

| Phase | What | Agents |
|---|---|---|
| **P1 Inventory** | one agent per section: read its SQL + notes + v1 render code, emit a structured spec — every KPI, its formula, its terms, its drill-down targets, its caveats | 11 |
| **P2 Foundation** | data splitter · derivation engine · verify engine · shared JS core + CSS design system + chart module | 5 |
| **P3 Pages** | one agent per page template, consuming its P1 spec and P2 foundation | 18 |
| **P4 Verify** | adversarial recompute per KPI · drill-down link integrity · layout/overflow/contrast · correction compliance | ~12 |
| **P5 Ship** | full build → deploy to `jivo-accounts-v2` → open public → verify logged-out 200 → cut over | 1 |

**Deployment is staged.** v2 builds into `accounts-dashboard/site-v2/` and
deploys to a **separate Vercel project**. `jivo-accounts.vercel.app` keeps
serving v1 throughout. Cutover happens only after P4 is green and Daman has
looked at v2 — and it is a one-line change back if he wants v1 again.
