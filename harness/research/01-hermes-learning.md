# WORKER A — The Hermes LEARNING subsystem, reverse-engineered

**Investigator:** Worker A · **Date:** 2026-07-30
**Source of truth:** `~/.hermes/hermes-agent/` @ `70411a6152024ecb061972e778f900289c7ef046` (2026-07-29)
**Live profile inspected:** `~/.hermes/` (read-only; all personal content redacted to shapes/counts)
**Method:** full reads of the 8 named files + outward import-following via grep into
`run_agent.py`, `agent/turn_context.py`, `agent/turn_finalizer.py`, `agent/conversation_loop.py`,
`agent/tool_executor.py`, `agent/agent_init.py`, `agent/system_prompt.py`, `agent/prompt_builder.py`,
`agent/skill_utils.py`, `agent/codex_runtime.py`, `tools/skill_usage.py`, `tools/skill_manager_tool.py`,
`tools/skills_tool.py`, `tools/skill_provenance.py`, `hermes_cli/curator.py`, `gateway/run.py`.
No file under `~/.hermes/` was modified.

---

## 0. Read this first — three corrections to the brief's premise

The brief names 8 files as "the learning/curation core." Three of them are not part of the
learning loop, and the two most load-bearing files are not on the list. Correcting this up front
because building from the brief's file list would produce the wrong architecture.

| Brief's file | What it actually is | In the learning loop? |
|---|---|---|
| `agent/insights.py` (1099) | **Usage/cost analytics engine.** Reads `sessions` / `messages` / `session_model_usage` from `state.db` and renders a `/insights` report — tokens, USD cost, tools, platforms, streaks. Modelled on Claude Code's `/insights` (`agent/insights.py:1-17`). It has *nothing* to do with learnings; the word "insight" here means "usage insight." | ❌ No |
| `agent/learning_graph.py` (328) | **Visualisation data-builder** for the desktop/TUI "journey" panel. Assembles a node/edge payload from learned skills + memory chunks (`agent/learning_graph.py:1-14`). Read-only over the real stores. | ❌ Read-only view |
| `agent/learning_graph_render.py` (658) | **Terminal renderer** for that same payload (timeline bar chart, sparkline, style runs) (`agent/learning_graph_render.py:1-14`). | ❌ Read-only view |
| `agent/learning_mutations.py` (206) | **Manual edit/delete** of journey nodes from CLI/TUI/GUI (`hermes journey delete|edit`). User-driven, not agent-driven. | ⚠️ Human-in-the-loop edit surface |
| `agent/learn_prompt.py` (150) | The `/learn` slash-command prompt builder. | ✅ Explicit trigger |
| `agent/background_review.py` (1009) | **The learning engine.** Post-turn forked agent + the three extraction prompts. | ✅ Core |
| `agent/curator.py` (2018) | **The curation engine.** Lifecycle transitions + LLM consolidation. | ✅ Core |
| `tools/memory_tool.py` (1240) | Memory store (MEMORY.md / USER.md). | ✅ Storage |
| **MISSING: `tools/skill_usage.py` (1119)** | The lifecycle/telemetry state store — `.usage.json`, states, provenance, archive/restore. Curator reads and writes nothing else. | ✅ **Core** |
| **MISSING: `agent/prompt_builder.py` (2107) + `agent/system_prompt.py`** | The **entire retrieval/injection path**. Question 5 cannot be answered without these. | ✅ **Core** |
| **MISSING: `tools/skill_manager_tool.py`** | Every write guard that makes autonomous curation safe. | ✅ **Core** |

**The one-sentence architecture:** *A learning in Hermes is a **skill** (a `SKILL.md` package on
disk) or a **memory entry** (a `§`-delimited text chunk in `MEMORY.md`/`USER.md`). Nothing is
stored in SQLite. Nothing is embedded. Both stores are injected into the system prompt in full as a
frozen snapshot at session start, and both are written by a forked agent that runs after the turn
is delivered.*

---

# PART 1 — VERIFIED

Everything in this part is backed by code I read. Citations are `file:LINE`.

## 1. Data model

### 1a. There is no database. (VERIFIED)

```
$ sqlite3 ~/.hermes/state.db "SELECT name FROM sqlite_master WHERE type IN ('table','view')
    AND (name LIKE '%mem%' OR name LIKE '%skill%' OR name LIKE '%learn%'
      OR name LIKE '%insight%' OR name LIKE '%curat%' OR name LIKE '%review%');"
(0 rows)
```

`state.db` holds only `sessions`, `messages` (+ 2 FTS5 shadow sets), `session_model_usage`,
`state_meta`, `schema_version`, `async_delegations`, `compression_locks`, `delivery_obligations`,
`gateway_routing`. `kanban.db` holds only `tasks`, `task_comments`, `task_events`, `task_links`,
`task_runs`, `task_attachments`, `kanban_notify_subs`. **Zero learning tables in either.**

Live row counts (this profile): `sessions=40`, `messages=1433`, `session_model_usage=33`.

The only thing the learning system reads out of SQLite is the conversation transcript it replays
into the review fork — and even that is passed in memory as `messages_snapshot`, not queried.

### 1b. Memory node (VERIFIED)

Two flat files under `~/.hermes/memories/`, resolved per-profile at call time
(`tools/memory_tool.py:53-55`):

- `MEMORY.md` — "your personal notes" (environment facts, conventions, tool quirks)
- `USER.md` — "who the user is" (preferences, style, expectations)

The entire schema:

```python
# tools/memory_tool.py:67
ENTRY_DELIMITER = "\n§\n"
```

An entry is **plain text between `§` separators.** No id, no timestamp, no author, no type, no
tags, no links, no embedding vector. Identity is *the text itself*: `replace` and `remove` locate an
entry by a "short unique substring" (`tools/memory_tool.py:449-451`, `:520-521`), and the tool
errors out when a substring matches two distinct entries (`:480-489`).

Budgets are **characters, not tokens** — deliberately, because char counts are model-independent
(`tools/memory_tool.py:17`):

```python
# tools/memory_tool.py:165
def __init__(self, memory_char_limit: int = 2200, user_char_limit: int = 1375):
```

Overridable via `memory.memory_char_limit` / `memory.user_char_limit`
(`agent/agent_init.py:1626-1630`). The limit is over the **whole joined store**, not per entry.

**Live state (redacted):** `MEMORY.md` = 1,870 chars / 3 entries (85% of 2,200).
`USER.md` = 2,437 chars / 7 entries — **177% of its 1,375-char limit.** See §8 for why that
matters.

### 1c. Skill node (VERIFIED)

A skill is a **directory package**, not a file:

```
~/.hermes/skills/<category>/<skill-name>/
    SKILL.md            # YAML frontmatter + markdown body — the only required file
    references/*.md     # session-specific detail, condensed knowledge banks
    templates/*.<ext>   # starter files to copy and modify
    scripts/*.<ext>     # statically re-runnable actions
    assets/*
```

`SKILL.md` frontmatter fields actually consumed by the runtime
(`agent/prompt_builder.py:1425-1451`, `agent/learning_graph.py:41-74`):
`name`, `description`, `version`, `author`, `platforms[]`, `category`,
`related_skills[]`, `metadata.hermes.{tags,category,related_skills}`, plus conditional-activation
keys read by `extract_skill_conditions` — `requires_tools`, `requires_toolsets`,
`fallback_for_tools`, `fallback_for_toolsets` (`agent/prompt_builder.py:1496-1510`).

The **description is hard-truncated for the system-prompt index**:

```python
# agent/skill_utils.py:784
SKILL_PROMPT_DESC_LIMIT = 60
# agent/skill_utils.py:793-800
def extract_skill_description(frontmatter: Dict[str, Any]) -> str:
    desc = _normalize_skill_description(frontmatter)
    if not desc:
        return ""
    if len(desc) > SKILL_PROMPT_DESC_LIMIT:
        return desc[:SKILL_PROMPT_DESC_LIMIT - 3] + "..."
    return desc
```

So: **60-char budget, 57 chars of signal + `"..."`.** That resolves the apparent contradiction
between `learn_prompt.py` ("<=60 characters", `agent/learn_prompt.py:37`) and `curator.py`
("truncated to 57 chars", `agent/curator.py:425-428`) — both are describing the same constant from
different ends. (Commit `bc744d30e docs: document 57-char system prompt truncation…` confirms this
was deliberately documented.)

### 1d. Skill lifecycle record — `.usage.json` (VERIFIED)

Sidecar JSON at `~/.hermes/skills/.usage.json`, keyed by skill name
(`tools/skill_usage.py:85-86`). This is the *only* mutable state the curator reasons over.

```python
# tools/skill_usage.py:640-654
def _empty_record() -> Dict[str, Any]:
    return {
        "created_by": None,        # "agent" == curator-managed opt-in (NOT authorship)
        "use_count": 0,
        "view_count": 0,
        "last_used_at": None,      # ISO8601 UTC
        "last_viewed_at": None,
        "patch_count": 0,
        "last_patched_at": None,
        "created_at": _now_iso(),
        "state": STATE_ACTIVE,     # "active" | "stale" | "archived"
        "pinned": False,           # orthogonal opt-out from all auto-transitions
        "archived_at": None,
    }
```

States (`tools/skill_usage.py:53-56`): `active` → `stale` → `archived`. `pinned` is a boolean
orthogonal to state.

`created_by` is a **naming trap the code itself flags** (`tools/skill_usage.py:481-501`): the field
reads like provenance but is consumed as a *management-policy opt-in*. `created_by == "agent"`
means "the curator may touch this," not "an agent wrote this."

Derived fields added by `curated_report()` (`tools/skill_usage.py:1026-1055`):
`name`, `last_activity_at`, `activity_count`, `provenance`, `_persisted`.

```python
# tools/skill_usage.py:146-164 — creation time is deliberately EXCLUDED
def latest_activity_at(record):
    for key in ("last_used_at", "last_viewed_at", "last_patched_at"): ...
# tools/skill_usage.py:166-179
def activity_count(record):
    for key in ("use_count", "view_count", "patch_count"): ...
```

`provenance()` (`tools/skill_usage.py:1068-1079`) classifies `hub` | `bundled` | `agent` by
checking the hub-install list and `.bundled_manifest`.

**Live state (this profile):** 59 records · states `{active: 32, stale: 27}` ·
`created_by` `{None: 58, "agent": 1}` · `pinned: 0`. 127 `SKILL.md` files across 64 categories
are indexed in `.skills_prompt_snapshot.json`.

### 1e. Graph model — visualisation only (VERIFIED)

`agent/learning_graph.py` builds a node/edge payload for the desktop starmap and TUI `/journey`.
It is **derived on every call from the real stores** — nothing is persisted.

Node ids (`agent/learning_mutations.py:3-9`):
- skill → the skill name, e.g. `"debugging-hermes-desktop"`
- memory → `memory:<source>:<index>` where `source ∈ {memory, profile}` and `index` is the
  position in the *combined* card list (MEMORY.md cards first, then USER.md)

```python
# agent/learning_graph.py:28-38
@dataclass
class SkillNode:
    name: str; category: str; source: str = "profile"
    timestamp: Optional[int] = None; use_count: int = 0; state: str = "active"
    created_by: Optional[str] = None; pinned: bool = False
    related: list[str] = field(default_factory=list)
```

**Two edge types, both undirected, no weights, no semantics beyond these:**

1. **skill↔skill** — declared `related_skills`, deduped, kept only when *both* endpoints exist
   in the filtered node set (`agent/learning_graph.py:156-168`).
2. **memory→skill** — **derived by lexical overlap**, top-4 per memory card
   (`agent/learning_graph.py:227-245`):

```python
score = 0
if skill_name_lower in text:      # whole skill name appears in the card
    score += 6
score += len(tokens & text_tokens) # shared tokens, len>=3, [^a-z0-9]+ split
```

Node filter (`agent/learning_graph.py:262-267`): only `source != "base"` skills that are
`created_by == "agent"` **or** `use_count > 0`. Memory cards are split on `\n§\n` and **all** are
shown (`agent/learning_graph.py:193-220`), body truncated to 1200 chars.

**This graph is never fed back to the model.** It is a UI artefact. The `_memory_skill_edges`
lexical scorer is the closest thing to "semantic retrieval" anywhere in the subsystem, and it
drives pixels, not prompts.

---

## 2. Trigger — what causes a learning to be created

There are **four** distinct triggers. Two automatic, two explicit.

### 2a. Automatic: post-turn background review (the main one) — VERIFIED

Two independent counters, ORed. Both fire *after the user's response is delivered.*

**Memory trigger — turn-based**, evaluated at turn start (`agent/turn_context.py:582-590`):

```python
should_review_memory = False
if (agent._memory_nudge_interval > 0
        and "memory" in agent.valid_tool_names
        and agent._memory_store):
    agent._turns_since_memory += 1
    if agent._turns_since_memory >= agent._memory_nudge_interval:
        should_review_memory = True
        agent._turns_since_memory = 0
```

**Skill trigger — tool-iteration-based**, evaluated at turn end
(`agent/turn_finalizer.py:634-639`):

```python
# Check skill trigger NOW — based on how many tool iterations THIS turn used.
_should_review_skills = False
if (agent._skill_nudge_interval > 0
        and agent._iters_since_skill >= agent._skill_nudge_interval
        and "skill_manage" in agent.valid_tool_names):
    _should_review_skills = True
    agent._iters_since_skill = 0
```

The iteration counter increments once per tool-calling loop iteration
(`agent/conversation_loop.py:1323-1327`) and — critically — **resets to zero whenever the model
actually calls `skill_manage` or `memory`** (`agent/tool_executor.py:476-479`):

```python
if function_name == "memory":
    agent._turns_since_memory = 0
elif function_name == "skill_manage":
    agent._iters_since_skill = 0
```

That is the anti-thrash mechanism: a session that is already writing learnings never gets a
review fork on top.

**The spawn** (`agent/turn_finalizer.py:649-658`):

```python
# Background memory/skill review — runs AFTER the response is delivered
# so it never competes with the user's task for model attention.
if final_response and not interrupted and (_should_review_memory or _should_review_skills):
    try:
        agent._spawn_background_review(
            messages_snapshot=list(messages),
            review_memory=_should_review_memory,
            review_skills=_should_review_skills,
        )
    except Exception:
        pass  # Background review is best-effort
```

→ `run_agent.py:1721-1748`, which builds the thread target from
`spawn_background_review_thread` and starts a **daemon thread** named `bg-review`, wrapping the
target in `propagate_context_to_thread` so the active profile follows it (`run_agent.py:1745-1748`).

Note the three gates: a review never runs on an **interrupted** turn, never on a turn with **no
final response**, and never when the corresponding tool isn't in `valid_tool_names`.

A parallel implementation exists for the Codex/Responses backend
(`agent/codex_runtime.py:811-857`) — same counters, same spawn, different turn plumbing.

**Nudge terminology warning:** the config keys are called `nudge_interval` /
`creation_nudge_interval`, but in this checkout they inject **no text into the live conversation**.
`agent/turn_context.py:306` and `:579` both explicitly say "no nudge injection". The counters do
exactly one thing: gate the fork.

**Defaults & live config:**

| Knob | Code default | Live value (`~/.hermes/config.yaml`) |
|---|---|---|
| `memory.nudge_interval` | 10 (`agent/agent_init.py:1609`) | **10** user turns |
| `skills.creation_nudge_interval` | 10 (`agent/agent_init.py:1709`) | **15** tool iterations |
| `memory.memory_enabled` | `False` (`agent/agent_init.py:1621`) | `true` |
| `memory.user_profile_enabled` | `False` | `true` |

### 2b. Automatic: the curator (weekly, inactivity-gated) — VERIFIED

`maybe_run_curator()` (`agent/curator.py:2000-2018`) is the public entrypoint. Gates:

```python
if not should_run_now():            # enabled AND not paused AND last_run older than interval
    return None
if idle_for_seconds is not None:
    if idle_for_seconds < get_min_idle_hours() * 3600.0:
        return None
return run_curator_review(on_summary=on_summary)
```

**First-run behaviour is deliberately deferred** (`agent/curator.py:259-276`): with no
`last_run_at`, it *seeds* the timestamp to now, writes the summary
`"deferred first run — curator seeded, will run after one interval…"`, and returns `False`. A
fresh install never curates on the first tick after `hermes update`.

Call site — the gateway housekeeping loop (`gateway/run.py:24641-24652`):

```python
# Curator — piggy-back on the housekeeping loop so long-running
# gateways get weekly skill maintenance without needing restarts.
if tick_count % CURATOR_EVERY == 0:
    from agent.curator import maybe_run_curator
    maybe_run_curator(idle_for_seconds=float("inf"),
                      on_summary=lambda msg: logger.info("curator: %s", msg))
```

(`idle_for_seconds=float("inf")` means the gateway path bypasses the idle gate entirely — the
interval gate is the only real one there.)

### 2c. Explicit: `/learn` — VERIFIED

User-typed. `hermes_cli/cli_commands_mixin.py:1775-1799` splits the command, calls
`build_learn_prompt(user_request)`, and **pushes the result onto the live agent's input queue as a
normal user turn** (`self._pending_input.put(msg)`). Same three surfaces:
- CLI: `hermes_cli/cli_commands_mixin.py:1785-1791`
- Gateway: `gateway/run.py:12283-12299`
- TUI gateway RPC: `tui_gateway/methods_tools.py:585-587`

No separate model call, no distillation engine — the *live* agent does the work with its existing
tools (`agent/learn_prompt.py:18-22`).

### 2d. Explicit: the model just calls the tool — VERIFIED

`memory` and `skill_manage` are ordinary tools available in every foreground turn. The system
prompt actively pushes both: `MEMORY_GUIDANCE` (`agent/prompt_builder.py:160-183`) and
`SKILLS_GUIDANCE` (`agent/prompt_builder.py:193+`), plus the mandatory skills header
(`agent/prompt_builder.py:1755-1783`) which ends with *"After difficult/iterative tasks, offer to
save as a skill."*

Foreground writes are marked with write-origin `"foreground"` and are therefore **user-owned** —
the curator can never touch them (see §6c).

---

## 3. Extraction — the actual prompts

### 3a. The three background-review prompts (VERIFIED)

Selected by which triggers fired (`agent/background_review.py:989-994`):

```python
if review_memory and review_skills: prompt = _COMBINED_REVIEW_PROMPT
elif review_memory:                 prompt = _MEMORY_REVIEW_PROMPT
else:                               prompt = _SKILL_REVIEW_PROMPT
```

**`_MEMORY_REVIEW_PROMPT` — verbatim (`agent/background_review.py:170-179`):**

```
Review the conversation above and consider saving to memory if appropriate.

Focus on:
1. Has the user revealed things about themselves — their persona, desires,
   preferences, or personal details worth remembering?
2. Has the user expressed expectations about how you should behave, their work
   style, or ways they want you to operate?

If something stands out, save it using the memory tool. If nothing is worth
saving, just say 'Nothing to save.' and stop.
```

**`_SKILL_REVIEW_PROMPT` (`agent/background_review.py:181-295`)** is the interesting one — 115
lines of prompt engineering. Load-bearing excerpts, verbatim:

> "Review the conversation above and update the skill library. Be **ACTIVE** — most sessions
> produce at least one skill update, even if small. **A pass that does nothing is a missed learning
> opportunity, not a neutral outcome.**"

> "Target shape of the library: CLASS-LEVEL skills, each with a rich SKILL.md and a `references/`
> directory for session-specific detail. Not a long flat list of narrow one-session-one-skill
> entries."

> "Signals to look for (any one of these warrants action):
> • User corrected your style, tone, format, legibility, or verbosity. Frustration signals like
> 'stop doing X', 'this is too verbose', 'don't format like this', 'why are you explaining',
> 'just give me the answer', 'you always do Y and I hate it', or an explicit 'remember this' are
> **FIRST-CLASS skill signals, not just memory signals.** Update the relevant skill(s) to embed the
> preference so the next session starts already knowing.
> • User corrected your workflow, approach, or sequence of steps. Encode the correction as a
> pitfall or explicit step in the skill that governs that class of task.
> • Non-trivial technique, fix, workaround, debugging path, or tool-usage pattern emerged…
> • A skill that got loaded or consulted this session turned out to be wrong, missing a step, or
> outdated. **Patch it NOW.**"

The **four-rung preference ladder** (`:206-244`) — this is the single most portable idea in the
whole system:

> 1. **UPDATE A CURRENTLY-LOADED SKILL.** Look back through the conversation for skills the user
>    loaded via `/skill-name` or you read via `skill_view`. If any covers the territory, PATCH that
>    one first. It is the skill that was in play, so it's the right one to extend.
> 2. **UPDATE AN EXISTING UMBRELLA** (via `skills_list` + `skill_view`). Add a subsection, a
>    pitfall, or broaden a trigger.
> 3. **ADD A SUPPORT FILE** under an existing umbrella — `references/<topic>.md` (session-specific
>    detail or condensed knowledge banks), `templates/<name>.<ext>` (starter files to copy),
>    `scripts/<name>.<ext>` (statically re-runnable actions). "The umbrella's SKILL.md should gain
>    a one-line pointer to any new support file so future agents know it exists."
> 4. **CREATE A NEW CLASS-LEVEL UMBRELLA SKILL** when no existing skill covers the class. "The name
>    MUST NOT be a specific PR number, error string, feature codename, library-alone name, or
>    'fix-X / debug-Y / audit-Z-today' session artifact. **If the proposed name only makes sense for
>    today's task, it's wrong** — fall back to (1), (2), or (3)."

The **memory-vs-skill boundary** (`:245-251`), stated three separate times across the prompts:

> "Memory captures 'who the user is and what the current situation and state of your operations
> are'; skills capture 'how to do this class of task for this user'. When they complain about how
> you handled a task, the skill that governs that task needs to carry the lesson."

The **negative list** (`:271-290`) — what NOT to capture, with the stated reason ("these become
persistent self-imposed constraints that bite you later when the environment changes"):

> • Environment-dependent failures: missing binaries, fresh-install errors, post-migration path
>   mismatches, 'command not found', unconfigured credentials, uninstalled packages. "The user can
>   fix these — they are not durable rules."
> • Negative claims about tools or features ('browser tools do not work', 'X tool is broken').
>   "**These harden into refusals the agent cites against itself for months after the actual problem
>   was fixed.**"
> • Session-specific transient errors that resolved before the conversation ended. "If retrying
>   worked, the lesson is the retry pattern, not the original failure."
> • One-off task narratives. "A user asking 'summarize today's market' or 'analyze this PR' is not
>   a class of work that warrants a skill."
> • "If a tool failed because of setup state, capture the FIX (install command, config step, env
>   var to set) under an existing setup or troubleshooting skill — never 'this tool does not work'
>   as a standalone constraint."

And the escape hatch (`:291-294`): *"'Nothing to save.' is a real option but should NOT be the
default."*

`_COMBINED_REVIEW_PROMPT` (`:297-387`) is a merge of the two with the same ladder and the same
negative list.

### 3b. The `/learn` prompt (VERIFIED)

`build_learn_prompt(user_request)` (`agent/learn_prompt.py:99-150`) returns a single string that is
fed to the *live* agent as a normal turn. Structure:

```
[/learn] The user wants you to learn a reusable skill from the request below, and save it.

THE REQUEST:
{req}

The request is open-ended and may mix two kinds of content, in any order: SOURCES to gather
(directories, file paths, URLs, "what we just did", pasted notes) AND REQUIREMENTS that shape the
skill … Treat EVERY part of the request as load-bearing. In particular, prose that comes after a
path or link is NOT incidental — it is the user telling you what they want from that source. …
Never fetch the first source and ignore the rest.

Do this:
1. Gather every source the user named, using the tools you already have — `read_file`/`search_files`
   for local files or directories, `web_extract` for URLs, the current conversation history …
1b. Apply every requirement, focus, and constraint in the request to the skill you author …
2. Author ONE SKILL.md and save it with the `skill_manage` tool (action="create") …

{_AUTHORING_STANDARDS}

When done, tell the user the skill name, its category, and a one-line summary of what it captured.
```

Empty argument defaults to *"the workflow we just went through in this conversation — review the
steps taken and distill them into a reusable skill"* (`agent/learn_prompt.py:112-117`).

`_AUTHORING_STANDARDS` (`agent/learn_prompt.py:30-96`) is a 67-line house-style block: frontmatter
rules, the mandated 8-section body order (`When to Use` → `Prerequisites` → `How to Run` →
`Quick Reference` → `Procedure` → `Pitfalls` → `Verification`), Hermes-tool framing ("say
`read_file` not cat/head/tail, `search_files` not grep/rg/find/ls, `patch` not sed/awk"), and a
quality bar: *"NEVER invent flags, paths, or APIs — if you didn't see it in the source, don't write
it"*, *"~100 lines for a simple skill, ~200 for a complex one"*, *"Don't write a
router/index/hub skill that only points at other skills."*

Note the privacy rule at `agent/learn_prompt.py:49-53`: `author:` is always the literal `Hermes` —
"NEVER fill it from the host environment … Skills get shared and published, so an
environment-derived name is a privacy leak the user never opted into."

### 3c. Which model, sync or async (VERIFIED)

**Background review — async daemon thread, parent's model by default.**

```python
# agent/background_review.py:34-42 (design comment)
# The review fork runs on the MAIN model by default ("auto"), replaying the
# full conversation — already warm in the prompt cache, so cheap cache reads.
# … A different model cannot reuse the parent's cache (different key), so the
# fork is cold regardless … So when (and only when) routed to a different model,
# we replay a compact DIGEST to minimise cold-written tokens.
```

`_resolve_review_runtime` (`:46-110`) inherits the parent's provider/model/api_key/base_url/
api_mode/credential_pool/request_overrides verbatim unless
`auxiliary.background_review.{provider,model}` names a *different* concrete model.

The **cache-parity engineering** is extensive and worth copying conceptually:

| What is pinned | Line | Why |
|---|---|---|
| `_cached_system_prompt = agent._cached_system_prompt` | `:798` | byte-identical prefix → cache hit (PR #17276, *"~26% end-to-end cost reduction on Sonnet 4.5"*) |
| `enabled_toolsets` / `disabled_toolsets` inherited | `:742-743` | `tools[]` byte-identical (Anthropic's cache key includes it) |
| `reasoning_config` inherited (same-model path only) | `:728-729` | `thinking` presence namespaces the cache key |
| `session_start`, `session_id` pinned | `:806-807` | any re-render path stays byte-identical |
| `_skip_mcp_refresh = True` | `:755` | late-connecting MCP tools would break `tools[]` parity |

Routed (different-model) path replays `_digest_history(snapshot, tail=24)`
(`agent/background_review.py:122-163`): last 24 messages verbatim (extended forward if the window
would open on a `tool` role), everything older collapsed into one synthetic **user**-role digest of
`USER: {text[:300]}` / `ASSISTANT[tools: …]` / `ASSISTANT: {text[:200]}` lines.

`max_iterations=16` (`:731`). Tool whitelist is `{skills}` plus `{memory}` when
`memory_enabled or user_profile_enabled` (`:833-853`) — everything else is denied at dispatch with
*"Background review denied non-whitelisted tool: {tool_name}."*

**Curator LLM pass — its own aux slot, `max_iterations=9999`.**
`_resolve_review_runtime` (`agent/curator.py:1760-1805`) precedence:
1. `auxiliary.curator.{provider,model}` (canonical aux-task slot)
2. legacy `curator.auxiliary.{provider,model}` (logs a migration warning, `:1792-1795`)
3. main `model.{provider, default|model}`

Live config: `auxiliary.curator = {provider: auto, model: '', timeout: 600}` → falls through to the
main chat model.

```python
# agent/curator.py:1926-1936
# Umbrella-building over a large skill collection is worth a high iteration
# ceiling — the pass typically takes 50-100 API calls against hundreds of
# candidate skills.
max_iterations=9999, quiet_mode=True, platform="curator",
skip_context_files=True, skip_memory=True,
```

Runs in a daemon thread named `curator-review` unless `synchronous=True`
(`agent/curator.py:1747-1751`).

---

## 4. Storage — write paths and concurrency

### 4a. Memory: file lock + atomic rename + a drift guard (VERIFIED)

Full write sequence for `add` (`tools/memory_tool.py:390-447`):

```
1. strip + reject empty
2. _scan_memory_content(content)          -> threat_patterns scope="strict"; reject on hit
3. with _file_lock(path):                 -> exclusive flock on a SEPARATE  <file>.lock
4.     _reload_target(target, skip_drift=True)
          -> _read_raw_checked() ; if the file EXISTS but is unreadable -> _READ_FAILED -> ABORT
          -> parse on "\n§\n", strip, drop empties, dict.fromkeys() dedupe
5.     reject exact duplicate  (idempotent success)
6.     char-budget check on the FINAL joined string
7.     append, save_to_disk() -> _write_file() -> atomic_write_text(tmp + os.replace)
```

The lock is on a **sidecar `.lock` file, not the memory file**, precisely so the memory file can
still be replaced by `os.replace()` (`tools/memory_tool.py:280-284`). fcntl on POSIX, `msvcrt` on
Windows, silent no-op if neither is importable (`:289-291`).

Three hard-won safety properties, each with the incident encoded in the comment:

**(i) Unreadable ≠ empty** (`tools/memory_tool.py:125`, `:749-771`, `:128-145`).
A file that exists but can't be read (transient lock, permission blip, invalid UTF-8) returns the
`_READ_FAILED` sentinel and **aborts the write**. Treating it as `[]` would rewrite the whole file
down to one entry. Note that `add` is the exposed case: it skips the drift guard because appending
is safe, *"but that reasoning only holds when the reload actually saw the file."*

**(ii) External-drift guard** (`_detect_external_drift`, `:807-861`). Two signals:
round-trip mismatch (`raw.strip() != "\n§\n".join(parsed)`), or any single parsed entry longer than
the store's whole-file limit — which means an external writer (patch tool, shell append, manual
edit, sister session) appended free-form content. On drift: snapshot to `<file>.bak.<unix-ts>` and
**refuse the mutation** with a remediation message (`_drift_error`, `:91-118`). `replace` / `remove`
/ `apply_batch` enforce it; `add` skips it.

**(iii) Single read, single snapshot** (`:350-357`) — the drift check and the entry parse are both
derived from the *same* raw bytes, because an earlier version re-read the file for the drift check
and treated a failed second read as "no drift", opening a lost-update window.

**Injection defence at both ends.** Content is scanned on write (`:86-88`) *and* every entry is
re-scanned at snapshot-build time (`_sanitize_entries_for_snapshot`, `:242-276`). A hit replaces
the entry **in the system-prompt snapshot only** with
`[BLOCKED: MEMORY.md entry contained threat pattern(s): …]`; the raw text stays in live state so
the user can see and delete it. Rationale at `:75-81`: memory enters the system prompt as a frozen
snapshot, so a poisoned entry persists for the whole session and across sessions.

**Batch writes are all-or-nothing** (`apply_batch`, `:562-669`): ops are applied to a working copy,
the char budget is checked **only against the final state**, and nothing is written if any op fails.
This exists to let the model free space and add in one call rather than a multi-turn
consolidate-then-retry dance.

**Anti-thrash on failure** (`_consolidation_failure`, `:180-201`): after
`_MAX_CONSOLIDATION_FAILURES_PER_TURN = 3` failed at-capacity attempts in one turn, the tool
returns a **terminal** result telling the model to stop retrying and answer the user — *"a failed
memory side effect must never block the turn's reply."* Reset on any success (`:702-706`).

**Optional approval gate** (`_apply_write_gate`, `:911-965`; `memory.write_approval`, live = `false`):
when on, a write is either blocked or **staged** as a pending record that a human approves later via
`/memory approve` → `apply_memory_pending` (`:1130-1148`).

### 4b. Skills: directory moves + atomic JSON sidecar (VERIFIED)

- Skill content: ordinary files under `~/.hermes/skills/<category>/<name>/`, written through
  `skill_manage` (`create|edit|patch|write_file|remove_file|delete`).
- Telemetry: `.usage.json`, guarded by `_usage_file_lock()` on `.usage.json.lock`
  (`tools/skill_usage.py:90-123`) and written via mkstemp → `json.dump` → `flush` → `fsync` →
  `os.replace` (`save_usage`, `:676-698`). **Every counter bump is best-effort** — a broken sidecar
  never breaks the underlying tool call (`:1-24`).
- Archive = `Path.rename()` of the whole directory into `~/.hermes/skills/.archive/<name>`, with a
  timestamp suffix on collision and a `shutil.move` fallback for cross-device
  (`archive_skill`, `tools/skill_usage.py:852-910`). Category nesting is **flattened**; restore does
  not reconstruct it (`restore_skill`, `:913+`).
- Archiving a bundled built-in also adds it to a **suppression list** so `hermes update`'s re-seeder
  leaves it archived (`:908-909`).
- Curator scheduler state: `~/.hermes/skills/.curator_state` via `atomic_json_write`
  (`agent/curator.py:85-121`).
- Per-run reports: `~/.hermes/logs/curator/<YYYYMMDD-HHMMSS>/` containing `run.json` (full
  fidelity), `REPORT.md` (human), and `cron_rewrites.json` (only when a cron job was touched)
  (`agent/curator.py:577-596`, `:1256-1281`). Collisions within the same second get a `-2` suffix
  (`:1119-1123`).
- Pre-run **snapshot backup** of the whole skills tree before any mutating curator run
  (`agent/curator.py:1551-1558` → `agent/curator_backup.py:216`), `keep: 5` by default
  (`curator_backup.py:57`; live config `curator.backup.{enabled: true, keep: 5}`).

**Cache invalidation:** any skill mutation calls
`clear_skills_system_prompt_cache(clear_snapshot=True)` (`tools/skill_manager_tool.py:1435`,
`agent/learning_mutations.py:200-206`), which clears both the in-process LRU and the on-disk
`.skills_prompt_snapshot.json` (`agent/prompt_builder.py:1350-1359`).

---

## 5. Retrieval + injection — how a learning gets back into context

**This is the most important answer, so, plainly: there is no retrieval.** There is no embedding,
no vector store, no similarity search, no relevance filter over learnings. I grepped
`tools/memory_tool.py`, `agent/prompt_builder.py` and `agent/system_prompt.py` for
`embed|vector|cosine|faiss|sentence_transform` — zero hits in any injection path. Both stores go in
**whole, every session, as static text**, and the budget is enforced at *write* time so the injected
text can never grow past the cap.

### 5a. Memory — full-text, frozen at session start (VERIFIED)

```python
# tools/memory_tool.py:11-14 (module docstring)
# Both are injected into the system prompt as a frozen snapshot at session start.
# Mid-session writes update files on disk immediately (durable) but do NOT change
# the system prompt -- this preserves the prefix cache for the entire session.
# The snapshot refreshes on the next session start.
```

`load_from_disk()` (`:203-240`) reads both files, dedupes, sanitises for threats, and freezes
`_system_prompt_snapshot = {"memory": …, "user": …}`. `format_for_system_prompt(target)`
(`:682-693`) returns *only* that snapshot — never live state.

Rendered block (`_render_block`, `:731-747`):

```
══════════════════════════════════════════════
MEMORY (your personal notes) [85% — 1,870/2,200 chars]
══════════════════════════════════════════════
<entry 1>
§
<entry 2>
…
```

The **usage percentage is inside the injected header** — a nice trick: the model can see its own
memory pressure without a tool call.

Injection point — the **volatile tier** of the layered system prompt
(`agent/system_prompt.py:499-511`):

```python
# ── Volatile tier (changes per session/turn — never cached) ───
volatile_parts: List[str] = []
if agent._memory_store:
    if agent._memory_enabled:
        mem_block = agent._memory_store.format_for_system_prompt("memory")
        if mem_block: volatile_parts.append(mem_block)
    if agent._user_profile_enabled:
        user_block = agent._memory_store.format_for_system_prompt("user")
        if user_block: volatile_parts.append(user_block)
```

Prompt layer order (`agent/system_prompt.py:9-14`, `:471-541`):

```
stable   : identity (SOUL.md or DEFAULT_AGENT_IDENTITY) + tool/memory/skills GUIDANCE
           + the skills index
context  : cwd-dependent context files (AGENTS.md, .cursorrules, SOUL.md)
volatile : MEMORY.md block, USER.md block, external-memory-provider block,
           "Conversation started: <date>" + session/model/provider/platform
```

Even the timestamp is **date-only, not minute-precision**, "so the system prompt is byte-stable for
the full day" (`agent/system_prompt.py:527-533`). The whole assembled string is cached on
`agent._cached_system_prompt` and only rebuilt after compression.

**Token budget for memory:** 2,200 + 1,375 = 3,575 characters ≈ **~900 tokens**, hard-capped. That
is the entire memory footprint, forever, regardless of how long the user has been using Hermes.

### 5b. Skills — a name+description index, then progressive disclosure (VERIFIED)

`build_skills_system_prompt()` (`agent/prompt_builder.py:1531-1792`) renders a category-grouped
index. The header is *mandatory-load* framing, verbatim (`:1755-1783`):

```
## Skills (mandatory)
Before replying, scan the skills below. If a skill matches or is even partially relevant to your
task, you MUST load it with skill_view(name) and follow its instructions. Err on the side of
loading — it is always better to have context you don't need than to miss critical steps,
pitfalls, or established workflows. … Skills also encode the user's preferred approach,
conventions, and quality standards … load them even for tasks you already know how to do, because
the skill defines how it should be done here.
…
If a skill has issues, fix it with skill_manage(action='patch').
After difficult/iterative tasks, offer to save as a skill. If a skill you loaded was missing steps,
had wrong commands, or needed pitfalls you discovered, update it before finishing.

<available_skills>
  <category>: <category description from DESCRIPTION.md>
    - <name>: <description truncated to 60 chars>
    …
</available_skills>

Only proceed without loading a skill if genuinely none are relevant to the task.
```

**The three-rung disclosure ladder** (VERIFIED — `tools/skills_tool.py:1700-1716`):

| Rung | Cost | What you get |
|---|---|---|
| 1. system-prompt index | always paid | `name` + ≤60-char description |
| 2. `skill_view(name)` | on demand | full `SKILL.md` **+ a `linked_files` dict** listing available `references/`, `templates/`, `scripts/` |
| 3. `skill_view(name, file_path="references/x.md")` | on demand | that one support file |

That is why `_SKILL_REVIEW_PROMPT` rung 3 insists the umbrella's SKILL.md gains "a one-line pointer
to any new support file" — the pointer *is* the index for rung 3.

**Measured cost of rung 1 on this live profile:** 127 skills, 64 categories → **191 index lines,
11,255 chars ≈ 2,800 tokens**, plus ~1.5 KB of header instructions. **53 of 127 descriptions (42%)
are ≥60 chars and are silently truncated.** That is the concrete cost of the "always-on index"
design and the concrete reason the 60-char rule is enforced so aggressively in both authoring
prompts.

**No hard token budget exists for the index.** The only pressure valves are:

1. **Two-layer cache** — in-process LRU capped at 8 entries keyed by
   `(skills_dir, external_dirs, tools, toolsets, platform, disabled, compact_categories)`
   (`agent/prompt_builder.py:1340-1342`, `:1562-1580`); disk snapshot
   `.skills_prompt_snapshot.json` validated by an mtime/size manifest, surviving process restarts
   (`:1346-1348`, `:1387-1456`). Live snapshot: 72 KB, 154 manifest entries.
2. **Filters that hide skills from the index** (never from `skill_view`):
   platform match, per-platform disabled list, environment gate, and conditional activation —
   `requires_tools` / `requires_toolsets` (hide when absent) and
   `fallback_for_tools` / `fallback_for_toolsets` (hide when the *primary* is present)
   (`_skill_should_show`, `agent/prompt_builder.py:1484-1512`).
3. **Category demotion** via `compact_categories` (from the coding posture): a demoted category
   collapses to one `category [names only]: a, b, c` line. Crucially, names are **never** removed
   (`:1708-1720`):

> "NEVER remove entries entirely: agent-created skills are the model's project memory, and models
> don't reach for `skills_list` to rediscover what the index stops showing them."

### 5c. What is NOT injected (VERIFIED)

- The learning **graph** — UI only, never enters a prompt.
- The **curator's reports** — `~/.hermes/logs/curator/*/REPORT.md`, surfaced to the human via
  `hermes curator status`, not to the model.
- Past **session transcripts** — reachable only via the `session_search` tool over the
  `messages_fts` FTS5 index (`tools/session_search_tool.py:829`). `MEMORY_GUIDANCE` explicitly
  routes task-progress questions there instead of memory
  (`agent/prompt_builder.py:171-174`).

---

## 6. Curation — what `curator.py` actually curates

**It curates skills only. Memory is never curated by anything but the model itself.** There is no
decay, no dedupe beyond exact-string rejection, no merge, no supersession, and no expiry for memory
entries. The only forces acting on memory are: the char cap forcing consolidation at write time,
the model's own `replace`/`remove` calls, and manual `hermes journey edit|delete`.

### 6a. Pass 1 — deterministic inactivity transitions, no LLM (VERIFIED)

`apply_automatic_transitions()` (`agent/curator.py:305-383`). Thresholds
(`agent/curator.py:70-78`, all live-confirmed in `config.yaml`):

```python
DEFAULT_INTERVAL_HOURS     = 24 * 7   # 168  — live: 168
DEFAULT_MIN_IDLE_HOURS     = 2        #      — live: 2
DEFAULT_STALE_AFTER_DAYS   = 30       #      — live: 30
DEFAULT_ARCHIVE_AFTER_DAYS = 90       #      — live: 90
DEFAULT_CONSOLIDATE        = False    #      — live: false
# prune_builtins defaults True (curator.py:192-201) — live: true
```

The state machine, keyed on `anchor = last_activity_at or created_at or now`:

```
anchor <= now-90d  and state != archived   -> archive_skill()          [counts.archived]
anchor <= now-30d  and state == active     -> set_state(STALE)         [counts.marked_stale]
anchor >  now-30d  and state == stale      -> set_state(ACTIVE)        [counts.reactivated]
```

Four exemptions, in evaluation order:

1. **`pinned`** → `continue` (`:331-332`).
2. **Referenced by any cron job**, including paused/disabled ones → `continue` (`:340-341`).
   The reason (`:334-339`): the scheduler only bumps usage when a job *fires*, so jobs that fire
   less often than `archive_after_days`, paused jobs, and far-future one-shots would have their
   skills aged out from under them.
3. **First sight, no persisted record** (`_persisted == False`) → `seed_record_if_missing()` and
   defer (`:343-348`). This anchors a newly-eligible built-in's clock to *now*, not to epoch — so
   flipping `prune_builtins` on doesn't mass-archive on the first pass.
4. **Never-used grace floor** (`:361-369`):

```python
# A use=0 skill is absence of evidence, not evidence of staleness — a skill
# created recently may simply not have had its trigger come up yet.
never_used = int(row.get("use_count", 0) or 0) == 0
if never_used and anchor > stale_cutoff:
    ...  # younger than the stale window — leave it alone entirely
    continue
```

Plus a hard allowlist that no path may archive: `PROTECTED_BUILTIN_SKILLS = {"plan"}`
(`tools/skill_usage.py:65-68`) — because it backs the `/plan` slash command and archiving it
"turns its slash command into 'Unknown command' with no signal to the user."

**This pass runs on every enabled curator tick, always.** Live proof: `.curator_state` shows
`run_count: 12`, last run `2026-07-27`, summary
`"auto: 26 marked stale; llm: skipped (consolidation off)"` — and `.usage.json` correspondingly
holds 27 stale records.

### 6b. Pass 2 — LLM umbrella consolidation (OFF by default) (VERIFIED)

Gated by `curator.consolidate`, **default `False`** (`agent/curator.py:76-78`, `:204-217`) — live
value `false`. When off, `run_curator_review` skips the fork entirely: *"no consolidation, no
umbrella-building, no aux-model cost"* (`:1594-1639`). Overridable per-invocation with
`hermes curator run --consolidate`.

`CURATOR_REVIEW_PROMPT` (`agent/curator.py:417-570`). Its thesis, verbatim:

> "This is an **UMBRELLA-BUILDING consolidation pass, not a passive audit and not a
> duplicate-finder.** The goal of the skill collection is a LIBRARY OF CLASS-LEVEL INSTRUCTIONS AND
> EXPERIENTIAL KNOWLEDGE. **A collection of hundreds of narrow skills where each one captures one
> session's specific bug is a FAILURE of the library — not a feature.** … One broad umbrella skill
> with labeled subsections beats five narrow siblings for discoverability, not the other way
> around."

Anti-rationalisation rules, verbatim (`:452-464`):

> **4.** "DO NOT use usage counters as a reason to skip consolidation. … Judge overlap on CONTENT,
> not on use_count. 'use=0' is not evidence a skill is valuable; it's absence of evidence either
> way. Corollary: 'use=0' is ALSO not a reason to PRUNE a skill."
> **5.** "DO NOT reject consolidation on the grounds that 'each skill has a distinct trigger'.
> Pairwise distinctness is the wrong bar. The right bar is: **'would a human maintainer write this
> as N separate skills, or as one skill with N labeled subsections?'** When the answer is the
> latter, merge."

Method (`:465-498`): find **prefix clusters** ("Expect 10-25 clusters"), then per cluster pick one
of three consolidation modes — (a) merge into an existing umbrella, (b) create a new umbrella
`SKILL.md`, (c) demote to `references/` / `templates/` / `scripts/` — then archive the siblings.
Then *"Iterate. … Don't stop after 3 merges."* And a productivity floor (`:545-548`):
*"If you end the pass with fewer than 10 archives, you stopped too early."*

**Package-integrity rule** (`:499-517`) — the sharpest failure mode it guards:

> "If the source skill has support files OR SKILL.md contains relative links such as
> `references/...`, `templates/...`, `scripts/...`, or `assets/...`, **DO NOT flatten only SKILL.md**
> into `<umbrella>/references/<old>.md`. … Never leave archived/demoted instructions pointing at
> files that were left behind under the old skill directory."

**Required structured output** (`:549-569`) — every archived skill must appear in exactly one list:

```yaml
consolidations:
  - from: <old-skill-name>
    into: <umbrella-skill-name>
    reason: <one short sentence — why merged, not just 'similar'>
prunings:
  - name: <skill-name>
    reason: <one short sentence — why archived with no merge target>
```

**Dry-run** prepends `CURATOR_DRY_RUN_BANNER` (`:390-414`), which enumerates the exact forbidden
calls (`skill_manage` patch/create/delete/write_file/remove_file, `terminal` mv into `.archive/`)
and says *"Your output IS the deliverable."* A dry run also does **not** bump `last_run_at` or
`run_count` — a preview must not push the next real pass out (`:1576-1583`).

### 6c. How consolidated-vs-pruned is decided — a 4-signal reconciler (VERIFIED)

This is the most sophisticated piece of the file and the part I'd steal wholesale. Four independent
signals, reconciled by explicit precedence in `_reconcile_classification`
(`agent/curator.py:874-1001`):

| Rank | Signal | Source | Line |
|---|---|---|---|
| 1 | `absorbed_into=<x>` passed to `skill_manage(action=delete)` **at the moment of deletion**, and `<x>` exists post-run | `_extract_absorbed_into_declarations` | `:820-871` |
| 1b | `absorbed_into=""` — explicit prune declaration | same | `:934-941` |
| 2 | The model's post-hoc YAML block, if its `into:` target exists | `_parse_structured_summary` | `:739-817` |
| 3 | Tool-call audit heuristic: some *other* surviving skill's `file_path`/`content`/`new_string` referenced the removed skill's name | `_classify_removed_skills` | `:617-736` |
| 4 | Fallback → `pruned` with `source: "no-evidence fallback"` | | `:993-999` |

Rank-2 **hallucination detection is explicit**: if the model claims `into: Y` but `Y` doesn't exist
post-run, the claim is downgraded and the heuristic's finding is used instead, with the report
printing *"⚠ The curator's summary named `Y` as the umbrella but that skill doesn't exist post-run"*
(`:1357-1362`).

The rank-3 heuristic avoids two classic false positives (`:696-716`): `file_path` matches require a
**complete path component** (so `"api"` doesn't match `references/api-design.md` —
`_needle_in_path_component`, `:599-614`), and content matches use `\b` word boundaries (so
`"test"` doesn't match `"latest"`).

And the enforcement that makes rank 1 real (`tools/skill_manager_tool.py:463-510`):

```python
# _curator_consolidation_delete_guard — fail CLOSED
# "A delete with no forwarding target … is the fail-open behavior reported in #29912: the
#  consolidation pass archived whole clusters of active skills with zero verified
#  consolidations (consolidated_this_run == 0), leaving active automations pointing at
#  names that no longer resolve."
declared = isinstance(absorbed_into, str) and absorbed_into.strip()
if declared: return None
return {"success": False, "error": "Refusing background curator delete …", "_fail_closed": True}
```

**Consolidation rewrites cron references.** When X is absorbed into Y, every cron job listing X is
rewritten in place (`agent/curator.py:1191-1222` → `cron.jobs.rewrite_skill_refs`), because
otherwise "the scheduler skips it and the job runs without the instructions it was scheduled to
follow." Pruned skills are dropped from job lists. Audited in `cron_rewrites.json`.

### 6d. The write-protection matrix (VERIFIED)

Everything autonomous is gated by `is_background_review()`, which reads a **ContextVar** bound at
turn start from `agent._memory_write_origin` (`tools/skill_provenance.py:37-78`;
bound at `agent/turn_context.py:378`; set to `"background_review"` on both forks at
`agent/background_review.py:747-748` and `agent/curator.py:1947`).

`_background_review_write_guard` (`tools/skill_manager_tool.py:301-419`) refuses an autonomous
write when the target is:

| Category | Line | Note |
|---|---|---|
| **pinned** | `:326-338` | *stricter than foreground* (which only blocks deletion) "precisely because there is no user in the loop to consent to an edit here" |
| in `skills.external_dirs` | `:340-354` | externally owned |
| a protected built-in (`plan`) | `:356-363` | |
| hub-installed | `:364-370` | |
| bundled | `:371-377` | unless `prune_builtins` + archive-only |
| **not curator-managed** — i.e. `created_by != "agent"`, **including a missing record** | `:379-405` | see below |

That last one carries a beautiful bug post-mortem (`:385-397`):

> "A MISSING record and an explicit `created_by: null` must resolve IDENTICALLY (issue #67140).
> Keying on `isinstance(usage_rec, dict)` made the policy depend on the guard's own side effect: a
> local skill with no telemetry record passed, the successful write called `bump_patch()` which
> created a `created_by: null` record, and the very same write was refused from then on.
> **'Allowed exactly once' is not a policy — it is a race with our own bookkeeping.**"

And the guard **fails closed on its own errors** (`:407-418`): if provenance can't be verified, the
write is refused.

Second guard: **read-before-write** (`_background_review_read_before_write_guard`, `:424-452`).
An autonomous fork may not mutate a file it has not `skill_view`'d **in this review turn**; the
read-marks ContextVar is reset at the start of every review (`agent/background_review.py:854-859`).
This is a hallucination brake — you cannot patch content you never loaded.

**Provenance is only stamped under the review fork** (`tools/skill_manager_tool.py:1445-1451`):

```python
if action == "create":
    if is_background_review():
        mark_agent_created(name)          # created_by = "agent"
elif action in {"patch", "edit", "write_file", "remove_file"}:
    bump_patch(name)
elif action == "delete":
    if not result.get("_archived"):
        forget(name)                      # hard delete drops the record; archive keeps it
```

So a skill the *user* asked a foreground agent to write is permanently off-limits to the curator
until the user runs `hermes curator adopt <name>` (`tools/skill_usage.py:592`;
CLI at `hermes_cli/curator.py:751-770`).

**Live consequence on this profile:** 58 of 59 records have `created_by: null`. Only **one** skill
is curator-managed. The consolidation pass, even if enabled, would have almost nothing to work on.
That is the design working as intended, not a bug.

### 6e. Usage counters — what "activity" means (VERIFIED)

`skill_view` bumps **both** `view_count` and `use_count` (`tools/skills_tool.py:1729-1750`):

```python
# A skill_view tool call is the agent actively loading the skill to act on it —
# that counts as use, not just a browse/view.
bump_view(str(resolved)); bump_use(str(resolved))
```

`bump_use` is also called from slash-command loads (`agent/skill_commands.py:597`, `:705`, `:792`)
and bundle preloads (`agent/skill_bundles.py:323-324`). `bump_patch` on any mutation. Telemetry is
recorded for **every** skill regardless of provenance (`tools/skill_usage.py:735-750`); only
*lifecycle* mutations require curation-eligibility.

---

## 7. Background review — full behaviour and isolation

Fires as described in §2a. The fork is a real `AIAgent` (`agent/background_review.py:730-746`) with
an aggressive set of isolation flags, each of which exists because of a specific production failure:

| Flag | Line | The failure it prevents |
|---|---|---|
| `_persist_disabled = True`, `_session_db = None`, `_session_json_enabled = False` | `:761-774` | **The curator-takeover bug.** The fork shares the parent's `session_id` for cache warmth; without this it wrote its harness turn ("Review the conversation above and update the skill library…") into the user's real session. "On the user's next live turn the agent re-reads that injected user message as a standing instruction and **'becomes' the curator**, refusing the actual task." |
| `_end_session_on_close = False` | `:808-814` | the fork's `close()` would finalize the parent's still-active session row mid-conversation |
| `compression_enabled = False` | `:816-825` | a compression race would rotate the parent into a NEW child the gateway never adopts, leaving one parent with two sibling children (#38727) |
| `skip_memory=True` | `:744`, `:697-708` | keeps the fork from rebuilding its own external memory provider and leaking the harness prompt into the user's memory namespace via three ingestion sites |
| `_memory_store` / `_memory_enabled` / `_user_profile_enabled` re-bound from parent | `:756-758` | built-in MEMORY.md writes still land on disk |
| `_memory_nudge_interval = 0`, `_skill_nudge_interval = 0` | `:759-760` (and `agent/curator.py:1938-1939`) | **a review fork must never spawn its own review** |
| `suppress_status_output = True` + `thread_scoped_silence()` | `:677`, `:776-782` | a process-global stdout redirect would blank a gateway Telegram long-poll thread for tens of seconds (#55769/#55925) |
| non-interactive approval callback → `"deny"` | `:655-664` | `input()` in a worker thread deadlocks against the parent's prompt_toolkit TUI (#15216) |
| tool whitelist `{skills}` ∪ `{memory}?` | `:833-853` | gated on `memory_enabled` — hardcoding `["memory","skills"]` contaminated memory-disabled profiles (#54937) |

**What the user actually sees.** `summarize_background_review_actions`
(`agent/background_review.py:391-605`) walks the fork's messages, maps successful `memory` /
`skill_manage` tool *results* back to their *calls* (the result JSON only says "Entry added"; the
arguments carry the detail), skips anything already present in the inherited snapshot (#14944), and
emits one line (`:930-942`):

```
  💾 Self-improvement review: Skill 'x' patched: "old…" → "new…" · Memory updated
```

Three verbosity modes via `memory_notifications`: `off` (nothing), `on` (generic
created/updated/patched messages), `verbose` (content previews truncated to 120 chars, 80 for patch
old/new, 60 for removals) (`:405-411`, `:517-595`).

The summariser is wrapped in its own try/except (`:915-928`) so that one malformed tool response
can't discard every successful action the fork already completed (#59437).

---

## 8. Live-state observations worth carrying into a design

All measured read-only on this profile, 2026-07-30. No personal content reproduced.

1. **`USER.md` is 177% over its cap.** 2,437 chars against `user_char_limit: 1375`. The cap is
   enforced **only on write** (`tools/memory_tool.py:428-441`) — never at load, never at injection.
   So the file loads and injects at full size, but *every* future `add`/`replace` to `USER.md` will
   be rejected with the consolidate-and-retry error, three times, and then terminally
   (`_MAX_CONSOLIDATION_FAILURES_PER_TURN = 3`). **The user profile is effectively frozen and
   nothing tells the user.** A char cap enforced on one side only is a silent write-lock.

2. **58/59 skills are unmanaged.** Only one record has `created_by: "agent"`. Because provenance is
   stamped *only* when the background-review fork creates a skill, every skill the user installed,
   hand-wrote, or asked a foreground agent to build is invisible to curation until explicitly
   adopted. Safe by default; also means the curator's headline feature is dormant for most users.

3. **Consolidation has never run here.** `consolidate: false` (the shipped default) + 12 curator
   runs = 12 deterministic prunes and zero LLM passes. The 150-line consolidation prompt and the
   4-signal reconciler are, on a default install, dead code.

4. **42% of skill descriptions are truncated in the index.** 53 of 127 are ≥60 chars. The routing
   signal the whole "mandatory scan" design depends on is being cut mid-sentence for four skills in
   ten — which is exactly why both authoring prompts nag about it so hard, and evidence the nag
   isn't sufficient. A validator would be.

5. **`memory.flush_min_turns: 6` is dead config.** A repo-wide grep (excluding `.git`/`__pycache__`)
   finds it **only** in `cli-config.yaml.example:664`. No code in this checkout reads it.

6. **The index is ~2.8k tokens, every turn, forever.** It grows linearly with the skill count and
   has no cap. The only relief valves are hiding descriptions (category demotion) — never entries.

---

# PART 2 — INFERRED (not verified)

Each item states exactly what I did not read.

- **The learning graph's memory→skill edges are never used for retrieval.** *Inferred — not
  verified.* I verified `build_learning_graph()` is called by the desktop/TUI/CLI journey surfaces
  and that no injection path in `system_prompt.py` / `prompt_builder.py` imports it, but I did not
  exhaustively grep every consumer of `agent.learning_graph` across `apps/desktop/`, `gateway/`, and
  `tui_gateway/`.

- **Exact `CURATOR_EVERY` poll period in the gateway housekeeping loop.** *Inferred — not verified.*
  I read the call site (`gateway/run.py:24644`) but not the constant's definition. It is only a
  poll rate; the real cadence is `curator.interval_hours = 168`.

- **`restore_skill` semantics beyond the docstring.** *Inferred — not verified.* I read
  `tools/skill_usage.py:913-916` (docstring: restores flat, does not reconstruct category nesting)
  but not the body.

- **The CLI/TUI `hermes journey` render pipeline.** *Inferred — not verified.* I read
  `learning_graph_render.py`'s docstring and function signatures and confirmed `hermes journey` is
  wired at `hermes_cli/main.py:11332-11350`, but did not read `hermes_cli/journey.py`.

- **External memory providers (`memory.provider` — honcho / mem0 / supermemory).** *Inferred — not
  verified.* Referenced at `agent/agent_init.py:1700+` and `agent/system_prompt.py:513-521`
  (`agent._memory_manager.build_system_prompt()`), and explicitly excluded from the review fork
  (`skip_memory=True`). These plugins may well do embedding-based retrieval — **my "no embeddings"
  claim is scoped strictly to the built-in MEMORY.md/USER.md + skills path.** Live config has
  `memory.provider: ''` (none active), so this profile is purely file-based.

- **Whether the model reliably obeys the review prompts.** *Inferred — not verified.* I read the
  prompts, not any eval. The prompts' own defensiveness ("A pass that does nothing is a missed
  learning opportunity", "'Nothing to save.' … should NOT be the default", "If you end the pass with
  fewer than 10 archives, you stopped too early") is strong circumstantial evidence that
  under-action was the observed failure mode, but that is inference from prompt archaeology.

- **`SOUL.md`'s exact role in the identity slot.** *Partially verified.* I confirmed it is the
  primary `stable`-tier identity when present (`agent/system_prompt.py:12`, `:189`), is seeded by
  `hermes_cli/config.py:831-838` on first run, is threat-scanned before injection
  (`agent/prompt_builder.py:1918-1930`), and is 513 bytes on this profile. I did **not** find any
  code path that lets the agent write to it — it appears to be human-authored identity, not a
  learning target. *Inferred: `SOUL.md` is not part of the learning loop.*

---

# PART 3 — Porting this to a Claude Code harness

Target: `/Users/damanpreetsingh/jivo-cli` — a read-only SAP/business toolkit that office staff fork
and drive through Claude Code. Goal: a human's correction ("no — ledger balance is
`CurrentAccountBalance`, positive = DEBIT") becomes durable, shared knowledge for every user's CLI.

## 3.1 The mapping

| Hermes | Claude Code | Fidelity |
|---|---|---|
| Skill = `SKILL.md` package with `references/`/`templates/`/`scripts/` | **Skill** = `.claude/skills/<name>/SKILL.md` + support files | **1:1.** Same format, same progressive disclosure, same frontmatter. |
| System-prompt skill index (name + ≤60-char desc) | Claude Code's own skill listing | **1:1** in effect. |
| `skill_view(name)` → `skill_view(name, file_path=…)` | `Skill` tool → `Read` on the support file | **1:1.** |
| `MEMORY.md` / `USER.md` (`§`-delimited, char-capped, frozen snapshot) | `~/.claude/projects/<id>/memory/*.md` + `MEMORY.md` index | **Close.** Claude Code already uses one-fact-per-file + an index line, which is *better* than Hermes' flat `§` blob — files have names, so they can be linked (`[[slug]]`) and selectively recalled. |
| Project-wide durable rules | `CLAUDE.md` | **Better than Hermes.** Hermes has no committed, team-shared equivalent; `CLAUDE.md` is in git, so a correction can reach every fork. |
| `_spawn_background_review` daemon thread after turn N | **`Stop` hook** running a headless `claude -p` | **Close.** A hook fires after the response is delivered — exactly the Hermes invariant ("runs AFTER the response is delivered so it never competes with the user's task"). |
| Background-review tool whitelist | Subagent with a restricted `tools:` list in its frontmatter | **1:1.** |
| Curator (weekly forked aux-model pass) | `cron` / `/loop` / a scheduled routine invoking a `curator` subagent | **Close.** |
| `.usage.json` lifecycle sidecar | A JSON file you write and maintain yourself | **Must be built.** No equivalent exists. |
| Write-origin ContextVar (`is_background_review()`) | Nothing. | **No equivalent — see §3.3.** |
| Prompt-cache-parity fork (`_cached_system_prompt` pinning) | Nothing you control. | **No equivalent.** |
| Frozen-snapshot invariant (mid-session writes don't change the prompt) | Roughly free — Claude Code doesn't rebuild the system prompt mid-session either. | **Free.** |

## 3.2 What ports cleanly — build these

**(a) The four-rung preference ladder.** This is the highest-value, zero-infrastructure idea in the
whole subsystem. Put it verbatim (adapted) into the reviewer subagent's prompt:

```
1. PATCH the skill that was actually loaded this session.
2. PATCH an existing class-level skill that covers the territory.
3. ADD references/<topic>.md under an existing skill + a one-line pointer in its SKILL.md.
4. CREATE a new class-level skill — only if nothing above fits, and only with a class-level name.
   If the name only makes sense for today's task, it is wrong. Fall back to 1/2/3.
```

For jivo-cli, rung 1 → 3 covers essentially everything: an Accounts correction about ledger sign
convention belongs as a **pitfall in the SAP skill**, not as a new `ledger-balance-sign-fix` skill.

**(b) The negative list.** Copy it nearly verbatim; it's the difference between a knowledge base and
a graveyard of self-imposed constraints. For this repo add two domain-specific entries:
- *never* capture a specific figure ("Oil turnover FY26 = ₹X Cr") — it goes stale in a day; capture
  the **query shape** that produces it;
- *never* capture "SAP is unreachable / the VPN is down" — the negative-claim rule, and it is
  exactly the class of thing that hardens into a refusal months after the tunnel is fixed. (The
  session log for this profile shows precisely that failure mode: "SAP Service Layer Unreachable
  (VPN Required)", "HANA Direct SQL Hangs" — durable-looking notes about transient state.)

**(c) The memory-vs-skill boundary, stated explicitly.** *Memory = who the user is and what the
current state of operations is. Skill = how to do this class of task for this user.* And the
Hermes rule that surprises people: **a style/format/workflow complaint is a SKILL signal, not just a
memory signal.** Fixing it in memory alone leaves the skill that governs the task still wrong.

**(d) Declarative-not-imperative memory phrasing** (`agent/prompt_builder.py:177-183`):
> "'User prefers concise responses' ✓ — 'Always respond concisely' ✗. Imperative phrasing gets
> re-read as a directive in later sessions and can cause repeated work or override the user's
> current request."

**(e) The frozen-snapshot + write-through split.** Writes land on disk immediately (durable);
the injected context does not change until the next session. Free in Claude Code, and it means a
correction made at 3pm is guaranteed to be live for tomorrow's session without destabilising
today's.

**(f) Progressive disclosure with an explicit pointer.** Index → SKILL.md → `references/*.md`, and
**always** add the one-line pointer when you add a support file. Rung 3 is invisible without it.

**(g) The `absorbed_into` discipline.** If you ever build consolidation: require the merge target to
be declared **at the moment of the delete**, verify it exists, and fail closed otherwise. Hermes
learned this from #29912 — "archived whole clusters of active skills with zero verified
consolidations." Post-hoc summaries and substring heuristics are backstops, never the primary
signal.

**(h) Read-before-write.** Refuse an automated patch to a file the automation has not read in this
pass. One line of state, kills a whole class of hallucinated edits.

**(i) The deterministic pass is the one that matters.** Hermes ships the LLM consolidation pass
**off**. The pure, no-LLM, timestamp-driven `active → stale → archived` walk runs always and is what
actually keeps the library honest. Build that first; the LLM pass is a luxury.

**(j) Never delete — archive.** `agent/curator.py:15-18`: *"Never auto-deletes — only archives.
Archive is recoverable."* Plus a pre-run snapshot with `keep: 5`.

## 3.3 What does NOT port — and what to do instead

**(a) There is no write-origin ContextVar.** This is the load-bearing absence. Hermes' entire safety
model rests on the runtime knowing "this write is coming from an autonomous fork, not a user."
Claude Code hooks and subagents have no such ambient signal.

*Substitute:* make the **path** the provenance. Two roots:
- `.claude/skills/` — human-authored, committed, **the automation may never write here**
- `.claude/skills-learned/` — automation-owned, and the reviewer subagent's prompt + its allowed
  write paths are scoped to it

Path-as-provenance is coarser than a ContextVar but it is enforceable with a `PreToolUse` hook that
rejects `Write`/`Edit` outside the learned root when the caller is the reviewer. It also gives you
Hermes' `adopt` flow for free: promoting a learned skill = `git mv` into `.claude/skills/`.

**(b) There is no post-turn fork sharing the parent's prompt cache.** Hermes' review is nearly free
because it replays a cache-warm transcript on the same model with a byte-identical system prompt.
A `Stop` hook spawning `claude -p` is a **cold** call that re-pays the whole transcript.

*Substitute:* adopt Hermes' own routed-path answer — **replay a digest, not the transcript**
(`_digest_history`, tail=24 verbatim + older turns collapsed to `USER:`/`ASSISTANT[tools: …]` lines).
And raise the trigger interval: Hermes fires every 10 user turns on a warm cache; on a cold cache,
fire at **session end only**, or at every 25–30 turns.

**(c) There is no `.usage.json` and nothing bumps counters.** Claude Code does not tell you which
skills were loaded.

*Substitute:* a `PostToolUse` hook on the `Skill` tool that appends
`{name, ts}` to `.claude/skills-learned/.usage.jsonl` (append-only JSONL sidesteps the entire
read-modify-write lock problem Hermes spent 200 lines solving). Fold it into a `.usage.json` in the
weekly curator pass. Keep Hermes' semantics: **loading a skill counts as *using* it**
(`tools/skills_tool.py:1744-1746`), and `use_count == 0` is *absence of evidence*, never grounds
for pruning inside the stale window.

**(d) There is no `memory` tool with a char budget and a consolidation loop.** Claude Code's memory
dir has no cap.

*Substitute:* you probably don't want the cap — one-fact-per-file is strictly better than a
char-capped blob, and the live `USER.md` at 177% of limit is a working demonstration of that design
failing. **Do** keep the discipline the cap was proxying for: cap `MEMORY.md` (the index) at ~40
lines and make the curator pass responsible for merging duplicate memory files. And **do** add what
Hermes lacks: enforce the budget symmetrically, or don't enforce it at all — a limit checked on
write but not on load is a silent write-lock.

**(e) There is no forked-agent isolation problem — but there is a new one.** Hermes' three ugliest
bugs (curator takeover via shared `session_id`, session finalisation mid-conversation, compression
race) all come from the fork sharing the parent's session. A `claude -p` subprocess has its own
session, so those vanish. The *new* risk is the opposite: a headless run with `--dangerously-skip-permissions`
in a repo whose CLAUDE.md rule 0 is **READ-ONLY, ALWAYS**. Scope the reviewer subagent's tools to
`Read, Grep, Glob, Write, Edit` with write paths restricted to `.claude/skills-learned/` and the
memory dir. No `Bash`. Hermes does exactly this
(`agent/background_review.py:840-853`, plus the auto-deny at `:655-664`).

**(f) There is no team-shared store — and this is where Claude Code *wins*.** Hermes' skills live in
`~/.hermes/skills/`, per-machine, un-versioned. jivo-cli is a **git repo that office staff fork**.
Committing `.claude/skills/` and `CLAUDE.md` gives you the thing Hermes cannot do: one Accounts
correction, reviewed in a PR, reaching every user's CLI. Make the learned root a **PR queue**, not
an auto-merge:

```
turn N ──▶ Stop hook ──▶ reviewer subagent (digest replay, restricted tools)
                              │
                              ├─ patches .claude/skills-learned/<skill>/SKILL.md
                              └─ appends .claude/skills-learned/PENDING.md
weekly  ──▶ curator subagent ──▶ deterministic stale/archive pass (no LLM)
                              └─ opens ONE PR promoting reviewed learnings into .claude/skills/
```

That maps Hermes' `foreground = user-owned` / `background = curator-owned` split onto
`main = reviewed` / `skills-learned = proposed`, and turns Hermes' weakest property (per-machine,
unshared) into your strongest.

## 3.4 Minimum viable port, in order

1. `CLAUDE.md` gains the memory-vs-skill boundary + the negative list. *(Zero code. Do this today.)*
2. `.claude/skills/sap-b1/` becomes the class-level umbrella; the ledger-sign correction lands as a
   **Pitfall** in it, not as a new skill. *(Rung 1 of the ladder, by hand.)*
3. `PostToolUse` hook on `Skill` → append to `.usage.jsonl`. *(~10 lines. Everything downstream
   needs it, and it's useless retroactively — start collecting now.)*
4. `Stop` hook → reviewer subagent with the four-rung ladder + negative list, restricted tools,
   writing only to `.claude/skills-learned/`. Trigger at session end first; tune to an interval once
   you can see the cost.
5. Weekly deterministic curator: stale at 30d, archive (`git mv` to `.archive/`) at 90d, with the
   `use_count == 0` grace floor and a pinned-list exemption. **No LLM.**
6. Only after all of the above: the LLM consolidation pass — with `absorbed_into` fail-closed. Ship
   it **off** by default, exactly as Hermes does.

---

## Open questions

1. **Does the background review actually fire in practice, and how often does it write?** The
   `.curator_state` gives me curator cadence but nothing records background-review invocations.
   `state.db` has no review table and `_persist_disabled = True` means the fork writes no messages.
   To answer I'd need to grep `~/.hermes/logs/agent.log` for the
   `💾 Self-improvement review:` line, which I did not do.

2. **What is `CURATOR_EVERY`?** Read the call site (`gateway/run.py:24644`), not the constant.
   Cosmetic — the 168-hour interval gate dominates — but unresolved.

3. **Why is `USER.md` 177% over its limit?** Three candidate causes I could not distinguish
   without reading the file (which I deliberately did not): (a) `user_char_limit` was lowered
   after the entries were written; (b) an external writer appended past the guard; (c) the entries
   predate the cap. The `.bak.20260517` files suggest a past drift event. Either way the
   asymmetric enforcement (write-time only) is the real finding.

4. **Do the external memory providers (honcho / mem0 / supermemory) do embedding-based retrieval?**
   If so, Hermes *does* have a semantic-recall path — just not in the built-in one I traced. Not
   active on this profile (`memory.provider: ''`), so I could not observe it.

5. **How does the curator behave when the LLM pass names an umbrella it then deletes later in the
   same run?** `_reconcile_classification` has an explicit comment for this case
   (`agent/curator.py:942-948`) saying the `skill_manage` layer should already reject it, but "if it
   slips through … fall through to the usual signals." I did not verify that the tool-layer
   validation (`tools/skill_manager_tool.py:1100-1125`) is ordering-safe within a single run.

6. **Is there any mechanism that removes a memory entry for being wrong (as opposed to being
   superseded or over budget)?** I found none — no decay, no confidence score, no contradiction
   detection. If a wrong fact is written, only the model choosing to `replace`/`remove` it, or a
   human running `hermes journey delete`, will remove it. I did not exhaustively read every consumer
   of the `memory` tool, so I cannot rule out a path I missed.

7. **How large can the skills index grow before it degrades routing?** Measured 2.8k tokens at 127
   skills here. No cap exists, and the mitigation (category demotion) drops descriptions but never
   names. I have no data on where the quality cliff is — and neither, as far as I can tell from the
   code, does Hermes.

8. **Are `references/` files ever read without the parent `SKILL.md` being read first?**
   `iter_skill_index_files` deliberately excludes support dirs from the index
   (`agent/skill_utils.py:812-830`), so rung 3 is reachable only via the SKILL.md pointer. Whether
   models reliably follow that pointer is untested here — and it is the single assumption the whole
   progressive-disclosure design rests on.
