# install-gst.ps1 - give this PC working GST portal sessions borrowed from the VPS.
# Expects, next to itself: gst-portal.exe, gst.env, gst-sync.cmd, jivo-gst-sync(.pub), checkout.txt
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$checkout = (Get-Content (Join-Path $here 'checkout.txt') -Raw).Trim()
if (-not (Test-Path $checkout)) { throw "checkout not found: $checkout" }
$gstDir = Join-Path $checkout 'portals\gst'; $cliDir = Join-Path $gstDir 'cli'
New-Item -ItemType Directory -Force -Path $cliDir | Out-Null
Copy-Item (Join-Path $here 'gst-portal.exe') (Join-Path $cliDir 'gst-portal.exe') -Force
Copy-Item (Join-Path $here 'gst.env') (Join-Path $gstDir '.env') -Force
"binary + .env -> $gstDir"
$sshDir = Join-Path $env:USERPROFILE '.ssh'; New-Item -ItemType Directory -Force -Path $sshDir | Out-Null
$key = Join-Path $sshDir 'jivo-gst-sync'
Copy-Item (Join-Path $here 'jivo-gst-sync') $key -Force
Copy-Item (Join-Path $here 'jivo-gst-sync.pub') "$key.pub" -Force
$acl = New-Object System.Security.AccessControl.FileSecurity
$acl.SetAccessRuleProtection($true, $false)
$me = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
foreach ($who in @($me, 'NT AUTHORITY\SYSTEM', 'BUILTIN\Administrators')) {
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($who, 'FullControl', 'Allow')))
}
Set-Acl -Path $key -AclObject $acl
"key locked -> $key"
$jivo = Join-Path $env:USERPROFILE '.jivo'; New-Item -ItemType Directory -Force -Path $jivo | Out-Null
$sync = Join-Path $jivo 'gst-sync.cmd'
Copy-Item (Join-Path $here 'gst-sync.cmd') $sync -Force
$envPath = Join-Path $gstDir '.env'
[Environment]::SetEnvironmentVariable('GST_ENV', $envPath, 'User'); $env:GST_ENV = $envPath
"GST_ENV (user) -> $envPath"
$r = schtasks /Create /TN JivoGstSync /TR $sync /SC MINUTE /MO 15 /F 2>&1
if ($LASTEXITCODE -ne 0) { throw "schtasks failed: $r" }
try { Set-ScheduledTask -TaskName 'JivoGstSync' -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 10)) | Out-Null } catch { "note: task settings not applied: $($_.Exception.Message)" }
"task JivoGstSync -> every 15 min while logged on"
"--- first sync:"
cmd /c $sync
"--- auth status:"
& (Join-Path $cliDir 'gst-portal.exe') auth status
"--- haryana whoami (filtered):"
& (Join-Path $cliDir 'gst-portal.exe') auth whoami --state haryana 2>&1 | Select-String -Pattern 'stcd|utype|error|expired|logged' | ForEach-Object { $_.Line.Trim() }
