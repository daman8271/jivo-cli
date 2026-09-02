package main

import (
	"strconv"

	"github.com/spf13/cobra"
)

// compare — the portal's own reconciliation report: GSTR-1 vs 3B liability and
// 2A/2B vs 3B ITC, month by month, already computed by GSTN. comparison-spec §C3
// calls this the cheapest cross-check there is, and it costs one call for a
// whole financial year.

func init() { registerSection(newCompareCmd) }

func newCompareCmd(app *App) *cobra.Command {
	var fy string
	var withHeader bool
	c := &cobra.Command{
		Use:   "compare",
		Short: "The portal's own GSTR-1-vs-3B and 2A-vs-3B tables for a financial year",
		Long: `One call returns every table of the portal's comparison report for the whole
financial year: 13 rows each (12 months + total) of declared liability, actual
liability, the difference and the cumulative difference, per tax head.

The report is precomputed by GSTN and refreshed roughly daily — it is not a live
recomputation, so a return filed an hour ago may not be in it yet.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			start, err := parseFY(fy)
			if err != nil {
				return err
			}
			cl := newClient(reg)
			if withHeader {
				if _, err := cl.do(epCompareUser, nil, nil, nil); err != nil {
					return app.emitError("compare", reg.GSTIN, endpointURL(epCompareUser), err)
				}
			}
			// The portal wants the FY's START YEAR here, not the "2026-27" label:
			// fy=2026 means FY 2026-27. Sending the label returns nothing useful.
			res, err := cl.do(epCompareData, nil,
				qs("form_type", "allreports", "fy", strconv.Itoa(start.Year())), nil)
			return app.emit("compare", reg.GSTIN, endpointURL(epCompareData), res, err)
		},
	}
	c.Flags().StringVar(&fy, "fy", "", "financial year, YYYY-YY (e.g. 2026-27)")
	c.Flags().BoolVar(&withHeader, "with-header", false, "also fetch the report header (legal name, liability code) first, as the page does")
	_ = c.MarkFlagRequired("fy")
	return c
}
