// Command amazon-portal is a READ-ONLY CLI over JIVO's Amazon Seller Central and
// Vendor Central portals, generated from the portal study in portals/amazon/vault.
//
// Read-only guarantee (three layers, deny-by-default):
//  1. transport — client.go refuses any HTTP method other than GET, before a socket opens;
//  2. allowlist — only paths classified READ/READ_FILE in endpoints_gen.go are reachable;
//  3. tests    — guardrail_test.go asserts no write path is wired and non-GET is refused;
//     guardrail_coverage_test.go asserts every wired command maps to a READ row.
//
// It CONSUMES the existing Seller Central session (G9: never mints one).
package main

import (
	"os"
)

func main() {
	cfg := loadConfig()
	app := &App{Client: newClient(cfg), cfg: cfg, pretty: true}
	if err := newRootCmd(app).Execute(); err != nil {
		os.Exit(1)
	}
}
