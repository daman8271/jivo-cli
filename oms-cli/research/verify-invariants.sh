#!/usr/bin/env bash
# Post-print invariant gate for oms-pp-cli.
#
# Run this against the PRE-change tree first and require it GREEN before
# trusting a red light from it. A gate that has never passed has not been
# tested, and a false failure here costs an hour chasing a bug in the checker.
#
# The rule this file exists to serve: a check that can pass while the
# requirement is violated is worse than no check. On the factory run an
# invariant passed on a header's PRESENCE while the feature it guarded was a
# silent no-op. So where a property can only be observed by running the
# command, this runs the command.
#
# usage: RESCRAPE_CLI=./oms-pp-cli bash research/verify-invariants.sh
set -uo pipefail
CLI="${RESCRAPE_CLI:-./oms-pp-cli}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail=0
pass(){ printf '  PASS  %s\n' "$1"; }
bad(){ printf '  FAIL  %s\n' "$1"; fail=1; }

# NEVER write `"$CLI" ... | grep -q ...` in this file.
#
# `set -o pipefail` plus `grep -q` is a race. grep -q exits on the FIRST match,
# which closes the pipe; the CLI then dies of SIGPIPE with status 141; pipefail
# promotes that to the pipeline's status; and the `if` reads a successful match
# as a failure. Whether it bites depends on whether the CLI finished writing
# before grep exited, so it fails on the commands with the LONGEST help output
# and passes on the short ones — an intermittent red light on a gate whose
# whole job is to be believed. It cost a false "patch 0004 lost" here.
#
# helptext captures the output first, so the match is a pure string test.
helptext(){ "$CLI" "$@" --help 2>/dev/null || true; }
# NOTE: `has` takes exactly two arguments. Do not pass a `--` separator at the
# call site: it becomes $2 and the function then greps for the pattern `--`,
# which matches any help text containing a flag — a check that passes while the
# requirement is violated. That silently green-lit both the --branch and the
# patch-0004 assertions here. Leading dashes in a pattern are escaped as
# [-][-] instead.
has(){ [ "$#" -eq 2 ] || { echo "has(): expected 2 args, got $#" >&2; return 2; }
       printf '%s' "$1" | grep -qE -- "$2"; }

[ -x "$CLI" ] || { echo "no executable at $CLI (set RESCRAPE_CLI)"; exit 2; }
echo "invariant gate: $CLI"
echo

# ---------------------------------------------------------------- read-only
echo "RULE 0 - the CLI and its MCP surface are read-only"
n=$(grep -cE '^\s+method: (POST|PUT|PATCH|DELETE)' oms-spec.yaml || true)
[ "$n" -eq 0 ] && pass "spec declares no non-GET endpoint" || bad "spec declares $n non-GET endpoints"
n=$(grep -c 'method: GET' oms-spec.yaml || true)
[ "$n" -ge 73 ] && pass "spec declares $n GET endpoints (>= the 73 shipped)" \
                || bad "spec declares only $n GET endpoints - fewer than the 73 shipped"

# The OMS surface carries order, invoice and SAP writes. None may be wrapped.
for p in /api/service-layer/invoice /api/orders/create /api/invoice/pending \
         /api/sap/approve-sales-order /api/tracker/jsap/sync /api/devices/register \
         /api/auth/users/create /api/orders/web-push/subscribe; do
  if grep -q "path: \"$p/\"" oms-spec.yaml; then
    bad "WRITE ENDPOINT $p is present in the spec"
  fi
done
pass "no known write endpoint appears in the spec"

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

# ------------------------------------------------- the branch contract (NEW)
# The load-bearing invariant of the 2026-08 rescrape. Every /api/hana/ endpoint
# rejects a call without `branch`:
#     {"error":"branch is required and must be one of: OIL, BEVERAGE"}
# The shipped v0.1.0 spec declared it on NONE of them, so all 14 hana commands
# returned HTTP 400 and could never succeed. Presence of the command is not the
# property that matters; presence of the parameter is.
echo
echo "the branch contract - 14 hana endpoints are dead without it"
hana_paths=$(grep -c 'path: "/api/hana/' oms-spec.yaml || true)
hana_branch=$(python3 - <<'PY'
import re
txt = open("oms-spec.yaml").read()
# count hana endpoints whose param block declares a required `branch`
blocks = re.split(r"\n      (?=[\w-]+:\n)", txt)
n = 0
for b in blocks:
    if 'path: "/api/hana/' not in b:
        continue
    if re.search(r"-\s*name:\s*branch\b", b) and re.search(r"required:\s*true", b):
        n += 1
print(n)
PY
)
if [ "$hana_paths" -gt 0 ] && [ "$hana_branch" -eq "$hana_paths" ]; then
  pass "all $hana_paths /api/hana/ endpoints declare a required branch param"
else
  bad "$hana_branch of $hana_paths /api/hana/ endpoints declare required branch - the rest return HTTP 400 always"
fi
H=$(helptext hana fg-items)
if has "$H" '[-][-]branch'; then
  pass "hana fg-items exposes --branch"
else
  bad "hana fg-items has no --branch flag - the command cannot succeed"
fi

# ---------------------------------------------------------------- patches
echo
echo "patches (behaviour, not symbols)"
H=$(helptext auth)
if has "$H" '^  login( |$)'; then
  pass "0001 native 'auth login' is registered"
else
  bad "0001 native 'auth login' was dropped by the reprint"
fi
H=$("$CLI" --help 2>/dev/null || true)
if has "$H" '^  import( |$)'; then
  bad "0002 generic 'import' write command is REGISTERED - RULE 0 violation"
else
  pass "0002 generic 'import' is unreachable from the Cobra tree"
fi
H=$(helptext invoices)
if has "$H" '^  history( |$)'; then
  bad "0003 'invoices history' is registered but its backend route is absent"
else
  pass "0003 'invoices history' stays unregistered"
fi
A=$(helptext hana so); B=$(helptext hana product-so)
if has "$A" '[-][-]card-code' && has "$B" '[-][-]item-code'; then
  pass "0004 HANA required params (--card-code, --item-code) preserved"
else
  bad "0004 HANA required params lost"
fi

# ---------------------------------------------------------- no silent renames
echo
echo "no shipped command was renamed (skill rule 6)"
missing=0
while IFS=$'\t' read -r res cmd _; do
  [ -z "$res" ] && continue
  # 'invoices history' is deliberately unregistered by patch 0003 and is
  # verified above; it must NOT count as a vanished command here.
  [ "$res $cmd" = "invoices history" ] && continue
  H=$(helptext "$res")
  if ! has "$H" "^  $cmd( |\$)"; then
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
src = open("oms-spec.yaml").read()
bad, cur = [], None
for line in src.split("\n"):
    m = re.match(r"^      ([\w\-]+):$", line)
    if m: cur = m.group(1)
    m = re.match(r'^\s+path:\s*"?([^"\s]+)', line)
    if m and "{}" in m.group(1):
        bad.append((cur, m.group(1)))
if bad:
    print("anonymous path placeholders (substitution is by NAME; {} disables it):")
    for c, p in bad: print("   ", c, p)
    sys.exit(1)
PY
then pass "no anonymous {} placeholders (they make the CLI send a literal brace)"
else bad "anonymous {} placeholders present - the CLI will send a literal brace"
fi

# OMS is Django: EVERY route terminates in a trailing slash. This is the
# opposite of ecom, where only /api/shipment/ paths take one.
noslash=$(grep -oE '^\s+path: "/api/[^"]*"' oms-spec.yaml | grep -vc '/"$' || true)
[ "$noslash" -eq 0 ] && pass "every /api/ path carries its Django trailing slash" \
                     || bad "$noslash paths are missing the trailing slash"

echo
[ "$fail" -eq 0 ] && echo "INVARIANT GATE GREEN" || echo "INVARIANT GATE RED"
exit "$fail"
