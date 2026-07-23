---
title: Preserve Jivo Factory Multi-Company Request Scoping
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, company-scope, cache]
---

# Patch 0002 — preserve company flag, header, and cache partitioning

- **Why:** one Factory API and one JWT serve `JIVO_MART`, `JIVO_OIL`, and `JIVO_BEVERAGES`; the `Company-Code` request header selects the tenant. Re-login is neither needed nor correct. Omitting the header yields 403, and sharing a cache key across company codes can silently return one tenant's data for another.
- **Company resolution:** the hand-authored `internal/client/company.go` normalizes the persistent `--company` value or `JIVO_FACTORY_COMPANY`, supports safe shorthands, validates values, and defaults to `JIVO_MART`.
- **CLI wiring:** `internal/cli/root.go` exposes `--company`, resolves it before command execution, and fails invalid values as usage errors.
- **Transport wiring:** `internal/client/client.go` sets `Company-Code` on every request and includes the normalized company in the HTTP response-cache key.
- **Files:** `internal/client/company.go`, `internal/cli/root.go`, `internal/client/client.go`, and their focused tests.
- **Re-apply after regeneration:** restore all three layers together. A flag without header injection does not scope the request; a header without cache partitioning can cross-contaminate reads.
- **Verification:** top-level help must list `--company`; normalization tests must cover all three canonical codes and invalid input; client tests must prove request headers and cache keys change by company.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/README|Jivo Factory CLI]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
