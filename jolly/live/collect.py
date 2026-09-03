#!/usr/bin/env python3
"""collect.py — the Mark 3 ingest cycle. One run = one pull of the live plant.

    python3 live/collect.py            # from jolly/
    python3 -m live.collect            # same thing
    live/loop.sh                       # what cron actually calls, every 3 min

WHAT IT DOES

  1. Discovers every adapter under ``live/adapters/`` (``*.py``, no leading
     underscore). Nothing is hard-coded — drop a new module in and it joins the
     cycle on the next run.
  2. Decides this cycle's depth from ``live/state/.cadence.json``:
         cheap   every run
         heavy   every 30 min   -> fetch(heavy=True)   where fetch takes it
         hourly  every 60 min   -> fetch(hourly=True)  where fetch takes it
     The flag is passed ONLY to adapters whose ``fetch`` signature accepts it
     (inspected, not assumed). ecom / exim / oms run their own internal slow
     caches and take no argument at all — they are called bare.
  3. Runs them CONCURRENTLY, at most 3 at a time. These servers are fragile;
     3 is deliberately gentle, not a throughput target.
  4. Each adapter runs in its own try/except. A crash, a hang or a garbage
     return value affects that source and nothing else.
  5. Writes, atomically (tmp + os.replace, because publish/state_server.py is
     serving these files while we write):
         live/state/<source>.json            the full envelope, every cycle
         live/state/<source>.last-good.json  the last envelope with ok:true
         live/state/state.json               the merged view for the site
  6. Exits non-zero ONLY if every adapter failed — a partial cycle is a normal,
     successful cycle.

THE RULES THIS FILE OBEYS (each one already bit this project)

  * A FAILED ADAPTER IS NEVER PAPERED OVER. state.json never substitutes
    last-good data for a failed source. `sources[key].ok` is false, the error
    is verbatim, and `last_good_at` tells a consumer that a stale file exists
    and how old it is — so a site can choose to fall back, out loud. Silently
    serving stale numbers is the exact failure this whole loop exists to
    eliminate.
  * PARTIAL DATA IS KEPT, AND LABELLED. Every adapter is written to return
    whatever did come back alongside ok:false. That partial `data` is published
    under its key with ok:false next to it; it is not thrown away and it is not
    dressed up as complete.
  * THE CADENCE CLOCK ADVANCES ON ATTEMPT, NOT ON SUCCESS. A heavy pull that
    fails does NOT re-fire on the next 3-minute cycle. A failing endpoint would
    otherwise get hit 10x more often precisely when it is already in trouble —
    the retry storm Daman's standing rule forbids. `heavy_last_ok_at` records
    the last one that actually returned, so "gated off" is distinguishable from
    "failing".
  * NO KEY IS SILENTLY CLOBBERED. `collected_at`, `cycle_seconds`, `sources`
    and `warnings` are reserved; an adapter claiming one is refused and the
    refusal is published in `warnings` rather than swallowed.

STATE.JSON SHAPE

    {
      "collected_at": "2026-09-03T14:31:02+05:30",   # top of the cycle
      "completed_at": "2026-09-03T14:31:09+05:30",   # bottom of it
      "cycle_seconds": 61.4,
      "cadence": {"heavy": true, "hourly": true, "run": 1},
      "sources": {
        "<key>": {"ok": bool, "fetched_at": str|null, "server_at": str|null,
                  "error": str|null, "seconds": float, "cadence": "cheap|heavy|hourly|heavy+hourly",
                  "has_data": bool, "last_good_at": str|null, "last_good_age_s": int|null}
      },
      "warnings": [...],
      "<key>": { ...that adapter's data verbatim... }
    }

ENV OVERRIDES (all optional)

    MARK3_HEAVY_EVERY_S=1800     MARK3_HOURLY_EVERY_S=3600
    MARK3_FORCE_HEAVY=1          MARK3_FORCE_HOURLY=1
    MARK3_MAX_WORKERS=3          MARK3_ADAPTER_TIMEOUT_S=170
    MARK3_ONLY=ecom,oms          MARK3_SKIP=factory_dispatch
    MARK3_STATE_DIR=/path        MARK3_QUIET=1

MARK3_ONLY / MARK3_SKIP make the run DIAGNOSTIC: per-source files are written,
state.json and .cadence.json are NOT. A one-source run must never become the
published view (it would delete every other source from the site) and must
never burn the global 30-minute heavy slot.

KNOWN LIMIT, STATED RATHER THAN HIDDEN: a wedged adapter thread cannot be
killed from Python. The deadline below stops collect.py WAITING on it, writes
state.json without it, and exits via os._exit so the cycle still ends inside
its 3-minute slot. The adapters all carry their own subprocess timeouts (20-75
s), so any orphaned CLI child dies on its own well before the next cycle.
"""

from __future__ import annotations

import concurrent.futures
import importlib
import importlib.util
import inspect
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

_HERE = os.path.dirname(os.path.abspath(__file__))          # …/jolly/live
_JOLLY = os.path.dirname(_HERE)                             # …/jolly
ADAPTER_DIR = os.path.join(_HERE, "adapters")
STATE_DIR = os.environ.get("MARK3_STATE_DIR") or os.path.join(_HERE, "state")
CADENCE_FILE = os.path.join(STATE_DIR, ".cadence.json")
STATE_FILE = os.path.join(STATE_DIR, "state.json")

# jolly/ on the path so `live.adapters.x` imports under its documented name
# (the README promises `python3 -m live.adapters.<source>` works).
if _JOLLY not in sys.path:
    sys.path.insert(0, _JOLLY)


def _envint(name: str, default: int) -> int:
    try:
        v = int(os.environ.get(name, "") or default)
    except ValueError:
        return default
    return v if v > 0 else default


HEAVY_EVERY_S = _envint("MARK3_HEAVY_EVERY_S", 30 * 60)
HOURLY_EVERY_S = _envint("MARK3_HOURLY_EVERY_S", 60 * 60)
MAX_WORKERS = _envint("MARK3_MAX_WORKERS", 3)
# Safety net only. Every adapter already bounds its own CLI calls; this stops
# collect.py from wedging the 3-minute loop if one of them ever does not.
ADAPTER_TIMEOUT_S = _envint("MARK3_ADAPTER_TIMEOUT_S", 170)
QUIET = os.environ.get("MARK3_QUIET") == "1"

RESERVED = {"collected_at", "completed_at", "cycle_seconds", "sources",
            "warnings", "cadence"}


# --------------------------------------------------------------------------- io
def _now() -> datetime:
    return datetime.now(IST)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _write_atomic(path: str, obj) -> None:
    """tmp + os.replace. state_server.py serves this directory live; a reader
    must never catch a half-written file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2, default=str)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _log(msg: str) -> None:
    if not QUIET:
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()


# ----------------------------------------------------------------- discovery
def discover() -> tuple:
    """Every live/adapters/*.py that exposes a callable fetch().

    Returns (adapters, problems, filtered). `filtered` is true when the operator
    narrowed the set with MARK3_ONLY / MARK3_SKIP — which makes this a
    diagnostic run, not a publishable cycle.
    """
    found, problems = [], []
    only = {s.strip() for s in (os.environ.get("MARK3_ONLY") or "").split(",") if s.strip()}
    skip = {s.strip() for s in (os.environ.get("MARK3_SKIP") or "").split(",") if s.strip()}
    filtered = bool(only or skip)

    try:
        names = sorted(
            f[:-3] for f in os.listdir(ADAPTER_DIR)
            if f.endswith(".py") and not f.startswith("_")
        )
    except OSError as exc:
        return [], [f"adapter directory unreadable: {exc}"], filtered

    for name in names:
        if only and name not in only:
            continue
        if name in skip:
            problems.append(f"{name}: skipped by MARK3_SKIP")
            continue
        try:
            mod = importlib.import_module(f"live.adapters.{name}")
        except Exception:                                   # noqa: BLE001
            # Fall back to a direct file load so a broken package layout does
            # not silently drop a working adapter out of the cycle.
            try:
                spec = importlib.util.spec_from_file_location(
                    f"_mark3_adapter_{name}", os.path.join(ADAPTER_DIR, f"{name}.py")
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)                 # type: ignore[union-attr]
            except Exception as exc:                        # noqa: BLE001
                problems.append(f"{name}: import failed — {type(exc).__name__}: {exc}")
                continue

        fn = getattr(mod, "fetch", None)
        if not callable(fn):
            problems.append(f"{name}: no callable fetch() — not an adapter")
            continue

        key = getattr(mod, "SOURCE", None)
        if not isinstance(key, str) or not key:
            key = name
        if key != name:
            problems.append(f"{name}: module SOURCE is {key!r} — keying state on {key!r}")

        try:
            params = set(inspect.signature(fn).parameters)
        except (TypeError, ValueError):
            params = set()

        found.append({"module": name, "key": key, "fetch": fn, "params": params})

    return found, problems, filtered


# ------------------------------------------------------------------ cadence
def cadence(now: datetime) -> tuple:
    """Decide this cycle's depth. Returns (flags, cadence_state).

    The clock advances on ATTEMPT. A heavy pull that errors is NOT retried on
    the next 3-minute cycle — it waits for its next 30-minute slot. Hammering
    an endpoint that just failed is the retry storm we are forbidden to cause.
    """
    st = _read_json(CADENCE_FILE)
    if not isinstance(st, dict):
        st = {}

    def due(kind: str, every: int) -> bool:
        if os.environ.get(f"MARK3_FORCE_{kind.upper()}") == "1":
            return True
        last = st.get(f"{kind}_last_at")
        if not isinstance(last, str):
            return True                                     # first ever run
        try:
            prev = datetime.fromisoformat(last)
        except ValueError:
            return True
        if prev.tzinfo is None:
            prev = prev.replace(tzinfo=IST)
        return (now - prev).total_seconds() >= every

    flags = {"heavy": due("heavy", HEAVY_EVERY_S), "hourly": due("hourly", HOURLY_EVERY_S)}
    st["run"] = int(st.get("run") or 0) + 1
    st["heavy_every_s"], st["hourly_every_s"] = HEAVY_EVERY_S, HOURLY_EVERY_S
    for kind in ("heavy", "hourly"):
        if flags[kind]:
            st[f"{kind}_last_at"] = _iso(now)
        st.setdefault(f"{kind}_last_at", None)
        st.setdefault(f"{kind}_last_ok_at", None)
    st["updated_at"] = _iso(now)
    return flags, st


# -------------------------------------------------------------------- runner
def run_one(ad: dict, flags: dict) -> dict:
    """Call one adapter. Returns a result row; NEVER raises."""
    kwargs, depth = {}, []
    for kind in ("heavy", "hourly"):
        if kind in ad["params"] and flags.get(kind):
            kwargs[kind] = True
            depth.append(kind)

    t0 = time.monotonic()
    row = {
        "key": ad["key"], "module": ad["module"],
        "cadence": "+".join(depth) if depth else "cheap",
        "payload": None, "error": None, "seconds": None,
    }
    try:
        payload = ad["fetch"](**kwargs)
        if not isinstance(payload, dict):
            raise TypeError(f"fetch() returned {type(payload).__name__}, not a dict")
        row["payload"] = payload
    except BaseException as exc:                            # noqa: BLE001
        # BaseException on purpose: a KeyboardInterrupt or SystemExit raised
        # inside one adapter must not take the other five down with it.
        head = f"{type(exc).__name__}: {exc}"
        tb = traceback.format_exc(limit=3).strip().splitlines()
        where = next((ln.strip() for ln in reversed(tb[:-1]) if ln.strip().startswith("File ")), "")
        row["error"] = (f"{head} | {where}" if where else head)[:600]
    row["seconds"] = round(time.monotonic() - t0, 2)
    return row


def _normalise(row: dict, now: datetime) -> dict:
    """Force whatever the adapter returned into the README's envelope shape."""
    p = row["payload"]
    if p is None:
        return {
            "source": row["key"], "fetched_at": _iso(now), "server_at": None,
            "ok": False, "error": row["error"] or "adapter returned nothing",
            "data": None,
        }
    ok = bool(p.get("ok")) and row["error"] is None
    err = p.get("error") or row["error"]
    if row["error"] and p.get("error"):
        err = f"{p['error']}; {row['error']}"
    return {
        "source": p.get("source") or row["key"],
        "fetched_at": p.get("fetched_at") or _iso(now),
        "server_at": p.get("server_at"),
        "ok": ok,
        "error": err,
        "data": p.get("data"),
    }


# ---------------------------------------------------------------------- main
def main() -> int:
    started = time.monotonic()
    now = _now()
    os.makedirs(STATE_DIR, exist_ok=True)

    adapters, warnings, filtered = discover()
    if not adapters:
        warnings.append("no adapters discovered — nothing to collect")

    flags, cad = cadence(now)
    _log(f"cycle {cad['run']} @ {_iso(now)}  heavy={flags['heavy']} hourly={flags['hourly']}  "
         f"adapters={len(adapters)} workers={MAX_WORKERS}")

    # ---- run, at most MAX_WORKERS at a time ------------------------------
    rows: dict = {}
    deadline = started + ADAPTER_TIMEOUT_S
    pool = concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, MAX_WORKERS), thread_name_prefix="mark3"
    )
    futures = {pool.submit(run_one, ad, flags): ad for ad in adapters}
    for fut in list(futures):
        ad = futures[fut]
        left = max(1.0, deadline - time.monotonic())
        try:
            rows[ad["key"]] = fut.result(timeout=left)
        except concurrent.futures.TimeoutError:
            rows[ad["key"]] = {
                "key": ad["key"], "module": ad["module"], "cadence": "cheap",
                "payload": None, "seconds": round(time.monotonic() - started, 2),
                "error": f"cycle deadline: still running after {ADAPTER_TIMEOUT_S}s "
                         f"— published without it, NOT stubbed",
            }
        except BaseException as exc:                        # noqa: BLE001
            rows[ad["key"]] = {
                "key": ad["key"], "module": ad["module"], "cadence": "cheap",
                "payload": None, "seconds": None,
                "error": f"executor: {type(exc).__name__}: {exc}",
            }
    pool.shutdown(wait=False, cancel_futures=True)

    # ---- write per-source files, build the merged view --------------------
    state = {
        "collected_at": _iso(now),
        "completed_at": None,          # filled at the bottom; declared here so
        "cycle_seconds": None,         # the shape is stable for the site
        "cadence": {"heavy": flags["heavy"], "hourly": flags["hourly"], "run": cad["run"]},
        "sources": {},
        "warnings": warnings,
    }
    ok_count = 0
    heavy_ok = hourly_ok = False
    # Ages are measured from NOW, not from the top of the cycle: `now` is
    # stamped before the adapters run, so a file written seconds later reads as
    # a negative age against it. A freshness number that can go negative is
    # exactly the kind of thing a panel renders straight-faced.
    age_now = _now()

    for ad in adapters:
        key = ad["key"]
        row = rows.get(key) or {"key": key, "module": ad["module"], "cadence": "cheap",
                                "payload": None, "error": "never ran", "seconds": None}
        env = _normalise(row, now)
        _write_atomic(os.path.join(STATE_DIR, f"{key}.json"), env)

        lg_path = os.path.join(STATE_DIR, f"{key}.last-good.json")
        if env["ok"]:
            ok_count += 1
            _write_atomic(lg_path, env)
            if "heavy" in row["cadence"]:
                heavy_ok = True
            if "hourly" in row["cadence"]:
                hourly_ok = True

        # A stale file EXISTS — say so, and say how stale. Never serve it in
        # place of the live number; that decision belongs to the consumer.
        lg_at, lg_age = None, None
        lg = _read_json(lg_path)
        if isinstance(lg, dict):
            lg_at = lg.get("fetched_at")
            try:
                d = datetime.fromisoformat(str(lg_at))
                if d.tzinfo is None:
                    d = d.replace(tzinfo=IST)
                lg_age = max(0, int((age_now - d).total_seconds()))
            except (TypeError, ValueError):
                lg_age = None

        state["sources"][key] = {
            "ok": env["ok"],
            "fetched_at": env["fetched_at"],
            "server_at": env["server_at"],
            "error": env["error"],
            "seconds": row["seconds"],
            "cadence": row["cadence"],
            "has_data": env["data"] is not None,
            "last_good_at": lg_at,
            "last_good_age_s": lg_age,
        }

        if key in RESERVED:
            warnings.append(f"{key}: reserved top-level name — data NOT merged into state.json")
        elif key in state:
            warnings.append(f"{key}: duplicate source key — later adapter dropped")
        else:
            # Partial data from a failed adapter is kept and published; the
            # ok:false beside it in `sources` is what makes it honest.
            state[key] = env["data"]

        mark = "ok " if env["ok"] else "FAIL"
        tail = "" if env["ok"] else f"  {(env['error'] or '')[:150]}"
        _log(f"  {mark} {key:<20} {row['cadence']:<13} "
             f"{(row['seconds'] if row['seconds'] is not None else -1):>6.2f}s"
             f"  server_at={env['server_at'] or '-'}{tail}")

    state["cycle_seconds"] = round(time.monotonic() - started, 2)
    # collected_at is the top of the cycle — the conservative end of the window,
    # so "as of" never claims to be newer than the oldest number in the file.
    # completed_at closes the window so nothing has to be inferred.
    state["completed_at"] = _iso(_now())

    # A PARTIAL CYCLE MUST NEVER BECOME THE PUBLISHED VIEW. MARK3_ONLY /
    # MARK3_SKIP is how an operator debugs one source by hand; writing its
    # result to state.json would silently delete every other source from the
    # site, and consuming the global heavy slot would gate the real 30-minute
    # pull. Per-source files are still written — that is the diagnostic output.
    if filtered or not adapters:
        why = "filtered by MARK3_ONLY/MARK3_SKIP" if filtered else "no adapters discovered"
        _log(f"  .. diagnostic run ({why}) — state.json and .cadence.json NOT written")
    else:
        _write_atomic(STATE_FILE, state)
        if flags["heavy"] and heavy_ok:
            cad["heavy_last_ok_at"] = _iso(now)
        if flags["hourly"] and hourly_ok:
            cad["hourly_last_ok_at"] = _iso(now)
        _write_atomic(CADENCE_FILE, cad)

    dest = "(diagnostic — state.json untouched)" if (filtered or not adapters) else STATE_FILE
    _log(f"cycle {cad['run']} done in {state['cycle_seconds']}s — "
         f"{ok_count}/{len(adapters)} ok -> {dest}")

    # Non-zero ONLY when every adapter failed. A partial cycle is a normal one.
    # The one addition: a FULL cycle that discovered nothing is a broken install,
    # not a healthy quiet plant, and must not report success forever. A filtered
    # run that matched nothing is just an operator typo — that stays 0.
    if not adapters:
        return 0 if filtered else 1
    return 0 if ok_count > 0 else 1


if __name__ == "__main__":
    code = 1
    try:
        code = main()
    except BaseException:                                   # noqa: BLE001
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
    # os._exit, not sys.exit: ThreadPoolExecutor's atexit hook JOINS its
    # non-daemon threads, so one wedged adapter would hold the whole cycle
    # open past its slot. Every file is already written and fsynced above.
    os._exit(code)
