# JIVO CLI — read this first

You are running inside **JIVO's data toolkit**. Someone (often the Accounts team) has opened a terminal here and wants answers about the business — SAP balances, turnover, ledgers, orders, stock. Your job: **answer their questions in plain language, with real numbers, pulled live.**

## ⛔ RULE 0 — READ-ONLY BY DEFAULT; WRITES ONLY WHEN EXPLICITLY ASKED

These tools point at JIVO's **live production** systems. Default behaviour is read-only.

- **Never write unprompted.** Not to "fix" data, not to "finish" a task, not as a helpful extra step. If the operator didn't explicitly ask you to create/update something in SAP, don't.
- **Everything except SAP is read-only, full stop.** postsql, portals, exim, factory, oms, TankhaPay, DSR — reads only. No exceptions, even if asked.
- **Show, don't do.** The way to help with a write is `--dry-run` + the operator's go-ahead, never a guess.
- **SAP has exactly three write commands**, all in `sapb1`, and all only when the operator asks for them by name:
  - `sapb1 draft <doctype>` — creates a **draft** document. Nothing is posted: no stock movement, no ledger entry, until a human opens SAP B1 → Document Drafts, reviews it, and presses **Add**. Drafts *are* visible to others and to any approval workflow.
  - `sapb1 post <EntitySet>` — creates live, no draft. Only for master data (BusinessPartners, Items). **Prefer `draft` for anything document-shaped.**
  - `sapb1 patch <Entity(key)>` — updates fields on one existing object.
- **What the CLI cannot do at all:** there is no `DELETE` and no `PUT` anywhere in it, and `post` only accepts a **bare, catalogued entity set** — so SAP's OData *actions* (`Invoices(9)/Cancel`, `Orders(1)/Close`, `Drafts(4321)/SaveDraftToDocument`) are refused, by design and with no override. Cancelling, closing and posting-a-draft are a human's job in the SAP B1 client. You still cannot undo a `post`/`patch` from here — only SAP can.
- **Every write previews, confirms, and logs.** The command prints the exact request, then requires a typed `yes` (exactly `yes` — `y` is rejected), and appends the attempt to `~/.sapb1-writes.jsonl` (override with `$SAPB1_WRITE_LOG`).
- **Agent flow for a write — do exactly this:** run the command with **`--dry-run`** (sends nothing, exits 0, prints the exact method, URL and payload), show that output to the operator, and only if they say go, run the same command again with `--yes`. Never add `--yes` on your own initiative: a non-interactive session can't answer the prompt, so `--yes` *is* the decision, and it must be the operator's.
- **When in doubt, draft it.** A draft is reversible by a human ignoring it; a posted invoice is not.
- **Exit code 7 means "unknown, go look".** If a write returns exit 7 / "the outcome is unknown", the request reached SAP but the answer didn't come back — it may have committed. **Do not re-run it.** Query SAP (or Document Drafts) to find out what actually exists, and tell the operator.
- The MCP server (`sapb1 mcp`) is **strictly read-only** — no write tool is exposed to agents.

## What's here

A folder of command-line tools ("CLIs"), each a window into one JIVO system. Read-only except for the three SAP write commands above.

| Folder | System | What you can answer |
|---|---|---|
| `sap-b1/` | **SAP B1** (the books, 3 companies) | ledger balances, turnover/sales, invoices, orders, stock, party statements |
| `ecom-cli/` `exim/` `factory-cli/` `oms-cli/` `jsap-cli/` | ecom / imports / factory / orders / ops | channel sales, POs, production, approvals (Go/Python CLIs) |
| `postsql/` | raw Postgres (16 DBs) | direct SQL reads under the apps |
| `portals/` | Blinkit/Zepto seller portals + **TankhaPay** HR/payroll | studied; read-only CLIs built (tankhapay: 297 cmds — employees/attendance/salary/payouts/leave/reports) |

**SAP is the main one for Accounts.** Start there unless asked otherwise.

## How to answer SAP questions

The SAP tool is **`sapb1`**. On **Windows** use `sap-b1\accounts-kit\sapb1.exe` (creds are in a `.env` next to it). On Mac/Linux use `sap-b1/cli/sapb1`. Always run `doctor` first if unsure it's connected.

**Three companies** (pass `--company`, default is Oil):
`JIVO_OIL_HANADB` (Oil) · `JIVO_MART_HANADB` (Mart) · `JIVO_BEVERAGES_HANADB` (Beverages)

**Core commands:**
```
sapb1 doctor                         # is SAP connected?
sapb1 query <Entity> --filter "…" --select "…" --top N [--company DB] [--json]
sapb1 query <Entity> --count --filter "…"        # just the number
sapb1 query <Entity> --all --json                # every matching row (paginated)
```

**Key entities:** `BusinessPartners` (customers/vendors + balances), `Invoices` (A/R sales), `CreditNotes` (sales returns), `Orders` (sales orders), `PurchaseInvoices`/`PurchaseOrders`, `IncomingPayments`/`VendorPayments`, `Items` (stock).

### Definitions that matter (use these, they're correct)
- **Ledger balance** = `BusinessPartners.CurrentAccountBalance`. **Positive = DEBIT** (the party owes JIVO / advance held). **Negative = CREDIT** (JIVO owes them).
- **Turnover / sales** = `Invoices` **net of GST** (`DocTotal − VatSum`) **minus** `CreditNotes` (returns), by `DocDate`, excluding cancelled (`Cancelled eq 'tNO'`). GST-inclusive = `DocTotal`.
- A party can have several accounts (e.g. an employee "IMPREST" vendor account + a customer account) — check all and say which is which.

### Gotchas
- Date filters: `DocDate ge '2026-04-01' and DocDate lt '2026-07-25'` (quoted).
- `toupper()`/`tolower()` are **not supported** — to name-search a partner, fetch `BusinessPartners` with `--all --json` and match in code (case-insensitive) rather than filtering by name.
- For sums/turnover there's no server-side SUM — fetch the rows (`--all --json`, add `--page-size 200` for speed) and total them yourself.
- Money is INR. Present with Indian grouping and crores for big numbers.

## How to behave
- Answer the actual question with the number, then a one-line "how I got it." Offer the drill-down.
- Name the company if it's not Oil. Give date ranges for sales questions.
- Don't wander, never write unprompted (RULE 0), don't expose the SAP password in output.
- More example questions: `sap-b1/accounts-kit/ASK-EXAMPLES.md`. Setup: `sap-b1/accounts-kit/SETUP.md`. Full map: `README.md`. Our work log: `chats/`.

## 🧠 The harness — this toolkit learns

`harness/` is JIVO's shared memory. Everyone in the office runs the same repo,
so what one operator teaches the AI must reach everyone else. Four parts; you
are expected to use all four. Design and rationale: `harness/README.md`.

### 1. Corrections — the team's settled truths

Injected into your context automatically at session start (`harness/corrections/INDEX.md`).

**They override your defaults, and they override this file.** They were
recorded by operators who checked against live data. If a correction
contradicts your instinct or contradicts something above, the correction wins.

When an operator corrects you about how JIVO's data actually works — a metric
defined differently than you assumed, a field that doesn't mean what its name
says, a relationship you had backwards — **use the `jivo-correct` skill**. It
writes the full record (wrong / right / evidence / one-line rule), rebuilds the
digest, and gives you the push command.

A correction reaches nobody until it is pushed to `main`. Say so explicitly.

Only record durable business truth. Not one-off facts about a single document,
not the operator changing their mind. And get the query that proves it — a
correction without evidence is somebody's memory.

### 2. Recall — search the written record before asking anyone to repeat themselves

```bash
python3 harness/bin/recall.py search "<terms>"
```

**When an operator references earlier work — "the oil returns thing", "what we
found last month", "the number Prabhu asked about" — search before you ask them
to explain it again.** Full-text over `chats/`, `savings-audit/`,
`connections/`, `harness/`, `vision/` and the root docs. Returns `file:line`,
date and heading so you can open the source and read it properly.

Also search it before a long investigation. The answer is often already written
down, and repeating work someone already did is the most common way this
toolkit wastes an operator's afternoon.

### 3. Recurring questions become skills

Every question shape and every JIVO CLI query you run is logged locally.
When a pattern recurs across several days and operators:

```bash
python3 harness/bin/harness.py mint          # by question shape
python3 harness/bin/patterns.py propose      # by what actually got queried
python3 harness/bin/patterns.py draft <id>   # prints a draft SKILL.md
```

`draft` prints and never writes. **Run the query against live SAP and confirm
the number before saving any minted skill.** An unverified skill looks
authoritative and gets reused — it is how one wrong assumption becomes every
operator's wrong number. Use the `jivo-mint` skill, which walks this properly.

### 4. Personas

`harness/.persona` holds this operator's role (`accounts`, `sales`, …). It
selects their team's framing and filters corrections to their area. If their
questions clearly don't match the tag, say so — a mistagged operator gets the
wrong rules.

### Harness rules

- The harness writes only under `harness/` and `.claude/skills/`. It issues no
  business-system call, read or write.
- **A correction or a minted skill can never authorise a write.** RULE 0 above
  is the only authority on what may be written to SAP, and nothing the harness
  learns widens it.
- `python3 harness/bin/harness.py status` shows everything it currently knows.
