package hana

import (
	"context"
	"os"
	"strings"
	"testing"
	"time"

	"hana-sql/internal/config"
	"hana-sql/internal/guard"
)

// The live suite runs only with HANA_TEST_LIVE=1 and only where HANA is
// reachable (in practice the VPS, through the office reverse tunnel):
//
//	HANA_TEST_LIVE=1 HANA_ENV=/opt/jivo-truth/hana.env ./hana-live.test -test.v
//
// Every statement here is a read. Nothing in this file — or anywhere else in the
// shipped code — attempts a write.
func liveDB(t *testing.T) *DB {
	t.Helper()
	if os.Getenv("HANA_TEST_LIVE") != "1" {
		t.Skip("set HANA_TEST_LIVE=1 (and HANA_ENV) to run the live suite")
	}
	cfg, err := config.Load(config.Find(""))
	if err != nil {
		t.Fatalf("config: %v", err)
	}
	db := New(cfg, Options{
		Limits:        Limits{MaxRows: DefaultMaxRows, MaxBytes: DefaultMaxBytes, Timeout: 120 * time.Second},
		MaxConcurrent: 2,
		AppName:       "hana-sql-live-test",
	})
	t.Cleanup(func() { db.Close() })
	return db
}

func liveOne(t *testing.T, db *DB, stmt string, args ...any) map[string]any {
	t.Helper()
	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, stmt, args...)
	if err != nil {
		t.Fatalf("query failed: %v\n%s", err, stmt)
	}
	if len(res.Rows) == 0 {
		t.Fatalf("no rows from:\n%s", stmt)
	}
	return res.Rows[0]
}

func TestLiveIdentityAndSchemas(t *testing.T) {
	db := liveDB(t)
	id, err := db.Identify(context.Background())
	if err != nil {
		t.Fatalf("Identify: %v", err)
	}
	if id.User == "" || id.Version == "" {
		t.Fatalf("identity is incomplete: %+v", id)
	}
	t.Logf("user=%s schema=%s hana=%s server_utc=%s skew=%s mode=%s",
		id.User, id.Schema, id.Version, id.ServerUTC, id.ClockSkew.Round(time.Millisecond), db.Mode())
	if len(id.SchemaRows) != 3 {
		t.Fatalf("got %d schema rows, want 3", len(id.SchemaRows))
	}
	for _, s := range id.SchemaRows {
		t.Logf("schema %-24s company=%-9s tables=%d readable=%v", s.Schema, s.Company, s.Tables, s.Readable)
		if !s.Readable {
			t.Errorf("%s (%s) is not readable; all three companies must be reachable", s.Schema, s.Company)
		}
	}
}

// The catalog SQL is written against column names I must not guess. This test
// runs each fixed statement and prints what came back.
func TestLiveCatalogViewsHaveTheColumnsWeAssume(t *testing.T) {
	db := liveDB(t)
	ctx := context.Background()

	res, err := db.Tables(ctx, TableQuery{Schema: "JIVO_OIL_HANADB", Like: "O%"})
	if err != nil {
		t.Fatalf("Tables: %v", err)
	}
	t.Logf("hana_tables: %d rows, note=%q, columns=%v", res.RowCount, res.Note, res.Columns)
	want := map[string]bool{"OCRD": false, "OINV": false, "ORIN": false, "ORDR": false,
		"OPOR": false, "OITM": false, "OITW": false, "OJDT": false, "ORCT": false, "OVPM": false}
	for _, row := range res.Rows {
		if n, _ := row["TABLE_NAME"].(string); want[n] == false {
			if _, ok := want[n]; ok {
				want[n] = true
			}
		}
	}
	for name, found := range want {
		if !found {
			t.Errorf("hana_tables did not find %s in JIVO_OIL_HANADB", name)
		}
	}

	cols, err := db.Columns(ctx, "JIVO_OIL_HANADB", "OINV", "")
	if err != nil {
		t.Fatalf("Columns: %v", err)
	}
	have := map[string]string{}
	for _, row := range cols.Rows {
		n, _ := row["COLUMN_NAME"].(string)
		dt, _ := row["DATA_TYPE"].(string)
		have[n] = dt
	}
	for _, c := range []string{"DocTotal", "VatSum", "DocDate", "CANCELED", "DocStatus", "CardCode"} {
		if dt, ok := have[c]; !ok {
			t.Errorf("OINV has no column %q — the crib sheet in internal/mcpsrv/facts.go is wrong", c)
		} else {
			t.Logf("OINV.%-10s %s", c, dt)
		}
	}
}

// Every column named in the hana_query crib sheet (internal/mcpsrv/facts.go)
// must actually exist, with exactly that spelling. This is the test that stops
// the crib sheet rotting into confident nonsense — the benchmark's D7 defect,
// where Service Layer field names were quoted as if they were HANA's.
//
// The spellings below were each confirmed by hand against SYS.TABLE_COLUMNS on
// 2026-07-30 before being written down.
func TestLiveCribSheetColumnsExist(t *testing.T) {
	db := liveDB(t)
	ctx := context.Background()

	want := map[string][]string{
		"OCRD": {"CardType", "Balance", "CardName", "CardCode", "CreditLine"},
		"OINV": {"DocTotal", "VatSum", "DocDate", "DocDueDate", "CANCELED", "DocStatus", "PaidToDate", "CardCode"},
		"ORIN": {"DocTotal", "VatSum", "DocDate", "CANCELED"},
		"ORDR": {"DocTotal", "VatSum", "DocDate", "CANCELED", "DocStatus"},
		"OJDT": {"RefDate"},
		"OITM": {"InvntItem", "validFor", "ItemName"},
		"OITW": {"OnHand", "MinStock"},
		// The payment tables are the trap: the flag loses a capital L, and —
		// unlike the Service Layer — "DocTotal" DOES exist here.
		"ORCT": {"Canceled", "DocTotal"},
		"OVPM": {"Canceled", "DocTotal"},
	}

	for table, cols := range want {
		res, err := db.Columns(ctx, "JIVO_OIL_HANADB", table, "")
		if err != nil {
			t.Errorf("%s: %v", table, err)
			continue
		}
		have := map[string]bool{}
		for _, row := range res.Rows {
			if n, _ := row["COLUMN_NAME"].(string); n != "" {
				have[n] = true
			}
		}
		for _, c := range cols {
			if !have[c] {
				t.Errorf(`%s has no column %q with that exact spelling — the crib sheet in internal/mcpsrv/facts.go is wrong`, table, c)
			}
		}
	}

	// And the negative half: the WRONG spelling must really be wrong, otherwise
	// the warning in the crib sheet is noise.
	res, err := db.Columns(ctx, "JIVO_OIL_HANADB", "ORCT", "")
	if err != nil {
		t.Fatalf("ORCT columns: %v", err)
	}
	for _, row := range res.Rows {
		if n, _ := row["COLUMN_NAME"].(string); n == "CANCELED" {
			t.Error(`ORCT does have a "CANCELED" column after all; the crib sheet's spelling warning is wrong`)
		}
	}
}

// The four benchmark answers, each in ONE call. The decimal path is validated by
// these matching to the paisa, not by inspection.
//
// Figures are live and the books are open, so a mismatch is not automatically a
// bug: the test prints both numbers so drift is legible. Set
// HANA_TEST_STRICT_TRUTH=1 to make any drift a hard failure.
func TestLiveBenchmarkTruth(t *testing.T) {
	db := liveDB(t)
	strict := os.Getenv("HANA_TEST_STRICT_TRUTH") == "1"

	check := func(name, got, want string) {
		if got == want {
			t.Logf("%-28s %s  (matches mcp-benchmark/truth-key.json)", name, got)
			return
		}
		msg := "%-28s %s  DRIFT from truth-key %s"
		if strict {
			t.Errorf(msg, name, got, want)
		} else {
			t.Logf(msg+" (books are open; re-verify by hand before calling it a bug)", name, got, want)
		}
	}

	// q03 — Oil business partners, split by type, in one call.
	row := liveOne(t, db, `SELECT COUNT(*) AS TOTAL,
	  SUM(CASE WHEN "CardType" = 'C' THEN 1 ELSE 0 END) AS CUSTOMERS,
	  SUM(CASE WHEN "CardType" = 'S' THEN 1 ELSE 0 END) AS SUPPLIERS,
	  SUM(CASE WHEN "CardType" = 'L' THEN 1 ELSE 0 END) AS LEADS
	FROM "JIVO_OIL_HANADB"."OCRD"`)
	check("q03 partners total", str(row["TOTAL"]), "3390")
	check("q03 customers", str(row["CUSTOMERS"]), "1170")
	check("q03 suppliers", str(row["SUPPLIERS"]), "2220")
	check("q03 leads", str(row["LEADS"]), "0")

	// q04 — open A/R invoices.
	row = liveOne(t, db, `SELECT COUNT(*) AS OPEN_AR FROM "JIVO_OIL_HANADB"."OINV"
	  WHERE "DocStatus" = 'O' AND "CANCELED" = 'N'`)
	check("q04 open A/R invoices", str(row["OPEN_AR"]), "12861")

	// q08 — A/R debit-only exposure. Netting understates it, so sum debits only.
	row = liveOne(t, db, `SELECT ROUND(TO_DOUBLE(SUM("Balance")), 2) AS AR_DEBIT
	  FROM "JIVO_OIL_HANADB"."OCRD" WHERE "CardType" = 'C' AND "Balance" > 0`)
	check("q08 A/R debit-only", str(row["AR_DEBIT"]), "1074316124.55")

	// q10 — Oil turnover 1 Apr - 31 Jul 2026, net of GST, invoices minus returns.
	row = liveOne(t, db, `SELECT ROUND(TO_DOUBLE(
	    (SELECT COALESCE(SUM("DocTotal" - "VatSum"), 0) FROM "JIVO_OIL_HANADB"."OINV"
	       WHERE "DocDate" >= '2026-04-01' AND "DocDate" < '2026-08-01' AND "CANCELED" = 'N')
	  - (SELECT COALESCE(SUM("DocTotal" - "VatSum"), 0) FROM "JIVO_OIL_HANADB"."ORIN"
	       WHERE "DocDate" >= '2026-04-01' AND "DocDate" < '2026-08-01' AND "CANCELED" = 'N')
	  ), 2) AS TURNOVER FROM DUMMY`)
	check("q10 Oil turnover Apr-Jul", str(row["TURNOVER"]), "1368965497.25")
}

// A raw DECIMAL column must arrive as an exact decimal string, never a
// big.Rat fraction (the bug the old CLI shipped: 8210929/100).
func TestLiveDecimalIsAnExactString(t *testing.T) {
	db := liveDB(t)
	row := liveOne(t, db, `SELECT "CardCode", "Balance" FROM "JIVO_OIL_HANADB"."OCRD"
	  WHERE "CardCode" = 'ORGV000044'`)
	bal, ok := row["Balance"].(string)
	if !ok {
		t.Fatalf("Balance came back as %T (%v); a DECIMAL must be an exact string", row["Balance"], row["Balance"])
	}
	t.Logf("OCRD.Balance for ORGV000044 = %s", bal)
	if strings.Contains(bal, "/") {
		t.Fatalf("Balance = %q — that is a big.Rat fraction, exactly what value.go exists to prevent", bal)
	}
	if !strings.HasPrefix(bal, "82109.29") {
		t.Errorf("Balance = %q, want 82109.29… (truth-key q01)", bal)
	}
}

// DATE must be date-only, not an RFC3339 midnight.
func TestLiveDateIsDateOnly(t *testing.T) {
	db := liveDB(t)
	row := liveOne(t, db, `SELECT "DocDate" FROM "JIVO_OIL_HANADB"."OINV"
	  WHERE "CANCELED" = 'N' ORDER BY "DocEntry" DESC LIMIT 1`)
	d, ok := row["DocDate"].(string)
	if !ok || len(d) != 10 || strings.Contains(d, "T") || strings.Contains(d, "UTC") {
		t.Fatalf("DocDate = %#v, want a bare \"2006-01-02\"", row["DocDate"])
	}
	t.Logf("latest OINV.DocDate = %s", d)
}

// The LOB path: scanning a HANA LOB naively into `any` yields the driver's
// locator object, not the text. SYS.PROCEDURES.DEFINITION is a LOB and touches
// no business data.
func TestLiveLobScan(t *testing.T) {
	db := liveDB(t)
	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{MaxRows: 3},
		`SELECT SCHEMA_NAME, PROCEDURE_NAME, DEFINITION FROM SYS.PROCEDURES WHERE DEFINITION IS NOT NULL LIMIT 3`)
	if err != nil {
		t.Skipf("SYS.PROCEDURES is not readable by this login: %v", err)
	}
	if len(res.Rows) == 0 {
		t.Skip("no procedures visible to this login")
	}
	for _, c := range res.Columns {
		t.Logf("column %s type=%s", c.Name, c.Type)
	}
	def, ok := res.Rows[0]["DEFINITION"].(string)
	if !ok {
		t.Fatalf("DEFINITION came back as %T; the LOB scan plan did not engage", res.Rows[0]["DEFINITION"])
	}
	if strings.Contains(def, "ltcUndefined") || strings.Contains(def, "typecode") {
		t.Fatalf("DEFINITION is the raw lob locator, not text: %.120s", def)
	}
	t.Logf("LOB length %d, first 80 chars: %.80s", len(def), def)
}

// The row cap must be exact, and the caller must be told.
func TestLiveRowCapIsExact(t *testing.T) {
	db := liveDB(t)
	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{MaxRows: 250},
		`SELECT "DocEntry", "DocNum", "DocDate", "DocTotal" FROM "JIVO_OIL_HANADB"."OINV" ORDER BY "DocEntry"`)
	if err != nil {
		t.Fatalf("query: %v", err)
	}
	if res.RowCount != 250 {
		t.Fatalf("RowCount = %d, want exactly 250", res.RowCount)
	}
	if !res.Truncated {
		t.Fatal("Truncated = false on a capped result")
	}
	t.Logf("row cap held at %d, note=%q", res.RowCount, res.Note)
}

// Layers 0-3 must refuse against the real database too, and nothing may reach it.
func TestLiveWritesAreRefused(t *testing.T) {
	db := liveDB(t)
	for _, stmt := range []string{
		`UPDATE "JIVO_OIL_HANADB"."OCRD" SET "Balance" = 0 WHERE 1 = 0`,
		`DELETE FROM "JIVO_OIL_HANADB"."OINV" WHERE 1 = 0`,
		`CREATE TABLE "JIVO_OIL_HANADB"."ZZ_PROBE" (X INT)`,
		`SELECT 1 FROM DUMMY; DROP TABLE "JIVO_OIL_HANADB"."OINV"`,
		`SELECT * FROM "JIVO_OIL_HANADB"."OCRD" FOR UPDATE`,
		`EXPLAIN PLAN FOR SELECT 1 FROM DUMMY`,
		`CALL "SYS"."GET_OBJECT_DEFINITION"('SYS','DUMMY')`,
		// A sequence advance is a write dressed as a SELECT, and there are 3158
		// sequences in SYS.SEQUENCES on this instance. It must be refused
		// STATICALLY — the point is that it never reaches HANA, so asserting it
		// here does not execute one.
		`SELECT "SOMESEQ".NEXTVAL FROM DUMMY`,
		`SELECT JIVO_OIL_HANADB.SOMESEQ.NEXTVAL FROM DUMMY`,
	} {
		_, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{}, stmt)
		if !guard.IsRefusal(err) {
			t.Fatalf("live: %q was NOT refused by the guard (err=%v)", stmt, err)
		}
		t.Logf("refused: %s", err)
	}
}

func str(v any) string {
	switch t := v.(type) {
	case nil:
		return "NULL"
	case string:
		return t
	case int64:
		return itoa(t)
	default:
		return strings.TrimSpace(CellText(v))
	}
}

func itoa(n int64) string {
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	var b [24]byte
	i := len(b)
	for n > 0 {
		i--
		b[i] = byte('0' + n%10)
		n /= 10
	}
	if neg {
		i--
		b[i] = '-'
	}
	return string(b[i:])
}

// --- live regressions for the reviewer findings --------------------------------

// The 5h30m defect, measured the way the reviewer measured it. CURRENT_TIMESTAMP
// is the server's LOCAL wall clock and CURRENT_UTCTIMESTAMP is the real UTC
// instant; rendering the first with RFC3339Nano stamped a "Z" on it and turned
// IST into a UTC claim 5h30m wrong.
func TestLiveTimestampWithAClockCarriesNoFalseZone(t *testing.T) {
	db := liveDB(t)
	row := liveOne(t, db, `SELECT CURRENT_TIMESTAMP AS LOCAL_WALLCLOCK, CURRENT_UTCTIMESTAMP AS REAL_UTC FROM DUMMY`)
	local, _ := row["LOCAL_WALLCLOCK"].(string)
	utc, _ := row["REAL_UTC"].(string)
	t.Logf("CURRENT_TIMESTAMP = %s   CURRENT_UTCTIMESTAMP = %s", local, utc)
	if local == "" || utc == "" {
		t.Fatalf("unexpected shapes: %#v", row)
	}
	for name, v := range map[string]string{"CURRENT_TIMESTAMP": local, "CURRENT_UTCTIMESTAMP": utc} {
		if strings.HasSuffix(v, "Z") {
			t.Errorf("%s = %q — a HANA TIMESTAMP carries no zone, and the \"Z\" publishes the server's wall clock as a UTC claim", name, v)
		}
		if strings.Contains(v, "+") {
			t.Errorf("%s = %q — no offset may be invented either", name, v)
		}
	}
	if local == utc {
		t.Skip("this server's local clock is UTC, so the two cannot be told apart today")
	}
}

// columns[].type must report the SQL type, not go-hdb's storage type: OINV
// ."DocDate" is declared TIMESTAMP (SYS.TABLE_COLUMNS) but the driver reports
// LONGDATE, and every DECIMAL reports FIXED8/12/16. Callers are told to use this
// field to tell an exact DECIMAL from a float DOUBLE.
func TestLiveColumnTypesAreSQLTypes(t *testing.T) {
	db := liveDB(t)
	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, Limits{MaxRows: 1},
		`SELECT "DocDate", "DocTotal", TO_DATE('2026-07-30') AS D, TO_DOUBLE(1.5) AS DBL
		 FROM "JIVO_OIL_HANADB"."OINV" ORDER BY "DocEntry" DESC LIMIT 1`)
	if err != nil {
		t.Fatalf("query: %v", err)
	}
	got := map[string]string{}
	for _, c := range res.Columns {
		got[c.Name] = c.Type
		t.Logf("column %-9s type=%s", c.Name, c.Type)
	}
	want := map[string]string{"DocDate": "TIMESTAMP", "DocTotal": "DECIMAL", "D": "DATE", "DBL": "DOUBLE"}
	for name, w := range want {
		if got[name] != w {
			t.Errorf("columns[%s].type = %q, want %q — the field exists so a caller can tell exact DECIMAL from float DOUBLE", name, got[name], w)
		}
	}
	// And the declared type in the catalog agrees with what we report.
	cols, err := db.Columns(context.Background(), "JIVO_OIL_HANADB", "OINV", "DocDate")
	if err != nil {
		t.Fatalf("Columns: %v", err)
	}
	if len(cols.Rows) == 1 {
		t.Logf("SYS.TABLE_COLUMNS says OINV.DocDate is %v", cols.Rows[0]["DATA_TYPE"])
	}
}

// An unknown schema must be an ERROR against the real database, not the clean
// empty success the reviewer measured.
func TestLiveUnknownSchemaIsRefused(t *testing.T) {
	db := liveDB(t)
	ctx := context.Background()
	for _, bad := range []string{"JIVO_BEVERAGE_HANADB", "Beverages", "Oil", "OIL"} {
		if res, err := db.Tables(ctx, TableQuery{Schema: bad}); err == nil {
			t.Errorf("hana_tables{schema:%q} returned %d rows with no error; a typo must not look like \"this company has no data\"", bad, res.RowCount)
		} else {
			t.Logf("refused %-22s %s", bad, firstSentence(err.Error()))
		}
	}
	if _, err := db.Columns(ctx, "JIVO_BEVERAGE_HANADB", "OINV", ""); err == nil {
		t.Error("hana_columns accepted a misspelt schema")
	}
	// A wrong-CASE table name in a REAL schema is explained, not answered empty.
	_, err := db.Columns(ctx, "JIVO_OIL_HANADB", "oinv", "")
	if err == nil {
		t.Error(`hana_columns{table:"oinv"} returned a clean empty result; that reads as "this table has no columns"`)
	} else {
		t.Logf("refused lower-case table: %s", err)
		if !strings.Contains(err.Error(), "OINV") {
			t.Errorf("the refusal does not offer the correct spelling: %v", err)
		}
	}
}

// The partial-catalog defect, end to end against the real 9,244-table catalog.
func TestLiveTableListingSaysWhichCompaniesItLeftOut(t *testing.T) {
	db := liveDB(t)
	ctx := context.Background()

	res, err := db.Tables(ctx, TableQuery{NoRowCounts: true})
	if err != nil {
		t.Fatalf("Tables: %v", err)
	}
	t.Logf("unfiltered listing: %d rows, truncated=%v", res.RowCount, res.Truncated)
	t.Logf("note: %s", res.Note)
	if !res.Truncated {
		t.Skip("this login sees fewer than the row cap; the partial-catalog path cannot be exercised")
	}
	if strings.Contains(res.Note, "SUM/COUNT/GROUP BY") {
		t.Error("the catalog page still tells the caller to aggregate server-side, which is impossible for a table listing")
	}
	for _, must := range []string{"PARTIAL CATALOG", "NOTHING from", "offset="} {
		if !strings.Contains(res.Note, must) {
			t.Errorf("the truncation note is missing %q", must)
		}
	}
	// Every company must be reachable by paging, which is the recovery the note
	// points at.
	seen := map[string]bool{}
	for off := 0; off < 9000 && len(seen) < len(Schemas); off += 1000 {
		page, err := db.Tables(ctx, TableQuery{NoRowCounts: true, Offset: off})
		if err != nil {
			t.Fatalf("Tables(offset=%d): %v", off, err)
		}
		for _, row := range page.Rows {
			if n, _ := row["SCHEMA_NAME"].(string); n != "" {
				seen[n] = true
			}
		}
	}
	for _, s := range Schemas {
		if !seen[s] {
			t.Errorf("paging never reached %s; the offset the note hands back must actually recover the rest of the catalog", s)
		}
	}
	t.Logf("paging reached all of: %v", seen)
}

func firstSentence(s string) string {
	if i := strings.Index(s, "."); i > 0 {
		return s[:i+1]
	}
	return s
}
