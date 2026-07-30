// Package guard is the read-only gate every SQL statement must pass before
// hana-sql sends it to JIVO's production SAP HANA database.
//
// It is deliberately dependency-free (stdlib only) and knows nothing about
// sockets, MCP or the driver, so it can be read and reviewed on its own. It is
// layers 0-3 of the read-only design; layer 4 (the HANA "set transaction read
// only" access mode, always rolled back) and layer 5 (row/byte/time/concurrency
// caps) live in internal/hana.
//
//	layer 0  lex the statement, masking strings / quoted identifiers /
//	         comments, and FAIL CLOSED on anything unterminated or non-ASCII
//	layer 1  first token must be in the policy's allowlist
//	layer 2  exactly one statement (no ';' except one optional trailing)
//	layer 3  no banned keyword anywhere in the masked token stream
//
// Every layer above 0 reads the masked form only, so a keyword inside a string
// literal or a quoted identifier is data, not a verb.
//
// This honours CLAUDE.md Rule 0: never mutate SAP.
package guard

import (
	"errors"
	"fmt"
	"sort"
	"strings"
)

// Refusal is the typed error every layer returns. Layer says which one refused.
type Refusal struct {
	Layer int
	Msg   string
}

func (r *Refusal) Error() string {
	return fmt.Sprintf("REFUSED (read-only layer %d): %s", r.Layer, r.Msg)
}

// IsRefusal reports whether err came from this package (i.e. the statement was
// never sent to HANA).
func IsRefusal(err error) bool {
	var r *Refusal
	return errors.As(err, &r)
}

// Policy is a named set of statement starters that a caller is allowed to run.
type Policy struct {
	// Name identifies the policy in doctor output and audit lines.
	Name string
	// AllowFirst is the first-token allowlist, upper-case.
	AllowFirst []string
}

// MCPPolicy governs everything reachable by an AI client.
//
// EXPLAIN is deliberately absent: HANA's EXPLAIN PLAN FOR ... persists rows
// into SYS.EXPLAIN_PLAN_TABLE, which is a write. Do not "normalise" it back in.
var MCPPolicy = Policy{Name: "mcp", AllowFirst: []string{"SELECT", "WITH"}}

// CLIPolicy governs the human command line, which may also plan a query.
// EXPLAIN is accepted here so no existing human workflow regresses; the
// EXPLAIN_PLAN_TABLE write is a deliberate, operator-initiated act.
var CLIPolicy = Policy{Name: "cli", AllowFirst: []string{"SELECT", "WITH", "EXPLAIN"}}

func (p Policy) allowsFirst(tok string) bool {
	for _, a := range p.AllowFirst {
		if a == tok {
			return true
		}
	}
	return false
}

// allowList renders the allowlist for an error message: "SELECT / WITH".
func (p Policy) allowList() string { return strings.Join(p.AllowFirst, " / ") }

// bannedTokens are keywords that may not appear ANYWHERE in a statement, not
// just as the first word. Curated, not exhaustive:
//
//   - REPLACE is a legitimate HANA string function, so it is blocked at layer 1
//     (as a statement starter) only.
//   - BEGIN / END are not banned because CASE ... END is ordinary read SQL.
//   - UPDATE anywhere also catches SELECT ... FOR UPDATE, which takes real
//     locks on production rows.
//   - INTO catches SELECT ... INTO and EXPORT ... INTO '/path'.
//   - COMMIT / ROLLBACK / SAVEPOINT would let a statement escape the read-only
//     transaction that layer 4 opens.
//   - NEXTVAL is a write dressed as a SELECT: `SELECT "MY_SEQ".NEXTVAL FROM
//     DUMMY` passes layer 1 (first token SELECT), layer 2 and layer 3's other
//     entries, yet advancing a sequence changes persistent state that no
//     rollback undoes. The JIVO schemas are full of them (796 / 777 / 788
//     sequences in Oil / Mart / Beverages, counted live 2026-07-30), so the
//     claim "there is no argument that can make a tool write" was false until
//     this entry existed. CURRVAL is deliberately NOT banned: it only reads the
//     value the session already has and advances nothing.
var bannedTokens = []string{
	"INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "TRUNCATE",
	"CREATE", "DROP", "ALTER", "RENAME", "COMMENT", "TRIGGER", "PROCEDURE",
	"GRANT", "REVOKE",
	"LOCK", "CALL", "DO", "EXEC", "EXECUTE",
	"IMPORT", "EXPORT", "LOAD", "UNLOAD",
	"SET", "UNSET", "COMMIT", "ROLLBACK", "SAVEPOINT",
	"CONNECT", "DISCONNECT", "INTO",
	"NEXTVAL",
}

var bannedSet = func() map[string]bool {
	m := make(map[string]bool, len(bannedTokens))
	for _, t := range bannedTokens {
		m[t] = true
	}
	return m
}()

// BannedTokens returns a sorted copy of the layer-3 banned keyword list, for
// doctor output and documentation.
func BannedTokens() []string {
	out := append([]string(nil), bannedTokens...)
	sort.Strings(out)
	return out
}

// Check runs layers 0-3 over stmt. A nil return means the statement is a single
// read that may be sent to HANA (inside a read-only transaction). Any non-nil
// error is a *Refusal and the statement was never sent.
func Check(stmt string, p Policy) error {
	m, err := Normalize(stmt) // layer 0
	if err != nil {
		return err
	}

	// Layer 1 — first token allowlist.
	if len(m.Tokens) == 0 {
		return &Refusal{Layer: 1, Msg: "empty query — nothing to run"}
	}
	if first := m.Tokens[0]; !p.allowsFirst(first) {
		return &Refusal{Layer: 1, Msg: fmt.Sprintf(
			"only %s are allowed (read-only); got %q", p.allowList(), first)}
	}

	// Layer 2 — exactly one statement.
	if err := checkSingleStatement(m.Text); err != nil {
		return err
	}

	// Layer 3 — banned keyword anywhere in the masked token stream.
	for _, t := range m.Tokens {
		if bannedSet[t] {
			return &Refusal{Layer: 3, Msg: fmt.Sprintf(
				"banned keyword %q appears in the statement — only %s reads are allowed",
				t, p.allowList())}
		}
	}

	// Layer 3b — a handful of names stay dangerous even when double-quoted, so
	// they must be re-checked against the identifiers layer 0 masked away.
	for _, id := range m.QuotedIdents {
		if dangerousQuoted[id] {
			return &Refusal{Layer: 3, Msg: fmt.Sprintf(
				"quoted identifier %q is not allowed — quoting does not make it a read", id)}
		}
	}
	return nil
}

// dangerousQuoted lists names that layer 3 must still refuse when they arrive
// as double-quoted identifiers. The banned-token list cannot catch these on its
// own: layer 0 masks every quoted identifier to maskIdent so that a column
// legitimately named "UPDATE" does not blow up an ordinary read — and that same
// masking hides `SELECT "SEQ"."NEXTVAL" FROM DUMMY` from the token scan.
//
// Only NEXTVAL is listed, deliberately. Under HANA's rules quoting NEXTVAL
// almost certainly turns it into an ordinary column reference rather than the
// sequence pseudo-column, so this form probably cannot advance a sequence at
// all — but "probably" is the wrong standard for the one guard standing between
// a public MCP endpoint and JIVO's production books, and confirming it
// empirically would itself have been the write we are trying to prevent. It is
// refused because the cost of refusing is a column nobody has ever needed to
// read, and the cost of being wrong is an unrollbackable change to persistent
// state. The rest of bannedTokens is left out on purpose: names like "SET" and
// "INTO" are plausible column names, and blocking them when quoted would break
// real reads for no gain.
var dangerousQuoted = map[string]bool{
	"NEXTVAL": true,
}

// checkSingleStatement rejects a ';' anywhere except as the final non-space
// character, so a read cannot smuggle a second (writing) statement after it.
// The text it inspects is already masked, so a ';' inside a string literal or a
// comment neither hides a statement nor triggers a false refusal.
func checkSingleStatement(masked string) error {
	s := strings.TrimRight(masked, " \t\r\n")
	s = strings.TrimSuffix(s, ";")
	if strings.Contains(s, ";") {
		return &Refusal{Layer: 2, Msg: "multiple statements are not allowed (found ';') — run one statement at a time"}
	}
	return nil
}
