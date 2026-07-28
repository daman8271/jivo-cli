package cli

import (
	"github.com/spf13/cobra"
)

func init() { register(newColsCmd) }

func newColsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "cols <[schema.]table>",
		Short: "List columns of a table: name, type, nullable, default, position",
		Long: "List the columns of a table with their true Postgres types via\n" +
			"format_type on pg_attribute — so enums show their type name, arrays show\n" +
			"element[], and varchar/numeric keep their length/precision.\n" +
			"Accepts an optional schema. prefix (default schema: public).",
		Example: "  postsql cols accounts_user\n" +
			"  postsql --db jivo_ecom cols public.amazon_mp --json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			schema, table := splitTableName(args[0])
			if table == "" {
				return Usagef("empty table name")
			}
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), `
				SELECT a.attname                              AS column,
				       format_type(a.atttypid, a.atttypmod)   AS type,
				       CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END AS nullable,
				       pg_get_expr(ad.adbin, ad.adrelid)      AS default,
				       a.attnum                               AS position
				FROM pg_attribute a
				JOIN pg_class c ON c.oid = a.attrelid
				JOIN pg_namespace n ON n.oid = c.relnamespace
				LEFT JOIN pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
				WHERE n.nspname = $1 AND c.relname = $2
				  AND a.attnum > 0 AND NOT a.attisdropped
				ORDER BY a.attnum`, schema, table)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}
