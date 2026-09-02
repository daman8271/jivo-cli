# JIVO Utilities Chase Board — design

**Status:** approved 2026-08-22 · **Company:** JIVO Wellness (Oil) only · **Live:** `https://jivo-utilities.vercel.app`

## The gap this closes

Accounts keeps a master sheet of ~47 recurring monthly obligations — electricity
connections, mobile and landline numbers, broadband links, rents. SAP holds the
*money*. The sheet holds the *calendar*. Neither alone answers the only question
that matters day to day: **what is due right now, and has it been dealt with?**

Three things SAP genuinely cannot tell you, verified live on 2026-08-22:

1. **It does not know the connection.** A BSES A/P invoice's `NumAtCard` is the
   bill number (`102227705760`), not the CA number on the sheet (`100165409`).
2. **It does not know the budget.** Every utility JE line since 2026-04 carries
   profit centre `CANOLA` — 162 of 162. Backoffice / Factory / Factory Common /
   ECOM exists only on the sheet.
3. **It lags.** As of 2026-08-22 the August book held 1 electricity line
   (Rs 1,410 against a Rs 5-7 L monthly norm) and 1 telephone line (Rs 5,385
   against Rs 20-40k). Un-booked and not-yet-due are indistinguishable in SAP.

## Architecture

```
register.yaml            the 47-row calendar. Human-owned, git-tracked.
      |                  Never derived, never overwritten by the pipeline.
      v
pipeline/build_data.py   reads SAP live (hana-sql, read-only) + register
      |                  -> matches postings to connections
      |                  -> derives expected amount per connection
      v
site/data.json           static, rebuilt daily, deployed to Vercel
      +
api/state, api/confirm   Upstash Redis. Operator ticks, read live in the browser.
```

Two truths, never conflated on screen: **what SAP says** and **what an operator
said**. Every row is badged with which one it came from.

## The matching engine

For the current month, for each register row, find the SAP postings that could be
its bill. Confidence is a first-class output, not an internal detail.

| `match` | Rows | Rule | Confidence |
|---|---|---|---|
| `sole` | 6 | The vendor card serves only this row. Any posting on it in the window is this bill. | **certain** |
| `reimbursed` | 8 | Booked to a person's imprest card (`ORGV*`), which also carries unrelated reimbursements. Filter to the utility ledgers, then amount-match. | **likely** |
| `shared` | 12 | One card, many connections — BSES serves 5 rows, Airtel 4, UHBVN 2. Disambiguate by the connection's own trailing-6-month amount band plus a date window around `bill_day`. | **guess — operator confirms** |
| `unmapped` | 1 | No vendor card identified. | **unknown** |

**A guess is never shown as a fact.** A `shared` match renders as
*"probably J-3/190 2nd Floor — Rs 24,310 booked 4 Aug, confirm?"* with a one-click
confirm or reassign. A confirmation is durable: it pins that invoice to that
connection permanently, and next month's matcher uses the accumulated pins as
training data. The map gets sharper with use rather than staying a guess forever.

Ledgers in scope: `5680011` ELECTRICITY, `5100020` ELECTRICITY DIRECT EXPENSE,
`5660002` RENT, `5660004` SPACE ON RENT, `5680003` TELEPHONE MOBILE AND INTERNET.
Provision and reversal lines (`TransType = 30`) are **excluded** from bill
matching — they are accruals, not bills — but surfaced separately so a month that
was provisioned rather than billed is visible instead of looking unpaid.

## Status model

Evaluated per row, per month, against today.

| Status | Condition |
|---|---|
| `done_booked` | A SAP posting matched, confidence certain or confirmed |
| `done_confirmed` | An operator ticked it, no SAP posting yet |
| `overdue` | `due_day` passed, nothing booked, nothing ticked |
| `due_soon` | `due_day` within 7 days |
| `awaiting_bill` | `bill_day` passed, nothing booked, nothing ticked, due day not yet reached |
| `not_yet_due` | `bill_day` not yet reached |
| `needs_confirm` | A posting matched at `guess` confidence and nobody has ruled on it |
| `no_due_date` | 6 rows carry no due day on the sheet. Never rendered as overdue — rendered as *"no due date on the register"*, which is a data gap to fix, not a payment failure. |

Month rollover uses the **due day**, not the calendar month: a bill with
`bill_day: 27, due_day: 6` is due in the *following* month, and the board must
not report it overdue on the 7th of the month it was raised.

## Expected amount

Each connection's own trailing 6-month median from SAP, shown for bills that have
not arrived yet, so the board doubles as a short-horizon cash view. Rows with
fewer than 3 months of history show no expectation rather than a thin average.
Labelled *expected*, never mixed with actuals in the same column.

## The board

Single page, today-first, grouped by **Budget**.

- **Header:** total due in the next 7 days, count overdue, count awaiting bill.
- **Bands** in order: Overdue → Needs confirming → Due this week → Awaiting bill →
  Not yet due → Done.
- **Row:** premises · category · connection · budget · expected or actual amount ·
  due date · who chases it (`source`) · status badge · confirm control.
- **Filters:** budget, category, status. **Month selector** for looking back.
- Read fine on a phone — this gets checked standing in a corridor.

## Storage and security

The page is public by standing rule, so the write path is guarded:

- `POST /api/confirm` requires a shared operator key (Vercel env var, entered once
  in the browser and held in `localStorage`). Without it the board is read-only.
- The route accepts **only** a known register `id`, a `YYYY-MM` month, one of a
  fixed status enum, an optional note, and an operator name. Anything else is
  rejected. There is no free-form write and no way to reach SAP through it.
- Every confirmation is stored with who and when, and is append-only — a
  correction writes a new record rather than erasing the old one.
- Rate-limited per key.

## Read-only against SAP, by construction

Honours **RULE 0**. The pipeline reaches SAP solely through `hana-sql`, which
permits only `SELECT`/`WITH`, refuses 33 mutating keywords, runs inside a HANA
read-only transaction and never commits. Nothing in this project can create,
change or delete an SAP document, master record or journal entry. The Vercel
functions never touch SAP at all — they only read and write Upstash.

## Non-goals

- Not a payments tool. It never pays a bill or drafts an A/P invoice.
- Not multi-company. Oil only; the pipeline is written company-agnostic so Mart
  and Beverages are a config change, but they are unverified and out of scope.
- Not a spend-analysis dashboard. Budget totals appear as context on the chase
  board; trend analysis is a later phase if asked for.

## Known data gaps

- **20 of 47 rows are missing** (sheet numbers 1-14 and 24-29) — not in the scan.
  The board renders `rows_captured` vs `rows_on_sheet` in its header so nobody
  mistakes a partial register for the whole picture.
- Row 37's connection number is partly obscured by a pen mark; recorded as
  `01112525849` and flagged for verification.
- 6 rows carry no due day on the sheet.
