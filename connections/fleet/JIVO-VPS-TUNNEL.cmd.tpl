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
  foreach ($d in @("$env:WINDIR\System32\OpenSSH", "$env:ProgramFiles\OpenSSH", "${env:ProgramFiles(x86)}\OpenSSH")) {
    if ($d -and (Test-Path (Join-Path $d $name))) { return (Join-Path $d $name) }
  }
  $c = Get-Command $name -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  return "$env:WINDIR\System32\OpenSSH\$name"
}
$SSH    = Find-Exe 'ssh.exe'
$KEYGEN = Find-Exe 'ssh-keygen.exe' 

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
  $iAmAdmin = $admins -contains "$env:COMPUTERNAME\$env:USERNAME"
  if ($iAmAdmin) { $f = "$env:ProgramData\ssh\administrators_authorized_keys" }
  else { $d="$env:USERPROFILE\.ssh"; New-Item -ItemType Directory -Force -Path $d | Out-Null; $f="$d\authorized_keys" }
  if (-not (Test-Path $f)) { New-Item -ItemType File -Path $f -Force -ErrorAction Stop | Out-Null }
  # APPEND only. These files can already hold other managers' keys.
  $have = @(Get-Content $f -ErrorAction SilentlyContinue)
  foreach ($k in $MANAGER_KEYS) { if ($have -notcontains $k) { Add-Content -Path $f -Value $k -Encoding ascii -ErrorAction Stop } }
  if ($iAmAdmin) { icacls.exe $f /inheritance:r /grant 'SYSTEM:F' /grant 'BUILTIN\Administrators:F' | Out-Null }
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
  $rk = "$DIR\reg_key"
  [IO.File]::WriteAllBytes($rk, [Convert]::FromBase64String($REGKEY_B64))
  Lock-KeyFile $rk
  $pub  = (Get-Content "$TUNKEY.pub" -Raw).Trim()
  $pubB = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pub))
  # The registrar only accepts [A-Za-z0-9._-] in USER, and Windows usernames can
  # contain spaces (e.g. "khushwinder singh") -- sanitise or it is rejected.
  $u = ($env:USERNAME -replace '[^A-Za-z0-9._-]','_')
  $req = "HOST=$env:COMPUTERNAME USER=$u KEY=$pubB"
  # Windows ssh.exe reliably RUNS the remote command but then sits on the session
  # teardown for ~160s -- measured on VICTUS, with and without -n. We only need the
  # reply, not a graceful exit, so cap the wait and read the answer from a file.
  $o = "$DIR\reg.out"; $e = "$DIR\reg.err"
  $p = Start-Process -FilePath $SSH -NoNewWindow -PassThru -RedirectStandardOutput $o -RedirectStandardError $e `
       -ArgumentList @('-n','-i',$rk,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
                       '-o','StrictHostKeyChecking=accept-new','-o','ConnectTimeout=20',$VPS,$req)
  if (-not $p.WaitForExit(45000)) { $p.Kill() }
  $out = @(Get-Content $o -EA SilentlyContinue) + @(Get-Content $e -EA SilentlyContinue)
  Remove-Item $rk,$o,$e -Force -ErrorAction SilentlyContinue   # registrar key never stays on the box
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
function Start-Sshd(`$why) {
  # One start, and if it refuses, the ssh-keygen -A retry the old watchdog never
  # had -- it stopped at the failed start, which is the exact point where these
  # boxes need help. Always logs the REAL error text: 'sshd down - starting' told
  # us nothing for four days; the SCM's own message would have named the fault.
  `$e = `$null
  Start-Service sshd -ErrorAction SilentlyContinue -ErrorVariable e
  if ((Get-Service sshd).Status -eq 'Running') { L "`$why - started"; return }
  L "`$why - Start-Service FAILED: `$(if(`$e){`$e[0].Exception.Message}else{'no error text'})"
  # Missing host keys are THE documented reason a start fails here: every box
  # installed by the version of 6d that returned early has none. -A creates only
  # what is missing and leaves an existing, working set alone.
  # Resolved at RUN time, never baked in: this runs as SYSTEM, which does not
  # find OpenSSH on PATH (same reason the task calls powershell.exe by full
  # path), and the watchdog is written BEFORE step 6d decides whether the inbox
  # capability (System32\OpenSSH) or the MSI (Program Files\OpenSSH) provides it.
  `$kg = @('$KEYGEN', "`$env:WINDIR\System32\OpenSSH\ssh-keygen.exe", "`$env:ProgramFiles\OpenSSH\ssh-keygen.exe") | Where-Object { `$_ -and (Test-Path `$_) } | Select-Object -First 1
  if (-not `$kg) { L 'ssh-keygen.exe is in neither System32\OpenSSH nor Program Files\OpenSSH - cannot regenerate host keys'; return }
  `$kd = "`$env:ProgramData\ssh"
  if (-not (Test-Path `$kd)) {
    # ssh-keygen -A writes into %ProgramData%\ssh and fails outright when it is
    # not there. Create it LOCKED: inheriting ProgramData's ACL leaves the new
    # PRIVATE host keys readable by Users, and sshd refuses to start on a host
    # key with open permissions -- a "repair" that swaps one dead sshd for another.
    New-Item -ItemType Directory -Force -Path `$kd | Out-Null
    icacls.exe `$kd /inheritance:r /grant 'SYSTEM:(OI)(CI)F' /grant 'BUILTIN\Administrators:(OI)(CI)F' | Out-Null
  }
  L "running '`$kg -A' (missing host keys) and retrying the start"
  & `$kg -A 2>&1 | Out-Null
  `$e = `$null
  Start-Service sshd -ErrorAction SilentlyContinue -ErrorVariable e
  if ((Get-Service sshd).Status -eq 'Running') { L 'started after ssh-keygen -A' }
  else { L "STILL not running after ssh-keygen -A: `$(if(`$e){`$e[0].Exception.Message}else{'no error text'})" }
}
# The whole sshd repair sits in ONE try/catch. It is best-effort plumbing behind
# the tunnel work, which has already run; an exception in here must produce a log
# line, not a dead run.
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
        L "SSHD BROKEN - sshd is listening on `$addr only, NOT on 127.0.0.1, and the tunnel forwards to 127.0.0.1:22. THIS PC IS UNREACHABLE. Fix by hand: remove the ListenAddress line in %ProgramData%\ssh\sshd_config (or add 'ListenAddress 127.0.0.1'), then restart sshd. Not restarting - a bounce cannot change a config file."
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
"@ | Set-Content -Path $wd -Encoding ascii
  if ($wd -match '\s') { throw "watchdog path has a space: $wd" }
  $r = schtasks /Create /TN JivoTunnelWatchdog /TR "$psExe2 -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $wd" /SC MINUTE /MO 15 /RU SYSTEM /RL HIGHEST /F 2>&1
  if ($LASTEXITCODE -ne 0) { throw "watchdog schtasks failed: $r" }
  try { Set-BootProof 'JivoTunnelWatchdog' $false } catch { Write-Host "  note: boot-proofing the watchdog failed ($($_.Exception.Message))" -ForegroundColor Yellow }
}

# ---- 6d. collect the background OpenSSH install (bounded, with a fallback) ----
Step 'openssh-server' {
  # Collecting the background install is CONDITIONAL (there is only a job when we
  # started one). Making sshd actually RUN is NOT -- it must happen on every path.
  # This used to `return` early whenever $sshJob was null, i.e. on exactly the
  # 'openssh-server(already)' path, which skipped every line below: the service
  # was never set to Automatic, never started, host keys were never generated,
  # and the loud failure below could not fire. Result: the step printed OK on a
  # box that was unreachable (DESKTOP-73N6JE8 23011, 2026-08-13 -- and VICTUS
  # 23001 and JIVO 23008 found in the same state). Never re-add an early return.
  if ($sshJob) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sshJob.State -eq 'Running' -and $sw.Elapsed.TotalSeconds -lt 150) {
      Start-Sleep 10
      Write-Host ("    OpenSSH Server still installing... {0}s" -f [int]$sw.Elapsed.TotalSeconds) -ForegroundColor DarkGray
    }
    if ($sshJob.State -eq 'Running') {
      Write-Host "  Windows Update is too slow - switching to the direct installer." -ForegroundColor Yellow
      Stop-Job $sshJob -ErrorAction SilentlyContinue
    }
    Remove-Job $sshJob -Force -ErrorAction SilentlyContinue
  }

  if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) {
    # Fallback: Microsoft's own Win32-OpenSSH MSI. A direct HTTPS download of a
    # few MB, seconds instead of minutes, and it does not touch Windows Update --
    # so it also works on boxes where policy blocks the component store (0x800f0954).
    $msi = "$env:TEMP\openssh-win64.msi"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    # Resolve the asset from the API. A hardcoded /releases/latest/download/<file>
    # URL 404s the moment Microsoft cuts a new version -- measured: the pinned
    # v9.8.1.0 name was already dead while the latest release was v10.0.0.0.
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'ARM64' } else { 'Win64' }
    $url = $null
    try {
      $rel = Invoke-RestMethod -Uri 'https://api.github.com/repos/PowerShell/Win32-OpenSSH/releases/latest' `
               -UseBasicParsing -TimeoutSec 30 -Headers @{ 'User-Agent' = 'jivo-fleet' }
      $url = ($rel.assets | Where-Object { $_.name -like "OpenSSH-$arch-*.msi" } | Select-Object -First 1).browser_download_url
    } catch { }
    if (-not $url) { $url = "https://github.com/PowerShell/Win32-OpenSSH/releases/download/10.0.0.0p2-Preview/OpenSSH-$arch-v10.0.0.0.msi" }
    Write-Host "  downloading $url" -ForegroundColor DarkGray
    Invoke-WebRequest -Uri $url -OutFile $msi -UseBasicParsing -TimeoutSec 120 -ErrorAction Stop
    Start-Process msiexec.exe -ArgumentList "/i `"$msi`" /quiet /norestart" -Wait -ErrorAction Stop
    Remove-Item $msi -Force -ErrorAction SilentlyContinue
  }
  if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) { throw 'OpenSSH Server could not be installed by either route' }
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
    if (Test-Path $KEYGEN) { & $KEYGEN -A 2>&1 | Out-Null }
    Start-Service sshd -ErrorAction SilentlyContinue
  }
  if ((Get-Service sshd).Status -ne 'Running') {
    throw ("sshd is installed but REFUSES TO START (status {0}) - this box will be UNREACHABLE even though the tunnel comes up. As admin: 'ssh-keygen -A', then 'Start-Service sshd'; if it still fails check nothing else holds port 22 (Get-NetTCPConnection -LocalPort 22)" -f (Get-Service sshd).Status)
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
Write-Host ("  ALWAYS-ON    : sleep off, hibernate off, watchdog every 15 min, survives reboot")
Write-Host ("  STEPS OK     : " + ($ok -join ', '))
if ($bad) {
  Write-Host "  FAILED       :" -ForegroundColor Red
  $bad | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor Red }
  Write-Host "  Full log on your Desktop: jivo-vps-tunnel-log.txt" -ForegroundColor Yellow
}
Write-Host "  ============================================" -ForegroundColor Green
Write-Host ""
try { Stop-Transcript | Out-Null } catch {}
