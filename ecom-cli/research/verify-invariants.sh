#!/usr/bin/env bash
# Post-print invariant gate for jivo-ecom-pp-cli.
#
# Run this against the PRE-change tree first and require it GREEN before
# trusting a red light from it. A gate that has never passed has not been
# tested, and a false failure here costs an hour chasing a bug in the checker.
#
# usage: RESCRAPE_CLI=./jivo-ecom-pp-cli bash research/verify-invariants.sh
set -uo pipefail
CLI="${RESCRAPE_CLI:-./jivo-ecom-pp-cli}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail=0
pass(){ printf '  PASS  %s\n' "$1"; }
bad(){ printf '  FAIL  %s\n' "$1"; fail=1; }

[ -x "$CLI" ] || { echo "no executable at $CLI (set RESCRAPE_CLI)"; exit 2; }
echo "invariant gate: $CLI"
echo

# ---------------------------------------------------------------- read-only
echo "RULE 0 - the CLI and its MCP surface are read-only"
n=$(grep -cE '^\s+method: (POST|PUT|PATCH|DELETE)' spec.yaml || true)
[ "$n" -eq 0 ] && pass "spec declares no non-GET endpoint" || bad "spec declares $n non-GET endpoints"
n=$(grep -c 'method: GET' spec.yaml || true)
[ "$n" -ge 151 ] && pass "spec declares $n GET endpoints" || bad "spec declares only $n GET endpoints (expected >= 151)"

# both MCP execution paths must refuse a write BY CONSTRUCTION, not because the
# current spec happens to be GET-only
for f in internal/mcp/tools.go internal/mcp/code_orch.go; do
  if grep -q 'READ-ONLY LAW' "$f" && grep -q 'is not permitted (GET only' "$f"; then
    pass "$f carries the fail-closed GET-only guard"
  else
    bad "$f lost its GET-only guard - a regeneration restores the write machinery"
  fi
  if grep -qE '\bc\.(Post|Put|Patch|Delete)[A-Za-z]*\(' "$f"; then
    bad "$f calls a mutating client method"
  else
    pass "$f makes no mutating client call"
  fi
done

# ---------------------------------------------------------------- patches
echo
echo "patches (behaviour, not symbols)"
if bash research/scripts/verify-patches.sh "$CLI" >/dev/null 2>&1; then
  pass "all 3 hand-authored patches hold"
else
  bad "patch verification failed - run research/scripts/verify-patches.sh for detail"
fi

# ---------------------------------------------------------- no silent renames
echo
echo "no shipped command was renamed"
missing=0
while IFS=$'\t' read -r res cmd _; do
  [ -z "$res" ] && continue
  # month-on-month-sale and sales-invoice-lines are the two DELIBERATE removals,
  # both justified in MIGRATION-2026-08.md
  case "$res $cmd" in
    "platform month-on-month-sale"|"sap sales-invoice-lines") continue ;;
  esac
  if ! "$CLI" "$res" --help 2>/dev/null | grep -qE "^  $cmd( |\$)"; then
    echo "      missing: $res $cmd"
    missing=$((missing+1))
  fi
done < research/evidence/shipped-commands.tsv
[ "$missing" -eq 0 ] && pass "every shipped command still resolves" \
                     || bad "$missing shipped commands vanished"

# ------------------------------------------------------- structural spec check
echo
echo "spec structure"
if python3 - <<'PY'
import re, sys
src = open("spec.yaml").read()
bad = []
cur = None
for line in src.split("\n"):
    m = re.match(r"^      ([\w\-]+):$", line)
    if m: cur = m.group(1)
    m = re.match(r"^        path:\s*(\S+)", line)
    if m and "{}" in m.group(1):
        bad.append((cur, m.group(1)))
if bad:
    print("anonymous path placeholders (substitution is by NAME; {} disables it):")
    for c, p in bad: print("   ", c, p)
    sys.exit(1)
PY
then pass "no anonymous {} placeholders (they silently disable substitution)"
else bad "anonymous {} placeholders present - the CLI will send a literal brace"
fi

# every shipment path must keep its trailing slash; nothing else may have one
sl=$(grep -oE '^\s+path: /api/[^ ]*/$' spec.yaml | wc -l | tr -d ' ')
nonship=$(grep -oE '^\s+path: /api/[^ ]*/$' spec.yaml | grep -vc '/api/shipment/' || true)
[ "$nonship" -eq 0 ] && pass "$sl trailing-slash paths, all under /api/shipment/" \
                     || bad "$nonship non-shipment paths carry a trailing slash (they 404 with one)"

echo
[ "$fail" -eq 0 ] && echo "INVARIANT GATE GREEN" || echo "INVARIANT GATE RED"
exit "$fail"
