---
name: jivo-mint
description: Use when a JIVO question shape has recurred often enough to deserve its own skill, when the user says "mint a skill for shape <id>", "/mint", "make a skill for this", "we keep asking this", or when `harness/bin/harness.py mint` reports candidates. Turns a repeated question into a verified, reusable skill.
---

# Minting a skill from a recurring question

The harness logs the *shape* of every question operators ask. When one shape
recurs (default: 5+ times), it has earned a skill: the next person gets the
right answer instantly, computed the right way, instead of the AI re-deriving
the approach and possibly re-deriving it wrong.

## Steps

### 1. Find the candidates

```bash
python3 harness/bin/harness.py mint
```

This prints shapes above threshold with their real example questions and which
persona asks them. Pick the shape you were asked to mint.

### 2. Read the real examples — do not invent the use case

The examples are what people actually typed. Build the skill for *that*, not
for an idealised version of it. Note especially:

- which parts vary (party name, date, company) → these become parameters
- which persona asks it → that becomes the skill's audience
- whether they wanted value or quantity, GST-inclusive or net

### 3. Work out the correct query, and VERIFY IT

This is the step that makes the skill worth having. Actually run the query
against live SAP and confirm the number is right:

```bash
sapb1 query <Entity> --filter "..." --select "..." --top 5 --json
```

Check it against the definitions in `CLAUDE.md` and against every active
correction in `harness/corrections/INDEX.md` — a skill that contradicts a
recorded correction is a bug that will now be repeated at scale.

**Do not mint a skill whose query you have not run.** An unverified skill is
worse than no skill: it looks authoritative and gets reused.

### 4. Write the skill

Create `.claude/skills/jivo-<name>/SKILL.md`:

```markdown
---
name: jivo-<name>
description: Use when <the real trigger, in the words operators actually use>.
shape_id: <the shape id from step 1>
persona: accounts
minted: <YYYY-MM-DD>
minted_from: <N> recurring questions
---

# <What this answers>

## The question
<the shape, e.g. "ledger balance for <party> as on <date>">

## How to answer it
<the exact, verified commands — with the parameters marked>

## Definitions that apply
<pull the relevant lines from CLAUDE.md and INDEX.md>

## Traps
<what goes wrong if done naively — cite correction ids where they apply>

## How to present it
<format, units, what to offer next>
```

The `shape_id` field matters: it is how `harness.py mint` knows this shape is
already handled and stops proposing it.

### 5. Verify it end to end, then push

Run the skill's own commands once more, exactly as written, and confirm they
produce a sensible number. Then:

```bash
git add .claude/skills/jivo-<name> && \
git commit -m "skill: jivo-<name> (minted from <N> recurring questions)" && \
git push
```

## Judgement

Do not mint mechanically because a counter crossed a threshold. Skip it when:

- the shape is trivial (one obvious command, no traps) — a skill adds noise
- the recurrence is one person on one afternoon, not a standing need
- `CLAUDE.md` already answers it well

Minting the wrong things dilutes the skill index, which makes every skill
harder to find. Fewer, sharper skills beat more.
