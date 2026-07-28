package cli

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

func init() { register(newStatsCmd) }

func newStatsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "stats",
		Short: "Storage summary: total database size and the top 15 tables by size",
		Long: "Show a storage summary for the target database (--db, else the profile default).\n" +
			"Prints the total database size and table count as a leading note (stderr),\n" +
			"then the 15 largest tables as a clean table: schema, table, est_rows, size.\n" +
			"With --json the output stays a plain array of the top-table rows.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()

			dbName := app.DBName()

			// Leading note (skipped for machine-readable output / --quiet).
			if !app.Flags.JSON && !app.Flags.CSV && !app.Flags.Quiet {
				sum, err := app.DB.Query(ctx, dbName, `
					SELECT pg_size_pretty(pg_database_size(current_database())) AS total_size,
					       (SELECT count(*)
					          FROM pg_class c
					          JOIN pg_namespace n ON n.oid = c.relnamespace
					         WHERE c.relkind IN ('r', 'p', 'm')
					           AND n.nspname NOT IN ('pg_catalog', 'information_schema')) AS table_count`)
				if err != nil {
					return err
				}
				if len(sum.Rows) == 1 && len(sum.Rows[0]) == 2 {
					fmt.Fprintf(os.Stderr, "database %s: total size %v across %v tables\n",
						dbName, sum.Rows[0][0], sum.Rows[0][1])
				}
			}

			res, err := app.DB.Query(ctx, dbName, `
				SELECT n.nspname                              AS schema,
				       c.relname                              AS "table",
				       CASE WHEN c.reltuples < 0 THEN 'unknown'
				            ELSE to_char(c.reltuples, 'FM999,999,999,990')
				       END                                    AS est_rows,
				       pg_size_pretty(pg_total_relation_size(c.oid)) AS size
				FROM pg_class c
				JOIN pg_namespace n ON n.oid = c.relnamespace
				WHERE c.relkind IN ('r', 'p', 'm')
				  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
				ORDER BY pg_total_relation_size(c.oid) DESC
				LIMIT 15`)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}
