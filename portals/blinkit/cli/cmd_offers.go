package main

import (
	"fmt"
	"net/url"

	"github.com/spf13/cobra"
)

func newOffersCmd(app *App) *cobra.Command {
	offers := &cobra.Command{
		Use:   "offers",
		Short: "Consumer offers / brand-funded promotions (Brand Fund)",
	}
	offers.AddCommand(
		newOffersSummaryCmd(app),
		newPOFacetCmd(app, "cities", "Brand-fund city reference list", "/api/attributes/v1/brands-fund/cities/?active=true&is_frontend=true"),
		newOffersHistoryCmd(app),
		newOffersSheetCmd(app),
		newOffersSheetRowsCmd(app),
		newOffersBundleSheetCmd(app),
		newOffersBundleSheetRowsCmd(app),
		newPOFacetCmd(app, "jobs", "Bulk-upload job status list", "/api/v1/bulk-upload-jobs/"),
	)
	return offers
}

func newOffersSummaryCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "summary",
		Short: "Spends summary cards (Total Spend + Unique Products)",
		RunE: func(cmd *cobra.Command, args []string) error {
			path := "/api/attributes/v1/brands-fund-summary/view/?manufacturer_id__in=" + url.QueryEscape(app.ManufID)
			return app.getJSON("offers summary", path)
		},
	}
}

func newOffersHistoryCmd(app *App) *cobra.Command {
	var from, to, state string
	var limit, offset int
	c := &cobra.Command{
		Use:   "history",
		Short: "Single-offer upload history",
		RunE: func(cmd *cobra.Command, args []string) error {
			q := url.Values{}
			q.Set("offset", fmt.Sprintf("%d", offset))
			q.Set("limit", fmt.Sprintf("%d", limit))
			q.Set("manufacturer_id__in", app.ManufID)
			q.Set("upload_source", "BRAND")
			if from != "" {
				q.Set("install_ts__gte", from)
			}
			if to != "" {
				q.Set("install_ts__lte", to)
			}
			if state != "" {
				q.Set("state__in", state)
			}
			return app.getJSON("offers history", "/api/attributes/v1/brands-sheets/?"+q.Encode())
		},
	}
	c.Flags().StringVar(&from, "from", "", "install_ts__gte")
	c.Flags().StringVar(&to, "to", "", "install_ts__lte")
	c.Flags().StringVar(&state, "state", "", "state__in filter")
	c.Flags().IntVar(&limit, "limit", 20, "page size")
	c.Flags().IntVar(&offset, "offset", 0, "pagination offset")
	return c
}

func newOffersSheetCmd(app *App) *cobra.Command {
	var row, limit int
	c := &cobra.Command{
		Use:   "sheet <sheetId>",
		Short: "Single offer sheet — row-wise detail",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			q := url.Values{}
			q.Set("sheet_id", args[0])
			q.Set("row_number", fmt.Sprintf("%d", row))
			q.Set("limit", fmt.Sprintf("%d", limit))
			return app.getJSON("offers sheet", "/api/attributes/v1/brands-fund/get/?"+q.Encode())
		},
	}
	c.Flags().IntVar(&row, "row", 0, "row_number")
	c.Flags().IntVar(&limit, "limit", 20, "page size")
	return c
}

func newOffersSheetRowsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "sheet-rows <sheetId>",
		Short: "Single offer sheet — row list",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			path := "/api/attributes/v1/brands-fund/get-sheet-rows/?sheet_id=" + url.QueryEscape(args[0])
			return app.getJSON("offers sheet-rows", path)
		},
	}
}

func newOffersBundleSheetCmd(app *App) *cobra.Command {
	var row, limit int
	c := &cobra.Command{
		Use:   "bundle-sheet <sheetId>",
		Short: "Bundle offer sheet — row-wise detail",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			q := url.Values{}
			q.Set("sheet_id", args[0])
			q.Set("row_number", fmt.Sprintf("%d", row))
			q.Set("limit", fmt.Sprintf("%d", limit))
			return app.getJSON("offers bundle-sheet", "/api/bundlesandcombos/v1/bundles_and_combos_approval/brand-fund/?"+q.Encode())
		},
	}
	c.Flags().IntVar(&row, "row", 0, "row_number")
	c.Flags().IntVar(&limit, "limit", 20, "page size")
	return c
}

func newOffersBundleSheetRowsCmd(app *App) *cobra.Command {
	var limit, offset int
	c := &cobra.Command{
		Use:   "bundle-sheet-rows <sheetId>",
		Short: "Bundle offer sheet — row list",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			q := url.Values{}
			q.Set("sheet_id", args[0])
			q.Set("limit", fmt.Sprintf("%d", limit))
			q.Set("offset", fmt.Sprintf("%d", offset))
			return app.getJSON("offers bundle-sheet-rows", "/api/bundlesandcombos/v1/bundles_and_combos_approval/get-sheet-rows/?"+q.Encode())
		},
	}
	c.Flags().IntVar(&limit, "limit", 20, "page size")
	c.Flags().IntVar(&offset, "offset", 0, "pagination offset")
	return c
}
