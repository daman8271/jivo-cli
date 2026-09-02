package main

import (
	"github.com/spf13/cobra"
)

// masters — the portal's own dropdown tables (return types, financial years,
// months, quarters, states). Cheap, stable reads; useful for validating a
// --period or --fy before spending a session on a real query.

func init() { registerSection(newMastersCmd) }

func newMastersCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "masters",
		Short: "Portal master data: return types, financial years, months, quarters, states",
	}
	c.AddCommand(
		mastersLeaf(app, "forms", "Return types and their filing day (GSTR-1, 3B, 9, …)", epMasterForms),
		mastersLeaf(app, "fy", "Financial years the portal offers", epMasterFY),
		mastersLeaf(app, "states", "State list", epMasterStates),
		mastersFYLeaf(app, "months", "Months of a financial year, with their MMYYYY codes", epMasterMonths),
		mastersFYLeaf(app, "quarters", "Quarters of a financial year", epMasterQuarters),
		mastersFYLeaf(app, "halfyears", "Half-years of a financial year", epMasterHalves),
	)
	return c
}

// mastersLeaf is a plain read with no parameters.
func mastersLeaf(app *App, use, short, endpoint string) *cobra.Command {
	return &cobra.Command{
		Use:   use,
		Short: short,
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			return app.read("masters "+use, reg, endpoint, nil, nil, nil)
		},
	}
}

// mastersFYLeaf is a read whose path carries a financial year. The FY is parsed
// before the request, so a typo costs nothing.
func mastersFYLeaf(app *App, use, short, endpoint string) *cobra.Command {
	var fy string
	c := &cobra.Command{
		Use:   use,
		Short: short,
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			if fy == "" {
				return errUsage("--fy is required (e.g. --fy 2026-27)")
			}
			if _, err := parseFY(fy); err != nil {
				return err
			}
			return app.read("masters "+use, reg, endpoint, map[string]string{"fy": fy}, nil, nil)
		},
	}
	c.Flags().StringVar(&fy, "fy", "", "financial year, YYYY-YY (e.g. 2026-27)")
	return c
}
