---
title: "jwa — WhatsApp, read-only, into the toolkit"
created: 2026-08-27
project: jivo-cli
type: readme
tags: [whatsapp, whatsmeow, read-only, accounts, bills, vps]
---

# `jwa` — the WhatsApp reader

Links to a WhatsApp number as a **companion device** — the same mechanism as
WhatsApp Web — archives what arrives, and lets Accounts pull a vendor's bill out
without anybody scrolling a phone. Built on
[whatsmeow](https://github.com/tulir/whatsmeow), chosen over Baileys on
2026-08-27 for being the sturdier of the two for something that must stay linked
for months.

**It never sends.** No replies, no read receipts, no "typing…", no joining or
leaving groups. That is enforced by a test that walks the syntax tree and fails
the build if a send verb appears anywhere in the module — same tripwire pattern
as `mail-cli`'s IMAP guard and the SAP MCP server's.

## Commands

```
jwa login                     link the number (QR, once, needs a human)
jwa run                       stay linked and archive          (the daemon)
jwa doctor                    linked? how much is archived?
jwa chats  [--limit N]        conversations, most recent first
jwa search [--chat X] [--from X] [--text X] [--since 30d] [--media]
jwa bills  [--since 30d]      only messages carrying a PDF or an image
jwa pull   <message-id> [--to DIR]
```

Everything lives under `~/.jwa` — `session.db` (the device keys),
`archive.db` (the messages), `media/YYYY-MM-DD/` (the files).
Override with `JWA_HOME`.

## Install on the VPS

```sh
scp -r whatsapp-cli vps:~/
ssh vps 'bash ~/whatsapp-cli/deploy/install-vps.sh'
ssh -t vps '~/go/bin/jwa login'        # scan the QR from the phone
ssh vps 'systemctl --user start jwa'
```

`sudo loginctl enable-linger $USER` on the VPS, once, or the service stops when
you log out — that failure looks exactly like "WhatsApp keeps unlinking itself".

## Three things to know before you rely on it

1. **It only sees WhatsApp from the moment it is linked.** Linking pulls a
   short slice of recent history — whatever the phone chooses to send, typically
   days, not years. **It is not a way to read the last two years of chats.** The
   archive gets useful by running, from the day it starts.
2. **The number can be banned.** Companion-device libraries are not sanctioned
   by Meta. It is uncommon, not unheard of. **Use a spare number, never the
   main one** — that was the decision on 2026-08-27.
3. **`~/.jwa/session.db` is as good as the account.** Anyone holding it is that
   linked device. It is 0700, the service runs unprivileged, and it must never
   be committed — this repo is public.

## Staying linked

"It keeps logging out" has three causes, and only one of them is WhatsApp.

1. **The phone went dark.** WhatsApp unlinks every companion when the primary
   phone has been off the network for 14 days. Nothing on the VPS can help;
   the SIM has to sit in a phone that stays charged and on data.
2. **The daemon stopped and nobody noticed.** `jwa run` is a user service with
   `Restart=always` and lingering on, so a crash or a reboot brings it back.
   It also writes two files under `~/.jwa`: `state` (connected, disconnected,
   or a fatal verdict — `logged_out`, `replaced`, `banned`, `outdated`,
   `unlinked`) and `heartbeat`, rewritten every minute while the socket is up.
   `jwa doctor` prints the verdict on its `daemon` line. On a fatal event the
   daemon exits non-zero (after waiting out a ban) so systemd shows it.
3. **Nobody was told.** `deploy/jwa-health.sh` runs from cron every 10 minutes,
   reads those two files and systemd — never `session.db` — and messages the
   Telegram channel once when the link goes down and once when it is back.
   `install-vps.sh` installs the cron line.

The session store opens with WAL and a 10 s busy timeout: whatsmeow writes
keys from several goroutines and `doctor` opens the same file, and without
those the log filled with `SQLITE_BUSY` on the first evening.

## Status, 2026-09-02

Linked on the VPS to a spare number bought for the purpose and archiving as a
`systemd --user` service (root, lingering) with the health cron installed.
The 2026-08-27 notes below describe the state before that.

## Status, 2026-08-27

Written on the Mac Air, **not yet compiled** — that box has no Go toolchain.
The first `go mod tidy && go build` on the VPS is what settles the code against
whatsmeow's current API; expect to fix a signature or two, as that library
renames things between releases. The guard test runs before the build in
`install-vps.sh` on purpose.
