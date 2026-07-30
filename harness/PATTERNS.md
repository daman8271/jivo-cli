# Query-pattern capture — the second learning signal

`harness.py` clusters what operators **typed**. `patterns.py` clusters what
actually **got run**.

```
harness/bin/patterns.py       record · propose · draft · status · selftest
harness/hooks/post-tool-use.sh   PostToolUse hook (silent, exit 0 always)
harness/questions/queries.jsonl  the log this writes
```

## Why a second signal exists

The question-shape signal is weak on its own, and it fails in a specific,
predictable way. Three operators want the same number:

| operator | typed | question shape |
|---|---|---|
| Accounts | "what's the ledger balance for Sharma Traders" | `qa1` |
| Sales | "how much does Gupta Oils owe us right now" | `qa2` |
| Ops | "give me the outstanding statement for that vendor" | `qa3` |

Three shapes. `harness.py mint` needs five of *one* shape, so it sees nothing —
even though the need came up eleven times. But every one of those sessions ran
the same command:

```
sapb1 query BusinessPartners --filter "CardCode eq <val>" --select "CardName,CurrentAccountBalance"
```

The command is the need stated unambiguously, in the vocabulary a skill has to
be written in. That is the signal this module captures.

It also answers the owner's framing directly — *"a person is continuously
selecting from one place, one table, it can make a skill of it"* — because the
table is a first-class field in every record.

---

## 1. What is captured

### The PostToolUse payload — verified, not assumed

I did not guess the schema. I ran an isolated `claude -p` session in a scratch
directory with a throwaway `--settings` file whose only hook dumped stdin to a
file, and captured real payloads: one `Bash` call, and one MCP call against a
throwaway stdio MCP server written for the purpose. Both are reproduced here
verbatim (values shortened).

**Bash:**

```jsonc
{
  "session_id": "1d352f3d-74df-437a-9089-01b93d9b5db4",
  "transcript_path": "/Users/…/1d352f3d….jsonl",
  "cwd": "/private/tmp/…/hookprobe",
  "prompt_id": "1543d774-8897-460e-a532-bae926a4724d",
  "permission_mode": "dontAsk",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input":    { "command": "echo HELLO_PROBE", "description": "Echo HELLO_PROBE" },
  "tool_response": { "stdout": "HELLO_PROBE", "stderr": "", "interrupted": false,
                     "isImage": false, "noOutputExpected": false },
  "tool_use_id": "toolu_01L6DrA5WNZdGyVgeDf8L2Xd",
  "duration_ms": 407
}
```

**MCP** — same envelope, but two differences that matter and that a guess would
have got wrong:

```jsonc
{
  "tool_name": "mcp__probesap__sapb1_query",
  "tool_input": { "entity": "BusinessPartners",
                  "filter": "CardType eq 'cSupplier'",
                  "select": "CardCode,CardName,CurrentAccountBalance",
                  "company": "JIVO_OIL_HANADB" },
  "tool_response": [ { "type": "text", "text": "PROBE_OK 1 row" } ]
}
```

* `tool_name` is `mcp__<server>__<tool>`.
* `tool_input` is the raw arguments object.
* **`tool_response` is a LIST of content blocks for MCP, a dict for Bash.** We
  read neither, but the asymmetry is the kind of thing that breaks code written
  from an assumption.

Real MCP argument names were taken from the live tool schemas, not invented:
`mcp__sapb1__sapb1_query{entity, filter, orderby, select, top}` — note there is
no `company` on the real tool, unlike my probe stand-in — and
`mcp__postsql__postgres_query{sql, database}`.

### What is recorded

Bash invocations of `sapb1`, `postsql`, `hana-sql`, `dsr`, `ecom`, `oms`,
`factory`, `exim` (plus `-cli` binary-name variants), and `mcp__sapb1__*` /
`mcp__postsql__*` tool calls. One JSONL line per invocation:

```jsonc
{ "ts": "2026-07-30T05:24:11",
  "persona": "accounts",
  "session": "1d352f3d",          // first 8 chars of session_id
  "tool": "Bash",                 // or the mcp__ tool name
  "family": "sapb1",              // canonical tool family
  "raw": "sapb1 query BusinessPartners --filter \"CardCode eq 'V0001'\" …",  // scrubbed, ≤300
  "shape": "sapb1 query BusinessPartners --filter \"CardCode eq <val>\" --select \"CardName,CurrentAccountBalance\"",
  "shape_id": "260c10a0672c",     // sha1(shape)[:12]
  "family_id": "6a6e1d359110",    // sha1(tool|verb|entity|filter-fields|scope)[:12]
  "q_shape_id": "qa1",            // the question shape that led here, if recent
  "parsed": { "tool": "sapb1", "verb": "query", "entity": "BusinessPartners",
              "filter": "CardCode eq <val>", "filter_fields": ["CardCode"],
              "select": ["CardName","CurrentAccountBalance"], "company": "",
              "tables": [], "flags": [], "orderby": "" } }
```

`parsed` exists so later analysis never re-parses a command string.

### What is the pattern, and what is noise

| kept in the shape | dropped from the shape |
|---|---|
| tool family, sub-command | `--top`, `--skip`, `--page-size`, `LIMIT`, `OFFSET` |
| entity / table | `--json`, `--csv`, `--compact` |
| filter **field names and operators** | filter **values** (→ `<val>` / `<date>` / `<num>`) |
| selected columns, as a **sorted set** | column order |
| company (SAP) or database (Postgres) | `--host`, `--port`, `--timeout`, `--insecure` |
| `--count`, `--all` | `--orderby` |

Reasoning for the two non-obvious calls:

* **`--count` and `--all` stay.** "Just the number" and "every matching row"
  are different needs that deserve different skills. `--top 5` versus
  `--top 500` is the same need.
* **`--orderby` goes.** Sort order changes how you read a result, not what data
  you need. It is still recorded in `parsed.orderby` so a draft can reuse the
  most common one.

### CLI and MCP collapse to one shape

`sapb1 query BusinessPartners --filter "CardCode eq 'V1'"` and
`mcp__sapb1__sapb1_query{entity:"BusinessPartners", filter:"CardCode eq 'V1'"}`
produce the **same** `shape_id`. Two operators reaching the same read through
different transports have the same need; the transport is not the pattern. The
convenience tools are normalised onto their entity sets too, so
`sapb1 partners --suppliers` and `sapb1 query BusinessPartners --filter
"CardType eq 'cSupplier'"` converge (`--suppliers` is a `CardType` filter
wearing a flag costume).

### Two identifiers, on purpose

`shape_id` is strict — entity + filter fields + selected columns + scope. It is
what a skill is minted against.

`family_id` is coarse — tool + verb + entity + filter fields, **ignoring the
selected columns**. It exists because the strict id fragments the moment a
colleague adds `Phone1` to `--select`, and because "someone keeps selecting from
one table" is a question about the table, not the column list. `propose` reports
families separately so one skill can be written to cover several strict shapes.

### Not captured, deliberately

* **Writes.** `sapb1 draft` / `post` / `patch` are skipped. A write is not a
  query pattern, and nothing minted from this log may authorise one (RULE 0).
* **Anything a tool returned.** See §2.
* **Non-JIVO tools.** `Read`, `Edit`, `Grep`, other MCP servers: ignored.

---

## 2. The redaction guarantee

**`tool_response` is never read.** Not stdout, not stderr, not one row of SAP
data. There is no field in the record that could hold it, so a leak is
structurally impossible rather than merely unlikely. The selftest asserts this
by planting a sentinel in `tool_response` and confirming it cannot be found
anywhere in the output.

The command string *is* recorded, because the flags are the pattern. Four layers
protect it:

1. **Whole-payload drop** if the command touches a credential file — `.env`,
   `.pgpass`, `.netrc`, `.npmrc`, `.pypirc`, `id_rsa`, `id_ed25519`, `.ssh/`,
   `credentials`, `auth.json`, `hana.env`, service-account JSON. Not the
   offending segment — the whole payload. A per-segment check would keep the
   harmless half of `cat .env && sapb1 doctor`, which is defensible but hard to
   state as a promise.
2. **Scrub at the input boundary.** The command segment is scrubbed *before*
   parsing, so every derived field — `entity`, `filter`, `company`, `shape` —
   inherits the redaction. Rules: `--password/--token/--secret/--api-key/
   --auth/--bearer/--user/…` values; `*PASSWORD*=`, `*TOKEN*=`, `*SECRET*=`,
   `*KEY*=`, `*PAT*` env assignments; `scheme://user:pass@host` userinfo;
   JSON-ish `"password": "…"`; vendor literals (`sk-ant-…`, `sk-…`, `ghp_…`,
   `github_pat_…`, `xox[baprs]-…`, `AKIA…`, `AIza…`, PEM private-key headers,
   JWTs); and any bare hex blob ≥40 chars.
3. **Fail closed.** After scrubbing, the assembled JSON line is re-inspected. If
   any secret pattern still matches, the record is **dropped** rather than
   logged half-clean.
4. **Control-character strip** on every persisted string, so a normaliser bug
   can never put a raw byte into a file destined for git.

Over-redaction is free here: a redacted token was never part of a query
pattern. `--user` is scrubbed too — it is half a credential and contributes
nothing to the shape.

---

## 3. Ranking design, and the argument for it

**Runs are cheap. Distinct days are not.**

One operator chasing a single number can produce twenty runs in an afternoon.
That is an investigation, not a standing need, and a ranking that sorts by count
promotes it to the top of the list. So volume is deliberately the
weakest-growing term, and it cannot carry a shape on its own.

### The gate runs before the score

A shape must clear **all three** to be a candidate:

| condition | default | env |
|---|---|---|
| total runs | ≥ 4 | `JIVO_QMINT_MIN_RUNS` |
| distinct calendar days | ≥ 3 | `JIVO_QMINT_MIN_DAYS` |
| distinct sessions | ≥ 2 | `JIVO_QMINT_MIN_SESSIONS` |

This is where "20 times in one afternoon" is actually handled. It fails
`days ≥ 3` and `sessions ≥ 2` no matter how high its score would be, so it is
*excluded*, not merely out-ranked. Scoring only orders what already passed.

### The score

```
spread    = 3.0 × min(days, 8)                    →  3 … 24   PRIMARY
persist   = 2.0 × min(weeks − 1, 3)               →  0 …  6
volume    = 2.0 × log2(runs + 1)                  →  saturating
breadth   = 3.0 × (personas − 1) + 0.5 × min(sessions, 8)
phrasing  = 1.5 × min(distinct_question_shapes − 1, 4)   → 0 … 6

score     = (spread + persist + volume + breadth + phrasing) × recency
```

* **spread** — distinct days, capped at 8, weighted highest. The single best
  discriminator between a burst and a habit.
* **persist** — appearing across separate ISO weeks is much stronger evidence
  than three days inside one week.
* **volume** — logarithmic. 4 runs → 4.6; 20 runs → 8.8; 100 runs → 13.3.
  A tiebreaker, never a driver.
* **breadth** — a *second person* independently needing the same read is the
  strongest single piece of evidence that the need is standing rather than one
  person's project, so it carries the largest per-unit weight. Distinct sessions
  separate "one long conversation" from "kept coming back".
* **phrasing** — the number of distinct question shapes that led to this query.
  This is the term that repays building a second signal at all: a shape reached
  from three different phrasings is a need the question-shape clusterer
  structurally cannot see.
* **recency** — × 1.0 within 14 days, × 0.6 within 45, × 0.3 beyond. A query
  pattern is more perishable than a correction: the report it served may have
  shipped. Hermes ages skills at 30 days stale / 90 archived
  (`tools/skill_usage.py`); a *proposal* deserves tighter windows than a skill.

Weights are module constants at the top of `patterns.py`, so tuning does not
mean editing logic.

### Skipping what is already covered

A shape is skipped when a `.claude/skills/*/SKILL.md` frontmatter declares its
`query_shape_id`, **or** its `query_family_id`. The family form matters: one
umbrella skill written for `BusinessPartners by CardCode` should suppress every
strict shape underneath it, not just the one that happened to be drafted.

---

## 4. Measured results

Everything below was produced by running the code. Command:
`python3 harness/bin/patterns.py selftest`.

### Selftest: 68 assertions, 0 failures

```
query-pattern selftest
  68 passed, 0 failed
```

### Shape collapse — 22 realistic payloads through the real shell hook

Fed as raw PostToolUse JSON to `harness/hooks/post-tool-use.sh`, in an isolated
harness tree. 22 payloads → **17 records, 10 distinct shapes**; all 22 hook
invocations exited 0.

```
  4x  260c10a0672c  sapb1 query BusinessPartners --filter "CardCode eq <val>" --select "CardName,CurrentAccountBalance"
  3x  592db398e53d  postsql query orders --filter "SELECT order_id, status FROM orders WHERE status = <val> AND channel_id IN (<list>) LIMIT <n>" --db jivo_oms
  2x  86aef06c4b84  sapb1 query Invoices --filter "DocDate ge <date> and DocDate lt <date> and Cancelled eq <val>" --select "DocTotal,VatSum" --all
  2x  5e38cdcb0e8f  dsr retailers list --filter "--beat <val>"
  1x  c5ad28a6c226  sapb1 query BusinessPartners --filter "CardType eq <val>" --select "CardCode,CardName,CurrentAccountBalance"
  1x  1a5da1ebc6d5  hana-sql query JIVO_OIL.OINV --filter "SELECT DocNum, DocTotal FROM "JIVO_OIL"."OINV" WHERE DocDate >= <date>"
  1x  5b9b1d682305  sapb1 doctor
  1x  a5c70f3f20f3  postsql query orders --filter "SELECT <num> FROM orders" --db jivo_oms
  1x  186847dc1f72  postsql query orders --filter "SELECT <num> FROM orders" --db postgres://<redacted>@10.0.0.1:5432/db
  1x  af9002186401  sapb1 query Items --filter "ItemName eq <val>" --select "ItemCode"
```

* The **4x** group is three different `--select`/`--top`/`--page-size`/quoting
  variants **plus one MCP call** — CLI and MCP collapsed as designed.
* The **3x** group is two CLI calls with different literals and different-length
  `IN` lists **plus one MCP call**.
* The 5 payloads that produced nothing: `ls -la && grep`, `mcp__github__list_prs`,
  `Read`, `sapb1 draft` (a write), and `cat .env && sapb1 doctor` (credential
  file → whole payload dropped).

### Negative tests — over-normalising is as broken as under-normalising

All verified as producing **different** `shape_id`s:

| A | B | why they must differ |
|---|---|---|
| `BusinessPartners … CardCode eq …` | `BusinessPartners … CardType eq …` | different filter field |
| `BusinessPartners … CardCode eq …` | `Invoices … CardCode eq …` | different entity |
| `… --select "CardName,CurrentAccountBalance"` | `… --count` | number vs rows |
| `… --company JIVO_OIL_HANADB` | `… --company JIVO_MART_HANADB` | different company |
| `SELECT … FROM orders` | `SELECT … FROM shipments` | different table |
| `dsr retailers list` | `dsr sales list` | different sub-command |
| `DocDate ge '2026-04-01'` | `DocDate ge 'notadate'` | `<date>` ≠ `<val>` |
| `# … sapb1 pattern, three …` | — | prose is not an invocation |

### Redaction — proved, not asserted

Seven planted secrets, scanned across the entire log after the run:

```
clean: Hunt3r            clean: sup3rs3cretpw     clean: p4ssw0rd
clean: sk-ant            clean: manager           clean: ecret
clean: ROWDATA_MUST_NEVER_APPEAR        ← the tool_response sentinel
lines with control chars: 0
```

What the records actually look like:

```
raw   : sapb1 doctor --user <redacted> --password <redacted> --host 10.0.0.5
raw   : PGPASSWORD=<redacted> postsql query "SELECT 1 FROM orders" --db jivo_oms
raw   : sapb1 query Items --filter "ItemName eq '<redacted>'" --select "ItemCode"
shape : postsql query orders --filter "SELECT <num> FROM orders" --db postgres://<redacted>@10.0.0.1:5432/db
```

### Ranking — on a synthetic month of activity (47 calls)

```
score  50.17  11x over 11d / 5w · 3 personas · 11 sessions · 3 phrasings   sapb1 query BusinessPartners … CardCode
score  31.67   5x over  5d / 5w · 2 personas ·  5 sessions · 1 phrasing    sapb1 query Invoices … DocDate range --all
score  27.64   4x over  4d / 4w · 2 personas ·  4 sessions · 1 phrasing    sapb1 query BusinessPartners … +Phone1
score   8.00   5x over  5d / 3w · 1 persona  ·  5 sessions · 0 phrasings   postsql query wip …   (last seen 70d ago)

Not (yet) candidates:
  22x/1d  59a45b35c2ab  [days 1<3, sessions 1<2]  sapb1 query JournalEntries --filter "TransId eq <num>"

Families spanning several strict shapes (one skill may cover all of them):
  score 51.0  family_id=6a6e1d359110  2 shapes · 15x over 15d · 3 personas
      sapb1 query BusinessPartners  by CardCode
```

Read that top-to-bottom, because it is the whole design working:

* The **standing need** (11 runs, 11 days, 5 weeks, 3 people, 3 phrasings) tops
  the list at 50.17.
* The **22-run burst** — the largest count in the dataset by a factor of two —
  is not a candidate at all. Gate, not score.
* The **stale pattern** has genuine spread (5 runs, 5 days, 3 weeks) but stopped
  70 days ago, so recency demotes it to last at 8.0.
* The **family** rolls the two `BusinessPartners by CardCode` shapes into one
  15-run signal — a skill written once for both.

A whole day's real capture (the 17 records above, all one day) yields **zero**
candidates, with the reason printed per shape: `4x/1d [days 1<3]`.

### `draft` — prints, never writes

`draft 260c10a0672c` emitted 2,884 bytes to stdout; a filesystem checksum
before and after was **identical**. The output carries frontmatter
(`query_shape_id`, `query_family_id`, persona, minted date, seven
`evidence_*` fields, `status: draft-unverified`), a `DRAFT — UNVERIFIED` banner
with a three-step verification checklist, the command with parameters marked
`<CARDCODE>`, one real logged run as the verified-shape source, and — pulled
from `log.jsonl` via `q_shape_id` — the three **real operator phrasings** that
led to the query:

```
- "what's the ledger balance for Sharma Traders"
- "how much does Gupta Oils owe us right now"
- "give me the outstanding statement for that vendor"

Note: 3 distinct phrasings, one query. That is why this skill is keyed on the
query, not the wording.
```

This is the autonomy line. The harness proposes and drafts unattended; a
verified query is what makes it real. Hermes ships autonomous skill-writing
with approval **and** static guards off by default (`write_approval: false`,
`guard_agent_created: false`); we deliberately do not copy that, because a
wrong skill here produces a wrong financial number someone acts on.

### Latency (n=30, macOS, Python 3.14)

| path | cost |
|---|---|
| non-JIVO tool call (`Read`, `Edit`, `Grep` …) | **12.4 ms** — pure-bash regex pre-filter, python never starts |
| JIVO CLI call (parse + normalise + append) | **57.2 ms** |

The pre-filter is the 95% case. It is a bash `[[ =~ ]]` with no fork, placed
before the `command -v python3` check, so the common path never pays interpreter
startup. Both paths emit nothing on stdout — zero tokens added to the turn.

---

## 5. Bugs the verification actually found

Listing these because "I wrote tests" and "the tests found things" are different
claims, and only the second one is evidence.

| # | defect | how it was caught |
|---|---|---|
| 1 | **NUL bytes in persisted shapes.** The `\x00`-delimited literal-hiding sentinel was being eaten by the number regex, so every quoted value rendered as `\x00<num>\x00` — corrupting the JSONL and silently destroying the `<val>` / `<date>` distinction. | selftest assertion `draft marks parameters` failed; the assertion was correct and the code was wrong |
| 2 | **`IN (9)` did not collapse with `IN (1,2,3)`.** The regex required 2+ elements, splitting one pattern into two. | end-to-end run: postsql collapsed 2x + 1 stray instead of 3x |
| 3 | **Scrub ran on the output boundary,** so derived fields (`company`, `shape`) never got it. A `postgres://user:pass@` in `--db` reached the shape unscrubbed; fail-closed then discarded an otherwise valid pattern. Nothing leaked, but the record was lost. | end-to-end run: one payload produced zero records |
| 4 | **Credential-file check was per-segment,** so `cat .env && sapb1 doctor` still logged its second half. | end-to-end run: an unexpected extra `sapb1 doctor` record |
| 5 | **`<DATE>` in SQL vs `<date>` in OData** — the SQL keyword uppercaser hit the placeholders, making identical values render differently by tool. | reading the shape strings in test output |
| 6 | **`"JIVO_OIL"."OINV"` → `JIVO_OIL"."OINV`** — quote stripping only handled the ends. | reading the hana-sql shape |
| 7 | **Generic CLIs lost unknown flag names.** `--beat 4471` became a bare boolean plus a stray positional, so `--beat` vanished from the shape — and for those CLIs the flag names *are* the pattern. | reading the `dsr` shape |
| 8 | **`import harness` silently resolved to a namespace package** when run from a directory containing a `harness/` folder: the import succeeded, the fallback never triggered, and every attribute access failed. | explicit fallback-path check |
| 9 | **Prose was parsed as invocations.** `find_invocation` scanned *every* token, so a bare `sapb1` in a comment or a Python string literal became a call. | **dogfooding** — the lead wired this hook live during development, and it recorded `sapb1 pattern, three` and `postsql via MCP:` from my own heredocs |

Defect 9 is the useful one. `find_invocation` now requires command position
(first token of a segment after `env` / `sudo` / `VAR=value` / loop-keyword
prefixes), `split_segments` strips shell comments, and the sub-command is
validated against the real `sapb1` / `postsql` vocabularies. Before the fix:
4 garbage records in ~10 minutes of development. After: 0 from the same
activity, while every legitimate form still captures — `PGPASSWORD=x postsql
query …`, `for c in …; do sapb1 query …; done`, `cd sap-b1/cli && ./sapb1 query
…`, `hana-sql "SELECT …"`.

---

## 6. Using it

```bash
python3 harness/bin/patterns.py status                 # what the log holds
python3 harness/bin/patterns.py propose                # which shapes earned a skill
python3 harness/bin/patterns.py propose --explain       # + score breakdown
python3 harness/bin/patterns.py propose --json          # machine-readable
python3 harness/bin/patterns.py draft <shape_id> > /tmp/SKILL.md   # review, verify, then save
python3 harness/bin/patterns.py selftest                # 68 assertions
```

`draft` accepts a `family_id` too, so a family spanning several strict shapes
can be drafted once.

### Tuning

| variable | default | effect |
|---|---|---|
| `JIVO_QMINT_MIN_RUNS` | `4` | gate: total runs |
| `JIVO_QMINT_MIN_DAYS` | `3` | gate: distinct days |
| `JIVO_QMINT_MIN_SESSIONS` | `2` | gate: distinct sessions |
| `JIVO_QMINT_ATTRIB_WINDOW` | `3600` | seconds a question stays attributable to a query |
| `JIVO_HARNESS_NO_LOG` | unset | `1` disables all harness logging |
| `JIVO_PATTERNS_NO_LOG` | unset | `1` disables query capture only |

### Notes for whoever wires and maintains this

* `harness/questions/queries.jsonl` wants `merge=union` in `.gitattributes`,
  exactly like `log.jsonl`, so parallel appends from several operators merge
  without conflicts.
* Adding a CLI means one entry in `TOOL_ALIASES`. Adding a sub-command
  vocabulary for it (`_KNOWN_SUBCOMMANDS`) tightens defect-9 protection but is
  optional; without it the generic `_SUBCOMMANDISH` check applies.
* `patterns.py` reuses `harness.py`'s `_active_persona`, `_parse_frontmatter`
  and `_slug` when it can, and falls back to local equivalents when it cannot,
  so a change in one module cannot break the hook in the other.

---

## 7. What I verified by running, and what I did not

**Verified by running:**

* the PostToolUse payload schema for both `Bash` and `mcp__*`, captured live
  from real `claude -p` invocations
* 68 selftest assertions, 0 failures
* 22 payloads driven through the real `post-tool-use.sh`, all exiting 0, with
  the shape-collapse table above
* every negative case in the table above
* redaction: 7 planted secrets, 0 found anywhere in the log; 0 control
  characters in any persisted field
* `tool_response` never reaching a record, via a planted sentinel
* the ranking on a 47-call synthetic month, including gate rejection of a
  22-run burst and recency demotion of a 70-day-old pattern
* `draft` writing nothing (filesystem checksum unchanged) and printing 2,884
  bytes of complete SKILL.md
* already-minted suppression, by `query_shape_id` and by `query_family_id`
  (one family skill correctly suppressed both member shapes: 4 candidates → 2)
* latency on both hook paths
* the `harness.py`-absent fallback path

**Not verified — stated plainly:**

* **No business system was contacted.** No SAP, Postgres, HANA or portal call
  was made, read or write. That is by design, and SAP is not reachable from
  this machine anyway. Everything above ran on synthetic payloads.
* **I never observed a real `mcp__sapb1__sapb1_query` PostToolUse payload.** I
  verified the envelope with a throwaway MCP server and the argument names from
  the live tool schemas, but the two were confirmed separately, not in one
  observation.
* **Windows / git-bash: not tested.** The hook avoids constructs known to break
  there and `_basename` normalises backslashes and strips `.exe`, but nobody has
  run it on Windows.
* **Concurrent appends from several operators: not tested.** Each record is a
  single `write()` of complete lines, which is atomic enough for JSONL on the
  platforms in use, but I did not test it under contention.
* **The ranking weights are a designed judgement, not a fitted model.** They
  behave correctly on the cases in §4 and on the two cases the brief names, but
  they have never seen a month of real JIVO traffic. Expect to tune
  `JIVO_QMINT_MIN_DAYS` first.
* **`q_shape_id` attribution is a time-proximity heuristic** — the most recent
  logged question within one hour. The PostToolUse payload carries `prompt_id`
  and `session_id`, but `harness.py ask` does not record either, so a
  join on ids is not currently possible. If the lead adds `prompt_id` to
  `cmd_ask`'s record, this becomes exact and the phrasing-diversity term gets
  materially more trustworthy.
