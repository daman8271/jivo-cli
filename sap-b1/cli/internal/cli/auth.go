package cli

import (
	"fmt"
	"time"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
)

func newAuthCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "auth",
		Short: "Manage the SAP Service Layer session",
	}
	cmd.AddCommand(newAuthLoginCmd())
	cmd.AddCommand(newAuthStatusCmd())
	cmd.AddCommand(newAuthLogoutCmd())
	return cmd
}

func newAuthLoginCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "login",
		Short: "Log in to the Service Layer and cache the session",
		Example: exampleBlock(
			`sapb1 auth login`,
			`sapb1 auth login --company SBODEMOUS --insecure`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := loadConfig(cmd)
			if err != nil {
				return err
			}
			if err := cfg.ValidateConnection(); err != nil {
				return err
			}
			if err := cfg.ValidateCompanyDB(); err != nil {
				return err
			}

			c := client.New(cfg)
			if err := c.Login(cmd.Context()); err != nil {
				return err
			}

			fmt.Fprintf(cmd.OutOrStdout(), "Connected to %s as %s\n", cfg.CompanyDB, cfg.User)
			return nil
		},
	}
}

func newAuthStatusCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: "Show resolved configuration and cached-session status",
		Example: exampleBlock(
			`sapb1 auth status`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := loadConfig(cmd)
			if err != nil {
				return err
			}

			out := cmd.OutOrStdout()
			fmt.Fprintln(out, "Configuration:")
			fmt.Fprintf(out, "  Host:       %s\n", orNotSet(cfg.Host))
			fmt.Fprintf(out, "  Port:       %d\n", cfg.Port)
			fmt.Fprintf(out, "  CompanyDB:  %s\n", orNotSet(cfg.CompanyDB))
			fmt.Fprintf(out, "  User:       %s\n", orNotSet(cfg.User))
			fmt.Fprintf(out, "  Password:   %s\n", cfg.MaskedPassword())
			fmt.Fprintf(out, "  Insecure:   %v\n", cfg.Insecure)
			fmt.Fprintf(out, "  Timeout:    %ds\n", cfg.Timeout)
			fmt.Fprintln(out)

			c := client.New(cfg)
			if !c.LoadCachedSession() {
				fmt.Fprintln(out, "Cached session: none (run `sapb1 auth login`, or any read command will log in automatically)")
				return nil
			}

			age, _ := c.SessionAge()
			const idleHint = 30 * time.Minute
			if age < 25*time.Minute {
				fmt.Fprintf(out, "Cached session: present, age %s — likely still valid (SAP idles sessions out after ~30m)\n", age.Round(time.Second))
			} else {
				fmt.Fprintf(out, "Cached session: present, age %s — likely expired (SAP idles sessions out after ~%s); the next read command will transparently re-login\n", age.Round(time.Second), idleHint)
			}
			return nil
		},
	}
}

func newAuthLogoutCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "logout",
		Short: "Log out and clear the cached session",
		Example: exampleBlock(
			`sapb1 auth logout`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := loadConfig(cmd)
			if err != nil {
				return err
			}
			c := client.New(cfg)
			hadSession := c.LoadCachedSession()
			if err := c.Logout(cmd.Context()); err != nil {
				return err
			}
			if hadSession {
				fmt.Fprintln(cmd.OutOrStdout(), "Logged out — session cleared")
			} else {
				fmt.Fprintln(cmd.OutOrStdout(), "No cached session — nothing to do")
			}
			return nil
		},
	}
}

func orNotSet(s string) string {
	if s == "" {
		return "(not set)"
	}
	return s
}
