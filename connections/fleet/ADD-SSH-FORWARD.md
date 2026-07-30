---
title: Add SSH to a machine that is ALREADY on the tailnet
created: 2026-07-30
project: jivo-cli
type: runbook
tags: [fleet, ssh, tailscale, windows, macos, onboarding]
---

# Add SSH to a box that's already on the tailnet

> ⚠️ **SUPERSEDED for new boxes (2026-07-30).** Daman's call: skip Tailscale entirely and
> reach Windows boxes by reverse tunnel through the VPS. That path needs no auth key, no
> browser click, and no Tailscale install — see **[README.md](README.md)** and use
> `build-tunnel-installer.sh`. Proven end-to-end on `victus` the same day.
>
> This file stays useful for a box that is *already* on the tailnet and just needs sshd
> (that's `dev`), and for the Windows-SSH mechanics — admin key files, ACLs, firewall
> scoping — which are identical either way.

> **Use this when** the machine already shows up in `tailscale status` but `ssh` to it
> times out or is refused. That is the case for every remaining office Windows box —
> they joined the tailnet in July and only ever needed the SSH half.

## Why this file exists (read once, saves you a week)

The four scripts in `ecomcliauto/fleet/installer/` (`FLEET-ENROLL.cmd`,
`fleet-enroll.ps1`, `fleet-enroll.sh`, `FLEET-ENROLL-WINDOWS.cmd`) **cannot do this
job**, for two reasons that are not bugs in their logic:

1. **They abort before the SSH phase without a Tailscale auth key.** Both the Windows
   and the shell version do `if (-not $TAILNET_AUTH_KEY) { ... exit 1 }` as their first
   real action. The boxes we need are *already joined*, so there is no key to give and
   the SSH phase downstream is unreachable.
2. **They are executable attachments.** WhatsApp and Gmail block `.cmd` / `.ps1`. There
   is no way to hand one to a colleague. The only artifact that survives a chat app is
   **text you paste**.

**The scripts are not broken — they work.** `victus` was enrolled with an earlier draft of
`fleet-enroll.ps1` and is living proof: `SSH-Tailscale` rule scoped to `100.64.0.0/10`,
`C:\ProgramData\fleet-watchdog.ps1`, a `FleetWatchdog` SYSTEM task still firing every
30 min, `powercfg` standby 0, keys appended to `administrators_authorized_keys` with a
correct SYSTEM+Administrators-only ACL, PowerShell as default shell, Tailscale
`UnattendedMode=always`. All verified live 2026-07-30.

What made victus work is that **Daman ran it himself, locally, elevated, with an auth key
in hand.** That is the one situation the scripts are built for. The two blockers above
only bite when the operator is someone else on a machine already in the mesh — which is
every remaining box. Verified on `dev` the same day: no `SSH-Tailscale` rule, no
`FleetWatchdog`, no transcript — it was configured by hand in July, not by the script.

So: **keep `fleet-enroll.ps1` for a machine you can sit in front of.** Use **this** file
for the ones you can only reach through somebody else's hands.

> ⚠️ One consequence: the committed script's `sshd_config` hardening block has never
> executed anywhere. Both `dev` and `victus` still show factory `#PasswordAuthentication
> yes` on L51 — the earlier draft that ran on victus predates that block. So that
> `-replace` is untested code, and it's the step that can lock you out. Test it on a box
> you can physically reach before it runs anywhere else.

---

## Windows — forward this to the person (it's just text)

> Hi! 2-minute one-time setup so the IT tooling can reach this PC. You only do this once.
>
> **Step 1.** Click **Start**, type **PowerShell**, **right-click "Windows PowerShell"
> → "Run as administrator"** → **Yes**.
>
> **Step 2.** Paste this whole block, press **Enter**, wait ~1 minute:

```powershell
# --- JIVO fleet: enable SSH on an already-joined tailnet box. Idempotent, safe to re-run. ---
# No auth key needed. Deliberately NO global ErrorActionPreference=Stop: each step reports
# its own failure and the rest still runs, so one hiccup can't abandon a half-configured box.
$ok=@(); $bad=@()
function Step($name,$block){ try { & $block; $script:ok += $name } catch { $script:bad += "$name -> $($_.Exception.Message)" } }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Host "STOP: not elevated. Re-open PowerShell with 'Run as administrator'." -ForegroundColor Red; Read-Host "Enter to close"; exit 1 }

$MANAGER_KEYS = @(
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB8+FPQ9luiwWsPUSZDY5UTwEiOVmL1o1zgf4sw1UORA daman8271@github',
  'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHR8F2rqvcl7hHaAmpmXd3uogcx0AUflmMvlAART0JNK hermes-agent-access'
)
$TAILNET = '100.64.0.0/10'

# 1. OpenSSH Server present
Step 'openssh-installed' {
  if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) {
    $c = Get-WindowsCapability -Online -Name 'OpenSSH.Server*' -ErrorAction Stop
    if ($c.State -ne 'Installed') { Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -ErrorAction Stop | Out-Null }
  }
}
# 2. running + automatic at boot
Step 'sshd-service' {
  Set-Service -Name sshd -StartupType Automatic -ErrorAction Stop
  Start-Service sshd -ErrorAction Stop
}
# 3. manager keys in the RIGHT file. sshd IGNORES ~/.ssh/authorized_keys for admin
#    accounts and reads administrators_authorized_keys, whose ACL must be SYSTEM +
#    Administrators ONLY or sshd silently refuses the file.
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
  # APPEND only what's missing. Never Set-Content here: these files can already hold
  # other managers' keys (HO-IT-PC10 carries a third, vps-to-mac-tunnel) and an
  # overwrite would silently revoke them.
  $have = @(Get-Content $f -ErrorAction SilentlyContinue)
  foreach ($k in $MANAGER_KEYS) { if ($have -notcontains $k) { Add-Content -Path $f -Value $k -Encoding ascii -ErrorAction Stop } }
  if ($iAmAdminAccount) { icacls.exe $f /inheritance:r /grant 'SYSTEM:F' /grant 'BUILTIN\Administrators:F' | Out-Null }
  Write-Host ("  keys written to: " + $(if($iAmAdminAccount){'administrators_authorized_keys (admin account)'}else{'%USERPROFILE%\.ssh\authorized_keys'}))
}
# 4. PowerShell as the default SSH shell
Step 'default-shell' {
  if (-not (Test-Path 'HKLM:\SOFTWARE\OpenSSH')) { New-Item -Path 'HKLM:\SOFTWARE\OpenSSH' -Force | Out-Null }
  New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell `
    -Value "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force -ErrorAction Stop | Out-Null
}
# 5. firewall: port 22 to the TAILNET ONLY. Also tighten the default rule if Windows
#    created it wide open (that is the live P0 on HO-IT-PC10).
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
$tsip  = if (Test-Path $tsExe) { (& $tsExe ip -4 2>$null | Select-Object -First 1) } else { 'TAILSCALE NOT INSTALLED' }

Write-Host "`n=========== SEND THESE LINES BACK ===========" -ForegroundColor Green
Write-Host "USERNAME     : $env:USERNAME"
Write-Host "COMPUTERNAME : $env:COMPUTERNAME"
Write-Host "TAILSCALE_IP : $tsip"
Write-Host ("SSHD         : " + (Get-Service sshd).Status + ", " + (Get-Service sshd).StartType)
Write-Host ("LISTENER :22 : " + $(if($listener){'BOUND ' + ($listener.LocalAddress -join ',')}else{'NOT BOUND (a reboot usually binds it)'}))
Write-Host ("STEPS OK     : " + ($ok -join ', '))
if ($bad) { Write-Host "FAILED       :" -ForegroundColor Red; $bad | ForEach-Object { Write-Host "   $_" -ForegroundColor Red } }
Write-Host "=============================================" -ForegroundColor Green
Read-Host "`nPress Enter to close"
```

> **Step 3.** Copy the block it prints at the end and send it back. Done forever. ✅
>
> *(This only lets the private JIVO network in. Nothing is exposed to the public
> internet and no password is shared.)*

### If `openssh-installed` fails with `0x800f0954`

That's a managed-Windows-Update policy refusing the online capability store. Install the
MSI directly instead, then re-paste the block:

```powershell
$u='https://github.com/PowerShell/Win32-OpenSSH/releases/latest/download/OpenSSH-Win64-v9.8.1.0.msi'
$m="$env:TEMP\openssh.msi"; Invoke-WebRequest $u -OutFile $m
Start-Process msiexec.exe -ArgumentList "/i `"$m`" /quiet" -Wait
```

### Optional — the `victus` pattern: a dedicated `fleet` account

On victus you don't log in as `prabh`, you log in as **`fleet`** — a separate local
Administrator created **by hand** (no script does this; verified: none of the four
installers contain `New-LocalUser`). Worth copying when it fits:

- You never touch the owner's profile, and their password changes can't break you.
- No space in the name, so no `User "khushwinder singh"` quoting trap.
- One clean account to revoke later instead of picking your key out of theirs.

Against it: it's a **second admin account** on someone else's PC, and it needs a real
password (never leave it blank). For a colleague's machine, appending your key to their
existing admin account — what the block above does — is the smaller ask. Use `fleet`
for boxes that are effectively fleet hardware, not for a coworker's daily laptop.

```powershell
# elevated. Prompts for the password — do not hard-code one, do not leave it blank.
$pw = Read-Host "New password for the 'fleet' account" -AsSecureString
New-LocalUser -Name fleet -Password $pw -PasswordNeverExpires -AccountNeverExpires
Add-LocalGroupMember -Group Administrators -Member fleet
```

Then re-run the paste block **while logged in as `fleet`**, so the keys land against
that account.

---

## macOS — same idea, two lines

Run in Terminal on the Mac (it will ask for the login password for `sudo`):

```sh
sudo systemsetup -setremotelogin on                    # enable Remote Login (sshd)
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys <<'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB8+FPQ9luiwWsPUSZDY5UTwEiOVmL1o1zgf4sw1UORA daman8271@github
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHR8F2rqvcl7hHaAmpmXd3uogcx0AUflmMvlAART0JNK hermes-agent-access
EOF
chmod 600 ~/.ssh/authorized_keys
sudo pmset -a sleep 0 disksleep 0 womp 1               # stay reachable
echo "USERNAME: $(whoami)  TAILSCALE_IP: $(/usr/local/bin/tailscale ip -4 2>/dev/null | head -1)"
```

Two macOS-specific traps:

- **`tailscaled` must run as a system daemon**, or the Mac drops off the tailnet at
  logout. If Tailscale came from the App Store it's already a daemon; the standalone
  binary needs `sudo tailscaled install-system-daemon`.
- **A Mac with the lid shut sleeps** regardless of `pmset sleep 0` unless it's on AC
  with an external display, or you add `sudo pmset -a disablesleep 1`. This is the same
  lid-closed problem documented for the Mac Air.

---

## Manager side — after they send the two lines

Add the host, then prove it. **Quote a username containing a space** or ssh aborts with
`keyword user extra arguments`:

```sh
cat >> ~/.ssh/config <<'EOF'

Host <short-alias>
    HostName <TAILSCALE_IP>
    User "<USERNAME>"
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
    ServerAliveInterval 20
    ServerAliveCountMax 6
EOF

ssh <short-alias> 'hostname'          # must print their COMPUTERNAME
```

**Test with `ssh`, never with `nc`.** `nc -z <tailnet-ip> 22` reports *closed* on a
working box — measured 2026-07-30 against `dev`, which `ssh` reached fine in the same
second. Read ssh's own error instead, it's diagnostic:

| ssh says | Means | Do |
|---|---|---|
| `Operation timed out` | firewall blocking, or no sshd at all | re-run the paste block elevated |
| `Connection refused` | box reachable, nothing listening on 22 | sshd not started — re-run step 2 |
| `Permission denied (publickey)` | sshd fine, key in the wrong file | admin account → `administrators_authorized_keys` + ACL |

## Harden AFTER access is proven — never before

Turning password auth off *before* confirming your key works locks out you **and** the
box's owner. Only once `ssh <alias> 'hostname'` succeeds, run:

```sh
ssh <alias> 'Set-Content -Path C:\ProgramData\ssh\sshd_config -Value ((Get-Content C:\ProgramData\ssh\sshd_config) -replace "^#?\s*PasswordAuthentication.*","PasswordAuthentication no"); sshd -t; Restart-Service sshd'
```

`sshd -t` validates the config first — if it complains, do **not** restart the service.
Then re-test `ssh <alias> 'hostname'` in a **second** terminal before closing the first.

## Status 2026-07-30

| Box | Tailnet | SSH | Needs |
|---|---|---|---|
| `dev` HO-IT-PC10 | online | ✅ | firewall scoped to tailnet + password auth off (both still open) |
| `victus` | online | ✅ | — |
| `neelesh-veerji` | online | ❌ refused | the paste block (reachable, sshd just not running) |
| `harsh-veerji` | online | ❌ timeout | the paste block |
| `kanhaiya-veerji` | online | ❌ timeout | the paste block |
| `diljeet-singh` | online | ❌ timeout | the paste block |
| `macpro` | offline 3d | — | physical power-cycle first |

Linked: [[NEW-DEVICE]] · [[../SAP-HOME-ACCESS]] · [[../reverse-tunnel/README]]
