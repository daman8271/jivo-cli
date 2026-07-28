package cli

import (
	"strings"

	"github.com/spf13/cobra"

	"postsql/internal/db"
)

func init() { register(newCountCmd) }

func newCountCmd(app *App) *cobra.Command {
	var where string
	cmd := &cobra.Command{
		Use:   "count <[schema.]table>",
		Short: "Count rows in a table, optionally filtered with --where",
		Long: "Run SELECT count(*) against a table.\n" +
			"The table may be schema-qualified (schema.table); schema defaults to public.\n" +
			"Use --where to add a filter expression (raw SQL, applied read-only).",
		Example: "  postsql count users\n" +
			"  postsql count public.orders --where \"status = 'paid'\"\n" +
			"  postsql --db jivo_ecom count products --json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			schema, table := splitTableName(args[0])
			if table == "" {
				return Usagef("count: table name is required")
			}

			sql := "SELECT count(*) AS count FROM " + db.Ident(schema, table)
			if w := strings.TrimSpace(where); w != "" {
				if err := validateWhere(w); err != nil {
					return err
				}
				sql += " WHERE (" + w + ")"
			}

			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sql)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
	cmd.Flags().StringVar(&where, "where", "", "filter expression added as WHERE (<expr>)")
	return cmd
}
