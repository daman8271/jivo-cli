#!/bin/sh
# ============================================================================
# SUPERSEDED — NOT THE RUNTIME. Kept only as manual/diagnostic tooling.
#
# The live runtime is now `dial.sh` (a flock-guarded cron dial): simpler and
# reboot-robust, with no keeper, no pidfiles and no orphan-reaping. See dial.sh
# and README.md. This keeper is retained because `start`/`stop`/`status` are
# handy by hand, but it is NOT installed into cron and should NOT run alongside
# dial.sh (both would fight over VPS port 47192). install-box.sh installs
# dial.sh, not this.
# ============================================================================
#
# box-revtun.sh — reverse-SSH-tunnel keeper. Runs ON the SAP box (jivo-dbsap) as
# superadmin. POSIX /bin/sh only: no bashisms, no autossh, no systemd, no root.
#
# It holds open   VPS 127.0.0.1:47192  ->  this box's sshd on localhost:22
# so the Mac can reach SAP's SSH from ANY IP, hopping through the fleet VPS and
# bypassing the box's public-IP whitelist.
#
#   box-revtun.sh start    idempotent — nohup the keeper loop, write the pidfile
#   box-revtun.sh stop     kill the keeper loop and its ssh child
#   box-revtun.sh status   up or down + the last log lines
#
# Self-healing: the keeper loop re-dials every 10s whenever ssh drops.
# Docs + teardown: jivo-cli/connections/reverse-tunnel/README.md
set -u

# --- fixed parameters (verified) ------------------------------------------
VPS_HOST=187.127.129.132
VPS_USER=root
REMOTE_BIND=127.0.0.1
REMOTE_PORT=47192
LOCAL_TARGET=localhost:22
RETRY_SECS=10

RT_DIR="$HOME/revtun"
KEY="$HOME/.ssh/jivo_revtun"
PIDFILE="$RT_DIR/revtun.pid"
SSH_PIDFILE="$RT_DIR/revtun.ssh.pid"
LOG="$RT_DIR/revtun.log"
MAX_LOG_BYTES=1048576

umask 077

log() {
    printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

# Is the keeper loop alive? PIDFILE-based on purpose: `pgrep -f 47192` also
# matches this launcher's own argv and would report a false positive forever.
is_running() {
    [ -f "$PIDFILE" ] || return 1
    _pid=$(cat "$PIDFILE" 2>/dev/null) || return 1
    [ -n "$_pid" ] || return 1
    kill -0 "$_pid" 2>/dev/null
}

rotate_log() {
    [ -f "$LOG" ] || return 0
    _sz=$(wc -c < "$LOG" 2>/dev/null | tr -d ' ')
    [ -n "$_sz" ] || return 0
    [ "$_sz" -gt "$MAX_LOG_BYTES" ] 2>/dev/null && mv -f "$LOG" "$LOG.1"
    return 0
}

# The keeper loop itself. Runs in the background under nohup; never called by hand.
keeper_loop() {
    log "keeper started (pid $$) -> ${VPS_USER}@${VPS_HOST} ${REMOTE_BIND}:${REMOTE_PORT} -> ${LOCAL_TARGET}"
    while : ; do
        ssh -N -T \
            -o ServerAliveInterval=30 \
            -o ServerAliveCountMax=3 \
            -o ExitOnForwardFailure=yes \
            -o StrictHostKeyChecking=accept-new \
            -o BatchMode=yes \
            -i "$KEY" \
            -R "${REMOTE_BIND}:${REMOTE_PORT}:${LOCAL_TARGET}" \
            "${VPS_USER}@${VPS_HOST}" &
        _ssh=$!
        echo "$_ssh" > "$SSH_PIDFILE"
        log "tunnel up (ssh pid $_ssh)"
        wait "$_ssh"
        _rc=$?
        rm -f "$SSH_PIDFILE"
        log "tunnel down (rc=$_rc); retrying in ${RETRY_SECS}s"
        sleep "$RETRY_SECS"
    done
}

cmd_start() {
    if is_running; then
        echo "revtun: already running (pid $(cat "$PIDFILE"))"
        return 0
    fi

    mkdir -p "$RT_DIR" || { echo "revtun: cannot create $RT_DIR" >&2; return 1; }

    if [ ! -f "$KEY" ]; then
        echo "revtun: missing key $KEY — run install-box.sh first" >&2
        return 1
    fi
    chmod 600 "$KEY" 2>/dev/null

    # Keeper is dead, but its ssh child may have outlived it (killed keeper, OOM).
    # Reap the orphan: it still holds VPS port 47192, so a fresh attempt would just
    # bounce off ExitOnForwardFailure every 10s forever.
    if [ -f "$SSH_PIDFILE" ]; then
        _spid=$(cat "$SSH_PIDFILE" 2>/dev/null)
        if [ -n "${_spid:-}" ] && kill -0 "$_spid" 2>/dev/null; then
            kill "$_spid" 2>/dev/null
            echo "revtun: reaped orphaned ssh (pid $_spid)"
        fi
    fi

    rm -f "$PIDFILE" "$SSH_PIDFILE"
    rotate_log

    nohup "$0" __keeper >> "$LOG" 2>&1 &
    echo $! > "$PIDFILE"
    echo "revtun: started (pid $(cat "$PIDFILE")), log $LOG"
}

cmd_stop() {
    _stopped=0

    # Kill the keeper FIRST so it cannot respawn the ssh child.
    if [ -f "$PIDFILE" ]; then
        _pid=$(cat "$PIDFILE" 2>/dev/null)
        if [ -n "${_pid:-}" ] && kill -0 "$_pid" 2>/dev/null; then
            kill "$_pid" 2>/dev/null
            _stopped=1
        fi
        rm -f "$PIDFILE"
    fi

    if [ -f "$SSH_PIDFILE" ]; then
        _spid=$(cat "$SSH_PIDFILE" 2>/dev/null)
        if [ -n "${_spid:-}" ] && kill -0 "$_spid" 2>/dev/null; then
            kill "$_spid" 2>/dev/null
            _stopped=1
        fi
        rm -f "$SSH_PIDFILE"
    fi

    [ -d "$RT_DIR" ] && log "stopped by $(id -un)" >> "$LOG" 2>/dev/null

    if [ "$_stopped" = 1 ]; then
        echo "revtun: stopped"
    else
        echo "revtun: was not running"
    fi
    return 0
}

cmd_status() {
    if is_running; then
        echo "revtun: RUNNING (keeper pid $(cat "$PIDFILE"))"
        if [ -f "$SSH_PIDFILE" ]; then
            _spid=$(cat "$SSH_PIDFILE" 2>/dev/null)
            if [ -n "${_spid:-}" ] && kill -0 "$_spid" 2>/dev/null; then
                echo "revtun: ssh child pid $_spid (tunnel up)"
            else
                echo "revtun: ssh child not alive (keeper is between retries)"
            fi
        else
            echo "revtun: ssh child not alive (keeper is between retries)"
        fi
    else
        echo "revtun: STOPPED"
    fi
    echo "revtun: target ${VPS_USER}@${VPS_HOST} ${REMOTE_BIND}:${REMOTE_PORT} -> ${LOCAL_TARGET}"
    if [ -f "$LOG" ]; then
        echo "--- last 10 log lines ($LOG) ---"
        tail -n 10 "$LOG"
    fi
    is_running
}

case "${1:-}" in
    start)    cmd_start ;;
    stop)     cmd_stop ;;
    status)   cmd_status ;;
    restart)  cmd_stop; cmd_start ;;
    __keeper) keeper_loop ;;     # internal — invoked by cmd_start under nohup
    *)
        echo "usage: $0 {start|stop|status|restart}" >&2
        exit 2
        ;;
esac
