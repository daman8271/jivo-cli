#!/bin/bash
# Daily refresh for the AWL party board.
#
# Rebuilds site/index.html live from SAP HANA (read-only) and opens it.
# Any failure leaves the previous page on disk, still readable.
#
#   ./refresh.sh                  # today, JIVO Oil, AWL
#   ./refresh.sh --as-of 2026-08-20
#   ./refresh.sh --card VENDA000123 --company mart
#
# Log: refresh.log
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/refresh.log"
PAGE="$DIR/site/index.html"

PY=python3
command -v "$PY" >/dev/null 2>&1 || PY="py -3"

{
  echo "=== refresh started $(date '+%F %T') ==="
  if ! $PY "$DIR/build.py" "$@"; then
    echo "BUILD FAILED — the previous page stays on disk"
    exit 1
  fi
  echo "=== done $(date '+%F %T') ==="
} 2>&1 | tee -a "$LOG"

# open it (Windows / macOS / Linux)
if command -v start >/dev/null 2>&1; then start "" "$PAGE"
elif command -v cmd.exe >/dev/null 2>&1; then cmd.exe /c start "" "$(cygpath -w "$PAGE" 2>/dev/null || echo "$PAGE")"
elif command -v open >/dev/null 2>&1; then open "$PAGE"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$PAGE"
fi
