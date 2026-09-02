#!/usr/bin/env bash
# jwa-health — is the WhatsApp reader still linked and connected?
#
# Cron, every 10 minutes. Reads only the two files the daemon writes
# (~/.jwa/state and ~/.jwa/heartbeat) plus systemd — it never opens session.db.
# Alerts Telegram once when the verdict flips to DOWN and once when it comes
# back; a failed alert is retried next tick because the last-verdict file is
# only written after the message went out.
#
#   JWA_HOME    where the daemon keeps its files      (default ~/.jwa)
#   JWA_NOTIFY  command that takes the message as $1  (default: the VPS's
#               telegram_helper.py, the same channel as the Mac Pro dead-man)
set -u
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}"

home="${JWA_HOME:-$HOME/.jwa}"
state_f="$home/state"; hb_f="$home/heartbeat"; last_f="$home/.health-last"
notify="${JWA_NOTIFY:-python3 /root/telegram_helper.py send}"
stale=300   # seconds without a heartbeat before it counts as dead

now=$(date +%s)
unit=$(systemctl --user is-active jwa 2>/dev/null || true); unit=${unit:-unknown}
state=$(sed -n 's/^state=//p' "$state_f" 2>/dev/null); state=${state:-none}
since=$(sed -n 's/^since=//p' "$state_f" 2>/dev/null)
detail=$(sed -n 's/^detail=//p' "$state_f" 2>/dev/null)
hb_age=999999
[ -f "$hb_f" ] && hb_age=$(( now - $(stat -c %Y "$hb_f") ))

verdict=OK; why=""
case "$state" in
    logged_out|banned|outdated|replaced|unlinked) verdict=DOWN; why="$state — $detail" ;;
esac
if [ "$verdict" = OK ] && [ "$unit" != active ]; then
    verdict=DOWN; why="jwa.service is $unit"
fi
if [ "$verdict" = OK ] && [ "$hb_age" -gt "$stale" ]; then
    verdict=DOWN; why="no heartbeat for $((hb_age / 60)) min (state=$state${detail:+ — $detail})"
fi

prev=$(cat "$last_f" 2>/dev/null || echo OK)
if [ "$verdict" != "$prev" ]; then
    if [ "$verdict" = DOWN ]; then
        msg="🔴 jwa WhatsApp reader DOWN on $(hostname): $why"
    else
        msg="🟢 jwa WhatsApp reader back on $(hostname): $state since $since"
    fi
    if $notify "$msg" >/dev/null 2>&1; then
        echo "$verdict" > "$last_f"
    else
        echo "$(date +%FT%T) ALERT FAILED: $msg" >&2
    fi
fi
echo "$(date +%FT%T) $verdict unit=$unit state=$state hb_age=${hb_age}s${why:+ — $why}"
