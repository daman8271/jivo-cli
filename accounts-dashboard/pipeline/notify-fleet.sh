#!/bin/bash
# notify-fleet.sh — raise an operational alert about the Accounts Board.
#
# Deliberately does NOT invent a push channel. It writes where someone actually
# looks: the alert log (read by health.html and by anyone tailing the box), and
# syslog. The alert that reaches a human without any infrastructure at all is the
# board's own freshness banner, which every page computes client-side from
# generated_at — this file is the second layer, for diagnosis.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
MSG="${1:-unspecified alert}"
TS="$(date '+%F %T %Z')"

printf '%s %s\n' "$TS" "$MSG" >> "$DIR/alerts.log"
logger -t jivo-accounts-board "$MSG" 2>/dev/null || true

# Machine-readable, picked up by split_data.py into the manifest so health.html
# can show it. Kept tiny and always valid JSON.
python3 - "$DIR" "$MSG" <<'PY' 2>/dev/null || true
import json, sys, datetime, pathlib
d, msg = pathlib.Path(sys.argv[1]), sys.argv[2]
p = d / "alert-state.json"
try:
    st = json.loads(p.read_text())
except Exception:
    st = {"alerts": []}
st["alerts"] = ([{"t": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                  "msg": msg}] + st.get("alerts", []))[:20]
st["latest"] = st["alerts"][0]
p.write_text(json.dumps(st, indent=2))
PY
