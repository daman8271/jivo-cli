package main

import (
	"sort"

	"github.com/spf13/cobra"
)

func newRootCmd() *cobra.Command {
	app := &App{}

	root := &cobra.Command{
		Use:   "swiggy-instamart-portal",
		Short: "Read-only CLI for JIVO's Swiggy Instamart brand + supply portal",
		Long: `swiggy-instamart-portal — read-only access to JIVO's Swiggy Instamart portal
(partner.instamart.in), across all six of its module-federation remotes.

Every command is a READ. No create/update/delete/approve/cancel/pay/upload/book,
no report generation, and no login/logout/refresh is wired — three layers make a
mutation impossible to send (see client.go, allowlist.go, guardrail_test.go).

Auth is INHERITED, never minted (G9): the token comes from the config JIVO's
existing swiggy-instamart-cli already maintains. This CLI will not log in and will
not refresh, because the refresh token is single-use and rotating it breaks the
live session belonging to JIVO's e-com team and the production keepalive cron.

Command groups mirror the studied sections — see vault/00-Swiggy-Instamart-Atlas.md.`,
		SilenceUsage:  true,
		SilenceErrors: true,
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			if app.Agent {
				app.JSON = true
			}
			cfg, err := loadConfig()
			if err != nil {
				return err
			}
			app.cfg = cfg
			app.Client = newClient(cfg)
			return nil
		},
	}

	root.PersistentFlags().BoolVar(&app.JSON, "json", false, "machine-readable JSON output")
	root.PersistentFlags().BoolVar(&app.Agent, "agent", false,
		"agent mode: JSON in a stable {ok,command,endpoint,account,data|error} envelope")
	root.PersistentFlags().StringVar(&app.Account, "account", "",
		"account to scope to: mart | wellness | jivo | a raw uuid (default: wellness)")

	root.AddCommand(newDoctorCmd(app), newAuthCmd(app), newEndpointsCmd(app))

	regs := make([]*cobra.Command, 0, len(sectionRegistrars))
	for _, f := range sectionRegistrars {
		regs = append(regs, f(app))
	}
	sort.Slice(regs, func(i, j int) bool { return regs[i].Use < regs[j].Use })
	root.AddCommand(regs...)
	return root
}
