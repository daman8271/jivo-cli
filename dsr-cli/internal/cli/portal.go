package cli

// Read-only commands that call the DSR web portal's own report endpoints, for
// cross-checking the direct-SQL numbers. Login uses DSR_PORTAL_USER/PASSWORD.
// GET-only — the portal is read-only for this tool (RULE 0).

import (
	"fmt"
	"net/url"
	"os"

	"github.com/spf13/cobra"

	"dsr/internal/portal"
)

func init() { register(newPortalCmd) }

func newPortalCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "portal",
		Short: "Read-only calls to the DSR web portal's own report endpoints (login required)",
		Long: "Authenticates with DSR_PORTAL_USER/DSR_PORTAL_PASSWORD and issues GET-only requests\n" +
			"to the portal's report endpoints. Never posts or writes. Useful to cross-check the\n" +
			"direct-SQL commands against the numbers the portal itself computes.",
	}
	c.AddCommand(portalCheckCmd(app), portalMonthlySaleCmd(app), portalItemSaleCmd(app), portalUnapprovedCmd(app))
	return c
}

func portalClient(app *App) (*portal.Client, error) {
	if app.Prof.PortalURL == "" {
		return nil, Usagef("no portal URL configured (set DSR_PORTAL_URL)")
	}
	if app.Prof.PortalUser == "" || app.Prof.PortalPassword == "" {
		return nil, Usagef("portal login not configured: set DSR_PORTAL_USER and DSR_PORTAL_PASSWORD")
	}
	cl, err := portal.New(app.Prof.PortalURL, app.Flags.Timeout)
	if err != nil {
		return nil, err
	}
	if err := cl.Login(app.Prof.PortalUser, app.Prof.PortalPassword); err != nil {
		return nil, err
	}
	return cl, nil
}

func portalEmit(b []byte) error {
	os.Stdout.Write(b)
	if n := len(b); n == 0 || b[n-1] != '\n' {
		fmt.Println()
	}
	return nil
}

func portalCheckCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "check",
		Short: "Log in and confirm the portal session works",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cl, err := portalClient(app)
			if err != nil {
				return err
			}
			body, err := cl.Get("/", nil)
			if err != nil {
				return err
			}
			fmt.Printf("portal: %s\nlogin:  %s — OK\nhome:   %d bytes\n", app.Prof.PortalURL, app.Prof.PortalUser, len(body))
			return nil
		},
	}
}

func portalMonthlySaleCmd(app *App) *cobra.Command {
	var from, to string
	c := &cobra.Command{
		Use:   "monthly-sale",
		Short: "Portal's monthly sale totals (litres) — /Home/MonthlySale",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cl, err := portalClient(app)
			if err != nil {
				return err
			}
			q := url.Values{}
			if from != "" {
				q.Set("fromdate", from)
			}
			if to != "" {
				q.Set("todate", to)
			}
			body, err := cl.Get("/Home/MonthlySale", q)
			if err != nil {
				return err
			}
			return portalEmit(body)
		},
	}
	c.Flags().StringVar(&from, "from", "", "fromdate (e.g. 2026-07-01)")
	c.Flags().StringVar(&to, "to", "", "todate (e.g. 2026-07-31)")
	return c
}

func portalItemSaleCmd(app *App) *cobra.Command {
	var month string
	c := &cobra.Command{
		Use:     "item-sale",
		Short:   "Portal's item-wise sale for a month — /Home/GetItemWiseSale",
		Example: "  dsr portal item-sale --month \"July,2026\"",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if month == "" {
				return Usagef("--month is required (e.g. \"July,2026\")")
			}
			cl, err := portalClient(app)
			if err != nil {
				return err
			}
			q := url.Values{}
			q.Set("month", month)
			body, err := cl.Get("/Home/GetItemWiseSale", q)
			if err != nil {
				return err
			}
			return portalEmit(body)
		},
	}
	c.Flags().StringVar(&month, "month", "", "month like \"July,2026\" (required)")
	return c
}

func portalUnapprovedCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "unapproved-count",
		Short: "Count of unapproved sales the portal shows — /geolocation/getUnapprovedSalesCount",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cl, err := portalClient(app)
			if err != nil {
				return err
			}
			body, err := cl.Get("/geolocation/getUnapprovedSalesCount", nil)
			if err != nil {
				return err
			}
			return portalEmit(body)
		},
	}
}
