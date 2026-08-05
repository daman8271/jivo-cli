//go:build readonly

package cli

import "github.com/spf13/cobra"

// This file is the `readonly` half of the build seam. A binary built with
//
//	go build -tags readonly ./cmd/sapb1
//
// contains no draft/post/patch command at all — the code for them is excluded
// by the matching `//go:build !readonly` constraint on draft.go, post.go,
// patch.go and write.go, so there is nothing to call and nothing to discover
// in `--help`.
//
// Read this honestly: compiling the write commands out does NOT make the
// grant read-only. Whoever holds SAPB1_USER/SAPB1_PASSWORD can write to SAP
// from curl, Postman or the SAP B1 client regardless of which binary they
// were handed. The control that actually stops a write is the SAP B1 account
// itself (Administration → System Initialisation → Authorisations → Read
// Only). This seam exists so that a read-only grant cannot write *by
// accident*, and so `--help` never advertises a capability the holder is not
// meant to use.

const rootShort = "CLI for the SAP Business One Service Layer (READ-ONLY build)"

const writeHelpSection = `
This is a READ-ONLY build: the draft, post and patch commands are compiled out
and cannot be invoked. Every command here is a plain OData GET.

If you need to create or change something in SAP, do it in the SAP Business One
client, or ask the SAP administrator for a write-enabled grant.
`

// addWriteCommands is the no-op half of the seam.
func addWriteCommands(root *cobra.Command) {}
