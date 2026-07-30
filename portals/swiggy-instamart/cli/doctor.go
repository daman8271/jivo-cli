package main

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
)

// newDoctorCmd reports whether the INHERITED session is usable, without printing
// the token (G6) and without touching any write endpoint.
func newDoctorCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "Check the inherited session, the clock and the read allowlist",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			fmt.Println("swiggy-instamart-portal — doctor")
			fmt.Println("READ-ONLY. No write, no login, no refresh, no report generation.")
			fmt.Printf("\nconfig       : %s\n", configPath())
			fmt.Printf("allowlist    : %d read endpoints across %d hosts\n",
				allowlistSize(), len(allowedReads))

			cfg, err := loadConfig()
			if err != nil {
				fmt.Printf("\nsession      : NONE — %v\n", err)
				os.Exit(3)
			}

			fmt.Println("\nsessions (values never printed):")
			any := false
			for label, tok := range map[string]string{
				"ads/brand (authorization: Bearer)": cfg.Token,
				"supply/vendor (Abacus-Token)":      cfg.SupplyToken,
			} {
				if tok == "" {
					fmt.Printf("  %-34s absent\n", label)
					continue
				}
				c, derr := decodeJWT(tok)
				if derr != nil {
					fmt.Printf("  %-34s present but undecodable (%v)\n", label, derr)
					continue
				}
				fmt.Printf("  %-34s %s\n", label, c.describe())
				if c.valid() {
					any = true
				}
			}

			// server clock — the one unauthenticated read on the platform
			t0 := time.Now()
			ms := app.Client.serverTimeMillis()
			skew := time.Since(t0)
			fmt.Printf("\nserver clock : %s (round trip %s)\n",
				time.UnixMilli(ms).UTC().Format(time.RFC3339), skew.Round(time.Millisecond))

			fmt.Printf("signing      : ")
			if signingPepper() == "" {
				fmt.Println("SWIGGY_SIGN_PEPPER not set — brand-portal calls cannot be signed " +
					"and will 403. The pepper is a secret and is deliberately not in this repo (G6).")
			} else {
				fmt.Printf("pepper present, app_version %s\n", appVersion())
			}

			fmt.Println("\nplatform note: even a correctly-signed hand-built request is rejected by")
			fmt.Println("Swiggy's server-side session-activation wall — verified from inside the")
			fmt.Println("human's own logged-in browser. See vault/_meta/Auth-and-Access.md §5.")
			fmt.Println("The authoritative read path remains the portal walk captures.")

			if !any {
				fmt.Println("\nverdict      : NO LIVE SESSION. A human must refresh it; this CLI will not (G9).")
				os.Exit(3)
			}
			fmt.Println("\nverdict      : a live session is present.")
			return nil
		},
	}
}
