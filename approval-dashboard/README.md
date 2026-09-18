---
title: "Approval Board — rejected entries, live"
created: 2026-09-18
project: jivo-cli
type: readme
tags: [sap, approvals, bhawani, dashboard, accounts, read-only]
---

# Approval Board

**https://jivo-approvals.vercel.app** — three tabs, Oil / Mart / Beverages.

Every A/P draft the Accounts entry team sends goes to **BHAWANI (USER03)**. When
she rejects one, SAP's Approval Status Report shows it — and then keeps showing it
forever, because **SAP never clears a rejection line and keeps no approval history
at all** (`OWDD_LOG` and `WDD1_LOG` are empty; only current state is stored).
So nobody can tell what is still outstanding, or how long it has been sitting.

This board answers both. It reads SAP every minute, shows what is still rejected
with a live clock on each row and **Bhawani's own reason**, and shouts once when
something crosses **2 days**.

Read-only throughout. The only SAP call is `hana-sql`, which refuses anything
that is not a SELECT.

## What it covers

- A/P invoices, A/P credit memos and GRPOs (`ObjType` 18, 19, 20)
- Keyed by **USER07 Harsh · USER08 Divjot · USER09 Satnam · USER19 Mahak/Priya ·
  USER39 Muqeem** — the same desk list as `.claude/skills/ap-rm-pm/bin/daily_sort.py`
- All three books. Scope lives in `pipeline/build.py` (`OBJTYPES`, `LOGINS`).

## How a row leaves

A rejected draft is never fixed and posted — measured over 90 days, not one was.
The operator cancels it and keys a fresh one, which flips `ODRF."WddStatus"` from
`'N'` to `'C'`. The board sees that within a minute and drops the row by itself.
Nothing to tick off. The moment it left is written to `state/history.jsonl`,
which is the only record anywhere of how long a rejection sat.

## The 2-day clock

Counts from when Bhawani rejected it (`WDD1."UpdateDate"` + `"UpdateTime"`), and
ticks live in the browser off each row's own timestamp.

**Only entries rejected after the board went live can raise the alarm.** On the day
it was built, 56 of the 65 open rejections were already past 2 days and 27 were
over 90 days old — alarming on those would have made the alarm meaningless from
the first morning. They are still shown, coloured by age, just silent. The cutoff
is `launched_at` in `state/board.json`; delete it to re-arm everything.

## Shape

The page is on Vercel and holds **no numbers**. The data comes from the VPS every
30 seconds. That split is not decoration: the board refreshes every minute and
Vercel allows 100 deploys a day, so baking the data in would break by mid-morning.

```
SAP HANA ──0.6s SELECT──▶ pipeline/build.py ──▶ state/board.json
  (via 127.0.0.1:43015)      every minute            │
                                                     ▼
                              publish/board_server.py :8798
                                   Traefik / HTTPS
                                          │
                          browser polls it every 30 seconds
```

- Data: `https://approvals-c84942f4.srv1685505.hstgr.cloud/board.json` (also `/healthz`, `/history.jsonl`)
- Service: `approval-board` (systemd, VPS)
- Cron: `* * * * * /root/jivo-cli/approval-dashboard/pipeline/refresh.sh`

**HANA host and port must stay forced in `refresh.sh`.** The env file's own
`HANA_PORT` still names 47301, which is the dead old SAP box. The live reverse
tunnel is `127.0.0.1:43015`.

## Alerts

On the page: a red banner, the count in the tab title, rows coloured by age.

WhatsApp is **built and dormant**. Neither route can send as of 2026-09-18:
Wati's trial has ended (`{"ok":false,"error":true,"fullTrialEnd":true}` on every
endpoint), and `jwa` has been `LOGGED_OUT since 2026-09-03 07:30`. Until one
works, `pipeline/whatsapp.py` writes every message it would have sent to
`state/alerts.log`. Running `jwa login` (a phone scans a QR, once) starts it with
no code change. Name a recipient in `state/recipients.json`:

```json
{"group": "<number or jid>", "people": {"USER07": "<number>"}}
```

Per-person routing is a later phase. The latch (`state/alerted.json`) means each
document is reported **once** when it goes late and once when it clears — without
it, this runs 1,440 times a day and everyone mutes it.

## Running it by hand

```bash
ssh vps 'cd /root/jivo-cli/approval-dashboard && python3 pipeline/build.py --once'
ssh vps 'cd /root/jivo-cli/approval-dashboard && python3 pipeline/alerts.py --dry-run'
curl -s https://approvals-c84942f4.srv1685505.hstgr.cloud/healthz
```

Deploy the page (Vercel is logged out on the Mac; the VPS is logged in):

```bash
rsync -az --exclude '.vercel' --exclude '__pycache__' --exclude 'state/' \
  ~/jivo-cli/approval-dashboard/ vps:/root/jivo-cli/approval-dashboard/
ssh vps 'cd /root/jivo-cli/approval-dashboard/site && npx -y vercel deploy --prod --yes'
```

## Traps paid for already

- `WDD1."AuthUpdDat"` is **NULL on 100% of rows**. The decision time is
  `"UpdateDate"` + `"UpdateTime"` (SMALLINT HHMM).
- One draft can carry **more than one** approval request (the double-request bug
  closed in 5584f319). The `OWDD` join multiplies rows — `GROUP BY` the draft.
- `WddStatus='C'` is **cancelled**, not rejected, and is about five times bigger.
  Only `'N'` is a rejection.
- `hana-sql` writes a SQL NULL into CSV as the literal text `NULL`, so an empty
  remark arrives as four characters. `clean()` in `build.py` strips it.
