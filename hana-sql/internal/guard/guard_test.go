package guard

import (
	"strings"
	"testing"
)

// The refuse table has one case per numbered bypass in the design, plus the
// fail-closed cases. `layer` is the layer that MUST catch it — if a change
// moves a case to a different layer the test fails, which is the point: it
// tells you the defence in depth actually shifted.
func TestCheckRefuses(t *testing.T) {
	cases := []struct {
		name  string
		sql   string
		layer int
	}{
		// --- bypass 1: the obvious write --------------------------------
		{"bypass01_update", `UPDATE "JIVO_OIL_HANADB"."OCRD" SET "Balance" = 0`, 1},
		{"bypass01_insert", `INSERT INTO "JIVO_OIL_HANADB"."OCRD" VALUES (1)`, 1},
		{"bypass01_delete", `DELETE FROM "JIVO_OIL_HANADB"."OINV"`, 1},

		// --- bypass 2: verb hidden behind a comment ---------------------
		{"bypass02_block_comment_prefix", `/* SELECT */ DELETE FROM OINV`, 1},
		{"bypass02_line_comment_prefix", "-- SELECT 1\nDROP TABLE OINV", 1},
		{"bypass02_comment_inside_verb", `DEL/*x*/ETE FROM OINV`, 1},

		// --- bypass 3: stacked statements -------------------------------
		{"bypass03_stacked_drop", `SELECT 1 FROM DUMMY; DROP TABLE T`, 2},
		{"bypass03_stacked_update", `SELECT 1 FROM DUMMY;UPDATE OCRD SET "Balance"=0`, 2},
		{"bypass03_stacked_after_trailing", `SELECT 1 FROM DUMMY; ; SELECT 2 FROM DUMMY`, 2},

		// --- bypass 7: DML smuggled into a CTE --------------------------
		{"bypass07_cte_delete", `WITH x AS (DELETE FROM OINV RETURNING 1) SELECT * FROM x`, 3},

		// --- bypass 8: anonymous block ----------------------------------
		{"bypass08_do_begin", `DO BEGIN UPDATE OCRD SET "Balance"=0; END`, 1},
		{"bypass08_do_in_select", `SELECT 1 FROM DUMMY WHERE 1=1 DO BEGIN END`, 3},

		// --- bypass 9: stored procedure ---------------------------------
		{"bypass09_call", `CALL "SYS"."SOME_PROC"()`, 1},

		// --- bypass 10: locking read ------------------------------------
		{"bypass10_select_for_update", `SELECT * FROM "JIVO_OIL_HANADB"."OCRD" FOR UPDATE`, 3},

		// --- bypass 11: LOCK TABLE --------------------------------------
		{"bypass11_lock_table", `LOCK TABLE "JIVO_OIL_HANADB"."OCRD" IN EXCLUSIVE MODE`, 1},

		// --- bypass 12: server-side file write --------------------------
		{"bypass12_export", `EXPORT "JIVO_OIL_HANADB"."OCRD" AS BINARY INTO '/tmp/x'`, 1},
		{"bypass12_export_in_select", `SELECT * FROM T INTO '/tmp/x'`, 3},

		// --- bypass 13: SELECT ... INTO ---------------------------------
		{"bypass13_select_into_var", `SELECT COUNT(*) INTO v FROM "JIVO_OIL_HANADB"."OCRD"`, 3},

		// --- bypass 14: DDL ---------------------------------------------
		{"bypass14_ctas", `CREATE TABLE T2 AS (SELECT * FROM "JIVO_OIL_HANADB"."OCRD")`, 1},
		{"bypass14_alter", `ALTER TABLE OCRD ADD (X INT)`, 1},
		{"bypass14_create_in_select", `SELECT 1 FROM DUMMY UNION ALL CREATE TABLE T (X INT)`, 3},

		// --- bypass 15: EXPLAIN writes SYS.EXPLAIN_PLAN_TABLE -----------
		{"bypass15_explain_under_mcp", `EXPLAIN PLAN FOR SELECT 1 FROM DUMMY`, 1},

		// --- bypass 16: unterminated literals hide the tail -------------
		{"bypass16_unterminated_string", `SELECT 'abc FROM DUMMY`, 0},
		{"bypass16_unterminated_block_comment", `SELECT 1 FROM DUMMY /* DROP TABLE T`, 0},
		{"bypass16_unterminated_ident", `SELECT "DocTotal FROM OINV`, 0},

		// --- bypass 17: homoglyph / zero-width disguise ------------------
		{"bypass17_zero_width_prefix", "​SELECT 1 FROM DUMMY", 0},
		{"bypass17_cyrillic_select", "СELECT 1 FROM DUMMY", 0},
		{"bypass17_nbsp_between", "SELECT 1 FROM DUMMY", 0},

		// --- bypass 18: escape the read-only transaction -----------------
		{"bypass18_commit", `SELECT 1 FROM DUMMY UNION ALL COMMIT`, 3},
		{"bypass18_rollback", `ROLLBACK`, 1},
		{"bypass18_savepoint", `SELECT 1 FROM DUMMY SAVEPOINT s`, 3},

		// --- session/permission changes ----------------------------------
		{"set_schema", `SET SCHEMA "JIVO_MART_HANADB"`, 1},
		{"grant", `GRANT SELECT ON SCHEMA "JIVO_OIL_HANADB" TO PUBLIC`, 1},
		{"connect", `CONNECT ZIA PASSWORD x`, 1},
		{"set_inside_select", `SELECT 1 FROM DUMMY WHERE 1 = 1 SET SCHEMA X`, 3},

		// --- misc write verbs anywhere ------------------------------------
		{"merge_anywhere", `SELECT * FROM (MERGE INTO T USING S ON (1=1))`, 3},
		{"truncate_anywhere", `WITH q AS (SELECT 1 FROM DUMMY) SELECT TRUNCATE FROM q`, 3},
		{"import_first", `IMPORT FROM CSV FILE '/tmp/x' INTO T`, 1},

		// --- degenerate input ---------------------------------------------
		{"empty", ``, 1},
		{"whitespace_only", "   \n\t ", 1},
		{"comment_only", `-- just a comment`, 1},
		{"control_char", "SELECT\x001 FROM DUMMY", 0},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			err := Check(c.sql, MCPPolicy)
			if err == nil {
				t.Fatalf("Check(%q) = nil, want a refusal at layer %d", c.sql, c.layer)
			}
			if !IsRefusal(err) {
				t.Fatalf("Check(%q) err = %v, want a *Refusal", c.sql, err)
			}
			r := err.(*Refusal)
			if r.Layer != c.layer {
				t.Fatalf("Check(%q) refused at layer %d (%v), want layer %d", c.sql, r.Layer, err, c.layer)
			}
			if !strings.HasPrefix(err.Error(), "REFUSED (read-only layer ") {
				t.Fatalf("error text %q lacks the REFUSED prefix", err.Error())
			}
		})
	}
}

// The must-allow table is the other half of the guarantee: a read-only gate
// that refuses legitimate accounting SQL is a broken gate.
func TestCheckAllows(t *testing.T) {
	cases := []struct {
		name string
		sql  string
	}{
		// bypass 4: ';' inside a string is data, not a statement separator.
		// The old regex guard refused this one — a real false positive.
		{"semicolon_in_string", `SELECT 'a;b' FROM DUMMY`},
		{"semicolon_in_comment", "SELECT 1 FROM DUMMY -- ; DROP TABLE T\n"},
		{"semicolon_in_block_comment", `SELECT 1 /* ; */ FROM DUMMY`},

		// bypass 5: a banned keyword inside a string literal is data.
		{"keyword_in_string", `SELECT 'DROP TABLE X' FROM DUMMY`},
		{"keyword_in_string_like", `SELECT * FROM "JIVO_OIL_HANADB"."OCRD" WHERE "CardName" LIKE '%UPDATE%'`},
		{"escaped_quote_in_string", `SELECT 'O''BRIEN; DELETE' FROM DUMMY`},

		// bypass 6: a banned keyword as a quoted identifier is a column name.
		{"keyword_as_quoted_ident", `SELECT "UPDATE" FROM "JIVO_OIL_HANADB"."OCRD"`},
		{"escaped_quote_in_ident", `SELECT "we""ird" FROM T`},

		// double quote inside a single-quoted string (the TO_VARCHAR format
		// mask we actually use in hana_doctor).
		{"double_quote_inside_string", `SELECT TO_VARCHAR(CURRENT_UTCTIMESTAMP, 'YYYY-MM-DD"T"HH24:MI:SS') FROM DUMMY`},

		{"case_end", `SELECT CASE WHEN "Balance" > 0 THEN 'DEBIT' ELSE 'CREDIT' END AS SIDE FROM "JIVO_OIL_HANADB"."OCRD"`},
		{"replace_function", `SELECT REPLACE("CardName", 'a', 'b') FROM "JIVO_OIL_HANADB"."OCRD"`},
		{"offset_is_not_set", `SELECT * FROM "JIVO_OIL_HANADB"."OCRD" ORDER BY "CardCode" LIMIT 10 OFFSET 20`},
		{"dollar_in_identifier", `SELECT MY$UPDATE FROM T`},
		{"comments_column_is_not_comment", `SELECT COMMENTS FROM SYS.TABLES WHERE SCHEMA_NAME = 'X'`},
		{"create_time_is_not_create", `SELECT CREATE_TIME FROM SYS.TABLES WHERE SCHEMA_NAME = 'X'`},

		{"three_table_join_group_by", `
			SELECT o."CardCode", c."CardName", SUM(i."Quantity") AS QTY
			FROM "JIVO_OIL_HANADB"."OINV" o
			JOIN "JIVO_OIL_HANADB"."INV1" i ON i."DocEntry" = o."DocEntry"
			JOIN "JIVO_OIL_HANADB"."OCRD" c ON c."CardCode" = o."CardCode"
			WHERE o."DocDate" >= '2026-04-01' AND o."CANCELED" = 'N'
			GROUP BY o."CardCode", c."CardName"
			HAVING SUM(i."Quantity") > 0
			ORDER BY QTY DESC`},

		{"with_select", `WITH t AS (SELECT "DocTotal" - "VatSum" AS NET FROM "JIVO_OIL_HANADB"."OINV" WHERE "CANCELED" = 'N') SELECT ROUND(TO_DOUBLE(SUM(NET)), 2) FROM t`},
		{"trailing_semicolon", `SELECT 1 FROM DUMMY;`},
		{"trailing_semicolon_whitespace", "SELECT 1 FROM DUMMY;  \n"},
		{"leading_comment", "/* turnover */\nSELECT 1 FROM DUMMY"},
		{"parenthesised_select", `(SELECT 1 FROM DUMMY) UNION ALL (SELECT 2 FROM DUMMY)`},
		{"lowercase_select", `select count(*) from "JIVO_MART_HANADB"."OCRD"`},
		{"bind_parameters", `SELECT COLUMN_NAME FROM SYS.TABLE_COLUMNS WHERE SCHEMA_NAME = ? AND TABLE_NAME = ?`},
		{"unicode_in_string_literal", `SELECT * FROM T WHERE "Name" = 'हिन्दी'`},
		{"unicode_in_quoted_ident", `SELECT "स्तंभ" FROM T`},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if err := Check(c.sql, MCPPolicy); err != nil {
				t.Fatalf("Check(%q) = %v, want nil (this is legitimate read SQL)", c.sql, err)
			}
		})
	}
}

// The deliberate split between the two policies. Nobody should "normalise" this
// away: HANA's EXPLAIN PLAN FOR persists rows into SYS.EXPLAIN_PLAN_TABLE.
func TestExplainPolicySplit(t *testing.T) {
	const stmt = `EXPLAIN PLAN FOR SELECT 1 FROM DUMMY`

	err := Check(stmt, MCPPolicy)
	if err == nil {
		t.Fatal("MCPPolicy accepted EXPLAIN; it writes SYS.EXPLAIN_PLAN_TABLE and must be refused")
	}
	if r, ok := err.(*Refusal); !ok || r.Layer != 1 {
		t.Fatalf("MCPPolicy EXPLAIN refusal = %v, want layer 1", err)
	}
	if err := Check(stmt, CLIPolicy); err != nil {
		t.Fatalf("CLIPolicy refused EXPLAIN (%v); the human CLI must keep it", err)
	}
	// ... and the CLI is not a free pass for writes.
	if err := Check(`UPDATE OCRD SET "Balance" = 0`, CLIPolicy); err == nil {
		t.Fatal("CLIPolicy accepted an UPDATE")
	}
}

func TestNormalizeMasks(t *testing.T) {
	cases := []struct {
		in   string
		text string
		toks []string
	}{
		{`SELECT 'a;b' FROM DUMMY`, `SELECT '?' FROM DUMMY`, []string{"SELECT", "FROM", "DUMMY"}},
		{`SELECT "UPDATE" FROM T`, `SELECT "I" FROM T`, []string{"SELECT", "I", "FROM", "T"}},
		{"SELECT 1 -- DROP\nFROM DUMMY", "SELECT 1  \nFROM DUMMY", []string{"SELECT", "1", "FROM", "DUMMY"}},
		{`SELECT/*DROP*/1 FROM DUMMY`, `SELECT 1 FROM DUMMY`, []string{"SELECT", "1", "FROM", "DUMMY"}},
		{`SELECT 'O''X' FROM DUMMY`, `SELECT '?' FROM DUMMY`, []string{"SELECT", "FROM", "DUMMY"}},
	}
	for _, c := range cases {
		m, err := Normalize(c.in)
		if err != nil {
			t.Fatalf("Normalize(%q) = %v", c.in, err)
		}
		if m.Text != c.text {
			t.Errorf("Normalize(%q).Text = %q, want %q", c.in, m.Text, c.text)
		}
		if strings.Join(m.Tokens, ",") != strings.Join(c.toks, ",") {
			t.Errorf("Normalize(%q).Tokens = %v, want %v", c.in, m.Tokens, c.toks)
		}
	}
}

// The banned list is load-bearing; keep it visible and non-empty.
func TestBannedTokensSorted(t *testing.T) {
	b := BannedTokens()
	if len(b) < 25 {
		t.Fatalf("banned list has only %d entries; that is suspiciously short", len(b))
	}
	for i := 1; i < len(b); i++ {
		if b[i-1] >= b[i] {
			t.Fatalf("BannedTokens() not sorted/unique at %d: %q then %q", i, b[i-1], b[i])
		}
	}
	for _, must := range []string{"UPDATE", "DELETE", "INSERT", "DROP", "CALL", "INTO", "COMMIT"} {
		found := false
		for _, t2 := range b {
			if t2 == must {
				found = true
			}
		}
		if !found {
			t.Fatalf("banned list is missing %q", must)
		}
	}
	// REPLACE must NOT be banned: it is a legitimate HANA string function.
	for _, t2 := range b {
		if t2 == "REPLACE" {
			t.Fatal("REPLACE is banned at layer 3; it is a string function and must only be blocked as a statement starter")
		}
	}
}
