# sapb1

A command-line client for the SAP Business One Service Layer (`b1s/v1`), built
for SAP B1 for HANA. **Read-only by default**, with four explicit write
commands you have to type on purpose.

Every business-data read (`orders`, `invoices`, `items`, `partners`, `query`,
`fields`, `doctor`) is a plain OData `GET`. Writes live in exactly four
commands — `draft`, `post`, `patch`, `delete` — each of which previews the
request, asks you to confirm, and records the attempt in a local log. `delete`
reaches **drafts only**: `sapb1 delete draft <DocEntry>` and
`sapb1 delete payment-draft <DocEntry>`, guarded so it will not touch a draft this
CLI did not create. Nothing here can delete a posted document.

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
- `internal/client` exposes exactly three write operations — `Create` (POST),
  `Update` (PATCH) and `Delete` (DELETE). There is **no `PUT`** anywhere in the
  codebase, and `Delete` refuses any entity set outside a two-name allowlist —
  `Drafts` and `PaymentDrafts` — which it checks itself before building the path.
  That allowlist, not the command tree, is what makes `DELETE Invoices(9)`
  impossible to express: no caller can hand it another entity set.
- `post` accepts only a **bare entity-set name that the embedded catalog knows
  and that supports a plain POST**. That is what keeps it from being a generic
  "POST anything" tool: SAP's OData **actions** — `Invoices(9)/Cancel`,
  `Orders(1)/Close`, `Drafts(4321)/SaveDraftToDocument`, `$batch`, anything with
  `(`, `)`, `/`, `?`, `$` or `.` in it — are refused before a session is even
  opened, with no flag to override. Cancelling, closing and posting a draft stay
  with a human in the SAP B1 client. (What the CLI *can't* do is not the same as
  "nothing can be changed": a `post`/`patch` it does perform is live and only SAP
  can reverse it.)
- Those three operations are reachable only from `sapb1 draft`, `sapb1 post`,
  `sapb1 patch` and `sapb1 delete draft`/`delete payment-draft`. Each one:
  1. prints the exact company, request and payload it is about to send (to
     **stderr**, so `--json` output on stdout stays parseable),
  2. requires a typed `yes` at the prompt — exactly `yes`, since one stray
     keystroke shouldn't commit a production write — or `--yes`, which is
     mandatory when stdin isn't a terminal (cron, pipes, agents), and
  3. appends an intent line before the request and an outcome line after it to
     the write log, successes and failures alike.
- `--dry-run` prints the exact request and sends **nothing** (not even a Login),
  exit 0. That is the sanctioned way for an agent to propose a write: dry-run it,
  show the operator, and only re-run with `--yes` if they say go. The one exception
  is `delete --dry-run`, which **does** contact SAP — read-only, to look the drafts
  up so the preview shows the real documents — and still sends no `DELETE`.
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

The catalog lists every operation the Service Layer documents, including `PUT` and
a `DELETE` on almost every entity. Those rows are informational: sapb1 implements
no `PUT` at all, and the only `DELETE` it will issue is on `Drafts`/`PaymentDrafts`
via [`sapb1 delete`](#sapb1-delete-draft-docentry--remove-a-draft). Its writes
are the `POST`/`PATCH`/`DELETE` behind
[`draft`, `post`, `patch` and `delete`](#writing-to-sap).

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

Four commands can change data. They only ever run because you typed them.

| Command | What it does | Reversible? |
|---|---|---|
| `sapb1 draft <doctype>` | creates a **draft** document (Drafts table) | yes — a human just never adds it |
| `sapb1 post <EntitySet>` | creates an object **live**, no draft (bare entity sets only) | no |
| `sapb1 patch <Entity(key)>` | updates fields on one existing object | no |
| `sapb1 delete draft <DocEntry>…` | removes a **draft** (`delete payment-draft` for payment drafts) | no — SAP has no undo for a deleted draft |

Add `--dry-run` to any of them to see the exact request and send nothing. (`delete
--dry-run` is the one that still *reads* SAP — see below.)

The first three take the body as a single JSON object via `--data '<json>'` or
`--data-file <path>` (`-` and `/dev/stdin` read stdin, which forces `--yes` since
stdin is then already spoken for), preview it, and confirm before sending.
`--json` prints SAP's response body verbatim; without it you get a one-line
summary. `delete` takes no body at all — just DocEntries.

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

**`delete --dry-run` is the exception**: it logs in and performs the read-only
`GET Drafts(N)` for every DocEntry, so the preview shows the actual draft you are
about to destroy — vendor, total, reference, status — instead of a URL you have to
take on trust. It still sends no `DELETE`, writes no write-log entry and exits `0`,
and it says so in as many words. The guards run in a dry run too, so a draft one of
them refuses exits **9** here as well — a dry run tells you it would be stopped
before you queue the real one.

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

### `sapb1 delete draft <DocEntry>` — remove a draft

The only delete there is, and it is bound to drafts by construction. `sapb1 delete
draft` always means `Drafts`, `sapb1 delete payment-draft` always means
`PaymentDrafts`, and there is no third subcommand and no entity argument — so
`sapb1 delete Invoices(9)` and `sapb1 delete "Drafts(1)/Cancel"` fail as *unknown
command*, not as a refused request. `sapb1 delete` on its own prints a refusal
explaining that only drafts can go. Underneath, `client.Delete` checks the entity
set against a two-name allowlist and builds the path itself, so even a future
caller inside the codebase cannot express a `DELETE` against anything else.

A draft is the one thing here that is safe to destroy: it posts nothing, moves no
stock and writes no ledger entry. A posted document is SAP's job, in the SAP B1
client — and a deleted draft does not come back, so the command is built to make
you look at what you are deleting first.

```bash
sapb1 delete draft 54990                        # preview, then type yes
sapb1 delete draft 54990 54991 54992 --dry-run  # look the drafts up, send no DELETE
sapb1 delete draft 54990 54991 --yes            # once the operator has okayed these
sapb1 delete payment-draft 77                   # PaymentDrafts, identical shape
```

DocEntries are digits only — no `0`, no sign, no decimals, and nothing larger than
SAP's 32-bit `DocEntry` (`2147483647`). Repeats are deleted once, with a note on
stderr; your order is preserved. **Up to 50 per invocation** (a bad `acc/` batch is
50 drafts); more than that and it tells you to split the list.

#### What it does, in order

1. **Reads every draft** — one read-only `GET` each — and prints a summary block:
   DocEntry, DocNum, DocObjectCode/DocType, CardCode/CardName, DocDate, DocTotal,
   NumAtCard, DocumentStatus, **AuthorizationStatus** (a draft can be sitting in
   somebody's Approval Status Report while still reading `bost_Open` — its own
   guard now, see `--in-approval` below), BPLName,
   Series, UserSign/CreationDate, AttachmentEntry, Comments, and a `created here`
   line naming the write-log entry that vouches for it. `payment-draft` prints its
   own set — the funding legs, `CashSum`/`TransferSum`/`BillOfExchangeAmount` plus a
   computed total per cheque/card leg — so a cheque-funded payment never previews as
   `0.0`. Fields SAP did not return are skipped rather than printed empty.
2. **Runs the guards** (below) against all of them. If any guard refuses, you get
   every problem at once and nothing is sent — exit **9**. Under `--json` that
   refusal is still a record per DocEntry on stdout, so a batch caller can see which
   one stopped it without scraping stderr.
3. **Previews the whole batch to stderr and asks once**:

   ```
   About to DELETE from SAP:
     company : JIVO_OIL_HANADB
     user    : USER36
     drafts  : 2
     request : DELETE https://127.0.0.1:15000/b1s/v1/Drafts(54990)   [created by USER36, queries/USER36/sap-writes.jsonl:2]
     request : DELETE https://127.0.0.1:15000/b1s/v1/Drafts(54991)   [created by USER36, queries/USER36/sap-writes.jsonl:8]
     record  : each DELETE is appended to queries/USER36/sap-writes.jsonl and shared with the team.
     contents: what the draft held (party, bill number, totals, line prices) is kept in
               /Users/USER36/.sapb1-delete-snapshots.jsonl on THIS machine only; the shared line carries just its sha256.
   A deleted draft is gone from Document Drafts. Nothing posted is touched, and SAP cannot bring a draft back.
   Type 'yes' to DELETE 2 draft(s) from JIVO_OIL_HANADB (this cannot be undone):
   ```

   The `record` line is not decoration: it says where this delete will be readable
   afterwards, and it changes. No operator registered in this checkout and it says so
   (`python3 harness/bin/setup.py` is the one-command fix); `$SAPB1_WRITE_LOG` pointing
   somewhere else and it names that file too.

   Same contract as every other write — exactly `yes`, `y` rejected, `--yes` skips
   it, a non-terminal stdin without `--yes` refuses — but the prompt names the verb,
   the count and the company, because a prompt you have typed `yes` at fifty times
   stops being a decision.
4. **Deletes sequentially.** Immediately before each `DELETE` it re-reads that draft:
   a batch takes minutes over a slow link, and in that window someone may have
   pressed **Add**. Already gone → counted **skipped**, never "deleted" (no request
   was sent and no log line exists for it), batch continues. `DocumentStatus`
   *changed* since the preview → the batch stops right there (exit **9**; `--closed`
   asserts what the draft was when you looked at it, and covers nothing a colleague
   did afterwards). That re-read is also what the snapshot is built from — see
   below.
5. **Verifies.** After a 2xx it reads the draft back. Gone → `verified gone`. Still
   readable, or the read-back itself failed → exit **8** with what to check, and the
   note that re-running a `DELETE` is safe.

Each draft gets its own intent/outcome pair in the write log, and the batch stops at
the first failure: you are told what was deleted, what could not be *verified*
(SAP answered the `DELETE`, only the read-back after it did not — almost certainly
gone, and its own column so nobody re-keys it), what failed, what was skipped and
what was never attempted, so re-running the same command finishes the job (the
drafts already gone are skipped, not treated as errors).

**It also stops if it cannot report.** `--json | head -1` and `| grep -q` close the
pipe after the first record; the batch then used to keep deleting into a stream
nobody was reading and die of `SIGPIPE`. Now a record that cannot be written to
stdout stops the run at that DocEntry with exit **8** — same code, same advice as a
failed read-back: it probably happened, go and look, re-running is safe. At most one
DocEntry is destroyed past the last record you managed to read. Redirect to a file
rather than piping into something that closes early.

#### The six guards, and the flag that lifts each one

On by default, all of them. Each flag is an assertion *you* are making, and each one
is recorded in the write log line for that delete.

| Refuses when | Flag that lifts it | Why the guard exists |
|---|---|---|
| No write-log line shows this CLI created that draft | `--not-created-here` | A person keyed it in the SAP B1 client; deleting it means they re-key it from scratch |
| The creating log line is more than **24h** old | `--older-than <dur>` (e.g. `48h`) | A delete a day later is not batch cleanup |
| The draft has a file attached (`AttachmentEntry` set) | `--with-attachment` | Someone did work on this draft — attachments do not appear on batch junk |
| `DocumentStatus` is not `bost_Open` | `--closed` | It may have been Added — the draft is the trail of a real document. (`PaymentDrafts` carries no `DocumentStatus`; the command says so and the check does not apply there) |
| The creating log line's user is not your configured user | `--other-operator` | A draft is owned by the login that made it — it is not even in *your* Document Drafts list, and they may be waiting on it |
| `AuthorizationStatus` is not `dasWithout` (`dasPending`, `dasApproved`, `dasGenerated`, `dasRejected`) | `--in-approval` | An approval template matched it, so a second person has it in their Approval Status Report. An Oil A/P draft routing through "USER03 AP" still reads `bost_Open`, so no other guard sees it — and with `--yes` nobody reads the summary either. Absent field = check does not apply (`PaymentDrafts`) |

Two more checks have **no flag of their own**, and both come out as
`--not-created-here`, because both mean the vouching line is not evidence about this
row: a log line whose timestamp is missing or in the future (a torn append, a
hand-edit, a box whose clock is wrong — and every age check rests on that stamp),
and a log line whose date contradicts SAP's own `CreationDate` on the row (DocEntry
numbers come round again after a company restore). SAP's answer beats the local
file. Where SAP returns no `CreationDate` at all — `PaymentDrafts` does not — the
cross-check cannot run, and the command says so on stderr rather than letting
`created here: yes` read as if the server had confirmed it.

`--not-created-here` is deliberately the awkward one: **exactly one DocEntry, a
person must answer the prompt, and it cannot be combined with `--yes`** (or with a
non-terminal stdin). It is the flag that says "I know a human made this draft and I
am removing it anyway", and that is a claim about one specific document, not a batch
mode.

The refusal itself tells you what to do:

```
refusing to delete Drafts(54990) in JIVO_OIL_HANADB: no record that this CLI created it.
  Scanned 1 write log(s): queries/USER36/sap-writes.jsonl — none has a successful POST Drafts that returned DocEntry=54990 for JIVO_OIL_HANADB.
  That usually means a person keyed this draft in the SAP B1 client, and deleting it means they re-key it from scratch.
  A colleague's sapb1 log only reaches this box if they committed queries/<them>/sap-writes.jsonl — ask them, or check `git log -- queries/`.
  If it really should go, re-run with --not-created-here (one DocEntry at a time, and a person must answer the prompt); the override is recorded in the write log.
```

#### What "this CLI created it" means

A line in a write log with `event=outcome`, `method=POST`, `path=Drafts` (or
`PaymentDrafts`), the same `company_db`, a 2xx status and
`result_key: "DocEntry=<N>"`. **Evidence is read from one place: every
`queries/*/sap-writes.jsonl` under the repo root** — one pass over all of them, and
the **earliest timestamped** line for a DocEntry wins, whichever file it came from
(not whichever the glob reached first, which is alphabetical by operator and says
nothing about who created the draft). A line with no timestamp never displaces a
real one; it is indexed only when nothing else has, so the log-timestamp check can
refuse on it by name instead of the delete falling through to "no record".
`$SAPB1_WRITE_LOG` is admitted only when the file it names
*resolves* inside that same `queries/` tree (which is how `acc/_playbook/sap` runs);
pointed anywhere else it is where this run **records** its writes, not a witness, and
you get a note on stderr saying so. **`~/.sapb1-writes.jsonl` is never evidence** —
`$HOME` is as settable as `$SAPB1_WRITE_LOG`, and a guard that a one-line env var can
satisfy is not a guard. A file that is not a regular file, or that resolves outside
`queries/` through a symlinked directory, is skipped with a note.

The repo root is found by walking up from the **binary** (then the working
directory) looking for a directory that has both `harness/` and `.git/`; a scratch
folder or a Drive-zip kit (`harness/` but no `.git/`) does not qualify, and in that
case you simply get "no write log found" and the recorded override path. If the
binary's checkout and the one you are standing in disagree, the binary's wins and
both are named on stderr — that is the stale-kit smell. **The same root decides
where your writes are recorded**, so a Drive zip both writes to
`~/.sapb1-writes.jsonl` and reads evidence from nowhere: one answer, not two that
can drift apart.

There is one trap worth knowing before a batch: an **unregistered** checkout records
its writes to `~/.sapb1-writes.jsonl` while reading evidence from `queries/*`, so
drafts it created thirty seconds ago refuse to delete. The refusal says this out
loud and names the fix — `python3 harness/bin/setup.py`, once — because the
alternative (`--not-created-here`, one DocEntry, a human at each prompt) is fifty
prompts for a fifty-draft batch.

This is an **audit** property, not a security boundary — nobody is stopped from
appending a line to their own log. What it buys is attributability: the file, line,
user and time that vouched for a delete are shown in the preview *and* persisted in
the delete's own log lines, so a planted line is greppable afterwards and belongs to
somebody.

#### `--json`

One compact JSON object **per draft, one per line** — deliberately not the single
object `draft`/`post`/`patch` produce, because a batch has an outcome per draft.
Human summaries and the preview go to stderr, so stdout stays parseable.

```json
{"docEntry":54990,"entitySet":"Drafts","companyDb":"JIVO_OIL_HANADB","host":"127.0.0.1","port":15000,"method":"DELETE","url":"https://127.0.0.1:15000/b1s/v1/Drafts(54990)","status":204,"verified":true,"createdHere":true,"origin":{"user":"USER36","time":"2026-08-22T14:59:11+05:30","file":"queries/USER36/sap-writes.jsonl","line":2},"overrides":[],"snapshotSha256":"9f2c1b…","snapshot":{"DocEntry":54990,"CardCode":"V10000","DocTotal":118000}}
{"docEntry":54991,"entitySet":"Drafts","companyDb":"JIVO_OIL_HANADB","verified":false,"createdHere":false,"skipped":"not found — already deleted","overrides":[]}
{"docEntry":54992,"entitySet":"Drafts","companyDb":"JIVO_OIL_HANADB","verified":false,"createdHere":false,"skipped":"not attempted — stopped after Drafts(54991) failed","overrides":[]}
```

`verified`, `createdHere` and `overrides` are on **every** record, present even when
false or empty, so fifty lines can be read without inferring anything from an absent
key.

**The snapshot CONTENTS ride exactly one kind of record: the one for a draft SAP has
actually destroyed.** That record is your receipt, and the only copy left on stdout.
A refused, skipped or dry-run record carries **`snapshotSha256` and nothing else** —
the draft is still there to be read, so putting the vendor, their bill number and
every line price into a journal or a CI transcript buys nothing. The hash is the
same one the write log's intent line carries and the key into the local snapshot
log, so anything that has to match the two up still can. (Two spellings, one hash:
`snapshotSha256` in this stream, `snapshot_sha256` in the write log, which is
snake_case throughout.)

**A refusal is a record too.** When a guard stops one draft, exit is **9** and stdout
still carries a line per DocEntry — the refused one with `refused` (the guard names),
`reason` (what the operator would have read) and `suggestedFlags` (the exact flags
that would assert past it), the rest marked not attempted:

```json
{"docEntry":54993,"entitySet":"Drafts","companyDb":"JIVO_OIL_HANADB","host":"127.0.0.1","port":15000,"method":"DELETE","url":"https://127.0.0.1:15000/b1s/v1/Drafts(54993)","verified":false,"createdHere":true,"refused":["in-approval"],"reason":"refusing to delete Drafts(54993): this draft is in an approval workflow (AuthorizationStatus dasPending) — someone is acting on it.\n  It is in their Approval Status Report, not only in your Document Drafts, and deleting it takes the request out from under them with no notice.\n  Ask them first. If it really should go, re-run with --in-approval (recorded in the write log).","suggestedFlags":["--in-approval"],"origin":{"user":"USER36","time":"2026-08-22T14:59:11+05:30","file":"queries/USER36/sap-writes.jsonl","line":9},"overrides":[],"snapshotSha256":"4d81ae…"}
{"docEntry":54994,"entitySet":"Drafts","companyDb":"JIVO_OIL_HANADB","verified":false,"createdHere":true,"skipped":"not attempted — Drafts(54993) was refused","origin":{"user":"USER36","time":"2026-08-22T15:01:44+05:30","file":"queries/USER36/sap-writes.jsonl","line":11},"overrides":[],"snapshotSha256":"7b03c9…"}
```

`--dry-run --json` gives the same one-line-per-draft shape with `"dryRun":true`,
`host`, `port`, `method`, `url` and `snapshotSha256` — no `status`, and no snapshot
contents. `--csv` is refused — use `--json`.

Redirect this stream to a file rather than piping it into something that closes
early: a record that cannot be written stops the batch at that DocEntry with exit
**8** (above).

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

**A delete is the exception, in three directions.**

*Extra fields.* Its log lines carry `origin` (the file, line, user and time of the
write-log entry that proved this CLI created the draft), `overrides`
(`["not-created-here"]`, `["older-than=48h","with-attachment"]`, … — absent when no
guard was lifted), and, **on the intent line only, `snapshot_sha256`** — the sha256
of the draft as it read *immediately before* the `DELETE`. That is the step-4
re-read, not the copy you were shown at the preview: an edit that leaves
`DocumentStatus` alone (a line added, a total corrected, the bill number fixed)
passes the status re-check, and the snapshot is the only surviving copy of what was
destroyed, so it has to be a copy of what was destroyed.

```json
{"time":"2026-08-24T21:41:07+05:30","event":"intent","host":"127.0.0.1","port":15000,"company_db":"JIVO_OIL_HANADB","user":"USER36","method":"DELETE","path":"Drafts(54990)","snapshot_sha256":"9f2c1b…","origin":{"file":"queries/USER36/sap-writes.jsonl","line":2,"user":"USER36","time":"2026-08-22T14:59:11+05:30","host":"127.0.0.1","port":15000}}
{"time":"2026-08-24T21:41:08+05:30","event":"outcome","host":"127.0.0.1","port":15000,"company_db":"JIVO_OIL_HANADB","user":"USER36","method":"DELETE","path":"Drafts(54990)","status":204,"origin":{"file":"queries/USER36/sap-writes.jsonl","line":2,"user":"USER36","time":"2026-08-22T14:59:11+05:30","host":"127.0.0.1","port":15000}}
```

*The contents are not in this file.* The snapshot itself goes to a **local** log,
`~/.sapb1-delete-snapshots.jsonl` (`$SAPB1_SNAPSHOT_LOG` redirects it), one line
carrying `sha256` + the object. `queries/<operator>/sap-writes.jsonl` is committed
into a repo that is **public**, and a snapshot holds the vendor's name, their bill
number and every line item with its price. So the shared history says a specific,
verifiable thing was destroyed and an auditor on that machine can prove *which*,
without publishing somebody's invoice. That local log is never committed —
`.gitignore` it if you ever move it into the tree.

*Both records are preconditions, not best-effort.* If the snapshot log cannot be
written, or the intent line cannot be written, the `DELETE` is **not sent** (exit
**3**). A `POST` whose log failed still leaves the object in SAP to look at; a
deleted draft leaves nothing. And a `DELETE` is written to
`queries/<operator>/sap-writes.jsonl` **whatever `$SAPB1_WRITE_LOG` says** (the
configured file gets it too, so a wrapper tailing it keeps working) — divert a
delete's record and there is no SAP row left to reconstruct it from.

Because that record fans out to two files, **every destination is proved writable
before any of them is written**. Written one at a time, a failure on the second left
the first — the committed, shared one — holding an intent line with no outcome, and
an intent with no outcome is precisely how this tool spells "sent, outcome unknown":
a delete that never left the machine published a phantom into the team's history and
then refused. The refusal now **names the file that has to change**, and offers
`$SAPB1_WRITE_LOG` only when that variable is what chose the failing file — for the
in-checkout log it says so plainly, because no environment variable moves that one.

The snapshot is a fixed allowlist of fields, not the whole object: document header
plus reduced lines, and for a payment draft each funding leg as **one computed
total** (`ChequeSum`, `CreditCardSum`). Bank and cheque detail — the numbers, bank
codes and account numbers inside `PaymentChecks`/`PaymentCreditCards`,
`TransferAccount`, `BankAccount` — is excluded by construction (an allowlist, not a
blocklist) and by test.

```bash
tail -4 queries/*/sap-writes.jsonl | jq .                              # what did this box change, and when
jq -r 'select(.event=="intent") | .path' queries/*/sap-writes.jsonl    # every request that was sent
jq -r 'select(.method=="DELETE" and .event=="intent") | "\(.path) \(.snapshot_sha256)"' \
  queries/*/sap-writes.jsonl                                           # every draft deleted, + the hash of its contents
jq --arg h "<that hash>" 'select(.sha256==$h) | .snapshot' \
  ~/.sapb1-delete-snapshots.jsonl                                      # …and what that one held (this machine only)
```

## MCP server (for AI agents)

`sapb1 mcp` runs a **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server over stdio, so an AI agent (Claude Code / Claude Desktop) can call the
Service Layer as tools. It reuses the same client, catalog, and config as the
CLI — and stays strictly read-only: every tool is a `GET` (plus `Login`/`Logout`
for the session), with `readOnlyHint: true` in the tool metadata. **The CLI's
write commands are deliberately not exposed as tools** — including `delete`, whose
`client.Delete` is named in the AST guard's forbidden list, so the mcp package
cannot so much as mention it — and a test (`TestRegisteredToolsAreReadOnly`) fails
the build if a non-read-only tool is ever registered. The password is never returned
in a tool result or error.

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
| 3    | config missing/invalid — and, for `delete`, an unwritable write log or snapshot log (**nothing was sent**) |
| 4    | authentication failed |
| 5    | network/unreachable — **nothing was sent** |
| 6    | API error (server reached, request definitively rejected) |
| 7    | **write outcome unknown** — the request was sent, the answer never came back |
| 8    | **sent, but unverified** — SAP answered and your evidence of it did not arrive (read-back failed, or the record could not be written to stdout); the draft is probably gone, re-running is safe |
| 9    | **a guard refused** — provenance/age/attachment/closed/other-operator/in-approval; get a human, don't reach for the override |

Write commands mostly reuse the read codes: SAP rejecting a
`draft`/`post`/`patch`/`delete` with its own error envelope is an API error (**6**,
nothing committed), and a bad payload, a rejected target, a DocEntry that isn't a
number, or an aborted confirmation is a usage error (**2**, nothing sent).

**Code 7 is the one that needs a human.** It means the write went out but its
result is unknown — a client-side timeout, a connection reset after the request
was transmitted, or a bare `502`/`504` from a gateway in front of SAP:

```
Error: POST Drafts on JIVO_OIL_HANADB: the write request was sent but its outcome
is unknown — it MAY have been committed in SAP (the response never arrived). Check
SAP (query the entity / Document Drafts) before re-running this command: a blind
retry can create a duplicate
```

A `delete` that times out gets the same code with different advice: go and check
(`sapb1 query Drafts --filter "DocEntry eq 54990"` — nothing back means it went
through), because unlike a `POST`, re-sending a `DELETE` cannot create a duplicate.
Look first either way.

**Codes 8 and 9 belong to `delete`.**

- **8** means SAP definitively answered the `DELETE` (a 2xx arrived) and *your*
  evidence of it did not arrive: the read-back failed, or still returned the draft,
  or the record could not be written to stdout at all because the pipe closed
  (`--json | head -1`). That is not code 7: the request's outcome is known, only the
  confirmation isn't. The message tells you to check Document Drafts, and says out
  loud that re-running the delete is safe — a `DELETE` cannot double-delete, which is
  exactly what makes it different from a timed-out `POST`.
- **9** means a guard refused: no provenance, an untrustworthy or contradicted log
  line, too old, has an attachment, not open, another operator's draft, or one in an
  approval workflow. Nothing
  was sent for that DocEntry. It is separated from usage errors on purpose, so a
  script can tell "a control stopped this, go get a human" from "you typed it wrong".
  The preflight guards all run before the first `DELETE`, so a 9 from them means the
  whole batch is untouched; the one guard that can fire *mid*-batch is the
  re-read — a draft whose `DocumentStatus` changed while the batch ran stops it
  there, and the tally lists what had already gone.

So in a script: `0` means it landed, `2`/`3`/`4`/`5`/`9` mean it did not, **`6` means
SAP refused it, `8` means the delete went through but wasn't confirmed, and `7` means
nobody knows — go look before doing anything else.** A non-zero exit does *not* by
itself prove the write didn't happen; only codes 2–6 and 9 do. (Writes also get a
longer default timeout than reads — 120s instead of 30s — precisely to make code 7
rare; an explicit `--timeout`/`SAPB1_TIMEOUT` still wins.)

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
