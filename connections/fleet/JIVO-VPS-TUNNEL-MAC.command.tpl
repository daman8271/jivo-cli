#!/bin/bash
# ============================================================================
#  JIVO VPS TUNNEL (macOS) — double-click this file. That's it.
#
#  Makes this Mac permanently reachable by Daman's Mac Air, from anywhere,
#  WITHOUT Tailscale and WITHOUT any password on our side.
#
#  How: the Mac dials OUT to the JIVO VPS and parks a private door there.
#  Outbound is never firewalled, so office/home/hotspot all work. Nothing is
#  exposed to the public internet — the door is on the VPS's loopback only.
#
#  Idempotent: safe to run again any time.
# ============================================================================
set -u

# --- self-elevate: macOS has no UAC, it asks for your login password --------
if [ "$(id -u)" -ne 0 ]; then
  echo
  echo "  Administrator access needed — type your Mac login password."
  echo "  (Nothing is shown as you type. That's normal.)"
  echo
  exec sudo -p "  Password for %u: " /bin/bash "$0" "$@"
fi

VPS='root@187.127.129.132'
DIR='/usr/local/jivo-revtun'
REGKEY_B64='@@REGKEY_B64@@'
MANAGER_KEYS=(
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB8+FPQ9luiwWsPUSZDY5UTwEiOVmL1o1zgf4sw1UORA daman8271@github'
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHR8F2rqvcl7hHaAmpmXd3uogcx0AUflmMvlAART0JNK hermes-agent-access'
)
# The account Daman will log in AS. Defaults to whoever ran this (not root).
TARGET_USER="${SUDO_USER:-$(stat -f%Su /dev/console)}"
TARGET_HOME="$(/usr/bin/dscl . -read "/Users/$TARGET_USER" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
[ -n "$TARGET_HOME" ] || TARGET_HOME="/Users/$TARGET_USER"

OK=(); BAD=()
step(){ n="$1"; shift; if "$@"; then OK+=("$n"); else BAD+=("$n"); fi; }

echo
echo "  === JIVO VPS TUNNEL SETUP (macOS) ==="
echo "  About a minute. Leave this window open."
echo

# ---- 1. Remote Login (the door the tunnel lands on) ------------------------
# `systemsetup -setremotelogin` needs Full Disk Access on 10.14+ and fails
# silently from a plain Terminal. launchctl is the reliable path; we try both
# and VERIFY rather than trusting either.
enable_ssh(){
  if systemsetup -getremotelogin 2>/dev/null | grep -qi 'On'; then return 0; fi
  systemsetup -setremotelogin on >/dev/null 2>&1
  launchctl enable system/com.openssh.sshd >/dev/null 2>&1
  launchctl bootstrap system /System/Library/LaunchDaemons/ssh.plist >/dev/null 2>&1
  systemsetup -getremotelogin 2>/dev/null | grep -qi 'On'
}
step 'remote-login' enable_ssh

# ---- 2. manager key, so Daman can log in once the tunnel is up -------------
install_manager_key(){
  local d="$TARGET_HOME/.ssh" f
  mkdir -p "$d" || return 1
  f="$d/authorized_keys"; touch "$f" || return 1
  # APPEND only — this file may already hold other keys.
  local k
  for k in "${MANAGER_KEYS[@]}"; do
    grep -qF "$k" "$f" || printf '%s\n' "$k" >> "$f"
  done
  chown -R "$TARGET_USER" "$d" && chmod 700 "$d" && chmod 600 "$f"
}
step 'manager-key' install_manager_key

# ---- 3. this Mac's OWN tunnel key. Private half never travels --------------
TUNKEY="$DIR/id_ed25519"
make_key(){
  mkdir -p "$DIR" && chown root:wheel "$DIR" && chmod 700 "$DIR" || return 1
  [ -f "$TUNKEY" ] || ssh-keygen -t ed25519 -N '' -f "$TUNKEY" -C "revtun-$(hostname -s)" -q || return 1
  chown root:wheel "$TUNKEY" "$TUNKEY.pub" && chmod 600 "$TUNKEY"
}
step 'tunnel-key' make_key

# ---- 4. register with the VPS -> permanent private port -------------------
PORT=''
register(){
  local rk="$DIR/reg_key" pub pubb host user out
  printf '%s' "$REGKEY_B64" | base64 -D > "$rk" 2>/dev/null || printf '%s' "$REGKEY_B64" | base64 -d > "$rk" || return 1
  chmod 600 "$rk"; chown root:wheel "$rk"
  pub="$(cat "$TUNKEY.pub")"
  pubb="$(printf '%s' "$pub" | base64 | tr -d '\n')"
  # The registrar only accepts [A-Za-z0-9._-]; sanitise or it refuses.
  # Capture FIRST, then sanitise: piping `hostname -s` straight into tr feeds the
  # trailing newline in, and tr turns it into a stray '_' on the end of the name.
  # `hostname -s` on macOS is NOT stable: when DHCP hands out a name the machine
  # reports something like 192.168.1.5, which truncates to "192". Measured on the
  # Mac Air, which registered as host "192". That is not unique -- ANY Mac on a
  # 192.168.x.x network reports the same, and since the registrar is keyed by HOST
  # the second one would seize the first one's port and replace its key.
  # LocalHostName / ComputerName are user-set and stable; fall back to the hardware
  # UUID rather than ever registering a name that cannot identify one machine.
  host="$(scutil --get LocalHostName 2>/dev/null)"
  [ -n "$host" ] || host="$(scutil --get ComputerName 2>/dev/null)"
  [ -n "$host" ] || host="$(hostname -s)"
  host="$(printf '%s' "$host" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-64)"
  if printf '%s' "$host" | grep -qE '^[0-9._-]*$' || [ "${#host}" -lt 3 ]; then
    uuid="$(ioreg -rd1 -c IOPlatformExpertDevice 2>/dev/null | awk -F'\"' '/IOPlatformUUID/{print $4}' | tr -d '-' | cut -c1-8)"
    host="mac-${uuid:-$$}"
  fi
  user="$(printf '%s' "$TARGET_USER" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-64)"
  out="$(ssh -n -i "$rk" -o IdentitiesOnly=yes -o BatchMode=yes \
           -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 \
           "$VPS" "HOST=$host USER=$user KEY=$pubb" 2>&1)"
  rm -f "$rk"                      # registrar key is never kept on the box
  PORT="$(printf '%s' "$out" | sed -n 's/.*PORT=\([0-9][0-9]*\).*/\1/p' | head -1)"
  [ -n "$PORT" ] || { echo "  registrar said: $out"; return 1; }
  echo "  VPS assigned this Mac port $PORT"
}
step 'register-with-vps' register

# ---- 5. the dialer, supervised by launchd ---------------------------------
# launchd's KeepAlive IS the supervisor: when the ssh exits, launchd restarts
# it immediately. No polling task, no lock file, no cron — this is why the mac
# side is simpler than the Windows one and recovers faster.
PLIST='/Library/LaunchDaemons/com.jivo.revtun.plist'
install_daemon(){
  [ -n "$PORT" ] || return 1
  cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.jivo.revtun</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/ssh</string>
    <string>-N</string><string>-T</string><string>-n</string>
    <string>-o</string><string>ServerAliveInterval=30</string>
    <string>-o</string><string>ServerAliveCountMax=3</string>
    <string>-o</string><string>ExitOnForwardFailure=yes</string>
    <string>-o</string><string>StrictHostKeyChecking=accept-new</string>
    <string>-o</string><string>BatchMode=yes</string>
    <string>-o</string><string>IdentitiesOnly=yes</string>
    <string>-o</string><string>ConnectTimeout=15</string>
    <string>-i</string><string>$TUNKEY</string>
    <string>-R</string><string>127.0.0.1:$PORT:localhost:22</string>
    <string>$VPS</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>15</integer>
  <key>StandardOutPath</key><string>$DIR/revtun.log</string>
  <key>StandardErrorPath</key><string>$DIR/revtun.log</string>
</dict>
</plist>
PLISTEOF
  chown root:wheel "$PLIST" && chmod 644 "$PLIST" || return 1
  plutil -lint "$PLIST" >/dev/null || return 1     # never load a malformed plist
  launchctl bootout system "$PLIST" >/dev/null 2>&1 || true
  launchctl bootstrap system "$PLIST" >/dev/null 2>&1 || launchctl load -w "$PLIST" >/dev/null 2>&1
  launchctl kickstart -k system/com.jivo.revtun >/dev/null 2>&1 || true
}
step 'install-dialer' install_daemon

# ---- 6. always-on ---------------------------------------------------------
harden(){
  # On a desktop this is free. On a laptop `disablesleep` would keep it awake on
  # battery and flatten it, so that one is only set when there is no battery.
  pmset -a sleep 0 disksleep 0 displaysleep 0 womp 1 >/dev/null 2>&1
  if ! pmset -g batt 2>/dev/null | grep -qi 'InternalBattery'; then
    pmset -a disablesleep 1 >/dev/null 2>&1
  fi
  # watchdog: launchd already restarts the dialer, so this only repairs what
  # launchd cannot — the daemon being unloaded, Remote Login switched off, or
  # pmset drifting back after a macOS update.
  cat > "$DIR/watchdog.sh" <<WDEOF
#!/bin/bash
log=$DIR/watchdog.log
[ -f "\$log" ] && [ "\$(stat -f%z "\$log")" -gt 1048576 ] && mv -f "\$log" "\$log.1"
pmset -a sleep 0 disksleep 0 displaysleep 0 womp 1 >/dev/null 2>&1
systemsetup -getremotelogin 2>/dev/null | grep -qi 'On' || systemsetup -setremotelogin on >/dev/null 2>&1
if ! launchctl print system/com.jivo.revtun >/dev/null 2>&1; then
  echo "\$(date -u +%FT%TZ) daemon not loaded - bootstrapping" >> "\$log"
  launchctl bootstrap system $PLIST >/dev/null 2>&1 || launchctl load -w $PLIST >/dev/null 2>&1
fi
WDEOF
  chmod 755 "$DIR/watchdog.sh"
  cat > /Library/LaunchDaemons/com.jivo.revtun.watchdog.plist <<WPEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.jivo.revtun.watchdog</string>
  <key>ProgramArguments</key><array><string>$DIR/watchdog.sh</string></array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>900</integer>
</dict>
</plist>
WPEOF
  chown root:wheel /Library/LaunchDaemons/com.jivo.revtun.watchdog.plist
  chmod 644 /Library/LaunchDaemons/com.jivo.revtun.watchdog.plist
  plutil -lint /Library/LaunchDaemons/com.jivo.revtun.watchdog.plist >/dev/null || return 1
  launchctl bootout system /Library/LaunchDaemons/com.jivo.revtun.watchdog.plist >/dev/null 2>&1 || true
  launchctl bootstrap system /Library/LaunchDaemons/com.jivo.revtun.watchdog.plist >/dev/null 2>&1 \
    || launchctl load -w /Library/LaunchDaemons/com.jivo.revtun.watchdog.plist >/dev/null 2>&1
  return 0
}
step 'harden-always-on' harden

# ---- 7. verify ------------------------------------------------------------
TUNNEL='down'
for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
  sleep 5
  if pgrep -f "127.0.0.1:${PORT:-none}:localhost:22" >/dev/null 2>&1; then TUNNEL='UP'; break; fi
done

echo
echo "  =========== SEND THIS BLOCK BACK ==========="
echo "  COMPUTERNAME : $(hostname -s)"
echo "  USERNAME     : $TARGET_USER"
echo "  VPS PORT     : ${PORT:-NOT ASSIGNED}"
echo "  MACOS        : $(sw_vers -productVersion)"
echo "  REMOTE LOGIN : $(systemsetup -getremotelogin 2>/dev/null | sed 's/.*: //')"
echo "  TUNNEL       : $TUNNEL"
echo "  ALWAYS-ON    : sleep off, launchd KeepAlive, watchdog every 15 min"
echo "  STEPS OK     : ${OK[*]:-none}"
[ ${#BAD[@]} -gt 0 ] && echo "  FAILED       : ${BAD[*]}"
echo "  ============================================"
echo
[ ${#BAD[@]} -gt 0 ] && echo "  If 'remote-login' failed: System Settings -> General -> Sharing -> turn ON Remote Login, then re-run."
echo "  Press return to close."
read -r _ || true
