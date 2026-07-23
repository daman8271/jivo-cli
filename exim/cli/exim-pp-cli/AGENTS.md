---
title: EXIM Printed CLI Agent Guide
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: instructions
tags: [jivogpt, exim, cli, agents]
---

# Exim Printed CLI Agent Guide

This directory is a generated `exim-pp-cli` printed CLI. It was produced by [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press), so treat systemic fixes as upstream Printing Press fixes first. Keep local edits narrow and document why a generated-tree patch belongs here.

## Local Operating Contract

Start by asking the generated CLI for current runtime truth:

```bash
exim-pp-cli doctor --json
exim-pp-cli agent-context --pretty
```

Use runtime discovery instead of relying on a copied command list:

```bash
exim-pp-cli which "<capability>" --json
exim-pp-cli <command> --help
```

Add `--agent` to command invocations for JSON, compact output, non-interactive defaults, no color, and confirmation-safe scripting:

```bash
exim-pp-cli <command> --agent
```

Before running an unfamiliar command that may mutate remote state, inspect its help and prefer a dry run:

```bash
exim-pp-cli <command> --help
exim-pp-cli <command> --dry-run --agent
```

Use `--yes --no-input` only after the target, arguments, and side effects are clear.

For install, auth, examples, and longer product guidance, read `README.md` and `SKILL.md`. This file intentionally stays small so repo-local agents get invariant local guidance without duplicating the generated docs.

## Release Ledger

`CHANGELOG.md` and `.printing-press-release.json` are the public library's per-CLI release ledger. Fresh prints may carry blank skeletons, but the final `YYYY.M.N` CLI release version is assigned only after a publish PR merges in `mvanhorn/printing-press-library`. Do not hand-bump those files or edit `var version = ...` for release bookkeeping; preserve existing ledger files on reprint and let the library workflow stamp the next release.

## Local Customizations

This directory is **generated output** -- a fresh print can overwrite the whole tree, so ad-hoc hand-edits don't survive on their own. If you modify the generated code, record each change under `.printing-press-patches/` (parallel to `.printing-press.json`) so a regen carries the intent forward instead of silently dropping it.

Start every reprint review at [[CLI/exim/cli/exim-pp-cli/.printing-press-patches/README|the EXIM local patch ledger]]. It indexes the native login, transport guard, and disabled generic import.

The entry shape, and the altitude to write it at -- a durable reprint-guard, not a changelog -- live in the source catalog's `AGENTS.md`, which is the single source of truth; this guide intentionally doesn't duplicate them.

Linked: [[CLI/exim/cli/exim-pp-cli/.printing-press-patches/README|EXIM patch ledger]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[CLI/exim/HARD-RULE|HARD-RULE]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
