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

## Domain commands

High-level, read-only commands over each subsystem (71 sub-commands across 18
groups). Common flags where they apply: `--from`/`--to` (date window),
`--salesperson`, `--retailer`, `--beat`, `--state`, `--zone`, `--include-deleted`,
plus the global `-n/--limit`, `--json`, `--csv`.

| Group | Sub-commands |
|---|---|
| `retailers` | list · get · count |
| `salespersons` | list · get · count · subordinates |
| `beats` | list · shops · assignments · count |
| `attendance` | list · summary · register · count |
| `geo` | track · last · count *(date window required — 27M rows)* |
| `sales` | visits · lines · summary · count |
| `promoters` | visits · lines · count |
| `schemes` | list-sold · issued · gifts · get · count |
| `targets` | person · retailer · category · count |
| `stock` | retailer · distributor · lines · monthly · count |
| `distributors` | list · shops · mappings · count |
| `products` | list · get · count |
| `geography` | states · zones · areas · subareas |
| `primary` | list · orders · stock · count |
| `ecom` | sales · returns · settlements · count |
| `travel` | rates · km · place · reports · count |
| `users` | list · roles · permissions · count *(never exposes passwords)* |
| `logs` | recent · errors · reports · count *(date bound required — 8.5M rows)* |

```bash
./dsr retailers count --type Distributor          # 893
./dsr sales visits --salesperson 4927 --from 2026-07-01 --to 2026-08-01
./dsr beats shops 41761                            # retailers on a beat
./dsr geo track 4926 --from 2026-07-01 --to 2026-07-31 -n 100
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

Working today: `doctor`, `query`, `count`, `peek`, `schema`, the study vault, and
all 18 domain command groups above (71 sub-commands) — every command has been
compiled and smoke-tested against the live database.

Still to come: a **live authenticated portal crawl** (pending real DSR app
credentials — the `Admin/English@jivo` pair is the *server* login, not the app
login), and a full **reconciliation** of command outputs against the portal's own
reports. Command outputs are currently validated to run correctly and return
plausible live data, not yet cross-checked number-for-number against the portal.
