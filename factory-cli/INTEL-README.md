---
title: "JIVO Factory Intel — Jivo Mart (ji.jivo.in)"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, intel]
---

# JIVO Factory Intel — Jivo Mart (ji.jivo.in)

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

> **🌐 Public repo, internal data — by design.** This repository is **public**
> (`github.com/daman8271/jivo-factory-intel`) and contains internal Jivo Mart / SAP
> factory-floor data made world-readable by the owner's explicit, informed choice. **No
> credentials or secrets are committed** — JWTs live in `~/.config/jivo-factory/` *outside* the
> tree, and `*.jwt`, `*.env`, `config.toml`, `*secret*`, `*.pem`, `*.key`, `*.log` are gitignored.
> Because it is public, treat every change as world-visible: never let a new credential, token, or
> private export land here.

A lossless capture of the **`ji.jivo.in` factory-floor app** for the **Jivo Mart** company
(`JIVO_MART`) — the read-only CLI pulls every record the app exposes, a deterministic renderer turns
it into a **linked Obsidian source vault** (one note per record, foreign keys as `[[wikilinks]]`),
and that vault becomes the **4th pillar** of the JIVO data bank. One note per gate arrival, vehicle,
driver, barcode box, pallet, scan, dispatch, inspection, SAP item — joined into one connected graph,
**keyed by the SAP item code `FG####`**. **The lossless graph is the deliverable — not a dashboard.**

---

## Start here — reading order

Read these four files **in order** (~10 minutes) and you have the whole foundation: what this is,
how it's built, how to read it, and what it means.

1. **`README.md`** ← you are here — what this is, the at-a-glance numbers, the rules.
2. **[[CLI/factory-cli/ARCHITECTURE|`ARCHITECTURE.md`]]** — how it's built: the CLI, the capture/render pipeline,
   the daily refresh, full-replace semantics, and the git-history time machine.
3. **[[CLI/factory-cli/VAULT-GUIDE|`VAULT-GUIDE.md`]]** — how to **read & navigate**: folder layout, the anatomy
   of a note, the MOC hubs, the SAP bridge, and the navigation recipes.
4. **[[CLI/factory-cli/DATA-MODEL|`DATA-MODEL.md`]]** — what the data **means**: Jivo Mart's business, the 46-entity
   catalog, the foreign-key graph, the SAP bridge, and what is *not* modeled.

**Also in this repo:** **[[CLI/factory-cli/PLAN|`PLAN.md`]]** (the phased plan that built this) ·
**[[CLI/factory-cli/REFRESH-RUNBOOK|`REFRESH-RUNBOOK.md`]]** (the daily auto-refresh runbook + one-time re-seed).

---

## What this is, in one picture

```
ji.jivo.in (React/Vite PWA)                          SAP Business One (OITM · GRPO · AR · transfers)
      │  factory-floor user actions                       ▲  reads + writes back
      ▼                                                    │
factory.jivo.in/api/v1  ── Django REST + SimpleJWT ────────┘
      │  GET only  (bearer JWT + header  Company-Code: JIVO_MART)
      ▼
jivo-factory-pp-cli   (19 resources · 152 GET endpoints, read-only)
      │
      ▼   05:30 IST  factory_refresh.sh
 refresh_token.py → capture.py → capture_gaps.py → render.py (rmtree vault/ → rebuild)
      │   (rotate JWT)   (raw/*.json)  (cap-bust+gaps)   FULL REPLACE
      ▼
 vault/  (16,995 .md + _bridge.json) ──git commit (history = time machine)──► PUBLIC repo
      │
      ▼   event-driven after noon upstream chain (~12:20 IST when sources are ready)
 factory_pillar.py → copy vault/ verbatim into jivo-data-bank/factory/ + append "## Factory lens"
                     to each product node whose FG#### appears (the SAP bridge)
```

---

## At a glance

| Metric | Value |
|---|---|
| Record notes (one per physical record) | **16,938** |
| Entity types (flat `domain__entity` folders) | **46** |
| `.md` files on disk | **16,995** (16,938 notes + **56** `_moc-*.md` + `_HOME.md`) |
| SAP `FG####` bridge codes | **421** (10,695 references in `_bridge.json`) |
| Empty modules (built but no data) | **59** |
| Rendered vault | **74 MB** |
| Lossless raw capture | **35 MB** — 152 endpoint files + `_manifest.json` |
| Company scope | **`JIVO_MART`** (company id 2) — the retail / dispatch arm only |

> **A snapshot mirror, not a growing archive.** `render.py` does `shutil.rmtree(vault)` then rebuilds
> from scratch every refresh — the vault is always the **current state**, nothing accumulates inside
> it. **History lives only in git commits:** one refresh = one commit, so any past day's gate / box /
> dispatch state is recoverable by checking out that day's commit. Date-stamp anything you report.

---

## Repo at a glance

```
jivo-factory-intel/
├── README.md            ← this file
├── ARCHITECTURE.md      ← how it's built + the refresh pipeline
├── VAULT-GUIDE.md       ← how to read & navigate the vault
├── DATA-MODEL.md        ← what the data means (business · entities · bridge · gaps)
├── PLAN.md              the phased plan (Goal #14: fuse Jivo Mart as the data-bank's 4th pillar)
├── REFRESH-RUNBOOK.md   daily auto-refresh runbook (cron chain · self-sustaining auth · re-seed)
├── vault-schema.md      ⚠️ ASPIRATIONAL design doc — NOT what render.py builds (see "honest gaps")
├── spec.yaml            the printing-press CLI spec (19 resources · 152 GETs · Company-Code header)
├── render-proof.json    render output proof (total_notes · entity_types · empty_modules · per_entity)
│
├── bin/                 the pipeline
│   ├── refresh_token.py    rotate the JWT (rotating refresh token → fresh access + refresh)
│   ├── capture.py          lossless capture of the 152 endpoints → raw/*.json
│   ├── capture_gaps.py     cap-buster + missed-domain backfill → raw/ (overwrites/adds)
│   ├── render.py           deterministic FULL REPLACE → vault/  (rmtree + rebuild)
│   ├── factory_refresh.sh  the orchestrator (token → capture → gaps → render; flock single-flight)
│   ├── factory_daily.sh    self-contained alt (refresh → data-bank rebuild → push) — NOT used by cron
│   └── reseed.sh           one-time password re-seed (owner runs with `!`; password never stored)
│
├── raw/                 lossless raw capture — one <slug>.json per endpoint + _manifest.json   [35 MB]
├── vault/               the rendered Obsidian vault — 46 entity folders + _HOME.md + _bridge.json [74 MB]
│   └── barcode__boxes/  gate-core__arrivals/  vehicle-management__vehicles/  …  + _moc-<slug>.md hubs
├── snapshots/           a frozen earlier raw capture (2026-06-30 00:27) — NOT refreshed by cron  [21 MB]
├── app-model/           the 13-section whole-app study (README · 00-OVERVIEW · _route-map · sections/01–13)
└── research/            CLI/endpoint research (API-FACTS · endpoints.txt · get200.txt · domain-schemas.json)
```

---

## The honest gaps (read before drawing conclusions)

This is a real dataset with real limits. The full discussion is in
**[[CLI/factory-cli/DATA-MODEL|`DATA-MODEL.md`]] § What's NOT modeled**; the headlines:

- **`object`-kind endpoints are captured but NOT rendered as notes.** Of the 152 endpoints, **49** are
  single-object responses (dashboards, summaries, options, WMS overviews, SAP plan-dashboards,
  production analytics, inventory-age report, intercompany dashboard). They are saved losslessly to
  `raw/*.json` but get **no vault notes** — honest lossiness, raw JSON retained.
- **`vault-schema.md` is ASPIRATIONAL, not as-built.** That 71 KB doc describes a much richer/prettier
  vault (pretty domain folders like `fleet-gate/`, `barcode/`, `production/`; dozens of entities) that
  **`render.py` never builds**. The shipped vault is **flat `domain__entity` slug folders, 46 entity
  types**. Trust `render.py` / `render-proof.json`, not `vault-schema.md`.
- **Production, Maintenance, inbound-QC and GRPO modules are built but dormant.** Jivo Mart does not
  manufacture — it receives finished cartons and dispatches them — so the MES/CMMS/goods-receipt
  muscles return `count:0` (the **59** empty modules). Schema-complete, zero master data.
- **`_manifest.json` is the PRE-gap inventory.** `capture_gaps.py` adds/overwrites raw files after
  `capture.py` but does **not** update the manifest. Quote `render-proof.json` for final counts, not
  the manifest.

---

## Hard rules

- **Read-only — no mutation.** The CLI and pipeline only GET. There are no write/mutation commands;
  do not add any without explicit approval.
- **Never write secrets** (the Jivo Factory password, a JWT) into any file, doc, or commit. Tokens
  live at `~/.config/jivo-factory/` (mode 0600) and self-sustain via the rotating refresh token; the
  password is never stored (cardinal rule).
- **It is PUBLIC — be doubly careful.** Nothing sensitive (a new credential, a private export) may
  ever land in the tree. The defensive `.gitignore` is a backstop, not a license to be careless.
- **Never hand-edit the vault.** `render.py` wipes and rebuilds `vault/` on the **next daily refresh**,
  so any manual edit to a note, MOC, or `_bridge.json` is silently lost. Change `bin/render.py` and
  re-render instead.
- **Accuracy at all costs — fail-closed.** A bad capture / gap-pull / render aborts **without
  committing** and Telegram-alerts; the previous day's commit stays live. Rather ship correct-yesterday
  than wrong-today.

---

## Where this fits — the JIVO data-bank programme

This is **one source pillar** of a four-repo programme. Three source repos each capture a system; the
fourth fuses them per product, keyed by the SAP code **`FG####`**:

1. **`/root/jivo-intel`** (`daman8271/jivo-intel`) → pillar **`jivo/`** — the `ecom.jivo.in` internal
   app: SKUs, POs, dashboards, targets, volume (~34,750 notes). Keys products by SAP code `sku-FG…`.
2. **`/opt/ecom-intel`** (`daman8271/ecom-intel`) → pillar **`ecom/`** — the competitor-price scraper:
   per-SKU price-match history across platforms. Keys products by name-slug `canonical_sku`.
3. **`/root/jivo-factory-intel`** (**this repo**, CLI `jivo-factory-pp-cli`) → pillar **`factory/`** —
   the `ji.jivo.in` factory app for Jivo Mart. Keys every item by SAP item code **`FG####`** (`item_code`).
4. **`/root/jivo-data-bank`** (`daman8271/jivo-data-bank`) — the **fusion repo**: copies all three
   pillars verbatim and appends one node per product with **three lenses** (competitor-price ·
   JIVO-volume · factory). The factory lens is bridged here by `FG####`.

---

## Refresh & ownership

- **05:30 IST** — `bin/factory_refresh.sh` refreshes this repo (rotate token → capture → cap-bust →
  full-replace render). Self-sustaining auth, no password at rest.
- **Event-driven after the noon upstream chain** — the data-bank fusion runs after the 12:00 ecom
  deadline sweep and competitor refresh complete; typical landing is around **12:20 IST**, not a fixed
  06:00 or 13:30 cron.
- **Every 15 minutes** — `/root/bin/push_all_repos.sh` runs from cron with `COMMIT_VAULTS=1` and syncs
  completed crawler/scraper output for the owner's Jivo repos.

Operational detail (the cron chain, self-sustaining auth, the one-time re-seed) lives in
**[[CLI/factory-cli/REFRESH-RUNBOOK|`REFRESH-RUNBOOK.md`]]**.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
