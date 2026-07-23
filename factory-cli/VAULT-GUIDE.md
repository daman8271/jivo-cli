---
title: "VAULT-GUIDE — how to read & navigate the factory vault"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: guide
tags: [jivogpt, factory-cli, vault]
---

# VAULT-GUIDE — how to read & navigate the factory vault

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

This is the manual for actually reading `vault/` to gather data and make sense of it. Read
**[[CLI/factory-cli/ARCHITECTURE|`ARCHITECTURE.md`]]** first for where the data comes from, and keep
**[[CLI/factory-cli/DATA-MODEL|`DATA-MODEL.md`]]** alongside for what the entities and numbers mean.

---

## The design in one sentence

> **Every record the `ji.jivo.in` factory app holds for Jivo Mart is one Obsidian note
> (`vault/<domain>__<entity>/<prefix>-<key>.md`) with its fields dumped losslessly and every foreign
> key emitted as a `[[wikilink]]` — so you navigate the physical operation (gate → vehicle → barcode
> box → pallet → dispatch → SAP item) by following links the way you'd browse a graph.**

**Open `_HOME.md` first** (in Obsidian: *Open folder as vault* → this folder). It is the map of
content: the headline stats, every entity hub grouped by domain, the list of empty modules, and the
SAP-bridge pointer. From there, click into an entity hub and then a note, or follow `## Related`
wikilinks across folders.

---

## Folder layout

The vault is **flat**: one folder per entity type, named by the **raw slug** = the endpoint path with
`/` → `__`. `ls vault/` shows **48 entries** = **46 entity folders** + `_HOME.md` + `_bridge.json`:

```
vault/
├── _HOME.md                              the MOC entry point (type: moc)
├── _bridge.json                          FG#### → [<slug>/<noteid>, …]  (the machine-readable bridge)
├── barcode__boxes/                       8,500 notes   (the largest entity; prefix `box`)
├── barcode__scan__history/               1,100 notes   (scan events)
├── gate-core__arrivals/                  139 notes     (prefix `arr`)
├── vehicle-management__vehicles/         346 notes     (prefix `veh`)
├── barcode__items__oitm/                 420 notes     (the SAP item master; prefix `oitm`)
├── person-gatein__visitors/              154 notes     (prefix `vis`)
│   … 40 more domain__entity folders …
```

> ⚠️ **This is NOT the layout in `vault-schema.md`.** That doc describes pretty domain folders
> (`fleet-gate/`, `quality-grpo/`, `barcode/`, `production/`, `maintenance/`, …) that **were never
> built**. The real vault is flat `domain__entity` slug folders. Trust `ls vault/`, not the schema doc.

Each entity folder holds its record notes **plus** its MOC hub file(s) `_moc-<slug>.md`.

---

## Anatomy of a note

Every record note has the same shape — frontmatter, a provenance blockquote, `## Fields`, and
(when foreign keys resolve) `## Related`. Here is a real note, `vault/barcode__boxes/box-100226.md`:

```markdown
---
type: factory-box
id: 100226
title: "MUSTARD KACHI GHANI 1 LTR 20 PCS"
entity: Barcode Box
source_endpoint: /barcode/boxes/
company: JIVO_MART
tags:
  - type/factory-box
  - source/factory
  - company/JIVO_MART
  - bridge/FG0000030        # ← present ONLY when the record carries an FG item code
---
# MUSTARD KACHI GHANI 1 LTR 20 PCS

> Barcode Box from `/barcode/boxes/` (Jivo Mart / JIVO_MART).

## Fields
- **id:** 100226
- **box_barcode:** BOX-20260619-XX-3682
- **item_code:** FG0000030
- **item_name:** MUSTARD KACHI GHANI 1 LTR 20 PCS
- **batch_number:** L2  007754
- **qty:** 20.00
- **uom:** PCS
- **current_warehouse:** BH-PF
- **status:** ACTIVE
- **created_at:** 2026-06-19T13:48:41.174066+05:30

## Related
- item -> [[oitm-FG0000030]]
- pallet -> [[pal-2060]]
```

- **`## Fields`** is the lossless dump: scalars render as `- **field:** value`; **nested arrays /
  objects dump as a fenced ```json block** (e.g. `gate-core__arrivals/arr-1.md` dumps its `gate_ins` /
  `gate_outs` arrays as JSON, and its `## Related` shows `driver -> [[drv-264]]`, `vehicle -> [[veh-301]]`).
- **`## Related`** is sorted, unique wikilinks — emitted only when a field name is a known foreign key
  **and** the resolved id exists in that target's registry (see [[CLI/factory-cli/DATA-MODEL|`DATA-MODEL.md`]] § FK graph).

---

## `_HOME`, MOC hubs & chunking

- **`_HOME.md`** — a `type: moc` note titled *"JIVO Factory (Jivo Mart) — Home"*. It states the
  headline stats (`Notes: 16938 · Entity types: 46 · SAP-bridged item codes: 421`), lists the **entity
  hubs grouped by domain** (each `[[_moc-<slug>|Title]] (count)`), then an **"Empty for Jivo Mart"**
  section listing all **59** empty endpoints, then a **"SAP product bridge"** pointer to `_bridge.json`.
- **One `_moc-<slug>.md` per entity type**, living inside that entity's folder (`type: moc`, `Up:
  [[_HOME]]`). It lists every note as `- [[noteid]] — title`.
- **Chunked at 1000 links.** Entities with > 1000 notes are paged: `_moc-<slug>-001.md`,
  `-002.md`, … — e.g. `barcode__boxes` has **9** pages (`_moc-barcode__boxes-001..009`),
  `barcode__scan__history` **2** pages, `gate-core__sales-dispatch__documents` 2 pages. **Total
  `_moc-*.md` files = 56.**

---

## The SAP bridge & `_bridge.json`

`vault/_bridge.json` is the machine-readable factory→product join map:

```json
{ "FG0000004": ["barcode__boxes/box-112501", …], "FG0000030": [ … ], … }
```

- **421 distinct FG codes**, **10,695 total references**. Each key is an `FG####` SAP item code; the
  value lists every `<slug>/<noteid>` whose record carries that code.
- It is **FG-only by design** — only codes matching `^FG\d+$` (finished goods) are recorded; PM
  (packaging) / RM (raw-material) codes are not (see [[CLI/factory-cli/DATA-MODEL|`DATA-MODEL.md`]] § SAP bridge).
- It is consumed downstream by the data-bank's `factory_pillar.py`, which appends a `## Factory lens`
  to each product node whose `FG####` appears here.

Query it directly: `jq 'keys|length' vault/_bridge.json` (→ 421); `jq '.FG0000030 | length'
vault/_bridge.json` (refs for one code).

---

## The tag scheme

Three always-present tags, plus an optional bridge tag:

| Tag | When | Example |
|---|---|---|
| `type/factory-<prefix>` | always | `type/factory-box`, `type/factory-arr`, `type/factory-oitm` |
| `source/factory` | always | — |
| `company/JIVO_MART` | always | — |
| `bridge/FG####` | only if the record carries an FG item code | `bridge/FG0000030` |

Filter the Obsidian graph (or `rg`) by any of these to slice the vault.

---

## Navigation recipes

| You want to know… | Path through the vault |
|---|---|
| The whole map | open **`_HOME.md`** — stats · per-domain entity hubs · empty modules · bridge pointer |
| Every note of one entity | its hub `_moc-<slug>.md` (paged `-001..NNN` if > 1000) |
| One barcode carton's full record | `barcode__boxes/box-<id>` — `## Fields` + `## Related` (item, pallet) |
| What an SAP item code maps to | `barcode__items__oitm/oitm-FG####`, or `jq '.FG####' vault/_bridge.json` |
| Every record carrying an FG code | search the tag **`bridge/FG####`**, or read its `_bridge.json` list |
| A truck's gate-ins/outs across companies | `gate-core__arrivals/arr-<id>` — nested arrays in `## Fields` |
| A box → its pallet → other boxes | follow `## Related` `pallet -> [[pal-…]]`, then that pallet's links |
| What Jivo Mart does NOT run | `_HOME.md` → **"Empty for Jivo Mart"** (the 59 empty modules) |
| The raw JSON behind any note | `raw/<slug>.json` (`{endpoint,kind,count,data}`) — including the unrendered `object` endpoints |

---

## How to open & query it

- **Obsidian** — *Open folder as vault* → start at `_HOME.md`; use the **graph view** and filter by
  tag (`type/factory-box`, `company/JIVO_MART`, `bridge/FG0000030`). Follow `## Related` wikilinks to
  traverse the foreign-key graph.
- **ripgrep / grep** — it's all Markdown; e.g. `rg -l "type/factory-box" vault/`,
  `rg "item_code:\*\*FG0000030" vault/`, `rg "bridge/FG0000030" vault/`.
- **jq** — `jq 'keys|length' vault/_bridge.json` (421 FG codes); `jq '.FG0000030 | length'
  vault/_bridge.json` (refs per code); per-entity note counts from `render-proof.json`; per-endpoint
  raw counts from `raw/_manifest.json` (pre-gap — see caveats).

---

## Caveats when reading

- **`object`-kind endpoints have no notes.** 49 of the 152 endpoints (dashboards, summaries, options,
  WMS overviews, SAP plan-dashboards, production analytics, inventory-age, intercompany dashboard) are
  captured **only** to `raw/*.json` — they are never rendered to vault notes. Read the raw JSON for them.
- **59 empty modules.** Whole built-but-dormant areas (Production, Maintenance, inbound-QC, GRPO
  posting) returned `count:0`, so they have no folder and no notes — only a mention in `_HOME.md`.
  Jivo Mart is the dispatch arm; it doesn't manufacture. See [[CLI/factory-cli/DATA-MODEL|`DATA-MODEL.md`]] § What's NOT modeled.
- **Date-stamp everything.** The vault is the current-state mirror as of the last 05:30 refresh; use
  **git history** to move through time.
- **Never hand-edit the vault.** Notes, MOCs, and `_bridge.json` are regenerated by `render.py` on the
  next refresh — any manual edit is wiped. Fix `bin/render.py` and re-render.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
