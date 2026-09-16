# JIVO CLI — read this first

You are running inside **JIVO's data toolkit**. Someone (often the Accounts team) has opened a terminal here and wants answers about the business — SAP balances, turnover, ledgers, orders, stock. Your job: **answer their questions in plain language, with real numbers, pulled live.**

## ✅ RULE 0 — YOU MAY WRITE TO SAP. IT IS PART OF THE JOB.

These tools point at JIVO's **live production** systems. Reads are free. **Writing
to SAP is allowed and expected** — this folder is given to Accounts operators who
create documents for a living. Daman authorised this on 2026-08-22.

- **Do not refuse a write, and do not lecture the operator about it.** When they
  ask for a document to be created, create it. Don't hedge, don't ask them to
  confirm they meant to do their own job, and never tell them "this is read-only".
- **SAP's four write commands, all in `sapb1`:**
  - `sapb1 draft <doctype>` — creates a **draft**. Nothing posts: no stock movement,
    no ledger entry, until a human opens SAP B1 → Document Drafts and presses
    **Add**. Drafts *are* visible to others and to any approval workflow.
  - `sapb1 post <EntitySet>` — creates live, no draft. **Master data only, and
    that is now enforced in code, not asked for:** it accepts a bare, catalogued
    entity set (BusinessPartners, Items, ItemGroups, ProjectCodes …) and
    **refuses every posting document** — invoices, A/P invoices, credit notes,
    orders, GRPOs, payments, journal entries, stock movements. There is no
    override. Document-shaped work goes through `draft`, because on 2026-08-26 a
    `POST PurchaseInvoices` through this CLI returned 201 and put a live,
    unapproved A/P invoice in the books.
  - `sapb1 patch <Entity(key)>` — updates fields on one existing object.
  - `sapb1 delete draft <DocEntry> [<DocEntry>...]` (and `sapb1 delete payment-draft`)
    — removes a **draft**, and nothing else. It reads the draft first and shows the
    operator what they are about to destroy, refuses any draft this CLI did not
    create, needs the typed `yes`, keeps a snapshot of what was there on that machine
    (only its sha256 goes in the shared log — this repo is public), and reads back
    to confirm it is gone. Up to 50 at a time — which is what a bad `acc/` batch
    needs. **A posted document can never be deleted from here.**
- **Show the `--dry-run` first, then send.** Not as a gate on the operator — it is
  what catches a wrong branch, wrong series or wrong posting date *before* it
  reaches the books. One preview they have seen, then go. `delete`'s `--dry-run` is
  the one that does talk to SAP: it *reads* the drafts so the preview shows the real
  documents, then sends no DELETE.
- **`--yes` is yours to add once they have okayed that specific document.** A
  fresh, unrelated document needs a fresh go-ahead.
- **A delete override is the operator's word, never your judgement.**
  `--not-created-here` says "a person keyed this draft in the SAP B1 client and I am
  telling you to remove it anyway" — add it only when the operator has said exactly
  that, about that DocEntry. Same for `--older-than`, `--with-attachment`, `--closed`,
  `--other-operator` and `--in-approval` (that draft is in somebody's Approval Status
  Report — ask them first): each is a fact the operator asserts, and each is recorded
  in the write log under their name. Never reach for one to make a refusal go away,
  and **never loop `delete … --yes` over drafts this CLI did not create.**
  `--not-created-here` takes exactly one DocEntry, needs a person at the prompt, and
  cannot be combined with `--yes` — by design.
- **When in doubt, draft it.** A draft a human ignores costs nothing. A posted
  invoice needs SAP to undo it.
- **Never write unprompted.** This is the one part that is not negotiable, and it
  is not a restriction on the operator: don't invent work, don't "finish" a task
  nobody asked for, don't tidy data as a helpful extra.
- **Every write previews, confirms, and logs.** Without `--yes` the command prints
  the exact request and requires a typed `yes` — **exactly `yes`; `y` is rejected**.
  Every attempt is appended to `queries/<operator>/sap-writes.jsonl`, which syncs to
  `main`, so **every write by every operator lands in one shared history** (override
  with `$SAPB1_WRITE_LOG`; falls back to `~/.sapb1-writes.jsonl` only outside a
  registered checkout). Register yourself once with `python3 harness/bin/setup.py`
  so writes carry your name.
- **A/P invoice from a vendor's bill (the common Accounts write): use the
  `jivo-ap-draft` skill.** Its pre-check finds the GRPO, branch, series and any
  existing draft before anything is sent; its read-back catches what SAP left
  blank (TDS). Built 2026-08-21 from live mistakes — don't hand-roll the payload.

- **🔴 A BILL IS NOT DONE AT THE DRAFT. Finish the job: send it to the approver.**
  **The moment an operator hands you a vendor bill — a PDF, a photo, a scan, one
  or twenty of them, with or without any instruction — the work ends when BHAWANI
  has it, not when a draft exists.** A draft nobody submits is invisible to her
  (`ODRF.WddStatus='-'`; 14,341 such drafts sit unseen in Oil). **Load the
  `jivo-add-and-new` skill and follow it to the end** — build the draft with the
  right skill, attach the bill, then `sapb1 add-draft <DocEntry>` and verify
  `WddStatus='W'`. Do not stop and ask whether to submit; do not hand back a draft
  number and wait. Operators here are not AI users — they will not know a magic
  word, and most will say nothing at all beyond handing you the paper.
  **Never `sapb1 post` a document to "just get it in"** — that bypasses her and
  lands unapproved in the ledger (C-0034); `post` now refuses documents outright.
  Say plainly when it is with her, and
  that her approval does not post it — a human presses Add a second time.

  **`add-draft` only reaches her from a login an approval template names.**
  Guard 5c (2026-09-03) refuses the submit otherwise, because SAP does not: with
  no Always-terms template covering the login and the doctype, it decides the
  document needs no approval and posts it LIVE. Verified live: the only
  Always-terms A/P-invoice templates are Oil **103**, Mart **48**, Bev **68**,
  and each names **USER39 (MUQEEM) and USER08 (DIVJOT)** — Divjot was added
  2026-09-10 on Daman's instruction; before that it was USER39 alone. Those two
  reach Bhawani from any of the three books. **Oil 103 also names USER07 (HARSH)
  since 2026-09-16** (Daman: "do it for Harsh also") and covers A/P credit memos
  too; the same day those three logins came OFF Oil's condition templates 40 and
  41, which had been sending Bhawani a second request for the same draft. Mart
  and Beverages still carry the old overlap until Daman okays the same change. **A box logged in as anyone else
  still stops at the draft** — attach the bill, say it is waiting, and a person
  presses Add in the SAP B1 client (that route does consult the template).
  Getting a login added is an admin's ten minutes in Approval Templates →
  Originators, never a flag here.

  **The one exception — a DRAFTS-ONLY desk, where this whole rule is OFF.**
  `harness/desks.json` → `drafts_only` names the boxes whose operator submits and
  posts the documents herself. On those, entering a bill FINISHES at the draft:
  build it, attach the scan, tell her the draft number, stop. `sapb1 add-draft`
  refuses there before it reads anything (exit 9), the SessionStart hook says so
  in your context, and `jivo-add-and-new` is not even on the box. Do not go
  looking for another route — `post` refuses documents, and a second login or a
  second checkout to get around a desk policy is not a workaround, it is the
  thing the policy exists to stop. **Mahak's GRPO desk (PC-AUDIT-05) is the first
  — Daman 2026-09-03: "only make drafts, only she will post".**

### What is still genuinely impossible — do not promise these

- **Everything except SAP is read-only** — postsql, portals, exim, factory, oms,
  DSR. Not caution: those CLIs have no write command to call.
- **`DELETE` reaches drafts and nothing else.** `sapb1 delete draft` /
  `delete payment-draft` take a DocEntry, not an entity — there is no argument that
  can point them somewhere else, and the client itself refuses any set but `Drafts`
  and `PaymentDrafts`. **Posted documents stay undeletable from here.**
- **No `PUT`, and no OData *actions*** (`Invoices(9)/Cancel`, `Orders(1)/Close`,
  `Drafts(4321)/SaveDraftToDocument`) — refused by design, with no override.
  Cancelling, closing and posting-a-draft are a human's job in the SAP B1
  client. **And you cannot undo a `post` or a `patch` from here — only SAP can**,
  nor bring back a draft you deleted: SAP has no undo for that either.
- **The MCP server (`sapb1 mcp`) exposes no write tool, ever** — an AST guard test
  enforces it. So Claude Desktop can read SAP and nothing more. **Writes happen
  from the `sapb1` CLI in a terminal.**
- **Exit code 7 means "unknown, go look".** The request reached SAP but the answer
  didn't come back — it may have committed. **Do not re-run it.** Query SAP (or
  Document Drafts) to see what exists, and tell the operator. (After a `delete` the
  looking is the same — but a re-sent DELETE cannot create a duplicate, so once you
  have looked you can decide.)
- **Exit code 8 = deleted, but not verified.** SAP answered the DELETE and the
  read-back then failed or still showed the draft. It is probably gone; check
  Document Drafts. Re-running that same delete is safe.
- **Exit code 9 = a guard refused.** Provenance, age, an attachment, a closed draft, a draft in approval,
  or someone else's draft. That is a "go ask the operator to say it out loud"
  signal, not an invitation to add the flag yourself.

## What's here

A folder of command-line tools ("CLIs"), each a window into one JIVO system. SAP can be written to with the four commands above; everything else reads only.

| Folder | System | What you can answer |
|---|---|---|
| `sap-b1/` | **SAP B1** (the books, 3 companies) | ledger balances, turnover/sales, invoices, orders, stock, party statements |
| `ecom-cli/` `exim/` `factory-cli/` `oms-cli/` `jsap-cli/` | ecom / imports / factory / orders / ops | channel sales, POs, production, approvals (Go/Python CLIs) |
| `postsql/` | raw Postgres (16 DBs) | direct SQL reads under the apps |
| `portals/` | Blinkit/Zepto seller portals | studied; read-only CLIs built |
| `sap-history-cli/` | **OLD SAP B1 books, 2014 → Oct-2024** (SQL Server) | anything before the HANA move: old turnover, old ledgers, old parties |
| `ary-cli/` | ARY FusionERP8 retail/distribution (same SQL Server) | ARY bills, stock, counters |

**SAP is the main one for Accounts.** Start there unless asked otherwise.

**Before October 2024, SAP lives somewhere else.** The live HANA system only
carries the books from the Oct-2024 migration onward. Everything earlier —
2014-11-01 to 2024-10-01 — is in three closed SAP company databases on the SQL
Server `138.252.101.118`, read with **`sap-history-cli/saphist`**. If an operator
asks about FY2016, FY2020 or "last five years", `sapb1` will return nothing and
that emptiness is NOT the answer: route it to `saphist`. It takes `--fy`/`--year`
or `--from/--to`, picks the right book itself, and reads both when a range
crosses the August-2019 changeover. `saphist` cannot write (SELECT-only guard +
always-rolled-back transaction). See `sap-history-cli/CLAUDE.md` for its traps —
the sharp one is that **the same CardCode is a different party in each book**.

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
- **A half-search is not an answer (C-0073).** SAP is three books. Before you tell an operator anything is "not found" — a GRPO, an invoice, a draft, a PO, a vendor — you have searched Oil, Mart *and* Beverages. If it is still missing, say exactly what you checked and by which key, then try the next key (vendor, date, amount) yourself. The accountants using this are not AI users: "not found" sounds final to them, they conclude the tool cannot do it, and they stop. Never leave them there.
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

### 3. What gets asked (owner-only, not a skill factory)

Question shapes and the JIVO CLI queries actually run are logged locally, so
the owner can see what this business asks about its own data:

```bash
python3 harness/bin/patterns.py propose      # what recurs, and how widely
```

**Do not auto-create skills from this.** It was tried and dropped: the trigger
ranks by how often a query shape repeats, and at JIVO frequency is inversely
correlated with value — the trivial lookup recurs constantly while the hard
question that actually burned an analyst fires once. Published results agree
(auto-generated agent skills show no average benefit, and large skill libraries
measurably degrade routing). Treat this as a demand signal, nothing more.

### 4. Personas

`harness/.persona` holds this operator's role (`accounts`, `sales`, …). It
selects their team's framing and filters corrections to their area. If their
questions clearly don't match the tag, say so — a mistagged operator gets the
wrong rules.

### 5. Entry skills fire on their own

The SessionStart hook prints a router table (which skill owns which document)
and the UserPromptSubmit hook names the skill when a prompt looks like an SAP
entry. **Obey it: invoke that skill with the Skill tool before any other tool
call**, even when the operator only dropped a PDF and said nothing. Routes live
in `harness/skill-router.json`; a skill hidden by `desks.json` never appears.

### Harness rules

- The harness writes only under `harness/` and `.claude/skills/`. It issues no
  business-system call, read or write.
- **A correction can never authorise a write.** RULE 0 above
  is the only authority on what may be written to SAP, and nothing the harness
  learns widens it.
- `python3 harness/bin/harness.py status` shows everything it currently knows.
