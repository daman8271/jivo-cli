# JIVO CLI — every window into the company, one folder

> ## ⚠️ READ-ONLY LAW — ALL of these tools only READ
> Every CLI here reads JIVO's live production systems and **never writes** to any of them.
> The only non-GET call any tool makes is Login. No exceptions, ever.

One home for all JIVO business-system CLIs, their credentials, and the knowledge of how they connect. Fleet live-tested 2026-07-23.

## The grid

| CLI | System | Surface | Run |
|---|---|---|---|
| `sap-b1/` | SAP B1 Service Layer — the books, 3 company DBs | 307 readable entities + 498-note Obsidian vault | `cd sap-b1/cli && ./sapb1 doctor` |
| `ecom-cli/` | ecom.jivo.in — marketplace sell-through | 138 cmds (+ MCP binary) | `./ecom-cli/jivo-ecom-pp-cli doctor` |
| `exim/` | exim.jivo.in — imports, RM, tanks, contracts | 65 cmds | `./exim/exim doctor` |
| `factory-cli/` | factory.jivo.in — gate/QC/production/dispatch, 3 companies | 183 cmds | `./factory-cli/jivo-factory-pp-cli doctor` |
| `oms-cli/` | oms.jivo.in — orders, schemes, parties, HANA stock | 72 cmds | `./oms-cli/oms-pp-cli doctor` |
| `jsap-cli/` | JSAP (103.89.45.75:5001) — approvals, tasks, tickets, bills | 146 cmds | `./jsap-cli/jsap-cli meta whoami` |
| `jivo-scraping-cli/` | ecom-intel archive — street price / availability / DRR | 14 cmds (data checkout lives on the VPS) | `jivo-scraping-cli/bin/jivo-scrape doctor` |
| `product-identity/` | THE BRIDGE: platform listing_id ↔ SAP item code (333↔1,906) | verifier | `python3 product-identity/tools/verify_map.py --json` |
| `control-panel/` | Jivo Group Control Panel (103.89.45.75:9080 Django ERP) | 62 endpoints | `./control-panel/cli/jivo/jivo doctor` |
| `postsql/` | **Raw Postgres** (103.89.45.76) — the DB layer *under* the apps: factory_flow, order_management, jivo_ecom, CRM, po_db, jivo_site, task… (16 DBs) | full SQL browser + MCP | `./postsql/postsql doctor` |
| `portals/blinkit/cli/` | **Blinkit partner portal** (partnersbiz.com) — POs, invoices, sales, SOH, scorecard, payments, appointments, offers, assortment | 65 read cmds | `BLINKIT_TOKEN=… ./portals/blinkit/cli/blinkit-partner doctor` |
| `portals/zepto/cli/` | **Zepto seller portal** (brands.zepto.co.in) — PO/ASN/GRN·catalog·stock·invoicing·ledger·payments·receivables·contracts·RTV·FBZ · ads campaigns/creative/analytics/wallet · geo/market/consumer insights · users·KYC·subscription | **417 read cmds, 25 groups** (+ study vault, 741 endpoints/7 backends) | `bash ~/ecomcliauto/orchestrate/zepto-login.sh` → `./portals/zepto/cli/zepto-portal doctor` |

**Brand/seller portals** (`portals/`) are studied then turned into read-only CLIs. Each portal gets an Obsidian study vault (`portals/<name>/vault/`) + a generated CLI (`portals/<name>/cli/`). Blinkit partner is done (study: 11 sections/89 read endpoints; CLI: 65 cmds, live-verified). **Zepto seller portal study is done** — the whole `brands.zepto.co.in` module-federation micro-frontend mapped from its harvested JS corpus: **25 sections / 741 endpoint contracts across 7 backends** (vault `portals/zepto/vault/`, start at `00-Zepto-Atlas.md`; master index `Zepto-Endpoints.md`). Unattended email-OTP auth via `bash ~/ecomcliauto/orchestrate/zepto-login.sh` (one JWT for all backends). Zepto CLI is **done**: `portals/zepto/cli/zepto-portal` — **417 read commands across 25 section groups** (cobra, stdlib; one JWT authorizes all 7 backends; 3-layer read-only guardrail), generated from the study vault. Auth (Blinkit): `bash ~/ecomcliauto/orchestrate/blinkit-login.sh` → `export BLINKIT_TOKEN=…`. Next: Blinkit **ads** portal, then Amazon-VC/Flipkart/BigBasket.

`postsql` is different in kind from the others: they read each system's **HTTP API**, `postsql` reads the **database directly** (read-only, 3-layer guarantee — `BEGIN READ ONLY` + `default_transaction_read_only` + SELECT-only allowlist). Config in `~/.postsql/config.toml`. ⚠️ connects as `postgres` superuser (only cred available) — wide read blast radius; a `NOSUPERUSER` SELECT-only role is the recommended hardening (see its README).

## Connections — how systems join

`connections/` is the Obsidian vault mapping **all 15 CLI-pair joins** with evidence levels (start at `connections/CONNECTIONS_MOC.md`). `CLI-HUB-README.md` is the original hub note. The value chain:

```
EXIM → Factory → OMS → Ecom → jivo-scrape (market)
          ╲ JSAP overlay (who approved/did what) ╱
                    SAP B1 (the books)
```

`product-identity/` is the exact-match bridge to walk one SKU across the whole chain.

## Credentials & auth

- `.env` (gitignored, chmod 600) — consolidated creds for ecom/exim/factory/oms/jsap.
- SAP creds: `sap-b1/cli/.env`. Control-panel creds: `control-panel/.env`.
- JWTs expire. Re-login (creds come from `.env`):
  - OMS: `set -a && source .env && ./oms-cli/oms-pp-cli auth login --username "$OMS_USERNAME" --password "$OMS_PASSWORD"`
  - Factory: `... ./factory-cli/jivo-factory-pp-cli auth login --email "$JIVO_FACTORY_EMAIL" --password "$JIVO_FACTORY_PASSWORD"`
  - JSAP: auto-bootstraps its session into `~/.jsap/`.
- Go CLIs support `--agent` (JSON+compact) for AI consumption. Doctor's "Cache: unknown" is harmless (local cache unhydrated); the auth lines are what matter.

## Layout notes

- `sap-b1/` and `control-panel/` keep their **own git repos** (this outer repo ignores them — see `.gitignore`).
- Compatibility symlinks left behind so nothing old breaks: `~/jivogpt/CLI` → here, `~/jivogpt/Connections` → `connections/`, `~/software` → `control-panel/`, `~/sap-b1` → `sap-b1/`.
- The VPS deployment of jsap/jivoscrape MCPs uses `/opt/jivogpt/CLI/...` — unaffected by this Mac-side layout.
- Related JIVO tools that live elsewhere on purpose: `~/pp-swiggy` (Swiggy intel), `~/jivo-instamart-collector`, jivoshop CLI (shop.jivo.in orders), `~/jivo-data-bank`.
