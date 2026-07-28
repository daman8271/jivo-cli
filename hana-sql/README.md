# hana-sql — direct read-only SQL into the SAP HANA core database

`hana-sql` connects **straight to the SAP Business One HANA database** and runs
`SELECT` queries. This is the fast path for Accounts questions: real SQL with
`SUM`, `GROUP BY`, `JOIN` — a turnover that used to mean downloading hundreds of
rows through the Service Layer is now **one query returning one number**.

It is the HANA sibling of `postsql` (which does the same for the Postgres apps).

## Read-only guarantee

Two layers, enforced before any statement reaches HANA:

1. **First-token allowlist** — only `SELECT` / `WITH` / `EXPLAIN` are accepted.
   `INSERT/UPDATE/DELETE/MERGE`, DDL, `CALL`, etc. are refused with an error.
2. **Single-statement guard** — a `;` in the middle of the text is rejected, so a
   query can't smuggle a second (writing) statement.

This honours **CLAUDE.md Rule 0** (never mutate SAP). Note: the guarantee is
*client-side discipline*, because the current login (`ZIA`) is a full SAP user.
The proper hardening is a dedicated **read-only HANA user** (see below).

## Credentials

Read from `../connections/hana.env` (gitignored — never committed). The tool
walks up from the working directory to find `connections/hana.env`, or you can
pass `-env <path>` or set `HANA_ENV`.

```
HANA_HOST=103.89.45.192
HANA_PORT=30015
HANA_USER=...
HANA_PASSWORD=...
```

## Build

```bash
cd hana-sql
go build -o hana-sql .
```

## Use

```bash
# a query as an argument
./hana-sql "SELECT CURRENT_USER, CURRENT_SCHEMA FROM DUMMY"

# a query from a file
./hana-sql -f queries/turnover-oil-july.sql

# a query on stdin
echo 'SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OCRD"' | ./hana-sql

# CSV instead of TSV
./hana-sql -csv "SELECT ... FROM ..."
```

## The three companies (HANA schemas)

- `JIVO_OIL_HANADB` (Oil)
- `JIVO_MART_HANADB` (Mart)
- `JIVO_BEVERAGES_HANADB` (Beverages)

## Handy SAP B1 tables

| Table | What |
|---|---|
| `OINV` / `INV1` | A/R invoices — header / lines (sales) |
| `ORIN` / `RIN1` | A/R credit notes — returns |
| `OCRD` | Business partners (customers & vendors) + `Balance` |
| `OITM` | Items (stock) |
| `ORDR` / `RDR1` | Sales orders |
| `OPCH` / `PCH1` | A/P invoices (purchases) |
| `OJDT` / `JDT1` | Journal entries — header / lines |

Turnover (net of GST) = `SUM("DocTotal" - "VatSum")` from `OINV` minus the same
from `ORIN`, filtered by `"DocDate"` and `"CANCELED" = 'N'`.

## TODO / hardening

- Ask IT / SAP partner for a **dedicated read-only HANA user** (only `SELECT`
  grants on the three schemas) to replace the personal `ZIA` login — then
  read-only is enforced by the database, not just the client, and the audit log
  attributes queries to a service account.
- Optional: an MCP server wrapper (like `postsql mcp`) so Claude Desktop on the
  Accounts team's laptops can ask HANA in plain English.
- Optional: typed convenience commands (turnover, ledger, party statement).
