# JIVO CLI — every window into the company, one folder

> # 👉 New here? Read [**SETUP.md**](SETUP.md) and start from there.
>
> One command, two questions, and you can ask about JIVO in plain English. You do
> not need to read this file — it is the technical map. **[SETUP.md](SETUP.md) is
> the one you want.**

> ## ⚠️ READS EVERYWHERE · WRITES ONLY INTO SAP, ONLY WHEN TYPED
>
> **Reading is safe everywhere.** Every CLI here reads JIVO's live production
> systems. Asking a question never changes anything, in any system.
>
> **SAP is the only system that can be written to, and only from the CLI, and only
> when a person types the command.** `sapb1` has exactly three:
>
> | | What it does | Reversible? |
> |---|---|---|
> | `sapb1 draft <doctype>` | Creates a SAP **draft**. No stock movement, no ledger entry, until a human opens Document Drafts and presses **Add** | **Yes** — a human ignoring it undoes it |
> | `sapb1 post <EntitySet>` | Creates **live**. Master data only (BusinessPartners, Items) | **No** |
> | `sapb1 patch <Entity(key)>` | Updates fields on one existing object | **No** |
>
> **When in doubt, draft it.** Prefer `draft` for anything document-shaped.
>
> Every write previews first (`--dry-run` sends nothing), then requires the word
> `yes` typed in full — `y` is rejected — and refuses outright when stdin is not a
> terminal, so a cron or an unattended agent cannot write without `--yes` being an
> explicit human decision. Every attempt is appended to
> `queries/<operator>/sap-writes.jsonl`, which syncs to `main` — **so every write
> by every operator lands in one shared history.**
>
> **Everything except SAP is read-only, full stop** — postsql, portals, exim,
> factory, oms, jsap, TankhaPay, DSR. No exceptions, even if asked.
>
> **What no tool here can do at all:** there is no `DELETE` and no `PUT` anywhere,
> and `post` accepts only a bare catalogued entity set — so SAP's OData *actions*
> (`Invoices(9)/Cancel`, `Orders(1)/Close`, `Drafts(4321)/SaveDraftToDocument`) are
> refused by design, with no override. Cancelling, closing and posting a draft are
> a human's job in the SAP B1 client.
>
> **⛔ Every "ask in English" surface stays read-only, permanently.** Claude Desktop
> and MCP expose read tools only, on every device — the write commands exist only in
> the CLI, where a human is at the keyboard. The MCP servers are published through
> the gateway and answer from a phone, so a write path there is a write path for
> anyone holding the URL. Two tests enforce it. See [NEW-DEVICE.md](NEW-DEVICE.md).

One home for all JIVO business-system CLIs, their credentials, and the knowledge of how they connect. Fleet live-tested 2026-07-23.

> **Setting up a new machine? → [NEW-DEVICE.md](NEW-DEVICE.md)** — clone, restore credentials,
> build, verify, and how writes work. Start there.
>
> **Cloning from GitHub?** One repo, everything in it — a plain `git clone` gets the whole toolkit.
> The repo ships **without secrets**: no `.env` / `*.env` / `*.token` files anywhere — every CLI needs its credentials restored locally before it will log in (see [Credentials & auth](#credentials--auth)).

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
| `portals/tankhapay/cli/` | **TankhaPay Business** (business.tankhapay.com) — JIVO's HR/payroll/workforce SaaS: employees·attendance·payouts·salary·approvals·leave·accounts/taxes·reports·recruit·masters·org·broadcast·contract-labour·training | **297 read cmds, 14 groups** (+ study vault, 726 endpoints/4 backends, 325 pages) | `tankhapay-portal doctor` (headless `.env` login; daily auto-refresh via LaunchAgent) |

**Brand/seller portals** (`portals/`) are studied then turned into read-only CLIs. Each portal gets an Obsidian study vault (`portals/<name>/vault/`) + a generated CLI (`portals/<name>/cli/`). Blinkit partner is done (study: 11 sections/89 read endpoints; CLI: 65 cmds, live-verified). **Zepto seller portal study is done** — the whole `brands.zepto.co.in` module-federation micro-frontend mapped from its harvested JS corpus: **25 sections / 741 endpoint contracts across 7 backends** (vault `portals/zepto/vault/`, start at `00-Zepto-Atlas.md`; master index `Zepto-Endpoints.md`). Unattended email-OTP auth via `bash ~/ecomcliauto/orchestrate/zepto-login.sh` (one JWT for all backends). Zepto CLI is **done**: `portals/zepto/cli/zepto-portal` — **417 read commands across 25 section groups** (cobra, stdlib; one JWT authorizes all 7 backends; 3-layer read-only guardrail), generated from the study vault. Auth (Blinkit): `bash ~/ecomcliauto/orchestrate/blinkit-login.sh` → `export BLINKIT_TOKEN=…`. **TankhaPay Business is done** — `business.tankhapay.com` (JIVO's HR/payroll SaaS) mapped from its harvested Angular corpus: **14 sections / 726 endpoints / 325 pages across 4 backends**, all reverse-engineered incl. the AES-128-ECB body cipher (`{encrypted}`/`commonData`, key `0123456789abcdef`) and headless bearer-JWT login (creds in root `.env` `TPAY_*` + `portals/tankhapay/.env`; reCAPTCHA-bypassed, one 24h JWT for all backends). CLI `portals/tankhapay/cli/tankhapay-portal` — **297 read commands, 14 groups** (cobra, stdlib; 3-layer read-only guardrail + coverage test), vault at `portals/tankhapay/vault/00-TankhaPay-Atlas.md`. A LaunchAgent (`com.jivo.tankhapay-login-refresh`) re-mints the token twice daily so nothing goes stale. Next: Blinkit **ads** portal, then Amazon-VC/Flipkart/BigBasket.

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

- `sap-b1/`, `control-panel/`, and `postsql/` used to be separate git repos; they're now plain folders of this one repo (old histories archived in `~/jivo-cli-archived-nested-git/`).
- Compatibility symlinks left behind so nothing old breaks: `~/jivogpt/CLI` → here, `~/jivogpt/Connections` → `connections/`, `~/software` → `control-panel/`, `~/sap-b1` → `sap-b1/`.
- The VPS deployment of jsap/jivoscrape MCPs uses `/opt/jivogpt/CLI/...` — unaffected by this Mac-side layout.
- Related JIVO tools that live elsewhere on purpose: `~/pp-swiggy` (Swiggy intel), `~/jivo-instamart-collector`, jivoshop CLI (shop.jivo.in orders), `~/jivo-data-bank`.
