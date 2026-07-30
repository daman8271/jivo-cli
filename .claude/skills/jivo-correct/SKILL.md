---
name: jivo-correct
description: Use when the user corrects the AI about how JIVO's business data works — a wrong metric definition, a wrong field, a wrong assumption about SAP, a misread number, or "no, that's not how we do it here". Also use when the user says "remember this", "correct this", "/correct", or "make sure this never happens again". Records the correction so every other JIVO operator's Claude picks it up.
---

# Recording a JIVO correction

Someone just corrected you about how JIVO's business actually works. That
correction is worth more than the answer — it must outlive this session and
reach every other operator.

## When to use this

Use it when the correction is **durable business truth**:

- a metric is defined differently than you assumed ("turnover is net of GST")
- a field means something other than its name ("qty is per bottle, not carton")
- a relationship you got wrong ("Oil→Mart is intercompany, not a sale")
- a trap that will catch the next person ("don't match partners by name")

Do **not** use it for:

- one-off facts about a single document or party (that's just an answer)
- the user changing their mind about what they wanted
- anything you have not actually verified — see step 2

## Steps

### 1. Confirm you understand the correction

State back, in one sentence, what you had wrong and what is actually true. If
you are not certain you have understood, ask. A wrong correction recorded here
propagates to everyone, which is worse than no correction.

### 2. Get the evidence

Ask for, or run, the query that proves it. A correction without evidence is
someone's memory; a correction with evidence is a fact. If the user cannot
supply evidence and you cannot verify it, still record it — but write
`unverified — asserted by <name>` in the Evidence field, and say so plainly.

### 3. Write the one-line rule

This is the part that gets injected into every future session, so it carries
the whole weight. It must be:

- **imperative and self-contained** — readable with zero context
- **specific** — name the entity and field, not "be careful with balances"
- **under ~200 characters**

Good: `BusinessPartners.CurrentAccountBalance: positive = DEBIT (party owes
JIVO), negative = CREDIT (JIVO owes party).`

Bad: `Be careful when interpreting balances.`

### 4. Record it

```bash
python3 harness/bin/harness.py record \
  --title "<short title>" \
  --wrong "<what the AI said that was wrong>" \
  --right "<what is actually true>" \
  --rule "<the one imperative line>" \
  --evidence "<the query or source that proves it>" \
  --area accounts \
  --severity high \
  --tag <tag> \
  --author "<who corrected it>"
```

- `--area`: `accounts` `sales` `factory` `ecom` `ops` `hr` or `all`. Use the
  narrowest one that fits — operators only load their own area plus `all`,
  so a wrongly-broad tag costs everyone tokens.
- `--severity`: `high` if getting this wrong produces a **wrong number someone
  might act on**. Otherwise `medium`/`low`.
- `--supersedes C-00NN`: if this replaces an earlier correction, pass its id.
  The old one is retired automatically rather than contradicting the new one.

The digest rebuilds itself, and the correction is **sent automatically** — the
command commits just `harness/corrections/` and pushes it. Operators here do not
use git and must never be asked to.

### 5. Confirm it actually went out

Read the output. There are three outcomes and they are not the same:

- `jivo-sync: sent 1 correction(s)` — done, everyone gets it next session.
- `...could not send to the server` / `...timed out` — **saved but NOT shared.**
  Say so plainly. It will go out with the next correction or session.
- `...have NOT reached the team, and N update(s) are waiting to come down` —
  this machine has diverged and needs Daman once. The work is safe but private.

Never tell the operator it reached the team unless you saw the `sent` line. A
recorded-but-unshared correction is the most common way this silently fails.

To record without sharing (rehearsal, or a correction you are unsure about),
add `--no-sync`.

## Reading corrections back

- Active rules, as injected: `harness/corrections/INDEX.md`
- Full record with evidence: `harness/corrections/C-NNNN-*.md`
- `python3 harness/bin/harness.py status`

## Hard rule

Recording a correction writes files under `harness/` only. It issues no
business-system call at all — read or write.

RULE 0 in `CLAUDE.md` governs what the toolkit may write to SAP. Nothing here
widens it, and a correction must never be used to pre-authorise a write the
operator did not explicitly ask for.
