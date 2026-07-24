package main

import (
	"fmt"
	"time"

	"github.com/spf13/cobra"
)

// newDoctorCmd reports config + JWT health and, unless --offline, does one
// harmless live READ to confirm the token is accepted end-to-end.
func newDoctorCmd(app *App) *cobra.Command {
	var offline bool
	c := &cobra.Command{
		Use:   "doctor",
		Short: "Check config, JWT expiry, and (optionally) a live read",
		// doctor tolerates a missing token so it can still report what's wrong.
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error { return nil },
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := resolveConfig()
			if err != nil {
				fmt.Printf("✗ credentials: %v\n", err)
				return err
			}
			fmt.Printf("config:   %s\n", configPath())
			fmt.Printf("base:     %s\n", cfg.Base)
			fmt.Printf("hosts:    %s | %s | %s | %s | %s | %s | %s\n",
				hostFCC, hostAuth, hostFin, hostSCP, hostOnboard, hostAdsPlat, hostPartner)
			fmt.Printf("brand_id: %s\n", cfg.BrandID)

			claims, err := decodeJWT(cfg.JWT)
			if err != nil {
				fmt.Printf("✗ jwt:     unreadable: %v\n", err)
				return err
			}
			now := time.Now()
			if claims.Expired(now) {
				fmt.Printf("✗ jwt:     EXPIRED at %s IST — %s\n", claims.Expiry().In(istLoc).Format("2006-01-02 15:04:05"), reLoginMsg)
			} else {
				fmt.Printf("✓ jwt:     %s, valid until %s IST (%s left)\n",
					claims.EmailID, claims.Expiry().In(istLoc).Format("15:04:05"),
					claims.Remaining(now).Round(time.Minute))
			}

			if offline {
				return nil
			}
			// One harmless live read: the vendor report queue (pure GET list).
			app.cfg = cfg
			app.Client = newClient(cfg)
			raw, err := app.Client.doRaw("GET", hostFCC+"/api/v1/reports?offset=0&limit=1", nil)
			if err != nil {
				fmt.Printf("✗ live:    %v\n", err)
				return err
			}
			fmt.Printf("✓ live:    reports queue reachable (%d bytes)\n", len(raw))
			return nil
		},
	}
	c.Flags().BoolVar(&offline, "offline", false, "skip the live read; only check config + JWT locally")
	return c
}
