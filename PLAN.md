# The entry-vault build — multi-phase plan

**Started 2026-08-24 20:10 IST.** Goal: stop learning SAP one bill at a time.

Today we made 9 A/P drafts and most were right, but the misses were all the same
shape — a field nobody knew was required (`OriginalRefNo`), a dimension inherited
instead of read off the paper (`CostingCode3`), a series looked up by hand. Each cost
a round trip. Each was knowable in advance.

This builds the thing that makes them knowable in advance: a vault of what JIVO's
books actually contain, mined from the books rather than from SAP's manual.

## The one design constraint that shapes everything

A 17-agent Claude fan-out **exhausted the session quota in 6 minutes** (916k tokens,
all 17 agents lost, resets 01:10). So the plan is built around a split that turns out
to be the right architecture anyway:

- **Measuring the books costs no model tokens.** It is SQL. It is also the part that
  takes hours.
- **Writing the notes costs model tokens.** But an agent writing from a pre-mined
  profile does no exploration — it reads a file and writes prose, which is a fraction
  of the cost of an agent that has to go find the data itself.

So: mine everything first with no model in the loop, then spend the scarce resource
only on turning measurements into knowledge. Agents run in small paced waves, not
bursts, and every wave is restartable — a note already written is skipped, so a
quota wall costs the current wave and nothing before it.

## Phases

| # | Phase | Cost | Status |
|---|---|---|---|
| 0 | **Recon + tooling** — census of every entry type; five read-only miners; self-healing SAP bridge | free | ✅ done |
| 1 | **Mine everything** — 234 profiling jobs across 3 books: field fill rates, GL fingerprints, document flows, real samples | **zero model tokens** | ✅ 219/234, 2.6 MB |
| 2 | **Foundations** — 17 notes: the machinery every entry depends on | agents, paced | ▶ |
| 3 | **Documents (core)** — 12 notes: the high-volume entries Accounts actually keys | agents, paced | queued |
| 4 | **Documents (tail)** — 16 notes: everything else with rows | agents, paced | queued |
| 5 | **Flows** — 8 notes: purchase-to-pay, order-to-cash, month-end, imports, intercompany, factory, returns, statutory | agents | queued |
| 6 | **Playbooks** — the keying checklists, built from phases 2–4 | agents | queued |
| 7 | **Synthesis** — the Atlas, the master pre-flight checklist, gaps, correction candidates | me | queued |
| 8 | **Wire it in** — reachable from `recall.py` and from the entry skills | me | queued |

## Phase 1 — what was actually mined (the raw material)

221 files, 2.6 MB, in `_data/`:

| Kind | Files | What each one holds |
|---|---:|---|
| `profile-<TABLE>.md` | 73 | Every column of a live table: fill rate over all history *and* the last 120 days, in all three books side by side, plus distinct counts and the full value list for every low-cardinality field |
| `gl-<TransType>-<CO>.md` | 50 | The journal that document type posts — accounts, sides, amounts, line-count shape, dimensions carried, line memos |
| `flow-<TABLE>-<CO>.md` | 78 | Copied-from vs keyed-from-scratch, per line and per document; drafted-first ratio; approval volume |
| `sample-<TABLE>-OIL.md` | 20 | Real finished documents — header, every line table, and the journal they made |

Why the fill rate is the load-bearing number: SAP stores `''` and `0` in fields
nobody ever types in, so a plain NULL test reports every field as fully used. The
profiler counts a field as filled only when it is non-null **and** non-blank
**and** non-zero. That is what separates "SAP offers this field" from "JIVO uses
this field", which is the entire question.

## Ground rules the agents run under

- **Read-only against SAP.** No `draft`, no `post`, no `patch`, not even a dry run.
- **Every number carries its query.** A figure without one is somebody's memory.
- **Measured / inferred / unverified** — labelled, always. A thorough explanation is
  not evidence.
- **The corrections in `harness/corrections/` outrank the miners.** A note that
  contradicts one is a finding to report, not a fact to overwrite.
- **The repo is public.** Field names, fill rates, GL codes and names, series
  numbers, vendor group names: fine. Credentials, GSTINs (including the `VATRegNum`
  values sitting in the profiles), bank accounts, individual pay: never.
- **Claude only.** No codex.

## Where it lives

`sap-b1/entry-vault/`, inside the repo's existing Obsidian vault, so `[[links]]`
resolve and the graph works. Its sibling `sap-b1/vault/` maps SAP's *API surface* —
that one answers "what can the Service Layer do", this one answers "what does JIVO
actually do".

## Status

Live progress: `00-index/Build-Log.md`.
