package cli

// Books — the historical SAP B1 company databases on the SQL Server, and the
// date-routing that picks the right one(s) for a question.
//
// JIVO's books are split across two SAP company databases because the company
// was re-implemented in August 2019, and a third for the BSU unit. An operator
// asking "what did we sell in 2016?" should not have to know that; saphist
// routes on the date range and, when a range crosses the cut-over, reads BOTH
// and labels every row with the book it came from.
//
// Verified live 2026-09-01 (row counts and spans from the server itself).

import (
	"strings"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newBooksCmd) }

// Book is one historical SAP B1 company database.
type Book struct {
	Key     string // short name used by --book
	DB      string // SQL Server database name
	Company string // OADM.CompnyName
	First   string // first document date (YYYY-MM-DD)
	Last    string // last document date (YYYY-MM-DD)
	JELast  string // last journal-entry date (books stay open past the last doc)
	Group   string // "jivo" = Jivo Wellness Pvt Ltd, "bsu" = the BSU unit
	Note    string
}

// books is the registry. Order matters: oldest first, and it is the order rows
// come back in for a multi-book answer.
var books = []Book{
	{
		Key: "old", DB: "Live_Jivo_WellnessN_Aug_2019",
		Company: "Jivo Wellness Pvt. Ltd. (Old)",
		First:   "2014-11-01", Last: "2019-08-31", JELast: "2019-10-29", Group: "jivo",
		Note: "the first SAP implementation — 33,066 A/R invoices, 185,991 journal entries",
	},
	{
		Key: "new", DB: "Jivo_All_Branches_Live",
		Company: "Jivo Wellness Pvt. Ltd.",
		First:   "2019-08-31", Last: "2024-10-01", JELast: "2025-03-31", Group: "jivo",
		Note: "the all-branches company, closed at the Oct-2024 move to HANA — 68,070 A/R invoices, 6 branches",
	},
	{
		Key: "bsu", DB: "ARY_BSU",
		Company: "Akal Rozgar Yojana A Unit Of Jivo Wellness Pvt. Ltd. (BSU)",
		First:   "2019-04-01", Last: "2023-03-14", JELast: "2025-03-31", Group: "bsu",
		Note: "separate company — NOT part of the Jivo Wellness figures; opt in with --book bsu",
	},
}

// otherDBs are databases on the same server that look like books but are not
// routable: a test copy, and the live systems that belong to other CLIs.
var otherDBs = [][3]string{
	{"zTest_Jivo", "test copy of Jivo_All_Branches_Live", "identical counts; never quote from it"},
	{"FR8HODBNEW", "ARY FusionERP8 (live retail/distribution)", "use the `ary` CLI"},
	{"jsaplive3", "JSAP budget/approval app (live)", "use the `jsap` CLI"},
	{"DSR_V6", "DSR field-force portal (live)", "use the `dsr` CLI"},
}

// bookByKey finds a book by its --book key or by its exact database name.
func bookByKey(s string) (Book, bool) {
	s = strings.TrimSpace(s)
	for _, b := range books {
		if strings.EqualFold(b.Key, s) || strings.EqualFold(b.DB, s) {
			return b, true
		}
	}
	return Book{}, false
}

// jivoBooks returns the Jivo Wellness books (old + new), excluding BSU.
func jivoBooks() []Book {
	var out []Book
	for _, b := range books {
		if b.Group == "jivo" {
			out = append(out, b)
		}
	}
	return out
}

// overlaps reports whether a book's coverage intersects [from, to). Empty
// bounds are open-ended. `to` is EXCLUSIVE, matching every date flag in this CLI.
func (b Book) overlaps(from, to string) bool {
	last := b.Last
	if b.JELast > last {
		last = b.JELast
	}
	if to != "" && to <= b.First {
		return false
	}
	if from != "" && from > last {
		return false
	}
	return true
}

// Resolve picks the books a command should read.
//
//	--book <key|dbname>  one specific book (bsu included)
//	--book all           every book, BSU included
//	--db <name>          any database on the server (escape hatch, unlabelled)
//	otherwise            the Jivo Wellness books whose coverage meets the dates
//
// It never silently returns nothing: a range entirely outside 2014-2024 is an
// error that says where the data actually lives.
func (a *App) Resolve(from, to string) ([]Book, error) {
	if raw := strings.TrimSpace(a.Flags.Database); raw != "" {
		return []Book{{Key: raw, DB: raw, Company: "(raw --db)", Group: "raw"}}, nil
	}
	switch key := strings.TrimSpace(a.Flags.Book); {
	case key == "":
	case strings.EqualFold(key, "all"):
		return books, nil
	case strings.EqualFold(key, "jivo"):
		return jivoBooks(), nil
	default:
		b, ok := bookByKey(key)
		if !ok {
			return nil, Usagef("unknown book %q — use one of: old, new, bsu, all (or `saphist books`)", key)
		}
		return []Book{b}, nil
	}

	var out []Book
	for _, b := range jivoBooks() {
		if b.overlaps(from, to) {
			out = append(out, b)
		}
	}
	if len(out) == 0 {
		return nil, Usagef("no historical book covers %s..%s — these books run %s to %s; "+
			"anything after that is in the LIVE SAP HANA system, use the `sapb1` CLI",
			orDash(from), orDash(to), books[0].First, "2024-10-01")
	}
	return out, nil
}

func orDash(s string) string {
	if s == "" {
		return "-"
	}
	return s
}

func newBooksCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "books",
		Short:   "The historical company databases, what period each covers, and which one a date lands in",
		Aliases: []string{"book", "dbs"},
		Long: "JIVO's pre-HANA SAP books live in three company databases on this SQL Server.\n" +
			"Every command routes on --from/--to automatically; --book pins one explicitly.",
		Example: "  saphist books\n  saphist books which --from 2016-04-01 --to 2017-04-01\n  saphist books which --year 2021",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			res := &db.Result{Columns: []string{"book", "database", "company", "first_doc", "last_doc", "last_je", "note"}}
			for _, b := range books {
				res.Rows = append(res.Rows, []any{b.Key, b.DB, b.Company, b.First, b.Last, b.JELast, b.Note})
			}
			for _, o := range otherDBs {
				res.Rows = append(res.Rows, []any{"-", o[0], o[1], "", "", "", o[2]})
			}
			return app.Render(res)
		},
	}
	c.AddCommand(booksWhichCmd(app))
	return c
}

func booksWhichCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "which",
		Short:   "Which book(s) hold a given period",
		Example: "  saphist books which --year 2016\n  saphist books which --from 2019-06-01 --to 2019-12-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			bks, err := app.Resolve(from, to)
			if err != nil {
				return err
			}
			res := &db.Result{Columns: []string{"book", "database", "company", "covers"}}
			for _, b := range bks {
				res.Rows = append(res.Rows, []any{b.Key, b.DB, b.Company, b.First + " .. " + b.Last})
			}
			return app.Render(res)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}
