package cli

import "github.com/spf13/cobra"

func init() { register(newViewsCmd) }

func newViewsCmd(app *App) *cobra.Command {
	var schema string
	cmd := &cobra.Command{
		Use:   "views",
		Short: "List views and materialized views (type, owner, and matview size)",
		Long: "List views and materialized views in --db.\n" +
			"describe/cols/peek/count/query all work on a view just like a table.",
		Example: "  postsql --db test_supabase views\n" +
			"  postsql --db test_supabase views --schema public --json",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			// Schema, when given, is passed as a bound VALUE ($1) — never
			// concatenated — so this stays injection-safe.
			sql := `
				SELECT n.nspname AS schema,
				       c.relname AS name,
				       CASE c.relkind WHEN 'v' THEN 'view'
				                      WHEN 'm' THEN 'materialized view' END AS type,
				       pg_catalog.pg_get_userbyid(c.relowner) AS owner,
				       CASE WHEN c.relkind = 'm'
				            THEN pg_size_pretty(pg_total_relation_size(c.oid))
				            ELSE '' END AS size
				FROM pg_class c
				JOIN pg_namespace n ON n.oid = c.relnamespace
				WHERE c.relkind IN ('v', 'm')
				  AND n.nspname NOT IN ('pg_catalog', 'information_schema')`
			var qargs []any
			if schema != "" {
				sql += " AND n.nspname = $1"
				qargs = append(qargs, schema)
			}
			sql += " ORDER BY n.nspname, c.relname"

			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sql, qargs...)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
	cmd.Flags().StringVar(&schema, "schema", "", "restrict to a single schema")
	return cmd
}
