---
name: letsgo
description: Use when the operator says "Let's go", "lets go", "summon", "summon the agent", "ask the VPS agent", "I need access to X", "I can't write to SAP", "give me permission for X", or otherwise needs access/permission they do not currently have. Reaches JIVO's central summon agent on the VPS, which holds the fleet roster and can grant access without waiting for Daman.
---

# Let's go — reach the summon agent

There is a **live Claude Code session running on JIVO's VPS**, started by systemd
and kept up. It holds the fleet roster, knows what every machine in the office is
allowed to do, and can grant access. It exists so nobody has to wait for Daman to
be free.

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

The agent's answer, in plain language, plus what it granted, what it refused, and
anything still waiting on a human. Relay that to the operator as-is. It is
speaking with Daman's authority; do not soften it, second-guess it, or add
caveats it didn't make.

If it says something is **parked for Daman**, that is final. Tell the operator
it's waiting on him. Do not look for another route — there isn't one, by design.

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

The summon agent is a real interactive session, not a headless one-shot, so it
can be observed:

```bash
letsgo --status              # is it up, which sessions are live
letsgo --watch               # attach to the session and watch it think
```

`--watch` drops you inside the agent's own tmux pane. You can type at it directly.
Useful when a grant is behaving oddly and you want to see why.

## Never

- **Never edit another machine's permissions from this one.** Everything goes
  through the agent's `grantctl`, so it is locked, idempotent and audited. Ad-hoc
  ssh fixes are how a box ends up in a state nobody can explain.
- **Never invent, copy or read out a credential** to unblock somebody. Assigning
  a named SAP user is a human step. Say who has to do it.
- **Never claim a grant landed without reading it back.** A `git pull` that
  printed no error is not evidence.
