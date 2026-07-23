---
title: "JIVO Factory → Data Bank: Multi-Phase Plan"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: plan
tags: [jivogpt, factory-cli, plan]
---

# JIVO Factory → Data Bank: Multi-Phase Plan

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

**Goal #14.** Fuse the Jivo Mart (JIVO_MART) factory app into `jivo-data-bank` as a 4th
data pillar, using the *same formula* as the previous app (jivo-intel → jivo-data-bank).

## The formula (copied from the previous app)
CLI/API  →  lossless linked Obsidian **source vault** (one note per entity + MOC hubs + wikilinks)
→  fuse into `jivo-data-bank` (verbatim copy + generated backbone + **fail-closed** verify + commit).

## Where we are
- ✅ **Aim #1 — CLI DONE.** `jivo-factory-pp-cli` (printing-press, 19 resources / 152 verified GET
  endpoints, `Company-Code: JIVO_MART`, bearer auth, hand-authored `auth login`). Installed, doctor green.
- ▶️ **Aim #2 — Import the data** (the rest of this plan).

## The 4 data pillars (target end-state of jivo-data-bank)
1. `ecom/`   — the scrapers (competitor prices)        [exists]
2. `jivo/`   — the ecom.jivo.in app (jivo-intel)        [exists]
3. `factory/`— the ji.jivo.in factory app (NEW)         [this work]
   + the SAP-code bridge ties factory finished-goods → existing product nodes (a manufacturing lens).

---

## Phases (each with its orchestration mechanism)

### Phase A — Design the factory vault schema  ·  *agents (small) + workflow*
Understand each Jivo Mart domain's data + relationships, then design the entity-per-note schema.
- A **Workflow** fans out one reader-agent per domain group (fleet, vehicles, gate, QC, GRPO,
  barcode/traceability, PO, production, maintenance, wms, dashboards) → each returns: entity list,
  key fields, and the cross-entity links (vehicle↔driver↔transporter↔gate-arrival↔GRPO↔PO-vendor;
  box↔pallet↔dispatch-session↔SKU).
- Synthesis stage → `vault-schema.md`: frontmatter shape, note-per-entity layout, MOC hubs, the
  wikilink graph, and the SAP-code bridge points (finished-goods → product nodes).

### Phase B — Lossless capture  ·  *fleet (parallel, deterministic)*
Pull ALL Jivo Mart data via the CLI (fresh, `--no-cache`), one worker per domain group → raw JSON in
`jivo-factory-intel/raw/`. Mechanical + parallel; the fleet just divides the 152 endpoints and
handles pagination/edge cases. Output: complete raw capture + a manifest (counts per endpoint).

### Phase C — Render the linked vault  ·  *workflow (deterministic renderer + agent QA)*
A Python renderer (modeled on jivo-intel's `bin/`) converts raw JSON → `factory/` Obsidian vault:
one `.md` per entity (frontmatter + body + `[[wikilinks]]`) + MOC hub per domain + a Home MOC.
An agent QA stage verifies link integrity + lossless coverage (every raw record → a note).

### Phase D — Fuse into the data bank (4th pillar)  ·  *solo + fail-closed verify*
Extend `jivo-data-bank/bin`: `combined_migrate.py` copies `factory/` verbatim (sha256 zero-loss);
`combined_backbone.py` bridges factory FG SAP codes → product nodes (manufacturing lens) + builds
new-entity hubs (Vehicles, Gate, QC, Production, Maintenance, Traceability); `verify_databank.py`
gains a factory zero-loss gate; update rsync protect-list + baseline. Rebuild → fail-closed verify →
commit (owner pushes with `!`).

### Phase E — Semantic cross-linking + adversarial verification  ·  *fleet/workflow*
Agent pass discovers cross-vault semantic links (factory FG ↔ its competitor-price lens ↔ its JIVO
volume lens) and writes them to the `.links/` cache. Adversarial verify stage: confirm zero-loss,
link integrity, no fabrication, before the final commit.

## Guardrails
- **Read-only & lossless**, fail-closed (would rather ship correct-yesterday than wrong-today).
- **Max-plan rate limits:** keep fleet fan-out modest (domain-grouped workers, not 152 parallel).
- **Never write secrets** to git; the token stays 0600 in ~/.config.
- **Owner pushes** the data-bank commit with `!` (classifier blocks Claude pushing ecom/factory data).
- Jivo Mart only (JIVO_MART) for now; Jivo Oil / Beverages are out of scope.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
