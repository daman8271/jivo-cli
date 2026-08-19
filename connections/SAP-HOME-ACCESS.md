---
title: SAP from home — full access runbook (data + attachments)
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: runbook
tags: [sap, hana, attachments, home-access, reverse-tunnel, read-only]
---

# SAP from home — how we reach ALL of it, off-office

> **TL;DR** — From any network (home, tether, hotel), with **zero office VPN**, we have:
> - **SAP HANA data** — 100%, live, all 3 companies (the actual books).
> - **SAP attachment files** — full admin, ~306k files / ~105 GB of scanned docs.
> - **The SAP Windows app-server** — total control (all drives).
>
> - **SAP from the phone**, always-on, nothing running on the Mac — see **§8b**.
>
> Everything rides reverse SSH tunnels the SAP box holds out to our fleet VPS
> (goal #96). Nothing here writes — CLAUDE.md **Rule 0 (read-only)** is unaffected.
> Last verified end-to-end from a **non-whitelisted home IP on 2026-07-30 ~14:40 IST.**

## 1 · The mental model (this is what confuses everyone)

There are **two different machines**, and two different kinds of "SAP":

| | The **data** | The **files** |
|---|---|---|
| What | Every number/record — invoices, ledgers, balances, orders, journals, stock. **This IS SAP.** | Scanned *images* of paper docs (a photo/PDF clipped to an entry). Not in the DB — just files SAP points at. |
| Box | **Linux** `jivo-dbsap` — `138.252.101.222` (internal `20.20.45.192`) | **Windows** `JIVO-APP` — `20.20.45.25` (Tailscale `100.104.229.5`) |
| Runs | HANA DB (`30015`) + SAP B1 Service Layer (`50000`) | SMB file shares (`445`) + RDP |
| Login | **data** logins — `hana.env` (ZIA) / `sapb1` (manager) | **OS** login — `fleet-access.env` (`JIVOAPP_SMB_*`). **Different credential.** |

Analogy: the Linux box is the **filing cabinet** (all the numbers). The Windows box
is the **photocopy room** (scanned images of the paper bills). Day-to-day "using SAP"
= reading the filing cabinet. You only touch the photocopy room to see a scanned bill.

**HANA does NOT run on the Windows box** — every DB port there is closed. So SSH'ing
the Windows box gives you *no data*; the data is all on the Linux box, which we own
fully. The Windows box only adds the scanned files.

## 2 · Why it needs a tunnel, and the one that fixes it

The Linux box only accepts SSH/HANA/Service-Layer from **whitelisted office IPs**, and
fail2bans wrong guesses. Leave the office → direct connections die. So the box **dials
OUT** to our fleet VPS and parks a listener; outbound is never whitelist-checked. We
then come in through the VPS from anywhere.

```
Mac (any IP)  --ssh jivo-sap-any-->  vps-pub (187.127.129.132)
                                       └─ 127.0.0.1:47192  (loopback listener)
                                            ▲  reverse tunnel dialed by the box
                                            └─ jivo-dbsap sshd :22  (whitelist bypassed)
```

Only **port 22** is tunneled; HANA/Service-Layer are reached by forwarding *inside* an
authenticated SSH session. Self-healing (flock-guarded cron dial, ≤60s recovery). Full
design, install, teardown, security notes: [`reverse-tunnel/README.md`](reverse-tunnel/README.md).

- `ssh jivo-sap-any` — works from **any** IP (the fallback that always works).
- `ssh jivo-sap` — direct, office-whitelisted IP only (faster when you're in office).

## 3 · Credentials — where everything lives (all gitignored, `chmod 600`)

| File | Holds | For |
|---|---|---|
| `connections/fleet-access.env` | `SAPLINUX_*` (Linux SSH), `JIVOAPP_*` (Windows SMB `ADMIN` + `JIVOAPP_RDP`), `SAPSRV_*`, `REVTUN_*`, `TS_*` | box OS + Windows files |
| `connections/hana.env` | `HANA_*` (user `ZIA`) — points at the box directly | HANA over office IP |
| `connections/hana-tunnel.env` | `HANA_*` — points at **localhost:13015** (the tunnel) | HANA from home |
| `sap-b1/cli/.env` | `SAPB1_*` (user `manager`) | Service Layer / `sapb1` CLI |

⚠️ **Never commit these** (they're `*.env`, already ignored) and **never print the
passwords**. Docs reference the *file*, not the value.

## 4 · Route A — HANA raw SQL from home (the fast path for Accounts)

```sh
# 1) open the HANA tunnel over the reverse route (idempotent; fails loud if 13015 taken)
ssh -f -N -o ExitOnForwardFailure=yes -L 13015:127.0.0.1:30015 jivo-sap-any

# 2) query — real SUM/GROUP BY/JOIN, all 3 schemas
./hana-sql/hana-sql -env connections/hana-tunnel.env \
  "SELECT COUNT(*) FROM \"JIVO_OIL_HANADB\".OINV WHERE \"CANCELED\"='N'"
```
Schemas: `JIVO_OIL_HANADB`, `JIVO_MART_HANADB`, `JIVO_BEVERAGES_HANADB`. Gotcha:
go-hdb returns DECIMAL sums as fractions — wrap in `ROUND(TO_DOUBLE(SUM(...)),0)`.
See [[sap-hana-direct-sql]] for query conventions (turnover, cost dimensions, etc.).

## 5 · Route B — SAP B1 Service Layer / `sapb1` CLI from home

```sh
# 1) forward the Service Layer port
ssh -f -N -o ExitOnForwardFailure=yes -L 15000:127.0.0.1:50000 jivo-sap-any

# 2) point the CLI at the tunnel (override host/port; creds come from sap-b1/cli/.env)
cd sap-b1/cli && set -a && source .env && set +a
SAPB1_HOST=localhost SAPB1_PORT=15000 ./sapb1 doctor        # -> "All checks passed"
SAPB1_HOST=localhost SAPB1_PORT=15000 ./sapb1 query BusinessPartners --company JIVO_OIL_HANADB --top 1
```
Use HANA (Route A) for aggregation; Service Layer has no server-side SUM.

## 6 · Route C — Windows attachment files over SMB

`smbclient` lives **on the Linux box**, which reaches `20.20.45.25:445` on the office
LAN — so the simplest path runs smbclient there and feeds the password through SSH's
encrypted **stdin** (never on a command line). Shares:
`Attachments_Oil` · `Attachments_Mart` · `Attachments_Bev` · `OMS_Attachments` ·
`"Jivo Oil"/"Jivo Mart"/"Jivo Beverages"` (B1_SHR) · `C$/D$/E$` (full admin).

```sh
set -a; source connections/fleet-access.env; set +a          # loads JIVOAPP_SMB_USER/PASS

# list a share
printf '%s\n' "$JIVOAPP_SMB_PASS" | ssh jivo-sap-any \
  "smbclient '//20.20.45.25/Attachments_Oil' -U $JIVOAPP_SMB_USER -c 'cd JIVO_OIL; ls'"

# fetch a file (lands on the box, then scp home)
printf '%s\n' "$JIVOAPP_SMB_PASS" | ssh jivo-sap-any \
  "smbclient '//20.20.45.25/Attachments_Oil' -U $JIVOAPP_SMB_USER -c 'cd JIVO_OIL; get \"TAN.pdf\" /tmp/x.pdf'"
scp jivo-sap-any:/tmp/x.pdf ./ ; ssh jivo-sap-any 'rm -f /tmp/x.pdf'
```
For bulk work, forward SMB to the Mac instead: `ssh -f -N -L 1445:20.20.45.25:445
jivo-sap-any` (then use a local SMB client against `//localhost:1445`). For many files,
`smbclient -A <authfile>` (mode 600) avoids re-entering the password per share.

**Alt route (no tunnel):** the Windows box also exposes **public RDP** at
`JIVOAPP_RDP` (`103.89.45.25:13579`) — a direct graphical login from home if ever needed.

## 7 · What's actually there (measured 2026-07-30)

| Share | Files | Size |
|---|---:|---:|
| Attachments_Oil | 180,693 | 65.2 GB |
| Attachments_Mart | 75,487 | 16.1 GB |
| Attachments_Bev | 49,908 | 23.3 GB |
| OMS_Attachments | 0 | (empty / different layout — recheck) |
| **Total** | **~306,000** | **~104.6 GB** |

More files than the SAP registry (ATC1 ≈ 202k) because the folders also hold generated
`WordDocs`/`XMLDocs`, screenshots, and loose drops. Live books (HANA) ≈ **4.6 GB**
(Oil 3.11 / Mart 0.78 / Bev 0.68); see [[sap-data-sizing-and-mirror]].

## 8 · What does NOT work from home (by design)

Direct connections to the box's public IP — `138.252.101.222:22`, `:30015`, `:50000` —
**time out** from any non-office IP (the whitelist). That's expected; we go *around* it
via the reverse tunnel (§2). Do not retry auth against `.192` directly — fail2ban bans
your whole IP across all ports.

## 8b · Route D — SAP from the PHONE, always-on (no laptop, no tunnel command)

Routes A–C need a shell. Since **2026-07-30** the always-on path exists: the
fleet VPS holds the SAP ports open permanently, so the **MCP gateway** answers SAP
questions from claude.ai / the phone with nothing running on the Mac.

```
phone → claude.ai → https://jivo-mcp.<vps-host>/<secret>/jivo/mcp   (75 tools)
   → gateway container → sapb1 container
   → 127.0.0.1:50000  (sapb1-sl-proxy sidecar, shares sapb1's netns)
   → 172.16.1.1:50000 (sap-bridge socat, host netns)
   → 127.0.0.1:47500  (reverse tunnel parked by the box)
   → SAP box :50000
```

Three pieces, all self-healing, none needing the office IP whitelist:

1. **`dial-ports.sh`** on the box (own flock + cron, **deliberately separate from
   `dial.sh`** — see the header comment; merging them would let a port clash kill
   port-22 access). Parks `127.0.0.1:47500` → SL `:50000` and `127.0.0.1:47301` →
   HANA `:30015` on the VPS. Needs the matching `permitlisten=` entries in the VPS
   `authorized_keys` (see `vps-authorize.md`) or ssh exits instantly.
2. **`sap-bridge` / `hana-bridge`** socat containers (host netns) republish those
   loopback ports on the docker bridge gateway `172.16.1.1`, because containers
   cannot reach the host's `127.0.0.1`.
3. **`sapb1-sl-proxy`** sidecar — the non-obvious one. ⚠️ **SAP's Apache 403s any
   request whose `Host` header it doesn't recognise.** Measured 2026-07-30:
   `Host: 127.0.0.1:*`, `localhost:*`, `138.252.101.222:*` → **200**;
   `Host: 172.16.1.1:50000` → **403 Forbidden**. The sapb1 client derives `Host`
   from `SAPB1_HOST:SAPB1_PORT`, so it must *dial* a name SAP accepts — hence a
   sidecar in sapb1's own netns listening on `127.0.0.1:50000`. Never "simplify"
   this by pointing `SAPB1_HOST` straight at the bridge IP; it will 403.

Verified end-to-end from a non-whitelisted home IP: `sap_doctor` → `ok:true`, live
`BusinessPartners` rows returned through the public URL. Killing the tunnel
recovered in **50 s** with no container restart. HANA (`30015`) is bridged and
reachable from the MCP network too — ready for a HANA tool, not yet exposed.

Gotcha when changing `env/sapb1/.env` on the VPS: it is a **single-file bind
mount**, so `sed -i` swaps the inode and the container keeps the old values —
`docker compose up -d --force-recreate sapb1 sapb1-sl-proxy`, not `restart`.

## 9 · The real long-run fix (don't stop at the tunnel)

Every route above still depends on the **office WAN being up** (the box + its tunnel
live in the office). The durable fix is the **mirror**: pull HANA → our own Postgres on
the VPS (`sap_oil`/`sap_mart`/`sap_beverages`), nightly, queryable via the existing
`postsql` MCP from anywhere even when the office is dark. Attachments are **phase 2**
(SMB file-sync of the ~105 GB). Direction approved by Daman 2026-07-29. See
[[sap-data-sizing-and-mirror]].

## 10 · Cheat sheet

```sh
# is the box reachable from here right now?
ssh -o ConnectTimeout=15 jivo-sap-any 'hostname; uptime'      # -> jivo-dbsap

# HANA one-liner from home
ssh -f -N -o ExitOnForwardFailure=yes -L 13015:127.0.0.1:30015 jivo-sap-any
./hana-sql/hana-sql -env connections/hana-tunnel.env "SELECT CURRENT_TIMESTAMP FROM DUMMY"

# sapb1 from home
ssh -f -N -o ExitOnForwardFailure=yes -L 15000:127.0.0.1:50000 jivo-sap-any
(cd sap-b1/cli && set -a && source .env && set +a && SAPB1_HOST=localhost SAPB1_PORT=15000 ./sapb1 doctor)

# close tunnels when done
pkill -f '13015:127.0.0.1:30015'; pkill -f '15000:127.0.0.1:50000'
```

---
Linked: [[README]] · [[reverse-tunnel/README]] · [[sap-hana-direct-sql]] · [[sap-data-sizing-and-mirror]] · [[CONNECTIONS_MOC]]
