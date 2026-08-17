#!/usr/bin/env bash
# ============================================================================
#  fleet-tunnel-register.sh — SSH FORCED COMMAND. Never run interactively.
#
#  A box that wants a permanent reverse tunnel calls this with its OWN freshly
#  generated public key. We assign it a stable loopback port and append a
#  TIGHTLY RESTRICTED authorized_keys line that can do exactly one thing:
#  open 127.0.0.1:<port> on this VPS. No shell, no -L, no other port.
#
#  Protocol (in $SSH_ORIGINAL_COMMAND):
#      HOST=<name> USER=<user> KEY=<base64 of one ssh pubkey line>
#  Replies:
#      PORT=<n>            on success (idempotent: same host -> same port)
#      ERR=<reason>        on refusal
#
#  Why the caller's key is generated ON the caller: no private key is ever
#  distributed. The only thing shipped in the installer is the registrar key,
#  which is pinned to THIS script and cannot get a shell.
# ============================================================================
set -u

AK=/root/.ssh/authorized_keys
DB=/root/fleet-tunnels.txt
LOG=/root/fleet-tunnel-register.log
LOCK=/root/.fleet-tunnel-register.lock
PORT_MIN=23001
PORT_MAX=23099
MAX_HOSTS=60

log(){ printf '%s | %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG"; }
die(){ echo "ERR=$1"; log "REFUSED from ${SSH_CONNECTION%% *} : $1"; exit 0; }

cmd="${SSH_ORIGINAL_COMMAND:-}"
[ -n "$cmd" ] || die "empty-request"
case "$cmd" in *$'\n'*|*$'\r'*) die "multiline-request" ;; esac
[ "${#cmd}" -le 1200 ] || die "request-too-long"

host=$(printf '%s' "$cmd" | grep -oE '(^| )HOST=[A-Za-z0-9._-]{1,64}( |$)' | head -1 | tr -d ' ' | cut -d= -f2)
user=$(printf '%s' "$cmd" | grep -oE '(^| )USER=[A-Za-z0-9._-]{1,64}( |$)' | head -1 | tr -d ' ' | cut -d= -f2)
keyb=$(printf '%s' "$cmd" | grep -oE '(^| )KEY=[A-Za-z0-9+/=]{40,1000}( |$)'  | head -1 | tr -d ' ' | cut -d= -f2)

[ -n "$host" ] || die "bad-or-missing-HOST"
# Reject names that cannot identify ONE machine. A Mac on DHCP can report "192"
# (from 192.168.x.x truncated at the first dot); since the registry is keyed by
# HOST, accepting it lets a second machine seize the first one's port and replace
# its key. Better to refuse than to hand out a colliding identity.
printf '%s' "$host" | grep -qE '^[0-9._-]+$' && die "host-not-unique-numeric"
[ "${#host}" -ge 3 ] || die "host-too-short"
[ -n "$user" ] || die "bad-or-missing-USER"
[ -n "$keyb" ] || die "bad-or-missing-KEY"

pub=$(printf '%s' "$keyb" | base64 -d 2>/dev/null | tr -d '\r' | sed -n '1p')
[ -n "$pub" ] || die "key-not-base64"
# Shape check first: exactly one plain pubkey line, no options, no newlines —
# this string is about to be written into authorized_keys.
printf '%s' "$pub" | grep -qE '^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256) AAAA[A-Za-z0-9+/=]+( [A-Za-z0-9._@-]{0,64})?$' \
  || die "key-not-a-single-plain-pubkey"

# Shape is not enough: "ssh-ed25519 AAAAB3 x" passes a regex and is still junk.
# ssh-keygen is the authority on whether this is a real, usable key.
_kf=$(mktemp) || die "mktemp-failed"
printf '%s\n' "$pub" > "$_kf"
if ! ssh-keygen -l -f "$_kf" >/dev/null 2>&1; then rm -f "$_kf"; die "key-fails-ssh-keygen-validation"; fi
rm -f "$_kf"

keybody=$(printf '%s' "$pub" | awk '{print $1" "$2}')

exec 9>"$LOCK"; flock -w 10 9 || die "busy"

touch "$AK" "$DB"

# Already known? Same host -> same port, and refresh the key if it was regenerated.
existing=$(grep -E "^${host}[[:space:]]" "$DB" 2>/dev/null | tail -1)
if [ -n "$existing" ]; then
  port=$(printf '%s' "$existing" | awk '{print $2}')
else
  [ "$(wc -l < "$DB")" -lt "$MAX_HOSTS" ] || die "registry-full"
  port=""
  p="$PORT_MIN"
  while [ "$p" -le "$PORT_MAX" ]; do
    if ! grep -qE "^[^[:space:]]+[[:space:]]+${p}[[:space:]]" "$DB" 2>/dev/null \
       && ! ss -ltn 2>/dev/null | grep -q "127.0.0.1:${p} "; then
      port="$p"; break
    fi
    p=$((p+1))
  done
  [ -n "$port" ] || die "no-free-port"
fi

# Rewrite this host's authorized_keys line (drop any previous one for this host).
#
# The comment field must be matched WHOLE. This was `grep -vF " revtun-${host}"`,
# which is a SUBSTRING match, so a host name that is a prefix of another host's
# name silently deleted its siblings' keys. On 2026-08-03T12:16:18Z the box named
# JIVO registered and took revtun-JIVO-B1 (23002) and revtun-JIVO202 (23006) with
# it; both boxes then dialled in for two weeks and were refused, and because they
# were still listed in fleet-tunnels.txt they looked like ordinary offline PCs.
# JIVO201 (23010) survived only because it registered afterwards -- verified
# 2026-08-17: `grep -vF " revtun-JIVO"` drops 2 of 19 keys, `$NF` drops 1.
# $NF is the trailing comment; compare it whole and this cannot recur.
tmp=$(mktemp) || die "mktemp-failed"
awk -v c="revtun-${host}" '$NF != c' "$AK" > "$tmp" 2>/dev/null || true
# Removing anything beyond this host's own single line means the match went wide.
# The old guard could not see that: it dropped 2 keys and appended 1, landing on
# exactly the threshold, so `-lt` was false by one line and it installed happily.
_before=$(grep -c . "$AK"); _kept=$(grep -c . "$tmp")
if [ "$(( _before - _kept ))" -gt 1 ]; then
  rm -f "$tmp"; die "refused-would-drop-$(( _before - _kept ))-keys"
fi
printf 'restrict,port-forwarding,permitlisten="127.0.0.1:%s",permitopen="127.0.0.1:1" %s revtun-%s\n' \
  "$port" "$keybody" "$host" >> "$tmp"
# Never install a truncated authorized_keys: it must still contain the operator
# keys. We removed at most one line and added exactly one, so the result can
# never be shorter than what we started with.
if [ "$(grep -c . "$tmp")" -lt "$_before" ]; then rm -f "$tmp"; die "sanity-check-failed"; fi
install -m 600 -o root -g root "$tmp" "$AK" && rm -f "$tmp"

grep -vE "^${host}[[:space:]]" "$DB" > "$DB.tmp" 2>/dev/null || true
mv -f "$DB.tmp" "$DB" 2>/dev/null || true
printf '%s %s %s %s\n' "$host" "$port" "$user" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DB"

flock -u 9
log "OK host=$host port=$port user=$user from=${SSH_CONNECTION%% *}"
echo "PORT=$port"
