---
name: cli-hub
description: Use BEFORE answering any question about JIVO data when you are not certain which CLI to reach for, before writing a raw SQL query or a curl by hand, and whenever you are about to say "there is no tool for that". Finds the CLI that answers a question, tells you how to run it, and warns you about its traps. Also use when an operator asks "what can this toolkit do", "is there a command for X", or when a CLI seems missing or broken.
---

# cli-hub — find the tool before you improvise

This checkout holds **14 CLIs**. No one — operator or agent — remembers all of
them. The most common way this toolkit wastes an afternoon is an agent
hand-rolling a query against a system that already has a command for it, or
telling an operator "we can't see that" when we can.

Borrowed from CLI-Anything's CLI-Hub. The idea worth stealing: **an agent that
does not know a tool exists should be able to find it mid-task.**

## The rule

Before you write a raw SQL query, a `curl`, or a bespoke script against any JIVO
system — and before you tell anyone a thing is not reachable — run:

```bash
python3 hub/bin/hub.py search "<the question in the operator's own words>"
```

It takes plain English. `"vendor outstanding balance"`, `"realise per litre"`,
`"who approved this budget"`, `"import shipment landed cost"`.

## Commands

```bash
python3 hub/bin/hub.py list                      # all 14, with read/WRITE marked
python3 hub/bin/hub.py search "aging by party"   # which CLI answers this
python3 hub/bin/hub.py info sapb1                # how to run it + its traps + its docs
python3 hub/bin/hub.py doctor                    # what is built in this checkout
python3 hub/bin/hub.py doctor --probe            # ...and what actually responds live
python3 hub/bin/hub.py run sapb1 -- doctor       # run it without knowing its path
```

`hub.py run` resolves the binary for you, picks the `.exe` on Windows, and runs
from the repo root — so a command works the same on the Mac and on an operator's
box regardless of where they opened the terminal.

## What the output tells you

`search` and `info` print four things that decide how you proceed:

- **run** — the exact path. Use it; do not go looking.
- **read / WRITE** — `sapb1` and `acc` are the only two that can write, and
  RULE 0 in `CLAUDE.md` governs both. Everything else is read-only *by absence* —
  no write path was ever built.
- **TRAP** — the correction that most often makes an answer from this CLI wrong
  (C-0008 Mart-only, C-0011 no Mart orders in OMS, the sales-lens/accounts-lens
  split). Read it before you quote a number, not after.
- **docs** — where the real domain guide lives when the question goes deeper.

## When nothing matches

Two honest outcomes, and neither is "I can't see that":

1. **The system exists but has no CLI yet.** Say so plainly — "that CLI has no
   command for it, I'd have to build one" — and offer to build it. `/printing-press`
   for an API; `press-desktop` for desktop software.
2. **`doctor` says MISSING.** It is not built in this checkout, not broken. The
   build command is in the output; run it.

A CLI that fails `doctor --probe` is a connectivity or credential fact, not a
missing feature — report which.

## Keeping it true

`hub/registry.json` is the index. When a CLI gains a command group, changes its
binary name, or a new CLI is built, add or update its entry — an out-of-date
registry sends the next agent to the wrong tool. The registry says what *should*
exist; `doctor` is the only part that knows what *does*.

Never put a host, IP, port or credential in the registry. **This repo is public.**
