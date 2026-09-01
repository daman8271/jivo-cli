// Command saphist is a fast, read-only CLI for JIVO's OLD SAP Business One
// books — the pre-migration company databases that live on the Microsoft SQL
// Server at 138.252.101.118 (JOY SERVICES).
//
// These are the closed books, 2014-11-01 to 2024-10-01:
//
//	old  Live_Jivo_WellnessN_Aug_2019  Jivo Wellness Pvt. Ltd. (Old)  2014-11 -> 2019-08
//	new  Jivo_All_Branches_Live        Jivo Wellness Pvt. Ltd.        2019-08 -> 2024-10
//	bsu  ARY_BSU                       Akal Rozgar Yojana (BSU)       2019-04 -> 2023-03
//
// Anything AFTER October 2024 is in the LIVE SAP HANA system — use `sapb1`,
// not this tool. saphist never writes: every statement passes a SELECT-only
// guard and runs inside an always-rolled-back transaction.
package main

import (
	"os"

	"saphist/internal/cli"
	"saphist/internal/config"
)

func main() {
	config.LoadDotEnv()
	os.Exit(cli.Execute())
}
