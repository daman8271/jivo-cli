package guard

import "testing"

// TestQuotedNextvalIsRefused covers layer 3b.
//
// Found by an independent probe after the build: the guard blocked every
// realistic NEXTVAL spelling — bare, lower-case, quoted schema and sequence
// with a bare NEXTVAL, split across whitespace or a newline, separated by a
// comment, nested in a subquery or a CTE — but let the fully-quoted form
// through, because layer 0 masks quoted identifiers to maskIdent before the
// banned-token scan ever sees them.
//
// Quoting NEXTVAL probably demotes it to an ordinary column reference, so this
// form likely could not advance a sequence in the first place. It is refused
// anyway: verifying the "probably" against live HANA would have meant issuing
// the very write the guard exists to prevent, and a column named NEXTVAL is not
// something any JIVO read has ever needed.
func TestQuotedNextvalIsRefused(t *testing.T) {
	refuse := []string{
		`SELECT "JIVO_OIL_HANADB"."SOMESEQ"."NEXTVAL" FROM DUMMY`,
		`SELECT "SOMESEQ"."NEXTVAL" FROM DUMMY`,
		`SELECT "nextval" FROM DUMMY`,
		`WITH t AS (SELECT "SEQ"."NEXTVAL" AS N FROM DUMMY) SELECT N FROM t`,
	}
	for _, q := range refuse {
		if err := Check(q, MCPPolicy); err == nil {
			t.Errorf("quoted NEXTVAL was ALLOWED: %s", q)
		}
	}

	// Quoting must keep working for everything else — the masking exists so a
	// column that happens to share a keyword's name does not break a real read.
	allow := []string{
		`SELECT "CardCode", "DocTotal" FROM "JIVO_OIL_HANADB".OINV`,
		`SELECT "UPDATE" FROM "JIVO_OIL_HANADB"."SOMETABLE"`,
		`SELECT "SET", "INTO" FROM DUMMY`,
		`SELECT ROUND(TO_DOUBLE(SUM("DocTotal")),2) FROM "JIVO_OIL_HANADB".OINV`,
	}
	for _, q := range allow {
		if err := Check(q, MCPPolicy); err != nil {
			t.Errorf("legitimate quoted identifier was refused: %s -> %v", q, err)
		}
	}
}

// TestQuotedIdentsAreCaptured pins the lexer half of the fix: if Normalize ever
// stops recording quoted identifiers, layer 3b silently becomes a no-op and the
// test above would still pass for the wrong reason.
func TestQuotedIdentsAreCaptured(t *testing.T) {
	m, err := Normalize(`SELECT "CardCode" FROM "JIVO_OIL_HANADB"."OINV"`)
	if err != nil {
		t.Fatalf("normalize: %v", err)
	}
	want := []string{"CARDCODE", "JIVO_OIL_HANADB", "OINV"}
	if len(m.QuotedIdents) != len(want) {
		t.Fatalf("QuotedIdents = %v, want %v", m.QuotedIdents, want)
	}
	for i := range want {
		if m.QuotedIdents[i] != want[i] {
			t.Errorf("QuotedIdents[%d] = %q, want %q", i, m.QuotedIdents[i], want[i])
		}
	}
}
