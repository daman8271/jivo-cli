# hana-sql — direct read-only SQL into the SAP HANA core database

`hana-sql` connects **straight to the SAP Business One HANA database** and runs
read queries. This is the fast path for Accounts questions: real SQL with `SUM`,
`GROUP BY`, `JOIN` — a turnover that used to mean downloading hundreds of rows
through the Service Layer is now **one query returning one number**.

It is the HANA sibling of `postsql` (which does the same for the Postgres apps).

Two front ends, one engine:

- **`hana-sql "<sql>"`** — the human CLI (TSV/CSV to stdout).
- **`hana-sql mcp`** — a read-only MCP server for AI clients, over stdio or
  streamable HTTP. See [MCP.md](MCP.md).

Both go through the same guard, the same read-only transaction and the same
value normalisation. There is exactly one read-only implementation in this repo.

---

## Read-only: the five layers

This honours **CLAUDE.md Rule 0** (never mutate SAP). A single first-token
check is not enough, so read-only is layered — each layer assumes the one above
it may have a bug.

### Layer 0 — a real lexer, not a regex (`internal/guard/lex.go`)

One pass over the statement produces a *masked* form:

| input | becomes |
|---|---|
| `'any string'` (with `''` escapes) | `'?'` |
| `"QuotedIdent"` (with `""` escapes) | `"I"` |
| `-- to end of line` | one space |
| `/* block */` | one space |

Every later layer reads **only** the masked form, so a keyword inside a string
literal or a quoted identifier is data, not a verb.

It **fails closed**. An unterminated string, quoted identifier or block comment
is a refusal, never a best-effort guess — an unclosed quote is precisely how you
would hide the tail of a statement from a scanner. So is any non-ASCII or
control character outside a literal, because zero-width and homoglyph characters
are how you disguise a verb.

This also fixes a real false positive in the old guard: `SELECT 'a;b' FROM DUMMY`
used to be refused for "containing a semicolon". It is now correctly allowed.

### Layer 1 — first-token allowlist

- **MCP: `SELECT`, `WITH`.**
- **CLI: `SELECT`, `WITH`, `EXPLAIN`.**

The split is deliberate. HANA's `EXPLAIN PLAN FOR …` persists rows into
`SYS.EXPLAIN_PLAN_TABLE` — that is a write — so an AI client may not run it,
while a human operator at a terminal may. `TestExplainPolicySplit` exists so
nobody "normalises" this away later.

### Layer 2 — exactly one statement

A `;` anywhere but as the final non-space character is refused, so a read cannot
smuggle a second, writing statement after it.

### Layer 3 — banned keywords anywhere

33 keywords are refused anywhere in the masked token stream, not just in first
position: `INSERT UPDATE DELETE MERGE UPSERT TRUNCATE CREATE DROP ALTER RENAME
COMMENT TRIGGER PROCEDURE GRANT REVOKE LOCK CALL DO EXEC EXECUTE IMPORT EXPORT
LOAD UNLOAD SET UNSET COMMIT ROLLBACK SAVEPOINT CONNECT DISCONNECT INTO NEXTVAL`.

Curated, not "every keyword":

- `REPLACE` is a legitimate HANA string function, so it is blocked at layer 1
  only (as a statement starter).
- `BEGIN`/`END` are **not** banned, because `CASE … END` is ordinary read SQL.
- `UPDATE` anywhere also catches `SELECT … FOR UPDATE`, which takes real locks
  on production rows without changing data.
- `INTO` catches both `SELECT … INTO var` and `EXPORT … INTO '/path'`.
- `NEXTVAL` is **a write dressed as a SELECT**. `SELECT "SOMESEQ".NEXTVAL FROM
  DUMMY` passed layer 0 (clean ASCII), layer 1 (first token `SELECT`), layer 2
  (one statement) and every other layer-3 entry — yet advancing a sequence
  changes persistent state that no rollback undoes, and the JIVO schemas hold
  796 / 777 / 788 sequences (Oil / Mart / Beverages, counted live 2026-07-30 via
  `SYS.SEQUENCES`; 3158 in total). It was a live counterexample to "there is no
  argument that can make a tool write", and it is closed statically — the
  statement never had to be executed against production to be shut off, which is
  what Rule 0 requires. `CURRVAL` is deliberately **not** banned: it reads the
  value the session already holds and advances nothing.

### Layer 4 — HANA's own read-only transaction (`internal/hana/hana.go`)

Every statement runs inside `BeginTx(ctx, &sql.TxOptions{ReadOnly: true,
Isolation: sql.LevelReadCommitted})`, which go-hdb turns into HANA's literal
`set transaction read only` (`driver/conn.go:43,264`), and the transaction is
**always rolled back**. There is no `Commit` call anywhere in the package, and
`TestNoCommitInPackageSource` walks the AST to keep it that way.

**How well this is actually proven — read this before relying on it.** The
backstop was probed once, by hand, offline, against a table that does not exist
(so nothing could mutate in either branch), on 2026-07-30 against HANA
`2.00.059.13.1713941539`:

```
PRECHECK  probe table in catalog? rows=0 (0 = absent, as required)
SESSION   connection id 308431; BeginTx(ReadOnly:true, ReadCommitted) accepted
PROBE SQL  UPDATE "JIVO_OIL_HANADB"."ZZ_JIVO_MCP_PROBE_DOES_NOT_EXIST" SET "X" = 1 WHERE 1 = 0
PROBE RESULT  VERBATIM: SQL Error 259 - invalid table name:  Could not find table/view
              ZZ_JIVO_MCP_PROBE_DOES_NOT_EXIST in schema JIVO_OIL_HANADB: line 1 col 26
              (at pos 25) (statement no: 0)
CONTROL RESULT (no read-only tx)  VERBATIM: SQL Error 259 - invalid table name: … (identical)
```

**The probe is inconclusive.** HANA resolves object names before it applies the
transaction access mode, so the read-only transaction and a plain one produce
byte-identical errors. What *is* established: HANA accepted `set transaction
read only` without complaint (`BeginTx` succeeded and the session stayed
usable). What is **not** established: that the access mode would actually reject
a write to a table that exists. Proving that would require sending a real write
at a real table, which is precisely what Rule 0 forbids.

Consequence, stated plainly: **layers 0-3 are load-bearing on their own**, and
the dedicated read-only HANA user below moves from "should" to "must".

### Layer 5 — resource caps (MCP only; the CLI is a human at a terminal)

| Cap | Default | Purpose |
|---|---|---|
| row cap | 1000 | bounds context; a per-call `max_rows` may only *lower* it |
| byte cap | ~1 MiB | bounds a wide result |
| statement deadline | 60s | go-hdb turns `ctx.Done()` into a real **server-side cancel**, so this bounds HANA CPU |
| in-flight semaphore | 2 | a model cannot stampede the database the business is using |

Order matters, and is fixed: `guard.Check → deadline → semaphore → READ ONLY tx →
query → rollback`. **The deadline is applied before the semaphore.** It used to
be the other way round, so a caller asking for `timeout_ms:100` behind one
in-flight 1.5s query waited 1.501s — its own deadline bounded only the statement,
not the queue — and a client that had already gone away (HTTP disconnect, gateway
timeout) still eventually ran its query against production HANA. The transport
also hands its own request context down to the tool, so a disconnect really does
cancel.

When a cap trips, `truncated: true` and a `note` say so. `truncated` means
exactly one thing: **there was at least one more row and the caller is not seeing
it.** Both caps are therefore checked *before* a row is consumed; the byte cap
used to be checked after, so a result set that ended on the cap reported
`truncated: true` with nothing cut, and the two cap paths disagreed about what
truncation means. The advice in the note is chosen by the caller: "aggregate
server-side" for a business query, and for a catalog listing — where there is
nothing to aggregate — the page's real coverage plus the `offset` to pass next.

### What each bypass is stopped by

| Attempt | Stopped by |
|---|---|
| `UPDATE OCRD SET …` | L1 |
| `/*x*/ DELETE …`, `-- x⏎DROP …` | L0 then L1 |
| `SELECT 1 FROM DUMMY; DROP TABLE T` | L2 |
| `;` inside a string or comment | L0 masks it — no refusal *and* no smuggling |
| banned keyword inside a string literal / as a quoted identifier | L0 masks it — correctly **allowed** |
| `WITH x AS (DELETE …)` | L3 |
| `DO BEGIN UPDATE … END` | L1 + L3 |
| `CALL SCHEMA.PROC(…)` | L1 + L3 |
| `SELECT … FOR UPDATE` (locks, no data change) | L3 |
| `EXPORT … INTO '/path'` (server-side file write) | L1 + L3 |
| `SELECT … INTO var` | L3 |
| DDL of every shape | L1 + L3 |
| `EXPLAIN PLAN FOR …` writing `SYS.EXPLAIN_PLAN_TABLE` | L1 (MCP policy) |
| unterminated `'` or `/*` hiding the tail | L0, fail-closed |
| zero-width / homoglyph before the verb | L0, fail-closed |
| `COMMIT` / `ROLLBACK` escaping the read-only tx | L3 |
| SQL injection through tool arguments | structurally impossible — `hana_query` takes no parameters, and the catalog tools use `?` binds with fixed SQL text |
| result-set flooding | L5 row + byte caps, with an explicit `truncated` flag |
| runaway cross-join burning production CPU | L5 deadline + server-side cancel + semaphore |
| `SELECT "SEQ".NEXTVAL` — a write dressed as a read | L3 (`NEXTVAL` banned) |
| a visited web page driving `127.0.0.1:7706/mcp` | HTTP transport: `Origin`, `Host` and `Content-Type` validation (see [MCP.md](MCP.md#loopback-binding-is-not-the-mitigation--these-three-checks-are)) |
| a queued call that the client already abandoned | L5 deadline is applied *before* the semaphore, so it is never sent |

Residual risk: a heavy query can still consume up to `--timeout` seconds of
production HANA CPU.

---

## Residual risk and the one real fix

The credential is a **full SAP user (`ZIA`)**. So the guarantee here is
client-side discipline plus HANA's transaction access mode — *not* a grant. The
only true enforcement is a **dedicated read-only HANA user** with `SELECT`-only
grants on the three schemas. That was already a TODO; now that a remote model
can hold the pen through the MCP server, and now that the layer-4 probe has come
back inconclusive, it is the top hardening item.

---

## Credentials

Read from `../connections/hana.env` (gitignored — never committed). The tool
walks up from the working directory to find `connections/hana.env`; `-env <path>`
or `$HANA_ENV` override that, and `HANA_HOST` / `HANA_PORT` / `HANA_USER` /
`HANA_PASSWORD` in the process environment override the file (which is how a
container is configured). The port defaults to `30015`.

No credential value is ever printed: `hana_doctor` shows `"**** (set)"`, and
every error and audit line is scrubbed on the way out.

## Build

```bash
cd hana-sql
go build -o hana-sql .
go test ./...
```

## Use

```bash
# a query as an argument
./hana-sql "SELECT CURRENT_USER, CURRENT_SCHEMA FROM DUMMY"

# a query from a file
./hana-sql -f queries/turnover-oil-july.sql

# a query on stdin
echo 'SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OCRD"' | ./hana-sql

# RFC 4180 CSV instead of TSV
./hana-sql -csv "SELECT ... FROM ..."

# MCP server for AI clients (see MCP.md)
./hana-sql mcp
./hana-sql mcp --transport http --addr 127.0.0.1:7706
```

Exit codes: `0` ok, `1` refused/bad input, `2` could not connect, `3` query error.

### Output is escaped, because live SAP data contains the delimiter

The old output was `strings.Join(cells, sep)` with no quoting at all. On Oil
alone, 67 of 3391 `OCRD."Address"` values, 37 `OINV."Comments"`, 4
`OITM."ItemName"` and one `OCRD."CardName"` contain a comma — so
`SELECT "CardCode","CardName","Balance"` emitted
`VENDA001230,V TRANS, V XPRESS & V LOGIS,0.000000`: **four fields for three
columns**, putting the balance under the wrong header in Excel. An embedded
newline was worse — one database row became two output lines.

- `-csv` emits **RFC 4180**: a field containing `,` `"` CR or LF is double-quoted
  and its quotes are doubled. `encoding/csv` reads it back exactly.
- TSV (the default) uses the **PostgreSQL `COPY TEXT` escapes** — `\\` `\t` `\n`
  `\r` — rather than quoting, because TSV's readers are `cut -f` and
  `awk -F'\t'`, which do not understand quotes. One row is always one line, and a
  field never contains a tab. An ordinary value passes through byte for byte.

The CLI also has **no LOB cap** (the MCP server clips at 8 KiB): a human running
`hana-sql "SELECT DEFINITION FROM SYS.VIEWS …"` gets the whole definition.

## How values come back

The naive rendering is wrong in several separate ways, so:

- **DECIMAL → an exact decimal string.** The old CLI printed `OINV."DocTotal"`
  as `170/1` and a crore figure as `1517229522682600/1000`, because go-hdb
  returns `*big.Rat` and `%v` prints a fraction. It is now `170.000000`.
- **Business dates → `2026-07-30`.** SAP B1 does not use HANA's `DATE` type;
  every date column is `TIMESTAMP` with a zero clock. A midnight timestamp is
  rendered as a bare date instead of `2026-07-30T00:00:00Z`.
- **A timestamp WITH a clock → `2026-07-30T19:33:19.913`, with no zone suffix.**
  A HANA `TIMESTAMP` carries no time zone: it is a wall clock, and on this server
  that wall clock is IST. `RFC3339Nano` stamped a `Z` on it and published local
  time as a UTC claim 5h30m wrong — measured live:
  `SELECT CURRENT_TIMESTAMP, CURRENT_UTCTIMESTAMP FROM DUMMY` →
  `2026-07-30 19:33:19.913` and `2026-07-30 14:03:19.913`. The midnight rule
  above exists for the same honesty reason; the non-midnight branch had the same
  disease.
- **DOUBLE → fixed notation.** HANA returns `DOUBLE` for the standard money
  recipe, and `%v` renders that as `1.07431612455e+09` — not a receivables
  figure anyone can read. It is now `1074316124.55`.
- **`columns[].type` → the SQL type, not go-hdb's storage type.** The driver
  reports `LONGDATE` for a column declared `TIMESTAMP`, `DAYDATE` for
  `TO_DATE()`, and `FIXED8/12/16` for every `DECIMAL(p,s)` (verified live against
  `SYS.TABLE_COLUMNS`, which reports `TIMESTAMP` and `DECIMAL` for the same
  columns). Callers are told to use this field to tell an exact `DECIMAL` from a
  float `DOUBLE`, so `FIXED12` broke the one promise it exists to keep.
- **Duplicate column names** are disambiguated against every name already
  assigned *and* every name a real column claims, not a per-name counter:
  `SELECT 1 AS X, 2 AS X, 3 AS X_2` used to produce columns `[X, X_2, X_2]` and a
  row with only two keys, dropping the value `2`. It is now `[X, X_3, X_2]` — the
  column the caller really aliased `X_2` keeps that name.
- **CLOB/NCLOB/BLOB** are scanned through a LOB target; scanning one into a plain
  `any` yields the driver's locator object, not the text. The MCP server caps
  each cell at 8 KiB and marks it ` …[clipped]`; the human CLI has no cap.

## The three companies (HANA schemas)

One login sees all three. You reach a company purely by **qualifying the table
name** — there is no company parameter anywhere.

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
| `OITW` | Stock per item per warehouse |
| `ORDR` / `RDR1` | Sales orders |
| `OPOR` / `POR1` | Purchase orders |
| `OPCH` / `PCH1` | A/P invoices (purchases) |
| `OJDT` / `JDT1` | Journal entries — header / lines |
| `ORCT` / `OVPM` | Incoming / outgoing payments |

Turnover (net of GST) = `SUM("DocTotal" - "VatSum")` from `OINV` minus the same
from `ORIN`, filtered by `"DocDate"` and `"CANCELED" = 'N'`.

### Column-name traps (all verified live, 2026-07-30)

HANA is case-sensitive, so SAP B1's mixed-case names **must** be double-quoted.
These are the ones that cost a round trip:

| Trap | The truth |
|---|---|
| cancel flag | `OINV`/`ORIN`/`ORDR` use `"CANCELED"`; **`ORCT`/`OVPM` use `"Canceled"`** |
| `OJDT` posting date | `"RefDate"` — `OJDT` has no `"DocDate"` at all |
| payment amount | `ORCT`/`OVPM` **do** have `"DocTotal"` here — the opposite of the Service Layer, where you must add `CashSum + TransferSum + …` |
| credit limit | `OCRD."CreditLine"` (the Service Layer calls it `CreditLimit`) |
| stock | `OITW."OnHand"`, `OITW."MinStock"`; `OITM."InvntItem" = 'Y'` means stock-managed |
| ledger balance | `OCRD."Balance"`, **positive = DEBIT** (the party owes JIVO). Sum debits only for receivables; netting understates what is owed. |

The same list lives in `internal/mcpsrv/facts.go` as the tool descriptions, and
`TestLiveCribSheetColumnsExist` re-verifies every spelling against the database
so it cannot rot into confident nonsense.

## Tests

```bash
go test ./...            # no database required
go vet ./...
```

The suite runs with **no HANA in the process**: the guard is pure stdlib, the
query core is driven by an in-memory fake driver that counts transactions and
asserts `ReadOnly`/`Rollback`, and the MCP transport suite runs against
`httptest` with `DB == nil`.

The live suite is opt-in and read-only, and is run from the VPS where the tunnel
terminates:

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go test -c -o hana-live.test ./internal/hana
scp hana-live.test vps:/opt/jivo-truth/
ssh vps 'cd /opt/jivo-truth && HANA_TEST_LIVE=1 HANA_ENV=./hana.env ./hana-live.test -test.v'
```

Set `HANA_TEST_STRICT_TRUTH=1` to make drift from `mcp-benchmark/truth-key.json`
a hard failure. It is *not* strict by default on purpose: the books are open and
posting continues during the day, so a changed count is usually business, not a
bug. (Observed on 2026-07-30: open A/R invoices went 12861 → 12862 → 12863
across three runs minutes apart, matching the independent oracle binary each
time.)

## TODO / hardening

- **Dedicated read-only HANA user** (`SELECT`-only grants on the three schemas)
  to replace the personal `ZIA` login. This is the one change that converts
  layered client-side discipline into a database-enforced guarantee — see
  layer 4 above for why the current backstop is unproven. **Treat this as
  BLOCKING for a gateway rollout, not optional hardening**: on HANA
  2.00.059.13.1713941539 `SYS.M_TRANSACTIONS` exposes no `ACCESS_MODE` column and
  reports `TRANSACTION_TYPE = 'USER TRANSACTION'` for a read-only transaction, so
  there is no read-only way to verify that `set transaction read only` took
  effect at all. `hana_doctor` says so out loud in
  `read_only.transaction_proof`.
- Stage 2 (not done here): register the backend with the MCP gateway, add the
  compose service on `:7706`, and re-run `mcp-benchmark`. Note the deploy trap:
  a container reaches HANA at `172.16.1.1:30015`, **not** the host's
  `127.0.0.1:47301`.
- Optional: typed convenience commands (turnover, ledger, party statement).
