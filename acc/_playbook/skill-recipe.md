# The recipe — how a JIVO accounts data-entry skill is built

Distilled from `jivo-ap-draft` (2026-08-21), the first one that survived two
fresh-agent test runs. Every skill built in this folder follows this shape.
Don't invent a new shape per document type; the shape is the reusable part.

## Why the shape exists

Three things go wrong when an agent does accounts data entry, and each part of
the shape exists to stop one of them:

| Failure | What stops it |
|---|---|
| **Duplicate** — Accounts already keyed it in the SAP client this morning | a **pre-check** that searches SAP by every identifier on the paper *before* building anything |
| **Invented facts** — agent guesses a branch, a series, a GL, an item code | the pre-check **refuses to build** (exit 3) rather than fill a blank; it only ever copies values it found in SAP |
| **Silent gaps** — SAP accepts the write but drops a field (TDS came out 0) | a **read-back** that compares what SAP stored against the paper and reports the diff as gaps, not as success |

## The five steps (same every time)

1. **Paper → facts.** Name every field on the source document and where it maps.
   Include the handwritten marks — at JIVO they carry the gate entry, the GRPO
   number, and often the draft number someone already made.
2. **Pre-check** (`bin/precheck.py`, read-only). Searches for an existing
   record, resolves every code from live SAP, writes the proposed payload to
   `--out`. Exit codes are the contract:
   - `0` ready, payload written
   - `2` **already exists in SAP — stop**, show the operator what's there
   - `3` cannot build (ambiguous / not found) — fix the inputs, never hand-edit
   - `4` SAP unreachable — a connection problem, not a data answer
3. **Dry-run** the write, show the operator the exact payload, wait for their go.
4. **Send** the same command with `--yes`. Record what SAP returned.
5. **Read back** (`bin/readback.py`) and compare against the paper. Report the
   diffs. Hand over the document number and the SAP-client click-path.

## Files a skill ships

```
.claude/skills/jivo-<name>/
├── SKILL.md                      # ~100 lines. Procedure, field-rule table, hard stops.
├── bin/precheck.py               # read-only. Resolves codes, finds duplicates, emits payload.
├── bin/readback.py               # reads the created doc, diffs vs expected, flags gaps.
└── reference/<topic>.md          # series tables, error codes, click-paths — the lookup stuff
```

`SKILL.md` frontmatter `description:` must contain the **operator's own words**
("enter this bill", "data entry for this invoice", "make a draft of this"), not
a tidy summary — that string is the only thing that decides whether the skill
fires.

## Writing rules

- **Everything in the skill was seen on live data.** No field rule goes in
  because it sounds right. If it isn't proven, it isn't in the file.
- **Encode the rule in the script, then also state it in SKILL.md.** The script
  is the enforcement; the table is so a human can audit it.
- **Every trap gets a row.** The `-10 / -4002 define the numbering series`
  class of error costs an hour the first time and zero minutes forever after.
- **Prefer `draft` over `post`.** A draft is undone by a human ignoring it.
- **Test with a fresh agent** given a realistic operator prompt and no context.
  Whatever it gets wrong is a missing rule, not a bad agent.

## Related

- Harness corrections `C-0017`, `C-0018`, `C-0022` came out of this work.
  A durable business truth belongs in `harness/` (via `/jivo-correct`), a
  how-to-key-it-in belongs in the skill.
