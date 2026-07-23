package main

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/spf13/cobra"
)

func newReportsCmd(app *App) *cobra.Command {
	reports := &cobra.Command{
		Use:   "reports",
		Short: "Async report queue (shared: Sales/SOH/Invoices/Scorecard/PO)",
	}
	reports.AddCommand(
		newReportsListCmd(app),
		newReportsDownloadCmd(app),
		newReportsURLCmd(app),
	)
	return reports
}

func newReportsListCmd(app *App) *cobra.Command {
	var typeSub, state string
	var limit int
	c := &cobra.Command{
		Use:   "list",
		Short: "List the report-request queue (newest first)",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runReportsList(app, typeSub, state, limit)
		},
	}
	c.Flags().StringVar(&typeSub, "type", "", "case-insensitive substring filter on report type")
	c.Flags().StringVar(&state, "state", "", "filter by state (e.g. success, failed)")
	c.Flags().IntVar(&limit, "limit", 0, "max rows (0 = all)")
	return c
}

// runReportsList is shared by reports/soh/invoices/scorecard queue views.
func runReportsList(app *App, typeSub, state string, limit int) error {
	all, err := app.Client.ListReports()
	if err != nil {
		return app.emitError("reports list", "/v1/report-requests/", err)
	}
	out := filterReports(all, typeSub, state, limit)
	if app.JSON || app.Agent {
		return app.emitValue("reports list", "/v1/report-requests/", out, len(out))
	}
	fmt.Printf("%-10s  %-28s  %-10s  %s\n", "ID", "TYPE", "STATE", "CREATED")
	for _, r := range out {
		fmt.Printf("%-10d  %-28s  %-10s  %s\n", r.ID, r.Type, r.State, r.CreatedAt)
	}
	return nil
}

func filterReports(in []Report, typeSub, state string, limit int) []Report {
	var out []Report
	for _, r := range in {
		if typeSub != "" && !strings.Contains(strings.ToLower(r.Type), strings.ToLower(typeSub)) {
			continue
		}
		if state != "" && !strings.EqualFold(r.State, state) {
			continue
		}
		out = append(out, r)
		if limit > 0 && len(out) >= limit {
			break
		}
	}
	return out
}

func newReportsDownloadCmd(app *App) *cobra.Command {
	var out string
	c := &cobra.Command{
		Use:   "download <id>",
		Short: "Mint a presigned URL for a completed report and download it",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return fmt.Errorf("bad report id %q", args[0])
			}
			return runReportDownload(app, id, out)
		},
	}
	c.Flags().StringVar(&out, "out", "", "output file path (default ./report-<id>.csv)")
	return c
}

// runReportDownload is shared by reports/soh/invoices/scorecard download.
func runReportDownload(app *App, id int, out string) error {
	if out == "" {
		out = fmt.Sprintf("report-%d.csv", id)
	}
	url, err := app.Client.DownloadURL(id)
	if err != nil {
		return app.emitError("reports download", "/v1/report-requests/download//{id}/", err)
	}
	n, err := app.Client.DownloadTo(url, out)
	if err != nil {
		return app.emitError("reports download", url, err)
	}
	if app.JSON || app.Agent {
		return app.emitValue("reports download", "/v1/report-requests/download//{id}/",
			map[string]any{"id": id, "out": out, "bytes": n}, 1)
	}
	fmt.Printf("✓ saved %s (%d bytes) from report #%d\n", out, n, id)
	return nil
}

func newReportsURLCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "url <id>",
		Short: "Print a freshly-minted presigned download URL (no fetch)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return fmt.Errorf("bad report id %q", args[0])
			}
			url, err := app.Client.DownloadURL(id)
			if err != nil {
				return app.emitError("reports url", "/v1/report-requests/download//{id}/", err)
			}
			if app.JSON || app.Agent {
				return app.emitValue("reports url", "/v1/report-requests/download//{id}/",
					map[string]any{"id": id, "download_url": url}, 1)
			}
			fmt.Println(url)
			return nil
		},
	}
}
