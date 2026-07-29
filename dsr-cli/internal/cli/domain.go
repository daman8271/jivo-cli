package cli

// Shared helpers for the high-level domain commands (retailers, salespersons,
// beats, sales, attendance, …). Every domain command file uses these so they
// stay consistent and compile together in one package.
//
// CONVENTIONS for domain command files (internal/cli/<subsystem>.go):
//   - one exported constructor per subsystem: newXxxCmd(app *App) *cobra.Command
//   - self-register in init(): func init() { register(newXxxCmd) }
//   - a parent cobra.Command with sub-commands (list/get/count/…)
//   - ALL package-level identifiers PREFIXED with the subsystem to avoid
//     collisions across files (e.g. retailersListCmd, salesTopSQL)
//   - build SQL with the fXxx / fWhere helpers below; never string-concat raw
//     user input — pass values through db.Lit / integer flags
//   - read-only only: app.DB.Query (never Exec); the guard blocks writes anyway
//   - apply fLive(...) unless --include-deleted; bound dates with the sentinels
//     in mind (1899-12-30 etc.)

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"dsr/internal/db"
)

// domFilters holds the common cross-domain filter flags. Add only the ones a
// command needs via addDomFilters(cmd, &f, "date","person",...).
type domFilters struct {
	From, To       string
	Person         int
	Retailer       int
	Beat           int
	Item           int
	State          string
	Zone           string
	IncludeDeleted bool
}

// addDomFilters registers the requested subset of shared flags on c.
func addDomFilters(c *cobra.Command, f *domFilters, which ...string) {
	want := map[string]bool{}
	for _, w := range which {
		want[w] = true
	}
	fl := c.Flags()
	if want["date"] {
		fl.StringVar(&f.From, "from", "", "start date, inclusive (e.g. 2026-07-01)")
		fl.StringVar(&f.To, "to", "", "end date, exclusive (e.g. 2026-08-01)")
	}
	if want["person"] {
		fl.IntVar(&f.Person, "salesperson", 0, "filter by salesperson ID (tbl_salesperson.ID)")
	}
	if want["retailer"] {
		fl.IntVar(&f.Retailer, "retailer", 0, "filter by retailer Id (tbl_retailers.Id)")
	}
	if want["beat"] {
		fl.IntVar(&f.Beat, "beat", 0, "filter by beat id (tbl_beats.beatId)")
	}
	if want["item"] {
		fl.IntVar(&f.Item, "item", 0, "filter by item Id (tbl_item.Id)")
	}
	if want["state"] {
		fl.StringVar(&f.State, "state", "", "filter by state (id or name, per column)")
	}
	if want["zone"] {
		fl.StringVar(&f.Zone, "zone", "", "filter by zone (id or name, per column)")
	}
	if want["deleted"] {
		fl.BoolVar(&f.IncludeDeleted, "include-deleted", false, "include soft-deleted rows")
	}
}

// fEqInt returns "col = <v>" (empty if v == 0, the DSR "unset" convention).
func fEqInt(col string, v int) string {
	if v == 0 {
		return ""
	}
	return fmt.Sprintf("%s = %d", col, v)
}

// fEqStr returns "col = '<v>'" safely quoted (empty if v == "").
func fEqStr(col, v string) string {
	if strings.TrimSpace(v) == "" {
		return ""
	}
	return col + " = " + db.Lit(v)
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

// fLive returns the soft-delete filter for a table (prefix is "" or "alias.").
func fLive(prefix string, includeDeleted bool) string {
	if includeDeleted {
		return ""
	}
	return fmt.Sprintf("ISNULL(%sdeleted, 0) = 0", prefix)
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

// inr formats a rupee amount with Indian digit grouping (₹ + crore for big sums).
func inr(v float64) string {
	neg := v < 0
	if neg {
		v = -v
	}
	whole := int64(v)
	frac := fmt.Sprintf("%.2f", v-float64(whole))[1:] // ".xx"
	s := groupIndian(whole)
	out := "₹" + s + frac
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
	head := s[:len(s)-3]
	tail := s[len(s)-3:]
	var parts []string
	for len(head) > 2 {
		parts = append([]string{head[len(head)-2:]}, parts...)
		head = head[:len(head)-2]
	}
	parts = append([]string{head}, parts...)
	return strings.Join(parts, ",") + "," + tail
}
