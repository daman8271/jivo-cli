# reverse-tunnel — reach SAP's SSH from ANY IP

The SAP/HANA box `jivo-dbsap` (`138.252.101.222`) only accepts SSH from whitelisted
public IPs, and it fail2bans anything that guesses wrong. That means the moment we
leave the office network — VPN on, hotel wifi, phone tether, a fleet box — `ssh
jivo-sap` dies and every Accounts tool that rides port 22 (the HANA tunnel included)
dies with it.

This folder pins open a **reverse tunnel**: the box dials *out* to our fleet VPS and
parks a listener there. Outbound is never whitelist-checked, so from then on we come
in through the VPS from wherever we are.

```
   Mac (any IP, VPN on or off)
        |
        |  ssh jivo-sap-any        <- one alias, nothing else to remember
        v
   ProxyJump vps-pub  ------->  FLEET VPS  187.127.129.132  (root, today)
                                    |
                                    |  127.0.0.1:47192   <- loopback ONLY
                                    |  (opened by the box, not by us)
                                    ^
                                    |  reverse tunnel, dialed by the box every
                                    |  minute from cron under flock:
                                    |  ssh -R 127.0.0.1:47192:localhost:22
                                    |
                            jivo-dbsap  138.252.101.222
                            sshd on localhost:22
                            (public-IP whitelist bypassed — the box dialled OUT)
```

Both hops are ordinary SSH. Nothing is installed on either machine beyond one shell
script and two crontab lines on the box, plus one line in the VPS's `authorized_keys`.

## Connect

Add `ssh-config-block.txt` to `~/.ssh/config` on the Mac, then:

```sh
ssh jivo-sap-any                 # shell on the box, from anywhere
ssh jivo-sap-any 'hostname'      # -> jivo-dbsap
```

HANA still rides the same session, so the read-only SQL path keeps working off-office:

```sh
ssh -f -N -L 13015:127.0.0.1:30015 jivo-sap-any
hana-sql -env connections/hana-tunnel.env "SELECT 1 FROM DUMMY"
```

`ssh jivo-sap` (direct, office IP) still works and is faster — use it when you're on a
whitelisted IP. `jivo-sap-any` is the fallback that always works.

## Install

| Where | What |
|---|---|
| Box (`superadmin`) | copy `dial.sh` + `install-box.sh`, run `sh install-box.sh` |
| VPS (`root`) | append one restricted line — see **`vps-authorize.md`** |
| Mac | paste `ssh-config-block.txt` into `~/.ssh/config` |

```sh
scp connections/reverse-tunnel/dial.sh \
    connections/reverse-tunnel/install-box.sh jivo-sap:~/
ssh jivo-sap 'sh ~/install-box.sh'          # prints the public key to authorize
```

The installer is idempotent — re-run it any time. It never overwrites the key,
de-dupes its own crontab lines, and **backs up the crontab before touching it**
(`~/revtun/crontab.bak`), aborting rather than rebuilding from a failed `crontab -l`.

## How it self-heals — a flock-guarded cron dial

We have **no root** on the box (SUSE `Defaults targetpw`), so there's no systemd unit
and no supervisor. Earlier this was a backgrounded keeper loop (`box-revtun.sh`); an
adversarial review retired that in favour of something simpler and reboot-robust:

1. **`dial.sh`, fired by cron every minute** (`* * * * *`) and `@reboot`. Each run does
   `flock -n "$HOME/revtun/.lock"` then `exec ssh -N -T … -R 127.0.0.1:47192:localhost:22`.
2. **`flock -n` is the whole supervisor.** While the tunnel is up the lock is held, so
   every later minute's cron run is an instant no-op — there is never more than one
   ssh, and no pile-up.
3. **The ssh runs in the cron job's FOREGROUND** (via `exec`), so its logind session
   stays alive for exactly as long as the tunnel is up. That sidesteps the
   `KillUserProcesses` race that bites backgrounded/nohup'd processes on logout.
4. **Recovery is ≤60s.** When the link drops, the lock frees and the next cron tick
   re-dials. Measured ~42s end-to-end. `ServerAliveInterval=30` / `…CountMax=3` makes a
   hung link surface in ~90s; `ExitOnForwardFailure=yes` means a session that couldn't
   grab port 47192 exits immediately instead of sitting there useless;
   `ConnectTimeout=15` keeps a dial from wedging a whole minute.

No keeper, no pidfiles, no orphan-reaping — the earlier design needed all three; the
flock-cron design needs none. `dial.sh` also caps its own log at 1MB before each dial.

Operate / observe it:

```sh
ssh jivo-sap 'crontab -l | grep dial.sh'       # both lines present?
ssh jivo-sap 'tail -f ~/revtun/revtun.log'     # live dial log
ssh jivo-sap 'pgrep -fa 47192'                 # is an ssh holding the tunnel?
ssh vps-pub  'ss -ltn | grep 47192'            # VPS side: listener present?
```

`box-revtun.sh` is kept in this folder as **superseded, manual-only** tooling
(`start`/`stop`/`status` by hand). It is **not** installed into cron and must not run
alongside `dial.sh` — both would fight over VPS port 47192.

## Security notes

- **Loopback-only listener.** The tunnel binds `127.0.0.1:47192` *on the VPS*. It is
  not on any public interface — you must already be inside the VPS (hold a fleet key)
  to touch it. `GatewayPorts` stays at its default `no`.
- **Only port 22 is tunneled.** `-R …:localhost:22` forwards SSH and nothing else.
  HANA (`30015`) and the SAP Service Layer (`50000`) are **not** exposed by this — they
  remain local to the box, reachable only by tunnelling *inside* an authenticated SSH
  session, exactly as before.
- **Restricted key on the VPS — and the intuition is wrong, so read carefully.** The
  line is `restrict,port-forwarding,permitlisten="127.0.0.1:47192",permitopen="127.0.0.1:1"`.
  `restrict` turns everything off; `port-forwarding` then re-enables port forwarding in
  **BOTH** directions (`-R` and `-L`). `permitlisten` constrains **only** the `-R`
  side. On its own that would still allow arbitrary `-L` local forwards from the VPS
  into anything the VPS can reach — so `permitopen="127.0.0.1:1"` is added to pin `-L`
  to a dead host:port, which is what actually **blocks `-L`**. Net: the key can open
  exactly one thing, the loopback listener `127.0.0.1:47192`, and nothing else either
  way. Full detail in `vps-authorize.md`.
- **The key authenticates as VPS `root` today.** That's heavier than ideal; the
  restrictions above neuter it, but a dedicated unprivileged VPS user (no shell) is the
  recommended follow-up — see "Known limitations / deferred".
- **The private key `jivo_revtun` lives ONLY on the box** (`~superadmin/.ssh/jivo_revtun`,
  mode 600). It is generated *on the box* by `install-box.sh` and is **never** copied to
  the Mac and **never** committed to this repo. Nothing in this folder contains key
  material — only the public half is ever handled, and only by pasting it into the VPS's
  `authorized_keys`. If you ever find a private key inside `jivo-cli/`, that's an
  incident: rotate it.
- **Still read-only.** This changes *reachability*, not permissions. CLAUDE.md Rule 0
  is unaffected — SAP is read-only, always.
- **Auth on the inner hop is unchanged.** Reaching the box still requires
  `~/.ssh/jivo_accounts_box`; the tunnel does not weaken the box's own login.

## Known limitations / deferred

- **(a) Stale VPS listener after an abrupt box death.** If the box vanishes hard
  (power/network yanked, not a clean ssh exit), the VPS can keep the dead
  `127.0.0.1:47192` listener for up to ~2h — the box's `ServerAliveInterval` can't fire
  from a box that's gone, so only the VPS's own TCP keepalive eventually reaps it. Until
  then the next box dial bounces off `ExitOnForwardFailure`. Fix (needs VPS root, which
  we have): add `ClientAliveInterval`/`ClientAliveCountMax` on the VPS sshd scoped to
  this key/user via a `Match` block, **or** a small VPS cron that reaps a `127.0.0.1:47192`
  listener that has no ESTABLISHED peer. Force-clear by hand meanwhile:
  `ssh vps-pub 'fuser -k 47192/tcp'`.
- **(b) The tunnel path bypasses the box's own perimeter.** Connections arriving through
  the reverse tunnel look like `127.0.0.1` to the box, so they sidestep the box's
  fail2ban and its public-IP whitelist, and **password auth is still enabled on the
  box**. That means the tunnel is only as safe as the VPS's own access control. Properly
  fixing it (disable box password auth, or key-only for the tunneled path) needs **box
  root, which we do not have** (`Defaults targetpw`). Mitigation for now lives entirely
  on the VPS side: guard the fleet key, keep the listener loopback-only.
- **(c) `jivo-sap-any` is pinned to `vps-pub`.** The `vps` multipath route currently
  needs a Tailscale re-auth, so the ssh-config uses `ProxyJump vps-pub` (public-IPv4
  route) rather than `ProxyJump vps`. Switch it back to `vps` once the Tailscale re-auth
  is done — nothing else changes.

## Undo

`teardown.sh` (run on the box) kills the dialer + its ssh, removes both crontab lines,
deletes `$HOME/revtun` (incl the flock `.lock`), the key pair, and the scp'd leftovers
in `$HOME` — then prints the remaining manual steps (VPS `authorized_keys` line + its
`.bak`, Mac config block) and how to verify VPS 47192 is gone.

```sh
scp connections/reverse-tunnel/teardown.sh jivo-sap:~/
ssh jivo-sap 'sh ~/teardown.sh --dry-run'    # preview
ssh jivo-sap 'sh ~/teardown.sh'
```

## Files

| File | Purpose |
|---|---|
| `dial.sh` | **the runtime** — flock-guarded cron dialer, runs on the box |
| `install-box.sh` | idempotent installer (dir, key, dial.sh, both cron lines, kick) |
| `box-revtun.sh` | SUPERSEDED keeper — kept as manual `start`/`stop`/`status` tooling |
| `vps-authorize.md` | the exact restricted `authorized_keys` line + verification |
| `ssh-config-block.txt` | the `Host jivo-sap-any` block for the Mac |
| `teardown.sh` | full reversal, box side + instructions for VPS/Mac |
