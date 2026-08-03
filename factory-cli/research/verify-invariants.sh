#!/usr/bin/env bash
# Post-print invariant check for jivo-factory-pp-cli.
#
# A Printing Press run rewrites the whole tree. Every hand-authored guarantee in
# .printing-press-patches/ can silently fail to re-apply, and a generator working
# from an endpoint list has no idea that reading /marketplace/settings/ creates
# production rows. This asserts the things that must be true no matter what the
# generator did.
#
# Run from factory-cli/:   bash research/verify-invariants.sh
# Exit 0 = every invariant holds. Exit 1 = do not ship.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

CLI=./jivo-factory-pp-cli
SPEC=spec.yaml
MANIFEST=tools-manifest.json
fails=0
pass() { printf "  \033[32mPASS\033[0m  %s\n" "$1"; }
fail() { printf "  \033[31mFAIL\033[0m  %s\n" "$1"; fails=$((fails+1)); }

echo "=== 1. READ_ONLY_LAW: no write method anywhere in the published surface ==="
# Every declared method in the spec and manifest must be GET.
badspec=$(grep -E "^\s+method: " "$SPEC" | grep -v "method: GET" | wc -l | tr -d ' ')
[ "$badspec" = "0" ] && pass "spec.yaml declares only GET ($badspec non-GET)" \
                     || fail "spec.yaml declares $badspec non-GET methods"
badman=$(python3 -c "
import json;d=json.load(open('$MANIFEST'))
print(sum(1 for t in d.get('tools',[]) if (t.get('method') or 'GET').upper()!='GET'))" 2>/dev/null || echo ERR)
[ "$badman" = "0" ] && pass "tools-manifest.json declares only GET" \
                    || fail "tools-manifest.json has $badman non-GET tools"

echo
echo "=== 2. Endpoints that must NEVER be published ==="
# Reading these mutates, or they are unproven and therefore excluded.
for p in \
  "/marketplace/settings/" \
  "/marketplace/orders/resolve/" \
  "/grpo/draft/" \
  "/security-checks/gate-entries" \
  "/weighment/gate-entries" \
  "/po-receipts/view" \
  "/production-planning/" \
  "/warehouse/wms/dashboard/" \
  "/warehouse/wms/stock/overview/" \
; do
  n=$( { grep -cF "$p" "$SPEC"; grep -cF "$p" "$MANIFEST"; } 2>/dev/null | paste -sd+ - | bc )
  [ "${n:-0}" = "0" ] && pass "absent: $p" || fail "PUBLISHED (${n}x): $p"
done

echo
echo "=== 3. Patch invariants (.printing-press-patches/) ==="
# Capture help output ONCE into variables, then match against the strings.
#
# Do NOT pipe the CLI into `grep -q` here. `grep -q` exits on the first match,
# closing the pipe while the CLI is still writing; the CLI dies on SIGPIPE
# (141) and `set -o pipefail` reports the whole pipeline as failed even though
# the match succeeded. That produced a false FAIL for --company (58 lines of
# help) while auth --help passed purely because its output is short enough to
# finish first. A safety gate that fails on output length is worse than none.
ROOT_HELP=$($CLI --help 2>&1 || true)
AUTH_HELP=$($CLI auth --help 2>&1 || true)

case "$AUTH_HELP" in
  *login*) pass "0001 — 'auth login' present" ;;
  *)       fail "0001 — 'auth login' MISSING" ;;
esac
case "$ROOT_HELP" in
  *--company*) pass "0002 — --company flag present" ;;
  *)           fail "0002 — --company flag MISSING" ;;
esac
if grep -q 'Header.Set("Company-Code", CompanyCode())' internal/client/client.go 2>/dev/null; then
  pass "0002 — Company-Code header carries the resolved company"
elif grep -q "Company-Code" internal/client/client.go 2>/dev/null; then
  fail "0002 — Company-Code header is present but HARDCODED; --company is ignored"
else
  fail "0002 — Company-Code header MISSING"
fi
if grep -qE 'Header.Set\("Company-Code", "' internal/client/client.go 2>/dev/null; then
  fail "0002 — a hardcoded Company-Code literal remains in the client"
else
  pass "0002 — no hardcoded Company-Code literal"
fi
# 0003 MCP GET-only guards, BOTH paths
grep -q "READ_ONLY_LAW\|GET-only\|refuse every write" internal/mcp/tools.go 2>/dev/null \
  && pass "0003 — guard present in mcp/tools.go" || fail "0003 — guard MISSING in mcp/tools.go"
grep -q "READ_ONLY_LAW\|GET-only\|refuse every write" internal/mcp/code_orch.go 2>/dev/null \
  && pass "0003 — guard present in mcp/code_orch.go" || fail "0003 — guard MISSING in mcp/code_orch.go (write bypass)"
# 0004 no generic import
case "$ROOT_HELP" in
  *$'\n  import '*|*$'\n    import '*) fail "0004 — generic 'import' command PRESENT" ;;
  *)                                    pass "0004 — no generic 'import' command" ;;
esac
# 0005 oil release flags + company scope
OIL_HELP=$($CLI barcode production-release-oil --help 2>&1 || true)
case "$OIL_HELP" in
  *--page-size*) pass "0005 — production-release-oil has --page-size" ;;
  *)             fail "0005 — --page-size MISSING" ;;
esac
# 0006 product identity consumer
case "$ROOT_HELP" in
  *$'\n  product '*|*$'\n    product '*) pass "0006 — 'product' command family present" ;;
  *)                                     fail "0006 — 'product' family MISSING" ;;
esac

echo
echo "=== 4. Quality gates ==="
gofmt -l . 2>/dev/null | grep -v '^$' | head -3
[ -z "$(gofmt -l . 2>/dev/null)" ] && pass "gofmt clean" || fail "gofmt reports unformatted files"
go vet ./... >/dev/null 2>&1 && pass "go vet clean" || fail "go vet reports problems"
go build ./... >/dev/null 2>&1 && pass "go build succeeds" || fail "go build FAILS"
go test ./internal/mcp/... >/dev/null 2>&1 && pass "MCP guard tests pass" || fail "MCP guard tests FAIL"

# 0008 — Go toolchain must not regress below the version that patches
# GO-2026-5856 (crypto/tls ECH privacy leak). The MCP server's TLS transport
# is in the vulnerable call path, so this is a live exposure, not a lint.
tc=$(grep -E "^toolchain go" go.mod 2>/dev/null | awk '{print $2}' | sed 's/^go//')
if [ -n "$tc" ] && [ "$(printf '%s\n1.26.5\n' "$tc" | sort -V | head -1)" = "1.26.5" ]; then
  pass "0008 — go.mod toolchain is $tc (>= 1.26.5)"
else
  fail "0008 — go.mod toolchain is '${tc:-absent}'; GO-2026-5856 needs >= 1.26.5"
fi

echo
echo "=== 5. Coverage sanity (a print that silently shrinks is a regression) ==="
n=$(grep -cE "^\s+method: GET" "$SPEC" 2>/dev/null || echo 0)
[ "$n" -ge 350 ] && pass "spec declares $n GET endpoints (>=350 expected)" \
                 || fail "spec declares only $n GET endpoints — expected >=350"

echo
if [ "$fails" -eq 0 ]; then
  echo "ALL INVARIANTS HOLD."
  exit 0
fi
echo "$fails INVARIANT(S) VIOLATED — DO NOT SHIP."
exit 1
