#!/bin/bash
# Daily refresh for the JIVO godown board (https://jivo-godown.vercel.app).
# Rebuilds site/data.json live from SAP HANA, redeploys to Vercel, re-opens
# public access, and verifies the page answers logged-out. Safe unattended:
# build_data.py refuses to write obviously-broken data, and any failure keeps
# the previous deployment live. Log: pipeline/refresh.log
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.hermes/node/bin:/usr/bin:/bin"
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/refresh.log"
{
  echo "=== refresh started $(date '+%F %T %Z') ==="
  if ! python3 "$DIR/build_data.py"; then
    echo "BUILD FAILED — previous data.json and deployment stay live"
    exit 1
  fi
  cd "$DIR/../site" || exit 1
  if ! vercel deploy --prod --yes >/dev/null 2>&1; then
    echo "DEPLOY FAILED — previous deployment stays live"
    exit 1
  fi
  python3 "$HOME/.claude/scripts/vercel-public.py" jivo-godown >/dev/null 2>&1
  code=$(curl -s -o /dev/null -w '%{http_code}' https://jivo-godown.vercel.app)
  echo "deployed; logged-out check: HTTP $code"
  echo "=== refresh done $(date '+%F %T %Z') ==="
} >> "$LOG" 2>&1
