# MARK V persistent service operations

This is a new service rooted at `/root/mark5`; it does not modify any MARK III/IV
collector, cron, feed or deployment. Root owns installation and the public route.

## Layout and start

- `/root/mark5/app`: deployed `site-mark5` source, including `service/` and
  `scripts/run-engine.ts`; Node 22.6+ supports `--experimental-strip-types`.
- `/root/mark5/data/mark5.sqlite`: persistent plans, revisions, source snapshots,
  activity, idempotency records, jobs and published dashboard (SQLite WAL/FULL).
- `/root/mark5/private/service.env`: mode 0600, provisioned privately. Never commit.
- Install `mark5.service` in systemd only after the root operator's deployment step.
  It binds loopback port 8795. Publish only the new host
  `https://mark5.srv1685505.hstgr.cloud` to this listener.
- Service start: `python3 service/server.py --host 127.0.0.1 --port 8795 --db
  /root/mark5/data/mark5.sqlite`. Root's systemd unit supplies secrets.

## Environment contract

Service:

| Variable | Meaning |
|---|---|
| `MARK5_SERVICE_SECRET` | Random bearer secret, at least 32 characters; server/proxy only |
| `MARK5_WEBHOOK_SECRET` | Different random secret, at least 32 characters |
| `MARK5_DB` | SQLite path; unit supplies explicit path |
| `MARK5_POLL_SECONDS` | Source poll cadence, default 180 |
| `MARK5_AUTO_AI` | `1` enables meaningful-change review; `0` disables automatic AI |
| `MARK5_AI_MIN_SECONDS` | Manual review enqueue cooldown, default 300 |
| `MARK5_AUTO_AI_MIN_SECONDS` | Automatic review cooldown, default 1800 |
| `MARK5_AUTO_AI_DAILY_LIMIT` | Automatic daily enqueue cap, default 12 (UTC counter) |
| `MARK5_AI_MODEL` | `gpt-6-astra` default; no automatic lower-model fallback |
| `CODEX_HOME` | `/root/mark5/private/codex`, dedicated private auth directory |
| `MARK5_CODEX` | `/usr/bin/codex` default; must have working service-user auth |
| `MARK5_NODE` | `node` default, or absolute supported Node binary |

Next/Vercel, all server-only (never `NEXT_PUBLIC_`):

| Variable | Meaning |
|---|---|
| `MARK5_SERVICE_URL` | `https://mark5.srv1685505.hstgr.cloud`, fixed upstream origin |
| `MARK5_SERVICE_SECRET` | Same private bearer secret as the service |
| `MARK5_SESSION_SECRET` | Separate random signing secret, at least 32 characters |
| `MARK5_OPERATOR_PASSCODE` | Privately generate at least 32 random characters; never a memorable shared phrase |
| `MARK5_PUBLIC_ORIGIN` | `https://jivo-mark5.vercel.app`, exact write Origin |

Session cookies are HttpOnly, SameSite=Strict, Secure in production, eight hours.
Login throttling is per warm serverless instance, not a distributed guarantee;
random high-entropy credentials are required. Rotate the session signing secret to
invalidate all existing sessions. Public visitors can read the dashboard; only
an authenticated same-origin operator can initiate revisions, approvals or AI.

## HTTP contract

| Method and path | Result |
|---|---|
| GET `/healthz` | Listener health; does not claim all sources are fresh |
| GET `/v1/dashboard` | Latest persisted PlanningSnapshot; ETag supports 304 |
| GET `/v1/plans/YYYY-MM-DD` | Computed proposal plus saved revisions |
| GET `/v1/jobs/<id>` | Persisted JobSummary |
| POST `/v1/refresh` | Bearer auth; `{}`; 202 `{job}`; active refresh coalesces |
| POST `/v1/plans/<date>/revise` | Bearer auth; PlanCommand; 202 `{job}` |
| POST `/v1/plans/<date>/approve` | Bearer auth; `{expectedRevision,idempotencyKey}`; exact approved revision |
| POST `/v1/ai/review` | Bearer auth; optional `{date,idempotencyKey}`; 202 `{job}` |
| POST `/v1/events` | HMAC webhook auth; `{id,type,source?,detail?}`; 202 `{job}` |

Next mirrors these under `/api`, and `/api/session` GET returns authentication
state, POST `{passcode}` creates the cookie, DELETE clears it. Errors use
`{error:string}`. Dates, job IDs, fields, change types and payload lengths are
validated. Browser write routes require exact Origin. No arbitrary CORS is added.

Webhook type is one of `production_changed`, `material_changed`, `orders_changed`,
`source_changed`. Sign exact UTF-8 body bytes:

```
X-Mark5-Timestamp: <Unix seconds>
X-Mark5-Signature: hex(HMAC-SHA256(secret, timestamp + "." + rawBody))
```

Timestamp tolerance is five minutes. Event IDs and request hashes persist, so a
replay cannot create another refresh. Reusing an ID with another body is 409.
Webhook data never supplies a fetch URL, executable command, or public free text.
No source-system write is implemented by these endpoints.

## Worker and persistence rules

Only the worker executes `node --experimental-strip-types scripts/run-engine.ts`;
Next routes only proxy short requests. Input comes from the two fixed MARK IV
public feeds (`inputs.json`, `factory-now.json`). Redirects are rejected. Each
original source body/timestamp survives unchanged; fetch errors retain last-good
content with explicit stale status. A first missing source yields a failed job and
503 dashboard, never synthetic zero stock. Dashboard summaries are bounded; plan
history remains persistent and date-addressable.

The service serializes its job worker. Publication is transactional and checks the
source revision and webhook generation again. Source revision ignores collection
clock metadata only; bodies retain all original timestamps, and business changes
still invalidate a draft. Concurrent commands carrying the same expected revision
cannot both publish: the loser becomes superseded. Each saved revision stores canonical cumulative controls, with later edits replacing
the same machine/shift run, machine enable flag or night choice. Priority SKUs
retain their latest ordering without duplicates. At most 30 distinct controls are
retained; overflow is rejected rather than silently losing earlier edits. Legacy
delta-only chains are reconstructed on read without changing historical approvals;
new canonical records carry a private version marker to avoid unbounded replay.

New plan revisions are drafts;
approved history is not overwritten by refresh, AI or operator edits. Approval
also rejects drafts based on a different current source revision. Interrupted
refresh/replan jobs resume on restart. Interrupted AI is marked failed to avoid
silently billing the same prompt twice; explicitly request another review.

AI runs the actual Codex CLI with `gpt-6-astra`, high reasoning, ephemeral mode (verified with isolated CLI 0.153.4),
read-only sandbox, ignored user config/rules and no shell/browser/apps/plugins/
hooks/multi-agent tools. The worker has an isolated temporary cwd and a filtered
environment. It sends bounded plan context (not raw source credentials). Structured
output is validated against allowlisted changes and passed through the same engine
before saving an AI draft. Any observed command/tool event rejects the result. The exact known initialization
notice that Code Mode is unavailable and fails closed is harmless metadata; no
other unexpected item type is accepted.
Raw provider logs are never published. No simulated recommendation is labelled AI.

Automatic AI fingerprints omit clocks and refreshed timestamps. They include
planned/recorded quantities rounded to 100 L, machine/SKU/status, blocker identities
and source-health states; small numerical changes alone do not trigger reviews.
Cooldown and daily cap persist. The unchanged fingerprint never re-bills because
of another 180-second poll. Provider failure never changes into a fabricated draft.

## Verification and recovery

- Unit/integration suite on VPS: `python3 -m unittest discover -s service/tests -v`;
  proxy/session suite: `node --experimental-strip-types --test service/tests/proxy.test.ts`.
- Perform a real isolated provider review before claiming AI is working; `codex
  login status` alone is insufficient. The 10 September initial probe found an
  expired refresh token (HTTP 401). A dedicated private auth profile then worked,
  but old CLI 0.144.6 was refused for this model. Isolated official npm CLI 0.153.4
  completed genuine acceptance: job `50185945188c4c2bbee8e1b5ce232c86`, AI draft
  revision `9609248b01ad489aa6cb965f716cfd03`, stored in the isolated build
  acceptance database. No lower model was used.
- Read `/healthz`, dashboard and its per-source freshness separately. Inspect
  persisted failed jobs when a dashboard remains last-good.
- Back up SQLite via Python `sqlite3.Connection.backup`, not a live raw-file copy
  that omits WAL. Keep backups mode 0600 outside the public application tree.
- Stop only this systemd unit for maintenance. Restore its database and restart;
  do not touch the existing MARK IV service or feeds.
