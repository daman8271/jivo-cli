package main

import (
	"fmt"
	"time"

	"github.com/spf13/cobra"
)

// newDoctorCmd reports config + credential + token health and, unless --offline,
// does one harmless live READ (the dashboard summary) to confirm end-to-end.
func newDoctorCmd(app *App) *cobra.Command {
	var offline bool
	c := &cobra.Command{
		Use:   "doctor",
		Short: "Check config, credentials, token, and (optionally) a live read",
		// doctor self-diagnoses; it must run even when config is incomplete.
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error { return nil },
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := resolveConfig()
			if err != nil {
				fmt.Printf("✗ config:  %v\n", err)
				return err
			}
			fmt.Printf("✓ config:  user=%s  body-key=%d bytes\n", cfg.Username, len(cfg.BodyKey))
			for _, k := range []string{"business", "mobapi", "tpPay", "tnd"} {
				fmt.Printf("  backend %-8s %s\n", k, cfg.Backends[k])
			}
			fmt.Printf("  token:   %s\n", tokenCachePath())

			app.cfg = cfg
			app.Client = newClient(cfg)
			if err := app.Client.ensureAuth(); err != nil {
				fmt.Printf("✗ auth:    %v\n", err)
				return err
			}
			cl, _ := decodeJWT(app.Client.token)
			fmt.Printf("✓ token:   %s (%s) — valid %s\n", app.Client.ctx.Name, app.Client.ctx.Role, cl.Remaining(time.Now()).Round(time.Minute))
			fmt.Printf("  account: tp_account_id=%s geo=%s ouIds=%s\n", app.Client.ctx.AccountID, app.Client.ctx.GeoLocationID, app.Client.ctx.OuIds)

			if offline {
				return nil
			}
			payload := mustJSON(map[string]any{
				"action":          "get_employee_list",
				"accountId":       app.Client.ctx.AccountID,
				"geo_location_id": app.Client.ctx.GeoLocationID,
				"ouIds":           app.Client.ctx.OuIds,
			})
			raw, err := app.Client.doRead("business", "dashboard/get_tpay_dashboard_data", payload)
			if err != nil {
				fmt.Printf("✗ live:    %v\n", err)
				return err
			}
			fmt.Printf("✓ live:    dashboard read OK (%d bytes decrypted)\n", len(raw))
			return nil
		},
	}
	c.Flags().BoolVar(&offline, "offline", false, "skip the live read; only check config + token locally")
	return c
}
