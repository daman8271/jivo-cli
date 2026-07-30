package main

import (
	"fmt"
	"sort"
	"strings"

	"github.com/spf13/cobra"
)

// sectionSlug turns a canonical section name ("Account-Health-Performance")
// into a CLI command group ("account-health-performance").
func sectionSlug(s string) string { return strings.ToLower(s) }

// newRootCmd builds the whole command tree from the generated read allowlist:
// one command group per section, one subcommand per READ endpoint. Plus
// `doctor` and `auth whoami`. Nothing outside readEndpoints is reachable.
func newRootCmd(app *App) *cobra.Command {
	root := &cobra.Command{
		Use:   "amazon-portal",
		Short: "Read-only CLI over JIVO's Amazon Seller Central + Vendor Central (goal: portal-atlas Wave 1)",
		Long: "amazon-portal — a READ-ONLY window into JIVO's Amazon portals.\n\n" +
			"Every command is a GET against a READ-classified endpoint from the vault study\n" +
			"(portals/amazon/vault). The binary is physically incapable of a write: the HTTP\n" +
			"layer refuses any method other than GET and any path not in the READ allowlist.\n" +
			"It CONSUMES the existing Seller Central session (never logs in).",
		SilenceUsage: true,
	}
	root.PersistentFlags().BoolVar(&app.pretty, "pretty", true, "pretty-print JSON output")

	// group endpoints by section
	bySection := map[string][]Endpoint{}
	for _, e := range readEndpoints {
		bySection[e.Section] = append(bySection[e.Section], e)
	}
	secs := make([]string, 0, len(bySection))
	for s := range bySection {
		secs = append(secs, s)
	}
	sort.Strings(secs)

	for _, sec := range secs {
		eps := bySection[sec]
		sort.Slice(eps, func(i, j int) bool { return eps[i].Name < eps[j].Name })
		grp := &cobra.Command{
			Use:   sectionSlug(sec),
			Short: fmt.Sprintf("%s — %d read endpoints", sec, len(eps)),
		}
		for _, e := range eps {
			e := e
			nargs := 0
			if e.Params != "" {
				nargs = len(splitPipe(e.Params))
			}
			short := fmt.Sprintf("GET %s · %s", e.Path, e.Class)
			sub := &cobra.Command{
				Use:   e.Name,
				Short: short,
				Args:  cobra.ExactArgs(nargs),
				RunE:  func(cmd *cobra.Command, args []string) error { return app.run(e, args) },
			}
			grp.AddCommand(sub)
		}
		root.AddCommand(grp)
	}

	root.AddCommand(newDoctorCmd(app))
	root.AddCommand(newAuthCmd(app))
	return root
}

// newAuthCmd — `auth whoami` prints the non-secret session identity.
func newAuthCmd(app *App) *cobra.Command {
	c := &cobra.Command{Use: "auth", Short: "Session identity (read-only)"}
	c.AddCommand(&cobra.Command{
		Use:   "whoami",
		Short: "Show the consumed Seller Central session (entity, jar path) — no secrets",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if app.cfg.Cookie == "" {
				fmt.Printf("no session loaded (jar: %s)\n", app.cfg.JarPath)
				return nil
			}
			fmt.Printf("entity : Jivo Mart (Seller Central, India) — merchant A2V85Y00QGIGP9\n")
			fmt.Printf("jar    : %s\n", app.cfg.JarPath)
			fmt.Printf("cookies: %d present (consumed, never minted)\n", strings.Count(app.cfg.Cookie, "=")|1)
			return nil
		},
	})
	return c
}
