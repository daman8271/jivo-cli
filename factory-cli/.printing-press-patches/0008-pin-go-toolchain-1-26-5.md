---
title: Pin the Go Toolchain to 1.26.5 or Newer
created: 2026-08-03
updated: 2026-08-03
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, security, toolchain]
---

# Patch 0008 — `toolchain go1.26.5` in go.mod

- **Why:** Go 1.26.4's `crypto/tls` carries **GO-2026-5856**, an Encrypted
  Client Hello privacy leak, fixed in 1.26.5. The generator writes the
  `toolchain` directive from whatever Go the build host has, so a machine still
  on 1.26.4 emits `toolchain go1.26.4` and ships a binary built against the
  vulnerable standard library.

- **This is not theoretical for this CLI.** `govulncheck` traced four call paths
  into the vulnerable code, and the first one is the MCP server's public HTTP
  transport — the surface serving the JIVO connector over TLS:

  ```
  cmd/jivo-factory-pp-mcp/main.go:51  server.StreamableHTTPServer.Start
                                    → tls.Conn.HandshakeContext
  internal/cliutil/probe.go:85        cliutil.ProbeReachable → http.Client.Do
                                    → tls.Dialer.DialContext
  internal/cliutil/probe.go:92        cliutil.ProbeReachable → io.Copy
                                    → tls.Conn.Read
  internal/store/store.go:1236        store.UpsertBatch → fmt.Fprintf
                                    → tls.Conn.Write
  ```

- **Evidence, both directions (2026-08-03):**

  | toolchain directive | `govulncheck ./...` |
  |---|---|
  | `go1.26.4` | affected by 1 vulnerability — GO-2026-5856, gate FAILS |
  | `go1.26.5` | **0 vulnerabilities**, gate passes |

- **Change:** `go.mod` must read `toolchain go1.26.5` (or newer). Nothing else
  in the tree changes; the build is otherwise identical.

- **The durable fix is upgrading the build host.** This patch corrects the
  emitted directive, but the generator will write `toolchain go1.26.4` again on
  any machine still running Go 1.26.4. Upgrade Go on the build host so the
  correct directive is emitted without intervention.

- **Re-apply after regeneration:** check `grep '^toolchain ' go.mod` and bump it
  if it regressed below 1.26.5. `research/verify-invariants.sh` asserts this.

- **Verification:** `go run golang.org/x/vuln/cmd/govulncheck@latest ./...` must
  report `Your code is affected by 0 vulnerabilities.` The residual "1
  vulnerability in modules you require" is not called by this code and is not a
  blocker.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/README|Jivo Factory CLI]]
