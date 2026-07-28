package cli

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"postsql/internal/db"
)

func init() { register(newSchemaDumpCmd) }

// schemadumpColumn is one column entry in the nested schema map.
type schemadumpColumn struct {
	Name     string `json:"name"`
	Type     string `json:"type"`
	Nullable bool   `json:"nullable"`
	Default  any    `json:"default"`
}

// schemadumpFK is one foreign-key constraint.
type schemadumpFK struct {
	Columns    []string `json:"columns"`
	References string   `json:"references"`
	RefColumns []string `json:"ref_columns"`
}

// schemadumpIndex is one index definition.
type schemadumpIndex struct {
	Name       string `json:"name"`
	Definition string `json:"definition"`
}

// schemadumpTable is the per-table structure.
type schemadumpTable struct {
	Columns     []schemadumpColumn `json:"columns"`
	PrimaryKey  []string           `json:"primary_key"`
	ForeignKeys []*schemadumpFK    `json:"foreign_keys"`
	Indexes     []schemadumpIndex  `json:"indexes"`
}

// schemadumpSchema groups tables under a schema.
type schemadumpSchema struct {
	Tables map[string]*schemadumpTable `json:"tables"`
}

// schemadumpDatabase is the top-level nested object.
type schemadumpDatabase struct {
	Database string                       `json:"database"`
	Schemas  map[string]*schemadumpSchema `json:"schemas"`
}

func newSchemaDumpCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "schema-dump",
		Aliases: []string{"schema"},
		Short:   "Emit the full schema of the database as one nested JSON object",
		Long: "Dump every user table's columns, primary keys, foreign keys, and indexes\n" +
			"for the --db database as a single nested JSON object. This is the AI schema\n" +
			"primer. System schemas (pg_catalog/information_schema/pg_toast) are excluded.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			dbName := app.DBName()
			out := &schemadumpDatabase{
				Database: dbName,
				Schemas:  map[string]*schemadumpSchema{},
			}

			// getTable lazily creates the schema/table nodes.
			getTable := func(schema, table string) *schemadumpTable {
				s, ok := out.Schemas[schema]
				if !ok {
					s = &schemadumpSchema{Tables: map[string]*schemadumpTable{}}
					out.Schemas[schema] = s
				}
				t, ok := s.Tables[table]
				if !ok {
					t = &schemadumpTable{
						Columns:     []schemadumpColumn{},
						PrimaryKey:  []string{},
						ForeignKeys: []*schemadumpFK{},
						Indexes:     []schemadumpIndex{},
					}
					s.Tables[table] = t
				}
				return t
			}

			// 1. Columns — authoritative list of all user tables.
			colRes, err := schemadumpRun(app, dbName, `
				SELECT n.nspname AS schema,
				       c.relname AS tbl,
				       a.attname AS col,
				       format_type(a.atttypid, a.atttypmod) AS typ,
				       NOT a.attnotnull AS nullable,
				       pg_get_expr(ad.adbin, ad.adrelid) AS def
				FROM pg_attribute a
				JOIN pg_class c ON c.oid = a.attrelid
				JOIN pg_namespace n ON n.oid = c.relnamespace
				LEFT JOIN pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
				WHERE c.relkind = 'r'
				  AND a.attnum > 0
				  AND NOT a.attisdropped
				  AND n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
				ORDER BY n.nspname, c.relname, a.attnum`)
			if err != nil {
				return err
			}
			ci := schemadumpColIdx(colRes)
			for _, r := range colRes.Rows {
				t := getTable(schemadumpStr(r[ci["schema"]]), schemadumpStr(r[ci["tbl"]]))
				t.Columns = append(t.Columns, schemadumpColumn{
					Name:     schemadumpStr(r[ci["col"]]),
					Type:     schemadumpStr(r[ci["typ"]]),
					Nullable: schemadumpBool(r[ci["nullable"]]),
					Default:  schemadumpNullStr(r[ci["def"]]),
				})
			}

			// 2. Primary keys (in key order).
			pkRes, err := schemadumpRun(app, dbName, `
				SELECT n.nspname AS schema, c.relname AS tbl, a.attname AS col
				FROM pg_index i
				JOIN pg_class c ON c.oid = i.indrelid
				JOIN pg_namespace n ON n.oid = c.relnamespace
				CROSS JOIN LATERAL unnest(i.indkey) WITH ORDINALITY AS k(attnum, ord)
				JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
				WHERE i.indisprimary
				  AND c.relkind = 'r'
				  AND n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
				ORDER BY n.nspname, c.relname, k.ord`)
			if err != nil {
				return err
			}
			pi := schemadumpColIdx(pkRes)
			for _, r := range pkRes.Rows {
				t := getTable(schemadumpStr(r[pi["schema"]]), schemadumpStr(r[pi["tbl"]]))
				t.PrimaryKey = append(t.PrimaryKey, schemadumpStr(r[pi["col"]]))
			}

			// 3. Foreign keys (grouped by constraint, columns in key order).
			fkRes, err := schemadumpRun(app, dbName, `
				SELECT n.nspname AS schema,
				       c.relname AS tbl,
				       con.conname AS nm,
				       lc.attname AS col,
				       fc_ns.nspname AS ref_schema,
				       fcl.relname AS ref_table,
				       rc.attname AS ref_col
				FROM pg_constraint con
				JOIN pg_class c ON c.oid = con.conrelid
				JOIN pg_namespace n ON n.oid = c.relnamespace
				JOIN pg_class fcl ON fcl.oid = con.confrelid
				JOIN pg_namespace fc_ns ON fc_ns.oid = fcl.relnamespace
				JOIN LATERAL unnest(con.conkey, con.confkey) WITH ORDINALITY AS k(conkey, confkey, ord) ON true
				JOIN pg_attribute lc ON lc.attrelid = con.conrelid AND lc.attnum = k.conkey
				JOIN pg_attribute rc ON rc.attrelid = con.confrelid AND rc.attnum = k.confkey
				WHERE con.contype = 'f'
				  AND n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
				ORDER BY n.nspname, c.relname, con.conname, k.ord`)
			if err != nil {
				return err
			}
			fi := schemadumpColIdx(fkRes)
			fkGroup := map[string]*schemadumpFK{}
			for _, r := range fkRes.Rows {
				schema := schemadumpStr(r[fi["schema"]])
				table := schemadumpStr(r[fi["tbl"]])
				conname := schemadumpStr(r[fi["nm"]])
				refSchema := schemadumpStr(r[fi["ref_schema"]])
				refTable := schemadumpStr(r[fi["ref_table"]])
				key := schema + "\x00" + table + "\x00" + conname
				fk, ok := fkGroup[key]
				if !ok {
					fk = &schemadumpFK{
						Columns:    []string{},
						References: refSchema + "." + refTable,
						RefColumns: []string{},
					}
					fkGroup[key] = fk
					t := getTable(schema, table)
					t.ForeignKeys = append(t.ForeignKeys, fk)
				}
				fk.Columns = append(fk.Columns, schemadumpStr(r[fi["col"]]))
				fk.RefColumns = append(fk.RefColumns, schemadumpStr(r[fi["ref_col"]]))
			}

			// 4. Indexes.
			ixRes, err := schemadumpRun(app, dbName, `
				SELECT schemaname AS schema, tablename AS tbl, indexname AS nm, indexdef AS def
				FROM pg_indexes
				WHERE schemaname NOT IN ('pg_catalog','information_schema','pg_toast')
				ORDER BY schemaname, tablename, indexname`)
			if err != nil {
				return err
			}
			xi := schemadumpColIdx(ixRes)
			for _, r := range ixRes.Rows {
				t := getTable(schemadumpStr(r[xi["schema"]]), schemadumpStr(r[xi["tbl"]]))
				t.Indexes = append(t.Indexes, schemadumpIndex{
					Name:       schemadumpStr(r[xi["nm"]]),
					Definition: schemadumpStr(r[xi["def"]]),
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

// schemadumpRun runs a read-only catalog query against dbName.
func schemadumpRun(app *App, dbName, sql string) (*db.Result, error) {
	ctx, cancel := app.Ctx()
	defer cancel()
	return app.DB.Query(ctx, dbName, sql)
}

// schemadumpColIdx maps a result's column names to their positions.
func schemadumpColIdx(res *db.Result) map[string]int {
	m := make(map[string]int, len(res.Columns))
	for i, c := range res.Columns {
		m[c] = i
	}
	return m
}

// schemadumpStr renders a driver value as a plain string.
func schemadumpStr(v any) string {
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

// schemadumpNullStr returns nil for SQL NULL, else the string form.
func schemadumpNullStr(v any) any {
	if v == nil {
		return nil
	}
	if b, ok := v.([]byte); ok {
		return string(b)
	}
	if s, ok := v.(string); ok {
		return s
	}
	return schemadumpStr(v)
}

// schemadumpBool interprets a driver value as a boolean.
func schemadumpBool(v any) bool {
	switch t := v.(type) {
	case bool:
		return t
	case string:
		return t == "true" || t == "t" || t == "TRUE" || t == "T"
	case []byte:
		s := string(t)
		return s == "true" || s == "t" || s == "TRUE" || s == "T"
	default:
		return false
	}
}
