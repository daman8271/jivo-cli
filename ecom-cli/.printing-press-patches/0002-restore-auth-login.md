---
title: Restore the Ecom Auth Login Command
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, ecom, cli, printing-press, authentication]
---

# Patch 0002 — restore the hand-authored `auth login` command

- **Date:** 2026-07-19
- **Why:** `internal/cli/jivo_login.go` adds `jivo-ecom-pp-cli auth login`
  (email+password -> JWT, stored via `config.SaveTokens`). It is the ONLY
  non-GET request in this CLI (a single `POST /api/auth/login`, HTTPS-guarded,
  password never persisted) and it is NOT part of the printing-press scaffold,
  so a `cli-printing-press generate --force` drops it. The 2026-07-19 02:45
  regen (44 -> 138 endpoints) did exactly this: the file and its `AddCommand`
  line vanished, leaving the CLI with ZERO login code. Recovered from
  `ecom-cli.preserve-1784409324383777000/` (now in `_archive/`).
- **Change:** restored `internal/cli/jivo_login.go` and re-added its
  registration in `internal/cli/auth.go`:
      cmd.AddCommand(newAuthLoginCmd(flags)) // hand-authored: email+password -> JWT (jivo_login.go)
  All helper symbols it depends on (`dryRunOK`, `boundCtx`, `printJSONFiltered`,
  `usageErr`, `configErr`, `cliError`, `cliutil.IsVerifyEnv`, `config.Load`,
  `cfg.SaveTokens`) already exist in the regenerated tree, so no adaptation was
  needed beyond the one `AddCommand` line.
- **RE-APPLY AFTER EVERY REGEN:** a clean regen (`rm dir + generate`) drops the
  file entirely — restore `jivo_login.go` AND re-add the `AddCommand` line. A
  warm `generate --force` may keep the file but drop only the `AddCommand`
  line — re-add it in `auth.go`. See docs/ecom/ECOM_CLI_MCP_AND_SKILL.md:259.
- **Read-Only Law:** login mints/refreshes a JWT and creates zero business data,
  so it is permitted (mirrors exim's `auth login` carve-out). Prefer a
  read-scoped credential regardless (defense in depth).
- **Verified:** `go build ./...` + `go vet ./...` green; `go test ./...` all
  pass; `./jivo-ecom-pp-cli auth --help` lists `login`. No network call made.

Linked: [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
