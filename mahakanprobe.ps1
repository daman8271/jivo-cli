param([string[]]$Hosts)
$ErrorActionPreference='SilentlyContinue'
"=== me: $env:COMPUTERNAME ==="
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' -or $_.IPAddress -like '10.*' }).IPAddress
"sshd here: $((Get-Service sshd).Status) / $((Get-CimInstance Win32_Service -Filter "Name='sshd'").StartMode)"
"=== neighbours ==="
foreach ($h in $Hosts) {
  $ip = $null
  try { $ip = (Resolve-DnsName $h -Type A -ErrorAction Stop | Select-Object -First 1).IPAddress } catch {}
  if (-not $ip) { try { $ip = ([Net.Dns]::GetHostAddresses($h) | Where-Object { $_.AddressFamily -eq 'InterNetwork' } | Select-Object -First 1).IPAddressToString } catch {} }
  if ($ip) {
    $p = Test-Connection $ip -Count 1 -Quiet
    $t = Test-NetConnection $ip -Port 22 -WarningAction SilentlyContinue
    $r = Test-NetConnection $ip -Port 3389 -WarningAction SilentlyContinue
    $s = Test-NetConnection $ip -Port 445 -WarningAction SilentlyContinue
    "$h $ip ping=$p ssh22=$($t.TcpTestSucceeded) rdp3389=$($r.TcpTestSucceeded) smb445=$($s.TcpTestSucceeded)"
  } else { "$h UNRESOLVED" }
}
"=== arp (192.168.*) ==="
arp -a | Select-String '192\.168\.' | ForEach-Object { $_.Line.Trim() } | Select-Object -First 60
