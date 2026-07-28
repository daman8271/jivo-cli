package cli

import "github.com/spf13/cobra"

func init() { register(newDbsCmd) }

func newDbsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "dbs",
		Short: "List all databases with size, owner, and encoding",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), `
				SELECT datname AS database,
				       pg_size_pretty(pg_database_size(datname)) AS size,
				       pg_catalog.pg_get_userbyid(datdba) AS owner,
				       pg_catalog.pg_encoding_to_char(encoding) AS encoding
				FROM pg_database
				WHERE NOT datistemplate
				ORDER BY pg_database_size(datname) DESC`)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}
