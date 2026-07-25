package main

import (
	"fmt"
	"time"

	"github.com/spf13/cobra"
)

// newAuthCmd manages the token. `login` performs the sanctioned token exchange
// (the ONLY non-read call in the CLI); `whoami` reads the cached token offline.
func newAuthCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:               "auth",
		Short:             "Token management — login (the only non-read call) and whoami",
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error { return nil },
	}

	login := &cobra.Command{
		Use:   "login",
		Short: "Force a fresh headless login and cache the 24h token",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := resolveConfig()
			if err != nil {
				return err
			}
			cl := newClient(cfg)
			if err := cl.relogin(); err != nil {
				return err
			}
			claims, _ := decodeJWT(cl.token)
			fmt.Printf("✓ logged in as %s (%s); token valid %s; cached at %s\n",
				cl.ctx.Name, cl.ctx.Role, claims.Remaining(time.Now()).Round(time.Minute), tokenCachePath())
			return nil
		},
	}

	whoami := &cobra.Command{
		Use:   "whoami",
		Short: "Show the cached token's account context (no network)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := resolveConfig()
			if err != nil {
				return err
			}
			tok := loadCachedToken()
			if tok == "" {
				return fmt.Errorf("no cached token; run `tankhapay-portal auth login`")
			}
			cl := newClient(cfg)
			cl.token = tok
			cl.loadCtx()
			claims, err := decodeJWT(tok)
			if err != nil {
				return err
			}
			fmt.Printf("user:    %s\nrole:    %s\nuserid:  %s\naccount: tp_account_id=%s geo=%s\nouIds:   %s\nexpires: %s (%s left)\n",
				cl.ctx.Name, cl.ctx.Role, cl.ctx.UserID, cl.ctx.AccountID, cl.ctx.GeoLocationID, cl.ctx.OuIds,
				claims.Expiry().Format(time.RFC3339), claims.Remaining(time.Now()).Round(time.Minute))
			return nil
		},
	}

	c.AddCommand(login, whoami)
	return c
}
