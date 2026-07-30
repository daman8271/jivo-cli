package hana

import (
	"context"
	"database/sql"
	"database/sql/driver"
	"errors"
	"fmt"
	"io"
	"reflect"
	"sync"
	"sync/atomic"
	"time"
)

// An in-memory database/sql driver, so the parts of this package that matter
// most — the READ ONLY transaction (layer 4) and the row/byte/time/concurrency
// caps (layer 5) — are tested with no HANA anywhere in the process.
//
// It records what the pipeline actually did to the transaction: whether
// ReadOnly was requested, whether Rollback ran, and whether Commit was ever
// called (it must never be).

type fakeCol struct {
	name     string
	dbType   string
	scanType reflect.Type
	prec     int64
	scale    int64
	hasDec   bool
}

// fakeScript is what one fake connection will do.
type fakeScript struct {
	cols []fakeCol
	// row builds row i. Returning false ends the result set.
	row func(i int) ([]driver.Value, bool)
	// queryErr, when set, is returned instead of a result set.
	queryErr error
	// queryDelay makes the query outlive a short deadline.
	queryDelay time.Duration
	// beginErr, when set, fails BeginTx.
	beginErr error
}

// fakeStats is what the test asserts on afterwards.
type fakeStats struct {
	begins     atomic.Int64
	readOnly   atomic.Int64
	rollbacks  atomic.Int64
	commits    atomic.Int64
	queries    atomic.Int64
	inFlight   atomic.Int64
	maxInFlite atomic.Int64
	lastStmt   atomic.Value // string
	lastArgs   atomic.Value // []driver.NamedValue
}

type fakeRegistryEntry struct {
	script *fakeScript
	stats  *fakeStats
}

var (
	fakeMu   sync.Mutex
	fakeReg  = map[string]*fakeRegistryEntry{}
	fakeSeq  atomic.Int64
	fakeOnce sync.Once
)

func registerFake(script *fakeScript) (dsn string, stats *fakeStats) {
	fakeOnce.Do(func() { sql.Register("hanafake", fakeDriver{}) })
	dsn = fmt.Sprintf("fake-%d", fakeSeq.Add(1))
	stats = &fakeStats{}
	fakeMu.Lock()
	fakeReg[dsn] = &fakeRegistryEntry{script: script, stats: stats}
	fakeMu.Unlock()
	return dsn, stats
}

// newFakeDB builds a DB whose pool is the in-memory driver.
func newFakeDB(t interface{ Fatalf(string, ...any) }, opts Options, script *fakeScript) (*DB, *fakeStats) {
	dsn, stats := registerFake(script)
	d := New(fakeConfig(), opts)
	d.dial = func(context.Context) (*sql.DB, string, error) {
		db, err := sql.Open("hanafake", dsn)
		if err != nil {
			return nil, "", err
		}
		db.SetMaxOpenConns(8)
		return db, "fake", nil
	}
	return d, stats
}

type fakeDriver struct{}

func (fakeDriver) Open(dsn string) (driver.Conn, error) {
	fakeMu.Lock()
	e := fakeReg[dsn]
	fakeMu.Unlock()
	if e == nil {
		return nil, errors.New("unknown fake dsn " + dsn)
	}
	return &fakeConn{script: e.script, stats: e.stats}, nil
}

type fakeConn struct {
	script *fakeScript
	stats  *fakeStats
}

func (c *fakeConn) Prepare(string) (driver.Stmt, error) {
	return nil, errors.New("fake: Prepare is not used; the pipeline queries directly")
}
func (c *fakeConn) Close() error { return nil }
func (c *fakeConn) Begin() (driver.Tx, error) {
	return nil, errors.New("fake: legacy Begin must not be used — the pipeline needs BeginTx to pass ReadOnly")
}

func (c *fakeConn) BeginTx(ctx context.Context, opts driver.TxOptions) (driver.Tx, error) {
	c.stats.begins.Add(1)
	if opts.ReadOnly {
		c.stats.readOnly.Add(1)
	}
	if c.script.beginErr != nil {
		return nil, c.script.beginErr
	}
	return &fakeTx{stats: c.stats}, nil
}

func (c *fakeConn) QueryContext(ctx context.Context, query string, args []driver.NamedValue) (driver.Rows, error) {
	c.stats.queries.Add(1)
	c.stats.lastStmt.Store(query)
	c.stats.lastArgs.Store(args)

	n := c.stats.inFlight.Add(1)
	for {
		m := c.stats.maxInFlite.Load()
		if n <= m || c.stats.maxInFlite.CompareAndSwap(m, n) {
			break
		}
	}
	defer c.stats.inFlight.Add(-1)

	if d := c.script.queryDelay; d > 0 {
		select {
		case <-time.After(d):
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}
	if c.script.queryErr != nil {
		return nil, c.script.queryErr
	}
	return &fakeRows{script: c.script}, nil
}

type fakeTx struct{ stats *fakeStats }

func (t *fakeTx) Commit() error {
	t.stats.commits.Add(1)
	return errors.New("fake: Commit was called; this package must never commit")
}
func (t *fakeTx) Rollback() error { t.stats.rollbacks.Add(1); return nil }

type fakeRows struct {
	script *fakeScript
	i      int
}

func (r *fakeRows) Columns() []string {
	out := make([]string, len(r.script.cols))
	for i, c := range r.script.cols {
		out[i] = c.name
	}
	return out
}
func (r *fakeRows) Close() error { return nil }
func (r *fakeRows) Next(dest []driver.Value) error {
	vals, ok := r.script.row(r.i)
	if !ok {
		return io.EOF
	}
	r.i++
	copy(dest, vals)
	return nil
}

// The optional metadata interfaces database/sql exposes as ColumnTypes.
func (r *fakeRows) ColumnTypeDatabaseTypeName(i int) string { return r.script.cols[i].dbType }
func (r *fakeRows) ColumnTypeScanType(i int) reflect.Type {
	if t := r.script.cols[i].scanType; t != nil {
		return t
	}
	return reflect.TypeOf(new(any)).Elem()
}
func (r *fakeRows) ColumnTypePrecisionScale(i int) (int64, int64, bool) {
	c := r.script.cols[i]
	return c.prec, c.scale, c.hasDec
}

var (
	_ driver.Rows                           = (*fakeRows)(nil)
	_ driver.RowsColumnTypeDatabaseTypeName = (*fakeRows)(nil)
	_ driver.RowsColumnTypeScanType         = (*fakeRows)(nil)
	_ driver.RowsColumnTypePrecisionScale   = (*fakeRows)(nil)
	_ driver.ConnBeginTx                    = (*fakeConn)(nil)
	_ driver.QueryerContext                 = (*fakeConn)(nil)
)
