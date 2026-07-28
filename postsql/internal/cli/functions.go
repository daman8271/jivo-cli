package cli

import "github.com/spf13/cobra"

func init() { register(newFunctionsCmd) }

func newFunctionsCmd(app *App) *cobra.Command {
	var schema string
	var all bool
	cmd := &cobra.Command{
		Use:     "functions",
		Aliases: []string{"funcs"},
		Short:   "List functions and procedures (kind, return type, arguments, language)",
		Long: "List functions and procedures in --db.\n" +
			"By default excludes functions provided by extensions; use --all to include them.",
		Example: "  postsql --db jivo_ecom functions\n" +
			"  postsql --db test_supabase functions --schema public --all",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			sql := `
				SELECT n.nspname AS schema,
				       p.proname AS name,
				       CASE p.prokind WHEN 'f' THEN 'function'
				                      WHEN 'p' THEN 'procedure'
				                      WHEN 'a' THEN 'aggregate'
				                      WHEN 'w' THEN 'window'
				                      ELSE p.prokind::text END AS kind,
				       pg_catalog.pg_get_function_result(p.oid)    AS returns,
				       pg_catalog.pg_get_function_arguments(p.oid) AS arguments,
				       l.lanname AS language
				FROM pg_proc p
				JOIN pg_namespace n ON n.oid = p.pronamespace
				JOIN pg_language  l ON l.oid = p.prolang
				WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')`
			if !all {
				// Exclude functions that are members of an installed extension
				// (pgcrypto, uuid-ossp, …) so the default list is the ones you wrote.
				sql += `
				  AND NOT EXISTS (
				      SELECT 1 FROM pg_depend d
				      WHERE d.classid = 'pg_proc'::regclass
				        AND d.objid = p.oid
				        AND d.deptype = 'e')`
			}
			var qargs []any
			if schema != "" {
				qargs = append(qargs, schema)
				sql += " AND n.nspname = $1"
			}
			sql += " ORDER BY n.nspname, p.proname"

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
	cmd.Flags().BoolVar(&all, "all", false, "include functions provided by extensions")
	return cmd
}
