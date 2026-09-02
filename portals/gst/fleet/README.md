# Keeping the GST portal logged in — `gstd` + `gst-sync`

**Problem this solves.** A GST session dies of idleness, and reviving one needs a
6-digit captcha typed by a human. Eight registrations × every operator × every
day was the tax. On 2026-09-01 all eight sessions had been dead for seven days
and nobody noticed until someone needed a number.

**Shape of the fix.** One machine (the VPS) holds the sessions and logs in when
they lapse, reading its own captchas. Every other device borrows its cookie jars
and never logs in at all.

```
  VPS  srv1685505 ─── gstd.timer (every 5 min) ── gstd ensure
   │                     ├─ keepalive all 8            (safe, disturbs nobody)
   │                     ├─ login only what is dead    (guarded, see below)
   │                     └─ captcha read by headless Claude on the box
   │
   │   gstd-webhook  127.0.0.1:7711   POST /wake   (token in state/token)
   │
   └── jars: /root/gstd/jars/gst-portal/session-*.json
              ▲
              │ rsync
        gst-sync  ── on each device, fires when it comes online
              └── ~/Library/Application Support/gst-portal/   (macOS)
                  ~/.config/gst-portal/                        (Linux)
```

## Why one shared jar and not a login per device

**The GST portal allows one session per username.** If five devices each logged
in, they would spend the day kicking each other off — and kicking the Accounts
team off with them. Sharing one jar is not a shortcut around the portal; it is
the only arrangement the portal permits.

The same fact is why `gstd` logs in *grudgingly*. A keepalive ping holds our own
session and bothers nobody. A login **ends whoever else is on that account**.

## The four rules, each learned from a live failure

1. **keepalive is safe; login is not.** Ping freely, log in reluctantly.
2. **503 means WAIT, never LOG IN.** The portal takes its authenticated API
   offline overnight — observed 2026-09-02 00:15 IST with `ustatus`, `return.`
   and `payment.` all 503, and the login flow with them. `gst-portal` exits 6
   for "portal down" and 4 for "session expired"; `gstd` branches on that.
3. **A locally-lapsed jar cannot tell you the portal is down.** The subtle one.
   `gst-portal` refuses to send anything on a jar past its 15-minute idle guard,
   so once every jar is stale the keepalive never reaches the portal and reports
   "expired" for all eight — *during an outage*. The first captcha mint of a run
   therefore doubles as the availability probe. Without this the first version
   of `gstd` tried 24 logins into a dead portal in one run.
4. **If our session keeps dying fast, a human is on it — yield.** A session lost
   within 10 min of our own login was taken by a person. Each such kill raises a
   strike and backs off exponentially (15 min → 4 h ceiling). We never fight a
   colleague for an account.

Plus the one that predates all of this: **a credential rejection is never
retried.** `gst-portal` records it in `rejected-<GSTIN>.json` and refuses
thereafter. That is how a statutory filing account avoids a lockout.

## Commands

```bash
# on the VPS
/root/gstd/bin/gstd ensure     # ping, then log in only what needs it
/root/gstd/bin/gstd status     # sessions + guard state (backoffs, strikes, logins today)
journalctl -u gstd.service -n 50
tail -f /root/gstd/log/gstd.log

# the webhook (loopback only)
curl -X POST -H "X-Gstd-Token: $(ssh vps cat /root/gstd/state/token)" \
     http://127.0.0.1:7711/wake        # run this ON the VPS, or over an SSH tunnel

# on a device
portals/gst/fleet/gst-sync     # ask the holder to refresh, then pull the jars
```

## Adding a device

1. It needs key-based SSH to `vps` (the fleet alias) and `rsync`.
2. Copy `fleet/gst-sync` to it.
3. Wire it to run when the box comes online:
   - **macOS** — `~/Library/LaunchAgents/com.jivo.gst-sync.plist` (this repo has
     the Mac Air's copy; `RunAtLoad` + `WatchPaths` on `resolv.conf` +
     a 15-min `StartInterval`).
   - **Windows** — Task Scheduler, trigger "On workstation unlock" + "On an
     event: network connected".
   - **Linux** — a `.timer` with `OnBootSec` plus `OnUnitActiveSec=15min`.

## Why the webhook is on 127.0.0.1

Two reasons, and the second is the real one.

- What it drives is logins on eight live registrations, and the jars it produces
  are a bearer token to a portal that can **file statutory returns**. That does
  not belong on a public port without TLS and a firewall rule.
- **A webhook cannot be pushed to a laptop that just woke up.** It is behind NAT
  with no stable address, and while asleep there is nothing to push to. Whoever
  wakes up has to make the call. So the trigger lives on the device (`gst-sync`)
  and the webhook is what it calls.

To expose it later: set `GSTD_BIND=0.0.0.0` in `gstd-webhook.service`, put it
behind the existing Traefik + TLS, and keep the token. That is a deliberate
decision, not a default.

## Known limits

- **Haryana `06AACCJ4223F1Z0` is not automated and cannot be.** Its stored
  password is wrong — the portal answered `SWEB_9014` on 2026-09-01. `gstd`
  skips it by design and will keep skipping it until a person puts the current
  password in `portals/gst/.env` as `GST_01_PASS`. Automation cannot guess a
  password, and retrying is how the account gets locked.
- **Nothing works during the portal's overnight window.** `gstd` waits it out.
- **If a colleague is actively using an account, `gstd` yields to them.** Their
  work matters more than our cached session.
- The captcha reader is headless Claude on the VPS, which shares the Max
  subscription quota. If the fleet is rate-limited, logins wait; keepalive
  (which needs no captcha) keeps working regardless.
