#!/usr/bin/env bash
# ============================================================================
#  ##########################################################################
#  ##  NOT DEPLOYED. DO NOT CRON THIS YET.  Reviewed 2026-08-17 and held.  ##
#  ##########################################################################
#
#  An adversarial review on 2026-08-17 confirmed the craft is sound — the
#  stdin-swallow trap is closed (arrays + `ssh -n`, 3/3 hosts processed), flock
#  prevents overlap, every ssh/scp carries BatchMode and an explicit timeout, the
#  identity guard refuses a wrong-answering box, and the stale-stamp bug really is
#  designed out (completion = live UP, never registry presence). It found four
#  blockers anyway. Fix these before the crontab line below is ever added:
#
#   1. ESCALATION THE HEADER DENIES. Lines 42-44 claim this never writes
#      /root/.ssh/authorized_keys or /root/fleet-tunnels.txt. True of its own file
#      handles, false in effect: phase 2 runs JIVO-VPS-TUNNEL.cmd, whose
#      register-with-vps step drives the registrar, which rewrites both. The same
#      installer flips power settings, NIC PnPCapabilities, DefaultShell and key
#      ACLs, and can download+msiexec OpenSSH from GitHub. As a root cron holding
#      admin SSH to every enrolled box, that is a large blast radius to hand a
#      loop that fires every 10 minutes.
#   2. THE BROKEN-STATE GATE IS TOO LOOSE. The primary parser accepts any token
#      that is neither UP nor empty (the $HSTATUS fallback validates, the primary
#      does not), so a garbage state string makes a box a repair candidate.
#      Measured with a fixture: state WEIRD-JUNK became a candidate.
#   3. `plan` IS NOT READ-ONLY. The enable check sits AFTER the hostname and uname
#      probes, so the mode the install header tells you to soak with SSHes into
#      every candidate box and overwrites the production status file. Measured.
#   4. STATE FILE LOADED UNVALIDATED. Config knobs are validated at length; the
#      script's own state file is not. Measured `[: q: integer expression
#      expected`, which silently skips the PARK and COOLDOWN checks — and the
#      prescribed crontab discards stderr, so it is guaranteed invisible.
#
#  Also, before this is useful at all: it resolves the Tailscale channel by
#  matching the registry hostname against plain `tailscale status` output, but on
#  this tailnet the Tailscale name is NOT the Windows hostname (diljeet-singh IS
#  JIVO-B1, khushvinder-dev-veerji IS HO-IT-PC10). Match HostName/DNSName from
#  `tailscale status --json` instead. And the registry's USER field is unreliable:
#  it holds `khushwinder_singh` where the real account is `khushwinder singh`
#  (with a space) — verified 2026-08-17, the underscore form gets Permission
#  denied while the space form logs in. Any ssh command built from the registry
#  user will fail on that box.
#
#  On today's fleet it would also do nothing useful: all remaining broken boxes
#  have no reachable channel, so it would log a miss per box per cycle forever,
#  repair nothing, and A_MISS is uncapped with no alert path.
#  ============================================================================
#  fleet-auto-repair.sh — runs ON THE VPS, every 10 min via cron.
#  Repo copy: connections/fleet/fleet-auto-repair.vps.sh
#  Deploy to: /root/bin/fleet-auto-repair.sh   (chmod 755)
#
#  INSTALL (main session does this, after review — this script installs nothing):
#      scp connections/fleet/fleet-auto-repair.vps.sh vps:/root/bin/fleet-auto-repair.sh
#      ssh vps 'chmod 755 /root/bin/fleet-auto-repair.sh'
#      # soak first — decides and logs, touches no box:
#      ssh vps '/root/bin/fleet-auto-repair.sh plan; tail -40 /root/fleet-auto-repair.log'
#      # then add ONE crontab line (offset 5 min so it never races the health check):
#
#  5-59/10 * * * * /root/bin/fleet-auto-repair.sh >/dev/null 2>&1   # fleet tunnel auto-repair queue
#
#  ---------------------------------------------------------------------------
#  WHY THIS EXISTS
#  ---------------
#  /root/dev-tunnel-install.sh already does this — for exactly one machine
#  (HO-IT-PC10), hardcoded, and it has since disabled itself. This is that
#  mechanism generalised to every box in /root/fleet-tunnels.txt.
#
#  It also fixes the bug that killed the single-box version. dev-tunnel-install.sh
#  stops forever once ~/fleet-tunnels.txt contains a line for the host:
#
#      if grep -qi '^HO-IT-PC10 ' /root/fleet-tunnels.txt; then touch $STAMP; exit 0
#
#  But that file records that a box ENROLLED ONCE. It never says the box is up.
#  HO-IT-PC10 has a registry line AND a dead tunnel (DOWN since 08-13), so the
#  script marked itself done and will never fire again — the exact machine it
#  was written for is the one it cannot help.
#
#  So the completion condition here is LIVE STATE, never registry presence:
#  a host is "done" only while the health monitor classifies it UP, and the
#  moment it stops being UP its counters are live again. Registry presence is
#  used for one thing only — knowing which hosts and ports exist.
#
#  WHAT IT DOES NOT DO
#  -------------------
#  These are colleagues' working machines. This script touches the SSH/tunnel
#  plumbing and NOTHING else: it never reboots, never logs anyone off, never
#  kills a user process, never deletes a file, never reads or writes any JIVO
#  business system. It never writes /root/.ssh/authorized_keys and never writes
#  /root/fleet-tunnels.txt — both are read-only inputs here.
#
#  IT DOES NOT RE-IMPLEMENT THE HEALTH CHECK
#  -----------------------------------------
#  UP / DOWN / UNREACHABLE is computed in exactly one place —
#  /root/bin/fleet-tunnel-health.sh — and consumed here from its state file.
#  Two copies of that classification WILL drift, and the drifting copy is the
#  one that pokes people's PCs. If the state file is stale this script does
#  nothing at all rather than act on an old picture.
#
#  THE THREE STATES, AND WHAT EACH ONE MEANS FOR REPAIR
#  ----------------------------------------------------
#    UP           port listens on the VPS and sshd answered with an SSH- banner.
#                 Nothing to do. Clears any counters we were holding.
#    DOWN         nothing listening. The box is off, or its dialer task is dead.
#                 Its own tunnel MIGHT work anyway (the snapshot is minutes old
#                 and the box redials every minute) — cheap to try, so we try it.
#    UNREACHABLE  the port listens but nothing answers on the box's port 22.
#                 The box is on and dialling; its sshd is dead. Its own tunnel
#                 is therefore useless by definition — we skip that channel and
#                 go straight to Tailscale.
#
#  A LISTENING PORT IS NOT REACHABILITY. Only an SSH banner is. The monitor
#  learned that on 2026-08-13 when three boxes reported UP for hours while
#  `ssh` died with kex_exchange_identification. Nothing here treats "listening"
#  as "reachable".
#
#  ORDER OF REPAIR — cheapest, most surgical first
#  -----------------------------------------------
#    phase 1    always: push jivo-tunnel-revive.ps1 and run it — set sshd
#               Automatic, ssh-keygen -A if it will not start, start it,
#               re-enable the JivoRevTunnel task and kick it only if no dialer
#               is running. Seconds, and it is precisely the fix the health
#               monitor's own alert text tells a human to run. If it leaves
#               127.0.0.1:22 ANSWERING on the box (a real TCP connect, not the
#               service's self-report) and a dialer process alive, we STOP: the
#               health cron will confirm UP within 10 min.
#    phase 2    push and run the full installer idempotently, the way
#               dev-tunnel-install.sh does (scp to C:\Windows\Temp, then
#               `cmd /c "... < NUL"`). Reached when the dial task is gone
#               (only the installer rebuilds it), when phase 1 did not restore
#               the box, or after ESCALATE_AFTER attempts where phase 1 claimed
#               success and the monitor still cannot see the port — that means
#               the box is dialling and not landing, which is a registration
#               problem no service restart can fix.
#
#  WE WAIT FOR THE BOX'S OWN SELF-HEALING FIRST. The dialer retries every
#  minute and the on-box watchdog every 15. Intervening before MIN_DOWN_MIN
#  (default 25 = one full watchdog cycle plus slack) would race layers that
#  usually win on their own.
#
#  RATE LIMITING — a dead box must not be poked forever
#  -----------------------------------------------------
#    * one attempt per host per tick, MAX_REPAIRS_PER_TICK hosts per tick,
#      and a whole-tick time budget so a slow installer cannot run into the
#      next cron tick.
#    * COOLDOWN_MIN between attempts on the same host.
#    * MAX_ATTEMPTS consecutive attempts, then the host is PARKED and skipped
#      until it is seen UP again, PARK_EXPIRE_H passes, or a human runs
#      `fleet-auto-repair.sh reset <HOST>`.
#    * every numeric knob is validated at startup. A typo (COOLDOWN_MIN=abc)
#      makes bash score every comparison against it FALSE, which silently means
#      NO rate limit at all — so a bad value reverts to its default and is named
#      in the log. Measured, not theorised.
#    * COUNTING RULE THAT MATTERS: an attempt is only counted when we actually
#      REACHED the box. A box that is simply switched off costs a "miss", not
#      an attempt. Otherwise every office PC would burn its whole attempt budget
#      overnight while nobody was there, and would be parked by the morning —
#      exactly when repairing it would have worked.
#
#  Manual use:
#      /root/bin/fleet-auto-repair.sh              # a tick: decide, repair, log
#      /root/bin/fleet-auto-repair.sh plan         # decide + log, touch no box
#      /root/bin/fleet-auto-repair.sh report       # print status, change nothing
#      /root/bin/fleet-auto-repair.sh reset HOST   # un-park one host (or: all)
#      tail -f /root/fleet-auto-repair.log
# ============================================================================
set -u
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LC_ALL=C

[ "${BASH_VERSINFO[0]:-0}" -ge 4 ] || { echo "needs bash 4+ (associative arrays)" >&2; exit 1; }

# ---- inputs we only ever READ ----------------------------------------------
# Every path is env-overridable purely as a test seam: it lets the whole tick be
# exercised against fixtures in a scratch directory without going anywhere near
# the real registry. Nothing in normal operation sets these.
DB=${FLEET_DB:-/root/fleet-tunnels.txt}                 # HOST PORT USER REGISTERED_AT
HSTATE=${FLEET_HSTATE:-/root/.fleet-tunnel-state.tsv}   # the monitor's classification
HSTATUS=${FLEET_HSTATUS:-/root/fleet-tunnel-status.txt} # human snapshot, fallback only
WIN_INSTALLER=${FLEET_WIN_INSTALLER:-/root/JIVO-VPS-TUNNEL.cmd}          # built artifact (holds the reg key)
MAC_INSTALLER=${FLEET_MAC_INSTALLER:-/root/JIVO-VPS-TUNNEL-MAC.command}  # optional; absent today

# ---- files we own ----------------------------------------------------------
STATE=${FLEET_STATE:-/root/.fleet-auto-repair-state.tsv}   # HOST ATT MISS LAST RESULT CHANNEL PARKED
STATUS=${FLEET_STATUS:-/root/fleet-auto-repair-status.txt}
LOG=${FLEET_LOG:-/root/fleet-auto-repair.log}
LOCK=${FLEET_LOCK:-/root/.fleet-auto-repair.lock}
KNOWN=${FLEET_KNOWN:-/root/.fleet-auto-repair.known_hosts}  # our own trust store, never the shared one
MAP=${FLEET_MAP:-/root/fleet-auto-repair-hosts.tsv}         # optional overrides, see below
CONF=${FLEET_CONF:-/root/fleet-auto-repair.conf}            # optional: shell vars, sourced if present

# Optional overrides file, whitespace separated, '#' comments:
#     HOST                     SSH_TARGET        OS
#     HO-IT-PC10               khush             windows
#     JIVO201                  100.104.229.9     -
#     Karanpreets-MacBook-Air  -                 skip
# SSH_TARGET is an ssh_config alias (preferred — it carries the right account
# name and key) or a bare host/IP. OS is windows|mac|linux|skip. '-' in either
# column means "work it out"; a host absent from the file is all defaults.
# Nothing here is required — the file need not exist.

# shellcheck source=/dev/null
[ -f "$CONF" ] && . "$CONF"

# ---- knobs (env or CONF) ----------------------------------------------------
FLEET_REPAIR_ENABLE=${FLEET_REPAIR_ENABLE:-1}   # 0 = decide and log, touch nothing
MIN_DOWN_MIN=${MIN_DOWN_MIN:-25}                # let the box's own watchdog try first
COOLDOWN_MIN=${COOLDOWN_MIN:-60}                # between attempts on one host
MISS_COOLDOWN_MIN=${MISS_COOLDOWN_MIN:-20}      # between probes of an unreachable box
MAX_ATTEMPTS=${MAX_ATTEMPTS:-6}                 # consecutive reached-but-unfixed, then park
ESCALATE_AFTER=${ESCALATE_AFTER:-2}             # phase-1-only attempts before the full installer
PARK_EXPIRE_H=${PARK_EXPIRE_H:-168}             # a parked host is retried after 7 days
MAX_REPAIRS_PER_TICK=${MAX_REPAIRS_PER_TICK:-2}
TICK_BUDGET_S=${TICK_BUDGET_S:-540}             # stop starting work after 9 min
PROBE_TIMEOUT_S=${PROBE_TIMEOUT_S:-12}
CONNECT_TIMEOUT_S=${CONNECT_TIMEOUT_S:-8}
REVIVE_TIMEOUT_S=${REVIVE_TIMEOUT_S:-120}
SCP_TIMEOUT_S=${SCP_TIMEOUT_S:-90}
INSTALLER_TIMEOUT_S=${INSTALLER_TIMEOUT_S:-420} # same as dev-tunnel-install.sh
STATE_MAX_AGE_MIN=${STATE_MAX_AGE_MIN:-30}      # older than this = do nothing
HOUR_FROM=${HOUR_FROM:-0}                       # repair window (VPS clock is IST)
HOUR_TO=${HOUR_TO:-23}
SKIP_HOSTS=${SKIP_HOSTS:-}                      # space separated, never touched
LOG_KEEP=${LOG_KEEP:-5000}

# Every knob above is a RATE LIMIT, and a typo in the conf file must never read
# as "no limit". Measured: COOLDOWN_MIN=abc makes `[ "$mins" -lt "$cd_min" ]`
# fail with "integer expected", bash scores that as FALSE, the cooldown branch
# is skipped, and every host is poked on every tick — the exact runaway this
# script exists to prevent, arriving silently through a one-character mistake.
# So: anything not a plain non-negative integer reverts to its default and is
# named in the log and the status file.
BAD_KNOBS=''
for _kv in MIN_DOWN_MIN=25 COOLDOWN_MIN=60 MISS_COOLDOWN_MIN=20 MAX_ATTEMPTS=6 \
           ESCALATE_AFTER=2 PARK_EXPIRE_H=168 MAX_REPAIRS_PER_TICK=2 TICK_BUDGET_S=540 \
           PROBE_TIMEOUT_S=12 CONNECT_TIMEOUT_S=8 REVIVE_TIMEOUT_S=120 SCP_TIMEOUT_S=90 \
           INSTALLER_TIMEOUT_S=420 STATE_MAX_AGE_MIN=30 HOUR_FROM=0 HOUR_TO=23 LOG_KEEP=5000; do
  _n=${_kv%%=*}; _d=${_kv#*=}; _v=${!_n}
  case "$_v" in
    ''|*[!0-9]*) BAD_KNOBS="$BAD_KNOBS $_n='$_v'(using $_d)"; printf -v "$_n" '%s' "$_d" ;;
  esac
done
unset _kv _n _d _v

# The installer currently on the VPS predates the fix for the 'openssh-server'
# early return — the bug that leaves sshd stopped on a box where OpenSSH was
# already installed, i.e. the bug that MADE today's UNREACHABLE boxes. Pushing
# that build would not repair a box; on a healthy one it could cause the very
# failure we are repairing. So phase 2 refuses to run until the rebuilt
# installer is uploaded. Two markers, either is enough, so rewording one of
# them upstream does not silently disable the guard.
REQUIRE_SSHD_FIX=${REQUIRE_SSHD_FIX:-1}
INSTALLER_FIX_MARKER=${INSTALLER_FIX_MARKER:-REFUSES TO START|Never re-add an early return}

MODE=${1:-run}
TARGET_ARG=${2:-}
NOW=$(date +%s)
HOUR=$(date +%-H)
DEADLINE=$(( NOW + TICK_BUDGET_S ))
PERSIST=1
# `plan` is a human typing it to see what a tick would do. It must not leave
# cooldowns behind that suppress the real tick five minutes later. A cron soak
# is a different thing: MODE=run with FLEET_REPAIR_ENABLE=0 in the conf file,
# which does persist, so the log paces itself exactly like the live version.
[ "$MODE" = plan ] && { FLEET_REPAIR_ENABLE=0; PERSIST=0; }

log() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }

# ============================================================================
#  ssh plumbing
#  ------------
#  Every call: BatchMode (never prompt, never hang on a password), an explicit
#  timeout, -n (stdin from /dev/null) and our own known_hosts.
#
#  -n is not cosmetic. The health monitor already lost a whole run to a probe
#  that inherited stdin inside a `while read` loop and swallowed the rest of
#  the registry — 12 hosts in, 2 hosts out. Candidates here are read into an
#  array BEFORE any ssh runs, and every ssh is -n as well. Belt and braces.
#
#  User and port go through -o User= / -o Port= rather than user@host and
#  -p/-P, because one box's Windows account name contains a space
#  ("khushwinder singh", recorded in the registry as khushwinder_singh) and
#  because ssh wants -p while scp wants -P.
# ============================================================================
ssh_opts() {   # $1 = target kind, $2 = user or '', $3 = port or ''
  local kind=$1 user=$2 port=$3
  OPTS=( -o BatchMode=yes
         -o "ConnectTimeout=$CONNECT_TIMEOUT_S"
         -o StrictHostKeyChecking=accept-new
         -o "UserKnownHostsFile=$KNOWN"
         -o LogLevel=ERROR
         -o ServerAliveInterval=15
         -o ServerAliveCountMax=3 )
  [ -n "$port" ] && OPTS+=( -o "Port=$port" )
  # The value MUST be quoted inside the -o string. ssh parses -o as a config
  # line and splits it on whitespace, so -o "User=khushwinder singh" dies with
  # "keyword user extra arguments at end of line" — and that is precisely the
  # one account on this fleet whose name has a space in it. Quoting works for
  # ssh and scp alike (both verified against 100.116.119.38).
  [ -n "$user" ] && OPTS+=( -o "User=\"$user\"" )
  # An ssh_config alias already carries its own identity; adding more here only
  # burns MaxAuthTries. For raw targets, offer the two keys the VPS holds.
  if [ "$kind" != alias ]; then
    [ -f /root/.ssh/id_ed25519 ] && OPTS+=( -o IdentityFile=/root/.ssh/id_ed25519 )
    [ -f /root/.ssh/vps_to_mac ] && OPTS+=( -o IdentityFile=/root/.ssh/vps_to_mac )
  fi
}

rssh() {   # <host> <timeout> <command...>   OPTS must already be set
  local host=$1 tmo=$2; shift 2
  timeout "$tmo" ssh -n "${OPTS[@]}" "$host" "$@" 2>&1
}

rscp() {   # <local> <host> <remote-path> ; OPTS must already be set
  local src=$1 host=$2 dst=$3
  timeout "$SCP_TIMEOUT_S" scp "${OPTS[@]}" "$src" "$host:$dst" 2>&1
}

# ============================================================================
#  the on-box repair script (phase 1)
#  ----------------------------------
#  Pushed as a FILE and run with -File. Quoting a multi-statement PowerShell
#  program through bash -> ssh -> PowerShell is how these scripts get silently
#  mangled; a file has no quoting at all. Remote Windows shells are PowerShell,
#  so it uses ';' and never '&&'.
#
#  It touches: the sshd service, its host keys, and the two Jivo scheduled
#  tasks. Nothing else exists in it.
# ============================================================================
REVIVE_PS1=$(mktemp) || exit 1
cat > "$REVIVE_PS1" <<'PS1EOF'
# jivo-tunnel-revive.ps1 - pushed by fleet-auto-repair.sh on the JIVO VPS.
# Touches ONLY the SSH server and the two JIVO tunnel tasks. Idempotent.
$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference    = 'SilentlyContinue'
function S { param($m) Write-Output ("JIVOREPAIR " + $m) }

# --- 0. are we elevated? ----------------------------------------------------
# Every step below needs admin: Set-Service, Start-Service, ssh-keygen -A,
# schtasks /Run on a SYSTEM task, and reading a SYSTEM process's command line.
# Without it they all fail SILENTLY (this whole file runs SilentlyContinue), and
# silent failure reads from the VPS exactly like "the box is broken" - which
# would escalate to the full installer, which needs admin too. Say it out loud.
$isAdmin = $false
try {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
} catch { }
S ('ADMIN=' + $(if ($isAdmin) { 'yes' } else { 'no' }))

# --- 1. sshd: the door the reverse tunnel lands on --------------------------
function Test-Ssh22 {
  # The service's opinion of itself is NOT the test. A 'Running' sshd that bound
  # nothing is precisely the UNREACHABLE state we are here to repair, and it
  # reports Running. So connect to 127.0.0.1:22 the way the VPS monitor does.
  # BeginConnect+WaitOne, never a plain Connect: a filtered port can hang for
  # longer than this whole repair is allowed to take.
  try {
    $c = New-Object Net.Sockets.TcpClient
    $a = $c.BeginConnect('127.0.0.1', 22, $null, $null)
    if (-not $a.AsyncWaitHandle.WaitOne(3000, $false)) { $c.Close(); return $false }
    $c.EndConnect($a); $c.Close(); return $true
  } catch { return $false }
}
$svc = Get-Service sshd -ErrorAction SilentlyContinue
if (-not $svc) {
  # ABSENT is not STOPPED - there is nothing to start. Installing OpenSSH is the
  # installer's job (phase 2), never this script's.
  S 'SSHD=ABSENT'
} else {
  # Automatic FIRST: a Manual sshd is dead again after the next reboot, and
  # restarting it every hour forever is not a repair.
  Set-Service -Name sshd -StartupType Automatic -ErrorAction SilentlyContinue
  $svc.Refresh()
  if ($svc.Status -ne 'Running') {
    Start-Service sshd -ErrorAction SilentlyContinue
    $svc.Refresh()
    if ($svc.Status -ne 'Running') {
      # THE line the on-box watchdog was missing. sshd refuses to start with no
      # host keys - the documented state of every box installed by the version
      # of step 6d that returned early, i.e. today's UNREACHABLE set. -A creates
      # only the missing keys and leaves a working set alone. Full path resolved
      # at run time: ssh-keygen is not on PATH for a service account.
      $kg = @("$env:WINDIR\System32\OpenSSH\ssh-keygen.exe",
              "$env:ProgramFiles\OpenSSH\ssh-keygen.exe") |
            Where-Object { Test-Path $_ } | Select-Object -First 1
      if ($kg) {
        & $kg -A 2>&1 | Out-Null; S 'KEYGEN=ran'
        Start-Service sshd -ErrorAction SilentlyContinue; $svc.Refresh()
      } else { S 'KEYGEN=notfound' }
    }
  }
  S ('SSHD=' + $svc.Status)
}
# The only claim that matters, and the one the VPS acts on.
S ('PORT22=' + $(if (Test-Ssh22) { 'yes' } else { 'no' }))

# --- 2. the two JIVO tasks --------------------------------------------------
$t = Get-ScheduledTask -TaskName 'JivoRevTunnel' -ErrorAction SilentlyContinue
if (-not $t) {
  S 'DIAL=ABSENT'          # only the installer can rebuild a deleted task
} else {
  if ($t.State -eq 'Disabled') { Enable-ScheduledTask -TaskName 'JivoRevTunnel' | Out-Null }
  S ('DIAL=' + (Get-ScheduledTask -TaskName 'JivoRevTunnel').State)
}
$w = Get-ScheduledTask -TaskName 'JivoTunnelWatchdog' -ErrorAction SilentlyContinue
if (-not $w) {
  S 'WD=ABSENT'
} else {
  if ($w.State -eq 'Disabled') { Enable-ScheduledTask -TaskName 'JivoTunnelWatchdog' | Out-Null }
  S ('WD=' + (Get-ScheduledTask -TaskName 'JivoTunnelWatchdog').State)
}

# --- 3. is a dialer actually running? kick it ONLY if it is not -------------
function Get-Dialer {
  # A SYSTEM-owned process's CommandLine is readable only by an admin, so a
  # non-admin session gets an empty answer here whether the dialer is alive or
  # dead. That is 'unknown', never 'down' - see the TUNNELPROC lines below.
  Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match '127\.0\.0\.1:\d+:localhost:22' }
}
$alive = Get-Dialer
if ((-not $alive) -and $t) {
  # Kick it only when it is genuinely not running. schtasks /Run against a live
  # dialer just spawns a second ssh that cannot bind the port and dies - noise
  # in someone's task history for no gain.
  schtasks /Run /TN JivoRevTunnel | Out-Null
  S 'DIAL=kicked'
  Start-Sleep -Seconds 10
  $alive = Get-Dialer
}
if     ($alive)        { S 'TUNNELPROC=up' }
elseif (-not $isAdmin) { S 'TUNNELPROC=unknown' }
else                   { S 'TUNNELPROC=down' }
S 'DONE'
PS1EOF
cleanup() { rm -f "$REVIVE_PS1" 2>/dev/null; }
trap cleanup EXIT

# ============================================================================
#  read the monitor's classification (never recompute it)
# ============================================================================
declare -A MON_STATE MON_SINCE
load_monitor() {
  local src='' age=0 mt=0
  if [ -f "$HSTATE" ]; then
    mt=$(stat -c %Y "$HSTATE" 2>/dev/null || echo 0)
    age=$(( (NOW - mt) / 60 ))
    if [ "$age" -le "$STATE_MAX_AGE_MIN" ]; then
      while IFS=$'\t' read -r h s since _alert; do
        [ -n "${h:-}" ] || continue
        MON_STATE[$h]=${s:-UNKNOWN}; MON_SINCE[$h]=${since:-0}
      done < "$HSTATE"
      src="$HSTATE (${age}m old)"
    fi
  fi
  if [ -z "$src" ] && [ -f "$HSTATUS" ]; then
    # Fallback only. Note the health check writes STATE atomically (mktemp+mv)
    # but STATUS with a plain redirect, so STATUS can be caught half written —
    # hence it is second choice, and only used when STATE is missing.
    mt=$(stat -c %Y "$HSTATUS" 2>/dev/null || echo 0)
    age=$(( (NOW - mt) / 60 ))
    if [ "$age" -le "$STATE_MAX_AGE_MIN" ]; then
      local dm
      while read -r h _p s _rest; do
        case "${h:-}" in ''|fleet) continue ;; esac
        case "${s:-}" in UP|DOWN|UNREACHABLE) ;; *) continue ;; esac
        MON_STATE[$h]=$s
        # Recover the outage age from the "(6083m)" the monitor prints, so the
        # MIN_DOWN_MIN grace still applies on this path. Without it a fallback
        # tick would treat a 3-minute flap as a 3-day outage and pile in on top
        # of the box's own dialer.
        dm=$(printf '%s' "${_rest:-}" | grep -oE '\([0-9]+m\)' | tr -dc '0-9')
        if [ -n "$dm" ]; then MON_SINCE[$h]=$(( NOW - dm * 60 )); else MON_SINCE[$h]=0; fi
      done < "$HSTATUS"
      src="$HSTATUS (${age}m old, fallback)"
    fi
  fi
  MONITOR_SRC=$src
  [ -n "$src" ]
}

# ============================================================================
#  our own per-host memory
# ============================================================================
#  EVERY FIELD IS WRITTEN NON-EMPTY, '-' standing in for a blank. Tab is an IFS
#  *whitespace* character, so bash's `read` collapses a run of tabs into one
#  delimiter: a line ending "...\tnochannel\t\t0" parses as chan=0, parked='',
#  and the record silently shifts by a column. (Measured — it corrupted two
#  records on the first fixture run.) No empty fields, no collapse. The health
#  monitor sidesteps the same trap by never writing a blank field either.
declare -A A_ATT A_MISS A_LAST A_RESULT A_CHAN A_PARKED
load_state() {
  [ -f "$STATE" ] || return 0
  local h att miss last res chan parked
  while IFS=$'\t' read -r h att miss last res chan parked; do
    [ -n "${h:-}" ] || continue
    [ "${res:-}" = "-" ] && res=''
    [ "${chan:-}" = "-" ] && chan=''
    A_ATT[$h]=${att:-0}; A_MISS[$h]=${miss:-0}; A_LAST[$h]=${last:-0}
    A_RESULT[$h]=${res:-}; A_CHAN[$h]=${chan:-}; A_PARKED[$h]=${parked:-0}
  done < "$STATE"
}
save_state() {
  local tmp h res chan
  tmp=$(mktemp) || return 1
  for h in "${!A_ATT[@]}"; do
    res=${A_RESULT[$h]:-}; [ -n "$res" ] || res='-'
    chan=${A_CHAN[$h]:-};  [ -n "$chan" ] || chan='-'
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$h" "${A_ATT[$h]:-0}" "${A_MISS[$h]:-0}" \
      "${A_LAST[$h]:-0}" "$res" "$chan" "${A_PARKED[$h]:-0}"
  done | sort > "$tmp"
  mv "$tmp" "$STATE"
}
touch_host() { : "${A_ATT[$1]:=0}" "${A_MISS[$1]:=0}" "${A_LAST[$1]:=0}" \
                 "${A_RESULT[$1]:=}" "${A_CHAN[$1]:=}" "${A_PARKED[$1]:=0}"; }

# ============================================================================
#  optional per-host overrides
# ============================================================================
declare -A MAP_TARGET MAP_OS
load_map() {
  [ -f "$MAP" ] || return 0
  local h t o
  while read -r h t o _rest; do
    case "${h:-}" in ''|\#*) continue ;; esac
    # '-' means "work it out" in EITHER column. Taking it literally in the OS
    # column made a Windows box read as os='-' and get filed as "needs a human".
    [ "${t:-}" = "-" ] && t=''
    [ "${o:-}" = "-" ] && o=''
    MAP_TARGET[$h]=${t:-}; MAP_OS[$h]=${o:-}
  done < "$MAP"
}

# ============================================================================
#  Tailscale — the second, independent path
#  ----------------------------------------
#  Read once per tick. A peer marked offline is skipped without a probe: it
#  saves a 12 s timeout per host and the answer is already known.
#  Names are matched case-insensitively against the registry host name, which
#  covers VICTUS/victus, JIVO/jivo, DESKTOP-73N6JE8/desktop-73n6je8 with no
#  table to maintain. The ones that genuinely differ (HO-IT-PC10 is
#  khushvinder-dev-veerji on the tailnet) are reached by their ssh_config
#  alias instead, which is checked first.
# ============================================================================
declare -A TS_IP TS_UP TS_OS
load_tailscale() {
  command -v tailscale >/dev/null 2>&1 || return 0
  local line ip name os st
  while read -r line; do
    [ -n "$line" ] || continue
    ip=$(printf '%s' "$line"   | awk '{print $1}')
    name=$(printf '%s' "$line" | awk '{print $2}')
    os=$(printf '%s' "$line"   | awk '{print $4}')
    case "$ip" in 100.*) ;; *) continue ;; esac
    [ -n "$name" ] || continue
    case "$line" in *offline*) st=0 ;; *) st=1 ;; esac
    name=${name,,}
    TS_IP[$name]=$ip; TS_UP[$name]=$st; TS_OS[$name]=${os,,}
  done < <(timeout 20 tailscale status 2>/dev/null)
}

# An ssh_config alias exists iff `ssh -G <name>` resolves hostname to something
# other than the name itself. Verified on the VPS: `ssh -G ho-it-pc10` gives
# 100.116.119.38, `ssh -G jivo201` gives back "jivo201".
alias_exists() {
  local a=$1 resolved
  resolved=$(ssh -G "$a" 2>/dev/null | awk '/^hostname /{print $2; exit}')
  [ -n "$resolved" ] && [ "${resolved,,}" != "${a,,}" ]
}

# ============================================================================
#  channels for one host, best first
#  ---------------------------------
#  Emits: kind|sshhost|user|port   (user/port empty means "ssh_config decides")
# ============================================================================
channels_for() {
  local host=$1 port=$2 user=$3 state=$4
  local lc=${host,,} u
  local -a uv
  # mapfile, never $(...): one account name is "khushwinder singh" and word
  # splitting turned that into two bogus users, "khushwinder" and "singh".
  mapfile -t uv < <(user_variants "$user")

  # 1. the box's own reverse tunnel.
  #    UNREACHABLE means the port listens and nothing answers behind it — that
  #    is a measured fact about this exact path, so do not waste a probe on it.
  #    DOWN means it was not listening ~5 min ago; the box redials every minute,
  #    so it may be back. Cheap, and correct when a tunnel merely flapped.
  if [ "$state" != UNREACHABLE ] && [ -n "$port" ]; then
    for u in "${uv[@]}"; do
      printf 'tunnel|127.0.0.1|%s|%s\n' "$u" "$port"
    done
  fi

  # 2. an ssh_config alias, if one resolves. Preferred over a raw Tailscale IP
  #    because the alias carries the right account name and key.
  #    An explicit entry in the map wins outright, and is honoured even when it
  #    is a bare host or IP rather than an alias — an operator who wrote a
  #    target down meant it, and silently falling through to guesswork would be
  #    the worst of both.
  local a
  if [ -n "${MAP_TARGET[$host]:-}" ]; then
    a=${MAP_TARGET[$host]}
    if alias_exists "$a"; then
      printf 'alias|%s||\n' "$a"
    else
      for u in "${uv[@]}"; do printf 'map|%s|%s|\n' "$a" "$u"; done
    fi
  else
    for a in "$host" "$lc"; do
      if alias_exists "$a"; then printf 'alias|%s||\n' "$a"; break; fi
    done
  fi

  # 3. Tailscale by name, registry account name (and its de-sanitised form).
  if [ -n "${TS_IP[$lc]:-}" ] && [ "${TS_UP[$lc]}" = 1 ]; then
    for u in "${uv[@]}"; do
      printf 'tailscale|%s|%s|\n' "${TS_IP[$lc]}" "$u"
    done
  fi
}

# The registrar sanitises the Windows account name: HO-IT-PC10's registry line
# says khushwinder_singh, the real account is "khushwinder singh". Try both.
user_variants() {
  local u=$1
  printf '%s\n' "$u"
  case "$u" in *_*) printf '%s\n' "${u//_/ }" ;; esac
}

# ============================================================================
#  is the built installer safe to push?
# ============================================================================
installer_ok() {
  [ -s "$WIN_INSTALLER" ] || { INSTALLER_WHY="missing at $WIN_INSTALLER"; return 1; }
  if [ "$REQUIRE_SSHD_FIX" = 1 ]; then
    if ! grep -qE -- "$INSTALLER_FIX_MARKER" "$WIN_INSTALLER" 2>/dev/null; then
      INSTALLER_WHY="build predates the openssh-server early-return fix (no marker); rebuild with connections/fleet/build-tunnel-installer.sh win and upload, or set REQUIRE_SSHD_FIX=0"
      return 1
    fi
  fi
  INSTALLER_WHY=ok; return 0
}

# ============================================================================
#  repair one host over one channel. Returns 0 only if we reached the box.
# ============================================================================
REACHED=0; OUTCOME=''; DETAIL=''
repair_over() {   # <host> <kind> <sshhost> <user> <port> <state> <attempt_no>
  local host=$1 kind=$2 sshhost=$3 user=$4 port=$5 state=$6 attempt=$7
  REACHED=0; OUTCOME=''; DETAIL=''
  ssh_opts "$kind" "$user" "$port"

  # -- probe. hostname is the only thing every one of these boxes answers the
  #    same way, and it doubles as an identity check.
  local hn
  hn=$(rssh "$sshhost" "$PROBE_TIMEOUT_S" hostname)
  local rc=$?
  hn=$(printf '%s' "$hn" | tr -d '\r' | grep -v '^Warning: Permanently added' | head -1)
  if [ $rc -ne 0 ] || [ -z "$hn" ]; then
    DETAIL=$(printf '%s' "$hn" | head -1)
    log "  channel=$kind target=$sshhost user='${user:-<config>}' -> no answer${DETAIL:+ ($DETAIL)}"
    return 1
  fi

  # -- identity guard. An alias or a Tailscale name could point at somebody
  #    else's machine; we are about to run an installer, so refuse unless the
  #    box says it is who the registry says it is.
  local hn_short=${hn%%.*}
  if [ "${hn_short,,}" != "${host,,}" ]; then
    log "  channel=$kind target=$sshhost -> WRONG BOX (answers '$hn', registry says '$host') - refusing"
    return 1
  fi
  REACHED=1
  log "  channel=$kind target=$sshhost user='${user:-<config>}' -> reached ($hn)"

  # -- what OS is this? The Windows installer must never land on a Mac.
  #    Order: the map is explicit and wins. Otherwise Tailscale's OS field may
  #    only ever VETO (mark a box non-Windows and stop us) — it can never be
  #    the thing that authorises a push. Authorising needs the live probe, and
  #    "no uname on this box" is exactly what a Windows shell looks like.
  local os=${MAP_OS[$host]:-} src=map
  if [ -z "$os" ]; then
    case "${TS_OS[${host,,}]:-}" in
      macos) os=mac;   src=tailscale ;;
      linux) os=linux; src=tailscale ;;
      *)
        src=probe
        local un; un=$(rssh "$sshhost" "$PROBE_TIMEOUT_S" uname)
        case "$un" in
          *Darwin*) os=mac ;;
          *Linux*)  os=linux ;;
          *)        os=windows ;;   # PowerShell/cmd have no uname; that IS the tell
        esac
        ;;
    esac
  fi
  log "  os=$os (from $src)"

  if [ "$os" = skip ]; then OUTCOME=skipped; DETAIL="$MAP says skip"; return 0; fi
  if [ "$os" != windows ]; then
    # The macOS installer self-elevates with `sudo -p` and blocks on a login
    # password, so it cannot be driven from here at all. Reaching the box is
    # still worth logging — a human can finish it in one command.
    OUTCOME=manual
    DETAIL="$os box: its installer self-elevates with sudo and blocks on a login password, so it cannot be run from here. By hand on that machine: double-click $(basename "$MAC_INSTALLER")"
    return 0
  fi

  if [ "$FLEET_REPAIR_ENABLE" != 1 ]; then
    OUTCOME=planned; DETAIL="would run phase1$( [ "$attempt" -ge "$ESCALATE_AFTER" ] && echo ' then the full installer (past ESCALATE_AFTER)')"
    return 0
  fi

  # ---- phase 1: revive sshd and kick the dialer ----------------------------
  local out=''
  if ! out=$(rscp "$REVIVE_PS1" "$sshhost" 'C:/Windows/Temp/jivo-tunnel-revive.ps1'); then
    OUTCOME=failed; DETAIL="scp revive.ps1 failed: $(printf '%s' "$out" | head -1)"
    log "  phase1 scp FAILED: $(printf '%s' "$out" | head -2 | tr '\n' ' ')"
    return 0
  fi
  # `< NUL` is cmd's /dev/null. Same shape dev-tunnel-install.sh uses, and it
  # is what stops a remote step blocking on a prompt nobody will ever answer.
  out=$(rssh "$sshhost" "$REVIVE_TIMEOUT_S" \
        'cmd /c "powershell -NoProfile -ExecutionPolicy Bypass -File C:\Windows\Temp\jivo-tunnel-revive.ps1 < NUL"')
  local p1; p1=$(printf '%s' "$out" | tr -d '\r' | grep '^JIVOREPAIR' | sed 's/^JIVOREPAIR //' | tr '\n' ' ')
  log "  phase1: ${p1:-no output: $(printf '%s' "$out" | head -1)}"

  # Escalate to the full installer only when the cheap fix cannot be enough:
  #   - the dial task is gone: nothing but the installer rebuilds it;
  #   - phase 1 did not leave sshd running AND a dialer process alive;
  #   - or phase 1 has claimed success ESCALATE_AFTER times and the monitor
  #     still does not see the port. That combination means the box is dialling
  #     and not landing — a registration problem the installer re-does and a
  #     service restart never will.
  # When phase 1 has just brought the tunnel up, stop here: the health cron
  # will confirm UP within 10 minutes and clear this host's counters. Running a
  # full installer on a colleague's PC to fix something already fixed is
  # exactly the kind of over-reach this queue must not do.
  local need_installer=0
  if [ -n "$p1" ]; then
    # Only the installer can create what is missing.
    case "$p1" in *DIAL=ABSENT*) need_installer=1 ;; esac
    case "$p1" in *SSHD=ABSENT*) need_installer=1 ;; esac
    # The door must actually ANSWER. PORT22 is a real TCP connect made on the
    # box itself — the same question the monitor asks from here, not the
    # service's self-report. A 'Running' sshd that bound nothing fails this,
    # and that is exactly the state nobody could see for four days.
    case "$p1" in *PORT22=yes*) ;; *) need_installer=1 ;; esac
    # A DEFINITE down only. TUNNELPROC=unknown means the session was not admin
    # and could not read a SYSTEM process's command line; escalating on "I could
    # not tell" would push a full installer onto boxes that are already fine.
    case "$p1" in *TUNNELPROC=down*) need_installer=1 ;; esac
  fi
  # Belt and braces. Phase 1 claiming success while the monitor still cannot see
  # the port means the box is dialling and not landing — a registration problem
  # no service restart can fix. This is also the only escalation path when phase
  # 1 produced no readable output at all, which is why it is not inside the
  # block above.
  [ "$attempt" -ge "$ESCALATE_AFTER" ] && need_installer=1

  if [ "$need_installer" = 0 ]; then
    OUTCOME=phase1; DETAIL="$p1"
    return 0
  fi

  # ---- phase 2: the full installer, idempotently ---------------------------
  if ! installer_ok; then
    OUTCOME=blocked; DETAIL="installer not pushed: $INSTALLER_WHY"
    log "  phase2 BLOCKED: $INSTALLER_WHY"
    return 0
  fi
  if ! out=$(rscp "$WIN_INSTALLER" "$sshhost" 'C:/Windows/Temp/JIVO-VPS-TUNNEL.cmd'); then
    OUTCOME=failed; DETAIL="scp installer failed: $(printf '%s' "$out" | head -1)"
    log "  phase2 scp FAILED: $(printf '%s' "$out" | head -2 | tr '\n' ' ')"
    return 0
  fi
  out=$(rssh "$sshhost" "$INSTALLER_TIMEOUT_S" 'cmd /c "C:\Windows\Temp\JIVO-VPS-TUNNEL.cmd < NUL"')
  printf '%s\n' "$out" | tr -d '\r' | sed 's/^/    installer| /' >> "$LOG"

  local sshd_line tun_line
  sshd_line=$(printf '%s' "$out" | tr -d '\r' | grep -m1 'SSHD *:')
  tun_line=$(printf '%s' "$out"  | tr -d '\r' | grep -m1 'TUNNEL *:')
  if printf '%s' "$out" | grep -q 'TUNNEL       : UP'; then
    OUTCOME=installed; DETAIL="${sshd_line:-} ${tun_line:-}"
  else
    OUTCOME=ran; DETAIL="installer finished, tunnel not confirmed UP. ${sshd_line:-} ${tun_line:-}"
  fi
  return 0
}

# ============================================================================
#  modes that do not need the lock
# ============================================================================
if [ "$MODE" = report ]; then
  [ -f "$STATUS" ] && cat "$STATUS" || echo "no status yet - run a tick first"
  exit 0
fi

# ============================================================================
#  one tick at a time. Concurrent with the health cron is fine (we only read
#  its files); concurrent with ourselves is not — an installer run can take 7
#  minutes and ticks are 10 apart.
# ============================================================================
exec 9>"$LOCK" || exit 1
if ! flock -n 9; then
  log "another tick holds the lock - exiting"
  exit 0
fi

if [ "$MODE" = reset ]; then
  load_state
  if [ -z "$TARGET_ARG" ]; then echo "usage: $0 reset <HOST|all>" >&2; exit 2; fi
  if [ "$TARGET_ARG" = all ]; then
    A_ATT=(); A_MISS=(); A_LAST=(); A_RESULT=(); A_CHAN=(); A_PARKED=()
    log "reset all - every host's counters cleared by hand"
  else
    touch_host "$TARGET_ARG"
    A_ATT[$TARGET_ARG]=0; A_MISS[$TARGET_ARG]=0; A_PARKED[$TARGET_ARG]=0
    A_RESULT[$TARGET_ARG]=reset
    log "reset $TARGET_ARG - counters cleared, un-parked"
  fi
  save_state
  echo "done"
  exit 0
fi

case "$MODE" in run|plan) ;; *) echo "usage: $0 [run|plan|report|reset <HOST>]" >&2; exit 2 ;; esac

# ============================================================================
#  the tick
# ============================================================================
[ -f "$DB" ] || { log "registry missing at $DB - nothing to do"; exit 0; }

if ! load_monitor; then
  # Acting on a stale picture is how an automation pokes boxes that are fine.
  log "SKIP TICK: no fresh classification (${HSTATE} older than ${STATE_MAX_AGE_MIN}m or absent). Is /root/bin/fleet-tunnel-health.sh still in cron?"
  exit 0
fi
load_state
load_map
load_tailscale

installer_ok || true   # sets INSTALLER_WHY for the log/status
log "tick start mode=$MODE enable=$FLEET_REPAIR_ENABLE monitor=$MONITOR_SRC installer=$INSTALLER_WHY tailscale_peers=${#TS_IP[@]}"
[ -n "$BAD_KNOBS" ] && log "BAD SETTINGS ignored (not integers), defaults used:$BAD_KNOBS  <- fix $CONF"

if [ "$HOUR" -lt "$HOUR_FROM" ] || [ "$HOUR" -gt "$HOUR_TO" ]; then
  log "outside repair window ${HOUR_FROM}:00-${HOUR_TO}:59 (now ${HOUR}) - no repairs this tick"
  exit 0
fi

# ---- pass 1: clear counters for anything the monitor now calls UP -----------
# THE ANTI-STALE-STAMP RULE. Completion is live state, never registry presence.
# A host that is UP right now is finished — and if it stops being UP tomorrow it
# is a candidate again with a clean slate. Nothing here is ever permanent.
up_list=''
while read -r host port user _reg; do
  [ -n "${host:-}" ] || continue
  case "$host" in \#*) continue ;; esac
  if [ "${MON_STATE[$host]:-}" = UP ]; then
    up_list="$up_list $host"
    if [ "${A_ATT[$host]:-0}" != 0 ] || [ "${A_MISS[$host]:-0}" != 0 ] || [ "${A_PARKED[$host]:-0}" != 0 ]; then
      log "$host: UP - clearing counters (was attempts=${A_ATT[$host]:-0} misses=${A_MISS[$host]:-0} parked=${A_PARKED[$host]:-0})"
      unset "A_ATT[$host]" "A_MISS[$host]" "A_LAST[$host]" "A_RESULT[$host]" "A_CHAN[$host]" "A_PARKED[$host]"
    fi
  fi
done < "$DB"
log "up, no action needed:${up_list:- none}"

# ---- pass 2: build the candidate list ---------------------------------------
# Read the whole registry into an array BEFORE any ssh runs. Nothing in the
# repair loop can then eat the file's stdin.
CANDIDATES=()
declare -A C_PORT C_USER C_STATE C_SINCE
while read -r host port user _reg; do
  [ -n "${host:-}" ] || continue
  case "$host" in \#*) continue ;; esac
  st=${MON_STATE[$host]:-}
  since=${MON_SINCE[$host]:-0}

  case " $SKIP_HOSTS " in *" $host "*) log "$host: skip (SKIP_HOSTS)"; continue ;; esac
  [ "$st" = UP ] && continue
  if [ -z "$st" ]; then
    log "$host: skip - registered but the monitor has no classification for it yet"
    continue
  fi

  touch_host "$host"
  down_min=0
  [ "${since:-0}" -gt 0 ] && down_min=$(( (NOW - since) / 60 ))

  if [ "$down_min" -lt "$MIN_DOWN_MIN" ] && [ "${since:-0}" -gt 0 ]; then
    log "$host: skip - $st for only ${down_min}m; the box's own dialer (1m) and watchdog (15m) get first go (<${MIN_DOWN_MIN}m)"
    continue
  fi
  if [ "${A_PARKED[$host]:-0}" -gt 0 ]; then
    parked_h=$(( (NOW - A_PARKED[$host]) / 3600 ))
    if [ "$parked_h" -lt "$PARK_EXPIRE_H" ]; then
      log "$host: skip - PARKED ${parked_h}h ago after ${A_ATT[$host]} attempts (last: ${A_RESULT[$host]:-?}). Un-park: fleet-auto-repair.sh reset $host"
      continue
    fi
    log "$host: un-parking - parked ${parked_h}h ago, past PARK_EXPIRE_H=${PARK_EXPIRE_H}h"
    A_PARKED[$host]=0; A_ATT[$host]=0
  fi
  last=${A_LAST[$host]:-0}
  if [ "$last" -gt 0 ]; then
    mins=$(( (NOW - last) / 60 ))
    if [ "${A_RESULT[$host]:-}" = miss ]; then cd_min=$MISS_COOLDOWN_MIN; else cd_min=$COOLDOWN_MIN; fi
    if [ "$mins" -lt "$cd_min" ]; then
      log "$host: skip - cooldown, last ${A_RESULT[$host]:-?} ${mins}m ago (need ${cd_min}m)"
      continue
    fi
  fi

  CANDIDATES+=("$host")
  C_PORT[$host]=$port; C_USER[$host]=$user; C_STATE[$host]=$st; C_SINCE[$host]=$down_min
done < "$DB"

# Fairest order: least-recently-touched first, so one stubborn box cannot
# monopolise the per-tick budget.
if [ ${#CANDIDATES[@]} -gt 0 ]; then
  mapfile -t CANDIDATES < <(
    for h in "${CANDIDATES[@]}"; do printf '%s\t%s\n' "${A_LAST[$h]:-0}" "$h"; done | sort -n | cut -f2
  )
fi
log "candidates: ${#CANDIDATES[@]}${CANDIDATES[*]:+ (${CANDIDATES[*]})}"

# ---- pass 3: repair, hard-capped --------------------------------------------
did=0
for host in ${CANDIDATES[@]+"${CANDIDATES[@]}"}; do
  if [ "$did" -ge "$MAX_REPAIRS_PER_TICK" ]; then
    log "$host: defer - per-tick cap ($MAX_REPAIRS_PER_TICK) reached"
    continue
  fi
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then
    log "$host: defer - tick budget ${TICK_BUDGET_S}s spent"
    continue
  fi

  port=${C_PORT[$host]}; user=${C_USER[$host]}; st=${C_STATE[$host]}
  attempt=${A_ATT[$host]:-0}
  log "$host ($port, $user): state=$st for ${C_SINCE[$host]}m, prior attempts=$attempt"

  mapfile -t chans < <(channels_for "$host" "$port" "$user" "$st")
  if [ ${#chans[@]} -eq 0 ]; then
    log "  no channel: tunnel $( [ "$st" = UNREACHABLE ] && echo 'is proven dead (listening, no banner)' || echo 'unavailable' ), no ssh alias, no online Tailscale peer named '${host,,}'"
    A_RESULT[$host]=nochannel; A_CHAN[$host]=''; A_LAST[$host]=$NOW
    A_MISS[$host]=$(( ${A_MISS[$host]:-0} + 1 ))
    continue
  fi

  got=0
  for ch in "${chans[@]}"; do
    IFS='|' read -r kind sshhost chuser chport <<<"$ch"
    if [ "$(date +%s)" -ge "$DEADLINE" ]; then log "  abandon - tick budget spent mid-host"; break; fi
    repair_over "$host" "$kind" "$sshhost" "$chuser" "$chport" "$st" "$attempt"
    if [ "$REACHED" = 1 ]; then got=1; A_CHAN[$host]="$kind:$sshhost"; break; fi
  done

  A_LAST[$host]=$NOW
  if [ "$got" = 0 ]; then
    # NOT an attempt. The box did not answer on any path — most likely it is
    # switched off. Counting this would park every office PC overnight.
    A_MISS[$host]=$(( ${A_MISS[$host]:-0} + 1 ))
    A_RESULT[$host]=miss
    log "  RESULT miss - no channel answered (misses=${A_MISS[$host]}, attempts still $attempt)"
    continue
  fi

  A_RESULT[$host]=${OUTCOME:-unknown}
  case "$OUTCOME" in
    planned|manual|skipped)
      # We reached the box but deliberately did nothing to it, so this consumes
      # neither an attempt nor a slot in the per-tick budget — otherwise one Mac
      # in the candidate list would block the real repairs behind it every tick.
      # The cooldown still applies, so we do not re-probe it every 10 minutes.
      log "  RESULT $OUTCOME - $DETAIL (nothing done: no attempt, no slot used)"
      ;;
    *)
      did=$(( did + 1 ))
      A_ATT[$host]=$(( attempt + 1 ))
      log "  RESULT $OUTCOME (attempt ${A_ATT[$host]}/$MAX_ATTEMPTS) - $DETAIL"
      if [ "${A_ATT[$host]}" -ge "$MAX_ATTEMPTS" ]; then
        A_PARKED[$host]=$NOW
        log "  PARKED $host after ${A_ATT[$host]} attempts that reached the box and did not fix it. This one needs a human. Un-park: fleet-auto-repair.sh reset $host"
      fi
      ;;
  esac
done

# ---- write our own snapshot --------------------------------------------------
{
  echo "fleet auto-repair @ $(date '+%Y-%m-%d %H:%M:%S')   mode=$MODE enable=$FLEET_REPAIR_ENABLE"
  echo "monitor: ${MONITOR_SRC:-none}"
  echo "installer: $INSTALLER_WHY"
  [ -n "$BAD_KNOBS" ] && echo "BAD SETTINGS (defaults used):$BAD_KNOBS"
  echo "repaired this tick: $did/${MAX_REPAIRS_PER_TICK}   candidates: ${#CANDIDATES[@]}"
  echo
  printf '%-28s %-13s %-4s %-5s %-10s %-22s %s\n' HOST MONITOR ATT MISS RESULT CHANNEL LAST
  while read -r host port user _reg; do
    [ -n "${host:-}" ] || continue
    case "$host" in \#*) continue ;; esac
    ls_at='-'
    [ "${A_LAST[$host]:-0}" -gt 0 ] && ls_at=$(date -d "@${A_LAST[$host]}" '+%m-%d %H:%M' 2>/dev/null)
    res=${A_RESULT[$host]:--}
    [ "${A_PARKED[$host]:-0}" -gt 0 ] && res="PARKED"
    printf '%-28s %-13s %-4s %-5s %-10s %-22s %s\n' \
      "$host" "${MON_STATE[$host]:-?}" "${A_ATT[$host]:-0}" "${A_MISS[$host]:-0}" \
      "$res" "${A_CHAN[$host]:--}" "$ls_at"
  done < "$DB"
} > "$STATUS.tmp" 2>/dev/null
mv "$STATUS.tmp" "$STATUS" 2>/dev/null

[ "$PERSIST" = 1 ] && save_state
log "tick end repaired=$did persist=$PERSIST"
tail -n "$LOG_KEEP" "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
exit 0
