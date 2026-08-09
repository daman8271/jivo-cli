# JIVO Distribution Bundle-Builder — Implementation Plan

*Authored by Atlas (Fable 5), 2026-08-10, from `distribution/manifest.json` (14-agent inventory). Load-bearing claims spot-checked in source: sapb1's cwd-only `godotenv.Load()` (`sap-b1/cli/internal/config/config.go:81`) plus next-to-binary load for `mcp` (`internal/cli/mcp.go:66`), hana-sql's upward walk for `connections/hana.env` (`hana-sql/internal/config/config.go:40-61`), the root `.gitignore`'s blanket `*.env` rules, the NTFS-illegal `sap-b1/vault/services/Entities:.md` (it exists), and `portals/tankhapay/` being entirely gitignored (exists only on Daman's Mac — matters for the availability scanner).*

## 0. Decisions (made here so Forge doesn't re-derive them)

**D1 — Zip layout: mirror the repo tree, one top-level `jivo-cli/` folder.**
Flat layout is dead on arrival: hana-sql *requires* a `connections/` ancestor directory, jsap walks up from its package dir, exim's wrapper resolves `cli/` and `scripts/` relative to itself, factory-cli and jivo-scrape ancestor-walk for `product-identity/v1/`, and every existing SETUP doc gives repo-relative instructions. The mirrored tree is also the exact layout field-verified twice (Karanpreet 08-08 rsync, Avtar 08-06). Mirroring means every env-resolution mechanism in every tool works unmodified, and the recipient instruction is uniform: "unzip to home → `~/jivo-cli` (Mac) / `C:\jivo-cli` (Windows)".

**D2 — Missing binaries: skip-with-warning. No build-on-demand.**
For the v1 targets (windows, mac-arm64) the only gaps are optional MCP servers and three portal `.exe`s whose token flows live on this Mac anyway. Build-on-demand would put the Go toolchain in the request path, add minutes to a click, and ship binaries nobody smoke-tested. The server packages *what exists on disk*, reports what it skipped, and surfaces known-stale warnings (hana-sql.exe lacks the Aug-2 MCP domain tools — warn, let Daman rebuild by hand with the manifest `build_cmd`, re-bundle).

**D3 — Stack: one Go binary (`net/http` + `archive/zip`), frontend served from disk, no embed.**
Repo is Go-heavy and `archive/zip` gives direct control of external attributes (exec bits) and produces no `__MACOSX` junk. Embedding the frontend buys nothing here — the server is inherently repo-anchored (it reads live env files by repo path), so the repo is always present; serving `distribution/web/` from disk lets the separately-designed frontend iterate without rebuilds. Bind `127.0.0.1:7788` by default (`-addr` flag for VPS later) — not an auth layer, just not broadcasting credentials on the LAN.

**D4 — Staging in `os.MkdirTemp` (outside the repo), zips in gitignored `distribution/dist/`.**
Secrets can't be committed from a directory that isn't in the repo. `-keep-staging` flag stages under `distribution/staging/` (gitignored) for debugging. Belt-and-braces: a pre-flight `git check-ignore -q distribution/dist` that aborts the build if it ever fails, plus a unit test that asserts the same.

**D5 — Env baking: allowlist staging + prefix-filtered root `.env` + a gitignored `secrets.local.env` overlay** for keys that live nowhere in the repo (DSR). A component's bundle carries only *its* credentials — a jsap-only zip must not carry OMS/EXIM/SAP passwords.

## 1. Directory layout

```
distribution/
├── manifest.json          # exists — the input, committed
├── API.md                 # contract for the frontend designer (step 11)
├── README.md              # dev doc: run server, CLI mode, tests
├── .gitignore             # step 1
├── overrides.json         # committed: structured per-binary/per-component warnings
├── secrets.local.env      # GITIGNORED, operator-maintained: DSR_USER, DSR_PASSWORD, …
├── server/                # Go module "jivodist"
│   ├── go.mod
│   ├── main.go            # -serve (default) | -selection x.json -o y.zip | -list
│   └── internal/
│       ├── manifest/      # types + loader + live availability scan
│       ├── engine/        # Build() + stage.go, envbake.go, readme.go, zipw.go, guard.go
│       └── httpapi/       # handlers, static file serving
├── web/                   # frontend (designed separately in the main session)
├── dist/                  # GITIGNORED — output zips
├── staging/               # GITIGNORED — only with -keep-staging
└── testdata/              # selection fixtures + golden ship-lists
```

## 2. `distribution/.gitignore` (exact contents)

```
# Generated bundles carry LIVE credentials — never commit, never deploy.
dist/
staging/
*.zip
secrets.local.env
```

(The root `.gitignore`'s `*.env` / `.env*` already cover stray env copies; this is the second belt. The third is the runtime `git check-ignore` guard in `engine/guard.go`.)

## 3. API contract (frontend ↔ server)

The UI renders **only** from `GET /api/manifest` — no hardcoded tool list.

**`GET /api/manifest`** → the manifest's UI-relevant fields, enriched live per target:

```json
{
  "generated_at": "2026-08-10T14:00:00+05:30",
  "targets": ["mac-arm64", "windows"],
  "components": [
    {
      "id": "hana-sql",
      "ui_name": "HANA SQL (direct SAP database)",
      "ui_description": "…from manifest…",
      "auth_mode": "baked-env",
      "sensitive": false,
      "availability": {
        "mac-arm64": { "ok": true,  "tools_included": 1, "tools_skipped": 0, "warnings": [] },
        "windows":   { "ok": true,  "tools_included": 1, "tools_skipped": 0,
                       "warnings": ["hana-sql.exe built Jul 31 — missing hana_turnover/… MCP tools; rebuild before shipping"] }
      },
      "est_size_bytes": 14200000
    }
  ]
}
```

`auth_mode` is one of `baked-env` (works out of the box) · `auth-login` (creds baked for reference, recipient runs `auth login`) · `home-config-install` (postsql: file must be copied to `~/.postsql/`) · `external-token` (blinkit/zepto/amazon/flipkart/swiggy: no useful credential can ship). `availability` is computed from **disk truth** (`os.Stat` on each manifest binary path), not the manifest `exists` flag — this automatically handles tankhapay being absent on the VPS.

**`POST /api/bundle`** — request:
```json
{ "target": "mac-arm64", "components": ["sap-b1", "hana-sql"], "recipient": "karanpreet", "include_docs": true }
```
Response `200` (JSON first so warnings are seen *before* download):
```json
{
  "bundle_id": "20260810-1430-a1b2",
  "filename": "jivo-kit-mac-arm64-20260810-karanpreet.zip",
  "size_bytes": 48211903,
  "sha256": "…",
  "warnings": ["dsr-cli: DSR_USER/DSR_PASSWORD not found in secrets.local.env — shipped blank template"],
  "skipped": [ { "component": "ecom-cli", "tool": "jivo-ecom-pp-mcp", "reason": "no windows binary prebuilt" } ],
  "download_url": "/api/bundle/20260810-1430-a1b2/download"
}
```
Errors: `400` unknown component / empty selection / bad target; `409` gitignore guard failed (message says exactly what to fix); `500` with plain message.

**`GET /api/bundle/{id}/download`** → `application/zip`, `Content-Disposition: attachment`.
**`GET /api/bundles`** → list of zips in `dist/` (name, size, age). **`DELETE /api/bundle/{id}`** → remove (the zips hold live creds; deleting after sending is part of the workflow).
**`GET /`** → serves `distribution/web/`.

## 4. Zip layout spec — exact tree for a 2-component mac-arm64 bundle (hana-sql + jsap-cli)

```
jivo-kit-mac-arm64-20260810-karanpreet.zip
└── jivo-cli/
    ├── README.txt                      [0644]  generated per-bundle
    ├── .env                            [0600]  generated: JSAP_* keys only (filtered from repo-root .env)
    ├── connections/
    │   ├── hana.env                    [0600]  live copy (direct-office variant)
    │   └── hana-tunnel.env             [0600]  live copy (from-home variant; README says when to swap)
    ├── hana-sql/
    │   ├── hana-sql                    [0755]
    │   ├── README.md
    │   ├── MCP.md
    │   └── queries/turnover-oil-july.sql
    └── jsap-cli/
        ├── jsap-cli                    [0755]
        ├── README.md
        ├── jsap/                       (full package, NO __pycache__)
        └── tests/test_readonly.py
```

Why this works with zero tool changes: hana-sql run from anywhere under `jivo-cli/` walks up and finds `connections/hana.env`; jsap's `config.py` walks up from `jsap-cli/jsap/` and finds `jivo-cli/.env`. Every path in the zip uses forward slashes (zip spec; Windows extractors handle them).

## 5. Env-baking table (component → live source → destination in zip → mode → mechanism)

| Component | Live source (this repo/machine) | Destination in zip | Mode | Why it works / notes |
|---|---|---|---|---|
| sap-b1 (mac) | `sap-b1/cli/.env` | `sap-b1/cli/.env` | 600 | cwd-load; README: `cd sap-b1/cli`. **Never** stage `lovepreet-veerji.env` |
| sap-b1 (win) | `sap-b1/accounts-kit/.env` | `sap-b1/accounts-kit/.env` | 600 | next-to-exe after `cd`; ship `claude_desktop_config.json` unmodified + README note that its `C:\jivo-sap\sapb1.exe` path must be edited (or that folder copied to `C:\jivo-sap`) |
| hana-sql | `connections/hana.env` + `connections/hana-tunnel.env` | same paths | 600 | upward walk; both variants ship, README explains office vs home |
| ecom-cli | repo-root `.env`, keys `ECOM_*`, `JIVO_ECOM_*` | `jivo-cli/.env` (filtered) | 600 | binary reads **no** .env — creds are reference for `auth login` (auth_mode `auth-login`) |
| exim | repo-root `.env`, keys `EXIM_*` (must include `EXIM_API`+`EXIM_WEB` — hard KeyErrors) | `jivo-cli/.env` (filtered) | 600 | `eximapi.py` walks up from `exim/`; also stage `exim/.secrets/README.txt` placeholder (empty dirs vanish from zips and eximapi never mkdirs) |
| factory-cli | repo-root `.env`, keys `JIVO_FACTORY_*` | `jivo-cli/.env` (filtered) | 600 | `auth login` reference; plus `product-identity/v1/` (map + attestation + sources + review-decisions + source-manifest, **byte-identical**) at zip root |
| oms-cli | repo-root `.env`, keys `OMS_*` | `jivo-cli/.env` (filtered) | 600 | `auth login` reference only |
| jsap-cli | repo-root `.env`, keys `JSAP_*` | `jivo-cli/.env` (filtered) | 600 | nearest-ancestor walk finds zip root `.env` |
| postsql | `~/.postsql/config.toml` | `postsql/config.toml.INSTALL` | 600 | binary reads **only** `~/.postsql/config.toml` / env vars; README: `mkdir -p ~/.postsql && cp`. Warn: password dead fleet-wide as of 08-06 (from `overrides.json`) |
| dsr-cli | `distribution/secrets.local.env`, keys `DSR_*` | `dsr-cli/.env` (generated) | 600 | exe-dir `.env` search finds it; if keys absent → blank-valued template + loud warning in response and README |
| portals: tankhapay | `portals/tankhapay/.env` | same path | 600 | `<exe dir>/../.env` resolution; `sensitive: true` in API (payroll data) |
| portals: blinkit/zepto/amazon/flipkart/swiggy | none baked | `.env.example` only where one exists | 644 | `external-token`: tokens are short-lived and minted by `~/ecomcliauto` on this Mac only — README states plainly this ships read access only until the current session expires, and never clone the token automation to a second box |
| control-panel | `control-panel/.env` | same path | 600 | default cred path is `~/software/.env` (compiled in); README: `jivo auth login --env-file <unzip>/control-panel/.env`. **Never** stage `control-panel/recon/` |
| jivo-scraping-cli | none (no secrets in tool) | — | — | README: `product` commands fully offline; data commands need `JIVO_SCRAPE_ROOT` pointing at an ecom-intel checkout |

Root-`.env` filter mechanics: parse `KEY=VALUE` lines from the live repo-root `.env`, emit only keys whose prefix belongs to a *selected* component (prefix map lives in `envbake.go`, mirroring the manifest envmap), under a generated header comment. `secrets.local.env` overlays gaps. Always-deny list enforced at stage time regardless of allowlist bugs: `env-vault/**`, `**/token.json`, `**/.secrets/token.json`, `lovepreet-veerji.env`, `control-panel/recon/**`, `**/captures/**`, `**/.git/**`, `**/__pycache__/**`, `*.pyc`, `.DS_Store`, `connections/fleet-access.env`.

## 6. Implementation steps (Forge, in order — each independently verifiable)

1. **`distribution/.gitignore`** (contents above) + **`server/internal/engine/guard.go`** with `AssertIgnored(paths...)` running `git check-ignore -q`; unit test creates probe files in `dist/`/`staging/` and asserts ignored, asserts `git status --porcelain` shows nothing new.
2. **Go module** `distribution/server/` (`go mod init jivodist`, Go ≥1.22, stdlib only). `main.go` with three modes: `-serve` (default), `-selection <json> -o <zip>` (CLI/verification seam), `-list` (print components/availability as JSON). Repo root: `-repo` flag, else walk up from cwd until a dir containing `distribution/manifest.json`.
3. **`internal/manifest/`** — typed loader for the existing `distribution/manifest.json` (components/tools/binaries/env/companion_files/docs_to_ship/zip_gotchas; `envmap` and `lessons` loosely typed — `lessons.readme_must_say` and `lessons.network_requirements` are consumed by the README generator). Availability scanner: `os.Stat` every binary path per target OS, record exists/size/mtime. Load `distribution/overrides.json` (committed) for structured warnings keyed by component or binary path — seed it with: hana-sql.exe stale; postsql password dead 08-06; env-vault creds burn-listed pending rotation; tankhapay sensitive; portal token expiry caveats. Unit test: loader round-trips the real manifest; scanner agrees with the manifest `exists` flags on this machine.
4. **Ship-list resolver** (`engine/stage.go` pure function): `(manifest, component, targetOS, includeDocs) → []StagedFile{src, zipPath, mode}` — binaries for the target OS only, companion files, docs_to_ship, env plan entries from the table in §5. Per-tool skip when no binary exists for the target (collect into `skipped`). Windows target additionally rejects any staged zipPath containing NTFS-illegal characters (`: * ? " < > |`) — assert, don't silently drop. Golden tests in `testdata/`: full mac selection and full windows selection produce exactly the expected file lists (this test is the allowlist's proof — it will catch anyone "helpfully" switching to directory copies).
5. **Env baker** (`engine/envbake.go`): root-.env prefix filter, live-file copies, `secrets.local.env` overlay, dsr template generation, postsql `config.toml.INSTALL` copy. Unit tests with fixture env files: a jsap-only selection's `.env` contains `JSAP_*` and nothing else; exim selection includes `EXIM_API`/`EXIM_WEB`; sap env retains `SAPB1_INSECURE=true`; missing DSR keys → blank template + warning.
6. **README generator** (`engine/readme.go`): per-bundle `README.txt` from templates — top block is `lessons.readme_must_say` essentially verbatim (live-credentials warning, unzip locations, Mac `xattr -dr com.apple.quarantine` + `chmod +x` with the *actual* staged binary list, harness `setup.py` first, doctor second); then the network matrix (SAP+HANA: office/VPN/tunnel; everything else: any internet); then one block per included component: how to run (`cd` instruction matching its env resolution), auth story per `auth_mode`, token-expiry note, offline check command, behavior-change notes (sapb1 write-log falls back to `~/.sapb1-writes.jsonl` outside a checkout; claude_desktop_config.json path; control-panel `--env-file`). CRLF line endings for windows-target bundles. Unit test: golden README for the 2-component example.
7. **Zip writer** (`engine/zipw.go`): `archive/zip` with `FileInfoHeader` + `SetMode(0o755)` binaries / `0o600` env / `0o644` docs, Deflate, forward-slash paths, single `jivo-cli/` root, explicit directory entries. Test: write, re-open with `zip.NewReader`, assert `f.Mode()&0o111 != 0` for binaries and `0o600` for env files; shell out to `unzip -Z` if present to double-check external attrs; assert no `__MACOSX`, no `.DS_Store`.
8. **`engine.Build(repoRoot, Selection) (Result, error)`** — the one testable seam: guard pre-flight → resolve ship-lists → stage into `os.MkdirTemp` (or `distribution/staging/` with `-keep-staging`) → bake env → generate README → zip into `distribution/dist/<filename>` → sha256 → `Result{ZipPath, SHA256, Size, Warnings, Skipped}`. Deny-list check runs over the final staged tree as the last gate before zipping.
9. **CLI mode** wired to `Build` (this is Proof's harness): `./server/jivodist -selection testdata/mac-all.json -o dist/test.zip` prints the Result JSON to stdout, exit 0/1.
10. **HTTP layer** (`internal/httpapi/`): the four endpoints from §3 + static serving of `distribution/web/`; a `sync.Mutex` around Build (one bundle at a time — this is a one-operator tool); default `127.0.0.1:7788`.
11. **`distribution/API.md`** — the §3 contract written down, including the rule *the UI renders only `GET /api/manifest`*. (The real frontend is built in the main session — Forge does NOT create or modify anything under `distribution/web/`.)
12. **`distribution/README.md`** (dev doc) + `testdata/` fixtures: `mac-all.json`, `win-all.json`, `mac-min.json` (hana+jsap example), `win-accounts.json` (sap-b1 only).

## 7. Verification procedure (for Proof)

1. `cd distribution/server && go test ./...` — guards, resolver goldens, env filter, zip modes, NTFS name check.
2. Generate the mac-min bundle via CLI mode; extract with **both** `unzip` and `ditto -x -k`; assert: `test -x` on every binary, env files 0600, `README.txt` present, no `__MACOSX`/`.DS_Store`/`__pycache__`.
3. Inside the extracted tree, run each included tool's manifest `offline_check` **as written** (mirrored layout means they run unmodified): `cd sap-b1/cli && ./sapb1 --help`, `./hana-sql --help` (usage text, not exit code — it exits 2 by flag convention), `cd jsap-cli && ./jsap-cli --help`, etc.
4. Generate `win-all`; assert zero staged paths contain NTFS-illegal characters, expected `.exe` set matches the manifest, `dsr-cli/.env` sits next to `dsr.exe`, skipped list names amazon/flipkart/swiggy/ecom-mcp/factory-mcp. (True Windows extraction is a later manual check on an office box — not automatable here; say so, don't fake it.)
5. Secret-safety sweep after a full-selection build: `git status --porcelain` unchanged; zip central directory (via `zip.NewReader`) contains none of: `lovepreet-veerji.env`, `token.json`, `all-env.txt`, `recon/`, `captures/`, `fleet-access.env`, `.git/`; a jsap-only bundle's `.env` has no `OMS_`/`SAPB1_` keys.
6. API smoke: `POST /api/bundle` sha256 matches the file on disk; `curl` the download; `DELETE` removes it.

## 8. The three details Forge must not get wrong

1. **Exec bits in the zip.** A naive `zip.Create()` writes mode-0 entries; every Mac binary lands non-executable and the whole bundle is dead on arrival. Must use `FileInfoHeader`+`SetMode` per file, and the test must re-read modes from the finished archive — not from staging.
2. **Allowlist staging, never folder copies.** The moment anyone stages a component by copying its directory, the bundle ships `lovepreet-veerji.env`, live `exim/.secrets/token.json`, `control-panel/recon/` admin cookies, or amazon's 99 MB captures. The golden ship-list tests plus the final-gate deny-list are the defense; both must exist.
3. **Tell the truth per `auth_mode`.** Baking a `.env` that a binary never reads (ecom, oms, postsql, most portals) and calling it "works out of the box" produces exactly the silent failure this repo's lessons document. The README generator must branch on `auth_mode`, the root-`.env` filter must include `EXIM_API`/`EXIM_WEB` and `SAPB1_INSECURE=true`, and portal bundles must say plainly that their sessions expire and cannot be refreshed off this Mac.

Near-miss fourth: `product-identity/v1/` files are hash-pinned — copy them byte-for-byte (no re-encoding, no CRLF translation) or every factory/jivo-scrape `product` command fails closed with exit 6.
