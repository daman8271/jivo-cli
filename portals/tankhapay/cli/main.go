// tankhapay-portal — read-only CLI for JIVO's TankhaPay Business portal
// (business.tankhapay.com, HR/payroll SaaS by Akal Information Systems).
//
// The command tree is generated from the READ-only endpoint inventory in
// ../captures/wired-reads.tsv — one command group per studied section (../vault).
// cobra + stdlib only.
//
// READ-ONLY LAW: every command is an AES-encrypted POST-to-read. No create /
// update / delete / save / approve / pay / upload / submit is wired. Three layers
// enforce it: (1) only READ rows are wired; (2) forbiddenPath fails closed on any
// write verb; (3) no PUT/PATCH/DELETE code path exists. The sole non-read call is
// the sanctioned login token exchange (auth.go).
package main

import (
	"fmt"
	"os"
)

func main() {
	if err := newRootCmd().Execute(); err != nil {
		fmt.Fprintln(os.Stderr, "error: "+err.Error())
		os.Exit(1)
	}
}
