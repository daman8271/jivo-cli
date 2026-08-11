// Package db is the read-only SQL Server access layer for dsr.
//
// Read-only is enforced defensively at three levels, because the shared `ab`
// login on this instance may hold write privileges we cannot revoke:
//  1. a first-token allowlist (GuardReadOnly) — only SELECT / WITH pass;
//  2. every statement runs inside an explicit transaction that is ALWAYS rolled
//     back and never committed, so any write that somehow slipped past the
//     allowlist can never persist;
//  3. we only ever call QueryContext (never ExecContext) for user SQL.
//
// The transaction uses READ UNCOMMITTED isolation so our reads take no shared
// locks — they never block, and are never blocked by, the live portal's writers
// (equivalent to WITH (NOLOCK)). This is the right posture for observing a busy
// production database. Values are scanned generically and rendered as text.
package db

import (
	"context"
	"database/sql"
	"fmt"
	"net/url"
	"strings"
	"sync"
	"time"
	"unicode"

	_ "github.com/microsoft/go-mssqldb"

	"dsr/internal/config"
)

// Result is a generic tabular query result.
type Result struct {
	Columns []string
	Rows    [][]any
}

// Error carries an exit code so the CLI can map failures to shell exit codes.
type Error struct {
	Kind string
	Code int
	Err  error
}

func (e *Error) Error() string { return e.Err.Error() }
func (e *Error) ExitCode() int { return e.Code }
func (e *Error) Unwrap() error { return e.Err }

// Exit codes used throughout dsr.
const (
	CodeConn     = 3
	CodeQuery    = 4
	CodeReadOnly = 5
)

// DB holds one *sql.DB per database name (a SQL Server instance hosts many
// databases; switching --db opens a distinct connector).
type DB struct {
	prof   config.Profile
	stmtTO time.Duration
	mu     sync.Mutex
	conns  map[string]*sql.DB
}

// New builds a DB for the given profile. Connections are opened lazily.
func New(prof config.Profile, stmtTimeout time.Duration) *DB {
	return &DB{prof: prof, stmtTO: stmtTimeout, conns: map[string]*sql.DB{}}
}

// DefaultDatabase reports the profile's database (used when --db is unset).
func (d *DB) DefaultDatabase() string { return d.prof.Database }

func (d *DB) conn(dbName string) (*sql.DB, error) {
	if dbName == "" {
		dbName = d.prof.Database
	}
	d.mu.Lock()
	defer d.mu.Unlock()
	if c, ok := d.conns[dbName]; ok {
		return c, nil
	}
	q := url.Values{}
	q.Set("database", dbName)
	enc := d.prof.Encrypt
	if enc == "" {
		enc = "disable"
	}
	q.Set("encrypt", enc)
	q.Set("app name", "dsr-cli")
	u := url.URL{
		Scheme:   "sqlserver",
		User:     url.UserPassword(d.prof.User, d.prof.Password),
		Host:     fmt.Sprintf("%s:%d", d.prof.Host, d.prof.Port),
		RawQuery: q.Encode(),
	}
	c, err := sql.Open("sqlserver", u.String())
	if err != nil {
		return nil, &Error{"conn", CodeConn, err}
	}
	c.SetMaxOpenConns(4)
	c.SetConnMaxIdleTime(5 * time.Minute)
	d.conns[dbName] = c
	return c, nil
}

// Query runs a read-only statement against dbName and returns all rows.
func (d *DB) Query(ctx context.Context, dbName, query string, args ...any) (*Result, error) {
	if err := GuardReadOnly(query); err != nil {
		return nil, err
	}
	c, err := d.conn(dbName)
	if err != nil {
		return nil, err
	}
	// Read-only backstop: a transaction we ALWAYS roll back. READ UNCOMMITTED so
	// we take no locks against the live database.
	tx, err := c.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadUncommitted, ReadOnly: true})
	if err != nil {
		// Driver may reject the read-only flag; retry without it (we still roll back).
		tx, err = c.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadUncommitted})
		if err != nil {
			return nil, &Error{"conn", CodeConn, err}
		}
	}
	defer tx.Rollback()

	rows, err := tx.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, &Error{"query", CodeQuery, err}
	}
	defer rows.Close()

	cols, err := rows.Columns()
	if err != nil {
		return nil, &Error{"query", CodeQuery, err}
	}
	res := &Result{Columns: cols}
	for rows.Next() {
		cells := make([]any, len(cols))
		ptrs := make([]any, len(cols))
		for i := range cells {
			ptrs[i] = &cells[i]
		}
		if err := rows.Scan(ptrs...); err != nil {
			return nil, &Error{"query", CodeQuery, err}
		}
		row := make([]any, len(cols))
		copy(row, cells)
		res.Rows = append(res.Rows, row)
	}
	if err := rows.Err(); err != nil {
		return nil, &Error{"query", CodeQuery, err}
	}
	return res, nil
}

// Ident safely quotes a SQL Server identifier (or schema.name pair) with brackets
// for interpolation. Callers building `SELECT ... FROM <x>` MUST use this.
func Ident(parts ...string) string {
	var out []string
	for _, p := range parts {
		if p == "" {
			continue
		}
		out = append(out, "["+strings.ReplaceAll(p, "]", "]]")+"]")
	}
	return strings.Join(out, ".")
}

// Lit safely single-quotes a string literal for SQL Server.
func Lit(s string) string {
	return "'" + strings.ReplaceAll(s, "'", "''") + "'"
}

// Close releases all connectors.
func (d *DB) Close() {
	d.mu.Lock()
	defer d.mu.Unlock()
	for _, c := range d.conns {
		c.Close()
	}
	d.conns = map[string]*sql.DB{}
}

var allowedPrefixes = []string{"select", "with"}

// GuardReadOnly rejects anything that is not exactly ONE leading-SELECT (or
// leading-WITH) statement. It is the first line of defense; the
// always-rolled-back transaction is the backstop.
//
// Two separate bypasses are closed here, both of which used to pass:
//
//  1. Comment prefixing. `stripLeading` removes the whitespace, line comments
//     (-- to end of line), block comments and statement separators that SQL
//     Server itself skips before parsing the first keyword, so
//     "/* x */ EXEC ..." is judged on EXEC, not on the comment.
//
//  2. Batching. A first-token check alone accepts
//     "SELECT 1; DECLARE @x int" — the second statement reaches SQL Server,
//     and the rolled-back transaction is NOT a complete backstop for it
//     (rollback undoes DML/DDL but not out-of-band effects such as
//     xp_cmdshell, sp_configure, BACKUP or a linked-server call, and does not
//     stop a WAITFOR-style stall). The connecting DSR login is a sysadmin, so
//     that gap is not theoretical. hasTrailingStatement therefore rejects any
//     statement separator followed by more executable SQL; a trailing
//     semicolon on its own is still fine.
func GuardReadOnly(sql string) error {
	s := strings.ToLower(stripLeading(sql))
	if hasTrailingStatement(s) {
		return &Error{"readonly", CodeReadOnly, fmt.Errorf(
			"read-only mode: only a SINGLE SELECT or WITH statement is allowed (a second statement was found after a ';')")}
	}
	for _, p := range allowedPrefixes {
		if strings.HasPrefix(s, p) && (len(s) == len(p) || !isIdentChar(rune(s[len(p)]))) {
			return nil
		}
	}
	return &Error{"readonly", CodeReadOnly, fmt.Errorf(
		"read-only mode: %q is not an allowed statement (only SELECT and WITH are permitted)", firstWord(s))}
}

// stripLeading removes leading whitespace, SQL line comments (-- to end of
// line), block comments (/* ... */) and statement separators (;) — everything
// the server skips before it parses the first keyword. A gate that does not
// strip them is judging different text than the one the driver executes.
func stripLeading(s string) string {
	for {
		s = strings.TrimLeft(strings.TrimLeftFunc(s, unicode.IsSpace), ";")
		switch {
		case strings.HasPrefix(s, "--"):
			if i := strings.IndexByte(s, '\n'); i >= 0 {
				s = s[i+1:]
				continue
			}
			return ""
		case strings.HasPrefix(s, "/*"):
			if i := strings.Index(s, "*/"); i >= 0 {
				s = s[i+2:]
				continue
			}
			return ""
		}
		return s
	}
}

// hasTrailingStatement reports whether s contains a statement terminator
// followed by more executable SQL. A trailing semicolon (with only whitespace
// or comments after it) is allowed; a second statement is not. Semicolons
// inside string literals, quoted identifiers, [bracket] identifiers and
// comments are ignored, so a legitimate "WHERE note = 'a;b'" still passes.
func hasTrailingStatement(s string) bool {
	var inSingle, inDouble, inBracket, inLineComment, inBlockComment bool

	for i := 0; i < len(s); i++ {
		ch := s[i]
		var next byte
		if i+1 < len(s) {
			next = s[i+1]
		}

		switch {
		case inLineComment:
			if ch == '\n' {
				inLineComment = false
			}
			continue
		case inBlockComment:
			if ch == '*' && next == '/' {
				inBlockComment = false
				i++
			}
			continue
		case inSingle:
			// '' is an escaped quote inside a T-SQL string literal.
			if ch == '\'' {
				if next == '\'' {
					i++
					continue
				}
				inSingle = false
			}
			continue
		case inDouble:
			if ch == '"' {
				if next == '"' {
					i++
					continue
				}
				inDouble = false
			}
			continue
		case inBracket:
			if ch == ']' {
				inBracket = false
			}
			continue
		}

		switch {
		case ch == '-' && next == '-':
			inLineComment = true
			i++
		case ch == '/' && next == '*':
			inBlockComment = true
			i++
		case ch == '\'':
			inSingle = true
		case ch == '"':
			inDouble = true
		case ch == '[':
			inBracket = true
		case ch == ';':
			// Anything executable after the separator makes this a batch.
			return stripLeading(s[i+1:]) != ""
		}
	}
	return false
}

func firstWord(s string) string {
	for i, r := range s {
		if !isIdentChar(r) {
			return s[:i]
		}
	}
	return s
}

func isIdentChar(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsDigit(r)
}
