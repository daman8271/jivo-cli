// Command ary is a fast, read-only, AI-native CLI for ARY's FusionERP8
// distribution/retail system — the SQL Server database FR8HODBNEW on the
// JOY SERVICES box. Every statement runs through a SELECT-only guard inside an
// always-rolled-back transaction: it can never write.
//
// ARY = "Akal Rozgar Yojana, a unit of Jivo Wellness Pvt Ltd" (PAN AACCJ4223F),
// three locations — Ary HO Delhi, Ary Baru Sahib (HP), Ary Bathinda (PB).
package main

import (
	"os"

	"ary/internal/cli"
	"ary/internal/config"
)

func main() {
	config.LoadDotEnv()
	os.Exit(cli.Execute())
}
