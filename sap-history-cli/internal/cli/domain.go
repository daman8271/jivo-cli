package cli

// Shared helpers for saphist's domain commands (sales, purchases, ledger, …).
//
// CONVENTIONS for domain command files (internal/cli/<subsystem>.go):
//   - one constructor per subsystem: newXxxCmd(app *App) *cobra.Command
//   - self-register in init(): func init() { register(newXxxCmd) }
//   - a parent cobra.Command with sub-commands (summary/list/show/…)
//   - ALL package-level identifiers PREFIXED with the subsystem name
//   - build SQL with the fXxx / fWhere helpers; never concatenate raw user
//     input — pass values through db.Lit or typed flags
//   - a dated command runs through runBooks so it spans both books
//   - read-only only: app.DB.Query (never Exec); the guard blocks writes anyway
//
// SAP B1 facts these helpers encode (this is the SQL Server flavour of the
// same schema the live HANA system uses, so the definitions in the repo's
// CLAUDE.md still hold):
//
//   - Turnover = OINV(DocTotal - VatSum) minus ORIN(DocTotal - VatSum), by
//     DocDate, excluding cancelled. GST-inclusive figure = DocTotal.
//   - The cancel flag is CANCELED = 'N'/'Y' on documents, Canceled on payments
//     (SQL Server is case-insensitive, so one spelling works for both).
//   - DocStatus 'O' = open, 'C' = closed.
//   - Ledger balance = OCRD.Balance. POSITIVE = DEBIT (they owe JIVO),
//     NEGATIVE = CREDIT (JIVO owes them).
//   - Journal lines are JDT1 (Debit/Credit, RefDate), headed by OJDT.
//   - Branch = OBPL.BPLId; the "new" book has 6, the "old" book has none.

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"

	"saphist/internal/db"
	"saphist/internal/render"
)

// domFilters holds the common cross-domain filter flags.
type domFilters struct {
	From, To         string
	Year             int
	FY               int
	Party            string
	Item             string
	Branch           int
	Account          string
	Warehouse        string
	Search           string
	IncludeCancelled bool
	OpenOnly         bool
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
		fl.IntVar(&f.Year, "year", 0, "calendar year shorthand, e.g. 2016 (Jan-Dec)")
		fl.IntVar(&f.FY, "fy", 0, "Indian financial year shorthand: --fy 2016 means 2016-04-01 to 2017-04-01")
	}
	if want["party"] {
		fl.StringVar(&f.Party, "party", "", "filter by CardCode (exact)")
	}
	if want["item"] {
		fl.StringVar(&f.Item, "item", "", "filter by ItemCode (exact)")
	}
	if want["branch"] {
		fl.IntVar(&f.Branch, "branch", 0, "filter by BPLId (see `saphist branches`) — the 'new' book only")
	}
	if want["account"] {
		fl.StringVar(&f.Account, "account", "", "filter by G/L AcctCode (exact)")
	}
	if want["warehouse"] {
		fl.StringVar(&f.Warehouse, "warehouse", "", "filter by WhsCode (exact)")
	}
	if want["search"] {
		fl.StringVar(&f.Search, "search", "", "case-insensitive substring match on the name")
	}
	if want["cancelled"] {
		fl.BoolVar(&f.IncludeCancelled, "include-cancelled", false, "include cancelled documents (excluded by default)")
	}
	if want["open"] {
		fl.BoolVar(&f.OpenOnly, "open", false, "only documents still open (DocStatus = 'O')")
	}
}

// dates resolves --year / --fy into --from / --to and returns the effective
// range. Explicit --from/--to always win.
func (f *domFilters) dates() (string, string) {
	from, to := f.From, f.To
	switch {
	case from != "" || to != "":
	case f.FY > 0:
		from = fmt.Sprintf("%d-04-01", f.FY)
		to = fmt.Sprintf("%d-04-01", f.FY+1)
	case f.Year > 0:
		from = fmt.Sprintf("%d-01-01", f.Year)
		to = fmt.Sprintf("%d-01-01", f.Year+1)
	}
	return from, to
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

// fLive excludes cancelled documents unless --include-cancelled was passed.
// prefix is "" or an alias with a dot, e.g. "h.".
func fLive(prefix string, includeCancelled bool) string {
	if includeCancelled {
		return ""
	}
	return "ISNULL(" + prefix + "CANCELED, 'N') = 'N'"
}

// fOpen restricts to open documents when --open was passed.
func fOpen(prefix string, openOnly bool) string {
	if !openOnly {
		return ""
	}
	return prefix + "DocStatus = 'O'"
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

// fAnd joins non-empty fragments with AND, WITHOUT the WHERE keyword.
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

// runSelect executes one read-only SELECT against the single effective database.
func runSelect(app *App, query string) error {
	ctx, cancel := app.Ctx()
	defer cancel()
	res, err := app.DB.Query(ctx, app.DBName(), query)
	if err != nil {
		return err
	}
	return app.Render(res)
}

// runBooks is the workhorse for every dated command: it resolves which books
// cover [from, to), runs sqlFor(book) against each, and renders one result
// with a leading `book` column so the operator can always see which set of
// books a number came from.
//
// Rows are concatenated book by book, ordered within each book — a two-book
// "top 20" is therefore the top 20 of each, which is the honest answer for two
// separate ledgers rather than a fake merged ranking.
func runBooks(app *App, from, to string, sqlFor func(b Book) string) error {
	bks, err := app.Resolve(from, to)
	if err != nil {
		return err
	}
	ctx, cancel := app.Ctx()
	defer cancel()

	out := &db.Result{}
	for _, b := range bks {
		res, err := app.DB.Query(ctx, b.DB, sqlFor(b))
		if err != nil {
			return fmt.Errorf("book %s (%s): %w", b.Key, b.DB, err)
		}
		if out.Columns == nil {
			out.Columns = append([]string{"book"}, res.Columns...)
		}
		for _, r := range res.Rows {
			out.Rows = append(out.Rows, append([]any{b.Key}, r...))
		}
	}
	if out.Columns == nil {
		out.Columns = []string{"book"}
	}
	return app.Render(out)
}

// section is one labelled result inside a multi-part command (a document:
// header + lines, an account: summary + entries).
type section struct {
	Name  string
	Query string
}

// runSections executes several SELECTs against one database and renders them
// as one output: labelled tables in human mode, a single JSON object keyed by
// section name in --json.
func runSections(app *App, dbName string, secs []section) error {
	ctx, cancel := app.Ctx()
	defer cancel()

	type part struct {
		name string
		res  *db.Result
	}
	parts := make([]part, 0, len(secs))
	for _, s := range secs {
		res, err := app.DB.Query(ctx, dbName, s.Query)
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

// findInBooks runs a probe query (which must return a single count) against
// each candidate book and returns the first book where it matches. Used by the
// "show me document N" commands, so the operator never has to know the book.
func findInBooks(app *App, from, to, probe string) (Book, error) {
	bks, err := app.Resolve(from, to)
	if err != nil {
		return Book{}, err
	}
	ctx, cancel := app.Ctx()
	defer cancel()
	for _, b := range bks {
		res, err := app.DB.Query(ctx, b.DB, probe)
		if err != nil {
			return Book{}, fmt.Errorf("book %s: %w", b.Key, err)
		}
		if len(res.Rows) > 0 && len(res.Rows[0]) > 0 && fmt.Sprintf("%v", res.Rows[0][0]) != "0" {
			return b, nil
		}
	}
	return Book{}, Usagef("not found in any book (searched %s) — check the number, or try --book all", bookKeys(bks))
}

func bookKeys(bks []Book) string {
	var ks []string
	for _, b := range bks {
		ks = append(ks, b.Key)
	}
	return strings.Join(ks, ", ")
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
