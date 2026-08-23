# SAP B1 — JIVO's SAP Business One toolkit

> ## ⚠️ READ-ONLY BY DEFAULT — four write commands, typed on purpose
> Every question you ask is a `GET`. Nothing changes unless an operator types one of
> `sapb1 draft` (a **draft**, inert until a human presses Add in SAP B1), `sapb1 post`
> (live, master data only), `sapb1 patch`, or `sapb1 delete draft` / `delete payment-draft`
> — which removes a **draft** and nothing else: a posted document cannot be addressed
> from here, and there is no `PUT` and no OData action (`Cancel`, `Close`,
> `SaveDraftToDocument`) anywhere in the CLI. Each write previews, needs the word `yes`
> typed in full, and is logged. **The MCP server exposes no write tool at all**, so
> asking a question in Claude can never change SAP. See
> [cli/README.md](cli/README.md) → "Writing to SAP", and RULE 0 in the repo's `CLAUDE.md`.
> (The `manager` login is a super-user; discipline in this repo is what keeps production safe.)

Connected **LIVE 2026-07-23** to the SAP B1 (HANA) Service Layer at `138.252.101.222:50000`.

## The three branch databases

JIVO runs one SAP server with **three company DBs, one per branch** — same credentials for all:

| CompanyDB | Branch |
|---|---|
| `JIVO_OIL_HANADB` | Oils *(default)* |
| `JIVO_MART_HANADB` | Mart |
| `JIVO_BEVERAGES_HANADB` | Beverages |

Switch per command: `./cli/sapb1 orders list --company JIVO_MART_HANADB`

## Layout

```
sap-b1/
├── vault/                  # Obsidian knowledge vault — open this folder in Obsidian
│   ├── 00-SAP-B1-Atlas.md  # master map (START HERE)
│   ├── 01-Data-Model.md    # document flows + join keys (mermaid)
│   ├── 02-Query-Cookbook.md# business questions → sapb1 commands
│   ├── 03-Live-Data-Census.md # which entities hold real JIVO data (3-branch counts)
│   ├── domains/            # 19 domain hubs
│   └── services/           # 498 per-service notes, wikilinked
├── cli/                    # `sapb1` Go CLI (reads + the four write commands) + MCP server (read-only by design)
│   ├── sapb1               # compiled binary (gitignored — rebuild: cd cli && go build -o sapb1 .)
│   ├── .env                # credentials + DB names (gitignored, chmod 600 — NEVER commit)
│   ├── .env.example        # safe template
│   ├── MCP.md              # how the MCP server is registered in ~/.claude.json
│   └── cmd/ internal/      # Go source
├── api-reference/          # full Service Layer API reference (498 services, 1950 ops)
│   ├── atlas.html          # self-contained searchable atlas of all 498 APIs
│   ├── docs/               # 19 domain docs + 00-READ-PLAYBOOK.md (question → query cheat-sheet)
│   ├── catalog/            # services.json / services.txt (deterministic extract)
│   ├── raw/                # original SAP help HTML
│   ├── mock/               # local mock Service Layer (serve.py) for offline testing
│   └── ready/              # admin-request.txt + CONNECT-CHECKLIST.md
└── SAP Remote Desktop.rdp  # RDP file for human GUI access (Windows App on Mac)
```

## Quickstart

```bash
cd ~/sap-b1/cli
./sapb1 doctor                 # config → network → login checklist
./sapb1 orders list --top 5 --orderby "DocDate desc"
./sapb1 items list --low-stock 10
./sapb1 query <EntitySet> ...  # generic read of ANY of the 498 entity sets
```

MCP: registered as `sapb1` in `~/.claude.json` → command `~/sap-b1/cli/sapb1 mcp` (reads `.env` from the binary's directory, so it works from any cwd).

## Gotchas (hard-won)

- **Network to the SAP box FLAPS** from home — if `doctor` fails on network, it's the firewall mood, not the creds. Re-test later or route via another box.
- Login without `CompanyDB` → error 206 "Invalid login credential" (same message as a bad password — don't misread).
- User `DSR` is rejected by the Service Layer (`-304` SLD error — likely no SL license); it's probably a desktop-client-only user. `manager` works on all 3 DBs.
- **Never brute-force login guesses** — account lockout on live production.
- List commands use `--top N`, not `--limit`.
- zsh does not word-split unquoted `$VAR` — pass CLI flags explicitly, not via a `$FLAGS` blob.
