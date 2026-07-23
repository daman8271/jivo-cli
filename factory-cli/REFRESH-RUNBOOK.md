---
title: "Jivo Mart Factory — Daily Auto-Refresh Runbook"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: guide
tags: [jivogpt, factory-cli, runbook]
---

# Jivo Mart Factory — Daily Auto-Refresh Runbook

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

The factory data (the `factory/` 4th pillar of `jivo-data-bank`) refreshes **every day**,
deterministic full-REPLACE, just like the ecom pipeline — each day's snapshot replaces the
last and every previous day stays in git history (the time machine).

## The daily chain (cron, IST)

```
05:30  factory_refresh.sh   rotating-auth → full capture → render FRESH source vault
        │                     (/root/jivo-factory-intel/vault, deterministic full REPLACE)
        ▼
12:00  ecom deadline sweep  lands the noon competitor-price source, then triggers competitor/data-bank
        │                    chain when the upstream sources are ready
        ▼
~12:20 run_daily.sh         event-driven data-bank fusion, not a fixed cron
        ├ daily_rebuild.sh   migrate jivo+ecom + factory_pillar(fresh factory) → FAIL-CLOSED verify → commit
        ├ push_both.sh       auto-push the verified commit to github.com/daman8271/jivo-data-bank
        └ notify.sh          Telegram heartbeat / loud failure alert
```

Cron lines (`crontab -l`):
```
30 5 * * * /root/jivo-factory-intel/bin/factory_refresh.sh >> /root/jivo-factory-intel/daily.log 2>&1
# data-bank daily fusion is event-driven via ecom-intel deadline_sweep.sh -> competitor -> run_daily.sh
# jivo-data-bank keeps only the weekly semantic cron unless JDB_DAILY_CRON is explicitly set.
```

## Auth — self-sustaining, no password stored

`factory_refresh.sh` first runs `refresh_token.py`: it POSTs the stored refresh token to
`/accounts/token/refresh/`, which **rotates** it — so it saves a fresh access token AND a
fresh 7-day refresh token every day. Running daily keeps auth alive **forever** with the
password never stored (cardinal rule). Resilient: if a refresh fails but the access token is
still valid (~25h grace), it WARNs and still captures today.

### One-time re-seed (only when needed)
If the cron is down **>7 days** (refresh token expires) — or to seed it the first time — the
owner runs this **once**, with the `!` prefix so the password stays in your session (never in
Claude's transcript or git):

```
! JIVO_FACTORY_EMAIL=test@jivo.in JIVO_FACTORY_PASSWORD='your-password' bash /root/jivo-factory-intel/bin/reseed.sh
```

It stores access+refresh to `~/.config/jivo-factory/` (0600). The password is never written.

## Scripts (`/root/jivo-factory-intel/bin/`)
- `refresh_token.py` — rotate+store the JWT (self-sustaining auth).
- `reseed.sh` — one-time login→tokens (owner runs with `!`, creds via env).
- `capture.py` + `capture_gaps.py` — full lossless capture (152 paginated endpoints + the
  gap endpoints person_gatein/company + cap-busted documents/oitm).
- `render.py` — deterministic full-REPLACE render of `vault/` (one note per record, FK links, SAP bridge).
- `factory_refresh.sh` — the 05:30 entrypoint (auth → capture → render).
- `factory_daily.sh` — self-contained alternative that also runs the rebuild (not used by cron;
  the data-bank event hook does the fuse+commit+push after the noon upstream chain).

## Verify / troubleshoot
- Last run: `tail /root/jivo-factory-intel/refresh.log` and `/var/log/jivo-data-bank/cron.log`.
- Manual run: `bash /root/jivo-factory-intel/bin/factory_refresh.sh` then `bash /root/jivo-data-bank/bin/run_daily.sh`.
- Fail-closed: a bad rebuild aborts WITHOUT committing (no corrupt data ships); the previous
  day's commit stays live. Telegram alerts on failure.
- "auth dead" alert → run the re-seed above.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
