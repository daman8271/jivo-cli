package cli

import (
	"strconv"
	"strings"

	"github.com/spf13/cobra"

	"postsql/internal/db"
)

func init() { register(newPeekCmd) }

func newPeekCmd(app *App) *cobra.Command {
	var where string
	cmd := &cobra.Command{
		Use:   "peek <[schema.]table>",
		Short: "Sample rows from a table (SELECT * with a LIMIT)",
		Long: "Sample rows from a table. Schema defaults to public.\n" +
			"Row count comes from --limit/-n (default 20 when unset). --where\n" +
			"appends a raw WHERE expression, still inside the read-only transaction.",
		Example: "  postsql peek users\n" +
			"  postsql --db jivo_ecom peek public.products -n 5\n" +
			"  postsql peek users --where \"is_active = true\" --json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			schema, table := splitTableName(args[0])
			if table == "" {
				return Usagef("empty table name")
			}

			limit := app.Flags.Limit
			if limit <= 0 {
				limit = 20
			}

			sql := "SELECT * FROM " + db.Ident(schema, table)
			if w := strings.TrimSpace(where); w != "" {
				if err := validateWhere(w); err != nil {
					return err
				}
				sql += " WHERE (" + w + ")"
			}
			sql += " LIMIT " + strconv.Itoa(limit)

			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sql)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
	cmd.Flags().StringVar(&where, "where", "", "single boolean expression appended as WHERE (<expr>)")
	return cmd
}
