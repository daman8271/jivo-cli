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
if ((Get-Service sshd).Status -ne 'Running') { L 'sshd down - starting'; Start-Service sshd }
`$t = Get-ScheduledTask -TaskName 'JivoRevTunnel'
if (-not `$t) { L 'dial task MISSING - recreating'; schtasks /Create /TN JivoRevTunnel /TR "$dialTr" /SC MINUTE /MO 1 /RU SYSTEM /RL HIGHEST /F | Out-Null }
elseif (`$t.State -eq 'Disabled') { L 'dial task disabled - enabling'; Enable-ScheduledTask -TaskName 'JivoRevTunnel' }
`$alive = Get-CimInstance Win32_Process | Where-Object { `$_.Name -eq 'ssh.exe' -and `$_.CommandLine -match '127\.0\.0\.1:$PORT' }
if (-not `$alive) { L 'tunnel DOWN - kicking dialer'; schtasks /Run /TN JivoRevTunnel | Out-Null }
"@ | Set-Content -Path $wd -Encoding ascii
  if ($wd -match '\s') { throw "watchdog path has a space: $wd" }
  $r = schtasks /Create /TN JivoTunnelWatchdog /TR "$psExe2 -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $wd" /SC MINUTE /MO 15 /RU SYSTEM /RL HIGHEST /F 2>&1
  if ($LASTEXITCODE -ne 0) { throw "watchdog schtasks failed: $r" }
  try { Set-BootProof 'JivoTunnelWatchdog' $false } catch { Write-Host "  note: boot-proofing the watchdog failed ($($_.Exception.Message))" -ForegroundColor Yellow }
}

# ---- 6d. collect the background OpenSSH install (bounded, with a fallback) ----
Step 'openssh-server' {
  if (-not $sshJob) { if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) { throw 'sshd missing and no install was started' }; return }
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
