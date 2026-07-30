# sapb1

A command-line client for the SAP Business One Service Layer (`b1s/v1`), built
for SAP B1 for HANA. **Read-only by default**, with three explicit write
commands you have to type on purpose.

Every business-data read (`orders`, `invoices`, `items`, `partners`, `query`,
`fields`, `doctor`) is a plain OData `GET`. Writes live in exactly three
commands — `draft`, `post`, `patch` — each of which previews the request, asks
you to confirm, and records the attempt in a local log. There is no `delete`.

It also ships with the **entire Service Layer schema embedded offline** — 498
services / 1950 operations — so you can explore what's available (`entities`,
`ops`, `catalog stats`, `fields`) with **zero network access**, before you're
even on the VPN.

## Before you do anything: get on the VPN

The Service Layer host is typically firewalled to the company network. **Get
on the company VPN, or get your IP whitelisted, before running anything
beyond `--help`.** If you're not connected, every network command will fail
with a clear "cannot reach ... are you on the VPN?" message instead of
hanging or crashing — but it still won't work until you're actually
connected.

## Setup

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Key                | Meaning                                              |
|--------------------|-------------------------------------------------------|
| `SAPB1_HOST`       | SAP Service Layer host/IP                              |
| `SAPB1_PORT`       | Service Layer port (default `50000`)                   |
| `SAPB1_COMPANYDB`  | The CompanyDB name — ask your SAP admin for this       |
| `SAPB1_USER`       | SAP username                                           |
| `SAPB1_PASSWORD`   | SAP password                                            |
| `SAPB1_INSECURE`   | `true` to skip TLS verification (self-signed certs)     |
| `SAPB1_TIMEOUT`    | Request timeout in seconds (default `30`)               |

`.env` is already git-ignored — **never commit it**. `.env.example` is the
template that *is* committed and contains no real credentials.

Build the binary:

```bash
go build -o sapb1 ./cmd/sapb1          # macOS / Linux
go build -o sapb1.exe ./cmd/sapb1      # Windows
```

Run it:

```bash
./sapb1 doctor                         # macOS / Linux
sapb1.exe doctor                       # Windows
```

## Configuration precedence

For every setting, highest wins:

```
CLI flag  >  environment variable  >  .env file  >  built-in default
```

Global flags (available on every command): `--host --port --company --user
--insecure --timeout --json --csv`. There is intentionally **no `--password`
flag** — the password only ever comes from `SAPB1_PASSWORD` in the real
environment or `.env`, so it never ends up in your shell history or process
list.

If `SAPB1_COMPANYDB` isn't set, any command that needs it fails with:

> Company database not set — set SAPB1_COMPANYDB in .env or pass --company.
> Ask your SAP admin for the CompanyDB name.

## Read-only by default; explicit writes

- Every read command is a `GET`. Nothing about running a read can change data.
- `internal/client` exposes exactly two write operations — `Create` (POST) and
  `Update` (PATCH). There is **no `DELETE` and no `PUT`** anywhere in the
  codebase.
- `post` accepts only a **bare entity-set name that the embedded catalog knows
  and that supports a plain POST**. That is what keeps it from being a generic
  "POST anything" tool: SAP's OData **actions** — `Invoices(9)/Cancel`,
  `Orders(1)/Close`, `Drafts(4321)/SaveDraftToDocument`, `$batch`, anything with
  `(`, `)`, `/`, `?`, `$` or `.` in it — are refused before a session is even
  opened, with no flag to override. Cancelling, closing and posting a draft stay
  with a human in the SAP B1 client. (What the CLI *can't* do is not the same as
  "nothing can be changed": a `post`/`patch` it does perform is live and only SAP
  can reverse it.)
- Those two operations are reachable only from `sapb1 draft`, `sapb1 post` and
  `sapb1 patch`. Each one:
  1. prints the exact company, request and payload it is about to send (to
     **stderr**, so `--json` output on stdout stays parseable),
  2. requires a typed `yes` at the prompt — exactly `yes`, since one stray
     keystroke shouldn't commit a production write — or `--yes`, which is
     mandatory when stdin isn't a terminal (cron, pipes, agents), and
  3. appends an intent line before the request and an outcome line after it to
     the write log, successes and failures alike.
- `--dry-run` prints the exact request and sends **nothing** (not even a Login),
  exit 0. That is the sanctioned way for an agent to propose a write: dry-run it,
  show the operator, and only re-run with `--yes` if they say go.
- Your payload goes on the wire **byte for byte** as you wrote it (compacted; and
  for `draft`, with `DocObjectCode` spliced in front if you left it out). Nothing
  is re-encoded, so key order survives and a long `DocNum` or a high-precision
  total can't be reshaped by a float round-trip.
- A write is retried **only** on a `401` (expired session), exactly once. A
  timeout or a gateway failure is never replayed — a POST that timed out may
  already have committed in SAP, and a silent double-post is worse than an error.
  That case gets its own error and its own exit code (**7**), see below.
- The MCP server (`sapb1 mcp`) exposes **no write tools at all**. That's
  enforced by a test, not just documentation.
- The password is never printed, logged, or written to the session cache or the
  write log. `sapb1 auth status` and `sapb1 doctor` mask it as `****`.
- The session cache (`~/.sapb1-session.json`) stores only the session cookie
  values (`B1SESSION`/`ROUTEID`) and connection metadata — never the
  password — and is written with `0600` permissions.

## Commands

### Offline discovery (no network needed)

These read only the catalog embedded in the binary. They work with **zero
network access** — no VPN, no login, no server — and always exit `0` on
success. Use them to figure out what you can query before you connect.

The catalog lists every operation the Service Layer documents, including
`PUT`/`DELETE`. sapb1 implements none of those — the only writes it can perform
are the `POST`/`PATCH` behind [`draft`, `post` and `patch`](#writing-to-sap).

#### `sapb1 entities`

List every service/entity: name, number of operations, HTTP methods present,
and whether it's readable (has a `GET`).

```bash
sapb1 entities                       # all 498
sapb1 entities --search invoice      # case-insensitive name filter
sapb1 entities --read-only           # only services that expose a GET
sapb1 entities --search order --json # machine-readable
```

#### `sapb1 ops <ServiceOrEntity>`

Show every operation (method + name) the catalog records for one service or
entity. Case-insensitive; on a miss it suggests the closest names.

```bash
sapb1 ops Orders                     # the readable Orders entity (GET/POST/PATCH...)
sapb1 ops OrdersService              # the OrdersService actions (POST-only)
sapb1 ops BusinessPartners --json
```

#### `sapb1 catalog stats`

Totals across the catalog: services, operations, per-method breakdown, and how
many services are readable.

```bash
sapb1 catalog stats
sapb1 catalog stats --json
```

#### `sapb1 fields <Entity>`

Answers "what can I `--select`?". **Live**, it does `GET <Entity>?$top=1` and
lists the JSON keys of the first record (sorted). If SAP is unreachable or not
configured, it falls back to showing that entity's catalogued operations, so
it's still useful offline.

```bash
sapb1 fields Orders
sapb1 fields BusinessPartners --json
```

### `sapb1 doctor`

Run this first. End-to-end diagnostic: is config present, is the host
reachable over TCP, does Login succeed. Prints a ✓/✗ checklist with
actionable hints (VPN, whitelist, missing CompanyDB, bad credentials).

```bash
sapb1 doctor
```

### `sapb1 auth login` / `status` / `logout`

```bash
sapb1 auth login              # logs in, caches the session, prints "Connected to <company> as <user>"
sapb1 auth status             # shows resolved config (password masked) + cached-session state
sapb1 auth logout             # logs out and clears the cached session
```

### `sapb1 orders list`

Sales orders (`Orders`).

```bash
sapb1 orders list
sapb1 orders list --open --top 50
sapb1 orders list --filter "CardCode eq 'C0001'" --orderby "DocDate desc"
sapb1 orders list --all --json | jq '.[] | .DocTotal'
```

### `sapb1 invoices list`

A/R invoices (`Invoices`). Same flag shape as `orders list`.

```bash
sapb1 invoices list --open --top 50
sapb1 invoices list --filter "DocTotal gt 10000"
```

### `sapb1 items list`

Items/products (`Items`).

```bash
sapb1 items list
sapb1 items list --low-stock 10          # QuantityOnStock le 10
sapb1 items list --filter "ItemsGroupCode eq 100"
```

### `sapb1 partners list`

Business partners — customers & suppliers (`BusinessPartners`).

```bash
sapb1 partners list --customers --top 50
sapb1 partners list --suppliers --json
```

### `sapb1 query <EntitySet>`

The power tool: a generic read against **any** Service Layer entity set.
This is what lets you (or an AI agent) pull data with no new code —
`Quotations`, `PurchaseOrders`, `PurchaseInvoices`, `Warehouses`,
`ItemGroups`, `Users`, `JournalEntries`, `BusinessPartnerGroups`, or
anything else in your schema.

```bash
sapb1 query Quotations --top 10
sapb1 query Warehouses --select "WarehouseCode,WarehouseName"
sapb1 query JournalEntries --filter "ReferenceDate ge '2024-01-01'" --all
sapb1 query Items --filter "ItemCode eq 'A0001'" --json
```

### Shared list flags

`orders list`, `invoices list`, `items list`, `partners list`, and `query`
all share:

| Flag           | Meaning                                                          |
|----------------|-------------------------------------------------------------------|
| `--filter`     | raw OData `$filter` expression                                    |
| `--select`     | comma-separated fields (also sets the table's column order)       |
| `--top`        | max rows (default 20, ignored with `--all`)                       |
| `--skip`       | pagination offset                                                  |
| `--orderby`    | raw OData `$orderby` expression                                    |
| `--all`        | paginate through everything via `odata.nextLink` (capped at 200 pages) |
| `--page-size`  | rows per page while paginating (`Prefer: odata.maxpagesize`)       |
| `--count`      | print only the server-side total row count (`$inlinecount=allpages`) |

### `--count`

On any list command or `query`, `--count` asks the server how many rows match
and prints just that number. It is **one** GET carrying `$top=0` and
`$inlinecount=allpages` plus your `--filter`, so SAP answers with the total and
**no rows at all** — roughly 120 bytes on the wire instead of the twenty full
~200-field documents the old count used to drag back to print a single number.
That also makes the number atomic: a paged tally can straddle live postings and
land between two truths.

Because a count returns no rows, `--select`, `--orderby`, `--skip` and
`--top` have nothing to apply to and `--all` has nothing to paginate; the count
is a single request either way.

If the Service Layer withholds `odata.count`, `--count` **fails** (exit 6). It
will not print a row tally in its place — with `$top=0` that substitute is
always `0`, which would report every entity set as empty.

With `--json` you get `{"count": N, "serverSide": true}`.

```bash
sapb1 orders list --open --count
sapb1 query Invoices --filter "DocTotal gt 10000" --count --json
```

### Output format: `--json` / `--csv`

Every read command (`orders`, `invoices`, `items`, `partners`, `query`)
supports two global output formats, mutually exclusive with each other:

- `--json` — the raw OData `value` array as indented JSON, for piping into `jq`
  or feeding an AI agent.
- `--csv` — a header row plus one CSV row per record. Columns come from
  `--select` (in that order) if given, otherwise from the union of keys in the
  returned rows. Object/array cell values are JSON-encoded.

Without either flag, output is an aligned text table of the most useful
columns. The offline discovery commands support `--json` too.

```bash
sapb1 items list --select "ItemCode,ItemName,QuantityOnStock" --csv > stock.csv
sapb1 orders list --all --json | jq '.[] | .DocTotal'
```

## Writing to SAP

Three commands can change data. They only ever run because you typed them.

| Command | What it does | Reversible? |
|---|---|---|
| `sapb1 draft <doctype>` | creates a **draft** document (Drafts table) | yes — a human just never adds it |
| `sapb1 post <EntitySet>` | creates an object **live**, no draft (bare entity sets only) | no |
| `sapb1 patch <Entity(key)>` | updates fields on one existing object | no |

Add `--dry-run` to any of them to see the exact request and send nothing.

All three take the body as a single JSON object via `--data '<json>'` or
`--data-file <path>` (`-` and `/dev/stdin` read stdin, which forces `--yes` since
stdin is then already spoken for), preview it, and confirm before sending.
`--json` prints SAP's response body verbatim; without it you get a one-line
summary.

### `--dry-run` — see it without sending it

```bash
$ sapb1 draft order --dry-run --data '{"CardCode":"C0001","DocumentLines":[{"ItemCode":"A0001","Quantity":10}]}'
DRY RUN — nothing was sent to SAP.
  company : JIVO_OIL_HANADB
  request : POST https://sap.example:50000/b1s/v1/Drafts
  payload :
    {
      "DocObjectCode": "oOrders",
      "CardCode": "C0001",
      "DocumentLines": [
        {
          "ItemCode": "A0001",
          "Quantity": 10
        }
      ]
    }
Re-run the same command with --yes to send it.
```

Nothing is contacted — there is no login, no request, no write-log entry — and it
exits `0`. With `--json` you get a single compact object (`dryRun`, `companyDb`,
`host`, `port`, `method`, `url`, `payload`) whose `payload` is the exact bytes
that would be sent, which is what makes it safe for an agent to show an operator
before asking permission.

### `sapb1 draft <doctype>` — the intended write path

**Draft first.** A draft is not a posted document: it moves no stock, writes no
ledger entry, and does not become real until a person opens SAP B1
(Sales/Purchasing → **Document Drafts**), reviews it, and presses **Add**. That
keeps the irreversible step where it belongs — with a human in the SAP client.

Drafts *are* visible in SAP: anyone can see them in Document Drafts, and if an
approval workflow is configured for that document type, a draft can enter it.
Treat a draft as "submitted for review", not as private scratch space.

```bash
sapb1 draft order --data '{"CardCode":"C0001","DocumentLines":[{"ItemCode":"A0001","Quantity":10}]}'
sapb1 draft purchase-order --company JIVO_MART_HANADB \
  --data '{"CardCode":"V10000","DocumentLines":[{"ItemCode":"A0001","Quantity":100}]}'
sapb1 draft invoice --data-file draft-invoice.json --yes --json
```

`<doctype>` sets the draft's `DocObjectCode` — the type of document it will
become. If you leave the field out, the canonical enum string (`oOrders`) is
spliced in as the first member of your object and nothing else is touched. If your
payload already carries a `DocObjectCode` it must agree with the argument, in
which case your bytes are sent exactly as written; if it disagrees, the command
refuses rather than guess. Accepted forms, case-insensitive: the friendly name,
the entity set, the `oXxx` enum, or the numeric object type.

| Name | Entity set | Enum | Code |
|---|---|---|---|
| `quotation` | Quotations | `oQuotations` | 23 |
| `order` | Orders | `oOrders` | 17 |
| `delivery` | DeliveryNotes | `oDeliveryNotes` | 15 |
| `return` | Returns | `oReturns` | 16 |
| `invoice` | Invoices | `oInvoices` | 13 |
| `credit-note` | CreditNotes | `oCreditNotes` | 14 |
| `purchase-quotation` | PurchaseQuotations | `oPurchaseQuotations` | 540000006 |
| `purchase-order` | PurchaseOrders | `oPurchaseOrders` | 22 |
| `grpo` / `goods-receipt-po` | PurchaseDeliveryNotes | `oPurchaseDeliveryNotes` | 20 |
| `purchase-return` | PurchaseReturns | `oPurchaseReturns` | 21 |
| `purchase-invoice` | PurchaseInvoices | `oPurchaseInvoices` | 18 |
| `purchase-credit-note` | PurchaseCreditNotes | `oPurchaseCreditNotes` | 19 |
| `down-payment` | DownPayments | `oDownPayments` | 203 |
| `purchase-down-payment` | PurchaseDownPayments | `oPurchaseDownPayments` | 204 |

The flow, end to end:

```
sapb1 draft order --data '…'        →  preview + "Type 'yes' to send this write to JIVO_OIL_HANADB:"
                                    →  Draft created in JIVO_OIL_HANADB: DocEntry 4321, DocNum 99 (oOrders).
                                       Open SAP B1 → Document Drafts → review → Add.
human in SAP B1                     →  Document Drafts → open it → check it → Add
```

### `sapb1 post <EntitySet>` — direct create (escape hatch)

Posts your JSON straight at an entity set. **Prefer `draft` for anything
document-shaped** — a document created here is live the moment SAP accepts it,
and this CLI can't cancel it. Where `post` earns its keep is master data and
other non-posting objects that have no draft equivalent.

```bash
sapb1 post BusinessPartners --data '{"CardCode":"C90001","CardName":"Test Customer","CardType":"cCustomer"}'
sapb1 post Items --data-file new-item.json --json
```

Field names are the entity's own — the same ones `sapb1 fields <Entity>` lists.
The argument must be a bare entity set the catalog knows (case-insensitive; the
catalog's canonical spelling is what's sent). Anything else is refused:

```bash
$ sapb1 post "Invoices(9)/Cancel" --data '{}'
Error: "Invoices(9)/Cancel" is not a bare entity-set name. Writes address entity
sets only (e.g. BusinessPartners, Items) — paths with (), /, ?, $ or . are
rejected. In particular OData actions like Invoices(9)/Cancel, Orders(1)/Close or
Drafts(4321)/SaveDraftToDocument are deliberately not supported: posting,
cancelling and closing documents is left to a human in the SAP B1 client
```

### `sapb1 patch <Entity(key)>` — update one object

Changes only the fields you send; everything else is left alone. A successful
PATCH normally returns `HTTP 204` with no body.

```bash
sapb1 patch "BusinessPartners('V10000')" --data '{"Phone1":"9876543210"}'
sapb1 patch BusinessPartners --key V10000 --data '{"EmailAddress":"ap@vendor.com"}'
sapb1 patch Items --key "OIL/1L/MUS" --data '{"ItemName":"Mustard Oil 1L"}'
sapb1 patch Orders --key 123 --data '{"Comments":"customer moved delivery to Monday"}' --yes
```

Both spellings are **parsed and rebuilt**, never forwarded as typed, which buys
three things:

- **Whether the key is quoted comes from the entity, not from how the key looks.**
  `CardCode` is a string key, so `--key 200001` becomes
  `BusinessPartners('200001')` — not `BusinessPartners(200001)`, which SAP would
  reject. Document entities (`DocEntry`) take bare numbers.
- **Keys are percent-encoded.** JIVO item codes contain `/` (`OIL/1L/MUS`), which
  raw would add path segments and address something else entirely; `#` would
  truncate the URL, `%` would be an invalid escape. What you see in the preview,
  what lands in the write log and what goes on the wire are the same bytes:
  `Items('OIL%2F1L%2FMUS')`.
- **Query strings, action paths and trailing junk are refused**, e.g.
  `patch "Items('A')?$select=ItemName"` or `patch "Orders(1)/Cancel"`.

Patch narrow, and patch things that are safe to change (remarks, contact
details, a reference field) — not the numbers on a posted document. SAP itself
refuses most edits to closed/posted documents.

### The write log

Every write attempt appends **two** JSON lines to `queries/<operator>/sap-writes.jsonl`
(inside the checkout, so it syncs with that operator's session log; falls back to
`~/.sapb1-writes.jsonl` outside a registered checkout)
(override with `$SAPB1_WRITE_LOG`), mode `0600` — an `intent` line *before* the
request goes out and an `outcome` line once it resolves:

```json
{"time":"2026-07-30T11:04:12+05:30","event":"intent","host":"sap.example","port":50000,"company_db":"JIVO_OIL_HANADB","user":"manager","method":"POST","path":"Drafts","payload":{"DocObjectCode":"oOrders","CardCode":"C0001"}}
{"time":"2026-07-30T11:04:13+05:30","event":"outcome","host":"sap.example","port":50000,"company_db":"JIVO_OIL_HANADB","user":"manager","method":"POST","path":"Drafts","payload":{"DocObjectCode":"oOrders","CardCode":"C0001"},"status":201,"result_key":"DocEntry=4321"}
```

Why two lines: if the process dies mid-POST (Ctrl-C, closed laptop), the intent
line is already on disk — so **an `intent` with no matching `outcome` is exactly
the "this may have committed, go check SAP" case**, in file form. A re-login
retry produces a pair per attempt, so the pair count always matches the number of
requests actually sent.

`host`/`port`/`company_db` are on every line, so the log can answer the question
that matters afterwards: *was that production?* Failures carry `"error"` and the
status SAP returned (`0` when the request never completed).

The SAP login password never appears. The **payload does**, verbatim — that's the
audit trail, and it's why the file is `0600` (a pre-existing looser file gets
tightened on the next write). Logging is best-effort: if the log can't be written
you get one warning on stderr and the write proceeds regardless.

```bash
tail -4 queries/*/sap-writes.jsonl | jq .                              # what did this box change, and when
jq -r 'select(.event=="intent") | .path' queries/*/sap-writes.jsonl    # every request that was sent
```

## MCP server (for AI agents)

`sapb1 mcp` runs a **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server over stdio, so an AI agent (Claude Code / Claude Desktop) can call the
Service Layer as tools. It reuses the same client, catalog, and config as the
CLI — and stays strictly read-only: every tool is a `GET` (plus `Login`/`Logout`
for the session), with `readOnlyHint: true` in the tool metadata. **The CLI's
write commands are deliberately not exposed as tools**, and a test
(`TestRegisteredToolsAreReadOnly`) fails the build if a non-read-only tool is
ever registered. The password is never returned in a tool result or error.

It exposes nine tools:

- `sapb1_doctor` — config + reachability + login self-check.
- `sapb1_query` — the core generic read (`entity`, `select`, `filter`, `top`, `orderby`).
- `sapb1_entities` / `sapb1_ops` — offline catalog discovery.
- `sapb1_fields` — live field discovery with offline fallback.
- `sapb1_orders` / `sapb1_invoices` / `sapb1_items` / `sapb1_partners` — convenience wrappers.

Register it with Claude Code by adding this to `~/.claude.json` under
`mcpServers`:

```json
{
  "mcpServers": {
    "sapb1": {
      "command": "/Users/damanpreetsingh/sapb1-cli/sapb1",
      "args": ["mcp"]
    }
  }
}
```

Once registered, an agent can call `sapb1_query` with
`entity="Orders"`, `filter="DocumentStatus eq 'bost_Open'"` to pull open sales
orders. (The Service Layer property is `DocumentStatus`; `DocStatus` is the HANA
column name and is rejected outright.)

Full copy-paste registration for Claude Code and Claude Desktop, the tool
reference, and a stdio smoke-test are in **[MCP.md](MCP.md)**.

## Exit codes

| Code | Meaning              |
|------|----------------------|
| 0    | success              |
| 2    | usage error          |
| 3    | config missing/invalid |
| 4    | authentication failed |
| 5    | network/unreachable — **nothing was sent** |
| 6    | API error (server reached, request definitively rejected) |
| 7    | **write outcome unknown** — the request was sent, the answer never came back |

Write commands mostly reuse the read codes: SAP rejecting a `draft`/`post`/`patch`
with its own error envelope is an API error (**6**, nothing committed), and a bad
payload, a rejected target or an aborted confirmation is a usage error (**2**,
nothing sent).

**Code 7 is the one that needs a human.** It means the write went out but its
result is unknown — a client-side timeout, a connection reset after the request
was transmitted, or a bare `502`/`504` from a gateway in front of SAP:

```
Error: POST Drafts on JIVO_OIL_HANADB: the write request was sent but its outcome
is unknown — it MAY have been committed in SAP (the response never arrived). Check
SAP (query the entity / Document Drafts) before re-running this command: a blind
retry can create a duplicate
```

So in a script: `0` means it landed, `2`/`3`/`4`/`5` mean it did not, **`6` means
SAP refused it, and `7` means nobody knows — go look before doing anything else.**
A non-zero exit does *not* by itself prove the write didn't happen; only codes
2–6 do. (Writes also get a longer default timeout than reads — 120s instead of
30s — precisely to make code 7 rare; an explicit `--timeout`/`SAPB1_TIMEOUT`
still wins.)

## Session handling

`Login` returns `B1SESSION`/`ROUTEID` cookies which are sent on every
subsequent request. Sessions idle out after roughly 30 minutes; when a
request comes back `401`, sapb1 transparently re-logs-in once and retries
before giving up. The session is cached at `~/.sapb1-session.json` (mode
`0600`) so you don't have to re-login for every command.

## Self-signed certificates

SAP boxes commonly run with self-signed TLS certificates, even on port
50000 (the Service Layer is HTTPS-only). Set `SAPB1_INSECURE=true` in
`.env`, or pass `--insecure`, to skip certificate verification.
