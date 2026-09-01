package cli

// `saphist query` — the escape hatch. One SELECT (or WITH), against one book,
// rendered as a table / JSON / CSV. Plus `tables` and `columns` so an operator
// (or an agent) can find their way around a 2,800-table SAP schema without
// leaving the terminal.

import (
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newQueryCmd); register(newTablesCmd); register(newColumnsCmd) }

func newQueryCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "query [SQL]",
		Short: "Run one read-only SELECT against a book (SQL from the argument or stdin)",
		Long: "Runs a single SELECT (or WITH) statement. Anything else — INSERT, UPDATE, DELETE, EXEC,\n" +
			"a second batched statement — is refused before it reaches the server, and what does run\n" +
			"runs inside a transaction that is always rolled back.\n\n" +
			"`query` reads ONE book: --book old | new | bsu (default: the newest Jivo Wellness book).\n" +
			"Use the domain commands (sales, ledger, party, …) when you want both books at once.",
		Example: "  saphist query \"SELECT TOP 5 DocNum, DocDate, CardName, DocTotal FROM OINV ORDER BY DocDate DESC\"\n" +
			"  saphist query --book old \"SELECT COUNT(*) FROM OINV\"\n" +
			"  echo \"SELECT TOP 3 AcctCode, AcctName FROM OACT\" | saphist query --json",
		Args: cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			var sql string
			if len(args) == 1 {
				sql = args[0]
			} else {
				b, err := io.ReadAll(os.Stdin)
				if err != nil {
					return err
				}
				sql = string(b)
			}
			if strings.TrimSpace(sql) == "" {
				return Usagef("no SQL given: pass it as an argument or pipe it on stdin")
			}
			return runSelect(app, sql)
		},
	}
	return c
}

func newTablesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "tables",
		Short:   "List tables in a book, with row counts (--search to filter)",
		Example: "  saphist tables --search inv\n  saphist tables --book old --search OCR",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf(`SELECT TOP %d t.name AS table_name,
  SUM(CASE WHEN p.index_id IN (0,1) THEN p.rows ELSE 0 END) AS rows_approx
FROM sys.tables t JOIN sys.partitions p ON p.object_id = t.object_id%s
GROUP BY t.name ORDER BY rows_approx DESC, t.name`,
				topN(app, 100), fWhere(fLike("t.name", f.Search)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search")
	return c
}

func newColumnsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "columns <TABLE>",
		Short:   "Columns and types of one table",
		Example: "  saphist columns OINV\n  saphist columns JDT1",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			q := `SELECT c.column_id AS ord, c.name AS column_name, ty.name AS type,
  c.max_length AS len, c.is_nullable AS nullable
FROM sys.columns c JOIN sys.types ty ON ty.user_type_id = c.user_type_id
WHERE c.object_id = OBJECT_ID(` + db.Lit(args[0]) + `) ORDER BY c.column_id`
			return runSelect(app, q)
		},
	}
	return c
}
