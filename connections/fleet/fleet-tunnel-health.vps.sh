#!/usr/bin/env bash
# ============================================================================
#  fleet-tunnel-health.sh — runs ON THE VPS, every 10 min via cron.
#
#  WHY THIS EXISTS
#  ---------------
#  Every reverse tunnel is self-healing on the box (1-min dialer + 15-min
#  watchdog), so the failure we actually hit is not "the tunnel dropped" — it
#  is "the tunnel stayed down and NOBODY KNEW". DESKTOP-5VCMOAS (Manav, 23005)
#  died at 04:23 on 2026-08-11 and was discovered 13.5 h later, by hand, when
#  someone needed the box. Nothing on the VPS was watching port 230xx.
#
#  So: compare who is REGISTERED against who is actually LISTENING, remember
#  how long each has been gone, and shout once when a box is properly dead.
#
#  NOISE IS THE ENEMY. Office PCs are switched off every night; alerting on
#  that trains everyone to ignore the alerts. Hence:
#    - a box must be down longer than ALERT_AFTER_MIN (default 4 h), AND
#    - the alert only fires inside working hours (10:00-19:00 IST),
#  so an overnight shutdown is silent while a genuinely dead box is reported
#  the morning after. Cooldown stops repeat nagging.
#
#  Reads nothing but the tunnel registry and the kernel's listen table. Writes
#  only its own state/log/status files. Sends no business data anywhere.
#
#  Manual use:
#      /root/bin/fleet-tunnel-health.sh          # check + alert if due
#      /root/bin/fleet-tunnel-health.sh report   # print status, never alerts
#      cat /root/fleet-tunnel-status.txt         # last computed state
# ============================================================================
set -u

DB=/root/fleet-tunnels.txt                 # HOST PORT USER REGISTERED_AT
STATE=/root/.fleet-tunnel-state.tsv        # HOST STATE DOWN_SINCE LAST_ALERT
STATUS=/root/fleet-tunnel-status.txt       # human-readable snapshot
LOG=/root/fleet-tunnel-health.log
TG=/root/telegram_helper.py

ALERT_AFTER_MIN=${ALERT_AFTER_MIN:-240}    # 4 h down before it counts as dead
COOLDOWN_MIN=${COOLDOWN_MIN:-720}          # 12 h between repeat alerts per host
HOUR_FROM=${HOUR_FROM:-10}                 # alert window (VPS clock is IST)
HOUR_TO=${HOUR_TO:-19}
DISK_WARN_PCT=${DISK_WARN_PCT:-85}

MODE=${1:-check}
NOW=$(date +%s)
HOUR=$(date +%-H)
TS=$(date '+%Y-%m-%d %H:%M:%S')

notify() {   # never let a broken notifier break the check
  [ -x "$TG" ] || [ -f "$TG" ] || return 0
  python3 "$TG" send "$1" >/dev/null 2>&1 || echo "$TS notify-failed" >> "$LOG"
}

in_alert_window() { [ "$HOUR" -ge "$HOUR_FROM" ] && [ "$HOUR" -le "$HOUR_TO" ]; }

# ---- who is actually listening right now -----------------------------------
# The dialer parks a listener on 127.0.0.1:<port>. Present = tunnel is up.
live_ports=$(ss -tlnH 2>/dev/null | awk '{print $4}' | grep -oE ':(230[0-9][0-9])$' | tr -d ':' | sort -u)
is_live() { printf '%s\n' "$live_ports" | grep -qx "$1"; }

[ -f "$STATE" ] || : > "$STATE"
new_state=$(mktemp) || exit 1
down_list=""; recovered_list=""; up_n=0; down_n=0

while read -r host port user reg; do
  [ -n "${host:-}" ] || continue
  case "$host" in \#*) continue ;; esac

  prev_line=$(grep -P "^\Q$host\E\t" "$STATE" 2>/dev/null | head -1)
  prev_state=$(printf '%s' "$prev_line" | cut -f2)
  prev_since=$(printf '%s' "$prev_line" | cut -f3)
  prev_alert=$(printf '%s' "$prev_line" | cut -f4)
  [ -n "${prev_since:-}" ] || prev_since=0
  [ -n "${prev_alert:-}" ] || prev_alert=0

  if is_live "$port"; then
    up_n=$((up_n+1))
    # Recovery is only worth announcing if we actually raised the alarm.
    if [ "${prev_state:-}" = "DOWN" ] && [ "$prev_alert" -gt 0 ]; then
      down_for=$(( (NOW - prev_since) / 60 ))
      recovered_list="$recovered_list\n  $host ($port) back after ${down_for}m"
    fi
    printf '%s\tUP\t0\t0\n' "$host" >> "$new_state"
    printf '%-28s %-6s UP\n' "$host" "$port" >> "$STATUS.tmp"
  else
    down_n=$((down_n+1))
    since=$prev_since
    [ "${prev_state:-}" = "DOWN" ] && [ "$since" -gt 0 ] || since=$NOW
    down_min=$(( (NOW - since) / 60 ))
    alert_at=$prev_alert

    if [ "$down_min" -ge "$ALERT_AFTER_MIN" ] \
       && in_alert_window \
       && [ $(( (NOW - prev_alert) / 60 )) -ge "$COOLDOWN_MIN" ]; then
      down_list="$down_list\n  $host ($port, $user) — down ${down_min}m"
      alert_at=$NOW
    fi
    printf '%s\tDOWN\t%s\t%s\n' "$host" "$since" "$alert_at" >> "$new_state"
    printf '%-28s %-6s DOWN  since %s (%dm)\n' \
      "$host" "$port" "$(date -d "@$since" '+%m-%d %H:%M' 2>/dev/null)" "$down_min" >> "$STATUS.tmp"
  fi
done < "$DB"

{ echo "fleet tunnel status @ $TS   ($up_n up, $down_n down)"; sort "$STATUS.tmp" 2>/dev/null; } > "$STATUS"
rm -f "$STATUS.tmp"

if [ "$MODE" = report ]; then cat "$STATUS"; rm -f "$new_state"; exit 0; fi
mv "$new_state" "$STATE"

echo "$TS up=$up_n down=$down_n" >> "$LOG"

[ -n "$down_list" ]      && notify "$(printf 'JIVO fleet — tunnel DOWN:%b\n\nFix: on that PC, double-click JIVO-VPS-TUNNEL.cmd (idempotent), or run: schtasks /Run /TN JivoRevTunnel' "$down_list")"
[ -n "$recovered_list" ] && notify "$(printf 'JIVO fleet — tunnel recovered:%b' "$recovered_list")"

# ---- disk guard -------------------------------------------------------------
# A full VPS root disk is a fleet-wide outage: the registrar cannot append to
# authorized_keys, so no NEW box can ever enrol. On 2026-08-10 a leaked temp
# directory in the hermes container filled all 193 GB and it was found only by
# a stray "No space left on device" from an unrelated command.
DISK_PCT=$(df --output=pcent / 2>/dev/null | tail -1 | tr -dc '0-9')
DISK_STAMP=/root/.fleet-disk-alert
if [ -n "${DISK_PCT:-}" ] && [ "$DISK_PCT" -ge "$DISK_WARN_PCT" ]; then
  last=$(cat "$DISK_STAMP" 2>/dev/null || echo 0)
  if [ $(( (NOW - last) / 60 )) -ge "$COOLDOWN_MIN" ]; then
    notify "JIVO VPS disk ${DISK_PCT}% full ($(df -h / | awk 'NR==2{print $4}') left). Biggest: $(du -xsh /root /var 2>/dev/null | tr '\n' ' ')"
    echo "$NOW" > "$DISK_STAMP"
  fi
  echo "$TS disk=${DISK_PCT}%" >> "$LOG"
fi

tail -n 2000 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
exit 0
