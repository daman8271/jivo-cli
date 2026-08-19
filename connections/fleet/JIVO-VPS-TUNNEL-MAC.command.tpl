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

# Stamped by build-tunnel-installer.sh from the commit this was built at. The
# Windows side got a version on 2026-08-17, after three boxes turned out to be
# running an OLD installer that prints an identical green OK and repairs
# nothing. The Mac side was left unstamped, so a Mac's "it says OK" had exactly
# the same hole in it and nobody had noticed. Same lesson, both platforms.
TUNNEL_VER='@@VERSION@@'

# Same reason the Windows side keeps a Start-Transcript: a colleague sends a
# photo of the summary block and every detail behind it is gone. Tee the lot to
# their Desktop so there is something to read afterwards.
LOG="$TARGET_HOME/Desktop/jivo-vps-tunnel-log.txt"
: > "$LOG" 2>/dev/null || LOG=/tmp/jivo-vps-tunnel-log.txt
exec > >(tee "$LOG") 2>&1

# The name this Mac registers under, computed ONCE and reused by the VERIFY call
# at the end — send a different string there and the VPS looks up a different
# machine's port and answers about someone else's box.
# `hostname -s` on macOS is NOT stable: when DHCP hands out a name the machine
# reports something like 192.168.1.5, which truncates to "192". Measured on the
# Mac Air, which registered as host "192". That is not unique — ANY Mac on a
# 192.168.x.x network reports the same, and since the registrar is keyed by HOST
# the second one would seize the first one's port and replace its key.
# LocalHostName / ComputerName are user-set and stable; fall back to the hardware
# UUID rather than ever registering a name that cannot identify one machine.
HOSTTAG="$(scutil --get LocalHostName 2>/dev/null)"
[ -n "$HOSTTAG" ] || HOSTTAG="$(scutil --get ComputerName 2>/dev/null)"
[ -n "$HOSTTAG" ] || HOSTTAG="$(hostname -s)"
# Capture FIRST, then sanitise: piping `hostname -s` straight into tr feeds the
# trailing newline in, and tr turns it into a stray '_' on the end of the name.
HOSTTAG="$(printf '%s' "$HOSTTAG" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-64)"
if printf '%s' "$HOSTTAG" | grep -qE '^[0-9._-]*$' || [ "${#HOSTTAG}" -lt 3 ]; then
  uuid="$(ioreg -rd1 -c IOPlatformExpertDevice 2>/dev/null | awk -F'"' '/IOPlatformUUID/{print $4}' | tr -d '-' | cut -c1-8)"
  HOSTTAG="mac-${uuid:-$$}"
fi

OK=(); BAD=()
# step() used to record a bare pass/fail and THROW THE REASON AWAY — worse than
# the Windows side, which at least kept the exception message. "FAILED:
# remote-login" with no reason is a phone call to the operator and a guess.
# Output is captured to a FILE, never with $( ), because these functions set
# variables the rest of the script depends on — PORT above all — and a command
# substitution runs them in a subshell where those assignments quietly vanish.
step(){
  local n="$1"; shift
  local tmp rc why
  tmp="$(mktemp -t jivostep)"
  "$@" >"$tmp" 2>&1; rc=$?
  [ -s "$tmp" ] && sed 's/^/  /' "$tmp"
  if [ "$rc" -eq 0 ]; then
    OK+=("$n")
  else
    why="$(tr '\n' ' ' < "$tmp" | tr -s ' ' | cut -c1-220)"
    [ -n "$why" ] || why='failed, and said nothing'
    BAD+=("$n -> $why")
  fi
  rm -f "$tmp"
}

# Is anything actually LISTENING on 22? `systemsetup -getremotelogin` saying On
# is the macOS twin of Windows' "the service is Running": it describes a setting,
# not a socket. Read the banner or believe nothing.
sshd_answers(){
  local b
  b="$( { exec 3<>/dev/tcp/127.0.0.1/22 && IFS= read -r -t 4 b <&3 && printf '%s' "$b"; } 2>/dev/null )"
  case "$b" in SSH-*) return 0 ;; *) return 1 ;; esac
}

# One call to the VPS registrar. The registrar key is written, used and WIPED on
# every call — it never sits on this Mac between calls, which is the whole point
# of generating the tunnel key locally.
registrar_call(){
  local rk="$DIR/reg_key" out
  mkdir -p "$DIR"
  printf '%s' "$REGKEY_B64" | base64 -D > "$rk" 2>/dev/null || printf '%s' "$REGKEY_B64" | base64 -d > "$rk" || return 1
  chmod 600 "$rk"; chown root:wheel "$rk"
  out="$(ssh -n -i "$rk" -o IdentitiesOnly=yes -o BatchMode=yes \
           -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "$VPS" "$1" 2>&1)"
  rm -f "$rk"
  printf '%s' "$out"
}

echo
echo "  === JIVO VPS TUNNEL SETUP (macOS) ==="
echo "  About a minute. Leave this window open."
echo

# ---- 1. Remote Login (the door the tunnel lands on) ------------------------
# `systemsetup -setremotelogin` needs Full Disk Access on 10.14+ and on 13+ it
# refuses outright from a plain Terminal with a message that says exactly that.
# The old version sent all three commands to /dev/null and returned a bare 1, so
# the entire diagnosis was the word "remote-login". Now each route REPORTS WHAT
# IT WAS TOLD — and none of them is believed: the only thing that ends this
# function successfully is a real SSH banner off 127.0.0.1:22.
enable_ssh(){
  local out
  if sshd_answers; then echo "already answering on 127.0.0.1:22"; return 0; fi
  # route 1 — the documented one. -f so it can never sit waiting on a prompt.
  out="$(systemsetup -f -setremotelogin on 2>&1)"
  echo "systemsetup: ${out:-no output}"
  sshd_answers && return 0
  # route 2 — launchd directly. This is what works when systemsetup is blocked
  # by TCC, the usual failure on macOS 13+ ("requires Full Disk Access").
  out="$(launchctl enable system/com.openssh.sshd 2>&1)"
  out="$out; $(launchctl bootstrap system /System/Library/LaunchDaemons/ssh.plist 2>&1)"
  echo "launchctl: ${out:-no output}"
  sshd_answers && return 0
  # route 3 — the legacy verb plus a forced restart, for older macOS and for a
  # job that is loaded but wedged (bootstrap says "already loaded" and stops).
  out="$(launchctl load -w /System/Library/LaunchDaemons/ssh.plist 2>&1)"
  out="$out; $(launchctl kickstart -k system/com.openssh.sshd 2>&1)"
  echo "load/kickstart: ${out:-no output}"
  sshd_answers && return 0
  echo "nothing answers on port 22 after all three routes"
  return 1
}
step 'remote-login' enable_ssh

# macOS can restrict Remote Login to one group. If com.apple.access_ssh exists
# and this user is not in it, key auth is refused — and the Mac is unreachable
# with Remote Login "On", the tunnel up, and nothing on screen to say so. Same
# shape as the Windows administrators_authorized_keys trap.
ssh_access(){
  dseditgroup -o read com.apple.access_ssh >/dev/null 2>&1 || { echo "no SSH access group — all users allowed"; return 0; }
  if dseditgroup -o checkmember -m "$TARGET_USER" com.apple.access_ssh 2>/dev/null | grep -qi '^yes'; then
    echo "$TARGET_USER is already allowed"; return 0
  fi
  dseditgroup -o edit -a "$TARGET_USER" -t user com.apple.access_ssh 2>&1 || return 1
  echo "added $TARGET_USER to com.apple.access_ssh"
}
step 'ssh-access-list' ssh_access

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
  # Which build last ran here, readable over the tunnel:
  #   ssh <mac> "cat /usr/local/jivo-revtun/version.txt"
  # A photo of the summary block can be cropped, stale, or of the wrong window.
  # This cannot. Written early so it lands even if a later step fails — knowing
  # WHICH build failed is exactly what you need when one does.
  printf '%s  installed %s  by %s\n' "$TUNNEL_VER" "$(date -u +%FT%TZ)" "$TARGET_USER" > "$DIR/version.txt"
  [ -f "$TUNKEY" ] || ssh-keygen -t ed25519 -N '' -f "$TUNKEY" -C "revtun-$HOSTTAG" -q || return 1
  chown root:wheel "$TUNKEY" "$TUNKEY.pub" && chmod 600 "$TUNKEY"
}
step 'tunnel-key' make_key

# ---- 4. register with the VPS -> permanent private port -------------------
PORT=''
register(){
  local pub pubb user out
  pub="$(cat "$TUNKEY.pub")"
  pubb="$(printf '%s' "$pub" | base64 | tr -d '\n')"
  # The registrar only accepts [A-Za-z0-9._-]; sanitise or it refuses.
  user="$(printf '%s' "$TARGET_USER" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-64)"
  out="$(registrar_call "HOST=$HOSTTAG USER=$user KEY=$pubb")"
  PORT="$(printf '%s' "$out" | sed -n 's/.*PORT=\([0-9][0-9]*\).*/\1/p' | head -1)"
  [ -n "$PORT" ] || { echo "registrar said: $out"; return 1; }
  echo "VPS assigned this Mac port $PORT"
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
# Probe the PORT, not the setting. A getremotelogin of On is perfectly true on a
# Mac where sshd is not listening — that is the state that makes a box look
# healthy and be unreachable, and the old line here could not see it.
sshd_answers(){ local b; b="\$( { exec 3<>/dev/tcp/127.0.0.1/22 && IFS= read -r -t 4 b <&3 && printf '%s' "\$b"; } 2>/dev/null )"; case "\$b" in SSH-*) return 0 ;; *) return 1 ;; esac; }
if ! sshd_answers; then
  echo "\$(date -u +%FT%TZ) nothing answering on 22 - re-enabling Remote Login" >> "\$log"
  systemsetup -f -setremotelogin on >/dev/null 2>&1
  launchctl enable system/com.openssh.sshd >/dev/null 2>&1
  launchctl bootstrap system /System/Library/LaunchDaemons/ssh.plist >/dev/null 2>&1
  launchctl kickstart -k system/com.openssh.sshd >/dev/null 2>&1
fi
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

# ---- 8. PROVE it from the OUTSIDE. The only check that has ever mattered. --
# Everything above this line is this Mac marking its own homework: a setting it
# can read, a process it can see. Both are true on a machine nobody can log in
# to — that is how JIVO201, 23011 and 23009 each burned days on the Windows
# side. Ask the VPS to come back DOWN the tunnel and read a real SSH banner off
# port 22 instead. That cannot succeed unless the tunnel is parked AND sshd
# answers, so it is the one line below a photograph can be trusted on.
REACH='not checked'
verify_reachable(){
  local i r
  [ -n "$PORT" ] || { echo "no port was assigned, so there is nothing to verify"; return 1; }
  for i in 1 2 3 4; do
    r="$(registrar_call "VERIFY HOST=$HOSTTAG")"
    case "$r" in
      *REACHABLE=yes*) REACH='yes'; return 0 ;;
      *REACHABLE=no*)  REACH="NO - $(printf '%s' "$r" | sed -n 's/.*REASON=\([^ ]*\).*/\1/p')" ;;
      *ERR=*)          REACH="unknown - registrar said $(printf '%s' "$r" | sed -n 's/.*ERR=\([^ ]*\).*/\1/p')" ;;
      *)               REACH="unknown - $r" ;;
    esac
    sleep 8
  done
  echo "the VPS could not reach this Mac back: $REACH"
  return 1
}
step 'verify-reachable' verify_reachable

echo
echo "  =========== SEND THIS BLOCK BACK ==========="
# VERSION FIRST, deliberately: it is the one line that tells the reader whether
# to trust the rest of the block. An old build prints an identical-looking OK.
echo "  VERSION      : $TUNNEL_VER"
echo "  COMPUTERNAME : $HOSTTAG"
echo "  USERNAME     : $TARGET_USER"
echo "  VPS PORT     : ${PORT:-NOT ASSIGNED}"
echo "  MACOS        : $(sw_vers -productVersion)"
echo "  REMOTE LOGIN : $(systemsetup -getremotelogin 2>/dev/null | sed 's/.*: //')"
echo "  TUNNEL       : $TUNNEL"
# The verdict. Every line above describes a part; this one describes the whole,
# measured from the far end.
if [ "$REACH" = yes ]; then
  echo "  REACHABLE    : YES - the VPS read this Mac's SSH banner back down the tunnel"
else
  echo "  REACHABLE    : $REACH  <-- NOBODY CAN LOG IN TO THIS MAC"
fi
echo "  ALWAYS-ON    : sleep off, launchd KeepAlive, watchdog every 15 min"
echo "  STEPS OK     : ${OK[*]:-none}"
if [ ${#BAD[@]} -gt 0 ]; then
  echo "  FAILED       :"
  for _b in "${BAD[@]}"; do echo "     $_b"; done
  echo "  Full log on your Desktop: jivo-vps-tunnel-log.txt"
fi
echo "  ============================================"
echo
if [ ${#BAD[@]} -gt 0 ]; then
  echo "  If 'remote-login' failed: System Settings -> General -> Sharing -> turn ON"
  echo "  Remote Login, then re-run this file. The line after each route name above"
  echo "  is what macOS actually said - send that too."
fi
chown "$TARGET_USER" "$LOG" 2>/dev/null || true
echo "  Press return to close."
read -r _ || true
