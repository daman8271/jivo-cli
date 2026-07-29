#!/bin/sh
# install-box.sh — one-shot, idempotent installer for the reverse tunnel.
# Run ON the SAP box (jivo-dbsap) as superadmin. Needs NO root, NO systemd,
# NO autossh. Safe to re-run: nothing is duplicated, nothing is overwritten
# except dial.sh itself.
#
# Installs the CANONICAL flock-cron design (not the old keeper):
#   1. creates $HOME/revtun
#   2. installs dial.sh there (chmod +x)  <- the runtime
#   3. creates $HOME/.ssh/jivo_revtun (ed25519, no passphrase) if absent, chmod 600
#   4. prints the PUBLIC key — paste it on the VPS (see vps-authorize.md)
#   5. installs BOTH crontab lines (@reboot + every minute), de-duplicated,
#      AFTER safely backing up the current crontab (clobber-proof, see below)
#   6. kicks one dial so the tunnel comes up now instead of waiting for cron
#
# Copy the scripts to the box first, e.g. from the Mac:
#   scp connections/reverse-tunnel/dial.sh \
#       connections/reverse-tunnel/install-box.sh jivo-sap:~/
#   ssh jivo-sap 'sh ~/install-box.sh'
set -u

RT_DIR="$HOME/revtun"
SCRIPT="$RT_DIR/dial.sh"
KEY="$HOME/.ssh/jivo_revtun"
CRON_REBOOT="@reboot $SCRIPT"
CRON_EVERY1="* * * * * $SCRIPT"

SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

say() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" = 0 ] && say "WARNING: running as root — this is designed for the normal user (superadmin)."

# --- 1. directory ----------------------------------------------------------
mkdir -p "$RT_DIR" || die "cannot create $RT_DIR"
chmod 700 "$RT_DIR"
say "dir ready: $RT_DIR"

# --- 2. dialer (the runtime) ----------------------------------------------
if [ "$SRC_DIR/dial.sh" != "$SCRIPT" ]; then
    [ -f "$SRC_DIR/dial.sh" ] || die "dial.sh not found next to $0 — copy it to the box too"
    cp "$SRC_DIR/dial.sh" "$SCRIPT" || die "cannot write $SCRIPT"
fi
chmod +x "$SCRIPT"
say "dialer installed: $SCRIPT"

# Optional: keep box-revtun.sh available as MANUAL tooling if it was copied too.
# It is NOT wired into cron and is NOT the runtime — dial.sh is.
if [ -f "$SRC_DIR/box-revtun.sh" ] && [ "$SRC_DIR/box-revtun.sh" != "$RT_DIR/box-revtun.sh" ]; then
    cp "$SRC_DIR/box-revtun.sh" "$RT_DIR/box-revtun.sh" && chmod +x "$RT_DIR/box-revtun.sh"
    say "manual tool (superseded) also placed: $RT_DIR/box-revtun.sh"
fi

# --- 3. dedicated key (private key NEVER leaves this box) ------------------
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
if [ -f "$KEY" ]; then
    say "key already present: $KEY (kept)"
else
    ssh-keygen -t ed25519 -N '' -C "revtun@$(hostname -s 2>/dev/null || echo jivo-dbsap)" -f "$KEY" >/dev/null \
        || die "ssh-keygen failed"
    say "key generated: $KEY"
fi
chmod 600 "$KEY"
[ -f "$KEY.pub" ] && chmod 644 "$KEY.pub"

# --- 4. show the public key ------------------------------------------------
echo
echo "-------------------------------------------------------------------------"
echo "PUBLIC KEY — add this to the VPS root ~/.ssh/authorized_keys, PREFIXED with"
echo '  restrict,port-forwarding,permitlisten="127.0.0.1:47192",permitopen="127.0.0.1:1"'
echo "(full instructions: connections/reverse-tunnel/vps-authorize.md)"
echo
cat "$KEY.pub"
echo "-------------------------------------------------------------------------"
echo

# --- 5. crontab (CLOBBER-PROOF) -------------------------------------------
# The whole point of this section: NEVER install a crontab that was rebuilt from
# a FAILED `crontab -l`. If `crontab -l` errors for any reason other than the
# benign "no crontab for user" (empty output), we would otherwise silently wipe
# every existing job. So: read once, capture rc + stderr, back it up, and abort
# loudly on a real failure.
CRON_ERR="$RT_DIR/.crontab.err"
CUR_CRON=$(crontab -l 2>"$CRON_ERR")
CRON_RC=$?

if [ "$CRON_RC" -ne 0 ]; then
    # Non-zero is only acceptable as the benign "no crontab" case: empty stdout
    # and a stderr that says so (or is empty). Anything else is a real failure.
    if [ -n "$CUR_CRON" ] || { [ -s "$CRON_ERR" ] && ! grep -qi 'no crontab' "$CRON_ERR" 2>/dev/null; }; then
        printf 'ERROR: crontab -l failed (rc=%s):\n' "$CRON_RC" >&2
        sed 's/^/    /' "$CRON_ERR" >&2
        rm -f "$CRON_ERR"
        die "refusing to rebuild the crontab from a failed 'crontab -l' — that would wipe existing jobs. Fix cron access for this user, then re-run."
    fi
    CUR_CRON=""    # benign: this user simply has no crontab yet
fi
rm -f "$CRON_ERR"

# Back up exactly what we safely read (empty file if there was no crontab).
printf '%s\n' "$CUR_CRON" | sed '/^[[:space:]]*$/d' > "$RT_DIR/crontab.bak"
say "current crontab backed up: $RT_DIR/crontab.bak"

# Rebuild: keep every line that is NOT one of ours (dial.sh or the old
# box-revtun.sh keeper), then append our two lines fresh. De-duped by construction.
TMP_CRON="$RT_DIR/.crontab.new"
{
    printf '%s\n' "$CUR_CRON" \
        | grep -v -e 'revtun/dial.sh' -e 'box-revtun.sh' \
        | sed '/^[[:space:]]*$/d'
    printf '%s\n' "$CRON_REBOOT"
    printf '%s\n' "$CRON_EVERY1"
} > "$TMP_CRON"

if crontab "$TMP_CRON"; then
    rm -f "$TMP_CRON"
    say "crontab installed (@reboot + every-minute dial), backup at $RT_DIR/crontab.bak"
    crontab -l | grep 'revtun/dial.sh' | sed 's/^/    /'
else
    rm -f "$TMP_CRON"
    die "crontab install failed — current crontab is unchanged; backup at $RT_DIR/crontab.bak"
fi

# --- 6. kick one dial ------------------------------------------------------
# Bring the tunnel up now rather than waiting up to 60s for the next cron tick.
# Detached: dial.sh execs ssh in the foreground, so we must NOT run it inline or
# the installer would block for the life of the tunnel. flock makes this safe —
# the next cron run just no-ops behind the lock. (If this session's logind gets
# reaped on logout, cron re-dials within 60s; that is the design.)
nohup "$SCRIPT" >/dev/null 2>&1 &
say "kicked one dial (pid $!) — cron maintains it from here"
echo
say "Verify from the Mac:  ssh jivo-sap-any 'hostname'   (-> jivo-dbsap)"
say "If the VPS key is not authorized yet, revtun.log will show repeated"
say "'Permission denied (publickey)' until step 4 is applied on the VPS."
