#!/bin/bash
# Daily refresh for the JIVO Accounts Board.
#
# Rebuilds site/data.json live from SAP HANA (read-only), redeploys to Vercel,
# re-opens public access, and verifies the page answers logged-out.
#
# Safe unattended: build_data.py refuses to write obviously-broken data (exit 2),
# and any failure leaves the previous data.json and the previous deployment live.
#
# Log: pipeline/refresh.log      Cron suggestion: 15 9 * * *  (09:15 IST, after
# the overnight SAP postings have settled — same slot as the godown board.)
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.hermes/node/bin:/usr/bin:/bin"
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/refresh.log"
PROJECT="jivo-accounts"
URL="https://${PROJECT}.vercel.app"

{
  echo "=== refresh started $(date '+%F %T %Z') ==="

  python3 "$DIR/build_data.py"
  rc=$?
  if [ $rc -eq 2 ]; then
    echo "SANITY GUARD REFUSED — previous data.json and deployment stay live"
    exit 2
  elif [ $rc -ne 0 ]; then
    echo "BUILD FAILED (exit $rc) — previous data.json and deployment stay live"
    exit 1
  fi

  cd "$DIR/../site" || exit 1
  if ! vercel deploy --prod --yes >/dev/null 2>&1; then
    echo "DEPLOY FAILED — previous deployment stays live"
    exit 1
  fi

  # New Vercel projects default to SSO-GATED. Strip it every time — Daman's
  # standing rule is that a shared link must open with no login.
  python3 "$HOME/.claude/scripts/vercel-public.py" "$PROJECT" >/dev/null 2>&1

  code=$(curl -s -o /dev/null -w '%{http_code}' "$URL")
  echo "deployed; logged-out check: HTTP $code"
  [ "$code" = "200" ] || echo "WARNING: $URL is not answering 200 logged-out"

  echo "=== refresh done $(date '+%F %T %Z') ==="
} >> "$LOG" 2>&1
