package main

import (
	"fmt"

	"github.com/spf13/cobra"
)

// newAuthCmd exposes ONLY `whoami`. There is deliberately no login, no refresh
// and no logout: those endpoints mint, rotate or destroy a session, and the
// refresh token is single-use so rotating it would break the live session of
// JIVO's e-com team and the production keepalive cron (G9).
func newAuthCmd(app *App) *cobra.Command {
	auth := &cobra.Command{
		Use:   "auth",
		Short: "Inspect the inherited session (no login/refresh/logout exists here)",
	}
	auth.AddCommand(&cobra.Command{
		Use:   "whoami",
		Short: "Who the inherited token belongs to, and what it can reach",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			for label, tok := range map[string]string{
				"ads/brand":     app.cfg.Token,
				"supply/vendor": app.cfg.SupplyToken,
			} {
				if tok == "" {
					fmt.Printf("%-14s absent\n", label)
					continue
				}
				c, err := decodeJWT(tok)
				if err != nil {
					fmt.Printf("%-14s undecodable\n", label)
					continue
				}
				fmt.Printf("%-14s %s\n", label, c.describe())
			}
			fmt.Println("\naccounts (verified 2026-07-30):")
			fmt.Printf("  wellness  %s   Jivo Wellness   (27 campaigns, 132 cities with sales)\n", acctJivoWellness)
			fmt.Printf("  mart      %s   Jivo Mart Pvt. Ltd (0 campaigns, 22 cities)\n", acctJivoMart)
			fmt.Printf("  jivo      %s   Jivo brand under Wellness\n", acctJivo)
			fmt.Println("\nNOTE: JIVO's own config.json maps brand_accounts.mart to the WELLNESS id.")
			fmt.Println("See vault/platform/Accounts-And-Entities.md — use the ids above.")
			return nil
		},
	})
	return auth
}
