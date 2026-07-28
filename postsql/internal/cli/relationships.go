package cli

import (
	"github.com/spf13/cobra"
)

func init() { register(newRelationshipsCmd) }

func newRelationshipsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "relationships <[schema.]table>",
		Aliases: []string{"fks"},
		Short:   "Show foreign keys referencing and referenced by a table",
		Long: "List foreign-key relationships for a table.\n" +
			"outgoing = FKs defined on this table pointing elsewhere;\n" +
			"incoming = FKs on other tables that reference this table.\n" +
			"Schema defaults to public when not qualified.",
		Example: "  postsql relationships shipment_items\n" +
			"  postsql relationships public.products --db jivo_ecom --json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			schema, table := splitTableName(args[0])
			if table == "" {
				return Usagef("empty table name")
			}

			const sql = `
WITH fk AS (
    SELECT c.conname,
           c.conrelid, c.confrelid, c.conkey, c.confkey,
           cn.nspname AS from_schema, cl.relname AS from_table,
           tn.nspname AS to_schema, tl.relname AS to_table
    FROM pg_constraint c
    JOIN pg_class cl ON cl.oid = c.conrelid
    JOIN pg_namespace cn ON cn.oid = cl.relnamespace
    JOIN pg_class tl ON tl.oid = c.confrelid
    JOIN pg_namespace tn ON tn.oid = tl.relnamespace
    WHERE c.contype = 'f'
)
SELECT 'outgoing' AS direction, conname AS "constraint",
       from_schema || '.' || from_table AS from_table,
       (SELECT string_agg(a.attname, ', ' ORDER BY k.ord)
          FROM unnest(conkey) WITH ORDINALITY AS k(attnum, ord)
          JOIN pg_attribute a ON a.attrelid = conrelid AND a.attnum = k.attnum) AS from_columns,
       to_schema || '.' || to_table AS to_table,
       (SELECT string_agg(a.attname, ', ' ORDER BY k.ord)
          FROM unnest(confkey) WITH ORDINALITY AS k(attnum, ord)
          JOIN pg_attribute a ON a.attrelid = confrelid AND a.attnum = k.attnum) AS to_columns
FROM fk
WHERE from_schema = $1 AND from_table = $2
UNION ALL
SELECT 'incoming' AS direction, conname AS "constraint",
       from_schema || '.' || from_table AS from_table,
       (SELECT string_agg(a.attname, ', ' ORDER BY k.ord)
          FROM unnest(conkey) WITH ORDINALITY AS k(attnum, ord)
          JOIN pg_attribute a ON a.attrelid = conrelid AND a.attnum = k.attnum) AS from_columns,
       to_schema || '.' || to_table AS to_table,
       (SELECT string_agg(a.attname, ', ' ORDER BY k.ord)
          FROM unnest(confkey) WITH ORDINALITY AS k(attnum, ord)
          JOIN pg_attribute a ON a.attrelid = confrelid AND a.attnum = k.attnum) AS to_columns
FROM fk
WHERE to_schema = $1 AND to_table = $2
ORDER BY direction, "constraint"`

			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sql, schema, table)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}
