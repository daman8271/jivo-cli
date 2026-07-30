package hana

import (
	"context"
	"database/sql"
	"database/sql/driver"
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"

	"hana-sql/internal/guard"
)

// Regression tests for the reviewer/tester findings against internal/hana.
// Each test names the defect it locks down, with the live evidence that proved
// it, so a future "simplification" that reintroduces the bug fails here.

// --- catalog: unknown schema is an error, not an empty success -----------------

// FINDING (BLOCKER + P2): resolveSchemas passed an unrecognised schema straight
// through upper-cased, so hana_tables{schema:"JIVO_BEVERAGE_HANADB"} (one
// missing S), {schema:"Beverages"} and {schema:"Oil"} each returned
// isError:false, row_count:0, note:"" against the live database. A one-letter
// typo was indistinguishable from "this company has no data" — the same
// silent-wrong-answer class the `company` argument is loudly refused for.
func TestUnknownSchemaIsRefusedNotAnEmptySuccess(t *testing.T) {
	cases := []struct {
		in       string
		wantHint string // the "did you mean" the caller should get
	}{
		{"JIVO_BEVERAGE_HANADB", "JIVO_BEVERAGES_HANADB"}, // the live typo
		{"Beverages", "JIVO_BEVERAGES_HANADB"},
		{"Oil", "JIVO_OIL_HANADB"},
		{"OIL", "JIVO_OIL_HANADB"},
		{"Mart", "JIVO_MART_HANADB"},
		{"JIVO_OIL", "JIVO_OIL_HANADB"},
		{"nonsense_schema_name", ""},
	}
	for _, c := range cases {
		t.Run(c.in, func(t *testing.T) {
			got, err := resolveSchemas(c.in)
			if err == nil {
				t.Fatalf("resolveSchemas(%q) = %v with no error; an unknown schema must be refused, "+
					"because an empty result reads as \"this company has no data\"", c.in, got)
			}
			if got != nil {
				t.Fatalf("resolveSchemas(%q) returned schemas %v alongside the error", c.in, got)
			}
			for _, s := range Schemas {
				if !strings.Contains(err.Error(), s) {
					t.Fatalf("the refusal for %q does not name %s, so the caller cannot self-correct: %v", c.in, s, err)
				}
			}
			if c.wantHint != "" && !strings.Contains(err.Error(), "Did you mean \""+c.wantHint+"\"") {
				t.Fatalf("resolveSchemas(%q) error = %v, want a \"did you mean %s\" hint", c.in, err, c.wantHint)
			}
		})
	}
}

// The refusal must not have broken the legitimate cases.
func TestKnownSchemasStillResolve(t *testing.T) {
	all, err := resolveSchemas("")
	if err != nil || len(all) != 3 {
		t.Fatalf(`resolveSchemas("") = (%v, %v), want all three companies`, all, err)
	}
	for _, in := range []string{"JIVO_OIL_HANADB", "jivo_oil_hanadb", " JIVO_OIL_HANADB "} {
		got, err := resolveSchemas(in)
		if err != nil || len(got) != 1 || got[0] != "JIVO_OIL_HANADB" {
			t.Fatalf("resolveSchemas(%q) = (%v, %v)", in, got, err)
		}
	}
	// HANA's own catalog schemas stay reachable: that is how the tool answers
	// questions about SYS.TABLES itself.
	for _, in := range []string{"SYS", "sys", "PUBLIC", "_SYS_BIC", "SYS_BIC"} {
		got, err := resolveSchemas(in)
		if err != nil || len(got) != 1 {
			t.Fatalf("resolveSchemas(%q) = (%v, %v), want the catalog schema through", in, got, err)
		}
	}
}

// Tables and Columns must surface the refusal rather than swallow it.
func TestCatalogToolsPropagateTheUnknownSchemaError(t *testing.T) {
	db, stats := newFakeDB(t, Options{}, oneRowScript())
	defer db.Close()
	ctx := context.Background()

	if _, err := db.Tables(ctx, TableQuery{Schema: "JIVO_BEVERAGE_HANADB"}); err == nil {
		t.Fatal("Tables accepted a misspelt schema")
	}
	if _, err := db.Columns(ctx, "Beverages", "OINV", ""); err == nil {
		t.Fatal("Columns accepted a company name where a schema was required")
	}
	if n := stats.queries.Load(); n != 0 {
		t.Fatalf("%d queries were sent to the database for an unknown schema; validation must happen first", n)
	}
}

// --- catalog: a wrong-case table name is explained, not answered with silence --

// FINDING (P2): Columns upper-cased the SCHEMA but not the TABLE, so
// hana_columns{schema:"JIVO_OIL_HANADB",table:"oinv"} returned isError:false,
// row_count:0 and no note against the live database, while "OINV" returned rows.
// A model reads that as "this table has no columns".
func TestWrongCaseTableNameIsExplainedNotEmpty(t *testing.T) {
	// The catalog probe answers "OINV exists" for the exists-check query.
	sc := &fakeScript{
		cols: []fakeCol{{name: "NAME", dbType: "NVARCHAR"}, {name: "KIND", dbType: "NVARCHAR"}},
		row: func(i int) ([]driver.Value, bool) {
			if i > 0 {
				return nil, false
			}
			return []driver.Value{"OINV", "TABLE"}, true
		},
	}
	// The fake answers every statement from one script, so the two halves are
	// driven separately. First: nothing matches at all — neither the column query
	// nor the exists probe — which is the "no such table" case.
	empty := &fakeScript{
		cols: []fakeCol{{name: "COLUMN_NAME", dbType: "NVARCHAR"}},
		row:  func(int) ([]driver.Value, bool) { return nil, false },
	}
	db, _ := newFakeDB(t, Options{}, empty)
	defer db.Close()

	res, err := db.Columns(context.Background(), "JIVO_OIL_HANADB", "oinv", "")
	if err == nil {
		t.Fatalf("Columns returned a clean empty success (%d rows, note=%q) for a table with no columns; "+
			"an empty column list reads as \"this table has no columns\"", res.RowCount, res.Note)
	}
	if !strings.Contains(err.Error(), "refusing to return an empty column list") {
		t.Fatalf("error = %v, want the explicit refusal", err)
	}
	if !strings.Contains(err.Error(), "hana_tables") {
		t.Fatalf("error = %v, want it to name the tool that finds the right spelling", err)
	}

	// And when the name DOES exist under a different case, say exactly that.
	db2, _ := newFakeDB(t, Options{}, sc)
	defer db2.Close()
	res2, err2 := db2.explainEmptyColumns(context.Background(), "JIVO_OIL_HANADB", "oinv", "",
		&Result{Rows: []map[string]any{}})
	if err2 == nil {
		t.Fatalf("a wrong-CASE table name came back as a clean empty result: %+v", res2)
	}
	if !strings.Contains(err2.Error(), "case-sensitive") || !strings.Contains(err2.Error(), `"OINV"`) {
		t.Fatalf("error = %v, want it to name the correct spelling and say HANA is case-sensitive", err2)
	}
}

// --- catalog: a truncated listing must say what it does NOT contain ------------

// FINDING (P1, CONFIRMED LIVE): hana_tables with no `schema` argument returned
// only JIVO_BEVERAGES_HANADB — row_count 1000, truncated true, rows spanning
// '@ABRAND'..'ECM2', all Beverages — while MCP.md and facts.go advertised it as
// "search all three companies at once" (there are 9244 tables: Oil 3111 / Mart
// 3046 / Beverages 3087). The note said "aggregate server-side with
// SUM/COUNT/GROUP BY instead of paging rows", which is impossible advice for a
// catalog listing, and no tool exposed an offset, so the caller could not
// recover. The listing is ordered by schema, so the missing companies are
// knowable — and must be named.
func TestTruncatedTableListingNamesTheMissingCompanies(t *testing.T) {
	// 1200 rows, all in the alphabetically-first schema, exactly like the live
	// three-schema listing that stopped inside Beverages.
	sc := &fakeScript{
		cols: []fakeCol{
			{name: "SCHEMA_NAME", dbType: "NVARCHAR"},
			{name: "TABLE_NAME", dbType: "NVARCHAR"},
			{name: "KIND", dbType: "NVARCHAR"},
			{name: "ROW_COUNT", dbType: "BIGINT"},
		},
		row: func(i int) ([]driver.Value, bool) {
			if i >= 1200 {
				return nil, false
			}
			return []driver.Value{"JIVO_BEVERAGES_HANADB", fmt.Sprintf("T%04d", i), "TABLE", int64(i)}, true
		},
	}
	db, _ := newFakeDB(t, Options{Limits: Limits{MaxRows: 1000}}, sc)
	defer db.Close()

	res, err := db.Tables(context.Background(), TableQuery{})
	if err != nil {
		t.Fatalf("Tables: %v", err)
	}
	if !res.Truncated || res.RowCount != 1000 {
		t.Fatalf("RowCount=%d truncated=%v, want 1000 and true", res.RowCount, res.Truncated)
	}
	if strings.Contains(res.Note, "SUM/COUNT/GROUP BY") {
		t.Fatalf("the catalog listing still tells the caller to aggregate server-side, which is impossible for a table list: %q", res.Note)
	}
	for _, must := range []string{
		"PARTIAL CATALOG",
		"JIVO_BEVERAGES_HANADB",             // what this page covers
		"NOTHING from",                      // and what it does not
		"JIVO_OIL_HANADB, JIVO_MART_HANADB", // named explicitly
		"offset=1000",                       // and how to get the rest
	} {
		if !strings.Contains(res.Note, must) {
			t.Fatalf("truncation note is missing %q — a partial catalog that looks whole is how a model concludes a company has no tables.\nnote: %s", must, res.Note)
		}
	}
}

// The recovery path the note points at must actually exist and work.
func TestTablesOffsetPagesTheListing(t *testing.T) {
	db, stats := newFakeDB(t, Options{Limits: Limits{MaxRows: 1000}}, oneRowScript())
	defer db.Close()

	res, err := db.Tables(context.Background(), TableQuery{Offset: 1000})
	if err != nil {
		t.Fatalf("Tables(offset=1000): %v", err)
	}
	stmt, _ := stats.lastStmt.Load().(string)
	if !strings.Contains(stmt, "LIMIT 1001 OFFSET 1000") {
		t.Fatalf("offset was not pushed into the SQL:\n%s", stmt)
	}
	if !strings.Contains(res.Note, "offset 1000") {
		t.Fatalf("a paged answer must say where it starts; note = %q", res.Note)
	}
	if _, err := db.Tables(context.Background(), TableQuery{Offset: -1}); err == nil {
		t.Fatal("a negative offset was accepted")
	}
	// The row cap is fetched as cap+1 so truncation is decided on real evidence
	// (there IS a next row), never guessed from "we got exactly the cap".
	if !strings.Contains(stmt, "LIMIT 1001") {
		t.Fatalf("the catalog should over-fetch by one row to decide truncation honestly:\n%s", stmt)
	}
}

// no_row_counts is the documented escape from the expensive default: the
// unfiltered three-schema listing joins SYS.M_TABLES and took 7.1s on the VPS.
func TestTablesCanSkipTheRowCountJoin(t *testing.T) {
	db, stats := newFakeDB(t, Options{}, oneRowScript())
	defer db.Close()

	if _, err := db.Tables(context.Background(), TableQuery{NoRowCounts: true}); err != nil {
		t.Fatalf("Tables: %v", err)
	}
	stmt, _ := stats.lastStmt.Load().(string)
	if strings.Contains(stmt, "M_TABLES") {
		t.Fatalf("no_row_counts still joined the monitoring view:\n%s", stmt)
	}
}

// --- layer 5: `truncated` must mean exactly one thing --------------------------

// FINDING (P2, reproduced with the package's own in-memory driver): the MaxBytes
// check ran AFTER the row was emitted, so a result set that ended exactly on the
// cap reported truncated:true with nothing cut (3 rows, MaxBytes 300 -> all 3
// rows returned, truncated:true, note "response byte cap reached"). The row cap
// checked BEFORE consuming and was honest, so the two cap paths disagreed about
// what truncation means — which is how a caller learns to distrust the flag.
func TestByteCapDoesNotFalsePositiveOnAnExactFit(t *testing.T) {
	// Find the payload size of exactly 3 rows, then set the cap to it: the old
	// code reported truncated:true here.
	sc := func() *fakeScript {
		return &fakeScript{
			cols: []fakeCol{{name: "N", dbType: "INTEGER"}, {name: "S", dbType: "NVARCHAR"}},
			row: func(i int) ([]driver.Value, bool) {
				if i >= 3 {
					return nil, false
				}
				return []driver.Value{int64(i), fmt.Sprintf("row-%d", i)}, true
			},
		}
	}
	measure, _ := newFakeDB(t, Options{}, sc())
	full, err := measure.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	measure.Close()
	if err != nil {
		t.Fatalf("measure: %v", err)
	}
	if full.RowCount != 3 || full.Truncated {
		t.Fatalf("uncapped baseline is wrong: rows=%d truncated=%v", full.RowCount, full.Truncated)
	}

	// Sweep every cap from "just under one row" to "well over three": whenever
	// all three rows come back, truncated MUST be false. The reviewer's exact
	// repro (MaxBytes 300, 3 rows) is inside this range.
	for limit := 1; limit <= 400; limit++ {
		db, _ := newFakeDB(t, Options{Limits: Limits{MaxBytes: limit}}, sc())
		res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
		db.Close()
		if err != nil {
			t.Fatalf("MaxBytes=%d: %v", limit, err)
		}
		if res.RowCount == 3 && res.Truncated {
			t.Fatalf("MaxBytes=%d returned all 3 rows but reported truncated:true (note %q) — "+
				"`truncated` must mean \"there was at least one more row and you are not seeing it\"", limit, res.Note)
		}
		if res.RowCount < 3 && !res.Truncated {
			t.Fatalf("MaxBytes=%d returned %d of 3 rows with truncated:false — silent loss", limit, res.RowCount)
		}
	}
}

// The same rule for the row cap: exactly-N rows under a cap of N is complete.
func TestRowCapDoesNotFalsePositiveOnAnExactFit(t *testing.T) {
	db, _ := newFakeDB(t, Options{Limits: Limits{MaxRows: 3}}, nRowScript(3))
	defer db.Close()

	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err != nil {
		t.Fatalf("QueryReadOnly: %v", err)
	}
	if res.RowCount != 3 {
		t.Fatalf("RowCount = %d, want 3", res.RowCount)
	}
	if res.Truncated {
		t.Fatalf("3 rows under a cap of 3 reported truncated:true (note %q); nothing was cut", res.Note)
	}
}

// --- layer 5: the deadline must bound the QUEUE, not just the statement --------

// FINDING (P2): the semaphore was taken BEFORE the per-call timeout was applied,
// so a caller asking for timeout_ms:100 behind one in-flight 1.5s query returned
// after 1.501s — its own deadline did not bound the wait. Worse, a client that
// had already given up still eventually ran its query against production HANA.
func TestOwnDeadlineBoundsTheQueueWait(t *testing.T) {
	sc := oneRowScript()
	sc.queryDelay = 1500 * time.Millisecond
	db, stats := newFakeDB(t, Options{MaxConcurrent: 1}, sc)
	defer db.Close()

	started := make(chan struct{})
	done := make(chan struct{})
	go func() {
		close(started)
		db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
		close(done)
	}()
	<-started
	time.Sleep(150 * time.Millisecond) // let the hog take the only slot

	t0 := time.Now()
	_, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy,
		Limits{Timeout: 100 * time.Millisecond}, "SELECT 1 FROM DUMMY")
	waited := time.Since(t0)

	if err == nil {
		t.Fatal("the queued call succeeded; it should have given up on its own deadline")
	}
	if waited > 700*time.Millisecond {
		t.Fatalf("a timeout_ms:100 call waited %s behind a 1.5s query — its own deadline must bound the QUEUE, not only the statement", waited)
	}
	if !strings.Contains(err.Error(), "free query slot") || !strings.Contains(err.Error(), "nothing was sent to HANA") {
		t.Fatalf("err = %v; a caller that died in the queue must be told it never reached the database", err)
	}
	<-done
	// The abandoned call must never have been sent: one query ran, not two.
	if n := stats.queries.Load(); n != 1 {
		t.Fatalf("%d queries reached the driver, want 1 — a caller that gave up must not still hit production HANA", n)
	}
}

// A cancelled caller (client disconnect, gateway timeout) is the other half.
func TestCancelledCallerNeverReachesTheDatabase(t *testing.T) {
	sc := oneRowScript()
	sc.queryDelay = 1500 * time.Millisecond
	db, stats := newFakeDB(t, Options{MaxConcurrent: 1}, sc)
	defer db.Close()

	go db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	time.Sleep(150 * time.Millisecond)

	ctx, cancel := context.WithCancel(context.Background())
	go func() { time.Sleep(50 * time.Millisecond); cancel() }()
	_, err := db.QueryReadOnly(ctx, guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err == nil {
		t.Fatal("a cancelled caller still got an answer")
	}
	if !strings.Contains(err.Error(), "nothing was sent to HANA") {
		t.Fatalf("err = %v, want the queue-cancellation message", err)
	}
	time.Sleep(1600 * time.Millisecond)
	if n := stats.queries.Load(); n != 1 {
		t.Fatalf("%d queries reached the driver; the abandoned call must never have been sent", n)
	}
}

// --- dial errors must name the right phase -------------------------------------

// FINDING (P3 + "Timeout consumed by the DIAL"): a short per-call timeout that
// elapsed while the FIRST connection was being opened surfaced as "could not
// connect to HANA at 103.89.45.192:30015 (tried plaintext and TLS): context
// deadline exceeded" — blaming the office tunnel for the caller's own limit,
// which sends whoever is on call to the wrong place.
func TestDialTimeoutIsReportedAsTheCallersOwnDeadline(t *testing.T) {
	d := New(fakeConfig(), Options{Limits: Limits{Timeout: 50 * time.Millisecond}})
	defer d.Close()
	// A dial that outlives the caller's deadline, exactly like the first call
	// after startup into a slow tunnel.
	d.dial = slowDial(2 * time.Second)

	_, err := d.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err == nil {
		t.Fatal("want an error")
	}
	msg := err.Error()
	if !strings.Contains(msg, "connection SETUP") {
		t.Fatalf("err = %v; a deadline spent DIALLING must say so, not read as \"HANA is unreachable\"", err)
	}
	if strings.Contains(msg, "tried plaintext and TLS") {
		t.Fatalf("err = %v; that message blames the tunnel for the caller's own timeout", err)
	}
	if !strings.Contains(msg, "50ms") {
		t.Fatalf("err = %v, want it to quote the deadline that actually elapsed", err)
	}
}

// Mode()/doctor must not queue behind a slow dial: the state lock is never held
// across one.
func TestModeIsNotBlockedByASlowDial(t *testing.T) {
	d := New(fakeConfig(), Options{})
	defer d.Close()
	d.dial = slowDial(600 * time.Millisecond)

	go d.Pool(context.Background()) //nolint:errcheck // we only care that it is in flight
	time.Sleep(100 * time.Millisecond)

	t0 := time.Now()
	_ = d.Mode()
	if waited := time.Since(t0); waited > 100*time.Millisecond {
		t.Fatalf("Mode() waited %s behind an in-flight dial; hana_doctor must stay answerable while the tunnel is slow", waited)
	}
}

// --- CLI opts out of the LOB cap too ------------------------------------------

// FINDING (P3): the CLI opted out of the row cap, byte cap and statement
// deadline but NOT the 8 KiB LobLimit, which New applies to a zero-value
// Options. A 40 KB NCLOB came back as 8205 bytes ending " …[clipped]", so
// `hana-sql "SELECT DEFINITION FROM SYS.VIEWS …"` silently handed a human a
// fragment where the old CLI had no length limit.
func TestNegativeLobLimitMeansNoLimit(t *testing.T) {
	if got := New(fakeConfig(), Options{}).opts.LobLimit; got != DefaultLobLimit {
		t.Fatalf("a zero LobLimit resolved to %d, want the %d default", got, DefaultLobLimit)
	}
	if got := New(fakeConfig(), Options{LobLimit: -1}).opts.LobLimit; got >= 0 {
		t.Fatalf("LobLimit -1 resolved to %d; a negative value must survive as \"no limit\"", got)
	}
	// And the sink honours it: 40 KB in, 40 KB out, no clip marker.
	w := &capWriter{limit: -1}
	big := strings.Repeat("x", 40<<10)
	if n, err := w.Write([]byte(big)); n != len(big) || err != nil {
		t.Fatalf("Write = (%d, %v)", n, err)
	}
	if len(w.buf) != len(big) || w.clipped {
		t.Fatalf("an unlimited LOB sink kept %d of %d bytes (clipped=%v)", len(w.buf), len(big), w.clipped)
	}
}

// --- helpers -------------------------------------------------------------------

func slowDial(d time.Duration) func(context.Context) (*sql.DB, string, error) {
	return func(ctx context.Context) (*sql.DB, string, error) {
		select {
		case <-time.After(d):
			return nil, "", errors.New("could not connect to HANA at 127.0.0.1:30015 (tried plaintext and TLS): dial tcp: i/o timeout")
		case <-ctx.Done():
			return nil, "", ctx.Err()
		}
	}
}

// --- value rendering -----------------------------------------------------------

// FINDING (P2, CONFIRMED LIVE): timeString's default branch rendered a
// TIMESTAMP with a clock using time.RFC3339Nano, which stamps a "Z" UTC suffix
// on a value carrying the server's LOCAL wall clock. One live row proved it:
//
//	SELECT CURRENT_TIMESTAMP, CURRENT_UTCTIMESTAMP FROM DUMMY
//	  -> "2026-07-30T19:33:19.913Z"   (rendered by this code)
//	  -> "2026-07-30T14:03:19.913"    (the actual UTC instant)
//
// The first is IST published as UTC — 5h30m wrong. A HANA TIMESTAMP has no zone
// at all, so the truthful rendering carries no zone suffix. MCP.md asserted
// "Timestamps with a clock -> RFC3339Nano" with no caveat; the midnight rule was
// added for exactly this honesty reason and the non-midnight branch had the same
// disease.
func TestTimestampWithAClockCarriesNoFalseZoneSuffix(t *testing.T) {
	// The live IST wall clock, as HANA handed it over.
	ist := time.Date(2026, 7, 30, 19, 33, 19, 913000000, time.UTC)
	got := timeString(ist, "TIMESTAMP")
	if strings.HasSuffix(got, "Z") || strings.Contains(got, "+") {
		t.Fatalf("timeString = %q — a HANA TIMESTAMP carries NO time zone, and a %q suffix turns the server's "+
			"local wall clock into a UTC claim that was measured 5h30m wrong", got, "Z")
	}
	if got != "2026-07-30T19:33:19.913" {
		t.Fatalf("timeString = %q, want the bare wall clock \"2026-07-30T19:33:19.913\"", got)
	}

	// Sub-second digits (HANA keeps up to 7) must still survive.
	if got := timeString(time.Date(2026, 7, 30, 9, 15, 0, 1234567, time.UTC), "TIMESTAMP"); got != "2026-07-30T09:15:00.001234567" {
		t.Fatalf("sub-second digits lost: %q", got)
	}
	// A whole second reads cleanly, with no trailing zeros.
	if got := timeString(time.Date(2026, 7, 30, 9, 15, 0, 0, time.UTC), "TIMESTAMP"); got != "2026-07-30T09:15:00" {
		t.Fatalf("whole-second timestamp = %q", got)
	}
	// The midnight rule is untouched: a SAP B1 business date stays a bare date.
	if got := timeString(time.Date(2026, 7, 30, 0, 0, 0, 0, time.UTC), "TIMESTAMP"); got != "2026-07-30" {
		t.Fatalf("midnight timestamp = %q, want a bare date", got)
	}
	// And the location the driver happens to attach must not leak either.
	inIST := time.Date(2026, 7, 30, 19, 33, 19, 0, time.FixedZone("IST", 5*3600+1800))
	if got := timeString(inIST, "TIMESTAMP"); strings.Contains(got, "+05:30") {
		t.Fatalf("timeString = %q; the driver's attached location must not be published as a zone", got)
	}
}

// FINDING (P2, CONFIRMED LIVE): the duplicate-column rename used a per-name
// counter (seen[name]++ / "%s_%d"), which could collide with a REAL column of
// the generated name and silently drop a value.
//
//	SELECT 1 AS X, 2 AS X, 3 AS X_2 FROM DUMMY
//	  -> columns ["X","X_2","X_2"], rows [{"X":1,"X_2":3}]
//
// The value 2 was gone and the advertised `columns` array disagreed with the row
// keys — the exact silent data loss the function's own comment claims to
// prevent. The generated name must be checked against every name already
// assigned, not against a per-name counter.
func TestDuplicateColumnRenameCannotCollideWithARealColumn(t *testing.T) {
	cases := []struct {
		names []string
		want  []string
	}{
		// The reviewer's live repro. The real X_2 keeps ITS name; the generated
		// disambiguator moves past it.
		{[]string{"X", "X", "X_2"}, []string{"X", "X_3", "X_2"}},
		{[]string{"X", "X_2", "X"}, []string{"X", "X_2", "X_3"}},
		{[]string{"X", "X", "X_2", "X_3"}, []string{"X", "X_4", "X_2", "X_3"}},
		{[]string{"A", "A", "A", "A_2"}, []string{"A", "A_3", "A_4", "A_2"}},
		// The unnamed-column path collides too: COL_1 belongs to the real column.
		{[]string{"", "COL_1", ""}, []string{"COL_1_2", "COL_1", "COL_3"}},
		{[]string{"N", "N", "N", "N", "N_2"}, []string{"N", "N_3", "N_4", "N_5", "N_2"}},
		// No duplicates at all: nothing may be renamed.
		{[]string{"CardCode", "CardName", "Balance"}, []string{"CardCode", "CardName", "Balance"}},
	}
	for _, c := range cases {
		t.Run(strings.Join(c.names, "|"), func(t *testing.T) {
			plans := newColPlans(c.names, nil, 0)
			if len(plans) != len(c.names) {
				t.Fatalf("got %d plans for %d columns", len(plans), len(c.names))
			}
			seen := map[string]bool{}
			for i, p := range plans {
				if p.col.Name == "" {
					t.Fatalf("column %d has no name", i)
				}
				if seen[p.col.Name] {
					t.Fatalf("column %d reuses the name %q — two columns collapse into one JSON key and a value is dropped; "+
						"plans: %v", i, p.col.Name, planNames(plans))
				}
				seen[p.col.Name] = true
			}
			if got := planNames(plans); strings.Join(got, "|") != strings.Join(c.want, "|") {
				t.Fatalf("newColPlans(%v) = %v, want %v — a column that CAN keep its own name must keep it, "+
					"and a generated name must never take one a real column claims", c.names, got, c.want)
			}
		})
	}
}

// End to end: the row must carry one key per column, and `columns` must agree
// with the row keys.
func TestColumnsArrayAgreesWithRowKeys(t *testing.T) {
	sc := &fakeScript{
		cols: []fakeCol{
			{name: "X", dbType: "INTEGER"},
			{name: "X", dbType: "INTEGER"},
			{name: "X_2", dbType: "INTEGER"},
		},
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
	row := res.Rows[0]
	if len(row) != 3 {
		t.Fatalf("row has %d keys (%v), want 3 — SELECT 1 AS X, 2 AS X, 3 AS X_2 must not lose the value 2", len(row), row)
	}
	values := map[int64]bool{}
	for _, v := range row {
		if n, ok := v.(int64); ok {
			values[n] = true
		}
	}
	for _, want := range []int64{1, 2, 3} {
		if !values[want] {
			t.Fatalf("the value %d was dropped; row = %v", want, row)
		}
	}
	for _, c := range res.Columns {
		if _, ok := row[c.Name]; !ok {
			t.Fatalf("columns advertises %q but the row has no such key (%v) — the two must never disagree", c.Name, row)
		}
	}
}

// FINDING ("Doc/behaviour mismatch on columns[].type"): go-hdb reports HANA's
// INTERNAL storage type, not the declared type. Live on 2026-07-30, OINV
// ."DocDate" and "CreateDate" came back as LONGDATE, TO_DATE() as DAYDATE and
// every DECIMAL as FIXED12 — while SYS.TABLE_COLUMNS reports TIMESTAMP and
// DECIMAL for the same columns. Callers are told to use columns[].type to tell
// an exact DECIMAL from a float DOUBLE, so reporting FIXED12 breaks the one
// promise the field exists to keep.
func TestColumnTypeNamesAreSQLTypesNotHanaStorageTypes(t *testing.T) {
	cases := map[string]string{
		"LONGDATE":   "TIMESTAMP",
		"longdate":   "TIMESTAMP",
		"DAYDATE":    "DATE",
		"SECONDTIME": "TIME",
		"FIXED8":     "DECIMAL",
		"FIXED12":    "DECIMAL",
		"FIXED16":    "DECIMAL",
		// Everything else passes through untouched.
		"DOUBLE":     "DOUBLE",
		"NVARCHAR":   "NVARCHAR",
		"DECIMAL":    "DECIMAL",
		"SECONDDATE": "SECONDDATE",
		"BIGINT":     "BIGINT",
	}
	for in, want := range cases {
		if got := sqlTypeName(in); got != want {
			t.Errorf("sqlTypeName(%q) = %q, want %q", in, got, want)
		}
	}

	// And through the pipeline: a FIXED12 column must be advertised as DECIMAL,
	// which is what tells a caller the value is exact rather than a float.
	sc := &fakeScript{
		cols: []fakeCol{
			{name: "BAL", dbType: "FIXED12", prec: 28, scale: 6, hasDec: true},
			{name: "WHEN", dbType: "LONGDATE"},
		},
		row: func(i int) ([]driver.Value, bool) {
			if i > 0 {
				return nil, false
			}
			return []driver.Value{int64(1), time.Date(2026, 7, 30, 0, 0, 0, 0, time.UTC)}, true
		},
	}
	db, _ := newFakeDB(t, Options{}, sc)
	defer db.Close()
	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, "SELECT 1 FROM DUMMY")
	if err != nil {
		t.Fatalf("QueryReadOnly: %v", err)
	}
	if res.Columns[0].Type != "DECIMAL" {
		t.Fatalf("columns[0].type = %q, want DECIMAL — a caller cannot tell exact from float otherwise", res.Columns[0].Type)
	}
	if res.Columns[1].Type != "TIMESTAMP" {
		t.Fatalf("columns[1].type = %q, want TIMESTAMP (MCP.md promises that name for a SAP B1 date column)", res.Columns[1].Type)
	}
}

func planNames(plans []*colPlan) []string {
	out := make([]string, len(plans))
	for i, p := range plans {
		out[i] = p.col.Name
	}
	return out
}
