# Sardar — say "Let's go" from any JIVO machine

**Sardar** is a **live Claude Code session running on JIVO's VPS**, started by
systemd and kept up. Any operator in the office says **"Let's go"** on their own
machine and reaches him. He knows the business, holds the fleet roster, and
grants access. Nobody waits for Daman.

A sardar is the one people go to when they need something settled — which is the
whole job. Daman named him on 2026-08-22.

```
letsgo                                    # it will ask what you need
letsgo "I need to make A/P invoices"
letsgo --status                           # is he up, which sessions are live
letsgo --watch                            # attach and watch him work
```

On Windows: `letsgo.cmd` (same arguments).

---

## Why a real session and not `claude -p`

Daman asked for this specifically, and it is the right call:

| | `claude -p` (headless) | a real session (what this is) |
|---|---|---|
| Memory of the last grant | none | keeps context between summons |
| Can ask a follow-up | no | yes |
| Watchable | no | `letsgo --watch` puts you in his pane |
| Prompt cache | cold every time | warm |

Three sessions live in tmux under systemd (`sardar-1..3`) with a queue and a
per-box lock, so two operators can summon at once without colliding. `claude -p`
survives only as the fallback for a wedged session.

**The pane is for humans, not for the machinery.** The request channel is not
screen-scraped: the receiver writes the summon as a file, types only a 32-char
hex id into tmux, and reads a reply file back. So an operator's free text never
reaches a shell, and the pane stays purely for watching.

---

## The shape of it

```
operator's box            VPS
──────────────            ───────────────────────────────────────────
letsgo  ──HTTPS──▶  traefik ──▶ summond (127.0.0.1:8710)
                                   │  authenticates the DEVICE by token
                                   │  appends to audit.jsonl (fsync'd)
                                   │  writes queue/<id>.json
                                   ▼
                            tmux: sardar-1..3        ← a real claude session
                                   │  reads the queue file
                                   │  calls grantctl (its ONLY way to act)
                                   │  writes replies/<id>.json
                                   ▼
                            grantctl ──ssh──▶ the operator's box
```

| File | What it is |
|---|---|
| `agent/summond.py` | the receiver: auth, rate limit, audit, dispatch |
| `agent/pool.py` | the tmux session pool, and the verified-typing logic |
| `agent/workspace-CLAUDE.md` | Sardar's brief — who he is, what JIVO is, what he may do |
| `bin/grantctl` | the containment boundary and the auto-enroller |
| `grants/*` | one script per grant; `_common.py` holds the shared plumbing |
| `client/letsgo`, `client/letsgo.cmd` | what an operator runs |
| `deploy/install-vps.sh` | idempotent installer for the VPS |
| `deploy/install-client.sh`, `.cmd` | put `letsgo` on a box |
| `agent/policy.example.json` | the roster's shape — **the live one is not in git** |

The service and its paths are still called `jivo-summond` and
`/opt/jivo-summon/` — deliberately. Sardar is the persona operators talk to;
renaming the plumbing underneath would mean migrating tokens, the audit log and
the Traefik route for no gain.

---

## Authorization: the gate is at token-mint time

Daman's decision, stated twice: **when a device asks, give it.** So the agent's
default answer is yes — full SAP draft/write included — and nothing parks for
him.

That is coherent rather than open because the gate moved rather than
disappearing: **only Daman can mint a device token.** `tokens.json` is `0600` on
the VPS and the daemon has no self-enrolment path, so a box holding a valid token
is a box he already trusted. Handing out the token *is* the decision.

**Revoking access means deleting a token**, not arguing with the agent:

```bash
# on the VPS
python3 - <<'EOF'
import json
p = "/opt/jivo-summon/tokens.json"
t = json.load(open(p))
for k, v in t.items():
    if v["device"] == "the-box-to-revoke":
        v["disabled"] = True
json.dump(t, open(p, "w"), indent=2)
EOF
systemctl restart jivo-summond
```

### What still constrains it, and why

None of these are permission gates; they are blast-radius limits that cost
nothing:

- **`grantctl` accepts only catalogued grants.** The agent has judgment about
  *which* grant a box needs, but it cannot run an arbitrary command on a fleet
  box. So a fully prompt-injected agent is confined to a vetted, idempotent
  grant on a known machine.
- **One lock per box**, so two summons cannot provision one machine at once.
- **An fsync'd append-only audit log.** Every request, grant and outcome. This is
  not a gate — it is the record of what a permissive system did.
- **No credential ever moves.** The agent will not create, copy or read out a SAP
  password. Assigning a named SAP user stays a human step, and it says whose.
- **The agent never writes to a business system.** It grants the ability; the
  operator does the writing under their own name, so the audit trail points at a
  person.

---

## Why an operator "cannot write" — in frequency order

This is the useful part, and it is what the grants actually encode. Work down it
before concluding anything about permissions:

1. **They are in a Google-Drive ZIP export, not a git checkout** (`…Z-1-001`).
   Its CLAUDE.md still says read-only and its `sapb1.exe` predates the `draft`
   command, so no permission change reaches them. Most common cause by a wide
   margin. *But the folder name alone does not prove it* — one operator
   git-cloned inside the unzipped export, so the path looks like a zip while git
   works fine. Only a missing `.git` is disqualifying.
2. **Their checkout predates `sapb1 draft`** (commit `6888265`). The command
   genuinely is not in their binary.
3. **Their SAP env points at `103.89.45.192`**, the decommissioned host. That is
   the 502.
4. **Their SAP user is `manager`**, which is read-only at JIVO. Write-capable
   named users in use: `USER01`, `USER06`, `USER36`.
5. **They are not registered as an operator**, so writes would land unnamed.

**Repo policy is deliberately not on that list.** Since commit `a3b9465` the
repo's own RULE 0 allows SAP writes fleet-wide, so a box that has merely pulled
is already write-enabled. If an operator's Claude still refuses, they have not
pulled — a sync problem, not a permission one, and the agent says so instead of
granting something.

---

## Traps this fleet will spring on you

Every one of these cost a debug cycle during the build. They are here so the next
person does not pay again.

**Windows shells.** Most boxes have PowerShell as the sshd default shell. The
only quoting shape that survives bash → ssh → PowerShell → cmd:

```bash
ssh BOX "cmd /c \"<the whole command, paths UNquoted>\""
```

Without the inner quotes PowerShell parses cmd's parentheses itself and you get
`operable program or batch file`. Quote the paths again and you get
`filename, directory name, or volume label syntax is incorrect`.

**cmd writes its errors to stdout.** `dir /b *.env` with no match prints
`File Not Found`; `type <missing>` prints `The system cannot find the file
specified.` Both are non-empty strings, so a truthiness test reads them as
content. That once reported env files present when there were none, and once
reported error text as an operator's slug. `_common.NOT_FOUND_RE` filters them.

**The kit is often not in the SSH login user's profile.** One box logs in as
`Administrator` with an empty profile while everything lives in
`C:\Users\Jivo108`. An empty profile is not "no kit".

**Not every python is python.** Several boxes have Microsoft Store execution-alias
stubs that print "Python was not found" and **exit 0**. A zero exit proves
nothing there — check for real output. This is why the Windows client contains no
python at all.

**A stale 0-byte `.git/index.lock`** silently blocks every git write. It stranded
one operator's commit for two days, twice. The grants clear it.

**`(echo A & echo B) > file` writes a trailing space**, and curl rejects a URL
with one as `Malformed input to a URL function`.

**`tmux send-keys` exits 0 whether or not the application took the keys.** A
fresh workspace opens Claude Code behind a trust dialog that silently swallows
the first request — the first real summon was lost that way with tmux reporting
success throughout. The pool now confirms the text is on the prompt line before
pressing Enter, and the installer pre-accepts the dialog.

**`systemctl enable --now` does not restart a running unit.** A redeploy wrote
new code and left the old process serving it for a whole test cycle. Reading the
file on disk is not proof the change is live — the process has to carry it.

**This VPS runs other agents that switch branches under you.** Installing from
`$REPO/summon/...` deployed a different branch's files twice. The installer now
extracts everything with `git show origin/main:<path>`, which does not care what
is checked out.

**Never `git stash -u` on an operator's box.** A fast-forward cannot touch
untracked files, so they never need stashing — and `-u` took 161 files and 31.5k
lines of somebody's unpushed dashboards off their disk because one tracked file
happened to be dirty. Stash tracked changes only, and say how many.

---

## Operating it

```bash
letsgo --watch                                  # attach to Sardar
ssh vps -t 'tmux attach -t sardar-2'            # or pick one
ssh vps 'systemctl status jivo-summond'
ssh vps 'journalctl -u jivo-summond -n 50'
ssh vps 'tail -20 /opt/jivo-summon/audit.jsonl'
ssh vps 'SUMMON_ROOT=/opt/jivo-summon /opt/jivo-summon/bin/grantctl list'
```

**Redeploy** after changing anything here — it deploys from `origin/main`, so
push first:

```bash
git push origin main
ssh vps 'bash -s' < summon/deploy/install-vps.sh
```

**Adding a box.** Nothing is required: an unknown device is auto-enrolled by
probing the machine, because its token already proved it is trusted. To record it
properly instead, add it to the live `policy.json` on the VPS (`ssh_user` +
`tunnel_port` are what make it reachable) and re-run the installer to regenerate
`ssh_config`.

**The live roster is not in git.** It carries hostnames, kit paths and SAP
usernames, and this repo is public. It lives only at
`/opt/jivo-summon/policy.json`; `policy.example.json` is the shape. To update it:
`scp summon/agent/policy.json vps:/tmp/policy.json` then re-run the installer,
which installs and shreds the staged copy.

### The endpoint

`https://jivo-mcp.srv1685505.hstgr.cloud/<random-slug>/v1/summon`

The slug is generated per install and stored at
`/opt/jivo-summon/state/path-slug`. It is obscurity **on top of** the bearer
token, never instead of it — `/healthz` is the only unauthenticated route, and it
returns liveness with no fleet detail.
