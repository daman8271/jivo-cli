#!/usr/bin/env python3
"""Record the plan chain's outcome and raise the alarm when it stays down.

    python3 live/chain_status.py <state_dir> <chain_rc> [failed_step]

Writes <state_dir>/chain.json (served by the publisher; /healthz folds it in):
  ok, at, step, consecutive_failures, last_ok_at, last_fail_at, alerted
The ingest loop's own exit code never reflects the chain (state.json is out
either way), which is how the plan sat 14 h at 4 Sep 21:36 with every badge
green. Now: after ALERT_AFTER straight failures one Telegram alarm goes out,
and one more when the chain comes back. Never raises.
"""
import json, os, subprocess, sys
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
ALERT_AFTER = int(os.environ.get("MARK3_CHAIN_ALERT_AFTER", "5"))   # cycles = ~15 min


def main(argv):
    state_dir, rc = argv[1], int(argv[2])
    step = argv[3] if len(argv) > 3 else None
    path = os.path.join(state_dir, "chain.json")
    try:
        prev = json.load(open(path))
    except Exception:                          # noqa: BLE001
        prev = {}
    now = datetime.now(IST).isoformat(timespec="seconds")
    fails = 0 if rc == 0 else int(prev.get("consecutive_failures") or 0) + 1
    cur = {
        "ok": rc == 0, "at": now, "rc": rc, "step": None if rc == 0 else step,
        "consecutive_failures": fails,
        "last_ok_at": now if rc == 0 else prev.get("last_ok_at"),
        "last_fail_at": prev.get("last_fail_at") if rc == 0 else now,
        "alerted": bool(prev.get("alerted")) and rc != 0,
        "note": ("the plan chain (freeze -> sim -> gen_live -> publish); ok:false means "
                 "live/state/plan is the LAST GOOD plan, not this cycle's"),
    }
    text = None
    if rc != 0 and fails >= ALERT_AFTER and not prev.get("alerted"):
        cur["alerted"] = True
        since = prev.get("last_ok_at") or "an unknown time"
        text = (f"Mark 3: the PLAN has not rebuilt for {fails} cycles (~{fails * 3} min), "
                f"stopped at {step or '?'} — last good plan {since}. The plant tiles are "
                f"still live; the plan on jivo-mark3.vercel.app is the last good one. "
                f"See loop.log on the VPS.")
    elif rc == 0 and prev.get("alerted"):
        down = int(prev.get("consecutive_failures") or 0)
        text = (f"Mark 3: the plan chain is back — rebuilt at {now[11:16]} after "
                f"{down} failed cycles (~{down * 3} min).")
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cur, f, indent=1)
    os.replace(tmp, path)
    if text:
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      "alert.py"), text], timeout=60)
    print(f"chain.json: ok={cur['ok']} consecutive_failures={fails}"
          + (" ALERT" if text else ""))


if __name__ == "__main__":
    try:
        main(sys.argv)
    except Exception as e:                     # noqa: BLE001
        print(f"chain_status: failed (non-fatal): {e}")
