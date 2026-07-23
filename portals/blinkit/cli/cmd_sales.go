package main

import (
	"fmt"
	"net/http"
	"time"

	"github.com/spf13/cobra"
)

func newSalesCmd(app *App) *cobra.Command {
	sales := &cobra.Command{
		Use:   "sales",
		Short: "Secondary sales / sell-out",
	}
	sales.AddCommand(newSalesTableCmd(app), newSalesPullCmd(app))
	return sales
}

func newSalesTableCmd(app *App) *cobra.Command {
	var from, to, body string
	var offset, limit int
	c := &cobra.Command{
		Use:   "table",
		Short: "On-screen sell-out grid (PURE READ, recommended default)",
		RunE: func(cmd *cobra.Command, args []string) error {
			now := time.Now()
			if from == "" || to == "" {
				df, dt := defaultSalesRange(now)
				if from == "" {
					from = df
				}
				if to == "" {
					to = dt
				}
			}
			path := fmt.Sprintf("/v1/get-sales-details/?offset=%d&limit=%d", offset, limit)
			var payload []byte
			if body != "" {
				payload = []byte(body)
			} else {
				payload = []byte(fmt.Sprintf(`{"filters":{"created_at__gte":%q,"created_at__lte":%q},"order_by":[]}`, from, to))
			}
			// get-sales-details is a proven {status,data} envelope endpoint.
			data, err := app.Client.do(http.MethodPost, app.cfg.Base+path, payload)
			return app.emit("sales table", path, data, err)
		},
	}
	c.Flags().StringVar(&from, "from", "", "window start YYYY-MM-DD (default 1st of month IST)")
	c.Flags().StringVar(&to, "to", "", "window end YYYY-MM-DD (default T-1 IST)")
	c.Flags().IntVar(&offset, "offset", 0, "pagination offset")
	c.Flags().IntVar(&limit, "limit", 50, "page size")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body (overrides --from/--to)")
	return c
}

func newSalesPullCmd(app *App) *cobra.Command {
	var from, to, out, timeout string
	var export, yesExport bool
	c := &cobra.Command{
		Use:   "pull",
		Short: "[EXPORT] generate → poll → download the per-date Sales Details CSV",
		Long: `Generate the Sales Details export, poll the queue, and download the CSV.

SIDE-EFFECT: this enqueues a report and emails a copy to the account owner, so
it is gated behind --export. In --agent mode it also requires --yes-export.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runExportPull(app, exportPull{
				kind: "sales", from: from, to: to, out: out,
				timeout: timeout, export: export, yesExport: yesExport,
			})
		},
	}
	c.Flags().StringVar(&from, "from", "", "window start YYYY-MM-DD (default 1st of month IST)")
	c.Flags().StringVar(&to, "to", "", "window end YYYY-MM-DD (default T-1 IST)")
	c.Flags().StringVar(&out, "out", "", "output CSV path")
	c.Flags().StringVar(&timeout, "timeout", "3m", "max wait for the async report")
	c.Flags().BoolVar(&export, "export", false, "opt in to the side-effecting export (required)")
	c.Flags().BoolVar(&yesExport, "yes-export", false, "confirm the export in --agent mode")
	return c
}

type exportPull struct {
	kind      string // sales | soh
	from, to  string
	out       string
	timeout   string
	export    bool
	yesExport bool
}

// runExportPull is the shared sanctioned generate→poll→download flow for the
// only two side-effecting reads permitted (sales + soh).
func runExportPull(app *App, p exportPull) error {
	if !p.export {
		return fmt.Errorf("%s pull is a side-effecting export (emails the account owner) — pass --export to proceed, or use the pure-read alternatives", p.kind)
	}
	if app.Agent && !p.yesExport {
		return fmt.Errorf("%s pull emails the account owner; in --agent mode pass --yes-export to confirm", p.kind)
	}
	timeout := 3 * time.Minute
	if p.timeout != "" {
		d, err := time.ParseDuration(p.timeout)
		if err != nil {
			return fmt.Errorf("bad --timeout %q: %w", p.timeout, err)
		}
		timeout = d
	}

	now := time.Now()
	var id int
	var err error
	switch p.kind {
	case "sales":
		if p.from == "" || p.to == "" {
			df, dt := defaultSalesRange(now)
			if p.from == "" {
				p.from = df
			}
			if p.to == "" {
				p.to = dt
			}
		}
		if p.out == "" {
			p.out = fmt.Sprintf("blinkit-sales-%s_%s.csv", p.from, p.to)
		}
		app.logf("generating Sales Details report %s → %s ...", p.from, p.to)
		id, err = app.Client.GenerateSales(p.from, p.to)
	case "soh":
		if p.out == "" {
			p.out = fmt.Sprintf("blinkit-soh-%s.csv", today(now))
		}
		app.logf("generating SOH snapshot report ...")
		id, err = app.Client.GenerateSOH()
	default:
		return fmt.Errorf("unknown export kind %q", p.kind)
	}
	if err != nil {
		return app.emitError(p.kind+" pull", "/v1/reports/"+p.kind+"-details-excel/", err)
	}

	app.logf("request_id=%d, polling (timeout %s) ...", id, timeout)
	if _, err := app.Client.WaitForReport(id, timeout, 3*time.Second); err != nil {
		return app.emitError(p.kind+" pull", "poll", err)
	}
	url, err := app.Client.DownloadURL(id)
	if err != nil {
		return app.emitError(p.kind+" pull", "download-url", err)
	}
	n, err := app.Client.DownloadTo(url, p.out)
	if err != nil {
		return app.emitError(p.kind+" pull", "download", err)
	}
	if app.JSON || app.Agent {
		return app.emitValue(p.kind+" pull", "/v1/reports/"+p.kind+"-details-excel/",
			map[string]any{"request_id": id, "out": p.out, "bytes": n}, 1)
	}
	fmt.Printf("✓ saved %s (%d bytes) from report #%d\n", p.out, n, id)
	return nil
}
