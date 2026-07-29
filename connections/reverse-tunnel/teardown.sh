#!/bin/sh
# teardown.sh — undo the reverse tunnel, box side. Run ON the SAP box (jivo-dbsap)
# as superadmin. POSIX /bin/sh, no root needed.
#
#   sh teardown.sh              do it
#   sh teardown.sh --dry-run    show what would be removed, change nothing
#
# Matches the CURRENT flock-cron design (dial.sh). Removes, on the box:
#   - any running dial.sh and its flock'd ssh
#   - BOTH crontab lines (dial.sh and the old box-revtun.sh keeper, if present)
#   - $HOME/revtun in full (scripts, log, and the flock .lock)
#   - the dedicated key pair $HOME/.ssh/jivo_revtun{,.pub}
#   - the scp'd leftovers in $HOME: dial.sh, box-revtun.sh, install-box.sh, teardown.sh
#
# Nothing else on the box is touched — the box's own sshd, superadmin's normal
# authorized_keys and the jivo_accounts_box login are all left exactly as before.
#
# It then PRINTS the remaining manual steps (VPS authorized_keys line + its .bak,
# Mac ~/.ssh/config block) — those live on other machines, so this script won't
# touch them — and the command to verify VPS port 47192 is gone.
set -u

RT_DIR="$HOME/revtun"
KEY="$HOME/.ssh/jivo_revtun"

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1
[ "${1:-}" = "-n" ] && DRY=1

say() { printf '==> %s\n' "$*"; }
ok()  { [ "$DRY" = 1 ] || printf '==> %s\n' "$*"; }   # past-tense: silent in dry-run
do_or_show() {
    if [ "$DRY" = 1 ]; then
        printf '    [dry-run] %s\n' "$*"
    else
        sh -c "$*"
    fi
}

# Kill every process whose argv matches a pattern, skipping this script's own pid.
# No pidfiles exist under the flock-cron design, so we match on argv. The patterns
# are specific to the tunnel (the -R forward spec, the dialer path, the flock lock)
# and never appear in this teardown's own argv, so there is no self-kill risk.
kill_pat() {
    _pat=$1
    if [ "$DRY" = 1 ]; then
        if command -v pgrep >/dev/null 2>&1; then
            _hits=$(pgrep -fl "$_pat" 2>/dev/null | grep -v "^$$ ")
            [ -n "$_hits" ] && printf '    [dry-run] would kill matches of "%s":\n%s\n' \
                "$_pat" "$(printf '%s\n' "$_hits" | sed 's/^/        /')"
        else
            printf '    [dry-run] would pkill -f %s\n' "$_pat"
        fi
        return 0
    fi
    if command -v pkill >/dev/null 2>&1; then
        pkill -f "$_pat" 2>/dev/null || true
    else
        for _p in $(ps -eo pid,args 2>/dev/null | grep -F "$_pat" | grep -v grep | awk '{print $1}'); do
            [ "$_p" = "$$" ] && continue
            kill "$_p" 2>/dev/null || true
        done
    fi
}

[ "$DRY" = 1 ] && say "DRY RUN — nothing will be changed."

# Grab the public key first so the VPS line can be identified after deletion.
PUB=""
[ -f "$KEY.pub" ] && PUB=$(cat "$KEY.pub" 2>/dev/null)

# --- 1. stop the tunnel (kill dialer + its ssh) ----------------------------
kill_pat '127.0.0.1:47192:localhost:22'   # the flock'd ssh (unique -R spec)
kill_pat 'revtun/dial.sh'                 # any dialer mid-run
kill_pat "flock -n $HOME/revtun/.lock"    # a flock holding the lock without ssh
ok "tunnel stopped (dialer + ssh killed)"

# --- 2. crontab (remove BOTH designs' lines) -------------------------------
if crontab -l 2>/dev/null | grep -q -e 'revtun/dial.sh' -e 'box-revtun.sh'; then
    if [ "$DRY" = 1 ]; then
        printf '    [dry-run] remove these crontab lines:\n'
        crontab -l 2>/dev/null | grep -e 'revtun/dial.sh' -e 'box-revtun.sh' | sed 's/^/        /'
    else
        TMP="$HOME/.crontab.revtun.teardown"
        crontab -l 2>/dev/null | grep -v -e 'revtun/dial.sh' -e 'box-revtun.sh' > "$TMP"
        if [ -s "$TMP" ]; then
            crontab "$TMP"
        else
            crontab -r 2>/dev/null || true   # our lines were the only ones
        fi
        rm -f "$TMP"
    fi
    ok "crontab lines removed"
else
    say "crontab: nothing to remove"
fi

# --- 3. files: $HOME/revtun (incl .lock), the key pair, and scp'd leftovers -
if [ -d "$RT_DIR" ] && [ "$RT_DIR" = "$HOME/revtun" ]; then
    do_or_show "rm -rf '$RT_DIR'"          # includes dial.sh, revtun.log*, .lock, crontab.bak
    ok "removed $RT_DIR (incl .lock)"
else
    say "$RT_DIR: already gone"
fi

if [ -f "$KEY" ] || [ -f "$KEY.pub" ]; then
    do_or_show "rm -f '$KEY' '$KEY.pub'"
    ok "removed $KEY and $KEY.pub"
else
    say "$KEY: already gone"
fi

# The scp'd copies that install leaves loose in $HOME. Only remove them from the
# home directory itself (never from the repo checkout), and never remove the
# copy this teardown is executing from unless it is one of those loose files.
for leftover in "$HOME/dial.sh" "$HOME/box-revtun.sh" "$HOME/install-box.sh" "$HOME/teardown.sh"; do
    [ -f "$leftover" ] || continue
    do_or_show "rm -f '$leftover'"
    ok "removed leftover $leftover"
done

# --- 4. what's left, on other machines -------------------------------------
if [ "$DRY" = 1 ]; then
    echo
    say "DRY RUN — nothing above was actually changed. Re-run without --dry-run."
fi

cat <<'EOT'

-------------------------------------------------------------------------
Box is clean. Manual steps remain on the other two machines, plus a verify.

(A) FLEET VPS — drop the restricted authorized_keys line AND its backup
    (run from the Mac):

    ssh vps-pub "cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak && \
                 sed -i '/permitlisten=\"127.0.0.1:47192\"/d' ~/.ssh/authorized_keys"
    ssh vps-pub 'grep -c permitlisten ~/.ssh/authorized_keys'   # expect 0
    ssh vps-pub 'rm -f ~/.ssh/authorized_keys.bak'              # remove the .bak too

(A2) FLEET VPS — verify port 47192 is GONE. The listener can linger after the
     box dies until the VPS sshd notices (up to ~2h). Force-clear + verify:

    ssh vps-pub 'fuser -k 47192/tcp 2>/dev/null; sleep 1; ss -ltn | grep 47192 || echo "47192 clear"'
    # expect: 47192 clear

(B) MAC — delete the ssh-config block from ~/.ssh/config:

    Host jivo-sap-any
        HostName 127.0.0.1
        Port 47192
        User superadmin
        IdentityFile ~/.ssh/jivo_accounts_box
        IdentitiesOnly yes
        ProxyJump vps-pub
        HostKeyAlias jivo-dbsap
        StrictHostKeyChecking accept-new

    ...and its stale host key, recorded under the HostKeyAlias:

    ssh-keygen -R jivo-dbsap
    ssh-keygen -R '[127.0.0.1]:47192'    # in case an older block recorded it here

After (A), (A2) and (B), both hosts are exactly as they were before the tunnel.
-------------------------------------------------------------------------
EOT

if [ -n "$PUB" ]; then
    echo "For reference, the key that was authorized on the VPS:"
    echo "    $PUB"
fi
