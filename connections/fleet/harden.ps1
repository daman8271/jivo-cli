# ============================================================================
#  JIVO tunnel hardening — make the reverse tunnel survive everything the box
#  can throw at it. Idempotent, safe to re-run, run elevated.
#  Usage:  powershell -ExecutionPolicy Bypass -File harden.ps1 -Port <n>
# ============================================================================
param([Parameter(Mandatory=$true)][int]$Port)

$ok=@(); $bad=@()
function Step($n,$b){ try { & $b; $script:ok+=$n } catch { $script:bad+="$n -> $($_.Exception.Message)" } }
$DIR = 'C:\ProgramData\jivo-revtun'
$PSX = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

# ---- 1. never sleep, never hibernate ----------------------------------------
# On a desktop this is free. On a laptop the -dc settings would drain the
# battery, so they are only applied when there is no battery present.
Step 'no-sleep' {
  powercfg /change standby-timeout-ac 0   | Out-Null
  powercfg /change hibernate-timeout-ac 0 | Out-Null
  powercfg /change monitor-timeout-ac 0   | Out-Null
  powercfg /change disk-timeout-ac 0      | Out-Null
  if (-not (Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue)) {
    powercfg /change standby-timeout-dc 0   | Out-Null
    powercfg /change hibernate-timeout-dc 0 | Out-Null
  }
  # Turning hibernate off also disables Fast Startup, which otherwise leaves the
  # box in a hybrid-shutdown state where boot triggers can behave oddly.
  powercfg /hibernate off 2>&1 | Out-Null
}

# ---- 2. stop Windows powering down the network card -------------------------
# Measured on JIVO-B1: the Ethernet adapter shipped with
# AllowComputerToTurnOffDevice=Enabled, which can drop the link under idle and
# take the tunnel with it.
Step 'nic-no-powersave' {
  # Disable-NetAdapterPowerManagement -NoRestart returns SUCCESS and changes nothing
  # readable until the adapter reinitialises -- measured on JIVO-B1. The durable
  # control is PnPCapabilities=24 on the adapter's class key, which persists and
  # applies at next boot. We do NOT bounce the adapter: losing the NIC on a remote
  # box is unrecoverable without physical access, and with never-sleep set the
  # device is not going to be powered down anyway.
  $classKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}'
  foreach ($a in (Get-NetAdapter -Physical -ErrorAction SilentlyContinue)) {
    Disable-NetAdapterPowerManagement -Name $a.Name -NoRestart -ErrorAction SilentlyContinue | Out-Null
    Get-ChildItem $classKey -ErrorAction SilentlyContinue |
      Where-Object { $_.PSChildName -match '^\d{4}$' } | ForEach-Object {
        $p = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
        if ($p.DriverDesc -eq $a.InterfaceDescription) {
          Set-ItemProperty -Path $_.PSPath -Name PnPCapabilities -Value 24 -Type DWord -Force -ErrorAction Stop
        }
      }
  }
}

# ---- 3. wake timers allowed (so a scheduled wake can pull it back) ----------
Step 'wake-timers' {
  powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP RTCWAKE 1 2>&1 | Out-Null
  powercfg /setactive SCHEME_CURRENT 2>&1 | Out-Null
}

# ---- 4. sshd always on ------------------------------------------------------
Step 'sshd-automatic' {
  Set-Service -Name sshd -StartupType Automatic -ErrorAction Stop
  if ((Get-Service sshd).Status -ne 'Running') { Start-Service sshd -ErrorAction Stop }
}

# ---- 5. watchdog: repairs what the 1-minute dialer cannot -------------------
# The dialer task recovers a DROPPED tunnel. It cannot recover from the task
# itself being deleted/disabled, sshd stopped, or power settings drifting back
# (Windows Update and Group Policy both do this). That is this watchdog's job.
Step 'watchdog' {
  $wd = "$DIR\watchdog.ps1"
  $dialer = "$DIR\dial.ps1"
  $tr = "$PSX -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $dialer"
  @"
`$ErrorActionPreference='SilentlyContinue'
`$log='$DIR\watchdog.log'
function L(`$m){ "`$(Get-Date -Format s) `$m" | Add-Content `$log }
if ((Test-Path `$log) -and ((Get-Item `$log).Length -gt 1MB)) { Move-Item `$log "`$log.1" -Force }

# power settings drift back after some Windows updates / policy refreshes
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
Get-NetAdapter -Physical | ForEach-Object { Disable-NetAdapterPowerManagement -Name `$_.Name -NoRestart }

if ((Get-Service sshd).Status -ne 'Running') { L 'sshd was down - starting'; Start-Service sshd }

`$t = Get-ScheduledTask -TaskName 'JivoRevTunnel'
if (-not `$t) {
  L 'dial task MISSING - recreating'
  schtasks /Create /TN JivoRevTunnel /TR "$tr" /SC MINUTE /MO 1 /RU SYSTEM /RL HIGHEST /F | Out-Null
} elseif (`$t.State -eq 'Disabled') { L 'dial task disabled - enabling'; Enable-ScheduledTask -TaskName 'JivoRevTunnel' }

`$alive = Get-CimInstance Win32_Process | Where-Object { `$_.Name -eq 'ssh.exe' -and `$_.CommandLine -match '127\.0\.0\.1:$Port' }
if (-not `$alive) { L 'tunnel DOWN - kicking dialer'; schtasks /Run /TN JivoRevTunnel | Out-Null }
"@ | Set-Content -Path $wd -Encoding ascii

  if ($wd -match '\s') { throw "watchdog path has a space: $wd" }
  $wtr = "$PSX -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $wd"
  $r = schtasks /Create /TN JivoTunnelWatchdog /TR $wtr /SC MINUTE /MO 15 /RU SYSTEM /RL HIGHEST /F 2>&1
  if ($LASTEXITCODE -ne 0) { throw "schtasks watchdog failed: $r" }
  try {
    $t = Get-ScheduledTask -TaskName 'JivoTunnelWatchdog' -ErrorAction Stop
    if (-not ($t.Triggers | Where-Object { $_.CimClass.CimClassName -match 'BootTrigger' })) {
      $t.Triggers = @($t.Triggers) + (New-ScheduledTaskTrigger -AtStartup)
      Set-ScheduledTask -InputObject $t -ErrorAction Stop | Out-Null
    }
  } catch {}
  schtasks /Run /TN JivoTunnelWatchdog 2>&1 | Out-Null
}

# ---- report -----------------------------------------------------------------
Start-Sleep 3
$sleepAC = (powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE | Select-String 'Current AC').ToString().Trim()
$classKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}'
$nics = foreach ($ad in (Get-NetAdapter -Physical)) {
  # $ad, not $_ : the inner ForEach-Object rebinds $_ and would shadow the adapter.
  $live = (Get-NetAdapterPowerManagement -Name $ad.Name -EA SilentlyContinue).AllowComputerToTurnOffDevice
  $reg = 'unset'
  foreach ($sub in (Get-ChildItem $classKey -EA SilentlyContinue | Where-Object { $_.PSChildName -match '^\d{4}$' })) {
    $pp = Get-ItemProperty $sub.PSPath -EA SilentlyContinue
    if ($pp.DriverDesc -eq $ad.InterfaceDescription -and $null -ne $pp.PnPCapabilities) { $reg = $pp.PnPCapabilities }
  }
  $verdict = if ($reg -eq 24) { if ($live -eq 'Disabled') { 'OFF' } else { 'OFF at next reboot' } } else { "STILL ON (reg=$reg)" }
  "$($ad.Name)=$verdict"
}
$tun = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'ssh.exe' -and $_.CommandLine -match "127\.0\.0\.1:$Port" }
Write-Host ""
Write-Host "  ====== HARDENING REPORT ======" -ForegroundColor Green
Write-Host ("  sleep AC      : " + $sleepAC)
Write-Host ("  hibernate     : " + $(if((Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Power').HibernateEnabled -eq 0){'off'}else{'ON (check)'}))
Write-Host ("  NIC powersave : " + ($nics -join ', '))
Write-Host ("  sshd          : " + (Get-Service sshd).Status + '/' + (Get-Service sshd).StartType)
Write-Host ("  dial task     : " + (Get-ScheduledTask -TaskName JivoRevTunnel -EA SilentlyContinue).State)
Write-Host ("  watchdog task : " + (Get-ScheduledTask -TaskName JivoTunnelWatchdog -EA SilentlyContinue).State)
Write-Host ("  tunnel :$Port  : " + $(if($tun){"UP (PID $($tun.ProcessId))"}else{'DOWN'}))
Write-Host ("  steps ok      : " + ($ok -join ', '))
if ($bad) { Write-Host "  FAILED        :" -ForegroundColor Red; $bad | ForEach-Object { Write-Host "     $_" -ForegroundColor Red } }
Write-Host "  ==============================" -ForegroundColor Green
