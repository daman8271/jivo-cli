# The entry-vault build — multi-phase plan

**Started 2026-08-24 20:10 IST.** Goal: stop learning SAP one bill at a time.

Today we made 9 A/P drafts and most were right, but the misses were all the same
shape — a field nobody knew was required (`OriginalRefNo`), a dimension inherited
instead of read off the paper (`CostingCode3`), a series that had to be looked up
by hand. Each cost a round trip. Each was knowable in advance.

So this builds the thing that makes them knowable in advance: a vault of what
JIVO's books actually contain, mined from the books, not from SAP's manual.

## The idea

Three layers, and the third is the one that saves time:

1. **Foundations** — the shared machinery every entry depends on. Series, branches,
   GL accounts, tax codes, TDS, dimensions, warehouses, UDFs, approvals, periods.
   These are what you have to know *before* you open any screen.
2. **Documents** — one note per document type JIVO actually makes, field by field,
   with measured fill rates, the journal it posts, real examples, and the traps.
3. **Playbooks** — for each entry an operator keys often: the pre-flight list, the
   payload, the read-back check. Built *from* layers 1 and 2, so nothing is
   remembered twice.

## What makes it different from documentation

Every number is measured against the live books, and the note carries the SQL that
produced it. "SAP has a field called `CostingCode3`" is documentation. "At JIVO that
field is filled on 61% of factory service lines and only ever holds one of four
budget codes, and a handwritten *Common* means `FACT_COM`" is what you need at
20:00 with a bill in your hand.

Measured and inferred are marked separately, on purpose. A confident wrong number
is worse than a gap.

## Phases

| # | Phase | Agents | What comes out |
|---|---|---:|---|
| 0 | **Recon + tooling** ✅ | — | The census of every entry type JIVO makes; four read-only miners; a self-healing SAP bridge |
| 1 | **Foundations** ▶ | 17 + 17 verify | `01-foundations/` — 17 notes |
| 2 | **Documents (core)** | 12 + 12 verify | `02-documents/` — the high-volume types |
| 3 | **Documents (tail)** | 16 + 16 verify | `02-documents/` — everything else with rows |
| 4 | **Flows** | 8 | `03-flows/` — purchase-to-pay, order-to-cash, month-end, imports, intercompany, factory, returns, statutory |
| 5 | **Playbooks** | 10 | `04-playbooks/` — the keying checklists |
| 6 | **Completeness + synthesis** | 6 | The Atlas, the master field checklist, gaps, correction candidates |
| 7 | **Wire it in** | — | Reachable from `recall.py` and from the entry skills |

Every mining agent is paired with an adversarial verifier that re-runs its numbers.
A well-structured explanation is not evidence, and one agent's plausible inference
is exactly what a second agent should be trying to break.

## Phase 0 — what already exists

Tools, all read-only, all through the guarded `hana-sql` binary:

| Tool | Answers |
|---|---|
| `bin/profile.py` | What operators actually fill in — per-field fill rate over all history and a recent window, distinct counts, and the value vocabulary for every low-cardinality column |
| `bin/gl.py` | The journal a document type posts — accounts, sides, amounts, line-count shape, dimensions carried, line memos |
| `bin/sample.py` | Real finished documents: header, every line table, and the journal they made |
| `bin/bridge.sh` | Idempotent, concurrency-safe repair of the SSH bridge to the SAP box |
| `bin/watchdog.sh` | Keeps it up for the length of the run |

The bridge matters more than it looks. The SAP box only accepts the office IP, so
everything here rides one tunnel — and it dropped twice in the first half hour.
Miners now repair and retry rather than reporting "no data", which is the failure
mode that would quietly poison a whole night's work.

## Ground rules the agents run under

- **Read-only against SAP.** No `draft`, no `post`, no `patch`, not even a dry run.
- **Every number has its query in the note.** A figure without one is somebody's memory.
- **Measured, inferred, unverified** — labelled, always.
- **The corrections in `harness/corrections/` outrank the miners.** A note that
  contradicts one is a finding to report, not a fact to overwrite.
- **The repo is public.** Field names, fill rates, GL codes and names, series
  numbers, vendor group names: fine. Credentials, GSTINs, bank accounts,
  individual pay: never.

## Where it lives

`sap-b1/entry-vault/`, inside the repo's existing Obsidian vault, so `[[links]]`
resolve and the graph view works. It sits alongside `sap-b1/vault/`, which maps
SAP's *API surface* — that one answers "what can the Service Layer do", this one
answers "what does JIVO do".

## Status

Live progress: `00-index/Build-Log.md`.
