// Package db is the read-only PostgreSQL access layer for postsql.
//
// Read-only is enforced defensively at three levels:
//  1. connection startup param default_transaction_read_only=on
//  2. every statement runs inside a BEGIN ... READ ONLY transaction, which the
//     server refuses to let write even for a superuser role
//  3. a first-token allowlist (GuardReadOnly) for friendly early errors
//
// Queries use the simple protocol and are read back with rows.RawValues(), so
// every value is kept as its exact server-sent text representation (what psql
// prints: uuid as "a1b2c3..", numeric as "20.0000", array as "{1,2,3}", json
// verbatim, SQL NULL as a Go nil). This avoids pgx type-decoding every value
// into a pgtype struct — which would otherwise render as garbage in table/CSV
// output and mis-marshal in JSON — and is ideal for feeding AI agents.
package db

import (
	"context"
	"fmt"
	"net/url"
	"strings"
	"sync"
	"time"
	"unicode"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"postsql/internal/config"
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

// Exit codes used throughout postsql.
const (
	CodeConn     = 3
	CodeQuery    = 4
	CodeReadOnly = 5
)

// DB holds one connection pool per database name (Postgres binds a connection
// to a single database, so switching --db means a distinct pool).
type DB struct {
	prof   config.Profile
	stmtTO time.Duration
	mu     sync.Mutex
	pools  map[string]*pgxpool.Pool
}

// New builds a DB for the given profile. Connections are opened lazily.
// stmtTimeout, when > 0, is applied as a server-side statement_timeout so the
// server independently aborts long statements even if the client's context
// cancel is lost (dropped connection). Pass 0 to leave the server default.
func New(prof config.Profile, stmtTimeout time.Duration) *DB {
	return &DB{prof: prof, stmtTO: stmtTimeout, pools: map[string]*pgxpool.Pool{}}
}

// DefaultDatabase reports the profile's database (used when --db is unset).
func (d *DB) DefaultDatabase() string { return d.prof.Database }

func (d *DB) pool(ctx context.Context, dbName string) (*pgxpool.Pool, error) {
	if dbName == "" {
		dbName = d.prof.Database
	}
	d.mu.Lock()
	defer d.mu.Unlock()
	if p, ok := d.pools[dbName]; ok {
		return p, nil
	}
	u := url.URL{
		Scheme: "postgres",
		User:   url.UserPassword(d.prof.User, d.prof.Password),
		Host:   fmt.Sprintf("%s:%d", d.prof.Host, d.prof.Port),
		Path:   "/" + dbName,
	}
	cfg, err := pgxpool.ParseConfig(u.String())
	if err != nil {
		return nil, &Error{"conn", CodeConn, err}
	}
	// Simple protocol => uniform text values; read-only startup param.
	cfg.ConnConfig.DefaultQueryExecMode = pgx.QueryExecModeSimpleProtocol
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["application_name"] = "postsql"
	// Server-side backstop: abort any statement running longer than the
	// configured timeout even if the client-side context cancel never arrives.
	if d.stmtTO > 0 {
		ms := d.stmtTO.Milliseconds()
		if ms < 1 {
			ms = 1
		}
		cfg.ConnConfig.RuntimeParams["statement_timeout"] = fmt.Sprintf("%d", ms)
	}
	cfg.MaxConns = 4
	p, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		return nil, &Error{"conn", CodeConn, err}
	}
	d.pools[dbName] = p
	return p, nil
}

// Query runs a read-only statement against dbName and returns all rows.
func (d *DB) Query(ctx context.Context, dbName, sql string, args ...any) (*Result, error) {
	if err := GuardReadOnly(sql); err != nil {
		return nil, err
	}
	p, err := d.pool(ctx, dbName)
	if err != nil {
		return nil, err
	}
	tx, err := p.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly})
	if err != nil {
		return nil, &Error{"conn", CodeConn, err}
	}
	defer tx.Rollback(ctx)

	rows, err := tx.Query(ctx, sql, args...)
	if err != nil {
		return nil, &Error{"query", CodeQuery, err}
	}
	defer rows.Close()

	res := &Result{}
	for _, fd := range rows.FieldDescriptions() {
		res.Columns = append(res.Columns, string(fd.Name))
	}
	for rows.Next() {
		// Under the simple protocol, RawValues() returns the exact text bytes
		// the server sent (what psql prints): uuid -> "a1b2c3..", numeric ->
		// "20.0000", array -> "{1,2,3}", json/jsonb verbatim. Decoding with
		// Values() instead would hand back pgtype structs / [16]byte that
		// %v-dump as garbage in table/CSV output and mis-marshal in JSON.
		// A nil raw value is a SQL NULL. We copy into fresh strings because
		// the raw buffer is only valid until the next Next().
		raw := rows.RawValues()
		row := make([]any, len(raw))
		for i, b := range raw {
			if b == nil {
				row[i] = nil
			} else {
				row[i] = string(b)
			}
		}
		res.Rows = append(res.Rows, row)
	}
	if err := rows.Err(); err != nil {
		return nil, &Error{"query", CodeQuery, err}
	}
	return res, nil
}

// Ident safely quotes a possibly-qualified identifier (schema.table) for
// interpolation into SQL text. Callers building `SELECT * FROM <x>` MUST use
// this rather than raw string formatting.
func Ident(parts ...string) string {
	clean := make([]string, 0, len(parts))
	for _, p := range parts {
		if p != "" {
			clean = append(clean, p)
		}
	}
	return pgx.Identifier(clean).Sanitize()
}

// Close releases all pools.
func (d *DB) Close() {
	d.mu.Lock()
	defer d.mu.Unlock()
	for _, p := range d.pools {
		p.Close()
	}
	d.pools = map[string]*pgxpool.Pool{}
}

var allowedPrefixes = []string{"select", "with", "explain", "show", "table", "values"}

// GuardReadOnly rejects statements that don't begin with a read-only keyword.
// It is a friendly-error guard, not the primary defense — the READ ONLY
// transaction is what actually blocks writes server-side.
func GuardReadOnly(sql string) error {
	s := strings.ToLower(stripLeading(sql))
	for _, p := range allowedPrefixes {
		if strings.HasPrefix(s, p) && (len(s) == len(p) || !isIdentChar(rune(s[len(p)]))) {
			return nil
		}
	}
	return &Error{"readonly", CodeReadOnly, fmt.Errorf(
		"read-only mode: %q is not an allowed statement (only SELECT/WITH/EXPLAIN/SHOW/TABLE/VALUES)", firstWord(s))}
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
