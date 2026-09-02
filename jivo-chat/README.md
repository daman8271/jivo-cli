# jivo-chat

A web page where anyone in the JIVO office asks a question in plain language and
gets a real number, pulled live. Claude Opus 5 drives it; the existing read-only
`mcp-gateway/` is the only way it touches a business system.

```
browser  ──►  this server (VPS)  ──►  Claude API
                    │
                    └──►  mcp-gateway  ──►  SAP B1 · HANA · ecom · oms · factory · exim · jsap · postgres
```

Claude never reaches a business system itself. It can only *ask* this server to
run a tool; this server checks the user's role first and then calls the gateway,
which is structurally read-only. Nothing in this app can write anywhere.

## Run it

```bash
cd jivo-chat
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env            # fill in ANTHROPIC_API_KEY
./.venv/bin/python -m app.server adduser you@jivo.in "Your Name" 'a-password' owner
./.venv/bin/python -m app.server
```

Then open <http://localhost:8080>.

The gateway must be reachable at `JIVO_GATEWAY_URL`. It runs on the VPS, so from
the Mac tunnel it first:

```bash
ssh -N -L 7700:127.0.0.1:7700 vps
```

Check what the model will be able to see, before running anything:

```bash
./.venv/bin/python -m app.server tools    # every tool the gateway advertises
./.venv/bin/python -m app.server roles    # which prefixes each role may use
```

## The API key is not your subscription

`ANTHROPIC_API_KEY` is a per-token key from console.anthropic.com. A Claude Code
/ Max subscription does **not** cover API calls. Without a billed key the app
starts, the page loads, and every question fails.

## Roles

A role is a whitelist of tool-name prefixes, in the `roles` table. Deny by
default: a tool matching no prefix is never advertised to the model, so it
cannot be called, and a call that arrives anyway is rejected before the gateway.

| Role | Sees |
|---|---|
| `owner` | everything |
| `accounts` | `sap_`, `hana_` — books, ledgers, turnover, payments |
| `sales` | `oms_`, `ecom_` — orders and channel sales |
| `factory` | `fct_`, `exim_` — production, stock, imports |

Change a role by editing its `tool_prefixes` JSON in the `roles` table. Add
someone with `adduser EMAIL NAME PASSWORD ROLE`.

## Cost

Opus 5 is $5 / $25 per million tokens. A typical answer — cached system prompt,
one tool result, a short reply — is around **₹6**. A long chat with big tool
results can reach **₹45+** for a single turn, which is why three things exist:

- tool output is capped at 60k characters before it reaches the context
- `JIVO_CHAT_DAILY_CAP_INR` stops a user once they pass their daily limit
- the context bar in the UI shows how full the chat is, live

Every request caches the system prompt and corrections digest, so the repeated
part costs 10% after the first turn. Do not put anything per-request above that
cache breakpoint in `agent.py`.

## What is recorded

Everything, in `jivo-chat.db`:

- `messages` — the full conversation, content blocks verbatim (thinking blocks
  included; they must be replayed unchanged on the same model)
- `audit` — every question, every tool call with its arguments, every answer,
  every denial
- `spend` — tokens and rupees per user per turn
- `memories` — what Claude has learned about each person, keyed by user so one
  person's memory can never appear in another's chat

## Known gaps

- **The SAP tunnel is the weak point.** It currently runs through an office PC.
  If that box is off, every question fails. The durable fix is a reverse tunnel
  from the SAP host to the VPS.
- No HTTPS yet — put nginx + certbot in front before this leaves the LAN.
- Compaction is not wired up yet, so a chat that fills 1M tokens will stop
  rather than summarizing itself.
