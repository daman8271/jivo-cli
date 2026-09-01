# saphist — JIVO's OLD SAP B1 books, 2014 → 2024

`saphist` is a read-only CLI over the **closed SAP Business One company
databases** that live on the Microsoft SQL Server at **`138.252.101.118:1433`**
(JOY SERVICES). These are JIVO's books from **2014-11-01 up to the October-2024
move to HANA** — ten years of invoices, bills, payments, stock and journals that
the live `sapb1` CLI cannot see.

| `--book` | Database | Company | Documents | Journals to |
|---|---|---|---|---|
| `old` | `Live_Jivo_WellnessN_Aug_2019` | Jivo Wellness Pvt. Ltd. **(Old)** | 2014-11-01 → 2019-08-31 | 2019-10-29 |
| `new` | `Jivo_All_Branches_Live` | Jivo Wellness Pvt. Ltd. | 2019-08-31 → 2024-10-01 | 2025-03-31 |
| `bsu` | `ARY_BSU` | Akal Rozgar Yojana (BSU) | 2019-04-01 → 2023-03-14 | 2025-03-31 |

**Anything after October 2024 is NOT here.** That is the live SAP HANA system —
use the `sapb1` CLI in `sap-b1/`.

## The one thing that makes this tool worth having

You do not have to know which book a date lives in. Give it a date range and it
routes itself; a range that crosses the August-2019 cut-over reads **both** books
and labels every row with the one it came from:

```
$ saphist sales summary --from 2019-04-01 --to 2020-04-01
book  invoices  gross_incl_gst  gst          net_sales     credit_notes  net_returns  turnover
old   1829      377104076.99    19877510.77  357226566.22  473           20003133.40  337223432.82
new   8010      700220428.97    30662060.63  669558368.34  1269          53668985.03  615889383.31
```

`--fy 2019` (Indian financial year, Apr–Mar), `--year 2019` (Jan–Dec) and
`--from/--to` all work. `--book old|new|bsu|jivo|all` pins it manually.

## It cannot write

Every statement passes a **SELECT-only guard** (one leading `SELECT` or `WITH`;
comment-prefixing and batched second statements are both rejected) and then runs
inside a transaction that is **always rolled back**. There is no write command in
this CLI and no code path that calls `Exec`. The books are closed and stay closed.

The connecting login is `sa`, which *is* a sysadmin on that instance — the guard
is what protects the books, not the login's privileges. Treat the `.env` as a
credential worth guarding.

## Install

```bash
# macOS / Linux
go build -o saphist .            # or use the committed binary
export SAPHIST_USER=… SAPHIST_PASSWORD=…
./saphist doctor
```

On Windows use `saphist.exe` with a `.env` file next to it. Full instructions,
including where the credentials come from: **[SETUP.md](SETUP.md)**.

Credentials are read from the first `.env` found, and the existing
`connections/ary.env` (same server, same login) works unchanged — `SAPHIST_*`
wins, then `ARY_*`, then `DSR_*`.

## What you can ask

Real questions with the exact command: **[ASK-EXAMPLES.md](ASK-EXAMPLES.md)**.

```
saphist doctor                     is it reachable, and what period does each book cover
saphist books                      the three books; `books which --year 2016` routes a date
saphist sales                      summary / monthly / yearly / invoices / invoice / by-party / by-item / by-branch / returns
saphist purchases                  summary / monthly / bills / bill / by-vendor / by-item / returns
saphist party                      search / show / statement / balances / open
saphist ledger                     chart / account / trial-balance / journal / entries
saphist items                      search / show / stock / movement
saphist payments                   in / out / summary / show
saphist orders                     sales / purchase / deliveries / receipts / show
saphist branches | warehouses | salespeople | item-groups
saphist query "SELECT …"           one SELECT, one book
saphist tables --search inv        find a table;  saphist columns OINV
```

Global flags: `--book`, `--from/--to/--year/--fy`, `--json`, `--csv`,
`--select col,col`, `-n` (rows per book), `--quiet`, `--timeout`, `--db` (raw
database escape hatch).

## Traps — read these before you quote a number

1. **A CardCode is NOT the same party in both books.** `CUSTA000694` is
   *Bala Ji Store (Janak Puri)* in `old` and *JIVO MART PVT. LTD.* in `new`. The
   two databases were numbered independently. Always read the `book` column, and
   never carry a code from one book to the other.
2. **`old` has no branches.** `OBPL` is empty there, so `--branch` and
   `sales by-branch` only mean anything in `new` (6 branches) and `bsu` (2).
3. **`items stock` is a frozen snapshot, not an as-at-date figure.** `OITW.OnHand`
   is the balance at the moment the book stopped being posted to — Aug-2019 for
   `old`, Oct-2024 for `new`. For movement between two dates use
   `saphist items movement`.
4. **Journals run past the last document.** `new` has journal entries to
   2025-03-31 (the FY24-25 close) even though its last invoice is 2024-10-01. A
   trial balance for FY2024 is meaningful; a sales figure for 2025 is not.
5. **BSU is a different company.** It is excluded from date-routing on purpose —
   `--book bsu` or `--book all` to reach it. Do not add its figures to Jivo
   Wellness's.
6. **`zTest_Jivo` is a test copy** of `Jivo_All_Branches_Live` with near-identical
   counts. It is listed in `saphist books` so nobody quotes from it by accident.

## Definitions (the same ones the live system uses)

- **Turnover** = `OINV(DocTotal − VatSum)` − `ORIN(DocTotal − VatSum)`, by
  `DocDate`, excluding cancelled. GST-inclusive figure = `DocTotal`.
- **Ledger balance** = `OCRD.Balance`. **Positive = DEBIT** (they owe JIVO);
  **negative = CREDIT** (JIVO owes them).
- The cancel flag is `CANCELED` on documents, `Canceled` on payments; SQL
  Server's collation is case-insensitive so either spelling resolves.
- Money is INR.

## Layout

```
main.go                     entry point
internal/config/            connection profile + .env loader (no baked-in creds)
internal/db/                SELECT-only guard, rolled-back transaction, generic scan
internal/render/            table / JSON / CSV output
internal/cli/
  root.go                   command tree, global flags
  books.go                  the book registry and the date routing
  domain.go                 shared filters, runBooks, findInBooks
  doctor.go query.go sales.go purchases.go party.go ledger.go
  items.go payments.go orders.go masters.go
```

Adding a command: write `internal/cli/<subsystem>.go`, self-register in `init()`,
build the SQL with the `fXxx`/`fWhere` helpers, and run it through `runBooks` if
it takes a date range. No shared file needs editing.
