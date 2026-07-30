# The JIVO harness — how this toolkit learns

Modelled on [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent),
studied from source at `~/.hermes/hermes-agent/`. The reverse-engineering that
produced this design is in `research/`.

---

## The problem

Someone in Accounts asks Claude for a ledger balance. Claude reads the sign
backwards and says a vendor owes us money when we owe them. The operator
catches it and corrects it. Claude apologises, gets it right, and the session
ends.

**Tomorrow, in someone else's session, Claude makes the same mistake.**

That is the whole problem. Knowledge produced by one person's session has to
reach every other person's session, automatically, and it must not pile up into
noise that makes answers worse.

## The shape of the answer

Hermes solves this with two stores and one loop:

- **memory** — a small, always-injected text file
- **skills** — procedures on disk, retrieved when relevant
- **a post-turn review** that writes to both without being asked

Three findings from its source shaped everything here:

1. **No database, no embeddings.** A learning is a text file. Both stores are
   injected into the prompt in full. Search infrastructure would be
   over-engineering at this scale.
   *(`research/01-hermes-learning.md` §0)*
2. **Memory is tiny on purpose** — 2,200 characters, hard cap. At capacity a
   write *fails* until the model consolidates. Scarcity is the curation
   mechanism; nothing else prunes memory.
   *(`tools/memory_tool.py:165`)*
3. **The injected snapshot is frozen at session start.** Mid-session writes hit
   disk immediately but do not change the prompt, so the prefix cache survives
   the whole session.
   *(`tools/memory_tool.py:686`)*

## What we built

```
harness/
├── corrections/          the team's settled truths
│   ├── INDEX.md          generated digest — this is what gets injected
│   └── C-0001-*.md       full record: wrong / right / evidence / rule
├── personas/             accounts.md, sales.md — role-specific framing
├── questions/log.jsonl   question shapes, for noticing what recurs
├── bin/harness.py        the whole tool
├── hooks/                session-start · user-prompt-submit · stop
└── research/             how Hermes actually works, with citations
```

Plus, tracked in git so a clone works with zero setup:

- `.claude/settings.json` — wires the three hooks
- `.claude/skills/jivo-correct/` — record a correction
- `.claude/skills/jivo-mint/` — turn a recurring question into a skill

### The loop

```
operator corrects Claude
   └─> jivo-correct skill
        └─> harness/corrections/C-0007-*.md   (full record + evidence)
             └─> INDEX.md rebuilt              (one line per rule)
                  └─> git push
                       └─> everyone else's SessionStart hook injects it
                            └─> nobody makes that mistake again
```

And, in parallel:

```
every question → shape-normalised → questions/log.jsonl
   └─> a shape recurs 5+ times
        └─> harness.py mint flags it
             └─> jivo-mint writes + verifies a skill
                  └─> git push → everyone has it
```

---

## Using it

```bash
python3 harness/bin/harness.py status      # what the harness knows
python3 harness/bin/harness.py mint        # which questions deserve a skill
python3 harness/bin/harness.py build       # rebuild the digest
```

Recording a correction is normally done by asking Claude ("that's wrong, X is
actually Y" → it uses `jivo-correct`), but the direct form is:

```bash
python3 harness/bin/harness.py record \
  --title "Ledger balance sign convention" \
  --wrong "Said a negative balance meant the customer owes JIVO." \
  --right "Negative = CREDIT, JIVO owes them." \
  --rule  "BusinessPartners.CurrentAccountBalance: positive = DEBIT (party owes JIVO), negative = CREDIT (JIVO owes party)." \
  --evidence "sapb1 query BusinessPartners --filter \"CardCode eq 'V0001'\" --select \"CurrentAccountBalance\"" \
  --area accounts --severity high
```

**A correction only reaches other people once it is pushed to `main`.** That is
the most common way this silently fails.

### Set your role

```bash
echo accounts > harness/.persona     # or sales, factory, ecom, ops, hr
```

Gitignored — each person sets their own. It does two things: loads your team's
framing (`personas/<role>.md`), and filters corrections so you only carry rules
for your area plus universal ones. An Accounts operator does not pay tokens for
Sales traps.

---

## Design decisions, and why

**Corrections are files, not a database.** Hermes has no DB for this and it is
right: the volume is small, git gives us history, review and distribution for
free, and a correction is worth reading as prose.

**The digest is bounded (6,000 chars) and the tool warns when it overflows.**
Copied straight from Hermes' char cap. When the digest is full, the answer is
to consolidate overlapping rules — not to raise the ceiling. A digest nobody
can read is a digest the model skims.

**Only the `## Rule` line is injected.** The full record — what was wrong, what
is right, the query that proves it — stays on disk and is read on demand. This
is Hermes' progressive disclosure: an index in the prompt, detail behind it.

**Corrections do not expire.** Hermes ages *skills* out (30 days idle → stale,
90 → archived) because a procedure can fall out of use. It never expires
memory. A ledger sign convention does not go stale, so ours don't decay —
they are replaced explicitly via `--supersedes`, which retires the old one so
the two can never contradict each other in the digest.

**The post-turn review doesn't fork a model.** Hermes spawns a background agent
every N turns to ask "did anything here deserve recording?"
(`research/01-hermes-learning.md` §2a). We keep the trigger and drop the fork:
a dozen office operators sharing one subscription cannot each pay for an extra
inference call every 10 turns for a check that is usually a no-op. The Stop
hook raises a flag; the next session surfaces it to the agent already in the
room. Same trigger, no extra spend.

**The anti-thrash rule is Hermes'.** A session that is already recording
corrections never gets nagged on top of it — recording one resets the counter
(`agent/tool_executor.py:476-479`).

---

## What is logged, and what isn't

`harness/questions/log.jsonl` stores the text of questions asked, with a
normalised shape and the operator's role. It exists to notice *"this shape came
up 12 times, it deserves a skill"* — nothing else reads it.

It does **not** capture answers, SAP data, credentials, or anything returned by
a query. Slash-commands and anything over 2,000 characters are skipped.

To turn it off for a machine: `export JIVO_HARNESS_NO_LOG=1`.

The log is tracked in git with `merge=union` (see `.gitattributes`) so parallel
appends from several operators merge without conflicts.

## Guarantees

The harness writes **only** to files under `harness/` and `.claude/skills/`.
It never touches SAP, Postgres, HANA, or any portal — it issues no business-system
call of any kind, read or write.

RULE 0 in `CLAUDE.md` is the authority on what the *toolkit* may write (SAP has
three explicit write commands — `draft`, `post`, `patch` — everything else is
read-only). Nothing in the harness widens that, and no correction or minted
skill may authorise a write the operator did not ask for. The only thing that
learns here is the harness itself.

## Tuning

| Variable | Default | Effect |
|---|---|---|
| `JIVO_PERSONA` | `all` | Role; overrides `harness/.persona` |
| `JIVO_DIGEST_BUDGET` | `6000` | Hard char cap on the injected digest |
| `JIVO_MINT_THRESHOLD` | `5` | Repeats before a shape is flagged |
| `JIVO_REVIEW_INTERVAL` | `10` | Turns between learning checks |
| `JIVO_HARNESS_NO_LOG` | unset | `1` disables question logging |
