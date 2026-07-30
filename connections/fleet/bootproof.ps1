# ============================================================================
#  Boot-proof the JIVO tunnel tasks. Idempotent, run elevated.
#  Makes both tasks fire after a reboot under every condition Windows checks.
# ============================================================================
$changes = @()

function Set-BootProof {
  param([string]$Name, [bool]$Unlimited)

  $t = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
  if (-not $t) { $script:changes += "$Name : MISSING"; return }

  # Conditions Windows silently uses to REFUSE a start:
  #  - DisallowStartIfOnBatteries: schtasks defaults this to TRUE, so on a laptop
  #    the task simply does not run on battery. This is how a watchdog quietly dies.
  #  - StopIfGoingOnBatteries: would kill a running tunnel when unplugged.
  #  - RunOnlyIfIdle / RunOnlyIfNetworkAvailable: both are start-blockers.
  #  - StartWhenAvailable: catches a trigger missed while the box was off.
  # ExecutionTimeLimit: the dialer must be UNLIMITED (its ssh runs forever); the
  # watchdog must be BOUNDED, or a hung run blocks every later run via IgnoreNew.
  $limit = if ($Unlimited) { [TimeSpan]::Zero } else { New-TimeSpan -Minutes 10 }
  $set = New-ScheduledTaskSettingsSet `
           -MultipleInstances IgnoreNew `
           -ExecutionTimeLimit $limit `
           -StartWhenAvailable `
           -DontStopOnIdleEnd `
           -AllowStartIfOnBatteries `
           -DontStopIfGoingOnBatteries `
           -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
  $set.RunOnlyIfNetworkAvailable = $false

  # Boot trigger with a delay: at T+0 the network stack is usually not up yet, so
  # an immediate dial is a guaranteed failure and log noise. 30s and it is ready.
  $boot = New-ScheduledTaskTrigger -AtStartup
  $boot.Delay = 'PT30S'
  $keep = @($t.Triggers | Where-Object { $_.CimClass.CimClassName -notmatch 'BootTrigger' })
  $t.Triggers = @($keep) + $boot
  $t.Settings = $set

  Set-ScheduledTask -InputObject $t -ErrorAction Stop | Out-Null
  $script:changes += "$Name : boot-proofed"
}

Set-BootProof -Name 'JivoRevTunnel'      -Unlimited $true
Set-BootProof -Name 'JivoTunnelWatchdog' -Unlimited $false

# The Task Scheduler service itself must start at boot.
Set-Service -Name Schedule -StartupType Automatic -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  ====== BOOT-PROOF REPORT ======" -ForegroundColor Green
$changes | ForEach-Object { Write-Host "  $_" }
foreach ($n in 'JivoRevTunnel','JivoTunnelWatchdog') {
  $x = (schtasks /Query /TN $n /XML 2>$null) -join "`n"
  if (-not $x) { Write-Host "  $n : MISSING" -ForegroundColor Red; continue }
  $bat  = if ($x -match '<DisallowStartIfOnBatteries>false')  { 'ok' } else { 'BLOCKS ON BATTERY' }
  $stop = if ($x -match '<StopIfGoingOnBatteries>false')      { 'ok' } else { 'STOPS ON BATTERY' }
  $swa  = if ($x -match '<StartWhenAvailable>true')           { 'ok' } else { 'no-catchup' }
  $bt   = if ($x -match '<BootTrigger>|<BootTrigger />')      { 'yes' } else { 'NO BOOT TRIGGER' }
  $dly  = if ($x -match '<Delay>PT30S</Delay>')               { '30s' } else { 'none' }
  Write-Host ("  {0,-19} boot={1} delay={2} onBattery={3} stopOnBattery={4} catchup={5}" -f $n,$bt,$dly,$bat,$stop,$swa)
}
Write-Host ("  Schedule service   : " + (Get-Service Schedule).Status + "/" + (Get-Service Schedule).StartType)
Write-Host "  ===============================" -ForegroundColor Green
