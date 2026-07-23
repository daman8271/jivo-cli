// blinkit-partner — read-only CLI for the Blinkit PartnersBiz (Partner) portal.
// Auth/http/date core is ported from the existing blinkit-cli; the command tree
// is generated from the read-only endpoint inventory. cobra + stdlib only.
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
