# AWL party board — one vendor, every day

A single page that answers what Accounts asks about **AWL Agri Business Limited**
(`VENDA000224`, JIVO Oil) every morning:

- what money went out to AWL, and whether it was an **advance** or **against a bill**
- what **bills** came in, and what **shortage credit notes** followed
- what is still hanging: **bills not paid**, and **payments with no bill against them**
- which of those two lists are the *same lorry* and only need reconciling in SAP

Built **2026-08-22** for Lovepreet, out of the AWL ledger reco.

## Run it

```bash
./refresh.sh
```

Or straight to the builder:

```bash
python3 build.py                        # today, JIVO Oil, AWL
python3 build.py --as-of 2026-08-20     # position on a past date
python3 build.py --card VENDA000123 --company mart
python3 build.py --days 90              # more daily history on the strip
```

Output is `site/index.html` — self-contained, no server, no network. Open it
from the file system or put it on a share.

## Read-only

Everything goes through `hana-sql`, which refuses anything but `SELECT`/`WITH`
and runs inside a HANA read-only transaction. This board **writes nothing** to
SAP, in line with CLAUDE.md RULE 0.

## Where the numbers come from

| On the page | Source |
|---|---|
| Balance | `JDT1` summed over `ShortName = <card>`; ties to `OCRD.Balance` |
| Advance on account | `JDT1.BalDueDeb` on outgoing payments — the unapplied part |
| Bills not paid | `JDT1.BalDueCred` on A/P invoices |
| "Set against" on a payment | `OITR`/`ITR1` — SAP's own internal reconciliation |
| Narration | `OPCH`/`ORPC`/`OVPM`/`ORCT` `.Comments`, falling back to `OJDT.Memo` |

Per **C-0023**, the ledger is built from `JDT1`, never from document extracts —
document tables miss journal entries, cancellations and pre-cutover postings.

Per **C-0019**, "still open" is read from the line's own `BalDue*`, which is what
SAP actually reconciled, not from `DocStatus` — at JIVO `DocStatus` stays `'O'`
long after the money has gone.

## The one judgement call on the page

**Reconcile these in SAP** is the only list the board infers rather than reads.
An open bill is paired with a payment on account when the two are within **30
days** and within **1%** (or ₹100) of each other. Anything under ₹100 apart is
flagged *just needs reconciling*; a wider gap is flagged *shortage credit note
not booked yet*. Everything else on the page is straight out of SAP.

## What gets kept, and why

Every run archives the day into `history/<card>/`:

- `<date>.json` — that day in full: the position, the day's payments/bills/credit
  notes, and both open registers
- `positions.csv` — one row per day, so the trend is a spreadsheet away

**This is kept because it cannot be rebuilt later.** A past *balance* can:
re-run with `--as-of` and `JDT1` gives it back exactly. A past *open position*
cannot — `BalDueDeb` / `BalDueCred` are current-state fields, so the moment
Accounts reconciles a bill, the fact that it stood open on a given morning is
gone from SAP. Same for which payments were still sitting on account.

For that reason `build.py` **refuses to archive a back-dated run**. `--as-of`
rebuilds the balance correctly but carries today's open flags, so archiving it
would record an open position that never existed. It says so and skips.

History starts **2026-08-22**. Earlier days are not backfilled — the daily
*movement* for them is still exact on the board's 45-day strip (that comes from
`JDT1`), but the open position for those mornings is not recoverable.

## Files

| Path | What |
|---|---|
| `build.py` | pulls the ledger + reconciliations, shapes the JSON, writes the page |
| `template.html` | the board itself; `/*__DATA__*/null` is where the data lands |
| `site/index.html` | the built page — this is the thing you open |
| `site/data.json` | the same data, if you want it in Excel or another tool |
| `history/<card>/` | the kept daily positions — see above |
| `refresh.sh` | build + open, with a log |
| `refresh.cmd` | what Windows Task Scheduler runs |

## The daily run

Windows scheduled task **`JIVO AWL board`**, 11:30 every day, pointing at
`refresh.cmd`. Log: `refresh.log`.

```cmd
schtasks /Query /TN "JIVO AWL board" /FO LIST
schtasks /Create /TN "JIVO AWL board" /SC DAILY /ST 11:30 /F /TR "\"<repo>\acc\awl-board\refresh.cmd\""
```

The task lives in Windows, not in the repo, so a fresh checkout has the folder
but no schedule — recreate it with the line above.

Anything driven by Task Scheduler starts in `C:\Windows\System32`, where
`hana-sql`'s upward search for `connections/hana.env` finds nothing. `build.py`
therefore passes `-env` explicitly and pins `cwd` to the repo. Keep that.
