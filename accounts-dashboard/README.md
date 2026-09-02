# JIVO Accounts Board

A single page that answers the questions Accounts actually asks about JIVO's
books — who owes us, who we owe, what's stuck — read **live and read-only** from
the SAP Business One HANA database, for all three companies.

Live: <https://jivo-accounts.vercel.app>

## The one thing to understand before reading any number

**A naive SAP ageing is wrong at JIVO, by roughly 3x.** Every section that
touches open documents accounts for this; here is why it matters.

SAP shows ₹180.69 Cr of open customer invoices in the Oil book. That is not what
customers owe. ₹71.83 Cr of it is money already banked, or credit notes already
raised, that was never *matched* against the individual invoice — so the invoice
still reads `DocStatus = 'O'` long after the cash arrived. Another ₹101 Cr is
JIVO's own branch, intercompany and staff accounts, which are not trade at all.

The real external trade receivable is **₹7.43 Cr**.

The same failure runs on the payables side: bills get settled by manual journal
entries and on-account vendor payments that were never internally reconciled, so
`OPCH.DocStatus` stays open too. **`OCRD.Balance` is the ground truth for what a
party actually owes or is owed**, not the document status.

So every ageing here is *credit-adjusted*: unapplied money is netted off
oldest-document-first, and only the remainder is bucketed. Branch and
intercompany accounts are **flagged and kept**, never silently dropped or
silently included.

## Sections

| # | Section | Answers |
|---|---|---|
| 1 | Vendor Ageing | What JIVO owes each vendor, aged on the bill due date |
| 2 | Customer Ageing | What each customer owes JIVO, credit-adjusted |
| 3 | Open Item List | Every open document both sides — the drill-down behind 1 and 2 |
| 4 | GRPO | Goods received with no vendor bill booked — unrecorded liability |
| 5 | Goods Return | Stock sent back to vendors, and whether a credit note followed |
| 6 | Return Note | Customer returns in, and whether they were credited |
| 7 | Provisions Register | Provided / reversed / still standing, with the age of what's left |
| 8 | Cash Sale | Invoices settled in cash rather than on credit |
| 9 | Bank A/c Wise | Position and movement per bank account |
| 10 | Bank Reconciliation | What SAP knows about reconciled vs unreconciled bank items |
| 11 | Transporter | Dispatch value by transporter, from the invoice UDFs |

## Every query was adversarially reviewed

Each of the 11 queries was written by one agent and then attacked by a second one
whose job was to prove it wrong — against live SAP, on all three books, re-deriving
each headline by an independent route. **All 11 came back FIXED. None was sound as
first written.** Three defects were critical:

| Section | What was wrong |
|---|---|
| `cash-sale` | 128 money cells rendered as raw float noise (`1358792.4106999983`) beside properly formatted ones. It was the only query in the pipeline with no `ROUND()`. |
| `bank-accounts` | Cancelled payments double-counted in every gross-movement column. SAP posts a cancellation as the original **plus** a mirror. Inflation: Oil +₹146.80 Cr (+14.5%), Mart +20.5%, Bev +11.6%. Fixed by anti-joining `OJDT."StornoToTr"`. |
| `transporter` | The freight-vendor universe was defined by supplier group alone, so R K TANKER SERVICE (₹945.12 L, filed under `PURCHASE OIL`) was invisible — more than the entire freight figure the section reported. The page printed "no freight vendor card matched" next to it, which was false. |

Plus 25 major findings, including: vendor-ageing's `--as-of` re-bucketed without
moving the position; open-item-list filed vendor refunds as customer receipts
(`ORCT."DocType"='S'` is money back **from a vendor**); GRPO's GR/IR headline
included JIVO's own branch cards; and cash-sale's breakdowns didn't add up to its
own total. Each section's `pipeline/notes/<id>.md` records what was attacked, what
survived, and what is still unresolved.

Two claims in the original SQL headers turned out to be **factually wrong** and were
corrected rather than trusted: return-note told operators to discard a figure that
was correct, and bank-reco claimed branch/intercompany doesn't apply to G/L accounts
when `JDT1."BPLId"` is populated on every bank line.

## Read-only, by construction

This honours **CLAUDE.md RULE 0**. The pipeline issues no write of any kind to
SAP. It goes through `hana-sql`, which allows only `SELECT`/`WITH`, refuses 33
mutating keywords anywhere in the statement, runs inside a HANA read-only
transaction and never commits. Nothing here can create, change or delete a
document, a master record or a journal entry.

## How it is built

```
pipeline/
  sql/<section>.sql          one HANA query per section, written once
  sql/<section>-detail.sql   optional drill-down companion
  notes/<section>.md         what the query does, the traps, the live numbers
  build_data.py              runs every .sql against all 3 books -> site/data.json
  refresh.sh                 build -> deploy -> re-open public -> verify 200
  raw/                       last raw TSV per section+company, for debugging
site/
  index.html                 the board (self-contained: no CDN, no framework)
  data.json                  built artefact
```

Each `.sql` is written **once** with two placeholders and executed three times:

| Placeholder | Substituted with |
|---|---|
| `{{SCHEMA}}` | `JIVO_OIL_HANADB` / `JIVO_MART_HANADB` / `JIVO_BEVERAGES_HANADB` |
| `{{ASOF}}` | the position date, `YYYY-MM-DD` (default: today) |

**Money-unit convention.** The column *name* carries the unit, so each query can
return whatever scale reads best in a TSV, and the page still formats it right:

| Suffix | Unit |
|---|---|
| `..._L` | INR lakhs |
| `..._CR` | INR crores |
| `..._INR`, anything else | INR rupees |

## Running it

```bash
python3 pipeline/build_data.py                     # today, all sections, all books
python3 pipeline/build_data.py --only vendor-ageing,bank-reco
python3 pipeline/build_data.py --company oil
python3 pipeline/build_data.py --as-of 2026-03-31  # see the warning below first
```

> **`--as-of` does not give you a true point-in-time position.** SAP keeps no
> history of `PaidToDate` or `OCRD.Balance`, so a past date ages *today's* open
> items against an older calendar. Measured on Oil: `--as-of 2026-03-31` reports
> a ₹80.34 Cr adjusted receivable against ₹108.86 Cr today, and ₹2.87 Cr of trade
> against ₹7.43 Cr. It is useful for looking at document dates and ageing
> buckets; it is **not** a March closing balance. Use today's date for any figure
> that leaves the building.

Exit codes: `0` ok · `1` no route to HANA or a SQL failure · `2` a sanity guard
refused to publish. On `1` or `2` the previous `data.json` and the previous
deployment are left untouched and still serving — a bad build never takes the
board down.

The guards refuse to write when a section errors, when a section returns zero
rows across all three books, or when a section's row count collapses by more
than half against the last build. Override with `--no-guard` only when you know
why the shape changed.

### Connection

`build_data.py` probes the direct office route first (8s fuse), then the home
bridge on `127.0.0.1:13015`, and re-raises that bridge itself if the port is
dead. Off the office network everything rides
`connections/sap-home-bridge.sh` → VPS-parked hanadb ports → SAP. Nothing
depends on an office PC being switched on.

### Live refresh — every 2 minutes, on the VPS

`pipeline/live-refresh.sh` runs from cron on the always-on VPS, which reaches
HANA directly on its own parked port (`127.0.0.1:43015`) with no bridge hop — a
full build there takes **~37s**, against ~81s from the Mac.

```
*/2 * * * * /root/jivo-cli/accounts-dashboard/pipeline/live-refresh.sh
```

Three things make a 2-minute loop safe to point at a production ERP:

| Guard | What it prevents |
|---|---|
| **`flock`** | A slow build stacking on the previous one. If a run is still going, the tick exits silently. |
| **Change detection** | Deploying when nothing happened. The build is hashed with `generated_at`/`build_seconds`/timings stripped, so only real business data counts. Quiet stretches produce **zero** deploys — Vercel is touched only when someone actually posted in SAP. |
| **Cadence gate** | Querying production 720 times a night to prove the books didn't move. Outside 07:00–23:00 IST it runs only on the half hour. |

A failed or partial build never reaches the hash check, so the last good
deployment simply keeps serving. Log: `pipeline/live-refresh.log`.

**Load, stated plainly:** 37s of serial analytical queries every 120s is roughly
a **31% duty cycle** on one HANA session during the working day, and one session
every 30 minutes overnight. Narrow it by editing `ACTIVE_FROM`/`ACTIVE_TO` in the
script, or change the cron to `*/5` if that's still more than Accounts needs — the
board's numbers do not move faster than someone can key an invoice.

The page polls `data.json` every 2 minutes and re-renders in place, preserving
scroll position and the selected company, so a tab left open stays current
without anyone reloading. The masthead shows "updated N min ago" with a live dot.

### The Mac daily refresh — built, not enabled

`pipeline/refresh.sh` rebuilds, deploys, strips Vercel's SSO gate (new projects
default to gated) and verifies the page answers `200` logged-out. Log:
`pipeline/refresh.log`.

It is **not scheduled by default**. It redeploys a public page every morning, so
turning it on is a deliberate choice. A ready launchd job sits next to it:

```bash
cp pipeline/com.jivo.accounts-board-refresh.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.jivo.accounts-board-refresh.plist   # 09:15 daily
launchctl unload ~/Library/LaunchAgents/com.jivo.accounts-board-refresh.plist # off again
```

**The VPS is the better home.** A Mac agent only fires when this laptop is awake,
and the godown board's equivalent agent is currently disabled for that reason. The
VPS is always on, is already the fleet's cron hub, and reaches HANA directly on its
own parked port (`127.0.0.1:43015`) with no bridge hop — set `HANA_ENV_FILE` to an
env file pointing there and `HANA_BRIDGE_CMD=true`.

## Design

Same **JIVO daylight** light language as the godown board — brand green
`#0A7D3F` on cream, from jivo.in. Light-only on purpose: it is read in office
daylight, on a phone.

The categorical palette (`#0A7D3F #1D63C4 #C2610A #8B2E9E #0894B0 #B01253`) was
validated, not eyeballed — lightness band, chroma floor, colour-blind separation,
normal-vision separation and contrast all pass. Ageing buckets use a sequential
warm ramp, light→dark, with "not due" held out in brand green as a *state*
rather than a step. The two lightest ramp steps fall under 3:1 on cream, so every
ageing mark carries a visible value label and a table view.

## What this cannot tell you

- **Bank reconciliation is SAP-side only, and thinner than it looks.** No external
  bank statement is loaded, and `OBNK."balance"` is `0.000000` on all 259 rows
  across all three books — SAP holds no bank-supplied closing balance anywhere. So
  the section can tell you *whether and when* a reconciliation happened, and what
  has never been reconciled at all, but never whether a reconciliation was right.
  The tie-out shown compares the book balance against a book-derived agreed
  balance; it is an internal consistency check, not "per bank statement vs per
  books". Getting the real thing needs the statement files.
- **Group totals include intercompany.** Switching to *Group* sums the three
  books; JIVO's inter-book trading is not eliminated. Read per-company figures
  for anything that matters.
- **`DocStatus` is unreliable** (see above). Where a section still has to lean on
  it, its note says so.
