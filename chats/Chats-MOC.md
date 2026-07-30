---
title: Chats — Map of Content
created: 2026-07-24
updated: 2026-07-28
project: jivo-cli
type: moc
tags: [chats, moc]
---

# Chats — Map of Content

Every conversation session, newest first. See [[README]] for the convention.

## Sessions
- [[2026-07-30]] — **From HOME: proved 100% of SAP reachable off-office** via the goal-#96 reverse tunnel — HANA data (29,851 Oil invoices, current) + Service Layer (`sapb1 doctor` green) + the Windows attachment share (full admin, **measured ~306k files / ~105 GB**, pulled a real PDF home). Cleared the DATA(Linux)-vs-FILES(Windows) confusion; consolidated secrets onto `fleet-access.env` (chmod 600). Documented in `connections/SAP-HOME-ACCESS.md` + memory. `vision/` folder created for tomorrow.
- [[2026-07-29]] — Office session: full SSH into `jivo-dbsap` (SLES 15) as `superadmin` (key-based `ssh jivo-sap`); HANA made bulletproof via an SSH `-L` tunnel (immune to the 30015 firewall); **goal #96 done — IP-independent access via a reverse SSH tunnel through the fleet VPS** (`ssh jivo-sap-any`, only port 22 tunneled, self-healing, verified from a non-whitelisted IP). Chosen over Tailscale (which would've exposed HANA to the tailnet). Root pw + `20.20.45.25` file-server login still outstanding (optional).
- [[2026-07-28]] — SAP back up after the outage → delivered the blocked July Oil turnover (₹26.18 Cr net, 1–28 Jul) → goal #87 attachments: JIVO-APP creds in hand but `jivo` subnet-router node offline (~2h), share unreachable; watcher armed to pull the 2 PDFs on route return.
- [[2026-07-27]] — SAP outage: app-server host itself down (public `.192:50000` dead AND `jivo` tailnet node offline ~1 day; postsql `.76` fine → office edge up). Oil quarterly-turnover ask blocked; IT to check the machine.
- [[2026-07-25]] — SAP attachment PDFs blocked by 3 walls: LAN-locked share (no route from Wi-Fi) + Service Layer missing Linux mount for `AttachmentsFolderPath` + `.192` endpoint itself unreachable from our egress IP (while `.76` postsql answers) → fixes: HANA CIFS mount (root), Tailscale subnet router, stable-IP whitelist, read-only SAP user. Morning-session log (goal #87) stranded on the other laptop.
- [[2026-07-24]] — SAP B1 connected → 498-service vault → grid consolidated into `~/jivo-cli` → postsql added → Blinkit partner portal studied + CLI built → VPS/Hermes transfer planned (not deployed) → this chat journal created.
