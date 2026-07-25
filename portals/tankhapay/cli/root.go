package main

import (
	"sort"

	"github.com/spf13/cobra"
)

func newRootCmd() *cobra.Command {
	app := &App{}

	root := &cobra.Command{
		Use:   "tankhapay-portal",
		Short: "Read-only CLI for the TankhaPay Business portal (business.tankhapay.com)",
		Long: `tankhapay-portal — read-only access to JIVO's TankhaPay HR/payroll portal.

Every command is a READ (an AES-encrypted POST-to-read). No create/update/delete/
save/approve/pay/upload/submit is wired — a three-layer guardrail makes a mutation
impossible to send. One JWT (auto-refreshed daily from .env) authorizes all four
backends. Command groups mirror the studied portal sections (../vault).`,
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
			app.Client = newClient(cfg)
			// Authenticate up front so the account context (accountId, geo, ouIds)
			// is loaded BEFORE payloads are built — otherwise reads would go out
			// without their account params. Uses the cached 24h token; logs in
			// only when it is missing/expired.
			return app.Client.ensureAuth()
		},
	}
	root.PersistentFlags().BoolVar(&app.JSON, "json", false, "machine-readable JSON output")
	root.PersistentFlags().BoolVar(&app.Agent, "agent", false, "agent mode: JSON + stable {ok,command,endpoint,count,data|error} envelope")

	// doctor + auth manage their own pre-run (they must run without full config).
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
