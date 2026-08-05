# godown-dashboard pipeline

Daily-refresh engine: runs the 12 extraction `.sql` files (oil/mart/bev x stock/velocity/history/expiry) against SAP HANA through the read-only `hana-sql` CLI, computes per-item stock metrics (90-day velocity net of returns, days of cover, month-end reconstructed levels, OUT/DEAD/LOW/HIGH/NORMAL status) and warehouse classes (only `physical` godowns count toward `physical_value`; `total_value` is all warehouses, matching OITW), then writes one minified `../site/data.json`.

Run: `python3 build_data.py` (stdlib only, deterministic, cron-safe; exits nonzero on any SQL failure and refuses to overwrite data.json if a company's value is 0 or its item count drops >60% vs the previous file).

## ⚠️ Production runs on the VPS, not on this Mac

Since **2026-08-02** the live board is refreshed by a cron on the VPS, not by this
checkout:

```
# on `ssh vps`
15 9 * * *  flock -n /root/godown-refresh/.lock /root/godown-refresh/refresh.sh
```

- Production working copy: `/root/godown-refresh/` (its own `pipeline/`, `site/`, `hana-sql`).
- Production log: `/root/godown-refresh/refresh.log` — **this is the log that matters**.
- The Mac LaunchAgent `com.jivo.godown-board-refresh.plist` is **disabled** and the local
  `pipeline/refresh.log` stops at 2026-08-01. It is history, not health. A stale local log
  does **not** mean the board is dead — check the VPS.
- The local `../site/data.json` is likewise a build artefact, not what the site serves.

**Therefore: any change to `build_data.py` or the `.sql` files must be copied to the VPS,
or production silently keeps running the old code.**

```bash
rsync -av pipeline/ vps:/root/godown-refresh/pipeline/
ssh vps 'cd /root/godown-refresh && python3 pipeline/build_data.py'   # verify before the next cron
```

Verify the two copies have not drifted:

```bash
ssh vps 'cd /root/godown-refresh/pipeline && md5sum build_data.py *.sql' | sort
( cd pipeline && md5 -r build_data.py *.sql )                          # macOS
```

## Connection

`connect()` tries the direct office route first (`connections/hana.env`); if that fails it
raises the home tunnel (`ssh -f -N -L 13015:127.0.0.1:30015 jivo-sap-any`) and retries with
`-env connections/hana-tunnel.env`; it aborts with a clear message if neither works.

Known failure mode (seen 2026-08-03): from outside the office **both** documented routes can
die at once — the direct route times out and `jivo-sap-any` is unreachable. The VPS is still
connected, because SAP maintains a reverse tunnel *into* it; the VPS reaches HANA at its own
`127.0.0.1:47301`, not at the office IP. So the working fallback from a laptop is to hop
through the VPS's local port, not through the office address:

```bash
ssh -N -L 13015:127.0.0.1:47301 vps        # then use -env connections/hana-tunnel.env
```

## Time-dependent SQL

The six month-end cutoffs in `*_history.sql` are computed at query time as
`LAST_DAY(ADD_MONTHS(CURRENT_DATE, -6 .. -1))`. They were hardcoded literals until
2026-08-03, which would have silently frozen the "6-month normal" baseline from
2026-09-01 onward with no error. If you edit these files, keep them relative to
`CURRENT_DATE` — a frozen baseline fails silently, which is the worst way to fail.
