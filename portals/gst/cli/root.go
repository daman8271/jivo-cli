package main

import (
	"os"
	"sort"

	"github.com/spf13/cobra"
)

func newRootCmd() *cobra.Command {
	return newRootCmdWithApp(&App{out: os.Stdout, errw: os.Stderr, in: os.Stdin})
}

// newRootCmdWithApp builds the tree around a caller-supplied App, so tests can
// drive the whole CLI with their own stdout/stderr.
func newRootCmdWithApp(app *App) *cobra.Command {

	root := &cobra.Command{
		Use:   "gst-portal",
		Short: "Read-only CLI for the GST portal (gst.gov.in) — JIVO's 8 registrations",
		Long: `gst-portal — read-only access to JIVO Wellness's GST registrations.

The GST portal is a live statutory filing system. Every command here is a READ.
No GENERATE / SAVE / SUBMIT / FILE / RESET / COMPUTE / AMEND / CREATE CHALLAN is
wired, and a deny-by-default allowlist refuses one before a socket is opened.
Logging in is the only sanctioned side effect.

Pick a registration with --gstin, --state or --all (see ` + "`auth list`" + `).`,
		SilenceUsage:  true,
		SilenceErrors: true,
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			if app.Agent {
				app.JSON = true
			}
			return app.resolve()
		},
	}

	root.PersistentFlags().BoolVar(&app.JSON, "json", false, "JSON output for the table-shaped commands (doctor, auth list/status, snapshot); portal reads are JSON already")
	root.PersistentFlags().BoolVar(&app.Agent, "agent", false, "agent mode: JSON + stable {ok,command,endpoint,gstin,count,data|error} envelope, quiet stderr")
	root.PersistentFlags().StringVar(&app.GSTIN, "gstin", "", "select a registration by GSTIN (e.g. 06AACCJ4223F1Z0)")
	root.PersistentFlags().StringVar(&app.State, "state", "", "select a registration by state name, code or alias (e.g. haryana, hr, 06)")
	// --all is NOT global. Only doctor, auth status and snapshot can act on more
	// than one registration; every read command answers about exactly one, and a
	// global flag that three commands honour and eleven reject with a hard error
	// is a flag that lies. Each of the three declares it locally.

	// doctor + auth are always present (house shape) and manage their own needs.
	root.AddCommand(newDoctorCmd(app), newAuthCmd(app))

	regs := make([]*cobra.Command, 0, len(sectionRegistrars))
	for _, f := range sectionRegistrars {
		regs = append(regs, f(app))
	}
	sort.Slice(regs, func(i, j int) bool { return regs[i].Use < regs[j].Use })
	root.AddCommand(regs...)
	return root
}
