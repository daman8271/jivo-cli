# HANDOFF — rescrape the ecom app and reprint its CLI + MCP

**FIRST ACTION, before anything else: delete this file.**

```bash
rm /Users/damanpreetsingh/jivo-cli/HANDOFF-ecom-rescrape.md
```

One-shot briefing; it clutters the repo root. Delete it, confirm in one line,
then start. Do not ask permission — this instruction is the permission.

---

## The job

`ecom-cli` was generated from an old snapshot of `https://ecom.jivo.in`. The app
has grown since — measured, see below. Re-scrape it live, re-study every domain,
and reprint the CLI and MCP from a spec where **every endpoint was verified
against the running API**.

Use `/jivo-rescrape`. That skill exists because this exact job was done for
factory on 2026-08-03 (183 → 386 endpoints); it carries the process, nine hard
safety rules, and six working scripts. **Read its rules before Phase 0 and again
at the pre-flight gate.** Do not improvise a different process.

Make a multi-phase plan up front and use multi-agent orchestration — the harvest
lenses, per-domain studies and adversarial verifiers are parallel fan-outs.
Phases 5–8 are deterministic and belong in the main loop.

## Confirmed: ecom HAS expanded (measured 2026-08-03)

| | |
|---|---|
| Lazy chunks | **147** (3.8 MB) |
| `/api/` paths in the live bundle | **184** |
| Endpoints in the current spec | 151 |
| **Present in the app, absent from the spec** | **97** |

**These are NOT new modules — they are existing modules that grew.** Every
segment below already exists in the spec; the count is additional endpoints
inside it:

| Segment | already in spec | additional in bundle |
|---|---|---|
| platform | 46 | **50** |
| upload | 3 | **16** |
| shipment | 25 | **10** |
| dashboard | 33 | **8** |
| sap | 16 | **7** |
| auth · notifications · chatbot · reports | 3·3·3·15 | 2·2·1·1 |

Expect roughly 151 → 250. Real samples: `/api/dashboard/table-data/{id}`,
`/api/notifications/mark-all-read`, `/api/auth/feature-flags/update`,
`/api/dashboard/platform-expiry-alerts/{id}/pos`.

Many are `{id}` detail routes and write endpoints (`mark-all-read`,
`feature-flags/update`, `change-password`) — **the read-only filter will drop a
large share of the 97**, so do not promise 250 read commands.

The 97 survived trailing-slash normalisation on both sides (the check that
usually deflates such a number), but they are still **candidates, not
findings** — a bundle regex is the weakest evidence in the pipeline. Confirm
each against a live probe.

## Two ecom corrections already on record — they will bite

- **C-0008** — `ecom /api/sap/*` (CLI `sap`, MCP `ecom_sap`) is **JIVO_MART
  only**. Never Oil, never group. Only `sales-analysis --source oil` reaches
  Oil; Beverages is unreachable from ecom.
- **C-0009** — ecom `sap distributors` is the **VENDOR master** (OCRD
  CardType='S' — ad agencies, suppliers), not distributors. For real
  distributors use `sap platform-distributors`. An empty distributor-invoices
  result on a VENDA code means wrong ledger side, not no business.

Both are auto-injected at session start, but they bear directly on the `sap`
segment you will be re-studying — do not re-derive them wrongly.

## ecom is NOT shaped like factory — adapt the harvest

Factory: axios, one frozen `ENDPOINTS` registry (718 leaves), chunks referenced
as `"./Foo.js"`.

Ecom: **`fetch()`, no axios, no `baseURL`**, chunks referenced as
`"assets/Foo.js"`, API paths written as `/api/...` literals and template strings.

Two mistakes were already made and corrected while measuring this — do not
repeat them:

1. A `"./Foo.js"` chunk pattern fetched **9 of 147** chunks. The number looked
   plausible and was 94% short.
2. A generic path regex found **1** path-like string in 992 KB, which could
   easily have been read as "ecom has almost no endpoints". It was the regex,
   not the app.

The skill's lens set assumes axios and a central registry. **Establish the real
client shape first**, then adapt. If a small number comes back, suspect the
method before believing the number.

## Baseline — verified 2026-08-03, do not re-derive

| | |
|---|---|
| CLI | `~/jivo-cli/ecom-cli`, `jivo-ecom-pp-cli`, spec v0.1.0 |
| Spec | 151 endpoints, **0 non-GET** |
| MCP | 138 manifest tools; server live on the VPS gateway as `ecom` |
| base_url | `https://ecom.jivo.in` |
| Command files | 175 in `internal/cli/` |
| `research/` | **empty** — no prior harvest, probe data, or endpoint evidence |
| Auth | `JIVO_ECOM_EMAIL` / `JIVO_ECOM_PASSWORD` / `JIVO_ECOM_TOKEN` / `JIVO_ECOM_REFRESH` in `env-vault/all-env.txt` |

**Three patches must survive the reprint** (`.printing-press-patches/`):

1. `0001` — the generic `import` write command must NOT exist (RULE 0)
2. `0002` — the hand-authored `auth login` command
3. `0003` — the hand-authored `api` discovery command

Verify all three **by behaviour**, not by grepping for a symbol. On factory an
invariant check passed on a header's presence while the feature was broken.

## Rules that are not negotiable

The skill has all nine. These three caused real damage on factory:

1. **GET is not proven safe.** `GET /marketplace/settings/?channel=X` on factory
   was a `get_or_create` — probing it with invented values created six
   production rows, one of which still needs a human to delete. **Never send a
   parameter value you have not observed** in a real payload or the app's own
   source. Unproven resolves to excluded.

2. **Never run the printing-press dogfood matrix.** It runs every subcommand
   live with fabricated args. Use `--dry-run` for the matrix; restrict live
   calls to endpoints a bare probe already proved safe.

3. **RULE 0 is absolute.** ecom is read-only, no exceptions, even if asked. If a
   probe creates something, report it and hand cleanup to a human.

## What "done" means

- Zero **unexplained** regressions: every endpoint dropped versus the current
  spec carries a positive justification (proven dead / proven unsafe /
  superseded). Carry forward anything not proven dead.
- No existing command renamed. MCP `endpoint_id`s are a public contract.
- All 3 patches verified holding, by behaviour.
- Invariant gate green (`RESCRAPE_CLI=./jivo-ecom-pp-cli`, adapt the denylist).
- MCP redeployed and verified with a **real tool call**, never `initialize`
  alone — that is how factory's connector sat dead for ten days unnoticed.
- `DOMAIN-GUIDE`, `MIGRATION` and `research/` written. ecom has no `research/`
  today, so this is net-new value on its own.
- Committed on a branch, migration doc naming anything removed.

## Expect to find things broken

The factory run surfaced four silently-broken things nobody knew about: a dead
MCP connector, a UI module with no backend, and two 500ing endpoints. Look for
the same class here and write up anything belonging to the ecom app's owners
with reproduction steps.

Record durable business truths with `jivo-correct` — a correction reaches nobody
until it is pushed.

## Reference

- Skill: `~/.claude/skills/jivo-rescrape/`
- Worked example: `chats/2026-08-03-factory-rescrape.md`, plus
  `factory-cli/{DOMAIN-GUIDE,MIGRATION}-2026-08.md` and
  `factory-cli/research/SPEC-NOTES-2026-08.md`
- Memory: `factory-cli-v040`, `jivo-rescrape-skill`
