#!/bin/bash
# sync-to-vps.sh — push code to the VPS WITHOUT destroying its runtime state.
#
# `rsync -az --delete pipeline/` did exactly that once: it removed
# live-refresh.log (five hours of diagnostic history, including the evidence of
# the freeze that started this work), .last-published.sha256, .consecutive-failures
# and .last-success — none of which exist in the repo, all of which the running
# loop depends on. Code is ours to overwrite; the box's own state is not.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$DIR")"
HOST="${1:-vps}"
DEST="/root/jivo-cli/accounts-dashboard"

EXCLUDES=(
  --exclude '*.log'                 # live-refresh.log, refresh.log, watchdog logs
  --exclude '.last-published.sha256'
  --exclude '.consecutive-failures'
  --exclude '.last-success'
  --exclude '.live-refresh.lock'
  --exclude '.v2-owed'              # v2 deploy-slot debt marker, runtime state
  --exclude '.last-publish-epoch'   # quota-pacing timestamp, runtime state
  --exclude '.live-refresh.sh.pre-cutover'
  --exclude 'alert-state.json'
  --exclude 'alerts.log'
  --exclude '__pycache__'
  --exclude 'raw/'                  # per-query debug TSVs, rebuilt on the box
)

echo "==> pipeline"
rsync -az --delete "${EXCLUDES[@]}" "$ROOT/pipeline/" "$HOST:$DEST/pipeline/"
echo "==> specs"
rsync -az --delete "$ROOT/specs/" "$HOST:$DEST/specs/"
echo "==> site (code only; data.json is built on the box)"
rsync -az --delete --exclude 'data.json' --exclude '.data.sha256' \
      --exclude 'index.html.pre-provfix' --exclude '.vercel/' \
      "$ROOT/site/" "$HOST:$DEST/site/"
echo "==> site-v2 (code only; data/ is built on the box)"
rsync -az --delete --exclude 'data/' --exclude '.vercel/' "$ROOT/site-v2/" "$HOST:$DEST/site-v2/"
echo "==> done"
ssh "$HOST" "cd $DEST && python3 pipeline/kpis.py"
