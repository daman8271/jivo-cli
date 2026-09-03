# live/ — the Mark 3 ingest loop

Every ~3 minutes, pull the plant's position from the LIVE systems and write it
to `live/state/`. No SAP. No frozen snapshot. RULE 0 in `../CLAUDE.md` applies.

## Contract — every adapter is the same shape

`live/adapters/<source>.py` exposes one function and is runnable standalone:

```python
def fetch() -> dict:
    return {
      "source":     "factory_dispatch",      # fixed id
      "fetched_at": "2026-09-03T13:10:20+05:30",  # when WE asked, ISO, tz-aware
      "server_at":  "...",                   # the server's own stamp if it gives one, else null
      "ok":         True,
      "error":      None,                    # string when ok is False; data may be partial
      "data":       { ... }                  # source-specific, documented in the module docstring
    }
```

`python3 -m live.adapters.<source>` prints that dict as JSON. `live/collect.py`
runs every adapter, writes `live/state/<source>.json`, and merges them into
`live/state/state.json` with a top-level `collected_at`. A failing adapter never
takes the others down — its file carries `ok: false` and the previous good file
is kept alongside as `<source>.last-good.json`.

## Rules every adapter obeys (each one is a trap that already bit us)

- **Call the existing CLIs via subprocess.** They own auth. Never write a new
  HTTP client except EXIM `raw` for the two routes the CLI does not wrap.
- **`--company oil` (or `JIVO_OIL`) on every factory/OMS call.** The CLIs
  default to JIVO_MART and return clean, plausible, wrong-company data.
- **`--data-source live --no-cache` wherever supported.** `auto` silently serves
  a stale local SQLite mirror on any error — the exact failure this loop exists
  to eliminate.
- **`--json --no-input --no-color --yes`, never `--agent`.** `--agent` implies
  `--compact`, which strips qty/ltrs/boxes on OMS.
- **Discard stderr** (the CLIs print warnings before the JSON) and coerce
  numbers — `gate-core sales-dispatch` returns `"3000.000"` as a string.
- **Parse timestamps, never slice.** `grpo pending` returns UTC `Z`, `grpo
  all-entries` returns `+05:30`, for the same instant.
- **De-duplicate vehicles on `vehicle_no`** — the same truck appears once per
  bill or once per company depending on the endpoint.
- **Drop ghosts**: gate-in rows older than 7 days that never closed
  (HR67C6723 has been "inside" since 22 June).
- **Read-only.** Never any EXIM `/sap_sync/*` path, never `/account/logout/`,
  never a POST that is not the CLI's own login.
- **Stamp everything** with the server's own timestamp when it gives one.

## Auth lifetimes the loop must survive

| Source | Access | Refresh | Action |
|---|---|---|---|
| factory (ji.jivo.in) | 25 h | 7 d | `auth login` daily via `live/keepalive.sh` |
| EXIM | 24 h | — | wrapper re-mints from `.env`; nothing to do |
| OMS (Daman@oms.com) | 24 h | 7 d | `auth login` daily, separate config file |
| ecom | 1 h | 30 d rotating | `ecom doctor` self-renews; call it first each cycle |

## The cycle

`live/collect.py` is one cycle. It discovers every `live/adapters/*.py` that
exposes `fetch()` — nothing is hard-coded — runs them **three at a time** (the
servers are fragile; 3 is deliberate, not a throughput target), each in its own
`try/except`, and writes:

```
live/state/<source>.json            the envelope, every cycle
live/state/<source>.last-good.json  the last envelope with ok:true
live/state/state.json               the merged view the site fetches
live/state/.cadence.json            the heavy/hourly clock
live/state/loop.log                 rotated at 5 MB, 3 kept
```

`state.json` is `{collected_at, completed_at, cycle_seconds, cadence,
sources:{key:{ok, fetched_at, server_at, error, seconds, cadence, has_data,
last_good_at, last_good_age_s}}, warnings, <key>: <that adapter's data>}`.
`collected_at` is the top of the cycle and `completed_at` the bottom, so an
"as of" stamp never claims to be newer than the oldest number under it.

**Depth is decided by `.cadence.json`, not by the adapter:** cheap every run,
`fetch(heavy=True)` every 30 min, `fetch(hourly=True)` every 60 min — passed
only to adapters whose signature actually takes it (inspected, not assumed;
`ecom`, `exim` and `oms` run their own internal slow caches and are called
bare). **The clock advances on ATTEMPT, not on success**: a heavy pull that
fails waits for its next 30-minute slot instead of re-firing every 3 minutes at
a server that is already in trouble. `heavy_last_ok_at` separates "gated off"
from "failing".

**A failed source is never papered over.** `state.json` does not substitute
last-good data — `sources[key].ok` is false, the error is verbatim, and
`last_good_age_s` tells the site a stale file exists and how old it is, so any
fallback is the site's decision, made out loud. Partial data from a
half-failed adapter is published as-is beside `ok:false`, never discarded and
never dressed up as complete. `collect.py` exits non-zero **only if every
adapter failed**.

Useful knobs: `MARK3_FORCE_HEAVY=1`, `MARK3_ONLY=ecom,oms`, `MARK3_SKIP=…`,
`MARK3_HEAVY_EVERY_S`, `MARK3_MAX_WORKERS`, `MARK3_ADAPTER_TIMEOUT_S`.

**`MARK3_ONLY` / `MARK3_SKIP` make the run DIAGNOSTIC**: per-source files are
written, `state.json` and `.cadence.json` are **not**. A one-source run must
never become the published view — it would delete every other source from the
site — and must never burn the global 30-minute heavy slot. So it is always
safe to debug one adapter by hand on the VPS while the cron loop is running.

## Where it runs

On the **VPS** (always-on, inside the office loop), from the checkout at
`/root/jivo-courier`. `live/loop.sh` is the 3-minute entry point: it takes an
`flock`, runs `collect.py` once under a 175 s hard timeout, and appends to
`live/state/loop.log`. A cycle that overruns its slot is **skipped, never
doubled up** — two collectors against these servers is the retry storm we are
not allowed to cause. `live/keepalive.sh` re-mints the tokens that would
otherwise kill the loop inside a week (factory refresh dies in 7 days, OMS in
7, ecom rotates hourly on its own).

```cron
# ---- Mark 3 live ingest (crontab -e as root on the VPS) ----
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""

# one cycle every 3 minutes; loop.sh logs and refuses to overlap
*/3 * * * * /root/jivo-courier/jolly/live/loop.sh >/dev/null 2>&1

# daily re-login: factory + OMS (both refresh tokens die in 7 days) and an
# ecom doctor. Non-zero exit = a login was skipped or failed — worth mailing.
17 4 * * * /root/jivo-courier/jolly/live/keepalive.sh >/dev/null 2>&1

# keep the checkout current (adapters and reference docs ship through main)
23 5 * * * cd /root/jivo-courier && git pull --ff-only >/dev/null 2>&1
```

`keepalive.sh` needs the OMS billing credential in `live/.keepalive.env`
(mode 600, already covered by the repo's `*.env` gitignore rule, so it does
**not** travel with a `git pull` — create it once per box):

```
OMS_DAMAN_USERNAME=Daman@oms.com
OMS_DAMAN_PASSWORD=…
```

The repo `.env` carries `OMS_USERNAME=paramjot`, a **different account with a
narrower order visibility**. `keepalive.sh` refuses to log that into the Daman
config rather than silently repointing what `oms.py` can see.

`state.json` is published over HTTPS for the Mark 3 site to fetch client-side —
the site is NOT redeployed every 3 minutes (Vercel caps at 100 deploys/day).
`live/publish/` holds that half: `state_server.py` (read-only JSON on
127.0.0.1:8793), the `mark3-state` systemd unit, and the Traefik router.

```bash
systemctl status mark3-state         # is the publisher up
tail -f  /root/jivo-courier/jolly/live/state/loop.log
python3  /root/jivo-courier/jolly/live/collect.py    # one cycle by hand
MARK3_ONLY=exim python3 .../collect.py    # one source, diagnostic only —
                                          # does NOT touch state.json
```
