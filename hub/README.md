# hub — which CLI answers this question?

This checkout holds 14 CLIs. Nobody remembers all of them, and the most common
way the toolkit wastes an afternoon is someone hand-rolling a query against a
system that already has a command for it.

```bash
python3 hub/bin/hub.py search "vendor outstanding balance"
python3 hub/bin/hub.py list
python3 hub/bin/hub.py info sapb1
python3 hub/bin/hub.py doctor --probe
python3 hub/bin/hub.py run sapb1 -- doctor
```

Borrowed from [CLI-Anything's CLI-Hub](https://clianything.cc/). We took the part
that matters — runtime discovery, so an agent can find a tool mid-task instead of
guessing — and left the package manager, because our CLIs ship with the checkout.

## The two files

- `registry.json` — what *should* exist. Name, what it answers, keywords, the
  binary, whether it can write, its build command, its docs, and the correction
  that most often makes an answer from it wrong.
- `bin/hub.py` — python3 stdlib only, no network. `doctor` is the only part that
  knows what *does* exist; everything else reads the registry.

## Rules

- **No hosts, IPs, ports or credentials in `registry.json`.** This repo is public.
- Update the registry when a CLI is added, renamed, or gains a command group. A
  stale registry sends the next agent to the wrong tool, which is worse than no
  registry at all.
- `doctor` failing is a connectivity or credential fact, not a missing feature.
  `MISSING` means not compiled here — the build command is in the output.

The agent-facing rule lives in `.claude/skills/cli-hub/SKILL.md`.
