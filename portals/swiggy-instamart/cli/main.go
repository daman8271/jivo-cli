// swiggy-instamart-portal — READ-ONLY CLI for JIVO's Swiggy Instamart brand +
// supply portal (partner.instamart.in).
//
// Generated from the READ allowlist in vault/Swiggy-Instamart-Endpoints.md. One
// command group per studied section.
//
// READ-ONLY LAW: no create / update / delete / approve / cancel / pay / upload /
// book / generate-a-report / login / logout is wired, and three layers make a
// mutation impossible to send — see client.go forbiddenRequest, allowlist.go, and
// guardrail_test.go.
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
