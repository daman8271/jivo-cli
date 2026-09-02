// gst-portal — read-only CLI for the GST common portal (gst.gov.in), for
// JIVO Wellness Pvt Ltd's 8 GST registrations.
//
// READ-ONLY LAW. The GST portal is a statutory filing system. Every command in
// this binary is a READ. Nothing here can GENERATE, SAVE, SUBMIT, FILE, RESET,
// COMPUTE, AMEND or CREATE A CHALLAN — the four layers that make that true are:
//
//  1. only READ rows exist in the endpoint table (endpoints.go);
//  2. forbidden() denies by default before any socket opens (guard.go);
//  3. no mutating code path exists — the client has no PUT/PATCH/DELETE and
//     POST is legal only for the three read-shaped rows the table marks;
//  4. tests: guardrail_test.go, guardrail_coverage_test.go, readonly_ast_test.go.
//
// The only sanctioned side effect in the whole binary is logging in
// (POST /services/authenticate), and that happens once per registration per
// process, never automatically retried.
//
// cobra + stdlib only, per house convention (portals/zepto/cli, dsr-cli).
package main

import (
	"fmt"
	"os"
)

func main() {
	app := &App{out: os.Stdout, errw: os.Stderr, in: os.Stdin}
	err := newRootCmdWithApp(app).Execute()
	if err == nil {
		return
	}
	fmt.Fprintln(os.Stderr, "error: "+err.Error())
	// An error raised BEFORE a leaf command runs — a missing .env, an unknown
	// flag, a --gstin that matches nothing — never reached emit()/emitError(),
	// so under --agent stdout was left completely empty and an agent parsing it
	// got zero bytes instead of {"ok":false,…}. Emit the envelope here for
	// exactly that case; anything that already wrote one is left alone.
	if (app.Agent || agentFlagPresent(os.Args)) && !app.wroteEnvelope {
		app.Agent = true
		_ = app.emitError("gst-portal", "", "", err)
	}
	os.Exit(exitCodeFor(err))
}

// agentFlagPresent scans argv directly, because a flag-parse failure is one of
// the errors this has to cover — and in that case cobra never set app.Agent.
func agentFlagPresent(args []string) bool {
	for _, a := range args {
		if a == "--agent" || a == "--agent=true" {
			return true
		}
	}
	return false
}
