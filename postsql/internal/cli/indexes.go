package cli

import (
	"github.com/spf13/cobra"
)

func init() { register(newIndexesCmd) }

func newIndexesCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "indexes <[schema.]table>",
		Short: "List indexes on a table (name, unique, primary, definition)",
		Long: "List every index on a table: name, whether it is unique, whether it is the\n" +
			"primary key, and its full CREATE INDEX definition.\n" +
			"Schema defaults to public; qualify the table as schema.table to override.",
		Example: "  postsql indexes users\n" +
			"  postsql --db jivo_ecom indexes public.products --json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			schema, table := splitTableName(args[0])
			if table == "" {
				return Usagef("empty table name")
			}
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), `
				SELECT
				  i.relname       AS index_name,
				  ix.indisunique  AS is_unique,
				  ix.indisprimary AS is_primary,
				  pi.indexdef     AS definition
				FROM pg_index ix
				JOIN pg_class i        ON i.oid = ix.indexrelid
				JOIN pg_class t        ON t.oid = ix.indrelid
				JOIN pg_namespace n    ON n.oid = t.relnamespace
				JOIN pg_indexes pi     ON pi.schemaname = n.nspname AND pi.indexname = i.relname
				WHERE n.nspname = $1 AND t.relname = $2
				ORDER BY ix.indisprimary DESC, ix.indisunique DESC, i.relname`,
				schema, table)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}
