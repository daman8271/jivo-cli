package main

import (
	"sort"

	"github.com/spf13/cobra"
)

func newRootCmd() *cobra.Command {
	app := &App{}

	root := &cobra.Command{
		Use:   "zepto-portal",
		Short: "Read-only CLI for the Zepto seller portal (brands.zepto.co.in)",
		Long: `zepto-portal — read-only access to JIVO's Zepto seller portal.

Every command is a READ (GET or POST-to-read). No create/update/delete/upload/
approve/schedule/cancel/pay is wired — a three-layer guardrail makes a mutation
impossible to send. One JWT authorizes every backend; auth is inherited from the
existing zepto-cli config (refresh: bash ~/ecomcliauto/orchestrate/zepto-login.sh).

Command groups mirror the studied portal sections (../vault/00-Zepto-Atlas.md).`,
		SilenceUsage:  true,
		SilenceErrors: true,
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			if app.Agent {
				app.JSON = true
			}
			cfg, err := resolveConfig()
			if err != nil {
				return err
			}
			app.cfg = cfg
			app.BrandID = cfg.BrandID
			app.ManufID = defaultManufID
			app.Client = newClient(cfg)
			return nil
		},
	}

	root.PersistentFlags().BoolVar(&app.JSON, "json", false, "machine-readable JSON output")
	root.PersistentFlags().BoolVar(&app.Agent, "agent", false, "agent mode: JSON + stable {ok,command,endpoint,count,data|error} envelope, quiet stderr")

	// doctor + auth are always present and manage their own pre-run needs.
	root.AddCommand(newDoctorCmd(app), newAuthCmd(app))

	// Every section command registered via init() → registerSection.
	regs := make([]*cobra.Command, 0, len(sectionRegistrars))
	for _, f := range sectionRegistrars {
		regs = append(regs, f(app))
	}
	sort.Slice(regs, func(i, j int) bool { return regs[i].Use < regs[j].Use })
	root.AddCommand(regs...)
	return root
}
