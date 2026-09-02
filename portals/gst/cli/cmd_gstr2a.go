package main

import (
	"strings"

	"github.com/spf13/cobra"
)

// gstr2a — the dynamic mirror of what suppliers have filed against this GSTIN.
// GSTR-2B is the legal basis for ITC and the one Accounts should reconcile
// against; 2A is here for the cases where 2B has not been generated yet, or
// where a supplier filed late and you want to see it move.

func init() { registerSection(newGSTR2ACmd) }

func newGSTR2ACmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "gstr2a",
		Short: "GSTR-2A: supplier-filed inward supplies (2B is the legal one — see `gstr2b`)",
	}
	c.AddCommand(
		gstr2aStatusCmd(app),
		gstr2aSuppliersCmd(app),
		gstr2aDocsCmd(app),
		gstr2aAmendmentsCmd(app),
	)
	return c
}

func gstr2aStatusCmd(app *App) *cobra.Command {
	var period string
	c := &cobra.Command{
		Use:   "status",
		Short: "GSTR-2A form status for one period",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			return app.read("gstr2a status", reg, epFormDetails, nil, qs("rtn_prd", period, "rtn_typ", "GSTR2A"), nil)
		},
	}
	periodFlag(c, &period)
	return c
}

// gstr2aSuppliersCmd lists every counterparty that filed against this GSTIN in
// the period, with their own GSTR-1 filing date — which is the field that tells
// Accounts whether an ITC claim is safe. One response, no paging (353 suppliers
// came back in a single body on Haryana Jul-26).
func gstr2aSuppliersCmd(app *App) *cobra.Command {
	var period, section string
	c := &cobra.Command{
		Use:   "suppliers",
		Short: "Suppliers who filed against this GSTIN in a period, with their filing dates",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			return app.read("gstr2a suppliers", reg, epGSTR2ACtin, nil,
				qs("rtn_prd", period, "section_name", strings.ToUpper(section)), nil)
		},
	}
	periodFlag(c, &period)
	c.Flags().StringVar(&section, "section", "B2B", "section name (B2B is the one that was captured live)")
	return c
}

func gstr2aDocsCmd(app *App) *cobra.Command {
	var period, ctin string
	c := &cobra.Command{
		Use:   "docs",
		Short: "GSTR-2A B2B documents filed by one supplier",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if _, err := parsePeriod(period); err != nil {
				return err
			}
			if ctin == "" {
				return errUsage("--ctin <supplier GSTIN> is required; list them with `gstr2a suppliers --period %s`", period)
			}
			return app.read("gstr2a docs", reg, epGSTR2AB2B, nil,
				qs("rtn_prd", period, "ctin", strings.ToUpper(ctin)), nil)
		},
	}
	periodFlag(c, &period)
	c.Flags().StringVar(&ctin, "ctin", "", "supplier GSTIN")
	return c
}

// gstr2aAmendmentsCmd is deliberately inert. The portal has a b2ba route and the
// UI links to it, but nobody has captured the request, and this CLI does not
// guess a contract with a live statutory system — a guessed parameter name comes
// back as a portal error that looks like a bug for the next person to chase.
func gstr2aAmendmentsCmd(app *App) *cobra.Command {
	var period string
	c := &cobra.Command{
		Use:   "amendments",
		Short: "(not captured live yet) GSTR-2A B2B amendments",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.deferred("gstr2a amendments",
				"the b2ba route is visible in the portal's SPA but its request has never been recorded; "+
					"capture it with discovery/recorder.js, add the row to endpoints.go and wired-reads.tsv, then wire this leaf")
		},
	}
	c.Flags().StringVar(&period, "period", "", "return period, MMYYYY")
	return c
}
