# dsr — read-only CLI for the JIVO DSR portal

`dsr` is a fast, **read-only** command-line window into the **JIVO DSR** field-sales
system (Daily Sales Report / Sales Force Automation — retailers, beats, SO &
promoter attendance, secondary sales, schemes, targets, stock). It reads the
portal's live SQL Server database (`DSR_V6`) directly — the same pattern as
`postsql` / `hana-sql` — and can reach the web portal for reachability checks.

## ⛔ Read-only, always (RULE 0)

Every database statement passes three independent guards, because the shared
`ab` login is a SQL Server **sysadmin** and we cannot revoke its rights:

1. a **SELECT/WITH-only** first-token allowlist (writes are rejected with exit 5);
2. every query runs inside an **always-rolled-back** transaction (never committed);
3. the code only ever calls `Query` (never `Exec`) for your SQL.

Reads use **READ UNCOMMITTED** isolation, so they take no locks and never block —
or get blocked by — the live portal. `dsr doctor` loudly warns that the login is
over-privileged; prefer a dedicated read-only login when one is available.

## Setup

Creds come from a gitignored `.env` next to the binary (or `DSR_*` env vars):

```bash
cp .env.example .env      # then fill in DSR_USER / DSR_PASSWORD
go build -o dsr .
./dsr doctor              # verifies SQL Server + portal reachability
```

Defaults target `103.89.45.75:1433`, database `DSR_V6`. Override any of
`DSR_HOST DSR_PORT DSR_DATABASE DSR_ENCRYPT DSR_USER DSR_PASSWORD DSR_PORTAL_URL`.
The instance hosts 72 databases — point at another with `--db <name>`.

## Commands

| Command | What it does |
|---|---|
| `dsr doctor` | Health check: DB reachability, version, privileges, table count, portal status |
| `dsr query "<SELECT…>"` | Run a read-only query (also reads stdin); `--limit N` wraps in `SELECT TOP N` |
| `dsr count <table> [--where …]` | Count rows in a table |
| `dsr peek <table> [-N n]` | First N rows (`SELECT TOP N *`) |
| `dsr schema tables [--min-rows N]` | List tables with row & column counts |
| `dsr schema columns [table]` | List columns |
| `dsr schema keys` | Declared foreign keys |
| `dsr schema views` | Views with definition size |
| `dsr schema dump [--out DIR] [--samples N] [--views-only]` | Extract the full catalog + sample rows to files |

Global flags: `--db`, `--json`, `--csv`, `--compact`, `-q/--quiet`, `-n/--limit`,
`--timeout`, `--select`.

```bash
./dsr query "SELECT COUNT(*) AS retailers FROM tbl_retailers"
./dsr count tbl_salesPersonAttendance --where "attDate >= '2026-07-01'"
./dsr peek tbl_SalesReport -N 5 --json
```

## The study vault

`study/schema/` is a full extract of `DSR_V6` (208 tables, 2,929 columns, 47.5M
rows, 12 view definitions, 131 sample-row files). `study/vault/` documents the
data model — start at **`study/vault/00-INDEX.md`** for the master linkage map and
the portal-menu → tables → commands coverage checklist. Per-subsystem deep dives
(retailers, sales entry, beats, attendance/geo, distributors, schemes, targets…)
sit alongside it; proposed command specs are under `study/specs/`.

**Key modelling facts** (all convention — the DB has only 1 declared FK):
`tbl_salesperson.ID`, `tbl_retailers.Id`, `tbl_item.Id`, `tbl_beats.beatId`, and
the visit header `tbl_SalesReport.salesId` are the five identity hubs. Distributors
are `tbl_retailers` rows with `type='Distributor'`. Filters that matter:
`ISNULL(deleted,0)=0` (soft delete), `productId>0` and other `-1` "all/unset"
sentinels, and `1899-12-30` empty-date sentinels — always bound date ranges.

## Status

Working today: `doctor`, `query`, `count`, `peek`, `schema`, and the study vault.
Still to come: the high-level named domain commands (`dsr retailers`, `dsr sales`,
`dsr attendance`, …) specced in `study/specs/`, and a live authenticated portal
crawl (pending real DSR app credentials — the server login is not the app login).
