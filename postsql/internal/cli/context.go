package cli

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/spf13/cobra"

	"postsql/internal/db"
)

func init() { register(newContextCmd) }

// contextDatabase is one row of the server-wide database inventory.
type contextDatabase struct {
	Name string `json:"name"`
	Size string `json:"size"`
}

// contextTable is one of the target database's largest tables.
type contextTable struct {
	Schema  string `json:"schema"`
	Table   string `json:"table"`
	EstRows int64  `json:"est_rows"`
	Size    string `json:"size"`
}

// contextTarget describes the --db (or default) database in focus.
type contextTarget struct {
	Database    string         `json:"database"`
	SchemaCount int64          `json:"schema_count"`
	TopTables   []contextTable `json:"top_tables"`
}

// contextOut is the compact, AI-primeable overview emitted to stdout.
type contextOut struct {
	ServerVersion string            `json:"server_version"`
	Databases     []contextDatabase `json:"databases"`
	Target        contextTarget     `json:"target"`
}

func newContextCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "context",
		Short: "Token-efficient JSON overview of the server for priming an AI agent",
		Long: "Emit a small, structured JSON snapshot — server version, every database with\n" +
			"its size, and the target database's schema count plus its ~20 largest tables.\n" +
			"Designed to be pasted into an AI prompt to prime it about the server.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()

			target := app.DBName()

			// Server version (kept short: the leading "major.minor").
			verRes, err := app.DB.Query(ctx, target, `SELECT current_setting('server_version')`)
			if err != nil {
				return err
			}
			out := contextOut{
				ServerVersion: contextShortVersion(contextScalar(verRes)),
				Target:        contextTarget{Database: target},
			}

			// All databases with pretty sizes, biggest first.
			dbRes, err := app.DB.Query(ctx, target, `
				SELECT datname AS name,
				       pg_size_pretty(pg_database_size(datname)) AS size
				FROM pg_database
				WHERE NOT datistemplate
				ORDER BY pg_database_size(datname) DESC`)
			if err != nil {
				return err
			}
			for _, r := range dbRes.Rows {
				out.Databases = append(out.Databases, contextDatabase{
					Name: contextStr(contextAt(r, 0)),
					Size: contextStr(contextAt(r, 1)),
				})
			}

			// Schema count for the target database (user schemas only).
			scRes, err := app.DB.Query(ctx, target, `
				SELECT count(DISTINCT schemaname)
				FROM pg_tables
				WHERE schemaname NOT IN ('pg_catalog', 'information_schema')`)
			if err != nil {
				return err
			}
			out.Target.SchemaCount = contextInt(contextScalar(scRes))

			// Top ~20 tables by total size in the target database.
			tblRes, err := app.DB.Query(ctx, target, `
				SELECT n.nspname AS schema,
				       c.relname AS table,
				       GREATEST(c.reltuples, 0)::bigint AS est_rows,
				       pg_size_pretty(pg_total_relation_size(c.oid)) AS size
				FROM pg_class c
				JOIN pg_namespace n ON n.oid = c.relnamespace
				WHERE c.relkind IN ('r', 'p')
				  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
				ORDER BY pg_total_relation_size(c.oid) DESC
				LIMIT 20`)
			if err != nil {
				return err
			}
			for _, r := range tblRes.Rows {
				out.Target.TopTables = append(out.Target.TopTables, contextTable{
					Schema:  contextStr(contextAt(r, 0)),
					Table:   contextStr(contextAt(r, 1)),
					EstRows: contextInt(contextAt(r, 2)),
					Size:    contextStr(contextAt(r, 3)),
				})
			}

			enc := json.NewEncoder(os.Stdout)
			enc.SetEscapeHTML(false)
			if !app.Flags.Compact {
				enc.SetIndent("", "  ")
			}
			return enc.Encode(out)
		},
	}
}

// contextScalar returns the single top-left cell of a result, or nil.
func contextScalar(res *db.Result) any {
	if res == nil || len(res.Rows) == 0 || len(res.Rows[0]) == 0 {
		return nil
	}
	return res.Rows[0][0]
}

// contextAt safely fetches column i from a row.
func contextAt(row []any, i int) any {
	if i < 0 || i >= len(row) {
		return nil
	}
	return row[i]
}

// contextStr renders a driver value (text under the simple protocol) as a string.
func contextStr(v any) string {
	switch t := v.(type) {
	case nil:
		return ""
	case string:
		return t
	case []byte:
		return string(t)
	default:
		return fmt.Sprintf("%v", t)
	}
}

// contextInt parses a driver value into an int64, defaulting to 0.
func contextInt(v any) int64 {
	s := strings.TrimSpace(contextStr(v))
	if s == "" {
		return 0
	}
	if n, err := strconv.ParseInt(s, 10, 64); err == nil {
		return n
	}
	// Tolerate a float-ish text form (e.g. "11541.0").
	if f, err := strconv.ParseFloat(s, 64); err == nil {
		return int64(f)
	}
	return 0
}

// contextShortVersion trims a verbose server_version to its numeric head.
func contextShortVersion(v any) string {
	s := strings.TrimSpace(contextStr(v))
	if i := strings.IndexByte(s, ' '); i >= 0 {
		return s[:i]
	}
	return s
}
