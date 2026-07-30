package main

import (
	"fmt"

	"github.com/spf13/cobra"
)

// newDoctorCmd — is the Seller Central session live? Probes one cheap READ.
func newDoctorCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "Check whether the consumed Seller Central session is alive",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			fmt.Printf("jar        : %s\n", app.cfg.JarPath)
			if app.cfg.Cookie == "" {
				fmt.Println("session    : NONE — no cookie jar loaded")
				fmt.Println("status     : ✗ set AMAZON_SC_COOKIE_JAR or run the ecomcliauto Amazon login")
				return fmt.Errorf("no session")
			}
			// a light, universally-present READ
			probe := Endpoint{Host: "sellercentral.amazon.in", Path: "/account-switcher/global-and-regional-account/merchantMarketplace", Class: "READ"}
			// this path may not be in the allowlist under that exact name; fall back to feedback csrf
			raw, code, err := app.Client.get(probe.Host, probe.Path, probe.Path)
			if err != nil {
				// try an allowlisted endpoint instead
				for _, e := range readEndpoints {
					if e.Params == "" && e.Host == "sellercentral.amazon.in" {
						raw, code, err = app.Client.get(e.Host, e.Path, e.Path)
						probe = e
						break
					}
				}
			}
			if err != nil {
				fmt.Printf("status     : ✗ %v\n", err)
				return err
			}
			fmt.Printf("probe      : GET %s → HTTP %d\n", probe.Path, code)
			fmt.Printf("session    : ✓ LIVE (%d bytes)\n", len(raw))
			fmt.Printf("entity     : Jivo Mart · Seller Central · India\n")
			fmt.Printf("endpoints  : %d read commands wired across the section groups\n", len(readEndpoints))
			return nil
		},
	}
}
