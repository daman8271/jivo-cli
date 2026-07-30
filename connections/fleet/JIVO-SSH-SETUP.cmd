@echo off
:: ====================================================================
::  JIVO SSH SETUP  -  double-click this file. That's it.
::  Enables SSH on this Windows PC so the JIVO fleet manager can reach
::  it over the private Tailscale network. Idempotent, safe to re-run.
::  Needs NO Tailscale auth key. Nothing is exposed to the internet.
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
# Deliberately NO global ErrorActionPreference=Stop: each step reports its own
# failure and the rest still runs, so one hiccup can't abandon a half-set-up box.
$log = "$env:USERPROFILE\Desktop\jivo-ssh-setup-log.txt"
try { Start-Transcript -Path $log -Force | Out-Null } catch {}

$ok=@(); $bad=@()
function Step($name,$block){ try { & $block; $script:ok += $name } catch { $script:bad += "$name -> $($_.Exception.Message)" } }

$MANAGER_KEYS = @(
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB8+FPQ9luiwWsPUSZDY5UTwEiOVmL1o1zgf4sw1UORA daman8271@github',
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHR8F2rqvcl7hHaAmpmXd3uogcx0AUflmMvlAART0JNK hermes-agent-access'
)
$TAILNET = '100.64.0.0/10'

Write-Host ""
Write-Host "  === JIVO SSH SETUP ===" -ForegroundColor White
Write-Host "  This takes about a minute. Leave the window open." -ForegroundColor Gray
Write-Host ""

# 1. OpenSSH Server present
Step 'openssh-installed' {
  if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) {
    Write-Host "  installing OpenSSH Server..." -ForegroundColor Cyan
    $c = Get-WindowsCapability -Online -Name 'OpenSSH.Server*' -ErrorAction Stop
    if ($c.State -ne 'Installed') { Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -ErrorAction Stop | Out-Null }
  }
}
# 2. running + automatic at boot
Step 'sshd-service' {
  Set-Service -Name sshd -StartupType Automatic -ErrorAction Stop
  Start-Service sshd -ErrorAction Stop
}
# 3. manager keys in the RIGHT file. sshd IGNORES the user's own authorized_keys for
#    admin accounts and reads administrators_authorized_keys, whose ACL must be
#    SYSTEM + Administrators ONLY or sshd silently refuses the whole file.
Step 'authorized-keys' {
  $admins = (Get-LocalGroupMember -Group 'Administrators' -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
  $me     = "$env:COMPUTERNAME\$env:USERNAME"
  $iAmAdminAccount = $admins -contains $me
  if ($iAmAdminAccount) {
    $f = "$env:ProgramData\ssh\administrators_authorized_keys"
    if (-not (Test-Path $f)) { New-Item -ItemType File -Path $f -Force -ErrorAction Stop | Out-Null }
  } else {
    $d = "$env:USERPROFILE\.ssh"; New-Item -ItemType Directory -Force -Path $d | Out-Null
    $f = "$d\authorized_keys"
    if (-not (Test-Path $f)) { New-Item -ItemType File -Path $f -Force -ErrorAction Stop | Out-Null }
  }
  # APPEND only what is missing. Never overwrite: these files can already hold other
  # managers' keys and a rewrite would silently revoke them.
  $have = @(Get-Content $f -ErrorAction SilentlyContinue)
  $added = 0
  foreach ($k in $MANAGER_KEYS) { if ($have -notcontains $k) { Add-Content -Path $f -Value $k -Encoding ascii -ErrorAction Stop; $added++ } }
  if ($iAmAdminAccount) { icacls.exe $f /inheritance:r /grant 'SYSTEM:F' /grant 'BUILTIN\Administrators:F' | Out-Null }
  Write-Host ("  keys: $added added, file = " + $f) -ForegroundColor Cyan
}
# 4. PowerShell as the default SSH shell
Step 'default-shell' {
  if (-not (Test-Path 'HKLM:\SOFTWARE\OpenSSH')) { New-Item -Path 'HKLM:\SOFTWARE\OpenSSH' -Force | Out-Null }
  New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell `
    -Value "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force -ErrorAction Stop | Out-Null
}
# 5. firewall: port 22 to the TAILNET ONLY (never the public internet, never the LAN)
Step 'firewall-tailnet-only' {
  if (-not (Get-NetFirewallRule -DisplayName 'SSH-Tailscale' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName 'SSH-Tailscale' -Direction Inbound -Protocol TCP -LocalPort 22 `
      -Action Allow -RemoteAddress $TAILNET -Profile Any -ErrorAction Stop | Out-Null
  }
  $def = Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue
  if ($def) { Set-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -RemoteAddress $TAILNET -ErrorAction Stop }
}
Step 'restart-sshd' { Restart-Service sshd -ErrorAction Stop }

# ---- verify: a service being "Running" is NOT proof a listener is bound ----
Start-Sleep 2
$listener = Get-NetTCPConnection -State Listen -LocalPort 22 -ErrorAction SilentlyContinue
$tsExe = 'C:\Program Files\Tailscale\tailscale.exe'
# Read the IP off the ADAPTER first. `tailscale ip` talks to tailscaled's LocalAPI and
# returns nothing from a non-interactive/service context even when the box is fully
# online -- measured on VICTUS, which was live on the tailnet while the CLI said nothing.
$tsip = $null
try {
  $a = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
       Where-Object { $_.InterfaceAlias -match 'Tailscale' -and $_.IPAddress -like '100.*' } |
       Select-Object -First 1
  if (-not $a) {
    $a = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
         Where-Object { $_.IPAddress -match '^100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.' } |
         Select-Object -First 1
  }
  if ($a) { $tsip = $a.IPAddress }
} catch {}
if (-not $tsip -and (Test-Path $tsExe)) { $tsip = (& $tsExe ip -4 2>$null | Select-Object -First 1) }
if (-not $tsip) { $tsip = if (Test-Path $tsExe) { 'TAILSCALE INSTALLED BUT NOT JOINED (needs an auth key)' } else { 'TAILSCALE NOT INSTALLED' } }

Write-Host ""
Write-Host "  =========== SEND THIS BLOCK BACK ===========" -ForegroundColor Green
Write-Host ("  USERNAME     : " + $env:USERNAME)
Write-Host ("  COMPUTERNAME : " + $env:COMPUTERNAME)
Write-Host ("  TAILSCALE_IP : " + $tsip)
Write-Host ("  SSHD         : " + (Get-Service sshd).Status + ", " + (Get-Service sshd).StartType)
Write-Host ("  LISTENER :22 : " + $(if($listener){'BOUND ' + (($listener.LocalAddress | Sort-Object -Unique) -join ',')}else{'NOT BOUND - reboot usually fixes this'}))
Write-Host ("  STEPS OK     : " + ($ok -join ', '))
if ($bad) {
  Write-Host "  FAILED       :" -ForegroundColor Red
  $bad | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor Red }
  Write-Host ("  A full log was saved to your Desktop: jivo-ssh-setup-log.txt") -ForegroundColor Yellow
}
Write-Host "  ============================================" -ForegroundColor Green
Write-Host ""
try { Stop-Transcript | Out-Null } catch {}
