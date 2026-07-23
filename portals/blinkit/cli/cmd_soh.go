package main

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/spf13/cobra"
)

const sohReportType = "SOH Details Excel"

func newSOHCmd(app *App) *cobra.Command {
	soh := &cobra.Command{
		Use:   "soh",
		Short: "Stock-on-Hand (inventory) reports",
	}
	soh.AddCommand(
		newSOHQueueCmd(app),
		newSOHLatestCmd(app),
		newSOHDownloadCmd(app),
		newSOHPullCmd(app),
	)
	return soh
}

func newSOHQueueCmd(app *App) *cobra.Command {
	var limit int
	c := &cobra.Command{
		Use:   "queue",
		Short: "List SOH rows in the report queue (pure read, no generate)",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runReportsList(app, sohReportType, "", limit)
		},
	}
	c.Flags().IntVar(&limit, "limit", 0, "max rows (0 = all)")
	return c
}

func newSOHLatestCmd(app *App) *cobra.Command {
	var out string
	c := &cobra.Command{
		Use:   "latest",
		Short: "Download the newest successful SOH report (no generate)",
		RunE: func(cmd *cobra.Command, args []string) error {
			all, err := app.Client.ListReports()
			if err != nil {
				return app.emitError("soh latest", "/v1/report-requests/", err)
			}
			var pick *Report
			for i := range all {
				r := all[i]
				if strings.Contains(strings.ToLower(r.Type), "soh") &&
					isSuccessState(r.State) {
					pick = &r
					break // newest-first
				}
			}
			if pick == nil {
				return fmt.Errorf("no successful SOH report found in the queue — enqueue one with `soh pull --export`")
			}
			return runReportDownload(app, pick.ID, out)
		},
	}
	c.Flags().StringVar(&out, "out", "", "output CSV path (default ./report-<id>.csv)")
	return c
}

func newSOHDownloadCmd(app *App) *cobra.Command {
	var out string
	c := &cobra.Command{
		Use:   "download <id>",
		Short: "Download a specific SOH report by id",
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

func newSOHPullCmd(app *App) *cobra.Command {
	var out, timeout string
	var export, yesExport bool
	c := &cobra.Command{
		Use:   "pull",
		Short: "[EXPORT] generate → poll → download a live SOH snapshot CSV",
		Long:  "SIDE-EFFECT: enqueues a report and emails a copy to the account owner. Gated behind --export (and --yes-export in --agent mode).",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runExportPull(app, exportPull{
				kind: "soh", out: out, timeout: timeout,
				export: export, yesExport: yesExport,
			})
		},
	}
	c.Flags().StringVar(&out, "out", "", "output CSV path")
	c.Flags().StringVar(&timeout, "timeout", "3m", "max wait for the async report")
	c.Flags().BoolVar(&export, "export", false, "opt in to the side-effecting export (required)")
	c.Flags().BoolVar(&yesExport, "yes-export", false, "confirm the export in --agent mode")
	return c
}

func isSuccessState(s string) bool {
	switch strings.ToLower(s) {
	case "success", "completed", "done":
		return true
	}
	return false
}
