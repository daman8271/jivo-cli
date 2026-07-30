# VPS side — authorize the box's tunnel key (restricted)

One line to add on the fleet VPS (`187.127.129.132`). This is the **only** change
made on the VPS. Nothing is installed, no service is touched.

The box authenticates with a dedicated key (`~/.ssh/jivo_revtun`, private half stays
on the box forever). **Today that key authenticates as the VPS `root` user** — the
only account with an existing fleet login on this box. That is heavier than it needs
to be: the restrictions below reduce the key to a single loopback listener, but a
dedicated **unprivileged** VPS user for the tunnel (e.g. `revtun`, no shell) is the
recommended follow-up so the key never resolves to `root` at all.

## 1. The line

```
restrict,port-forwarding,permitlisten="127.0.0.1:47192",permitlisten="127.0.0.1:47500",permitlisten="127.0.0.1:47301",permitopen="127.0.0.1:1" ssh-ed25519 AAAA...PASTE_BOX_PUBKEY_HERE... revtun@jivo-dbsap
```

Replace everything from `ssh-ed25519` onward with the **exact** public key that
`install-box.sh` printed on the box (it is one line: type, base64 blob, comment).
Get it again any time with:

```sh
ssh jivo-sap 'cat ~/.ssh/jivo_revtun.pub'
```

### What the options actually do (read this — the intuition is wrong)

| Option | Effect |
|---|---|
| `restrict` | turns **everything** off (pty, agent/X11 forwarding, port forwarding both ways, user-rc, commands) |
| `port-forwarding` | re-enables port forwarding — but **BOTH directions**, `-R` (remote/listen) *and* `-L` (local/open) |
| `permitlisten="127.0.0.1:47192"` | scopes only the `-R` side: the key may open **only these** listeners and no others. 47192 = SSH (dial.sh); **47500 = SAP Service Layer, 47301 = HANA** (dial-ports.sh, added 2026-07-30) — a forward with no matching entry is refused and, under `ExitOnForwardFailure=yes`, kills that whole dial |
| `permitopen="127.0.0.1:1"` | scopes the `-L` side: local forwards may target only `127.0.0.1:1` (a dead port), which in practice **denies useful `-L`** |

The trap: people assume `restrict,port-forwarding,permitlisten=…` locks the key to
just the reverse tunnel. It does not. `port-forwarding` switches **both** forward
directions back on, and `permitlisten` constrains **only** `-R`. Without a
`permitopen`, the key could still set up arbitrary `-L` local forwards from the VPS
into anything the VPS can reach. `permitopen="127.0.0.1:1"` closes that door by
pinning `-L` to a host:port nothing listens on. Net effect of the full line: the key
can open exactly one thing — the loopback listener `127.0.0.1:47192` — and nothing
else in either direction.

Because the listen bind address is `127.0.0.1`, that listener is **loopback-only on
the VPS**; it is unreachable from the internet even if `GatewayPorts` were ever
flipped on. `permitlisten`/`permitopen` need OpenSSH ≥ 7.2 — the VPS (Ubuntu) is well
past that.

## 2. Append it

From the Mac, in one shot (quote carefully — the line contains `"`):

```sh
ssh vps-pub 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys' <<'EOF'
restrict,port-forwarding,permitlisten="127.0.0.1:47192",permitlisten="127.0.0.1:47500",permitlisten="127.0.0.1:47301",permitopen="127.0.0.1:1" ssh-ed25519 AAAA...PASTE_BOX_PUBKEY_HERE... revtun@jivo-dbsap
EOF
ssh vps-pub 'chmod 600 ~/.ssh/authorized_keys'
```

Do **not** use `ssh-copy-id` — it would append the key *unrestricted*, handing the box
a full root shell on the VPS.

## 3. Verify

Just look at the file — no sshd reload, no config change, nothing to restart
(`authorized_keys` is read fresh on every login):

```sh
ssh vps-pub 'tail -n 3 ~/.ssh/authorized_keys'             # our line is last
ssh vps-pub 'grep -c permitlisten ~/.ssh/authorized_keys'  # expect exactly 1
ssh vps-pub 'grep -c permitopen  ~/.ssh/authorized_keys'   # expect exactly 1
```

Then, once `dial.sh` has run on the box (cron fires it every minute), the listener
should appear:

```sh
ssh vps-pub 'ss -ltn | grep 47192'
# LISTEN 0 128 127.0.0.1:47192 0.0.0.0:*
```

End-to-end from the Mac:

```sh
ssh jivo-sap-any 'hostname; whoami'
# jivo-dbsap
# superadmin
```

## Troubleshooting

- **Box log says `Permission denied (publickey)`** → the line isn't in
  `authorized_keys` yet, or the pasted blob got line-wrapped. It must be ONE line.
- **Box log says `remote port forwarding failed for listen port 47192`** → either the
  options line is wrong (typo in `permitlisten`), or a stale `sshd` on the VPS still
  holds the port. Cron re-dials every minute and `flock -n` keeps it from piling up;
  the port clears once the old session is reaped, or force it with
  `ssh vps-pub 'fuser -k 47192/tcp'`.
- **Box log says `administratively prohibited` on an `-L`** → expected: `permitopen`
  is doing its job. Local forwards are intentionally denied.
- **Tunnel goes stale silently** (VPS holds a dead session after an abrupt box death):
  the box already sends `ServerAliveInterval=30`, but that only helps while the box is
  alive. A VPS that never hears the box again can hold the dead `127.0.0.1:47192`
  listener for up to ~2h (TCP keepalive). Belt-and-braces is `ClientAliveInterval 30`
  / `ClientAliveCountMax 3` on the VPS sshd (ideally scoped to this key/user via a
  `Match` block) — it touches shared fleet config, so leave it unless we see stale
  listeners in practice. See README "Known limitations / deferred".

## Removing it

See `teardown.sh` — the VPS step is one `sed` to delete the line (and its `.bak`).
