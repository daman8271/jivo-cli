//go:build !readonly

package cli

import "github.com/spf13/cobra"

// rootShort / writeHelpSection describe a full build — one that can write.
const rootShort = "CLI for the SAP Business One Service Layer (read-only by default)"

const writeHelpSection = `
Three commands can write, and only when you type them:

  draft <doctype>    create a DRAFT document — inert until a human opens SAP B1
                     → Document Drafts, reviews it, and presses Add. This is the
                     intended way to write.
  post <EntitySet>   create an object live, no draft — for master data
                     (BusinessPartners, Items, …). Prefer draft for documents.
  patch <Entity(key)> update fields on one existing object.

Each of those previews the exact request, asks you to confirm (or takes --yes),
and appends every attempt to a local write log (~/.sapb1-writes.jsonl, or
$SAPB1_WRITE_LOG). There is no delete command. The MCP server (sapb1 mcp) stays
strictly read-only — no write tool is exposed to agents.
`

// addWriteCommands wires the three write commands onto the root. Nothing here
// runs unless an operator explicitly types the command: each one previews the
// request, requires a confirmation (or --yes), and is appended to the local
// write log. `draft` is the intended path — it creates a Drafts row that stays
// inert until a human reviews and adds it in the SAP client; `post`/`patch` are
// the direct escape hatches. There is deliberately no delete, and the MCP
// surface exposes none of these.
func addWriteCommands(root *cobra.Command) {
	root.AddCommand(newDraftCmd())
	root.AddCommand(newPostCmd())
	root.AddCommand(newPatchCmd())
}
