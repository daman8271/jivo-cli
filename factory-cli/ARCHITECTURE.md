---
title: "ARCHITECTURE — how jivo-factory-intel is built"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, architecture]
---

# ARCHITECTURE — how jivo-factory-intel is built

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

How the data physically flows and where everything lives. Read **[[CLI/factory-cli/README|`README.md`]]** first for
the mental model; read **[[CLI/factory-cli/VAULT-GUIDE|`VAULT-GUIDE.md`]]** next for how to read the output, and
**[[CLI/factory-cli/REFRESH-RUNBOOK|`REFRESH-RUNBOOK.md`]]** for the operational commands.

---

## The core idea

> The `ji.jivo.in` factory app describes Jivo Mart's physical operation — every gate arrival, vehicle,
> barcode carton, scan, dispatch, inspection, SAP item — as records behind a REST API. This repo
> captures **every record losslessly** and renders **one Obsidian note per record**, with every
> foreign key emitted as a `[[wikilink]]` so the whole operation becomes a navigable graph. It does so
> **deterministically and with no LLM**: each refresh is a complete **full-replace mirror** — the
> renderer wipes `vault/` and rebuilds it from `raw/`, so nothing is summarised, rewritten, or
> accumulated. The vault is always exactly "what the app holds today", and every claim traces back to
> a raw JSON record.

---

## The components

| Component | What it is | Edit? |
|---|---|---|
| **App + API** | `ji.jivo.in` (React/Vite PWA) → `https://factory.jivo.in/api/v1` (Django REST + SimpleJWT). Health: `/accounts/me/`. Every call carries `Company-Code: JIVO_MART` (missing → `403`). | upstream |
| **`jivo-factory-pp-cli`** | The read-only CLI (built by "printing-press"; source `/root/printing-press/library/jivo-factory`). **19 resources · 152 GET endpoints.** Bearer JWT + `Company-Code: JIVO_MART`. No mutations. | spec in `spec.yaml` |
| **`bin/capture.py`** | Lossless capture of the 152 verified endpoints (`research/get200.txt`). Probes DRF pagination first; walks every page (`paginated_list`) or plain-GETs to `list`/`object`. Writes `raw/<slug>.json` as `{endpoint,kind,count,data}` + `raw/_manifest.json`. 8 worker threads. Deterministic. | `bin/` |
| **`bin/capture_gaps.py`** | Cap-buster + missed-domain backfill — runs **after** capture.py, overwrites/adds raw files in the same shape. Adds the `person-gatein` domain + `company/companies`; busts the 200-cap on sales-dispatch documents (→1130) and the `oitm` item master (→~420); re-pulls QC/production SAP-items via search proxies (→193 each). **Does NOT update `_manifest.json`.** | `bin/` |
| **`bin/render.py`** | The authority on what the vault *is*. Deterministic full-replace render: scans `raw/*.json` directly, classifies by `kind`, emits one note per record, the `_HOME.md` MOC, per-entity `_moc-*.md` hubs, `render-proof.json`, and the SAP bridge `vault/_bridge.json`. | `bin/` |
| **`vault/`** | The rendered Obsidian source vault — **16,995** `.md` (16,938 notes + 56 MOCs + `_HOME.md`) + `_bridge.json`. Becomes `jivo-data-bank/factory/` on fusion. | **never** (regenerated) |
| **Fusion — `factory_pillar.py`** | Lives in the **data-bank** repo (`/opt/ecom-intel/bin/factory_pillar.py`), not here. Copies `vault/` verbatim into the combined vault and appends a `## Factory lens` to product nodes by `FG####`. | data-bank repo |

The CLI, `raw/`, and `vault/` are this repo's responsibility; the fusion belongs to the data bank and
is documented here only for the seam.

---

## The refresh pipeline

Orchestrated by `bin/factory_refresh.sh` (`set -euo pipefail`, single-flight `flock -n .refresh.lock`),
a deterministic **full REPLACE** that runs at **05:30 IST**:

```
 1. refresh_token.py      POST the stored refresh token → /accounts/token/refresh/
        │                   server ROTATES it → store fresh access + fresh refresh (0600)
        ▼
 2. capture.py            GET all 152 endpoints → raw/<slug>.json  ({endpoint,kind,count,data})
        │                   probes DRF pagination, walks pages, writes _manifest.json (pre-gap)
        ▼
 3. capture_gaps.py       cap-bust + missed-domain backfill → raw/ (overwrites/adds; manifest NOT updated)
        │                   person-gatein domain · company · sales-dispatch docs 1130 · oitm 420 · sap-items 193
        ▼
 4. render.py             if isdir(vault): shutil.rmtree(vault)  → then rebuild from raw/*.json
        │                   one note per record · _HOME.md · _moc-*.md hubs · render-proof.json · _bridge.json
        ▼
   git commit (history = time machine)   ── pushed every 3h ──►  PUBLIC repo

   ───────────── separate repo, event-driven after noon upstream chain ─────────────
   data-bank run_daily.sh → daily_rebuild.sh → factory_pillar.py: copy vault/ verbatim into jivo-data-bank/factory/
   + append "## Factory lens" to product nodes by FG#### + fail-closed verify → commit (owner pushes)
```

**Fail-closed at every stage.** Each stage aborts the whole run on failure, with a Telegram alert via
`/root/.claude/hooks/notify.sh`. Exit codes: **2** auth dead, **3** capture failed, **4** gaps failed,
**5** render failed. A bad run never commits — the previous day's commit stays live ("rather ship
correct-yesterday than wrong-today").

> **`factory_daily.sh` is a self-contained alternative** (refresh → run the data-bank
> `daily_rebuild.sh` → optional push) that is **NOT used by cron** — the data-bank's event-driven hook
> does the fuse + commit + push after the noon upstream chain. Auto-push there is OFF by default
> (`FACTORY_AUTOPUSH=1` to enable).

---

## Full-replace semantics & where history lives

- `render.py` does `shutil.rmtree(vault)` then rebuilds from `raw/`. **Nothing accumulates inside the
  vault** — every refresh is a complete, current-state mirror. The downstream data-bank rebuild is
  likewise a full REPLACE.
- **History lives only in git commits.** Each refresh produces one commit, so **git history is the
  time machine**: any past day's gate / box / dispatch / inventory state is recoverable by checking
  out that day's commit. Nothing else preserves the past.
- **Corollary — never hand-edit the vault.** A manual edit to any note, `_moc-*.md`, `_HOME.md`, or
  `_bridge.json` is wiped by the next 05:30 refresh. Fix `bin/render.py` and re-render.
- `render.py` reads `raw/*.json` **directly** (skipping `_manifest.json`), so it is robust to gap
  re-captures the manifest doesn't list — the vault reflects the *post-gap* raw, which is why it has
  entities/counts the manifest doesn't show.

---

## Auth model

Self-sustaining, no password at rest.

- Tokens live at `~/.config/jivo-factory/` — `access.jwt` (~25h, `access_expires_in: 90000`) and
  `refresh.jwt` (~7d, `refresh_expires_in: 604800`), mode **0600**, outside the repo tree.
- **`refresh_token.py`** POSTs the stored refresh token to `/accounts/token/refresh/`. The server
  **rotates** the refresh token, so each run stores **both** a fresh access AND a fresh refresh token.
  Run daily ⇒ auth self-sustains **forever** without the password.
- **Grace:** `factory_refresh.sh` tolerates a failed refresh as long as `/accounts/me/` still returns
  200 (logs a WARN, captures anyway). It hard-fails (exit 2) + alerts only when access is **also** dead.
- **`reseed.sh`** is the one-time re-seed (only if cron has been down > 7d, or for the first seed). The
  owner runs it with the `!` prefix so the password stays in their shell:
  `! JIVO_FACTORY_EMAIL=… JIVO_FACTORY_PASSWORD=… bash bin/reseed.sh`. It logs in once at
  `/accounts/login/` and writes access + refresh (0600). **The password is never stored** (cardinal rule).

---

## Push & sync

- **`/root/bin/push_all_repos.sh`** (cron **`*/15 * * * *`**, every 15 minutes, with
  `COMMIT_VAULTS=1`) commits completed crawler/scraper output and pushes the owner's Jivo repos. The
  repo is **PUBLIC** (`github.com/daman8271/jivo-factory-intel`).
- **Fusion path:** the data-bank's `factory_pillar.py` is the only consumer of `vault/` + `_bridge.json`.
  It `copytree`s `vault/` into `/opt/ecom-intel/combined-vault/factory` (verbatim, sha256 zero-loss
  proof), appends the `## Factory lens` to product nodes by `FG####`, then the build is rsynced into
  `/root/jivo-data-bank` and committed. See [[CLI/factory-cli/DATA-MODEL|`DATA-MODEL.md`]] § Cross-repo for the seam.

---

## Failure modes & guards

- **Single-flight:** `flock -n .refresh.lock` — a second refresh can't overlap the first.
- **Stage abort + alert:** exit **2** (auth dead) / **3** (capture) / **4** (gaps) / **5** (render),
  each Telegram-alerting; no commit on failure.
- **Partial-render risk:** `render.py` is all-or-nothing within a run (`rmtree` then rebuild), and the
  orchestrator aborts on any stage failure, so a half-built vault shouldn't ship. But **there is no
  within-repo note-count regression baseline** — the zero-loss gate and count checks live downstream in
  `factory_pillar.py` / `verify_databank.py`. This repo's own integrity proof is `render-proof.json`
  (counts) plus the downstream sha256 manifest.
- **Pre-gap manifest:** `_manifest.json` reflects the BEFORE-gap inventory (oitm 100, sales-dispatch
  documents 200, QC/prod sap-items 0, no person-gatein, no company). Don't quote it as final — quote
  `render-proof.json`.

---

## Directory map (annotated)

```
jivo-factory-intel/
├── README.md ARCHITECTURE.md VAULT-GUIDE.md DATA-MODEL.md   repo-only docs
├── PLAN.md                  the phased plan that built this (Goal #14)
├── REFRESH-RUNBOOK.md       daily auto-refresh runbook (cron · auth · re-seed)
├── vault-schema.md          ⚠️ ASPIRATIONAL design — NOT what render.py builds
├── spec.yaml                printing-press CLI spec (19 resources · 152 GETs · Company-Code header)
├── render-proof.json        render proof: total_notes · entity_types · empty_modules · sap_bridge_codes · per_entity
│
├── bin/                     the pipeline
│   ├── refresh_token.py        rotate JWT (rotating refresh token → fresh access + refresh, 0600)
│   ├── capture.py              lossless capture of 152 endpoints → raw/*.json + _manifest.json
│   ├── capture_gaps.py         cap-bust + missed-domain backfill → raw/ (manifest NOT updated)
│   ├── render.py               deterministic FULL REPLACE → vault/ (rmtree + rebuild)
│   ├── factory_refresh.sh      orchestrator (token → capture → gaps → render; flock; exit 2/3/4/5)
│   ├── factory_daily.sh        self-contained alt (refresh → data-bank rebuild → push) — NOT cron-wired
│   └── reseed.sh               one-time password re-seed (owner runs with `!`; password never stored)
│
├── raw/                     lossless raw capture — 152 <slug>.json + _manifest.json   [35 MB]   [source of render]
├── vault/                   the rendered Obsidian vault                                [74 MB]  [never edit]
│   ├── _HOME.md                the MOC entry point
│   ├── _bridge.json            FG#### → [<slug>/<noteid>, …]  (421 codes / 10,695 refs)
│   └── <domain>__<entity>/     46 flat entity folders, each with notes + _moc-<slug>.md hub(s)
├── snapshots/               a frozen earlier raw capture (2026-06-30 00:27) — NOT refreshed by cron  [21 MB]
├── app-model/               the 13-section whole-app study (README · 00-OVERVIEW · _route-map · sections/01–13)
└── research/                CLI/endpoint research (API-FACTS · endpoints.txt · get200.txt · domain-schemas.json)
```

> Logs (`refresh.log`, `daily.log`, `render.log`, `raw_capture.log`) and `.refresh.lock` are
> gitignored. The fusion consumer (`factory_pillar.py`) lives in the **data-bank** repo, not here.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
