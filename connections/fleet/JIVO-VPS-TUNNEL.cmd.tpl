@echo off
:: ====================================================================
::  JIVO VPS TUNNEL  -  double-click this file. That's it.
::
::  Makes this Windows PC permanently reachable by Daman's Mac, from
::  anywhere, WITHOUT Tailscale and WITHOUT any password.
::
::  How: the PC dials OUT to the JIVO VPS every minute and parks a
::  private door there. Outbound is never firewalled, so this works
::  from any office/home/hotspot network. Nothing is exposed to the
::  public internet -- the door is on the VPS's loopback only.
::
::  Idempotent: safe to run again any time.
:: ====================================================================
net session >nul 2>&1
if %errorlevel% NEQ 0 (
  echo.
  echo   Requesting administrator rights ^(click YES on the popup^)...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=[IO.File]::ReadAllText('%~f0'); $m='#:::'+'JIVOPS'+':::'; Invoke-Expression $c.Substring($c.IndexOf($m)+$m.Length)"
echo.
pause
exit /b
#:::JIVOPS:::
# ================= PowerShell body (runs elevated) ===================
# No global ErrorActionPreference=Stop: every step reports its own failure and
# the rest still runs, so one hiccup can't abandon a half-configured box.
# The blue "Operation Running [ooooo]" banner comes from PowerShell's progress
# stream. It hides real output, redraws constantly, and is the single biggest
# reason this looks hung. Off.
$ProgressPreference = 'SilentlyContinue'
$log = "$env:USERPROFILE\Desktop\jivo-vps-tunnel-log.txt"
try { Start-Transcript -Path $log -Force | Out-Null } catch {}

$ok=@(); $bad=@()
function Step($name,$block){ try { & $block; $script:ok += $name } catch { $script:bad += "$name -> $($_.Exception.Message)" } }

# Windows OpenSSH REFUSES a private key that any extra SID can read, and dies with
# "UNPROTECTED PRIVATE KEY FILE" -> "Permission denied (publickey)".
# `icacls /inheritance:r /grant` is NOT enough: it strips INHERITED aces but leaves
# EXPLICIT ones, including the per-logon-session SID (NT AUTHORITY\LogonSessionId_0_*)
# that gets stamped on a file at creation. Measured on VICTUS -- the key was silently
# ignored and the whole registration hung.
# Building a FRESH FileSecurity and Set-Acl'ing it REPLACES the entire DACL, so
# nothing can survive. SYSTEM is required because the dialer task runs as SYSTEM.
function Lock-KeyFile($path) {
  $acl = New-Object System.Security.AccessControl.FileSecurity
  $acl.SetAccessRuleProtection($true, $false)   # protected, and do NOT copy inherited rules
  $acl.SetOwner([System.Security.Principal.NTAccount]'BUILTIN\Administrators')
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('NT AUTHORITY\SYSTEM','FullControl','Allow')))
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('BUILTIN\Administrators','FullControl','Allow')))
  Set-Acl -Path $path -AclObject $acl -ErrorAction Stop
}

# Windows silently REFUSES to start a task under several conditions, and schtasks
# defaults DisallowStartIfOnBatteries to TRUE -- which means on a laptop the watchdog,
# the very thing meant to repair everything, does not run on battery. Measured on
# VICTUS. This normalises both tasks so they fire after a reboot in every state.
function Set-BootProof($Name, $Unlimited) {
  $t = Get-ScheduledTask -TaskName $Name -ErrorAction Stop
  # dialer must be UNLIMITED (its ssh runs forever); watchdog must be BOUNDED or a
  # hung run blocks every later run via IgnoreNew.
  $limit = if ($Unlimited) { [TimeSpan]::Zero } else { New-TimeSpan -Minutes 10 }
  $set = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit $limit `
           -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
           -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
  $set.RunOnlyIfNetworkAvailable = $false
  # 30s boot delay: at T+0 the network stack is not up, so an immediate dial is a
  # guaranteed failure. The 1-minute repeat would recover it, but this avoids the noise.
  $boot = New-ScheduledTaskTrigger -AtStartup
  $boot.Delay = 'PT30S'
  $t.Triggers = @($t.Triggers | Where-Object { $_.CimClass.CimClassName -notmatch 'BootTrigger' }) + $boot
  $t.Settings = $set
  Set-ScheduledTask -InputObject $t -ErrorAction Stop | Out-Null
}

$VPS        = 'root@187.127.129.132'
$DIR        = 'C:\ProgramData\jivo-revtun'
$REGKEY_B64 = '@@REGKEY_B64@@'
# Stamped by build-tunnel-installer.sh from the commit the template was built at.
# WHY THIS EXISTS: on 2026-08-17 three boxes were unreachable because an OLD copy
# of this very file was already sitting on them -- and the old one RUNS, prints a
# green OK, and repairs nothing (it skipped Set-Service Automatic and
# ssh-keygen -A entirely). Old and new were indistinguishable on screen, so a
# colleague's "it says OK" photo could not be trusted. Now the version is in the
# summary block AND written to $DIR\version.txt, so which build ran is a fact you
# can read over the tunnel instead of a thing you assume.
$TUNNEL_VER = '@@VERSION@@'
# Daman's Mac public key -- this is what lets him in through the tunnel.
$MANAGER_KEYS = @(
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB8+FPQ9luiwWsPUSZDY5UTwEiOVmL1o1zgf4sw1UORA daman8271@github',
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHR8F2rqvcl7hHaAmpmXd3uogcx0AUflmMvlAART0JNK hermes-agent-access'
)

# ssh.exe lives in System32\OpenSSH for the inbox capability, but in
# Program Files\OpenSSH when installed from the MSI. Resolve, do not assume.
function Find-Exe($name) {
  foreach ($d in @("$env:WINDIR\System32\OpenSSH", "$env:ProgramFiles\OpenSSH",
                   "$env:ProgramFiles\OpenSSH-Win64", "$env:ProgramFiles\OpenSSH-ARM64",
                   "${env:ProgramFiles(x86)}\OpenSSH")) {
    if ($d -and (Test-Path (Join-Path $d $name))) { return (Join-Path $d $name) }
  }
  $c = Get-Command $name -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  return "$env:WINDIR\System32\OpenSSH\$name"
}
$SSH    = Find-Exe 'ssh.exe'
$KEYGEN = Find-Exe 'ssh-keygen.exe'
# The name this box registers under. The VERIFY call at the end MUST use the
# identical string or the VPS looks up a different machine's port.
$HOSTTAG = $env:COMPUTERNAME

# ===================== proof, not paperwork ==========================
# Everything below exists because a step that reports success without checking
# the thing it claims is worse than no step at all: it turns an unreachable box
# into a green screenshot, and nobody looks again for days.

# A download that did not throw is NOT the file you asked for. An office proxy
# answers a blocked host with an HTML notice and HTTP 200 -- Invoke-WebRequest
# calls that success, and msiexec then rejects it with an exit code nobody was
# reading. Check the length and the magic bytes, or do not bother downloading.
function Get-Validated($url, $path, $magic, $minBytes) {
  Remove-Item $path -Force -ErrorAction SilentlyContinue
  Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing -TimeoutSec 180 -ErrorAction Stop
  if (-not (Test-Path $path)) { throw "nothing was written to $path" }
  $len = (Get-Item $path).Length
  if ($len -lt $minBytes) { throw "got $len bytes, expected over $minBytes - that is a block page, not the file" }
  $head = New-Object byte[] $magic.Count
  $fs = [IO.File]::OpenRead($path)
  try { $null = $fs.Read($head, 0, $magic.Count) } finally { $fs.Dispose() }
  for ($i = 0; $i -lt $magic.Count; $i++) {
    if ($head[$i] -ne $magic[$i]) {
      throw ("wrong file type (starts {0}) - a block or error page, not the file" -f (($head | ForEach-Object { '{0:X2}' -f $_ }) -join ' '))
    }
  }
}

# The bar the VPS monitor uses, applied locally. A service in state Running is
# not evidence that anything answers on port 22: sshd runs happily with no host
# keys, with a config it cannot parse, or with another process holding the port
# -- all identical in Get-Service, none of them lets a human in.
function Test-SshBanner($sshPort, $tries) {
  for ($i = 0; $i -lt $tries; $i++) {
    try {
      $c = New-Object Net.Sockets.TcpClient
      $ar = $c.BeginConnect('127.0.0.1', $sshPort, $null, $null)
      if ($ar.AsyncWaitHandle.WaitOne(3000)) {
        $c.EndConnect($ar)
        $st = $c.GetStream(); $st.ReadTimeout = 4000
        $buf = New-Object byte[] 64
        $n = $st.Read($buf, 0, 64)
        if ($n -gt 0 -and [Text.Encoding]::ASCII.GetString($buf, 0, $n) -match '^SSH-') { $c.Close(); return $true }
      }
      $c.Close()
    } catch { }
    Start-Sleep 2
  }
  return $false
}

# One call to the VPS registrar. The registrar key is written, used and WIPED on
# every call -- it never sits on the box between calls, which is the whole point
# of generating this box's own tunnel key locally.
# Windows ssh.exe reliably RUNS the remote command and then sits on session
# teardown for ~160s -- measured on VICTUS, with and without -n. We need the
# reply, not a graceful exit: cap the wait and read the answer from a file.
function Invoke-Registrar($request, $timeoutMs) {
  if (-not $timeoutMs) { $timeoutMs = 45000 }
  $rk = "$DIR\reg_key"; $o = "$DIR\reg.out"; $e = "$DIR\reg.err"
  try {
    New-Item -ItemType Directory -Force -Path $DIR | Out-Null
    [IO.File]::WriteAllBytes($rk, [Convert]::FromBase64String($REGKEY_B64))
    Lock-KeyFile $rk
    $p = Start-Process -FilePath $SSH -NoNewWindow -PassThru -RedirectStandardOutput $o -RedirectStandardError $e `
         -ArgumentList @('-n','-i',$rk,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
                         '-o','StrictHostKeyChecking=accept-new','-o','ConnectTimeout=20',$VPS,$request)
    if (-not $p.WaitForExit($timeoutMs)) { $p.Kill() }
    return @(Get-Content $o -EA SilentlyContinue) + @(Get-Content $e -EA SilentlyContinue)
  } finally {
    Remove-Item $rk, $o, $e -Force -ErrorAction SilentlyContinue
  }
}
$sshRoutes = @()

Write-Host ""
Write-Host "  === JIVO VPS TUNNEL SETUP ===" -ForegroundColor White
Write-Host "  About a minute. Leave this window alone (do not click inside it)." -ForegroundColor Gray
Write-Host ""

# ---- 1. START the OpenSSH Server install IN THE BACKGROUND ----
# This is the only slow step (it pulls from Windows Update and has been measured
# at 14+ minutes on a throttled office line). Nothing below depends on it until
# the very end, so it runs in parallel instead of blocking everything.
$sshJob = $null
if (Get-Service sshd -ErrorAction SilentlyContinue) {
  $ok += 'openssh-server(already)'
} else {
  Write-Host "  OpenSSH Server not present - installing in the background while we continue..." -ForegroundColor Cyan
  $sshJob = Start-Job -ScriptBlock {
    $ProgressPreference = 'SilentlyContinue'
    try { Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -ErrorAction Stop | Out-Null; 'capability' }
    catch { "capability-failed: $($_.Exception.Message)" }
  }
}

# ---- 2. the ssh CLIENT, needed to dial out ----
Step 'openssh-client' {
  if (-not (Test-Path $SSH)) {
    $c = Get-WindowsCapability -Online -Name 'OpenSSH.Client*' -ErrorAction Stop
    if ($c.State -ne 'Installed') { Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0 -ErrorAction Stop | Out-Null }
  }
  if (-not (Test-Path $SSH)) { throw "ssh.exe not found at $SSH" }
}
# ---- 3. manager key, so Daman can actually log in once the tunnel is up ----
Step 'manager-key' {
  $admins = (Get-LocalGroupMember -Group 'Administrators' -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
  $script:iAmAdmin = $admins -contains "$env:COMPUTERNAME\$env:USERNAME"
  if ($script:iAmAdmin) { $f = "$env:ProgramData\ssh\administrators_authorized_keys" }
  else { $d="$env:USERPROFILE\.ssh"; New-Item -ItemType Directory -Force -Path $d | Out-Null; $f="$d\authorized_keys" }
  if (-not (Test-Path $f)) { New-Item -ItemType File -Path $f -Force -ErrorAction Stop | Out-Null }
  # APPEND only. These files can already hold other managers' keys.
  $have = @(Get-Content $f -ErrorAction SilentlyContinue)
  foreach ($k in $MANAGER_KEYS) { if ($have -notcontains $k) { Add-Content -Path $f -Value $k -Encoding ascii -ErrorAction Stop } }
  if ($script:iAmAdmin) { icacls.exe $f /inheritance:r /grant 'SYSTEM:F' /grant 'BUILTIN\Administrators:F' | Out-Null }
}
Step 'default-shell' {
  if (-not (Test-Path 'HKLM:\SOFTWARE\OpenSSH')) { New-Item -Path 'HKLM:\SOFTWARE\OpenSSH' -Force | Out-Null }
  New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell `
    -Value "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force -ErrorAction Stop | Out-Null
}

# ---- 4. this box's OWN tunnel key. Generated HERE; the private half never travels ----
$TUNKEY = "$DIR\id_ed25519"
Step 'tunnel-key' {
  New-Item -ItemType Directory -Force -Path $DIR | Out-Null
  # (OI)(CI) or files created inside inherit NOTHING and admins cannot manage the logs.
  icacls.exe $DIR /inheritance:r /grant 'SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administrators:(OI)(CI)F' | Out-Null
  # Which build last ran here, readable over the tunnel:
  #   ssh <box> "type C:\ProgramData\jivo-revtun\version.txt"
  # A photo of the summary block can be misread or cropped; this cannot. Written
  # early so it lands even if a later step fails -- knowing WHICH build failed is
  # exactly what you need when a step fails.
  Set-Content -Path "$DIR\version.txt" -Value ("{0}  installed {1}  by {2}" -f $TUNNEL_VER, (Get-Date -Format s), $env:USERNAME) -Encoding ascii -ErrorAction SilentlyContinue
  if (-not (Test-Path $TUNKEY)) {
    & $KEYGEN -t ed25519 -N '""' -f $TUNKEY -C "revtun-$env:COMPUTERNAME" -q 2>&1 | Out-Null
  }
  if (-not (Test-Path $TUNKEY)) { throw "key generation failed" }
  Lock-KeyFile $TUNKEY
}

# ---- 5. register with the VPS -> get this box a permanent private port ----
$PORT = $null
Step 'register-with-vps' {
  $pub  = (Get-Content "$TUNKEY.pub" -Raw).Trim()
  $pubB = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pub))
  # The registrar only accepts [A-Za-z0-9._-] in USER, and Windows usernames can
  # contain spaces (e.g. "khushwinder singh") -- sanitise or it is rejected.
  $u = ($env:USERNAME -replace '[^A-Za-z0-9._-]','_')
  $out = Invoke-Registrar "HOST=$HOSTTAG USER=$u KEY=$pubB"
  $m = ($out | Select-String -Pattern 'PORT=(\d+)' | Select-Object -First 1)
  if (-not $m) { throw "registrar said: $($out -join ' ')" }
  $script:PORT = [int]$m.Matches[0].Groups[1].Value
  Write-Host "  VPS assigned this PC port $script:PORT" -ForegroundColor Cyan
}

# ---- 6. the dialer + a scheduled task that keeps it alive forever ----
Step 'install-dialer' {
  if (-not $PORT) { throw "no port assigned - cannot install dialer" }
  $dialer = "$DIR\dial.ps1"
  @"
# JIVO reverse-tunnel dialer. Runs as SYSTEM from Task Scheduler, every minute.
# The task's MultipleInstances=IgnoreNew IS the lock: while this ssh is alive the
# next minute's run is skipped, so there is never more than one tunnel and no
# pile-up. If the link dies the task ends, and the next tick re-dials (<=60s).
`$log = '$DIR\revtun.log'
if ((Test-Path `$log) -and ((Get-Item `$log).Length -gt 1MB)) { Move-Item `$log "`$log.1" -Force }
& '$SSH' -N -T -n ``
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ``
  -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new ``
  -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=15 ``
  -i '$TUNKEY' -R 127.0.0.1:${PORT}:localhost:22 $VPS *>> `$log
"@ | Set-Content -Path $dialer -Encoding ascii

  # schtasks (not Register-ScheduledTask): the cmdlet failed 0x80070002 on Win11 26100.
  # /SC MINUTE /MO 1 also covers boot. Task Scheduler's DEFAULT multiple-instance policy
  # is IgnoreNew, which IS the lock -- while the tunnel ssh lives, the next tick is skipped.
  # $dialer lives under C:\ProgramData\jivo-revtun (no spaces) precisely so /TR needs
  # NO inner quotes. PowerShell 5.1 mangles embedded quotes passed to native exes --
  # escaping them here made schtasks lose /SC entirely ("Mandatory option 'sc' is missing").
  # FULL path to powershell.exe. Bare "powershell" made the SYSTEM task fail
  # 0x80070002 (file not found) -- SYSTEM does not resolve it from PATH here.
  $psExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
  $tr = "$psExe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $dialer"
  if ($dialer -match '\s') { throw "dialer path contains a space: $dialer" }
  $r = schtasks /Create /TN JivoRevTunnel /TR $tr /SC MINUTE /MO 1 /RU SYSTEM /RL HIGHEST /F 2>&1
  if ($LASTEXITCODE -ne 0) { throw "schtasks failed: $r" }
  # Default execution time limit is 72h, which would silently drop the tunnel every 3
  # days. Best-effort lift it; if this fails the 1-min re-dial still recovers in <=60s.
  try { Set-ScheduledTask -TaskName 'JivoRevTunnel' -Settings (New-ScheduledTaskSettingsSet `
        -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable `
        -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries) -EA Stop | Out-Null }
  catch { Write-Host "  note: could not lift the 72h task limit ($($_.Exception.Message))" -ForegroundColor Yellow }
  try { Set-BootProof 'JivoRevTunnel' $true } catch { Write-Host "  note: boot-proofing the dialer failed ($($_.Exception.Message)); minute-repeat still covers reboot" -ForegroundColor Yellow }
}

# ---- 6b. harden: make it survive sleep, reboot, and tampering ----
Step 'harden-always-on' {
  powercfg /change standby-timeout-ac 0   | Out-Null
  powercfg /change hibernate-timeout-ac 0 | Out-Null
  powercfg /change monitor-timeout-ac 0   | Out-Null
  powercfg /change disk-timeout-ac 0      | Out-Null
  # Only force never-sleep on battery when there IS no battery -- on a laptop the
  # -dc settings would flatten it.
  if (-not (Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue)) {
    powercfg /change standby-timeout-dc 0   | Out-Null
    powercfg /change hibernate-timeout-dc 0 | Out-Null
  }
  powercfg /hibernate off 2>&1 | Out-Null          # also kills Fast Startup
  # Stop Windows powering down the NIC. Disable-NetAdapterPowerManagement -NoRestart
  # reports success and changes nothing readable until the adapter reinitialises
  # (measured on JIVO-B1), so set the durable registry control too. We never bounce
  # the adapter: losing the NIC on a remote box needs physical access to fix.
  $ck = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}'
  foreach ($a in (Get-NetAdapter -Physical -ErrorAction SilentlyContinue)) {
    Disable-NetAdapterPowerManagement -Name $a.Name -NoRestart -ErrorAction SilentlyContinue | Out-Null
    Get-ChildItem $ck -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d{4}$' } | ForEach-Object {
      $pp = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
      if ($pp.DriverDesc -eq $a.InterfaceDescription) {
        Set-ItemProperty -Path $_.PSPath -Name PnPCapabilities -Value 24 -Type DWord -Force -ErrorAction SilentlyContinue
      }
    }
  }
}
# ---- 6c. watchdog: repairs what the 1-minute dialer cannot ----
# The dialer recovers a DROPPED tunnel. It cannot recover from its own task being
# deleted or disabled, sshd stopped, or power settings drifting back after a
# Windows update. Verified on VICTUS: task deleted + tunnel killed -> watchdog
# rebuilt both and the VPS listener returned.
# sshd is the case it used to only PRETEND to repair (one Start-Service, no
# Automatic, no host keys, no check) -- see the block below, which now handles
# absent-vs-stopped, sets Automatic, runs ssh-keygen -A on a failed start,
# restarts a wedged sshd (at most once an hour), and refuses to call itself done
# until 127.0.0.1:22 answers with an SSH- banner -- the same bar the VPS monitor
# applies (fleet-tunnel-health.vps.sh, sshd_answers).
# The TUNNEL repair runs FIRST inside the generated script: sshd work touches a
# service that may be wedged, and it must never be able to cost this box its
# tunnel. See the ordering note in the script itself.
Step 'watchdog' {
  $wd = "$DIR\watchdog.ps1"
  $psExe2 = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
  $dialTr = "$psExe2 -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $DIR\dial.ps1"
  @"
`$ErrorActionPreference='SilentlyContinue'
`$log='$DIR\watchdog.log'
function L(`$m){ "`$(Get-Date -Format s) `$m" | Add-Content -Path `$log }
if ((Test-Path `$log) -and ((Get-Item `$log).Length -gt 1MB)) { Move-Item `$log "`$log.1" -Force }
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
# ---- 1. the dial task and the tunnel. FIRST, and the order is load-bearing ----
# This used to run LAST, after the sshd repair. The sshd repair touches a service
# that may be wedged, and a call that blocks there ends the run before this point
# -- leaving the TUNNEL unmaintained, which is strictly worse than never touching
# sshd at all: without the tunnel nothing about this box is reachable, sshd
# healthy or not. So the cheap, load-bearing work happens first and
# unconditionally, and sshd is best-effort behind it (in its own try/catch).
`$t = Get-ScheduledTask -TaskName 'JivoRevTunnel'
if (-not `$t) { L 'dial task MISSING - recreating'; schtasks /Create /TN JivoRevTunnel /TR "$dialTr" /SC MINUTE /MO 1 /RU SYSTEM /RL HIGHEST /F | Out-Null }
elseif (`$t.State -eq 'Disabled') { L 'dial task disabled - enabling'; Enable-ScheduledTask -TaskName 'JivoRevTunnel' }
`$alive = Get-CimInstance Win32_Process | Where-Object { `$_.Name -eq 'ssh.exe' -and `$_.CommandLine -match '127\.0\.0\.1:$PORT' }
if (-not `$alive) { L 'tunnel DOWN - kicking dialer'; schtasks /Run /TN JivoRevTunnel | Out-Null }
else { L 'tunnel up - ssh.exe is dialing VPS port $PORT' }
# ---- 2. sshd: the front door. Repairing it is the OTHER half of this watchdog ----
# A dead sshd is invisible from the VPS: the dialer, the task and the VPS
# listener all look perfect, so the monitor reports UNREACHABLE (port listens,
# nothing answers) instead of DOWN, and nobody is told. What lived here was one
# line -- if ((Get-Service sshd).Status -ne 'Running') { Start-Service sshd } --
# which (a) threw on a box that has no sshd at all, (b) never set StartupType,
# so a Manual service came back dead after every reboot and this played
# whack-a-mole forever, (c) gave up SILENTLY when Start-Service failed for
# missing host keys, which is the documented failure on these boxes (see 6d),
# and (d) never checked that anything ended up listening. Cost: DESKTOP-73N6JE8
# 23011, JIVO 23008 and JIVO201 23010 unreachable for 4+ days with this running
# every 15 minutes. So: repair every case, then PROVE it, and log both outcomes.
# When the last sshd restart happened, kept beside the log so it survives runs
# (each run is a fresh process; an in-memory variable would forget every time).
`$stamp='$DIR\sshd-restart.stamp'
function Test-Ssh22 {
  # Test the front door the way the VPS tests it -- not the service's own opinion
  # of itself, and not a bare TCP connect either. The monitor
  # (fleet-tunnel-health.vps.sh, sshd_answers) calls a box UP only when the first
  # line off the socket starts with 'SSH-'. A wedged sshd ACCEPTS the connection
  # and then never speaks: connect-only would log 'ok' on exactly the box the
  # monitor is reporting UNREACHABLE, which is the divergence this watchdog
  # exists to close. So: connect, then read the banner.
  # TWO probes 1.5s apart, because what we do about a failure is RESTART sshd,
  # and a restart drops live sessions: two failures 1.5s apart mean the door is
  # genuinely shut, so there is no session left to drop.
  # BeginConnect+WaitOne, not Connect: a connect to a filtered port can hang far
  # past any task time limit. On a REFUSED port WaitOne returns true at once and
  # EndConnect throws -- which is why the try/catch is inside the loop.
  for (`$i=0; `$i -lt 2; `$i++) {
    if (`$i) { Start-Sleep -Milliseconds 1500 }
    `$c = `$null
    try {
      `$c = New-Object Net.Sockets.TcpClient
      `$a = `$c.BeginConnect('127.0.0.1',22,`$null,`$null)
      if (`$a.AsyncWaitHandle.WaitOne(3000,`$false)) {
        `$c.EndConnect(`$a)
        # ReceiveTimeout is what bounds a connected-but-silent sshd: without it
        # Read() waits for a peer that is never going to speak. It throws on
        # expiry, and the catch below scores that as a failed probe.
        `$c.ReceiveTimeout = 5000
        `$buf = New-Object byte[] 4
        `$got = 0
        # Read may hand back fewer bytes than asked for; each call is bounded by
        # ReceiveTimeout, so this cannot spin (worst case ~20s per probe).
        while (`$got -lt 4) {
          `$r = `$c.GetStream().Read(`$buf,`$got,4-`$got)
          if (`$r -le 0) { break }
          `$got += `$r
        }
        if ((`$got -eq 4) -and ([Text.Encoding]::ASCII.GetString(`$buf) -eq 'SSH-')) { `$c.Close(); return `$true }
      }
    } catch { }
    if (`$c) { `$c.Close() }
  }
  return `$false
}
function Get-Port22Listener {
  # Whoever actually holds 22, by name, AND on which address. Seen from the VPS,
  # "sshd wedged", "port stolen by other software", "service dead" and "sshd
  # bound to the wrong address" are one identical symptom; here they are four
  # different repairs, and this is the only thing that tells them apart.
  # LocalAddress is not optional: the reverse tunnel forwards to 127.0.0.1:22, so
  # an sshd with a ListenAddress of (say) 192.168.1.x is Running and Listening
  # and still refuses the loopback connect. Filtering on the port alone read that
  # as "nobody home" and bounced a healthy service every 15 minutes forever
  # without ever naming the real fault.
  `$o = New-Object psobject -Property @{ Name=''; Loopback=`$false; Addresses='' }
  `$c = @(Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue)
  if (`$c.Count -eq 0) { return `$o }
  # 0.0.0.0 and :: are all-interfaces binds and DO cover loopback.
  `$lb = @(`$c | Where-Object { @('127.0.0.1','::1','0.0.0.0','::') -contains `$_.LocalAddress })
  `$o.Loopback  = (`$lb.Count -gt 0)
  `$o.Addresses = ((`$c | ForEach-Object { `$_.LocalAddress }) -join ',')
  `$own = if (`$lb.Count -gt 0) { `$lb[0] } else { `$c[0] }
  `$p = Get-Process -Id `$own.OwningProcess -ErrorAction SilentlyContinue
  if (`$p) { `$o.Name = `$p.ProcessName } else { `$o.Name = "pid `$(`$own.OwningProcess)" }
  return `$o
}
function Stop-SshdBounded {
  # NOT Stop-Service -Force: it has no deadline, and a wedged service is exactly
  # where it blocks. Nothing here may hang -- the task's ExecutionTimeLimit is no
  # safety net (schtasks /Create defaults to 72h and the 10-minute setting is
  # applied best-effort afterwards, with a warning on failure).
  # ServiceController.Stop() only SENDS the control and returns; the wait is a
  # separate call that takes a timespan. WaitForStatus THROWS on expiry, so the
  # timeout is caught, logged, and we go on to the start attempt instead of
  # hanging. A start over a stuck-stopping service may fail -- that is logged too,
  # and a logged failure beats a run that never ends.
  `$sc = Get-Service sshd -ErrorAction SilentlyContinue
  if (-not `$sc) { L 'stop skipped - no sshd service object'; return }
  if (`$sc.Status -eq 'Stopped') { L 'sshd already stopped - nothing to stop'; return }
  try { `$sc.Stop() } catch { L "sshd stop control refused: `$(`$_.Exception.Message)" }
  try {
    `$sc.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Stopped, (New-TimeSpan -Seconds 20))
    L 'sshd stopped'
  } catch {
    L 'sshd did NOT stop within 20s (wedged, not merely busy) - not waiting any longer, trying the start'
  }
}
function Invoke-Repair(`$why) {
  # The repair tool: the same ladder the installer runs (stray/wedged sshd.exe,
  # service registration, host keys + ACLs, sshd_config) minus the reinstall --
  # downloading OpenSSH from a SYSTEM task behind a colleague's back is not ours
  # to do. Every rung it takes lands in this log. JIVO_SSHD_LOCK_HELD tells it
  # this run already holds the repair lock, so it does not wait on its parent.
  `$rep = '$DIR\sshd-repair.ps1'
  if (-not (Test-Path `$rep)) { L "`$why - sshd-repair.ps1 is missing; re-run JIVO-VPS-TUNNEL.cmd on this PC to install it"; return }
  L "`$why - running sshd-repair.ps1 -NoReinstall"
  & "`$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File `$rep -NoReinstall 2>&1 | ForEach-Object { L "  repair: `$_" }
}
function Start-Sshd(`$why) {
  # One start; if it refuses, the ssh-keygen -A retry; if THAT refuses, the repair
  # tool. Nothing in here returns early before the tool: whether the ladder runs
  # must not depend on whether ssh-keygen happened to be found. Always logs the
  # REAL error text: 'sshd down - starting' told us nothing for four days.
  `$e = `$null
  Start-Service sshd -ErrorAction SilentlyContinue -ErrorVariable e
  if ((Get-Service sshd).Status -eq 'Running') { L "`$why - started"; return }
  L "`$why - Start-Service FAILED: `$(if(`$e){`$e[0].Exception.Message}else{'no error text'})"
  # Missing host keys are THE documented reason a start fails here. -A creates only
  # what is missing. Resolved at RUN time (this runs as SYSTEM, no OpenSSH on PATH)
  # across every place an install route can put it.
  `$kg = @('$KEYGEN', "`$env:WINDIR\System32\OpenSSH\ssh-keygen.exe", "`$env:ProgramFiles\OpenSSH\ssh-keygen.exe", "`$env:ProgramFiles\OpenSSH-Win64\ssh-keygen.exe", "`$env:ProgramFiles\OpenSSH-ARM64\ssh-keygen.exe") | Where-Object { `$_ -and (Test-Path `$_) } | Select-Object -First 1
  if (`$kg) {
    `$kd = "`$env:ProgramData\ssh"
    if (-not (Test-Path `$kd)) {
      # ssh-keygen -A fails outright without this directory. Create it LOCKED: an
      # inherited ProgramData ACL leaves the new PRIVATE host keys readable by Users,
      # and sshd refuses to start on a host key with open permissions.
      New-Item -ItemType Directory -Force -Path `$kd | Out-Null
      icacls.exe `$kd /inheritance:r /grant 'SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administrators:(OI)(CI)F' | Out-Null
    }
    L "running '`$kg -A' (missing host keys) and retrying the start"
    & `$kg -A 2>&1 | Out-Null
    `$e = `$null
    Start-Service sshd -ErrorAction SilentlyContinue -ErrorVariable e
    if ((Get-Service sshd).Status -eq 'Running') { L 'started after ssh-keygen -A'; return }
    L "STILL not running after ssh-keygen -A: `$(if(`$e){`$e[0].Exception.Message}else{'no error text'})"
  } else { L 'ssh-keygen.exe not found in any OpenSSH directory - skipping host-key regeneration, going straight to the repair tool' }
  Invoke-Repair "`$why"
}
# The whole sshd repair sits in ONE try/catch. It is best-effort plumbing behind
# the tunnel work, which has already run; an exception in here must produce a log
# line, not a dead run.
# One sshd repair at a time. The installer's ladder (sshd-repair.ps1) holds
# Global\JivoSshdRepair for its whole run; while it does, this section steps
# aside instead of stopping/starting the same service underneath it. When THIS
# run calls the tool, JIVO_SSHD_LOCK_HELD=1 tells the child not to wait on a
# lock its own parent is holding.
`$mx = New-Object System.Threading.Mutex(`$false, 'Global\JivoSshdRepair')
`$haveLock = `$false
try { `$haveLock = `$mx.WaitOne(2000) } catch [System.Threading.AbandonedMutexException] { `$haveLock = `$true }
if (-not `$haveLock) { L 'sshd section skipped - another repair (the installer or sshd-repair.ps1) holds the lock right now' }
else {
`$env:JIVO_SSHD_LOCK_HELD = '1'
try {
try {
  `$svc = Get-Service sshd -ErrorAction SilentlyContinue
  if (-not `$svc) {
    # ABSENT is not STOPPED -- there is nothing to start. Installing OpenSSH from an
    # unattended SYSTEM task is not something to do behind a colleague's back (the
    # capability pull has been measured at 14+ min and the MSI fallback needs the
    # internet), so say so every single run: this log is the only place it shows.
    L 'sshd NOT INSTALLED - the watchdog cannot repair that; re-run JIVO-VPS-TUNNEL.cmd on this PC. UNREACHABLE until then.'
  } else {
    # Automatic FIRST, before any start attempt: a Manual or Disabled sshd is dead
    # again at the next reboot, and restarting it every 15 min forever is not a fix.
    # Win32_Service.StartMode, not Get-Service's .StartType -- that property is
    # missing on older PowerShell 5.1 builds and would read empty on exactly the
    # old boxes this is meant to save. StartMode is 'Auto'/'Manual'/'Disabled'.
    `$mode = (Get-CimInstance Win32_Service -Filter "Name='sshd'" -ErrorAction SilentlyContinue).StartMode
    if (`$mode -and `$mode -ne 'Auto') {
      L "sshd StartMode=`$mode - setting Automatic (Manual means it dies again at the next reboot)"
      Set-Service -Name sshd -StartupType Automatic
      `$m2 = (Get-CimInstance Win32_Service -Filter "Name='sshd'" -ErrorAction SilentlyContinue).StartMode
      if (`$m2 -ne 'Auto') { L "could NOT set sshd Automatic (still `$m2) - it will be dead again after the next reboot" }
    }
    `$tried = `$false
    if (`$svc.Status -ne 'Running') { Start-Sshd "sshd `$(`$svc.Status)"; `$tried = `$true }
    # Outcome, EVERY run, pass or fail. A watchdog whose log cannot tell "fixed it"
    # from "gave up" is the reason four days went by unnoticed; and the pass line
    # doubles as the heartbeat that proves the task itself is still firing, which
    # a silent log can never prove.
    if (Test-Ssh22) { L "ok - sshd `$((Get-Service sshd).Status), 127.0.0.1:22 answered with an SSH- banner" }
    else {
      `$lsn  = Get-Port22Listener
      `$who  = `$lsn.Name
      `$addr = if (`$lsn.Addresses) { `$lsn.Addresses } else { 'none' }
      if (`$who -and (`$who -ne 'sshd')) {
        # Somebody else's software owns 22, so sshd can never bind it and no amount
        # of restarting helps. We do NOT kill that process -- it is a colleague's
        # software, not our plumbing. Name it and let a human decide.
        L "SSHD BROKEN - '`$who' is holding port 22 (listening on `$addr), sshd cannot bind it. THIS PC IS UNREACHABLE until that process is stopped (a restart would not help, so we do not try)."
      } elseif ((`$who -eq 'sshd') -and (-not `$lsn.Loopback)) {
        # sshd is up and listening, just nowhere the tunnel can reach it: a
        # ListenAddress line in %ProgramData%\ssh\sshd_config binds one NIC only,
        # while the reverse tunnel forwards to 127.0.0.1:22. Restarting cannot
        # change a config file, so name the actual fault instead of bouncing the
        # service every 15 minutes forever.
        L "SSHD BROKEN - sshd is listening on `$addr only, NOT on 127.0.0.1, and the tunnel forwards to 127.0.0.1:22 (a ListenAddress or Port line in %ProgramData%\ssh\sshd_config). Running the repair tool: it disables that line and restarts sshd."
        Invoke-Repair 'sshd off-loopback'
      } elseif (`$tried) {
        # Start + ssh-keygen -A already ran this pass and the door is still shut;
        # bouncing the service again in the same 15-minute pass just churns it.
        L "SSHD BROKEN - start and ssh-keygen -A already tried this run, service `$((Get-Service sshd).Status), listener `$addr, 127.0.0.1:22 still dead. THIS PC IS UNREACHABLE - needs a human: 'ssh-keygen -A', 'Start-Service sshd', 'Get-NetTCPConnection -LocalPort 22'."
      } else {
        # The service says Running and the door does not open: sshd is WEDGED. This
        # is the state the old watchdog scored as healthy and left alone forever.
        # Restarting is safe here precisely because Test-Ssh22 probed twice -- if 22
        # gives no banner twice there is no usable session to drop.
        # At most ONE bounce an hour, remembered across runs in a stamp file beside
        # this log: a restart every 15 minutes forever is not a repair, it is a loop
        # that hides a permanent fault and kills any session a human just got in on.
        # The stamp's LastWriteTime is the clock -- no date parsing, so no locale
        # setting on any box can break it.
        `$last = (Get-Item `$stamp -ErrorAction SilentlyContinue).LastWriteTime
        `$mins = 9999
        # Parens around the whole member access, not just the subtraction: casting
        # a TimeSpan to [int] fails, `$mins would land null, and null -lt 60 is TRUE
        # -- i.e. a typo here would silently disable every restart, forever.
        if (`$last) { `$mins = [int](((Get-Date) - `$last).TotalMinutes) }
        if (`$mins -lt 60) {
          L "SSHD BROKEN - sshd says `$(`$svc.Status) but 127.0.0.1:22 gave no SSH- banner on two probes (listener: `$addr); last restart was `$mins min ago, SKIPPING (at most one restart an hour). THIS PC IS UNREACHABLE - restarting has not fixed it, so it needs a human."
        } else {
          L "sshd says `$(`$svc.Status) but 127.0.0.1:22 gave no SSH- banner on two probes (listener: `$addr) - restarting sshd"
          # Stamped BEFORE the bounce, so a restart that goes badly still counts
          # against the hourly budget.
          Set-Content -Path `$stamp -Value (Get-Date -Format s)
          Stop-SshdBounded
          Start-Sshd 'sshd restart'
          if (Test-Ssh22) { L 'FIXED - 127.0.0.1:22 answering with an SSH- banner after restart' }
          else { L "SSHD BROKEN - the restart did not fix it, service `$((Get-Service sshd).Status), 127.0.0.1:22 still silent. THIS PC IS UNREACHABLE." }
        }
      }
    }
  }
} catch {
  L "sshd repair ERRORED and was abandoned: `$(`$_.Exception.Message) - the tunnel maintenance above already ran, so the box is only unreachable if sshd itself is down."
}
} finally { try { `$mx.ReleaseMutex() } catch { } }
}
"@ | Set-Content -Path $wd -Encoding ascii
  if ($wd -match '\s') { throw "watchdog path has a space: $wd" }
  $r = schtasks /Create /TN JivoTunnelWatchdog /TR "$psExe2 -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $wd" /SC MINUTE /MO 15 /RU SYSTEM /RL HIGHEST /F 2>&1
  if ($LASTEXITCODE -ne 0) { throw "watchdog schtasks failed: $r" }
  try { Set-BootProof 'JivoTunnelWatchdog' $false } catch { Write-Host "  note: boot-proofing the watchdog failed ($($_.Exception.Message))" -ForegroundColor Yellow }
}

# ---- 6c2. the sshd REPAIR TOOL, shared by this installer and the watchdog ----
# Written BEFORE 6d so the step that needs it can call it, and kept on the box so
# the watchdog (every 15 min, as SYSTEM) and a human (as admin) can run the same
# ladder. A single-quoted here-string: nothing in it is interpolated here, the
# only substitution is the @@DIR@@ placeholder. Usage and rungs are documented
# in the file's own header.
Step 'sshd-repair-tool' {
  New-Item -ItemType Directory -Force -Path $DIR | Out-Null
  $tool = @'
# JIVO sshd repair tool -- written to C:\ProgramData\jivo-revtun by JIVO-VPS-TUNNEL.cmd.
# Run by the installer (full ladder) and by the watchdog (-NoReinstall, every 15 min).
#   exit 0 = 127.0.0.1:22 answers with an SSH- banner (the bar the VPS monitor applies)
#   exit 1 = still dead; the lines it printed say exactly what it saw and what it tried
# Rungs, in order, each followed by a start attempt and a banner probe:
#   0 already answering?   1 diagnose (service, exe, port 22, host keys, sshd -t, events)
#   2 another process on 22 / stray or wedged sshd.exe   3 service registration
#   4 host keys + permissions   5 sshd_config   6 reinstall from the ZIP
# One repair at a time: a named mutex (Global\JivoSshdRepair) keeps the installer's
# ladder and the watchdog from stopping/starting sshd or rewriting sshd_config together.
# WHY: on 2026-08-21 DESKTOP-73N6JE8 ran v7, the tunnel parked, and sshd "refused to
# start" -- the installer's only reply was 'ssh-keygen -A, then Start-Service', both of
# which it had just done itself. Nothing named the fault and nothing tried the next thing.
# Manual use, as admin:  powershell -File C:\ProgramData\jivo-revtun\sshd-repair.ps1 [-DiagnoseOnly]
param([switch]$NoReinstall, [switch]$DiagnoseOnly)
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$DIR = '@@DIR@@'
$log = "$DIR\sshd-repair.log"
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 1MB)) { Move-Item $log "$log.1" -Force }
# Write-Host, NOT Write-Output: a logger that writes to the output stream pollutes its
# caller's return value (Try-Start would hand back @('<line>', $false), which is TRUE,
# and the ladder would stop at the first rung claiming success). A child powershell.exe's
# Write-Host still reaches the parent's pipe, so the installer and the watchdog capture
# every line unchanged.
function Trail($m) { "$(Get-Date -Format s) $m" | Add-Content -Path $log -EA SilentlyContinue; Write-Host $m }
function Short($s) { $s = ("$s" -replace '\s+', ' ').Trim(); if ($s.Length -gt 240) { $s.Substring(0, 240) } else { $s } }
$mx = $null
function Done($code) { if ($mx) { try { $mx.ReleaseMutex() } catch { } }; exit $code }
if (-not $DiagnoseOnly -and ($env:JIVO_SSHD_LOCK_HELD -ne '1')) {
  $mx = New-Object System.Threading.Mutex($false, 'Global\JivoSshdRepair')
  $have = $false
  try { $have = $mx.WaitOne(180000) } catch [System.Threading.AbandonedMutexException] { $have = $true }
  if (-not $have) { $mx = $null; Trail 'another sshd repair (installer or watchdog) has held the lock for 3 minutes - not starting a second one'; Done 1 }
}

function Test-Banner {
  # Two probes 1.5s apart; connect AND read 'SSH-'. A wedged sshd accepts and never speaks.
  for ($i = 0; $i -lt 2; $i++) {
    if ($i) { Start-Sleep -Milliseconds 1500 }
    $c = $null
    try {
      $c = New-Object Net.Sockets.TcpClient
      $a = $c.BeginConnect('127.0.0.1', 22, $null, $null)
      if ($a.AsyncWaitHandle.WaitOne(3000, $false)) {
        $c.EndConnect($a)
        $c.ReceiveTimeout = 5000
        $buf = New-Object byte[] 4; $got = 0
        while ($got -lt 4) { $r = $c.GetStream().Read($buf, $got, 4 - $got); if ($r -le 0) { break }; $got += $r }
        if (($got -eq 4) -and ([Text.Encoding]::ASCII.GetString($buf) -eq 'SSH-')) { $c.Close(); return $true }
      }
    } catch { }
    if ($c) { $c.Close() }
  }
  return $false
}
function Test-OurSshdPath($path) {
  # Ours = the registered service binary, or any sshd.exe under an OpenSSH directory.
  # A Cygwin / Git-for-Windows sshd is somebody else's and is never touched.
  if (-not $path) { return $false }
  if ($script:exe -and ($path -ieq $script:exe)) { return $true }
  return [bool]($path -match '\\OpenSSH(-Win64|-ARM64)?\\sshd\.exe$')
}
function Get-Port22 {
  @(Get-NetTCPConnection -LocalPort 22 -State Listen -EA SilentlyContinue) | ForEach-Object {
    $p = Get-Process -Id $_.OwningProcess -EA SilentlyContinue
    $path = $null; if ($p) { try { $path = $p.Path } catch { } }
    New-Object psobject -Property @{ Addr = $_.LocalAddress; Pid = $_.OwningProcess; Path = $path; Ours = (Test-OurSshdPath $path)
                                     Name = $(if ($p) { $p.ProcessName } else { 'pid' }) }
  }
}
function Stop-OurSshd($why) {
  # By IMAGE PATH, never by name. Nothing is answering on 22 when this runs, so there is
  # no live session of ours to protect; a third-party sshd is not ours to kill.
  $ps = @(Get-Process -Name sshd -EA SilentlyContinue | Where-Object { $pp = $null; try { $pp = $_.Path } catch { }; Test-OurSshdPath $pp })
  if ($ps.Count) { $ps | Stop-Process -Force -EA SilentlyContinue; Start-Sleep 2; Trail "$why - killed $($ps.Count) sshd.exe process(es) belonging to our OpenSSH" }
  else { Trail "$why - no sshd.exe of ours to kill" }
}
function Get-ExePath($pathName) {
  $p = "$pathName".Trim()
  if (-not $p) { return '' }
  if ($p.StartsWith('"')) { $q = $p.IndexOf('"', 1); if ($q -gt 1) { return $p.Substring(1, $q - 1) } }
  if (Test-Path -LiteralPath $p) { return $p }
  $m = [regex]::Match($p, '^(.+?\.exe)', 'IgnoreCase')   # unquoted path with spaces and/or arguments
  if ($m.Success) { return $m.Groups[1].Value }
  return ($p -split ' ')[0]
}
function Find-Keygen {
  @("$env:WINDIR\System32\OpenSSH\ssh-keygen.exe", "$env:ProgramFiles\OpenSSH\ssh-keygen.exe",
    "$env:ProgramFiles\OpenSSH-Win64\ssh-keygen.exe", "$env:ProgramFiles\OpenSSH-ARM64\ssh-keygen.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
}
function Find-SshdExe {
  @("$env:WINDIR\System32\OpenSSH\sshd.exe", "$env:ProgramFiles\OpenSSH\sshd.exe",
    "$env:ProgramFiles\OpenSSH-Win64\sshd.exe", "$env:ProgramFiles\OpenSSH-ARM64\sshd.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
}
function Lock-File($path) {
  # Replace the whole DACL: sshd refuses a private key any extra SID can read.
  $acl = New-Object System.Security.AccessControl.FileSecurity
  $acl.SetAccessRuleProtection($true, $false)
  $acl.SetOwner([System.Security.Principal.NTAccount]'BUILTIN\Administrators')
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('NT AUTHORITY\SYSTEM', 'FullControl', 'Allow')))
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('BUILTIN\Administrators', 'FullControl', 'Allow')))
  Set-Acl -Path $path -AclObject $acl -ErrorAction Stop
}
function Test-Config($exe) {
  # 'sshd -t' loads the config AND the host keys and names the first thing it cannot live with.
  $script:cfgExit = 0
  try { $o = (& $exe -t 2>&1 | ForEach-Object { "$_" }) -join ' | '; $script:cfgExit = $LASTEXITCODE } catch { $o = $_.Exception.Message; $script:cfgExit = 1 }
  return (Short $o)
}
function Get-LastErrors {
  $since = (Get-Date).AddMinutes(-20)
  $out = @()
  try { $out += Get-WinEvent -FilterHashtable @{ LogName = 'OpenSSH/Operational'; StartTime = $since } -MaxEvents 4 -EA Stop |
          ForEach-Object { "OpenSSH $($_.TimeCreated.ToString('HH:mm:ss')) $(Short $_.Message)" } } catch { }
  try { $out += Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Service Control Manager'; StartTime = $since } -MaxEvents 60 -EA Stop |
          Where-Object { $_.Message -match 'sshd|OpenSSH' } | Select-Object -First 3 |
          ForEach-Object { "SCM $($_.TimeCreated.ToString('HH:mm:ss')) $(Short $_.Message)" } } catch { }
  $out
}
function Write-Lines($path, $lines) {
  # UTF-8 without BOM: sshd reads it, and nothing in an existing config gets turned into '?'.
  [IO.File]::WriteAllLines($path, [string[]]$lines, (New-Object System.Text.UTF8Encoding($false)))
}
function Test-OffTarget($line) {
  # sshd_config lines that keep sshd alive but NOT on 127.0.0.1:22, where the tunnel lands.
  if ($line -match '^\s*Port\s+(\S+)') { return ($Matches[1] -ne '22') }
  if ($line -match '^\s*ListenAddress\s+(\S+)') {
    $v = $Matches[1]; $hst = $v; $prt = $null
    if ($v -match '^\[(.*)\]:(\d+)$') { $hst = $Matches[1]; $prt = $Matches[2] }
    elseif ($v -match '^(\d+\.\d+\.\d+\.\d+):(\d+)$') { $hst = $Matches[1]; $prt = $Matches[2] }
    if ($prt -and ($prt -ne '22')) { return $true }
    return (@('0.0.0.0', '127.0.0.1', '::', '::1', 'localhost') -notcontains $hst)
  }
  return $false
}
function Try-Start($why) {
  $sc = Get-Service sshd -EA SilentlyContinue
  if (-not $sc) { Trail "$why - no sshd service to start"; return $false }
  if ($sc.Status -ne 'Stopped') {
    try { $sc.Stop() } catch { }
    try { $sc.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Stopped, (New-TimeSpan -Seconds 20)) }
    catch { Stop-OurSshd 'sshd did not stop within 20s' }
  }
  $e = $null
  Start-Service sshd -EA SilentlyContinue -ErrorVariable e
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while (((Get-Service sshd).Status -ne 'Running') -and ($sw.Elapsed.TotalSeconds -lt 10)) { Start-Sleep 1 }
  $st = (Get-Service sshd).Status
  if (($st -eq 'Running') -and (Test-Banner)) { Trail "$why - sshd Running and 127.0.0.1:22 answers with an SSH- banner"; return $true }
  $detail = if ($e) { ": $(Short $e[0].Exception.Message)" } elseif ($st -eq 'Running') { ', but no SSH- banner on 127.0.0.1:22' } else { '' }
  Trail "$why - sshd $st$detail"
  return $false
}

Trail "---- sshd repair start (NoReinstall=$NoReinstall DiagnoseOnly=$DiagnoseOnly, as $env:USERNAME) ----"
if ((-not $DiagnoseOnly) -and (Test-Banner)) { Trail 'ok - 127.0.0.1:22 already answers with an SSH- banner, nothing to repair'; Done 0 }

# ---- 1. diagnose: say what is there before touching anything ----
$needInstall = $false; $script:exe = ''; $exeOk = $false; $ci = $null; $regMissing = $false
$svc = Get-Service sshd -EA SilentlyContinue
if (-not $svc) {
  Trail 'service: NO sshd service is registered'
  $needInstall = $true
  $script:exe = Find-SshdExe
} else {
  $ci = Get-CimInstance Win32_Service -Filter "Name='sshd'" -EA SilentlyContinue
  if ($ci) { $script:exe = Get-ExePath $ci.PathName } else { Trail 'service: Win32_Service could not be read (WMI) - using the known OpenSSH locations instead' }
  if (-not ($script:exe -and (Test-Path -LiteralPath $script:exe))) {
    $alt = Find-SshdExe
    if ($script:exe -and $alt) { Trail "service: the registered binary '$script:exe' is MISSING but $alt exists - the service will be re-pointed at it"; $regMissing = $true }
    if ($alt) { $script:exe = $alt }
  }
  $exeOk = [bool]($script:exe -and (Test-Path -LiteralPath $script:exe))
  Trail ("service: status={0} startmode={1} account={2} exe={3} exists={4}" -f $svc.Status, $(if ($ci) { $ci.StartMode } else { '?' }),
         $(if ($ci) { $ci.StartName } else { '?' }), $(if ($script:exe) { $script:exe } else { 'none found anywhere' }), $exeOk)
  # Only a binary that exists NOWHERE means reinstall; a failed WMI read does not.
  if (-not $exeOk) { $needInstall = $true }
}
$exe = $script:exe
$lsn = @(Get-Port22)
if ($lsn.Count) { Trail ("port 22: " + (($lsn | ForEach-Object { "$($_.Name)(pid $($_.Pid), $(if ($_.Ours) { 'ours' } else { 'NOT ours' })) on $($_.Addr)" }) -join ', ')) } else { Trail 'port 22: nobody listening' }
$kd = "$env:ProgramData\ssh"; $cfg = "$kd\sshd_config"
$keys = @(Get-ChildItem "$kd\ssh_host_*_key" -EA SilentlyContinue)
Trail ("host keys: " + $(if ($keys.Count) { ($keys | ForEach-Object { "$($_.Name)=$($_.Length)b" }) -join ' ' } else { 'NONE in ' + $kd }))
Trail ("sshd_config: " + $(if (Test-Path $cfg) { "present, $((Get-Item $cfg).Length)b" } else { 'MISSING' }))
if ($exeOk) { $t = Test-Config $exe; Trail ("sshd -t (exit $script:cfgExit): " + $(if ($t) { $t } else { 'clean' })) }
Get-LastErrors | ForEach-Object { Trail "event: $_" }
if ($DiagnoseOnly) { $up = Test-Banner; Trail "diagnose-only: 127.0.0.1:22 answers=$up"; if ($up) { Done 0 } else { Done 1 } }

# ---- 2. port 22: somebody else, a stray sshd.exe of ours, or a wedged service ----
$other = @($lsn | Where-Object { -not $_.Ours })
if ($other.Count) {
  Trail "BLOCKED - '$($other[0].Name)' (pid $($other[0].Pid), $(if ($other[0].Path) { $other[0].Path } else { 'path unreadable' })) is holding port 22, so sshd can never bind it. Not killing software that is not ours - a human must stop or reconfigure it."
  Done 1
}
if ($svc -and ($svc.Status -eq 'Stopped') -and (@($lsn | Where-Object { $_.Ours }).Count)) { Stop-OurSshd 'a stray sshd.exe of ours holds port 22 while the service is Stopped' }
if ($svc -and ("$($svc.Status)" -match 'Pending')) { Stop-OurSshd "sshd is $($svc.Status) (wedged)" }

# ---- 3. service registration: binary path, start mode, account, privileges, crash recovery ----
if ($svc -and $exeOk) {
  if ($regMissing) { $null = sc.exe config sshd binPath= "`"$exe`""; Trail "service binPath -> $exe (sc exit $LASTEXITCODE)" }
  if ($ci -and ("$($ci.StartMode)" -ne 'Auto')) { Set-Service -Name sshd -StartupType Automatic -EA SilentlyContinue; Trail "startmode $($ci.StartMode) -> Automatic" }
  if ($ci -and ("$($ci.StartName)" -notmatch '^(LocalSystem|NT AUTHORITY\\SYSTEM)$')) { $null = sc.exe config sshd obj= LocalSystem; Trail "service account '$($ci.StartName)' -> LocalSystem (sc exit $LASTEXITCODE)" }
  # the privilege set install-sshd.ps1 grants; a service stripped of SeTcb/SeAssignPrimaryToken cannot log anyone in
  $null = sc.exe privs sshd SeAssignPrimaryTokenPrivilege/SeTcbPrivilege/SeBackupPrivilege/SeRestorePrivilege/SeImpersonatePrivilege
  if ($LASTEXITCODE -ne 0) { Trail "sc privs was refused (exit $LASTEXITCODE)" }
  # let the SCM restart it if it crashes, instead of leaving it Stopped until the watchdog notices
  $null = sc.exe failure sshd reset= 86400 actions= restart/5000/restart/30000/restart/60000
  if ($LASTEXITCODE -ne 0) { Trail "sc failure was refused (exit $LASTEXITCODE)" }
  if (Try-Start 'rung 3 (service registration)') { Done 0 }
}

# ---- 4. host keys: missing, empty, or readable by the wrong people ----
if (-not (Test-Path $kd)) {
  New-Item -ItemType Directory -Force -Path $kd | Out-Null
  icacls.exe $kd /inheritance:r /grant 'SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administrators:(OI)(CI)F' | Out-Null
  Trail 'created %ProgramData%\ssh (locked to SYSTEM + Administrators)'
}
$zeroKeys = @(Get-ChildItem "$kd\ssh_host_*_key" -EA SilentlyContinue | Where-Object { $_.Length -eq 0 })
if ($zeroKeys.Count) {
  # a 0-byte key from an interrupted keygen: sshd cannot load it, and -A will not recreate a file that exists
  foreach ($k in $zeroKeys) { Remove-Item -LiteralPath $k.FullName -Force -EA SilentlyContinue; Remove-Item -LiteralPath "$($k.FullName).pub" -Force -EA SilentlyContinue }
  Trail ("removed {0} empty host key(s) and their .pub: {1}" -f $zeroKeys.Count, (($zeroKeys | ForEach-Object { $_.Name }) -join ' '))
}
$kg = Find-Keygen
if ($kg) { $null = & $kg -A 2>&1; Trail "ssh-keygen -A done ($kg, exit $LASTEXITCODE)" } else { Trail 'ssh-keygen.exe not found in any OpenSSH directory - cannot generate host keys' }
if ($kg) {
  # a 0-byte .pub beside a healthy private key: -A leaves it; derive it again
  Get-ChildItem "$kd\ssh_host_*_key.pub" -EA SilentlyContinue | Where-Object { $_.Length -eq 0 } | ForEach-Object {
    $priv = $_.FullName -replace '\.pub$', ''
    $pub = (& $kg -y -f $priv 2>&1 | ForEach-Object { "$_" }) -join ''
    if ($pub -match '^(ssh|ecdsa)-') { Set-Content -LiteralPath $_.FullName -Value $pub -Encoding ascii; Trail "regenerated empty $($_.Name)" }
  }
}
$locked = 0
Get-ChildItem "$kd\ssh_host_*_key" -EA SilentlyContinue | ForEach-Object { try { Lock-File $_.FullName; $locked++ } catch { Trail "could not lock $($_.Name): $($_.Exception.Message)" } }
Trail "host-key permissions reset on $locked file(s): SYSTEM + Administrators only"
if (-not @(Get-ChildItem "$kd\ssh_host_*_key" -EA SilentlyContinue).Count) { Trail 'still NO host keys after ssh-keygen -A - sshd cannot start without them' }
if ($exeOk -and (Try-Start 'rung 4 (host keys)')) { Done 0 }

# ---- 5. sshd_config: missing, rejected by sshd -t, or pointing sshd away from 127.0.0.1:22 ----
$arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'ARM64' } else { 'Win64' }
$def = @("$env:WINDIR\System32\OpenSSH\sshd_config_default", "$env:ProgramFiles\OpenSSH\sshd_config_default",
         "$env:ProgramFiles\OpenSSH-$arch\sshd_config_default") | Where-Object { Test-Path $_ } | Select-Object -First 1
$changed = $false; $bad = $false
if (-not (Test-Path $cfg)) { $bad = $true; Trail 'sshd_config is MISSING' }
elseif ($exeOk) {
  $t = Test-Config $exe
  # Only a message that names the CONFIG counts. 'no hostkeys available' and 'UNPROTECTED
  # PRIVATE KEY FILE' exit non-zero too, and they are host-key faults, not config faults.
  if (($t -match 'Bad configuration|Unsupported option|Missing argument|Directive .* is not allowed|line \d+') -and ($t -notmatch 'hostkey|host key|ssh_host_|PRIVATE KEY')) {
    $bad = $true; Trail "sshd_config rejected by 'sshd -t': $t"
  }
}
if ((-not $bad) -and (Test-Path $cfg)) {
  $txt = @(Get-Content $cfg)
  $off = @($txt | Where-Object { Test-OffTarget $_ })
  if ($off.Count) {
    Copy-Item $cfg "$cfg.bak-$(Get-Date -Format yyyyMMddHHmmss)" -Force
    Write-Lines $cfg @($txt | ForEach-Object { if ($off -contains $_) { "#jivo-disabled# $_" } else { $_ } })
    Trail ("disabled {0} sshd_config line(s) that put sshd somewhere other than 127.0.0.1:22, where the tunnel lands: {1}" -f $off.Count, ($off -join ' | '))
    $changed = $true
  }
}
if ($bad) {
  if (Test-Path $cfg) { Copy-Item $cfg "$cfg.broken-$(Get-Date -Format yyyyMMddHHmmss)" -Force }
  if ($def) { Copy-Item $def $cfg -Force; Trail "sshd_config replaced with the shipped default ($def); the old one is kept beside it as .broken-*" }
  else {
    Write-Lines $cfg @('Port 22', 'PubkeyAuthentication yes', 'PasswordAuthentication yes', 'AuthorizedKeysFile .ssh/authorized_keys',
      'Subsystem sftp sftp-server.exe', 'Match Group administrators',
      '       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys')
    Trail 'sshd_config rewritten from a minimal known-good template (no shipped default found on this PC)'
  }
  $changed = $true
}
if ((Test-Path $cfg) -and -not (Select-String -Path $cfg -Pattern '^\s*[^#].*administrators_authorized_keys' -Quiet)) {
  Add-Content -Path $cfg -Encoding ascii -Value "`r`nMatch Group administrators`r`n       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys"
  Trail 'sshd_config: added the missing administrators block'; $changed = $true
}
if ($exeOk -and $changed -and (Try-Start 'rung 5 (sshd_config)')) { Done 0 }

# ---- 6. reinstall: the ZIP route. install-sshd.ps1 deletes and recreates the service, so it is a clean slate ----
$dead = $needInstall -or ((Get-Service sshd -EA SilentlyContinue).Status -ne 'Running') -or (-not (Test-Banner))
if ($dead) {
  if ($NoReinstall) { Trail 'STILL DEAD after rungs 1-5; not reinstalling OpenSSH from the watchdog - re-run JIVO-VPS-TUNNEL.cmd on this PC'; Done 1 }
  Trail $(if ($needInstall) { 'sshd service/binary missing - installing OpenSSH from the ZIP' } else { 'sshd still refuses after rungs 1-5 - reinstalling OpenSSH from the ZIP (the service is deleted and recreated)' })
  try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $zurl = "https://github.com/PowerShell/Win32-OpenSSH/releases/download/10.0.0.0p2-Preview/OpenSSH-$arch.zip"
    try {
      $rel = Invoke-RestMethod -Uri 'https://api.github.com/repos/PowerShell/Win32-OpenSSH/releases/latest' -UseBasicParsing -TimeoutSec 30 -Headers @{ 'User-Agent' = 'jivo-fleet' }
      $z = ($rel.assets | Where-Object { $_.name -eq "OpenSSH-$arch.zip" } | Select-Object -First 1).browser_download_url
      if ($z) { $zurl = $z }
    } catch { }
    $zip = "$env:TEMP\openssh-$arch.zip"
    Remove-Item $zip -Force -EA SilentlyContinue
    Trail "downloading $zurl"
    Invoke-WebRequest -Uri $zurl -OutFile $zip -UseBasicParsing -TimeoutSec 180 -EA Stop
    $h = New-Object byte[] 4
    $fs = [IO.File]::OpenRead($zip)
    try { $null = $fs.Read($h, 0, 4) } finally { $fs.Dispose() }
    if (((Get-Item $zip).Length -lt 2000000) -or ($h[0] -ne 0x50) -or ($h[1] -ne 0x4B) -or ($h[2] -ne 0x03) -or ($h[3] -ne 0x04)) { throw "what came back from $zurl is not a zip (a proxy block page?)" }
    try { Stop-Service sshd -Force -EA SilentlyContinue } catch { }
    Stop-OurSshd 'before reinstall'
    Expand-Archive -LiteralPath $zip -DestinationPath $env:ProgramFiles -Force -EA Stop
    Remove-Item $zip -Force -EA SilentlyContinue
    $inst = "$env:ProgramFiles\OpenSSH-$arch\install-sshd.ps1"
    if (-not (Test-Path $inst)) { throw "install-sshd.ps1 missing at $inst" }
    # -Confirm:$false -- the script is ConfirmImpact=High and would otherwise stop to ask before fixing %ProgramData%\ssh permissions
    $ir = & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command "& '$inst' -Confirm:`$false" 2>&1
    if (-not (Get-Service sshd -EA SilentlyContinue)) { throw "install-sshd.ps1 said: $(Short ($ir -join ' '))" }
    $script:exe = Get-ExePath (Get-CimInstance Win32_Service -Filter "Name='sshd'" -EA SilentlyContinue).PathName
    $exe = $script:exe
    Trail "reinstalled - the service now points at $exe"
    Set-Service -Name sshd -StartupType Automatic -EA SilentlyContinue
    $kg = Find-Keygen
    if ($kg) { $null = & $kg -A 2>&1 }
    Get-ChildItem "$kd\ssh_host_*_key" -EA SilentlyContinue | ForEach-Object { try { Lock-File $_.FullName } catch { } }
    if (-not (Test-Path $cfg)) { $d2 = "$env:ProgramFiles\OpenSSH-$arch\sshd_config_default"; if (Test-Path $d2) { Copy-Item $d2 $cfg -Force; Trail 'sshd_config: installed the shipped default' } }
    if ((Test-Path $cfg) -and -not (Select-String -Path $cfg -Pattern '^\s*[^#].*administrators_authorized_keys' -Quiet)) {
      Add-Content -Path $cfg -Encoding ascii -Value "`r`nMatch Group administrators`r`n       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys"
    }
    if (Try-Start 'rung 6 (reinstall)') { Done 0 }
  } catch { Trail "reinstall failed: $(Short $_.Exception.Message)" }
}

# ---- verdict ----
if (Test-Banner) { Trail 'FIXED - 127.0.0.1:22 answers with an SSH- banner'; Done 0 }
$s = (Get-Service sshd -EA SilentlyContinue).Status
$l2 = @(Get-Port22)
Trail ("STILL DEAD - service {0}, port 22 {1}. Full trail: {2}" -f $(if ($s) { $s } else { 'absent' }),
   $(if ($l2.Count) { 'held by ' + (($l2 | ForEach-Object { "$($_.Name) on $($_.Addr)" }) -join ', ') } else { 'nobody listening' }), $log)
Get-LastErrors | ForEach-Object { Trail "event: $_" }
Done 1
'@
  Set-Content -Path "$DIR\sshd-repair.ps1" -Value $tool.Replace('@@DIR@@', $DIR) -Encoding ascii -ErrorAction Stop
  if (-not (Select-String -Path "$DIR\sshd-repair.ps1" -Pattern '^Done 1' -Quiet)) { throw "sshd-repair.ps1 was written truncated" }
}

# ---- 6d. make sshd EXIST, RUN, and ANSWER -- three independent routes ----
Step 'openssh-server' {
  # Collecting the background install is CONDITIONAL (there is only a job when we
  # started one). Making sshd actually RUN is NOT -- it must happen on every path.
  # This used to `return` early whenever $sshJob was null, i.e. on exactly the
  # 'openssh-server(already)' path, which skipped every line below: the service
  # was never set to Automatic, never started, host keys were never generated,
  # and the loud failure below could not fire. Result: the step printed OK on a
  # box that was unreachable (DESKTOP-73N6JE8 23011, 2026-08-13 -- and VICTUS
  # 23001 and JIVO 23008 found in the same state). Never re-add an early return.
  #
  # THREE routes, tried in order, each one RECORDING WHY IT FAILED. On 2026-08-19
  # JIVO201 (23010) had two routes fail and the whole step could say only "could
  # not be installed by either route": route 1's error died with the job it was
  # never received from, route 2's died because nobody read msiexec's exit code,
  # and the Desktop log is a Start-Transcript so neither ever reached it. An hour
  # went into re-deriving what the box already knew. Every reason now survives
  # into the summary block the operator photographs.
  $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'ARM64' } else { 'Win64' }

  # ---- route 1: Windows Update / the component store ----
  if ($sshJob) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sshJob.State -eq 'Running' -and $sw.Elapsed.TotalSeconds -lt 150) {
      Start-Sleep 10
      Write-Host ("    OpenSSH Server still installing... {0}s" -f [int]$sw.Elapsed.TotalSeconds) -ForegroundColor DarkGray
    }
    if ($sshJob.State -eq 'Running') {
      Write-Host "  Windows Update is too slow - switching to the direct installer." -ForegroundColor Yellow
      $script:sshRoutes += 'windows-update: still running at 150s, abandoned'
      Stop-Job $sshJob -ErrorAction SilentlyContinue
    } else {
      # RECEIVE the job. Without this the reason Windows Update refused went into
      # the bin with the job. A refusal that returns in ~15s is the 0x800f0954
      # WSUS/policy block, and that single string is the difference between
      # "why did it fail" and "office policy blocks the component store".
      $jr = (@(Receive-Job $sshJob -ErrorAction SilentlyContinue) -join ' ').Trim()
      if (Get-Service sshd -ErrorAction SilentlyContinue) { $script:sshRoutes += 'windows-update: ok' }
      else { $script:sshRoutes += ("windows-update: no sshd service - " + $(if ($jr) { $jr } else { 'the job said nothing' })) }
    }
    Remove-Job $sshJob -Force -ErrorAction SilentlyContinue
  } else {
    $script:sshRoutes += 'windows-update: skipped, sshd was already present'
  }

  # ---- route 2: Microsoft's signed MSI. No Windows Update, no component store,
  # so it also works where policy blocks 0x800f0954. ----
  if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) {
    try {
      # Resolve the asset from the API: a hardcoded /releases/latest/download/<file>
      # URL 404s the moment Microsoft cuts a new version -- measured, the pinned
      # v9.8.1.0 name was already dead while the latest release was v10.0.0.0.
      # The API is also the first thing an office proxy blocks (JIVO201 fell back),
      # so the pinned URL stays, and which one we used is recorded either way.
      [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
      $url = $null
      try {
        $rel = Invoke-RestMethod -Uri 'https://api.github.com/repos/PowerShell/Win32-OpenSSH/releases/latest' `
                 -UseBasicParsing -TimeoutSec 30 -Headers @{ 'User-Agent' = 'jivo-fleet' }
        $url = ($rel.assets | Where-Object { $_.name -like "OpenSSH-$arch-*.msi" } | Select-Object -First 1).browser_download_url
      } catch { $script:sshRoutes += "github-api: $($_.Exception.Message)" }
      if (-not $url) { $url = "https://github.com/PowerShell/Win32-OpenSSH/releases/download/10.0.0.0p2-Preview/OpenSSH-$arch-v10.0.0.0.msi" }
      $msi = "$env:TEMP\openssh-$arch.msi"; $mlog = "$env:TEMP\openssh-msi.log"
      Write-Host "  downloading $url" -ForegroundColor DarkGray
      Get-Validated $url $msi @(0xD0,0xCF,0x11,0xE0) 2000000      # D0 CF 11 E0 = a real MSI
      # -PassThru and the exit code. Without them msiexec 1603 (fatal), 1618
      # (another install running), 1620 (not a valid package) and 1638 (this
      # version already registered) were ALL indistinguishable from success --
      # the step just died one line later blaming "either route".
      $mp = Start-Process msiexec.exe -Wait -PassThru -ErrorAction Stop `
              -ArgumentList @('/i', "`"$msi`"", '/quiet', '/norestart', '/l*v', "`"$mlog`"")
      if ($mp.ExitCode -eq 1638) {
        # The product is registered but the service is gone -- an `sc delete sshd`,
        # or an uninstall that half-completed. A plain /i is a no-op in that state;
        # REINSTALL re-runs the custom actions that create the service.
        $script:sshRoutes += 'msi: 1638, product already registered - repairing'
        $mp = Start-Process msiexec.exe -Wait -PassThru -ErrorAction Stop `
                -ArgumentList @('/i', "`"$msi`"", 'REINSTALL=ALL', 'REINSTALLMODE=vomus', '/quiet', '/norestart', '/l*v', "`"$mlog`"")
      }
      if ($mp.ExitCode -ne 0 -and $mp.ExitCode -ne 3010) {
        $tail = ((Get-Content $mlog -EA SilentlyContinue | Where-Object { $_ -match 'Error|error status|failed' } | Select-Object -Last 2) -join ' | ')
        throw ("msiexec exit {0}{1}" -f $mp.ExitCode, $(if ($tail) { " -- $tail" } else { '' }))
      }
      Remove-Item $msi -Force -ErrorAction SilentlyContinue
      # A zero exit is NOT the same as "the service exists". Measured on JIVO201
      # 2026-08-19: msiexec reconfigured the package and returned 0, and there was
      # still no sshd service -- the ZIP route is what actually repaired that box.
      # Recording 'ok' off the exit code alone is the same lie this whole step
      # exists to stop telling, one level down.
      if (Get-Service sshd -ErrorAction SilentlyContinue) { $script:sshRoutes += 'msi: ok' }
      else { $script:sshRoutes += ("msi: exit {0} but NO sshd service was created" -f $mp.ExitCode) }
    } catch { $script:sshRoutes += "msi: $($_.Exception.Message)" }
  }

  # ---- route 3: the plain ZIP. No installer engine, no component store, no MSI
  # policy -- just files plus the bundled install-sshd.ps1. This is the route
  # that still works on a locked-down office box where the other two are shut. ----
  if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) {
    try {
      $zurl = "https://github.com/PowerShell/Win32-OpenSSH/releases/download/10.0.0.0p2-Preview/OpenSSH-$arch.zip"
      try {
        $rel2 = Invoke-RestMethod -Uri 'https://api.github.com/repos/PowerShell/Win32-OpenSSH/releases/latest' `
                  -UseBasicParsing -TimeoutSec 30 -Headers @{ 'User-Agent' = 'jivo-fleet' }
        $z = ($rel2.assets | Where-Object { $_.name -eq "OpenSSH-$arch.zip" } | Select-Object -First 1).browser_download_url
        if ($z) { $zurl = $z }
      } catch { }
      $zip = "$env:TEMP\openssh-$arch.zip"
      Write-Host "  downloading $zurl" -ForegroundColor DarkGray
      Get-Validated $zurl $zip @(0x50,0x4B,0x03,0x04) 2000000     # 50 4B 03 04 = PK.., a real zip
      Expand-Archive -LiteralPath $zip -DestinationPath $env:ProgramFiles -Force -ErrorAction Stop
      Remove-Item $zip -Force -ErrorAction SilentlyContinue
      $inst = Join-Path $env:ProgramFiles "OpenSSH-$arch\install-sshd.ps1"
      if (-not (Test-Path $inst)) { throw "install-sshd.ps1 missing at $inst" }
      # -Confirm:$false: install-sshd.ps1 is ConfirmImpact=High and, when it decides
      # %ProgramData%\ssh permissions need fixing, stops to ASK. Unattended, that is
      # a hang with no output -- exactly what this step must never do.
      $ir = & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command "& '$inst' -Confirm:`$false" 2>&1
      if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) { throw "install-sshd.ps1 said: $($ir -join ' ')" }
      $script:KEYGEN = Find-Exe 'ssh-keygen.exe'     # the zip route moved it
      $script:sshRoutes += 'zip: ok'
    } catch { $script:sshRoutes += "zip: $($_.Exception.Message)" }
  }

  if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) {
    throw ("OpenSSH Server could not be installed. Routes tried >> " + ($script:sshRoutes -join '  >>  '))
  }

  # sshd reads C:\ProgramData\ssh\sshd_config, and it is the SHIPPED default that
  # carries the `Match Group administrators` block pointing at
  # administrators_authorized_keys -- the file the manager-key step writes to on
  # an admin account, which every office box is. The capability and MSI routes
  # drop that default in on first start; the ZIP route does not. Without it the
  # manager key is silently ignored and the box is unreachable with sshd Running
  # and the tunnel up: the exact fault this step exists to stop, arriving by a
  # different door.
  $cfgDir = "$env:ProgramData\ssh"; $cfg = "$cfgDir\sshd_config"
  New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
  if (-not (Test-Path $cfg)) {
    $def = @("$env:WINDIR\System32\OpenSSH\sshd_config_default",
             "$env:ProgramFiles\OpenSSH\sshd_config_default",
             (Join-Path $env:ProgramFiles "OpenSSH-$arch\sshd_config_default")) |
           Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if ($def) { Copy-Item $def $cfg -Force; $script:sshRoutes += 'sshd_config: installed the shipped default' }
  }
  if ($script:iAmAdmin -and (Test-Path $cfg) -and
      -not (Select-String -Path $cfg -Pattern '^\s*[^#].*administrators_authorized_keys' -Quiet)) {
    Add-Content -Path $cfg -Encoding ascii -Value "`r`nMatch Group administrators`r`n       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys"
    $script:sshRoutes += 'sshd_config: added the missing administrators block'
  }

  Set-Service -Name sshd -StartupType Automatic -ErrorAction Stop
  # A STOPPED sshd is indistinguishable from a broken tunnel when seen from the
  # VPS: the reverse tunnel forwards to localhost:22, so with no listener there
  # `ssh <box>` dies with "kex_exchange_identification: Connection closed by
  # remote host" while the dialer, the task and the VPS listener all look fine.
  # SilentlyContinue alone swallowed a failed start and still reported the step
  # OK -- which shipped two silently unreachable boxes (DILPREETSINGH 23009,
  # DESKTOP-73N6JE8 23011, the latter with 'openssh-server(already)'). Fail loud.
  Start-Service sshd -ErrorAction SilentlyContinue
  if ((Get-Service sshd).Status -ne 'Running') {
    # Commonest cause on a box where OpenSSH was ALREADY present: host keys were
    # never generated, and sshd refuses to start without them. -A creates only
    # the missing ones and leaves an existing, working set alone.
    if (Test-Path $script:KEYGEN) { & $script:KEYGEN -A 2>&1 | Out-Null }
    Start-Service sshd -ErrorAction SilentlyContinue
  }
  # Running is STILL not proof. Ask port 22 for a banner -- the same bar the VPS
  # monitor applies (fleet-tunnel-health.vps.sh, sshd_answers).
  $healthy = ((Get-Service sshd).Status -eq 'Running') -and (Test-SshBanner 22 6)
  if (-not $healthy) {
    # 2026-08-21, DESKTOP-73N6JE8: v7 got exactly here, printed "REFUSES TO START
    # ... as admin: ssh-keygen -A, then Start-Service" -- the two things it had
    # just done itself -- and stopped. A human then had nothing to act on except
    # a photo. So: run the ladder (sshd-repair.ps1, written in 6c2). It names what
    # it finds (service account, exe, port-22 holder, host keys, 'sshd -t', the
    # event log) and fixes the known causes in order, down to reinstalling OpenSSH
    # from the ZIP. Its lines stream to the screen and the tail lands in the block.
    $rep = "$DIR\sshd-repair.ps1"
    if (-not (Test-Path $rep)) { throw "sshd does not answer and the repair tool was not written ($rep) - see the sshd-repair-tool step" }
    Write-Host "  sshd is not answering on 127.0.0.1:22 - running the repair ladder (a few minutes if it has to reinstall OpenSSH)..." -ForegroundColor Yellow
    $rout = @(& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File $rep 2>&1 |
              ForEach-Object { Write-Host ("    " + $_) -ForegroundColor DarkGray; "$_" })
    $rc = $LASTEXITCODE
    # The block gets photographed. Keep the LAST lines -- the verdict and what led
    # to it -- so VERSION and REACHABLE at the top do not scroll out of the frame.
    if ($rout.Count -gt 10) { $script:sshRoutes += ("repair: ({0} earlier lines in {1}\sshd-repair.log)" -f ($rout.Count - 10), $DIR); $rout = $rout[-10..-1] }
    $rout | ForEach-Object { $script:sshRoutes += ("repair: " + $_) }
    if (($rc -ne 0) -or -not (Test-SshBanner 22 3)) {
      throw ("sshd DOES NOT ANSWER on 127.0.0.1:22 even after the repair ladder (service {0}) - this PC is UNREACHABLE. The 'repair:' lines above name what it found; full trail in {1}\sshd-repair.log" -f (Get-Service sshd -EA SilentlyContinue).Status, $DIR)
    }
    $script:sshRoutes += 'sshd: repaired by the ladder'
  }
}

# ---- 7. verify the tunnel actually came up ----
$tunnelUp = $false
Step 'verify-tunnel' {
  for ($i=0; $i -lt 12; $i++) {
    Start-Sleep 5
    $p = Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
         Where-Object { $_.CommandLine -match "127\.0\.0\.1:$PORT" }
    if ($p) { $script:tunnelUp = $true; break }
  }
}

# ---- 8. PROVE it from the OUTSIDE. The only check that has ever mattered. ----
# Everything above this line is the box marking its own homework: a service it
# can see, a process it can see. Both were true on JIVO201, 23011 and 23009
# while nobody could log in. This asks the VPS to come back DOWN the tunnel and
# read a real SSH banner off port 22 -- which cannot succeed unless the tunnel
# is parked AND sshd answers. It is the one line in the block below that a
# photograph can be trusted on.
$reach = 'not checked'
Step 'verify-reachable' {
  if (-not $PORT) { throw 'no port was assigned, so there is nothing to verify' }
  for ($i = 0; $i -lt 4; $i++) {
    $r = (Invoke-Registrar "VERIFY HOST=$HOSTTAG" 40000) -join ' '
    if ($r -match 'REACHABLE=yes')              { $script:reach = 'yes'; break }
    if ($r -match 'REACHABLE=no.*REASON=(\S+)') { $script:reach = "NO - $($Matches[1])" }
    elseif ($r -match 'ERR=(\S+)')              { $script:reach = "unknown - registrar said $($Matches[1])" }
    else                                        { $script:reach = "unknown - $r" }
    Start-Sleep 8
  }
  if ($script:reach -ne 'yes') { throw "the VPS could not reach this PC back: $script:reach" }
}

Write-Host ""
Write-Host "  =========== SEND THIS BLOCK BACK ===========" -ForegroundColor Green
# VERSION FIRST, deliberately: it is the one line that tells the reader whether
# to trust the rest of the block. An old build prints an identical-looking OK.
Write-Host ("  VERSION      : " + $TUNNEL_VER) -ForegroundColor Green
Write-Host ("  COMPUTERNAME : " + $env:COMPUTERNAME)
Write-Host ("  USERNAME     : " + $env:USERNAME)
Write-Host ("  VPS PORT     : " + $(if($PORT){$PORT}else{'NOT ASSIGNED'}))
$sshdStatus = (Get-Service sshd -EA SilentlyContinue).Status
if ($sshdStatus -eq 'Running') {
  Write-Host ("  SSHD         : " + $sshdStatus)
} else {
  # Anything other than Running means the box is unreachable no matter how
  # healthy the tunnel looks. Do not let this scroll past as one grey word.
  Write-Host ("  SSHD         : " + $sshdStatus + "  <-- NOT RUNNING: THIS PC IS UNREACHABLE") -ForegroundColor Red
}
Write-Host ("  TUNNEL       : " + $(if($tunnelUp){'UP - dialing the VPS'}else{'not up yet (task retries every minute)'}))
# The verdict. Every other line above describes a part; this one describes the
# whole, measured from the far end.
if ($reach -eq 'yes') {
  Write-Host  "  REACHABLE    : YES - the VPS read this PC's SSH banner back down the tunnel"
} else {
  Write-Host ("  REACHABLE    : " + $reach + "  <-- NOBODY CAN LOG IN TO THIS PC") -ForegroundColor Red
}
Write-Host ("  ALWAYS-ON    : sleep off, hibernate off, watchdog every 15 min, survives reboot")
Write-Host ("  STEPS OK     : " + ($ok -join ', '))
# ALWAYS printed. This was filtered to "only when something looks interesting",
# and the filter's own regex read `capability-failed:` as the quiet word
# `capability` -- so on JIVO201, the very first box v6 repaired, the lines saying
# WHICH route saved it were suppressed. A classification rule that can hide the
# answer is worse than three extra lines on a healthy box.
if ($sshRoutes) {
  Write-Host "  SSHD ROUTES  :  (install routes, then the repair ladder's last lines)" -ForegroundColor DarkGray
  $sshRoutes | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
}
if ($bad) {
  Write-Host "  FAILED       :" -ForegroundColor Red
  $bad | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor Red }
  Write-Host "  Full log on your Desktop: jivo-vps-tunnel-log.txt" -ForegroundColor Yellow
}
Write-Host "  ============================================" -ForegroundColor Green
Write-Host ""
try { Stop-Transcript | Out-Null } catch {}
