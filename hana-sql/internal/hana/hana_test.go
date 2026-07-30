package hana

import (
	"context"
	"database/sql/driver"
	"errors"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"math/big"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"

	"hana-sql/internal/config"
	"hana-sql/internal/guard"
)

func fakeConfig() *config.Config {
	return &config.Config{Host: "127.0.0.1", Port: "30015", User: "TESTUSER", Password: "s3cr3t-sentinel"}
}

// --- layer 0-3: nothing reaches the driver ------------------------------------

// Every refusable statement must be stopped by the guard BEFORE the pipeline
// opens a transaction or sends anything. The fake counts begins and queries, so
// "never reached the driver" is measured, not assumed.
func TestQueryReadOnlyRefusesBeforeTouchingTheDriver(t *testing.T) {
	writes := []string{
		`UPDATE "JIVO_OIL_HANADB"."OCRD" SET "Balance" = 0`,
		`DELETE FROM "JIVO_OIL_HANADB"."OINV"`,
		`INSERT INTO "JIVO_OIL_HANADB"."OCRD" VALUES (1)`,
		`DROP TABLE "JIVO_OIL_HANADB"."OINV"`,
		`SELECT 1 FROM DUMMY; DROP TABLE T`,
		`SELECT * FROM "JIVO_OIL_HANADB"."OCRD" FOR UPDATE`,
		`CALL "SYS"."SOME_PROC"()`,
		`EXPLAIN PLAN FOR SELECT 1 FROM DUMMY`,
		`SELECT 'abc FROM DUMMY`,
		`DO BEGIN UPDATE "JIVO_OIL_HANADB"."OCRD" SET "Balance"=0; END`,
		`SELECT COUNT(*) INTO v FROM "JIVO_OIL_HANADB"."OCRD"`,
		`COMMIT`,
	}
	db, stats := newFakeDB(t, Options{}, oneRowScript())
	defer db.Close()

	for _, stmt := range writes {
		t.Run(strings.Fields(stmt + " x")[0]+"_"+fmt.Sprint(len(stmt)), func(t *testing.T) {
			_, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, stmt)
			if err == nil {
				t.Fatalf("QueryReadOnly(%q) = nil error; a write must never be accepted", stmt)
			}
			if !guard.IsRefusal(err) {
				t.Fatalf("QueryReadOnly(%q) err = %v, want a guard refusal", stmt, err)
			}
		})
	}
	if n := stats.begins.Load(); n != 0 {
		t.Fatalf("the driver opened %d transactions for refused statements; want 0", n)
	}
	if n := stats.queries.Load(); n != 0 {
		t.Fatalf("the driver saw %d queries for refused statements; want 0", n)
	}
}

// --- layer 4: READ ONLY transaction, always rolled back -----------------------

func TestReadOnlyTransactionAlwaysRolledBack(t *testing.T) {
	db, stats := newFakeDB(t, Options{}, oneRowScript())
	defer db.Close()

	if _, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY"); err != nil {
		t.Fatalf("QueryReadOnly: %v", err)
	}
	if stats.begins.Load() != 1 {
		t.Fatalf("begins = %d, want 1", stats.begins.Load())
	}
	if stats.readOnly.Load() != 1 {
		t.Fatal("BeginTx was called without ReadOnly:true — layer 4 (HANA's own read-only access mode) is not in force")
	}
	if stats.rollbacks.Load() != 1 {
		t.Fatalf("rollbacks = %d, want 1 (the transaction must always be rolled back)", stats.rollbacks.Load())
	}
	if stats.commits.Load() != 0 {
		t.Fatalf("commits = %d, want 0", stats.commits.Load())
	}
}

// The backstop must survive an error mid-query too.
func TestRollbackHappensOnQueryError(t *testing.T) {
	sc := oneRowScript()
	sc.queryErr = errors.New("invalid table name: NOPE")
	db, stats := newFakeDB(t, Options{}, sc)
	defer db.Close()

	_, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, `SELECT * FROM "NOPE"`)
	if err == nil {
		t.Fatal("want an error")
	}
	if !strings.Contains(err.Error(), "schema-qualified") {
		t.Fatalf("an 'invalid table name' error should carry the schema-qualification hint; got %v", err)
	}
	if stats.rollbacks.Load() != 1 {
		t.Fatalf("rollbacks = %d, want 1 even on a failed query", stats.rollbacks.Load())
	}
	if stats.commits.Load() != 0 {
		t.Fatalf("commits = %d, want 0", stats.commits.Load())
	}
}

// Structural: there must be no Commit call in the package's non-test source.
// A future edit that "fixes" the rollback into a commit fails here.
func TestNoCommitInPackageSource(t *testing.T) {
	fset := token.NewFileSet()
	pkgs, err := parser.ParseDir(fset, ".", func(fi os.FileInfo) bool {
		return !strings.HasSuffix(fi.Name(), "_test.go")
	}, 0)
	if err != nil {
		t.Fatalf("parse package: %v", err)
	}
	for _, pkg := range pkgs {
		for name, file := range pkg.Files {
			ast.Inspect(file, func(n ast.Node) bool {
				sel, ok := n.(*ast.SelectorExpr)
				if ok && sel.Sel.Name == "Commit" {
					t.Errorf("%s: calls .Commit — internal/hana must never commit; the read-only transaction's only exit is Rollback",
						filepath.Base(name))
				}
				return true
			})
		}
	}
}

// --- layer 5: caps ------------------------------------------------------------

func TestRowCapTruncates(t *testing.T) {
	db, _ := newFakeDB(t, Options{Limits: Limits{MaxRows: 1000}}, nRowScript(5000))
	defer db.Close()

	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err != nil {
		t.Fatalf("QueryReadOnly: %v", err)
	}
	if res.RowCount != 1000 || len(res.Rows) != 1000 {
		t.Fatalf("RowCount = %d (rows %d), want exactly 1000", res.RowCount, len(res.Rows))
	}
	if !res.Truncated {
		t.Fatal("Truncated = false; the caller must be told the answer is partial")
	}
	if !strings.Contains(res.Note, "aggregate server-side") {
		t.Fatalf("note = %q, want the 'aggregate server-side' steer", res.Note)
	}
}

// A per-call cap may tighten the server cap but never loosen it.
func TestPerCallLimitsCanOnlyTighten(t *testing.T) {
	db, _ := newFakeDB(t, Options{Limits: Limits{MaxRows: 100}}, nRowScript(5000))
	defer db.Close()

	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{MaxRows: 10}, "SELECT 1 FROM DUMMY")
	if err != nil {
		t.Fatalf("tighten: %v", err)
	}
	if res.RowCount != 10 {
		t.Fatalf("tightened cap gave %d rows, want 10", res.RowCount)
	}

	res, err = db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{MaxRows: 100000}, "SELECT 1 FROM DUMMY")
	if err != nil {
		t.Fatalf("loosen: %v", err)
	}
	if res.RowCount != 100 {
		t.Fatalf("a caller raised the row cap to %d rows; the server ceiling of 100 must win", res.RowCount)
	}
}

func TestByteCapTruncates(t *testing.T) {
	wide := strings.Repeat("x", 4096)
	sc := &fakeScript{
		cols: []fakeCol{{name: "BLOB_TEXT", dbType: "NVARCHAR"}},
		row: func(i int) ([]driver.Value, bool) {
			if i >= 10000 {
				return nil, false
			}
			return []driver.Value{wide}, true
		},
	}
	db, _ := newFakeDB(t, Options{Limits: Limits{MaxBytes: 64 << 10}}, sc)
	defer db.Close()

	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err != nil {
		t.Fatalf("QueryReadOnly: %v", err)
	}
	if !res.Truncated {
		t.Fatal("Truncated = false; the byte cap must be reported")
	}
	if res.RowCount > 20 {
		t.Fatalf("byte cap let %d wide rows through; ~16 is the expectation for a 64 KiB cap", res.RowCount)
	}
	if !strings.Contains(res.Note, "byte cap") {
		t.Fatalf("note = %q, want the byte-cap explanation", res.Note)
	}
}

func TestTimeoutIsCleanNotAPanic(t *testing.T) {
	sc := oneRowScript()
	sc.queryDelay = 2 * time.Second
	db, stats := newFakeDB(t, Options{Limits: Limits{Timeout: 100 * time.Millisecond}}, sc)
	defer db.Close()

	_, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err == nil {
		t.Fatal("want a timeout error")
	}
	if !strings.Contains(err.Error(), "timed out") {
		t.Fatalf("err = %v, want a clean 'timed out' message", err)
	}
	if stats.commits.Load() != 0 {
		t.Fatalf("commits = %d, want 0", stats.commits.Load())
	}
}

func TestSemaphoreSerialisesPastMaxConcurrent(t *testing.T) {
	sc := oneRowScript()
	sc.queryDelay = 60 * time.Millisecond
	db, stats := newFakeDB(t, Options{MaxConcurrent: 2}, sc)
	defer db.Close()

	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if _, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY"); err != nil {
				t.Errorf("QueryReadOnly: %v", err)
			}
		}()
	}
	wg.Wait()
	if got := stats.maxInFlite.Load(); got > 2 {
		t.Fatalf("peak in-flight queries = %d, want <= 2 (the semaphore must bound load on production HANA)", got)
	}
	if stats.queries.Load() != 8 {
		t.Fatalf("queries = %d, want all 8 to have run", stats.queries.Load())
	}
}

// --- value normalization ------------------------------------------------------

func TestNormalizeValues(t *testing.T) {
	rat := func(s string) *big.Rat {
		r, ok := new(big.Rat).SetString(s)
		if !ok {
			t.Fatalf("bad rat %q", s)
		}
		return r
	}
	cases := []struct {
		name     string
		in       any
		dbType   string
		scale    int
		hasScale bool
		want     any
	}{
		// The bug this replaces: fmt "%v" on a *big.Rat printed 8210929/100.
		{"decimal_balance", rat("8210929/100"), "DECIMAL", 6, true, "82109.290000"},
		{"decimal_crore_15_digits", rat("136896549725/100"), "DECIMAL", 2, true, "1368965497.25"},
		{"decimal_ar_debit", rat("107431612455/100"), "DECIMAL", 2, true, "1074316124.55"},
		// A declared scale that would lose precision must not be used.
		{"decimal_scale_too_small", rat("1/3"), "DECIMAL", 2, true, "0.3333333333333333333333333333333333333333"},
		{"decimal_exact_beyond_scale", rat("12345/1000"), "DECIMAL", 1, true, "12.345"},
		{"decimal_no_scale", rat("5/2"), "DECIMAL", 0, false, "2.5"},
		{"decimal_integer_valued", rat("680"), "DECIMAL", 6, true, "680.000000"},
		{"date", time.Date(2026, 7, 22, 0, 0, 0, 0, time.UTC), "DATE", 0, false, "2026-07-22"},
		{"daydate", time.Date(2026, 7, 22, 0, 0, 0, 0, time.UTC), "DAYDATE", 0, false, "2026-07-22"},
		{"time", time.Date(2026, 7, 22, 15, 4, 5, 0, time.UTC), "TIME", 0, false, "15:04:05"},
		// No "Z": a HANA TIMESTAMP carries no zone (see the timestamp regression
		// test in regression_test.go for the live measurement).
		{"timestamp", time.Date(2026, 7, 22, 15, 4, 5, 0, time.UTC), "TIMESTAMP", 0, false, "2026-07-22T15:04:05"},
		// SAP B1 declares every business date as TIMESTAMP with a zero clock
		// (verified live: OINV."DocDate" is DATA_TYPE_NAME = TIMESTAMP). A
		// posting date must not come back looking like an instant.
		{"timestamp_midnight_is_a_date", time.Date(2026, 7, 30, 0, 0, 0, 0, time.UTC), "TIMESTAMP", 0, false, "2026-07-30"},
		{"timestamp_one_second_past_midnight", time.Date(2026, 7, 30, 0, 0, 1, 0, time.UTC), "TIMESTAMP", 0, false, "2026-07-30T00:00:01"},
		{"timestamp_one_nanosecond_past_midnight", time.Date(2026, 7, 30, 0, 0, 0, 1, time.UTC), "TIMESTAMP", 0, false, "2026-07-30T00:00:00.000000001"},
		{"seconddate_midnight", time.Date(2026, 7, 30, 0, 0, 0, 0, time.UTC), "SECONDDATE", 0, false, "2026-07-30"},
		{"bytes", []byte("JIVO"), "VARBINARY", 0, false, "JIVO"},
		{"null", nil, "NVARCHAR", 0, false, nil},
		{"int64", int64(3390), "BIGINT", 0, false, int64(3390)},
		{"float64", 1.5, "DOUBLE", 0, false, 1.5},
		{"string", "ORGV000044", "NVARCHAR", 0, false, "ORGV000044"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := normalize(c.in, c.dbType, c.scale, c.hasScale)
			if !reflect.DeepEqual(got, c.want) {
				t.Fatalf("normalize(%v, %s) = %#v, want %#v", c.in, c.dbType, got, c.want)
			}
			if s, ok := got.(string); ok && strings.Contains(s, "/") && strings.Contains(c.dbType, "DECIMAL") {
				t.Fatalf("normalize returned a big.Rat fraction %q — a money figure must never look like that", s)
			}
		})
	}
}

// End to end through the pipeline: a DECIMAL column arrives as an exact string.
func TestDecimalArrivesAsExactStringThroughThePipeline(t *testing.T) {
	val, _ := new(big.Rat).SetString("136896549725/100")
	sc := &fakeScript{
		cols: []fakeCol{{name: "TURNOVER", dbType: "DECIMAL", prec: 28, scale: 2, hasDec: true}},
		row: func(i int) ([]driver.Value, bool) {
			if i > 0 {
				return nil, false
			}
			return []driver.Value{val}, true
		},
	}
	db, _ := newFakeDB(t, Options{}, sc)
	defer db.Close()

	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err != nil {
		t.Fatalf("QueryReadOnly: %v", err)
	}
	if got := res.Rows[0]["TURNOVER"]; got != "1368965497.25" {
		t.Fatalf("TURNOVER = %#v, want the exact string \"1368965497.25\"", got)
	}
	if res.Columns[0].Type != "DECIMAL" {
		t.Fatalf("column type = %q, want DECIMAL so the caller can tell exact from float", res.Columns[0].Type)
	}
}

func TestLobIsCappedAndMarked(t *testing.T) {
	// The driver hands a Lob writer the bytes; capWriter is the sink.
	w := &capWriter{limit: 16}
	n, err := w.Write([]byte(strings.Repeat("a", 100)))
	if err != nil || n != 100 {
		t.Fatalf("Write = (%d, %v), want (100, nil) — a short write would stall the driver", n, err)
	}
	if len(w.buf) != 16 || !w.clipped {
		t.Fatalf("buf=%d clipped=%v, want 16 bytes and clipped=true", len(w.buf), w.clipped)
	}
	// A second write past the limit must not grow the buffer.
	w.Write([]byte("bbbb"))
	if len(w.buf) != 16 {
		t.Fatalf("buf grew to %d past the cap", len(w.buf))
	}
	w.reset()
	if len(w.buf) != 0 || w.clipped {
		t.Fatal("reset did not clear the buffer/flag; rows would bleed into each other")
	}
}

func TestLobColumnDetection(t *testing.T) {
	for _, n := range []string{"CLOB", "NCLOB", "BLOB", "TEXT", "nclob"} {
		if !isLobColumn(nil, n) {
			t.Fatalf("isLobColumn(%q) = false; scanning a LOB into `any` yields the raw locator, not the text", n)
		}
	}
	for _, n := range []string{"NVARCHAR", "DECIMAL", "INTEGER"} {
		if isLobColumn(nil, n) {
			t.Fatalf("isLobColumn(%q) = true; that would route an ordinary column through the LOB path", n)
		}
	}
}

// Two columns with the same name must not collapse into one JSON key.
func TestDuplicateColumnNamesAreDisambiguated(t *testing.T) {
	sc := &fakeScript{
		cols: []fakeCol{{name: "N", dbType: "INTEGER"}, {name: "N", dbType: "INTEGER"}, {name: "", dbType: "INTEGER"}},
		row: func(i int) ([]driver.Value, bool) {
			if i > 0 {
				return nil, false
			}
			return []driver.Value{int64(1), int64(2), int64(3)}, true
		},
	}
	db, _ := newFakeDB(t, Options{}, sc)
	defer db.Close()

	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err != nil {
		t.Fatalf("QueryReadOnly: %v", err)
	}
	if len(res.Rows[0]) != 3 {
		t.Fatalf("row has %d keys (%v), want 3 — a duplicate name silently dropped a value", len(res.Rows[0]), res.Rows[0])
	}
	for _, want := range []string{"N", "N_2", "COL_3"} {
		if _, ok := res.Rows[0][want]; !ok {
			t.Fatalf("row is missing key %q; got %v", want, res.Rows[0])
		}
	}
}

func TestCellText(t *testing.T) {
	cases := []struct {
		name string
		in   any
		want string
	}{
		{"null", nil, "NULL"},
		{"string", "x", "x"},
		{"int", int64(5), "5"},
		// HANA returns DOUBLE for the standard money recipe
		// ROUND(TO_DOUBLE(SUM(...)), 2). Go's %v renders that as
		// 1.07431612455e+09 — measured against the live database, and unreadable
		// as a receivables figure.
		{"money_double_is_not_exponential", 1074316124.55, "1074316124.55"},
		{"turnover_double", 1368965498.12, "1368965498.12"},
		{"small_double", 1.5, "1.5"},
		{"whole_double", float64(680), "680"},
		{"negative_double", -8210929.29, "-8210929.29"},
		{"float32", float32(2.5), "2.5"},
		// DECIMAL already arrives as an exact string and must pass through
		// untouched.
		{"decimal_string_passthrough", "1074316124.550000", "1074316124.550000"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := CellText(c.in)
			if got != c.want {
				t.Fatalf("CellText(%v) = %q, want %q", c.in, got, c.want)
			}
			if strings.ContainsAny(got, "eE") && c.name != "string" {
				t.Fatalf("CellText(%v) = %q — exponential notation is not a number an Accounts user can read", c.in, got)
			}
		})
	}
}

// --- streaming (the CLI path) --------------------------------------------------

func TestStreamReadOnlyUsesTheSamePipeline(t *testing.T) {
	db, stats := newFakeDB(t, Options{}, nRowScript(3))
	defer db.Close()

	var cols []Column
	var rows []map[string]any
	err := db.StreamReadOnly(context.Background(), guard.CLIPolicy, Limits{}, "SELECT 1 FROM DUMMY", nil,
		func(c []Column) error { cols = c; return nil },
		func(m map[string]any) error { rows = append(rows, m); return nil })
	if err != nil {
		t.Fatalf("StreamReadOnly: %v", err)
	}
	if len(cols) == 0 || len(rows) != 3 {
		t.Fatalf("cols=%d rows=%d, want 1+ and 3", len(cols), len(rows))
	}
	if stats.readOnly.Load() != 1 || stats.rollbacks.Load() != 1 || stats.commits.Load() != 0 {
		t.Fatalf("the CLI path skipped a layer: readOnly=%d rollbacks=%d commits=%d",
			stats.readOnly.Load(), stats.rollbacks.Load(), stats.commits.Load())
	}

	// ... and it is guarded too.
	err = db.StreamReadOnly(context.Background(), guard.CLIPolicy, Limits{}, `UPDATE OCRD SET "Balance"=0`, nil,
		func([]Column) error { return nil }, func(map[string]any) error { return nil })
	if !guard.IsRefusal(err) {
		t.Fatalf("StreamReadOnly accepted an UPDATE (err=%v)", err)
	}
}

// --- catalog SQL --------------------------------------------------------------

// Our own fixed catalog SQL must pass the guard. If it did not, the guard would
// be producing false positives on ordinary read SQL.
func TestCatalogSQLPassesGuard(t *testing.T) {
	stmts := CatalogStatements()
	if len(stmts) < 5 {
		t.Fatalf("CatalogStatements() returned %d statements; the catalog has more than that", len(stmts))
	}
	for i, s := range stmts {
		if err := guard.Check(s, guard.MCPPolicy); err != nil {
			t.Errorf("catalog statement %d is refused by the read-only guard: %v\n%s", i, err, s)
		}
	}
}

func TestCatalogUsesBindParametersNotConcatenation(t *testing.T) {
	db, stats := newFakeDB(t, Options{}, oneRowScript())
	defer db.Close()

	evil := `X" OR 1=1 --`
	if _, err := db.Columns(context.Background(), "JIVO_OIL_HANADB", evil, ""); err != nil {
		t.Fatalf("Columns: %v", err)
	}
	stmt, _ := stats.lastStmt.Load().(string)
	if strings.Contains(stmt, evil) {
		t.Fatalf("caller input was concatenated into the SQL text:\n%s", stmt)
	}
	args, _ := stats.lastArgs.Load().([]driver.NamedValue)
	found := false
	for _, a := range args {
		if s, ok := a.Value.(string); ok && s == evil {
			found = true
		}
	}
	if !found {
		t.Fatalf("the table name was not passed as a bind parameter; args = %v", args)
	}
}

func TestResolveSchemas(t *testing.T) {
	all, _ := resolveSchemas("")
	if len(all) != 3 {
		t.Fatalf("empty schema resolved to %v, want all three companies", all)
	}
	one, _ := resolveSchemas("jivo_beverages_hanadb")
	if len(one) != 1 || one[0] != "JIVO_BEVERAGES_HANADB" {
		t.Fatalf("lower-case schema resolved to %v, want [JIVO_BEVERAGES_HANADB]", one)
	}
	sys, _ := resolveSchemas("sys")
	if len(sys) != 1 || sys[0] != "SYS" {
		t.Fatalf("SYS resolved to %v", sys)
	}
}

// --- credentials never leak ----------------------------------------------------

func TestErrorsAreScrubbedOfThePassword(t *testing.T) {
	sc := oneRowScript()
	sc.queryErr = errors.New("auth failed for user TESTUSER with password s3cr3t-sentinel")
	db, _ := newFakeDB(t, Options{}, sc)
	defer db.Close()

	_, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err == nil {
		t.Fatal("want an error")
	}
	if strings.Contains(err.Error(), "s3cr3t-sentinel") {
		t.Fatalf("the password appeared in an error returned to the caller: %v", err)
	}
	if !strings.Contains(err.Error(), "****") {
		t.Fatalf("expected the password to be masked; got %v", err)
	}
}

func TestAuditLineIsWrittenAndScrubbed(t *testing.T) {
	var buf strings.Builder
	db, _ := newFakeDB(t, Options{Log: &buf}, oneRowScript())
	defer db.Close()

	db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY -- s3cr3t-sentinel")
	db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, `UPDATE OCRD SET "Balance"=0`)

	out := buf.String()
	if !strings.Contains(out, "verdict=accepted") || !strings.Contains(out, "verdict=refused") {
		t.Fatalf("audit log is missing a verdict:\n%s", out)
	}
	if strings.Contains(out, "s3cr3t-sentinel") {
		t.Fatalf("the audit log leaked the password:\n%s", out)
	}
}

// --- helpers ------------------------------------------------------------------

func oneRowScript() *fakeScript {
	return &fakeScript{
		cols: []fakeCol{{name: "ONE", dbType: "INTEGER"}},
		row: func(i int) ([]driver.Value, bool) {
			if i > 0 {
				return nil, false
			}
			return []driver.Value{int64(1)}, true
		},
	}
}

func nRowScript(n int) *fakeScript {
	return &fakeScript{
		cols: []fakeCol{{name: "N", dbType: "INTEGER"}, {name: "S", dbType: "NVARCHAR"}},
		row: func(i int) ([]driver.Value, bool) {
			if i >= n {
				return nil, false
			}
			return []driver.Value{int64(i), fmt.Sprintf("row-%d", i)}, true
		},
	}
}
