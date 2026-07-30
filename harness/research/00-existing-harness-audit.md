# Audit — what jivo-cli's harness actually is today

**Date:** 2026-07-30 · **Author:** lead session · **Status:** verified unless marked

The goal of this audit is one question: *when a person in Accounts corrects the
AI, where does that correction go, and who else ever sees it?*

Short answer: **it goes into a directory that never leaves Daman's laptop, and
nobody else ever sees it.**

---

## 1. What a forker actually receives

`git clone https://github.com/daman8271/jivo-cli` delivers exactly this as
"the harness":

| Artefact | Tracked? | Role |
|---|---|---|
| `CLAUDE.md` (3.9 KB) | ✅ tracked | The entire brain. RULE 0 (read-only), system map, entity list, the metric definitions, the gotchas |
| `README.md`, `CLI-HUB-README.md` | ✅ tracked | Orientation |
| `sap-b1/accounts-kit/ASK-EXAMPLES.md`, `SETUP.md` | ✅ tracked | Worked examples |
| `chats/`, `connections/` | ✅ tracked | Work log + system-relationship notes |
| `.claude/` | ❌ **untracked** | Local hooks only (bridgespace). Never ships |

**Verified:** `git ls-files .claude` returns nothing; `.claude/` shows as `??`
in `git status`. So every forker starts with zero hooks, zero skills, zero
memory.

### The one-line consequence

`CLAUDE.md` is a **static, hand-edited, human-authored** document. It is the
conscious mind, and it is the *only* thing that travels. It has no write path
from a running session. Nothing the AI learns can ever get into it except by
Daman personally editing the file and pushing.

---

## 2. Where learning currently lands (and dies)

Four separate stores exist on this machine. **None of them are in the repo.**

| Store | Path | Size now | Travels? |
|---|---|---|---|
| Claude Code auto-memory | `~/.claude/projects/-Users-damanpreetsingh-jivo-cli/memory/` | 11 files, ~30 KB | ❌ |
| Skill-observation log | `…/skill-observations/log.md` | 16 observations | ❌ |
| claude-mem plugin | plugin-managed store | 50 obs / 285 k tokens of work | ❌ |
| Global skills | `~/.claude/skills/` | **270 skills** | ❌ |

The memory path is the damning one. It is keyed on
`-Users-damanpreetsingh-jivo-cli` — a slug of **Daman's absolute home
directory**. A colleague who clones to `/Users/ramesh/jivo-cli` gets project id
`-Users-ramesh-jivo-cli`: a different, empty directory. There is no merge, no
sync, no conflict — the two simply never meet.

Those 11 memory files contain exactly the class of knowledge the whole exercise
is about — e.g. `sap-sales-analysis-traps.md` records *"qty is per BOTTLE not
carton; Oil→Mart is intercompany; use U_TYPE/U_Sub_Group not name matching."*
That is a hard-won correction that would stop a colleague shipping a wrong
number tomorrow, and today it is unreachable to them.

---

## 3. The three gaps, named

Mapping our stack against Hermes' (see `01-hermes-*.md` for the evidence):

| Hermes | Purpose | jivo-cli equivalent | Gap |
|---|---|---|---|
| `SOUL.md` (stable tier) | Fixed identity + hard rules | `CLAUDE.md` RULE 0 | ✅ fine |
| `AGENTS.md` (context tier) | Repo-discovered instructions | `CLAUDE.md` body | ✅ fine |
| `MEMORY.md` (volatile tier) | **Auto-written**, bounded, injected every turn | `~/.claude/…/memory/` | ❌ manual, unbounded, doesn't travel |
| `USER.md` (volatile tier) | Per-user profile | *nothing* | ❌ absent |
| `skills/` + snapshot index | Retrieved-on-demand procedures | `~/.claude/skills/` | ❌ personal, doesn't travel |

**GAP 1 — no write path.** Learning is human-authored. Hermes has a `memory`
tool the model itself calls mid-turn.

**GAP 2 — no distribution.** Every store is machine-local and home-dir-keyed.

**GAP 3 — no role segmentation.** Accounts and Sales get a byte-identical
prompt. Hermes' `USER.md` slot is the natural home for "this operator is
Accounts", and we have nothing in it.

---

## 4. Two design constraints we must not get wrong

### 4.1 Bounded memory is a feature, not a limitation

**Verified** in `tools/memory_tool.py:165`:

```python
def __init__(self, memory_char_limit: int = 2200, user_char_limit: int = 1375):
```

Hermes caps the always-injected memory at **2,200 characters** and the user
profile at **1,375**. That is startlingly small — and deliberate. At capacity,
a write *fails* and forces a consolidation pass
(`_consolidation_failure`, `memory_tool.py:180`) before anything new can land.

Scarcity is the curation mechanism. Our `memory/` dir has no bound and is
already 30 KB across 11 files. Left alone it becomes a junk drawer that costs
tokens every turn and degrades answers.

**Design rule for us:** the always-injected tier stays small and bounded.
Everything else is retrieved on demand.

### 4.2 The always-injected tier must be byte-stable

**Verified** in `agent/system_prompt.py:503-512` — the memory block injected is
a *frozen snapshot taken at load time*, not live state:

> "This returns the state captured at load_from_disk() time, NOT the live
> state. Mid-session writes do not affect this. This keeps the system prompt
> stable across all turns, preserving the prefix cache."
> — `tools/memory_tool.py:686`

Same reasoning drives the timestamp being **date-only, not minute-precision**
(`system_prompt.py:525-530`), so the prompt is byte-identical all day.

**Design rule for us:** a learning written at 11:00 takes effect in the *next*
session, not mid-turn. Trying to be cleverer than this silently destroys cache
economics for every user in the office.

---

## 5. The unresolved question: forks don't flow back

The current distribution model is *fork*. Git forks are one-way by default.
If Ramesh in Accounts corrects a metric definition and it lands in his fork's
harness files, Priya in Sales never receives it. Learning would silo per person
— the exact opposite of the goal.

There are only two ways out, and they are not mutually exclusive:

- **(a) Git-native.** Shared clone + branches + PR, or forks + upstream PRs.
  Versioned, reviewable, offline-capable, free. Costs git literacy from
  non-technical staff and propagates only on `git pull`.
- **(b) Central store.** A shared learning service everyone's CLI reads and
  writes. We already run the infrastructure for this: five read-only MCP
  servers live on the VPS behind Traefik+LE at `/opt/jivo-mcp`
  (see memory `jivo-mcp-layer`). A sixth `jivo-learn` server is a small
  increment on proven ground. Instant propagation, no git literacy — but a
  *wrong* correction also propagates instantly, to everyone.

**Recommendation (confidence ~85%):** layer them, mirroring how Hermes
separates volatile memory from curated identity —

- **fast path** — corrections captured centrally, bounded, low-trust,
  visible to all immediately;
- **slow path** — a curation/promotion step lifts proven items into the
  repo's versioned rulebook, which is reviewed and permanent.

What keeps this below certainty: it depends on whether office staff are
always-online and whether anyone besides Daman can be expected to run `git`.
Both are facts only Daman has.

---

## Open questions

1. Do staff truly **fork**, or can they clone one shared repo and work on
   branches? This decides whether (b) is optional or mandatory.
2. Is the office always-online relative to the VPS?
3. Who is allowed to promote a candidate learning into canon — Daman only, or
   a team lead per department?
4. Do we need per-department isolation (Accounts rules invisible to Sales), or
   is one shared rulebook with role *tagging* enough?
