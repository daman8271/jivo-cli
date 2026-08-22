---
name: letsgo
description: Use when the operator says "Let's go", "lets go", "summon", "ask Sardar", "summon Sardar", "ask the VPS agent", "I need access to X", "I can't write to SAP", "give me permission for X", or otherwise needs access/permission they do not currently have. Reaches Sardar, JIVO's summon agent on the VPS, who holds the fleet roster and can grant access without waiting for Daman.
---

# Let's go — reach Sardar

**Sardar** is a **live Claude Code session running on JIVO's VPS**, started by
systemd and kept up. He holds the fleet roster, knows what every machine in the
office is allowed to do, and can grant access. He exists so nobody has to wait
for Daman to be free.

When the operator says **"Let's go"** — or asks for access they don't have — send
it there. Do not try to fix their permissions yourself from this machine.

## Do this

```bash
letsgo "<what they need, in their words>"
```

If `letsgo` is not on PATH, the box hasn't been set up yet:

```bash
bash <kit>/summon/deploy/install-client.sh        # mac/linux
<kit>\summon\deploy\install-client.cmd            # windows
```

That needs a device token, which only Daman can mint (`/opt/jivo-summon/tokens.json`
on the VPS). If there's no token, say so plainly and stop — don't improvise a
workaround.

## What comes back

Sardar's answer, in plain language, plus what he granted, what he refused, and
anything still waiting on a human. Relay that to the operator as-is. He speaks
with Daman's authority; do not soften it, second-guess it, or add caveats he
didn't make.

Sardar's default answer is **yes** — Daman set him up permissive on purpose, and
the gate happens when a device token is minted, not when a request arrives. So if
he says no, it is a fact about the machine (offline, no git checkout, no SAP user
assigned), never a policy. Relay the fact and who fixes it.

## Before you summon: check the boring causes first

Most "I can't write to SAP" is not a permission problem, and the agent will just
tell you the same thing after a slower round trip. Check these here first:

1. **Are they in a Google-Drive ZIP export instead of a git checkout?** Folder
   names like `jivo-cli-…Z-1-001`. This is the most common cause by a wide
   margin — the zip's `CLAUDE.md` still says read-only and its `sapb1.exe`
   predates the `draft` command. `git -C <kit> rev-parse HEAD` failing is the
   tell. They need a real `git clone`.
2. **Has this box pulled recently?** RULE 0 allowing SAP writes landed in commit
   `a3b9465`. `grep -c "YOU MAY WRITE TO SAP" <kit>/CLAUDE.md` returning 0 means
   they simply haven't pulled — a sync problem, not a permission one.
3. **Is their SAP user `manager`?** That account is read-only at JIVO.
   Write-capable named users in use: `USER01`, `USER06`, `USER36`.

If it's one of those, say so and fix it directly — that's faster than a summon.
Summon when it's genuinely about access, or when you've ruled these out.

## Watching it work

Sardar is a real interactive session, not a headless one-shot, so he can be
watched:

```bash
letsgo --status              # is he up, which sessions are live
letsgo --watch               # attach and watch him think
```

`--watch` drops you inside Sardar's own tmux pane (`sardar-1`). You can type at
him directly. Useful when a grant is behaving oddly and you want to see why.

## Never

- **Never edit another machine's permissions from this one.** Everything goes
  through Sardar's `grantctl`, so it is locked, idempotent and audited. Ad-hoc
  ssh fixes are how a box ends up in a state nobody can explain.
- **Never invent, copy or read out a credential** to unblock somebody. Assigning
  a named SAP user is a human step. Say who has to do it.
- **Never claim a grant landed without reading it back.** A `git pull` that
  printed no error is not evidence.
