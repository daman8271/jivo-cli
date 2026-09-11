#!/bin/bash
# Put the site behind the maintenance page, or take it back off.
#   engine/maintenance.sh on     everyone sees "we are updating this page"
#   engine/maintenance.sh off    everyone sees the plan again
#   engine/maintenance.sh link   print the bypass link for an approved browser
# The daily 07:30 refresh honours whatever this leaves behind — it is a file in the repo,
# not a switch on Vercel, so a redeploy cannot silently drop it.
set -euo pipefail
cd "$(dirname "$0")/.."
F=site-sep/maintenance.json
case "${1:-}" in
  on|off)
    python3 - "$1" "$F" <<'PY'
import json,sys
want = sys.argv[1] == "on"; p = sys.argv[2]
d = json.load(open(p)); d["on"] = want
json.dump(d, open(p, "w"), indent=2); print(f"maintenance = {d['on']}")
PY
    cd site-sep
    npm run build >/dev/null 2>&1 || { echo "build failed — nothing published"; exit 1; }
    npx -y vercel deploy --prod --yes >/dev/null 2>&1 || { echo "deploy failed"; exit 1; }
    sleep 10
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 https://jivo-mark2.vercel.app)
    echo "live: HTTP $code  (maintenance $1)"
    ;;
  link)
    python3 -c "import json;d=json.load(open('$F'));print('https://jivo-mark2.vercel.app/?pass='+d['pass'])"
    ;;
  *) echo "usage: engine/maintenance.sh on|off|link"; exit 1;;
esac
