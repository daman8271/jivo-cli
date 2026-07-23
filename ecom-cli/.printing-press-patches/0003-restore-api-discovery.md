---
title: Restore the Ecom API Discovery Command
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, ecom, cli, printing-press, discovery]
---

# Patch 0003 — restore the hand-authored `api` discovery command

- **Date:** 2026-07-19
- **Why:** `internal/cli/api_discovery.go` adds `jivo-ecom-pp-cli api` — a
  read-only browser of every generated endpoint group and method. It makes NO
  HTTP call (it only walks the Cobra command tree) and is annotated
  `mcp:read-only`. It is hand-authored,
  not part of the printing-press scaffold, so a `cli-printing-press generate
  --force` drops it. The 2026-07-19 02:45 regen (44 -> 138 endpoints) removed
  the file and its registration. Recovered from
  `ecom-cli.preserve-1784409324383777000/` (now in `_archive/`).
- **Change:** restored `internal/cli/api_discovery.go` and re-added its
  registration in `internal/cli/root.go`, right after the workflow command:
      rootCmd.AddCommand(newAPICmd(flags)) // hand-authored: raw endpoint browser, no HTTP (api_discovery.go)
  The July 138-endpoint regeneration made all 12 generated resource parents
  visible, so the old `Hidden`-flag discovery rule became stale and could also
  admit unrelated hidden utilities. Discovery now defines an interface strictly
  as a top-level command whose subtree contains a non-empty `pp:endpoint`
  annotation. It recursively enumerates endpoint descendants, preserving full
  relative command paths for future nested layouts; JSON detail includes
  `name`, `short`, `endpoint`, HTTP `method`, and API `path`.
- **RE-APPLY AFTER EVERY REGEN:** a clean regen drops the file — restore
  `api_discovery.go` AND re-add the `AddCommand` line in `root.go`. A warm
  `generate --force` may keep the file but drop only the registration — re-add it.
- **Read-Only Law:** the `api` command performs no network I/O at all (pure
  tree-walk), never invokes an endpoint `RunE`, and is inherently safe to keep.
- **Verified:** `go build ./...` + `go vet ./...` green; `go test ./...` all
  pass. Focused tests compare discovery dynamically with every top-level
  `resources:` key in `spec.yaml`, cover hidden/visible independence, exclude
  generic commands, verify nested paths/metadata, and prove endpoint handlers
  never execute. Current runtime exposes exactly 12 groups (`account`,
  `chatbot`, `dashboard`, `master`, `notifications`, `platform`, `reports`,
  `sap`, `shipment`, `tables`, `upload`, `uploads`); dashboard detail reports
  26 methods. No network call made.

Linked: [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
