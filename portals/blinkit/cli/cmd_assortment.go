package main

import (
	"github.com/spf13/cobra"
)

func newAssortmentCmd(app *App) *cobra.Command {
	as := &cobra.Command{
		Use:   "assortment",
		Short: "Listed / active SKUs (entity-tab gate + shared queue)",
	}
	as.AddCommand(
		newPOFacetCmd(app, "tabs", "Entity-tab gate check for entity 1117", "/v1/get-entity-tabs/"),
		newAssortmentReportsCmd(app),
		&cobra.Command{
			Use:   "list",
			Short: "[DEFERRED] assortment data feed — path to confirm via live capture",
			RunE: func(cmd *cobra.Command, args []string) error {
				return app.deferred("assortment list", "assortment data feed (lazy-loaded chunk, not in bundle)")
			},
		},
	)
	return as
}

func newAssortmentReportsCmd(app *App) *cobra.Command {
	var limit int
	c := &cobra.Command{
		Use:   "reports",
		Short: "Generic report-queue view (no assortment report type observed yet)",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runReportsList(app, "", "", limit)
		},
	}
	c.Flags().IntVar(&limit, "limit", 0, "max rows (0 = all)")
	return c
}
