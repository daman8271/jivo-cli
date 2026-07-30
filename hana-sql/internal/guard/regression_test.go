package guard

import (
	"strings"
	"testing"
)

// Regression tests for reviewer findings against internal/guard.
//
// Each test names the defect it locks down. A fix without a test that would
// have caught it is not a fix.

// FINDING (P3 / "UNVERIFIED WRITE VECTOR"): sequence NEXTVAL passed all five
// layers. `SELECT "SOMESEQ".NEXTVAL FROM DUMMY` is clean ASCII (layer 0), starts
// with SELECT (layer 1), is a single statement (layer 2) and contained no banned
// token (layer 3) — yet advancing a sequence is persistent state no rollback
// undoes, and the JIVO schemas hold 796 / 777 / 788 sequences (Oil / Mart /
// Beverages, counted live 2026-07-30). It was a live counterexample to MCP.md's
// "there is no argument that can make a tool write", so it is now a layer-3
// refusal — a static one, which means it never had to be executed to be closed.
func TestSequenceNextvalIsRefused(t *testing.T) {
	cases := []string{
		`SELECT MY_SEQ.NEXTVAL FROM DUMMY`,
		`SELECT "JIVO_OIL_HANADB"."MY_SEQ".NEXTVAL FROM DUMMY`,
		`SELECT JIVO_OIL_HANADB.MY_SEQ.NEXTVAL FROM DUMMY`,
		`select my_seq.nextval from dummy`,
		`WITH t AS (SELECT MY_SEQ.NEXTVAL AS N FROM DUMMY) SELECT N FROM t`,
		`SELECT "CardCode", MY_SEQ.NEXTVAL FROM "JIVO_OIL_HANADB"."OCRD"`,
	}
	for _, stmt := range cases {
		t.Run(shortName(stmt), func(t *testing.T) {
			for _, p := range []Policy{MCPPolicy, CLIPolicy} {
				err := Check(stmt, p)
				if err == nil {
					t.Fatalf("%s policy ACCEPTED %q — advancing a sequence is a write that no rollback undoes", p.Name, stmt)
				}
				r, ok := err.(*Refusal)
				if !ok || r.Layer != 3 {
					t.Fatalf("%s policy refusal for %q = %v, want a layer-3 banned-keyword refusal", p.Name, stmt, err)
				}
				if !strings.Contains(err.Error(), "NEXTVAL") {
					t.Fatalf("refusal %q does not name NEXTVAL, so the caller cannot tell what was wrong", err)
				}
			}
		})
	}
}

// The other half of the sequence rule: CURRVAL only reads the value the session
// already holds and advances nothing, so banning it would be a false positive.
// A column or alias that merely CONTAINS the word must also survive, because
// layer 3 matches whole tokens.
//
// `SELECT "NEXTVAL" FROM ...` used to be listed here as an allowed read, on the
// reasoning that quoting demotes NEXTVAL to an ordinary column name. That
// reasoning is sound in the abstract but was wrong to act on here — see
// TestQuotedNextvalIsRefused (layer 3b) and the note below.
func TestCurrvalAndNextvalLookalikesAreAllowed(t *testing.T) {
	for _, stmt := range []string{
		`SELECT MY_SEQ.CURRVAL FROM DUMMY`,
		`SELECT 'NEXTVAL' AS WHAT FROM DUMMY`,
		`SELECT NEXTVALUE FROM T`,
		`SELECT MY_NEXTVAL_LOG FROM T`,
	} {
		if err := Check(stmt, MCPPolicy); err != nil {
			t.Errorf("Check(%q) = %v, want nil — this is a read, and a false refusal is its own defect", stmt, err)
		}
	}
}

// TestQuotedNextvalCostsNoRealRead records why layer 3b refuses a quoted
// NEXTVAL even though a delimited identifier is, in principle, just a column.
//
// The trade was settled with data rather than argument. Counted live against
// production on 2026-07-30:
//
//	SELECT COUNT(*) FROM SYS.TABLE_COLUMNS
//	 WHERE UPPER(COLUMN_NAME)='NEXTVAL'
//	   AND SCHEMA_NAME IN ('JIVO_OIL_HANADB','JIVO_MART_HANADB','JIVO_BEVERAGES_HANADB')
//	=> 0
//
// No table in any of the three company schemas has a column by that name, so
// refusing the quoted form blocks no read anyone can actually perform, while
// allowing it would rest on HANA resolving a delimited identifier the way the
// documentation implies. That asymmetry — zero cost against an unrollbackable
// sequence advance — is the whole argument. The empirical check that would
// settle it the other way is itself the write we are preventing, so it was
// never run.
//
// If a JIVO schema ever legitimately gains a NEXTVAL column, this comment and
// the count above are the evidence to revisit, not a reason to quietly relax
// the guard.
func TestQuotedNextvalCostsNoRealRead(t *testing.T) {
	if !dangerousQuoted["NEXTVAL"] {
		t.Fatal("NEXTVAL dropped out of dangerousQuoted — layer 3b is now a no-op for the one name it exists to catch")
	}
}

// The banned list is quoted verbatim in MCP.md and README.md and reported by
// hana_doctor as a count. This pins the count so the docs cannot drift.
func TestBannedTokenCountIsPinned(t *testing.T) {
	const want = 33 // 32 originally + NEXTVAL
	if got := len(BannedTokens()); got != want {
		t.Fatalf("BannedTokens() has %d entries, want %d — update MCP.md's layer-3 row and README's banned list in the same change", got, want)
	}
}

func shortName(s string) string {
	if len(s) > 40 {
		s = s[:40]
	}
	return strings.ReplaceAll(s, " ", "_")
}
