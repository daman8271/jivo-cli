package cli

import "github.com/spf13/cobra"

func init() { register(newSchemasCmd) }

func newSchemasCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "schemas",
		Short: "List schemas in the target database with a table count each",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), `
				SELECT n.nspname AS schema,
				       count(c.oid) FILTER (WHERE c.relkind IN ('r', 'p')) AS tables
				FROM pg_namespace n
				LEFT JOIN pg_class c ON c.relnamespace = n.oid
				WHERE n.nspname NOT LIKE 'pg\_%'
				  AND n.nspname <> 'information_schema'
				GROUP BY n.nspname
				ORDER BY tables DESC, schema`)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}
