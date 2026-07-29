// Command dsr is a fast, read-only, AI-native CLI for the JIVO DSR portal's
// backing SQL Server database (DSR_V6), with a secondary HTTP layer over the
// portal itself. Every database statement runs through a SELECT-only guard and
// a rolled-back READ UNCOMMITTED transaction — it can never write.
package main

import (
	"os"

	"dsr/internal/cli"
	"dsr/internal/config"
)

func main() {
	// Best-effort: pull creds from a local .env before flags/env are resolved.
	config.LoadDotEnv()
	os.Exit(cli.Execute())
}
