// zepto-portal — read-only CLI for the Zepto seller portal (brands.zepto.co.in).
//
// Auth/HTTP core is ported from the existing ~/ecomcliauto/clis/zepto-cli (JWT
// bearer, one token for every backend). The command tree is generated from the
// read-only endpoint inventory in ../vault/Zepto-Endpoints.md — one command
// group per studied section. cobra + stdlib only.
//
// READ-ONLY LAW: every command is a GET or a POST-to-read. No create / update /
// delete / upload / approve / schedule / cancel / pay is wired. Three layers
// enforce it (see client.go forbiddenPath + guardrail_test.go).
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
