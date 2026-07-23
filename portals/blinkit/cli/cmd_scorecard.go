package main

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/spf13/cobra"
)

func newScorecardCmd(app *App) *cobra.Command {
	sc := &cobra.Command{
		Use:   "scorecard",
		Short: "Performance metrics (fill rate, potential loss) via report queue",
	}
	sc.AddCommand(
		newScorecardReportsCmd(app),
		newScorecardDownloadCmd(app),
		newScorecardDeferredCmd(app, "summary", "scorecard-summary panel feed (ScoreCard chunk)"),
		newScorecardDeferredCmd(app, "fill-rate", "fill-rate panel feed (ScoreCard chunk)"),
	)
	return sc
}

func newScorecardReportsCmd(app *App) *cobra.Command {
	var limit int
	c := &cobra.Command{
		Use:   "reports",
		Short: "List 'Scorecard Details Excel' / 'Top 5 Potential Loss' rows (proven read)",
		RunE: func(cmd *cobra.Command, args []string) error {
			all, err := app.Client.ListReports()
			if err != nil {
				return app.emitError("scorecard reports", "/v1/report-requests/", err)
			}
			var out []Report
			for _, r := range all {
				t := strings.ToLower(r.Type)
				if strings.Contains(t, "scorecard") || strings.Contains(t, "potential loss") {
					out = append(out, r)
					if limit > 0 && len(out) >= limit {
						break
					}
				}
			}
			if app.JSON || app.Agent {
				return app.emitValue("scorecard reports", "/v1/report-requests/", out, len(out))
			}
			fmt.Printf("%-10s  %-28s  %-10s  %s\n", "ID", "TYPE", "STATE", "CREATED")
			for _, r := range out {
				fmt.Printf("%-10d  %-28s  %-10s  %s\n", r.ID, r.Type, r.State, r.CreatedAt)
			}
			return nil
		},
	}
	c.Flags().IntVar(&limit, "limit", 0, "max rows (0 = all)")
	return c
}

func newScorecardDownloadCmd(app *App) *cobra.Command {
	var out string
	c := &cobra.Command{
		Use:   "download <id>",
		Short: "Download a completed scorecard report by id",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return fmt.Errorf("bad report id %q", args[0])
			}
			return runReportDownload(app, id, out)
		},
	}
	c.Flags().StringVar(&out, "out", "", "output file path")
	return c
}

func newScorecardDeferredCmd(app *App, use, note string) *cobra.Command {
	return &cobra.Command{
		Use:   use,
		Short: "[DEFERRED] " + note + " — path to confirm via live capture",
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.deferred("scorecard "+use, note)
		},
	}
}
