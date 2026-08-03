#!/usr/bin/env bash
# Verify the three .printing-press-patches BY BEHAVIOUR, not by grepping for a
# symbol.
#
# This exists because of a specific failure on the sibling factory project: a
# required header was hardcoded to a constant by the generator template, the
# patch script skipped its edit ("header already present"), the invariant gate
# passed ("found the string"), and --company was a silent no-op that routed
# every request to the wrong tenant. Presence is not correctness.
#
# So each check below runs the CLI and asserts on what it DOES. Every check
# also carries a negative assertion, because a check that can pass while the
# requirement is violated is worse than no check.
#
# usage: verify-patches.sh [path-to-cli]        (default ./jivo-ecom-pp-cli)
set -uo pipefail
CLI="${1:-./jivo-ecom-pp-cli}"
fail=0
pass() { printf '  PASS  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=1; }

[ -x "$CLI" ] || { echo "no executable at $CLI"; exit 2; }
echo "verifying patches against: $CLI"
echo

# ---------------------------------------------------------------- patch 0001
# The generic `import` write command must not exist. It POSTs to the live API
# with a Super-Admin JWT; RULE 0 forbids it.
echo "patch 0001 - generic 'import' write command must be unreachable"
if "$CLI" --help 2>&1 | grep -qE '^[[:space:]]+import[[:space:]]'; then
  bad "0001: 'import' is listed in top-level help"
else
  pass "0001: 'import' absent from top-level help"
fi
out="$("$CLI" import anything 2>&1)"
if printf '%s' "$out" | grep -qi 'unknown command'; then
  pass "0001: 'import x' rejected as unknown command"
else
  bad "0001: 'import x' did NOT report unknown command; got: $(printf '%s' "$out" | head -1)"
fi
# Negative assertion, done properly. Cobra's `help` ALWAYS exits 0 - it prints
# "Unknown help topic" for a missing command rather than failing - so asserting
# on its exit status is a false-failure generator, not a check. Assert instead
# that `help import` is indistinguishable from `help <nonsense>`; if `import`
# were registered, the first would print its usage block and the two would
# differ.
a="$("$CLI" help import 2>&1 | head -1)"
b="$("$CLI" help zzz-not-a-command-9f3a 2>&1 | head -1)"
if printf '%s' "$a" | grep -qi 'unknown help topic' &&
   printf '%s' "$b" | grep -qi 'unknown help topic'; then
  pass "0001: 'help import' reports an unknown topic, same as a nonsense topic"
else
  bad "0001: 'help import' resolved to a real command (got: $a)"
fi

# ---------------------------------------------------------------- patch 0002
# The hand-authored `auth login` command (email+password -> JWT) is not part of
# the printing-press scaffold and a --force regen drops it.
echo
echo "patch 0002 - hand-authored 'auth login' must exist and be wired"
if "$CLI" auth --help 2>&1 | grep -qE '^[[:space:]]+login[[:space:]]'; then
  pass "0002: 'auth login' listed under auth"
else
  bad "0002: 'auth login' missing from 'auth --help'"
fi
# behaviour, not presence: invoking it with no credentials must fail with a
# credential/usage error, NOT with 'unknown command'. That proves a real RunE
# is wired, not just a help string.
out="$("$CLI" auth login --no-input 2>&1)"
if printf '%s' "$out" | grep -qi 'unknown command'; then
  bad "0002: 'auth login' is not registered (unknown command)"
elif printf '%s' "$out" | grep -qiE 'email|password|credential|required|usage'; then
  pass "0002: 'auth login' runs and demands credentials"
else
  bad "0002: 'auth login' gave an unexpected response: $(printf '%s' "$out" | head -2)"
fi

# ---------------------------------------------------------------- patch 0003
# The hand-authored `api` discovery command: walks the Cobra tree, makes no
# HTTP call.
echo
echo "patch 0003 - hand-authored 'api' discovery command must exist and list groups"
if "$CLI" --help 2>&1 | grep -qE '^[[:space:]]+api[[:space:]]'; then
  pass "0003: 'api' listed in top-level help"
else
  bad "0003: 'api' missing from top-level help"
fi
# behaviour: it must actually enumerate endpoint groups, not just print help.
groups="$("$CLI" api 2>&1)"
n=$(printf '%s\n' "$groups" | grep -cE '^[[:space:]]*[a-z][a-z-]+' || true)
if [ "$n" -ge 8 ]; then
  pass "0003: 'api' enumerated $n lines of endpoint groups"
else
  bad "0003: 'api' produced only $n lines - discovery is not walking the tree"
fi
# and it must do so with NO network: unset every credential and it must still work
if env -u JIVO_ECOM_TOKEN -u JIVO_ECOM_EMAIL -u JIVO_ECOM_PASSWORD \
     "$CLI" api >/dev/null 2>&1; then
  pass "0003: 'api' works with no credentials (confirms it makes no HTTP call)"
else
  bad "0003: 'api' failed without credentials - it is making a network call"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "ALL PATCH CHECKS PASSED"
else
  echo "PATCH CHECKS FAILED"
fi
exit "$fail"
