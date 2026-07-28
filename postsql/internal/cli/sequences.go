package cli

import "github.com/spf13/cobra"

func init() { register(newSequencesCmd) }

func newSequencesCmd(app *App) *cobra.Command {
	var schema string
	cmd := &cobra.Command{
		Use:     "sequences",
		Aliases: []string{"seqs"},
		Short:   "List sequences (last value, start, increment, min/max, cycle)",
		Example: "  postsql --db jivo_ecom sequences\n" +
			"  postsql --db jivo_ecom sequences --schema public --json",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			sql := `
				SELECT schemaname   AS schema,
				       sequencename AS name,
				       last_value,
				       start_value,
				       increment_by,
				       min_value,
				       max_value,
				       cycle
				FROM pg_sequences
				WHERE schemaname NOT IN ('pg_catalog', 'information_schema')`
			var qargs []any
			if schema != "" {
				qargs = append(qargs, schema)
				sql += " AND schemaname = $1"
			}
			sql += " ORDER BY schemaname, sequencename"

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
