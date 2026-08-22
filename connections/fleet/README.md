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

# 3. they send back the block. Read REACHABLE first — v6 proves it from the VPS.
#    You also need COMPUTERNAME, USERNAME, VPS PORT.

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

### ⚠️ `bash` is missing on the operator boxes — which silently kills the harness

Measured 2026-08-22 across every reachable Windows operator box (`lovepreet`,
`param`, `preshit`, and `sohail` at enrolment): **`bash` did not resolve at
all.** Git was installed on all of them, but its installer only puts
`C:\Program Files\Git\cmd` on the PATH — and `bash.exe` lives in
`Git\bin`, which is not added. On Sohail's box the only `bash` on the PATH was
the `WindowsApps` WSL stub, out of *Administrator's* profile, so it would not
have resolved for the human user either.

This matters far more than it looks. Every harness hook in
`.claude/settings.json` is `bash "$CLAUDE_PROJECT_DIR/harness/hooks/…"`. With
no `bash`, `session-start.sh` never runs, and because the hook's stderr is
redirected **the operator is told nothing** — their Claude simply starts with
zero corrections and behaves like a stock model on JIVO's data. That is the
exact failure mode `harness.py`'s own UTF-8 comment warns about, arriving
through a different door.

Fix (idempotent, applied to all four boxes 2026-08-22) — prepend Git's `bin`
to the **Machine** PATH so every profile gets it:

```powershell
$gitbin='C:\Program Files\Git\bin'
$m=[Environment]::GetEnvironmentVariable('Path','Machine')
if (($m -split ';') -notcontains $gitbin) {
  [Environment]::SetEnvironmentVariable('Path',(@($gitbin)+($m -split ';'|?{$_})) -join ';','Machine')
}
```

Verify with the hook itself, not with `Get-Command bash` alone — a healthy box
returns ~4.9 KB of correction text:

```powershell
$env:CLAUDE_PROJECT_DIR=$repo; bash "$repo/harness/hooks/session-start.sh"
```

**Add this to every future enrolment.** A box can pass `doctor`, reach SAP, and
still be running a Claude that knows none of the team's rules.


| Symptom | Cause | Fix |
|---|---|---|
| `Permission denied (publickey)` dialing the VPS; key "ignored" | Windows OpenSSH refuses a private key any extra SID can read. `icacls /inheritance:r /grant` strips **inherited** ACEs but leaves **explicit** ones — including the per-logon-session SID stamped at file creation | Rebuild the DACL from scratch with `Set-Acl` (see `Lock-KeyFile` in the template) |
| Registration appears to hang forever | Windows `ssh.exe` runs the remote command in <1s then sits ~160s on session teardown, with or without `-n`. It is **latency, not a deadlock** — the work already succeeded | `Start-Process` + `WaitForExit(45000)` + `Kill()`, read the reply from a redirect file |
| `schtasks: Mandatory option 'sc' is missing` | PowerShell 5.1 mangles embedded quotes passed to native exes, so `/TR "... -File \"$p\""` loses `/SC` | Keep the dialer at a **space-free** path so `/TR` needs no inner quotes |
| Task `Last Result: -2147024894` (0x80070002) | Bare `powershell` doesn't resolve for SYSTEM | Full path `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |
| `Register-ScheduledTask` fails 0x80070002 on Win11 26100 | cmdlet bug on that build | Create with `schtasks`, then adjust settings via `Set-ScheduledTask` |
| Tunnel dies after 3 days | Task default `ExecutionTimeLimit` is 72h | `ExecutionTimeLimit PT0S` (unlimited) |
| `nc -z <host> 22` says closed on a working box | Generic TCP probes misreport over overlay/proxied paths | Test with `ssh` itself; read its error text — *refused* (no listener) ≠ *timed out* (filtered) |
| Installer prints `STEPS OK … verify-tunnel` **and** `SSHD : Stopped`; VPS listener binds but `ssh <box>` gives `kex_exchange_identification: Connection closed by remote host` | The tunnel forwards to `localhost:22`, so a **stopped sshd** looks identical to a broken tunnel. Step 6d starts the service with `-ErrorAction SilentlyContinue`, so a failed start is swallowed and the run still reports success. Seen where OpenSSH was **already present** (`openssh-server(already)`) — a pre-existing install with missing host keys refuses to start | Read the `SSHD :` line of the installer summary before trusting `STEPS OK`. **Since v8 the installer does not stop at advice:** when sshd is not answering on 127.0.0.1:22 it runs `C:\ProgramData\jivo-revtun\sshd-repair.ps1` (diagnose -> port-22 holder -> service registration -> host keys + ACLs -> sshd_config -> reinstall from the ZIP) and prints every rung under `SSHD ROUTES`. By hand, as admin: `powershell -File C:\ProgramData\jivo-revtun\sshd-repair.ps1` (`-DiagnoseOnly` to look without touching). The watchdog runs the same ladder (`-NoReinstall`) every 15 min whenever sshd is down or bound off-loopback; a foreign process holding port 22 is named, never killed. Hit on `DILPREETSINGH` (23009, dead 24 h) and `DESKTOP-73N6JE8` (23011; v7 on 2026-08-21 still printed "REFUSES TO START" and nothing else, which is why the ladder exists) |

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
- **SSH sessions cannot LIST `~/Documents`, `~/Desktop`, `~/Downloads`** (TCC returns
  `Operation not permitted` — hit on Karanpreet's Air 2026-08-08). But it is
  enumeration that's blocked, not everything: **creating files at exact known paths
  (`mkdir -p` + `cp` to a full path) worked, and even cd+exec succeeded minutes later**
  — so credentials CAN be placed into a Documents checkout remotely if you know the
  paths. Still, prefer repos in the home root (`~/jivo-cli`), or flip
  System Settings → General → Sharing → Remote Login (ⓘ) →
  **"Allow full disk access for remote users"** on the box.

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

## Monitoring — added 2026-08-11 after a 13.5 h silent outage

Self-healing covers a *dropped* tunnel. It does nothing for a box whose dialer has
stopped altogether, and **nothing was watching for that**. `DESKTOP-5VCMOAS` (Manav,
23005) last dialed at **04:23 on 2026-08-11** and the outage was found 13.5 h later,
by hand, only because someone needed the box. Every tunnel had the same blind spot.

`fleet-tunnel-health.vps.sh` → `/root/bin/fleet-tunnel-health.sh`, cron `*/10`.
It diffs the registry against the kernel's listen table, remembers how long each box
has been gone, and alerts over Telegram.

```sh
ssh vps 'cat /root/fleet-tunnel-status.txt'          # last computed state, all boxes
ssh vps '/root/bin/fleet-tunnel-health.sh report'    # recompute now, never alerts
ssh vps 'tail /root/fleet-tunnel-health.log'
```

**Alerting is deliberately quiet.** Office PCs are switched off nightly; alerting on
that trains everyone to ignore the alerts. So a box must be down **>4 h** *and* it must
be **10:00–19:00 IST** before it is reported, with a 12 h per-host cooldown. An
overnight shutdown is silent; a genuinely dead box is reported the next morning.
Tune with `ALERT_AFTER_MIN` / `HOUR_FROM` / `HOUR_TO` / `COOLDOWN_MIN`.

### The disk guard is part of the same script, and it is not optional

The same day, the VPS root filesystem was found **100% full — 0 bytes free**. Cause:
**39,671 leaked `/tmp/tirith-install-*` directories inside the `hermes` container**
(8.5 MB each, ~36 GB), created one-per-run by hermes' installer and never removed.

A full disk is a **fleet-wide outage that looks like nothing**: the registrar cannot
append to `authorized_keys` or `fleet-tunnels.txt`, so **no new box can ever enrol**,
and it surfaces only as a stray `No space left on device` from some unrelated command.
The health script therefore also alerts at **≥85%**, and `hermes-tmp-gc.vps.sh`
(cron `17 * * * *`) reaps leak dirs older than 2 h. That GC is a mitigation — the leak
itself is upstream in hermes.

| Trap | Detail |
|---|---|
| `grep -c` exits **1** on a zero count | so `count=$(... grep -c ... \|\| echo 0)` fires the fallback on the *healthy* path and yields `"0\n0"`, which blows up the arithmetic. Swallow the status inside the container (`\|\| true`) and default in the shell. Hit while writing the GC script. |
| Docker stores layers under containerd's **`moby`** namespace | `ctr -n default c ls` shows **zero containers** on a box running 15 of them, which makes 44 GB of live images look like prunable junk. Check `docker ps` before concluding anything is orphaned. |

## v6 — the installer now proves the box is reachable (2026-08-19)

Up to v5 the installer finished by checking things it could see **from inside the
box**: the `sshd` service says Running, an `ssh.exe` holds the `-R` flag. Both are
true on a machine nobody can log in to, which is how `JIVO201` (23010),
`DESKTOP-73N6JE8` (23011) and `DILPREETSINGH` (23009) each burned days behind a
green screen.

v6 asks the VPS instead. The registrar takes a second verb:

```sh
VERIFY HOST=<name>
  -> REACHABLE=yes PORT=<n> BANNER=SSH-2.0-OpenSSH_for_Windows_9.5
  -> REACHABLE=no  PORT=<n> REASON=tunnel-up-but-sshd-silent
  -> REACHABLE=no  PORT=<n> REASON=no-tunnel-parked-on-this-vps
```

It reads a real SSH banner off that box's own loopback port **here**, which cannot
answer unless the tunnel is parked *and* `sshd` is listening — and it names which
half is broken, because from the box those two look identical. The installer calls
it at the end and prints a `REACHABLE` line. **That is the only line in the report
block worth trusting**; every other line describes a part.

Check any box yourself, any time:

```sh
ssh vps 'SSH_CONNECTION="1 1 1 1" SSH_ORIGINAL_COMMAND="VERIFY HOST=JIVO201" /root/fleet-tunnel-register.sh'
```

Also in v6, all of it because a route failed **without saying why**:

- **three** independent routes to `sshd` on Windows — Windows Update, the signed
  MSI, and the plain ZIP + `install-sshd.ps1`. The ZIP route needs neither Windows
  Update nor the MSI engine, so it survives a locked-down office box. Every route
  records its reason and they all reach the report block.
- downloads are validated by length **and magic bytes**. An office proxy answers a
  blocked host with an HTML page and HTTP 200, which `Invoke-WebRequest` calls
  success and `msiexec` then rejects with an exit code nobody was reading.
- `msiexec` is finally checked (`-PassThru`), including a `REINSTALL` retry on 1638
  — the product registered but the service deleted.
- the shipped `sshd_config` is dropped in when missing. It carries the
  `Match Group administrators` block, without which the manager key the installer
  just wrote is silently ignored — unreachable by a different door.
- **macOS caught up.** It had the same faults and some worse ones: `step()` threw
  the failure *reason* away entirely, there was no log file, and there was no
  version stamp at all (v1–v5 shipped unversioned, because the build script only
  checked that the placeholder was *gone*, which passes when it was never there).
  Remote Login now has three routes that each report what macOS actually said, and
  is believed only when port 22 returns a banner — `-getremotelogin: On` is true on
  a Mac where `sshd` is not listening. The `com.apple.access_ssh` membership trap is
  handled too.

Verified on real hardware, not in theory: full v6 run end to end on `VICTUS`
(Windows 11, PowerShell 5.1) and `dannys-Mac-Pro` (macOS 12.7.6) — both returned
`REACHABLE: YES`, both left the registrar key wiped, neither had its `sshd_config`
or scheduled tasks disturbed.

## When one is broken → [`RECOVERY-RUNBOOK.md`](RECOVERY-RUNBOOK.md)

This file is how a tunnel gets *built*. [`RECOVERY-RUNBOOK.md`](RECOVERY-RUNBOOK.md) is
what to do when one is **down**: a decision table of state → which channel to try in what
order (reverse tunnel → Tailscale → a human), the two root causes found 2026-08-17 (the
installer's early `return` that skipped starting sshd; a watchdog that cannot recover a
missing host key), and **copy-pasteable messages per colleague** for the boxes where no
remote channel is left.

⚠️ Read it before trusting `ss -ltn`. An **UNREACHABLE** box — port listening, sshd dead
— passes every naive check and is the state that cost 4+ days on three boxes. And read
the state **during office hours**: measured 2026-08-17, `JIVO` and `JIVO201` read
UNREACHABLE at 19:10 and **DOWN at 21:14** with an unchanged `since`, because the PCs
were switched off. Nothing was repaired — a broken box quietly files itself under
"switched off for the day", which is the one bucket whose documented response is *wait*.

## Revoke a box

```sh
ssh vps 'sed -i "/ revtun-<HOST>/d" /root/.ssh/authorized_keys; sed -i "/^<HOST>/d" /root/fleet-tunnels.txt'
ssh <box>-vps 'schtasks /Delete /TN JivoRevTunnel /F; Remove-Item C:\ProgramData\jivo-revtun -Recurse -Force'
```
Removing the VPS line alone is enough to cut it off — the box can then dial but not listen.

## Give an operator SAP with **no VPN** (done for `JIVO201` 2026-08-05)

The office PCs reach SAP only over the FortiClient VPN (profile `Mieux` →
`103.178.248.2:20443`), because `138.252.101.222` is IP-whitelisted to the office. An
operator working from home who forgets the VPN gets `cannot reach
138.252.101.222:50000 over TCP` and nothing runs.

They don't need the VPN. The SAP box already parks its own outbound tunnels on the
VPS — `127.0.0.1:47500` → Service Layer `:50000` and `127.0.0.1:47301` → HANA
`:30015` (see [`../reverse-tunnel/`](../reverse-tunnel/README.md) §8b). A box that
already has a fleet tunnel just needs permission to reach *in* to those two ports.

**Two changes. Both small.**

```sh
# 1. VPS — widen that ONE key's permitopen (it ships locked to 127.0.0.1:1 = deny-all)
ssh vps 'cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak-$(date +%F-%H%M%S)'
#   restrict,port-forwarding,permitlisten="127.0.0.1:<PORT>",permitopen="127.0.0.1:1"
#     ->  ...,permitopen="127.0.0.1:47500",permitopen="127.0.0.1:47301"
```

```powershell
# 2. On the box — a SECOND dialer + task, never merged into dial.ps1
#    C:\ProgramData\jivo-revtun\dial-sap.ps1  (same key, adds only -L)
ssh.exe -N -T -n -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 `
  -i C:\ProgramData\jivo-revtun\id_ed25519 `
  -L 127.0.0.1:50000:127.0.0.1:47500 `
  -L 127.0.0.1:30015:127.0.0.1:47301 root@187.127.129.132
schtasks /Create /TN JivoSapTunnel /TR "...-File C:\ProgramData\jivo-revtun\dial-sap.ps1" `
  /SC MINUTE /MO 1 /RU SYSTEM /RL HIGHEST /F
```

⚠️ **Keep it a separate task from `JivoRevTunnel`.** `ExitOnForwardFailure=yes` means
a local 50000/30015 clash kills the process. Separate, that costs only SAP; merged, it
would take port-22 with it and lock you out of the box. Same reason `dial-ports.sh` is
split from `dial.sh` on the SAP box. Check both ports are free *before* installing, and
extend `watchdog.ps1` to kick the new task too.

Then point their kit at the tunnel — **host only, the port number is unchanged**:

```
SAPB1_HOST=localhost      # instead of the direct 138.252.101.222
SAPB1_PORT=50000
```

`localhost:50000` is safe for the Host-header trap: SAP's Apache 403s unrecognised
`Host` values, but `127.0.0.1:*` and `localhost:*` are both accepted (measured — see
[`../SAP-HOME-ACCESS.md`](../SAP-HOME-ACCESS.md) §8b). Never point `SAPB1_HOST` at a
bridge/LAN IP.

This is strictly better than the VPN for them: one config that works at home, on a
hotspot **and** in the office, since the path never touches the office network. It adds
no write capability — RULE 0 is untouched, it's a route not a permission. Trade-off:
the chain is longer (`box → VPS → SAP box`), so a VPS or SAP-tunnel outage now costs
them SAP even while sitting in the office; the VPN remains the fallback.

Measured on `JIVO201`: `sapb1 doctor` → **All checks passed** from a non-whitelisted
home IP; all 3 company DBs returned counts; killing the tunnel recovered in **40 s**
with the port-22 tunnel untouched.

## Status

| Box | Port | Alias | State |
|---|---|---|---|
| `VICTUS` | 23001 | `victus-vps` | ✅ live, hardened, clean-room verified end to end. **On v6** (2026-08-19), `REACHABLE=yes` |
| `JIVO-B1` (Diljeet's) | 23002 | `diljeet` | ✅ live, hardened; **reaches SAP** (50000/30015/22 all open) |
| `dannys-Mac-Pro` | 23003 | `macpro-vps` | ✅ live, hardened (macOS 12.7.6); launchd restart verified ~1 s. **On v6** (2026-08-19), `REACHABLE=yes` |
| `JIVO201` (avtar's) | 23010 | `avtar` | ✅ **repaired 2026-08-19 18:36 by the v6 ZIP route**, `REACHABLE=yes`, shell verified. It had been unreachable since that morning — sshd absent, tunnel parked, nothing behind it. Windows Update was blocked and the MSI reconfigured itself to exit 0 **without creating the service**; only route 3 (ZIP + `install-sshd.ps1`) worked, and `sshd.exe` now lives in `C:\Program Files\OpenSSH-Win64`. First box the third route ever saved. Originally ✅ live 2026-08-05; Dell Inspiron 15 3511, i5-1135G7, 8 GB, Win 11; dialer + watchdog verified, battery traps clear. **+ `JivoSapTunnel` — SAP with no VPN** (see section above); `.env` → `localhost:50000`, `doctor` passes from home. **Brought current 2026-08-22 13:30–14:10** — he had been silently stuck since 08-20 14:09 on a **0-byte `.git/index.lock`**: an interactive rebase of his own correction commit died mid-flight, so `main` sat detached at `f16807c` and **every git write on the box failed for two days**. This is the second time this box has lost time to a stale lock (see the 08-06 note) — when git "does nothing" on an operator box, look for the lock first. Recovered: lock deleted, `rebase --abort`, `reset --hard origin/main`, then ff to `06fe05e`. His stranded correction was rescued and re-filed as **C-0023** (a party ledger comes from JDT1, not from document extracts) and pushed — it had reached nobody. `sparse-checkout disable`d: its only pattern was the obsolete `Entities:.md` exclude, dead since `c7d84b6`. Overlaid the not-in-git work: `portals/gst/` (all 8 registrations configured, `doctor --offline` clean — no live login run), `connections/ary.env`, `accounts-dashboard/`, `acc/`, both `sap-*-bridge.sh`. Verified from the box: `sapb1 doctor` green on Oil via `localhost:50000`, ARY healthy (SQL Server 2017, 72 user DBs) with a live 7-day `FR8HODBNEW` sale query, `hana-sql.exe` reproduced the whole C-0023 evidence query, harness 23 corrections + digest built + recall indexed (141 files / 1627 chunks). Claude Code was **absent** (its `.claude/` history showed it had once run) — reinstalled 2.1.239 via npm into `%APPDATA%\npm` (already on PATH; SSH lands as `avtar`, the same user the human works as, so **no two-profile trap here** unlike `HO-IPEXP-PC2`) and auth relayed → `claude -p` **AUTH-OK**. Note `npm i -g` blocks the postinstall by default on npm 11 — re-run with `--allow-scripts=@anthropic-ai/claude-code` or `claude` never appears. **Two untracked dashboards of his own live here and exist nowhere else** — `sap-b1/accounts-kit/branch-reco/` and `reco-dashboard/` (JIVO Wellness vs Mart reco, with its xlsx); they survived the reset, and they should be reviewed for main. `harness/.persona` is still **`all`**, not `accounts` — he loads every area's rules. **Not shipped:** TankhaPay, any infra key, `jolly/` (per-person dossiers), `jivo-chat/`. |
| `DESKTOP-73N6JE8` (Ziyaul's) | 23011 | `ziyaul` | ✅ **repaired 2026-08-21 18:05 by v9's rung 4**, `REACHABLE=yes`, `ssh ziyaul` verified **6/6** from the Mac; `sshd` StartType=Automatic + Running, dialer `JivoRevTunnel` + watchdog `JivoTunnelWatchdog` both Enabled. **Root cause: host-key ACLs too open** — the three `ssh_host_*_key` files existed at correct sizes, but their permissions were loose, so `sshd -t` failed `UNPROTECTED PRIVATE KEY FILE` and sshd **crash-looped 66 times** (SCM auto-restarting every 60 s, never staying up). Every earlier run's `ssh-keygen -A` check passed *because the keys were present* — the fault was the ACLs, not missing keys, which is why v7 could only report "refuses to start". v9's rung 4 ran `ssh-keygen -A` **and reset the host-key ACLs to SYSTEM + Administrators only**, and sshd came up on that rung. **First box to prove the v9 ladder climbs past rung 3** — v8 (17:40) stopped at rung 3 on the logger bug; v9 (18:00) climbed to rung 4 and fixed it. Had been UNREACHABLE since 2026-08-05 (tunnel up, sshd dead). |
| `DILPREETSINGH` (now **Param, accounts**) | 23009 | `dilpreet`, `param`, `param-acc` | ✅ **back 2026-08-21 ~18:00 on v8**, `REACHABLE : YES`, `SSHD : Running` (plain start; the ladder was not needed). Had been unreachable since 2026-08-04 |
| `Karanpreets-MacBook-Air` | 23012 | `karanpreet` | ✅ live 2026-08-08; macOS 26.5.1, installer AirDropped + double-clicked, verified end to end. Daemon KeepAlive+watchdog confirmed running. `disablesleep 1` set by hand 2026-08-08 (verified `SleepDisabled=1`) — lid-proof, but it's a battery laptop: **keep it plugged in** or it drains to empty with the lid shut |
| `HO-IT-PC1` (preshit's) | 23013 | `preshit` | ✅ live 2026-08-19 on **v7**, `REACHABLE=yes`, shell verified, `ssh preshit` works from the Mac. ⚠️ **Its sshd service is MARKED FOR DELETION** (a pre-install OpenSSH uninstall on this IT PC left the SCM mark; `Set-Service` is refused — the summary's red FAILED line — and Windows deletes the service at the next reboot, which the watchdog cannot repair). Covered by a hand-planted **`JivoSshdReviver`** ONSTART task (`C:\ProgramData\jivo-revtun\sshd-reviver.ps1`, log next to it) that recreates sshd from the on-disk binaries with `start= auto` + failure-restart at every boot. Quirk: on-demand `schtasks /Run` silently no-ops on this box while scheduled triggers fire fine — verify by the script's log line, not by /Run. Reaches SAP directly (`138.252.101.222:50000` open — office LAN). Git 2.55 installed 2026-08-19; `jivo-cli` sparse clone in `Downloads` (excludes `portals/`, `jivo-scraping-cli/`, and the colon-named vault file; `core.protectNTFS=false` repo-local because `sap-b1/vault/services/Entities:.md` otherwise kills any Windows checkout); `C:\jivo-sap\sapb1.exe` staged with the shared manager `.env` (Daman's call 2026-08-19) — `doctor` green, all 3 companies verified from the box |
| `83USER` (Navdeep, accounts) | 23014 | `navdeep`, `navdeep-acc` | ✅ live 2026-08-21 18:18 on **v9** (the same installer file as Ziyaul's), `REACHABLE=yes` (banner `OpenSSH_for_Windows_10.0`), `ssh navdeep-acc` shell verified; sshd Automatic + Running, `JivoRevTunnel` + `JivoTunnelWatchdog` present. Windows Update route abandoned at 150 s → the MSI route installed OpenSSH 10.0 preview into `C:\Program Files\OpenSSH`. **Laptop** (Dell Inspiron 15 3520, Win 11 26200): AC sleep off, but sleep-on-battery stays at 3 min **by design** (harden.ps1 skips `-dc` on battery boxes) — **keep it plugged in** or it drops off the fleet 3 min after he walks away. Registered from `132.154.66.99` (not the office IP) and SAP `doctor` still logged in from there. Kit fitted 18:25–18:40: `Documents\jivo-cli` full shallow clone @ `c7d84b6` — the first Windows clone that needed **no sparse excludes** (the colon file is gone); Git 2.55 was already installed; Claude Code 2.1.238 + relayed auth (`claude -p` → AUTH-OK; shares the Max limits); `C:\jivo-sap\sapb1.exe` + shared manager `.env` (partners Oil 3407 / Mart 2191 / Bev 2957 verified from the box); `connections\hana.env` direct `.222:30015` verified as ZIA; root `.env` minus TankhaPay; `control-panel\.env`; `harness/.persona`=accounts. **Not shipped:** TankhaPay, DSR (sysadmin SQL login), any infra key. |
| `HO-IPEXP-PC2` (Lovepreet, import/export) | 23015 | `lovepreet`, `ho-ipexp-pc2` | ✅ live 2026-08-22 12:56 on **v9** (`e30a3ed`), `REACHABLE=yes` (banner `OpenSSH_for_Windows_9.5`), `ssh lovepreet` shell verified from the Mac; sshd Running, watchdog every 15 min, sleep/hibernate off. Registered from `122.180.240.216` — **not** the office IP, and SAP still logged in from there (third counter-example to the IP-block theory). Win 10 Enterprise N, 157 GB free. **Two profiles matter here:** SSH lands as `Administrator`, but the human works in `C:\Users\Jivo108` — his Documents is the one holding `LICENSE DETAILS\ADVANCE LICENSE` / `DFIA LICENSE`, shipping-line and seal-proof files. The kit belongs in **`C:\Users\Jivo108\Documents\jivo-cli`** (it was first dropped in `Administrator\Documents`, which he cannot see, then moved and `icacls`-granted `Jivo108:F`). Kit fitted 13:05–13:45: shallow clone @ `34fd63f` **plus** the uncommitted work (`acc/`, `accounts-dashboard/`, `portals/gst/` minus its `.env`, the two `connections/sap-*-bridge.sh`, the harness + fleet-doc edits) overlaid on top; **winget's source is broken on this box** (`0x8a15000f`) so Git 2.55.0.5 and Python 3.12.10 were both installed from direct downloads; the preinstalled `python` was only the Microsoft Store stub — real Python now wins the PATH and `harness.py status` + `recall.py index` (147 files / 1633 chunks) both run. SAP verified from the box: shared manager `.env` green on all three (Oil 3407 / Mart 2191 / Bev 2957), **and his own named `USER06` now works** — the password we held was dead, the new one was supplied 2026-08-22 and `doctor` logs in as USER06. `connections\hana.env` direct `.222:30015`; root `.env` minus TankhaPay; `control-panel\.env`; `harness/.persona`=**exim**. **Not shipped:** TankhaPay, DSR, GST portal `.env`, ARY/MSSQL, any infra key, and neither `jolly/` (per-person dossiers) nor `jivo-chat/` (VPS app + live DB). Tarring the overlay on macOS dragged in 278 `._*` AppleDouble files (one, `._.`, even broke `icacls`) — all deleted; use `COPYFILE_DISABLE=1 tar` next time. Then fitted for AI use: Node 22.20.0 (MSI) + **Claude Code 2.1.239** installed with a **machine-wide npm prefix `C:\ProgramData\npm`** (the default `%APPDATA%\npm` would have hidden it from `Jivo108` — same two-profile trap), that prefix added to the *Machine* PATH, and the Mac Keychain OAuth blob relayed into **both** `Jivo108\.claude\.credentials.json` and `Administrator\.claude\.credentials.json` with only `oauthAccount` merged into each `.claude.json`. `claude -p … --model opus` → **AUTH-OK** verified from Administrator's profile (Jivo108's copy is byte-identical but unverified — no interactive login available over SSH). ⚠️ In PowerShell `$home` is a read-only automatic variable — a per-user loop must use another name or it throws `VariableNotWritable` and silently provisions nobody. **The Claude *desktop app* is NOT on this box** (checked machine-wide, both profiles' `AppData\Local\Programs`, and the uninstall registry) — CLI only. |
| `HO-IT-PC2` (Sohail, accounts) | 23016 | `sohail`, `sohail-acc`, `ho-it-pc2` | ✅ live 2026-08-22 18:02, `ssh sohail` shell verified from the Mac. Registered from `122.180.240.216` (the same non-office egress as Lovepreet's box) and **SAP `138.252.101.222:50000` is open from it**. MSI desktop (MS-7D22), Win 11 Pro, 15.9 GB. ⚠️ **Do not read a silent banner as a fault on a fresh enrolment.** `register-with-vps` runs *before* `openssh-server` in the v9 step order, so between `OK host=HO-IT-PC2` at 12:32:41Z and sshd actually listening at ~12:36Z the port looked exactly like `tunnel-up-but-sshd-silent`: listener bound on the VPS, byte-stream probe EMPTY, no VERIFY line yet. Nothing was wrong — OpenSSH was still installing (Windows Update abandoned at 150 s, then the MSI route took it, OpenSSH 10.0 preview). The installer's own `verify-reachable` logged `VERIFY … OK banner=OpenSSH_for_Windows_10.0` at 12:36:21Z. **Re-probe for ~5 min before climbing the sshd ladder on a box that has only just registered.** ⚠️ **Two profiles, same trap as `HO-IPEXP-PC2`:** SSH lands as `Administrator`, but the human's profile is `C:\Users\SOHAIL` (the box also carries `devel`, `Jyoti`, `bACKUP`, `WsiAccount`) — any kit belongs under **`C:\Users\SOHAIL\Documents`**, and an npm global must use a machine-wide prefix. **No kit yet:** no `jivo-cli` clone, no `sapb1`, no Claude Code. Git 2.x and Node are already present; `python` resolves only to `devel`'s Python 3.12 and `python3` is the Microsoft Store stub, so real Python must be installed before `harness.py` will run. |
| harsh, kanhaiya, neelesh | — | — | not yet onboarded; send them the installer |

`JIVO-B1` sits inside the office network, so `Mac → VPS → JIVO-B1 → SAP` works from
anywhere. Verified: the SAP Service Layer answered **HTTP 401** through that chain — a
response, so reachable; it just wants credentials. That is a second, independent route to
SAP alongside [`../reverse-tunnel/`](../reverse-tunnel/README.md).

```sh
# SAP Service Layer from home, through Diljeet's box
ssh -f -N -L 15055:138.252.101.222:50000 diljeet
(cd sap-b1/cli && set -a && source .env && set +a && SAPB1_HOST=localhost SAPB1_PORT=15055 ./sapb1 doctor)
```

Linked: [[../reverse-tunnel/README]] · [[../SAP-HOME-ACCESS]] · [[ADD-SSH-FORWARD]] · [[../../NEW-DEVICE]]
