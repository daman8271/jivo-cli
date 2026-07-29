package cli

import (
	"context"
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"dsr/internal/db"
)

func init() { register(newCountCmd) }

func newCountCmd(app *App) *cobra.Command {
	var where string
	c := &cobra.Command{
		Use:     "count <table>",
		Short:   "Count rows in a table, optionally filtered by --where",
		Example: "  dsr count tbl_retailers\n  dsr count tbl_salesPersonAttendance --where \"attDate >= '2026-07-01'\"",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()
			schema, table, err := lookupTable(ctx, app, args[0])
			if err != nil {
				return err
			}
			q := "SELECT COUNT(*) AS n FROM " + db.Ident(schema, table)
			if strings.TrimSpace(where) != "" {
				q += " WHERE " + where
			}
			res, err := app.DB.Query(ctx, app.DBName(), q)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
	c.Flags().StringVar(&where, "where", "", "optional WHERE clause (T-SQL, read-only)")
	return c
}

// lookupTable resolves a case-insensitive table name to its (schema, table),
// erroring with near-miss suggestions if not found. This keeps the raw table
// name out of interpolated SQL — we only ever interpolate the catalog's own value.
func lookupTable(ctx context.Context, app *App, name string) (string, string, error) {
	res, err := app.DB.Query(ctx, app.DBName(),
		"SELECT s.name AS [schema], t.name AS [table] FROM sys.tables t "+
			"JOIN sys.schemas s ON s.schema_id = t.schema_id WHERE LOWER(t.name) = LOWER("+db.Lit(name)+")")
	if err != nil {
		return "", "", err
	}
	if len(res.Rows) == 0 {
		sug, _ := app.DB.Query(ctx, app.DBName(),
			"SELECT TOP 8 t.name AS [table] FROM sys.tables t WHERE t.name LIKE "+db.Lit("%"+name+"%")+" ORDER BY t.name")
		var names []string
		if sug != nil {
			for _, r := range sug.Rows {
				names = append(names, doctorStr(r, sug.Columns, "table"))
			}
		}
		msg := fmt.Sprintf("no table named %q in %s", name, app.DBName())
		if len(names) > 0 {
			msg += " (did you mean: " + strings.Join(names, ", ") + ")"
		}
		return "", "", &db.Error{Kind: "query", Code: db.CodeQuery, Err: fmt.Errorf("%s", msg)}
	}
	return doctorStr(res.Rows[0], res.Columns, "schema"), doctorStr(res.Rows[0], res.Columns, "table"), nil
}
