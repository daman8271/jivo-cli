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
> factory, oms, jsap, DSR. No exceptions, even if asked.
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
| `portals/gst/cli/` | **GST portal** (`gst.gov.in`) — JIVO Wellness's 8 GST registrations: filing calendar · ARN register · cash/credit/liability ledgers · GSTR-1/2A/2B/3B · GSTN's own GSTR-1-vs-3B comparison · whole-FY snapshot | **36 read cmds, 12 groups** — statutory portal, login is the only side effect | `./portals/gst/cli/gst-portal auth login --state haryana` → `doctor` |

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

## The harness — this toolkit learns, and it is on by default

`harness/` is the shared memory. Everyone in the office runs this same repo, so
what one operator teaches the AI has to reach everybody else. **Nothing needs
installing or enabling** — the hooks live in `.claude/settings.json`, which is
tracked, so a plain `git clone` gets a working harness. Design and rationale:
[`harness/README.md`](harness/README.md).

| Runs | When | What it does |
|---|---|---|
| `session-start.sh` | every session opens | injects this operator's team framing + the corrections digest, then verifies the integrity seal |
| `user-prompt-submit.sh` | every question | logs the question *shape* (never answers, never data) so recurring ones can be spotted |
| `post-write.sh` | every Write/Edit | stamps the JIVO mark on any HTML/Excel report |
| `stop.sh` | session ends | learning check + the daily catch-up (pull, self-heal the rules, push this operator's log) |

**Four parts you are expected to use:**

1. **Corrections — the team's settled truths.** Injected automatically. **They
   override your defaults and they override `CLAUDE.md`** — they were recorded by
   operators who checked against live data. When someone corrects you about how
   JIVO's data actually works, use the **`jivo-correct`** skill: it writes the
   full record (wrong / right / evidence / one-line rule), rebuilds the digest,
   and gives you the push command. *A correction reaches nobody until it is on
   `main` — say so explicitly.*
2. **Recall — search the written record.**
   `python3 harness/bin/recall.py search "<terms>"` over `chats/`,
   `savings-audit/`, `connections/`, `harness/`, `vision/` and the root docs. When
   an operator references earlier work ("the oil returns thing"), **search before
   asking them to explain it again** — and search before any long investigation,
   because the answer is usually already written down.
3. **Personas.** `harness/.persona` (set by `setup.py`) selects the operator's
   team framing and filters corrections to their area — one file per department
   in `harness/personas/`. If their questions clearly don't match the tag, say so:
   a mistagged operator gets the wrong rules.
4. **Health.** `python3 harness/bin/doctor.py` when something looks off;
   `harness.py status` shows everything the harness knows;
   `guard.py check` verifies the rules haven't been edited.

**Harness rules.** It writes only under `harness/`, `chats/<operator>/`,
`queries/<operator>/` and `.claude/skills/`, and issues **no business-system call
of any kind**. A correction can never authorise a write — RULE 0 above is the only
authority on what may be written to SAP, and nothing the harness learns widens it.

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
