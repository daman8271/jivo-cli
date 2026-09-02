#!/bin/bash
# cutover-v2.sh — point jivo-accounts.vercel.app at v2, or roll straight back.
#
# Until this runs, v1 and v2 are two independent Vercel projects and the URL
# Accounts has bookmarked keeps serving v1. Cutover is deliberately a separate,
# reversible act: it changes which directory the 2-minute loop deploys, and
# nothing else.
#
#   ./cutover-v2.sh --check      what would change (default)
#   ./cutover-v2.sh --go         cut jivo-accounts.vercel.app over to site-v2
#   ./cutover-v2.sh --rollback   put v1 back
#
# Rollback is one command and takes one deploy, because site/ is never touched.
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$DIR")"
URL="https://jivo-accounts.vercel.app"
MODE="${1:---check}"

live_stamp() {
  for p in /data/manifest.json /data.json; do
    curl -s --max-time 20 "${URL}${p}?t=$(date +%s)" 2>/dev/null \
      | python3 -c 'import sys,json;print(json.load(sys.stdin).get("generated_at",""))' 2>/dev/null && return 0
  done
  echo ""
}

current_target() { grep -oE 'SITE="\$DIR/\.\./[a-z0-9-]+"' "$DIR/live-refresh.sh" | sed 's|.*/\.\./||;s|"||'; }

case "$MODE" in
--check)
  echo "jivo-accounts project : $(python3 -c 'import json;print(json.load(open("'"$ROOT"'/site/.vercel/project.json"))["projectName"])' 2>/dev/null)"
  echo "live-refresh deploys  : $(current_target)"
  echo "live generated_at     : $(live_stamp)"
  echo "v2 built?             : $([ -f "$ROOT/site-v2/data/manifest.json" ] && echo yes || echo NO — run build-v2.sh first)"
  echo
  echo "--go       repoints jivo-accounts.vercel.app at site-v2/ and deploys once"
  echo "--rollback puts site/ back"
  ;;

--go)
  [ -f "$ROOT/site-v2/data/manifest.json" ] || { echo "refusing: site-v2 has no built data" >&2; exit 1; }
  [ -f "$ROOT/site-v2/index.html" ]         || { echo "refusing: site-v2 has no index.html" >&2; exit 1; }
  # Carry the project link across so site-v2 deploys to the SAME project — the
  # bookmarked URL must not change.
  mkdir -p "$ROOT/site-v2/.vercel"
  cp "$ROOT/site/.vercel/project.json" "$ROOT/site-v2/.vercel/project.json"
  cp "$DIR/live-refresh.sh" "$DIR/.live-refresh.sh.pre-cutover"
  sed -i.bak 's|SITE="$DIR/../site"|SITE="$DIR/../site-v2"|' "$DIR/live-refresh.sh"
  rm -f "$DIR/live-refresh.sh.bak"
  # Force the next tick to publish rather than believing the v1 fingerprint.
  rm -f "$DIR/.last-published.sha256"
  ( cd "$ROOT/site-v2" && vercel deploy --prod --yes ) || { echo "DEPLOY FAILED — rolling back"; "$0" --rollback; exit 1; }
  python3 "$DIR/vercel-public.py" jivo-accounts >/dev/null 2>&1 || true
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 "$URL" || echo 000)
  echo "$URL -> HTTP $CODE"
  [ "$CODE" = "200" ] || { echo "NOT PUBLIC — rolling back" >&2; "$0" --rollback; exit 1; }
  echo "CUT OVER to v2. Roll back any time with: $0 --rollback"
  ;;

--rollback)
  if [ -f "$DIR/.live-refresh.sh.pre-cutover" ]; then
    cp "$DIR/.live-refresh.sh.pre-cutover" "$DIR/live-refresh.sh"
  else
    sed -i.bak 's|SITE="$DIR/../site-v2"|SITE="$DIR/../site"|' "$DIR/live-refresh.sh"; rm -f "$DIR/live-refresh.sh.bak"
  fi
  chmod +x "$DIR/live-refresh.sh"
  rm -f "$DIR/.last-published.sha256"
  ( cd "$ROOT/site" && vercel deploy --prod --yes ) || { echo "ROLLBACK DEPLOY FAILED" >&2; exit 1; }
  python3 "$DIR/vercel-public.py" jivo-accounts >/dev/null 2>&1 || true
  echo "$URL -> HTTP $(curl -s -o /dev/null -w '%{http_code}' --max-time 25 "$URL")"
  echo "ROLLED BACK to v1."
  ;;
*) echo "usage: $0 [--check|--go|--rollback]" >&2; exit 64 ;;
esac
