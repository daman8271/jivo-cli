package cli

import "github.com/spf13/cobra"

func init() { register(newTablesCmd) }

func newTablesCmd(app *App) *cobra.Command {
	var schema string
	cmd := &cobra.Command{
		Use:   "tables",
		Short: "List tables in a database with estimated row counts and size",
		Long: "List ordinary and partitioned tables in the target database.\n" +
			"Columns: schema, table, est_rows (from pg_class.reltuples), size\n" +
			"(pg_total_relation_size). System schemas are excluded. Ordered by\n" +
			"total on-disk size, largest first.",
		Example: "  postsql --db jivo_ecom tables\n" +
			"  postsql --db jivo_ecom tables --schema public --json",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			const sql = `
				SELECT n.nspname AS schema,
				       c.relname AS "table",
				       CASE WHEN c.reltuples < 0 THEN 'unknown'
				            ELSE to_char(c.reltuples, 'FM999,999,999,990')
				       END AS est_rows,
				       pg_size_pretty(pg_total_relation_size(c.oid)) AS size
				FROM pg_class c
				JOIN pg_namespace n ON n.oid = c.relnamespace
				WHERE c.relkind IN ('r', 'p')
				  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
				  AND n.nspname !~ '^pg_toast'
				  AND ($1 = '' OR n.nspname = $1)
				ORDER BY pg_total_relation_size(c.oid) DESC, n.nspname, c.relname`

			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sql, schema)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
	cmd.Flags().StringVar(&schema, "schema", "", "restrict to a single schema (default: all user schemas)")
	return cmd
}
