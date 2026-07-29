#!/bin/sh
# dial.sh — the reverse-tunnel DIALER. Runs ON the SAP box (jivo-dbsap) as
# superadmin, FROM CRON. POSIX /bin/sh only: no bashisms, no autossh, no systemd,
# no root.
#
# THIS IS THE CANONICAL RUNTIME. It supersedes box-revtun.sh's keeper loop.
#
# Mechanism — a flock-guarded cron dial (simpler + reboot-robust):
#   crontab has BOTH  `@reboot dial.sh`  AND  `* * * * * dial.sh`.
#   Every run does `flock -n "$HOME/revtun/.lock"` and then execs ssh. While the
#   tunnel is up the lock is held, so every later cron run is an instant no-op —
#   there is never more than one ssh, no pile-up. The ssh runs in the cron job's
#   FOREGROUND (via exec), so its logind session stays alive for exactly as long
#   as the tunnel is up: no KillUserProcesses race, no keeper, no pidfiles, no
#   orphan-reaping. If the link dies the lock frees, and the next minute's cron
#   re-dials — recovery is <=60s (measured ~42s).
#
#   Holds open:  VPS 127.0.0.1:47192  ->  this box's sshd on localhost:22
#   so the Mac can reach SAP's SSH from ANY IP via the fleet VPS, bypassing the
#   box's public-IP whitelist.
#
# Docs + teardown: jivo-cli/connections/reverse-tunnel/README.md
set -u

LOG="$HOME/revtun/revtun.log"
MAX_LOG_BYTES=1048576

mkdir -p "$HOME/revtun"

# Cap the log at 1MB before (re)dialing, so a persistent auth-failure loop can
# never fill the disk. Rotate-truncate: keep one previous copy as revtun.log.1.
if [ -f "$LOG" ]; then
    _sz=$(wc -c < "$LOG" 2>/dev/null | tr -d ' ')
    if [ -n "$_sz" ] && [ "$_sz" -gt "$MAX_LOG_BYTES" ] 2>/dev/null; then
        mv -f "$LOG" "$LOG.1"
    fi
fi

exec flock -n "$HOME/revtun/.lock" ssh -N -T \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=accept-new \
    -o BatchMode=yes \
    -o IdentitiesOnly=yes \
    -o ConnectTimeout=15 \
    -i "$HOME/.ssh/jivo_revtun" \
    -R 127.0.0.1:47192:localhost:22 \
    root@187.127.129.132 >> "$HOME/revtun/revtun.log" 2>&1
