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

// GuardReadOnly rejects statements that don't begin with SELECT or WITH. It is
// the first line of defense; the always-rolled-back transaction is the backstop.
func GuardReadOnly(sql string) error {
	s := strings.ToLower(stripLeading(sql))
	for _, p := range allowedPrefixes {
		if strings.HasPrefix(s, p) && (len(s) == len(p) || !isIdentChar(rune(s[len(p)]))) {
			return nil
		}
	}
	return &Error{"readonly", CodeReadOnly, fmt.Errorf(
		"read-only mode: %q is not an allowed statement (only SELECT and WITH are permitted)", firstWord(s))}
}

func stripLeading(s string) string {
	for {
		s = strings.TrimLeftFunc(s, unicode.IsSpace)
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
