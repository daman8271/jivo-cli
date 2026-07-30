# WORKER B — The Hermes SKILL subsystem, reverse-engineered

**Target:** `~/.hermes/hermes-agent/` @ `70411a6152024ecb061972e778f900289c7ef046` (2026-07-29)
**Live state inspected:** `~/.hermes/skills/`, `~/.hermes/.skills_prompt_snapshot.json`, `~/.hermes/skills/.usage.json`, `~/.hermes/skills/.hub/lock.json`, `~/.hermes/skills/.bundled_manifest`, `~/.hermes/skills/.curator_state`, `~/.hermes/logs/curator/*`, `~/.hermes/state.db`, `~/.hermes/config.yaml`
**Mode:** read-only. Nothing under `~/.hermes/` was modified.

## Method / confidence conventions

Every section is tagged **VERIFIED** (I read the code or the live file that proves the claim, and cite it) or **INFERRED** (reasoned from what I read, not proven). Line numbers are from the files above at the commit named. Where I quote, the quote is verbatim.

Files read in full: `tools/skill_usage.py`, `tools/skill_provenance.py`, `tools/skills_ast_audit.py`, `agent/skill_preprocessing.py`, `agent/skill_utils.py`, `agent/learn_prompt.py`.
Files read in the load-bearing regions: `tools/skill_manager_tool.py`, `tools/skills_guard.py`, `tools/skills_tool.py`, `tools/skills_hub.py`, `tools/skills_sync.py`, `tools/write_approval.py`, `agent/prompt_builder.py`, `agent/background_review.py`, `agent/curator.py`, `agent/skill_commands.py`, `agent/coding_context.py`, `agent/system_prompt.py`, `agent/turn_finalizer.py`, `agent/insights.py`, `hermes_cli/skills_hub.py`, `hermes_cli/curator.py`.
Files I only grepped (so any claim about them is marked inferred): `cli.py` (829 KB), `hermes_state.py`, `gateway/run.py`, `hermes_cli/web_server.py`, `agent/skill_bundles.py` (read docstring + map only).

---

## 0. Executive summary — the eight findings that matter for JIVO

1. **Yes, Hermes creates skills with no human writing them.** Three distinct paths, two fully autonomous. §4.
2. **The trigger is a tool-iteration counter, not a pattern detector.** After a turn that burned ≥ `skills.creation_nudge_interval` tool iterations (default 10, **15 on this machine**), a forked agent replays the transcript and is told "most sessions produce at least one skill update." Nothing anywhere clusters *recurring question shapes*. §4.1, §10.
3. **Usage telemetry exists, is read back, and drives exactly one decision: lifecycle (active → stale → archived).** It does **not** influence discovery, ordering, or relevance. The curator prompt explicitly forbids using it as a consolidation signal. §3.
4. **The discovery payload is one static block of `name: 57-chars-of-description` for every skill, injected on every turn.** On this machine that is **15,452 characters ≈ 3.9–4.3k tokens** for 127 skills. No semantic filtering, no retrieval. §2.
5. **`SKILL_PROMPT_DESC_LIMIT = 60` is the single highest-leverage constraint in the whole system.** Descriptions are hard-truncated to 57 chars + `...` in the index. 47 of 127 installed skills are truncated — i.e. **37% of the library has a mutilated routing signal**. §2.5.
6. **Provenance is a *policy opt-in*, not a historical fact — and a foreground `skill_manage(create)` deliberately does NOT set it.** A skill the user asks the AI to write is permanently invisible to autonomous maintenance until someone runs `hermes curator adopt <name>`. §5.
7. **Guardrails are heuristics, self-declared as "not boundaries," and OFF by default for agent-created skills.** `skills.guard_agent_created: false` is the shipped default and the live value here. Hub installs are always scanned. §6.
8. **Hermes has no multi-user story.** All state is per-`HERMES_HOME`. Sharing is pull-based: a hub registry, a `.well-known/skills` endpoint, git taps, or a snapshot JSON. The interesting mechanism for JIVO is the **origin-hash three-way merge** in `skills_sync.py`, which lets a central bundle evolve without clobbering local edits. §7, §9.7.

---

## 1. Skill format — **VERIFIED**

### 1.1 On-disk layout

Single root: `~/.hermes/skills/` (`tools/skills_tool.py:139-143`, comment: *"All skills live in ~/.hermes/skills/ (seeded from bundled skills/ on install). This is the single source of truth -- agent edits, hub installs, and bundled skills all coexist here without polluting the git repo."*). Profile-scoped: `_skills_dir()` re-resolves `get_hermes_home()/skills` on every call so long-lived multi-profile runtimes bind correctly (`skills_tool.py:147-158`, `skill_manager_tool.py:160-172`).

A skill is a **directory** containing `SKILL.md` plus optional support dirs. Two layouts coexist and both are discovered:

```
~/.hermes/skills/
├── <skill>/SKILL.md                    # flat
├── <category>/<skill>/SKILL.md         # 1-level category
├── <cat>/<subcat>/<skill>/SKILL.md     # nested (mlops/training/<skill>)
├── <category>/DESCRIPTION.md           # category-level blurb (frontmatter `description:`)
├── .bundled_manifest                   # "name:md5" per line — bundled provenance
├── .usage.json                         # usage/lifecycle sidecar
├── .usage.json.lock                    # flock/msvcrt lock file
├── .curator_state                      # curator scheduler state
├── .curator_suppressed                 # built-ins the curator pruned (don't re-seed)
├── .curator_backups/<ISO>/{manifest.json,skills.tar.gz}
├── .archive/<skill>/                   # recoverable archive (flat)
└── .hub/{lock.json,taps.json,audit.log,index-cache/,quarantine/}
```

Every path above is confirmed against the live tree. Support dirs are exactly `references`, `templates`, `assets`, `scripts` (`skill_utils.py:50` `SKILL_SUPPORT_DIRS`; write-side allow-list `skill_manager_tool.py:520` `ALLOWED_SUBDIRS`). The hub bundle fetcher additionally accepts `examples` (`skills_hub.py:155`).

**Support dirs are excluded from discovery** — a preserved old skill package at `foo/references/old-skill/SKILL.md` is data, not a skill (`skill_utils.py:73-99` `is_skill_support_path`, and the pruning walk `iter_skill_index_files` at `skill_utils.py:812-834`). Excluded dirs: `.git .github .hub .archive .venv venv node_modules site-packages __pycache__ .tox .nox .pytest_cache .mypy_cache .ruff_cache` (`skill_utils.py:27-44`).

Note `iter_skill_index_files` uses `os.walk(..., followlinks=True)`. On this machine **17 of the 64 top-level entries are symlinks into `~/.agents/skills/`** (e.g. `confidence-honesty -> ../../.agents/skills/confidence-honesty`), a cross-agent shared skill dir. Hermes treats these as *local*, not as `skills.external_dirs`, so they are curator-eligible. That is a real footgun: autonomous maintenance can write into a directory shared with other agents.

### 1.2 Frontmatter schema

The authoritative spec is `website/docs/developer-guide/creating-skills.md:44-84`. Parsing is `skill_utils.py:125-171` (`parse_frontmatter`) — full YAML via `CSafeLoader`, with a leading-BOM strip (`skill_utils.py:144-146`; Windows editors otherwise silently void the whole frontmatter) and a naive `key: value` fallback on YAML error.

```yaml
---
name: my-skill                    # REQUIRED. ≤64 chars (MAX_NAME_LENGTH, skills_tool.py:162)
                                  #   write path also enforces ^[a-z0-9][a-z0-9._-]*$
                                  #   (VALID_NAME_RE, skill_manager_tool.py:517)
description: One sentence.        # REQUIRED. ≤1024 chars stored (MAX_DESCRIPTION_LENGTH,
                                  #   skills_tool.py:163) but ≤60 chars to survive the
                                  #   prompt index (see §2.5)
version: 1.0.0                    # optional
author: Hermes                    # optional
license: MIT                      # optional
platforms: [macos, linux, windows]  # optional hard-compat gate → sys.platform
environments: [kanban|docker|s6]  # optional OFFER-time relevance gate
compatibility: "Requires X"       # optional, agentskills.io passthrough
prerequisites:                    # optional LEGACY
  env_vars: [API_KEY]             #   normalized into required_environment_variables
  commands: [curl, jq]            #   advisory only, never enforced
required_environment_variables:   # optional; missing ones → setup_needed
  - name: MY_API_KEY
    prompt: "Enter your API key"
    help: "Get one at https://example.com"
    required_for: "API access"
    optional: false
required_credential_files: []     # optional; mounted into Modal/Docker sandboxes
setup:                            # optional; collect_secrets folded into the above
  help: "..."
  collect_secrets: [{env_var: X, prompt: "...", provider_url: "...", secret: true}]
metadata:                         # arbitrary; Hermes reads only metadata.hermes.*
  hermes:
    tags: [Fine-tuning, LLM]
    related_skills: [peft, lora]
    category: productivity
    requires_toolsets: [terminal]        # hide unless toolset active
    requires_tools: [web_search]         # hide unless tool available
    fallback_for_toolsets: [browser]     # hide WHEN toolset active
    fallback_for_tools: [browser_navigate]
    supersedes: [find-nearby]
    homepage: https://...
    config:                              # config.yaml keys this skill needs
      - {key: wiki.path, description: "...", default: "~/wiki", prompt: "..."}
    blueprint:                           # makes the skill a runnable automation
      schedule: "0 9 * * *"
      deliver: origin
      prompt: "..."
      no_agent: false
---
# Human Title
## When to Use / ## Prerequisites / ## How to Run / ## Quick Reference
## Procedure / ## Pitfalls / ## Verification
```

Only four keys are load-bearing for the prompt path: `name`, `description`, `platforms`, `metadata.hermes.{requires,fallback}_{tools,toolsets}` (`prompt_builder.py:1440-1451`, `skill_utils.py:616-630`).

**Empirical key census** across all 127 installed skills (I walked the tree and counted top-level frontmatter keys):

| key | count | | `metadata.hermes.*` | count |
|---|---|---|---|---|
| `name` | 127 | | `tags` | 77 |
| `description` | 127 | | `related_skills` | 44 |
| `version` | 90 | | `category` | 16 |
| `platforms` | 78 | | `homepage` | 14 |
| `metadata` | 77 | | `requires_toolsets` | 3 |
| `author` | 72 | | `upstream_skill` | 1 |
| `license` | 71 | | `credits` | 1 |
| `dependencies` | 16 | | `supersedes` | 1 |
| `prerequisites` | 13 | | `related_docs` | 1 |
| `allowed-tools` | 12 | | | |
| `tags` (top-level) | 6 | | | |
| `min-binary-version` | 4 | | | |
| `argument-hint` | 4 | | | |
| `title` / `context` / `user-invocable` / `triggers` | 2 each | | | |
| `environments` / `compatibility` / `setup` / `required_credential_files` | 1 each | | | |

`dependencies`, `allowed-tools`, `min-binary-version`, `argument-hint`, `title`, `context`, `user-invocable`, `triggers` are **not read by any Hermes code path I found** — they are Claude-Code / agentskills.io artifacts that survived import. `allowed-tools` is even explicitly demoted in the guard: *"`allowed-tools:` is REQUIRED SKILL.md frontmatter per the agent-skill spec — every compliant skill declares it, so it cannot be a threat signal on its own"* (`skills_guard.py:440-446`). `tags` at top level is read as a fallback (`skills_tool.py:1459-1462`).

### 1.3 The four provenance classes

There is no field on disk that says "I'm bundled." Class is derived from **three side files**:

| class | how identified | curator may archive/consolidate? | who may write it |
|---|---|---|---|
| **bundled** (built-in) | name in `~/.hermes/skills/.bundled_manifest` (`skill_usage.py:181-201`) | only if `curator.prune_builtins` (default `true`) — `skill_usage.py:443-445, 455-478` | foreground agent yes; background review **no** (`skill_manager_tool.py:373-380`) |
| **hub-installed** | name (or resolved frontmatter name) in `.hub/lock.json → installed` (`skill_usage.py:204-247`) | **never** (`skill_usage.py:469-470`) | foreground yes; background **no** (`skill_manager_tool.py:365-372`) |
| **external** | path under a `skills.external_dirs` root (`skill_utils.py:593-610`) | **never** | foreground yes; background **no** (`skill_manager_tool.py:341-351`) |
| **local** (agent- or user-authored) | everything else | only if its `.usage.json` record carries `created_by: "agent"` (`skill_usage.py:481-511`) | both, subject to §5 |

Plus a hardcoded exemption set: `PROTECTED_BUILTIN_SKILLS = {"plan"}` (`skill_usage.py:66-68`) — never archivable on any path, because *"`plan` powers the `/plan` slash-command flow… silently archiving one turns its slash command into 'Unknown command' with no signal to the user."*

**Bundled vs optional:** the repo ships `skills/` (15 categories, seeded on install) and `optional-skills/` (23 categories, not activated by default). Optional skills that get installed are recorded in `.hub/lock.json` with `source: "official"`, `trust_level: "builtin"`, `scan_verdict: "backfilled"`, `metadata.backfilled_from: "optional-skills"` — live evidence: all 8 entries in this machine's `lock.json` have exactly that shape, written by `skills_sync._backfill_optional_provenance` (`skills_sync.py:455`).

### 1.4 Preprocessing at load time

`agent/skill_preprocessing.py` (144 lines, read in full):

- `${HERMES_SKILL_DIR}` / `${HERMES_SESSION_ID}` substitution, on by default (`skills.template_vars: true`). Unresolved tokens are **left in place** deliberately, "so the author can spot them" (`skill_preprocessing.py:44-48`).
- Inline shell: `` !`cmd` `` executes with `bash -c`, cwd = skill dir, output capped at 4000 chars, timeout default 10s (`skill_preprocessing.py:19-22, 65-103`). **Off by default** (`skills.inline_shell: false`, and that is the live value). This is a code-execution surface hanging off a markdown file; keep it off.

---

## 2. Discovery + injection — **VERIFIED**

### 2.1 Three tiers of progressive disclosure

The module docstring names the model it copies: *"Inspired by Anthropic's Claude Skills system with progressive disclosure architecture"* (`skills_tool.py:9-12`).

| tier | payload | mechanism |
|---|---|---|
| 1 — always in prompt | `name` + **57 chars** of description, grouped by category | `build_skills_system_prompt` (`prompt_builder.py:1531`) |
| 2 — on request | full `SKILL.md` body + `linked_files` manifest + env readiness | `skill_view(name)` (`skills_tool.py:961`) |
| 3 — on request | one support file | `skill_view(name, file_path="references/x.md")` (`skills_tool.py:1293-1402`) |

`skills_list()` is a *fourth* surface, not a tier: it returns name + description up to **1024** chars + category, uncached-per-30s (`skills_tool.py:785-851`, `_SKILLS_CACHE_TTL_SECONDS = 30.0` at `:101`). So the model can recover a truncated description — but only if it thinks to ask.

### 2.2 The tier-1 block: exact shape

Rendered by `prompt_builder.py:1730-1783`. The literal header (`:1756-1776`) is worth quoting because it is doing most of the work:

> `## Skills (mandatory)`
> `Before replying, scan the skills below. If a skill matches or is even partially relevant to your task, you MUST load it with skill_view(name) and follow its instructions. Err on the side of loading — it is always better to have context you don't need than to miss critical steps, pitfalls, or established workflows. …`
> `If a skill has issues, fix it with skill_manage(action='patch').`
> `After difficult/iterative tasks, offer to save as a skill. If a skill you loaded was missing steps, had wrong commands, or needed pitfalls you discovered, update it before finishing.`

Body format (`:1734-1753`):

```
<available_skills>
  <category>: <category DESCRIPTION.md description>
    - <frontmatter name>: <57 chars>...
  <demoted-category> [names only]: nameA, nameB, nameC
</available_skills>

Only proceed without loading a skill if genuinely none are relevant to the task.
```

Injected into `stable_parts` of the system prompt — the cross-session-stable, prompt-cache-warm prefix — and only when at least one of `skills_list`/`skill_view`/`skill_manage` is in `agent.valid_tool_names` (`agent/system_prompt.py:299-329`).

### 2.3 Measured token cost — **VERIFIED (chars), ESTIMATED (tokens)**

I reconstructed the exact rendered block from this machine's snapshot, applying the real darwin platform filter and the real dedupe/sort:

| quantity | value |
|---|---|
| skills shown | **127** |
| categories | **64** |
| index body | **13,863 chars** |
| header literal | 1,487 chars |
| footer literal | 102 chars |
| **total block** | **15,452 chars** |
| tokens @ 4 chars/tok | ~3,863 |
| tokens @ 3.6 chars/tok | ~4,292 |

The token figures are an estimate — no tokenizer (`tiktoken`) is installed on this machine, so I could not count exactly. Char counts are exact.

**64 categories for 127 skills is a structural cost bug.** `_build_snapshot_entry` (`prompt_builder.py:1431-1438`) derives `category` from the path: for a flat `animejs/SKILL.md`, `parts` has length 2, so `skill_name = "animejs"` and `category = parts[0] = "animejs"`. Every flat skill therefore invents its own single-member category and buys an extra header line. 47 of the 64 categories on this machine hold exactly one skill.

### 2.4 The filter chain — what decides whether a skill is *offered*

Applied in order, in `build_skills_system_prompt`:

1. **Path exclusion** — `iter_skill_index_files` prunes `EXCLUDED_SKILL_DIRS` + support dirs (`skill_utils.py:812-834`).
2. **Platform** — `platforms:` vs `sys.platform` via `PLATFORM_MAP`, with Termux/Android special-casing (`skill_utils.py:177-222`). Absent/empty ⇒ all platforms.
3. **Environment** — `environments: [kanban|docker|s6]` vs live detection, cached per-process; **unknown tags fail open** (`skill_utils.py:286-322`). Offer-time only: explicit `skill_view` / `--skills` bypasses it, because *"an explicit load is explicit consent"* (`skill_utils.py:230-233`).
4. **User disable list** — `skills.disabled` ∪ `skills.platform_disabled[<platform>]` (`skill_utils.py:371-406`). Matched against **both** the frontmatter name and the directory name (`prompt_builder.py:1599`).
5. **Conditional activation** — `_skill_should_show` (`prompt_builder.py:1484-1512`): hide if any `fallback_for_*` is present; hide if any `requires_*` is absent. When both `available_tools` and `available_toolsets` are `None`, show everything (backward compat).
6. **Local-wins dedupe** — external-dir skills are skipped if the name is already claimed locally (`prompt_builder.py:1661-1690`).
7. **Posture demotion** — under the *opt-in* `agent.coding_context: focus` mode in a code workspace, a deny-list of 18 non-coding categories (`apple, communication, cooking, creative, email, finance, gaming, gifs, health, media, music, note-taking, productivity, shopping, smart-home, social-media, travel, yuanbao` — `coding_context.py:304-309`) collapses to a `[names only]` line. Names are **never** removed. The comment explaining why is the best design note in the codebase (`prompt_builder.py:1708-1716`): *"NEVER remove entries entirely: agent-created skills are the model's project memory, and models don't reach for skills_list to rediscover what the index stops showing them."* An earlier revision did prune them and caused "silent capability loss in a real workflow" (`coding_context.py:574-580`).

**What is NOT in the chain:** semantic search, embeddings, recency, usage frequency, query relevance, per-turn selection, or any token budget. The block is identical on turn 1 and turn 200 of a session. That is deliberate — it keeps the block inside the cacheable prefix.

### 2.5 The 60-char cliff

```python
SKILL_PROMPT_DESC_LIMIT = 60                                  # skill_utils.py:784

def extract_skill_description(frontmatter):                   # skill_utils.py:793-800
    desc = _normalize_skill_description(frontmatter)
    if not desc: return ""
    if len(desc) > SKILL_PROMPT_DESC_LIMIT:
        return desc[:SKILL_PROMPT_DESC_LIMIT - 3] + "..."
    return desc
```

Three enforcement/mitigation layers were added around it over time (git history: `5eb772111` 2026-05-12 extracted the constant; `accbf4d91` same day added the preview; `8611b69da` 2026-07-23 scoped hard enforcement to the create path):

- **Create path hard-fails** an over-60 description with an explanatory error (`skill_manager_tool.py:607-614`): *"the skill index truncates longer descriptions to 57 chars + '...', destroying the routing signal. Move detail into the skill body."* Edit and patch deliberately do **not** enforce, so existing over-limit skills stay maintainable.
- **`system_prompt_preview`** is returned on create/edit when truncation will occur, showing the model exactly what the index will say (`skill_manager_tool.py:822-830`).
- The `/learn` authoring standards call it *"the most-violated rule and it is NOT cosmetic"* and instruct the model to count characters (`learn_prompt.py:36-47`).

**Live measurement: 47 of 127 skills (37%) are truncated.** All 47 sit at exactly 60 chars in the snapshot. Given that the *entire* routing decision runs off this string, that is the biggest quality defect in the deployed library.

### 2.6 The snapshot — `~/.hermes/.skills_prompt_snapshot.json`

This is **not** the prompt payload. It is a **cold-start parse cache**: pre-parsed per-skill metadata plus an mtime/size fingerprint. Two-layer cache (`prompt_builder.py:1538-1543`):

- **Layer 1** — in-process LRU, max 8 entries (`_SKILLS_PROMPT_CACHE_MAX = 8`, `:1340-1342`), keyed by `(skills_dir, external_dirs, sorted tools, sorted toolsets, platform_hint, sorted disabled, sorted compact_categories)` (`:1567-1575`). Caches the **rendered string**.
- **Layer 2** — the disk snapshot. Caches the **parsed metadata**, surviving process restarts.

**Exact structure** (confirmed against the live 72,328-byte file, `json.dump(..., indent=2)`):

```jsonc
{
  "version": 1,                                  // _SKILLS_SNAPSHOT_VERSION, prompt_builder.py:1343
  "manifest": {                                  // rel_path -> [st_mtime_ns, st_size]
    "hyperframes/SKILL.md":      [1778668045230749275, 30613],
    "apple/DESCRIPTION.md":      [1776709926347019491,   152]
  },
  "skills": [                                    // one entry per SKILL.md, incl. platform-incompatible
    { "skill_name":        "animejs",            // path-derived dir name
      "category":          "animejs",            // path-derived (see §2.3)
      "frontmatter_name":  "animejs",            // the `name:` field — what skill_view() takes
      "description":       "Anime.js adapter patterns for HyperFrames. Use when writi...",  // ALREADY TRUNCATED to 60
      "platforms":         [],
      "conditions": { "requires_toolsets": [], "requires_tools": [],
                      "fallback_for_toolsets": [], "fallback_for_tools": [] } }
  ],
  "category_descriptions": { "apple": "Apple/macOS-specific skills — iMessage, …" }
}
```

Live reconciliation, all confirmed:

| | count |
|---|---|
| `manifest` entries | 154 = 127 `SKILL.md` + 27 `DESCRIPTION.md` |
| `skills` entries | 127 |
| `category_descriptions` | 26 |
| skill entries with non-empty `platforms` | 55 |
| skill entries with any non-empty `conditions` | **2** (`maps`, `research-paper-writing`) |
| `frontmatter_name != skill_name` | 4 (`creative-ideation`→`ideation`, `audiocraft`→`audiocraft-audio-generation`, `segment-anything`→`segment-anything-model`, `trl-fine-tuning`→`fine-tuning-with-trl`) |

27 `DESCRIPTION.md` but only 26 category descriptions: `inference-sh/DESCRIPTION.md` has no frontmatter `description:` key, so it is skipped at `prompt_builder.py:1640-1642`. I confirmed that file directly — it opens with `# inference.sh` and plain prose.

**Generation** — cold path only (`prompt_builder.py:1614-1655`): full walk, parse every `SKILL.md`, build entries, read every `DESCRIPTION.md`, then `atomic_json_write`. Entries are appended **before** the compatibility check (`:1619-1622`), so the snapshot is platform-portable and the platform filter runs at render time from the stored `platforms` list. Only the **local** skills dir is snapshotted; external dirs are re-walked on every cold render (`:1657-1660`, *"no snapshot caching — they're read-only and typically small"*).

**Invalidation** — two mechanisms:

1. **Passive**: `_load_skills_snapshot` rebuilds `_build_skills_manifest(skills_dir)` and compares it for *exact dict equality* to the stored manifest; any mismatch discards the snapshot (`prompt_builder.py:1387-1402`). Version bump also discards. So out-of-band edits, adds, and deletes are caught by mtime-ns + size.
2. **Active**: `clear_skills_system_prompt_cache(clear_snapshot=True)` unlinks the file (`:1350-1358`). Called after every successful `skill_manage` action (`skill_manager_tool.py:1432-1437`) and from six hub CLI mutation paths (`hermes_cli/skills_hub.py:799, 1170, 1217, 1357, 1387, 1430`) plus the web dashboard (`hermes_cli/web_server.py:14718`).

**Gaps I can see (inferred, not proven by a failing test):** (a) the curator's `archive_skill()` moves a directory without calling the active invalidator — the passive manifest check covers it, one render later; (b) mtime-ns + size can theoretically miss a same-size same-timestamp edit; (c) `_build_skills_manifest` is a full `os.walk` on every cold render *even on a snapshot hit*, so the "fast path" still pays one stat per skill file.

---

## 3. Usage tracking — **VERIFIED**

### 3.1 Storage: a JSON sidecar. Nothing in SQLite.

`~/.hermes/skills/.usage.json`, keyed by **frontmatter skill name** (`skill_usage.py:85-86`). The design rationale is stated up front (`skill_usage.py:8-16`): *"Sidecar, not frontmatter. Keeps operational telemetry out of user-authored SKILL.md content and avoids conflict pressure for bundled/hub skills."*

I confirmed there are **no skill tables in `~/.hermes/state.db`** — `SELECT name FROM sqlite_master WHERE name LIKE '%skill%'` returns nothing (tables are `messages`, `messages_fts*`, `sessions`, `session_model_usage`, `async_delegations`, `delivery_obligations`, `gateway_routing`, `compression_locks`, `schema_version`, `state_meta`). Same for `kanban.db`.

Record shape (`_empty_record`, `skill_usage.py:640-653`):

```jsonc
{ "created_by": null,          // "agent" == curator-managed (see §5). NOT provenance.
  "use_count": 0,   "last_used_at": null,
  "view_count": 0,  "last_viewed_at": null,
  "patch_count": 0, "last_patched_at": null,
  "created_at": "<ISO8601 UTC>",
  "state": "active",           // active | stale | archived  (:53-56)
  "pinned": false,             // orthogonal opt-out from auto-transitions
  "archived_at": null }
```

Concurrency: every read-modify-write cycle takes an exclusive `flock` (Unix) / `msvcrt.locking` (Windows) on `.usage.json.lock` (`skill_usage.py:89-122`); writes are tempfile + `fsync` + `os.replace` (`:676-697`). Every mutation is best-effort — *"A broken sidecar never breaks the underlying tool call"* (`:12-13`); failures log at DEBUG and return.

### 3.2 What is recorded, from where

| counter | bumped by | call sites |
|---|---|---|
| `view_count` / `last_viewed_at` | `bump_view` (`:767-776`) | **only** the `skill_view` tool wrapper (`skills_tool.py:1743`) |
| `use_count` / `last_used_at` | `bump_use` (`:779-788`) | `skill_view` tool wrapper (`skills_tool.py:1747`); `/skill-name` slash invocation (`skill_commands.py:598`); stacked `/a /b` invocation (`:706`); `hermes -s <skill>` session preload (`:793`); `/bundle` invocation (`skill_bundles.py:324`) |
| `patch_count` / `last_patched_at` | `bump_patch` (`:791-799`) | `skill_manage` on `patch`, `edit`, `write_file`, `remove_file` (`skill_manager_tool.py:1450-1451`) |
| record dropped | `forget` (`:834-845`) | hard `skill_manage(delete)` only — a curator archive keeps the record as `archived` (`skill_manager_tool.py:1452-1457`) |

The `skill_view` handler bumps **both** view and use, with the reasoning inline:

```python
# skills_tool.py:1743-1747
bump_view(str(resolved))
# A skill_view tool call is the agent actively loading the skill
# to act on it — that counts as use, not just a browse/view.
# Curator's stale timer keys off last_used_at (see agent/curator.py).
bump_use(str(resolved))
```

This is why the live file has `use_count == view_count` for every entry (53 = 53 across 59 records). **Consequence: `view_count` carries no information the tool path doesn't already give you.** Divergence only arises from slash/preload/bundle invocations, which bump `use` alone.

Telemetry is recorded for **every** skill regardless of class — `_mutate` defaults `require_curation_eligible=False` because *"usage tracking is pure observability and is orthogonal to whether a skill is ever curated"* (`skill_usage.py:735-745`). Only the three lifecycle mutators (`set_state`, `set_pinned`, `mark_agent_created`) pass `True`.

### 3.3 What reads it back — and the exact decision it drives

**One decision: the lifecycle state machine.** `agent/curator.py:305-383` `apply_automatic_transitions`, a pure function with no LLM:

```
anchor = latest(last_used_at, last_viewed_at, last_patched_at)   # skill_usage.py:146-163
         or created_at or now                                     # curator.py:350-353

skip if pinned                                        (curator.py:331-332)
skip if referenced by ANY cron job, incl. paused      (curator.py:324, 340-341)
if no persisted record → seed_record_if_missing, defer (curator.py:345-348)
if use_count == 0 and anchor > stale_cutoff → leave alone, reactivate if stale
                                                       (curator.py:363-369)
anchor <= now - archive_after_days  → archive_skill()  (curator.py:371-374)
anchor <= now - stale_after_days    → state = stale    (curator.py:375-377)
anchor >  now - stale_after_days    → state = active    (reactivation, :378-381)
```

Config: `curator.stale_after_days` (30), `curator.archive_after_days` (90) — live values. Two grace clauses matter: never-used skills get a floor (*"'use=0' is absence of evidence, not evidence of staleness"*, `curator.py:359-362`), and first-sight built-ins get their clock anchored to *now* rather than epoch, so flipping `prune_builtins` on doesn't mass-archive (`curator.py:309-313`, `skill_usage.py:713-732`).

`.usage.json` is also read for: the `pinned` delete-guard (`skill_manager_tool.py:274-298`), the background-review write guard (`:326-339`, `:395-397`), `curated_report()`/`unmanaged_report()` for `hermes curator status` (`skill_usage.py:1026-1054`, `:567-589`), and the web dashboard's per-skill `usage` column (`hermes_cli/web_server.py:14669-14688`).

### 3.4 A second, independent telemetry source

`agent/insights.py:298-372` `_get_skill_usage` computes per-skill counts **from scratch** by SQL-scanning `state.db.messages` for assistant `tool_calls` named `skill_view` / `skill_manage` and reading `arguments.name`:

```sql
SELECT m.tool_calls, m.timestamp FROM messages m
  JOIN sessions s ON s.id = m.session_id
 WHERE s.started_at >= ? AND m.role = 'assistant' AND m.tool_calls IS NOT NULL
```

It produces `{skill, view_count, manage_count, last_used_at}` and feeds `_compute_skill_breakdown` (`:735-739`) → `total_skill_loads`, `total_skill_edits`, `distinct_skills_used`, `top_skills`. **Read-only reporting; no decision.** It can be filtered by session `source`, which `.usage.json` cannot. Note it counts *attempts* (the tool call), whereas `.usage.json` counts *successes* (the wrapper only bumps on `parsed["success"]`).

### 3.5 What usage tracking explicitly does NOT do

- **Does not influence discovery.** The index is sorted `(category, name)` alphabetically (`prompt_builder.py:1734, 1746`). `skills_list` likewise (`skills_tool.py:780-782`).
- **Is explicitly forbidden as a consolidation signal.** From the curator's own prompt (`curator.py:452-459`):
  > *"DO NOT use usage counters as a reason to skip consolidation. The counters are new and often mostly zero. Judge overlap on CONTENT, not on use_count. 'use=0' is not evidence a skill is valuable; it's absence of evidence either way. Corollary: 'use=0' is ALSO not a reason to PRUNE a skill."*
- **Is not aggregated across users or machines.** Per-`HERMES_HOME`, per-profile.

---

## 4. Auto-creation — **VERIFIED: YES, three paths**

The answer to the brief's key question is unambiguously yes. Hermes creates and edits skills with no human writing them, and does so on a fixed cadence by default. Here is each path with its trigger, prompt, write path, and approval story.

### 4.1 Path A — the post-turn background review fork (fully autonomous, DEFAULT ON)

**Trigger** (`agent/turn_finalizer.py:633-659`, after the response is delivered):

```python
_should_review_skills = False
if (agent._skill_nudge_interval > 0
        and agent._iters_since_skill >= agent._skill_nudge_interval
        and "skill_manage" in agent.valid_tool_names):
    _should_review_skills = True
    agent._iters_since_skill = 0
...
if final_response and not interrupted and (_should_review_memory or _should_review_skills):
    agent._spawn_background_review(messages_snapshot=list(messages), ...)
```

`_iters_since_skill` increments once per tool-calling iteration (`agent/conversation_loop.py:1323-1327`). Threshold from `skills.creation_nudge_interval`, default **10** (`agent/agent_init.py:1708-1714`); **live value on this machine: 15**. Setting it to `0` disables the path. A parallel copy of the same logic exists for the Codex runtime (`agent/codex_runtime.py:823-857`).

**The fork** (`agent/background_review.py:730-746`, docstring at `:1-17`): a daemon thread constructs a second `AIAgent` that replays the conversation snapshot with:

- `max_iterations=16`, `quiet_mode=True`, `suppress_status_output=True`
- `_memory_write_origin = "background_review"` (`:747`) — the signal §5 keys off
- `_persist_disabled = True`, `_session_db = None` (`:772-774`). The comment names the bug this fixed: without it the fork wrote its harness prompt into the user's real session, and *"On the user's next live turn the agent re-reads that injected user message as a standing instruction and 'becomes' the curator, refusing the actual task."*
- `compression_enabled = False` (`:825`)
- `_cached_system_prompt = agent._cached_system_prompt` when not routed to a different aux model (`:797-806`) — deliberate prompt-prefix-cache reuse, cited as *"~26% end-to-end cost reduction on Sonnet 4.5"*
- a hard **runtime tool whitelist** of the `skills` toolset (+ `memory` iff enabled) (`:837-853`), with deny message *"Background review denied non-whitelisted tool: {tool_name}. Only memory/skill tools are allowed."*
- read-before-write marks reset (`:854-859`)

**The prompt** — `_SKILL_REVIEW_PROMPT`, `background_review.py:181-295` (114 lines). `_COMBINED_REVIEW_PROMPT` (`:297-387`) runs when memory review fires the same turn. Selection at `:989-994`. The operative parts:

> *"Review the conversation above and update the skill library. Be ACTIVE — most sessions produce at least one skill update, even if small. **A pass that does nothing is a missed learning opportunity, not a neutral outcome.**"*

> *"Target shape of the library: CLASS-LEVEL skills, each with a rich SKILL.md and a `references/` directory for session-specific detail. Not a long flat list of narrow one-session-one-skill entries."*

Signals that warrant action (`:190-205`) — note the first one is exactly the JIVO correction case:

> *"User corrected your style, tone, format, legibility, or verbosity. Frustration signals like 'stop doing X', 'this is too verbose', … or an explicit 'remember this' are **FIRST-CLASS skill signals, not just memory signals**. Update the relevant skill(s) to embed the preference so the next session starts already knowing."*
> *"User corrected your workflow, approach, or sequence of steps. Encode the correction as a pitfall or explicit step in the skill that governs that class of task."*
> *"A skill that got loaded or consulted this session turned out to be wrong, missing a step, or outdated. Patch it NOW."*

A strict **preference order** (`:206-244`) — 1. patch a currently-loaded skill; 2. patch an existing umbrella; 3. add a `references/` / `templates/` / `scripts/` support file; 4. **create a new class-level umbrella skill**, with a naming rule: *"The name MUST NOT be a specific PR number, error string, feature codename, library-alone name, or 'fix-X / debug-Y / audit-Z-today' session artifact. If the proposed name only makes sense for today's task, it's wrong."*

The memory/skill boundary is stated crisply (`:245-251`):
> *"Memory captures 'who the user is and what the current situation and state of your operations are'; skills capture 'how to do this class of task for this user'."*

And a **do-NOT-capture list** (`:271-290`) that reads like hard-won production experience:
> *"Environment-dependent failures… Negative claims about tools or features ('browser tools do not work', 'X tool is broken'). **These harden into refusals the agent cites against itself for months after the actual problem was fixed.** … Session-specific transient errors that resolved before the conversation ended. If retrying worked, the lesson is the retry pattern, not the original failure. … One-off task narratives."*

**Write path:** `skill_manage(action="create"|"patch"|"write_file")` → `_create_skill` (`skill_manager_tool.py:833-899`) → `atomic_write_text(skill_dir/"SKILL.md", content)`. On success, `mark_agent_created(name)` fires **only because the origin is `background_review`** (`:1447-1449`).

**Result surfacing:** `summarize_background_review_actions` (`background_review.py:391`, dispatch at `:915-942`) walks the fork's messages and prints e.g. `💾 Self-improvement review: 📝 Skill 'x' created: <desc>`. That one line is the user's entire window into what just happened.

### 4.2 Path B — the weekly curator consolidation pass (fully autonomous)

**Trigger:** `maybe_run_curator()` on CLI startup in a daemon thread (`cli.py:14639-14652`, `idle_for_seconds=float("inf")`) and from the gateway (`gateway/run.py:24642-24648`, grep-confirmed only). Gates (`curator.py:233-283`, `2000-2018`): `curator.enabled` ∧ ¬paused ∧ `now - last_run_at >= interval_hours` ∧ `idle >= min_idle_hours`. Live config: `enabled: true`, `interval_hours: 168` (7 days), `min_idle_hours: 2`. First run is deliberately deferred one full interval (`:241-248`).

Each pass: (1) a pre-run tarball snapshot of the whole skills tree (`agent/curator_backup.py`; live evidence: 5 dirs under `.curator_backups/`, latest `manifest.json` = `{"reason":"pre-curator-run","skill_files":83,"archive_bytes":2759135}`); (2) the pure `apply_automatic_transitions` walk; (3) **optionally** the LLM consolidation pass, gated on `curator.consolidate` — **`false` on this machine**, so it has never run here.

**The prompt** — `CURATOR_REVIEW_PROMPT`, `curator.py:417-570`. It is explicitly a *builder*, not an auditor:

> *"You are running as Hermes' background skill CURATOR. This is an UMBRELLA-BUILDING consolidation pass, not a passive audit and not a duplicate-finder. … A collection of hundreds of narrow skills where each one captures one session's specific bug is a FAILURE of the library — not a feature. An agent searching skills matches on descriptions, not on exact names (note: long descriptions are truncated to 57 chars in the system prompt skill index — keep the trigger class in that window). One broad umbrella skill with labeled subsections beats five narrow siblings for discoverability, not the other way around."*

Method: find **prefix clusters** (*"Expect 10-25 clusters"*), then per cluster pick one of three moves — (a) merge into an existing umbrella, (b) **`skill_manage action=create` a new umbrella**, (c) demote to `references/`/`templates/`/`scripts/`. Bar for keeping things separate is set aggressively: *"'This is narrow but distinct from its siblings' is NOT a reason to keep."* And *"If you end the pass with fewer than 10 archives, you stopped too early."*

Structured output is mandatory — a YAML block splitting every archived skill into `consolidations:` (with `into:`) or `prunings:` (`:549-569`), which drives cron-job skill-reference rewriting.

A `--dry-run` mode prepends `CURATOR_DRY_RUN_BANNER` (`:390-414`) forbidding every mutating call, so *"Your output IS the deliverable"* and a human approves before a live run.

**Live evidence of a real pass** (`~/.hermes/logs/curator/20260727-182444/REPORT.md`, run #12):

```
Model: (not resolved)  ·  Duration: 0s  ·  Agent-created skills: 56 → 56 (+0)
## Auto-transitions (pure, no LLM)
- checked: 56   - marked stale: 26   - archived: 0   - reactivated: 0
## LLM consolidation pass
- tool calls: 0 … ## LLM summary: skipped (consolidation off)
```

### 4.3 Path C — `/learn` (human-triggered, agent-authored)

A registered slash command: `CommandDef("learn", "Learn a reusable skill from anything you describe (dirs, URLs, this chat, notes)", args_hint="<what to learn from>")` (`hermes_cli/commands.py:260-261`).

`agent/learn_prompt.py` (150 lines, read in full) builds **one** prompt that runs as a normal foreground turn. There is *"no separate distillation engine and no model-tool footprint: the agent does the work with its existing toolset, so this works identically on local, Docker, and remote terminal backends"* (`:18-22`). With no argument it defaults to *"the workflow we just went through in this conversation"* (`:112-116`).

Its embedded `_AUTHORING_STANDARDS` (`:30-96`) is the best single artefact in my scope to steal outright. Highlights: the 60-char rule with worked good/bad examples and a "COUNT the characters" instruction; a **privacy rule** — *"author: always the literal value `Hermes`. NEVER fill it from the host environment… Skills get shared and published, so an environment-derived name is a privacy leak the user never opted into"*; a fixed 8-section body order; a "Hermes-tool framing" rule (*"say `read_file` not cat/head/tail, `search_files` not grep/rg/find/ls, `patch` not sed/awk"*); and a quality bar (*"NEVER invent flags, paths, or APIs — if you didn't see it in the source, don't write it"*, ~100–200 lines).

Because `/learn` runs in the **foreground**, `is_background_review()` is false, so `mark_agent_created` is **not** called (`skill_manager_tool.py:1447-1449`). A `/learn`-created skill is therefore user-owned and permanently outside autonomous maintenance. See §5 — this is intentional and it is the single most consequential design decision for the JIVO use case.

### 4.4 Is there a human in the loop?

**By default, no.** `skills.write_approval: false` is the shipped default and the live value. When set to `true`:

- `_apply_skill_write_gate` (`skill_manager_tool.py:1302-1338`) runs before every mutating action and calls `write_approval.evaluate_gate(wa.SKILLS)`.
- Skills **always stage** rather than prompt inline, because *"skills are too large to review inline"* (`:1384-1387`; module rationale at `write_approval.py:26-36`).
- The full `skill_manage` kwargs are written to `~/.hermes/pending/skills/<id>.json` with a one-line `gist` and the `origin` (`foreground` | `background_review`) recorded for audit (`write_approval.py:110-130`).
- Review is out-of-band: `/skills pending | approve | reject | diff | approval` (`hermes_cli/commands.py:245-249`). Approval replays via `apply_skill_pending` with a ContextVar bypass so the gate doesn't re-stage (`skill_manager_tool.py:1341-1360`).
- Failure mode is deliberately fail-*closed*-ish: *"on disk failure it logs and still returns a record (the write is simply lost, which is the safe failure for an approval gate — nothing is silently committed)"* (`write_approval.py:128-130`).

Additionally, `_apply_skill_write_gate` fails **open** if `tools.write_approval` can't be imported (`:1312-1315`).

### 4.5 Six independent brakes on the autonomous writer

All in `skill_manager_tool.py`, all active only when `is_background_review()`:

1. **Class guard** — refuses writes to external-dir, protected-built-in, hub-installed, and bundled skills (`:301-380`).
2. **Ownership guard** — refuses any skill whose record is not `created_by: "agent"`, treating a *missing* record and an explicit `null` identically. The comment documents the bug this fixed (`:381-410`): keying on `isinstance(usage_rec, dict)` made the policy depend on the guard's own side effect — the first write succeeded, called `bump_patch()`, created a `created_by: null` record, and every later write was refused. *"'Allowed exactly once' is not a policy — it is a race with our own bookkeeping."*
3. **Pin guard, stricter than foreground** — pin blocks *content edits* for the fork, not just deletes, *"precisely because there is no user in the loop to consent to an edit here"* (`:320-337`). Foreground pin blocks deletion only (`:274-298`).
4. **Read-before-write** — the fork must have called `skill_view` on the exact target file in this review turn, tracked via a ContextVar of resolved paths (`:55-95`, `:424-451`). Purpose: *"it must not patch or rewrite content it has only inferred from the transcript."* Marks are set from both `skill_view` return paths (`skills_tool.py:1383-1391`, `:1596-1605`).
5. **Consolidation-delete fail-closed** — a curator `delete` **must** declare `absorbed_into=<existing umbrella>`. A bare prune is refused. The docstring names issue #29912: *"the consolidation pass archived whole clusters of active skills with zero verified consolidations, leaving active automations pointing at names that no longer resolve"* (`:463-510`).
6. **Curator deletes are archives, not deletes** — when `is_background_review()`, `_delete_skill` routes through `skill_usage.archive_skill()` instead of `shutil.rmtree`, so `hermes curator restore` can undo it (`:1139-1156`).

Plus, on every path: `_validate_delete_target` (`:213-271`) refuses `rmtree` on a symlink/junction, on a skills root itself, or on anything not strictly inside a known root — an explicit port of Kilo Code issue #11227/#11240, where a built-in-skill sentinel resolved to the server cwd and wiped a working directory.

---

## 5. Provenance — **VERIFIED**

Two cooperating pieces.

**`tools/skill_provenance.py`** (78 lines, read in full) is a single `ContextVar`:

```python
_write_origin: contextvars.ContextVar[str] = contextvars.ContextVar(
    "skill_write_origin", default="foreground")           # :37-40
BACKGROUND_REVIEW = "background_review"                   # :45
def is_background_review() -> bool:                       # :75-78
    return get_current_write_origin() == BACKGROUND_REVIEW
```

The docstring states the whole policy (`:1-14`): *"The curator only consolidates/prunes skills it autonomously created via the background self-improvement review fork. Skills a user asks a foreground agent to write belong to the user and must never be auto-curated."* It piggybacks on `AIAgent._memory_write_origin`, set to `background_review` in the fork (`background_review.py:747`) and `foreground` everywhere else — CLI, gateway, cron, subagents.

**The on-disk marker** is `created_by: "agent"` in `.usage.json`. And here is the finding that matters most:

```python
# skill_usage.py:481-501 (excerpt)
"""NAMING (issue #67140): the on-disk field is ``created_by``, which reads
like provenance but is consumed as a **curator-management opt-in policy
flag**. The two are not the same question:

  * provenance = "who authored this file" — historical fact, and for records
    written before the marker existed it is simply unrecoverable.
  * management = "may autonomous curation mutate/archive this" — a policy
    decision the user can change at any time via ``hermes curator adopt``.

``created_by: "agent"`` therefore means "curator-managed", NOT "proof the
agent wrote it"."""
```

The field name is retained only because *"it is already on disk in every user's `.usage.json`; renaming it would strand those records."* `is_curator_managed()` is the intent-revealing alias (`:504-511`).

**Provenance is a declaration, never an inference** (`skill_usage.py:514-537`): *"Heavy patch or use counts are evidence of maintenance, not of authorship — the agent edits user-authored skills on the user's behalf routinely."* Hence `list_unmanaged_skill_names()` **reports** the blind spot and `hermes curator adopt` requires an explicit user act, with `--all-unmanaged` and a confirmation prompt for bulk (`hermes_cli/curator.py:345-397`). `adopt_skill` refuses hub, external, protected-built-in, and bundled skills, and pointedly **does not reset the inactivity clock** (`skill_usage.py:592-633`).

A separate, coarser classifier for display: `provenance(name) -> "hub" | "bundled" | "agent"` (`skill_usage.py:1068-1078`), where `"agent"` sweeps in hand-written local skills too.

**Why it matters:** it is the entire trust boundary for the autonomous writer. Every one of the six brakes in §4.5 either reads this marker or reads a class derived from the same three side files. Without it the review fork would be free to rewrite bundled and user-authored skills, which is exactly the "wrong assumptions" complaint `write_approval.py:14-16` says motivated the approval gate.

**Live state: 1 of 59 records carries `created_by: "agent"`** — `autonomous-personas`, created 2026-06-17T07:05:30Z, `patch_count: 4`, `use_count: 1`, `state: active`. Its `SKILL.md` on disk is a well-formed class-level skill with `version: 1.0.0`, `metadata.hermes.tags: [swarm, persona, roleplay, autonomous, multi-agent, profiles, playwright]`, `related_skills: [hermes-agent]`, an ASCII architecture diagram, and a "Critical pitfall" section. It also has `references/platform-adapters.md`, `templates/persona-soul.md`, `templates/personas.yaml`. That is the shape the system is aiming for, and it produced it unsupervised. The other 58 records are `created_by: null`.

---

## 6. Guardrails — **VERIFIED**

Two modules, and the boundary between them is explicit.

### 6.1 `tools/skills_guard.py` — regex + structural scanner, "useful, not boundaries"

`SCANNER_VERSION = "skills-guard-v1"` (`:35`). **~140 threat patterns** across 14 categories (`THREAT_PATTERNS`, `:101-521`):

`exfiltration` (curl/wget/fetch/httpx/requests interpolating `KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API`; `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.kube`, `~/.docker`, **`~/.hermes/.env`**; `printenv`; `os.environ`; DNS exfil via `dig $VAR`; markdown-image exfil `![](https://…${`; "output the conversation history"); `injection` (~20 patterns: ignore-previous, role hijack, "do not tell the user", DAN mode, developer mode, hidden HTML comments, `display:none` divs); `destructive` (`rm -rf /`, `mkfs`, `dd of=/dev/`, `> /etc/`); `persistence` (crontab, shell rc files, `authorized_keys`, systemd, launchd, sudoers, `git config --global`, **and `AGENTS.md|CLAUDE.md|.cursorrules|.clinerules` at `critical`** — *"could persist malicious instructions across sessions"*, `:461-463`); `network` (reverse shells, ngrok, `webhook.site`); `obfuscation` (base64-pipe, `eval("…")`, `chr()+chr()`, unicode-escape chains); `execution`; `traversal`; `mining`; `supply_chain` (`curl | sh`, unpinned `pip install`, `uv run`, `git clone`); `privilege_escalation`; `credential_exposure` (live regexes for `ghp_`, `sk-`, `sk-ant-`, `AKIA`, PEM headers).

Plus:
- **17 invisible/bidi unicode codepoints** flagged at `high` (`INVISIBLE_CHARS`, `:541-560`) — ZWSP, ZWJ, BOM, RTL override, isolates.
- **Structural checks** (`_check_structure`, `:864-990`): `MAX_FILE_COUNT = 50`, `MAX_TOTAL_SIZE_KB = 1024`, `MAX_SINGLE_FILE_KB = 256` (`:523-526`); binary extensions (`.exe .dll .so .dylib .bin .dat .com .msi .dmg .app .deb .rpm`) at `critical`; **symlink escaping the skill dir** at `critical`; executable bit on a non-script file at `medium`.
- Scan scope: 25 text extensions plus always `SKILL.md` (`:529-533, 581-582`). A `.skillignore` / `.clawhubignore` can exclude dev artefacts, gitignore-style — but *"Patterns cannot un-ignore the skill's own `SKILL.md`, which is always scanned"* (`:641-647`, `_NEVER_IGNORABLE` at `:1030`).

**Verdict** (`_determine_verdict`, `:1131-1144`): any `critical` → `dangerous`; else any `high` → `caution`; else `safe`. *Medium and low findings alone are informational and never block.*

**Trust-aware install policy** (`:55-65`):

```python
INSTALL_POLICY = {          # safe      caution    dangerous
    "builtin":            ("allow",  "allow",   "allow"),
    "trusted":            ("allow",  "allow",   "block"),
    "community":          ("allow",  "block",   "block"),
    "agent-created":      ("allow",  "allow",   "ask"),
}
```

`TRUSTED_REPOS = {openai/skills, anthropics/skills, huggingface/skills, NVIDIA/skills}` (`:44-53`), matched exactly or as a path prefix — *"Do not trust sibling repositories that merely share a prefix"* (`:1125-1127`). `--force` overrides a block **except** a `dangerous` verdict from community/trusted (`should_allow_install`, `:766-807`). `scan_skill_cached` binds an attestation (`bundle_hash`, `scanner_version`, `rules`, `verdict`) to the exact content SHA-256, so a cache hit can't survive a content change (`:716-763`).

**Where it actually runs:**
- **Every hub install**, always, in quarantine before the move (`skills_hub.install_from_quarantine` is called only after a scan; audit line records the verdict, `:3562-3566`).
- **`hermes skills audit [--deep]`** re-scans installed hub skills (`hermes_cli/skills_hub.py:1100-1143`).
- **`hermes skills publish`** self-scans and refuses a `dangerous` verdict (`hermes_cli/skills_hub.py:1515-1521`).
- **Agent-created skills: only if `skills.guard_agent_created` is true — default `false`.** The rationale is stated plainly (`skill_manager_tool.py:106-113`): *"Off by default because the agent can already execute the same code paths via terminal() with no gate, so the scan adds friction without meaningful security."* When on, a block triggers a **rollback**: create `shutil.rmtree`s the new dir (`:869-873`); edit/patch/write_file restore the original bytes (`:930-935`, `:1052-1056`, `:1221-1228`).

Live value on this machine: `guard_agent_created: false`.

### 6.2 `tools/skills_ast_audit.py` — opt-in diagnostic, explicitly not a gate

133 lines, read in full. The docstring draws the line itself (`:1-11`):

> *"Per SECURITY.md §2.4, Skills Guard is in-process heuristics ('useful — not boundaries'). This module is a separate opt-in diagnostic that flags dynamic import / dynamic attribute access patterns operators may want to eyeball… Every pattern flagged here has legitimate uses; **findings are hints for human review, not verdicts**."*

An `ast.NodeVisitor` over `*.py` flagging 5 patterns: `importlib.import_module()`, `__import__(<non-literal>)`, `getattr(obj, <non-literal>)`, `obj.__dict__[<computed>]`, and any `import importlib` (`:33-73`). Handles hostile input by returning partial results on `RecursionError` (`:75-79`). Surfaced only via `hermes skills audit --deep` (`hermes_cli/skills_hub.py:1128-1141`), and the report footer repeats: *"diagnostic hints for human review, not security verdicts"* (`:132`).

### 6.3 A third layer nobody advertises: `skill_view`'s own injection check

`skills_tool.py:1249-1260` scans loaded content against a 9-item `_INJECTION_PATTERNS` list (`:231-241`) and checks whether the file lives outside every trusted root. **Both are log-only.** The content is returned to the model regardless:

```python
if _outside_skills_dir or _injection_detected:
    ...
    logging.getLogger(__name__).warning("Skill security warning for '%s': %s", name, "; ".join(_warnings))
```

Genuine hard refusals on the read path: path traversal in `name` and Windows drive paths (`:179-203`, `:987-996`), traversal in `file_path` plus a resolved-within-dir check (`:1294-1319`), platform incompatibility (`:1268-1276`), user-disabled (`:1280-1290`), and **name-collision ambiguity** — if a bare name matches in more than one root, `skill_view` refuses rather than guessing, because *"silent shadowing of a local skill by a same-named external skill is a real bug class (`/skills` shows one, agent loaded the other)"* (`:1101-1204`).

### 6.4 What a skill is forbidden from doing — the honest answer

Nothing, at runtime. A `SKILL.md` is markdown injected into the context; the model then acts through its ordinary tools with its ordinary permissions. There is no sandbox, no capability declaration that is enforced (`allowed-tools` is explicitly demoted to informational), no per-skill tool restriction. Every guardrail described above is **install-time and author-time static analysis**, plus one runtime code path (`skills.inline_shell`) that is off by default. `skills_guard.py`'s docstring is candid: it exists so *"every skill downloaded from a registry passes through this scanner before installation"* (`:5-7`) — the threat model is a **hostile third-party skill**, not a hostile local one.

---

## 7. Distribution — **VERIFIED**

Three orthogonal mechanisms.

### 7.1 The Hub — a pull-based multi-registry client

`tools/skills_hub.py` (4151 lines). Two dataclasses (`:130-152`): `SkillMeta {name, description, source, identifier, trust_level, repo, path, tags, extra}` and `SkillBundle {name, files: {rel_path -> str|bytes}, source, identifier, trust_level, metadata}`. An ABC with four methods — `search`, `fetch`, `inspect`, `source_id`, plus `trust_level_for` (`:474-499`).

**Nine adapters** (`create_source_router`, `:3982-4005`), in priority order: `OptionalSkillSource` (repo-bundled optional skills), `HermesIndexSource` (`https://hermes-agent.nousresearch.com/docs/api/skills-index.json`, 6h TTL, `:3700-3701`), `SkillsShSource`, `WellKnownSkillSource`, `UrlSource`, `GitHubSource` (7 default taps + user taps), `ClawHubSource`, `LobeHubSource`, `BrowseShSource`.

Search is parallel with a 30s overall timeout on a daemon pool capped at 8 workers, then deduped by `identifier` preferring higher trust (`_TRUST_RANK = {builtin:2, trusted:1, community:0}`, `:4019-4151`). A neat optimisation: when the centralized index is available and no source filter is set, the five external API sources are skipped entirely — *"This avoids ~70 GitHub API calls per search for unauthenticated users"* (`:4048-4068`).

**Install pipeline:** `fetch` → `quarantine_bundle` (path-validated writes into `.hub/quarantine/<name>/`, `:3459-3481`) → `scan_skill` → `should_allow_install` → `install_from_quarantine` (`:3484-3568`), which re-validates the install path, **refuses any symlink inside the bundle** (*"its target contents would then be copied into skills/ and leaked to the agent on the next skill_view call"*, `:3529-3542`), moves it into place, records the lock entry, and appends the audit line.

**Versioning** is content-hash, not semver. `HubLockFile` (`:3302-3369`) writes per-skill: `source`, `identifier`, `trust_level`, `scan_verdict`, `content_hash` (`sha256:<16 hex>`), `install_path`, `files[]`, `metadata`, `scan_provenance`, `installed_at`, `updated_at`. The frontmatter `version:` field is **never** consulted for update decisions. `check_for_skill_updates` (`:3625-3693`) re-fetches the bundle and compares `bundle_content_hash` — which mixes relative paths into the digest *"so swapping file contents between two paths changes the hash (avoids filename-swap evading update detection)"* (`:3601-3614`), and must stay symmetric with the on-disk `content_hash` (`skills_guard.py:846-857`).

**Conflict resolution** in the hub is deliberately blunt: `do_update` re-installs with `force=True`, **overwriting local edits**, but pinned to the lockfile's recorded `source_id` — *"An update must never change a skill's provenance"* (`hermes_cli/skills_hub.py:1082-1095`). When no adapter matches the recorded source, the entry is reported `unavailable` rather than satisfied from another registry, because *"Skill names are not namespaced across registries, so that fallback is unsafe by construction"* (`skills_hub.py:3647-3653`).

Provenance is also protected on the *local* side: `uninstall_skill` refuses non-hub skills, `restore_skill` refuses to restore over a hub-installed name (*"restore would shadow the upstream version"*, `skill_usage.py:925-929`), and `_resolve_lock_install_path` walks the path component-by-component refusing symlink redirects before any `rmtree` (`skills_hub.py:265-291`).

`.hub/audit.log` is append-only, one space-separated line per action: `<ISO8601Z> INSTALL|UNINSTALL <name> <source>:<trust> <verdict> [extra]` (`:3421-3435`). Empty on this machine (the 8 lock entries were backfilled, not installed).

### 7.2 Bundled-skill sync — the three-way merge (the mechanism JIVO should copy)

`tools/skills_sync.py`, docstring `:1-22`, implementation `sync_skills` `:675-948`. Manifest v2 is `~/.hermes/skills/.bundled_manifest`, one `skill_name:md5_of_bundled_dir_at_last_sync` per line — **70 entries live**. The `origin_hash` is what makes a genuine three-way merge possible:

| manifest | on disk | bundled vs origin | user vs origin | action |
|---|---|---|---|---|
| absent | absent | — | — | copy; record `bundled_hash` |
| absent | present, identical | — | — | skip; baseline the manifest |
| absent | present, **differs** | — | — | **skip and do NOT baseline** — recording the hash *"would poison update detection by making user_hash != origin_hash read as 'user-modified' on every subsequent sync, permanently blocking bundled updates"* (`:806-813`) |
| present | present | unchanged | — | skip **without hashing the user copy** (`:840-847`) |
| present | present | changed | unchanged | **update** via move-to-`.bak` → copytree → remove backup, with full restore-on-failure (`:869-907`) |
| present | present | changed | **changed** | **skip** — report `user_modified` (`:862-867`) |
| present | absent | — | — | user deleted it — respected, never re-added (`:914-916`) |
| gone from bundle | — | — | — | cleaned from manifest (`:918-921`) |

Plus four recovery paths I did not expect to find and which are exactly the kind of thing a naive reimplementation gets wrong: orphaned `.bak` recovery from an interrupted prior update (`:744-754`); **upstream rename/recategorisation** recovery, because the manifest key is the frontmatter name which survives a directory move while `dest` is a brand-new path (`:756-774`); curator-suppression (`.curator_suppressed` names are never re-seeded, *"Without this skip, every `hermes update` would resurrect a skill the user deliberately pruned"*, `:726-733`); and external-dir deference with self-healing removal of a stale local shadow **only when it is byte-identical to bundled** (`:776-799`).

Companion CLI: `hermes skills list-modified` (`list_user_modified_bundled_skills`, `:1111`), `hermes skills diff <name>` (`:1167`), `hermes skills reset <name>` (`:1000`), `hermes skills opt-out/opt-in` (`:1266`, `:1363`, marker file `.no-bundled-skills`).

### 7.3 Publish, snapshot, and self-hosting

- **`hermes skills publish <path> --to github --repo owner/repo`** — self-scans, refuses `dangerous`, then `_github_publish` opens a PR (`hermes_cli/skills_hub.py:1479-1546`). ClawHub publishing is a stub.
- **`hermes skills snapshot export|import`** (`:1646-1730`) — a portable JSON of `{hermes_version, exported_at, skills:[{name, source, identifier, category}], taps:[…]}`. Import restores taps then re-installs each identifier. It records **pointers, not content**, so it only reproduces hub-installed skills; locally authored skills are not captured.
- **`WellKnownSkillSource`** (`:1196-1290`) — point Hermes at a domain serving `/.well-known/skills/index.json` with `[{name, description, files:[…]}]` and it becomes a registry. This is the cheapest self-hosted-registry path in the whole system and needs no Hermes-side code.
- **`TapsManager`** (`:3376-3414`) — `.hub/taps.json` = `{"taps":[{"repo":"owner/repo","path":"skills/"}]}`. Live: `{"taps": []}`.
- **`skills.external_dirs`** (`skill_utils.py:434-525`) — mount a shared directory (e.g. an NFS or git-cloned path) read-only into discovery. Local names win on collision; the curator treats them as read-only on every path.

**The gap:** none of this is multi-user. There is no notion of user identity, no shared usage aggregation, no push, no merge of two evolved copies of the same skill. Every mechanism is one machine pulling from a source of truth it does not write back to.

---

## 8. Live-state audit of this machine — **VERIFIED**

| fact | value |
|---|---|
| skills discovered with valid frontmatter | 127 (in 64 top-level entries, 17 of them symlinks to `~/.agents/skills/`) |
| bundled built-ins tracked | 70 (`.bundled_manifest`) |
| hub-installed | 8 (all `source: official`, `trust_level: builtin`, `scan_verdict: backfilled`, `backfilled_from: optional-skills`) |
| taps configured | 0 |
| `.usage.json` records | 59 |
| records with `created_by: "agent"` | **1** (`autonomous-personas`) |
| records `pinned` | 0 |
| states | 32 `active`, 27 `stale` |
| total `use_count` / `view_count` / `patch_count` | 53 / 53 / 9 |
| curator runs | 12; last `2026-07-27T18:24:44Z`, 0.51s, `"auto: 26 marked stale; llm: skipped (consolidation off)"` |
| curator backups retained | 5 (weekly, `keep: 5`), latest 2.76 MB / 83 skill files |
| `.hub/audit.log` | empty |
| `.archive/` | does not exist — nothing has ever been archived |
| skill tables in `state.db` | **none** |
| prompt-index block size | 15,452 chars ≈ 3.9–4.3k tokens |
| truncated descriptions | **47 / 127 (37%)** |

Config (`~/.hermes/config.yaml:409-427`):

```yaml
skills:
  external_dirs: []
  template_vars: true
  inline_shell: false
  inline_shell_timeout: 10
  guard_agent_created: false
  write_approval: false
  creation_nudge_interval: 15
curator:
  enabled: true
  interval_hours: 168
  min_idle_hours: 2
  stale_after_days: 30
  archive_after_days: 90
  consolidate: false
  prune_builtins: true
  backup: {enabled: true, keep: 5}
```

**Reading of this state:** the *deterministic* half of the system is running (lifecycle transitions, backups, weekly passes) and the *generative* half is almost entirely dormant. 26 skills were marked stale on the last pass. `consolidate: false` means the LLM umbrella pass has never run. Exactly one skill was ever autonomously created — six weeks ago. Two candidate explanations, and I cannot distinguish them from the artefacts on disk: (a) `creation_nudge_interval: 15` plus the prompt's own do-not-capture list makes the review pass genuinely conservative; (b) the review pass fires often but its writes are being refused by the §4.5 ownership guard (58 of 59 records are `created_by: null`, and once a skill is unmanaged the fork can never touch it). Distinguishing them requires the agent log, which I did not read.

**Also note the trap this creates:** because `mark_agent_created` only fires from the fork, the population of curator-writable skills can only ever grow through the fork itself or through explicit `hermes curator adopt`. A library seeded by `/learn` and foreground `skill_manage` — which is what an office deployment would actually produce — is permanently unmaintained by design.

---

## 9. How I'd reimplement this in a Claude Code harness

Claude Code gives us: `SKILL.md` + frontmatter skills, hooks (`SessionStart`, `PostToolUse`, `PreToolUse`, `Stop`/`SessionEnd`), `CLAUDE.md`, subagents (`.claude/agents/*.md`), MCP servers, and — in this harness — a file-based memory dir with a `MEMORY.md` index. Mapping, honestly:

| Hermes mechanism | Ports to Claude Code? | How |
|---|---|---|
| SKILL.md + frontmatter | **1:1** | Same file, same `name`/`description`. Keep `metadata:` for anything Hermes-specific. |
| Category dirs + `DESCRIPTION.md` | **partial** | Claude Code namespaces plugin/dir-scoped skills but has no category blurb. Encode the class in the description instead. |
| 60-char description budget | **N/A, and don't copy it** | Claude Code injects *full* descriptions in its available-skills listing (visible in this very session — multi-sentence with trigger phrases). Copying the 60-char cliff would throw away routing signal for no benefit. **Do copy the *discipline*: trigger-first, self-contained first sentence.** |
| Two-layer prompt cache + snapshot | **no equivalent, and unnecessary** | Claude Code owns discovery injection; we can't insert a cache layer, and there is nothing to cache. |
| Conditional activation (`requires_tools` etc.) | **no equivalent** | Claude Code has no frontmatter tool-gating. Best approximation: a `SessionStart` hook that emits "the sapb1 CLI is unreachable, skip SAP skills this session" as context. |
| Platform gating | **no equivalent** | Put the OS check in the skill body's first line instead. |
| `skill_view(name, file_path=…)` tier 3 | **1:1** | Claude Code skills already load `references/` on demand via `Read`. Keep the `references/` / `templates/` / `scripts/` convention verbatim — it is the single most transferable idea in the whole codebase. |
| `${HERMES_SKILL_DIR}` template vars | **partial** | Claude Code resolves skill-relative paths; a `SessionStart` hook can export a var if needed. |
| `` !`cmd` `` inline shell | **skip** | Code execution from a markdown file. Off by default in Hermes for good reason. |
| **Usage tracking** | **buildable, and this is the first thing to build** | `PostToolUse` hook matching the `Skill` tool → read args, append to `.claude/skill-usage.json` under an flock, same record shape as `_empty_record()`. This is ~60 lines and it is the substrate everything else needs. |
| Lifecycle state machine | **buildable** | Port `apply_automatic_transitions` verbatim as a script; run it from `SessionStart`, gated on a `.curator_state` interval file. Keep every grace clause: pin, cron-referenced, first-sight seeding, and the `use_count == 0` floor. |
| **Auto-creation (background fork)** | **buildable, but the cache trick does not port** | A `SessionEnd`/`Stop` hook that shells `claude -p "<review prompt>" --allowed-tools Skill,Write,Edit` against the transcript. What you lose: Hermes reuses the parent's byte-identical cached system prompt for a ~26% cost saving; a fresh `claude -p` is a cold prefix. Mitigation: pass a **digest** of the transcript rather than the whole thing — Hermes already does exactly this on its routed-aux-model path (`_digest_history`, `background_review.py:122-163`: keep the last 24 messages verbatim, collapse the rest into one synthetic user turn). |
| Runtime tool whitelist for the fork | **1:1** | `--allowed-tools` on the headless call is stronger than Hermes' in-process registry whitelist. |
| Read-before-write guard | **buildable** | A `PreToolUse` hook on `Write`/`Edit` under `.claude/skills/` that refuses unless the same path appears in a `Read`/`Skill` result earlier in the transcript. |
| Provenance (`created_by`) | **1:1** | Same sidecar field. **Copy the naming lesson, not the name**: call it `curator_managed`, not `created_by`. Hermes is stuck with the wrong name and documented 20 lines of apology about it. |
| `skills_guard` regex scan | **buildable** | `PreToolUse` hook on `Write|Edit` where the path is under `.claude/skills/`. The 140-pattern table transfers wholesale. So does the trust×verdict matrix — replace `builtin/trusted/community` with `central-repo/reviewed/agent-created`. |
| AST audit | **1:1** | Standalone script; the module is 133 lines and has no Hermes dependencies. |
| Injection-pattern warning on load | **skip as designed** | Log-only in Hermes, so it buys nothing. If you want it, make it blocking. |
| Skill bundles (`/backend-dev` = 3 skills) | **partial** | Claude Code slash commands can reference multiple skills; a `.claude/commands/*.md` that says "load skills A, B, C" is the closest analogue. |
| Hub (9 registries, quarantine, lock) | **skip entirely** | Massive surface for one office. |
| **`skills_sync` origin-hash three-way merge** | **buildable, and this is the second thing to build** | This is the multi-user answer. See §9.7. |
| Snapshot export/import | **superseded by git** | |

### 9.1 Concrete build order for `jivo-cli`

1. **Fix descriptions first, before any automation.** Every skill's first sentence must be trigger-first and self-contained: `Use when someone asks for a party's ledger balance or outstanding. Reads BusinessPartners.CurrentAccountBalance.` This is free and it is what makes step 4 work.
2. **Usage sidecar** — `PostToolUse` on `Skill` → `.claude/skill-usage.json`. Do it before anything else; you cannot tune what you cannot measure. Learn from Hermes' mistake and **do not bump two counters from one event** — pick `use` and drop `view`, or record the invocation *surface* (`tool` / `slash` / `preload`) as a field.
3. **Lifecycle script** — port `apply_automatic_transitions`. Run from `SessionStart` behind a 7-day interval file. Archive to `.claude/skills/.archive/`, never delete.
4. **Guard hook** — `PreToolUse` on writes under `.claude/skills/`. Turn it **on** for agent-created skills, unlike Hermes. Hermes' rationale for defaulting it off ("the agent can already run the same code via terminal") does not hold here: your CLIs are read-only by RULE 0, so a skill that tells a future agent to write is the exact failure you need to catch, and the `AGENTS.md|CLAUDE.md` persistence pattern (`skills_guard.py:461-463`) is directly relevant.
5. **Review fork** — `SessionEnd` hook → `claude -p` with a JIVO-adapted `_SKILL_REVIEW_PROMPT`. Start with `write_approval` semantics **on**: stage to `.claude/pending/skills/*.json`, surface via a `/skills-pending` command. Turn staging off only after a few weeks of reading what it proposes.
6. **Central repo + origin-hash sync** — §9.7.

### 9.2 The two prompts to lift almost verbatim

`_SKILL_REVIEW_PROMPT` (`background_review.py:181-295`) and `_AUTHORING_STANDARDS` (`learn_prompt.py:30-96`). The four pieces that carry the value:

- **"A pass that does nothing is a missed learning opportunity, not a neutral outcome."** Without this, review passes return "Nothing to save" ~100% of the time.
- **The preference order** (patch loaded → patch umbrella → add support file → create new). This is what prevents the 300-narrow-skills failure the curator prompt calls *"a FAILURE of the library — not a feature."*
- **The do-not-capture list** (`:271-290`). For JIVO this needs one addition: *"never capture a specific balance, a specific party's number, or a period's total — capture the query shape and the definition."* A skill that hardcodes "Blessing Advertising owes ₹X" is wrong within a day.
- **The class-level naming rule.** For JIVO: `sap-party-ledger-lookup`, not `blessing-advertising-balance-jul-2026`.

Add one JIVO-specific rule that has no Hermes analogue: **RULE 0 propagation** — any generated skill must state that its commands are read-only and must not introduce a write path. That belongs in both the authoring standards and the guard's pattern table.

### 9.3 What has genuinely no equivalent

- **Warm-cache forking.** Hermes' review fork reuses the parent's byte-identical cached system prompt, `tools[]`, and reasoning config to hit the same provider prefix cache. A headless `claude -p` cannot do this. Budget for it or use digests.
- **Frontmatter-driven conditional activation.** No hook point.
- **A registry client.** Nor should you want one.
- **Runtime per-skill tool restriction.** Neither system has it; Hermes' `allowed-tools` field is decorative.

### 9.4 Where Hermes' design would actively hurt JIVO

1. **The 60-char truncation.** Do not port it. Claude Code shows full descriptions.
2. **Foreground creates are unmanaged forever.** In an office deployment, nearly every skill will be born from "hey, make a skill for this" — i.e. foreground. Under Hermes' rule they are all `created_by: null` and invisible to maintenance. **Invert the default**: mark everything created inside the repo as managed, and let a user opt a skill *out* with `pinned: true`.
3. **Usage counters barred from consolidation decisions.** Hermes bars them because its counters are new and mostly zero. Yours will not be — Accounts asking the same question 40 times a month is precisely the signal you want. Ignore `curator.py:452-459` for your case, but keep its corollary: `use=0` is not evidence for pruning.
4. **Weekly cadence + 2h idle gate.** Fine for one laptop; wrong for a team. Run consolidation nightly on one machine against the shared repo, not on every fork.
5. **One category per flat skill.** Put skills in real categories (`sap-accounts/`, `sap-sales/`, `ecom/`) from day one.

### 9.5 The mechanism the brief is asking for, which Hermes does not have

**Nothing in Hermes detects a recurring question shape.** I looked for it specifically. The signals that fire a skill review are: a tool-iteration count, and an LLM's per-session judgement about corrections and novel technique. `agent/insights.py` aggregates skill *loads* across sessions, but it feeds a report, not a decision. The curator clusters **skills that already exist** by name prefix — not questions, and not across users.

To get what you want you must build it. The cheapest version that would work:

- A `UserPromptSubmit` hook appends `{ts, user, sha256(normalized_prompt), first_120_chars}` to `.claude/question-log.jsonl`. Normalize aggressively: lowercase, strip digits and date literals, strip quoted party names. That normalization *is* the "shape."
- A nightly job buckets shapes, and for any bucket with ≥ N distinct sessions (start N=5) and no covering skill, hands the bucket's exemplars to a `claude -p` call with the authoring standards and `--allowed-tools Write` scoped to `.claude/skills/`.
- The output stages for human approval before landing in the shared repo.

That is roughly 200 lines plus a prompt, and it uses Hermes' authoring standards, its guard, and its sync merge — but its trigger is frequency, which is the part Hermes never built.

### 9.6 Multi-user usage aggregation

`.usage.json` is per-machine. For an office you want one number per skill across all forks. Simplest shape that works: each fork writes `.claude/skill-usage.json` locally, and a `SessionEnd` hook appends **append-only event lines** (`{ts, machine, skill, event}`) to a shared file or a small table. Never sync the aggregate record itself — you will get last-write-wins clobbering. Aggregate events; derive counters. Hermes never had to solve this, so there is nothing to port.

### 9.7 The sync design for many office users

This is the part of Hermes worth copying most carefully, because §7.2 is a real solution to "a central skill set evolves while local users edit it."

- Central `jivo-skills` git repo is the "bundled" source.
- Each fork keeps `.claude/skills/.bundled_manifest` — `skill_name:sha256_of_central_dir_at_last_sync`.
- `hermes update`'s equivalent is a `SessionStart` hook (or a `make sync-skills`) running the §7.2 table verbatim: **update only when central changed AND the local copy still matches the recorded origin hash.** Otherwise report `user_modified` and leave it alone.
- Port all four recovery paths — orphaned-`.bak`, rename-recovery keyed on frontmatter name, suppression list, and the identical-shadow self-heal. Each one exists because it broke in production for someone.
- Provide the companion commands: `list-modified`, `diff <name>`, `reset <name>`. Without `diff`, a `user_modified` report is a dead end.
- Promotion path: a fork's locally-proven skill gets PR'd to central (Hermes' `skills publish`, minus the registry). Once merged, the local copy converges to the central hash on the next sync and stops being `user_modified`. That closes the loop the brief asks for: one person's correction becomes everyone's skill.

---

## Open questions

1. **Why has exactly one skill ever been autonomously created on this machine?** I can see the trigger config (`creation_nudge_interval: 15`), the prompt, and the outcome, but not the intermediate behaviour. The distinguishing evidence is in `~/.hermes/logs/agent.log` (how often the review fork actually fired, and whether its `skill_manage` calls were refused by the ownership guard). I did not read it.
2. **Actual token cost of the index.** I measured 15,452 characters exactly. The token figure is a chars/token estimate — `tiktoken` is not installed. Someone with a tokenizer should confirm; my 3.6–4.0 range could be off by ±15% on a table-heavy string.
3. **Does the curator's LLM consolidation pass work in practice?** `consolidate: false` here, so it has never run on this machine and I have zero empirical evidence for it. Everything in §4.2 is read from source and from the prompt text. Given the fail-closed guards added for issue #29912 (`skill_manager_tool.py:463-510`), it has clearly misbehaved badly at least once upstream.
4. **`hermes_state.py:324-358` `_is_background_review_harness_message`.** I grepped it but did not read it. It appears to filter the review fork's harness turn out of session recall; if so it is a second layer of the persistence-isolation fix at `background_review.py:761-774`. Unverified.
5. **Symlinked skills under `~/.agents/skills/`.** 17 of this machine's skills are symlinks into a directory shared with other agents (Claude Code among them). `os.walk(followlinks=True)` means Hermes discovers them as *local*, so they are curator-eligible and the background fork could write into them if adopted. Whether that has ever happened, and whether upstream considers it a bug, I could not determine. `is_external_skill_path` resolves the path — but only against configured `external_dirs`, which is `[]` here, so the symlink target gets no protection.
6. **Snapshot invalidation on curator archive.** `skill_usage.archive_skill()` moves a directory without calling `clear_skills_system_prompt_cache`. I believe the passive manifest check catches it on the next cold render, but I did not verify that a live in-process LRU entry (layer 1) is also invalidated — layer 1 is keyed on config/tools/platform, not on filesystem state, so a long-lived process could serve a stale rendered index after an archive. Inferred, not tested.
7. **Whether `skills.write_approval: true` actually intercepts the background fork.** `_apply_skill_write_gate` is called from `skill_manage` (`skill_manager_tool.py:1388`) and `write_approval.evaluate_gate` forces staging when `subsystem == SKILLS or background` (`write_approval.py:281`), so it should. I did not exercise it, and the gate fails **open** on an import error (`skill_manager_tool.py:1312-1315`), which is the wrong direction for a safety gate.
8. **`dependencies:` frontmatter (16 skills) and `min-binary-version:` (4).** I found no Hermes code reading either. They may be consumed by a path I only grepped (`cli.py`, `web_server.py`) or they may be dead imports from other ecosystems. Unresolved.
9. **`agent/skill_bundles.py`** — I read the docstring and the function map but not the implementation. `build_bundle_invocation_message` is the only place besides `skill_commands.py` that bumps usage, and the bundle-vs-skill slash-name conflict resolution ("the bundle wins") is documented but unverified by me.
10. **Whether any deployment actually runs `guard_agent_created: true`.** The default is off and the stated rationale ("the agent can already run the same code via terminal") suggests upstream does not expect anyone to turn it on. If so, agent-authored skills are effectively unscanned everywhere, and the §6 threat model covers only third-party imports.
