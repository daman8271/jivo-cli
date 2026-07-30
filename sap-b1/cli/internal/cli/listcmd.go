package cli

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/errs"
)

// openDocumentFilter is how the Service Layer expresses "open document", and
// the ONLY spelling it accepts.
//
// The Service Layer property is DocumentStatus, with values 'bost_Open' /
// 'bost_Close'. DocStatus (values 'O'/'C') is the HANA COLUMN name, and the
// Service Layer rejects it outright — a $select or $filter naming it fails the
// whole request with "Property 'DocStatus' of 'Document' is invalid", so
// `orders list` and `invoices list` returned nothing but an error against real
// SAP. Both the default $select and the --open filter of those two commands
// depend on this constant; do not reintroduce the column name.
const openDocumentFilter = "DocumentStatus eq 'bost_Open'"

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
	cmd.Flags().BoolVar(&lf.count, "count", false, "print only the server-side total row count: one GET, $top=0 with $inlinecount=allpages, no rows fetched (--select/--orderby/--skip/--top/--all do not apply)")
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

	filter := combineFilters(extraFilter, lf.filter)
	c := client.New(cfg)
	ctx := cmd.Context()
	out := cmd.OutOrStdout()

	// --count is a question about the SET, so it is its own request shape: one
	// GET, $top=0, $inlinecount=allpages, and no rows.
	//
	// It used to reuse the row path, which meant `sapb1 query BusinessPartners
	// --count` asked for $top=20 with the command's full $select and pulled
	// twenty complete SAP documents across the wire to print a single number —
	// and with --all it walked up to 200 pages of them for the same one number,
	// since the total always came from the first page's odata.count anyway.
	if lf.count {
		res, err := c.Query(ctx, entitySet, client.QueryOptions{Filter: filter, CountOnly: true})
		if err != nil {
			return err
		}
		if !res.CountKnown {
			// Never fall back to len(rows): a count-only request holds no rows,
			// so that fallback would print 0 and call it the total. A refusal is
			// recoverable; a confident wrong number is not.
			return &errs.APIError{Msg: fmt.Sprintf(
				"the Service Layer did not return a server-side total (odata.count) for %s — "+
					"refusing to print a row tally in its place; re-run without --count and count the rows you get, "+
					"or narrow the request with --filter", entitySet)}
		}
		return renderCount(out, res, cfg.JSON)
	}

	opts := client.QueryOptions{
		Select:   sel,
		Filter:   filter,
		OrderBy:  ob,
		Skip:     lf.skip,
		PageSize: lf.pageSize,
	}

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

	switch {
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
