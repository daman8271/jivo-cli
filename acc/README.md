# acc — the Accounts data-entry skill workbench

**Started 2026-08-22.** Purpose: do real Accounts work with the operator,
capture the exact steps while doing it, and turn each one into a skill any
JIVO operator's Claude can run.

Yesterday produced one: `ap-rm-pm` (A/P invoice from a vendor bill).
This folder is where the rest get built.

## How a session works

1. Operator brings a real document / task.
2. We do it live, slowly, writing down every decision — especially the ones
   that aren't on the paper (which branch, which series, which GL, what
   Accounts already did with it).
3. Steps land in `_playbook/session-log.md` as we go.
4. When a document type is done end-to-end **twice** without surprises, it
   gets built into `.claude/skills/jivo-<name>/` using `_playbook/skill-recipe.md`.
5. A fresh agent is given a realistic operator prompt to test it. What it gets
   wrong is a missing rule.

## Get a shell ready

```bash
source acc/_playbook/connect.sh navdeep-user36.env
(cd sap-b1/cli && ./sapb1 doctor)
```

## Layout

| Path | What |
|---|---|
| `_playbook/skill-recipe.md` | the proven shape every entry skill follows |
| `_playbook/session-log.md` | live capture of steps, per document type |
| `_playbook/connect.sh` | bridge + operator login + write log, one command |
| `_samples/` | the actual paperwork and payloads worked on (gitignored if sensitive) |

## Candidate skills — status

| # | Document / task | Skill | Status |
|---|---|---|---|
| 1 | A/P invoice from a vendor bill | `ap-rm-pm` | ✅ shipped 08-21 |
| 2 | A/P invoice drafts in bulk from open GRPOs (Excel review round trip) | `acc batch` — see [BATCH.md](BATCH.md) | 🚧 built 08-24; scan + send live-verified read-only, first supervised send pending Daman's go |
| 3 | _(to be chosen with the operator)_ | — | — |

Fill this table as the day goes. A row only turns ✅ after a fresh-agent test.

## Ground rules for this workbench

- Writes go in as **drafts** wherever the document type supports one — a human
  presses Add. Master data (`post`) and field fixes (`patch`) go live, so those
  get the dry-run shown before every single send.
- Every send is preceded by a `--dry-run` the operator has actually seen.
- Every write is logged to `queries/<operator>/sap-writes.jsonl` (shared history).
- `--yes` is the operator's decision, never the agent's initiative.
