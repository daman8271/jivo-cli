#!/usr/bin/env bash
# =============================================================================
# reseed.sh — ONE-TIME (re)seed of the Jivo Mart factory tokens.
#
# Run it with the `!` prefix so the password stays in YOUR shell session and
# never lands in Claude's transcript or git:
#
#   ! JIVO_FACTORY_EMAIL=test@jivo.in JIVO_FACTORY_PASSWORD='your-password' \
#       bash /root/jivo-factory-intel/bin/reseed.sh
#
# It logs in once and stores BOTH the access and refresh tokens to
# ~/.config/jivo-factory/ (mode 0600). The PASSWORD IS NEVER STORED — only the
# tokens. After this, the daily cron self-sustains via the rotating refresh
# token; you only need to re-run this if the cron is down for more than ~7 days.
# =============================================================================
set -euo pipefail
: "${JIVO_FACTORY_EMAIL:?set JIVO_FACTORY_EMAIL (e.g. test@jivo.in)}"
: "${JIVO_FACTORY_PASSWORD:?set JIVO_FACTORY_PASSWORD}"
DIR="$HOME/.config/jivo-factory"; mkdir -p "$DIR"; chmod 700 "$DIR"
python3 - "$DIR" <<'PY'
import json, os, sys, urllib.request, urllib.error
DIR = sys.argv[1]
body = json.dumps({"email": os.environ["JIVO_FACTORY_EMAIL"],
                   "password": os.environ["JIVO_FACTORY_PASSWORD"]}).encode()
req = urllib.request.Request("https://factory.jivo.in/api/v1/accounts/login/",
                             data=body, headers={"Content-Type": "application/json"})
try:
    d = json.load(urllib.request.urlopen(req, timeout=30))
except urllib.error.HTTPError as e:
    print(f"login HTTP {e.code} — check email/password", file=sys.stderr); sys.exit(1)
os.umask(0o077)
for k, fn in [("access", "access.jwt"), ("refresh", "refresh.jwt")]:
    if d.get(k):
        p = os.path.join(DIR, fn); open(p, "w").write(d[k]); os.chmod(p, 0o600)
if not (d.get("access") and d.get("refresh")):
    print("login returned no tokens", file=sys.stderr); sys.exit(1)
print("re-seeded access+refresh tokens (0600). The daily cron will now self-sustain.")
PY
