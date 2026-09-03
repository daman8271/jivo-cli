#!/usr/bin/env bash
# keepalive.sh — the daily re-logins a 3-minute loop needs to survive the week.
#
#   0 4 * * *  /root/jivo-courier/jolly/live/keepalive.sh
#
# WHY THIS EXISTS. Nothing here is about data. Three of the four live sources
# hold short-lived tokens, and when one dies the loop does not stop — it starts
# returning "nothing happened" for a plant that is running. That is the failure
# mode this whole project exists to prevent, and exim already did it silently
# for 12 days.
#
#   factory (ji.jivo.in)   access 25 h, refresh 7 d  -> auth login, daily
#   OMS (Daman@oms.com)    access 24 h, refresh 7 d  -> auth login, daily,
#                                                       into its OWN config file
#   ecom (ecom.jivo.in)    access  1 h, refresh 30 d -> `ecom doctor`; the
#                          wrapper decodes the JWT's own exp and rotates the
#                          refresh token itself. Calling it daily is belt and
#                          braces; the loop's own first call renews it anyway.
#   EXIM                   access 24 h, no refresh   -> NOTHING TO DO. The
#                          exim wrapper re-mints from .env on demand. Do not
#                          add a "keepalive" call here; it would be pure load.
#
# The three logins are the ONLY writes anything in live/ performs, and each CLI
# documents it as such: POST .../login exchanges a password for a token and
# mutates no JIVO data. Never add /account/logout/ here — it invalidates the
# refresh token for everyone on that login.
#
# SECRETS. Nothing is ever echoed. Passwords are passed to the CLIs through the
# environment (never on argv, where `ps` would show them), and every line of
# output is filtered through a redactor that blanks the known secret values and
# anything JWT-shaped before it reaches the log.
#
# WHERE CREDENTIALS COME FROM (first hit wins, per variable):
#   1. the environment
#   2. live/.keepalive.env       <- the right home for the OMS billing pair
#   3. <repo>/.env               <- factory + ecom already live here
#
# live/.keepalive.env is a plain KEY=VALUE file, matched by the repo's existing
# `*.env` gitignore rule, so it never reaches a commit. It needs exactly this:
#
#   OMS_DAMAN_USERNAME=Daman@oms.com
#   OMS_DAMAN_PASSWORD=...
#
# The repo .env carries OMS_USERNAME=paramjot — a DIFFERENT account with a
# different order-visibility scope. Logging that into the Daman config would
# quietly change what oms.py can see, so this script refuses to do it: if the
# resolved username is not the account the adapter expects, OMS is skipped
# loudly rather than repointed silently.
#
# TOOL PATHS come from the same three places, in the same order, and are then
# platform-corrected: on Linux a committed `<binary>.linux` build wins over the
# Mac binary of the same name. (Before 2026-09-03 they were read from the
# process environment ONLY, so these knobs did nothing in .keepalive.env, and
# the VPS exec'd the Mac binaries: "rc=126 Exec format error".)
#
# Env knobs: KEEPALIVE_ONLY=factory,oms,ecom · MARK3_STATE_DIR · OMS_CONFIG ·
# OMS_EXPECT_USER · JIVO_FACTORY_CLI · OMS_BIN · ECOM_WRAPPER (or the older
# JIVO_ECOM_WRAPPER). All but OMS_EXPECT_USER also work in .keepalive.env.

set -uo pipefail

LIVE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
JOLLY_DIR="$(dirname -- "$LIVE_DIR")"
REPO_DIR="$(dirname -- "$JOLLY_DIR")"
STATE_DIR="${MARK3_STATE_DIR:-$LIVE_DIR/state}"
LOG="$STATE_DIR/keepalive.log"
MAX_BYTES="${KEEPALIVE_MAX_LOG_BYTES:-1048576}"

# OMS_EXPECT_USER stays PROCESS-ENV ONLY, deliberately. It is the guard the OMS
# block checks the resolved username against; letting a .env file lower it would
# let the repo's paramjot pair through into the Daman config.
OMS_EXPECT_USER="${OMS_EXPECT_USER:-Daman@oms.com}"

ENV_FILES=("$LIVE_DIR/.keepalive.env" "$REPO_DIR/.env")
# The four CLI paths are resolved further down, AFTER resolve() exists — see
# "tool paths". They used to be set here, from the process environment alone,
# which silently ignored JIVO_FACTORY_CLI / OMS_BIN / OMS_CONFIG /
# JIVO_ECOM_WRAPPER placed in live/.keepalive.env.
ONLY="${KEEPALIVE_ONLY:-factory,oms,ecom}"

mkdir -p "$STATE_DIR"
[ -f "$LOG" ] || : >"$LOG"
if [ "$(wc -c <"$LOG" 2>/dev/null | tr -d ' ')" -ge "$MAX_BYTES" ] 2>/dev/null; then
  mv -f "$LOG" "$LOG.1"; : >"$LOG"
fi

# ---------------------------------------------------------------- redaction
# Every byte of output goes through here. It blanks the exact secret values we
# resolved plus anything JWT-shaped, so a CLI that helpfully echoes a token
# cannot leak it into a log that syncs to the VPS.
SECRETS_FILE="$(mktemp "${TMPDIR:-/tmp}/mark3-keepalive.XXXXXX")"
REDACTOR="$SECRETS_FILE.py"
chmod 600 "$SECRETS_FILE"
cleanup() { rm -f "$SECRETS_FILE" "$REDACTOR"; }
trap cleanup EXIT INT TERM

# The filter is written to a FILE, not fed to `python3 -` on a heredoc: a
# heredoc IS stdin, so the script would eat the very stream it is meant to
# filter and silently emit nothing. (It did exactly that on the first run.)
cat >"$REDACTOR" <<'PY'
import re, sys
try:
    secrets = [s for s in open(sys.argv[1], encoding="utf-8").read().split("\n") if len(s) >= 4]
except OSError:
    secrets = []
jwt = re.compile(r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}\b")
for line in sys.stdin:
    for s in secrets:
        line = line.replace(s, "<redacted>")
    sys.stdout.write(jwt.sub("<jwt-redacted>", line))
    sys.stdout.flush()
PY
chmod 600 "$REDACTOR"

redact() { python3 "$REDACTOR" "$SECRETS_FILE"; }

stamp() { date +'%Y-%m-%dT%H:%M:%S%z'; }
say() { printf '%s %s\n' "$(stamp)" "$*" | redact | tee -a "$LOG"; }

# ------------------------------------------------------------ env resolution
# Reads ONE key out of a KEY=VALUE file. Deliberately not `source`: a password
# containing a backtick or $( would otherwise be executed by the shell.
env_get() {
  local key="$1" f v
  for f in "${ENV_FILES[@]}"; do
    [ -r "$f" ] || continue
    v="$(sed -n -E "s/^[[:space:]]*(export[[:space:]]+)?${key}=//p" "$f" | head -n 1)" || v=""
    [ -n "$v" ] || continue
    v="${v%$'\r'}"
    case "$v" in
      \"*\") v="${v#\"}"; v="${v%\"}" ;;
      \'*\') v="${v#\'}"; v="${v%\'}" ;;
    esac
    printf '%s' "$v"; return 0
  done
  return 1
}

# resolve VAR [fallback-key ...] — environment first, then the env files.
resolve() {
  local var="$1"; shift
  local cur="${!var:-}" k v
  if [ -n "$cur" ]; then printf '%s' "$cur"; return 0; fi
  for k in "$var" "$@"; do
    if v="$(env_get "$k")"; then printf '%s' "$v"; return 0; fi
  done
  return 1
}

note_secret() { [ -n "${1:-}" ] && printf '%s\n' "$1" >>"$SECRETS_FILE"; }

# ------------------------------------------------------------------ tool paths
# RESOLVED HERE, not at the top of the file, for two reasons that were both live
# bugs on 2026-09-03:
#
#  1. These used to be `${JIVO_FACTORY_CLI:-...}` etc., read from the PROCESS
#     environment only and set BEFORE ENV_FILES even existed. Every one of those
#     knobs is documented as settable in live/.keepalive.env, and none of them
#     took effect there. resolve() keeps the same precedence the credentials
#     use — environment first, then .keepalive.env, then the repo .env.
#  2. On the VPS the bare binary name is the MAC build, so keepalive exec'd it
#     and got "rc=126 cannot execute binary file: Exec format error" for both
#     factory and oms. prefer_linux() picks the committed <base>.linux build,
#     exactly as the adapters now do.

# Same rule as live/adapters/*: on Linux, use <base>.linux when it is there and
# executable. Idempotent — pointing a knob straight at the .linux file is fine.
prefer_linux() {
  local base="$1"
  if [ "$(uname -s 2>/dev/null)" = "Linux" ] && [ -x "$base.linux" ]; then
    printf '%s' "$base.linux"
  else
    printf '%s' "$base"
  fi
}

FACTORY_CLI="$(prefer_linux "$(resolve JIVO_FACTORY_CLI \
  || printf '%s' "$REPO_DIR/factory-cli/jivo-factory-pp-cli")")"
OMS_CLI="$(prefer_linux "$(resolve OMS_BIN \
  || printf '%s' "$REPO_DIR/oms-cli/oms-pp-cli")")"
# A config file, not a binary — nothing to prefer, just resolve it properly.
OMS_CFG="$(resolve OMS_CONFIG || printf '%s' "$HOME/.config/oms-pp-cli/oms-daman.toml")"

# The ecom wrapper, in the SAME order live/adapters/ecom.py now uses — keepalive
# must renew the token of the wrapper the loop actually runs, not a second
# install. ECOM_WRAPPER is the current name; JIVO_ECOM_WRAPPER still works.
ECOM="$(resolve ECOM_WRAPPER JIVO_ECOM_WRAPPER || true)"
if [ -z "$ECOM" ]; then
  if [ -x "$REPO_DIR/ecom-cli/ecom" ]; then ECOM="$REPO_DIR/ecom-cli/ecom"
  else ECOM="$(command -v ecom || printf '%s' "$HOME/.local/bin/ecom")"
  fi
fi
ECOM="$(prefer_linux "$ECOM")"

wants() { case ",$ONLY," in *",$1,"*) return 0 ;; *) return 1 ;; esac; }

FAILED=0
SKIPPED=0

say "==== keepalive start (host $(hostname -s 2>/dev/null || echo '?')) ===="

# --------------------------------------------------------------------- factory
if wants factory; then
  F_EMAIL="$(resolve JIVO_FACTORY_EMAIL || true)"
  F_PASS="$(resolve JIVO_FACTORY_PASSWORD || true)"
  note_secret "$F_PASS"
  if [ ! -x "$FACTORY_CLI" ]; then
    say "factory SKIP — CLI not executable at $FACTORY_CLI"; SKIPPED=$((SKIPPED+1))
  elif [ -z "$F_EMAIL" ] || [ -z "$F_PASS" ]; then
    say "factory SKIP — no JIVO_FACTORY_EMAIL/JIVO_FACTORY_PASSWORD in env, live/.keepalive.env or $REPO_DIR/.env"
    SKIPPED=$((SKIPPED+1))
  else
    # Password goes in via the environment, never argv. --password-stdin would
    # also work; env is what the CLI documents as the preferred path.
    out="$(JIVO_FACTORY_EMAIL="$F_EMAIL" JIVO_FACTORY_PASSWORD="$F_PASS" \
           "$FACTORY_CLI" auth login --no-input --no-color --yes 2>&1)"
    rc=$?
    if [ "$rc" -eq 0 ]; then
      say "factory OK   — auth login as $F_EMAIL (token ~25 h, refresh 7 d)"
    else
      say "factory FAIL — auth login rc=$rc: $(printf '%s' "$out" | tail -n 3 | tr '\n' ' ')"
      FAILED=$((FAILED+1))
    fi
  fi
fi

# ------------------------------------------------------------------------- OMS
if wants oms; then
  O_USER="$(resolve OMS_DAMAN_USERNAME || true)"
  O_PASS="$(resolve OMS_DAMAN_PASSWORD || true)"
  # Only fall back to the generic pair when it IS the expected account —
  # never repoint the Daman config at paramjot's narrower visibility.
  if [ -z "$O_USER" ]; then
    cand="$(resolve OMS_USERNAME || true)"
    if [ "$cand" = "$OMS_EXPECT_USER" ]; then
      O_USER="$cand"; [ -n "$O_PASS" ] || O_PASS="$(resolve OMS_PASSWORD || true)"
    fi
  fi
  note_secret "$O_PASS"
  if [ ! -x "$OMS_CLI" ]; then
    say "oms     SKIP — CLI not executable at $OMS_CLI"; SKIPPED=$((SKIPPED+1))
  elif [ -z "$O_USER" ] || [ -z "$O_PASS" ]; then
    say "oms     SKIP — no credential for $OMS_EXPECT_USER. Put OMS_DAMAN_USERNAME/OMS_DAMAN_PASSWORD in $LIVE_DIR/.keepalive.env (chmod 600). The .env pair is a different account and is NOT used."
    SKIPPED=$((SKIPPED+1))
  elif [ "$O_USER" != "$OMS_EXPECT_USER" ]; then
    say "oms     SKIP — resolved user is not $OMS_EXPECT_USER; refusing to repoint $OMS_CFG at another account (oms.py's order visibility depends on it)."
    SKIPPED=$((SKIPPED+1))
  else
    # The config file must exist with base_url before login; creating it is how
    # the billing token stays out of the default paramjot config.
    mkdir -p "$(dirname "$OMS_CFG")"
    if [ ! -s "$OMS_CFG" ]; then
      printf "base_url = 'https://oms.jivo.in'\n" >"$OMS_CFG"; chmod 600 "$OMS_CFG"
      say "oms     .... created $OMS_CFG (base_url only)"
    fi
    out="$(OMS_USERNAME="$O_USER" OMS_PASSWORD="$O_PASS" \
           "$OMS_CLI" auth login --config "$OMS_CFG" --no-input --no-color --yes 2>&1)"
    rc=$?
    if [ "$rc" -eq 0 ]; then
      say "oms     OK   — auth login as $O_USER into $(basename "$OMS_CFG") (token 24 h, refresh 7 d)"
    else
      say "oms     FAIL — auth login rc=$rc: $(printf '%s' "$out" | tail -n 3 | tr '\n' ' ')"
      FAILED=$((FAILED+1))
    fi
  fi
fi

# ------------------------------------------------------------------------ ecom
if wants ecom; then
  if [ ! -x "$ECOM" ]; then
    say "ecom    SKIP — wrapper not executable at $ECOM (set ECOM_WRAPPER)"; SKIPPED=$((SKIPPED+1))
  else
    out="$("$ECOM" doctor 2>&1)"; rc=$?
    if [ "$rc" -eq 0 ]; then
      renewed=""
      printf '%s' "$out" | grep -qi "renewed" && renewed=" (token renewed, refresh rotated)"
      say "ecom    OK   — doctor passed$renewed"
    else
      say "ecom    FAIL — doctor rc=$rc: $(printf '%s' "$out" | tail -n 3 | tr '\n' ' ')"
      FAILED=$((FAILED+1))
    fi
  fi
fi

say "exim    n/a  — wrapper re-mints its 24 h token from .env on demand; nothing to keep alive"
say "==== keepalive done: failed=$FAILED skipped=$SKIPPED ===="

# Non-zero on a real failure OR a skip: a silently skipped login is how a loop
# dies in a week with nobody watching. Cron mails on non-zero.
[ "$FAILED" -eq 0 ] && [ "$SKIPPED" -eq 0 ] && exit 0
exit 1
