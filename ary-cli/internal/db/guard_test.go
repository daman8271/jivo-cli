package db

import "testing"

// TestGuardReadOnlyAcceptsSingleReads pins the statements that MUST keep
// working — the whole CLI is built on them.
func TestGuardReadOnlyAcceptsSingleReads(t *testing.T) {
	ok := []string{
		"SELECT 1",
		"select top 5 * from tbl_retailers",
		"  \n\t SELECT 1",
		"-- a comment\nSELECT 1",
		"/* block */ SELECT 1",
		"WITH x AS (SELECT 1 AS n) SELECT * FROM x",
		"SELECT 1;",          // a bare trailing separator is not a second statement
		"SELECT 1; -- done",  // nor is a comment after it
		"SELECT 1;\n/* x */", // nor a block comment
		"SELECT COUNT(*) AS n FROM [dbo].[tbl_roles] WHERE note = 'a;b'",
		"SELECT * FROM [dbo].[weird;name]",
		"SELECT 'it''s; fine' AS s",
	}
	for _, q := range ok {
		if err := GuardReadOnly(q); err != nil {
			t.Errorf("GuardReadOnly(%q) = %v, want nil", q, err)
		}
	}
}

// TestGuardReadOnlyRejectsBatches is the regression test for the bypass that
// was reproduced live against DSR_V6: a first-token check let a SECOND,
// non-SELECT statement through to a sysadmin login. The rolled-back
// transaction does not undo out-of-band effects, so this gate is the one that
// has to hold.
func TestGuardReadOnlyRejectsBatches(t *testing.T) {
	bad := []string{
		"SELECT 1 AS a; SELECT 2 AS b",
		"SELECT 1 AS a; DECLARE @x int = 1",
		"SELECT 1; EXEC xp_cmdshell 'whoami'",
		"select 1;update tbl_roles set name='x'",
		"WITH x AS (SELECT 1 AS n) SELECT * FROM x; DROP TABLE t",
		"SELECT 'a;b' AS s; DECLARE @y int",
		"SELECT 1 /* c */ ; sp_configure",
	}
	for _, q := range bad {
		err := GuardReadOnly(q)
		if err == nil {
			t.Errorf("GuardReadOnly(%q) = nil, want a read-only rejection", q)
			continue
		}
		if got := err.(*Error).Code; got != CodeReadOnly {
			t.Errorf("GuardReadOnly(%q) exit code = %d, want %d", q, got, CodeReadOnly)
		}
	}
}

// TestGuardReadOnlyRejectsNonSelectLeadingKeywords covers the original
// first-token rule, including the comment-prefixed forms.
func TestGuardReadOnlyRejectsNonSelectLeadingKeywords(t *testing.T) {
	bad := []string{
		"UPDATE tbl_roles SET name = 'x'",
		"DELETE FROM tbl_roles",
		"INSERT INTO tbl_roles VALUES (1)",
		"EXEC sp_who",
		"DROP TABLE t",
		"/* SELECT */ EXEC xp_cmdshell 'whoami'",
		"-- SELECT\nEXEC sp_configure",
		"; DELETE FROM tbl_roles",
		"selectx * from t", // not the SELECT keyword
		"",
	}
	for _, q := range bad {
		if err := GuardReadOnly(q); err == nil {
			t.Errorf("GuardReadOnly(%q) = nil, want a read-only rejection", q)
		}
	}
}

// TestWhereClauseInjectionIsRejected is the `dsr count <table> --where` shape:
// the flag value is appended raw into the WHERE clause, so a batching payload
// there used to reach SQL Server. It must not any more.
func TestWhereClauseInjectionIsRejected(t *testing.T) {
	q := "SELECT COUNT(*) AS n FROM [dbo].[tbl_roles] WHERE 1=0; DECLARE @y int = 1"
	if err := GuardReadOnly(q); err == nil {
		t.Fatal("a --where payload carrying a second statement was accepted; the guard must reject it")
	}
}
