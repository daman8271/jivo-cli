package cli

import (
	"os"
	"strconv"
	"strings"

	"github.com/spf13/cobra"

	"postsql/internal/db"
	"postsql/internal/render"
)

func init() { register(newExportCmd) }

func newExportCmd(app *App) *cobra.Command {
	var exportQuery string
	var exportOut string

	cmd := &cobra.Command{
		Use:   "export [[schema.]table]",
		Short: "Dump table or query data to CSV (default) or JSON",
		Long: "Export data to CSV or JSON.\n" +
			"Source is either a positional [schema.]table (SELECT * FROM it) or --query \"<sql>\" — exactly one.\n" +
			"Destination is stdout by default, or a file via --out. Format defaults to CSV; use --json for JSON.\n" +
			"The global --limit applies to the positional-table form.",
		Example: "  postsql export public.amazon_mp --out amazon.csv\n" +
			"  postsql export --query \"SELECT * FROM accounts_user\" --json --out users.json\n" +
			"  postsql --db jivo_ecom export amazon_mp --limit 100",
		Args: cobra.ArbitraryArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			table := strings.TrimSpace(strings.Join(args, " "))
			hasTable := table != ""
			hasQuery := strings.TrimSpace(exportQuery) != ""

			switch {
			case hasTable && hasQuery:
				return Usagef("provide either a table argument or --query, not both")
			case !hasTable && !hasQuery:
				return Usagef("provide a [schema.]table argument or --query \"<sql>\"")
			}

			var sql string
			if hasTable {
				sql = "SELECT * FROM " + exportIdent(table)
				if app.Flags.Limit > 0 {
					sql += " LIMIT " + strconv.Itoa(app.Flags.Limit)
				}
			} else {
				sql = strings.TrimSpace(exportQuery)
			}

			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sql)
			if err != nil {
				return err
			}

			// Format: honor --json/--compact; otherwise default to CSV for export.
			opts := app.RenderOpts()
			if !opts.JSON && !opts.Compact && !opts.CSV {
				opts.CSV = true
			}

			if strings.TrimSpace(exportOut) == "" {
				return render.Render(os.Stdout, res, opts)
			}
			f, err := os.Create(exportOut)
			if err != nil {
				return err
			}
			defer f.Close()
			return render.Render(f, res, opts)
		},
	}

	cmd.Flags().StringVar(&exportQuery, "query", "", "SQL to export instead of a table (mutually exclusive with the table arg)")
	cmd.Flags().StringVar(&exportOut, "out", "", "write output to this file instead of stdout")
	return cmd
}

// exportIdent turns a user-supplied [schema.]table into a safely quoted
// identifier. It never string-concats raw names into SQL — db.Ident quotes
// each part via pgx.Identifier.Sanitize.
func exportIdent(name string) string {
	if i := strings.Index(name, "."); i >= 0 {
		return db.Ident(name[:i], name[i+1:])
	}
	return db.Ident(name)
}
