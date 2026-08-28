package cli

// Shared helpers for ary's domain commands (sales, purchases, stock, audit, …).
//
// CONVENTIONS for domain command files (internal/cli/<subsystem>.go):
//   - one constructor per subsystem: newXxxCmd(app *App) *cobra.Command
//   - self-register in init(): func init() { register(newXxxCmd) }
//   - a parent cobra.Command with sub-commands (list/get/count/…)
//   - ALL package-level identifiers PREFIXED with the subsystem name
//   - build SQL with the fXxx / fWhere helpers; never concatenate raw user
//     input — pass values through db.Lit or typed flags
//   - read-only only: app.DB.Query (never Exec); the guard blocks writes anyway
//
// FusionERP8 facts these helpers encode (verified live 2026-08-27, see
// study/specs/schema-notes.md):
//   - every voucher table is Header/Detail keyed on SerialNumber (decimal)
//   - dates are smalldatetime; the "empty" sentinel is 1900-01-01
//   - SaleHeader has no cancel flag: all 1,088,607 rows are Status=2, no voids;
//     reversals are separate SaleReturn documents
//   - PurchaseHeader/TransactionMaster DO have IsDeleted — filter it
//   - Stock.Quantity is the system's own on-hand and equals
//     OP+Pur-PR-Sal+SR+Prod-Cons+TrIn-TrOut+Exc-Sho-Was on 104,221/104,221 rows

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"

	"ary/internal/db"
	"ary/internal/render"
)

// domFilters holds the common cross-domain filter flags.
type domFilters struct {
	From, To       string
	Warehouse      int
	Location       int
	Product        string
	Account        int
	Customer       string
	SalesPerson    int
	Search         string
	IncludeDeleted bool
	ActiveOnly     bool
}

// addDomFilters registers the requested subset of shared flags on c.
func addDomFilters(c *cobra.Command, f *domFilters, which ...string) {
	want := map[string]bool{}
	for _, w := range which {
		want[w] = true
	}
	fl := c.Flags()
	if want["date"] {
		fl.StringVar(&f.From, "from", "", "start date, inclusive (YYYY-MM-DD)")
		fl.StringVar(&f.To, "to", "", "end date, EXCLUSIVE (YYYY-MM-DD)")
	}
	if want["warehouse"] {
		fl.IntVar(&f.Warehouse, "warehouse", 0, "filter by WarehouseID (see `ary warehouses`)")
	}
	if want["location"] {
		fl.IntVar(&f.Location, "location", 0, "filter by LocationID (1=Ary HO, 15=Baru Sahib, 16=Bathinda)")
	}
	if want["product"] {
		fl.StringVar(&f.Product, "product", "", "filter by ProductID (e.g. 0CU7)")
	}
	if want["account"] {
		fl.IntVar(&f.Account, "account", 0, "filter by AccountID (see `ary accounts list`)")
	}
	if want["customer"] {
		fl.StringVar(&f.Customer, "customer", "", "filter by CustomerID")
	}
	if want["salesperson"] {
		fl.IntVar(&f.SalesPerson, "salesperson", 0, "filter by SalesPersonID (see `ary sales staff`)")
	}
	if want["search"] {
		fl.StringVar(&f.Search, "search", "", "case-insensitive substring match on the name")
	}
	if want["deleted"] {
		fl.BoolVar(&f.IncludeDeleted, "include-deleted", false, "include rows flagged IsDeleted")
	}
	if want["active"] {
		fl.BoolVar(&f.ActiveOnly, "active", false, "only rows with IsActive = 1")
	}
}

// fEqInt returns "col = <v>" (empty when v == 0, the "unset" convention).
func fEqInt(col string, v int) string {
	if v == 0 {
		return ""
	}
	return fmt.Sprintf("%s = %d", col, v)
}

// fEqStr returns "col = '<v>'" safely quoted (empty when v == "").
func fEqStr(col, v string) string {
	if strings.TrimSpace(v) == "" {
		return ""
	}
	return col + " = " + db.Lit(v)
}

// fLike returns a safely-quoted case-insensitive substring match.
func fLike(col, v string) string {
	if strings.TrimSpace(v) == "" {
		return ""
	}
	return col + " LIKE " + db.Lit("%"+v+"%")
}

// fDateGE / fDateLT build safely-quoted date-bound fragments.
func fDateGE(col, v string) string {
	if strings.TrimSpace(v) == "" {
		return ""
	}
	return col + " >= " + db.Lit(v)
}

func fDateLT(col, v string) string {
	if strings.TrimSpace(v) == "" {
		return ""
	}
	return col + " < " + db.Lit(v)
}

// fLive returns the IsDeleted filter for tables that have one ("" or "alias.").
func fLive(prefix string, includeDeleted bool) string {
	if includeDeleted {
		return ""
	}
	return fmt.Sprintf("ISNULL(%sIsDeleted, 0) = 0", prefix)
}

// fActive returns the IsActive filter, applied only when --active was passed.
func fActive(prefix string, activeOnly bool) string {
	if !activeOnly {
		return ""
	}
	return fmt.Sprintf("ISNULL(%sIsActive, 0) = 1", prefix)
}

// fWhere joins non-empty fragments with AND and prefixes " WHERE " (or "").
func fWhere(parts ...string) string {
	var nz []string
	for _, p := range parts {
		if strings.TrimSpace(p) != "" {
			nz = append(nz, p)
		}
	}
	if len(nz) == 0 {
		return ""
	}
	return " WHERE " + strings.Join(nz, " AND ")
}

// fAnd joins non-empty fragments with AND, WITHOUT the WHERE keyword — for
// appending to a query that already has a WHERE.
func fAnd(parts ...string) string {
	var nz []string
	for _, p := range parts {
		if strings.TrimSpace(p) != "" {
			nz = append(nz, p)
		}
	}
	if len(nz) == 0 {
		return ""
	}
	return " AND " + strings.Join(nz, " AND ")
}

// topN returns the effective TOP: the global --limit if set, else def.
func topN(app *App, def int) int {
	if app.Flags.Limit > 0 {
		return app.Flags.Limit
	}
	return def
}

// runSelect executes a read-only SELECT and renders it with the active options.
func runSelect(app *App, query string) error {
	ctx, cancel := app.Ctx()
	defer cancel()
	res, err := app.DB.Query(ctx, app.DBName(), query)
	if err != nil {
		return err
	}
	return app.Render(res)
}

// section is one labelled result inside a multi-part command (e.g. a bill:
// header + lines + payments).
type section struct {
	Name  string
	Query string
}

// runSections executes several SELECTs and renders them as one output: labelled
// tables in human mode, a single JSON object keyed by section name in --json.
func runSections(app *App, secs []section) error {
	ctx, cancel := app.Ctx()
	defer cancel()

	type part struct {
		name string
		res  *db.Result
	}
	parts := make([]part, 0, len(secs))
	for _, s := range secs {
		res, err := app.DB.Query(ctx, app.DBName(), s.Query)
		if err != nil {
			return err
		}
		parts = append(parts, part{s.Name, res})
	}

	if app.Flags.JSON || app.Flags.Compact {
		out := make(map[string]any, len(parts))
		for _, p := range parts {
			out[p.name] = render.Maps(p.res)
		}
		return render.WriteJSON(os.Stdout, out, app.Flags.Compact)
	}
	for i, p := range parts {
		if i > 0 {
			fmt.Fprintln(os.Stdout)
		}
		if !app.Flags.Quiet && !app.Flags.CSV {
			fmt.Fprintf(os.Stdout, "== %s ==\n", strings.ToUpper(p.name))
		}
		if err := app.Render(p.res); err != nil {
			return err
		}
	}
	return nil
}

// inr formats a rupee amount with Indian digit grouping (lakh/crore suffix).
func inr(v float64) string {
	neg := v < 0
	if neg {
		v = -v
	}
	whole := int64(v)
	frac := fmt.Sprintf("%.2f", v-float64(whole))[1:]
	out := "₹" + groupIndian(whole) + frac
	if v >= 1e7 {
		out += fmt.Sprintf(" (%.2f Cr)", v/1e7)
	} else if v >= 1e5 {
		out += fmt.Sprintf(" (%.2f L)", v/1e5)
	}
	if neg {
		out = "-" + out
	}
	return out
}

// groupIndian groups an integer with the Indian system (last 3, then pairs).
func groupIndian(n int64) string {
	s := fmt.Sprintf("%d", n)
	if len(s) <= 3 {
		return s
	}
	head, tail := s[:len(s)-3], s[len(s)-3:]
	var parts []string
	for len(head) > 2 {
		parts = append([]string{head[len(head)-2:]}, parts...)
		head = head[:len(head)-2]
	}
	parts = append([]string{head}, parts...)
	return strings.Join(parts, ",") + "," + tail
}
