#!/bin/sh
# dial-ports.sh — SECOND reverse-tunnel dialer. Runs ON the SAP box (jivo-dbsap)
# as superadmin, FROM CRON. POSIX /bin/sh only.
#
# WHY THIS IS SEPARATE FROM dial.sh (do not merge them):
#   dial.sh carries port 22 — our ONLY off-office route to this box — and it uses
#   ExitOnForwardFailure=yes. Adding forwards there means ANY one of them failing
#   (port busy on the VPS, permitlisten not updated) kills SSH access to the box
#   from every non-whitelisted IP. So the data ports get their own dialer, own
#   flock, own cron line. If this one dies, port 22 is unaffected.
#
# Holds open, on the fleet VPS loopback:
#   127.0.0.1:47500 -> this box's SAP B1 Service Layer on localhost:50000
#   127.0.0.1:47301 -> this box's HANA SQL port      on localhost:30015
#
# Those loopback ports are bridged to the docker network by socat containers on
# the VPS (see jivo-cli/connections/reverse-tunnel/README.md), which is how the
# always-on MCP servers reach SAP from anywhere without the office IP whitelist.
#
# Same flock-guarded cron mechanism as dial.sh: `@reboot` + `* * * * *`, each run
# execs ssh under `flock -n`, so while the tunnel is up every later run is an
# instant no-op and recovery after a drop is <=60s.
#
# The VPS key line must permit these listeners:
#   permitlisten="127.0.0.1:47500",permitlisten="127.0.0.1:47301"
# (see vps-authorize.md). Without them ssh exits immediately and cron retries
# forever — check ~/revtun/revtun-ports.log.
#
# READ-ONLY: forwarding a port grants no privilege by itself; every consumer
# (sapb1 CLI/MCP, hana-sql) is read-only by construction. CLAUDE.md Rule 0 stands.
set -u

LOG="$HOME/revtun/revtun-ports.log"
MAX_LOG_BYTES=1048576

mkdir -p "$HOME/revtun"

# Cap the log before (re)dialing so a persistent auth-failure loop can't fill the
# disk. Rotate-truncate: keep one previous copy.
if [ -f "$LOG" ]; then
    _sz=$(wc -c < "$LOG" 2>/dev/null | tr -d ' ')
    if [ -n "$_sz" ] && [ "$_sz" -gt "$MAX_LOG_BYTES" ] 2>/dev/null; then
        mv -f "$LOG" "$LOG.1"
    fi
fi

exec flock -n "$HOME/revtun/.lock-ports" ssh -N -T \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=accept-new \
    -o BatchMode=yes \
    -o IdentitiesOnly=yes \
    -o ConnectTimeout=15 \
    -i "$HOME/.ssh/jivo_revtun" \
    -R 127.0.0.1:47500:localhost:50000 \
    -R 127.0.0.1:47301:localhost:30015 \
    root@187.127.129.132 >> "$LOG" 2>&1
