package cli

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/errs"
)

// listFlags backs the common --filter/--select/--top/--skip/--orderby/--all
// flag shape shared by orders/invoices/items/partners `list` subcommands and
// by the generic `query` command.
type listFlags struct {
	filter   string
	sel      string
	top      int
	skip     int
	orderby  string
	all      bool
	pageSize int
	count    bool
}

func addListFlags(cmd *cobra.Command, lf *listFlags, defaultTop int) {
	cmd.Flags().StringVar(&lf.filter, "filter", "", "raw OData $filter expression, e.g. \"DocTotal gt 1000\"")
	cmd.Flags().StringVar(&lf.sel, "select", "", "comma-separated fields to return, e.g. \"DocEntry,DocNum,CardName\"")
	cmd.Flags().IntVar(&lf.top, "top", defaultTop, "max rows to return (ignored with --all)")
	cmd.Flags().IntVar(&lf.skip, "skip", 0, "rows to skip (pagination offset)")
	cmd.Flags().StringVar(&lf.orderby, "orderby", "", "raw OData $orderby expression, e.g. \"DocDate desc\"")
	cmd.Flags().BoolVar(&lf.all, "all", false, fmt.Sprintf("paginate through ALL matching rows via odata.nextLink (capped at %d pages)", client.MaxPages))
	cmd.Flags().IntVar(&lf.pageSize, "page-size", 0, "rows per page while paginating (sent as Prefer: odata.maxpagesize); server default is 20")
	cmd.Flags().BoolVar(&lf.count, "count", false, "print only the server-side total row count ($inlinecount=allpages)")
}

// combineFilters ANDs together any non-empty filter fragments, parenthesizing
// each so a user-supplied --filter can't accidentally change precedence of
// a command's built-in filter (e.g. --open on `orders list`).
func combineFilters(parts ...string) string {
	var nonEmpty []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			nonEmpty = append(nonEmpty, "("+p+")")
		}
	}
	return strings.Join(nonEmpty, " and ")
}

// runList resolves config, opens a client, runs the query (paginated via
// --all or a single page via --top), and renders the result. entitySet is
// the OData EntitySet name. extraFilter is ANDed in front of the user's
// --filter (used for e.g. `--open`, `--customers`, `--low-stock`).
// defaultSelect/defaultOrderBy are used only when the user didn't pass
// --select/--orderby.
func runList(cmd *cobra.Command, entitySet string, lf listFlags, extraFilter, defaultSelect, defaultOrderBy string) error {
	cfg, err := loadConfig(cmd)
	if err != nil {
		return err
	}
	if cfg.JSON && cfg.CSV {
		return &errs.UsageError{Msg: "--json and --csv are mutually exclusive"}
	}
	if err := cfg.ValidateConnection(); err != nil {
		return err
	}
	if err := cfg.ValidateCompanyDB(); err != nil {
		return err
	}

	sel := lf.sel
	if sel == "" {
		sel = defaultSelect
	}
	ob := lf.orderby
	if ob == "" {
		ob = defaultOrderBy
	}

	opts := client.QueryOptions{
		Select:      sel,
		Filter:      combineFilters(extraFilter, lf.filter),
		OrderBy:     ob,
		Skip:        lf.skip,
		PageSize:    lf.pageSize,
		InlineCount: lf.count,
	}

	c := client.New(cfg)
	ctx := cmd.Context()

	var res *client.QueryResult
	if lf.all {
		res, err = c.QueryAll(ctx, entitySet, opts)
	} else {
		opts.Top = lf.top
		res, err = c.Query(ctx, entitySet, opts)
	}
	if err != nil {
		return err
	}

	out := cmd.OutOrStdout()
	switch {
	case lf.count:
		return renderCount(out, res, cfg.JSON)
	case cfg.CSV:
		if err := renderCSV(out, res.Value, parseFieldList(sel)); err != nil {
			return err
		}
		if res.Capped {
			fmt.Fprintf(cmd.ErrOrStderr(), "(note: stopped after %d pages — more results may exist; narrow your --filter)\n", client.MaxPages)
		}
		return nil
	default:
		return renderResult(out, res, cfg.JSON, parseFieldList(sel))
	}
}
