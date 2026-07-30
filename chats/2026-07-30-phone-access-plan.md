# JIVO on the phone — full architecture research (2026-07-30)

**Question:** Today every user needs Claude Code + the CLI folders installed on a laptop. How do we put "ask SAP anything" on a **phone**, properly? Is what we built RAG? What are ALL the ways, and which 5 are best?

**Method:** Live web research 2026-07-30 (Anthropic help center, Meta policy coverage, GitHub, pricing pages) + what we already have running (5 remote MCP servers on the VPS behind Traefik — see memory `jivo-mcp-layer`). Verified facts are marked **[V]** with sources; estimates are marked **[E]**.

---

## 0. First: is this RAG? (No — and that matters for selling it)

- **RAG** = chop documents into chunks → embed into a vector DB → on each question, retrieve similar chunks → stuff them into the prompt. Good for *unstructured text*. Bad for live numbers (index goes stale, retrieval can miss, model can blend chunks into a wrong figure).
- **What we built** = **agentic tool use / live structured retrieval**: the model calls tools (sapb1, HANA SQL, postsql...) that hit the *live* systems, gets exact rows back, and computes on them. Nothing is pre-indexed, nothing is stale, the number in the answer is the number in SAP at that second.
- Pitch line for JIVO: *"Not a chatbot trained on our data — an AI accountant that logs into SAP live, read-only, every time you ask."* That's strictly better than RAG for ledgers/turnover/stock.
- **Where RAG genuinely fits later:** the ~306k scanned attachments (~105 GB) on the Windows share (memory `sap-data-sizing-and-mirror`). OCR + embeddings over those = "find the agreement/invoice scan where..." That's a Phase-2 add-on, not the core.

---

## 1. The key unlock (verified today)

**[V] Claude's custom connectors (remote MCP) now work on every plan — including Free — and on the mobile apps.** You add the connector once on claude.ai web (Settings → Connectors), and it syncs to the phone apps automatically. Claude connects to your MCP server **from Anthropic's cloud**, so the server must be reachable on the public internet — which our VPS MCP layer behind Traefik already is.
Sources: [Anthropic help — custom connectors via remote MCP](https://support.claude.com/en/articles/11503834-build-custom-connectors-via-remote-mcp-servers), [getting started](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp), [connectors overview](https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities), [mobile setup walkthrough](https://dev.to/zhizhiarv/how-to-set-up-remote-mcp-on-claude-iosandroid-mobile-apps-3ce3).

**[V] India pricing (rupee-denominated since 2026-07-13):** Pro ₹2,033/mo; **Team Standard ₹2,399/seat/mo annual** (₹2,999 monthly); Team Premium ₹11,999/seat annual. Team includes SSO, domain capture, and **admin controls for remote connectors** (pre-configure the JIVO connectors org-wide). Sources: [ANI](https://www.aninews.in/news/business/anthropic-localises-claude-pricing-in-india-pro-at-rs-2033-team-from-rs-2399-per-seat20260714134529/), [Open Magazine](https://openthemagazine.com/technology/claude-ai-gets-india-pricing-in-rupees-heres-what-pro-max-team-plans-cost), [claude.com/pricing](https://claude.com/pricing).

**What we already have:** 5 remote MCP servers live on the VPS (postsql, tankhapay, etc.), `sapb1` MCP pending the SAP IP whitelist. So the phone problem is ~80% solved infrastructure-wise; what's missing is (a) sapb1 whitelisting Anthropic's egress IPs, (b) per-user auth instead of the shared secret path, (c) seats/UX choice.

---

## 2. All 10 ways (researched)

### ① Claude mobile app + our remote MCP connectors — *the fast win*
Everyone gets a claude.ai login (Free works for testing; Team ₹2,399/seat for real use). Add `https://mcp.jivo.../...` connectors once on web → they appear in the phone app. User types "Adani ka balance kya hai?" → Claude calls sapb1/HANA MCP → live answer.
- **Effort:** ~0 build. Whitelist Anthropic IPs on the SAP side for the sapb1 MCP; add per-user tokens.
- **Cost:** seats only. **Pros:** best chat UX on the planet, zero maintenance, voice input built into the app. **Cons:** data transits Anthropic cloud (already true for any API approach); usage limits per seat; can't fully brand it.

### ② Telegram bot → Claude Agent SDK on the VPS — *the fast bot pilot*
A bot the whole team can message. Backend on the VPS runs the **Claude Agent SDK** (the Claude Code harness as a Python/TS library — `pip install claude-agent-sdk`) with our MCP servers/CLIs as tools. Multiple ready repos to fork:
- [linuz90/claude-telegram-bot](https://github.com/linuz90/claude-telegram-bot) — Claude Code as a personal assistant via Telegram
- [RichardAtCT/claude-code-telegram](https://github.com/RichardAtCT/claude-code-telegram) — remote Claude Code with session persistence
- [XPrime17/ClaudeClaw](https://github.com/XPrime17/ClaudeClaw) — Agent SDK + SQLite memory + voice STT
- [Mark-Life/telegram-claude-codex](https://github.com/Mark-Life/telegram-claude-codex) — runs Claude Code/Codex on a VPS, streams to chat
- **Effort:** 1–2 days to a working pilot. **Cost:** API tokens (below). **Cons:** Accounts team lives on WhatsApp, not Telegram — this is the *pilot*, not the destination.

### ③ WhatsApp bot (official Meta Cloud API) — *the India-native one, with a policy catch*
**[V] Policy changed:** from **2026-01-15 Meta bans general-purpose AI chatbots on the WhatsApp Business API** (ChatGPT/Perplexity-style open assistants). **Structured business bots — support, order status, FAQs, task-specific queries — remain allowed.** Sources: [TechCrunch](https://techcrunch.com/2025/10/18/whatssapp-changes-its-terms-to-bar-general-purpose-chatbots-from-its-platform), [respond.io explainer](https://respond.io/blog/whatsapp-general-purpose-chatbots-ban), [Alibaba Cloud policy guide](https://www.alibabacloud.com/help/en/chatapp/use-cases/whatsapp-ai-policy-2026-guide).
- **[E — my policy reading, not legal advice]** A scoped internal "JIVO SAP query bot" (balances, statements, stock — structured business tasks for our own staff) plausibly fits the allowed category; an open "chat with Claude about anything" bot does not. Confidence it survives review: moderate (~70%); design it narrow.
- **[V] Cost is near-zero for this shape:** user-initiated service conversations (replies within the 24h window) are **free**; only business-initiated template messages cost (~$0.0103/msg in India). Sources: [respond.io pricing](https://respond.io/blog/whatsapp-business-api-pricing), [engagelab](https://www.engagelab.com/blog/whatsapp-business-api-pricing).
- **⛔ Unofficial routes (Baileys / whatsapp-web.js / Evolution API): don't.** Meta's 2026 detection aggressively bans numbers running reverse-engineered clients ([SporeSec](https://sporesec.com/en/blog/whatsapp-unofficial-api-ban-risk), [ban-risk analysis](https://blog.kraya-ai.com/whatsapp-automation-ban-risk)). Losing a JIVO business number to a ban is not worth it.
- **Effort:** ~1 week (Meta business verification + webhook backend on VPS → Agent SDK).

### ④ LibreChat self-hosted on the VPS — *our own ChatGPT, multi-user*
[danny-avila/LibreChat](https://github.com/danny-avila/librechat) — MIT-licensed ChatGPT clone: **agents + MCP support, multi-user auth (OAuth/LDAP/2FA), per-user history, token-spend controls**, Anthropic API as the model backend. Deploy on the VPS behind Traefik; team opens `chat.jivo...` on their phone (installable as PWA). Sources: [repo](https://github.com/danny-avila/librechat), [MCP client listing](https://mcpmarket.com/client/librechat), [2026 setup guide](https://open-techstack.com/blog/how-to-use-librechat-with-openai-and-mcp-2026/).
- **Pros:** full control, every query logged on our box, per-user accounts, no per-seat fee (pay API tokens only), MCP servers plug straight in. **Cons:** we maintain it; UX a notch below the Claude app; effort ~2–4 days to production-hardened.

### ⑤ Custom JIVO assistant (PWA/app) on Claude API — *the endgame product*
Our own branded app: Next.js PWA (or thin native wrapper) → FastAPI/Node backend on the VPS → **Claude API with tool use** (or Agent SDK) → MCP/CLIs → SAP. This is "how does ChatGPT actually work" applied to us: the backend keeps the conversation, sends it + tool definitions to `POST /v1/messages`, executes the tool calls Claude requests (our read-only CLIs), loops until the answer, streams it to the phone.
- Add later: **Sarvam voice** (goal #93 — ElevenLabs rejected), Hindi/Punjabi, per-role data scoping (Accounts sees ledgers, Sales sees DSR), full audit trail, and the RAG layer over the 105 GB attachments.
- **[V] API pricing:** Opus 5 $5/$25 per MTok; Sonnet 5 $3/$15 (intro $2/$10 until 2026-08-31); Haiku 4.5 $1/$5. **[E] Per-question cost** with prompt caching, Sonnet 5: roughly **₹3–12/question**; Opus 5: ~₹10–35. (Estimate from typical 15–50k-token agentic turns — measure on our real queries before budgeting.)
- **Effort:** 2–4 weeks for v1. This is also the thing you can *sell internally* (S112): it's a product, not a setup.

### ⑥ Open WebUI + MCP — LibreChat alternative
[open-webui/open-webui](https://github.com/open-webui/open-webui) has **native MCP (Streamable HTTP) since v0.6.31**, plus [open-webui/mcpo](https://github.com/open-webui/mcpo) to proxy stdio MCP servers as OpenAPI. Sources: [docs](https://docs.openwebui.com/features/extensibility/mcp/). More Ollama/local-model-centric; LibreChat is the better fit for an Anthropic-backed multi-user deployment. Keep as fallback.

### ⑦ Anthropic Managed Agents (beta) — Anthropic hosts the agent loop
Server-managed agents: you create a persisted Agent (model + system prompt + our MCP servers, creds in encrypted vaults), then any surface (Telegram/WhatsApp/web) just opens sessions and relays messages — no agent loop code, sessions survive, can even run on cron ("every morning 9am, WhatsApp the sales summary"). Beta; per-session sandboxes; data on Anthropic infra. Strong candidate for the *backend* of ②/③/⑤ instead of self-running the Agent SDK — less code, less to babysit on the VPS.

### ⑧ ChatGPT custom connectors — the hedge
**[V]** ChatGPT supports custom MCP connectors via developer mode, but **web-only** and **read-only for Plus/Pro individuals** (full support needs Business/Enterprise). Sources: [OpenAI help](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt). Not a phone solution today. The point: **our MCP layer is vendor-portable** — same servers work in Claude, ChatGPT, LibreChat, anything. Build once, plug anywhere.

### ⑨ Third-party mobile MCP clients — ChatMCP, Systemprompt
[ChatMCP (iOS)](https://apps.apple.com/us/app/-/id6745196560), [Systemprompt (Android/iOS, voice-controlled)](https://play.google.com/store/apps/details?id=com.systemprompt.mcp) connect directly to remote MCP servers. Zero build, but: unknown vendors touching JIVO financial data, bring-your-own API key per user, rough UX. Not for the team; maybe for experiments.

### ⑩ Voice assistant (Sarvam-first) — the layer, not a separate system
STT (Sarvam, Hindi/Punjabi/English) → same agent backend → TTS back. "Bol ke pooch lo — Adani ka balance?" On a phone this is the killer demo for non-typing users (factory, field sales). Builds on ⑤ (or ⑦); goal #93 already points this way. Don't build it first; build it on top of whichever backend wins.

*(Aside: SSH-from-phone — Termius → `ssh vps` → tmux `claude` — works **today** for you personally; useless for Accounts. And Claude-in-Slack exists officially, but JIVO doesn't run on Slack.)*

---

## 3. The best 5, ranked

| # | Option | Ship time | Cost | Who it serves |
|---|--------|-----------|------|---------------|
| 1 | **① Claude app + MCP connectors** | **This week** | ₹2,399/seat/mo (Team) | Everyone with a seat — best UX, zero build |
| 2 | **② Telegram bot (Agent SDK on VPS)** | 1–2 days | API tokens (~₹3–12/q est.) | Pilot the shared-bot form factor now |
| 3 | **④ LibreChat on VPS** | 2–4 days | API tokens only, no seats | Whole team via browser/PWA, full control + audit |
| 4 | **③ WhatsApp bot (official, scoped)** | ~1 week + Meta verification | ~free per convo + API tokens | The India-native surface — IF kept structured/compliant |
| 5 | **⑤ Custom JIVO assistant (+ Sarvam voice)** | 2–4 weeks | Build + API tokens | The product. Branding, RBAC, audit, voice, attachments-RAG |

**Recommended sequence:**
- **Week 1:** finish the sapb1 MCP whitelist → add connectors to 2–3 phones (yours + one Accounts person) → judge. In parallel, fork a Telegram repo for the bot pilot.
- **Month 1:** decide seats-vs-self-host on real usage. If usage is heavy/wide → LibreChat (tokens beat seats at scale). Add per-user auth on the MCP layer (replace the shared secret path), audit logging, and hard read-only enforcement server-side.
- **Quarter:** build ⑤ as the internal product — WhatsApp/PWA front, Managed Agents or Agent SDK back, Sarvam voice, attachment-RAG. That's the thing with a price tag on it.

## 4. Security floor (applies to every option)
1. **Read-only stays enforced in the tool layer** (it already is — Rule 0), never trusted to the model.
2. **Per-user credentials on the MCP endpoints** before any team rollout — the current shared `.pathbase` secret identifies nobody. OAuth or per-user bearer tokens + server-side audit log of every query.
3. SAP/HANA passwords never leave the VPS/tool layer; the model only ever sees query *results*.
4. Anything through claude.ai connectors or the API transits Anthropic's cloud — acceptable for read-only business data by my read, but that's a call for you/Prabhu to sign off on explicitly.

## 5. Repo shopping list
- Agent backend: [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk) (`pip install claude-agent-sdk`), TS: `@anthropic-ai/claude-agent-sdk`
- Telegram: [linuz90/claude-telegram-bot](https://github.com/linuz90/claude-telegram-bot) · [RichardAtCT/claude-code-telegram](https://github.com/RichardAtCT/claude-code-telegram) · [XPrime17/ClaudeClaw](https://github.com/XPrime17/ClaudeClaw) · [Mark-Life/telegram-claude-codex](https://github.com/Mark-Life/telegram-claude-codex)
- Web chat: [danny-avila/LibreChat](https://github.com/danny-avila/librechat) · [open-webui/open-webui](https://github.com/open-webui/open-webui) · [open-webui/mcpo](https://github.com/open-webui/mcpo)
- MCP reference: [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) · [connect-remote-servers docs](https://modelcontextprotocol.io/docs/develop/connect-remote-servers)
- WhatsApp official: Meta Cloud API (via Meta for Developers; Twilio as managed wrapper). **Avoid** Baileys/whatsapp-web.js for anything on a real JIVO number.

## Confidence summary (honesty floor)
- Connectors-on-mobile-all-plans, India pricing, WhatsApp Jan-2026 policy + free service conversations, LibreChat/Open WebUI MCP support, ChatGPT web-only limits: **verified today, sourced above — high confidence (~95%)**.
- Per-question API cost figures: **estimated**, not measured on our workload — measure in the Telegram pilot before any budget claim.
- WhatsApp compliance of a scoped internal bot: **my policy reading (~70%)** — worth a check against Meta's actual Business Messaging Policy text before investing the week.
