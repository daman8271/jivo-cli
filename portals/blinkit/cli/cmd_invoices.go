package main

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

const invoicesReportType = "Invoices Excel"

func newInvoicesCmd(app *App) *cobra.Command {
	inv := &cobra.Command{
		Use:   "invoices",
		Short: "JIVO invoices against POs (via the shared report queue)",
	}
	inv.AddCommand(
		newInvoicesReportsCmd(app),
		newInvoicesDownloadCmd(app),
		newInvoicesDeferredCmd(app, "summary", "invoice-summary list/detail feed"),
		newInvoicesDeferredCmd(app, "detail", "per-invoice document/detail feed"),
	)
	return inv
}

func newInvoicesReportsCmd(app *App) *cobra.Command {
	var limit int
	c := &cobra.Command{
		Use:   "reports",
		Short: "List 'Invoices Excel' rows in the report queue (proven read)",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runReportsList(app, invoicesReportType, "", limit)
		},
	}
	c.Flags().IntVar(&limit, "limit", 0, "max rows (0 = all)")
	return c
}

func newInvoicesDownloadCmd(app *App) *cobra.Command {
	var out string
	c := &cobra.Command{
		Use:   "download <id>",
		Short: "Download a completed Invoices Excel by id (bulk_invoice_csv-<id>.csv)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return fmt.Errorf("bad report id %q", args[0])
			}
			return runReportDownload(app, id, out)
		},
	}
	c.Flags().StringVar(&out, "out", "", "output CSV path")
	return c
}

func newInvoicesDeferredCmd(app *App, use, note string) *cobra.Command {
	return &cobra.Command{
		Use:   use,
		Short: "[DEFERRED] " + note + " — path to confirm via live capture",
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.deferred("invoices "+use, note)
		},
	}
}
