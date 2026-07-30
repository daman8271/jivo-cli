---
title: Fleet reverse tunnels — reach any Windows box from anywhere, no Tailscale
created: 2026-07-30
project: jivo-cli
type: runbook
tags: [fleet, ssh, reverse-tunnel, windows, vps, onboarding]
---

# Fleet reverse tunnels

Reach a Windows PC from the Mac Air, from **any** network, with **no Tailscale**, **no
password**, and **no auth key for the operator to paste**. The PC dials OUT to the fleet
VPS and parks a private door there; we come in through the VPS.

Same principle as [`../reverse-tunnel/`](../reverse-tunnel/README.md) (which reaches the
SAP box past its IP whitelist) — this is the Windows fleet version, with self-service
registration so no one has to hand-edit the VPS for each new box.

```
  Mac Air  ── ssh <box>-vps ──►  vps-pub 187.127.129.132
                                     │  127.0.0.1:230xx   (loopback ONLY)
                                     ▲
                                     │  reverse tunnel, redialed every minute
                                     │  by a SYSTEM scheduled task on the box
                               Windows PC  sshd :22
                               (outbound is never whitelist-checked,
                                so office/home/hotspot all work)
```

## Onboarding a box — 4 steps

```sh
# 1. build the installers (injects the registrar key; NEVER commit the output)
connections/fleet/build-tunnel-installer.sh both     # win | mac | both
#   -> ~/Downloads/JIVO-VPS-TUNNEL.cmd           (Windows, double-click + UAC)
#   -> ~/Downloads/JIVO-VPS-TUNNEL-MAC.command   (macOS, double-click + login password)

# 2. send them the file. They double-click it and approve the UAC prompt.
#    ~1 min. It prints a report block.

# 3. they send back the block. You need COMPUTERNAME, USERNAME, VPS PORT.

# 4. add the alias
cat >> ~/.ssh/config <<'EOF'
Host <name>-vps
    HostName 127.0.0.1
    Port <VPS PORT>
    User <USERNAME>
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ProxyJump vps-pub
    HostKeyAlias <name>-revtun
    StrictHostKeyChecking accept-new
    ServerAliveInterval 20
EOF
ssh <name>-vps 'hostname'
```

`HostKeyAlias` matters: every box is `127.0.0.1` from the Mac's point of view, so without
it their host keys collide and ssh starts refusing connections.

## What the installer does

1. **OpenSSH Server** — installs + sets Automatic. The door the tunnel lands on.
2. **OpenSSH Client** — needed to dial out.
3. **Manager key** — appends the Mac's public key to `administrators_authorized_keys`
   (or the user file for non-admins), ACL'd SYSTEM + Administrators only. **Appends,
   never overwrites** — these files can already hold other managers' keys.
4. **Default shell** → PowerShell.
5. **Its own tunnel keypair**, generated on the box. The private half never travels.
6. **Registers with the VPS** → gets a permanent port assigned.
7. **Dialer + SYSTEM scheduled task**, every minute + at boot.
8. **Verifies** the tunnel actually came up, then prints the report.

Idempotent — safe to re-run. Same box always gets the same port.

## The registrar (VPS side)

`fleet-tunnel-register.vps.sh` is deployed at `/root/fleet-tunnel-register.sh` as an SSH
**forced command**. The box sends its own public key; the registrar assigns a free port
from **23001–23099** and writes a tightly restricted `authorized_keys` line:

```
restrict,port-forwarding,permitlisten="127.0.0.1:<port>",permitopen="127.0.0.1:1" <key> revtun-<host>
```

`restrict` disables everything, `port-forwarding` re-enables forwarding **both ways**,
`permitlisten` constrains only the `-R` side — so `permitopen="127.0.0.1:1"` is what
actually blocks `-L`. Net: that key can open exactly one loopback port and nothing else.
No shell, ever.

Registry: `/root/fleet-tunnels.txt`. Log: `/root/fleet-tunnel-register.log`.

### Security tradeoff — read before handing the file out

The installer **embeds the registrar's private key**. That key is pinned to the registrar
script and cannot get a shell; worst case, whoever holds the file can register a tunnel
port on the VPS loopback. That is bounded, but it is not nothing:

- The built `.cmd` is **gitignored**. Only the template is in git. If you ever find the
  built file committed, rotate the registrar key.
- The key lives at `~/.ssh/jivo_tunnel_registrar` on the Mac, outside the repo.
- Rotate: `ssh-keygen -t ed25519 -f ~/.ssh/jivo_tunnel_registrar`, replace the
  `fleet-tunnel-registrar` line in the VPS `authorized_keys`, rebuild.

Validation is deliberately strict — the submitted key is shape-checked *and* run through
`ssh-keygen -l`, because `"ssh-ed25519 AAAAB3 x"` passes a regex and is still junk.

## Hard-won gotchas (all measured 2026-07-30, all cost real time)

| Symptom | Cause | Fix |
|---|---|---|
| `Permission denied (publickey)` dialing the VPS; key "ignored" | Windows OpenSSH refuses a private key any extra SID can read. `icacls /inheritance:r /grant` strips **inherited** ACEs but leaves **explicit** ones — including the per-logon-session SID stamped at file creation | Rebuild the DACL from scratch with `Set-Acl` (see `Lock-KeyFile` in the template) |
| Registration appears to hang forever | Windows `ssh.exe` runs the remote command in <1s then sits ~160s on session teardown, with or without `-n`. It is **latency, not a deadlock** — the work already succeeded | `Start-Process` + `WaitForExit(45000)` + `Kill()`, read the reply from a redirect file |
| `schtasks: Mandatory option 'sc' is missing` | PowerShell 5.1 mangles embedded quotes passed to native exes, so `/TR "... -File \"$p\""` loses `/SC` | Keep the dialer at a **space-free** path so `/TR` needs no inner quotes |
| Task `Last Result: -2147024894` (0x80070002) | Bare `powershell` doesn't resolve for SYSTEM | Full path `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |
| `Register-ScheduledTask` fails 0x80070002 on Win11 26100 | cmdlet bug on that build | Create with `schtasks`, then adjust settings via `Set-ScheduledTask` |
| Tunnel dies after 3 days | Task default `ExecutionTimeLimit` is 72h | `ExecutionTimeLimit PT0S` (unlimited) |
| `nc -z <host> 22` says closed on a working box | Generic TCP probes misreport over overlay/proxied paths | Test with `ssh` itself; read its error text — *refused* (no listener) ≠ *timed out* (filtered) |

**Not a bug:** `<Duration>PT10M</Duration>` in the task XML is under `<IdleSettings>`,
**not** the trigger. The trigger is `<Repetition><Interval>PT1M</Interval></Repetition>`
with no Duration — that means repeat **indefinitely**, which is correct.

## Always-on hardening (applied automatically by the installer)

The tunnel is only as permanent as the box under it. The installer therefore also:

- **Never sleeps / never hibernates.** `-ac` timeouts zeroed always; `-dc` only when the
  machine has **no battery** — on a laptop that would flatten it. Hibernate off also
  kills Fast Startup, which otherwise leaves a hybrid-shutdown state where boot triggers
  misbehave.
- **Stops Windows powering down the NIC.** `PnPCapabilities=24` on the adapter's class
  key. ⚠️ `Disable-NetAdapterPowerManagement -NoRestart` **returns success and changes
  nothing readable** until the adapter reinitialises — measured on JIVO-B1, where the
  report claimed OK while the setting was still `Enabled`. The registry value is the
  durable control and lands at next reboot. We deliberately do **not** bounce the
  adapter: losing the NIC on a remote box needs physical access to fix, and with
  never-sleep set it will not be powered down anyway.
- **Watchdog task, every 15 min + at boot.** The 1-minute dialer recovers a *dropped*
  tunnel. It cannot recover from its own task being deleted or disabled, sshd stopped, or
  power settings drifting back after a Windows update. That is the watchdog's job.

### Measured resilience — not assumed

| Test | Result |
|---|---|
| Kill the tunnel (victus) | back in **55 s** |
| Kill the tunnel (JIVO-B1) | back in **35 s** |
| **Delete the dial task entirely + kill the tunnel** (victus) | watchdog rebuilt the task and the VPS listener returned |
| **Real reboot** (victus, 2026-07-30) | listener returned **unattended in ~70 s**; boot time 04:27→21:25, new tunnel PID — genuinely power-cycled |

### Surviving a reboot

Windows silently **refuses** to start a task under conditions most people never look at,
and `schtasks` defaults some of them the wrong way. Both tasks are normalised to:

| Setting | Value | Why |
|---|---|---|
| `BootTrigger` + `<Delay>PT30S</Delay>` | present | at T+0 the network stack is not up, so an immediate dial is a guaranteed failure |
| `DisallowStartIfOnBatteries` | **false** | ⚠️ `schtasks` defaults this to **true** — on a laptop the watchdog, the thing meant to repair everything, silently does not run on battery. Found on VICTUS |
| `StopIfGoingOnBatteries` | false | unplugging must not kill a live tunnel |
| `StartWhenAvailable` | true | catches a trigger missed while the box was off |
| `RunOnlyIfNetworkAvailable` | false | Windows' own network detection is a start-blocker |
| `ExecutionTimeLimit` | `PT0S` dialer / `PT10M` watchdog | the dialer's ssh runs forever; a *bounded* watchdog is required or one hung run blocks all later runs via `IgnoreNew` |
| `Schedule` service | Automatic | no scheduler, no tunnel |

A fresh install produces all of this with no manual step — verified by wiping VICTUS and
its VPS registration and re-running the installer untouched.

**Verified by an actual power-cycle**, not just config inspection: VICTUS was rebooted
2026-07-30, its VPS listener vanished within 5 s and came back **unattended in ~70 s**.
Boot time moved 04:27:39 → 21:25:16 and the tunnel PID changed (6884 → 8076), so it was a
real restart and a real re-dial — nobody logged in, nothing was touched by hand.


## macOS variant

`JIVO-VPS-TUNNEL-MAC.command` — same architecture, same registrar, same VPS. Only the
persistence layer differs, and the Mac one is **better**: launchd's `KeepAlive` restarts
the dialer the instant it exits, instead of Windows polling every minute.

| | Windows | macOS |
|---|---|---|
| Supervisor | scheduled task, 1-min repeat + boot trigger | launchd `KeepAlive` + `RunAtLoad` |
| Recovery | 35–55 s | **~1 s** (measured: PID 62683 → 62695) |
| Elevation | UAC prompt | `sudo`, asks for the login password |
| Never-sleep | `powercfg` | `pmset -a sleep 0 disksleep 0 womp 1` |
| Door | OpenSSH Server capability | Remote Login |
| Config | `C:\ProgramData\jivo-revtun` | `/usr/local/jivo-revtun` |

### macOS gotchas

- **Gatekeeper quarantine.** A `.command` that arrives by download/AirDrop carries
  `com.apple.quarantine`, and double-clicking gives *"cannot be opened because it is from
  an unidentified developer."* Fix: **right-click → Open** (once), or
  `xattr -d com.apple.quarantine ~/Downloads/JIVO-VPS-TUNNEL-MAC.command`. Expected but
  not exercised in testing — the test copy was `scp`'d, which does not set the attribute.
- **`systemsetup -setremotelogin` needs Full Disk Access** on 10.14+ and fails *silently*
  from a plain Terminal. The script tries `systemsetup` **and** `launchctl bootstrap`,
  then **verifies** with `-getremotelogin` rather than trusting either. If it still
  fails, the report says so and the operator turns on Remote Login in
  System Settings → General → Sharing.
- **Sanitise the hostname AFTER capturing it.** `hostname -s | tr -c ...` pipes the
  trailing newline into `tr`, which converts it to `_` — the registry showed
  `dannys-Mac-Pro_`. Capture with `$(...)` first, then sanitise.
- **Log in as the human, not root.** `TARGET_USER` comes from `$SUDO_USER`, so the
  manager key lands in the real user's `~/.ssh/authorized_keys`. Usernames can contain a
  dot (`danny.` on the Mac Pro) — legal for the registrar, no quoting needed, unlike the
  Windows space case.
- **Lid-closed laptops still sleep** despite `pmset sleep 0`. `disablesleep 1` fixes it
  but is only applied when the machine has **no battery** — on a laptop it would flatten
  it. A closed MacBook on battery will drop off; that is deliberate.
- **`plutil -lint` before loading.** A malformed plist that launchd refuses leaves the
  box with no tunnel and no error anyone will see.

## Operate

```sh
ssh vps 'cat /root/fleet-tunnels.txt'                  # who is registered, on which port
ssh vps 'ss -ltn | grep 127.0.0.1:230'                 # which tunnels are actually live
ssh vps 'tail /root/fleet-tunnel-register.log'         # registration history
ssh <box>-vps 'Get-Content C:\ProgramData\jivo-revtun\revtun.log -Tail 20'
ssh <box>-vps 'schtasks /Query /TN JivoRevTunnel /V /FO LIST | Select-String "Last Result|Status"'
```

**Self-healing is measured, not assumed:** killing the tunnel and timing recovery gave
**55s** (design target ≤60s). The VPS's `ClientAliveInterval 30` / `CountMax 3` reaps a
stale listener in ~90s, so a hard-dead box doesn't wedge its port.

## Revoke a box

```sh
ssh vps 'sed -i "/ revtun-<HOST>/d" /root/.ssh/authorized_keys; sed -i "/^<HOST>/d" /root/fleet-tunnels.txt'
ssh <box>-vps 'schtasks /Delete /TN JivoRevTunnel /F; Remove-Item C:\ProgramData\jivo-revtun -Recurse -Force'
```
Removing the VPS line alone is enough to cut it off — the box can then dial but not listen.

## Status

| Box | Port | Alias | State |
|---|---|---|---|
| `VICTUS` | 23001 | `victus-vps` | ✅ live, hardened, clean-room verified end to end |
| `JIVO-B1` (Diljeet's) | 23002 | `diljeet` | ✅ live, hardened; **reaches SAP** (50000/30015/22 all open) |
| `dannys-Mac-Pro` | 23003 | `macpro-vps` | ✅ live, hardened (macOS 12.7.6); launchd restart verified ~1 s |
| harsh, kanhaiya, neelesh | — | — | not yet onboarded; send them the installer |

`JIVO-B1` sits inside the office network, so `Mac → VPS → JIVO-B1 → SAP` works from
anywhere. Verified: the SAP Service Layer answered **HTTP 401** through that chain — a
response, so reachable; it just wants credentials. That is a second, independent route to
SAP alongside [`../reverse-tunnel/`](../reverse-tunnel/README.md).

```sh
# SAP Service Layer from home, through Diljeet's box
ssh -f -N -L 15055:103.89.45.192:50000 diljeet
(cd sap-b1/cli && set -a && source .env && set +a && SAPB1_HOST=localhost SAPB1_PORT=15055 ./sapb1 doctor)
```

Linked: [[../reverse-tunnel/README]] · [[../SAP-HOME-ACCESS]] · [[ADD-SSH-FORWARD]] · [[../../NEW-DEVICE]]
