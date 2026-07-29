package cli

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/spf13/cobra"

	"dsr/internal/db"
	"dsr/internal/render"
)

func init() { register(newSchemaCmd) }

func newSchemaCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "schema",
		Short: "Explore the database catalog: tables, columns, keys, and a full dump",
	}
	c.AddCommand(newSchemaTablesCmd(app), newSchemaColumnsCmd(app), newSchemaKeysCmd(app), newSchemaViewsCmd(app), newSchemaDumpCmd(app))
	return c
}

func newSchemaViewsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "views",
		Short: "List views with their definition size",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(),
				"SELECT s.name AS [schema], v.name AS [view], "+
					"LEN(CAST(m.definition AS nvarchar(max))) AS def_len "+
					"FROM sys.views v JOIN sys.schemas s ON s.schema_id = v.schema_id "+
					"LEFT JOIN sys.sql_modules m ON m.object_id = v.object_id ORDER BY v.name")
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}

// --- catalog queries (bulk, few round-trips) ---

const sqlTables = `
SELECT s.name AS [schema], t.name AS [table],
       SUM(CASE WHEN p.index_id IN (0,1) THEN p.rows ELSE 0 END) AS [rows],
       (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id) AS [cols]
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id = t.schema_id
LEFT JOIN sys.partitions p ON p.object_id = t.object_id
GROUP BY s.name, t.name, t.object_id
ORDER BY [rows] DESC, [table] ASC`

const sqlColumns = `
SELECT s.name AS [schema], t.name AS [table], c.column_id AS pos, c.name AS [column],
       ty.name AS [type], c.max_length AS max_len, c.precision AS prec, c.scale AS scale,
       c.is_nullable AS nullable
FROM sys.columns c
JOIN sys.tables t ON t.object_id = c.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
ORDER BY s.name, t.name, c.column_id`

const sqlPKs = `
SELECT OBJECT_SCHEMA_NAME(i.object_id) AS [schema], OBJECT_NAME(i.object_id) AS [table], col.name AS [column]
FROM sys.indexes i
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
JOIN sys.columns col ON col.object_id = ic.object_id AND col.column_id = ic.column_id
WHERE i.is_primary_key = 1
ORDER BY [schema], [table], ic.key_ordinal`

const sqlFKs = `
SELECT fk.name AS fk,
       OBJECT_SCHEMA_NAME(fk.parent_object_id) AS from_schema,
       OBJECT_NAME(fk.parent_object_id) AS from_table, pc.name AS from_col,
       OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS to_schema,
       OBJECT_NAME(fk.referenced_object_id) AS to_table, rc.name AS to_col
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.columns pc ON pc.object_id = fkc.parent_object_id AND pc.column_id = fkc.parent_column_id
JOIN sys.columns rc ON rc.object_id = fkc.referenced_object_id AND rc.column_id = fkc.referenced_column_id
ORDER BY from_table, fk`

const sqlViews = `
SELECT s.name AS [schema], v.name AS [view], m.definition AS definition
FROM sys.views v
JOIN sys.schemas s ON s.schema_id = v.schema_id
LEFT JOIN sys.sql_modules m ON m.object_id = v.object_id
ORDER BY v.name`

func newSchemaTablesCmd(app *App) *cobra.Command {
	var minRows int
	c := &cobra.Command{
		Use:   "tables",
		Short: "List tables with row and column counts (biggest first)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sqlTables)
			if err != nil {
				return err
			}
			if minRows > 0 {
				res = filterByRows(res, minRows)
			}
			return app.Render(res)
		},
	}
	c.Flags().IntVar(&minRows, "min-rows", 0, "only tables with at least this many rows")
	return c
}

func newSchemaColumnsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "columns [table]",
		Short: "List columns (optionally for one table)",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()
			q := sqlColumns
			if len(args) == 1 {
				q = "SELECT * FROM (" + sqlColumns + ") _c WHERE [table] = " + db.Lit(args[0])
			}
			res, err := app.DB.Query(ctx, app.DBName(), q)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}

func newSchemaKeysCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "keys",
		Short: "List declared foreign-key relationships",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), sqlFKs)
			if err != nil {
				return err
			}
			return app.Render(res)
		},
	}
}

func newSchemaDumpCmd(app *App) *cobra.Command {
	var out string
	var samples int
	var viewsOnly bool
	c := &cobra.Command{
		Use:   "dump",
		Short: "Extract the full catalog (tables, columns, keys, views, sample rows) to files",
		Long: "Writes tables.tsv, columns.tsv, primary_keys.tsv, foreign_keys.tsv, views.tsv,\n" +
			"views/<name>.sql, catalog.json, an INDEX.md overview, and samples/<schema>.<table>.json\n" +
			"for every non-empty table. This is the raw material for the study vault.\n" +
			"--views-only refreshes just the view definitions without touching tables/samples.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runDump(app, out, samples, viewsOnly)
		},
	}
	c.Flags().StringVar(&out, "out", "study/schema", "output directory")
	c.Flags().IntVar(&samples, "samples", 3, "sample rows to capture per non-empty table (0 = none)")
	c.Flags().BoolVar(&viewsOnly, "views-only", false, "dump only views (leave tables/columns/samples untouched)")
	return c
}

func runDump(app *App, outDir string, samples int, viewsOnly bool) error {
	dbName := app.DBName()
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		return err
	}

	// Longer budget for the whole dump than a single --timeout query.
	ctx := context.Background()

	if viewsOnly {
		n, err := dumpViews(app, dbName, outDir, ctx)
		if err != nil {
			return err
		}
		fmt.Printf("dumped %d views from %s to %s\n", n, dbName, outDir)
		return nil
	}

	tables, err := app.DB.Query(ctx, dbName, sqlTables)
	if err != nil {
		return err
	}
	cols, err := app.DB.Query(ctx, dbName, sqlColumns)
	if err != nil {
		return err
	}
	pks, err := app.DB.Query(ctx, dbName, sqlPKs)
	if err != nil {
		return err
	}
	fks, err := app.DB.Query(ctx, dbName, sqlFKs)
	if err != nil {
		return err
	}

	// --- TSVs ---
	if err := writeTSV(filepath.Join(outDir, "tables.tsv"), tables); err != nil {
		return err
	}
	if err := writeTSV(filepath.Join(outDir, "columns.tsv"), cols); err != nil {
		return err
	}
	if err := writeTSV(filepath.Join(outDir, "primary_keys.tsv"), pks); err != nil {
		return err
	}
	if err := writeTSV(filepath.Join(outDir, "foreign_keys.tsv"), fks); err != nil {
		return err
	}

	// --- views (definitions are often the real report interface) ---
	nViews, _ := dumpViews(app, dbName, outDir, ctx)

	// --- structured catalog.json ---
	type colInfo struct {
		Pos      string `json:"pos"`
		Name     string `json:"name"`
		Type     string `json:"type"`
		MaxLen   string `json:"max_len"`
		Nullable string `json:"nullable"`
		PK       bool   `json:"pk"`
	}
	type tblInfo struct {
		Schema  string    `json:"schema"`
		Table   string    `json:"table"`
		Rows    string    `json:"rows"`
		Columns []colInfo `json:"columns"`
	}

	pkSet := map[string]bool{} // "table\tcolumn"
	for _, r := range pks.Rows {
		pkSet[doctorStr(r, pks.Columns, "table")+"\t"+doctorStr(r, pks.Columns, "column")] = true
	}
	colsByTable := map[string][]colInfo{}
	for _, r := range cols.Rows {
		tbl := doctorStr(r, cols.Columns, "table")
		ci := colInfo{
			Pos:      doctorStr(r, cols.Columns, "pos"),
			Name:     doctorStr(r, cols.Columns, "column"),
			Type:     doctorStr(r, cols.Columns, "type"),
			MaxLen:   doctorStr(r, cols.Columns, "max_len"),
			Nullable: doctorStr(r, cols.Columns, "nullable"),
			PK:       pkSet[tbl+"\t"+doctorStr(r, cols.Columns, "column")],
		}
		colsByTable[tbl] = append(colsByTable[tbl], ci)
	}
	var catalog []tblInfo
	for _, r := range tables.Rows {
		tbl := doctorStr(r, tables.Columns, "table")
		catalog = append(catalog, tblInfo{
			Schema:  doctorStr(r, tables.Columns, "schema"),
			Table:   tbl,
			Rows:    doctorStr(r, tables.Columns, "rows"),
			Columns: colsByTable[tbl],
		})
	}
	if err := writeJSON(filepath.Join(outDir, "catalog.json"), catalog); err != nil {
		return err
	}

	// --- sample rows per non-empty table ---
	var sampled, skipped, failed int
	var sampleErrs []string
	if samples > 0 {
		sampDir := filepath.Join(outDir, "samples")
		if err := os.MkdirAll(sampDir, 0o755); err != nil {
			return err
		}
		for _, r := range tables.Rows {
			schema := doctorStr(r, tables.Columns, "schema")
			tbl := doctorStr(r, tables.Columns, "table")
			nrows := doctorInt(r, tables.Columns, "rows")
			if nrows <= 0 {
				skipped++
				continue
			}
			sctx, cancel := context.WithTimeout(ctx, 20e9) // 20s per sample
			q := fmt.Sprintf("SELECT TOP %d * FROM %s", samples, db.Ident(schema, tbl))
			sres, serr := app.DB.Query(sctx, dbName, q)
			cancel()
			if serr != nil {
				failed++
				sampleErrs = append(sampleErrs, tbl+": "+serr.Error())
				continue
			}
			fn := filepath.Join(sampDir, sanitize(schema)+"."+sanitize(tbl)+".json")
			if err := writeJSON(fn, render.Maps(sres)); err != nil {
				failed++
				sampleErrs = append(sampleErrs, tbl+": "+err.Error())
				continue
			}
			sampled++
		}
	}

	// --- INDEX.md overview ---
	if err := writeIndex(outDir, dbName, tables, cols, pks, fks, sampled, skipped, failed, sampleErrs); err != nil {
		return err
	}

	fmt.Printf("dumped %s to %s: %d tables, %d views, %d columns, %d PK cols, %d FKs; samples: %d written, %d empty-skipped, %d failed\n",
		dbName, outDir, len(tables.Rows), nViews, len(cols.Rows), len(pks.Rows), len(fks.Rows), sampled, skipped, failed)
	return nil
}

func filterByRows(res *db.Result, min int) *db.Result {
	out := &db.Result{Columns: res.Columns}
	for _, r := range res.Rows {
		if doctorInt(r, res.Columns, "rows") >= min {
			out.Rows = append(out.Rows, r)
		}
	}
	return out
}

func dumpViews(app *App, dbName, outDir string, ctx context.Context) (int, error) {
	vres, err := app.DB.Query(ctx, dbName, sqlViews)
	if err != nil {
		return 0, err
	}
	var vb strings.Builder
	vb.WriteString("schema\tview\tdef_bytes\n")
	vdir := filepath.Join(outDir, "views")
	if err := os.MkdirAll(vdir, 0o755); err != nil {
		return 0, err
	}
	for _, r := range vres.Rows {
		sc := doctorStr(r, vres.Columns, "schema")
		vn := doctorStr(r, vres.Columns, "view")
		def := doctorStr(r, vres.Columns, "definition")
		fmt.Fprintf(&vb, "%s\t%s\t%d\n", sc, vn, len(def))
		if def != "" {
			_ = os.WriteFile(filepath.Join(vdir, sanitize(sc)+"."+sanitize(vn)+".sql"), []byte(def), 0o644)
		}
	}
	if err := os.WriteFile(filepath.Join(outDir, "views.tsv"), []byte(vb.String()), 0o644); err != nil {
		return 0, err
	}
	return len(vres.Rows), nil
}

func writeTSV(path string, res *db.Result) error {
	var b strings.Builder
	b.WriteString(strings.Join(res.Columns, "\t"))
	b.WriteByte('\n')
	for _, r := range res.Rows {
		cells := make([]string, len(res.Columns))
		for i := range res.Columns {
			if i < len(r) {
				cells[i] = tsvCell(r[i])
			}
		}
		b.WriteString(strings.Join(cells, "\t"))
		b.WriteByte('\n')
	}
	return os.WriteFile(path, []byte(b.String()), 0o644)
}

func tsvCell(v any) string {
	s := ""
	switch t := v.(type) {
	case nil:
		s = ""
	case []byte:
		s = string(t)
	default:
		s = fmt.Sprintf("%v", t)
	}
	s = strings.ReplaceAll(s, "\t", " ")
	s = strings.ReplaceAll(s, "\n", " ")
	s = strings.ReplaceAll(s, "\r", " ")
	return s
}

func writeJSON(path string, v any) error {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0o644)
}

func writeIndex(outDir, dbName string, tables, cols, pks, fks *db.Result, sampled, skipped, failed int, sampleErrs []string) error {
	var totalRows int64
	type tr struct {
		name string
		rows int
	}
	var top []tr
	for _, r := range tables.Rows {
		n := doctorInt(r, tables.Columns, "rows")
		totalRows += int64(n)
		top = append(top, tr{doctorStr(r, tables.Columns, "table"), n})
	}
	sort.Slice(top, func(i, j int) bool { return top[i].rows > top[j].rows })

	var b strings.Builder
	fmt.Fprintf(&b, "# DSR schema dump — `%s`\n\n", dbName)
	fmt.Fprintf(&b, "- Tables: **%d**\n- Columns: **%d**\n- Primary-key columns: **%d**\n- Declared foreign keys: **%d**\n- Total rows (all tables): **%d**\n- Samples: %d written, %d empty tables skipped, %d failed\n\n",
		len(tables.Rows), len(cols.Rows), len(pks.Rows), len(fks.Rows), totalRows, sampled, skipped, failed)
	b.WriteString("Files: `tables.tsv`, `columns.tsv`, `primary_keys.tsv`, `foreign_keys.tsv`, `catalog.json`, `samples/`.\n\n")
	b.WriteString("## Top 40 tables by row count\n\n| table | rows |\n|---|---:|\n")
	for i, t := range top {
		if i >= 40 {
			break
		}
		fmt.Fprintf(&b, "| %s | %d |\n", t.name, t.rows)
	}
	if len(sampleErrs) > 0 {
		b.WriteString("\n## Sample failures\n\n")
		for _, e := range sampleErrs {
			fmt.Fprintf(&b, "- %s\n", e)
		}
	}
	return os.WriteFile(filepath.Join(outDir, "INDEX.md"), []byte(b.String()), 0o644)
}

func sanitize(s string) string {
	return strings.Map(func(r rune) rune {
		switch {
		case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9', r == '_', r == '-':
			return r
		default:
			return '_'
		}
	}, s)
}
