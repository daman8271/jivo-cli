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

## Where it runs

On the **VPS** (always-on, inside the office loop). `live/loop.sh` is the
3-minute entry point. `state.json` is published over HTTPS for the Mark 3 site
to fetch client-side — the site is NOT redeployed every 3 minutes (Vercel caps
at 100 deploys/day).
