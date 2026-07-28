package cli

import (
	"github.com/spf13/cobra"

	"postsql/internal/db"
)

func init() { register(newSearchCmd) }

// searchColumnSQL finds schemas/tables/columns whose name matches the ILIKE
// pattern in $1. It returns one row per matching column (a schema- or
// table-name match surfaces all of that table's columns). System schemas are
// excluded. No user input is interpolated — the pattern is bound as an arg.
const searchColumnSQL = `
	SELECT c.table_schema AS schema,
	       c.table_name   AS table,
	       c.column_name  AS column,
	       c.data_type    AS type
	FROM information_schema.columns c
	JOIN information_schema.tables t
	  ON t.table_schema = c.table_schema
	 AND t.table_name   = c.table_name
	WHERE t.table_type = 'BASE TABLE'
	  AND c.table_schema NOT IN ('pg_catalog', 'information_schema')
	  AND (c.table_schema ILIKE $1
	    OR c.table_name   ILIKE $1
	    OR c.column_name  ILIKE $1)
	ORDER BY c.table_schema, c.table_name, c.column_name`

func newSearchCmd(app *App) *cobra.Command {
	var all bool
	cmd := &cobra.Command{
		Use:   "search <term>",
		Short: "Find schemas/tables/columns whose name matches term (case-insensitive)",
		Long: "Search catalog names for a case-insensitive substring (ILIKE %term%).\n" +
			"By default scans the --db database; --all scans every database in the cluster.\n" +
			"Output columns: database, schema, table, column, type.",
		Example: "  postsql search order\n" +
			"  postsql --db jivo_ecom search amount\n" +
			"  postsql search price --all --json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			pattern := "%" + args[0] + "%"

			ctx, cancel := app.Ctx()
			defer cancel()

			merged := &db.Result{
				Columns: []string{"database", "schema", "table", "column", "type"},
			}

			dbNames := []string{app.DBName()}
			if all {
				names, err := app.DB.Query(ctx, app.DBName(),
					`SELECT datname FROM pg_database
					 WHERE datallowconn AND NOT datistemplate
					 ORDER BY datname`)
				if err != nil {
					return err
				}
				dbNames = dbNames[:0]
				for _, row := range names.Rows {
					if len(row) > 0 {
						dbNames = append(dbNames, searchStr(row[0]))
					}
				}
			}

			for _, dbName := range dbNames {
				res, err := app.DB.Query(ctx, dbName, searchColumnSQL, pattern)
				if err != nil {
					return err
				}
				for _, row := range res.Rows {
					out := make([]any, 0, 5)
					out = append(out, dbName)
					out = append(out, row...)
					merged.Rows = append(merged.Rows, out)
				}
			}

			return app.Render(merged)
		},
	}
	cmd.Flags().BoolVar(&all, "all", false, "scan every database in the cluster")
	return cmd
}

// searchStr renders a driver value (text protocol => string/[]byte) as a
// plain string for use as a database name.
func searchStr(v any) string {
	switch t := v.(type) {
	case string:
		return t
	case []byte:
		return string(t)
	case nil:
		return ""
	default:
		return ""
	}
}
