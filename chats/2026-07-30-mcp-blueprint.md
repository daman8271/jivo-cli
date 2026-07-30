# MCP done right — the complete blueprint (2026-07-30)

**Decision:** phone access goes through the MCP layer. This doc is the "nothing left out" checklist: what exists, what's missing, and the exact build order.

## Verified current state (probed live 2026-07-30 ~02:30)

- **5 servers live** on VPS behind Traefik at `jivo-mcp.srv1685505.hstgr.cloud/<pathbase>/<name>/mcp`: **sapb1, postsql, ecom, oms, factory** — all answered MCP `initialize` with 200, containers up 12h.
- **Auth = one shared secret path** (`.pathbase`) for everyone. No per-user identity, no revocation, no audit trail of *who* asked.
- **sapb1 tools** (read `sap-b1/cli/internal/mcp/server.go`): doctor, query, entities, ops, fields, orders, invoices, items, partners. Parameter docs are good; **the accounting domain knowledge is NOT in the server** — it lives only in this repo's CLAUDE.md, which a phone client never sees.
- **No aggregation tools** — "FY26 turnover" currently requires the client to page through every invoice and sum client-side. Fine in Claude Code on a laptop; token-death on a phone.
- **Blocked:** sapb1's SAP Service Layer access pending SAP-side whitelist of the VPS IP (memory `jivo-mcp-layer`) — server responds but tool calls can't reach SAP until then.
- **Built but not deployed:** exim (`exim-pp-mcp`), control-panel (`jivo-pp-mcp`) — binaries exist in repo, just not in the compose bundle. **No MCP at all yet:** tankhapay, hana-sql (the fast path!), dsr, attachments.

---

## The 6 layers (miss none)

### Layer 1 — Coverage: every system gets a server

| Server | Status | Action |
|---|---|---|
| sapb1 | live, SAP-blocked | unblock whitelist — **blocker #1** |
| postsql | live | — |
| ecom / oms / factory | live | — |
| exim | binary exists | add to compose (~30 min) |
| control-panel (jivo) | binary exists | add to compose (~30 min) |
| tankhapay | CLI exists (297 cmds) | build `mcp` subcommand same pattern, deploy |
| **hana** (direct SQL) | **missing — highest value** | new server: `hana_sql` (SELECT-only, enforced LIMIT+timeout), `hana_tables`, `hana_describe`, + the aggregate tools below. Runs on VPS via the existing SSH tunnel to port 30015 |
| dsr | goal #97 | `dsr` CLI → mcp subcommand when CLI lands |
| attachments | missing | Phase 2: `attachments_search`/`attachments_fetch` over the SMB share (later: OCR+embeddings = the real RAG piece) |

### Layer 2 — Tool design: correct AND cheap on a phone

1. **Server-side aggregation tools — the single biggest gap.** Add to sapb1/hana: `turnover(company, from, to)` (net of GST, minus credit notes, excl. cancelled — computed server-side), `party_balance(name)` (all accounts, sign explained), `party_statement(name, from, to)`, `stock_position(item/group)`, `top_customers(n, period)`. Small JSON out, never thousands of rows.
2. **Bake the domain knowledge into the servers** so ANY client answers correctly without our CLAUDE.md:
   - MCP `instructions` field (sent at initialize): positive balance = DEBIT, turnover formula, `Cancelled eq 'tNO'`, qty is per BOTTLE not carton, Oil→Mart is intercompany — exclude from real sales, use U_TYPE/U_Sub_Group not name matching, `toupper()` unsupported, date-filter syntax, money is INR/crores.
   - Same rules repeated in the relevant tool descriptions (clients ignore instructions sometimes; descriptions always load).
   - An MCP **resource** `jivo://definitions` + MCP **prompts** (`party_statement`, `monthly_turnover`) for guided workflows.
3. **`readOnlyHint: true` annotation on every tool** (add wherever missing) + human titles.
4. **Output discipline:** hard row caps, cursor pagination, compact JSON — phone contexts are small.
5. **Errors that teach:** when a filter uses `toupper()`, return "not supported — fetch partners and match client-side" instead of a raw OData error.
6. **Tool-count discipline:** ≤ ~15 tools per server, each with a "call this when…" line — connectors load them all into every chat.

### Layer 3 — Security (gate for any rollout beyond 2-3 people)

1. **Per-user auth, phased:**
   - *Now (day):* per-user path tokens — one Traefik router per user (`/mcp-<user-token>/…`), revocable, identifies the user in logs.
   - *At >5 users:* proper MCP OAuth 2.1 gateway in front (claude.ai connectors support OAuth with dynamic client registration) — real logins, revocation, scopes per role (Accounts vs Sales vs Ops see different servers).
2. **Audit log:** per-tool-call record (user, tool, args, row count, duration) appended server-side + Traefik access logs. This is non-negotiable for financial data.
3. **Read-only enforced in code, with tests:** keep the GET-only guards (cf. `factory-cli/.printing-press-patches/0003-preserve-mcp-get-only-guards.md`); add a test per server asserting no mutating verb can exist. For `hana_sql`: SELECT-only parser check, statement timeout, row cap.
4. **Rate limits** per token (Traefik middleware) + request-size caps.
5. **Secrets:** env dirs stay 700/600 (already), rotation calendar, SAP password never echoed (check `doctor` output), pathbase secrets rotate when anyone leaves.
6. **Network:** HANA 30015 and SAP Service Layer never public — only the VPS IP whitelisted SAP-side; MCP servers are the only public surface, TLS via Let's Encrypt (already).

### Layer 4 — Ops & reliability

- **Health probe cron** (extend today's probe): initialize + `tools/list` + one cheap call per server every 10 min; alert on failure (same pattern as `fleet-health.sh`).
- **Staging lane:** second pathbase (`/mcp-staging-…`) pointing at new binaries — test before swapping prod.
- **Deploy script:** build → scp → `docker compose up -d` documented in `README-DEPLOY.md` (exists — keep current).
- Version-pin binaries, keep `/opt/jivo-mcp/env` backed up, watch the HANA tunnel (hana tools die if the reverse tunnel drops — add it to the health probe).

### Layer 5 — Client rollout

- **Team plan** (₹2,399/seat): admin pre-configures the connectors org-wide (Team includes remote-connector admin controls); users just sign in on the phone app.
- Connector naming matters — "JIVO SAP (Books)", "JIVO HANA (fast)", "JIVO Payroll" with one-line descriptions; users toggle per chat.
- One-page setup doc with screenshots: claude.ai → Settings → Connectors → add URL → open phone app.
- Same servers plug into LibreChat / a custom app / even ChatGPT later — zero rework. That's the whole point of betting on MCP.

### Layer 6 — Testing & acceptance

- **Golden-question set:** ~20 questions with known answers (use savings-audit verified figures + ASK-EXAMPLES.md) — run from a phone, numbers must match SAP exactly. Re-run monthly and after every server change.
- Token/cost sampling per question during pilot (before promising anyone a budget).

---

## Build order

**Week 1 (unblock + safety):**
1. SAP whitelist of VPS IP → sapb1 actually works end-to-end
2. Per-user path tokens + audit logging
3. Bake `instructions` + definitions into sapb1 server
4. Health-probe cron
5. Connectors on 2 phones (you + one Accounts person) → run 10 golden questions

**Week 2–3 (make it excellent):**
6. `hana` MCP server with the aggregation tools (turnover/balance/statement/stock)
7. Deploy exim + control-panel (exist), build tankhapay MCP
8. Full golden-question harness, error-message polish, prompts/resources

**Month 2 (scale):**
9. OAuth gateway + per-role scoping
10. dsr MCP, attachments search, staging lane
11. Team-plan rollout with the setup doc

**Definition of "best":** an Accounts person on a phone asks "Adani ka is month ka statement" and gets the exact SAP number in one tool call, we know exactly who asked and when, nothing can write, and the same server powers whatever front-end comes next.
