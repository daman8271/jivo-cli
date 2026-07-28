package cli

import (
	"github.com/spf13/cobra"
)

func init() { register(newDescribeCmd) }

func newDescribeCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "describe <[schema.]table>",
		Aliases: []string{"desc"},
		Short:   "Show columns with type, nullability, default, and primary-key flag",
		Long: "Describe a table's columns: column, type, nullable, default, and is_primary_key.\n" +
			"Accepts an optional schema qualifier (schema.table); defaults to the public schema.",
		Example: "  postsql describe users\n" +
			"  postsql --db jivo_ecom desc public.products --json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			schema, table := splitTableName(args[0])
			if table == "" {
				return Usagef("empty table name")
			}

			// Schema and table are passed as query VALUES ($1,$2) — never
			// concatenated into SQL text — so this is injection-safe.
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), describeColumnsSQL, schema, table)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}

// describeColumnsSQL reports a table's columns with true Postgres types via
// format_type on pg_attribute (enums show their type name, arrays show
// element[], varchar/numeric keep length/precision) — unlike
// information_schema.columns which flattens these to USER-DEFINED / ARRAY and
// drops length. Shared by the describe command and the MCP describe_table tool.
const describeColumnsSQL = `
SELECT a.attname                              AS column,
       format_type(a.atttypid, a.atttypmod)   AS type,
       CASE WHEN a.attnotnull THEN 'no' ELSE 'yes' END AS nullable,
       pg_get_expr(ad.adbin, ad.adrelid)      AS default,
       CASE WHEN pk.attnum IS NOT NULL THEN 'yes' ELSE 'no' END AS is_primary_key
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
LEFT JOIN (
    SELECT k.attnum
    FROM pg_index i
    JOIN pg_class ic ON ic.oid = i.indrelid
    JOIN pg_namespace inz ON inz.oid = ic.relnamespace
    CROSS JOIN LATERAL unnest(i.indkey) AS k(attnum)
    WHERE i.indisprimary AND inz.nspname = $1 AND ic.relname = $2
) pk ON pk.attnum = a.attnum
WHERE n.nspname = $1 AND c.relname = $2
  AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attnum`
