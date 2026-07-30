package hana

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	"hana-sql/internal/guard"
)

// Schemas are JIVO's three SAP Business One companies. They are HANA schemas,
// not databases: one login sees all three, and a query reaches another company
// purely by qualifying the table name.
var Schemas = []string{"JIVO_OIL_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB"}

// SchemaCompany maps a schema to the company it holds.
var SchemaCompany = map[string]string{
	"JIVO_OIL_HANADB":       "Oil",
	"JIVO_MART_HANADB":      "Mart",
	"JIVO_BEVERAGES_HANADB": "Beverages",
}

// The catalog SQL below is FIXED TEXT with ? bind parameters — caller input is
// never concatenated into it. Every one of these statements is also run through
// guard.Check like any other query (TestCatalogSQLPassesGuard asserts they pass,
// which is the proof that the guard does not false-positive on real read SQL).

// tablesSQL lists base tables, with live row counts from the monitoring view.
// The M_TABLES join is what needs the monitoring privilege; tablesSQLNoCounts
// is the documented degrade when it is not granted.
const tablesSQL = `
SELECT t.SCHEMA_NAME AS SCHEMA_NAME,
       t.TABLE_NAME  AS TABLE_NAME,
       'TABLE'       AS KIND,
       m.RECORD_COUNT AS ROW_COUNT
FROM SYS.TABLES t
LEFT OUTER JOIN SYS.M_TABLES m
  ON m.SCHEMA_NAME = t.SCHEMA_NAME AND m.TABLE_NAME = t.TABLE_NAME
WHERE t.SCHEMA_NAME IN (%s)
  AND (? = '' OR UPPER(t.TABLE_NAME) LIKE UPPER(?))`

const tablesSQLNoCounts = `
SELECT t.SCHEMA_NAME AS SCHEMA_NAME,
       t.TABLE_NAME  AS TABLE_NAME,
       'TABLE'       AS KIND,
       NULL          AS ROW_COUNT
FROM SYS.TABLES t
WHERE t.SCHEMA_NAME IN (%s)
  AND (? = '' OR UPPER(t.TABLE_NAME) LIKE UPPER(?))`

const viewsSQL = `
UNION ALL
SELECT v.SCHEMA_NAME AS SCHEMA_NAME,
       v.VIEW_NAME   AS TABLE_NAME,
       'VIEW'        AS KIND,
       NULL          AS ROW_COUNT
FROM SYS.VIEWS v
WHERE v.SCHEMA_NAME IN (%s)
  AND (? = '' OR UPPER(v.VIEW_NAME) LIKE UPPER(?))`

const tablesOrder = `
ORDER BY SCHEMA_NAME, TABLE_NAME`

// columnsSQL describes one table's columns, with a primary-key flag from
// SYS.CONSTRAINTS. Views have no SYS.TABLE_COLUMNS rows, so SYS.VIEW_COLUMNS is
// unioned in — otherwise asking for a view's columns silently returns nothing.
const columnsSQL = `
SELECT c.POSITION       AS POSITION,
       c.COLUMN_NAME    AS COLUMN_NAME,
       c.DATA_TYPE_NAME AS DATA_TYPE,
       c.LENGTH         AS LENGTH,
       c.SCALE          AS SCALE,
       c.IS_NULLABLE    AS IS_NULLABLE,
       CASE WHEN k.CONSTRAINT_NAME IS NULL THEN 'NO' ELSE 'YES' END AS PRIMARY_KEY
FROM SYS.TABLE_COLUMNS c
LEFT OUTER JOIN SYS.CONSTRAINTS k
  ON  k.SCHEMA_NAME = c.SCHEMA_NAME
  AND k.TABLE_NAME  = c.TABLE_NAME
  AND k.COLUMN_NAME = c.COLUMN_NAME
  AND k.IS_PRIMARY_KEY = 'TRUE'
WHERE c.SCHEMA_NAME = ? AND c.TABLE_NAME = ?
  AND (? = '' OR UPPER(c.COLUMN_NAME) LIKE UPPER(?))
UNION ALL
SELECT v.POSITION       AS POSITION,
       v.COLUMN_NAME    AS COLUMN_NAME,
       v.DATA_TYPE_NAME AS DATA_TYPE,
       v.LENGTH         AS LENGTH,
       v.SCALE          AS SCALE,
       v.IS_NULLABLE    AS IS_NULLABLE,
       'NO'             AS PRIMARY_KEY
FROM SYS.VIEW_COLUMNS v
WHERE v.SCHEMA_NAME = ? AND v.VIEW_NAME = ?
  AND (? = '' OR UPPER(v.COLUMN_NAME) LIKE UPPER(?))
ORDER BY POSITION`

// identitySQL is the doctor's single round trip: who am I, what time does the
// server think it is, and what build is this.
const identitySQL = `
SELECT CURRENT_USER AS DB_USER,
       CURRENT_SCHEMA AS DB_SCHEMA,
       TO_VARCHAR(CURRENT_UTCTIMESTAMP, 'YYYY-MM-DD"T"HH24:MI:SS') AS SERVER_UTC,
       (SELECT VERSION FROM SYS.M_DATABASE) AS HANA_VERSION
FROM DUMMY`

// schemaCountSQL counts visible tables per JIVO schema, proving readability.
const schemaCountSQL = `
SELECT SCHEMA_NAME AS SCHEMA_NAME, COUNT(*) AS TABLE_COUNT
FROM SYS.TABLES
WHERE SCHEMA_NAME IN (%s)
GROUP BY SCHEMA_NAME
ORDER BY SCHEMA_NAME`

// existsSQL asks whether a name exists in a schema, ignoring case, so an empty
// column list can be explained instead of just handed back.
const existsSQL = `
SELECT TABLE_NAME AS NAME, 'TABLE' AS KIND FROM SYS.TABLES
WHERE SCHEMA_NAME = ? AND UPPER(TABLE_NAME) = UPPER(?)
UNION ALL
SELECT VIEW_NAME AS NAME, 'VIEW' AS KIND FROM SYS.VIEWS
WHERE SCHEMA_NAME = ? AND UPPER(VIEW_NAME) = UPPER(?)`

// placeholders renders "?, ?, ?" for n bind parameters.
func placeholders(n int) string {
	if n <= 0 {
		return "''" // IN ('') matches nothing, which is the honest empty answer
	}
	return strings.TrimSuffix(strings.Repeat("?, ", n), ", ")
}

// resolveSchemas validates the requested schema, defaulting to all three.
//
// An unrecognised schema is an ERROR, not an empty result. It used to be passed
// straight through upper-cased, so `schema:"JIVO_BEVERAGE_HANADB"` (one missing
// S), `schema:"Beverages"` and `schema:"Oil"` each returned a clean
// row_count:0 success — a one-letter typo indistinguishable from "this company
// has no data". That is the same silent-wrong-answer class the `company`
// argument is loudly refused for; it has no business being tolerated here.
func resolveSchemas(schema string) ([]string, error) {
	schema = strings.TrimSpace(schema)
	if schema == "" {
		return append([]string(nil), Schemas...), nil
	}
	up := strings.ToUpper(schema)
	for _, s := range Schemas {
		if s == up {
			return []string{s}, nil
		}
	}
	// HANA's own catalog schemas stay reachable — that is how the tool answers
	// questions about SYS.TABLES itself.
	if isSystemSchema(up) {
		return []string{up}, nil
	}
	return nil, unknownSchemaError(schema)
}

// isSystemSchema reports whether name is one of HANA's catalog schemas.
func isSystemSchema(up string) bool {
	return up == "SYS" || up == "PUBLIC" || strings.HasPrefix(up, "SYS_") || strings.HasPrefix(up, "_SYS")
}

func unknownSchemaError(schema string) error {
	msg := fmt.Sprintf("unknown schema %q — refusing rather than returning an empty result, because a typo is otherwise indistinguishable from \"this company has no data\". The three companies are %s (Oil / Mart / Beverages); HANA's own SYS/_SYS_* catalog schemas are also allowed.",
		schema, strings.Join(Schemas, ", "))
	if best := closestSchema(schema); best != "" {
		msg += fmt.Sprintf(" Did you mean %q (%s)?", best, SchemaCompany[best])
	}
	return errors.New(msg)
}

// closestSchema guesses what the caller meant: the company name ("Oil"), a
// distinctive fragment ("BEVERAGES"), or a near-miss spelling.
func closestSchema(in string) string {
	up := strings.ToUpper(strings.TrimSpace(in))
	if up == "" {
		return ""
	}
	for _, s := range Schemas {
		if strings.EqualFold(SchemaCompany[s], up) {
			return s
		}
	}
	if len(up) >= 3 {
		hit := ""
		for _, s := range Schemas {
			if strings.Contains(s, up) {
				if hit != "" {
					hit = "" // ambiguous fragment: say nothing rather than guess
					break
				}
				hit = s
			}
		}
		if hit != "" {
			return hit
		}
	}
	best, bestD := "", 1<<30
	for _, s := range Schemas {
		if d := editDistance(up, s); d < bestD {
			best, bestD = s, d
		}
	}
	if bestD <= 4 {
		return best
	}
	return ""
}

// editDistance is Levenshtein, used only to say "did you mean".
func editDistance(a, b string) int {
	prev := make([]int, len(b)+1)
	cur := make([]int, len(b)+1)
	for j := range prev {
		prev[j] = j
	}
	for i := 1; i <= len(a); i++ {
		cur[0] = i
		for j := 1; j <= len(b); j++ {
			cost := 1
			if a[i-1] == b[j-1] {
				cost = 0
			}
			cur[j] = min(min(cur[j-1]+1, prev[j]+1), prev[j-1]+cost)
		}
		prev, cur = cur, prev
	}
	return prev[len(b)]
}

// TableQuery is one hana_tables request.
type TableQuery struct {
	// Schema is one company schema, or "" for all three.
	Schema string
	// Like is a case-insensitive LIKE pattern on the object name ("" = all).
	Like string
	// IncludeViews adds SYS.VIEWS to the listing.
	IncludeViews bool
	// Offset skips this many rows, so a truncated listing can be paged.
	Offset int
	// NoRowCounts skips the SYS.M_TABLES join, which is what makes an
	// unfiltered three-schema listing slow.
	NoRowCounts bool
}

// Tables lists tables (and optionally views) in one or all JIVO schemas.
//
// The listing is ordered by schema, so when the row cap trips the answer covers
// only the alphabetically-first company — 1000 Beverages tables out of 9244
// across the three. It used to say so only via truncated:true plus a note
// telling the caller to "aggregate server-side", which is impossible for a
// catalog listing, with no offset to recover with. Now the note names the
// schemas the page actually covers, names the ones it does NOT, and hands back
// the offset for the next page.
func (d *DB) Tables(ctx context.Context, q TableQuery) (*Result, error) {
	schemas, err := resolveSchemas(q.Schema)
	if err != nil {
		return nil, err
	}
	if q.Offset < 0 {
		return nil, fmt.Errorf("offset must not be negative (got %d)", q.Offset)
	}
	ph := placeholders(len(schemas))

	build := func(base string) (string, []any) {
		stmt := fmt.Sprintf(base, ph)
		args := make([]any, 0, 2*len(schemas)+4)
		for _, s := range schemas {
			args = append(args, s)
		}
		args = append(args, q.Like, q.Like)
		if q.IncludeViews {
			stmt += fmt.Sprintf(viewsSQL, ph)
			for _, s := range schemas {
				args = append(args, s)
			}
			args = append(args, q.Like, q.Like)
		}
		return stmt + tablesOrder + d.pageClause(q.Offset), args
	}

	first := tablesSQL
	if q.NoRowCounts {
		first = tablesSQLNoCounts
	}
	stmt, args := build(first)
	res, err := d.queryReadOnly(ctx, guard.MCPPolicy, Limits{}, catalogAdvice, stmt, args...)
	if err == nil {
		annotateTables(res, q, schemas)
		return res, nil
	}
	if q.NoRowCounts || guard.IsRefusal(err) || !isPrivilegeOrMissing(err) {
		return nil, err
	}
	// Documented degrade: this login cannot read the monitoring view, so ship
	// the table list without row counts rather than failing the tool.
	stmt, args = build(tablesSQLNoCounts)
	res, err2 := d.queryReadOnly(ctx, guard.MCPPolicy, Limits{}, catalogAdvice, stmt, args...)
	if err2 != nil {
		return nil, err
	}
	res.Note = joinNote(res.Note, "row counts unavailable: this login cannot read SYS.M_TABLES (needs CATALOG READ / monitoring privilege)")
	annotateTables(res, q, schemas)
	return res, nil
}

// pageClause renders LIMIT/OFFSET. The numbers are Go ints, never caller text,
// so this cannot become a concatenation hole; HANA does not accept a bare
// OFFSET without a LIMIT, hence the paired form.
func (d *DB) pageClause(offset int) string {
	rowCap := d.opts.Limits.MaxRows
	if rowCap <= 0 {
		if offset <= 0 {
			return ""
		}
		return fmt.Sprintf("\nLIMIT %d OFFSET %d", 1<<31-1, offset)
	}
	// rowCap+1 lets the row cap in walk() decide truncation on real evidence:
	// the extra row exists only if there is genuinely a next page.
	return fmt.Sprintf("\nLIMIT %d OFFSET %d", rowCap+1, offset)
}

// annotateTables tells the caller exactly which part of the catalog it is
// holding. A partial listing that looks whole is how a model concludes a company
// has no tables.
func annotateTables(res *Result, q TableQuery, schemas []string) {
	if res == nil {
		return
	}
	if q.Offset > 0 {
		res.Note = joinNote(res.Note, fmt.Sprintf("this page starts at offset %d", q.Offset))
	}
	if !res.Truncated {
		return
	}
	seen := map[string]bool{}
	var covered []string
	for _, row := range res.Rows {
		if n, _ := row["SCHEMA_NAME"].(string); n != "" && !seen[n] {
			seen[n] = true
			covered = append(covered, n)
		}
	}
	var missing []string
	for _, s := range schemas {
		if !seen[s] {
			missing = append(missing, s)
		}
	}
	msg := fmt.Sprintf("PARTIAL CATALOG: rows %d-%d of the matching objects", q.Offset+1, q.Offset+res.RowCount)
	if len(covered) > 0 {
		msg += ", covering only " + strings.Join(covered, ", ")
	}
	if len(missing) > 0 {
		msg += "; NOTHING from " + strings.Join(missing, ", ") + " is in this answer"
	}
	msg += fmt.Sprintf("; fetch the next page with offset=%d", q.Offset+res.RowCount)
	res.Note = joinNote(res.Note, msg)
}

// Columns describes one table or view.
//
// An empty answer is investigated rather than returned: a wrong-case table name
// ("oinv") or a table that does not exist at all used to come back as a clean
// row_count:0 success, from which a model concludes the table HAS no columns.
func (d *DB) Columns(ctx context.Context, schema, table, like string) (*Result, error) {
	schemas, err := resolveSchemas(schema)
	if err != nil {
		return nil, err
	}
	s := schemas[0]
	t := strings.TrimSpace(table)
	if t == "" {
		return nil, errors.New("missing table name")
	}
	res, err := d.queryReadOnly(ctx, guard.MCPPolicy, Limits{}, catalogAdvice, columnsSQL,
		s, t, like, like,
		s, t, like, like)
	if err != nil || res.RowCount > 0 {
		return res, err
	}
	return d.explainEmptyColumns(ctx, s, t, like, res)
}

// explainEmptyColumns turns "no rows" into an answer to the question the caller
// was actually asking: does this table exist, and is it spelled that way?
func (d *DB) explainEmptyColumns(ctx context.Context, schema, table, like string, res *Result) (*Result, error) {
	names, err := d.queryReadOnly(ctx, guard.MCPPolicy, Limits{}, catalogAdvice, existsSQL,
		schema, table, schema, table)
	if err != nil {
		// Could not check. Say so rather than implying the table is empty.
		res.Note = joinNote(res.Note, fmt.Sprintf(
			"no columns matched, and whether %q exists in %s could not be verified: %v", table, schema, err))
		return res, nil
	}
	if len(names.Rows) == 0 {
		return nil, fmt.Errorf("no table or view named %q in schema %s — refusing to return an empty column list, because an empty list reads as \"this table has no columns\". Check the spelling with hana_tables{\"schema\":%q,\"like\":\"%%%s%%\"}.",
			table, schema, schema, table)
	}
	actual, _ := names.Rows[0]["NAME"].(string)
	if actual != "" && actual != table {
		return nil, fmt.Errorf("no table or view named %q in schema %s, but %q exists — HANA identifiers are case-sensitive, so use that exact spelling",
			table, schema, actual)
	}
	res.Note = joinNote(res.Note, fmt.Sprintf(
		"%q exists in %s but no column matched like %q — the table is real; the filter matched nothing", table, schema, like))
	return res, nil
}

// Identity is the doctor's one-row fact sheet.
type Identity struct {
	User       string
	Schema     string
	ServerUTC  string
	Version    string
	ClockSkew  time.Duration
	SkewKnown  bool
	SchemaRows []SchemaInfo
}

// SchemaInfo is one JIVO company schema and whether it can be read.
type SchemaInfo struct {
	Schema   string `json:"schema"`
	Company  string `json:"company"`
	Tables   int    `json:"tables"`
	Readable bool   `json:"readable"`
}

// Identify runs the doctor's two read-only queries.
func (d *DB) Identify(ctx context.Context) (*Identity, error) {
	res, err := d.QueryReadOnly(ctx, guard.MCPPolicy, Limits{}, identitySQL)
	if err != nil {
		return nil, err
	}
	id := &Identity{}
	if len(res.Rows) > 0 {
		r := res.Rows[0]
		id.User, _ = r["DB_USER"].(string)
		id.Schema, _ = r["DB_SCHEMA"].(string)
		id.ServerUTC, _ = r["SERVER_UTC"].(string)
		id.Version, _ = r["HANA_VERSION"].(string)
	}
	if t, err := time.Parse("2006-01-02T15:04:05", id.ServerUTC); err == nil {
		id.ClockSkew = time.Since(t.UTC())
		id.SkewKnown = true
	}

	args := make([]any, len(Schemas))
	for i, s := range Schemas {
		args[i] = s
	}
	counts, err := d.QueryReadOnly(ctx, guard.MCPPolicy, Limits{},
		fmt.Sprintf(schemaCountSQL, placeholders(len(Schemas))), args...)
	if err != nil {
		return id, nil // identity still useful; schema readability unknown
	}
	seen := map[string]int{}
	for _, row := range counts.Rows {
		name, _ := row["SCHEMA_NAME"].(string)
		switch n := row["TABLE_COUNT"].(type) {
		case int64:
			seen[name] = int(n)
		case string:
			var v int
			fmt.Sscanf(n, "%d", &v)
			seen[name] = v
		}
	}
	for _, s := range Schemas {
		n, ok := seen[s]
		id.SchemaRows = append(id.SchemaRows, SchemaInfo{
			Schema: s, Company: SchemaCompany[s], Tables: n, Readable: ok && n > 0,
		})
	}
	return id, nil
}

// CatalogStatements returns every fixed catalog statement this package can
// send, so a test can prove they all pass the read-only guard.
func CatalogStatements() []string {
	ph := placeholders(len(Schemas))
	paged := (&DB{opts: Options{Limits: Limits{MaxRows: DefaultMaxRows}}}).pageClause(1000)
	return []string{
		fmt.Sprintf(tablesSQL, ph) + fmt.Sprintf(viewsSQL, ph) + tablesOrder,
		fmt.Sprintf(tablesSQL, ph) + fmt.Sprintf(viewsSQL, ph) + tablesOrder + paged,
		fmt.Sprintf(tablesSQLNoCounts, ph) + tablesOrder,
		columnsSQL,
		existsSQL,
		identitySQL,
		fmt.Sprintf(schemaCountSQL, ph),
	}
}

func isPrivilegeOrMissing(err error) bool {
	m := strings.ToLower(err.Error())
	return strings.Contains(m, "insufficient privilege") ||
		strings.Contains(m, "invalid table name") ||
		strings.Contains(m, "not authorized")
}

func joinNote(existing, add string) string {
	if existing == "" {
		return add
	}
	return existing + "; " + add
}
