# Start here

This folder lets you ask questions about JIVO in plain English and get real
numbers back — whichever part of the business you work in.

Sales, Accounts, Factory, E-commerce, Imports, Operations, HR, IT — it reads the
live system behind your work and answers. You type a question the way you would
say it out loud.

**Asking a question never changes anything.** Nothing you ask can alter a record.

You do not need to know any code. There is **one** thing to do before you start.

---

## Step 1 — Tell it who you are

Open the terminal in this folder, type this, and press Enter:

```
python3 harness/bin/setup.py
```

> On Windows, if that says *"Python was not found"*, use `python` instead of
> `python3`. That is the only difference.

It asks you two things:

```
  Your full name: Param Singh
  Your department (accounts/sales/factory/ecom/exim/ops/hr/it): sales
```

That is the whole setup. Ten seconds, and you never do it again.

**Why it asks.**

- **Your name** goes on any report you produce, so whoever reads it later knows
  who to ask about it. It is stored on your machine at `harness/.operator`.
- **Your department** decides what it knows about *your* work. Someone in Sales
  gets Sales' vocabulary and Sales' warnings; someone in Factory gets Factory's.
  You should not be carrying another team's rules around.

Pick the one closest to your actual work. If none of them fit, say so — a
department can be added.

---

## Step 2 — Check your system is connected

Run the check for **your** area. Every tool is built for both machines — pick
your column.

| Your department | On a Mac | On Windows |
|---|---|---|
| **Accounts** | `./sap-b1/cli/sapb1 doctor` | `sap-b1\accounts-kit\sapb1.exe doctor` |
| **Sales** | `./oms-cli/oms-pp-cli doctor` | `oms-cli\oms-pp-cli.exe doctor` |
| **Factory** | `./factory-cli/jivo-factory-pp-cli doctor` | `factory-cli\jivo-factory-pp-cli.exe doctor` |
| **E-commerce** | `./ecom-cli/jivo-ecom-pp-cli doctor` | `ecom-cli\jivo-ecom-pp-cli.exe doctor` |
| **Imports / EXIM** | `./exim/exim doctor` | `bash exim/exim doctor` |
| **Operations** | `./jsap-cli/jsap-cli meta whoami` | `python jsap-cli\jsap-cli meta whoami` |
| **IT** | `./postsql/postsql doctor` | `postsql\postsql.exe doctor` |

Two of those rows are not plain programs, which is why they look different:

- **Imports** goes through `exim/exim`, a small script that fetches your login
  token and blocks the handful of requests that would change data. Always run it
  through the script — calling the program directly skips that guard.
- **Operations** (`jsap-cli`) is a Python script, so it runs the same on both
  machines; Windows just needs `python` in front of it.

Green means you are ready.

**Red, or "missing config"? Your credentials are not in place yet — message
Daman.** Credentials are handed over separately, on purpose. They are never in
this folder.

---

## Step 3 — Ask something

Say it normally. No commands, no syntax.

**Accounts** — *"What is the Oil turnover for July?"* · *"How much does Blessing
Advertising owe us?"* · *"Which vendors have advances with no bill against them?"*

**Sales** — *"Which parties bought the most 5L mustard last month?"* · *"What
orders are still open for the North region?"* · *"Show me this month against last
month by party."*

**Factory** — *"How many bottles did we fill yesterday?"* · *"Which batches
failed QC this week?"* · *"What went out on dispatch today?"*

**E-commerce** — *"What did Blinkit sell of 1L mustard last week?"* · *"Which of
our listings are out of stock right now?"* · *"Show me Zepto POs pending
appointment."*

**Imports** — *"What contracts are in transit?"* · *"How much RM is in tank 3?"* ·
*"What was the landed cost on the last olive oil shipment?"*

**Operations** — *"What approvals are stuck and with whom?"* · *"Which bills have
been pending more than a week?"*

**HR** — *"How many people were absent yesterday?"* · *"What is the leave balance
for the dispatch team?"* · *"Has this month's salary run gone through?"*

**IT** — *"Is the factory feed into SAP still running?"* · *"Why does OMS show a
different number than SAP for this order?"*

More examples: [`sap-b1/accounts-kit/ASK-EXAMPLES.md`](sap-b1/accounts-kit/ASK-EXAMPLES.md)

### The most useful thing you can do

**If an answer looks wrong, say so.** *"No, that's not how we count returns."*

It will record the correction properly, and by tomorrow **nobody else's copy
makes that mistake either.** You are the person who knows your own numbers — this
is how the whole team's answers get better.

---

## What happens on its own

So nothing surprises you later, here is everything that runs without you asking:

| What | Why |
|---|---|
| **Your sessions are written down** — one note a day in `chats/<your-name>/` | So the work is not lost, and the next person asking the same thing gets a faster answer |
| **Queries you run are saved** in `queries/<your-name>/` | A query that worked once should not be rebuilt from scratch |
| **Once a day it syncs** — pulls everyone's latest, sends yours up | This is how a correction you made this morning reaches the whole team |
| **Reports get a small mark** in the top-right corner | Any Excel or HTML report you make says `powered by daman`, your first name, and the date. It is deliberate and cannot be removed |

None of this needs anything from you, and none of it is hidden. If you want to
see exactly what was written about your session, open your own folder under
`chats/` and read it — it is plain text.

---

## Please don't

- **Don't edit `CLAUDE.md`, `.claude/`, or anything in `harness/bin/`.** Those are
  the shared rules for everybody. If they change on your machine the daily sync
  puts them back and reports it. If you think a rule is wrong, tell Daman — that
  is worth fixing for everyone, not just you.
- **Don't remove the mark from a report.** It needs a password, and asking Claude
  to strip it will not work.
- **Don't share your credentials** or copy them anywhere else.

---

## About changing things in SAP

Almost everything you do here is **reading**. Asking a question never changes a
record, in any system.

SAP is the one system that can also be written to, and only if you ask for it by
name. Everything else — Postgres, the portals, exim, factory, orders,
DSR — is read-only and cannot write at all, even if you ask.

**If you do want something created in SAP, ask for a draft.**

> *"Draft a purchase order for 500 cases to SHARMA TRADERS."*

A **draft** goes into SAP's Document Drafts for a human to open, check, and press
**Add**. Nothing moves — no stock, no ledger entry — until someone does that. If
it was wrong, ignoring it is enough.

**What always happens before anything is written:**

1. It shows you the exact request first and sends nothing.
2. You type the word **`yes`** in full. `y` is not accepted.
3. It is recorded in `queries/<your-name>/sap-writes.jsonl`, which syncs to the
   team.

So nothing can be written by accident, and nothing can be written quietly.

**Two things it cannot do at all, by design:** it cannot delete anything, and it
cannot cancel, close, or post a document. Those are a human's job in the SAP B1
client.

**If you ever see "the outcome is unknown" (exit code 7)** — stop. Don't run it
again. The request reached SAP but the answer didn't come back, so it may have
gone through. Tell Daman, and check SAP before doing anything else.

---

## If something looks broken

**"Python was not found"** → use `python` instead of `python3`.

**`doctor` is red** → credentials aren't set. Message Daman.

**A message about protected files having changed** → something edited the shared
rules. Don't try to fix it. Send Daman a screenshot.

**An answer you don't believe** → say so in the chat. Push back. It is supposed
to check itself against live data, and telling it that it is wrong is how it gets
better for everybody.

**Anything else** → Daman.

---

## For whoever set this machine up

In order:

1. `git clone` the repo onto the machine.
2. Install Git, Python 3, and Claude Code if missing.
3. Put the credential files in place (`.env` files — never committed, handed over
   out of band). Only the ones that person's department needs.
4. Have the operator run `python3 harness/bin/setup.py` **themselves**, so the
   name on their reports is genuinely theirs.
5. Run their department's `doctor` from the table above → green.
6. Set the override password once, on your own machine only:
   `python3 harness/bin/guard.py set-password`
7. `python3 harness/bin/guard.py check` → should print OK.

Technical detail: [`README.md`](README.md) and [`NEW-DEVICE.md`](NEW-DEVICE.md).
The learning layer — corrections, personas, the daily sync — is in
[`harness/README.md`](harness/README.md).
