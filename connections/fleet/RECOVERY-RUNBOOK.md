---
title: Fleet recovery runbook — a box is unreachable, now what
created: 2026-08-17
project: jivo-cli
type: runbook
tags: [fleet, ssh, reverse-tunnel, recovery, tailscale, windows, macos]
---

# Fleet recovery runbook

[`README.md`](README.md) explains how the tunnels are *built*. This is what to do when
one is **broken** — which channel to try, in what order, and what to say to the person
sitting at the keyboard when no channel is left.

Two audiences, two halves:

- **[Part 1](#part-1--fixing-it-yourself)** — you, or an agent in a future session.
- **[Part 2](#part-2--messages-to-send-a-colleague)** — the colleague at the keyboard,
  who should never have to read Part 1.

> Measured live on **2026-08-17**, 19:10 and again 21:15 IST. Facts about *who is down*
> go stale in hours — and the two readings already disagree, which is itself the most
> useful thing in this file (see [the day/night trap](#the-daynight-trap--the-same-box-reads-unreachable-at-1900-and-down-at-2100)).
> The traps, the channels and the two root causes do not go stale.

---

## Part 1 — fixing it yourself

### The three states, and the one that lies to you

`/root/bin/fleet-tunnel-health.sh` reports exactly three, and the difference between
them is the whole diagnosis:

| State | What is true | What it means |
|---|---|---|
| **UP** | port listens on the VPS **and** something answered with an `SSH-` banner | reachable, nothing to do |
| **DOWN** | nothing listening on the VPS | the box is **off**, or its dialer task is dead |
| **UNREACHABLE** | port listens, **nothing answers on the box's port 22** | the box is **on and dialling**, but sshd on it is dead |

⚠️ **UNREACHABLE is the state that passes every naive check.** The box is registered in
`~/fleet-tunnels.txt`, `ss -ltn` shows `127.0.0.1:230xx` listening, the monitor said UP
for hours — and `ssh <box>-vps` still dies with
`kex_exchange_identification: Connection closed by remote host`. The tunnel forwards to
`localhost:22` on the box, so a **stopped sshd looks byte-for-byte like a healthy
tunnel** from the VPS side. Three boxes sat in this state for 4+ days.

**Never conclude "it's up" from a listening port.** The only honest test is the banner:

```sh
# the one probe that distinguishes UP from UNREACHABLE (this is what the monitor does)
ssh vps 'exec 3<>/dev/tcp/127.0.0.1/23011; read -t 5 -r l <&3; echo "$l"'
#   SSH-2.0-OpenSSH_for_Windows_9.5   -> genuinely UP
#   (empty / hangs / connection reset) -> UNREACHABLE, sshd is dead on the box
```

Deliberately bash's own `/dev/tcp`, **not `nc`** — `nc` inherits stdin and, inside the
monitor's `while read` loop over the registry, swallows the rest of the file (measured:
12 hosts in, 2 hosts out).

### The day/night trap — the same box reads UNREACHABLE at 19:00 and DOWN at 21:00

⚠️ **This is new, it is not in the monitor, and it will mislead you at night.**

`JIVO` (23008) and `JIVO201` (23010) read **UNREACHABLE** at 19:10 and **DOWN** at 21:14
on the same evening, with an unchanged `since 08-13 14:06`. Nothing was repaired. The
colleagues went home and switched their PCs off, so the dialer stopped and the VPS
listener disappeared — an sshd-dead box **decays into a box-is-off box** the moment the
power goes.

That matters because the two states route to opposite actions:

- **DOWN in the evening** is the benign case. The documented advice is *do nothing*.
- **UNREACHABLE** is never benign — it is a fault that needs a human or a reinstall.

So a night-time reading files a genuinely broken PC under "switched off for the day", and
the correct response to that filing is to wait. That is precisely how three boxes bought
themselves four more days.

**Rule: classify during office hours (10:00–19:00 IST).** If you must look at night, read
the `since` timestamp, not the state — a `since` that is days old with a DOWN beside it is
a box that has been broken through several working days, not one that went home at six.

```sh
# what the box looked like while it was actually switched on
ssh vps 'grep -E "JIVO|23008|23010" /root/fleet-tunnel-status.txt'
ssh vps 'tail -50 /root/fleet-tunnel-health.log'      # the state history, not just now
```

### Decision table — box is broken, what do I do

Work **down** the channel column. Stop at the first one that answers.

| State | Channel 1 | Channel 2 | Channel 3 |
|---|---|---|---|
| **UP** but you still can't work | reconnect: `ssh <box>-vps 'hostname'` | — | — |
| **UNREACHABLE** | **Tailscale**, if that box is a peer with `22=OPEN` | — *(no other remote path exists — the reverse tunnel **is** the dead thing)* | **a human at the keyboard** → [Part 2](#part-2--messages-to-send-a-colleague) |
| **DOWN**, box online elsewhere (Tailscale peer, tasks disabled) | **Tailscale** → re-enable the tasks | reverse tunnel, if it redials on its own | a human |
| **DOWN**, box offline everywhere | — | — | a human: switch the PC on |
| **DOWN** < ~2 h, evening/night, recent `since` | **do nothing** — office PCs are switched off nightly, this is the benign case | | |
| **DOWN** at night with a `since` **days** old | ⚠️ **not** the benign case — treat as UNREACHABLE and re-read in the morning | | |

#### Channel 1 — the reverse tunnel (only works when the state is UP)

```sh
ssh vps 'cat /root/fleet-tunnel-status.txt'          # last computed state, all boxes
ssh vps '/root/bin/fleet-tunnel-health.sh report'    # recompute now, never alerts
ssh <box>-vps 'hostname'                             # aliases live in the Mac's ~/.ssh/config
```

#### Channel 2 — Tailscale, the second and fully independent path

**This is the lever, and it is now proven.** Tailscale does not touch the reverse tunnel,
the registrar, or sshd-on-port-22 — so a box whose tunnel plumbing is entirely dead can
still be fixed remotely, *if* it is a Tailscale peer with port 22 open.

**Measured today, before and after:** `HO-IT-PC10` (23007) was **DOWN since 08-13** with
**both** scheduled tasks `Disabled` when checked at 19:10. At 21:15 it answered
`SSH-2.0-OpenSSH_for_Windows_9.5` on 23007, with `JivoRevTunnel` **Running** and
`JivoTunnelWatchdog` **Ready** — six days of outage cleared, and Khushwinder was never
messaged.

Both readings are verified; the repair *between* them was not observed, so who ran it is
inferred, not proven. It is a safe inference: Tailscale (`22=OPEN`) was the only remote
channel open to that box, since the thing needing repair was the tunnel itself. Either
way the point stands — one of the eight broken boxes cost a colleague nothing, and it was
the one box with a second path in.

```sh
ssh vps 'tailscale status'                           # who is a peer, who is online
ssh vps 'ssh khush "hostname; (Get-Service sshd).Status"'
```

Aliases already configured in the **VPS's** `~/.ssh/config`:
`khush` / `khushvinder` / `ho-it-pc10` / `dev` → `100.116.119.38` ·
`victus` / `laptop` / `win` → `100.64.84.24` · `macpro` → reverse tunnel `22022`.

⚠️ **The remote default shell is PowerShell, so `&&` is a parser error.** Use `;`.
The first time this was tried it came back with a PowerShell error about `&&` — which
was misread as a failure when it was in fact **proof the SSH session had established**.

Coverage is thinner than the peer list suggests — re-probed from the VPS **21:15**:

| Tailscale peer | IP | 22 | 445 | 3389 | 5985 | Usable as a repair channel? |
|---|---|---|---|---|---|---|
| `khushvinder-dev-veerji` (**HO-IT-PC10**) | 100.116.119.38 | **OPEN** | OPEN | OPEN | OPEN | ✅ yes — and it worked |
| `victus` | 100.64.84.24 | **OPEN** | OPEN | closed | closed | ✅ yes |
| `desktop-73n6je8` (Ziyaul) | 100.96.50.42 | closed | OPEN | closed | closed | ❌ no shell — human needed |
| `jivo` (Administrator1) | 100.104.229.5 | closed | closed | closed | closed | ❌ human needed |
| `harsh-veerji` | 100.118.57.28 | closed | OPEN | closed | closed | ❌ — and not a tunnel box at all |
| `kanhaiya-veerji` | 100.69.239.40 | offline at 21:15 | | | | ❌ |
| **JIVO201** (Avtar) | — | — | — | — | — | ❌ **not a Tailscale peer at all** |

Port **445 open with 22 closed is not a channel** — it is a file share, and this runbook
does not touch anything but the SSH/tunnel plumbing. Do not go looking for a way to use it.

**A LAN hop is not an option either — checked, not assumed.** From VICTUS (which is up
and on the office network), `Test-NetConnection` to `JIVO201`, `JIVO-B1` and `JIVO202`
does not even resolve, and `JIVO` / `DESKTOP-73N6JE8` resolve **only to their Tailscale
IPs** with port 22 closed. There is no third way in. When both channels are out, the
answer is genuinely a person.

#### Fixing an UNREACHABLE box, once you have a shell on it

**First choice (any box that has run v8 or later):** as Administrator,
`powershell -File C:\ProgramData\jivo-revtun\sshd-repair.ps1` — the same ladder the installer and the
15-minute watchdog run. It prints what it finds (service account/exe, who holds port 22, host keys,
`sshd -t`, the last OpenSSH and Service Control Manager events) and then fixes, in order: stray or
wedged `sshd.exe`, service registration, host keys + ACLs, `sshd_config`, the firewall rule, and
finally reinstalls OpenSSH from the ZIP. Exit 0 means 127.0.0.1:22 answered with an `SSH-` banner;
`-DiagnoseOnly` looks without touching; the trail is in `sshd-repair.log` beside it. If the box
never ran v8, just run `JIVO-VPS-TUNNEL.cmd` (v8+) — it writes the tool and runs it when sshd is dead.

**By hand**, as Administrator, **in this order** — the `ssh-keygen -A` is the step everybody skips:

```powershell
ssh-keygen -A                                 # regenerate missing host keys FIRST
Set-Service sshd -StartupType Automatic       # or it dies again at the next reboot
Start-Service sshd
```

`Start-Service sshd` on a box with **no host keys fails**, and it fails quietly. Starting
before generating is the single most common wasted attempt here. Then prove it from the
box the way the VPS will judge it — the service's own opinion of itself is not evidence:

```powershell
Test-NetConnection 127.0.0.1 -Port 22         # TcpTestSucceeded : True
```

#### Fixing a DOWN box whose tasks were disabled

```powershell
schtasks /Query  /TN JivoRevTunnel      /V /FO LIST | Select-String "Status|Last Result"
schtasks /Query  /TN JivoTunnelWatchdog /V /FO LIST | Select-String "Status|Last Result"
schtasks /Change /TN JivoRevTunnel      /ENABLE
schtasks /Change /TN JivoTunnelWatchdog /ENABLE
schtasks /Run    /TN JivoRevTunnel
```

`Status: Running` on `JivoRevTunnel` is correct and expected — its `ssh` runs forever, so
a *Ready* dialer means no tunnel. The watchdog is the opposite: **Ready** is healthy,
because it is bounded at `PT10M` and exits between runs.

Then confirm from the VPS, not from the box:

```sh
ssh vps '/root/bin/fleet-tunnel-health.sh report'
```

### The two root causes found on 2026-08-17 — do not re-diagnose these

**1. The installer returned early and never started sshd.**
In [`JIVO-VPS-TUNNEL.cmd.tpl`](JIVO-VPS-TUNNEL.cmd.tpl), the `openssh-server` step
`return`ed as soon as OpenSSH was found already installed. Collecting the background
install job *is* conditional; **making sshd run is not** — but the early return sat above
both, so on the `openssh-server(already)` path it skipped
`Set-Service sshd -StartupType Automatic`, `ssh-keygen -A` and `Start-Service sshd`, and
skipped the loud failure that would have reported it. The installer printed **OK** on a
box that was unreachable.

Today's UNREACHABLE set is exactly the set of boxes installed by that version.

**2. The watchdog could not recover a missing host key.**
The `JivoTunnelWatchdog` source generated inside the same template was, in full:

```powershell
if ((Get-Service sshd).Status -ne 'Running') { L 'sshd down - starting'; Start-Service sshd }
```

No `ssh-keygen -A`, no `Set-Service -StartupType Automatic`, no check that anything ended
up listening. On a box with missing host keys that `Start-Service` fails,
`$ErrorActionPreference='SilentlyContinue'` swallows it, and the watchdog logs
`sshd down - starting` every 15 minutes forever while nothing gets better. **This is why
three boxes stayed dead for 4+ days with a healthy watchdog running.**

#### Status of both fixes — read this before you act on the two paragraphs above

| | Fixed in the repo | Committed | Shipped to any box |
|---|---|---|---|
| #1 installer early `return` | ✅ yes — the step now always sets Automatic, runs `ssh-keygen -A` on a failed start, and **throws** if sshd still will not run | ❌ no | ❌ **no** |
| #2 watchdog | ✅ yes — sets Automatic first (via `Win32_Service.StartMode`, because `Get-Service.StartType` is missing on the old PowerShell 5.1 builds this is meant to save), runs `ssh-keygen -A` on a failed start, then proves `127.0.0.1:22` answers and logs the outcome either way | ❌ no | ❌ **no** |

⚠️ **Both fixes exist only in the working tree of this repo.** Not one box is running
them. That is the operative fact for [Part 2](#part-2--messages-to-send-a-colleague):
re-sending the **old** installer to Ziyaul, Administrator1 or Avtar would run, print a
green block, and change nothing. Rebuild before you send —
`connections/fleet/build-tunnel-installer.sh win`.

### The gaps those two exposed — worth knowing before you trust the self-healing

| Gap | Why it matters |
|---|---|
| **Nothing repairs the watchdog.** The watchdog repairs `JivoRevTunnel`; if the *watchdog's own* task is disabled, no on-box component notices | Measured on HO-IT-PC10: **both** tasks `Disabled`, `Last Result 267014` (`0x41306`, task terminated). sshd was Running and Tailscale open the whole time, so the box was perfectly healthy — and its tunnel was down from 08-13 with nobody home to restart it. Cause of the disabling is **unknown** (not determined; could be a person, a Windows update, or task cleanup) |
| **`/root/dev-tunnel-install.sh` will never fix anything.** It exits on line 14, `[ -f /root/.dev-tunnel-installed ] && exit 0` — and that stamp was touched **2026-07-31** | It was written to *enrol* HO-IT-PC10, not to *repair* it, and it declared itself finished the day the box first registered. Cron has fired it every 10 minutes since, as a no-op. Don't wait on it |
| **The generalised replacement is not deployed.** `connections/fleet/fleet-auto-repair.vps.sh` exists in the repo and is intended for `/root/bin/fleet-auto-repair.sh` on a `5-59/10` cron | Verified 21:15: **`/root/bin/` contains no such file** and no cron line references it. Until the main session reviews and installs it, every repair in this runbook is manual |
| An UNREACHABLE box is **never** the benign nightly-shutdown case | It is powered on and dialling. The monitor already treats it separately (`UNREACHABLE_AFTER_MIN`, default 60) — don't relax that back to the 4 h DOWN threshold. But see [the day/night trap](#the-daynight-trap--the-same-box-reads-unreachable-at-1900-and-down-at-2100): after hours it *disguises itself* as one |

### Live snapshot — 2026-08-17 21:15 IST (4 up, 8 down)

State is as of 21:15, when most office PCs are already off. **Daytime state** is the
diagnostically real one — that is the box with power on it.

| Box | Port | Person | 21:15 | Daytime (19:10) | Down since | Channel that works |
|---|---|---|---|---|---|---|
| `VICTUS` | 23001 | Prabh | ✅ UP | UP | — | tunnel + Tailscale |
| `dannys-Mac-Pro` | 23003 | — | ✅ UP | UP | — | tunnel + Tailscale |
| `Damanpreets-MacBook-Air` | 23004 | Daman | ✅ UP | UP | — | tunnel |
| `HO-IT-PC10` | 23007 | Khushwinder | ✅ **UP** | DOWN *(tasks disabled)* | *was 08-13; cleared between 19:10 and 21:15* | ✅ repaired remotely — **do not message him** |
| `DESKTOP-73N6JE8` | 23011 | Ziyaul | ⛔ **UNREACHABLE** | UNREACHABLE | 08-14 11:20 | **human only** |
| `JIVO` | 23008 | Administrator1 | ⚠️ DOWN *(PC off)* | ⛔ **UNREACHABLE** | 08-13 14:06 | **human only** — sshd dead, not "off" |
| `JIVO201` | 23010 | Avtar | ⚠️ DOWN *(PC off)* | ⛔ **UNREACHABLE** | 08-13 14:06 | **human only** — sshd dead, not "off" |
| `JIVO-B1` | 23002 | Ecom team | ⚠️ DOWN | DOWN | 08-11 18:02 | human — **longest outage, 6 days** |
| `JIVO202` | 23006 | Jeet | ⚠️ DOWN | DOWN | 08-13 14:06 | human |
| `Karanpreets-MacBook-Air` | 23012 | Karanpreet | ⚠️ DOWN | DOWN | 08-14 16:30 | human — Mac, see the note in Part 2 |
| `DILPREETSINGH` | 23009 | Dilpreet | ⚠️ DOWN *(19:50)* | UP | 08-17 19:50 | **none needed** — went home, benign |
| `DESKTOP-5VCMOAS` | 23005 | Manav | ⚠️ DOWN *(19:10)* | UP | 08-17 19:10 | **none needed** — went home, benign |

Refresh before acting on any of it:

```sh
ssh vps '/root/bin/fleet-tunnel-health.sh report'
```

---

## Part 2 — messages to send a colleague

Drafts, for the operator to send. Nothing here has been sent.

### ⚠️ Read before you send anything

1. **The sshd-dead boxes (Ziyaul, Administrator1, Avtar) must get the REBUILT
   installer.** The file they already have is the version with root cause #1 — it will
   run, print **OK**, and fix nothing. Build the patched one first
   (`connections/fleet/build-tunnel-installer.sh win`), then send. Sending the old file
   burns the one favour you get to ask a colleague for.
2. **Khushwinder does not need a message.** HO-IT-PC10 was verified UP at 21:15, repaired
   remotely. His message below is a *fallback* only, for if it drops again and the remote
   fix fails.
3. **Send in the morning.** Four of these PCs are switched off right now. A message at
   21:00 about a computer that is off gets read at 10:00 tomorrow with no context.

Each message is two sentences, names the exact file, and says what success looks like.
If a message would need a follow-up question to act on, it is the wrong message.

### Ziyaul — DESKTOP-73N6JE8

> Hi Ziyaul, please double-click the **JIVO-VPS-TUNNEL.cmd** file I've just sent you and
> click **Yes** on the prompt that pops up. It takes about a minute — when it's done a
> green block appears saying **SSHD : Running** and **TUNNEL : UP**; please send me a
> photo of that block.

### Administrator1 — JIVO

> Hi, please double-click the **JIVO-VPS-TUNNEL.cmd** file I've just sent you and click
> **Yes** on the prompt that pops up. It takes about a minute — when it's done a green
> block appears saying **SSHD : Running** and **TUNNEL : UP**; please send me a photo of
> that block.

### Avtar — JIVO201

> Avtar bhai, please double-click the **JIVO-VPS-TUNNEL.cmd** file I've just sent you and
> click **Yes** on the prompt. It takes about a minute — when it's done a green block
> appears saying **SSHD : Running** and **TUNNEL : UP**; send me a photo of that block.

*(Re-running the installer does not touch his `JivoSapTunnel`, so his no-VPN SAP access
is unaffected — worth knowing if he asks, not worth putting in the message.)*

### Khushwinder — HO-IT-PC10 · **fallback only, already fixed remotely**

> Khushwinder ji, please double-click the **JIVO-VPS-TUNNEL.cmd** file I've just sent you
> and click **Yes** on the prompt. When it finishes you'll see a green block saying
> **TUNNEL : UP** — please send me a photo of it.

### ⚠️ JIVO-B1 and JIVO202 are a DIFFERENT failure class — read this first

These two are not offline PCs. **Their keys were deleted off the VPS** on
2026-08-03T12:16:18Z, when the box named `JIVO` registered and the registrar's
`grep -vF " revtun-${host}"` substring-matched `revtun-JIVO-B1` and
`revtun-JIVO202` as well. They have been dialling in and being refused ever
since, and because both are still listed in `fleet-tunnels.txt` the monitor
prints a plain `DOWN` — indistinguishable from a PC that is simply switched off.
(Registrar fixed 2026-08-17; `authorized_keys` has no 23002 or 23006 entry.)

**So "switch the PC on" does nothing for these two.** Powering them on produces a
`publickey` failure at the VPS and the monitor still says DOWN. They must **run
the installer**, which carries the registrar key and re-registers the box — that
is what restores the missing `authorized_keys` line, and each box keeps its
original port (23002 / 23006) because the registrar is idempotent per host.

The key is unrecoverable from any VPS backup — the 2026-08-05 `authorized_keys`
backup already lacks both, and the 07-30 backups predate the fleet. Re-registering
is the only route. **Send the freshly built `.cmd`; running the old copy already on
the box also works, but only if that file is still there.**

### Ecom team — JIVO-B1

> Hi, please switch on the **JIVO-B1** computer, then double-click the
> **JIVO-VPS-TUNNEL.cmd** file I've just sent and click **Yes** on the prompt. It takes
> about a minute — please send me a photo of the green block it prints at the end.

### Jeet — JIVO202

> Jeet, please switch on the **JIVO202** computer, then double-click the
> **JIVO-VPS-TUNNEL.cmd** file I've just sent and click **Yes** on the prompt. It takes
> about a minute — please send me a photo of the green block it prints at the end.

### Karanpreet — MacBook Air · **this one is genuinely different**

A Mac has no `.cmd` file, no **Yes** prompt and no UAC. His file is
**`JIVO-VPS-TUNNEL-MAC.command`**, it asks for his **Mac login password** in a black
Terminal window, and it must be opened with **right-click → Open** — a plain double-click
on a file that arrived by AirDrop or download gives *"cannot be opened because it is from
an unidentified developer"* and nothing else. Do not send him the Windows wording.

Most likely he needs no file at all: his Air is a battery laptop and a closed lid on
battery drops the tunnel by design, which fits an outage that started 08-14 16:30. Lead
with the charger.

> Karanpreet, please plug the MacBook into its charger, open the lid, and leave it
> plugged in. If it's already plugged in and open, **right-click** the
> **JIVO-VPS-TUNNEL-MAC.command** file I've just sent and choose **Open** (right-click,
> not double-click), type your Mac password when the black window asks, and send me a
> photo of what it prints at the end.

Two sentences, and the right-click clause earns its length: it is the difference between
the file working and him hitting a Gatekeeper wall with no idea what it means.

### Nobody to message

- **DILPREETSINGH (23009)** — down since 19:50 tonight, and it was UP all day.
- **DESKTOP-5VCMOAS (Manav, 23005)** — down since 19:10 tonight, UP all day.

Both are PCs that were switched off for the evening. Messaging on these is how you teach a
team to ignore you.

### After they reply

```sh
ssh vps '/root/bin/fleet-tunnel-health.sh report'    # recompute, no alerts
ssh <box>-vps 'hostname'                             # the real test
```

⚠️ **A photo of the green block is not confirmation.** Root cause #1 was an installer
printing a green block on a dead box, for days. Confirm from the VPS, and confirm you got
a **banner**, not a listening port.

---

Linked: [[README]] · [[../reverse-tunnel/README]] · [[../SAP-HOME-ACCESS]] · [[ADD-SSH-FORWARD]]
