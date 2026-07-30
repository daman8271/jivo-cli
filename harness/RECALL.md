# `recall` — search over everything the team has written down

The harness has two memory tiers, both taken from NousResearch/hermes-agent
(reverse-engineered in `research/01-hermes-learning.md`):

| tier | what it is | cost |
|---|---|---|
| **corrections digest** | tiny, bounded, injected into every session | paid every turn |
| **`recall`** | full-text search over the whole written record | **zero until called** |

The first stops a known mistake being repeated. The second answers *"what did we
work out about the oil returns escalation last month?"* — which today means
guessing which file to grep. The answer is 324 lines inside
`savings-audit/findings/finding-oil-returns-escalation.md`, referenced by a
single wikilink from `chats/2026-07-28.md`. Nobody finds that by guessing.

Hermes' equivalent is `session_search` — SQLite FTS5 over every past message,
plus a parallel trigram index for substring recovery
(`hermes_state_search.py`, schema at `hermes_state_common.py:331` / `:391`).
Same problem, different substrate: our corpus is dated markdown, not a message
table.

**RULE 0 is untouched.** `recall` reads local markdown and writes exactly one
file — its own index. It issues no business-system call of any kind.

---

## Using it

```bash
python3 harness/bin/recall.py index                 # build / refresh (incremental)
python3 harness/bin/recall.py search "oil returns escalation"
python3 harness/bin/recall.py stats                 # what's indexed, how big, how fresh
```

Useful flags on `search`:

| flag | default | what it does |
|---|---|---|
| `--limit N` | 8 | results to return |
| `--per-file N` | 2 | max hits from one document (`0` = no cap) |
| `--db PATH` | — | search a different index |
| `--persona X` | — | X-tagged notes **plus** untagged/shared ones |
| `--since` / `--until` | — | `YYYY-MM-DD`, filters on the document's date |
| `--path GLOB` | — | e.g. `--path 'chats/*'` |
| `--full` | off | print the whole matching chunk, not a snippet |
| `--json` | off | machine-readable, for a hook or an agent |

On `index`: `--rebuild` (start clean), `--no-trigram` (see [Disk](#disk)),
`-v` (one line per file showing exactly what was done).

On all three: `--corpus PATH` (repeatable — replaces the default roots) and
`--db PATH` (use a different index file).

Environment: `JIVO_RECALL_CORPUS` replaces the corpus roots,
`JIVO_RECALL_DB` relocates the index, `JIVO_RECALL_DEBUG=1` turns off the
fail-quiet wrapper while developing.

**`index` fails closed on a corpus mismatch.** Pointing `index` at a different
corpus without saying so would silently replace the shared index with a narrower
one — I did exactly that to myself during testing and left it at 0 files. So:

```
$ python3 harness/bin/recall.py index --corpus /somewhere/else
recall: this index was built from [chats, savings-audit, harness, connections, vision, .]
        but you asked for [/somewhere/else]. Nothing was changed.
  To re-point this index:      add --rebuild
  To keep them separate:       JIVO_RECALL_DB=<path> (or --db <path>)
```

**Every subcommand exits 0, always** — including on a missing corpus, a missing
index, or a corrupt database. A hook can call this and a broken index will never
block an operator mid-question.

---

## What it indexes, and why those six roots

The rule: **index what a human wrote about a decision; don't index what a
generator wrote about an API.**

| root | files / chunks | why it's in |
|---|---|---|
| `chats/` | 10 / 68 | the point of the exercise — dated session work logs |
| `savings-audit/` | 33 / 437 | the audit vault. **The motivating query resolves here, not in `chats/`** — the chat log only wikilinks to it. Leaving it out would return the one-line mention instead of the 324-line answer |
| `harness/` | 10 / 182 | the digest injects only a correction's one-line `## Rule`; the wrong / right / **evidence query** stays on disk and is exactly what you want to search. Plus the research and design notes |
| `connections/` | 48 / 617 | system runbooks and inter-system lineage — what a chat log *points at* ("documented in `SAP-HOME-ACCESS.md`") |
| `vision/` | 1 / 5 | intent and direction |
| repo-root `*.md` | 3 / 18 | `README`, `CLI-HUB-README`, `CLAUDE.md` — the toolkit map |

**Deliberately out:** `sap-b1/` (548 files), `portals/` (194), `exim/` (156),
`control-panel/`, `factory-cli/`, `dsr-cli/`, `tankhapay/`, `ecom-cli/`,
`oms-cli/`. That is ~80,000 lines of generated study vault and API reference,
and it already has a purpose-built lookup path — `sapb1 entities|fields`, the
MCP catalog tools, each CLI's own `--help`. Indexing it would bury every
work-log hit under API stubs, which is the single failure mode that makes people
stop using a search tool. Including all of it would have made the index ~6×
bigger and measurably worse.

This is a default, not a cage — `--corpus` (repeatable) or
`JIVO_RECALL_CORPUS` replaces the set entirely.

⚠️ **The index inherits the corpus's sensitivity.** Some tracked markdown
already contains credential-shaped strings (several files under `chats/` and
`connections/`). `recall` neither adds nor removes exposure — it prints
snippets from files the operator can already `cat`, and its database is
gitignored and never leaves the machine. Redacting at this layer would only make
search lie about its own corpus; the right fix is upstream, not here.

---

## Design decisions

### Chunks are heading sections

A whole 800-line work log is a useless search result; a single line has no
context. Before choosing, I measured the real corpus: **1,127 H1–H3 sections,
median 14 lines, p90 36, p99 67, max 236.** That grain is already right, so
`recall` splits at H1–H3 and leaves H4+ inside the parent. Only the 16 sections
that exceed ~4,000 characters are split further, at blank lines, and those parts
are labelled `(part N)`.

Each chunk carries the document title, the **full heading trail**
(`2026-07-28 › Delivered: Oil turnover this quarter`), the date, tags, and its
1-based start line — so a result is a `file:line` you can open, not just a
filename. Measured mean chunk: **1,161 characters.**

Frontmatter is stripped from the body but its title and tags are indexed as
separate columns, so a search matches a document's title even when the matching
section never repeats those words.

### Two indexes, like Hermes

- **`chunks_fts`** — `porter unicode61 remove_diacritics 2`. Stemming means
  `returns` finds `return`. Good for prose work logs.
- **`chunks_tri`** — `trigram`. Substring matching for what the word tokenizer
  cannot reach.

Standard runs first and always ranks above trigram; trigram only **tops up** a
page that came back thin, and every trigram hit is labelled as such in the
output. Measured, on this corpus:

| query | word index | trigram index |
|---|---|---|
| `scalation` (truncated) | 0 rows | 19 rows |
| `0052` (inside item code `RM0000052`) | 0 rows | 20 rows |
| `ANADB` (inside `JIVO_OIL_HANADB`) | 0 rows | 284 rows |
| `ail2ban` (inside `fail2ban`) | 0 rows | 6 rows |

(Measured excluding this file — `harness/` is in the corpus, so once
`RECALL.md` documented those example terms the *word* index started matching
them too. A small demonstration that the index is live and that a document
about search becomes searchable like anything else.)

**Honest limit:** trigram is *substring* matching, not fuzzy matching. It
recovers partial words, truncations and mid-token matches — an operator who
remembers "the 0052 olive oil thing" finds it. It does **not** recover
transpositions or dropped letters: `Blesing` does not find `Blessing`, because
`Blesing` is not a substring of it. Where the brief said "misspelled", read
"partial".

### Ranking

`bm25(title 4.0, heading 3.0, tags 2.0, body 1.0)`, ascending (SQLite's bm25 is
negative; more negative is better — verified against this build rather than
assumed). A title hit is a far stronger signal than the same word buried in a
paragraph, which is why `"oil returns escalation"` returns the finding note
whose *title* says that, above the chat log that mentions it in passing.

`--per-file 2` caps how many sections of one document can take the page.
Without it, the 324-line audit note won all four slots with four near-identical
excerpts — the operator learns more from one hit in each of four sources, and
the rest of the file is one `--path` away.

### Incremental indexing

Two gates, cheapest first:

1. **`(mtime_ns, size)` unchanged** → skip; the file is never even hashed.
2. **mtime moved but `sha256` identical** (a `touch`, a fresh clone, a
   save-with-no-edit) → refresh the stat, **keep the chunks**. Re-chunking
   identical bytes is pure waste.
3. Otherwise → delete that file's chunks from all three tables and re-chunk it.

Files that vanish from the corpus have their chunks removed. Paths are stored
repo-relative with POSIX separators so an index built under git-bash on Windows
stays comparable with one built on macOS.

### Degradation, one step at a time

FTS5 and the trigram tokenizer are **independent optional** features of a SQLite
build (trigram needs ≥ 3.34). Both are probed at open time — never assumed — and
`recall` loses only what is actually missing:

```
fts5 + trigram  →  fts5 only  →  LIKE over the same chunks  →  ripgrep  →  pure-python scan
```

`stats` and every search header name the live path, so it is never a mystery
which one answered. The LIKE rung matters: it keeps chunking, headings and
`file:line` intact on a build with no FTS5 at all. The last two rungs run only
when there is no usable database, and both are given the *same* file list the
index would have used — a degraded search never silently widens the corpus to
the whole repo.

Ripgrep is used when present but **not depended on**; the pure-Python scan is
the guaranteed floor, since an office box on git-bash may well not have `rg`.

### Fail quiet, exit 0

Every path returns 0, and internal failures print one line to stderr. A failed
`index` rolls back and leaves the previous index intact.

### Ordinary FTS5 tables, not `content=` external-content

External-content tables avoid duplicating the text, but every delete must then
supply the *old* column values — and incremental re-indexing deletes constantly.
Getting that wrong corrupts the index silently and search returns wrong answers
forever. At this corpus size the duplication is cheap and the bug class it
removes is not. **This is the one decision with a measured, material cost — see
below.**

---

## Disk

The index is **10.2× the text it indexes**. That is mostly inherent, partly not.
Measured with `dbstat` on the real corpus (1,505 KB of indexed text):

| component | size | share | inherent? |
|---|---|---|---|
| trigram index (`chunks_tri_*`) | 9.22 MB | 61.8% | **mostly yes** |
| word index (`chunks_fts_*`) | 3.23 MB | 21.7% | partly |
| chunk store (`chunks` + indexes) | 2.41 MB | 16.2% | yes |
| other | 0.05 MB | 0.4% | — |
| **total** | **14.93 MB** | | |

Splitting that by cause:

- **7.02 MB (47%) is the trigram postings list, and it is inherent.** A trigram
  index stores every overlapping 3-character window of every document, so it is
  intrinsically several times the size of the source text. There is no tuning
  that avoids this — only choosing not to have substring search.
- **4.29 MB (28.7%) is *not* inherent.** It is the `chunks_fts_content` +
  `chunks_tri_content` shadow copies, i.e. the price of the ordinary-FTS5-table
  decision above. Switching both tables to `content='chunks'` external-content
  would remove it exactly.
- The remaining ~16% is the chunk store, which is what makes headings, line
  numbers and snippets possible. Necessary.

**The lever that exists today** — `index --no-trigram` drops the substring index
and `VACUUM`s the file in one step:

| configuration | db size | vs. indexed text |
|---|---|---|
| default (fts5 + trigram) | **14.93 MB** | 10.2× |
| `--no-trigram` | **5.70 MB** | 3.9× |

`stats` prints this breakdown live, so nobody has to read this file to find out
where the disk went. Turning trigram back on needs `--rebuild`.

**When the corpus grows 10× after the shared repo lands** (~15 MB of text, every
operator's chats with persona tags), expect roughly **150 MB** at the default and
**57 MB** with `--no-trigram`, scaling linearly. That is a gitignored local
artefact that rebuilds from scratch in well under a minute, so 150 MB is
survivable — but it is the point at which the external-content refactor becomes
worth its risk, because it would take the default to ~106 MB with no loss of
capability. **I did not make that change here**: it is a correctness-sensitive
refactor of the delete path, and doing it at the end of a verification pass
without re-verifying everything is exactly how you ship a silently-corrupting
index. It is a deliberate, measured, documented deferral, not an oversight.

---

## Personas

The corpus does **not** carry per-operator tags yet. The column, the filter and
the reporting are built and working, ready for when the shared repo lands.

Persona means **role, not identity**. `recall` reads `persona:` → `operator:` →
`area:` from frontmatter, and deliberately prefers `area:` over `author:`: a
correction written by *daman* **for Accounts** must answer to
`--persona accounts`, not `--persona daman`. `area: all` and "no tag at all"
both mean universal, so they behave identically. A path convention
(`chats/<persona>/…`) is honoured for when operator chats arrive that way.

`--persona X` returns X-tagged chunks **plus** untagged ones — the same
"your area plus universal" rule `harness.py` already uses for corrections, so an
Accounts operator doesn't pay for Sales traps but never loses shared knowledge.
Verified: `--persona sales` correctly drops the `area: accounts` correction
while keeping shared content.

---

## Measured results

Environment: macOS, Python 3.14.5, SQLite **3.53.2**. FTS5 **available**,
trigram tokenizer **available** — both probed, not assumed.

### Index

```
$ python3 harness/bin/recall.py index
recall: indexed 105 files / 1327 chunks in 0.28s  [fts5+trigram]
  new 105 · changed 0 · touched 0 · unchanged 0 · removed 0
  re-chunked 1327 chunks across 105 file(s)
```

Cold builds over three runs: **0.28s / 0.37s / 0.33s.** 105 files, 1,327 chunks,
1,505 KB of indexed text, mean chunk 1,161 chars.

### Incrementality

```
$ python3 harness/bin/recall.py index          # nothing changed
recall: indexed 105 files / 1327 chunks in 0.01s  [fts5+trigram]
  new 0 · changed 0 · touched 0 · unchanged 105 · removed 0

$ touch chats/2026-07-28.md
$ python3 harness/bin/recall.py index -v
  touch  chats/2026-07-28.md (mtime moved, content identical)
recall: indexed 105 files / 1327 chunks in 0.00s  [fts5+trigram]
  new 0 · changed 0 · touched 1 · unchanged 104 · removed 0
```

**0.01s warm vs 0.28s cold — 28× faster**, no file hashed, nothing re-chunked.
After a `touch`, exactly one file is looked at; the sha256 gate catches that the
bytes are identical and keeps its chunks.

A **real content edit** (one line appended to this file) re-chunks that file and
nothing else:

```
$ printf '\n<!-- probe -->\n' >> harness/RECALL.md
$ python3 harness/bin/recall.py index -v          # `same` lines elided
  update harness/RECALL.md (21 chunks)
recall: indexed 106 files / 1348 chunks in 0.02s  [fts5+trigram]
  new 0 · changed 1 · touched 0 · unchanged 105 · removed 0
  re-chunked 21 chunks across 1 file(s)
```

A **deleted file** has its chunks removed and stops being searchable, verified
on an isolated two-file corpus:

```
$ rm b.md && python3 harness/bin/recall.py index -v --corpus <tmp>
  same   …/a.md
  remove …/b.md (gone from corpus)
recall: indexed 1 files / 2 chunks in 0.00s  [fts5+trigram]
  new 0 · changed 0 · touched 0 · unchanged 1 · removed 1

$ recall search "ledgers"   # b.md's only content
recall: no match for "ledgers"  [fts5+trigram]
$ recall search "turnover"  # a.md still indexed
recall: 1 result(s) …
```

> The 105-file / 1,327-chunk figures throughout this document were measured
> before this file existed, and the harness itself is under active development.
> At the last run the corpus was **107 files / 1,375 chunks**. It moves; `stats`
> always shows the live number, and the ratios and timings hold.

### Search

Four real queries against the real corpus. Median latency **45–48 ms**
including Python startup.

```
$ python3 harness/bin/recall.py search "oil returns escalation" --limit 4
recall: 4 result(s) for "oil returns escalation"  [fts5+trigram]

1. savings-audit/findings/finding-oil-returns-escalation.md:10  (2026-07-28)
   Oil third-party returns ₹3.56 Cr above a 5% allowance — REFUTED as money, the rate trend is real
   › Oil third-party returns escalation — verification of rank #14
   # »Oil« third-party »returns« »escalation« — verification of rank #14 Part of [[SAVINGS-MOC]] · Evidence: [[»returns«-leakage]] **Verdict: REFUTED as a saving — ₹3.56 Cr …

2. savings-audit/findings/finding-oil-returns-escalation.md:313  (2026-07-28)
   › … › Overlaps — do not add these together
   … Direct double count. - **[[finding-unlinked-credit-notes]]** — ₹3.76 Cr of the same rupees …

3. savings-audit/SAVINGS-MOC.md:46  (2026-07-28)
   › 💰 Savings Audit — Map of Content › 🚩 Red flags — worth MORE than the savings (CFO/owner eyes)
   … »oil«-»returns«-»escalation«]] — the "»returns« explosion" is largely **invoice recycling** …

4. savings-audit/findings/finding-wip-variance-july.md:145  (2026-07-28)
   › WIP variance ₹2.04 Cr (July 2026) — REVISED …
   ## Overlaps — read before adding anything up - **[[finding-»oil«-»returns«-»escalation«]]** — same population of goods …
```

```
$ python3 harness/bin/recall.py search "reverse tunnel" --limit 4
1. connections/reverse-tunnel/README.md:163  (2026-07-29)   › … › Undo
2. connections/reverse-tunnel/README.md:54   (2026-07-29)   › … › Install
3. connections/SAP-HOME-ACCESS.md:76         (2026-07-30)   › 1) open the HANA tunnel over the reverse route …
4. connections/SAP-HOME-ACCESS.md:171        (2026-07-30)   › close tunnels when done

$ python3 harness/bin/recall.py search "Blessing Advertising overdue" --limit 3
1. savings-audit/findings/finding-blessing-advertising-overdue.md:10  — ₹3.11 Cr overdue in Beverages
2. savings-audit/findings/finding-blessing-advertising-overdue.md:181 — › What is bankable
3. savings-audit/lenses/receivables-aging.md:222 — › H6 — Bev's single biggest debtor

$ python3 harness/bin/recall.py search "July Oil turnover net of GST" --limit 3
1. chats/2026-07-28.md:17  › 2026-07-28 › Delivered: Oil turnover this quarter (blocked since the 27th)
   … **₹26.18 Cr »net« »of« »GST«** for 1–28 Jul 2026 (»Oil« / `JIVO_»OIL«_HANADB`) …
2. chats/2026-07-28.md:27  › 2026-07-28 › BREAKTHROUGH — direct read-only SQL into the SAP HANA database
3. chats/2026-07-24.md:30  › 2026-07-24 › Data pulled (live from SAP, read-only)
```

Trigram recovery, labelled in the output:

```
$ python3 harness/bin/recall.py search "0052" --limit 2
1. savings-audit/findings/finding-off-spec-olive-oil.md:10  (2026-07-28 · trigram)
   Off-spec olive oil RM0000052 — ₹8.21 Cr of inventory that was never bought, never sold …
   # RM000»0052« ₹8.21 Cr — REV …
```

### Empty / missing / hostile input

All exit **0**, none crash:

| case | result |
|---|---|
| `--corpus` points at a nonexistent dir | `no markdown found under … — nothing to index.` |
| `--corpus` points at an empty dir | same |
| `search` with no index built | falls through to ripgrep/python scan, header says `[file scan (no index — run: recall index)]` |
| `stats` with no index | `no index yet.` + the command to build one |
| `search` over an empty index | `no match` |
| `TODO: fix the turnover query` | sanitised (a bare `:` is FTS5's column-filter operator) |
| `what about "oil` | unmatched quote dropped, searches fine |
| `(returns) AND`, `turnover AND`, `***`, `*` | sanitised, no `OperationalError` |
| `hana-sql doctor`, `C-0001` | hyphenated terms auto-quoted so they stay phrases |
| `NOT`, `AND OR` | reported as having no searchable terms |
| empty query | `nothing to search for.` |

The query sanitiser is ported from Hermes' `_sanitize_fts5_query`
(`hermes_state_search.py:782`). It is the highest-value thing in that file:
FTS5's `MATCH` argument is a query *language*, and raw user text hits
`sqlite3.OperationalError` on a colon, an unbalanced quote, a bare `*` or a
dangling boolean — which reads to an operator as "search is broken".

---

## What I verified by running vs. what I did not

**Verified by running, on the real corpus:** FTS5 and trigram availability
(probed); every number in this document (file/chunk counts, all timings, all db
sizes and the `dbstat` breakdown, chunk statistics); all four required searches
plus the trigram and persona cases; incrementality including the touch-vs-edit
distinction; both fallback rungs (ripgrep and pure-Python, the latter by hiding
`rg` from `PATH`); the `--no-trigram` lever end to end including space reclaim;
every empty/missing/hostile case in the table above; and that `bm25` orders
ascending on this build.

**Not verified by running:**

- **Windows / git-bash.** Everything is written for it — `pathlib`, POSIX-normalised
  stored paths, `st_mtime_ns`, no `fcntl` — but it was built and tested on macOS
  only. This is the one claim I would want someone to check on a real office
  machine before relying on it.
- **A SQLite build without FTS5, or without the trigram tokenizer.** The
  degradation ladder is written and the LIKE rung was exercised (via
  `--no-trigram`, which reaches it for substring queries), but I could not test
  a genuinely FTS5-less build — this SQLite has both.
- **The external-content refactor.** Its 4.29 MB saving is measured from the
  existing shadow tables; the refactor itself is not written, so its correctness
  is unproven.
- **Behaviour at 10× corpus.** The growth projection above is linear
  extrapolation from one measurement, not a load test.
- **Concurrency.** Two `index` runs at once rely on SQLite's own locking plus
  `BEGIN IMMEDIATE`; not tested under real contention.

Three bugs were found by running rather than by reading, and are fixed:
ripgrep's output was truncated *before* the multi-term filter (so the fallback
returned nothing for any query whose first term was common); a query of only
boolean operators returned an arbitrary chunk instead of nothing; and
`Index(db_path=DB_PATH)` bound the index path as a **default argument**, which
Python evaluates once at class-definition time — so `--db` never reached it and
writes still landed on the shared index. All three were invisible on inspection
and obvious the moment the code was exercised.

---

## Wiring it in

`recall.py` is standalone (`python3 harness/bin/recall.py …`) **and** mountable:

```python
# in harness.py main(), three lines:
from recall import register_cli as _register_recall
_register_recall(sub.add_parser("recall", help="search the written record"))
```

`register_cli(parent)` attaches `index` / `search` / `stats` to any parser —
the same shape Hermes uses for its own optional subcommand modules
(`hermes_cli/curator.py:680`). `harness/bin/harness.py` is untouched.

The index lives at `harness/.state/recall.db`, already gitignored via
`harness/.state/`. It is a derived artefact: delete it any time, rebuild in
~0.3s.
